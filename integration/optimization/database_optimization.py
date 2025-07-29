"""
Database optimization for character interaction system
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from backend.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Optimize database performance for character interactions"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
    
    async def create_optimized_indexes(self):
        """Create performance-critical indexes"""
        
        indexes = [
            # Character queries
            "CREATE INDEX IF NOT EXISTS idx_character_ecosystem_active ON characters(ecosystem_id, is_active) WHERE is_active = true",
            "CREATE INDEX IF NOT EXISTS idx_character_owner ON characters(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_character_social_energy ON characters(social_energy) WHERE is_active = true",
            
            # Relationship queries
            "CREATE INDEX IF NOT EXISTS idx_relationship_characters ON character_relationships(character_a_id, character_b_id)",
            "CREATE INDEX IF NOT EXISTS idx_relationship_strength ON character_relationships(strength)",
            "CREATE INDEX IF NOT EXISTS idx_relationship_type ON character_relationships(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_relationship_last_interaction ON character_relationships(last_interaction DESC)",
            
            # Message queries
            "CREATE INDEX IF NOT EXISTS idx_message_conversation ON messages(conversation_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_message_sender_type ON messages(sender_type, sender_id)",
            "CREATE INDEX IF NOT EXISTS idx_message_character ON messages(character_id, created_at DESC)",
            
            # Conversation queries
            "CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_character ON conversations(character_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversation_group ON conversations(is_group_chat)",
            
            # Ecosystem queries
            "CREATE INDEX IF NOT EXISTS idx_ecosystem_owner ON ecosystems(owner_id, is_active)",
            
            # Memory queries
            "CREATE INDEX IF NOT EXISTS idx_memory_character_type ON character_memories(character_id, memory_type)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON character_memories(importance DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_created ON character_memories(created_at DESC)",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_character_ecosystem_energy ON characters(ecosystem_id, social_energy DESC) WHERE is_active = true",
            "CREATE INDEX IF NOT EXISTS idx_relationship_interaction_count ON character_relationships(interaction_count DESC)",
        ]
        
        async with self.engine.begin() as conn:
            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
    
    async def analyze_tables(self):
        """Run ANALYZE on all tables for query planner optimization"""
        
        tables = [
            "users",
            "characters",
            "character_relationships",
            "messages",
            "conversations",
            "ecosystems",
            "character_memories",
            "documents"
        ]
        
        async with self.engine.begin() as conn:
            for table in tables:
                try:
                    await conn.execute(text(f"ANALYZE {table}"))
                    logger.info(f"Analyzed table: {table}")
                except Exception as e:
                    logger.error(f"Failed to analyze table {table}: {e}")
    
    async def optimize_query_performance(self):
        """Apply query performance optimizations"""
        
        optimizations = [
            # Increase work memory for complex queries
            "SET work_mem = '16MB'",
            
            # Optimize for read-heavy workload
            "SET random_page_cost = 1.1",
            
            # Enable parallel queries
            "SET max_parallel_workers_per_gather = 2",
            
            # Optimize join performance
            "SET join_collapse_limit = 12",
            
            # Enable JIT compilation for complex queries
            "SET jit = on",
            "SET jit_above_cost = 100000",
        ]
        
        async with self.engine.begin() as conn:
            for optimization in optimizations:
                try:
                    await conn.execute(text(optimization))
                    logger.info(f"Applied optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Could not apply optimization {optimization}: {e}")
    
    async def create_materialized_views(self):
        """Create materialized views for complex queries"""
        
        views = [
            # Character relationship summary
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS character_relationship_summary AS
            SELECT 
                c.id as character_id,
                c.name,
                c.ecosystem_id,
                COUNT(DISTINCT CASE WHEN cr.character_a_id = c.id THEN cr.character_b_id 
                                   ELSE cr.character_a_id END) as relationship_count,
                AVG(cr.strength) as avg_relationship_strength,
                AVG(cr.trust) as avg_trust,
                SUM(cr.interaction_count) as total_interactions
            FROM characters c
            LEFT JOIN character_relationships cr ON c.id IN (cr.character_a_id, cr.character_b_id)
            WHERE c.is_active = true
            GROUP BY c.id, c.name, c.ecosystem_id
            """,
            
            # Ecosystem activity summary
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS ecosystem_activity_summary AS
            SELECT 
                e.id as ecosystem_id,
                e.name as ecosystem_name,
                COUNT(DISTINCT c.id) as character_count,
                COUNT(DISTINCT cr.id) as relationship_count,
                SUM(c.interaction_count) as total_interactions,
                AVG(c.social_energy) as avg_social_energy
            FROM ecosystems e
            LEFT JOIN characters c ON e.id = c.ecosystem_id AND c.is_active = true
            LEFT JOIN character_relationships cr ON c.id IN (cr.character_a_id, cr.character_b_id)
            WHERE e.is_active = true
            GROUP BY e.id, e.name
            """,
        ]
        
        async with self.engine.begin() as conn:
            for view_sql in views:
                try:
                    await conn.execute(text(view_sql))
                    view_name = view_sql.split("VIEW IF NOT EXISTS ")[1].split(" AS")[0]
                    logger.info(f"Created materialized view: {view_name}")
                    
                    # Create index on materialized view
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{view_name}_id ON {view_name}(character_id)"))
                except Exception as e:
                    logger.error(f"Failed to create materialized view: {e}")
    
    async def setup_partitioning(self):
        """Setup table partitioning for large tables"""
        
        # Partition messages table by month
        partition_sql = """
        -- Create partitioned messages table
        CREATE TABLE IF NOT EXISTS messages_partitioned (
            LIKE messages INCLUDING ALL
        ) PARTITION BY RANGE (created_at);
        
        -- Create partitions for recent months
        CREATE TABLE IF NOT EXISTS messages_y2024m01 PARTITION OF messages_partitioned
            FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
        
        CREATE TABLE IF NOT EXISTS messages_y2024m02 PARTITION OF messages_partitioned
            FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
        
        -- Add more partitions as needed
        """
        
        # Note: In production, you'd migrate data and swap tables
        logger.info("Partitioning setup would be applied in production")
    
    async def optimize_all(self):
        """Run all optimizations"""
        logger.info("Starting database optimization...")
        
        await self.create_optimized_indexes()
        await self.analyze_tables()
        await self.optimize_query_performance()
        await self.create_materialized_views()
        await self.setup_partitioning()
        
        logger.info("Database optimization complete!")
    
    async def get_slow_queries(self):
        """Identify slow queries for optimization"""
        
        query = """
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            max_time
        FROM pg_stat_statements
        WHERE mean_time > 100  -- Queries averaging over 100ms
        ORDER BY mean_time DESC
        LIMIT 20
        """
        
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text(query))
                slow_queries = result.fetchall()
                
                logger.info("Slow queries identified:")
                for query in slow_queries:
                    logger.info(f"Query: {query[0][:100]}...")
                    logger.info(f"  Calls: {query[1]}, Avg: {query[3]:.2f}ms, Max: {query[4]:.2f}ms")
        except Exception as e:
            logger.warning(f"Could not fetch slow queries (pg_stat_statements may not be enabled): {e}")


async def main():
    """Run database optimizations"""
    optimizer = DatabaseOptimizer()
    await optimizer.optimize_all()
    await optimizer.get_slow_queries()


if __name__ == "__main__":
    asyncio.run(main())