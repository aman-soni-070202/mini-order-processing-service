from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from main import app
from src.db.database import Base, get_db
from src.db.models.model import Product

import dotenv
import os
dotenv.load_dotenv()

# Create a test database with PostgreSQL
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URL")
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
        Product(name="Luxury Item", description="Very expensive item", price=100.00, inventory=5),
        Product(name="Bulk Item", description="Item often sold in bulk", price=2.50, inventory=200),
    ]
    db.add_all(products)
    db.commit()
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


# Root endpoint tests
def test_read_root(setup_test_db):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mini Order Processing Service"}


# Product endpoint tests
def test_get_products(setup_test_db):
    response = client.get("/products/get_all_products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 5
    assert products[0]["name"] == "Test Product 1"
    assert products[1]["name"] == "Test Product 2"


def test_get_products_with_pagination(setup_test_db):
    # Test skip parameter
    response = client.get("/products/get_all_products?skip=2")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 3  # 5 total - 2 skipped
    assert products[0]["name"] == "Test Product 3"
    
    # Test limit parameter
    response = client.get("/products/get_all_products?limit=2")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    
    # Test both skip and limit
    response = client.get("/products/get_all_products?skip=1&limit=2")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 2
    assert products[0]["name"] == "Test Product 2"
    assert products[1]["name"] == "Test Product 3"


def test_get_product(setup_test_db):
    # Get existing product
    response = client.get("/products/get_product/1")
    assert response.status_code == 200
    product = response.json()
    assert product["name"] == "Test Product 1"
    assert product["price"] == 10.0
    assert product["inventory"] == 20
    
    # Try to get non-existent product
    response = client.get("/products/get_product/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product(setup_test_db):
    # Create new product with valid data
    product_data = {
        "name": "New Product",
        "description": "New product description",
        "price": 15.99,
        "inventory": 25
    }
    response = client.post("/products/add_product", json=product_data)
    assert response.status_code == 201
    product = response.json()
    assert product["name"] == "New Product"
    assert product["price"] == 15.99
    assert product["inventory"] == 25
    
    # Verify product was added to database
    response = client.get("/products/get_all_products")
    assert len(response.json()) == 6
    
    # Test invalid product data
    invalid_product = {
        "name": "Invalid Product",
        "description": "Missing price and inventory"
    }
    response = client.post("/products/add_product", json=invalid_product)
    assert response.status_code == 422  # Validation error
    
    # Test negative price
    invalid_product = {
        "name": "Invalid Product",
        "description": "Negative price",
        "price": -10.0,
        "inventory": 5
    }
    response = client.post("/products/add_product", json=invalid_product)
    assert response.status_code == 422  # Validation error
    
    # Test negative inventory
    invalid_product = {
        "name": "Invalid Product",
        "description": "Negative inventory",
        "price": 10.0,
        "inventory": -5
    }
    response = client.post("/products/add_product", json=invalid_product)
    assert response.status_code == 422  # Validation error


# Inventory update endpoint tests
def test_update_inventory_add(setup_test_db):
    """Test adding inventory to a product"""
    # First, get current inventory
    response = client.get("/products/get_product/1")
    assert response.status_code == 200
    initial_inventory = response.json()["inventory"]
    
    # Add 10 to inventory
    update_data = {"quantity": 10}
    response = client.patch("/products/update_product_inventory/1", json=update_data)
    
    # Check response
    assert response.status_code == 200
    assert response.json()["inventory"] == initial_inventory + 10
    
    # Verify the update persisted
    response = client.get("/products/get_product/1")
    assert response.json()["inventory"] == initial_inventory + 10


def test_update_inventory_remove(setup_test_db):
    """Test removing inventory from a product"""
    # First, get current inventory
    response = client.get("/products/get_product/1")
    assert response.status_code == 200
    initial_inventory = response.json()["inventory"]
    
    # Remove 5 from inventory
    update_data = {"quantity": -5}
    response = client.patch("/products/update_product_inventory/1", json=update_data)
    
    # Check response
    assert response.status_code == 200
    assert response.json()["inventory"] == initial_inventory - 5
    
    # Verify the update persisted
    response = client.get("/products/get_product/1")
    assert response.json()["inventory"] == initial_inventory - 5


def test_update_inventory_invalid(setup_test_db):
    """Test removing more inventory than available"""
    # First, get current inventory
    response = client.get("/products/get_product/1")
    assert response.status_code == 200
    initial_inventory = response.json()["inventory"]
    
    # Try to remove more than available
    update_data = {"quantity": -(initial_inventory + 10)}
    response = client.patch("/products/update_product_inventory/1", json=update_data)
    
    # Check error response
    assert response.status_code == 400
    assert "Cannot reduce inventory below zero" in response.json()["detail"]
    
    # Verify inventory wasn't changed
    response = client.get("/products/get_product/1")
    assert response.json()["inventory"] == initial_inventory


def test_update_inventory_nonexistent_product(setup_test_db):
    """Test updating inventory for a product that doesn't exist"""
    update_data = {"quantity": 10}
    response = client.patch("/products/update_product_inventory/999", json=update_data)
    
    # Check error response
    assert response.status_code == 404
    assert "Product not found" in response.json()["detail"]


def test_update_inventory_validation(setup_test_db):
    """Test inventory update validation"""
    # Missing quantity field
    update_data = {}
    response = client.patch("/products/update_product_inventory/1", json=update_data)
    assert response.status_code == 422  # Validation error


# Order endpoint tests
def test_create_order_no_discount_with_shipping(setup_test_db):
    """Test creating an order with no discount and shipping fee applied"""
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 3, "quantity": 3}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 201
    data = response.json()
    
    # Calculate expected values
    expected_subtotal = (2 * 10.0) + (3 * 5.0)  # 2 of product 1 at $10 + 3 of product 3 at $5
    expected_shipping_fee = 5.0  # Order is under $50
    expected_total = expected_subtotal + expected_shipping_fee
    
    assert data["subtotal"] == expected_subtotal
    assert data["shipping_fee"] == expected_shipping_fee
    assert data["total_amount"] == expected_total
    assert len(data["items"]) == 2
    assert not any(item["discount_applied"] for item in data["items"])
    
    # Check inventory was updated
    response = client.get("/products/get_product/1")
    assert response.json()["inventory"] == 18  # 20 - 2
    
    response = client.get("/products/get_product/3")
    assert response.json()["inventory"] == 47  # 50 - 3


def test_create_order_with_bulk_discount_no_shipping(setup_test_db):
    """Test creating an order with bulk discount and no shipping fee"""
    order_data = {
        "customer_name": "Jane Smith",
        "customer_email": "jane@example.com",
        "items": [
            {"product_id": 1, "quantity": 6},  # Should qualify for bulk discount
            {"product_id": 2, "quantity": 1}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
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
    
    # Verify inventory updates
    response = client.get("/products/get_product/1")
    assert response.json()["inventory"] == 14  # 20 - 6
    
    response = client.get("/products/get_product/2")
    assert response.json()["inventory"] == 14  # 15 - 1


def test_create_order_expensive_item_no_shipping(setup_test_db):
    """Test order with expensive item that automatically crosses free shipping threshold"""
    order_data = {
        "customer_name": "Rich Customer",
        "customer_email": "rich@example.com",
        "items": [
            {"product_id": 4, "quantity": 1}  # Luxury item at $100
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 201
    data = response.json()
    
    assert data["subtotal"] == 100.0
    assert data["shipping_fee"] == 0.0  # No shipping fee as order > $50
    assert data["total_amount"] == 100.0


def test_create_order_bulk_item_with_discount(setup_test_db):
    """Test order with bulk items at discount"""
    order_data = {
        "customer_name": "Bulk Buyer",
        "customer_email": "bulk@example.com",
        "items": [
            {"product_id": 5, "quantity": 30}  # 30 bulk items at $2.50 each
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 201
    data = response.json()
    
    # 30 items at $2.50 each with 10% discount
    expected_subtotal = 30 * 2.50 * 0.9
    assert round(data["subtotal"], 2) == round(expected_subtotal, 2)
    assert data["shipping_fee"] == 0.0  # No shipping fee as order > $50
    assert round(data["total_amount"], 2) == round(expected_subtotal, 2)
    assert data["items"][0]["discount_applied"]


def test_create_order_insufficient_inventory(setup_test_db):
    """Test order with insufficient inventory"""
    order_data = {
        "customer_name": "Invalid Customer",
        "customer_email": "invalid@example.com",
        "items": [
            {"product_id": 2, "quantity": 20}  # Product 2 only has 15 in inventory
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 400
    assert "Not enough inventory" in response.json()["detail"]
    
    # Verify inventory wasn't changed
    response = client.get("/products/get_product/2")
    assert response.json()["inventory"] == 15  # Still 15


def test_create_order_nonexistent_product(setup_test_db):
    """Test order with nonexistent product"""
    order_data = {
        "customer_name": "Invalid Customer",
        "customer_email": "invalid@example.com",
        "items": [
            {"product_id": 999, "quantity": 1}  # Product doesn't exist
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_order_validation(setup_test_db):
    """Test order input validation"""
    # Invalid email
    order_data = {
        "customer_name": "Invalid Customer",
        "customer_email": "not-an-email",
        "items": [
            {"product_id": 1, "quantity": 1}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 422  # Validation error
    
    # Missing customer name
    order_data = {
        "customer_email": "valid@example.com",
        "items": [
            {"product_id": 1, "quantity": 1}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 422  # Validation error
    
    # Zero quantity
    order_data = {
        "customer_name": "Valid Customer",
        "customer_email": "valid@example.com",
        "items": [
            {"product_id": 1, "quantity": 0}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 422  # Validation error
    
    # Negative quantity
    order_data = {
        "customer_name": "Valid Customer",
        "customer_email": "valid@example.com",
        "items": [
            {"product_id": 1, "quantity": -1}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 422  # Validation error


def test_get_orders(setup_test_db):
    """Test getting all orders"""
    # First, create some orders
    order_data_1 = {
        "customer_name": "Customer One",
        "customer_email": "one@example.com",
        "items": [{"product_id": 1, "quantity": 1}]
    }
    order_data_2 = {
        "customer_name": "Customer Two",
        "customer_email": "two@example.com",
        "items": [{"product_id": 2, "quantity": 2}]
    }
    
    client.post("/orders/add_order", json=order_data_1)
    client.post("/orders/add_order", json=order_data_2)
    
    # Now get all orders
    response = client.get("/orders/get_all_orders")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 2
    assert orders[0]["customer_name"] == "Customer One"
    assert orders[1]["customer_name"] == "Customer Two"
    
    # Test pagination
    response = client.get("/orders/get_all_orders?skip=1")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["customer_name"] == "Customer Two"
    
    response = client.get("/orders/get_all_orders?limit=1")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["customer_name"] == "Customer One"


def test_get_order(setup_test_db):
    """Test getting a specific order"""
    # First, create an order
    order_data = {
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "items": [
            {"product_id": 1, "quantity": 3},
            {"product_id": 2, "quantity": 2}
        ]
    }
    response = client.post("/orders/add_order", json=order_data)
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Now get the order
    response = client.get(f"/orders/get_order/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["customer_name"] == "Test Customer"
    assert order["customer_email"] == "test@example.com"
    assert len(order["items"]) == 2
    
    # Try to get non-existent order
    response = client.get("/orders/get_order/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
