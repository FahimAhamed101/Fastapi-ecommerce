from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlmodel import select, Session
from models import Products, Images
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}



class productService:
    @staticmethod
    def save_uploaded_file(file: UploadFile, base_url: str = "http://localhost:8000") -> str:
        """Save uploaded file and return its URL """
        if not file.filename or '.' not in file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name"
            )
        
        ext = file.filename.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            contents = file.file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            return f"{base_url}/static/{filename}"
            #return f"/static/{filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        finally:
            file.file.close()

    def get_all_products(self, session: Session) -> Dict[str, List[Dict[str, Any]]]:
        """Get all products"""
        try:
            products = session.exec(select(Products)).all()
            return {
                'products': [{
                    "id": p.id,
                    "pname": p.pname,
                    "p_desc": p.p_desc,
                    "price": p.price,
                    "images": [img.image_url for img in p.images]
                } for p in products]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch products: {str(e)}"
            )

    def add_product(
        self, 
        product_model: Any, 
        images: List[UploadFile], 
        session: Session
    ) -> Dict[str, Any]:
        """Add a new product with uploaded images"""
        try:
            if not images:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one image is required"
                )

            product = Products(
                pname=product_model.pname,
                p_desc=product_model.p_desc,
                price=product_model.price,
                
            )
            session.add(product)
            session.commit()
            session.refresh(product)

            image_urls = []
            for image in images:
                try:
                    image_url = self.save_uploaded_file(image, base_url="http://localhost:8000")
                    #image_url = self.save_uploaded_file(image)
                    session.add(Images(image_url=image_url, product_id=product.id))
                    image_urls.append(image_url)
                except HTTPException:
                    continue

            if not image_urls:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid images were provided"
                )

            session.commit()
            return {
                'success': True,
                'message': 'Product created successfully',
                'product_id': product.id,
                'image_urls': image_urls,
                'product_details': {
                    'pname': product.pname,
                    'p_desc': product.p_desc,
                    'price': product.price
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create product: {str(e)}"
            )
        
    def update_product(
        self,
        product_model: Any,
        product_id: int,
       
        session: Session,
        images: Optional[List[UploadFile]] = None
    ) -> Dict[str, Any]:
        """Update an existing product and its images"""
        try:
            product = session.exec(
                select(Products).where(Products.id == product_id)
            ).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            product.pname = product_model.pname
            product.p_desc = product_model.p_desc
            product.price = product_model.price
            
            image_urls = []
            if images is not None:
                existing_images = session.exec(
                    select(Images).where(Images.product_id == product_id)
                ).all()
                for img in existing_images:
                    session.delete(img)
                
                for image in images:
                    try:
                        image_url = self.save_uploaded_file(image, base_url="http://localhost:8000")
                        session.add(Images(
                            image_url=image_url, 
                            product_id=product.id
                        ))
                        image_urls.append(image_url)
                    except HTTPException:
                        continue

            session.commit()
            
            return {
                'success': True,
                'message': 'Product updated successfully',
                'product_id': product.id,
                'image_urls': image_urls if images is not None else [],
                'product_details': {
                    'pname': product.pname,
                    'p_desc': product.p_desc,
                    'price': product.price
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update product: {str(e)}"
            )
    
    def remove_product(self, product_id: int, session: Session) -> Dict[str, str]:
        """Remove a product and its associated images"""
        try:
        # First get the product with its images
            product = session.exec(
                select(Products).where(Products.id == product_id)
            ).first()

            if not product:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
                )

        # Delete all associated images first
            images = session.exec(
                select(Images).where(Images.product_id == product_id)
            ).all()
        
            for image in images:
            # Optional: Delete the actual image file from storage
                try:
                    if image.image_url.startswith('/static/'):
                        file_path = os.path.join(UPLOAD_FOLDER, image.image_url[8:])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                except Exception as e:
                # Log the error but continue with deletion
                    print(f"Failed to delete image file: {str(e)}")
            
            # Delete the image record from database
                session.delete(image)

        # Now delete the product
            session.delete(product)
            session.commit()
        
            return {'message': 'Product and associated images deleted successfully'}
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete product: {str(e)}"
            )

    def retrieve_product(self, product_id: int, session: Session) -> Dict[str, Any]:
        """Retrieve a single product"""
        try:
            product = session.exec(
                select(Products).where(Products.id == product_id)
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            return {
                'product': {
                    'id': product.id,
                    'images': [{'image_url': img.image_url} for img in product.images],
                    'pname': product.pname,
                    'p_desc': product.p_desc,
                    'price': product.price
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve product: {str(e)}"
            )



