"""
Event Stream Service - Handles real-time event publishing and subscription
"""
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import json
import asyncio
import logging

from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class CharacterEventStream:
    """
    Manages real-time event streaming for character interactions and ecosystem updates
    """
    
    def __init__(self):
        self.redis = redis_client
        self.subscriptions = {}
        
    async def emit_interaction_event(self, event_data: Dict[str, Any]):
        """
        Emit a character interaction event
        
        Args:
            event_data: Event data containing interaction details
        """
        try:
            ecosystem_id = event_data.get('ecosystem_id')
            if not ecosystem_id:
                logger.error("No ecosystem_id in event data")
                return
            
            # Add event metadata
            event = {
                'id': str(uuid4()),
                'type': 'character_interaction',
                'timestamp': datetime.utcnow().isoformat(),
                'data': event_data
            }
            
            # Publish to ecosystem channel
            channel = f"ecosystem:{ecosystem_id}:events"
            await self.redis.publish(channel, event)
            
            # Also publish to global channel for monitoring
            await self.redis.publish("global:character_events", event)
            
            logger.info(f"Emitted interaction event to {channel}")
            
        except Exception as e:
            logger.error(f"Error emitting interaction event: {str(e)}")
    
    async def emit_relationship_change(
        self,
        ecosystem_id: str,
        character_a_id: str,
        character_b_id: str,
        change_data: Dict[str, Any]
    ):
        """Emit a relationship change event"""
        event = {
            'id': str(uuid4()),
            'type': 'relationship_change',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'ecosystem_id': ecosystem_id,
                'character_a_id': character_a_id,
                'character_b_id': character_b_id,
                'changes': change_data
            }
        }
        
        channel = f"ecosystem:{ecosystem_id}:events"
        await self.redis.publish(channel, event)
    
    async def emit_character_state_change(
        self,
        ecosystem_id: str,
        character_id: str,
        state_changes: Dict[str, Any]
    ):
        """Emit a character state change event"""
        event = {
            'id': str(uuid4()),
            'type': 'character_state_change',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'ecosystem_id': ecosystem_id,
                'character_id': character_id,
                'changes': state_changes
            }
        }
        
        channel = f"ecosystem:{ecosystem_id}:events"
        await self.redis.publish(channel, event)
    
    async def emit_scenario_event(
        self,
        ecosystem_id: str,
        scenario_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Emit a scenario-related event"""
        event = {
            'id': str(uuid4()),
            'type': f'scenario_{event_type}',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'ecosystem_id': ecosystem_id,
                'scenario_id': scenario_id,
                **event_data
            }
        }
        
        channel = f"ecosystem:{ecosystem_id}:events"
        await self.redis.publish(channel, event)
    
    async def subscribe_to_ecosystem(
        self,
        ecosystem_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """
        Subscribe to ecosystem events
        
        Args:
            ecosystem_id: ID of the ecosystem to subscribe to
            callback: Function to call when events are received
            
        Returns:
            Subscription ID
        """
        channel = f"ecosystem:{ecosystem_id}:events"
        subscription_id = str(uuid4())
        
        await self.redis.subscribe(channel, callback)
        self.subscriptions[subscription_id] = {
            'channel': channel,
            'callback': callback,
            'ecosystem_id': ecosystem_id
        }
        
        logger.info(f"Subscribed to {channel} with ID {subscription_id}")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        if subscription_id in self.subscriptions:
            sub_info = self.subscriptions[subscription_id]
            await self.redis.unsubscribe(sub_info['channel'])
            del self.subscriptions[subscription_id]
            logger.info(f"Unsubscribed from {sub_info['channel']}")
    
    async def get_recent_events(
        self,
        ecosystem_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent events for an ecosystem
        
        Args:
            ecosystem_id: ID of the ecosystem
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        # This would typically query from a persistent event store
        # For now, we'll return an empty list as events are ephemeral in Redis pub/sub
        # In production, events should be stored in a database or event store
        return []
    
    async def emit_bulk_events(self, events: List[Dict[str, Any]]):
        """Emit multiple events efficiently"""
        for event in events:
            ecosystem_id = event.get('ecosystem_id')
            if ecosystem_id:
                await self.emit_interaction_event(event)
    
    def format_activity_message(self, event_data: Dict[str, Any]) -> str:
        """Format event data into a human-readable activity message"""
        event_type = event_data.get('type', 'unknown')
        
        if event_type == 'character_interaction':
            data = event_data.get('data', {})
            participants = data.get('participants', [])
            if len(participants) >= 2:
                initiator = participants[0]['name']
                responder = participants[1]['name']
                interaction_type = data.get('interaction_type', 'interacted with')
                
                # Format based on interaction type
                if interaction_type == 'greeting':
                    return f"🤝 {initiator} greeted {responder}"
                elif interaction_type == 'conflict':
                    return f"⚔️ {initiator} had a conflict with {responder}"
                elif interaction_type == 'collaboration':
                    return f"🤝 {initiator} is collaborating with {responder}"
                else:
                    return f"💬 {initiator} is chatting with {responder}"
        
        elif event_type == 'relationship_change':
            data = event_data.get('data', {})
            changes = data.get('changes', {})
            if changes.get('strength_delta', 0) > 0:
                return f"💕 Relationship strengthened"
            elif changes.get('strength_delta', 0) < 0:
                return f"💔 Relationship weakened"
        
        elif event_type == 'character_state_change':
            data = event_data.get('data', {})
            changes = data.get('changes', {})
            if 'social_energy' in changes:
                return f"🔋 Character energy changed"
            elif 'emotional_state' in changes:
                return f"😊 Character mood changed"
        
        return f"📍 {event_type.replace('_', ' ').title()}"