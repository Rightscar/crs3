"""
Integration tests for CharacterInteractionEngine
"""
import pytest
from uuid import uuid4
from services.character_interaction_engine import CharacterInteractionEngine, InteractionResult
from models.database import Message, Conversation


class TestCharacterInteractionEngine:
    """Test suite for CharacterInteractionEngine"""
    
    @pytest.mark.asyncio
    async def test_process_interaction_success(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test successful character interaction"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Process greeting interaction
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="greeting",
            content="Hello Bob! How are you today?",
            context={}
        )
        
        assert result.success is True
        assert result.response is not None
        assert "Bob" in result.response or "hello" in result.response.lower()
        assert result.relationship_change is not None
        assert result.emotional_state is not None
        
        # Check Redis events were published
        assert len(mock_redis.pubsub_messages) > 0
        channel, message = mock_redis.pubsub_messages[0]
        assert "ecosystem" in channel
    
    @pytest.mark.asyncio
    async def test_process_interaction_character_not_found(self, test_db):
        """Test interaction with non-existent character"""
        engine = CharacterInteractionEngine(test_db)
        
        result = await engine.process_interaction(
            initiator_id=uuid4(),
            target_id=uuid4(),
            interaction_type="chat",
            content="Hello!",
            context={}
        )
        
        assert result.success is False
        assert "not found" in result.reason
    
    @pytest.mark.asyncio
    async def test_process_interaction_different_ecosystems(self, test_db, test_characters, test_user):
        """Test interaction between characters in different ecosystems"""
        engine = CharacterInteractionEngine(test_db)
        alice = test_characters[0]
        
        # Create character in different ecosystem
        other_ecosystem_char = test_characters[1]
        other_ecosystem_char.ecosystem_id = uuid4()
        await test_db.commit()
        
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=other_ecosystem_char.id,
            interaction_type="chat",
            content="Hello!",
            context={}
        )
        
        assert result.success is False
        assert "same ecosystem" in result.reason
    
    @pytest.mark.asyncio
    async def test_process_interaction_low_energy(self, test_db, test_characters):
        """Test interaction when character has low social energy"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Set low energy
        alice.social_energy = 0.05
        await test_db.commit()
        
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="chat",
            content="Let's have a long conversation!",
            context={}
        )
        
        assert result.success is False
        assert "exhausted" in result.reason
    
    @pytest.mark.asyncio
    async def test_process_interaction_inactive_character(self, test_db, test_characters):
        """Test interaction with inactive character"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Make Bob inactive
        bob.is_active = False
        await test_db.commit()
        
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="chat",
            content="Hello Bob!",
            context={}
        )
        
        assert result.success is False
        assert "inactive" in result.reason
    
    @pytest.mark.asyncio
    async def test_energy_depletion_after_interaction(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test that social energy depletes after interaction"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        initial_alice_energy = alice.social_energy
        initial_bob_energy = bob.social_energy
        
        # Process interaction
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="discussion",  # Higher energy cost
            content="Let's discuss philosophy!",
            context={}
        )
        
        assert result.success is True
        
        # Refresh characters
        await test_db.refresh(alice)
        await test_db.refresh(bob)
        
        # Check energy decreased
        assert alice.social_energy < initial_alice_energy
        assert bob.social_energy < initial_bob_energy
        # Responder uses less energy
        assert (initial_alice_energy - alice.social_energy) > (initial_bob_energy - bob.social_energy)
    
    @pytest.mark.asyncio
    async def test_conversation_history_stored(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test that conversation history is properly stored"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Process interaction
        content = "Hello Bob! Want to work together?"
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="collaboration",
            content=content,
            context={}
        )
        
        assert result.success is True
        
        # Check messages were created
        messages = await test_db.execute(
            test_db.query(Message).filter(
                Message.content.in_([content, result.response])
            )
        )
        messages = messages.scalars().all()
        
        assert len(messages) == 2
        assert any(msg.sender_id == alice.id for msg in messages)
        assert any(msg.sender_id == bob.id for msg in messages)
    
    @pytest.mark.asyncio
    async def test_emotional_state_tracking(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test that emotional states are tracked and updated"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Process positive interaction
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="emotional_support",
            content="I'm here for you, Bob. You're doing great!",
            context={"emotion_level": 0.8}
        )
        
        assert result.success is True
        assert result.emotional_state is not None
        
        # Check emotional state has positive emotions
        assert "joy" in result.emotional_state
        assert sum(result.emotional_state.values()) == pytest.approx(1.0, 0.01)
        
        # Refresh Bob and check current context
        await test_db.refresh(bob)
        assert bob.current_context is not None
        assert "last_emotional_state" in bob.current_context
    
    @pytest.mark.asyncio
    async def test_relationship_progression_over_interactions(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test relationship progression over multiple interactions"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Initial interaction
        result1 = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="greeting",
            content="Nice to meet you, Bob!",
            context={}
        )
        
        assert result1.success is True
        initial_strength = result1.relationship_change["new_strength"]
        
        # Multiple positive interactions
        for i in range(5):
            result = await engine.process_interaction(
                initiator_id=alice.id,
                target_id=bob.id,
                interaction_type="chat",
                content=f"I really enjoy talking with you! ({i})",
                context={}
            )
            assert result.success is True
        
        # Check relationship improved
        final_strength = result.relationship_change["new_strength"]
        assert final_strength > initial_strength
        assert final_strength > 0.2  # Should be positive
    
    @pytest.mark.asyncio
    async def test_conflict_interaction_effects(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test effects of conflict interaction on relationship"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Build some relationship first
        await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="chat",
            content="Let's be friends!",
            context={}
        )
        
        # Now have a conflict
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="conflict",
            content="I completely disagree with everything you said!",
            context={}
        )
        
        assert result.success is True
        assert result.relationship_change["strength_delta"] < 0  # Relationship weakened
        assert result.relationship_change["trust_delta"] < 0  # Trust decreased
        
        # Check emotional state has negative emotions
        assert result.emotional_state["anger"] > 0.1 or result.emotional_state["sadness"] > 0.1
    
    @pytest.mark.asyncio
    async def test_personality_influenced_responses(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test that responses are influenced by character personality"""
        engine = CharacterInteractionEngine(test_db)
        alice = test_characters[0]  # High agreeableness
        bob = test_characters[1]    # Low agreeableness
        charlie = test_characters[2]  # High neuroticism
        
        # Alice to Bob (friendly to unfriendly)
        result_ab = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="greeting",
            content="Hello! How wonderful to see you!",
            context={}
        )
        
        # Alice to Charlie (friendly to anxious)
        result_ac = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=charlie.id,
            interaction_type="greeting",
            content="Hello! How wonderful to see you!",
            context={}
        )
        
        assert result_ab.success is True
        assert result_ac.success is True
        
        # Responses should be different based on personality
        assert result_ab.response != result_ac.response
        
        # Bob's response should be less enthusiastic
        assert "wonderful" not in result_ab.response.lower()
    
    @pytest.mark.asyncio
    async def test_metadata_tracking(self, test_db, test_characters, mock_redis, mock_graph_db):
        """Test that interaction metadata is properly tracked"""
        engine = CharacterInteractionEngine(test_db)
        alice, bob = test_characters[0], test_characters[1]
        
        # Process interaction
        result = await engine.process_interaction(
            initiator_id=alice.id,
            target_id=bob.id,
            interaction_type="collaboration",
            content="Let's work on this project together!",
            context={"project": "test_project", "priority": "high"}
        )
        
        assert result.success is True
        assert result.metadata is not None
        assert "interaction_type" in result.metadata
        assert "timestamp" in result.metadata
        assert "sentiment" in result.metadata
        assert result.metadata["interaction_type"] == "collaboration"