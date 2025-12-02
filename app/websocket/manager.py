from typing import Dict, List
from fastapi import WebSocket


class OrderWSManager:
    def __init__(self):
        self.order_clients: Dict[int, List[WebSocket]] = {}
        self.chef_clients: Dict[int, List[WebSocket]] = {}

    async def connect_order(self, order_id: int, ws: WebSocket):
        await ws.accept()
        self.order_clients.setdefault(order_id, []).append(ws)

    def disconnect_order(self, order_id: int, ws: WebSocket):
        self.order_clients.get(order_id, []).remove(ws)

    async def broadcast_order(self, order_id: int, message: dict):
        for ws in list(self.order_clients.get(order_id, [])):
            await ws.send_json(message)

    async def connect_chef_restaurant(self, restaurant_id: int, ws: WebSocket):
        await ws.accept()
        self.chef_clients.setdefault(restaurant_id, []).append(ws)

    def disconnect_chef_restaurant(self, restaurant_id: int, ws: WebSocket):
        self.chef_clients.get(restaurant_id, []).remove(ws)

    async def broadcast_to_restaurant(self, restaurant_id: int, message: dict):
        for ws in list(self.chef_clients.get(restaurant_id, [])):
            await ws.send_json(message)


order_ws_manager = OrderWSManager()
