import random
from ..models.model import Product
from src.db.database import engine, SessionLocal, Base

# Sample product data
PRODUCTS = [
    {
        "name": "Laptop",
        "description": "High-performance laptop with 16GB RAM and 512GB SSD",
        "price": 1299.99,
        "inventory": 25
    },
    {
        "name": "Smartphone",
        "description": "Latest smartphone with 128GB storage and 48MP camera",
        "price": 799.99,
        "inventory": 50
    },
    {
        "name": "Wireless Headphones",
        "description": "Noise-cancelling wireless headphones with 30-hour battery life",
        "price": 249.99,
        "inventory": 100
    },
    {
        "name": "Tablet",
        "description": "10-inch tablet with 64GB storage and HD display",
        "price": 399.99,
        "inventory": 35
    },
    {
        "name": "Smart Watch",
        "description": "Fitness tracker with heart rate monitor and GPS",
        "price": 199.99,
        "inventory": 70
    },
    {
        "name": "Bluetooth Speaker",
        "description": "Portable waterproof bluetooth speaker",
        "price": 89.99,
        "inventory": 120
    },
    {
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with long battery life",
        "price": 49.99,
        "inventory": 150
    },
    {
        "name": "USB-C Cable",
        "description": "6ft braided USB-C charging cable",
        "price": 15.99,
        "inventory": 200
    },
    {
        "name": "External Hard Drive",
        "description": "2TB USB 3.0 external hard drive",
        "price": 79.99,
        "inventory": 60
    },
    {
        "name": "Wireless Charger",
        "description": "Fast wireless charging pad compatible with all Qi devices",
        "price": 29.99,
        "inventory": 90
    }
]

def seed_database():
    """Seed the database with initial product data"""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Check if we already have products in the database
        existing_products = db.query(Product).count()
        
        if existing_products > 0:
            print(f"Database already contains {existing_products} products. Skipping seeding.")
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
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()