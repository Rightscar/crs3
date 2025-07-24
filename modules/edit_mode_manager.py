"""
Edit Mode Manager Module
=======================

Provides edit mode functionality for AI PDF Pro including:
- Inline text editing with live preview
- Annotation tools (highlights, notes, shapes)
- Version control and change tracking
- Edit history with undo/redo
- Compare versions side-by-side

Features:
- Rich text editing interface
- Drawing tools integration
- Version management
- Change tracking and diff visualization
- Export with edit preservation
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class EditAnnotation:
    """Annotation container for highlights, notes, and shapes"""
    id: str
    type: str  # 'highlight', 'note', 'shape', 'freehand'
    content: str
    position: Dict[str, Any]  # position data
    color: str
    author: str
    timestamp: str
    page_number: int

@dataclass
class EditChange:
    """Change tracking for version control"""
    id: str
    change_type: str  # 'insert', 'delete', 'modify', 'annotate'
    original_text: str
    new_text: str
    position: Tuple[int, int]  # start, end
    timestamp: str
    author: str
    page_number: int

@dataclass
class DocumentVersion:
    """Document version container"""
    version_id: str
    version_number: int
    title: str
    content: str
    changes: List[EditChange]
    annotations: List[EditAnnotation]
    created_at: str
    author: str
    is_current: bool

class EditModeManager:
    """Manages edit mode functionality for documents"""
    
    def __init__(self):
        self.current_version = None
        self.version_history = []
        self.annotations = []
        self.changes = []
        self.edit_mode_active = False
        self.current_tool = 'select'  # select, highlight, note, draw, text
        
        # Editor configuration
        self.editor_config = {
            'highlight_colors': ['#FFFF00', '#00FF00', '#FF9500', '#FF0000', '#0099FF'],
            'annotation_tools': ['highlight', 'note', 'shape', 'freehand', 'text'],
            'auto_save_interval': 30,  # seconds
            'max_versions': 50
        }
        
        self._initialize_edit_state()
    
    def _initialize_edit_state(self):
        """Initialize edit mode session state"""
        if 'edit_mode_active' not in st.session_state:
            st.session_state.edit_mode_active = False
        if 'current_edit_tool' not in st.session_state:
            st.session_state.current_edit_tool = 'select'
        if 'edit_annotations' not in st.session_state:
            st.session_state.edit_annotations = []
        if 'edit_changes' not in st.session_state:
            st.session_state.edit_changes = []
        if 'edit_versions' not in st.session_state:
            st.session_state.edit_versions = []
        if 'edit_content' not in st.session_state:
            st.session_state.edit_content = ""
        if 'edit_undo_stack' not in st.session_state:
            st.session_state.edit_undo_stack = []
        if 'edit_redo_stack' not in st.session_state:
            st.session_state.edit_redo_stack = []
    
    def enable_edit_mode(self, document_content: str) -> bool:
        """Enable edit mode for the current document"""
        try:
            st.session_state.edit_mode_active = True
            st.session_state.edit_content = document_content
            
            # Create initial version
            initial_version = DocumentVersion(
                version_id=str(uuid.uuid4())[:8],
                version_number=1,
                title="Original Document",
                content=document_content,
                changes=[],
                annotations=[],
                created_at=datetime.now().isoformat(),
                author="User",
                is_current=True
            )
            
            st.session_state.edit_versions = [initial_version]
            self.current_version = initial_version
            
            logger.info("Edit mode enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable edit mode: {e}")
            return False
    
    def disable_edit_mode(self) -> bool:
        """Disable edit mode and return to read-only"""
        try:
            st.session_state.edit_mode_active = False
            logger.info("Edit mode disabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable edit mode: {e}")
            return False
    
    def render_edit_interface(self, current_text: str) -> str:
        """Render the main edit interface"""
        if not st.session_state.edit_mode_active:
            return current_text
        
        # Edit toolbar
        self._render_edit_toolbar()
        
        # Main editing area
        col1, col2 = st.columns([3, 1])
        
        with col1:
            edited_text = self._render_text_editor(current_text)
        
        with col2:
            self._render_annotation_panel()
        
        # Version control panel
        self._render_version_control_panel()
        
        return edited_text
    
    def _render_edit_toolbar(self):
        """Render the edit mode toolbar"""
        st.markdown("### ✏️ Edit Mode Toolbar")
        
        # Tool selection
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            if st.button("🔍 Select", help="Selection tool"):
                st.session_state.current_edit_tool = 'select'
        
        with col2:
            if st.button("🖍️ Highlight", help="Highlight text"):
                st.session_state.current_edit_tool = 'highlight'
        
        with col3:
            if st.button("📝 Note", help="Add sticky note"):
                st.session_state.current_edit_tool = 'note'
        
        with col4:
            if st.button("✏️ Draw", help="Freehand drawing"):
                st.session_state.current_edit_tool = 'draw'
        
        with col5:
            if st.button("📝 Text", help="Edit text"):
                st.session_state.current_edit_tool = 'text'
        
        with col6:
            if st.button("↶ Undo", help="Undo last change"):
                self._undo_change()
        
        with col7:
            if st.button("↷ Redo", help="Redo last change"):
                self._redo_change()
        
        # Current tool indicator
        st.markdown(f"**Current Tool:** {st.session_state.current_edit_tool.title()}")
        
        # Color picker for annotations
        if st.session_state.current_edit_tool in ['highlight', 'draw']:
            selected_color = st.selectbox(
                "Color:",
                self.editor_config['highlight_colors'],
                format_func=lambda x: f"Color {self.editor_config['highlight_colors'].index(x) + 1}"
            )
            st.session_state.current_annotation_color = selected_color
    
    def _render_text_editor(self, current_text: str) -> str:
        """Render the main text editing interface"""
        st.markdown("#### 📝 Document Editor")
        
        # Rich text editor (simulated with text area)
        edited_text = st.text_area(
            "Edit document content:",
            value=st.session_state.edit_content or current_text,
            height=400,
            key="main_text_editor",
            help="Edit the document content directly. Changes are tracked automatically."
        )
        
        # Track changes if text has been modified
        if edited_text != st.session_state.edit_content:
            self._track_text_change(st.session_state.edit_content, edited_text)
            st.session_state.edit_content = edited_text
        
        # Live preview with changes highlighted
        if st.checkbox("Show Changes", value=True):
            self._render_change_preview(edited_text)
        
        return edited_text
    
    def _render_change_preview(self, current_text: str):
        """Render preview with changes highlighted"""
        try:
            if st.session_state.edit_versions:
                original_text = st.session_state.edit_versions[0].content
                
                # Simple diff visualization
                changes_html = self._create_diff_html(original_text, current_text)
                
                with st.expander("📊 Changes Preview", expanded=True):
                    st.markdown(changes_html, unsafe_allow_html=True)
                    
                    # Change statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Characters Added", len(current_text) - len(original_text))
                    with col2:
                        st.metric("Total Changes", len(st.session_state.edit_changes))
                    with col3:
                        st.metric("Annotations", len(st.session_state.edit_annotations))
            
        except Exception as e:
            logger.error(f"Change preview error: {e}")
    
    def _create_diff_html(self, original: str, current: str) -> str:
        """Create HTML diff visualization"""
        try:
            # Simple character-level diff
            if original == current:
                return f'<div style="background: white; color: black; padding: 1rem; border-radius: 8px;">{current}</div>'
            
            # Highlight changes (simplified)
            diff_html = current
            
            # Mark additions in green
            if len(current) > len(original):
                added_chars = len(current) - len(original)
                diff_html = f'<span style="background-color: #10B981; padding: 2px;">+{added_chars} chars</span> ' + diff_html
            
            # Mark deletions in red
            elif len(current) < len(original):
                deleted_chars = len(original) - len(current)
                diff_html = f'<span style="background-color: #EF4444; padding: 2px;">-{deleted_chars} chars</span> ' + diff_html
            
            return f'''
            <div style="background: white; color: black; padding: 1rem; border-radius: 8px; line-height: 1.6;">
                {diff_html}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.7;">
                🟢 Additions • 🔴 Deletions • ✏️ Modifications
            </div>
            '''
            
        except Exception as e:
            logger.error(f"Diff HTML creation error: {e}")
            return f'<div style="background: white; color: black; padding: 1rem; border-radius: 8px;">{current}</div>'
    
    def _render_annotation_panel(self):
        """Render annotation tools panel"""
        st.markdown("#### 🎨 Annotations")
        
        # Add new annotation
        if st.session_state.current_edit_tool == 'note':
            note_content = st.text_area("Add Note:", height=100, key="new_note")
            if st.button("📌 Add Note") and note_content:
                self._add_annotation('note', note_content)
                st.rerun()
        
        elif st.session_state.current_edit_tool == 'highlight':
            highlight_text = st.text_input("Text to highlight:", key="highlight_text")
            if st.button("🖍️ Add Highlight") and highlight_text:
                self._add_annotation('highlight', highlight_text)
                st.rerun()
        
        # Show existing annotations
        annotations = st.session_state.edit_annotations
        if annotations:
            st.markdown("**Current Annotations:**")
            
            for i, annotation in enumerate(annotations):
                with st.container():
                    icon = "📌" if annotation.type == 'note' else "🖍️" if annotation.type == 'highlight' else "✏️"
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"{icon} **{annotation.type.title()}**")
                        st.markdown(f"_{annotation.content[:50]}..._")
                        st.caption(f"Page {annotation.page_number} • {annotation.timestamp[:16]}")
                    
                    with col2:
                        if st.button("🗑️", key=f"del_annotation_{i}"):
                            st.session_state.edit_annotations.remove(annotation)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No annotations yet. Use the tools above to add annotations.")
    
    def _render_version_control_panel(self):
        """Render version control and history panel"""
        with st.expander("📚 Version Control", expanded=False):
            
            # Save current version
            col1, col2 = st.columns(2)
            
            with col1:
                version_title = st.text_input("Version name:", value=f"Version {len(st.session_state.edit_versions) + 1}")
            
            with col2:
                if st.button("💾 Save Version"):
                    self._save_version(version_title)
                    st.success("Version saved!")
                    st.rerun()
            
            # Version history
            versions = st.session_state.edit_versions
            if len(versions) > 1:
                st.markdown("**Version History:**")
                
                for version in reversed(versions):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{version.title}**")
                        st.caption(f"v{version.version_number} • {version.created_at[:16]}")
                    
                    with col2:
                        st.caption(f"{len(version.changes)} changes, {len(version.annotations)} annotations")
                    
                    with col3:
                        if not version.is_current:
                            if st.button("📥", key=f"restore_{version.version_id}", help="Restore this version"):
                                self._restore_version(version.version_id)
                                st.rerun()
            
            # Compare versions
            if len(versions) >= 2:
                st.markdown("**Compare Versions:**")
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    version1 = st.selectbox("Version A:", versions, format_func=lambda v: v.title, key="compare_v1")
                
                with col2:
                    version2 = st.selectbox("Version B:", versions, format_func=lambda v: v.title, key="compare_v2")
                
                with col3:
                    if st.button("🔍 Compare"):
                        self._show_version_comparison(version1, version2)
    
    def _track_text_change(self, original: str, new: str):
        """Track text changes for version control"""
        if original != new:
            change = EditChange(
                id=str(uuid.uuid4())[:8],
                change_type='modify',
                original_text=original,
                new_text=new,
                position=(0, len(new)),
                timestamp=datetime.now().isoformat(),
                author="User",
                page_number=st.session_state.get('current_page', 1)
            )
            
            # Add to undo stack
            st.session_state.edit_undo_stack.append({
                'type': 'text_change',
                'original': original,
                'new': new
            })
            
            # Clear redo stack on new change
            st.session_state.edit_redo_stack = []
            
            st.session_state.edit_changes.append(change)
    
    def _add_annotation(self, annotation_type: str, content: str):
        """Add new annotation"""
        annotation = EditAnnotation(
            id=str(uuid.uuid4())[:8],
            type=annotation_type,
            content=content,
            position={},  # Would contain actual position data in full implementation
            color=st.session_state.get('current_annotation_color', '#FFFF00'),
            author="User",
            timestamp=datetime.now().isoformat(),
            page_number=st.session_state.get('current_page', 1)
        )
        
        st.session_state.edit_annotations.append(annotation)
        
        # Add to undo stack
        st.session_state.edit_undo_stack.append({
            'type': 'annotation_add',
            'annotation': annotation
        })
    
    def _save_version(self, title: str):
        """Save current state as new version"""
        try:
            # Mark previous versions as not current
            for version in st.session_state.edit_versions:
                version.is_current = False
            
            new_version = DocumentVersion(
                version_id=str(uuid.uuid4())[:8],
                version_number=len(st.session_state.edit_versions) + 1,
                title=title,
                content=st.session_state.edit_content,
                changes=st.session_state.edit_changes.copy(),
                annotations=st.session_state.edit_annotations.copy(),
                created_at=datetime.now().isoformat(),
                author="User",
                is_current=True
            )
            
            st.session_state.edit_versions.append(new_version)
            
            # Limit version history
            if len(st.session_state.edit_versions) > self.editor_config['max_versions']:
                st.session_state.edit_versions = st.session_state.edit_versions[-self.editor_config['max_versions']:]
            
            logger.info(f"Version saved: {title}")
            
        except Exception as e:
            logger.error(f"Failed to save version: {e}")
    
    def _restore_version(self, version_id: str):
        """Restore a previous version"""
        try:
            target_version = next((v for v in st.session_state.edit_versions if v.version_id == version_id), None)
            
            if target_version:
                # Save current state to undo stack
                st.session_state.edit_undo_stack.append({
                    'type': 'version_restore',
                    'content': st.session_state.edit_content,
                    'changes': st.session_state.edit_changes.copy(),
                    'annotations': st.session_state.edit_annotations.copy()
                })
                
                # Restore version
                st.session_state.edit_content = target_version.content
                st.session_state.edit_changes = target_version.changes.copy()
                st.session_state.edit_annotations = target_version.annotations.copy()
                
                # Mark as current
                for version in st.session_state.edit_versions:
                    version.is_current = (version.version_id == version_id)
                
                logger.info(f"Version restored: {version_id}")
            
        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
    
    def _show_version_comparison(self, version1: DocumentVersion, version2: DocumentVersion):
        """Display side-by-side version comparison"""
        st.markdown("### 🔍 Version Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{version1.title}**")
            st.markdown(f"*Version {version1.version_number} • {version1.created_at[:16]}*")
            st.text_area("Content A:", value=version1.content, height=300, disabled=True, key="compare_a")
        
        with col2:
            st.markdown(f"**{version2.title}**")
            st.markdown(f"*Version {version2.version_number} • {version2.created_at[:16]}*")
            st.text_area("Content B:", value=version2.content, height=300, disabled=True, key="compare_b")
        
        # Comparison metrics
        st.markdown("**Comparison Statistics:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            char_diff = len(version2.content) - len(version1.content)
            st.metric("Character Difference", char_diff)
        
        with col2:
            change_diff = len(version2.changes) - len(version1.changes)
            st.metric("Changes Difference", change_diff)
        
        with col3:
            annotation_diff = len(version2.annotations) - len(version1.annotations)
            st.metric("Annotations Difference", annotation_diff)
    
    def _undo_change(self):
        """Undo the last change"""
        if st.session_state.edit_undo_stack:
            last_action = st.session_state.edit_undo_stack.pop()
            
            # Move to redo stack
            st.session_state.edit_redo_stack.append(last_action)
            
            if last_action['type'] == 'text_change':
                st.session_state.edit_content = last_action['original']
            elif last_action['type'] == 'annotation_add':
                if last_action['annotation'] in st.session_state.edit_annotations:
                    st.session_state.edit_annotations.remove(last_action['annotation'])
            
            st.success("Change undone!")
    
    def _redo_change(self):
        """Redo the last undone change"""
        if st.session_state.edit_redo_stack:
            last_undone = st.session_state.edit_redo_stack.pop()
            
            # Move back to undo stack
            st.session_state.edit_undo_stack.append(last_undone)
            
            if last_undone['type'] == 'text_change':
                st.session_state.edit_content = last_undone['new']
            elif last_undone['type'] == 'annotation_add':
                st.session_state.edit_annotations.append(last_undone['annotation'])
            
            st.success("Change redone!")
    
    def export_edited_document(self, format_type: str = "txt") -> str:
        """Export the edited document with annotations"""
        try:
            content = st.session_state.edit_content
            
            if format_type == "txt":
                return content
            elif format_type == "html":
                html_content = f"""
                <html>
                <head><title>Edited Document</title></head>
                <body>
                <h1>Edited Document</h1>
                <div style="white-space: pre-wrap;">{content}</div>
                
                <h2>Annotations</h2>
                """
                
                for annotation in st.session_state.edit_annotations:
                    html_content += f"""
                    <div style="margin: 10px 0; padding: 10px; border-left: 3px solid {annotation.color};">
                        <strong>{annotation.type.title()}:</strong> {annotation.content}<br>
                        <small>Page {annotation.page_number} • {annotation.timestamp}</small>
                    </div>
                    """
                
                html_content += """
                </body>
                </html>
                """
                return html_content
            
            return content
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            return ""
    
    def get_edit_statistics(self) -> Dict[str, Any]:
        """Get editing session statistics"""
        return {
            'edit_mode_active': st.session_state.edit_mode_active,
            'total_changes': len(st.session_state.edit_changes),
            'total_annotations': len(st.session_state.edit_annotations),
            'total_versions': len(st.session_state.edit_versions),
            'undo_stack_size': len(st.session_state.edit_undo_stack),
            'redo_stack_size': len(st.session_state.edit_redo_stack),
            'current_tool': st.session_state.current_edit_tool
        }

# Global instance
edit_manager = EditModeManager()

def get_edit_mode_manager() -> EditModeManager:
    """Get the global edit mode manager instance"""
    return edit_manager