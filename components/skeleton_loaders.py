"""
Skeleton Loader Component
=========================

Implements skeleton loaders for better visual feedback during loading.
Shows animated placeholders instead of spinners.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, List, Dict, Literal
import time

class SkeletonLoader:
    """Create skeleton loading animations"""
    
    def __init__(self):
        self._inject_skeleton_styles()
    
    def _inject_skeleton_styles(self):
        """Inject CSS for skeleton loaders"""
        css = """
        <style>
        /* Skeleton Base */
        .skeleton {
            background: linear-gradient(
                90deg,
                var(--skeleton-base, #2a2a4a) 25%,
                var(--skeleton-highlight, #3a3a5a) 50%,
                var(--skeleton-base, #2a2a4a) 75%
            );
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }
        
        @keyframes loading {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }
        
        /* Skeleton Types */
        .skeleton-text {
            height: 1em;
            margin-bottom: 0.5rem;
            border-radius: 4px;
        }
        
        .skeleton-title {
            height: 1.5em;
            margin-bottom: 1rem;
            width: 60%;
            border-radius: 4px;
        }
        
        .skeleton-paragraph {
            margin-bottom: 1.5rem;
        }
        
        .skeleton-paragraph .skeleton-text:last-child {
            width: 80%;
        }
        
        .skeleton-image {
            height: 200px;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .skeleton-card {
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .skeleton-button {
            height: 2.5rem;
            width: 120px;
            border-radius: 6px;
            display: inline-block;
            margin-right: 0.5rem;
        }
        
        .skeleton-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 1rem;
        }
        
        .skeleton-table {
            width: 100%;
            margin-bottom: 1rem;
        }
        
        .skeleton-table-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 0.75rem;
            align-items: center;
        }
        
        .skeleton-table-cell {
            flex: 1;
            height: 1.2em;
        }
        
        .skeleton-table-cell:first-child {
            flex: 0 0 150px;
        }
        
        /* Document Skeleton */
        .skeleton-document {
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 2rem;
            min-height: 600px;
        }
        
        .skeleton-page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        
        .skeleton-page-nav {
            display: flex;
            gap: 0.5rem;
        }
        
        .skeleton-page-content {
            margin-bottom: 2rem;
        }
        
        /* Processing Skeleton */
        .skeleton-processing {
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }
        
        .skeleton-processing-icon {
            width: 64px;
            height: 64px;
            margin: 0 auto 1rem;
            border-radius: 50%;
        }
        
        .skeleton-processing-text {
            width: 200px;
            margin: 0 auto 0.5rem;
        }
        
        .skeleton-processing-subtext {
            width: 300px;
            margin: 0 auto;
            opacity: 0.7;
        }
        
        /* Pulse Animation Variant */
        .skeleton-pulse {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
            100% {
                opacity: 1;
            }
        }
        
        /* Sidebar Skeleton */
        .skeleton-sidebar {
            padding: 1rem;
        }
        
        .skeleton-sidebar-section {
            margin-bottom: 2rem;
        }
        
        .skeleton-sidebar-item {
            height: 2.5rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
        }
        
        /* Chat Skeleton */
        .skeleton-chat {
            padding: 1rem;
        }
        
        .skeleton-chat-message {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .skeleton-chat-content {
            flex: 1;
        }
        
        .skeleton-chat-bubble {
            background: var(--skeleton-base, #2a2a4a);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }
        
        /* Grid Skeleton */
        .skeleton-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .skeleton-grid-item {
            background: var(--surface-bg, #252548);
            border: 1px solid var(--border-color, #3a3a5a);
            border-radius: 8px;
            padding: 1rem;
            min-height: 150px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .skeleton-grid {
                grid-template-columns: 1fr;
            }
            
            .skeleton-document {
                padding: 1rem;
            }
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def text(self, lines: int = 3, width_pattern: Optional[List[str]] = None):
        """Render skeleton text lines"""
        if width_pattern is None:
            width_pattern = ['100%', '100%', '80%']
        
        html = '<div class="skeleton-paragraph">'
        for i in range(lines):
            width = width_pattern[i % len(width_pattern)]
            html += f'<div class="skeleton skeleton-text" style="width: {width}"></div>'
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def title(self, width: str = '60%'):
        """Render skeleton title"""
        st.markdown(
            f'<div class="skeleton skeleton-title" style="width: {width}"></div>',
            unsafe_allow_html=True
        )
    
    def image(self, height: str = '200px', width: str = '100%'):
        """Render skeleton image"""
        st.markdown(
            f'<div class="skeleton skeleton-image" style="height: {height}; width: {width}"></div>',
            unsafe_allow_html=True
        )
    
    def card(self, show_image: bool = True, show_title: bool = True, 
             show_text: bool = True, text_lines: int = 3):
        """Render skeleton card"""
        html = '<div class="skeleton-card">'
        
        if show_image:
            html += '<div class="skeleton skeleton-image"></div>'
        
        if show_title:
            html += '<div class="skeleton skeleton-title"></div>'
        
        if show_text:
            html += '<div class="skeleton-paragraph">'
            for i in range(text_lines):
                width = '100%' if i < text_lines - 1 else '80%'
                html += f'<div class="skeleton skeleton-text" style="width: {width}"></div>'
            html += '</div>'
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def button(self, count: int = 1, width: str = '120px'):
        """Render skeleton buttons"""
        html = '<div>'
        for _ in range(count):
            html += f'<div class="skeleton skeleton-button" style="width: {width}"></div>'
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def table(self, rows: int = 5, columns: int = 3):
        """Render skeleton table"""
        html = '<div class="skeleton-table">'
        
        for _ in range(rows):
            html += '<div class="skeleton-table-row">'
            for _ in range(columns):
                html += '<div class="skeleton skeleton-table-cell"></div>'
            html += '</div>'
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def document_reader(self):
        """Render skeleton for document reader"""
        html = """
        <div class="skeleton-document">
            <div class="skeleton-page-header">
                <div class="skeleton skeleton-text" style="width: 150px"></div>
                <div class="skeleton-page-nav">
                    <div class="skeleton skeleton-button" style="width: 80px"></div>
                    <div class="skeleton skeleton-button" style="width: 80px"></div>
                </div>
            </div>
            <div class="skeleton-page-content">
                <div class="skeleton skeleton-title"></div>
                <div class="skeleton-paragraph">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text" style="width: 80%"></div>
                </div>
                <div class="skeleton skeleton-image" style="height: 300px"></div>
                <div class="skeleton-paragraph">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text" style="width: 60%"></div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)
    
    def processing(self, message: str = "Processing..."):
        """Render skeleton for processing state"""
        html = f"""
        <div class="skeleton-processing">
            <div class="skeleton skeleton-processing-icon skeleton-pulse"></div>
            <div class="skeleton skeleton-processing-text"></div>
            <div class="skeleton skeleton-processing-subtext"></div>
        </div>
        """
        
        st.markdown(html, unsafe_allow_html=True)
    
    def sidebar_section(self, items: int = 4):
        """Render skeleton for sidebar section"""
        html = '<div class="skeleton-sidebar-section">'
        html += '<div class="skeleton skeleton-title" style="width: 120px; height: 1.2em"></div>'
        
        for _ in range(items):
            html += '<div class="skeleton skeleton-sidebar-item"></div>'
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def chat_messages(self, count: int = 3):
        """Render skeleton for chat messages"""
        html = '<div class="skeleton-chat">'
        
        for i in range(count):
            align = 'flex-start' if i % 2 == 0 else 'flex-end'
            html += f'<div class="skeleton-chat-message" style="justify-content: {align}">'
            
            if i % 2 == 0:
                html += '<div class="skeleton skeleton-avatar"></div>'
            
            html += '<div class="skeleton-chat-content" style="max-width: 70%">'
            html += '<div class="skeleton-chat-bubble">'
            html += '<div class="skeleton skeleton-text"></div>'
            html += '<div class="skeleton skeleton-text" style="width: 80%"></div>'
            html += '</div>'
            html += '</div>'
            
            if i % 2 == 1:
                html += '<div class="skeleton skeleton-avatar"></div>'
            
            html += '</div>'
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)
    
    def grid(self, items: int = 6):
        """Render skeleton grid"""
        html = '<div class="skeleton-grid">'
        
        for _ in range(items):
            html += """
            <div class="skeleton-grid-item">
                <div class="skeleton skeleton-image" style="height: 100px; margin-bottom: 0.5rem"></div>
                <div class="skeleton skeleton-text" style="width: 70%; margin-bottom: 0.5rem"></div>
                <div class="skeleton skeleton-text" style="width: 50%"></div>
            </div>
            """
        
        html += '</div>'
        
        st.markdown(html, unsafe_allow_html=True)


# Context managers for loading states
class LoadingContext:
    """Context manager for showing skeleton during loading"""
    
    def __init__(self, skeleton_type: str = 'text', **kwargs):
        self.skeleton = SkeletonLoader()
        self.skeleton_type = skeleton_type
        self.kwargs = kwargs
        self.placeholder = None
    
    def __enter__(self):
        self.placeholder = st.empty()
        
        with self.placeholder.container():
            # Render appropriate skeleton
            if self.skeleton_type == 'text':
                self.skeleton.text(**self.kwargs)
            elif self.skeleton_type == 'card':
                self.skeleton.card(**self.kwargs)
            elif self.skeleton_type == 'document':
                self.skeleton.document_reader()
            elif self.skeleton_type == 'processing':
                self.skeleton.processing(**self.kwargs)
            elif self.skeleton_type == 'table':
                self.skeleton.table(**self.kwargs)
            elif self.skeleton_type == 'grid':
                self.skeleton.grid(**self.kwargs)
            elif self.skeleton_type == 'chat':
                self.skeleton.chat_messages(**self.kwargs)
        
        return self.placeholder
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clear skeleton
        if self.placeholder:
            self.placeholder.empty()


# Decorator for skeleton loading
def with_skeleton_loader(skeleton_type: str = 'text', **skeleton_kwargs):
    """Decorator to show skeleton while function executes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoadingContext(skeleton_type, **skeleton_kwargs) as placeholder:
                result = func(*args, **kwargs)
                
                # If function returns content, display it
                if result is not None and hasattr(placeholder, 'write'):
                    placeholder.write(result)
                
                return result
        return wrapper
    return decorator


# Utility functions
def show_skeleton_while_loading(loading_function, skeleton_type: str = 'text', **kwargs):
    """Show skeleton while a function is loading"""
    with LoadingContext(skeleton_type, **kwargs):
        return loading_function()


# Example usage patterns
class SkeletonExamples:
    """Example skeleton patterns for common UI elements"""
    
    @staticmethod
    def document_upload_processing():
        """Skeleton for document upload and processing"""
        skeleton = SkeletonLoader()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📄 Processing Document")
            skeleton.processing("Analyzing document structure...")
        
        with col2:
            st.markdown("### 📊 Progress")
            skeleton.text(lines=2, width_pattern=['100%', '60%'])
            skeleton.button(count=2)
    
    @staticmethod
    def ai_response_loading():
        """Skeleton for AI response"""
        skeleton = SkeletonLoader()
        
        st.markdown("### 🤖 AI Analysis")
        skeleton.chat_messages(count=1)
    
    @staticmethod
    def search_results_loading():
        """Skeleton for search results"""
        skeleton = SkeletonLoader()
        
        st.markdown("### 🔍 Search Results")
        skeleton.grid(items=6)


# Singleton instance
_skeleton_instance = None

def get_skeleton_loader() -> SkeletonLoader:
    """Get singleton skeleton loader instance"""
    global _skeleton_instance
    if _skeleton_instance is None:
        _skeleton_instance = SkeletonLoader()
    return _skeleton_instance