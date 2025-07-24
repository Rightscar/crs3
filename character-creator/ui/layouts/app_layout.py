"""
Main Application Layout
======================

Main layout structure for the character creator app.
"""

import streamlit as st
from pathlib import Path
from ui.pages.character_gallery import render_character_gallery
from ui.pages.character_chat import render_character_chat

def render_app():
    """Render the main application"""
    
    # Apply custom CSS
    apply_custom_css()
    
    # Render header
    render_header()
    
    # Render main content based on current page
    current_page = st.session_state.get('current_page', 'home')
    
    if current_page == 'home':
        render_home_page()
    elif current_page == 'create':
        st.info("🚧 Character creation page coming in Phase 2!")
    elif current_page == 'chat':
        render_character_chat()
    elif current_page == 'gallery':
        render_character_gallery()
    else:
        st.error("Page not found")

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    
    /* Header styles */
    .app-header {
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(10px);
        padding: 1rem 2rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
        margin-bottom: 2rem;
    }
    
    .app-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    /* Card styles */
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render application header"""
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">🎭 Character Creator</h1>
        <p style="color: rgba(255, 255, 255, 0.7); margin: 0;">
            Transform any document into a living AI character
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
    
    with col2:
        if st.button("✨ Create", use_container_width=True):
            st.session_state.current_page = 'create'
            st.rerun()
    
    with col3:
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.current_page = 'chat'
            st.rerun()
    
    with col4:
        if st.button("🎭 Gallery", use_container_width=True):
            st.session_state.current_page = 'gallery'
            st.rerun()

def render_home_page():
    """Render the home page"""
    
    # Hero section
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">
            Bring Your Documents to Life
        </h1>
        <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8); max-width: 600px; margin: 0 auto;">
            Upload any document and transform it into an intelligent AI character 
            that can chat, answer questions, and embody the knowledge within.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📚 Any Document</h3>
            <p>Upload PDFs, Word docs, text files, or even entire books. 
            Our system extracts and understands the content.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎭 Living Characters</h3>
            <p>Create characters with unique personalities, speaking styles, 
            and deep knowledge from your documents.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>💬 Natural Conversations</h3>
            <p>Chat naturally with your characters. They remember context 
            and respond based on their source material.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Create Your First Character", use_container_width=True):
            st.session_state.current_page = 'create'
            st.rerun()
    
    # Stats section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 📊 Platform Stats")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Characters Created", "0", help="Total characters on the platform")
    
    with col2:
        st.metric("Documents Processed", "0", help="Total documents uploaded")
    
    with col3:
        st.metric("Conversations", "0", help="Total chat sessions")
    
    with col4:
        st.metric("Active Users", "1", help="You're the first!")