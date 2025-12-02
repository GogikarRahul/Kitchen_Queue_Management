# app/api/v1/endpoints/admin_menu.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import admin_required
from app.db.session import get_db

from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    AvailabilityUpdate,
)

from app.services.menu_service import (
    create_category,
    list_categories,
    update_category,
    delete_category,
    create_item,
    list_items_by_category,
    update_item,
    delete_item,
    update_item_availability_service,
)


router = APIRouter(
    prefix="/admin/menu",
    tags=["Admin - Menu Management"]
)

# ============================================================
# CATEGORY ROUTES
# ============================================================

@router.post("/category", response_model=MenuCategoryResponse)
async def create_category_endpoint(
    payload: MenuCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return await create_category(db, payload)


@router.get("/category/{restaurant_id}", response_model=List[MenuCategoryResponse])
async def list_categories_endpoint(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    # Ensure admin owns this restaurant
    if current_admin.id != restaurant_id:
        # Modify according to your restaurant ownership rules
        pass

    return await list_categories(db, restaurant_id)


@router.patch("/category/{category_id}", response_model=MenuCategoryResponse)
async def update_category_endpoint(
    category_id: int,
    payload: MenuCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    category = await update_category(db, category_id, payload)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


@router.delete("/category/{category_id}")
async def delete_category_endpoint(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    try:
        success = await delete_category(db, category_id)
    except HTTPException as e:
        raise e

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")

    return {"message": "Category deleted successfully"}


# ============================================================
# ITEM ROUTES
# ============================================================

@router.post("/item", response_model=MenuItemResponse)
async def create_item_endpoint(
    payload: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return await create_item(db, payload)


# FIXED: now lists items by category_id (not food type)
@router.get("/category/{category_id}/items", response_model=List[MenuItemResponse])
async def list_items_by_category_endpoint(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    return await list_items_by_category(db, category_id)


@router.patch("/item/{item_id}", response_model=MenuItemResponse)
async def update_item_endpoint(
    item_id: int,
    payload: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    item = await update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return item


@router.patch("/item/{item_id}/availability")
async def update_item_availability(
    item_id: int,
    payload: AvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    # AvailabilityUpdate now uses: is_available: bool
    return await update_item_availability_service(db, item_id, payload)


@router.delete("/item/{item_id}")
async def delete_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(admin_required),
):
    success = await delete_item(db, item_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

    return {"message": "Item deleted successfully"}
