from typing import List, Optional
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.menu import MenuCategory, MenuItem
from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuItemCreate,
    MenuItemUpdate,
    AvailabilityUpdate,
)


# ---------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------

async def _get_category(db: AsyncSession, category_id: int) -> Optional[MenuCategory]:
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.id == category_id)
    )
    return result.scalar_one_or_none()


async def _get_item(db: AsyncSession, item_id: int) -> Optional[MenuItem]:
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == item_id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------
# CATEGORY SERVICES
# ---------------------------------------------------------
async def create_category(db: AsyncSession, payload: MenuCategoryCreate) -> MenuCategory:

    # Get max category_number for this restaurant
    result = await db.execute(
        select(func.max(MenuCategory.category_number)).where(
            MenuCategory.restaurant_id == payload.restaurant_id
        )
    )
    last_number = result.scalar() or 0  # If none, start at 0

    next_number = last_number + 1

    category = MenuCategory(
        name=payload.name,
        restaurant_id=payload.restaurant_id,
        category_number=next_number,  # NEW
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def list_categories(db: AsyncSession, restaurant_id: int) -> List[MenuCategory]:
    stmt = select(MenuCategory).where(MenuCategory.restaurant_id == restaurant_id)
    return (await db.execute(stmt)).scalars().all()


async def get_category(db: AsyncSession, category_id: int) -> Optional[MenuCategory]:
    return await _get_category(db, category_id)


async def update_category(db: AsyncSession, category_id: int, payload: MenuCategoryUpdate) -> Optional[MenuCategory]:
    category = await _get_category(db, category_id)
    if not category:
        return None

    if payload.name is not None:
        # Duplicate name prevention
        existing = await db.execute(
            select(MenuCategory).where(
                MenuCategory.restaurant_id == category.restaurant_id,
                func.lower(MenuCategory.name) == func.lower(payload.name),
                MenuCategory.id != category_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Another category with this name exists")

        category.name = payload.name

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error updating category")

    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: int) -> bool:
    category = await _get_category(db, category_id)
    if not category:
        return False

    # Block delete if items exist
    item_count = await db.execute(
        select(func.count(MenuItem.id)).where(MenuItem.category_id == category_id)
    )
    if item_count.scalar() > 0:
        raise HTTPException(400, "Cannot delete category with existing menu items")

    try:
        await db.delete(category)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error deleting category")

    return True


# ---------------------------------------------------------
# MENU ITEM SERVICES
# ---------------------------------------------------------

async def create_item(db: AsyncSession, payload: MenuItemCreate) -> MenuItem:
    # Validate category exists
    category = await _get_category(db, payload.category_id)
    if not category:
        raise HTTPException(404, "Category not found")

    # Duplicate item name prevention
    existing = await db.execute(
        select(MenuItem).where(
            MenuItem.category_id == payload.category_id,
            func.lower(MenuItem.name) == func.lower(payload.name),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Item already exists in this category")

    item = MenuItem(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        food_type=payload.food_type,
        category_id=payload.category_id,
    )
    db.add(item)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error creating item")

    await db.refresh(item)
    return item


async def list_items_by_category(db: AsyncSession, category_id: int) -> List[MenuItem]:
    # Corrected: lookup by category, not food_type
    stmt = select(MenuItem).where(MenuItem.category_id == category_id)
    return (await db.execute(stmt)).scalars().all()


async def get_item(db: AsyncSession, item_id: int) -> Optional[MenuItem]:
    return await _get_item(db, item_id)


async def update_item(db: AsyncSession, item_id: int, payload: MenuItemUpdate) -> Optional[MenuItem]:
    item = await _get_item(db, item_id)
    if not item:
        return None

    # Safe updates
    if payload.name is not None:
        item.name = payload.name

    if payload.description is not None:
        item.description = payload.description

    if payload.price is not None:
        item.price = payload.price

    if payload.food_type is not None:
        item.food_type = payload.food_type

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error updating item")

    await db.refresh(item)
    return item


async def update_item_availability_service(db: AsyncSession, item_id: int, payload: AvailabilityUpdate):
    item = await _get_item(db, item_id)
    if not item:
        raise HTTPException(404, "Menu item not found")

    # Corrected: field must match model
    item.is_available = payload.is_available

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error updating availability")

    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    item = await _get_item(db, item_id)
    if not item:
        return False

    try:
        await db.delete(item)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(500, "Database error deleting item")

    return True
