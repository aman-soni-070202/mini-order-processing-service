from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    unit_price: float
    discount_applied: bool

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    name: str
    description: str
    price: float = Field(..., gt=0)
    inventory: int = Field(..., ge=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    customer_name: str
    customer_email: EmailStr


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: int
    items: List[OrderItemResponse]
    subtotal: float
    shipping_fee: float
    total_amount: float
    created_at: datetime

    class Config:
        orm_mode = True

class InventoryUpdate(BaseModel):
    """Schema for inventory update requests"""
    quantity: int = Field(..., description="The quantity to add (positive) or remove (negative)")
