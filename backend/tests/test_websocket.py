"""
WebSocket integration tests
"""
import pytest
import json
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from api.websocket.character_events import ConnectionManager, get_current_user_ws
from core.security import create_access_token


class TestConnectionManager:
    """Test suite for WebSocket ConnectionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connect_new_ecosystem(self, manager):
        """Test connecting to a new ecosystem"""
        websocket = AsyncMock()
        ecosystem_id = "test_eco_123"
        user_id = "user_123"
        
        await manager.connect(websocket, ecosystem_id, user_id)
        
        # Check websocket accepted
        websocket.accept.assert_called_once()
        
        # Check connection registered
        assert ecosystem_id in manager.active_connections
        assert websocket in manager.active_connections[ecosystem_id]
        assert manager.connection_users[websocket] == user_id
        
        # Check welcome message sent
        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connection"
        assert call_args["status"] == "connected"
    
    def test_disconnect(self, manager):
        """Test disconnecting from ecosystem"""
        websocket = MagicMock()
        ecosystem_id = "test_eco_123"
        user_id = "user_123"
        
        # Add connection first
        manager.active_connections[ecosystem_id] = {websocket}
        manager.connection_users[websocket] = user_id
        
        # Disconnect
        manager.disconnect(websocket, ecosystem_id)
        
        # Check connection removed
        assert ecosystem_id not in manager.active_connections
        assert websocket not in manager.connection_users
    
    @pytest.mark.asyncio
    async def test_broadcast_to_ecosystem(self, manager):
        """Test broadcasting message to all connections in ecosystem"""
        # Create mock websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()  # Different ecosystem
        
        ecosystem_id = "test_eco_123"
        other_ecosystem = "other_eco"
        
        # Set up connections
        manager.active_connections[ecosystem_id] = {ws1, ws2}
        manager.active_connections[other_ecosystem] = {ws3}
        
        # Broadcast message
        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_ecosystem(ecosystem_id, message)
        
        # Check correct websockets received message
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self, manager):
        """Test broadcast handles disconnected clients gracefully"""
        # Create websocket that will fail
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = Exception("Connection lost")
        
        ecosystem_id = "test_eco_123"
        manager.active_connections[ecosystem_id] = {ws_good, ws_bad}
        manager.connection_users[ws_good] = "user1"
        manager.connection_users[ws_bad] = "user2"
        
        # Broadcast should not raise exception
        message = {"type": "test"}
        await manager.broadcast_to_ecosystem(ecosystem_id, message)
        
        # Good websocket should receive message
        ws_good.send_json.assert_called_once_with(message)
        
        # Bad websocket should be removed
        assert ws_bad not in manager.active_connections[ecosystem_id]
        assert ws_bad not in manager.connection_users
    
    def test_get_ecosystem_connections(self, manager):
        """Test getting connection count for ecosystem"""
        ecosystem_id = "test_eco_123"
        
        # No connections
        assert manager.get_ecosystem_connections(ecosystem_id) == 0
        
        # Add connections
        manager.active_connections[ecosystem_id] = {MagicMock(), MagicMock()}
        assert manager.get_ecosystem_connections(ecosystem_id) == 2


class TestWebSocketAuthentication:
    """Test WebSocket authentication"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_ws_valid_token(self):
        """Test authentication with valid token"""
        websocket = AsyncMock()
        
        # Create valid token
        token_data = {"sub": "user_123"}
        token = create_access_token(token_data)
        
        # Test with token parameter
        user = await get_current_user_ws(websocket, token)
        
        assert user is not None
        assert user["id"] == "user_123"
        assert user["token"] == token
    
    @pytest.mark.asyncio
    async def test_get_current_user_ws_query_param(self):
        """Test authentication with token in query params"""
        websocket = AsyncMock()
        
        # Create valid token
        token_data = {"sub": "user_456"}
        token = create_access_token(token_data)
        
        # Mock query params
        websocket.query_params = {"token": token}
        
        # Test without token parameter
        user = await get_current_user_ws(websocket)
        
        assert user is not None
        assert user["id"] == "user_456"
    
    @pytest.mark.asyncio
    async def test_get_current_user_ws_no_token(self):
        """Test authentication without token"""
        websocket = AsyncMock()
        websocket.query_params = {}
        
        user = await get_current_user_ws(websocket)
        
        assert user is None
        websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_user_ws_invalid_token(self):
        """Test authentication with invalid token"""
        websocket = AsyncMock()
        
        # Invalid token
        token = "invalid.token.here"
        
        user = await get_current_user_ws(websocket, token)
        
        assert user is None
        websocket.close.assert_called_once()


class TestWebSocketEventFlow:
    """Test complete WebSocket event flow"""
    
    @pytest.mark.asyncio
    async def test_character_interaction_event_flow(self, test_db, test_characters, mock_redis):
        """Test that character interactions trigger WebSocket events"""
        from services import CharacterInteractionEngine
        
        # Create mock WebSocket and manager
        websocket = AsyncMock()
        manager = ConnectionManager()
        ecosystem_id = str(test_characters[0].ecosystem_id)
        
        # Connect WebSocket
        await manager.connect(websocket, ecosystem_id, "user_123")
        
        # Create interaction engine
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Process interaction (this should emit events)
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="greeting",
            content="Hello Bob!",
            context={}
        )
        
        assert result.success is True
        
        # Check Redis received event
        assert len(mock_redis.pubsub_messages) > 0
        channel, event = mock_redis.pubsub_messages[0]
        assert f"ecosystem:{ecosystem_id}:events" in channel
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong mechanism"""
        websocket = AsyncMock()
        manager = ConnectionManager()
        
        # Connect
        await manager.connect(websocket, "test_eco", "user_123")
        
        # Send ping
        ping_message = {"type": "ping"}
        
        # Simulate receiving ping and sending pong
        await manager.send_personal_message(websocket, {
            "type": "pong",
            "timestamp": "2024-01-01T00:00:00"
        })
        
        # Check pong sent
        websocket.send_json.assert_called()
        last_call = websocket.send_json.call_args[0][0]
        assert last_call["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        websocket = AsyncMock()
        manager = ConnectionManager()
        
        # Connect
        await manager.connect(websocket, "test_eco", "user_123")
        
        # Send invalid JSON
        await manager.send_personal_message(websocket, {
            "type": "error",
            "message": "Invalid JSON",
            "timestamp": "2024-01-01T00:00:00"
        })
        
        # Check error message sent
        websocket.send_json.assert_called()
        last_call = websocket.send_json.call_args[0][0]
        assert last_call["type"] == "error"
        assert "Invalid JSON" in last_call["message"]