"""
Enhanced Personality Service
===========================

Advanced personality modeling with evolution, compatibility calculations,
and trait-based behavior prediction.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import random
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.models.character_enhanced import (
    PersonalityProfile, PersonalityTrait, EmotionalState,
    EmotionalStateRecord, CharacterGoal, GoalType
)
from backend.models.database import Character, CharacterRelationship
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PersonalityCompatibility:
    """Result of personality compatibility analysis"""
    overall_score: float  # 0.0 to 1.0
    trait_scores: Dict[str, float]
    harmony_factors: List[str]
    conflict_factors: List[str]
    relationship_potential: Dict[str, float]  # friendship, romance, rivalry, etc.


@dataclass
class BehaviorPrediction:
    """Predicted behavior based on personality"""
    action_type: str
    likelihood: float
    reasoning: List[str]
    personality_factors: Dict[str, float]


class EnhancedPersonalityService:
    """
    Advanced personality service with evolution, compatibility,
    and behavior prediction capabilities.
    """
    
    # Trait interaction matrix (how traits influence each other)
    TRAIT_INTERACTIONS = {
        PersonalityTrait.OPENNESS: {
            PersonalityTrait.CONSCIENTIOUSNESS: -0.1,  # Slight negative correlation
            PersonalityTrait.EXTRAVERSION: 0.3,
            PersonalityTrait.AGREEABLENESS: 0.2,
            PersonalityTrait.NEUROTICISM: 0.0
        },
        PersonalityTrait.CONSCIENTIOUSNESS: {
            PersonalityTrait.OPENNESS: -0.1,
            PersonalityTrait.EXTRAVERSION: 0.0,
            PersonalityTrait.AGREEABLENESS: 0.2,
            PersonalityTrait.NEUROTICISM: -0.3
        },
        PersonalityTrait.EXTRAVERSION: {
            PersonalityTrait.OPENNESS: 0.3,
            PersonalityTrait.CONSCIENTIOUSNESS: 0.0,
            PersonalityTrait.AGREEABLENESS: 0.2,
            PersonalityTrait.NEUROTICISM: -0.1
        },
        PersonalityTrait.AGREEABLENESS: {
            PersonalityTrait.OPENNESS: 0.2,
            PersonalityTrait.CONSCIENTIOUSNESS: 0.2,
            PersonalityTrait.EXTRAVERSION: 0.2,
            PersonalityTrait.NEUROTICISM: -0.2
        },
        PersonalityTrait.NEUROTICISM: {
            PersonalityTrait.OPENNESS: 0.0,
            PersonalityTrait.CONSCIENTIOUSNESS: -0.3,
            PersonalityTrait.EXTRAVERSION: -0.1,
            PersonalityTrait.AGREEABLENESS: -0.2
        }
    }
    
    # Derived trait calculations
    DERIVED_TRAITS = {
        "creativity": lambda p: (p.openness * 0.6 + p.extraversion * 0.2 + (1 - p.conscientiousness) * 0.2),
        "leadership": lambda p: (p.extraversion * 0.4 + p.conscientiousness * 0.3 + (1 - p.neuroticism) * 0.3),
        "empathy": lambda p: (p.agreeableness * 0.5 + p.openness * 0.3 + p.extraversion * 0.2),
        "resilience": lambda p: ((1 - p.neuroticism) * 0.5 + p.conscientiousness * 0.3 + p.extraversion * 0.2),
        "curiosity": lambda p: (p.openness * 0.7 + p.extraversion * 0.3),
        "ambition": lambda p: (p.conscientiousness * 0.5 + p.extraversion * 0.3 + (1 - p.agreeableness) * 0.2),
        "independence": lambda p: ((1 - p.agreeableness) * 0.4 + p.openness * 0.3 + (1 - p.neuroticism) * 0.3),
        "loyalty": lambda p: (p.agreeableness * 0.5 + p.conscientiousness * 0.5)
    }
    
    def __init__(self):
        self.evolution_threshold = 0.05  # Minimum change to trigger evolution
        self.compatibility_cache = {}  # Cache compatibility calculations
    
    async def create_personality_profile(
        self,
        character_id: str,
        traits: Optional[Dict[str, float]] = None,
        db: AsyncSession = None
    ) -> PersonalityProfile:
        """Create a new personality profile for a character"""
        profile = PersonalityProfile(character_id=character_id)
        
        if traits:
            for trait, value in traits.items():
                if hasattr(profile, trait):
                    setattr(profile, trait, max(0.0, min(1.0, value)))
        else:
            # Generate random personality
            profile.openness = random.gauss(0.5, 0.15)
            profile.conscientiousness = random.gauss(0.5, 0.15)
            profile.extraversion = random.gauss(0.5, 0.15)
            profile.agreeableness = random.gauss(0.5, 0.15)
            profile.neuroticism = random.gauss(0.5, 0.15)
            
            # Clamp values
            for trait in PersonalityTrait:
                value = getattr(profile, trait.value)
                setattr(profile, trait.value, max(0.0, min(1.0, value)))
        
        # Calculate derived traits
        profile.derived_traits = self._calculate_derived_traits(profile)
        
        if db:
            db.add(profile)
            await db.commit()
        
        return profile
    
    def _calculate_derived_traits(self, profile: PersonalityProfile) -> Dict[str, float]:
        """Calculate derived personality traits"""
        derived = {}
        
        for trait_name, calculator in self.DERIVED_TRAITS.items():
            derived[trait_name] = calculator(profile)
        
        return derived
    
    async def evolve_personality(
        self,
        character_id: str,
        experience: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[PersonalityProfile]:
        """
        Evolve character personality based on experiences.
        
        Args:
            character_id: Character ID
            experience: Dictionary containing experience details
                - type: "positive", "negative", "traumatic", "growth"
                - intensity: 0.0 to 1.0
                - traits_affected: List of personality traits
                - context: Additional context
        """
        # Get current personality
        result = await db.execute(
            select(PersonalityProfile).where(PersonalityProfile.character_id == character_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        # Check if enough time has passed since last evolution
        if profile.last_evolution:
            time_since = datetime.utcnow() - profile.last_evolution
            if time_since < timedelta(hours=1):  # Minimum time between evolutions
                return profile
        
        # Calculate trait changes based on experience
        changes = self._calculate_trait_changes(profile, experience)
        
        # Apply changes if significant
        any_change = False
        for trait, change in changes.items():
            if abs(change) > self.evolution_threshold * profile.evolution_rate:
                current_value = getattr(profile, trait)
                new_value = max(0.0, min(1.0, current_value + change))
                setattr(profile, trait, new_value)
                any_change = True
                
                logger.info(f"Character {character_id} {trait} evolved: {current_value:.3f} -> {new_value:.3f}")
        
        if any_change:
            # Recalculate derived traits
            profile.derived_traits = self._calculate_derived_traits(profile)
            profile.last_evolution = datetime.utcnow()
            
            await db.commit()
        
        return profile
    
    def _calculate_trait_changes(
        self,
        profile: PersonalityProfile,
        experience: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate how an experience affects personality traits"""
        changes = {}
        
        exp_type = experience.get("type", "neutral")
        intensity = experience.get("intensity", 0.5)
        traits_affected = experience.get("traits_affected", [])
        
        # Base change calculation
        base_change = intensity * profile.evolution_rate
        
        # Experience type modifiers
        type_modifiers = {
            "positive": 1.0,
            "negative": -0.8,
            "traumatic": -1.5,
            "growth": 1.2,
            "neutral": 0.0
        }
        
        modifier = type_modifiers.get(exp_type, 0.0)
        
        # Apply changes to affected traits
        for trait in traits_affected:
            if trait in [t.value for t in PersonalityTrait]:
                change = base_change * modifier
                
                # Add some randomness
                change += random.gauss(0, 0.01)
                
                # Consider trait interactions
                for other_trait, interaction in self.TRAIT_INTERACTIONS.get(PersonalityTrait(trait), {}).items():
                    other_value = getattr(profile, other_trait.value)
                    change += interaction * other_value * 0.1
                
                changes[trait] = change
        
        return changes
    
    async def calculate_compatibility(
        self,
        character1_id: str,
        character2_id: str,
        db: AsyncSession
    ) -> PersonalityCompatibility:
        """Calculate personality compatibility between two characters"""
        # Check cache
        cache_key = tuple(sorted([character1_id, character2_id]))
        if cache_key in self.compatibility_cache:
            cached = self.compatibility_cache[cache_key]
            if (datetime.utcnow() - cached["time"]).seconds < 3600:  # 1 hour cache
                return cached["result"]
        
        # Get both personalities
        result = await db.execute(
            select(PersonalityProfile).where(
                PersonalityProfile.character_id.in_([character1_id, character2_id])
            )
        )
        profiles = result.scalars().all()
        
        if len(profiles) != 2:
            return PersonalityCompatibility(
                overall_score=0.5,
                trait_scores={},
                harmony_factors=[],
                conflict_factors=[],
                relationship_potential={}
            )
        
        p1, p2 = profiles[0], profiles[1]
        
        # Calculate trait-by-trait compatibility
        trait_scores = {}
        for trait in PersonalityTrait:
            v1 = getattr(p1, trait.value)
            v2 = getattr(p2, trait.value)
            
            # Similar values = higher compatibility, with some exceptions
            diff = abs(v1 - v2)
            
            if trait == PersonalityTrait.EXTRAVERSION:
                # Opposites can attract for extraversion
                score = 1.0 - diff * 0.5
            elif trait == PersonalityTrait.NEUROTICISM:
                # Both low is best, both high is worst
                score = 1.0 - (v1 + v2) / 2
            else:
                # Generally, similarity is good
                score = 1.0 - diff
            
            trait_scores[trait.value] = score
        
        # Calculate overall compatibility
        overall_score = np.mean(list(trait_scores.values()))
        
        # Identify harmony and conflict factors
        harmony_factors = []
        conflict_factors = []
        
        for trait, score in trait_scores.items():
            if score > 0.7:
                harmony_factors.append(f"Compatible {trait}")
            elif score < 0.3:
                conflict_factors.append(f"Conflicting {trait}")
        
        # Calculate relationship potential
        relationship_potential = {
            "friendship": self._calculate_friendship_potential(p1, p2, trait_scores),
            "romance": self._calculate_romance_potential(p1, p2, trait_scores),
            "rivalry": self._calculate_rivalry_potential(p1, p2, trait_scores),
            "mentorship": self._calculate_mentorship_potential(p1, p2, trait_scores),
            "collaboration": self._calculate_collaboration_potential(p1, p2, trait_scores)
        }
        
        result = PersonalityCompatibility(
            overall_score=overall_score,
            trait_scores=trait_scores,
            harmony_factors=harmony_factors,
            conflict_factors=conflict_factors,
            relationship_potential=relationship_potential
        )
        
        # Cache result
        self.compatibility_cache[cache_key] = {
            "result": result,
            "time": datetime.utcnow()
        }
        
        return result
    
    def _calculate_friendship_potential(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> float:
        """Calculate potential for friendship"""
        # High agreeableness and similar extraversion are key
        agreeableness_avg = (p1.agreeableness + p2.agreeableness) / 2
        extraversion_similarity = trait_scores[PersonalityTrait.EXTRAVERSION.value]
        
        # Shared interests (openness similarity)
        openness_similarity = trait_scores[PersonalityTrait.OPENNESS.value]
        
        return (agreeableness_avg * 0.4 + 
                extraversion_similarity * 0.3 + 
                openness_similarity * 0.3)
    
    def _calculate_romance_potential(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> float:
        """Calculate potential for romance"""
        # Balance of similarity and complementarity
        overall_similarity = np.mean(list(trait_scores.values()))
        
        # Emotional stability matters
        neuroticism_avg = (p1.neuroticism + p2.neuroticism) / 2
        stability_factor = 1.0 - neuroticism_avg
        
        # Openness to experience
        openness_avg = (p1.openness + p2.openness) / 2
        
        return (overall_similarity * 0.5 + 
                stability_factor * 0.3 + 
                openness_avg * 0.2)
    
    def _calculate_rivalry_potential(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> float:
        """Calculate potential for rivalry"""
        # High ambition (derived trait) and low agreeableness
        ambition1 = p1.derived_traits.get("ambition", 0.5)
        ambition2 = p2.derived_traits.get("ambition", 0.5)
        ambition_factor = (ambition1 + ambition2) / 2
        
        # Low agreeableness
        agreeableness_avg = (p1.agreeableness + p2.agreeableness) / 2
        conflict_factor = 1.0 - agreeableness_avg
        
        # Similar goals but different approaches
        conscientiousness_diff = abs(p1.conscientiousness - p2.conscientiousness)
        
        return (ambition_factor * 0.4 + 
                conflict_factor * 0.4 + 
                conscientiousness_diff * 0.2)
    
    def _calculate_mentorship_potential(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> float:
        """Calculate potential for mentorship"""
        # One should be more experienced (higher conscientiousness)
        experience_diff = abs(p1.conscientiousness - p2.conscientiousness)
        
        # Both should be open to learning
        openness_avg = (p1.openness + p2.openness) / 2
        
        # Good communication (extraversion helps)
        extraversion_avg = (p1.extraversion + p2.extraversion) / 2
        
        return (experience_diff * 0.4 + 
                openness_avg * 0.4 + 
                extraversion_avg * 0.2)
    
    def _calculate_collaboration_potential(
        self,
        p1: PersonalityProfile,
        p2: PersonalityProfile,
        trait_scores: Dict[str, float]
    ) -> float:
        """Calculate potential for collaboration"""
        # High conscientiousness and agreeableness
        conscientiousness_avg = (p1.conscientiousness + p2.conscientiousness) / 2
        agreeableness_avg = (p1.agreeableness + p2.agreeableness) / 2
        
        # Complementary skills (some difference in openness/extraversion)
        openness_diff = abs(p1.openness - p2.openness)
        complementarity = min(openness_diff * 2, 1.0)  # Some difference is good
        
        return (conscientiousness_avg * 0.4 + 
                agreeableness_avg * 0.4 + 
                complementarity * 0.2)
    
    async def predict_behavior(
        self,
        character_id: str,
        situation: Dict[str, Any],
        db: AsyncSession
    ) -> List[BehaviorPrediction]:
        """
        Predict character behavior based on personality.
        
        Args:
            character_id: Character ID
            situation: Dictionary describing the situation
                - context: "social", "conflict", "decision", "stress"
                - participants: List of other character IDs
                - stakes: "low", "medium", "high"
                - options: List of possible actions
        """
        # Get personality profile
        result = await db.execute(
            select(PersonalityProfile).where(PersonalityProfile.character_id == character_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return []
        
        context = situation.get("context", "general")
        stakes = situation.get("stakes", "medium")
        options = situation.get("options", [])
        
        predictions = []
        
        # Analyze each option
        for option in options:
            likelihood = self._calculate_action_likelihood(profile, option, context, stakes)
            reasoning = self._generate_reasoning(profile, option, context)
            factors = self._identify_personality_factors(profile, option)
            
            predictions.append(BehaviorPrediction(
                action_type=option,
                likelihood=likelihood,
                reasoning=reasoning,
                personality_factors=factors
            ))
        
        # Sort by likelihood
        predictions.sort(key=lambda x: x.likelihood, reverse=True)
        
        return predictions
    
    def _calculate_action_likelihood(
        self,
        profile: PersonalityProfile,
        action: str,
        context: str,
        stakes: str
    ) -> float:
        """Calculate likelihood of taking a specific action"""
        base_likelihood = 0.5
        
        # Stakes modifier
        stakes_modifiers = {"low": 0.8, "medium": 1.0, "high": 1.2}
        stakes_mod = stakes_modifiers.get(stakes, 1.0)
        
        # Context-specific calculations
        if context == "social":
            if "approach" in action.lower() or "talk" in action.lower():
                base_likelihood += profile.extraversion * 0.3
                base_likelihood += profile.agreeableness * 0.2
            elif "avoid" in action.lower() or "leave" in action.lower():
                base_likelihood += (1 - profile.extraversion) * 0.3
                base_likelihood += profile.neuroticism * 0.2
        
        elif context == "conflict":
            if "confront" in action.lower() or "fight" in action.lower():
                base_likelihood += (1 - profile.agreeableness) * 0.3
                base_likelihood += profile.extraversion * 0.2
                base_likelihood -= profile.neuroticism * 0.1
            elif "compromise" in action.lower() or "negotiate" in action.lower():
                base_likelihood += profile.agreeableness * 0.3
                base_likelihood += profile.openness * 0.2
        
        elif context == "decision":
            if "careful" in action.lower() or "plan" in action.lower():
                base_likelihood += profile.conscientiousness * 0.4
                base_likelihood -= profile.openness * 0.1
            elif "spontaneous" in action.lower() or "quick" in action.lower():
                base_likelihood += profile.openness * 0.3
                base_likelihood += (1 - profile.conscientiousness) * 0.2
        
        # Apply stakes modifier
        likelihood = base_likelihood * stakes_mod
        
        # Add some randomness for unpredictability
        likelihood += random.gauss(0, 0.05)
        
        return max(0.0, min(1.0, likelihood))
    
    def _generate_reasoning(
        self,
        profile: PersonalityProfile,
        action: str,
        context: str
    ) -> List[str]:
        """Generate reasoning for why character might take an action"""
        reasoning = []
        
        # Add trait-based reasoning
        if profile.extraversion > 0.7:
            reasoning.append("Enjoys social interaction and being around others")
        elif profile.extraversion < 0.3:
            reasoning.append("Prefers solitude and quiet reflection")
        
        if profile.conscientiousness > 0.7:
            reasoning.append("Values careful planning and consideration")
        elif profile.conscientiousness < 0.3:
            reasoning.append("Acts on impulse and intuition")
        
        if profile.agreeableness > 0.7:
            reasoning.append("Seeks harmony and cooperation")
        elif profile.agreeableness < 0.3:
            reasoning.append("Prioritizes personal goals over group harmony")
        
        # Add context-specific reasoning
        if context == "conflict" and profile.neuroticism > 0.6:
            reasoning.append("Feels anxious in confrontational situations")
        
        if context == "social" and profile.openness > 0.6:
            reasoning.append("Curious about new people and experiences")
        
        return reasoning
    
    def _identify_personality_factors(
        self,
        profile: PersonalityProfile,
        action: str
    ) -> Dict[str, float]:
        """Identify which personality factors influence an action"""
        factors = {}
        
        # Analyze action keywords
        action_lower = action.lower()
        
        if any(word in action_lower for word in ["social", "talk", "meet", "group"]):
            factors["extraversion"] = profile.extraversion
        
        if any(word in action_lower for word in ["plan", "careful", "organize", "prepare"]):
            factors["conscientiousness"] = profile.conscientiousness
        
        if any(word in action_lower for word in ["help", "cooperate", "share", "support"]):
            factors["agreeableness"] = profile.agreeableness
        
        if any(word in action_lower for word in ["new", "explore", "creative", "different"]):
            factors["openness"] = profile.openness
        
        if any(word in action_lower for word in ["worry", "avoid", "fear", "stress"]):
            factors["neuroticism"] = profile.neuroticism
        
        return factors
    
    async def create_emotional_state(
        self,
        character_id: str,
        emotion: EmotionalState,
        intensity: float,
        trigger: Dict[str, Any],
        db: AsyncSession
    ) -> EmotionalStateRecord:
        """Create a new emotional state for a character"""
        emotional_state = EmotionalStateRecord(
            character_id=character_id,
            primary_emotion=emotion,
            emotion_intensity=intensity,
            trigger_event=trigger.get("event"),
            trigger_character_id=trigger.get("character_id"),
            context=trigger.get("context", {})
        )
        
        # Calculate emotion blend based on personality
        result = await db.execute(
            select(PersonalityProfile).where(PersonalityProfile.character_id == character_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            emotional_state.emotion_blend = self._calculate_emotion_blend(
                emotion, intensity, profile
            )
        
        db.add(emotional_state)
        await db.commit()
        
        return emotional_state
    
    def _calculate_emotion_blend(
        self,
        primary_emotion: EmotionalState,
        intensity: float,
        profile: PersonalityProfile
    ) -> Dict[str, float]:
        """Calculate secondary emotions based on personality"""
        blend = {primary_emotion.value: intensity}
        
        # Neuroticism affects emotional complexity
        if profile.neuroticism > 0.6:
            # High neuroticism = more complex emotional states
            if primary_emotion == EmotionalState.HAPPY:
                blend[EmotionalState.ANXIOUS.value] = intensity * 0.3
            elif primary_emotion == EmotionalState.ANGRY:
                blend[EmotionalState.SAD.value] = intensity * 0.4
        
        # Openness affects emotional variety
        if profile.openness > 0.7:
            # High openness = more nuanced emotions
            if primary_emotion == EmotionalState.SURPRISED:
                blend[EmotionalState.EXCITED.value] = intensity * 0.5
        
        return blend