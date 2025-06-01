from fastapi import APIRouter, Depends
from sqlmodel import Session
from db import get_session
from services import productService
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import List,Dict,Any
product_router = APIRouter(tags=['Product API'], prefix='/product')
product_service = productService()


@product_router.post('/addProduct', status_code=201)
async def add_product(
    pname: str = Form(...),
    p_desc: str = Form(...),
    price: str = Form(...),
    images: List[UploadFile] = File(...),
    session: Session = Depends(get_session)
):
    try:
        # Convert price to float
        price_float = float(price)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be a valid number"
        )
    
    # Create a simple object to hold the product data
    class ProductModel:
        def __init__(self, pname, p_desc, price):
            self.pname = pname
            self.p_desc = p_desc
            self.price = price
    
    product_model = ProductModel(pname=pname, p_desc=p_desc, price=price_float)
    
    return product_service.add_product(
        product_model=product_model,
        images=images,
        session=session
    )


@product_router.get('/all', response_model=Dict[str, List[Dict[str, Any]]])
async def get_all_products(session: Session = Depends(get_session)):
    return product_service.get_all_products(session)

@product_router.put('/{product_id}')
async def update_product(
    product_id: int,
    pname: str = Form(...),
    p_desc: str = Form(...),
    price: str = Form(...),
    images: List[UploadFile] = File(...),
    session: Session = Depends(get_session)
):
    try:
        price_float = float(price)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be a valid number"
        )
    
    class ProductModel:
        def __init__(self, pname, p_desc, price):
            self.pname = pname
            self.p_desc = p_desc
            self.price = price
    
    product_model = ProductModel(pname=pname, p_desc=p_desc, price=price_float)
    
    return product_service.update_product(
        product_model=product_model,
        product_id=product_id,
        session=session,
        images=images
    )

@product_router.delete('/{product_id}')
async def delete_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    return product_service.remove_product(product_id, session)

@product_router.get('/{product_id}')
async def get_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    return product_service.retrieve_product(product_id, session)