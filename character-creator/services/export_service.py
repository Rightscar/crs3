"""
Export Service
==============

Service for exporting characters and training data.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from integrations.adapters.export_adapter import ExportAdapter
from integrations.adapters.analytics_adapter import AnalyticsAdapter
from core.database import DatabaseManager
from config.logging_config import logger
from core.exceptions import StorageError


class ExportService:
    """Service for exporting character data"""
    
    def __init__(self):
        """Initialize export service"""
        self.export_adapter = ExportAdapter()
        self.analytics_adapter = AnalyticsAdapter()
        self.db = DatabaseManager()
    
    def export_character(
        self,
        character_id: str,
        format: str = 'json',
        include_analytics: bool = False
    ) -> Dict[str, Any]:
        """
        Export a character in specified format
        
        Args:
            character_id: Character ID to export
            format: Export format (json, jsonl, pdf, docx, csv)
            include_analytics: Include analytics data
            
        Returns:
            Export result with file path
        """
        try:
            # Get character from database
            character = self.db.get_character(character_id)
            if not character:
                raise StorageError(f"Character {character_id} not found")
            
            # Include analytics if requested
            if include_analytics:
                analytics = self.analytics_adapter.get_character_analytics(character_id)
                character['analytics'] = analytics
            
            # Export character
            result = self.export_adapter.export_character(
                character,
                format=format
            )
            
            # Track export event
            self.analytics_adapter.track_event(
                'character_exported',
                {
                    'character_id': character_id,
                    'format': format,
                    'include_analytics': include_analytics
                }
            )
            
            logger.info(f"Exported character {character_id} as {format}")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting character: {e}")
            raise StorageError(f"Failed to export character: {str(e)}")
    
    def export_all_characters(
        self,
        format: str = 'json',
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all characters or filtered set
        
        Args:
            format: Export format
            search_query: Optional search filter
            
        Returns:
            Export result
        """
        try:
            # Get characters from database
            if search_query:
                characters = self.db.search_characters(search_query)
            else:
                characters = self.db.list_characters()
            
            if not characters:
                return {
                    'success': False,
                    'error': 'No characters found'
                }
            
            # Export based on format
            if format in ['json', 'jsonl']:
                # Bulk export
                timestamp = Path('exports') / f'all_characters_{format}'
                timestamp.parent.mkdir(exist_ok=True)
                
                export_results = []
                for char in characters:
                    result = self.export_adapter.export_character(
                        char,
                        format=format
                    )
                    export_results.append(result)
                
                return {
                    'success': True,
                    'exported_count': len(export_results),
                    'files': export_results
                }
            else:
                # Individual exports
                export_results = []
                for char in characters:
                    result = self.export_character(
                        char['id'],
                        format=format
                    )
                    export_results.append(result)
                
                return {
                    'success': True,
                    'exported_count': len(export_results),
                    'files': export_results
                }
                
        except Exception as e:
            logger.error(f"Error exporting characters: {e}")
            raise StorageError(f"Failed to export characters: {str(e)}")
    
    def export_training_data(
        self,
        character_ids: Optional[List[str]] = None,
        model_type: str = 'gpt',
        format: str = 'jsonl'
    ) -> Dict[str, Any]:
        """
        Export training data for fine-tuning
        
        Args:
            character_ids: Specific characters to include (None for all)
            model_type: Target model type (gpt, claude, etc.)
            format: Export format
            
        Returns:
            Export result with file path
        """
        try:
            # Get characters
            if character_ids:
                characters = [
                    self.db.get_character(cid) 
                    for cid in character_ids 
                    if self.db.get_character(cid)
                ]
            else:
                characters = self.db.list_characters()
            
            if not characters:
                return {
                    'success': False,
                    'error': 'No characters found'
                }
            
            # Export training data
            result = self.export_adapter.export_training_data(
                characters,
                format=format,
                model_type=model_type
            )
            
            # Track export event
            self.analytics_adapter.track_event(
                'training_data_exported',
                {
                    'character_count': len(characters),
                    'model_type': model_type,
                    'format': format
                }
            )
            
            logger.info(f"Exported training data for {len(characters)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            raise StorageError(f"Failed to export training data: {str(e)}")
    
    def export_character_card(
        self,
        character_id: str,
        template: str = 'default'
    ) -> Dict[str, Any]:
        """
        Export character as shareable card
        
        Args:
            character_id: Character ID
            template: Card template
            
        Returns:
            Export result with file path
        """
        try:
            # Get character
            character = self.db.get_character(character_id)
            if not character:
                raise StorageError(f"Character {character_id} not found")
            
            # Get analytics for performance badge
            analytics = self.analytics_adapter.get_character_performance_metrics(
                character_id
            )
            character['performance'] = analytics
            
            # Export card
            result = self.export_adapter.export_character_card(
                character,
                template=template
            )
            
            # Track event
            self.analytics_adapter.track_event(
                'character_card_created',
                {
                    'character_id': character_id,
                    'template': template
                }
            )
            
            logger.info(f"Created character card for {character_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating character card: {e}")
            raise StorageError(f"Failed to create character card: {str(e)}")
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        """
        Get available export formats
        
        Returns:
            List of format options
        """
        return [
            {
                'format': 'json',
                'name': 'JSON',
                'description': 'JavaScript Object Notation - Universal format'
            },
            {
                'format': 'jsonl',
                'name': 'JSONL',
                'description': 'JSON Lines - For training data'
            },
            {
                'format': 'pdf',
                'name': 'PDF',
                'description': 'Portable Document Format - For sharing'
            },
            {
                'format': 'docx',
                'name': 'Word Document',
                'description': 'Microsoft Word format'
            },
            {
                'format': 'csv',
                'name': 'CSV',
                'description': 'Comma-separated values - For spreadsheets'
            }
        ]
    
    def get_model_types(self) -> List[Dict[str, str]]:
        """
        Get available model types for training data
        
        Returns:
            List of model options
        """
        return [
            {
                'type': 'gpt',
                'name': 'OpenAI GPT',
                'description': 'For fine-tuning GPT-3.5/GPT-4'
            },
            {
                'type': 'claude',
                'name': 'Anthropic Claude',
                'description': 'For Claude model training'
            },
            {
                'type': 'generic',
                'name': 'Generic Format',
                'description': 'Universal training format'
            }
        ]