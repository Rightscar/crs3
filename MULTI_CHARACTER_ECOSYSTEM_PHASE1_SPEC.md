# Multi-Character Ecosystem - Phase 1 Technical Specification

## Overview

This document provides the detailed technical specification for Phase 1 of the Multi-Character Ecosystem implementation. Phase 1 focuses on establishing the foundational infrastructure and basic character interaction capabilities.

## Current State Analysis

Based on code analysis, LiteraryAI Studio already has:
- Basic character evolution tracking (`character_evolution_service.py`)
- Character behavior engine (`character_behavior_engine.py`)
- Emotional memory system (`emotional_memory_core.py`)
- Character fusion service (`character_fusion_service.py`)
- Database schema for character evolution
- Placeholder UI for multi-character interactions

This provides a strong foundation to build upon rather than starting from scratch.

## Phase 1 Objectives (Weeks 1-8)

### Primary Goals:
1. Extend existing character models to support multi-character awareness
2. Implement basic character-to-character interaction engine
3. Create relationship tracking and management system
4. Build foundational UI for character ecosystem observation
5. Establish event-driven architecture for real-time interactions

## Technical Architecture

### 1. Enhanced Character Model

Extend the existing character model to support ecosystem participation:

```python
# character-creator/core/models/character_ecosystem.py

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from datetime import datetime
import uuid

@dataclass
class EcosystemCharacter:
    """Extended character model for ecosystem participation"""
    
    # Existing character data
    character_id: str
    name: str
    source_document: str
    personality_profile: Dict[str, float]
    
    # New ecosystem-specific attributes
    ecosystem_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    active_status: bool = True
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    # Social attributes
    social_energy: float = 1.0  # 0-1, depletes with interactions
    interaction_capacity: int = 5  # Max concurrent interactions
    social_preferences: Dict[str, float] = field(default_factory=dict)
    
    # Relationship tracking
    relationships: Dict[str, 'CharacterRelationship'] = field(default_factory=dict)
    interaction_history: List['Interaction'] = field(default_factory=list)
    
    # Behavioral modifiers
    autonomy_level: float = 0.5  # 0-1, how independently they act
    initiative_threshold: float = 0.3  # Likelihood to initiate interactions
    
    def can_interact(self) -> bool:
        """Check if character has capacity for new interactions"""
        active_interactions = sum(1 for r in self.relationships.values() 
                                 if r.is_active)
        return (self.active_status and 
                self.social_energy > 0.1 and 
                active_interactions < self.interaction_capacity)
```

### 2. Relationship Model

Create a comprehensive relationship tracking system:

```python
# character-creator/core/models/relationships.py

@dataclass
class CharacterRelationship:
    """Model for character-to-character relationships"""
    
    relationship_id: str
    character_a_id: str
    character_b_id: str
    
    # Relationship metrics
    relationship_type: str  # friend, rival, neutral, romantic, mentor
    strength: float = 0.0  # -1 to 1 (hostile to devoted)
    trust: float = 0.5  # 0 to 1
    familiarity: float = 0.0  # 0 to 1
    
    # Interaction tracking
    total_interactions: int = 0
    last_interaction: Optional[datetime] = None
    interaction_frequency: float = 0.0  # interactions per day
    
    # Emotional context
    emotional_tone: str = "neutral"  # positive, negative, mixed
    shared_experiences: List[Dict[str, Any]] = field(default_factory=list)
    
    # Status flags
    is_active: bool = False
    is_blocked: bool = False
    
    def update_from_interaction(self, interaction: 'Interaction'):
        """Update relationship based on interaction outcome"""
        self.total_interactions += 1
        self.last_interaction = interaction.timestamp
        
        # Update metrics based on interaction sentiment
        sentiment_delta = interaction.sentiment_score
        self.strength = max(-1, min(1, self.strength + sentiment_delta * 0.1))
        
        # Trust changes more slowly
        if interaction.trust_impact:
            self.trust = max(0, min(1, self.trust + interaction.trust_impact * 0.05))
        
        # Familiarity always increases
        self.familiarity = min(1, self.familiarity + 0.02)
```

### 3. Interaction Engine

Build the core engine for character interactions:

```python
# character-creator/services/interaction_engine.py

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

class CharacterInteractionEngine:
    """Core engine for managing character-to-character interactions"""
    
    def __init__(self, llm_service, behavior_engine, emotion_engine):
        self.llm_service = llm_service
        self.behavior_engine = behavior_engine
        self.emotion_engine = emotion_engine
        self.active_interactions: Dict[str, 'ActiveInteraction'] = {}
        self.interaction_queue = asyncio.Queue()
        
    async def initiate_interaction(
        self,
        initiator: EcosystemCharacter,
        target: EcosystemCharacter,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional['Interaction']:
        """Initiate interaction between two characters"""
        
        # Validate interaction possibility
        if not self._can_interact(initiator, target):
            return None
            
        # Create interaction context
        interaction_context = self._build_interaction_context(
            initiator, target, context
        )
        
        # Generate interaction content
        interaction = await self._generate_interaction(
            initiator, target, interaction_context
        )
        
        # Process interaction effects
        await self._process_interaction_effects(interaction)
        
        # Queue for broadcasting
        await self.interaction_queue.put(interaction)
        
        return interaction
    
    def _can_interact(
        self, 
        char_a: EcosystemCharacter, 
        char_b: EcosystemCharacter
    ) -> bool:
        """Check if two characters can interact"""
        # Both must be active and have capacity
        if not (char_a.can_interact() and char_b.can_interact()):
            return False
            
        # Check if relationship is blocked
        rel_key = self._get_relationship_key(char_a.character_id, char_b.character_id)
        if rel_key in char_a.relationships:
            if char_a.relationships[rel_key].is_blocked:
                return False
                
        return True
    
    async def _generate_interaction(
        self,
        initiator: EcosystemCharacter,
        target: EcosystemCharacter,
        context: Dict[str, Any]
    ) -> 'Interaction':
        """Generate interaction content using LLM"""
        
        # Build prompts incorporating both characters
        system_prompt = self._build_system_prompt(initiator, target, context)
        
        # Generate initiator's action/dialogue
        initiator_prompt = f"""
        As {initiator.name}, you are initiating an interaction with {target.name}.
        Context: {json.dumps(context)}
        Your personality: {json.dumps(initiator.personality_profile)}
        Relationship status: {context.get('relationship_summary', 'first meeting')}
        
        Generate your action or dialogue:
        """
        
        initiator_content = await self.llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=initiator_prompt,
            temperature=0.8
        )
        
        # Generate target's response
        target_prompt = f"""
        As {target.name}, {initiator.name} has just said/done:
        "{initiator_content}"
        
        Your personality: {json.dumps(target.personality_profile)}
        How do you respond?
        """
        
        target_response = await self.llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=target_prompt,
            temperature=0.8
        )
        
        # Analyze interaction sentiment and impact
        sentiment = await self._analyze_sentiment(initiator_content, target_response)
        
        return Interaction(
            interaction_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            initiator_id=initiator.character_id,
            target_id=target.character_id,
            initiator_content=initiator_content,
            target_response=target_response,
            context=context,
            sentiment_score=sentiment['score'],
            trust_impact=sentiment.get('trust_impact', 0),
            emotional_impact=sentiment.get('emotional_impact', {})
        )
```

### 4. Social Dynamics Processor

Implement the relationship dynamics system:

```python
# character-creator/services/social_dynamics_processor.py

import networkx as nx
from typing import Dict, List, Set, Tuple
import numpy as np

class SocialDynamicsProcessor:
    """Process and analyze social dynamics in character ecosystem"""
    
    def __init__(self):
        self.social_graph = nx.Graph()
        self.compatibility_cache: Dict[Tuple[str, str], float] = {}
        
    def add_character(self, character: EcosystemCharacter):
        """Add character to social graph"""
        self.social_graph.add_node(
            character.character_id,
            character=character,
            centrality=0.0,
            influence=0.0,
            community=None
        )
        
    def update_relationship(
        self, 
        char_a_id: str, 
        char_b_id: str,
        relationship: CharacterRelationship
    ):
        """Update relationship in social graph"""
        # Add or update edge
        self.social_graph.add_edge(
            char_a_id,
            char_b_id,
            relationship=relationship,
            weight=abs(relationship.strength),
            sentiment=relationship.strength
        )
        
        # Recalculate network metrics
        self._update_network_metrics()
        
    def calculate_compatibility(
        self,
        char_a: EcosystemCharacter,
        char_b: EcosystemCharacter
    ) -> float:
        """Calculate compatibility between two characters"""
        
        cache_key = tuple(sorted([char_a.character_id, char_b.character_id]))
        if cache_key in self.compatibility_cache:
            return self.compatibility_cache[cache_key]
            
        # Personality compatibility (Big Five alignment)
        personality_compat = self._calculate_personality_compatibility(
            char_a.personality_profile,
            char_b.personality_profile
        )
        
        # Social preference compatibility
        social_compat = self._calculate_social_compatibility(
            char_a.social_preferences,
            char_b.social_preferences
        )
        
        # Historical compatibility (if they have history)
        historical_compat = self._calculate_historical_compatibility(
            char_a, char_b
        )
        
        # Weighted average
        compatibility = (
            personality_compat * 0.5 +
            social_compat * 0.3 +
            historical_compat * 0.2
        )
        
        self.compatibility_cache[cache_key] = compatibility
        return compatibility
    
    def identify_interaction_opportunities(
        self,
        ecosystem_characters: List[EcosystemCharacter]
    ) -> List[Tuple[str, str, float]]:
        """Identify promising character pairs for interaction"""
        
        opportunities = []
        
        for i, char_a in enumerate(ecosystem_characters):
            if not char_a.can_interact():
                continue
                
            for char_b in ecosystem_characters[i+1:]:
                if not char_b.can_interact():
                    continue
                    
                # Calculate interaction potential
                compatibility = self.calculate_compatibility(char_a, char_b)
                
                # Check existing relationship
                rel_key = self._get_relationship_key(
                    char_a.character_id, 
                    char_b.character_id
                )
                
                if rel_key in char_a.relationships:
                    relationship = char_a.relationships[rel_key]
                    # Boost potential for positive relationships
                    if relationship.strength > 0:
                        compatibility *= 1.2
                    # Reduce for recent interactions
                    if relationship.last_interaction:
                        hours_since = (
                            datetime.utcnow() - relationship.last_interaction
                        ).total_seconds() / 3600
                        if hours_since < 1:
                            compatibility *= 0.3
                
                opportunities.append((
                    char_a.character_id,
                    char_b.character_id,
                    compatibility
                ))
        
        # Sort by potential
        opportunities.sort(key=lambda x: x[2], reverse=True)
        return opportunities[:10]  # Top 10 opportunities
```

### 5. Event Streaming System

Implement real-time event broadcasting:

```python
# character-creator/services/event_streaming.py

import asyncio
from typing import Dict, List, Callable, Any
from datetime import datetime
import json

class CharacterEventStream:
    """Real-time event streaming for character interactions"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {
            'interaction': [],
            'relationship_change': [],
            'character_state': [],
            'story_event': []
        }
        self.event_history: List[Dict[str, Any]] = []
        self.active_streams: Dict[str, asyncio.Queue] = {}
        
    async def publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """Publish event to all subscribers"""
        
        event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': event_data
        }
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
        
        # Notify subscribers
        for subscriber in self.subscribers.get(event_type, []):
            try:
                await subscriber(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")
        
        # Push to active streams
        for stream_id, queue in self.active_streams.items():
            try:
                await queue.put(event)
            except asyncio.QueueFull:
                # Drop oldest event if queue is full
                try:
                    queue.get_nowait()
                    await queue.put(event)
                except:
                    pass
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].append(callback)
    
    async def create_stream(self, stream_id: str) -> asyncio.Queue:
        """Create new event stream for real-time updates"""
        queue = asyncio.Queue(maxsize=100)
        self.active_streams[stream_id] = queue
        return queue
    
    def close_stream(self, stream_id: str):
        """Close event stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
```

### 6. Character Observatory UI

Create the observation interface:

```python
# character-creator/ui/components/character_observatory.py

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

class CharacterObservatory:
    """UI component for observing character ecosystem"""
    
    def __init__(self, ecosystem_service, event_stream):
        self.ecosystem_service = ecosystem_service
        self.event_stream = event_stream
        
    def render(self):
        """Render the character observatory interface"""
        
        st.markdown("## 🔭 Character Observatory")
        
        # Main layout
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            self._render_character_list()
            
        with col2:
            self._render_interaction_view()
            
        with col3:
            self._render_relationship_metrics()
            
        # Bottom section
        self._render_activity_timeline()
        
    def _render_character_list(self):
        """Render active characters panel"""
        st.markdown("### Active Characters")
        
        characters = self.ecosystem_service.get_active_characters()
        
        for char in characters:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Character info with status indicator
                    status_emoji = "🟢" if char.can_interact() else "🔴"
                    st.markdown(f"{status_emoji} **{char.name}**")
                    
                    # Mini status bars
                    st.progress(
                        char.social_energy,
                        text=f"Energy: {char.social_energy:.0%}"
                    )
                    
                with col2:
                    # Quick actions
                    if st.button("👁️", key=f"view_{char.character_id}"):
                        st.session_state.selected_character = char.character_id
                        
    def _render_interaction_view(self):
        """Render current interactions"""
        st.markdown("### Live Interactions")
        
        # Create placeholder for real-time updates
        interaction_container = st.container()
        
        with interaction_container:
            # Get recent interactions
            recent = self.ecosystem_service.get_recent_interactions(limit=5)
            
            for interaction in recent:
                self._render_interaction_card(interaction)
                
        # Real-time update placeholder
        if st.button("🔄 Refresh"):
            st.experimental_rerun()
            
    def _render_relationship_metrics(self):
        """Render relationship network visualization"""
        st.markdown("### Relationship Network")
        
        # Get relationship graph data
        graph_data = self.ecosystem_service.get_relationship_graph()
        
        # Create network visualization
        fig = go.Figure()
        
        # Add nodes (characters)
        for node in graph_data['nodes']:
            fig.add_trace(go.Scatter(
                x=[node['x']],
                y=[node['y']],
                mode='markers+text',
                marker=dict(
                    size=20 + node['influence'] * 20,
                    color=node['community'],
                    colorscale='Viridis'
                ),
                text=node['name'],
                textposition="top center",
                hovertemplate=f"{node['name']}<br>Influence: {node['influence']:.2f}"
            ))
        
        # Add edges (relationships)
        for edge in graph_data['edges']:
            color = 'green' if edge['sentiment'] > 0 else 'red'
            width = abs(edge['sentiment']) * 5
            
            fig.add_trace(go.Scatter(
                x=[edge['x0'], edge['x1']],
                y=[edge['y0'], edge['y1']],
                mode='lines',
                line=dict(color=color, width=width),
                hovertemplate=f"Strength: {edge['sentiment']:.2f}"
            ))
        
        fig.update_layout(
            showlegend=False,
            hovermode='closest',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

### 7. Database Schema Updates

Extend the existing database schema:

```sql
-- Add to character-creator/core/database.py migrations

-- Character ecosystem participation
CREATE TABLE IF NOT EXISTS ecosystem_characters (
    character_id UUID PRIMARY KEY REFERENCES characters(id),
    ecosystem_id UUID NOT NULL,
    active_status BOOLEAN DEFAULT true,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    social_energy FLOAT DEFAULT 1.0,
    interaction_capacity INT DEFAULT 5,
    autonomy_level FLOAT DEFAULT 0.5,
    initiative_threshold FLOAT DEFAULT 0.3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Character relationships
CREATE TABLE IF NOT EXISTS character_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_a_id UUID REFERENCES characters(id),
    character_b_id UUID REFERENCES characters(id),
    relationship_type VARCHAR(50) DEFAULT 'neutral',
    strength FLOAT DEFAULT 0.0 CHECK (strength >= -1 AND strength <= 1),
    trust FLOAT DEFAULT 0.5 CHECK (trust >= 0 AND trust <= 1),
    familiarity FLOAT DEFAULT 0.0 CHECK (familiarity >= 0 AND familiarity <= 1),
    total_interactions INT DEFAULT 0,
    last_interaction TIMESTAMP,
    emotional_tone VARCHAR(50) DEFAULT 'neutral',
    is_active BOOLEAN DEFAULT false,
    is_blocked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_a_id, character_b_id)
);

-- Character interactions
CREATE TABLE IF NOT EXISTS character_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiator_id UUID REFERENCES characters(id),
    target_id UUID REFERENCES characters(id),
    interaction_type VARCHAR(50),
    initiator_content TEXT,
    target_response TEXT,
    context JSONB,
    sentiment_score FLOAT,
    trust_impact FLOAT,
    emotional_impact JSONB,
    story_significance FLOAT DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_ecosystem_active ON ecosystem_characters(ecosystem_id, active_status);
CREATE INDEX idx_relationships_characters ON character_relationships(character_a_id, character_b_id);
CREATE INDEX idx_interactions_timestamp ON character_interactions(timestamp DESC);
CREATE INDEX idx_interactions_participants ON character_interactions(initiator_id, target_id);
```

### 8. Integration Points

#### With Existing Services

```python
# character-creator/integrations/ecosystem_integration.py

class EcosystemIntegration:
    """Integration layer for ecosystem with existing services"""
    
    def __init__(self):
        # Existing services
        self.character_analyzer = CharacterAnalyzer()
        self.behavior_engine = CharacterBehaviorEngine
        self.evolution_service = CharacterEvolutionService()
        self.emotion_engine = EmotionalMemoryCore()
        
        # New ecosystem services
        self.interaction_engine = CharacterInteractionEngine(
            llm_service=self.llm_service,
            behavior_engine=self.behavior_engine,
            emotion_engine=self.emotion_engine
        )
        self.social_processor = SocialDynamicsProcessor()
        self.event_stream = CharacterEventStream()
        
    def upgrade_character_to_ecosystem(
        self, 
        character_id: str
    ) -> EcosystemCharacter:
        """Upgrade existing character to ecosystem participant"""
        
        # Load existing character
        char_data = self.character_analyzer.get_character(character_id)
        
        # Create ecosystem character
        eco_char = EcosystemCharacter(
            character_id=character_id,
            name=char_data['name'],
            source_document=char_data['source_document'],
            personality_profile=char_data['personality_profile']
        )
        
        # Initialize social preferences based on personality
        eco_char.social_preferences = self._derive_social_preferences(
            char_data['personality_profile']
        )
        
        # Add to ecosystem
        self.social_processor.add_character(eco_char)
        
        return eco_char
```

## Implementation Timeline

### Week 1-2: Infrastructure Setup
- [ ] Set up Neo4j for relationship graphs
- [ ] Implement event streaming with Redis Streams
- [ ] Create database migrations
- [ ] Set up development environment

### Week 3-4: Core Character System
- [ ] Implement EcosystemCharacter model
- [ ] Build CharacterRelationship model
- [ ] Create interaction data structures
- [ ] Integrate with existing character services

### Week 5-6: Interaction Engine
- [ ] Build CharacterInteractionEngine
- [ ] Implement interaction generation
- [ ] Create sentiment analysis
- [ ] Add interaction effects processing

### Week 7-8: UI and Integration
- [ ] Build Character Observatory UI
- [ ] Implement real-time updates
- [ ] Create relationship visualizations
- [ ] Integration testing

## Testing Strategy

### Unit Tests
```python
# tests/test_interaction_engine.py

import pytest
from services.interaction_engine import CharacterInteractionEngine

@pytest.mark.asyncio
async def test_character_interaction():
    """Test basic character interaction"""
    engine = CharacterInteractionEngine(
        llm_service=MockLLMService(),
        behavior_engine=MockBehaviorEngine(),
        emotion_engine=MockEmotionEngine()
    )
    
    char_a = create_test_character("Alice")
    char_b = create_test_character("Bob")
    
    interaction = await engine.initiate_interaction(char_a, char_b)
    
    assert interaction is not None
    assert interaction.initiator_id == char_a.character_id
    assert interaction.target_id == char_b.character_id
    assert len(interaction.initiator_content) > 0
    assert len(interaction.target_response) > 0
```

### Integration Tests
```python
# tests/test_ecosystem_integration.py

def test_ecosystem_workflow():
    """Test complete ecosystem workflow"""
    ecosystem = EcosystemIntegration()
    
    # Add characters
    char_a = ecosystem.upgrade_character_to_ecosystem("char_001")
    char_b = ecosystem.upgrade_character_to_ecosystem("char_002")
    
    # Test interaction
    interaction = ecosystem.initiate_interaction(char_a, char_b)
    
    # Verify relationship update
    relationship = ecosystem.get_relationship(char_a, char_b)
    assert relationship.total_interactions == 1
    
    # Verify event streaming
    events = ecosystem.get_recent_events()
    assert len(events) > 0
```

## Performance Considerations

### Optimization Strategies
1. **Caching**: Cache compatibility scores, relationship states
2. **Batch Processing**: Process multiple interactions in parallel
3. **Lazy Loading**: Load character details only when needed
4. **Event Throttling**: Limit event frequency for UI updates

### Scalability Targets
- Support 100+ active characters
- Handle 1000+ interactions per hour
- Sub-second response time for interactions
- Real-time UI updates with <100ms latency

## Security Considerations

### Data Protection
- Encrypt character relationship data
- Implement access controls for ecosystem management
- Audit trail for all character interactions

### Content Moderation
- Filter inappropriate interactions
- Flag concerning relationship patterns
- Admin tools for intervention

## Success Metrics

### Phase 1 KPIs
- Successfully process 95%+ of interaction requests
- Maintain character consistency score >90%
- UI responsiveness <200ms
- Zero data loss for interactions
- User satisfaction >4.0/5.0

## Next Steps

Upon completion of Phase 1:
1. User testing with beta group
2. Performance optimization based on metrics
3. Begin Phase 2: Advanced Social Dynamics
4. Iterate based on user feedback

This specification provides a solid foundation for implementing the Multi-Character Ecosystem while leveraging existing infrastructure and maintaining system stability.