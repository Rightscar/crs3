"""
Neo4j graph database integration for character relationships
"""
from neo4j import AsyncGraphDatabase, AsyncSession
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import json

from core.config import settings

logger = logging.getLogger(__name__)


class GraphDB:
    """Neo4j graph database manager"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    async def close(self):
        """Close database connection"""
        await self.driver.close()
    
    async def verify_connection(self) -> bool:
        """Verify Neo4j connection"""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                test = await result.single()
                return test["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False
    
    # Character Node Operations
    
    async def create_character_node(self, character_data: Dict[str, Any]) -> bool:
        """Create a character node in the graph"""
        async with self.driver.session() as session:
            try:
                query = """
                MERGE (c:Character {id: $id})
                SET c.name = $name,
                    c.ecosystem_id = $ecosystem_id,
                    c.personality = $personality,
                    c.created_at = $created_at,
                    c.updated_at = $updated_at
                RETURN c
                """
                await session.run(
                    query,
                    id=str(character_data["id"]),
                    name=character_data["name"],
                    ecosystem_id=str(character_data.get("ecosystem_id", "")),
                    personality=json.dumps(character_data.get("personality_traits", {})),
                    created_at=character_data.get("created_at", datetime.utcnow()).isoformat(),
                    updated_at=datetime.utcnow().isoformat()
                )
                logger.info(f"Created character node: {character_data['name']}")
                return True
            except Exception as e:
                logger.error(f"Error creating character node: {e}")
                return False
    
    async def update_character_node(self, character_id: str, updates: Dict[str, Any]) -> bool:
        """Update character node properties"""
        async with self.driver.session() as session:
            try:
                set_clauses = []
                params = {"id": character_id}
                
                for key, value in updates.items():
                    if key not in ["id"]:  # Don't update ID
                        set_clauses.append(f"c.{key} = ${key}")
                        params[key] = value if not isinstance(value, dict) else json.dumps(value)
                
                if not set_clauses:
                    return True
                
                query = f"""
                MATCH (c:Character {{id: $id}})
                SET {', '.join(set_clauses)}, c.updated_at = $updated_at
                RETURN c
                """
                params["updated_at"] = datetime.utcnow().isoformat()
                
                result = await session.run(query, **params)
                return await result.single() is not None
            except Exception as e:
                logger.error(f"Error updating character node: {e}")
                return False
    
    async def delete_character_node(self, character_id: str) -> bool:
        """Delete character node and all its relationships"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (c:Character {id: $id})
                DETACH DELETE c
                """
                await session.run(query, id=character_id)
                return True
            except Exception as e:
                logger.error(f"Error deleting character node: {e}")
                return False
    
    # Relationship Operations
    
    async def create_relationship(
        self,
        character_a_id: str,
        character_b_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create or update relationship between characters"""
        async with self.driver.session() as session:
            try:
                # Prepare properties
                props = properties or {}
                props["created_at"] = props.get("created_at", datetime.utcnow().isoformat())
                props["updated_at"] = datetime.utcnow().isoformat()
                props["strength"] = props.get("strength", 0.5)
                props["trust"] = props.get("trust", 0.5)
                props["familiarity"] = props.get("familiarity", 0.0)
                
                # Create relationship (bidirectional)
                query = f"""
                MATCH (a:Character {{id: $id_a}})
                MATCH (b:Character {{id: $id_b}})
                MERGE (a)-[r:{relationship_type.upper()}]-(b)
                SET r += $properties
                RETURN r
                """
                
                await session.run(
                    query,
                    id_a=character_a_id,
                    id_b=character_b_id,
                    properties=props
                )
                
                logger.info(f"Created {relationship_type} relationship between {character_a_id} and {character_b_id}")
                return True
            except Exception as e:
                logger.error(f"Error creating relationship: {e}")
                return False
    
    async def update_relationship(
        self,
        character_a_id: str,
        character_b_id: str,
        relationship_type: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing relationship properties"""
        async with self.driver.session() as session:
            try:
                updates["updated_at"] = datetime.utcnow().isoformat()
                
                query = f"""
                MATCH (a:Character {{id: $id_a}})-[r:{relationship_type.upper()}]-(b:Character {{id: $id_b}})
                SET r += $updates
                RETURN r
                """
                
                result = await session.run(
                    query,
                    id_a=character_a_id,
                    id_b=character_b_id,
                    updates=updates
                )
                
                return await result.single() is not None
            except Exception as e:
                logger.error(f"Error updating relationship: {e}")
                return False
    
    async def delete_relationship(
        self,
        character_a_id: str,
        character_b_id: str,
        relationship_type: Optional[str] = None
    ) -> bool:
        """Delete relationship between characters"""
        async with self.driver.session() as session:
            try:
                if relationship_type:
                    query = f"""
                    MATCH (a:Character {{id: $id_a}})-[r:{relationship_type.upper()}]-(b:Character {{id: $id_b}})
                    DELETE r
                    """
                else:
                    # Delete all relationships between the two characters
                    query = """
                    MATCH (a:Character {id: $id_a})-[r]-(b:Character {id: $id_b})
                    DELETE r
                    """
                
                await session.run(query, id_a=character_a_id, id_b=character_b_id)
                return True
            except Exception as e:
                logger.error(f"Error deleting relationship: {e}")
                return False
    
    # Query Operations
    
    async def get_character_relationships(self, character_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a character"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (c:Character {id: $id})-[r]-(other:Character)
                RETURN type(r) as relationship_type,
                       properties(r) as properties,
                       other.id as other_id,
                       other.name as other_name,
                       other.ecosystem_id as ecosystem_id
                """
                
                result = await session.run(query, id=character_id)
                relationships = []
                
                async for record in result:
                    relationships.append({
                        "character_id": record["other_id"],
                        "character_name": record["other_name"],
                        "ecosystem_id": record["ecosystem_id"],
                        "relationship_type": record["relationship_type"],
                        "properties": dict(record["properties"])
                    })
                
                return relationships
            except Exception as e:
                logger.error(f"Error getting character relationships: {e}")
                return []
    
    async def find_shortest_path(self, character_a_id: str, character_b_id: str) -> Optional[List[str]]:
        """Find shortest path between two characters"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH path = shortestPath((a:Character {id: $id_a})-[*]-(b:Character {id: $id_b}))
                RETURN [n in nodes(path) | n.id] as path
                """
                
                result = await session.run(query, id_a=character_a_id, id_b=character_b_id)
                record = await result.single()
                
                return record["path"] if record else None
            except Exception as e:
                logger.error(f"Error finding shortest path: {e}")
                return None
    
    async def get_ecosystem_network(self, ecosystem_id: str) -> Dict[str, Any]:
        """Get entire network for an ecosystem"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (c:Character {ecosystem_id: $ecosystem_id})
                OPTIONAL MATCH (c)-[r]-(other:Character {ecosystem_id: $ecosystem_id})
                RETURN collect(DISTINCT c) as characters,
                       collect(DISTINCT {
                           source: c.id,
                           target: other.id,
                           type: type(r),
                           properties: properties(r)
                       }) as relationships
                """
                
                result = await session.run(query, ecosystem_id=ecosystem_id)
                record = await result.single()
                
                if not record:
                    return {"characters": [], "relationships": []}
                
                characters = [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "personality": json.loads(c.get("personality", "{}"))
                    }
                    for c in record["characters"]
                ]
                
                relationships = [
                    rel for rel in record["relationships"]
                    if rel["target"] is not None  # Filter out null relationships
                ]
                
                return {
                    "characters": characters,
                    "relationships": relationships
                }
            except Exception as e:
                logger.error(f"Error getting ecosystem network: {e}")
                return {"characters": [], "relationships": []}
    
    async def calculate_influence_score(self, character_id: str) -> float:
        """Calculate influence score based on relationships"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (c:Character {id: $id})
                OPTIONAL MATCH (c)-[r]-(other:Character)
                WITH c, count(r) as relationship_count,
                     avg(r.strength) as avg_strength,
                     avg(r.trust) as avg_trust
                RETURN relationship_count * COALESCE(avg_strength, 0.5) * COALESCE(avg_trust, 0.5) as influence
                """
                
                result = await session.run(query, id=character_id)
                record = await result.single()
                
                return record["influence"] if record else 0.0
            except Exception as e:
                logger.error(f"Error calculating influence score: {e}")
                return 0.0
    
    async def find_communities(self, ecosystem_id: str) -> List[List[str]]:
        """Find character communities using Louvain algorithm"""
        async with self.driver.session() as session:
            try:
                # Note: This requires Neo4j Graph Data Science library
                query = """
                CALL gds.graph.project.cypher(
                    'ecosystem-' + $ecosystem_id,
                    'MATCH (c:Character {ecosystem_id: $ecosystem_id}) RETURN id(c) as id',
                    'MATCH (a:Character {ecosystem_id: $ecosystem_id})-[r]-(b:Character {ecosystem_id: $ecosystem_id})
                     RETURN id(a) as source, id(b) as target, r.strength as weight'
                )
                YIELD graphName
                
                CALL gds.louvain.stream(graphName)
                YIELD nodeId, communityId
                
                MATCH (c:Character) WHERE id(c) = nodeId
                RETURN communityId, collect(c.id) as members
                ORDER BY communityId
                """
                
                result = await session.run(query, ecosystem_id=ecosystem_id)
                communities = []
                
                async for record in result:
                    communities.append(record["members"])
                
                # Clean up the projection
                await session.run(f"CALL gds.graph.drop('ecosystem-{ecosystem_id}')")
                
                return communities
            except Exception as e:
                logger.warning(f"Community detection failed (GDS may not be installed): {e}")
                # Fallback to simple connected components
                return await self._find_connected_components(ecosystem_id)
    
    async def _find_connected_components(self, ecosystem_id: str) -> List[List[str]]:
        """Find connected components as a fallback for community detection"""
        async with self.driver.session() as session:
            try:
                query = """
                MATCH (c:Character {ecosystem_id: $ecosystem_id})
                OPTIONAL MATCH path = (c)-[*]-(connected:Character {ecosystem_id: $ecosystem_id})
                WITH c, collect(DISTINCT connected) + [c] as component
                WITH component, size(component) as size
                ORDER BY size DESC
                RETURN [n in component | n.id] as members
                """
                
                result = await session.run(query, ecosystem_id=ecosystem_id)
                components = []
                seen = set()
                
                async for record in result:
                    members = record["members"]
                    # Skip if we've seen any member (to avoid duplicates)
                    if not any(m in seen for m in members):
                        components.append(members)
                        seen.update(members)
                
                return components
            except Exception as e:
                logger.error(f"Error finding connected components: {e}")
                return []