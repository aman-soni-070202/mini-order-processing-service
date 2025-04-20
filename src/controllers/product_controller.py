from sqlalchemy.orm import Session
from src.schemas import schema
from src.services.product_service import ProductService


class ProductController:
    def __init__(self, db: Session):
        self.product_service = ProductService(db)

    def get_product_list(self, skip: int = 0, limit: int = 100):
        return self.product_service.get_product_list(skip, limit)

    def get_product(self, product_id: int):
        return self.product_service.get_product(product_id)

    def create_product(self, product: schema.ProductCreate):
        return self.product_service.create_product(product)

    def update_product_inventory(self, product_id: int, inventory_update: schema.InventoryUpdate):
        return self.product_service.update_product_inventory(product_id, inventory_update)
