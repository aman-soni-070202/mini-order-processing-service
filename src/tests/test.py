# test_main.py
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from main import app
from src.db.database import Base, get_db
from src.db.models import Product

# Create a test database with PostgreSQL
# Use a dedicated test database to avoid interfering with production data
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/order_processing_test"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_test_db():
    # Drop all tables to ensure clean state
    Base.metadata.drop_all(bind=engine)
    
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    products = [
        Product(name="Test Product 1", description="Description 1", price=10.00, inventory=20),
        Product(name="Test Product 2", description="Description 2", price=20.00, inventory=15),
        Product(name="Test Product 3", description="Description 3", price=5.00, inventory=50),
    ]
    db.add_all(products)
    db.commit()
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


# The rest of the test file remains the same...
def test_read_root(setup_test_db):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mini Order Processing Service"}


def test_get_products(setup_test_db):
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_product(setup_test_db):
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product 1"


def test_create_product(setup_test_db):
    product_data = {
        "name": "New Product",
        "description": "New product description",
        "price": 15.99,
        "inventory": 25
    }
    response = client.post("/products/", json=product_data)
    assert response.status_code == 201
    assert response.json()["name"] == "New Product"


def test_create_order_no_discount_with_shipping(setup_test_db):
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 3}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 201
    data = response.json()
    
    # Calculate expected values
    expected_subtotal = (2 * 10.0) + (3 * 5.0) # 2 of product 1 at $10 + 3 of product 3 at $5
    expected_shipping_fee = 5.0  # Order is under $50
    expected_total = expected_subtotal + expected_shipping_fee
    
    assert data["subtotal"] == expected_subtotal
    assert data["shipping_fee"] == expected_shipping_fee
    assert data["total_amount"] == expected_total
    assert len(data["items"]) == 2
    assert not any(item["discount_applied"] for item in data["items"])
    
    # Check inventory was updated
    response = client.get("/products/1")
    assert response.json()["inventory"] == 18  # 20 - 2
    
    response = client.get("/products/3")
    assert response.json()["inventory"] == 47  # 50 - 3


def test_create_order_with_bulk_discount_no_shipping(setup_test_db):
    order_data = {
        "customer_name": "Jane Smith",
        "customer_email": "jane@example.com",
        "items": [
            {"product_id": 1, "quantity": 6},  # Should qualify for bulk discount
            {"product_id": 2, "quantity": 1}
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 201
    data = response.json()
    
    # Product 1: 6 items at $10 each with 10% discount = 6 * $10 * 0.9 = $54
    # Product 2: 1 item at $20 = $20
    # Total: $74
    # No shipping fee as total > $50
    expected_subtotal = (6 * 10.0 * 0.9) + (1 * 20.0)
    expected_shipping_fee = 0.0  # Order is over $50
    expected_total = expected_subtotal + expected_shipping_fee
    
    assert round(data["subtotal"], 2) == round(expected_subtotal, 2)
    assert data["shipping_fee"] == expected_shipping_fee
    assert round(data["total_amount"], 2) == round(expected_total, 2)
    
    # First item should have discount applied
    assert data["items"][0]["discount_applied"]
    assert not data["items"][1]["discount_applied"]


def test_create_order_insufficient_inventory(setup_test_db):
    order_data = {
        "customer_name": "Invalid Customer",
        "customer_email": "invalid@example.com",
        "items": [
            {"product_id": 2, "quantity": 20}  # Product 2 only has 15 in inventory
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 400
    assert "Not enough inventory" in response.json()["detail"]
    
    # Verify inventory wasn't changed
    response = client.get("/products/2")
    assert response.json()["inventory"] == 15  # Still 15


def test_create_order_nonexistent_product(setup_test_db):
    order_data = {
        "customer_name": "Invalid Customer",
        "customer_email": "invalid@example.com",
        "items": [
            {"product_id": 999, "quantity": 1}  # Product doesn't exist
        ]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]