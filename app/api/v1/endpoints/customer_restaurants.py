# app/api/v1/endpoints/customer_restaurants.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.restaurant import Restaurant
from app.models.menu import MenuCategory, MenuItem

from app.schemas.restaurant import RestaurantResponse
from app.schemas.menu import (
    MenuCategoryResponse,
    MenuItemResponse
)

router = APIRouter(
    prefix="/customer/restaurants",
    tags=["Customer - Restaurants"],
)


# ============================================================
# LIST ALL OPEN RESTAURANTS
# ============================================================

@router.get("/", response_model=list[RestaurantResponse])
async def list_restaurants(db: AsyncSession = Depends(get_db)):
    stmt = select(Restaurant).where(Restaurant.is_open == True)
    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================
# GET SINGLE RESTAURANT DETAILS
# ============================================================

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await db.execute(stmt)
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return restaurant


# ============================================================
# MENU CATEGORIES FOR RESTAURANT
# ============================================================

@router.get("/{restaurant_id}/menu/categories", response_model=list[MenuCategoryResponse])
async def get_categories(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    # Validate restaurant exists and is open
    rest_stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    rest = await db.execute(rest_stmt)
    restaurant = rest.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    if not restaurant.is_open:
        raise HTTPException(400, "Restaurant is currently closed")

    stmt = select(MenuCategory).where(MenuCategory.restaurant_id == restaurant_id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================
# MENU ITEMS FOR RESTAURANT
# ============================================================

@router.get("/{restaurant_id}/menu/items", response_model=list[MenuItemResponse])
async def get_items(restaurant_id: int, db: AsyncSession = Depends(get_db)):
    # Validate restaurant exists and is open
    rest_stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    rest = await db.execute(rest_stmt)
    restaurant = rest.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    if not restaurant.is_open:
        raise HTTPException(400, "Restaurant is currently closed")

    # Get all items belonging to restaurant categories
    stmt = (
        select(MenuItem)
        .join(MenuCategory)
        .where(MenuCategory.restaurant_id == restaurant_id)
        .distinct()  # avoid duplicates if join blows
    )

    result = await db.execute(stmt)
    return result.scalars().all()
