from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import order_ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/orders/{order_id}")
async def ws_order(websocket: WebSocket, order_id: int):
    await order_ws_manager.connect_order(order_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_ws_manager.disconnect_order(order_id, websocket)


@router.websocket("/ws/chef/{restaurant_id}/orders")
async def ws_chef_orders(websocket: WebSocket, restaurant_id: int):
    await order_ws_manager.connect_chef_restaurant(restaurant_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_ws_manager.disconnect_chef_restaurant(restaurant_id, websocket)
