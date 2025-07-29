"""
Integration tests for character lifecycle flow
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import json

from backend.api.main import app
from backend.models.database import User, Character, Ecosystem
from backend.core.security import create_access_token


@pytest.mark.asyncio
class TestCharacterFlow:
    """Test complete character lifecycle from creation to interactions"""
    
    async def setup_method(self):
        """Setup test data"""
        self.test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
        self.auth_headers = None
        self.user_id = None
        self.ecosystem_id = None
    
    async def test_complete_character_flow(self, async_client: AsyncClient, test_db: AsyncSession):
        """Test the complete character flow from creation to interaction"""
        
        # Step 1: Register user
        response = await async_client.post(
            "/api/v1/auth/register",
            json=self.test_user
        )
        assert response.status_code == 200
        user_data = response.json()
        self.user_id = user_data["id"]
        
        # Step 2: Login
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        assert response.status_code == 200
        token_data = response.json()
        self.auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Create ecosystem
        ecosystem_data = {
            "name": "Test Literary Universe",
            "description": "A test ecosystem for character interactions",
            "settings": {
                "allow_autonomous": True,
                "interaction_cooldown": 60
            }
        }
        response = await async_client.post(
            "/api/v1/ecosystems/",
            json=ecosystem_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        ecosystem = response.json()
        self.ecosystem_id = ecosystem["id"]
        
        # Step 4: Create multiple characters
        characters = []
        character_data = [
            {
                "name": "Alice Wonderland",
                "description": "A curious and adventurous character",
                "personality_traits": {
                    "openness": 0.9,
                    "conscientiousness": 0.6,
                    "extraversion": 0.7,
                    "agreeableness": 0.8,
                    "neuroticism": 0.3
                },
                "ecosystem_id": self.ecosystem_id
            },
            {
                "name": "Bob Builder",
                "description": "A practical and organized character",
                "personality_traits": {
                    "openness": 0.4,
                    "conscientiousness": 0.9,
                    "extraversion": 0.5,
                    "agreeableness": 0.6,
                    "neuroticism": 0.4
                },
                "ecosystem_id": self.ecosystem_id
            },
            {
                "name": "Charlie Chaplin",
                "description": "A creative and emotional character",
                "personality_traits": {
                    "openness": 0.8,
                    "conscientiousness": 0.5,
                    "extraversion": 0.6,
                    "agreeableness": 0.7,
                    "neuroticism": 0.7
                },
                "ecosystem_id": self.ecosystem_id
            }
        ]
        
        for char_data in character_data:
            response = await async_client.post(
                "/api/v1/characters/",
                json=char_data,
                headers=self.auth_headers
            )
            assert response.status_code == 200
            character = response.json()
            characters.append(character)
            
            # Verify character fields
            assert character["name"] == char_data["name"]
            assert character["ecosystem_id"] == self.ecosystem_id
            assert character["social_energy"] == 1.0  # Full energy
            assert character["autonomy_level"] == 0.5  # Default
            assert character["is_active"] == True
        
        # Step 5: Get characters in ecosystem
        response = await async_client.get(
            f"/api/v1/ecosystems/{self.ecosystem_id}/characters",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        ecosystem_chars = response.json()
        assert len(ecosystem_chars["items"]) == 3
        
        # Step 6: Create interactions between characters
        alice_id = characters[0]["id"]
        bob_id = characters[1]["id"]
        charlie_id = characters[2]["id"]
        
        # Alice greets Bob
        interaction1 = {
            "initiator_id": alice_id,
            "target_id": bob_id,
            "interaction_type": "greeting",
            "content": "Hello Bob! It's nice to meet you.",
            "context": {"test": True}
        }
        
        response = await async_client.post(
            "/api/v1/interactions/",
            json=interaction1,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        result1 = response.json()
        assert result1["success"] == True
        assert result1["response"] is not None
        assert result1["relationship_change"] is not None
        
        # Bob chats with Alice
        interaction2 = {
            "initiator_id": bob_id,
            "target_id": alice_id,
            "interaction_type": "chat",
            "content": "Nice to meet you too, Alice! How are you?",
            "context": {"test": True}
        }
        
        response = await async_client.post(
            "/api/v1/interactions/",
            json=interaction2,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        result2 = response.json()
        assert result2["success"] == True
        
        # Charlie has conflict with Bob
        interaction3 = {
            "initiator_id": charlie_id,
            "target_id": bob_id,
            "interaction_type": "conflict",
            "content": "I disagree with your approach, Bob!",
            "context": {"test": True}
        }
        
        response = await async_client.post(
            "/api/v1/interactions/",
            json=interaction3,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        result3 = response.json()
        assert result3["success"] == True
        
        # Step 7: Check character states after interactions
        response = await async_client.get(
            f"/api/v1/characters/{alice_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        alice_after = response.json()
        assert alice_after["social_energy"] < 1.0  # Energy depleted
        assert alice_after["interaction_count"] == 2
        
        # Step 8: Check relationships
        response = await async_client.get(
            f"/api/v1/characters/{alice_id}/relationships",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        alice_relationships = response.json()
        assert len(alice_relationships) > 0
        
        # Find relationship with Bob
        bob_relationship = next(
            (r for r in alice_relationships if r["character_id"] == bob_id),
            None
        )
        assert bob_relationship is not None
        assert bob_relationship["strength"] > 0  # Positive relationship
        assert bob_relationship["interaction_count"] == 2
        
        # Step 9: Test character update
        update_data = {
            "description": "Alice has grown more confident",
            "autonomy_level": 0.7
        }
        response = await async_client.patch(
            f"/api/v1/characters/{alice_id}",
            json=update_data,
            headers=self.auth_headers
        )
        assert response.status_code == 200
        updated_alice = response.json()
        assert updated_alice["autonomy_level"] == 0.7
        
        # Step 10: Test character deletion
        response = await async_client.delete(
            f"/api/v1/characters/{charlie_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        response = await async_client.get(
            f"/api/v1/characters/{charlie_id}",
            headers=self.auth_headers
        )
        assert response.status_code == 404
    
    async def test_character_energy_depletion(self, async_client: AsyncClient, test_db: AsyncSession):
        """Test that character energy depletes with interactions"""
        
        # Setup (abbreviated)
        await self._setup_test_user_and_ecosystem(async_client)
        
        # Create character with full energy
        char_data = {
            "name": "Energy Test Character",
            "description": "Testing energy depletion",
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
            headers=self.auth_headers
        )
        character1 = response.json()
        
        # Create second character
        char_data["name"] = "Energy Test Character 2"
        response = await async_client.post(
            "/api/v1/characters/",
            json=char_data,
            headers=self.auth_headers
        )
        character2 = response.json()
        
        initial_energy = character1["social_energy"]
        assert initial_energy == 1.0
        
        # Multiple interactions to deplete energy
        for i in range(5):
            interaction = {
                "initiator_id": character1["id"],
                "target_id": character2["id"],
                "interaction_type": "chat",
                "content": f"Test message {i}",
                "context": {}
            }
            
            response = await async_client.post(
                "/api/v1/interactions/",
                json=interaction,
                headers=self.auth_headers
            )
            assert response.status_code == 200
        
        # Check energy after interactions
        response = await async_client.get(
            f"/api/v1/characters/{character1['id']}",
            headers=self.auth_headers
        )
        character1_after = response.json()
        assert character1_after["social_energy"] < initial_energy
        assert character1_after["social_energy"] >= 0  # Never negative
    
    async def test_character_validation(self, async_client: AsyncClient, test_db: AsyncSession):
        """Test character creation validation"""
        
        await self._setup_test_user_and_ecosystem(async_client)
        
        # Test invalid personality traits
        invalid_char = {
            "name": "Invalid Character",
            "description": "Testing validation",
            "personality_traits": {
                "openness": 1.5,  # Out of range
                "conscientiousness": -0.1,  # Out of range
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            },
            "ecosystem_id": self.ecosystem_id
        }
        
        response = await async_client.post(
            "/api/v1/characters/",
            json=invalid_char,
            headers=self.auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test missing required fields
        incomplete_char = {
            "name": "Incomplete Character"
            # Missing description and other fields
        }
        
        response = await async_client.post(
            "/api/v1/characters/",
            json=incomplete_char,
            headers=self.auth_headers
        )
        assert response.status_code == 422
    
    async def _setup_test_user_and_ecosystem(self, async_client: AsyncClient):
        """Helper method to setup user and ecosystem"""
        # Register and login
        await async_client.post("/api/v1/auth/register", json=self.test_user)
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        token_data = response.json()
        self.auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Create ecosystem
        ecosystem_data = {
            "name": "Test Ecosystem",
            "description": "Test",
            "settings": {}
        }
        response = await async_client.post(
            "/api/v1/ecosystems/",
            json=ecosystem_data,
            headers=self.auth_headers
        )
        ecosystem = response.json()
        self.ecosystem_id = ecosystem["id"]