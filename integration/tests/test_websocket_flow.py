"""
Integration tests for WebSocket real-time event flow
"""
import asyncio
import pytest
import json
from websockets import connect, WebSocketClientProtocol
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestWebSocketFlow:
    """Test WebSocket connections and real-time event propagation"""
    
    async def setup_method(self):
        """Setup test data"""
        self.base_url = "ws://localhost:8000"
        self.test_user = {
            "email": "wstest@example.com",
            "username": "wstestuser",
            "password": "testpass123"
        }
        self.auth_token = None
        self.ecosystem_id = None
        self.character_ids = []
    
    async def test_websocket_connection_and_events(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test WebSocket connection and real-time event reception"""
        
        # Setup: Create user, ecosystem, and characters
        await self._setup_test_environment(async_client)
        
        # Connect to WebSocket
        ws_url = f"{self.base_url}/api/v1/interactions/ws/{self.ecosystem_id}?token={self.auth_token}"
        
        async with connect(ws_url) as websocket:
            # Wait for connection confirmation
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            assert connection_data["type"] == "connection"
            assert connection_data["status"] == "connected"
            
            # Get initial state
            initial_state_msg = await websocket.recv()
            initial_state = json.loads(initial_state_msg)
            assert initial_state["type"] == "initial_state"
            
            # Create a task to receive WebSocket messages
            received_events = []
            
            async def receive_messages():
                try:
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        if data["type"] == "ecosystem_event":
                            received_events.append(data)
                            logger.info(f"Received event: {data['event']['type']}")
                except Exception as e:
                    logger.error(f"WebSocket receive error: {e}")
            
            # Start receiving messages in background
            receive_task = asyncio.create_task(receive_messages())
            
            # Trigger character interaction via API
            interaction_data = {
                "initiator_id": self.character_ids[0],
                "target_id": self.character_ids[1],
                "interaction_type": "greeting",
                "content": "Hello! Testing WebSocket events.",
                "context": {"websocket_test": True}
            }
            
            response = await async_client.post(
                "/api/v1/interactions/",
                json=interaction_data,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            assert response.status_code == 200
            
            # Wait for event to be received
            await asyncio.sleep(0.5)
            
            # Cancel receive task
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            
            # Verify we received the interaction event
            assert len(received_events) > 0
            
            interaction_event = next(
                (e for e in received_events if e["event"]["type"] == "character_interaction"),
                None
            )
            assert interaction_event is not None
            assert interaction_event["event"]["data"]["interaction_type"] == "character_interaction"
            assert len(interaction_event["event"]["data"]["participants"]) == 2
    
    async def test_multiple_websocket_clients(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test multiple WebSocket clients receiving same events"""
        
        await self._setup_test_environment(async_client)
        
        ws_url = f"{self.base_url}/api/v1/interactions/ws/{self.ecosystem_id}?token={self.auth_token}"
        
        # Connect multiple clients
        async with connect(ws_url) as ws1, connect(ws_url) as ws2:
            # Skip connection messages
            await ws1.recv()  # connection
            await ws1.recv()  # initial state
            await ws2.recv()  # connection
            await ws2.recv()  # initial state
            
            # Track received events for both clients
            client1_events = []
            client2_events = []
            
            async def receive_for_client(ws: WebSocketClientProtocol, events_list: list):
                try:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data["type"] == "ecosystem_event":
                            events_list.append(data)
                except Exception:
                    pass
            
            # Start receiving for both clients
            task1 = asyncio.create_task(receive_for_client(ws1, client1_events))
            task2 = asyncio.create_task(receive_for_client(ws2, client2_events))
            
            # Trigger interaction
            interaction_data = {
                "initiator_id": self.character_ids[0],
                "target_id": self.character_ids[1],
                "interaction_type": "chat",
                "content": "Broadcasting to multiple clients!",
                "context": {}
            }
            
            await async_client.post(
                "/api/v1/interactions/",
                json=interaction_data,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            # Wait for events
            await asyncio.sleep(0.5)
            
            # Cleanup
            task1.cancel()
            task2.cancel()
            
            # Both clients should receive the same event
            assert len(client1_events) > 0
            assert len(client2_events) > 0
            assert client1_events[0]["event"]["type"] == client2_events[0]["event"]["type"]
    
    async def test_websocket_ping_pong(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test WebSocket ping/pong keepalive"""
        
        await self._setup_test_environment(async_client)
        
        ws_url = f"{self.base_url}/api/v1/interactions/ws/{self.ecosystem_id}?token={self.auth_token}"
        
        async with connect(ws_url) as websocket:
            # Skip initial messages
            await websocket.recv()  # connection
            await websocket.recv()  # initial state
            
            # Send ping
            ping_msg = json.dumps({"type": "ping"})
            await websocket.send(ping_msg)
            
            # Wait for pong
            response = await websocket.recv()
            pong_data = json.loads(response)
            assert pong_data["type"] == "pong"
    
    async def test_websocket_reconnection(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test WebSocket reconnection behavior"""
        
        await self._setup_test_environment(async_client)
        
        ws_url = f"{self.base_url}/api/v1/interactions/ws/{self.ecosystem_id}?token={self.auth_token}"
        
        # First connection
        async with connect(ws_url) as ws1:
            await ws1.recv()  # connection
            await ws1.recv()  # initial state
            
            # Close connection
            await ws1.close()
        
        # Reconnect
        async with connect(ws_url) as ws2:
            connection_msg = await ws2.recv()
            connection_data = json.loads(connection_msg)
            assert connection_data["type"] == "connection"
            assert connection_data["status"] == "connected"
    
    async def test_websocket_authentication_failure(self):
        """Test WebSocket connection with invalid token"""
        
        # Try to connect with invalid token
        ws_url = f"{self.base_url}/api/v1/interactions/ws/test-ecosystem?token=invalid-token"
        
        try:
            async with connect(ws_url) as websocket:
                # Should not reach here
                assert False, "Connection should have been rejected"
        except Exception as e:
            # Expected to fail
            assert "401" in str(e) or "403" in str(e) or "1008" in str(e)
    
    async def test_event_types(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession
    ):
        """Test different event types through WebSocket"""
        
        await self._setup_test_environment(async_client)
        
        ws_url = f"{self.base_url}/api/v1/interactions/ws/{self.ecosystem_id}?token={self.auth_token}"
        
        async with connect(ws_url) as websocket:
            # Skip initial messages
            await websocket.recv()  # connection
            await websocket.recv()  # initial state
            
            received_events = []
            
            async def receive_events():
                try:
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        if data["type"] == "ecosystem_event":
                            received_events.append(data["event"])
                except Exception:
                    pass
            
            receive_task = asyncio.create_task(receive_events())
            
            # Trigger different interaction types
            interaction_types = ["greeting", "chat", "conflict", "collaboration"]
            
            for i, interaction_type in enumerate(interaction_types):
                interaction_data = {
                    "initiator_id": self.character_ids[i % 2],
                    "target_id": self.character_ids[(i + 1) % 2],
                    "interaction_type": interaction_type,
                    "content": f"Testing {interaction_type} interaction",
                    "context": {}
                }
                
                await async_client.post(
                    "/api/v1/interactions/",
                    json=interaction_data,
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                
                await asyncio.sleep(0.1)
            
            # Wait for all events
            await asyncio.sleep(0.5)
            
            receive_task.cancel()
            
            # Verify we received events for all interaction types
            assert len(received_events) >= len(interaction_types)
            
            event_types = [e["data"]["interaction_type"] for e in received_events if e["type"] == "character_interaction"]
            for expected_type in ["greeting", "chat", "conflict", "collaboration"]:
                assert expected_type in event_types
    
    async def _setup_test_environment(self, async_client: AsyncClient):
        """Helper to setup test user, ecosystem, and characters"""
        
        # Register user
        await async_client.post("/api/v1/auth/register", json=self.test_user)
        
        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        token_data = response.json()
        self.auth_token = token_data["access_token"]
        
        # Create ecosystem
        ecosystem_data = {
            "name": "WebSocket Test Ecosystem",
            "description": "Testing WebSocket events",
            "settings": {}
        }
        response = await async_client.post(
            "/api/v1/ecosystems/",
            json=ecosystem_data,
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        ecosystem = response.json()
        self.ecosystem_id = ecosystem["id"]
        
        # Create test characters
        for i in range(3):
            char_data = {
                "name": f"WebSocket Test Character {i}",
                "description": "Test character for WebSocket testing",
                "personality_traits": {
                    "openness": 0.5,
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.5
                },
                "ecosystem_id": self.ecosystem_id
            }
            
            response = await async_client.post(
                "/api/v1/characters/",
                json=char_data,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            character = response.json()
            self.character_ids.append(character["id"])