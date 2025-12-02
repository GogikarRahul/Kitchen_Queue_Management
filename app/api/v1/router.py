from fastapi import APIRouter

from app.api.v1.endpoints.admin_auth import router as admin_auth_router
from app.api.v1.endpoints.admin_restaurants import router as admin_restaurants_router
from app.api.v1.endpoints.admin_menu import router as admin_menu_router
# from app.api.v1.endpoints.admin_chefs import router as admin_chefs_router
from app.api.v1.endpoints.customer_restaurants import router as customer_restaurants_router
from app.api.v1.endpoints.customer_orders import router as customer_orders_router
from app.api.v1.endpoints.chef_orders import router as chef_orders_router
from app.api.v1.endpoints.chef_analytics import router as chef_analytics_router
# from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.websocket_endpoints import router as websocket_router

router = APIRouter()

router.include_router(admin_auth_router)
router.include_router(admin_restaurants_router)
# router.include_router(admin_chefs_router)
router.include_router(admin_menu_router)
router.include_router(customer_restaurants_router)
router.include_router(customer_orders_router)
router.include_router(chef_orders_router)
router.include_router(chef_analytics_router)
# router.include_router(reports_router)
router.include_router(notifications_router)
router.include_router(websocket_router)


# from fastapi import APIRouter

# router = APIRouter()

# def safe_include(import_path, name):
#     try:
#         module = __import__(import_path, fromlist=["router"])
#         router.include_router(module.router)
#         print(f"LOADED: {name}")
#     except Exception as e:
#         print(f"❌ ERROR in {name}: {e}")


# safe_include("app.api.v1.endpoints.admin_auth", "admin_auth")
# safe_include("app.api.v1.endpoints.admin_restaurants", "admin_restaurants")
# safe_include("app.api.v1.endpoints.admin_menu", "admin_menu")
# safe_include("app.api.v1.endpoints.admin_chefs", "admin_chefs")
# safe_include("app.api.v1.endpoints.customer_restaurants", "customer_restaurants")
# safe_include("app.api.v1.endpoints.customer_orders", "customer_orders")
# safe_include("app.api.v1.endpoints.chef_orders", "chef_orders")
# safe_include("app.api.v1.endpoints.chef_analytics", "chef_analytics")
# safe_include("app.api.v1.endpoints.reports", "reports")
# safe_include("app.api.v1.endpoints.notifications", "notifications")
# safe_include("app.api.v1.endpoints.websocket_endpoints", "websocket_endpoints")
