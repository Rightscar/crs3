"""Export adapter for multi_format_exporter module"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Add modules path to system path
sys.path.insert(0, '/workspace/modules')

from ..config import integration_config

logger = logging.getLogger(__name__)

class ExportAdapter:
    """Adapter for the existing multi_format_exporter module"""
    
    def __init__(self):
        """Initialize the export adapter"""
        self._initialized = False
        self.exporter = None
        
        try:
            from multi_format_exporter import MultiFormatExporter
            self.exporter = MultiFormatExporter()
            self._initialized = True
            logger.info("MultiFormatExporter initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import MultiFormatExporter: {e}")
            self._initialized = False
        except Exception as e:
            logger.error(f"Error initializing MultiFormatExporter: {e}")
            self._initialized = False
    
    def export_character(
        self, 
        character: Dict[str, Any], 
        format: str = 'json',
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Export character in specified format
        
        Args:
            character: Character data to export
            format: Export format (json, jsonl, pdf, docx, csv)
            output_path: Optional output file path
            
        Returns:
            Export result with file path and status
        """
        if not self._initialized:
            return {
                'success': False,
                'error': 'Export adapter not initialized'
            }
        
        try:
            # Prepare character data for export
            export_data = self._prepare_character_data(character)
            
            # Generate filename if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{character.get('name', 'character')}_{timestamp}.{format}"
                output_path = Path('exports') / filename
                output_path.parent.mkdir(exist_ok=True)
            
            # Export based on format
            if format == 'json':
                result = self._export_json(export_data, output_path)
            elif format == 'jsonl':
                result = self._export_jsonl([export_data], output_path)
            elif format == 'pdf':
                result = self._export_pdf(export_data, output_path)
            elif format == 'docx':
                result = self._export_docx(export_data, output_path)
            elif format == 'csv':
                result = self._export_csv([export_data], output_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }
            
            return {
                'success': True,
                'file_path': str(output_path),
                'format': format,
                'size': output_path.stat().st_size if output_path.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Error exporting character: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_training_data(
        self,
        characters: List[Dict[str, Any]],
        format: str = 'jsonl',
        model_type: str = 'gpt'
    ) -> Dict[str, Any]:
        """
        Export character data as training data for LLMs
        
        Args:
            characters: List of characters to export
            format: Export format (jsonl for fine-tuning)
            model_type: Target model type (gpt, claude, etc.)
            
        Returns:
            Export result
        """
        if not self._initialized:
            return {
                'success': False,
                'error': 'Export adapter not initialized'
            }
        
        try:
            # Prepare training data
            training_data = []
            
            for character in characters:
                # Convert to training format
                if model_type == 'gpt':
                    training_data.extend(self._prepare_gpt_training_data(character))
                elif model_type == 'claude':
                    training_data.extend(self._prepare_claude_training_data(character))
                else:
                    training_data.extend(self._prepare_generic_training_data(character))
            
            # Export
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path('exports') / f'training_data_{model_type}_{timestamp}.{format}'
            output_path.parent.mkdir(exist_ok=True)
            
            if format == 'jsonl':
                result = self._export_jsonl(training_data, output_path)
            else:
                result = self._export_json(training_data, output_path)
            
            return {
                'success': True,
                'file_path': str(output_path),
                'format': format,
                'model_type': model_type,
                'num_examples': len(training_data)
            }
            
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_character_card(
        self,
        character: Dict[str, Any],
        template: str = 'default'
    ) -> Dict[str, Any]:
        """
        Export character as a shareable card (PDF/Image)
        
        Args:
            character: Character data
            template: Card template to use
            
        Returns:
            Export result with file path
        """
        if not self._initialized:
            # Fallback to simple implementation
            return self._export_simple_card(character)
        
        try:
            # Use the exporter's card generation if available
            if hasattr(self.exporter, 'generate_character_card'):
                result = self.exporter.generate_character_card(
                    character,
                    template=template
                )
                return {
                    'success': True,
                    'file_path': result['path'],
                    'format': 'pdf'
                }
            else:
                # Fallback to PDF export with formatting
                return self._export_character_as_pdf_card(character)
                
        except Exception as e:
            logger.error(f"Error exporting character card: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_character_data(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare character data for export"""
        return {
            'id': character.get('id'),
            'name': character.get('name'),
            'role': character.get('role'),
            'description': character.get('description'),
            'personality_traits': character.get('personality_traits', {}),
            'speaking_style': character.get('speaking_style'),
            'key_quotes': character.get('key_quotes', []),
            'relationships': character.get('relationships', {}),
            'emotional_profile': character.get('emotional_profile', {}),
            'character_dna': character.get('character_dna', {}),
            'metadata': {
                'created_at': character.get('created_at', datetime.now().isoformat()),
                'version': '1.0',
                'export_timestamp': datetime.now().isoformat()
            }
        }
    
    def _prepare_gpt_training_data(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare character data for GPT fine-tuning"""
        training_examples = []
        
        # System message for character
        system_message = self._generate_system_prompt(character)
        
        # Create training examples from quotes
        for quote in character.get('key_quotes', []):
            training_examples.append({
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": "Say something in character."},
                    {"role": "assistant", "content": quote}
                ]
            })
        
        # Add personality-based examples
        personality = character.get('personality_traits', {})
        if personality:
            for trait, value in personality.items():
                if value > 0.7:  # Strong traits
                    training_examples.append({
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": f"How do you show your {trait}?"},
                            {"role": "assistant", "content": self._generate_trait_response(character, trait)}
                        ]
                    })
        
        return training_examples
    
    def _prepare_claude_training_data(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare character data for Claude fine-tuning"""
        # Similar to GPT but with Claude's format
        training_examples = []
        
        system_prompt = self._generate_system_prompt(character)
        
        for quote in character.get('key_quotes', []):
            training_examples.append({
                "prompt": f"Human: Say something as {character['name']}.\n\nAssistant: ",
                "completion": quote
            })
        
        return training_examples
    
    def _prepare_generic_training_data(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare character data in generic format"""
        return [{
            "input": "Describe yourself",
            "output": character.get('description', ''),
            "character": character.get('name', ''),
            "metadata": self._prepare_character_data(character)
        }]
    
    def _generate_system_prompt(self, character: Dict[str, Any]) -> str:
        """Generate system prompt for character"""
        name = character.get('name', 'Character')
        description = character.get('description', '')
        personality = character.get('personality_traits', {})
        style = character.get('speaking_style', '')
        
        prompt = f"You are {name}. {description}\n\n"
        prompt += f"Your speaking style is {style}.\n"
        
        if personality:
            traits = [f"{k}: {v:.1f}" for k, v in personality.items() if v > 0.5]
            prompt += f"Your personality traits: {', '.join(traits)}\n"
        
        prompt += "\nAlways stay in character and respond as this character would."
        
        return prompt
    
    def _generate_trait_response(self, character: Dict[str, Any], trait: str) -> str:
        """Generate a response showcasing a specific trait"""
        responses = {
            'humor': "Oh, you want to see my funny side? Well, buckle up!",
            'formality': "I maintain proper decorum in all my interactions.",
            'creativity': "My mind is a canvas of endless possibilities.",
            'extraversion': "I love meeting new people and sharing stories!",
            'agreeableness': "I believe in finding common ground with everyone.",
        }
        return responses.get(trait, f"My {trait} is an essential part of who I am.")
    
    def _export_json(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export data as JSON"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return False
    
    def _export_jsonl(self, data: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export data as JSONL"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logger.error(f"Error exporting JSONL: {e}")
            return False
    
    def _export_pdf(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export data as PDF"""
        if self.exporter and hasattr(self.exporter, 'export_to_pdf'):
            return self.exporter.export_to_pdf(data, str(output_path))
        else:
            # Simple fallback
            logger.warning("PDF export not available, using JSON instead")
            return self._export_json(data, output_path.with_suffix('.json'))
    
    def _export_docx(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export data as DOCX"""
        if self.exporter and hasattr(self.exporter, 'export_to_docx'):
            return self.exporter.export_to_docx(data, str(output_path))
        else:
            # Simple fallback
            logger.warning("DOCX export not available, using JSON instead")
            return self._export_json(data, output_path.with_suffix('.json'))
    
    def _export_csv(self, data: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export data as CSV"""
        if self.exporter and hasattr(self.exporter, 'export_to_csv'):
            return self.exporter.export_to_csv(data, str(output_path))
        else:
            # Simple fallback
            import csv
            try:
                if data:
                    keys = data[0].keys()
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=keys)
                        writer.writeheader()
                        writer.writerows(data)
                return True
            except Exception as e:
                logger.error(f"Error exporting CSV: {e}")
                return False
    
    def _export_simple_card(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Simple character card export when exporter not available"""
        try:
            # Create a simple text card
            card_content = f"""
CHARACTER CARD
==============

Name: {character.get('name', 'Unknown')}
Role: {character.get('role', 'Character')}

Description:
{character.get('description', 'No description available.')}

Personality Traits:
{json.dumps(character.get('personality_traits', {}), indent=2)}

Key Quotes:
{chr(10).join(['- "' + q + '"' for q in character.get('key_quotes', [])])}

Speaking Style: {character.get('speaking_style', 'Unknown')}
"""
            
            output_path = Path('exports') / f"{character.get('name', 'character')}_card.txt"
            output_path.parent.mkdir(exist_ok=True)
            output_path.write_text(card_content)
            
            return {
                'success': True,
                'file_path': str(output_path),
                'format': 'txt'
            }
            
        except Exception as e:
            logger.error(f"Error creating simple card: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _export_character_as_pdf_card(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Export character as formatted PDF card"""
        # This would use the multi_format_exporter's PDF capabilities
        # For now, fallback to simple card
        return self._export_simple_card(character)