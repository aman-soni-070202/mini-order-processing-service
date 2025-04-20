from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.db.models import model
from src.schemas import schema


class ProductService:
    def __init__(self, db: Session):
        self.db = db


    def get_product_list(self, skip: int = 0, limit: int = 100):
        """Get all available products"""
        products = self.db.query(model.Product).offset(skip).limit(limit).all()
        return products


    def get_product(self, product_id: int):
        """Get a specific product by ID"""
        product = self.db.query(model.Product).filter(model.Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product


    def create_product(self, product: schema.ProductCreate):
        """Create a new product"""
        db_product = model.Product(**product.dict())
        self.db.add(db_product)
        try:
            self.db.commit()
            self.db.refresh(db_product)
            return db_product
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Product already exists")


    def update_product_inventory(self, product_id: int, inventory_update: schema.InventoryUpdate):
        """
        Update product inventory by adding or removing stock.
        Use positive quantity to add inventory, negative to remove inventory.
        """
        # Get the product
        product = self.db.query(model.Product).filter(model.Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
    
        # Calculate new inventory level
        new_inventory = product.inventory + inventory_update.quantity
        
        # Validate new inventory level
        if new_inventory < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reduce inventory below zero. Current inventory: {product.inventory}, Requested change: {inventory_update.quantity}"
            )
        
        # Update inventory
        product.inventory = new_inventory
        
        try:
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating inventory: {str(e)}")
