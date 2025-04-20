from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
from typing import List
from src.schemas import schema
from src.db.database import get_db
from src.services.order_service import OrderService


order_router = APIRouter(tags=["Orders"])


@order_router.post("/add_order", response_model=schema.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: schema.OrderCreate, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    return order_service.create_order(order)


@order_router.get("/get_all_order", response_model=List[schema.OrderResponse])
def get_all_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    return order_service.get_all_orders(skip, limit)


@order_router.get("/get_order/{order_id}", response_model=schema.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    return order_service.get_order(order_id)

