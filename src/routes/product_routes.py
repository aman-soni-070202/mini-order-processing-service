from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session
from typing import List
from src.controllers.product_controller import ProductController
from src.schemas import schema
from src.db.database import get_db


product_router = APIRouter(tags=["Products"])


@product_router.get("/get_all_products", response_model=List[schema.ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all available products"""
    product_controller = ProductController(db)
    return product_controller.get_product_list(skip, limit)


@product_router.get("/get_product/{product_id}", response_model=schema.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product_controller = ProductController(db)
    return product_controller.get_product(product_id)


@product_router.post("/add_product", response_model=schema.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: schema.ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    product_controller = ProductController(db)
    return product_controller.create_product(product)


@product_router.patch("/update_product_inventory/{product_id}", response_model=schema.ProductResponse)
def update_product_inventory(product_id: int, inventory_update: schema.InventoryUpdate, db: Session = Depends(get_db)):
    """Update product inventory by adding or removing stock"""
    product_controller = ProductController(db)
    return product_controller.update_product_inventory(product_id, inventory_update)
