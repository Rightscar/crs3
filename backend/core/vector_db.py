"""
Pinecone vector database integration for character embeddings and memories
"""
import pinecone
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from datetime import datetime
import json
import openai

from core.config import settings

logger = logging.getLogger(__name__)


class VectorDB:
    """Pinecone vector database manager"""
    
    def __init__(self):
        """Initialize Pinecone connection"""
        # Initialize Pinecone
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENV
        )
        
        # Index names
        self.character_index_name = "character-embeddings"
        self.memory_index_name = "character-memories"
        
        # Embedding dimension (OpenAI ada-002)
        self.dimension = 1536
        
        # Initialize OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        
        # Create indexes if they don't exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist"""
        existing_indexes = pinecone.list_indexes()
        
        # Create character embeddings index
        if self.character_index_name not in existing_indexes:
            pinecone.create_index(
                self.character_index_name,
                dimension=self.dimension,
                metric='cosine',
                metadata_config={
                    "indexed": ["ecosystem_id", "character_name"]
                }
            )
            logger.info(f"Created index: {self.character_index_name}")
        
        # Create memory index
        if self.memory_index_name not in existing_indexes:
            pinecone.create_index(
                self.memory_index_name,
                dimension=self.dimension,
                metric='cosine',
                metadata_config={
                    "indexed": ["character_id", "memory_type", "importance"]
                }
            )
            logger.info(f"Created index: {self.memory_index_name}")
        
        # Get index references
        self.character_index = pinecone.Index(self.character_index_name)
        self.memory_index = pinecone.Index(self.memory_index_name)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = openai.Embedding.create(
                input=text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.dimension  # Return zero vector on error
    
    # Character Embedding Operations
    
    async def upsert_character_embedding(
        self,
        character_id: str,
        character_data: Dict[str, Any]
    ) -> bool:
        """Store or update character embedding"""
        try:
            # Create character description for embedding
            description = self._create_character_description(character_data)
            
            # Generate embedding
            embedding = await self.generate_embedding(description)
            
            # Prepare metadata
            metadata = {
                "character_id": character_id,
                "character_name": character_data.get("name", "Unknown"),
                "ecosystem_id": str(character_data.get("ecosystem_id", "")),
                "personality": json.dumps(character_data.get("personality_traits", {})),
                "description": character_data.get("description", "")[:500],  # Truncate for metadata limits
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert to Pinecone
            self.character_index.upsert(
                vectors=[(character_id, embedding, metadata)]
            )
            
            logger.info(f"Upserted character embedding: {character_data.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Error upserting character embedding: {e}")
            return False
    
    async def search_similar_characters(
        self,
        query: str,
        ecosystem_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar characters based on query"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare filter
            filter_dict = {}
            if ecosystem_id:
                filter_dict["ecosystem_id"] = ecosystem_id
            
            # Search
            results = self.character_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Format results
            similar_characters = []
            for match in results['matches']:
                similar_characters.append({
                    "character_id": match['id'],
                    "score": match['score'],
                    "character_name": match['metadata'].get('character_name'),
                    "ecosystem_id": match['metadata'].get('ecosystem_id'),
                    "description": match['metadata'].get('description'),
                    "personality": json.loads(match['metadata'].get('personality', '{}'))
                })
            
            return similar_characters
        except Exception as e:
            logger.error(f"Error searching similar characters: {e}")
            return []
    
    async def find_compatible_characters(
        self,
        character_id: str,
        ecosystem_id: str,
        compatibility_type: str = "friendship",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find compatible characters for relationships"""
        try:
            # Get character's embedding
            character_data = self.character_index.fetch([character_id])
            if not character_data['vectors']:
                return []
            
            character_embedding = character_data['vectors'][character_id]['values']
            
            # Adjust embedding based on compatibility type
            adjusted_embedding = self._adjust_embedding_for_compatibility(
                character_embedding,
                compatibility_type
            )
            
            # Search for compatible characters
            results = self.character_index.query(
                vector=adjusted_embedding,
                top_k=top_k + 1,  # +1 to exclude self
                include_metadata=True,
                filter={"ecosystem_id": ecosystem_id}
            )
            
            # Format results (exclude self)
            compatible = []
            for match in results['matches']:
                if match['id'] != character_id:
                    compatible.append({
                        "character_id": match['id'],
                        "compatibility_score": match['score'],
                        "character_name": match['metadata'].get('character_name'),
                        "personality": json.loads(match['metadata'].get('personality', '{}'))
                    })
            
            return compatible[:top_k]
        except Exception as e:
            logger.error(f"Error finding compatible characters: {e}")
            return []
    
    # Memory Operations
    
    async def store_character_memory(
        self,
        character_id: str,
        memory_content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store a character memory"""
        try:
            # Generate memory ID
            memory_id = f"{character_id}_{datetime.utcnow().timestamp()}"
            
            # Generate embedding
            embedding = await self.generate_embedding(memory_content)
            
            # Prepare metadata
            metadata = {
                "character_id": character_id,
                "memory_type": memory_type,
                "importance": importance,
                "content": memory_content[:500],  # Truncate for metadata limits
                "context": json.dumps(context or {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Upsert to Pinecone
            self.memory_index.upsert(
                vectors=[(memory_id, embedding, metadata)]
            )
            
            logger.info(f"Stored memory for character {character_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Error storing character memory: {e}")
            return None
    
    async def retrieve_memories(
        self,
        character_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a character"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare filter
            filter_dict = {
                "character_id": character_id,
                "importance": {"$gte": min_importance}
            }
            if memory_types:
                filter_dict["memory_type"] = {"$in": memory_types}
            
            # Search memories
            results = self.memory_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            memories = []
            for match in results['matches']:
                memories.append({
                    "memory_id": match['id'],
                    "relevance_score": match['score'],
                    "content": match['metadata'].get('content'),
                    "memory_type": match['metadata'].get('memory_type'),
                    "importance": match['metadata'].get('importance'),
                    "context": json.loads(match['metadata'].get('context', '{}')),
                    "created_at": match['metadata'].get('created_at')
                })
            
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def consolidate_memories(
        self,
        character_id: str,
        time_window_hours: int = 24
    ) -> Optional[str]:
        """Consolidate recent memories into a summary"""
        try:
            # Retrieve recent memories
            cutoff_time = datetime.utcnow().timestamp() - (time_window_hours * 3600)
            
            # Query all recent memories
            results = self.memory_index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=100,
                include_metadata=True,
                filter={
                    "character_id": character_id,
                    "created_at": {"$gte": cutoff_time}
                }
            )
            
            if not results['matches']:
                return None
            
            # Extract memory contents
            memory_contents = [
                match['metadata'].get('content', '')
                for match in results['matches']
            ]
            
            # Create summary (in production, use LLM for this)
            summary = f"Consolidated {len(memory_contents)} memories from the past {time_window_hours} hours."
            
            # Store consolidated memory
            consolidated_id = await self.store_character_memory(
                character_id=character_id,
                memory_content=summary,
                memory_type="semantic",
                importance=0.8,
                context={"source": "consolidation", "memory_count": len(memory_contents)}
            )
            
            return consolidated_id
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            return None
    
    # Utility Methods
    
    def _create_character_description(self, character_data: Dict[str, Any]) -> str:
        """Create a comprehensive character description for embedding"""
        parts = []
        
        # Name and basic description
        parts.append(f"Character: {character_data.get('name', 'Unknown')}")
        if desc := character_data.get('description'):
            parts.append(f"Description: {desc}")
        
        # Personality traits
        if traits := character_data.get('personality_traits'):
            trait_str = ", ".join([f"{k}: {v}" for k, v in traits.items()])
            parts.append(f"Personality: {trait_str}")
        
        # Behavioral patterns
        if patterns := character_data.get('behavioral_patterns'):
            parts.append(f"Behaviors: {', '.join(patterns[:5])}")
        
        # Speech patterns
        if speech := character_data.get('speech_patterns'):
            speech_str = ", ".join([f"{k}: {v}" for k, v in speech.items()])
            parts.append(f"Speech: {speech_str}")
        
        return " | ".join(parts)
    
    def _adjust_embedding_for_compatibility(
        self,
        embedding: List[float],
        compatibility_type: str
    ) -> List[float]:
        """Adjust embedding to find specific compatibility types"""
        # Convert to numpy for easier manipulation
        emb = np.array(embedding)
        
        # Apply transformations based on compatibility type
        if compatibility_type == "rivalry":
            # Invert some dimensions to find opposites
            emb[::2] = -emb[::2]  # Invert every other dimension
        elif compatibility_type == "romance":
            # Enhance emotional dimensions (hypothetical)
            emb[:100] *= 1.5  # Boost first 100 dimensions
        elif compatibility_type == "mentor":
            # Shift towards wisdom/experience (hypothetical)
            emb[500:600] *= 2.0  # Boost specific range
        
        # Normalize
        emb = emb / np.linalg.norm(emb)
        
        return emb.tolist()
    
    async def delete_character_data(self, character_id: str) -> bool:
        """Delete all data for a character"""
        try:
            # Delete from character index
            self.character_index.delete(ids=[character_id])
            
            # Delete memories (would need to query first in production)
            # For now, we'll need to implement batch deletion separately
            
            logger.info(f"Deleted character data: {character_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting character data: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics for vector indexes"""
        try:
            return {
                "character_embeddings": self.character_index.describe_index_stats(),
                "character_memories": self.memory_index.describe_index_stats()
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}