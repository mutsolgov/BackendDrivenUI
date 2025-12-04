from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.admin_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, screen_id: str = None, is_admin: bool = False):
        await websocket.accept()
        
        if is_admin:
            self.admin_connections.append(websocket)
            print(f"Admin connected. Total admin connections: {len(self.admin_connections)}")
        else:
            if screen_id not in self.active_connections:
                self.active_connections[screen_id] = []
            self.active_connections[screen_id].append(websocket)
            print(f"Client connected to screen {screen_id}. Total connections: {len(self.active_connections.get(screen_id, []))}")

