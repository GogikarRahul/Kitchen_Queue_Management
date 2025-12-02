from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import BackgroundTasks
from app.api.deps import customer_required
from app.db.session import get_db

from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import (
    create_customer_order,
    list_customer_orders,
    get_customer_order,
)

router = APIRouter(
    prefix="/customer/orders",
    tags=["Customer - Orders"],
)


# ============================
# 🛒 PLACE ORDER
# ============================



@router.post("/", response_model=OrderResponse)
async def place_order(
    payload: OrderCreate,
    background_tasks: BackgroundTasks,   # ⬅️ ADD THIS
    db: AsyncSession = Depends(get_db),
    current_customer=Depends(customer_required),
):
    order, error = await create_customer_order(
        db,
        payload,
        current_customer,
        background_tasks   # ⬅️ PASS IT
    )

    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=error)

    return order


# ============================
# 📜 LIST ORDERS  (FIXED PATH)
# ============================

@router.get("/", response_model=List[OrderResponse])
async def get_my_orders_root(
    db: AsyncSession = Depends(get_db),
    current_customer=Depends(customer_required),
):
    return await list_customer_orders(db, current_customer.name)

# ============================
# 🔎 GET SINGLE ORDER (INT ONLY)
# ============================

@router.get("/{order_id:int}", response_model=OrderResponse)
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_customer=Depends(customer_required),
):
    order = await get_customer_order(db, current_customer.name, order_id)

    if not order:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return order


# ============================
# 🔄 GET STATUS ONLY (INT ONLY)
# ============================

@router.get("/{order_id:int}/status")
async def get_order_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_customer=Depends(customer_required),
):
    order = await get_customer_order(db, current_customer.name, order_id)

    if not order:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return {"order_id": order.id, "status": order.status}

# ============================
# ❌ CANCEL ORDER (Customer)
# ============================
@router.post("/{order_id:int}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_customer=Depends(customer_required),
):
    from app.services.order_service import cancel_order_by_customer

    order, error = await cancel_order_by_customer(
        db=db,
        order_id=order_id,
        current_customer=current_customer
    )

    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=error)

    return order
