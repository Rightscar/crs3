"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import psutil
import platform
from datetime import datetime

from core.database import get_async_db, check_database_connection
from core.config import settings
from core.graph_db import GraphDB
from core.vector_db import VectorDB
from core.redis_client import redis_client

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, any]:
    """Detailed health check with all systems"""
    
    # Check PostgreSQL
    db_status = await check_database_connection()
    
    # Check Redis
    redis_status = False
    try:
        await redis_client.redis.ping()
        redis_status = True
    except:
        pass
    
    # Check Neo4j
    neo4j_status = False
    try:
        graph_db = GraphDB()
        neo4j_status = await graph_db.verify_connection()
        await graph_db.close()
    except:
        pass
    
    # Check Pinecone
    pinecone_status = False
    try:
        vector_db = VectorDB()
        stats = vector_db.get_index_stats()
        pinecone_status = bool(stats)
    except:
        pass
    
    # Get system info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Overall status
    all_healthy = all([db_status, redis_status, neo4j_status, pinecone_status])
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "postgresql": {
                "status": "up" if db_status else "down",
                "url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else "local"
            },
            "redis": {
                "status": "up" if redis_status else "down",
                "url": settings.REDIS_URL.split('@')[-1] if '@' in settings.REDIS_URL else "local"
            },
            "neo4j": {
                "status": "up" if neo4j_status else "down",
                "url": settings.NEO4J_URI.split('@')[-1] if '@' in settings.NEO4J_URI else "local"
            },
            "pinecone": {
                "status": "up" if pinecone_status else "down",
                "environment": settings.PINECONE_ENV
            }
        },
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            }
        }
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, bool]:
    """Kubernetes readiness probe"""
    db_status = await check_database_connection()
    
    return {
        "ready": db_status,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, bool]:
    """Kubernetes liveness probe"""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }