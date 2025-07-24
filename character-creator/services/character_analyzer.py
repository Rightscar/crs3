"""
Advanced Character Analyzer
===========================

Deep personality and characteristic analysis for unique character creation.
"""

import re
import spacy
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from config.logging_config import logger
from core.exceptions import DocumentProcessingError

class CharacterAnalyzer:
    """Deep character analysis for unique personality extraction"""
    
    def __init__(self):
        """Initialize analysis tools"""
        # Load NLP models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize sentiment analyzer
        try:
            self.sia = SentimentIntensityAnalyzer()
        except:
            nltk.download('vader_lexicon')
            self.sia = SentimentIntensityAnalyzer()
        
        # Character-specific data
        self.character_data = defaultdict(lambda: {
            'speech_patterns': [],
            'emotional_moments': [],
            'actions': [],
            'reactions': [],
            'thoughts': [],
            'physical_descriptions': [],
            'habits': [],
            'relationships': defaultdict(list),
            'conflicts': [],
            'growth_moments': [],
            'unique_phrases': set(),
            'decision_points': [],
            'values': [],
            'fears': [],
            'desires': [],
            'humor_style': [],
            'communication_style': {
                'questions_asked': 0,
                'commands_given': 0,
                'exclamations': 0,
                'interruptions': 0,
                'silence_moments': 0
            }
        })
    
    def analyze_character_depth(self, character_name: str, text: str, 
                              dialogues: List[Dict], contexts: List[str]) -> Dict[str, Any]:
        """
        Perform deep analysis of a character
        
        Args:
            character_name: Character's name
            text: Full document text
            dialogues: Character's dialogues
            contexts: Contexts where character appears
            
        Returns:
            Deep character analysis
        """
        logger.info(f"Deep analysis for character: {character_name}")
        
        # Analyze speech patterns
        speech_analysis = self._analyze_speech_patterns(dialogues)
        
        # Analyze emotional journey
        emotional_profile = self._analyze_emotional_journey(character_name, contexts)
        
        # Extract unique behaviors
        behaviors = self._extract_unique_behaviors(character_name, contexts)
        
        # Analyze relationships dynamics
        relationship_dynamics = self._analyze_relationship_dynamics(character_name, text)
        
        # Extract character arc
        character_arc = self._extract_character_arc(character_name, contexts)
        
        # Identify quirks and mannerisms
        quirks = self._identify_quirks_and_mannerisms(dialogues, contexts)
        
        # Analyze decision-making patterns
        decision_patterns = self._analyze_decision_patterns(character_name, contexts)
        
        # Extract core values and beliefs
        values_beliefs = self._extract_values_and_beliefs(dialogues, contexts)
        
        # Extract character motives and behavioral patterns
        motives_behaviors = self._extract_motives_and_behaviors(character_name, dialogues, contexts)
        
        # Extract interaction patterns (how they treat others)
        interaction_patterns = self._extract_interaction_patterns(character_name, dialogues, contexts)
        
        # Generate unique character DNA
        character_dna = self._generate_character_dna(
            speech_analysis, emotional_profile, behaviors, 
            quirks, values_beliefs, decision_patterns
        )
        
        return {
            'character_dna': character_dna,
            'speech_patterns': speech_analysis,
            'emotional_profile': emotional_profile,
            'unique_behaviors': behaviors,
            'relationship_dynamics': relationship_dynamics,
            'character_arc': character_arc,
            'quirks_mannerisms': quirks,
            'decision_patterns': decision_patterns,
            'values_beliefs': values_beliefs,
            'motives_behaviors': motives_behaviors,
            'interaction_patterns': interaction_patterns,
            'uniqueness_score': self._calculate_uniqueness_score(character_dna)
        }
    
    def _analyze_speech_patterns(self, dialogues: List[Dict]) -> Dict[str, Any]:
        """Analyze unique speech patterns"""
        patterns = {
            'vocabulary_richness': 0,
            'sentence_complexity': 0,
            'favorite_words': Counter(),
            'speech_rhythm': '',
            'verbal_tics': [],
            'communication_style': '',
            'emotional_expression': '',
            'unique_expressions': [],
            'speech_evolution': []
        }
        
        if not dialogues:
            return patterns
        
        all_text = ' '.join([d['text'] for d in dialogues])
        
        # Vocabulary analysis
        words = all_text.lower().split()
        unique_words = set(words)
        patterns['vocabulary_richness'] = len(unique_words) / len(words) if words else 0
        
        # Find favorite words (excluding common ones)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                       'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                       'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                       'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need'}
        
        word_freq = Counter(word for word in words if word not in common_words and len(word) > 3)
        patterns['favorite_words'] = dict(word_freq.most_common(10))
        
        # Analyze sentence patterns
        sentences = [d['text'] for d in dialogues]
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if avg_length < 5:
            patterns['speech_rhythm'] = 'terse'
        elif avg_length < 10:
            patterns['speech_rhythm'] = 'concise'
        elif avg_length < 15:
            patterns['speech_rhythm'] = 'balanced'
        elif avg_length < 20:
            patterns['speech_rhythm'] = 'elaborate'
        else:
            patterns['speech_rhythm'] = 'verbose'
        
        # Detect verbal tics
        tic_patterns = [
            (r'\b(um|uh|er|ah)\b', 'hesitation markers'),
            (r'\b(like)\b(?!.*\blike\b)', 'filler words'),
            (r'\b(you know|I mean|sort of|kind of)\b', 'hedge phrases'),
            (r'\b(actually|basically|literally|honestly)\b', 'emphasis markers'),
            (r'\.{3,}', 'trailing thoughts'),
            (r'\b(well|so|now|then)\b\s*,', 'sentence starters'),
            (r'!{2,}', 'multiple exclamations'),
            (r'\?{2,}', 'multiple questions')
        ]
        
        for pattern, tic_type in tic_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                patterns['verbal_tics'].append(tic_type)
        
        # Analyze emotional expression
        sentiment_scores = []
        for dialogue in dialogues:
            scores = self.sia.polarity_scores(dialogue['text'])
            sentiment_scores.append(scores)
        
        avg_sentiment = {
            'positive': sum(s['pos'] for s in sentiment_scores) / len(sentiment_scores),
            'negative': sum(s['neg'] for s in sentiment_scores) / len(sentiment_scores),
            'neutral': sum(s['neu'] for s in sentiment_scores) / len(sentiment_scores)
        }
        
        if avg_sentiment['positive'] > 0.6:
            patterns['emotional_expression'] = 'optimistic and upbeat'
        elif avg_sentiment['negative'] > 0.4:
            patterns['emotional_expression'] = 'pessimistic or troubled'
        elif avg_sentiment['neutral'] > 0.7:
            patterns['emotional_expression'] = 'reserved and factual'
        else:
            patterns['emotional_expression'] = 'emotionally balanced'
        
        # Find unique expressions
        unique_phrases = []
        for dialogue in dialogues:
            # Look for interesting phrases
            if len(dialogue['text']) > 10:
                doc = self.nlp(dialogue['text'])
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) > 2:
                        unique_phrases.append(chunk.text)
        
        patterns['unique_expressions'] = list(set(unique_phrases))[:10]
        
        return patterns
    
    def _analyze_emotional_journey(self, character_name: str, contexts: List[str]) -> Dict[str, Any]:
        """Analyze character's emotional journey"""
        emotional_profile = {
            'dominant_emotions': Counter(),
            'emotional_range': 0,
            'emotional_triggers': [],
            'coping_mechanisms': [],
            'emotional_growth': [],
            'vulnerability_moments': []
        }
        
        emotion_keywords = {
            'joy': ['happy', 'joyful', 'delighted', 'pleased', 'cheerful', 'elated', 'laughed', 'smiled'],
            'sadness': ['sad', 'depressed', 'melancholy', 'sorrowful', 'cried', 'tears', 'mourned'],
            'anger': ['angry', 'furious', 'enraged', 'irritated', 'frustrated', 'mad', 'shouted', 'yelled'],
            'fear': ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'nervous', 'trembled'],
            'surprise': ['surprised', 'shocked', 'astonished', 'amazed', 'startled', 'stunned'],
            'disgust': ['disgusted', 'repulsed', 'revolted', 'sickened', 'appalled'],
            'love': ['loved', 'adored', 'cherished', 'affection', 'fond', 'devoted'],
            'trust': ['trusted', 'believed', 'confident', 'relied', 'faith'],
            'anticipation': ['anticipated', 'expected', 'hoped', 'looked forward', 'eager']
        }
        
        # Analyze contexts for emotions
        for context in contexts:
            context_lower = context.lower()
            
            # Check for emotion keywords
            for emotion, keywords in emotion_keywords.items():
                for keyword in keywords:
                    if keyword in context_lower and character_name.lower() in context_lower:
                        emotional_profile['dominant_emotions'][emotion] += 1
                        
                        # Extract trigger
                        trigger_match = re.search(
                            rf"(because|when|after|since|as)\s+([^.]+)",
                            context_lower
                        )
                        if trigger_match:
                            emotional_profile['emotional_triggers'].append({
                                'emotion': emotion,
                                'trigger': trigger_match.group(2).strip()
                            })
        
        # Calculate emotional range
        emotions_expressed = len([e for e in emotional_profile['dominant_emotions'] if emotional_profile['dominant_emotions'][e] > 0])
        emotional_profile['emotional_range'] = emotions_expressed / len(emotion_keywords)
        
        # Identify vulnerability moments
        vulnerability_keywords = ['admitted', 'confessed', 'revealed', 'broke down', 'opened up', 'vulnerable']
        for context in contexts:
            if any(keyword in context.lower() for keyword in vulnerability_keywords):
                if character_name.lower() in context.lower():
                    emotional_profile['vulnerability_moments'].append(context[:100] + '...')
        
        return emotional_profile
    
    def _extract_unique_behaviors(self, character_name: str, contexts: List[str]) -> List[Dict[str, Any]]:
        """Extract unique behaviors and actions"""
        behaviors = []
        
        # Action patterns to look for
        action_patterns = [
            # Physical actions
            (r'(\w+ed|ing)\s+(?:his|her|their)?\s*(\w+)', 'physical_action'),
            # Habitual actions
            (r'always\s+(\w+ed|ing)', 'habit'),
            (r'never\s+(\w+ed|ing)', 'avoidance'),
            (r'(?:often|frequently|usually)\s+(\w+ed|ing)', 'tendency'),
            # Unique gestures
            (r'(?:gestured|motioned|signaled)\s+(?:with)?\s*(\w+)', 'gesture'),
            # Reactions
            (r'(?:reacted|responded)\s+(?:by|with)\s+(\w+ing)', 'reaction'),
        ]
        
        for context in contexts:
            if character_name.lower() in context.lower():
                for pattern, behavior_type in action_patterns:
                    matches = re.finditer(pattern, context, re.IGNORECASE)
                    for match in matches:
                        behaviors.append({
                            'type': behavior_type,
                            'action': match.group(0),
                            'context': context[:100]
                        })
        
        # Deduplicate and prioritize unique behaviors
        unique_behaviors = []
        seen_actions = set()
        
        for behavior in behaviors:
            action_key = behavior['action'].lower()
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                unique_behaviors.append(behavior)
        
        return unique_behaviors[:20]  # Top 20 unique behaviors
    
    def _analyze_relationship_dynamics(self, character_name: str, text: str) -> Dict[str, Any]:
        """Analyze how character interacts with others"""
        dynamics = {
            'interaction_styles': defaultdict(list),
            'power_dynamics': {},
            'emotional_connections': {},
            'conflict_patterns': [],
            'alliance_patterns': []
        }
        
        # Find all character interactions
        sentences = text.split('.')
        
        for sentence in sentences:
            if character_name in sentence:
                # Look for other character names (simple heuristic)
                doc = self.nlp(sentence)
                other_persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON" and ent.text != character_name]
                
                for other_person in other_persons:
                    # Analyze interaction type
                    interaction_keywords = {
                        'supportive': ['helped', 'supported', 'encouraged', 'comforted', 'defended'],
                        'antagonistic': ['argued', 'fought', 'opposed', 'challenged', 'confronted'],
                        'romantic': ['loved', 'kissed', 'embraced', 'flirted', 'admired'],
                        'mentoring': ['taught', 'guided', 'advised', 'instructed', 'showed'],
                        'competitive': ['competed', 'rivaled', 'raced', 'challenged', 'outdid'],
                        'collaborative': ['worked with', 'teamed up', 'cooperated', 'partnered']
                    }
                    
                    for interaction_type, keywords in interaction_keywords.items():
                        if any(keyword in sentence.lower() for keyword in keywords):
                            dynamics['interaction_styles'][other_person].append(interaction_type)
        
        return dynamics
    
    def _extract_character_arc(self, character_name: str, contexts: List[str]) -> Dict[str, Any]:
        """Extract character development arc"""
        arc = {
            'starting_point': '',
            'turning_points': [],
            'growth_moments': [],
            'setbacks': [],
            'resolution': '',
            'transformation_score': 0
        }
        
        # Divide contexts into beginning, middle, end
        if len(contexts) >= 3:
            beginning = contexts[:len(contexts)//3]
            middle = contexts[len(contexts)//3:2*len(contexts)//3]
            end = contexts[2*len(contexts)//3:]
            
            # Analyze transformation
            beginning_sentiment = self._get_average_sentiment(beginning)
            end_sentiment = self._get_average_sentiment(end)
            
            arc['transformation_score'] = abs(end_sentiment - beginning_sentiment)
            
            # Look for turning points
            turning_point_keywords = ['realized', 'discovered', 'understood', 'changed', 'decided', 
                                    'transformed', 'became', 'turned into', 'evolved']
            
            for context in middle:
                if any(keyword in context.lower() for keyword in turning_point_keywords):
                    if character_name.lower() in context.lower():
                        arc['turning_points'].append(context[:150])
        
        return arc
    
    def _identify_quirks_and_mannerisms(self, dialogues: List[Dict], contexts: List[str]) -> List[str]:
        """Identify unique quirks and mannerisms"""
        quirks = []
        
        # Speech quirks
        if dialogues:
            all_dialogue = ' '.join([d['text'] for d in dialogues])
            
            # Repetitive phrases
            words = all_dialogue.lower().split()
            word_pairs = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
            pair_freq = Counter(word_pairs)
            
            for pair, count in pair_freq.most_common(5):
                if count > 3 and len(pair) > 5:  # Repeated more than 3 times
                    quirks.append(f"Often says '{pair}'")
            
            # Unique speech patterns
            if '...' in all_dialogue:
                quirks.append("Trails off mid-sentence")
            if all_dialogue.count('!') > len(dialogues) * 0.5:
                quirks.append("Speaks with excessive enthusiasm")
            if all_dialogue.count('?') > len(dialogues) * 0.7:
                quirks.append("Constantly questioning")
            
            # Check for specific patterns
            if re.search(r'\b(hmm|hm|erm)\b', all_dialogue, re.IGNORECASE):
                quirks.append("Makes thinking sounds")
            if re.search(r'^\w+\s*-\s*\w+', all_dialogue, re.MULTILINE):
                quirks.append("Self-interrupts or stutters")
        
        # Physical quirks from contexts
        physical_quirk_patterns = [
            (r'always\s+(\w+ing\s+\w+)', "Has habit of {}"),
            (r'nervously\s+(\w+ed)', "Nervously {}"),
            (r'habitually\s+(\w+ed)', "Habitually {}"),
            (r'constantly\s+(\w+ing)', "Constantly {}"),
            (r'kept\s+(\w+ing)', "Keeps {}"),
        ]
        
        for context in contexts:
            for pattern, template in physical_quirk_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    quirks.append(template.format(match.group(1)))
        
        return list(set(quirks))[:10]  # Return top 10 unique quirks
    
    def _analyze_decision_patterns(self, character_name: str, contexts: List[str]) -> Dict[str, Any]:
        """Analyze how character makes decisions"""
        patterns = {
            'decision_style': '',
            'motivations': Counter(),
            'hesitation_level': 0,
            'impulsivity_score': 0,
            'moral_alignment': ''
        }
        
        decision_keywords = {
            'impulsive': ['suddenly', 'immediately', 'without thinking', 'instantly', 'spontaneously'],
            'calculated': ['carefully', 'planned', 'considered', 'weighed', 'analyzed'],
            'emotional': ['felt', 'heart', 'passion', 'emotion', 'feeling'],
            'logical': ['reasoned', 'logical', 'rational', 'practical', 'sensible'],
            'hesitant': ['hesitated', 'paused', 'uncertain', 'doubtful', 'wavered']
        }
        
        for context in contexts:
            if character_name.lower() in context.lower():
                for style, keywords in decision_keywords.items():
                    if any(keyword in context.lower() for keyword in keywords):
                        patterns['motivations'][style] += 1
        
        # Determine primary decision style
        if patterns['motivations']:
            primary_style = patterns['motivations'].most_common(1)[0][0]
            patterns['decision_style'] = primary_style
        
        return patterns
    
    def _extract_values_and_beliefs(self, dialogues: List[Dict], contexts: List[str]) -> Dict[str, Any]:
        """Extract character's core values and beliefs"""
        values = {
            'stated_values': [],
            'demonstrated_values': [],
            'contradictions': [],
            'moral_code': '',
            'worldview': ''
        }
        
        # Value keywords
        value_keywords = {
            'honor': ['honor', 'dignity', 'respect', 'integrity'],
            'freedom': ['freedom', 'liberty', 'independence', 'choice'],
            'loyalty': ['loyal', 'faithful', 'devoted', 'allegiance'],
            'justice': ['justice', 'fair', 'right', 'wrong', 'moral'],
            'power': ['power', 'control', 'strength', 'dominance'],
            'knowledge': ['knowledge', 'wisdom', 'truth', 'understanding'],
            'love': ['love', 'compassion', 'care', 'kindness'],
            'survival': ['survive', 'protect', 'safety', 'security']
        }
        
        # Analyze dialogues for stated values
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            for value, keywords in value_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    # Look for value statements
                    if any(phrase in text_lower for phrase in ['believe in', 'stand for', 'fight for', 'value']):
                        values['stated_values'].append(value)
        
        # Analyze contexts for demonstrated values
        for context in contexts:
            context_lower = context.lower()
            for value, keywords in value_keywords.items():
                if any(keyword in context_lower for keyword in keywords):
                    values['demonstrated_values'].append(value)
        
        # Determine moral code
        value_counts = Counter(values['stated_values'] + values['demonstrated_values'])
        if value_counts:
            top_values = value_counts.most_common(3)
            values['moral_code'] = f"Guided by {', '.join([v[0] for v in top_values])}"
        
        return values
    
    def _extract_motives_and_behaviors(self, character_name: str, dialogues: List[Dict], 
                                      contexts: List[str]) -> Dict[str, Any]:
        """Extract character's core motives and behavioral patterns"""
        motives = {
            'primary_motivations': [],
            'behavioral_traits': {},
            'manipulation_tactics': [],
            'ego_indicators': 0,
            'empathy_level': 0.5,
            'aggression_style': '',
            'social_tactics': [],
            'hidden_agendas': []
        }
        
        # Analyze for ego/narcissism
        ego_keywords = ['i', 'me', 'my', 'myself', 'mine']
        other_keywords = ['you', 'they', 'them', 'others', 'people']
        
        if dialogues:
            all_dialogue = ' '.join([d['text'].lower() for d in dialogues])
            words = all_dialogue.split()
            
            # Calculate ego ratio
            ego_count = sum(1 for word in words if word in ego_keywords)
            other_count = sum(1 for word in words if word in other_keywords)
            
            if ego_count + other_count > 0:
                ego_ratio = ego_count / (ego_count + other_count)
                motives['ego_indicators'] = ego_ratio
                
                if ego_ratio > 0.7:
                    motives['behavioral_traits']['narcissistic'] = True
                    motives['primary_motivations'].append('self-importance')
                elif ego_ratio > 0.5:
                    motives['behavioral_traits']['self-focused'] = True
                    motives['primary_motivations'].append('personal gain')
        
        # Analyze put-downs and superiority complex
        putdown_patterns = [
            (r'(?:stupid|idiotic|foolish|dumb|ignorant)', 'intellectual_superiority'),
            (r'(?:weak|pathetic|worthless|useless)', 'power_superiority'),
            (r'(?:ugly|disgusting|repulsive)', 'aesthetic_superiority'),
            (r'(?:poor|peasant|common|beneath)', 'class_superiority'),
            (r'(?:naive|simple|childish|immature)', 'maturity_superiority')
        ]
        
        superiority_count = 0
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            for pattern, superiority_type in putdown_patterns:
                if re.search(pattern, text_lower):
                    superiority_count += 1
                    if superiority_type not in motives['behavioral_traits']:
                        motives['behavioral_traits'][superiority_type] = True
                        motives['social_tactics'].append(f'puts others down for {superiority_type.replace("_", " ")}')
        
        # Determine aggression style
        if superiority_count > len(dialogues) * 0.3:
            motives['aggression_style'] = 'actively hostile'
            motives['empathy_level'] = 0.2
        elif superiority_count > len(dialogues) * 0.1:
            motives['aggression_style'] = 'passive-aggressive'
            motives['empathy_level'] = 0.4
        else:
            motives['aggression_style'] = 'non-aggressive'
        
        # Analyze manipulation tactics
        manipulation_patterns = [
            (r'(?:if you really|if you truly|if you cared)', 'guilt-tripping'),
            (r'(?:everyone knows|everyone thinks|people say)', 'social pressure'),
            (r'(?:you always|you never)', 'absolutism'),
            (r'(?:i\'m just saying|just being honest|no offense but)', 'false disclaimers'),
            (r'(?:you\'re too sensitive|can\'t take a joke|overreacting)', 'gaslighting'),
            (r'(?:do this for me|you owe me|after all i\'ve done)', 'emotional blackmail')
        ]
        
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            for pattern, tactic in manipulation_patterns:
                if re.search(pattern, text_lower):
                    if tactic not in motives['manipulation_tactics']:
                        motives['manipulation_tactics'].append(tactic)
        
        # Analyze hidden agendas from contexts
        agenda_keywords = {
            'power': ['control', 'dominate', 'rule', 'command', 'authority'],
            'wealth': ['money', 'rich', 'gold', 'treasure', 'fortune'],
            'revenge': ['revenge', 'payback', 'vengeance', 'retribution'],
            'recognition': ['fame', 'glory', 'recognition', 'admiration', 'respect'],
            'love': ['love', 'affection', 'romance', 'heart', 'passion'],
            'survival': ['survive', 'escape', 'hide', 'protect', 'safety']
        }
        
        for context in contexts:
            if character_name.lower() in context.lower():
                for agenda, keywords in agenda_keywords.items():
                    if any(keyword in context.lower() for keyword in keywords):
                        if agenda not in motives['primary_motivations']:
                            motives['primary_motivations'].append(agenda)
        
        # Analyze empathy level based on helping vs harming behaviors
        helping_keywords = ['helped', 'saved', 'protected', 'comforted', 'supported', 'cared']
        harming_keywords = ['hurt', 'harmed', 'betrayed', 'abandoned', 'ignored', 'mocked']
        
        helping_count = 0
        harming_count = 0
        
        for context in contexts:
            if character_name.lower() in context.lower():
                context_lower = context.lower()
                helping_count += sum(1 for keyword in helping_keywords if keyword in context_lower)
                harming_count += sum(1 for keyword in harming_keywords if keyword in context_lower)
        
        if helping_count + harming_count > 0:
            motives['empathy_level'] = helping_count / (helping_count + harming_count)
        
        return motives
    
    def _extract_interaction_patterns(self, character_name: str, dialogues: List[Dict], 
                                    contexts: List[str]) -> Dict[str, Any]:
        """Extract how character interacts with different types of people"""
        patterns = {
            'default_stance': '',
            'power_dynamics': {},
            'conversation_tactics': [],
            'emotional_manipulation': [],
            'respect_indicators': {},
            'dismissive_behaviors': [],
            'dominance_tactics': []
        }
        
        # Analyze conversation starters
        if dialogues:
            # Check how they start conversations
            first_words = []
            for dialogue in dialogues[:10]:  # First 10 dialogues
                words = dialogue['text'].split()
                if words:
                    first_words.append(words[0].lower())
            
            # Determine default stance
            if any(word in ['listen', 'look', 'now', 'well'] for word in first_words):
                patterns['default_stance'] = 'commanding'
                patterns['conversation_tactics'].append('takes control of conversations')
            elif any(word in ['i', 'my', 'me'] for word in first_words):
                patterns['default_stance'] = 'self-centered'
                patterns['conversation_tactics'].append('makes conversations about themselves')
            elif any(word in ['you', 'your'] for word in first_words):
                patterns['default_stance'] = 'confrontational'
                patterns['conversation_tactics'].append('directly addresses others')
            
            # Analyze interruption patterns
            interruption_markers = ['but', 'actually', 'no,', 'wait', 'hold on', 'excuse me']
            interruption_count = 0
            
            for dialogue in dialogues:
                text_lower = dialogue['text'].lower()
                if any(text_lower.startswith(marker) for marker in interruption_markers):
                    interruption_count += 1
            
            if interruption_count > len(dialogues) * 0.2:
                patterns['dominance_tactics'].append('frequently interrupts others')
                patterns['conversation_tactics'].append('dominates conversations')
        
        # Analyze respect/disrespect indicators
        respect_patterns = {
            'respectful': ['please', 'thank you', 'excuse me', 'pardon', 'sorry'],
            'dismissive': ['whatever', 'who cares', 'so what', 'big deal', 'boring'],
            'condescending': ['obviously', 'clearly', 'simple', 'basic', 'elementary'],
            'sarcastic': ['oh really', 'sure', 'right', 'of course', 'brilliant']
        }
        
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            for pattern_type, keywords in respect_patterns.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        if pattern_type not in patterns['respect_indicators']:
                            patterns['respect_indicators'][pattern_type] = 0
                        patterns['respect_indicators'][pattern_type] += 1
        
        # Determine dismissive behaviors
        if patterns['respect_indicators'].get('dismissive', 0) > 3:
            patterns['dismissive_behaviors'].append('regularly dismisses others\' concerns')
        if patterns['respect_indicators'].get('condescending', 0) > 3:
            patterns['dismissive_behaviors'].append('talks down to people')
        if patterns['respect_indicators'].get('sarcastic', 0) > 5:
            patterns['dismissive_behaviors'].append('uses sarcasm to belittle others')
        
        # Analyze power dynamics
        command_words = ['must', 'will', 'shall', 'need to', 'have to', 'supposed to']
        question_words = ['can i', 'may i', 'could you', 'would you', 'please']
        
        command_count = 0
        question_count = 0
        
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            command_count += sum(1 for word in command_words if word in text_lower)
            question_count += sum(1 for word in question_words if word in text_lower)
        
        if command_count > question_count * 2:
            patterns['power_dynamics']['style'] = 'authoritative'
            patterns['dominance_tactics'].append('gives orders rather than requests')
        elif question_count > command_count * 2:
            patterns['power_dynamics']['style'] = 'submissive'
        else:
            patterns['power_dynamics']['style'] = 'balanced'
        
        # Emotional manipulation patterns
        emotional_patterns = [
            (r'you\'re making me', 'blame-shifting'),
            (r'look what you\'ve done', 'guilt-inducing'),
            (r'i\'m disappointed in you', 'shame-inducing'),
            (r'after everything i', 'obligation-creating'),
            (r'you don\'t care about', 'emotional accusation'),
            (r'if you loved me', 'love manipulation')
        ]
        
        for dialogue in dialogues:
            text_lower = dialogue['text'].lower()
            for pattern, manipulation_type in emotional_patterns:
                if re.search(pattern, text_lower):
                    if manipulation_type not in patterns['emotional_manipulation']:
                        patterns['emotional_manipulation'].append(manipulation_type)
        
        return patterns
    
    def _generate_character_dna(self, speech_analysis: Dict, emotional_profile: Dict,
                               behaviors: List, quirks: List, values: Dict, 
                               decision_patterns: Dict) -> Dict[str, Any]:
        """Generate unique character DNA profile"""
        dna = {
            'core_identity': '',
            'personality_matrix': {},
            'behavioral_fingerprint': [],
            'emotional_signature': '',
            'communication_dna': '',
            'value_system': '',
            'unique_traits': [],
            'character_essence': ''
        }
        
        # Build core identity
        identity_parts = []
        
        # Add emotional signature
        if emotional_profile['dominant_emotions']:
            top_emotion = emotional_profile['dominant_emotions'].most_common(1)[0][0]
            identity_parts.append(f"primarily {top_emotion}")
        
        # Add communication style
        if speech_analysis['speech_rhythm']:
            identity_parts.append(f"{speech_analysis['speech_rhythm']} speaker")
        
        # Add decision style
        if decision_patterns['decision_style']:
            identity_parts.append(f"{decision_patterns['decision_style']} decision-maker")
        
        dna['core_identity'] = "A " + ", ".join(identity_parts) if identity_parts else "A complex individual"
        
        # Create personality matrix (0-1 scores)
        dna['personality_matrix'] = {
            'introversion_extraversion': self._calculate_social_score(speech_analysis, behaviors),
            'thinking_feeling': self._calculate_thinking_feeling_score(decision_patterns, emotional_profile),
            'judging_perceiving': self._calculate_judging_perceiving_score(behaviors, decision_patterns),
            'sensing_intuition': self._calculate_sensing_intuition_score(speech_analysis, values),
            'stability_neuroticism': self._calculate_stability_score(emotional_profile, quirks),
            'tradition_innovation': self._calculate_tradition_innovation_score(values, behaviors),
            'cooperation_competition': self._calculate_cooperation_score(behaviors),
            'optimism_pessimism': self._calculate_optimism_score(speech_analysis, emotional_profile)
        }
        
        # Create behavioral fingerprint
        dna['behavioral_fingerprint'] = [
            behavior['action'] for behavior in behaviors[:5]
        ]
        
        # Emotional signature
        if emotional_profile['emotional_range'] > 0.7:
            dna['emotional_signature'] = "Emotionally expressive and varied"
        elif emotional_profile['emotional_range'] > 0.4:
            dna['emotional_signature'] = "Balanced emotional expression"
        else:
            dna['emotional_signature'] = "Emotionally reserved"
        
        # Communication DNA
        comm_traits = []
        if speech_analysis['verbal_tics']:
            comm_traits.append(f"uses {', '.join(speech_analysis['verbal_tics'][:2])}")
        if speech_analysis['favorite_words']:
            top_words = list(speech_analysis['favorite_words'].keys())[:3]
            comm_traits.append(f"frequently says {', '.join(top_words)}")
        
        dna['communication_dna'] = "; ".join(comm_traits) if comm_traits else "Standard communication"
        
        # Value system
        if values['moral_code']:
            dna['value_system'] = values['moral_code']
        else:
            dna['value_system'] = "Undefined moral compass"
        
        # Unique traits (combination of quirks and behaviors)
        dna['unique_traits'] = quirks[:5]
        
        # Character essence (one-line summary)
        essence_parts = []
        if dna['personality_matrix']['optimism_pessimism'] > 0.7:
            essence_parts.append("optimistic")
        elif dna['personality_matrix']['optimism_pessimism'] < 0.3:
            essence_parts.append("pessimistic")
        
        if dna['personality_matrix']['thinking_feeling'] > 0.7:
            essence_parts.append("logical")
        elif dna['personality_matrix']['thinking_feeling'] < 0.3:
            essence_parts.append("emotional")
        
        if quirks:
            essence_parts.append(f"character who {quirks[0].lower()}")
        
        dna['character_essence'] = " ".join(essence_parts).capitalize() if essence_parts else "Complex character"
        
        return dna
    
    def _calculate_social_score(self, speech_analysis: Dict, behaviors: List) -> float:
        """Calculate introversion/extraversion score (0=introvert, 1=extravert)"""
        score = 0.5  # Start neutral
        
        # Speech indicators
        if speech_analysis['speech_rhythm'] in ['verbose', 'elaborate']:
            score += 0.2
        elif speech_analysis['speech_rhythm'] in ['terse', 'concise']:
            score -= 0.2
        
        # Behavioral indicators
        social_behaviors = sum(1 for b in behaviors if any(
            word in b['action'].lower() for word in ['talked', 'spoke', 'chatted', 'socialized']
        ))
        
        if social_behaviors > 5:
            score += 0.2
        elif social_behaviors < 2:
            score -= 0.2
        
        return max(0, min(1, score))
    
    def _calculate_thinking_feeling_score(self, decision_patterns: Dict, emotional_profile: Dict) -> float:
        """Calculate thinking/feeling score (0=feeling, 1=thinking)"""
        score = 0.5
        
        # Decision style
        if decision_patterns['decision_style'] == 'logical':
            score += 0.3
        elif decision_patterns['decision_style'] == 'emotional':
            score -= 0.3
        
        # Emotional expression
        if emotional_profile['emotional_range'] > 0.7:
            score -= 0.2
        elif emotional_profile['emotional_range'] < 0.3:
            score += 0.2
        
        return max(0, min(1, score))
    
    def _calculate_judging_perceiving_score(self, behaviors: List, decision_patterns: Dict) -> float:
        """Calculate judging/perceiving score (0=perceiving, 1=judging)"""
        score = 0.5
        
        # Decision patterns
        if decision_patterns['decision_style'] == 'calculated':
            score += 0.3
        elif decision_patterns['decision_style'] == 'impulsive':
            score -= 0.3
        
        # Look for planning behaviors
        planning_behaviors = sum(1 for b in behaviors if any(
            word in b['action'].lower() for word in ['planned', 'organized', 'scheduled', 'prepared']
        ))
        
        if planning_behaviors > 3:
            score += 0.2
        
        return max(0, min(1, score))
    
    def _calculate_sensing_intuition_score(self, speech_analysis: Dict, values: Dict) -> float:
        """Calculate sensing/intuition score (0=sensing, 1=intuition)"""
        score = 0.5
        
        # Abstract language use
        if speech_analysis['vocabulary_richness'] > 0.7:
            score += 0.2
        
        # Value orientation
        if 'knowledge' in values['demonstrated_values'] or 'wisdom' in values['demonstrated_values']:
            score += 0.2
        
        return max(0, min(1, score))
    
    def _calculate_stability_score(self, emotional_profile: Dict, quirks: List) -> float:
        """Calculate emotional stability score (0=neurotic, 1=stable)"""
        score = 0.7  # Start slightly stable
        
        # Emotional range
        if emotional_profile['emotional_range'] > 0.8:
            score -= 0.3
        
        # Nervous quirks
        nervous_quirks = sum(1 for q in quirks if any(
            word in q.lower() for word in ['nervous', 'anxious', 'worried', 'stressed']
        ))
        
        if nervous_quirks > 2:
            score -= 0.3
        
        return max(0, min(1, score))
    
    def _calculate_tradition_innovation_score(self, values: Dict, behaviors: List) -> float:
        """Calculate tradition/innovation score (0=traditional, 1=innovative)"""
        score = 0.5
        
        # Value indicators
        if 'honor' in values['demonstrated_values'] or 'loyalty' in values['demonstrated_values']:
            score -= 0.2
        if 'freedom' in values['demonstrated_values'] or 'independence' in values['demonstrated_values']:
            score += 0.2
        
        return max(0, min(1, score))
    
    def _calculate_cooperation_score(self, behaviors: List) -> float:
        """Calculate cooperation/competition score (0=competitive, 1=cooperative)"""
        score = 0.5
        
        # Cooperative behaviors
        coop_behaviors = sum(1 for b in behaviors if any(
            word in b['action'].lower() for word in ['helped', 'supported', 'shared', 'collaborated']
        ))
        
        # Competitive behaviors
        comp_behaviors = sum(1 for b in behaviors if any(
            word in b['action'].lower() for word in ['competed', 'won', 'beat', 'challenged']
        ))
        
        if coop_behaviors > comp_behaviors:
            score += 0.3
        elif comp_behaviors > coop_behaviors:
            score -= 0.3
        
        return max(0, min(1, score))
    
    def _calculate_optimism_score(self, speech_analysis: Dict, emotional_profile: Dict) -> float:
        """Calculate optimism/pessimism score (0=pessimistic, 1=optimistic)"""
        score = 0.5
        
        # Emotional expression
        if speech_analysis['emotional_expression'] == 'optimistic and upbeat':
            score += 0.3
        elif speech_analysis['emotional_expression'] == 'pessimistic or troubled':
            score -= 0.3
        
        # Positive emotions
        positive_emotions = emotional_profile['dominant_emotions'].get('joy', 0) + \
                          emotional_profile['dominant_emotions'].get('love', 0) + \
                          emotional_profile['dominant_emotions'].get('trust', 0)
        
        negative_emotions = emotional_profile['dominant_emotions'].get('sadness', 0) + \
                          emotional_profile['dominant_emotions'].get('anger', 0) + \
                          emotional_profile['dominant_emotions'].get('fear', 0)
        
        if positive_emotions > negative_emotions:
            score += 0.2
        elif negative_emotions > positive_emotions:
            score -= 0.2
        
        return max(0, min(1, score))
    
    def _get_average_sentiment(self, texts: List[str]) -> float:
        """Get average sentiment score for texts"""
        if not texts:
            return 0.0
        
        scores = []
        for text in texts:
            sentiment = self.sia.polarity_scores(text)
            scores.append(sentiment['compound'])
        
        return sum(scores) / len(scores)
    
    def _calculate_uniqueness_score(self, character_dna: Dict) -> float:
        """Calculate how unique this character is"""
        score = 0.0
        
        # Unique traits contribute most
        score += len(character_dna['unique_traits']) * 0.1
        
        # Behavioral fingerprint
        score += len(character_dna['behavioral_fingerprint']) * 0.05
        
        # Personality matrix extremes
        for trait, value in character_dna['personality_matrix'].items():
            if value < 0.2 or value > 0.8:  # Extreme values
                score += 0.1
        
        # Communication DNA
        if character_dna['communication_dna'] != "Standard communication":
            score += 0.2
        
        return min(1.0, score)