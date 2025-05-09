from sqlmodel import select, Session
from models import Products, Images
from fastapi import HTTPException, UploadFile, status
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class productService:
    @staticmethod
    def save_uploaded_file(file: UploadFile) -> str:
        """Save uploaded file and return its URL"""
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
        
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            # Read file content in binary mode
            contents = file.file.read()
            # Write file in binary mode
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            return f"/static/{filename}"
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
            statement = select(Products)
            products = session.exec(statement).all()
            
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

    def remove_product(self, product_id: int, session: Session) -> Dict[str, str]:
        """Remove a product"""
        try:
            product = session.get(Products, product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            session.delete(product)
            session.commit()
            return {'message': 'Product deleted successfully'}
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete product: {str(e)}"
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

            # Create product
            product = Products(
                pname=product_model.pname,
                p_desc=product_model.p_desc,
                price=product_model.price,
                user_id=getattr(product_model, 'user_id', None)
            )
            session.add(product)
            session.commit()
            session.refresh(product)

            # Process images
            image_urls = []
            for image in images:
                try:
                    image_url = self.save_uploaded_file(image)
                    session.add(Images(image_url=image_url, product_id=product.id))
                    image_urls.append(image_url)
                except HTTPException as e:
                    continue  # Skip invalid images but continue with others

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