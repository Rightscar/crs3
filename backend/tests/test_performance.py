"""
Performance tests using Locust
"""
from locust import HttpUser, task, between
from uuid import uuid4
import json
import random


class CharacterInteractionUser(HttpUser):
    """Simulates users interacting with characters"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login and setup before tasks"""
        # Login to get token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
        
        # Create test characters
        self.character_ids = []
        self.ecosystem_id = str(uuid4())
        
        for i in range(3):
            char_data = {
                "name": f"TestChar{i}",
                "description": f"Test character {i}",
                "personality_traits": {
                    "openness": random.uniform(0.3, 0.8),
                    "conscientiousness": random.uniform(0.3, 0.8),
                    "extraversion": random.uniform(0.3, 0.8),
                    "agreeableness": random.uniform(0.3, 0.8),
                    "neuroticism": random.uniform(0.2, 0.6)
                }
            }
            
            response = self.client.post(
                "/api/v1/characters/",
                json=char_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                char = response.json()
                self.character_ids.append(char["id"])
    
    @task(3)
    def process_interaction(self):
        """Test character interaction endpoint"""
        if len(self.character_ids) < 2:
            return
        
        # Random character pair
        initiator_id = random.choice(self.character_ids)
        target_id = random.choice([id for id in self.character_ids if id != initiator_id])
        
        # Random interaction type
        interaction_types = ["greeting", "chat", "discussion", "collaboration"]
        interaction_type = random.choice(interaction_types)
        
        # Random content
        contents = [
            "Hello! How are you today?",
            "What do you think about this?",
            "I have an interesting idea to share.",
            "Would you like to work together?",
            "I disagree with your perspective.",
            "That's a fascinating point!"
        ]
        
        interaction_data = {
            "initiator_id": initiator_id,
            "target_id": target_id,
            "interaction_type": interaction_type,
            "content": random.choice(contents),
            "context": {}
        }
        
        with self.client.post(
            "/api/v1/interactions/",
            json=interaction_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_character_relationships(self):
        """Test getting character relationships"""
        if not self.character_ids:
            return
        
        character_id = random.choice(self.character_ids)
        
        self.client.get(
            f"/api/v1/characters/{character_id}/relationships",
            headers=self.headers
        )
    
    @task(1)
    def get_interaction_types(self):
        """Test getting interaction types"""
        self.client.get(
            "/api/v1/interactions/types",
            headers=self.headers
        )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health")


class WebSocketUser(HttpUser):
    """Simulates WebSocket connections"""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """Setup WebSocket connection"""
        # Get auth token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
        else:
            self.token = None
        
        self.ecosystem_id = str(uuid4())
    
    @task
    def websocket_connection(self):
        """Test WebSocket connection"""
        # Note: Locust doesn't natively support WebSockets
        # This simulates the HTTP upgrade request
        
        headers = {
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": "x3JJHMbDL1EzLkh9GBhXDw=="
        }
        
        with self.client.get(
            f"/api/v1/interactions/ws/{self.ecosystem_id}?token={self.token}",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code in [101, 426]:  # WebSocket upgrade or upgrade required
                response.success()
            else:
                response.failure(f"WebSocket upgrade failed: {response.status_code}")


class MixedLoadUser(HttpUser):
    """Simulates mixed load patterns"""
    
    wait_time = between(0.5, 2)
    
    tasks = {
        CharacterInteractionUser: 3,
        WebSocketUser: 1
    }


# Locust configuration for different test scenarios
class QuickTest(CharacterInteractionUser):
    """Quick performance test - 10 users"""
    min_wait = 500
    max_wait = 1000


class StressTest(CharacterInteractionUser):
    """Stress test - 100 users"""
    min_wait = 100
    max_wait = 500


class EnduranceTest(MixedLoadUser):
    """Endurance test - mixed load over time"""
    min_wait = 1000
    max_wait = 5000