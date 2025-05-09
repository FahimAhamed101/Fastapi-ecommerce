from fastapi import APIRouter
from product import product_router






app_router = APIRouter()
app_router.include_router(product_router)
