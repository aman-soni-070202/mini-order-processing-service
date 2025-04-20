# Mini Order Processing Service

A FastAPI application that processes customer orders, applies discount rules, calculates shipping fees, and manages product inventory. This application uses PostgreSQL as the database backend.

## Features

- Product management
- Order processing with the following business rules:
  - Bulk discount (10%) for product quantities ≥ 5
  - Shipping fee ($5) for orders under $50
  - Inventory validation and atomic updates
- Input validation with Pydantic models
- PostgreSQL database storage with SQLAlchemy ORM
- Comprehensive test suite

## Prerequisites

- Python 3.8+
- PostgreSQL installation
- Access to create databases in PostgreSQL

## Database Setup

1. Create the main and test databases in PostgreSQL:

```sql
CREATE DATABASE order_processing;
CREATE DATABASE order_processing_test;
```

2. Ensure your PostgreSQL credentials are correctly set in `database.py` (and `test_main.py` for tests).

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. First time setup: Create the tables by running:
   ```
   python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
   ```

2. Start the application:
   ```
   uvicorn main:app --reload
   ```

The API will be available at http://localhost:8000

## API Documentation

FastAPI automatically generates API documentation. Access it at:
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

## API Endpoints

### Products

- `GET /products/` - Get all products
- `GET /products/{product_id}` - Get a specific product
- `POST /products/` - Create a new product
- `PATCH /products/{product_id}/inventory` - Update product inventory levels

### Orders

- `GET /orders/` - Get all orders
- `GET /orders/{order_id}` - Get a specific order
- `POST /orders/` - Create a new order

## Database Schema

- **Products**: id, name, description, price, inventory
- **Orders**: id, customer_name, customer_email, subtotal, shipping_fee, total_amount, created_at
- **OrderItems**: id, order_id, product_id, quantity, unit_price, discount_applied

## Testing

Run the test suite with:

```
pytest
```

Note: The test suite will create and destroy tables in the `order_processing_test` database.

## Example Usage

### Create a Product

```bash
curl -X 'POST' \
  'http://localhost:8000/products/' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Sample Product",
  "description": "A sample product description",
  "price": 19.99,
  "inventory": 100
}'
```

### Create an Order

```bash
curl -X 'POST' \
  'http://localhost:8000/orders/' \
  -H 'Content-Type: application/json' \
  -d '{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "items": [
    {
      "product_id": 1,
      "quantity": 3
    },
    {
      "product_id": 2,
      "quantity": 6
    }
  ]
}'
```

## Update Product Inventory

### Add inventory (increase by 15):

```bash
curl -X 'PATCH' \
  'http://localhost:8000/products/1/inventory' \
  -H 'Content-Type: application/json' \
  -d '{
  "quantity": 15
}'
```

### Remove inventory (decrease by 5):

```bash
curl -X 'PATCH' \
  'http://localhost:8000/products/1/inventory' \
  -H 'Content-Type: application/json' \
  -d '{
  "quantity": -5
}'
```