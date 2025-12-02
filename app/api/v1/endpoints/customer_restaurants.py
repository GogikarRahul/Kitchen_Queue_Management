# app/api/v1/endpoints/customer_restaurants.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.restaurant import Restaurant
from app.models.menu import MenuCategory, MenuItem

from app.schemas.restaurant import RestaurantResponse
from app.schemas.menu import (
    MenuCategoryResponse,
    MenuItemResponse,
    MenuItemWithRestaurant
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
# GET RESTAURANTS BY PARTIAL NAME
# ============================================================
@router.get("/{restaurant_name}", response_model=List[RestaurantResponse])
async def get_restaurant(restaurant_name: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Restaurant).where(Restaurant.name.ilike(f"%{restaurant_name}%"))
    result = await db.execute(stmt)
    restaurants = result.scalars().all()

    if not restaurants:
        raise HTTPException(
            status_code=404,
            detail="No matching restaurants found"
        )

    return restaurants


# ============================================================
# MENU CATEGORIES FOR RESTAURANT
# ============================================================

@router.get("/name/{restaurant_name}/menu/categories", response_model=list[MenuCategoryResponse])
async def get_categories_by_name(restaurant_name: str, db: AsyncSession = Depends(get_db)):
    
    # 1. Fetch restaurant by name (partial search allowed)
    rest_stmt = select(Restaurant).where(Restaurant.name.ilike(f"%{restaurant_name}%"))
    rest = await db.execute(rest_stmt)
    restaurant = rest.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    if not restaurant.is_open:
        raise HTTPException(400, "Restaurant is currently closed")

    # 2. Fetch categories for the restaurant
    stmt = select(MenuCategory).where(MenuCategory.restaurant_id == restaurant.id)
    result = await db.execute(stmt)

    return result.scalars().all()

#----------------------------------------------------------------------------------------
 #fetch restaurants by category
#----------------------------------------------------------------------------------------
@router.get("/menu/category/{category_name}", response_model=list[RestaurantResponse])
async def get_restaurants_by_category(category_name: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Restaurant)
        .join(MenuCategory, MenuCategory.restaurant_id == Restaurant.id)
        .where(MenuCategory.name.ilike(f"%{category_name}%"))
    )
    
    result = await db.execute(stmt)
    restaurants = result.scalars().all()

    if not restaurants:
        raise HTTPException(404, "No restaurants found for this category")

    return restaurants

@router.get("/name/{restaurant_name}/menu/items", response_model=list[MenuItemResponse])
async def get_items_by_name(restaurant_name: str, db: AsyncSession = Depends(get_db)):

    # 1. Fetch restaurant by name (case-insensitive, partial match)
    rest_stmt = select(Restaurant).where(Restaurant.name.ilike(f"%{restaurant_name}%"))
    rest = await db.execute(rest_stmt)
    restaurant = rest.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(404, "Restaurant not found")

    if not restaurant.is_open:
        raise HTTPException(400, "Restaurant is currently closed")

    # 2. Fetch all items belonging to this restaurant via category join
    stmt = (
        select(MenuItem)
        .join(MenuCategory, MenuCategory.id == MenuItem.category_id)
        .where(MenuCategory.restaurant_id == restaurant.id)
        .distinct()
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/search/items/{keyword}", response_model=list[MenuItemWithRestaurant])
async def search_items(keyword: str, db: AsyncSession = Depends(get_db)):

    stmt = (
        select(
            MenuItem.id,
            MenuItem.name,
            MenuItem.price,
            MenuItem.description,
            Restaurant.name.label("restaurant_name"),
            Restaurant.address.label("restaurant_location"),   # update field name
        )
        .join(MenuCategory, MenuCategory.id == MenuItem.category_id)
        .join(Restaurant, Restaurant.id == MenuCategory.restaurant_id)
        .where(MenuItem.name.ilike(f"%{keyword}%"))
    )

    result = await db.execute(stmt)
    items = result.all()

    if not items:
        raise HTTPException(404, "No items found for this search")

    return [
        MenuItemWithRestaurant(
            id=i.id,
            name=i.name,
            price=i.price,
            description=i.description,
            restaurant_name=i.restaurant_name,
            restaurant_location=i.restaurant_location,
        )
        for i in items
    ]
    
    
    
# ---------------------------------------------------------------------------
@router.get("/search/{keyword}")
async def universal_search(keyword: str, db: AsyncSession = Depends(get_db)):

    # ====================================================
    # 1️⃣ SEARCH RESTAURANTS BY NAME
    # ====================================================
    rest_stmt = (
        select(Restaurant)
        .where(Restaurant.name.ilike(f"%{keyword}%"))
    )
    rest_result = await db.execute(rest_stmt)
    restaurants = rest_result.scalars().all()

    if restaurants:
        return {
            "type": "restaurants",
            "data": [
                {
                    "id": r.id,
                    "name": r.name,
                    "location": r.address,
                    "is_open": r.is_open
                }
                for r in restaurants
            ]
        }

    # ====================================================
    # 2️⃣ SEARCH CATEGORIES (ONLY IF RESTAURANTS NOT FOUND)
    # ====================================================
    cat_stmt = (
        select(
            MenuCategory.id,
            MenuCategory.name.label("category_name"),
            Restaurant.id.label("restaurant_id"),
            Restaurant.name.label("restaurant_name"),
            Restaurant.address.label("restaurant_location")
        )
        .join(Restaurant, Restaurant.id == MenuCategory.restaurant_id)
        .where(MenuCategory.name.ilike(f"%{keyword}%"))
    )

    cat_result = await db.execute(cat_stmt)
    categories = cat_result.all()

    if categories:
        return {
            "type": "categories",
            "data": [
                {
                    "category_id": c.id,
                    "category_name": c.category_name,
                    "restaurant_id": c.restaurant_id,
                    "restaurant_name": c.restaurant_name,
                    "restaurant_location": c.restaurant_location
                }
                for c in categories
            ]
        }

    # ====================================================
    # 3️⃣ SEARCH MENU ITEMS (ONLY IF NO REST + CATEGORY)
    # ====================================================
    item_stmt = (
        select(
            MenuItem.id,
            MenuItem.name,
            MenuItem.price,
            MenuItem.description,
            MenuCategory.name.label("category_name"),
            Restaurant.name.label("restaurant_name"),
            Restaurant.address.label("restaurant_location")
        )
        .join(MenuCategory, MenuCategory.id == MenuItem.category_id)
        .join(Restaurant, Restaurant.id == MenuCategory.restaurant_id)
        .where(MenuItem.name.ilike(f"%{keyword}%"))
    )

    item_result = await db.execute(item_stmt)
    items = item_result.all()

    if items:
        return {
            "type": "items",
            "data": [
                {
                    "item_id": i.id,
                    "item_name": i.name,
                    "price": i.price,
                    "description": i.description,
                    "category_name": i.category_name,
                    "restaurant_name": i.restaurant_name,
                    "restaurant_location": i.restaurant_location
                }
                for i in items
            ]
        }

    # ====================================================
    # If nothing matches
    # ====================================================
    raise HTTPException(404, "No results found")
