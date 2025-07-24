"""
Character Creator Configuration Settings
=======================================

Central configuration for the character creation system.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = DATA_DIR / "uploads"
CHARACTER_DIR = DATA_DIR / "characters"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
for directory in [DATA_DIR, UPLOAD_DIR, CHARACTER_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

@dataclass
class LLMConfig:
    """LLM Configuration"""
    primary_model: str = "gpt-3.5-turbo"
    fallback_model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-ada-002"
    max_tokens: int = 2000
    temperature: float = 0.8
    api_key: Optional[str] = None
    
    def __post_init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

@dataclass
class CharacterConfig:
    """Character System Configuration"""
    max_knowledge_chunks: int = 1000
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_dimension: int = 1536  # OpenAI ada-002
    
    # Personality dimensions
    personality_traits: List[str] = None
    
    def __post_init__(self):
        if self.personality_traits is None:
            self.personality_traits = [
                "openness",
                "conscientiousness", 
                "extraversion",
                "agreeableness",
                "neuroticism",
                "humor",
                "formality",
                "creativity"
            ]

@dataclass
class PerformanceConfig:
    """Performance Settings"""
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000
    response_timeout: int = 30
    max_concurrent_requests: int = 10
    enable_response_streaming: bool = True

@dataclass
class UIConfig:
    """UI Configuration"""
    theme: str = "dark"
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [
                ".pdf", ".txt", ".md", ".docx", 
                ".epub", ".rtf", ".html"
            ]

class Settings:
    """Main Settings Class"""
    
    def __init__(self):
        self.llm = LLMConfig()
        self.character = CharacterConfig()
        self.performance = PerformanceConfig()
        self.ui = UIConfig()
        
        # Database settings
        self.database_url = os.getenv(
            "DATABASE_URL", 
            f"sqlite:///{DATA_DIR}/character_creator.db"
        )
        
        # Security settings
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.enable_cors = os.getenv("ENABLE_CORS", "false").lower() == "true"
        
        # Feature flags
        self.features = {
            "enable_voice_synthesis": False,
            "enable_character_sharing": False,
            "enable_analytics": True,
            "enable_advanced_rag": True,
            "enable_personality_evolution": False
        }
        
        # Development settings
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def get_llm_config(self) -> Dict:
        """Get LLM configuration as dict"""
        return {
            "model": self.llm.primary_model,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "api_key": self.llm.api_key
        }
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.llm.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        if not UPLOAD_DIR.exists():
            raise ValueError(f"Upload directory {UPLOAD_DIR} does not exist")
        
        return True

# Global settings instance
settings = Settings()

# Validate on import
if __name__ != "__main__":
    try:
        settings.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")