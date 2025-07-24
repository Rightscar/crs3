"""Integration configuration management"""

from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path

@dataclass
class IntegrationConfig:
    """Configuration for module integration"""
    
    # Paths
    modules_path: Path = Path("/workspace/modules")
    character_creator_path: Path = Path("/workspace/character-creator")
    
    # Feature flags
    use_enhanced_ocr: bool = True
    use_intelligent_processor: bool = True
    use_gpt_dialogue: bool = True
    use_realtime_processing: bool = True
    
    # Performance
    enable_caching: bool = True
    cache_ttl: int = 3600
    max_concurrent_requests: int = 10
    
    # API Keys (from environment)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Document Processing
    max_file_size_mb: int = 100
    supported_formats: list = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [
                'pdf', 'docx', 'txt', 'md', 'epub', 
                'rtf', 'html', 'odt', 'tex'
            ]
        
        # Ensure paths exist
        self.modules_path = Path(self.modules_path)
        self.character_creator_path = Path(self.character_creator_path)
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            modules_path=Path(os.getenv("MODULES_PATH", "/workspace/modules")),
            character_creator_path=Path(os.getenv("CHARACTER_CREATOR_PATH", "/workspace/character-creator")),
            use_enhanced_ocr=os.getenv("USE_ENHANCED_OCR", "true").lower() == "true",
            use_intelligent_processor=os.getenv("USE_INTELLIGENT_PROCESSOR", "true").lower() == "true",
            use_gpt_dialogue=os.getenv("USE_GPT_DIALOGUE", "true").lower() == "true",
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100"))
        )

# Global configuration instance
integration_config = IntegrationConfig.from_env()