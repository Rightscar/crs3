"""
Character Gallery Page
======================

Display all extracted characters from uploaded documents.
"""

import streamlit as st
from typing import List, Dict, Any
import json

from config.logging_config import logger
from core.database import db
from core.models import Character, CharacterStatus

def render_character_gallery():
    """Render the character gallery page"""
    
    st.markdown("""
    <style>
    /* Character card styles */
    .character-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
        padding: 1rem 0;
    }
    
    .character-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .character-card:hover {
        transform: translateY(-5px);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .character-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .character-card:hover::before {
        transform: scaleX(1);
    }
    
    .character-avatar {
        font-size: 3rem;
        text-align: center;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
    }
    
    .character-name {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    
    .character-role {
        font-size: 0.875rem;
        color: #667eea;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    
    .character-description {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.5;
        margin-bottom: 1rem;
        max-height: 3rem;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .character-dna {
        font-size: 0.75rem;
        color: #667eea;
        font-style: italic;
        margin-bottom: 0.5rem;
    }
    
    .quirk-badge {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.5);
        border-radius: 12px;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
        font-size: 0.7rem;
        color: #a8b9ff;
    }
    
    .uniqueness-indicator {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 50%;
        width: 2.5rem;
        height: 2.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.875rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    
    .character-stats {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .importance-bar {
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        margin-top: 0.5rem;
        overflow: hidden;
    }
    
    .importance-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
        transition: width 0.5s ease;
    }
    
    .filter-section {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .document-selector {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .document-selector:hover {
        border-color: rgba(102, 126, 234, 0.5);
        background: rgba(102, 126, 234, 0.1);
    }
    
    .document-selector.active {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.2);
    }
    
    .no-characters {
        text-align: center;
        padding: 4rem 2rem;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .upload-prompt {
        background: rgba(102, 126, 234, 0.1);
        border: 2px dashed rgba(102, 126, 234, 0.5);
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get extracted characters from session state
    extracted_characters = st.session_state.get('extracted_characters', [])
    
    if not extracted_characters:
        # No characters yet - show upload prompt
        st.markdown("""
        <div class="upload-prompt">
            <h2>📚 No Characters Found</h2>
            <p>Upload a book or document to discover all the characters within!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📤 Upload Document", use_container_width=True):
            st.session_state.current_page = 'create'
            st.rerun()
        
        return
    
    # Show document info
    doc_info = st.session_state.get('document_info', {})
    if doc_info:
        st.markdown(f"""
        <div class="document-selector active">
            <h4>📖 {doc_info.get('filename', 'Unknown Document')}</h4>
            <p style="margin: 0.5rem 0; font-size: 0.875rem; color: rgba(255, 255, 255, 0.7);">
                {doc_info.get('word_count', 0):,} words • {doc_info.get('page_count', 0)} pages
            </p>
            <p style="margin: 0; font-size: 0.875rem; color: #667eea;">
                {len(extracted_characters)} characters discovered
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Filter controls
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Role filter
            all_roles = list(set(char['role'] for char in extracted_characters))
            selected_role = st.selectbox(
                "Filter by Role",
                ["All Roles"] + all_roles,
                key="role_filter"
            )
        
        with col2:
            # Importance filter
            min_importance = st.slider(
                "Minimum Importance",
                0.0, 1.0, 0.0, 0.1,
                key="importance_filter"
            )
        
        with col3:
            # Sort options
            sort_by = st.selectbox(
                "Sort by",
                ["Importance", "Name", "Mentions"],
                key="sort_by"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter and sort characters
    filtered_characters = extracted_characters
    
    if selected_role != "All Roles":
        filtered_characters = [
            char for char in filtered_characters 
            if char['role'] == selected_role
        ]
    
    filtered_characters = [
        char for char in filtered_characters 
        if char['importance_score'] >= min_importance
    ]
    
    # Sort
    if sort_by == "Importance":
        filtered_characters.sort(key=lambda x: x['importance_score'], reverse=True)
    elif sort_by == "Name":
        filtered_characters.sort(key=lambda x: x['name'])
    elif sort_by == "Mentions":
        filtered_characters.sort(key=lambda x: x['mention_count'], reverse=True)
    
    # Display characters in grid
    if filtered_characters:
        # Create grid container
        grid_html = '<div class="character-grid">'
        
        for char in filtered_characters:
            # Get character DNA and quirks
            character_dna = char.get('character_dna', {})
            quirks = char.get('quirks_mannerisms', [])[:2]  # Show top 2 quirks
            uniqueness = char.get('uniqueness_score', 0)
            
            # Create quirk badges HTML
            quirk_badges = ''.join([f'<span class="quirk-badge">{quirk}</span>' for quirk in quirks])
            
            # Generate character card HTML
            card_html = f"""
            <div class="character-card" onclick="selectCharacter('{char['name']}')">
                {f'<div class="uniqueness-indicator">{int(uniqueness * 100)}%</div>' if uniqueness > 0.5 else ''}
                <div class="character-avatar">{char['avatar']}</div>
                <div class="character-name">{char['name']}</div>
                <div class="character-role">{char['role']}</div>
                <div class="character-dna">{character_dna.get('character_essence', '')}</div>
                <div class="character-description">{char['description']}</div>
                
                {f'<div style="margin-bottom: 0.5rem;">{quirk_badges}</div>' if quirks else ''}
                
                <div class="character-stats">
                    <div class="stat-item">
                        <span>💬</span>
                        <span>{char['dialogue_count']} quotes</span>
                    </div>
                    <div class="stat-item">
                        <span>📍</span>
                        <span>{char['mention_count']} mentions</span>
                    </div>
                </div>
                
                <div class="importance-bar">
                    <div class="importance-fill" style="width: {char['importance_score'] * 100}%"></div>
                </div>
            </div>
            """
            grid_html += card_html
        
        grid_html += '</div>'
        
        # JavaScript for character selection
        st.markdown("""
        <script>
        function selectCharacter(name) {
            // This will be handled by Streamlit
            const event = new CustomEvent('characterSelected', { detail: { name: name } });
            window.dispatchEvent(event);
        }
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # Character selection handler
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            selected_char_name = st.selectbox(
                "Select a character to create AI persona:",
                ["Choose a character..."] + [char['name'] for char in filtered_characters],
                key="selected_character"
            )
            
            if selected_char_name != "Choose a character...":
                selected_char = next(
                    (char for char in filtered_characters if char['name'] == selected_char_name),
                    None
                )
                
                if selected_char:
                    # Show character details
                    with st.expander("📋 Character Details", expanded=True):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown(f"""
                            <div style="text-align: center; padding: 1rem;">
                                <div style="font-size: 5rem;">{selected_char['avatar']}</div>
                                <h3>{selected_char['name']}</h3>
                                <p style="color: #667eea;">{selected_char['role']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Character DNA
                            dna = selected_char.get('character_dna', {})
                            if dna:
                                st.markdown("**Character DNA:**")
                                st.write(dna.get('core_identity', 'Unknown'))
                                
                                # Personality Matrix
                                if dna.get('personality_matrix'):
                                    st.markdown("**Personality Traits:**")
                                    matrix = dna['personality_matrix']
                                    
                                    # Show extreme traits
                                    extreme_traits = []
                                    for trait, value in matrix.items():
                                        trait_name = trait.replace('_', ' ').title()
                                        if value > 0.7:
                                            extreme_traits.append(f"• Very {trait_name.split()[1]}")
                                        elif value < 0.3:
                                            extreme_traits.append(f"• Very {trait_name.split()[0]}")
                                    
                                    if extreme_traits:
                                        for trait in extreme_traits[:4]:
                                            st.write(trait)
                            
                            # Unique Quirks
                            quirks = selected_char.get('quirks_mannerisms', [])
                            if quirks:
                                st.markdown("**Unique Quirks:**")
                                for quirk in quirks[:3]:
                                    st.write(f"• {quirk}")
                            
                            # Speech Patterns
                            speech = selected_char.get('speech_patterns', {})
                            if speech:
                                st.markdown("**Speech Patterns:**")
                                if speech.get('verbal_tics'):
                                    st.write(f"• Uses {', '.join(speech['verbal_tics'][:2])}")
                                if speech.get('favorite_words'):
                                    words = list(speech['favorite_words'].keys())[:3]
                                    st.write(f"• Often says: {', '.join(words)}")
                                st.write(f"• {speech.get('speech_rhythm', 'Normal')} speaker")
                            
                            # Values & Beliefs
                            values = selected_char.get('values_beliefs', {})
                            if values and values.get('moral_code'):
                                st.markdown("**Core Values:**")
                                st.write(values['moral_code'])
                            
                            # Motives & Behaviors
                            motives = selected_char.get('motives_behaviors', {})
                            if motives:
                                st.markdown("**Hidden Motives & Behaviors:**")
                                
                                # Primary motivations
                                if motives.get('primary_motivations'):
                                    st.write(f"🎯 Driven by: {', '.join(motives['primary_motivations'])}")
                                
                                # Behavioral traits
                                if motives.get('behavioral_traits'):
                                    traits = list(motives['behavioral_traits'].keys())
                                    if traits:
                                        st.write(f"⚡ Traits: {', '.join(traits[:3])}")
                                
                                # Manipulation tactics
                                if motives.get('manipulation_tactics'):
                                    st.write(f"🎭 Uses: {', '.join(motives['manipulation_tactics'][:2])}")
                                
                                # Empathy level
                                empathy = motives.get('empathy_level', 0.5)
                                if empathy < 0.3:
                                    st.write("❄️ Very low empathy")
                                elif empathy > 0.7:
                                    st.write("💖 High empathy despite flaws")
                            
                            # Interaction Patterns
                            interactions = selected_char.get('interaction_patterns', {})
                            if interactions:
                                st.markdown("**How They Treat Others:**")
                                
                                if interactions.get('default_stance'):
                                    st.write(f"💬 {interactions['default_stance'].capitalize()} in conversations")
                                
                                if interactions.get('dismissive_behaviors'):
                                    for behavior in interactions['dismissive_behaviors'][:2]:
                                        st.write(f"⚠️ {behavior}")
                                
                                if interactions.get('emotional_manipulation'):
                                    st.write(f"🎪 Emotional tactics: {', '.join(interactions['emotional_manipulation'][:2])}")
                            
                            # Engagement Warning
                            if motives.get('aggression_style') == 'actively hostile' or \
                               motives.get('ego_indicators', 0) > 0.7 or \
                               len(motives.get('manipulation_tactics', [])) > 2:
                                st.warning("⚡ **High Intensity Character** - Expect dramatic interactions!")
                            
                            if selected_char['key_quotes']:
                                st.markdown("**Signature Quotes:**")
                                for quote in selected_char['key_quotes'][:2]:
                                    st.info(f'"{quote}"')
                    
                    # Create AI button
                    if st.button(
                        f"🎭 Create AI from {selected_char['name']}", 
                        use_container_width=True,
                        type="primary"
                    ):
                        # Store selected character in session state
                        st.session_state.selected_character_data = selected_char
                        st.session_state.current_page = 'create'
                        st.session_state.creation_step = 2  # Skip to customization
                        st.rerun()
    
    else:
        st.markdown("""
        <div class="no-characters">
            <h3>No characters match your filters</h3>
            <p>Try adjusting the filters to see more characters</p>
        </div>
        """, unsafe_allow_html=True)