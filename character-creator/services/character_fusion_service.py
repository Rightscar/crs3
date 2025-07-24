"""
Character Fusion Service
========================

Merge multiple characters into unique hybrids.
"""

import uuid
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import numpy as np

from core.database import DatabaseManager
from core.models import Character, PersonalityProfile
from config.logging_config import logger
from integrations.adapters.analytics_adapter import AnalyticsAdapter


class CharacterFusionService:
    """Service for fusing characters into hybrids"""
    
    def __init__(self):
        """Initialize fusion service"""
        self.db = DatabaseManager()
        self.analytics = AnalyticsAdapter()
        
        # Fusion configuration
        self.fusion_config = {
            'trait_blend_methods': ['average', 'dominant', 'random', 'harmonic'],
            'memory_merge_threshold': 0.7,  # Importance threshold for memory merge
            'conflict_resolution_method': 'weighted_average',
            'personality_stability_factor': 0.8,
            'max_fusion_depth': 3  # Max generations of fusion
        }
    
    def fuse_characters(
        self,
        character_ids: List[str],
        fusion_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fuse multiple characters into a hybrid
        
        Args:
            character_ids: List of character IDs to fuse (2-4 characters)
            fusion_params: Optional fusion parameters:
                - name: str (hybrid name)
                - blend_method: str (trait blending method)
                - preserve_dominant: bool (preserve dominant traits)
                - fusion_type: str ('balanced', 'weighted', 'random')
                
        Returns:
            New hybrid character data
        """
        try:
            # Validate input
            if len(character_ids) < 2:
                return {'success': False, 'error': 'Need at least 2 characters to fuse'}
            if len(character_ids) > 4:
                return {'success': False, 'error': 'Maximum 4 characters can be fused'}
            
            # Get characters
            characters = []
            for char_id in character_ids:
                char = self.db.get_character(char_id)
                if not char:
                    return {'success': False, 'error': f'Character {char_id} not found'}
                characters.append(char)
            
            # Set default params
            if fusion_params is None:
                fusion_params = {}
            
            # Generate hybrid character
            hybrid = self._create_hybrid_character(characters, fusion_params)
            
            # Save hybrid character
            hybrid_id = str(uuid.uuid4())
            hybrid['id'] = hybrid_id
            hybrid['created_at'] = datetime.now().isoformat()
            hybrid['fusion_data'] = {
                'parent_ids': character_ids,
                'fusion_params': fusion_params,
                'generation': self._calculate_fusion_generation(characters)
            }
            
            # Store in database
            self.db.save_character(hybrid)
            
            # Track analytics
            self.analytics.track_event(
                'character_fusion',
                {
                    'hybrid_id': hybrid_id,
                    'parent_count': len(character_ids),
                    'fusion_type': fusion_params.get('fusion_type', 'balanced')
                }
            )
            
            logger.info(f"Created hybrid character {hybrid_id} from {len(character_ids)} parents")
            
            return {
                'success': True,
                'character': hybrid,
                'fusion_summary': self._generate_fusion_summary(hybrid, characters)
            }
            
        except Exception as e:
            logger.error(f"Error fusing characters: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_hybrid_character(
        self,
        characters: List[Dict[str, Any]],
        fusion_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create hybrid character from parents"""
        # Generate name
        hybrid_name = fusion_params.get('name') or self._generate_hybrid_name(characters)
        
        # Blend personality traits
        personality_traits = self._blend_personality_traits(
            characters,
            fusion_params.get('blend_method', 'weighted')
        )
        
        # Merge descriptions
        description = self._merge_descriptions(characters)
        
        # Combine speech patterns
        speaking_style = self._blend_speaking_styles(characters)
        
        # Merge key quotes
        key_quotes = self._merge_key_quotes(characters)
        
        # Create unique avatar
        avatar = self._generate_hybrid_avatar(characters)
        
        # Determine role
        role = self._determine_hybrid_role(characters)
        
        # Merge memories and knowledge
        character_dna = self._merge_character_dna(characters)
        
        # Calculate relationships (average of all parents)
        relationships = self._merge_relationships(characters)
        
        return {
            'name': hybrid_name,
            'role': role,
            'description': description,
            'avatar': avatar,
            'personality_traits': personality_traits,
            'speaking_style': speaking_style,
            'key_quotes': key_quotes,
            'relationships': relationships,
            'character_dna': character_dna,
            'is_hybrid': True,
            'importance_score': self._calculate_hybrid_importance(characters)
        }
    
    def _generate_hybrid_name(self, characters: List[Dict[str, Any]]) -> str:
        """Generate name for hybrid character"""
        # Take parts from each parent name
        name_parts = []
        for char in characters:
            name = char.get('name', 'Unknown')
            parts = name.split()
            if parts:
                # Take first part of first name or last part of last name
                if len(name_parts) % 2 == 0:
                    name_parts.append(parts[0][:len(parts[0])//2])
                else:
                    name_parts.append(parts[-1][len(parts[-1])//2:])
        
        # Combine parts
        hybrid_name = ''.join(name_parts)
        
        # Add suffix if needed
        if len(hybrid_name) < 4:
            hybrid_name += '-X'
        
        return hybrid_name.title()
    
    def _blend_personality_traits(
        self,
        characters: List[Dict[str, Any]],
        blend_method: str
    ) -> Dict[str, float]:
        """Blend personality traits from multiple characters"""
        blended_traits = {}
        
        # Get all trait keys
        all_traits = set()
        for char in characters:
            all_traits.update(char.get('personality_traits', {}).keys())
        
        for trait in all_traits:
            values = []
            weights = []
            
            for char in characters:
                char_traits = char.get('personality_traits', {})
                if trait in char_traits:
                    values.append(char_traits[trait])
                    # Weight by character importance
                    weights.append(char.get('importance_score', 0.5))
            
            if not values:
                continue
            
            # Apply blend method
            if blend_method == 'average':
                blended_value = np.mean(values)
            elif blend_method == 'weighted':
                blended_value = np.average(values, weights=weights)
            elif blend_method == 'dominant':
                # Take trait from most important character
                max_weight_idx = np.argmax(weights)
                blended_value = values[max_weight_idx]
            elif blend_method == 'harmonic':
                # Harmonic mean for balanced fusion
                blended_value = len(values) / sum(1/v for v in values if v > 0)
            else:  # random
                blended_value = np.random.choice(values)
            
            # Add some variation
            variation = np.random.normal(0, 0.05)
            blended_value = np.clip(blended_value + variation, 0, 1)
            
            blended_traits[trait] = round(blended_value, 2)
        
        return blended_traits
    
    def _merge_descriptions(self, characters: List[Dict[str, Any]]) -> str:
        """Merge character descriptions"""
        descriptions = []
        
        for char in characters:
            desc = char.get('description', '')
            if desc:
                # Extract key phrases
                key_parts = desc.split('.')[:2]  # First two sentences
                descriptions.extend(key_parts)
        
        # Combine and create new description
        if descriptions:
            base_desc = ' '.join(descriptions[:3])
            hybrid_desc = f"A unique fusion combining traits from multiple sources. {base_desc}"
            
            # Add fusion note
            parent_names = [char.get('name', 'Unknown') for char in characters]
            hybrid_desc += f" This character embodies aspects of {', '.join(parent_names)}."
            
            return hybrid_desc
        
        return "A mysterious hybrid character with blended traits."
    
    def _blend_speaking_styles(self, characters: List[Dict[str, Any]]) -> str:
        """Blend speaking styles"""
        styles = []
        
        for char in characters:
            style = char.get('speaking_style', '')
            if style:
                # Extract style components
                style_parts = style.split(',')
                styles.extend([s.strip() for s in style_parts])
        
        # Remove duplicates and combine
        unique_styles = list(set(styles))
        
        if len(unique_styles) > 3:
            # Take most interesting combination
            np.random.shuffle(unique_styles)
            unique_styles = unique_styles[:3]
        
        return ', '.join(unique_styles) if unique_styles else 'unique hybrid style'
    
    def _merge_key_quotes(self, characters: List[Dict[str, Any]]) -> List[str]:
        """Merge key quotes from characters"""
        all_quotes = []
        
        for char in characters:
            quotes = char.get('key_quotes', [])
            all_quotes.extend(quotes)
        
        # Select diverse quotes
        if len(all_quotes) > 5:
            # Sort by length for variety
            all_quotes.sort(key=len)
            # Take quotes from different length ranges
            selected = [
                all_quotes[0],  # Shortest
                all_quotes[len(all_quotes)//2],  # Medium
                all_quotes[-1]  # Longest
            ]
            return selected
        
        return all_quotes[:3]
    
    def _generate_hybrid_avatar(self, characters: List[Dict[str, Any]]) -> str:
        """Generate avatar for hybrid character"""
        # Hybrid-specific avatars
        hybrid_avatars = ['🔮', '⚡', '🌟', '💫', '🎭', '🦄', '🐉', '🌀']
        
        # If all parents have similar avatars, use related one
        parent_avatars = [char.get('avatar', '👤') for char in characters]
        
        # Check for patterns
        if all('🦸' in avatar for avatar in parent_avatars):
            return '⚡'  # Super hybrid
        elif all('👤' in avatar for avatar in parent_avatars):
            return '🔮'  # Mysterious hybrid
        
        # Random hybrid avatar
        return np.random.choice(hybrid_avatars)
    
    def _determine_hybrid_role(self, characters: List[Dict[str, Any]]) -> str:
        """Determine role for hybrid character"""
        roles = [char.get('role', 'Character') for char in characters]
        
        # Check for dominant roles
        if 'Protagonist' in roles:
            return 'Hybrid Protagonist'
        elif all('Main Character' in role for role in roles):
            return 'Fusion Main Character'
        elif 'Supporting Character' in roles:
            return 'Hybrid Supporting Character'
        
        return 'Fusion Character'
    
    def _merge_character_dna(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge character DNA and deep traits"""
        merged_dna = {
            'core_values': [],
            'motivations': [],
            'fears': [],
            'quirks': [],
            'speech_patterns': [],
            'emotional_triggers': []
        }
        
        for char in characters:
            char_dna = char.get('character_dna', {})
            
            for key in merged_dna:
                if key in char_dna:
                    if isinstance(char_dna[key], list):
                        merged_dna[key].extend(char_dna[key])
                    else:
                        merged_dna[key].append(char_dna[key])
        
        # Remove duplicates and limit
        for key in merged_dna:
            if merged_dna[key]:
                # Keep unique values
                merged_dna[key] = list(set(merged_dna[key]))[:5]
        
        return merged_dna
    
    def _merge_relationships(self, characters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Merge relationships from all parents"""
        merged_relationships = {}
        
        for char in characters:
            relationships = char.get('relationships', {})
            for name, strength in relationships.items():
                if name in merged_relationships:
                    # Average the relationship strength
                    merged_relationships[name] = (merged_relationships[name] + strength) / 2
                else:
                    merged_relationships[name] = strength * 0.7  # Reduced for hybrid
        
        return merged_relationships
    
    def _calculate_hybrid_importance(self, characters: List[Dict[str, Any]]) -> float:
        """Calculate importance score for hybrid"""
        # Average of parent importance scores
        scores = [char.get('importance_score', 0.5) for char in characters]
        
        # Hybrids are inherently interesting, so boost slightly
        base_score = np.mean(scores)
        hybrid_boost = 0.1
        
        return min(base_score + hybrid_boost, 1.0)
    
    def _calculate_fusion_generation(self, characters: List[Dict[str, Any]]) -> int:
        """Calculate fusion generation (how many times fused)"""
        max_generation = 0
        
        for char in characters:
            fusion_data = char.get('fusion_data', {})
            generation = fusion_data.get('generation', 0)
            max_generation = max(max_generation, generation)
        
        return max_generation + 1
    
    def _generate_fusion_summary(
        self,
        hybrid: Dict[str, Any],
        parents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of fusion results"""
        parent_names = [p.get('name', 'Unknown') for p in parents]
        
        # Calculate trait differences
        trait_variance = {}
        for trait in hybrid.get('personality_traits', {}):
            parent_values = []
            for parent in parents:
                if trait in parent.get('personality_traits', {}):
                    parent_values.append(parent['personality_traits'][trait])
            
            if parent_values:
                variance = np.var(parent_values)
                trait_variance[trait] = round(variance, 3)
        
        # Find most different trait
        most_varied_trait = max(trait_variance.items(), key=lambda x: x[1])[0] if trait_variance else None
        
        return {
            'hybrid_name': hybrid['name'],
            'parent_names': parent_names,
            'generation': hybrid['fusion_data']['generation'],
            'trait_variance': trait_variance,
            'most_varied_trait': most_varied_trait,
            'fusion_type': 'Multi-parent fusion',
            'unique_features': len(hybrid.get('character_dna', {}).get('quirks', []))
        }
    
    def get_fusion_compatibility(
        self,
        character_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Check compatibility between characters for fusion
        
        Args:
            character_ids: List of character IDs to check
            
        Returns:
            Compatibility analysis
        """
        try:
            # Get characters
            characters = []
            for char_id in character_ids:
                char = self.db.get_character(char_id)
                if char:
                    characters.append(char)
            
            if len(characters) < 2:
                return {'success': False, 'error': 'Not enough valid characters'}
            
            # Calculate compatibility metrics
            personality_compatibility = self._calculate_personality_compatibility(characters)
            role_compatibility = self._calculate_role_compatibility(characters)
            style_compatibility = self._calculate_style_compatibility(characters)
            
            # Overall compatibility
            overall = (personality_compatibility + role_compatibility + style_compatibility) / 3
            
            # Recommendations
            recommendations = []
            if overall < 0.3:
                recommendations.append("Low compatibility - fusion may create unstable character")
            elif overall < 0.6:
                recommendations.append("Moderate compatibility - interesting fusion possible")
            else:
                recommendations.append("High compatibility - excellent fusion potential")
            
            if personality_compatibility < 0.4:
                recommendations.append("Consider using 'dominant' blend method for traits")
            
            return {
                'success': True,
                'overall_compatibility': round(overall, 2),
                'personality_compatibility': round(personality_compatibility, 2),
                'role_compatibility': round(role_compatibility, 2),
                'style_compatibility': round(style_compatibility, 2),
                'recommendations': recommendations,
                'fusion_preview': self._generate_fusion_preview(characters)
            }
            
        except Exception as e:
            logger.error(f"Error checking fusion compatibility: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_personality_compatibility(
        self,
        characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate personality trait compatibility"""
        if len(characters) < 2:
            return 0.0
        
        # Get common traits
        common_traits = set(characters[0].get('personality_traits', {}).keys())
        for char in characters[1:]:
            common_traits &= set(char.get('personality_traits', {}).keys())
        
        if not common_traits:
            return 0.3  # Low compatibility if no common traits
        
        # Calculate variance for each trait
        variances = []
        for trait in common_traits:
            values = [char['personality_traits'][trait] for char in characters]
            variances.append(np.var(values))
        
        # Lower variance = higher compatibility
        avg_variance = np.mean(variances)
        compatibility = 1.0 - min(avg_variance * 2, 1.0)
        
        return compatibility
    
    def _calculate_role_compatibility(
        self,
        characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate role compatibility"""
        roles = [char.get('role', 'Character') for char in characters]
        
        # Same roles = high compatibility
        if len(set(roles)) == 1:
            return 1.0
        
        # Compatible role combinations
        compatible_pairs = [
            ('Protagonist', 'Main Character'),
            ('Supporting Character', 'Speaking Role'),
            ('Main Character', 'Supporting Character')
        ]
        
        compatibility_score = 0.5  # Base score
        
        for i, role1 in enumerate(roles):
            for role2 in roles[i+1:]:
                if (role1, role2) in compatible_pairs or (role2, role1) in compatible_pairs:
                    compatibility_score += 0.2
        
        return min(compatibility_score, 1.0)
    
    def _calculate_style_compatibility(
        self,
        characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate speaking style compatibility"""
        styles = [char.get('speaking_style', '') for char in characters]
        
        # Extract style components
        all_components = []
        for style in styles:
            components = [s.strip().lower() for s in style.split(',')]
            all_components.extend(components)
        
        # Check for conflicting styles
        conflicts = [
            ('verbose', 'brief'),
            ('formal', 'casual'),
            ('serious', 'humorous')
        ]
        
        compatibility = 0.7  # Base score
        
        for conflict_pair in conflicts:
            if conflict_pair[0] in all_components and conflict_pair[1] in all_components:
                compatibility -= 0.2
        
        # Bonus for shared components
        unique_components = set(all_components)
        if len(unique_components) < len(all_components) * 0.7:
            compatibility += 0.2  # Many shared components
        
        return max(0, min(compatibility, 1.0))
    
    def _generate_fusion_preview(
        self,
        characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate preview of potential fusion"""
        # Quick preview without saving
        preview_params = {'blend_method': 'average'}
        preview_character = self._create_hybrid_character(characters, preview_params)
        
        return {
            'name': preview_character['name'],
            'personality_preview': {
                k: v for k, v in 
                list(preview_character['personality_traits'].items())[:3]
            },
            'style_preview': preview_character['speaking_style'],
            'role': preview_character['role']
        }