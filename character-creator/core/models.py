"""
Core Data Models
================

Data models for the character creation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
import json
from enum import Enum

class CharacterStatus(Enum):
    """Character status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

class PersonalityTrait(Enum):
    """Personality trait dimensions"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"
    HUMOR = "humor"
    FORMALITY = "formality"
    CREATIVITY = "creativity"

@dataclass
class DocumentReference:
    """Reference to source document"""
    id: str = field(default_factory=lambda: str(uuid4()))
    filename: str = ""
    filepath: str = ""
    content_hash: str = ""
    total_pages: int = 0
    word_count: int = 0
    uploaded_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersonalityProfile:
    """Character personality profile"""
    traits: Dict[str, float] = field(default_factory=dict)  # trait_name -> value (0-1)
    voice_attributes: Dict[str, Any] = field(default_factory=dict)
    speaking_style: str = "neutral"
    vocabulary_level: str = "medium"  # simple, medium, advanced
    quirks: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)
    emotional_range: float = 0.5  # 0 = stoic, 1 = very emotional
    
    def to_prompt_string(self) -> str:
        """Convert personality to prompt instructions"""
        traits_str = ", ".join([
            f"{trait}: {value:.1f}/1.0" 
            for trait, value in self.traits.items()
        ])
        
        return f"""
Personality Traits: {traits_str}
Speaking Style: {self.speaking_style}
Vocabulary Level: {self.vocabulary_level}
Emotional Range: {self.emotional_range:.1f}/1.0
Quirks: {', '.join(self.quirks) if self.quirks else 'None'}
Catchphrases: {', '.join(self.catchphrases) if self.catchphrases else 'None'}
"""

@dataclass
class KnowledgeChunk:
    """Single chunk of knowledge"""
    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_page: Optional[int] = None
    importance_score: float = 0.5
    topics: List[str] = field(default_factory=list)

@dataclass
class KnowledgeBase:
    """Character's knowledge base"""
    chunks: List[KnowledgeChunk] = field(default_factory=list)
    total_chunks: int = 0
    embedding_model: str = "text-embedding-ada-002"
    index_type: str = "flat"  # flat, hnsw, annoy
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_chunk(self, chunk: KnowledgeChunk):
        """Add a knowledge chunk"""
        self.chunks.append(chunk)
        self.total_chunks += 1
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """Get chunk by ID"""
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                return chunk
        return None

@dataclass
class ConversationTurn:
    """Single conversation turn"""
    id: str = field(default_factory=lambda: str(uuid4()))
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_used: Optional[List[str]] = None  # chunk IDs used

@dataclass
class ConversationMemory:
    """Character's conversation memory"""
    short_term: List[ConversationTurn] = field(default_factory=list)
    long_term_facts: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    emotional_state: Dict[str, float] = field(default_factory=dict)
    relationship_level: float = 0.0  # 0 = stranger, 1 = close friend
    
    def add_turn(self, turn: ConversationTurn):
        """Add conversation turn to memory"""
        self.short_term.append(turn)
        # Keep only last 20 turns in short term
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]
    
    def get_recent_context(self, n: int = 5) -> List[ConversationTurn]:
        """Get recent conversation context"""
        return self.short_term[-n:] if len(self.short_term) >= n else self.short_term

@dataclass
class Character:
    """Main character model"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    avatar: str = "🤖"
    
    # Core components
    source_document: Optional[DocumentReference] = None
    personality: PersonalityProfile = field(default_factory=PersonalityProfile)
    knowledge_base: KnowledgeBase = field(default_factory=KnowledgeBase)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    
    # Configuration
    temperature: float = 0.8
    max_tokens: int = 500
    model_preference: str = "gpt-3.5-turbo"
    
    # Metadata
    status: CharacterStatus = CharacterStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Stats
    total_conversations: int = 0
    total_messages: int = 0
    average_rating: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "avatar": self.avatar,
            "source_document": self.source_document.__dict__ if self.source_document else None,
            "personality": {
                "traits": self.personality.traits,
                "voice_attributes": self.personality.voice_attributes,
                "speaking_style": self.personality.speaking_style,
                "vocabulary_level": self.personality.vocabulary_level,
                "quirks": self.personality.quirks,
                "catchphrases": self.personality.catchphrases,
                "emotional_range": self.personality.emotional_range
            },
            "knowledge_base": {
                "total_chunks": self.knowledge_base.total_chunks,
                "embedding_model": self.knowledge_base.embedding_model,
                "metadata": self.knowledge_base.metadata
            },
            "configuration": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "model_preference": self.model_preference
            },
            "metadata": {
                "status": self.status.value,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "created_by": self.created_by,
                "tags": self.tags
            },
            "stats": {
                "total_conversations": self.total_conversations,
                "total_messages": self.total_messages,
                "average_rating": self.average_rating
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Create from dictionary"""
        character = cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            avatar=data.get("avatar", "🤖")
        )
        
        # Load components
        if data.get("source_document"):
            character.source_document = DocumentReference(**data["source_document"])
        
        if data.get("personality"):
            p = data["personality"]
            character.personality = PersonalityProfile(
                traits=p.get("traits", {}),
                voice_attributes=p.get("voice_attributes", {}),
                speaking_style=p.get("speaking_style", "neutral"),
                vocabulary_level=p.get("vocabulary_level", "medium"),
                quirks=p.get("quirks", []),
                catchphrases=p.get("catchphrases", []),
                emotional_range=p.get("emotional_range", 0.5)
            )
        
        # Load configuration
        if data.get("configuration"):
            c = data["configuration"]
            character.temperature = c.get("temperature", 0.8)
            character.max_tokens = c.get("max_tokens", 500)
            character.model_preference = c.get("model_preference", "gpt-3.5-turbo")
        
        # Load metadata
        if data.get("metadata"):
            m = data["metadata"]
            character.status = CharacterStatus(m.get("status", "draft"))
            character.created_at = datetime.fromisoformat(m.get("created_at", datetime.now().isoformat()))
            character.updated_at = datetime.fromisoformat(m.get("updated_at", datetime.now().isoformat()))
            character.created_by = m.get("created_by")
            character.tags = m.get("tags", [])
        
        # Load stats
        if data.get("stats"):
            s = data["stats"]
            character.total_conversations = s.get("total_conversations", 0)
            character.total_messages = s.get("total_messages", 0)
            character.average_rating = s.get("average_rating", 0.0)
        
        return character
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for LLM"""
        return f"""You are {self.name}. {self.description}

{self.personality.to_prompt_string()}

Important: Stay in character at all times. Respond as {self.name} would, using their personality, knowledge, and speaking style.
"""