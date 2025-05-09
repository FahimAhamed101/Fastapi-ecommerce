from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List



class Images(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    image_url: str
    product_id: int = Field(foreign_key="products.id")
    product: Optional["Products"] = Relationship(back_populates="images")

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pname: str
    p_desc: str
    price: float
    images: List["Images"] = Relationship(back_populates="product")  
    
class addProductModel(SQLModel):
    pname: str
    p_desc: str
    price: float
    images: List[str]