from fastapi import APIRouter
from .routes.order_routes import order_router
from .routes.product_routes import product_router

router = APIRouter()

router.include_router(router=order_router, prefix='/orders')
router.include_router(router=product_router, prefix='/products')
