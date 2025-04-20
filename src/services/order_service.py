from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.db.models import model
from src.schemas import schema
from dotenv import load_dotenv
import os

load_dotenv()

BULK_DISCOUNT_THRESHOLD = int(os.getenv("BULK_DISCOUNT_THRESHOLD"))
BULK_DISCOUNT_PERCENT = int(os.getenv("BULK_DISCOUNT_PERCENT"))
FREE_SHIPPING_THRESHOLD = float(os.getenv("FREE_SHIPPING_THRESHOLD"))
SHIPPING_FEE = float(os.getenv("SHIPPING_FEE"))


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order: schema.OrderCreate):
        """Process a new order with discount and shipping fee calculation"""
        # Calculate order details and validate inventory
        order_items = []
        subtotal = 0.0

        for item in order.items:
            # Get product from database
            product = self.db.query(model.Product).filter(model.Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
        
            # Check inventory
            if product.inventory < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Not enough inventory for product {product.name}. Requested: {item.quantity}, Available: {product.inventory}"
                )
            
            # Calculate item price with potential bulk discount
            unit_price = product.price
            discount_applied = False
            
            if item.quantity >= BULK_DISCOUNT_THRESHOLD:
                discount_applied = True
                unit_price = unit_price * (1 - BULK_DISCOUNT_PERCENT / 100)
            
            item_total = unit_price * item.quantity
            subtotal += item_total
            
            # Create OrderItem object
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "discount_applied": discount_applied
            })
            
        # Calculate shipping fee
        shipping_fee = SHIPPING_FEE if subtotal < FREE_SHIPPING_THRESHOLD else 0.0
        total_amount = subtotal + shipping_fee
        
        # Create order in database
        db_order = model.Order(
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount
        )
        
        # Add order to database
        self.db.add(db_order)
        self.db.flush()  # Get the order ID without committing
        
        # Add order items and update inventory
        for item_data, item_request in zip(order_items, order.items):
            db_item = model.OrderItem(
                order_id=db_order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                discount_applied=item_data["discount_applied"]
            )
            self.db.add(db_item)
            
            # Update product inventory
            product = self.db.query(model.Product).filter(model.Product.id == item_request.product_id).first()
            product.inventory -= item_request.quantity
        
        try:
            self.db.commit()    
            self.db.refresh(db_order)
            
            # Build response
            response = schema.OrderResponse(
                id=db_order.id,
                customer_name=db_order.customer_name,
                customer_email=db_order.customer_email,
                items=[
                    schema.OrderItemResponse(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        discount_applied=item.discount_applied
                    )
                    for item in db_order.items
                ],
                subtotal=db_order.subtotal,
                shipping_fee=db_order.shipping_fee,
                total_amount=db_order.total_amount,
                created_at=db_order.created_at
            )
            
            return response
        
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


    def get_all_orders(self, skip: int = 0, limit: int = 100):
        """Get all orders"""
        orders = self.db.query(model.Order).offset(skip).limit(limit).all()
        return orders


    def get_order(self, order_id: int):
        """Get a specific order by ID"""
        order = self.db.query(model.Order).filter(model.Order.id == order_id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order