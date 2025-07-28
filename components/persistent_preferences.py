"""
Persistent Preferences Component
================================

Manages user preferences that persist across sessions.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class PersistentPreferences:
    """
    Manages persistent user preferences stored in JSON file
    """
    
    def __init__(self, preferences_file: str = "user_preferences.json"):
        """
        Initialize persistent preferences
        
        Args:
            preferences_file: Path to preferences JSON file
        """
        self.preferences_file = Path(preferences_file)
        self.preferences_dir = Path("data/preferences")
        self.preferences_path = self.preferences_dir / self.preferences_file
        
        # Default preferences
        self.defaults = {
            'theme': 'light',
            'animations_enabled': True,
            'tooltips_enabled': True,
            'high_contrast': False,
            'font_size': 16,
            'color_blind_mode': 'normal',
            'auto_save': True,
            'show_line_numbers': True,
            'word_wrap': True,
            'tab_size': 4,
            'language': 'en',
            'timezone': 'UTC',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24h',
            'first_visit': True,
            'tour_completed': False,
            'last_version': None,
            'ui_density': 'normal',
            'sidebar_collapsed': False,
            'keyboard_shortcuts': True
        }
        
        # Ensure preferences directory exists
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing preferences
        self._preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Load preferences from file
        
        Returns:
            Dictionary of preferences
        """
        if self.preferences_path.exists():
            try:
                with open(self.preferences_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    preferences = self.defaults.copy()
                    preferences.update(loaded)
                    return preferences
            except Exception as e:
                logger.error(f"Failed to load preferences: {e}")
                return self.defaults.copy()
        else:
            return self.defaults.copy()
    
    def _save_preferences(self) -> bool:
        """
        Save preferences to file
        
        Returns:
            True if successful
        """
        try:
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get preference value
        
        Args:
            key: Preference key
            default: Default value if key doesn't exist
            
        Returns:
            Preference value or default
        """
        return self._preferences.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set preference value
        
        Args:
            key: Preference key
            value: Value to set
            
        Returns:
            True if successful
        """
        self._preferences[key] = value
        success = self._save_preferences()
        
        # Also update session state if available
        if hasattr(st, 'session_state'):
            st.session_state[f'pref_{key}'] = value
        
        return success
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update multiple preferences
        
        Args:
            updates: Dictionary of updates
            
        Returns:
            True if successful
        """
        self._preferences.update(updates)
        success = self._save_preferences()
        
        # Also update session state if available
        if hasattr(st, 'session_state'):
            for key, value in updates.items():
                st.session_state[f'pref_{key}'] = value
        
        return success
    
    def reset(self, key: Optional[str] = None) -> bool:
        """
        Reset preference(s) to default
        
        Args:
            key: Specific key to reset, or None to reset all
            
        Returns:
            True if successful
        """
        if key:
            if key in self.defaults:
                self._preferences[key] = self.defaults[key]
            else:
                logger.warning(f"Unknown preference key: {key}")
                return False
        else:
            self._preferences = self.defaults.copy()
        
        return self._save_preferences()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all preferences
        
        Returns:
            Dictionary of all preferences
        """
        return self._preferences.copy()
    
    def sync_with_session_state(self) -> None:
        """
        Sync preferences with Streamlit session state
        """
        if hasattr(st, 'session_state'):
            for key, value in self._preferences.items():
                st.session_state[f'pref_{key}'] = value
    
    def load_from_session_state(self) -> None:
        """
        Load preferences from session state
        """
        if hasattr(st, 'session_state'):
            updates = {}
            for key in st.session_state:
                if key.startswith('pref_'):
                    pref_key = key[5:]  # Remove 'pref_' prefix
                    if pref_key in self.defaults:
                        updates[pref_key] = st.session_state[key]
            
            if updates:
                self.update(updates)
    
    def export_preferences(self) -> str:
        """
        Export preferences as JSON string
        
        Returns:
            JSON string of preferences
        """
        return json.dumps(self._preferences, indent=2)
    
    def import_preferences(self, json_str: str) -> bool:
        """
        Import preferences from JSON string
        
        Args:
            json_str: JSON string of preferences
            
        Returns:
            True if successful
        """
        try:
            imported = json.loads(json_str)
            # Validate imported preferences
            valid_updates = {}
            for key, value in imported.items():
                if key in self.defaults:
                    valid_updates[key] = value
            
            if valid_updates:
                return self.update(valid_updates)
            else:
                logger.warning("No valid preferences found in import")
                return False
                
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            return False

# Global instance
preferences = PersistentPreferences()