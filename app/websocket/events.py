from app.models.order import Order
from app.websocket.manager import order_ws_manager


async def push_new_order(order: Order):
    msg = {
        "event": "new_order",
        "order_id": order.id,
        "restaurant_id": order.restaurant_id,
        "status": order.status.value,
    }
    await order_ws_manager.broadcast_to_restaurant(order.restaurant_id, msg)


async def push_status_update(order: Order):
    msg = {
        "event": "order_status_update",
        "order_id": order.id,
        "status": order.status.value,
    }
    await order_ws_manager.broadcast_order(order.id, msg)
    await order_ws_manager.broadcast_to_restaurant(order.restaurant_id, msg)


async def push_order_canceled(order: Order):
    msg = {
        "event": "order_canceled",
        "order_id": order.id,
    }
    await order_ws_manager.broadcast_order(order.id, msg)
    await order_ws_manager.broadcast_to_restaurant(order.restaurant_id, msg)


async def push_order_delayed(order: Order):
    msg = {
        "event": "order_delayed",
        "order_id": order.id,
        "reason": order.delay_reason,
    }
    await order_ws_manager.broadcast_order(order.id, msg)
    await order_ws_manager.broadcast_to_restaurant(order.restaurant_id, msg)
