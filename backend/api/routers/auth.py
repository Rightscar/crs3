"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import timedelta

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)
from core.config import settings

router = APIRouter()


# Mock user database (replace with real database in production)
fake_users_db = {
    "testuser": {
        "id": "user_001",
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpass123"),
        "is_active": True,
        "is_superuser": False
    },
    "admin": {
        "id": "user_admin",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "is_active": True,
        "is_superuser": True
    }
}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, str]:
    """
    OAuth2 compatible token login
    
    - **username**: User's username
    - **password**: User's password
    """
    # Authenticate user
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user["id"],
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user["id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str) -> Dict[str, str]:
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user_id,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user information"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "is_active": current_user["is_active"],
        "is_superuser": current_user.get("is_superuser", False)
    }


@router.post("/register")
async def register(
    username: str,
    email: str,
    password: str
) -> Dict[str, str]:
    """
    Register a new user
    
    - **username**: Unique username
    - **email**: User's email
    - **password**: User's password (min 8 characters)
    """
    # Check if user exists
    if username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Validate password
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Create user (in real app, save to database)
    user_id = f"user_{len(fake_users_db) + 1}"
    fake_users_db[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "hashed_password": get_password_hash(password),
        "is_active": True,
        "is_superuser": False
    }
    
    return {
        "message": "User created successfully",
        "user_id": user_id
    }


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Logout current user
    
    Note: Since we're using JWT tokens, logout is handled client-side
    by removing the token. This endpoint can be used for logging purposes.
    """
    # In a real application, you might want to:
    # - Add the token to a blacklist
    # - Log the logout event
    # - Clear server-side sessions if any
    
    return {
        "message": "Successfully logged out",
        "user_id": current_user["id"]
    }