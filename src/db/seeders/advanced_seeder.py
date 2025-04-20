# advanced_seeder.py
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.db.database import engine, SessionLocal, Base
from src.db.models.model import Product, Order, OrderItem

# Import the products from the basic seeder
from src.db.seeders.seeder import PRODUCTS

# Sample customer data
CUSTOMERS = [
    {"name": "John Smith", "email": "john.smith@example.com"},
    {"name": "Emma Johnson", "email": "emma.johnson@example.com"},
    {"name": "Michael Brown", "email": "michael.brown@example.com"},
    {"name": "Sophia Williams", "email": "sophia.williams@example.com"},
    {"name": "William Davis", "email": "william.davis@example.com"},
    {"name": "Olivia Miller", "email": "olivia.miller@example.com"},
    {"name": "James Wilson", "email": "james.wilson@example.com"},
    {"name": "Ava Moore", "email": "ava.moore@example.com"},
    {"name": "Alexander Taylor", "email": "alex.taylor@example.com"},
    {"name": "Isabella Anderson", "email": "isabella.anderson@example.com"}
]

# Constants for business logic (same as in main.py)
BULK_DISCOUNT_THRESHOLD = 5  # Quantity threshold for bulk discount
BULK_DISCOUNT_PERCENT = 10  # 10% discount for bulk orders
SHIPPING_FEE = 5.0  # $5 shipping fee
FREE_SHIPPING_THRESHOLD = 50.0  # Free shipping for orders over $50

def seed_products(db: Session):
    """Seed the database with product data"""
    # Check if we already have products in the database
    existing_products = db.query(Product).count()
    
    if existing_products > 0:
        print(f"Database already contains {existing_products} products. Skipping product seeding.")
        return
    
    # Add products to the database
    for product_data in PRODUCTS:
        # Add some random variation to inventory for more realistic data
        inventory_variation = random.randint(-5, 10)
        product_data["inventory"] = max(1, product_data["inventory"] + inventory_variation)
        
        # Create and add the product
        product = Product(**product_data)
        db.add(product)
    
    # Commit the changes
    db.commit()
    print(f"Successfully seeded database with {len(PRODUCTS)} products.")

def seed_orders(db: Session, num_orders=20):
    """Seed the database with random orders"""
    # Check if we already have orders in the database
    existing_orders = db.query(Order).count()
    
    if existing_orders > 0:
        print(f"Database already contains {existing_orders} orders. Skipping order seeding.")
        return
    
    # Get all products from the database
    products = db.query(Product).all()
    
    if not products:
        print("No products found in database. Please run seed_products first.")
        return
    
    # Create random orders
    for _ in range(num_orders):
        # Select a random customer
        customer = random.choice(CUSTOMERS)
        
        # Determine number of items in this order (1-4)
        num_items = random.randint(1, 4)
        
        # Randomly select products for this order (no duplicates)
        order_products = random.sample(products, num_items)
        
        # Calculate order details
        order_items = []
        subtotal = 0.0
        
        for product in order_products:
            # Determine quantity (1-8)
            quantity = random.randint(1, 8)
            
            # Calculate price with potential bulk discount
            unit_price = product.price
            discount_applied = False
            
            if quantity >= BULK_DISCOUNT_THRESHOLD:
                discount_applied = True
                unit_price = unit_price * (1 - BULK_DISCOUNT_PERCENT / 100)
            
            item_total = unit_price * quantity
            subtotal += item_total
            
            # Track item details for later
            order_items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_applied": discount_applied
            })
        
        # Calculate shipping fee
        shipping_fee = SHIPPING_FEE if subtotal < FREE_SHIPPING_THRESHOLD else 0.0
        total_amount = subtotal + shipping_fee
        
        # Create a random order date within the last 30 days
        days_ago = random.randint(0, 30)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Create order
        db_order = Order(
            customer_name=customer["name"],
            customer_email=customer["email"],
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            created_at=order_date
        )
        
        db.add(db_order)
        db.flush()  # Get the order ID without committing
        
        # Add order items and update inventory
        for item in order_items:
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=item["product"].id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                discount_applied=item["discount_applied"]
            )
            db.add(db_item)
            
            # Update product inventory
            item["product"].inventory -= item["quantity"]
    
    # Commit all changes
    db.commit()
    print(f"Successfully seeded database with {num_orders} orders.")

def seed_database(num_orders=20):
    """Seed the entire database with products and orders"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Seed products first
        # seed_products(db)
        
        # Then seed orders
        seed_orders(db, num_orders)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()