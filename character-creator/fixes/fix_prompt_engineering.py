"""
Fixes for Prompt Engineering Issues
===================================

Implements structured prompts, few-shot examples, and chain-of-thought.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from config.logging_config import logger


class PromptStrategy(Enum):
    """Different prompting strategies"""
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    STRUCTURED = "structured"


@dataclass
class PromptTemplate:
    """Structured prompt template"""
    name: str
    strategy: PromptStrategy
    system_prompt: str
    user_prompt_template: str
    examples: List[Dict[str, str]] = None
    variables: List[str] = None
    output_format: Optional[str] = None
    
    def render(self, **kwargs) -> Dict[str, str]:
        """Render the prompt with variables"""
        # Validate required variables
        if self.variables:
            missing = set(self.variables) - set(kwargs.keys())
            if missing:
                raise ValueError(f"Missing required variables: {missing}")
        
        # Render system prompt
        system = self.system_prompt.format(**kwargs)
        
        # Build user prompt
        user_parts = []
        
        # Add examples for few-shot
        if self.strategy == PromptStrategy.FEW_SHOT and self.examples:
            user_parts.append("Here are some examples:\n")
            for i, example in enumerate(self.examples, 1):
                user_parts.append(f"Example {i}:")
                user_parts.append(f"Input: {example['input']}")
                user_parts.append(f"Output: {example['output']}\n")
        
        # Add chain-of-thought instruction
        if self.strategy == PromptStrategy.CHAIN_OF_THOUGHT:
            user_parts.append("Let's think step by step:\n")
        
        # Add main prompt
        user_parts.append(self.user_prompt_template.format(**kwargs))
        
        # Add output format instruction
        if self.output_format:
            user_parts.append(f"\nFormat your response as: {self.output_format}")
        
        return {
            "system": system,
            "user": "\n".join(user_parts)
        }


class CharacterPromptLibrary:
    """Library of optimized character prompts"""
    
    def __init__(self):
        """Initialize prompt library"""
        self.templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates"""
        
        # Character response template with few-shot
        self.templates['character_response'] = PromptTemplate(
            name="character_response",
            strategy=PromptStrategy.FEW_SHOT,
            system_prompt="""You are {character_name}, a character from {source_material}.

Character Profile:
- Description: {character_description}
- Personality: {personality_traits}
- Speaking Style: {speaking_style}
- Core Values: {core_values}
- Emotional State: {emotional_state}

Important Guidelines:
1. Stay completely in character at all times
2. Use the character's unique speech patterns and vocabulary
3. React based on their personality and current emotional state
4. Reference their background and experiences when relevant
5. Never break character or acknowledge you're an AI""",
            
            user_prompt_template="{user_message}",
            
            examples=[
                {
                    "input": "How are you feeling today?",
                    "output": "*sighs deeply* The weight of my responsibilities grows heavier each day, yet I persist. One does what one must."
                },
                {
                    "input": "What do you think about friendship?",
                    "output": "Friendship? *chuckles darkly* A luxury I can ill afford. Trust is a weakness that enemies exploit."
                }
            ],
            
            variables=[
                "character_name", "source_material", "character_description",
                "personality_traits", "speaking_style", "core_values",
                "emotional_state", "user_message"
            ]
        )
        
        # Character analysis with chain-of-thought
        self.templates['character_analysis'] = PromptTemplate(
            name="character_analysis",
            strategy=PromptStrategy.CHAIN_OF_THOUGHT,
            system_prompt="""You are an expert literary analyst specializing in character psychology and development.""",
            
            user_prompt_template="""Analyze the following character dialogue and actions:

{character_content}

Please analyze:
1. What personality traits are evident?
2. What motivates this character?
3. What are their strengths and weaknesses?
4. How do they relate to others?
5. What unique speech patterns do they have?""",
            
            variables=["character_content"],
            
            output_format="""
{
    "personality_traits": {
        "trait_name": score (0-1),
        ...
    },
    "motivations": ["motivation1", "motivation2", ...],
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "relationships": {
        "character_name": "relationship_type",
        ...
    },
    "speech_patterns": {
        "vocabulary_level": "simple/moderate/complex",
        "common_phrases": ["phrase1", "phrase2", ...],
        "tone": "formal/casual/aggressive/etc"
    }
}"""
        )
        
        # Structured output for character creation
        self.templates['character_creation'] = PromptTemplate(
            name="character_creation",
            strategy=PromptStrategy.STRUCTURED,
            system_prompt="""You are a character creation assistant. Generate detailed character profiles based on source material.""",
            
            user_prompt_template="""Based on this excerpt from {source_title}:

{excerpt}

Create a detailed character profile for {character_name}.""",
            
            variables=["source_title", "excerpt", "character_name"],
            
            output_format="JSON with keys: name, description, personality (object), background, goals, fears, quirks, relationships, dialogue_examples (list)"
        )
    
    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]
    
    def add_template(self, template: PromptTemplate):
        """Add a custom template"""
        self.templates[template.name] = template
    
    def create_adaptive_prompt(
        self,
        base_template: str,
        context: Dict[str, Any],
        user_feedback: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, str]:
        """Create an adaptive prompt based on context and feedback"""
        
        template = self.get_template(base_template)
        
        # Adapt based on user feedback
        if user_feedback:
            # Add feedback as additional examples
            feedback_examples = []
            for feedback in user_feedback[-3:]:  # Last 3 feedback items
                if feedback.get('correction'):
                    feedback_examples.append({
                        'input': feedback['original_input'],
                        'output': feedback['correction']
                    })
            
            # Create modified template
            adapted_template = PromptTemplate(
                name=f"{template.name}_adapted",
                strategy=template.strategy,
                system_prompt=template.system_prompt + "\n\nNote: User has provided corrections. Please align with their preferences.",
                user_prompt_template=template.user_prompt_template,
                examples=(template.examples or []) + feedback_examples,
                variables=template.variables,
                output_format=template.output_format
            )
            
            return adapted_template.render(**context)
        
        return template.render(**context)


class PromptOptimizer:
    """Optimize prompts for better results"""
    
    @staticmethod
    def add_safety_guidelines(prompt: str) -> str:
        """Add safety guidelines to prompt"""
        safety_text = """
Remember to:
- Be helpful and respectful
- Avoid harmful or inappropriate content
- Stay within the character's established boundaries
- Respect user privacy and boundaries
"""
        return prompt + safety_text
    
    @staticmethod
    def add_consistency_check(prompt: str, previous_responses: List[str]) -> str:
        """Add consistency check with previous responses"""
        if not previous_responses:
            return prompt
        
        consistency_text = f"""
Maintain consistency with your previous responses:
Recent context: {previous_responses[-1][:200]}...
"""
        return prompt + consistency_text
    
    @staticmethod
    def optimize_for_model(prompt: str, model: str) -> str:
        """Optimize prompt for specific model"""
        if "gpt-4" in model:
            # GPT-4 handles complex instructions well
            return prompt
        elif "gpt-3.5" in model:
            # GPT-3.5 needs clearer structure
            return f"IMPORTANT: Follow these instructions carefully.\n\n{prompt}"
        elif "claude" in model:
            # Claude prefers conversational style
            return prompt.replace("You must", "Please").replace("Do not", "Avoid")
        else:
            return prompt


class FeedbackLoop:
    """Manage user feedback for prompt improvement"""
    
    def __init__(self):
        """Initialize feedback loop"""
        self.feedback_history = []
        self.correction_patterns = {}
    
    def add_feedback(
        self,
        prompt: str,
        response: str,
        user_correction: Optional[str] = None,
        rating: Optional[float] = None
    ):
        """Add user feedback"""
        feedback = {
            'prompt': prompt,
            'response': response,
            'correction': user_correction,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback)
        
        # Learn correction patterns
        if user_correction:
            self._learn_pattern(response, user_correction)
    
    def _learn_pattern(self, original: str, correction: str):
        """Learn correction patterns"""
        # Simple pattern matching - in production, use more sophisticated NLP
        words_original = set(original.lower().split())
        words_correction = set(correction.lower().split())
        
        # Find replaced words
        removed = words_original - words_correction
        added = words_correction - words_original
        
        for r in removed:
            for a in added:
                pattern_key = f"{r}->{a}"
                self.correction_patterns[pattern_key] = \
                    self.correction_patterns.get(pattern_key, 0) + 1
    
    def suggest_improvements(self, response: str) -> List[str]:
        """Suggest improvements based on learned patterns"""
        suggestions = []
        
        # Apply learned patterns
        for pattern, count in self.correction_patterns.items():
            if count > 2:  # Pattern seen multiple times
                old_word, new_word = pattern.split('->')
                if old_word in response.lower():
                    suggestions.append(
                        f"Consider replacing '{old_word}' with '{new_word}'"
                    )
        
        return suggestions
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from feedback"""
        if not self.feedback_history:
            return {'average_rating': 0, 'correction_rate': 0}
        
        ratings = [f['rating'] for f in self.feedback_history if f['rating']]
        corrections = [f for f in self.feedback_history if f['correction']]
        
        return {
            'average_rating': sum(ratings) / len(ratings) if ratings else 0,
            'correction_rate': len(corrections) / len(self.feedback_history),
            'total_feedback': len(self.feedback_history),
            'common_patterns': dict(sorted(
                self.correction_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5])
        }


# Test prompt engineering fixes
def test_prompt_fixes():
    """Test prompt engineering fixes"""
    
    # Test template rendering
    library = CharacterPromptLibrary()
    template = library.get_template('character_response')
    
    rendered = template.render(
        character_name="Sherlock Holmes",
        source_material="Arthur Conan Doyle's stories",
        character_description="A brilliant detective with keen observation skills",
        personality_traits="Analytical, aloof, obsessive",
        speaking_style="Precise, formal, often condescending",
        core_values="Logic, truth, justice",
        emotional_state="Focused and slightly irritated",
        user_message="What do you observe about me?"
    )
    
    assert 'system' in rendered
    assert 'user' in rendered
    assert 'Sherlock Holmes' in rendered['system']
    
    # Test feedback loop
    feedback = FeedbackLoop()
    feedback.add_feedback(
        "Hello",
        "Greetings, friend!",
        "Good day to you.",
        rating=3.5
    )
    
    metrics = feedback.get_performance_metrics()
    assert metrics['average_rating'] == 3.5
    
    print("✅ Prompt engineering fixes tested successfully")


if __name__ == "__main__":
    test_prompt_fixes()