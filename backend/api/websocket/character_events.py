"""
WebSocket handler for character ecosystem events
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Set, Optional
import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

from core.security import decode_token
from services.event_stream import CharacterEventStream
from core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# WebSocket authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


class ConnectionManager:
    """Manages WebSocket connections for character ecosystems"""
    
    def __init__(self):
        # ecosystem_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.connection_users: Dict[WebSocket, str] = {}
        
    async def connect(self, websocket: WebSocket, ecosystem_id: str, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if ecosystem_id not in self.active_connections:
            self.active_connections[ecosystem_id] = set()
        
        self.active_connections[ecosystem_id].add(websocket)
        self.connection_users[websocket] = user_id
        
        logger.info(f"User {user_id} connected to ecosystem {ecosystem_id}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "ecosystem_id": ecosystem_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, ecosystem_id: str):
        """Remove a WebSocket connection"""
        if ecosystem_id in self.active_connections:
            self.active_connections[ecosystem_id].discard(websocket)
            
            # Clean up empty ecosystems
            if not self.active_connections[ecosystem_id]:
                del self.active_connections[ecosystem_id]
        
        # Remove user mapping
        user_id = self.connection_users.pop(websocket, "unknown")
        logger.info(f"User {user_id} disconnected from ecosystem {ecosystem_id}")
    
    async def broadcast_to_ecosystem(self, ecosystem_id: str, message: dict):
        """Broadcast a message to all connections in an ecosystem"""
        if ecosystem_id not in self.active_connections:
            return
        
        disconnected = set()
        
        # Send to all connected clients
        for connection in self.active_connections[ecosystem_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections[ecosystem_id].discard(conn)
            self.connection_users.pop(conn, None)
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    def get_ecosystem_connections(self, ecosystem_id: str) -> int:
        """Get number of active connections for an ecosystem"""
        return len(self.active_connections.get(ecosystem_id, set()))


# Global connection manager
manager = ConnectionManager()


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None
) -> Optional[dict]:
    """Authenticate WebSocket connection"""
    if not token:
        # Try to get token from query params
        token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    try:
        payload = decode_token(token)
        return {"id": payload.get("sub"), "token": token}
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


async def websocket_endpoint(
    websocket: WebSocket,
    ecosystem_id: str,
    db: AsyncSession
):
    """Main WebSocket endpoint for character ecosystem events"""
    
    # Authenticate
    user = await get_current_user_ws(websocket)
    if not user:
        return
    
    # TODO: Verify user has access to this ecosystem
    
    # Connect
    await manager.connect(websocket, ecosystem_id, user["id"])
    
    # Create event stream
    event_stream = CharacterEventStream()
    
    # Subscribe to ecosystem events
    async def handle_redis_event(event_data):
        """Handle events from Redis and broadcast to WebSocket clients"""
        try:
            # Format the event for WebSocket
            ws_event = {
                "type": "ecosystem_event",
                "event": event_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to all connected clients
            await manager.broadcast_to_ecosystem(ecosystem_id, ws_event)
            
        except Exception as e:
            logger.error(f"Error handling Redis event: {e}")
    
    # Subscribe to Redis events
    subscription_id = await event_stream.subscribe_to_ecosystem(
        ecosystem_id, handle_redis_event
    )
    
    try:
        # Send initial state
        await manager.send_personal_message(websocket, {
            "type": "initial_state",
            "ecosystem_id": ecosystem_id,
            "connected_users": manager.get_ecosystem_connections(ecosystem_id),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Handle different message types
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "request_state":
                    # Send current ecosystem state
                    # TODO: Implement state retrieval
                    await manager.send_personal_message(websocket, {
                        "type": "state_update",
                        "ecosystem_id": ecosystem_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Add more message handlers as needed
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in WebSocket handler: {e}")
                break
    
    finally:
        # Clean up
        manager.disconnect(websocket, ecosystem_id)
        await event_stream.unsubscribe(subscription_id)


# Export for use in routers
async def character_events_ws(
    websocket: WebSocket,
    ecosystem_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """WebSocket endpoint wrapper for FastAPI"""
    await websocket_endpoint(websocket, ecosystem_id, db)