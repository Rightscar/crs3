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
    """Detailed health check with system information"""
    
    # Check database
    db_status = await check_database_connection()
    
    # Get system info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if db_status else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_status,
            "url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else "local"
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