"""
Error handling middleware
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Callable

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next: Callable):
    """
    Global error handler middleware
    """
    try:
        response = await call_next(request)
        return response
    except ValueError as e:
        logger.warning(f"Value error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(e),
                "type": "value_error"
            }
        )
    except PermissionError as e:
        logger.warning(f"Permission error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": str(e),
                "type": "permission_error"
            }
        )
    except FileNotFoundError as e:
        logger.warning(f"File not found: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": str(e),
                "type": "not_found"
            }
        )
    except Exception as e:
        # Log the full traceback for debugging
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return generic error to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred",
                "type": "internal_error"
            }
        )