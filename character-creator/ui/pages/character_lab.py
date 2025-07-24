"""
Character Laboratory UI
=======================

Advanced features for character manipulation and experimentation.
"""

import streamlit as st
from datetime import datetime, timedelta

from services.character_evolution_service import CharacterEvolutionService
from services.character_fusion_service import CharacterFusionService
from config.logging_config import logger


def render_character_lab():
    """Render the character laboratory page"""
    st.markdown("## 🧪 Character Laboratory")
    st.markdown("Experiment with advanced character features and transformations.")
    
    # Lab sections
    tab1, tab2, tab3 = st.tabs([
        "🧬 Character Evolution",
        "⚡ Character Fusion",
        "🌐 Multi-Character Interactions"
    ])
    
    with tab1:
        render_evolution_lab()
    
    with tab2:
        render_fusion_lab()
    
    with tab3:
        render_multi_character_lab()


def render_evolution_lab():
    """Render character evolution section"""
    st.markdown("### Character Evolution")
    st.markdown("Watch your characters grow and change through interactions.")
    
    evolution_service = CharacterEvolutionService()
    
    # Character selection
    characters = st.session_state.get('extracted_characters', [])
    if not characters:
        st.warning("No characters available. Create some characters first!")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        character_names = [char['name'] for char in characters]
        selected_char_name = st.selectbox(
            "Select Character to Evolve",
            character_names
        )
        
        # Find selected character
        character = next(
            (char for char in characters if char['name'] == selected_char_name),
            None
        )
        
        if character:
            # Evolution controls
            st.markdown("#### Evolution Controls")
            
            # Simulate interaction
            with st.expander("🎭 Simulate Interaction"):
                user_message = st.text_area(
                    "Your message to the character",
                    placeholder="Type something that might influence the character..."
                )
                
                interaction_quality = st.slider(
                    "Interaction Quality",
                    0.0, 1.0, 0.7,
                    help="How meaningful is this interaction?"
                )
                
                emotional_context = {
                    'intensity': st.slider("Emotional Intensity", 0.0, 1.0, 0.5),
                    'valence': st.slider("Emotional Valence", -1.0, 1.0, 0.0),
                    'conflict': st.checkbox("Contains Conflict"),
                    'vulnerability': st.checkbox("Shows Vulnerability"),
                    'trust_building': st.checkbox("Builds Trust")
                }
                
                if st.button("🧬 Apply Evolution"):
                    if user_message:
                        interaction_data = {
                            'user_message': user_message,
                            'character_response': "Simulated response",
                            'emotional_context': emotional_context,
                            'interaction_quality': interaction_quality
                        }
                        
                        result = evolution_service.track_interaction(
                            character['id'],
                            interaction_data
                        )
                        
                        if result['success']:
                            st.success("Evolution applied!")
                            st.json(result['trait_changes'])
                        else:
                            st.error(f"Evolution failed: {result.get('error')}")
            
            # Healing options
            with st.expander("💚 Character Healing"):
                healing_type = st.radio(
                    "Healing Type",
                    ["natural", "therapeutic", "reset"],
                    horizontal=True
                )
                
                healing_descriptions = {
                    'natural': "Gradual healing through positive interactions",
                    'therapeutic': "Move traits toward balanced state",
                    'reset': "Full reset to original personality"
                }
                
                st.info(healing_descriptions[healing_type])
                
                if st.button("🌱 Apply Healing"):
                    result = evolution_service.apply_healing(
                        character['id'],
                        healing_type
                    )
                    
                    if result['success']:
                        st.success(f"Applied {healing_type} healing!")
                        st.json(result['new_traits'])
                    else:
                        st.error(f"Healing failed: {result.get('error')}")
    
    with col2:
        if character:
            # Evolution status
            st.markdown("#### Evolution Status")
            
            # Current personality
            st.markdown("**Current Traits:**")
            traits = character.get('personality_traits', {})
            for trait, value in traits.items():
                st.progress(value, text=f"{trait.title()}: {value:.2f}")
            
            # Evolution history
            history = evolution_service.get_evolution_history(
                character['id'],
                days=30
            )
            
            if history:
                st.metric("Total Drift", f"{history.get('total_drift', 0):.2%}")
                st.metric("Evolution Count", history.get('evolution_count', 0))
                
                # Show trends
                if history.get('trait_trends'):
                    st.markdown("**Recent Changes:**")
                    for trait, changes in history['trait_trends'].items():
                        if changes:
                            latest_change = changes[-1]['change']
                            direction = "↑" if latest_change > 0 else "↓"
                            st.text(f"{trait}: {direction} {abs(latest_change):.3f}")


def render_fusion_lab():
    """Render character fusion section"""
    st.markdown("### Character Fusion")
    st.markdown("Combine characters to create unique hybrids.")
    
    fusion_service = CharacterFusionService()
    
    characters = st.session_state.get('extracted_characters', [])
    if not characters or len(characters) < 2:
        st.warning("Need at least 2 characters for fusion. Create more characters first!")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Character selection
        st.markdown("#### Select Characters to Fuse")
        
        character_names = [char['name'] for char in characters]
        selected_chars = st.multiselect(
            "Choose 2-4 characters",
            character_names,
            max_selections=4
        )
        
        if len(selected_chars) >= 2:
            # Get selected character IDs
            selected_ids = [
                char['id'] for char in characters 
                if char['name'] in selected_chars
            ]
            
            # Check compatibility
            compatibility = fusion_service.get_fusion_compatibility(selected_ids)
            
            if compatibility['success']:
                # Show compatibility
                st.markdown("#### Fusion Compatibility")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric(
                        "Overall",
                        f"{compatibility['overall_compatibility']:.0%}"
                    )
                with col_b:
                    st.metric(
                        "Personality",
                        f"{compatibility['personality_compatibility']:.0%}"
                    )
                with col_c:
                    st.metric(
                        "Style",
                        f"{compatibility['style_compatibility']:.0%}"
                    )
                
                # Recommendations
                if compatibility['recommendations']:
                    st.info(compatibility['recommendations'][0])
                
                # Fusion parameters
                st.markdown("#### Fusion Parameters")
                
                hybrid_name = st.text_input(
                    "Hybrid Name (optional)",
                    placeholder="Leave empty for auto-generated name"
                )
                
                blend_method = st.selectbox(
                    "Trait Blending Method",
                    ["weighted", "average", "dominant", "harmonic", "random"]
                )
                
                fusion_type = st.radio(
                    "Fusion Type",
                    ["balanced", "weighted", "random"],
                    horizontal=True
                )
                
                # Fusion button
                if st.button("⚡ Fuse Characters", type="primary"):
                    fusion_params = {
                        'blend_method': blend_method,
                        'fusion_type': fusion_type
                    }
                    
                    if hybrid_name:
                        fusion_params['name'] = hybrid_name
                    
                    with st.spinner("Creating hybrid character..."):
                        result = fusion_service.fuse_characters(
                            selected_ids,
                            fusion_params
                        )
                        
                        if result['success']:
                            st.success("Fusion successful!")
                            
                            # Show hybrid character
                            hybrid = result['character']
                            st.markdown(f"### {hybrid['avatar']} {hybrid['name']}")
                            st.markdown(f"**Role:** {hybrid['role']}")
                            st.markdown(f"**Description:** {hybrid['description']}")
                            
                            # Show fusion summary
                            summary = result['fusion_summary']
                            st.json(summary)
                            
                            # Add to characters
                            if 'extracted_characters' not in st.session_state:
                                st.session_state.extracted_characters = []
                            st.session_state.extracted_characters.append(hybrid)
                            
                            st.balloons()
                        else:
                            st.error(f"Fusion failed: {result.get('error')}")
    
    with col2:
        if len(selected_chars) >= 2 and compatibility.get('success'):
            # Preview
            st.markdown("#### Fusion Preview")
            
            preview = compatibility.get('fusion_preview', {})
            if preview:
                st.markdown(f"**Name:** {preview.get('name', 'Unknown')}")
                st.markdown(f"**Role:** {preview.get('role', 'Unknown')}")
                st.markdown(f"**Style:** {preview.get('style_preview', 'Unknown')}")
                
                # Preview traits
                st.markdown("**Personality Preview:**")
                for trait, value in preview.get('personality_preview', {}).items():
                    st.progress(value, text=f"{trait}: {value:.2f}")


def render_multi_character_lab():
    """Render multi-character interaction section"""
    st.markdown("### Multi-Character Interactions")
    st.info("🚧 Coming Soon: Watch characters interact with each other in real-time!")
    
    # Placeholder for future features
    st.markdown("""
    **Planned Features:**
    - 🎭 Character-to-character conversations
    - 🌍 Shared world building
    - 📖 Emergent storytelling
    - 🎲 Dungeon Master mode
    - 👥 Multi-user collaboration
    """)
    
    # Preview
    with st.expander("Preview: Character Interaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Character 1**")
            st.text_area(
                "Character 1 says:",
                "Hello there! I've heard much about you.",
                disabled=True
            )
        
        with col2:
            st.markdown("**Character 2**")
            st.text_area(
                "Character 2 says:",
                "The pleasure is mine. Shall we begin?",
                disabled=True
            )
        
        st.markdown("**Narrator**")
        st.text_area(
            "Scene description:",
            "The two characters meet in a dimly lit tavern, the air thick with anticipation...",
            disabled=True
        )
        
        st.info("This feature will enable rich, multi-character narratives and collaborative storytelling.")