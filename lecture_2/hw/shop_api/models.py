from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    id: int = None
    name: str
    price: float
    deleted: bool = False

class ItemInCart(BaseModel):
    id: int = None
    quantity: int

class Cart(BaseModel):
    id: int
    items: List[ItemInCart] = []
    price: float = 0.0