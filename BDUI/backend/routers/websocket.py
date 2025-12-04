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

    def disconnect(self, websocket: WebSocket, screen_id: str = None, is_admin: bool = False):
        if is_admin:
            if websocket in self.admin_connections:
                self.admin_connections.remove(websocket)
            print(f"Admin disconnected. Total admin connections: {len(self.admin_connections)}")
        else:
            if screen_id and screen_id in self.active_connections:
                if websocket in self.active_connections[screen_id]:
                    self.active_connections[screen_id].remove(websocket)
                if not self.active_connections[screen_id]:
                    del self.active_connections[screen_id]
            print(f"Client disconnected from screen {screen_id}")

    async def send_to_screen(self, screen_id: str, message: dict):
        """Отправить сообщение всем клиентам, просматривающим конкретный экран"""
        if screen_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[screen_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.active_connections[screen_id].remove(conn)

