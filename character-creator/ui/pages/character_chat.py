"""
Character Chat Interface
========================

Real-time chat interface with emotional memory and engagement tracking.
"""

import streamlit as st
import time
from datetime import datetime
import json
from typing import Dict, List, Any, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.logging_config import logger
from core.models import Character
from services.character_chat_service import CharacterChatService
from services.llm_service import LLMService


def render_character_chat():
    """Render the character chat interface"""
    
    # Check if a character is selected
    if 'selected_character' not in st.session_state:
        st.warning("⚠️ Please select a character from the gallery first!")
        if st.button("Go to Gallery"):
            st.session_state.current_page = 'gallery'
            st.rerun()
        return
    
    character = st.session_state.selected_character
    
    # Initialize chat service if needed
    if 'chat_service' not in st.session_state or st.session_state.get('current_character_id') != character['id']:
        # Create Character object from dict
        char_obj = Character.from_dict(character)
        st.session_state.chat_service = CharacterChatService(char_obj)
        st.session_state.current_character_id = character['id']
        st.session_state.chat_messages = []
        
        # Add initial greeting
        greetings = st.session_state.chat_service.get_conversation_starters()
        if greetings:
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': greetings[0],
                'timestamp': datetime.now(),
                'emotional_state': st.session_state.chat_service.emotional_memory.emotional_state['current_mood']
            })
    
    chat_service = st.session_state.chat_service
    
    # Apply chat-specific CSS
    apply_chat_css()
    
    # Layout: Sidebar for character info, main area for chat
    with st.sidebar:
        render_character_info(character, chat_service)
    
    # Main chat area
    st.markdown(f"### 💬 Chat with {character['name']}")
    
    # Relationship and mood indicators
    render_relationship_bar(chat_service)
    
    # Chat container
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        render_chat_messages()
    
    # Input area
    render_chat_input(chat_service)
    
    # Debug info (if enabled)
    if st.checkbox("🔍 Show Debug Info", value=False):
        render_debug_info(chat_service)


def apply_chat_css():
    """Apply custom CSS for chat interface"""
    st.markdown("""
    <style>
    /* Chat message styles */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        max-width: 70%;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(45deg, #667eea, #764ba2);
        margin-left: auto;
        text-align: right;
    }
    
    .assistant-message {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Emotional state indicator */
    .mood-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .mood-happy { background: rgba(76, 175, 80, 0.3); color: #81c784; }
    .mood-sad { background: rgba(33, 150, 243, 0.3); color: #64b5f6; }
    .mood-angry { background: rgba(244, 67, 54, 0.3); color: #e57373; }
    .mood-neutral { background: rgba(158, 158, 158, 0.3); color: #bdbdbd; }
    .mood-anxious { background: rgba(255, 152, 0, 0.3); color: #ffb74d; }
    .mood-hurt { background: rgba(156, 39, 176, 0.3); color: #ba68c8; }
    
    /* Relationship bar */
    .relationship-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .relationship-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .relationship-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transition: width 0.5s ease;
    }
    
    /* Memory trigger notification */
    .memory-trigger {
        background: rgba(102, 126, 234, 0.2);
        border-left: 3px solid #667eea;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        font-style: italic;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.3rem;
        padding: 1rem;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
        30% { opacity: 1; transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)


def render_character_info(character: Dict, chat_service: CharacterChatService):
    """Render character information in sidebar"""
    # Character avatar and name
    st.markdown(f"## {character.get('avatar', '🎭')} {character['name']}")
    
    # Current emotional state
    emotional_state = chat_service.emotional_memory.emotional_state
    mood = emotional_state['current_mood']
    mood_intensity = emotional_state['mood_intensity']
    
    st.markdown(f"""
    <div class="mood-indicator mood-{mood}">
        Mood: {mood.title()} ({mood_intensity:.0%} intensity)
    </div>
    """, unsafe_allow_html=True)
    
    # Character description
    st.markdown("### About")
    st.write(character.get('description', 'No description available'))
    
    # Personality traits
    if 'personality_traits' in character:
        st.markdown("### Personality")
        traits = character['personality_traits']
        for trait, value in list(traits.items())[:5]:
            st.progress(value, text=f"{trait.title()}: {value:.0%}")
    
    # Relationship status
    relationship = chat_service.emotional_memory.relationship_memory
    st.markdown("### Your Relationship")
    st.write(f"**Status:** {relationship['relationship_stage'].title()}")
    st.progress(relationship['trust_level'], text=f"Trust: {relationship['trust_level']:.0%}")
    
    # Stats
    st.markdown("### Session Stats")
    st.write(f"Messages: {chat_service.message_count}")
    st.write(f"Emotional Investment: {relationship['emotional_investment']:.0%}")
    
    # Engagement score
    engagement = chat_service.behavior_engine.dopamine_engine.user_profile['engagement_score']
    st.progress(engagement, text=f"Engagement: {engagement:.0%}")


def render_relationship_bar(chat_service: CharacterChatService):
    """Render relationship progress bar"""
    relationship = chat_service.emotional_memory.relationship_memory
    trust = relationship['trust_level']
    stage = relationship['relationship_stage']
    
    # Calculate stage progress
    stage_progress = {
        'stranger': 0.1,
        'acquaintance': 0.3,
        'friend': 0.6,
        'close': 0.9
    }
    
    progress = stage_progress.get(stage, 0.1)
    
    st.markdown(f"""
    <div class="relationship-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>Relationship: {stage.title()}</span>
            <span style="color: rgba(255, 255, 255, 0.6);">Trust: {trust:.0%}</span>
        </div>
        <div class="relationship-bar">
            <div class="relationship-fill" style="width: {progress * 100}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_messages():
    """Render chat messages with emotional context"""
    messages = st.session_state.get('chat_messages', [])
    
    for i, msg in enumerate(messages):
        role = msg['role']
        content = msg['content']
        
        # Add emotional state for assistant messages
        if role == 'assistant' and 'emotional_state' in msg:
            mood = msg['emotional_state']
            st.markdown(f'<div class="mood-indicator mood-{mood}">Feeling: {mood}</div>', 
                       unsafe_allow_html=True)
        
        # Check for memory triggers
        if 'memory_trigger' in msg:
            st.markdown(f"""
            <div class="memory-trigger">
                💭 {msg['memory_trigger']}
            </div>
            """, unsafe_allow_html=True)
        
        # Render message
        css_class = "user-message" if role == "user" else "assistant-message"
        st.markdown(f"""
        <div class="chat-message {css_class}">
            {content}
        </div>
        """, unsafe_allow_html=True)


def render_chat_input(chat_service: CharacterChatService):
    """Render chat input area"""
    # Create columns for input and send button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message...",
            key="chat_input",
            label_visibility="collapsed",
            placeholder=f"Say something to {chat_service.character.name}..."
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    # Handle message sending
    if send_button and user_input:
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now()
        })
        
        # Show typing indicator
        with st.spinner(""):
            # Generate response
            response_data = chat_service.generate_response(user_input)
            
            # Check for memory triggers
            memory_trigger = None
            if response_data['memory_triggers']:
                trigger = response_data['memory_triggers'][0]
                memory_trigger = f"Remembers: {trigger.replace('_', ' ').title()}"
            
            # Add assistant response
            st.session_state.chat_messages.append({
                'role': 'assistant',
                'content': response_data['response'],
                'timestamp': datetime.now(),
                'emotional_state': response_data['emotional_state'],
                'memory_trigger': memory_trigger
            })
        
        # Clear input and rerun
        st.rerun()


def render_debug_info(chat_service: CharacterChatService):
    """Render debug information"""
    st.markdown("---")
    st.markdown("### 🔍 Debug Information")
    
    # Get chat summary
    summary = chat_service.get_chat_summary()
    
    # Emotional journey
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Emotional Journey")
        st.json({
            'start_mood': summary['emotional_journey']['start_mood'],
            'current_mood': summary['emotional_journey']['current_mood'],
            'mood_changes': summary['emotional_journey']['mood_changes']
        })
        
        st.markdown("#### Engagement Metrics")
        st.json(summary['engagement_metrics'])
    
    with col2:
        st.markdown("#### Relationship Progress")
        st.json(summary['relationship_progress'])
        
        st.markdown("#### Memory Context")
        memory_context = chat_service.emotional_memory.get_memory_context_for_response()
        st.json({
            'recent_themes': memory_context['recurring_themes'],
            'emotional_debts': memory_context['emotional_debts'],
            'relationship_context': memory_context['relationship_context']
        })


# Export the render function
__all__ = ['render_character_chat']