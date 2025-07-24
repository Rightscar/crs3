"""
Character Extraction Service
============================

Extract and analyze all characters from uploaded documents.
Now uses the integration adapter for enhanced NLP capabilities.
"""

import re
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional

# Use our integration adapter for NLP
from integrations.adapters.nlp_adapter import IntelligentProcessorAdapter
from integrations.config import integration_config

from config.logging_config import logger
from core.models import Character, PersonalityProfile
from core.exceptions import DocumentProcessingError
from .character_analyzer import CharacterAnalyzer

class CharacterExtractor:
    """Extract characters from documents using NLP"""
    
    def __init__(self):
        """Initialize NLP models using integration adapter"""
        # Use the intelligent processor adapter
        self.nlp_adapter = IntelligentProcessorAdapter()
        
        # Initialize character analyzer
        self.analyzer = CharacterAnalyzer()
        
        # Character data storage
        self.characters = {}
        self.character_mentions = defaultdict(list)
        self.character_relationships = defaultdict(lambda: defaultdict(int))
        self.character_dialogues = defaultdict(list)
        self.character_actions = defaultdict(list)
        self.character_descriptions = defaultdict(list)
        self.character_contexts = defaultdict(list)
        
    def extract_characters(self, text: str, min_mentions: int = 3) -> List[Dict[str, Any]]:
        """
        Extract all characters from text
        
        Args:
            text: Document text
            min_mentions: Minimum mentions to consider as character
            
        Returns:
            List of character data
        """
        logger.info("Starting character extraction with enhanced NLP...")
        
        # Perform comprehensive text analysis
        nlp_analysis = self.nlp_adapter.analyze_text(text)
        
        # Extract entities using adapter
        entities = self.nlp_adapter.extract_entities(text)
        
        # Extract themes for character context
        themes = self.nlp_adapter.extract_themes(text)
        
        # Extract dialogues using adapter
        dialogues = self.nlp_adapter.extract_dialogue(text)
        
        # Process entities as characters
        self._process_entities(entities, text)
        
        # Process dialogues
        self._process_dialogues(dialogues)
        
        # Extract additional dialogues with patterns
        self._extract_dialogues(text)
        
        # Extract character interactions from entities
        self._extract_interactions_from_entities(entities, text)
        
        # Extract descriptions
        self._extract_descriptions(text)
        
        # Filter and rank characters
        characters = self._filter_characters(min_mentions)
        
        # Generate character profiles with deep analysis
        character_profiles = []
        for char_name, char_data in characters.items():
            # Basic profile
            basic_profile = self._generate_character_profile(char_name, char_data)
            
            # Deep analysis
            deep_analysis = self.analyzer.analyze_character_depth(
                char_name, 
                text,
                char_data['dialogues'],
                self.character_contexts[char_name]
            )
            
            # Merge profiles
            enhanced_profile = {
                **basic_profile,
                'character_dna': deep_analysis['character_dna'],
                'speech_patterns': deep_analysis['speech_patterns'],
                'emotional_profile': deep_analysis['emotional_profile'],
                'unique_behaviors': deep_analysis['unique_behaviors'],
                'quirks_mannerisms': deep_analysis['quirks_mannerisms'],
                'values_beliefs': deep_analysis['values_beliefs'],
                'uniqueness_score': deep_analysis['uniqueness_score']
            }
            
            character_profiles.append(enhanced_profile)
        
        logger.info(f"Extracted {len(character_profiles)} characters with deep analysis")
        return character_profiles
    
    def _process_entities(self, entities: List[Dict[str, Any]], text: str):
        """Process extracted entities as potential characters"""
        for ent in entities:
            if ent.get('type') == "PERSON":
                # Clean character name
                char_name = self._normalize_name(ent['text'])
                
                # Get context around entity
                context = self._get_entity_context(ent, text)
                
                self.character_mentions[char_name].append({
                    'text': ent['text'],
                    'context': context,
                    'start': ent.get('start', 0),
                    'end': ent.get('end', 0)
                })
                
                # Store context for deep analysis
                self.character_contexts[char_name].append(context)
    
    def _process_dialogues(self, dialogues: List[Dict[str, str]]):
        """Process dialogues extracted by NLP adapter"""
        for dialogue in dialogues:
            speaker = dialogue.get('speaker', 'Unknown')
            if speaker != 'Unknown':
                speaker = self._normalize_name(speaker)
                self.character_dialogues[speaker].append({
                    'text': dialogue['text'],
                    'verb': 'said',
                    'context': dialogue.get('context', '')
                })
    
    def _extract_dialogues(self, text: str):
        """Extract character dialogues"""
        # Common dialogue patterns
        dialogue_patterns = [
            r'"([^"]+)"[,\s]+said\s+(\w+)',
            r'(\w+)\s+said[,:\s]+"([^"]+)"',
            r'"([^"]+)"[,\s]+(\w+)\s+replied',
            r'(\w+)\s+replied[,:\s]+"([^"]+)"',
            r'"([^"]+)"[,\s]+(\w+)\s+asked',
            r'(\w+)\s+asked[,:\s]+"([^"]+)"',
            r'"([^"]+)"[,\s]+(\w+)\s+whispered',
            r'(\w+)\s+whispered[,:\s]+"([^"]+)"',
            r'"([^"]+)"[,\s]+(\w+)\s+shouted',
            r'(\w+)\s+shouted[,:\s]+"([^"]+)"',
        ]
        
        for pattern in dialogue_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.group(1) and match.group(2):
                    # Determine speaker and dialogue
                    if pattern.startswith('"'):
                        dialogue = match.group(1)
                        speaker = self._normalize_name(match.group(2))
                    else:
                        speaker = self._normalize_name(match.group(1))
                        dialogue = match.group(2)
                    
                    self.character_dialogues[speaker].append({
                        'text': dialogue,
                        'verb': pattern.split('\\s+')[2] if '\\s+' in pattern else 'said'
                    })
    
    def _extract_interactions_from_entities(self, entities: List[Dict[str, Any]], text: str):
        """Extract character interactions and relationships from entities"""
        # Group entities by sentence
        sentences = text.split('.')
        
        for sentence in sentences:
            # Find all person entities in this sentence
            persons_in_sentence = []
            
            for ent in entities:
                if ent.get('type') == "PERSON":
                    # Check if entity appears in this sentence
                    if ent['text'] in sentence:
                        persons_in_sentence.append(ent)
            
            if len(persons_in_sentence) >= 2:
                # Extract relationships between characters
                for i, person1 in enumerate(persons_in_sentence):
                    for person2 in persons_in_sentence[i+1:]:
                        char1 = self._normalize_name(person1['text'])
                        char2 = self._normalize_name(person2['text'])
                        
                        # Increment interaction count
                        self.character_relationships[char1][char2] += 1
                        self.character_relationships[char2][char1] += 1
                        
                        # Store interaction context
                        self.character_actions[char1].append({
                            'action': sentence.strip(),
                            'with': char2
                        })
    
    def _extract_descriptions(self, text: str):
        """Extract character descriptions"""
        description_patterns = [
            r'(\w+)\s+was\s+(?:a|an)\s+([^.]+)',
            r'(\w+)\s+looked\s+([^.]+)',
            r'(\w+)\s+had\s+([^.]+)',
            r'(\w+),\s+(?:a|an|the)\s+([^,]+),',
        ]
        
        for pattern in description_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                char_name = self._normalize_name(match.group(1))
                description = match.group(2)
                
                # Check if this is actually a character we've seen
                if char_name in self.character_mentions:
                    self.character_descriptions[char_name].append(description)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize character names"""
        # Remove titles
        titles = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sir', 'Lady', 'Lord']
        for title in titles:
            name = name.replace(title, '').strip()
        
        # Capitalize properly
        return ' '.join(word.capitalize() for word in name.split())
    
    def _get_entity_context(self, entity: Dict[str, Any], text: str, window: int = 50) -> str:
        """Get context around entity mention"""
        start = max(0, entity.get('start', 0) - window)
        end = min(len(text), entity.get('end', 0) + window)
        return text[start:end]
    
    def _filter_characters(self, min_mentions: int) -> Dict[str, Dict]:
        """Filter and rank characters by importance"""
        filtered = {}
        
        for char_name, mentions in self.character_mentions.items():
            if len(mentions) >= min_mentions:
                filtered[char_name] = {
                    'mentions': mentions,
                    'mention_count': len(mentions),
                    'dialogues': self.character_dialogues.get(char_name, []),
                    'relationships': dict(self.character_relationships.get(char_name, {})),
                    'actions': self.character_actions.get(char_name, []),
                    'descriptions': self.character_descriptions.get(char_name, [])
                }
        
        # Sort by mention count
        return dict(sorted(filtered.items(), 
                          key=lambda x: x[1]['mention_count'], 
                          reverse=True))
    
    def _generate_character_profile(self, name: str, data: Dict) -> Dict[str, Any]:
        """Generate character profile from extracted data"""
        
        # Analyze personality from dialogues and actions
        personality_traits = self._analyze_personality(data)
        
        # Generate character description
        description = self._generate_description(name, data)
        
        # Determine character role
        role = self._determine_role(data)
        
        # Extract key quotes
        key_quotes = self._extract_key_quotes(data['dialogues'])
        
        # Generate avatar emoji based on role/personality
        avatar = self._select_avatar(role, personality_traits)
        
        return {
            'name': name,
            'role': role,
            'description': description,
            'avatar': avatar,
            'mention_count': data['mention_count'],
            'personality_traits': personality_traits,
            'key_quotes': key_quotes,
            'relationships': data['relationships'],
            'dialogue_count': len(data['dialogues']),
            'speaking_style': self._analyze_speaking_style(data['dialogues']),
            'importance_score': self._calculate_importance(data)
        }
    
    def _analyze_personality(self, data: Dict) -> Dict[str, float]:
        """Analyze personality traits from character data"""
        traits = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5,
            'humor': 0.0,
            'formality': 0.5,
            'creativity': 0.5
        }
        
        # Analyze based on dialogue count (extraversion)
        if len(data['dialogues']) > 20:
            traits['extraversion'] = 0.8
        elif len(data['dialogues']) < 5:
            traits['extraversion'] = 0.3
        
        # Analyze based on relationships (agreeableness)
        if len(data['relationships']) > 5:
            traits['agreeableness'] = 0.7
            traits['openness'] = 0.7
        
        # Analyze dialogue content for other traits
        all_dialogue = ' '.join([d['text'] for d in data['dialogues']])
        
        # Humor detection
        humor_words = ['laugh', 'joke', 'funny', 'humor', 'jest', 'tease']
        if any(word in all_dialogue.lower() for word in humor_words):
            traits['humor'] = 0.7
        
        # Formality detection
        formal_words = ['sir', 'madam', 'indeed', 'certainly', 'shall']
        informal_words = ['yeah', 'gonna', 'wanna', 'hey', 'cool']
        
        formal_count = sum(1 for word in formal_words if word in all_dialogue.lower())
        informal_count = sum(1 for word in informal_words if word in all_dialogue.lower())
        
        if formal_count > informal_count:
            traits['formality'] = 0.8
        elif informal_count > formal_count:
            traits['formality'] = 0.2
        
        return traits
    
    def _generate_description(self, name: str, data: Dict) -> str:
        """Generate character description"""
        descriptions = data['descriptions']
        dialogue_count = len(data['dialogues'])
        relationship_count = len(data['relationships'])
        
        # Build description
        desc_parts = []
        
        # Role in story
        if data['mention_count'] > 50:
            desc_parts.append(f"{name} is a major character in the story")
        elif data['mention_count'] > 20:
            desc_parts.append(f"{name} plays an important role in the narrative")
        else:
            desc_parts.append(f"{name} is a supporting character")
        
        # Physical/personality descriptions
        if descriptions:
            desc_parts.append(f"described as {descriptions[0]}")
        
        # Social aspects
        if relationship_count > 5:
            desc_parts.append("with many connections to other characters")
        elif relationship_count > 0:
            main_relationships = sorted(data['relationships'].items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:2]
            rel_names = [rel[0] for rel in main_relationships]
            desc_parts.append(f"particularly connected to {' and '.join(rel_names)}")
        
        # Speaking characteristics
        if dialogue_count > 10:
            desc_parts.append("and is quite talkative throughout the story")
        elif dialogue_count > 0:
            desc_parts.append("who speaks occasionally")
        
        return '. '.join(desc_parts) + '.'
    
    def _determine_role(self, data: Dict) -> str:
        """Determine character's role in the story"""
        mention_count = data['mention_count']
        dialogue_count = len(data['dialogues'])
        
        if mention_count > 100:
            return "Protagonist"
        elif mention_count > 50:
            return "Main Character"
        elif mention_count > 20:
            return "Supporting Character"
        elif dialogue_count > 10:
            return "Speaking Role"
        else:
            return "Minor Character"
    
    def _extract_key_quotes(self, dialogues: List[Dict], max_quotes: int = 3) -> List[str]:
        """Extract most representative quotes"""
        if not dialogues:
            return []
        
        # Sort by length and uniqueness
        sorted_dialogues = sorted(dialogues, 
                                key=lambda x: len(x['text']), 
                                reverse=True)
        
        # Get diverse quotes
        quotes = []
        for dialogue in sorted_dialogues[:max_quotes * 2]:
            if len(quotes) >= max_quotes:
                break
            
            # Avoid very short or very long quotes
            if 10 < len(dialogue['text']) < 150:
                quotes.append(dialogue['text'])
        
        return quotes
    
    def _analyze_speaking_style(self, dialogues: List[Dict]) -> str:
        """Analyze character's speaking style"""
        if not dialogues:
            return "silent"
        
        all_text = ' '.join([d['text'] for d in dialogues])
        avg_length = sum(len(d['text']) for d in dialogues) / len(dialogues)
        
        # Determine style
        if avg_length > 100:
            style = "verbose"
        elif avg_length > 50:
            style = "articulate"
        elif avg_length > 20:
            style = "conversational"
        else:
            style = "brief"
        
        # Check for questions
        if all_text.count('?') > len(dialogues) * 0.3:
            style += ", inquisitive"
        
        # Check for exclamations
        if all_text.count('!') > len(dialogues) * 0.2:
            style += ", emphatic"
        
        return style
    
    def _calculate_importance(self, data: Dict) -> float:
        """Calculate character importance score (0-1)"""
        # Weighted factors
        mention_weight = 0.4
        dialogue_weight = 0.3
        relationship_weight = 0.2
        action_weight = 0.1
        
        # Normalize counts (assuming max values)
        mention_score = min(data['mention_count'] / 200, 1.0)
        dialogue_score = min(len(data['dialogues']) / 50, 1.0)
        relationship_score = min(len(data['relationships']) / 10, 1.0)
        action_score = min(len(data['actions']) / 30, 1.0)
        
        importance = (
            mention_score * mention_weight +
            dialogue_score * dialogue_weight +
            relationship_score * relationship_weight +
            action_score * action_weight
        )
        
        return round(importance, 2)
    
    def _select_avatar(self, role: str, traits: Dict[str, float]) -> str:
        """Select appropriate emoji avatar based on character analysis"""
        # Role-based avatars
        role_avatars = {
            'Protagonist': ['🦸', '👤', '🧑‍💼', '👨‍🎓', '👩‍🎓'],
            'Main Character': ['👨', '👩', '🧑', '👱', '👧'],
            'Supporting Character': ['👥', '🧔', '👵', '👴', '🧓'],
            'Speaking Role': ['🗣️', '💬', '🙋', '🤷', '🙆'],
            'Minor Character': ['👤', '🚶', '🧍', '👥', '🫂']
        }
        
        # Personality-based modifiers
        if traits['humor'] > 0.6:
            return '😄'
        elif traits['formality'] > 0.7:
            return '🎩'
        elif traits['creativity'] > 0.7:
            return '🎨'
        elif traits['extraversion'] > 0.7:
            return '🗣️'
        elif traits['neuroticism'] > 0.6:
            return '😰'
        
        # Default based on role
        avatars = role_avatars.get(role, ['👤'])
        return avatars[0]