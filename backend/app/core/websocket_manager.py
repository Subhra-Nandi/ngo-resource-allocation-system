import json
from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    Each NGO dashboard that is open connects here.
    When a new event happens (match, new request etc)
    we broadcast to all connected clients.
    """

    def __init__(self):
        # List of all currently connected WebSocket clients
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict[str, Any]):
        """
        Send an event to ALL connected dashboards.
        Called whenever something important happens.
        """
        message = json.dumps({
            "type": event_type,
            "data": data,
        })

        # Send to each connection — remove dead ones
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)

        for d in dead:
            self.disconnect(d)

    async def send_to_one(self, websocket: WebSocket, event_type: str, data: dict):
        """Send an event to a single connection."""
        try:
            await websocket.send_text(json.dumps({
                "type": event_type,
                "data": data,
            }))
        except Exception:
            self.disconnect(websocket)


# Single shared instance — imported everywhere that needs to broadcast
manager = ConnectionManager()