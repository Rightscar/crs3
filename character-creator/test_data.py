"""
Test Data for Character Creator
===============================

Sample characters for testing the integrated systems.
"""

import streamlit as st
from datetime import datetime

def load_test_characters():
    """Load test characters into session state"""
    
    test_characters = [
        {
            'id': 'char_001',
            'name': 'Elizabeth Bennet',
            'avatar': '👩‍🎨',
            'role': 'Protagonist',
            'description': 'Witty and independent young woman who values intelligence and integrity over wealth and status.',
            'source_document': {
                'filename': 'pride_and_prejudice.pdf',
                'title': 'Pride and Prejudice'
            },
            'personality': {
                'traits': {
                    'openness': 0.8,
                    'conscientiousness': 0.7,
                    'extraversion': 0.6,
                    'agreeableness': 0.7,
                    'neuroticism': 0.3,
                    'humor': 0.8,
                    'formality': 0.6,
                    'creativity': 0.7
                },
                'speaking_style': 'eloquent',
                'vocabulary_level': 'advanced',
                'quirks': ['Uses wit as defense', 'Questions social norms'],
                'catchphrases': ['I dearly love to laugh', 'My courage always rises with every attempt to intimidate me']
            },
            'motives_behaviors': {
                'primary_motivations': ['independence', 'true love', 'family loyalty'],
                'behavioral_traits': {
                    'quick-witted': True,
                    'prejudiced': True,
                    'loyal': True
                },
                'manipulation_tactics': [],
                'empathy_level': 0.8,
                'ego_indicators': 0.3,
                'aggression_style': 'verbal sparring'
            },
            'key_quotes': [
                'I could easily forgive his pride, if he had not mortified mine.',
                'There is a stubbornness about me that never can bear to be frightened at the will of others.'
            ],
            'dialogue_count': 127,
            'mention_count': 342,
            'importance_score': 0.95,
            'uniqueness_score': 0.85,
            'character_dna': {
                'character_essence': 'Independent spirit who challenges societal expectations'
            },
            'knowledge_base': {
                'total_chunks': 150,
                'topics': ['marriage', 'social class', 'family', 'love', 'prejudice']
            }
        },
        {
            'id': 'char_002',
            'name': 'Mr. Darcy',
            'avatar': '🎩',
            'role': 'Love Interest',
            'description': 'Proud, wealthy gentleman who struggles with his feelings and social prejudices.',
            'source_document': {
                'filename': 'pride_and_prejudice.pdf',
                'title': 'Pride and Prejudice'
            },
            'personality': {
                'traits': {
                    'openness': 0.4,
                    'conscientiousness': 0.9,
                    'extraversion': 0.2,
                    'agreeableness': 0.4,
                    'neuroticism': 0.3,
                    'humor': 0.3,
                    'formality': 0.9,
                    'creativity': 0.5
                },
                'speaking_style': 'formal',
                'vocabulary_level': 'advanced',
                'quirks': ['Uncomfortable in social settings', 'Brutally honest'],
                'catchphrases': ['My good opinion once lost is lost forever', 'I cannot forget the follies and vices of others']
            },
            'motives_behaviors': {
                'primary_motivations': ['honor', 'duty', 'genuine connection'],
                'behavioral_traits': {
                    'prideful': True,
                    'reserved': True,
                    'loyal': True,
                    'judgmental': True
                },
                'manipulation_tactics': ['cold silence', 'social pressure'],
                'empathy_level': 0.5,
                'ego_indicators': 0.8,
                'aggression_style': 'cold dismissal',
                'superiority_complex': 0.7
            },
            'interaction_patterns': {
                'default_stance': 'aloof',
                'dismissive_behaviors': ['Ignores those beneath his station', 'Gives cutting remarks'],
                'emotional_manipulation': ['withdrawal', 'silent treatment']
            },
            'key_quotes': [
                'She is tolerable, but not handsome enough to tempt me.',
                'My feelings will not be repressed. You must allow me to tell you how ardently I admire and love you.'
            ],
            'dialogue_count': 89,
            'mention_count': 298,
            'importance_score': 0.9,
            'uniqueness_score': 0.75,
            'character_dna': {
                'character_essence': 'Proud aristocrat learning humility through love'
            },
            'knowledge_base': {
                'total_chunks': 120,
                'topics': ['estate management', 'social hierarchy', 'honor', 'family duty']
            }
        },
        {
            'id': 'char_003',
            'name': 'Sherlock Holmes',
            'avatar': '🔍',
            'role': 'Detective',
            'description': 'Brilliant but eccentric detective with extraordinary deductive abilities and little patience for ordinary minds.',
            'source_document': {
                'filename': 'sherlock_holmes.pdf',
                'title': 'The Adventures of Sherlock Holmes'
            },
            'personality': {
                'traits': {
                    'openness': 0.9,
                    'conscientiousness': 0.3,
                    'extraversion': 0.3,
                    'agreeableness': 0.2,
                    'neuroticism': 0.6,
                    'humor': 0.4,
                    'formality': 0.5,
                    'creativity': 0.95
                },
                'speaking_style': 'precise',
                'vocabulary_level': 'advanced',
                'quirks': ['Plays violin when thinking', 'Experiments with chemicals', 'Ignores social pleasantries'],
                'catchphrases': ['Elementary, my dear Watson', 'When you eliminate the impossible, whatever remains must be the truth']
            },
            'motives_behaviors': {
                'primary_motivations': ['intellectual stimulation', 'solving puzzles', 'proving superiority'],
                'behavioral_traits': {
                    'arrogant': True,
                    'obsessive': True,
                    'brilliant': True,
                    'dismissive': True,
                    'narcissistic': True
                },
                'manipulation_tactics': ['intellectual intimidation', 'condescension', 'dramatic reveals'],
                'empathy_level': 0.2,
                'ego_indicators': 0.9,
                'aggression_style': 'intellectual humiliation',
                'superiority_complex': 0.95
            },
            'interaction_patterns': {
                'default_stance': 'superior',
                'dismissive_behaviors': [
                    'Calls others idiots',
                    'Explains obvious things condescendingly',
                    'Ignores social niceties'
                ],
                'emotional_manipulation': ['making others feel stupid', 'withholding information for dramatic effect']
            },
            'key_quotes': [
                'I am a brain, Watson. The rest of me is a mere appendix.',
                'Mediocrity knows nothing higher than itself; but talent instantly recognizes genius.'
            ],
            'dialogue_count': 203,
            'mention_count': 567,
            'importance_score': 1.0,
            'uniqueness_score': 0.95,
            'character_dna': {
                'character_essence': 'Genius detective with no patience for inferior minds'
            },
            'knowledge_base': {
                'total_chunks': 250,
                'topics': ['deduction', 'crime', 'chemistry', 'disguises', 'London', 'criminal psychology']
            }
        }
    ]
    
    # Set test data in session state
    st.session_state.extracted_characters = test_characters
    st.session_state.document_info = {
        'filename': 'classic_literature_collection.pdf',
        'word_count': 125000,
        'page_count': 450,
        'upload_time': datetime.now()
    }
    
    return test_characters


# Auto-load test data when imported
if 'extracted_characters' not in st.session_state:
    load_test_characters()