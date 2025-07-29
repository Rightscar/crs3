"""
Unit tests for RelationshipService
"""
import pytest
from uuid import uuid4
from services.relationship_service import RelationshipService, RelationshipUpdate
from models.database import CharacterRelationship


class TestRelationshipService:
    """Test suite for RelationshipService"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_relationship_new(self, test_db, test_characters, mock_graph_db):
        """Test creating a new relationship"""
        service = RelationshipService(test_db, mock_graph_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Create new relationship
        relationship = await service.get_or_create_relationship(
            alice.id, bob.id
        )
        
        assert relationship is not None
        assert relationship.character_a_id == min(alice.id, bob.id)
        assert relationship.character_b_id == max(alice.id, bob.id)
        assert relationship.relationship_type == "neutral"
        assert relationship.strength == 0.0
        assert relationship.trust == 0.5
        assert relationship.familiarity == 0.0
        
        # Check Neo4j was called
        assert len(mock_graph_db.relationships) == 1
    
    @pytest.mark.asyncio
    async def test_get_or_create_relationship_existing(self, test_db, test_relationship, mock_graph_db):
        """Test getting an existing relationship"""
        service = RelationshipService(test_db, mock_graph_db)
        
        # Get existing relationship
        relationship = await service.get_or_create_relationship(
            test_relationship.character_a_id,
            test_relationship.character_b_id
        )
        
        assert relationship.id == test_relationship.id
        assert len(mock_graph_db.relationships) == 0  # Should not create new
    
    @pytest.mark.asyncio
    async def test_update_relationship_positive_interaction(self, test_db, test_relationship, mock_graph_db):
        """Test updating relationship with positive interaction"""
        service = RelationshipService(test_db, mock_graph_db)
        
        # Positive chat interaction
        update = await service.update_relationship(
            test_relationship.character_a_id,
            test_relationship.character_b_id,
            "chat",
            0.7  # Positive sentiment
        )
        
        assert update.strength_delta > 0  # Should increase
        assert update.trust_delta > 0  # Should increase
        assert update.familiarity_delta > 0  # Always increases
        assert update.new_strength > test_relationship.strength
        assert update.new_trust > test_relationship.trust
    
    @pytest.mark.asyncio
    async def test_update_relationship_negative_interaction(self, test_db, test_relationship, mock_graph_db):
        """Test updating relationship with negative interaction"""
        service = RelationshipService(test_db, mock_graph_db)
        
        # Negative conflict interaction
        update = await service.update_relationship(
            test_relationship.character_a_id,
            test_relationship.character_b_id,
            "conflict",
            -0.8  # Negative sentiment
        )
        
        assert update.strength_delta < 0  # Should decrease
        assert update.trust_delta < 0  # Should decrease significantly
        assert update.familiarity_delta > 0  # Still increases
    
    @pytest.mark.asyncio
    async def test_relationship_type_progression(self, test_db, test_characters, mock_graph_db):
        """Test relationship type changes based on interactions"""
        service = RelationshipService(test_db, mock_graph_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Create relationship
        rel = await service.get_or_create_relationship(alice.id, bob.id)
        assert rel.relationship_type == "neutral"
        
        # Multiple positive interactions
        for _ in range(10):
            await service.update_relationship(
                alice.id, bob.id, "chat", 0.8
            )
        
        # Check relationship type changed
        updated_rel = await service.get_or_create_relationship(alice.id, bob.id)
        assert updated_rel.relationship_type in ["friend", "acquaintance"]
        assert updated_rel.strength > 0.3
    
    @pytest.mark.asyncio
    async def test_diminishing_returns_on_strength(self, test_db, test_characters, mock_graph_db):
        """Test diminishing returns as relationship strength approaches extremes"""
        service = RelationshipService(test_db, mock_graph_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Create relationship and boost it high
        rel = await service.get_or_create_relationship(alice.id, bob.id)
        
        # Set high initial strength
        rel.strength = 0.8
        await test_db.commit()
        
        # Try to increase further
        update = await service.update_relationship(
            alice.id, bob.id, "chat", 0.9
        )
        
        # Should have diminished increase
        assert update.strength_delta < 0.05  # Small increase due to diminishing returns
    
    @pytest.mark.asyncio
    async def test_trust_harder_to_rebuild(self, test_db, test_characters, mock_graph_db):
        """Test that trust is harder to rebuild when low"""
        service = RelationshipService(test_db, mock_graph_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Create relationship with low trust
        rel = await service.get_or_create_relationship(alice.id, bob.id)
        rel.trust = 0.2
        await test_db.commit()
        
        # Try to increase trust
        update = await service.update_relationship(
            alice.id, bob.id, "collaboration", 0.8
        )
        
        # Trust should increase slowly
        assert update.trust_delta > 0
        assert update.trust_delta < 0.03  # Reduced increase due to low trust
    
    @pytest.mark.asyncio
    async def test_get_character_relationships(self, test_db, test_characters, mock_graph_db):
        """Test getting all relationships for a character"""
        service = RelationshipService(test_db, mock_graph_db)
        alice = test_characters[0]
        
        # Create multiple relationships
        for other in test_characters[1:]:
            await service.get_or_create_relationship(alice.id, other.id)
        
        # Get Alice's relationships
        relationships = await service.get_character_relationships(alice.id)
        
        assert len(relationships) == 2  # Bob and Charlie
        for rel in relationships:
            assert "character_id" in rel
            assert "relationship_type" in rel
            assert "strength" in rel
    
    @pytest.mark.asyncio
    async def test_calculate_compatibility_similar_personalities(self, test_db, mock_graph_db):
        """Test compatibility calculation for similar personalities"""
        service = RelationshipService(test_db, mock_graph_db)
        
        # Similar personalities
        personality_a = {
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.8,
            "neuroticism": 0.3
        }
        personality_b = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.7,
            "neuroticism": 0.4
        }
        
        compatibility = await service.calculate_compatibility(
            personality_a, personality_b
        )
        
        assert compatibility["overall"] > 0.6  # Should be compatible
        assert compatibility["intellectual"] > 0.8  # Similar openness
        assert compatibility["harmony"] > 0.7  # High agreeableness
    
    @pytest.mark.asyncio
    async def test_calculate_compatibility_opposite_personalities(self, test_db, mock_graph_db):
        """Test compatibility calculation for opposite personalities"""
        service = RelationshipService(test_db, mock_graph_db)
        
        # Opposite personalities
        personality_a = {
            "openness": 0.9,
            "conscientiousness": 0.2,
            "extraversion": 0.8,
            "agreeableness": 0.9,
            "neuroticism": 0.2
        }
        personality_b = {
            "openness": 0.1,
            "conscientiousness": 0.9,
            "extraversion": 0.2,
            "agreeableness": 0.1,
            "neuroticism": 0.9
        }
        
        compatibility = await service.calculate_compatibility(
            personality_a, personality_b
        )
        
        assert compatibility["overall"] < 0.5  # Should be less compatible
        assert compatibility["intellectual"] < 0.3  # Very different openness
        assert compatibility["stability"] < 0.5  # High neuroticism average
    
    def test_relationship_update_to_dict(self):
        """Test RelationshipUpdate to_dict method"""
        update = RelationshipUpdate(
            strength_delta=0.1,
            trust_delta=0.05,
            new_strength=0.6,
            new_trust=0.7,
            familiarity_delta=0.03,
            new_familiarity=0.4
        )
        
        result = update.to_dict()
        
        assert result["strength_delta"] == 0.1
        assert result["trust_delta"] == 0.05
        assert result["new_strength"] == 0.6
        assert result["new_trust"] == 0.7
        assert result["familiarity_delta"] == 0.03
        assert result["new_familiarity"] == 0.4