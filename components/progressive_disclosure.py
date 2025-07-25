"""
Progressive Disclosure Component
================================

Implements progressive disclosure of features based on user experience level.
Hides advanced features initially to reduce cognitive load for new users.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json

class ProgressiveDisclosure:
    """Manage progressive disclosure of features"""
    
    def __init__(self):
        self.experience_levels = {
            'beginner': {
                'label': '🌱 Beginner',
                'description': 'Essential features only',
                'features': ['upload', 'view', 'basic_export'],
                'max_features': 5
            },
            'intermediate': {
                'label': '🌿 Intermediate', 
                'description': 'Core features + AI tools',
                'features': ['upload', 'view', 'basic_export', 'ai_summary', 'search', 'bookmarks'],
                'max_features': 10
            },
            'advanced': {
                'label': '🌳 Advanced',
                'description': 'All features including advanced tools',
                'features': 'all',
                'max_features': None
            }
        }
        
        self.feature_categories = {
            'essential': {
                'label': 'Essential',
                'icon': '📌',
                'features': ['upload', 'view', 'navigate', 'basic_export']
            },
            'ai_tools': {
                'label': 'AI Tools',
                'icon': '🤖',
                'features': ['ai_summary', 'ai_qa', 'ai_translate', 'ai_extract']
            },
            'advanced_tools': {
                'label': 'Advanced Tools',
                'icon': '🛠️',
                'features': ['batch_process', 'api_access', 'custom_models', 'automation']
            },
            'collaboration': {
                'label': 'Collaboration',
                'icon': '👥',
                'features': ['share', 'comments', 'version_control', 'team_workspace']
            }
        }
        
        # Initialize user level
        self._init_user_level()
    
    def _init_user_level(self):
        """Initialize user experience level"""
        if 'user_experience_level' not in st.session_state:
            st.session_state.user_experience_level = 'beginner'
            st.session_state.features_unlocked = set(['upload', 'view', 'navigate'])
            st.session_state.first_visit = datetime.now()
            st.session_state.feature_discovery_hints = True
            st.session_state.features_used = {}
    
    def get_current_level(self) -> str:
        """Get current user experience level"""
        return st.session_state.get('user_experience_level', 'beginner')
    
    def should_show_feature(self, feature: str) -> bool:
        """Check if a feature should be shown based on user level"""
        level = self.get_current_level()
        level_config = self.experience_levels[level]
        
        # Advanced users see everything
        if level_config['features'] == 'all':
            return True
        
        # Check if feature is in allowed list
        if feature in level_config['features']:
            return True
        
        # Check if feature has been manually unlocked
        if feature in st.session_state.get('features_unlocked', set()):
            return True
        
        return False
    
    def render_experience_selector(self):
        """Render experience level selector"""
        with st.expander("🎯 Experience Level", expanded=False):
            current_level = self.get_current_level()
            
            # Level selector
            new_level = st.select_slider(
                "Choose your experience level",
                options=list(self.experience_levels.keys()),
                value=current_level,
                format_func=lambda x: self.experience_levels[x]['label']
            )
            
            if new_level != current_level:
                st.session_state.user_experience_level = new_level
                st.success(f"Updated to {self.experience_levels[new_level]['label']}")
                st.rerun()
            
            # Show current level description
            st.info(self.experience_levels[current_level]['description'])
            
            # Feature discovery toggle
            st.checkbox(
                "Show feature hints",
                value=st.session_state.get('feature_discovery_hints', True),
                key='feature_discovery_hints',
                help="Show hints when new features become available"
            )
    
    def render_feature_with_disclosure(self, feature_id: str, render_func: Callable, 
                                     category: str = 'essential', **kwargs) -> Any:
        """Render a feature with progressive disclosure"""
        if not self.should_show_feature(feature_id):
            # Feature is hidden for current level
            if st.session_state.get('feature_discovery_hints', True):
                self._render_locked_feature_hint(feature_id, category)
            return None
        
        # Track feature usage
        self._track_feature_usage(feature_id)
        
        # Render the feature
        return render_func(**kwargs)
    
    def _render_locked_feature_hint(self, feature_id: str, category: str):
        """Render hint for locked feature"""
        category_info = self.feature_categories.get(category, {})
        
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.markdown(f"### {category_info.get('icon', '🔒')}")
            
            with col2:
                st.markdown(f"**{feature_id.replace('_', ' ').title()}**")
                st.caption("Unlock more features by increasing your experience level")
                
                if st.button("🔓 Unlock", key=f"unlock_{feature_id}"):
                    self._unlock_feature(feature_id)
    
    def _unlock_feature(self, feature_id: str):
        """Manually unlock a feature"""
        if 'features_unlocked' not in st.session_state:
            st.session_state.features_unlocked = set()
        
        st.session_state.features_unlocked.add(feature_id)
        st.success(f"✅ Unlocked: {feature_id.replace('_', ' ').title()}")
        st.rerun()
    
    def _track_feature_usage(self, feature_id: str):
        """Track when features are used"""
        if 'features_used' not in st.session_state:
            st.session_state.features_used = {}
        
        if feature_id not in st.session_state.features_used:
            st.session_state.features_used[feature_id] = {
                'first_used': datetime.now(),
                'use_count': 0
            }
        
        st.session_state.features_used[feature_id]['use_count'] += 1
        st.session_state.features_used[feature_id]['last_used'] = datetime.now()
    
    def suggest_level_upgrade(self):
        """Suggest upgrading to next level based on usage"""
        current_level = self.get_current_level()
        
        if current_level == 'advanced':
            return  # Already at max level
        
        # Check usage patterns
        features_used = len(st.session_state.get('features_used', {}))
        days_since_start = (datetime.now() - st.session_state.get('first_visit', datetime.now())).days
        
        # Suggest upgrade criteria
        should_upgrade = False
        
        if current_level == 'beginner':
            # Upgrade to intermediate after 3 days or 5 features used
            should_upgrade = days_since_start >= 3 or features_used >= 5
        elif current_level == 'intermediate':
            # Upgrade to advanced after 7 days or 10 features used
            should_upgrade = days_since_start >= 7 or features_used >= 10
        
        if should_upgrade:
            self._show_upgrade_suggestion()
    
    def _show_upgrade_suggestion(self):
        """Show suggestion to upgrade experience level"""
        current_level = self.get_current_level()
        next_level_key = list(self.experience_levels.keys())
        current_idx = next_level_key.index(current_level)
        
        if current_idx < len(next_level_key) - 1:
            next_level = next_level_key[current_idx + 1]
            next_info = self.experience_levels[next_level]
            
            with st.info("🎯 **Ready for more features?**"):
                st.write(f"You've been using the app actively! Consider upgrading to **{next_info['label']}** to unlock more features.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⬆️ Upgrade Now", type="primary"):
                        st.session_state.user_experience_level = next_level
                        st.success(f"Upgraded to {next_info['label']}!")
                        st.balloons()
                        st.rerun()
                
                with col2:
                    if st.button("Later"):
                        st.session_state.last_upgrade_suggestion = datetime.now()
    
    def render_feature_grid(self, context: str = 'all'):
        """Render available features in a grid"""
        st.markdown("### 🎯 Available Features")
        
        # Group features by category
        for category_id, category_info in self.feature_categories.items():
            if context != 'all' and category_id not in context:
                continue
            
            with st.expander(f"{category_info['icon']} {category_info['label']}", expanded=True):
                features = category_info['features']
                
                # Create grid
                cols = st.columns(3)
                for idx, feature in enumerate(features):
                    with cols[idx % 3]:
                        self._render_feature_card(feature, category_id)
    
    def _render_feature_card(self, feature_id: str, category: str):
        """Render a feature card"""
        is_available = self.should_show_feature(feature_id)
        usage_data = st.session_state.get('features_used', {}).get(feature_id, {})
        
        # Card styling based on availability
        if is_available:
            card_class = "feature-card available"
            icon = "✅"
        else:
            card_class = "feature-card locked"
            icon = "🔒"
        
        # Feature info
        feature_name = feature_id.replace('_', ' ').title()
        use_count = usage_data.get('use_count', 0)
        
        # Render card
        st.markdown(f"""
        <div class="{card_class}">
            <div class="feature-icon">{icon}</div>
            <div class="feature-name">{feature_name}</div>
            <div class="feature-usage">Used {use_count} times</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not is_available:
            if st.button(f"Unlock", key=f"unlock_card_{feature_id}"):
                self._unlock_feature(feature_id)


class AdvancedToolsAccordion:
    """Accordion for advanced tools with progressive disclosure"""
    
    def __init__(self):
        self.sections = {
            'ai_advanced': {
                'label': '🧠 Advanced AI Tools',
                'tools': ['custom_prompts', 'model_selection', 'batch_ai', 'api_integration']
            },
            'document_advanced': {
                'label': '📄 Advanced Document Tools',
                'tools': ['ocr_settings', 'layout_analysis', 'table_extraction', 'form_recognition']
            },
            'export_advanced': {
                'label': '📤 Advanced Export Options',
                'tools': ['custom_templates', 'batch_export', 'api_export', 'webhook_integration']
            }
        }
    
    def render(self, disclosure: ProgressiveDisclosure):
        """Render advanced tools accordion"""
        level = disclosure.get_current_level()
        
        if level == 'beginner':
            # Don't show accordion for beginners
            return
        
        with st.expander("🛠️ Advanced Tools", expanded=False):
            if level == 'intermediate':
                st.info("Some advanced tools are hidden. Upgrade to Advanced level to see all tools.")
            
            for section_id, section_info in self.sections.items():
                st.markdown(f"#### {section_info['label']}")
                
                # Render tools in section
                cols = st.columns(2)
                for idx, tool in enumerate(section_info['tools']):
                    with cols[idx % 2]:
                        if disclosure.should_show_feature(tool):
                            if st.button(tool.replace('_', ' ').title(), 
                                       key=f"tool_{tool}",
                                       use_container_width=True):
                                st.session_state.selected_tool = tool
                        else:
                            st.button(f"🔒 {tool.replace('_', ' ').title()}", 
                                    key=f"locked_{tool}",
                                    disabled=True,
                                    use_container_width=True)


# Feature hint system
class FeatureHints:
    """Show contextual hints for feature discovery"""
    
    def __init__(self):
        self.hints = {
            'first_upload': {
                'trigger': 'document_uploaded',
                'message': "Great! Now try the AI Summary button to get key insights.",
                'feature': 'ai_summary'
            },
            'first_summary': {
                'trigger': 'ai_summary_completed',
                'message': "Nice! You can also ask questions about your document using Q&A.",
                'feature': 'ai_qa'
            },
            'frequent_user': {
                'trigger': 'documents_processed > 5',
                'message': "Power user tip: Try batch processing for multiple documents!",
                'feature': 'batch_process'
            }
        }
    
    def check_and_show_hints(self):
        """Check conditions and show relevant hints"""
        if not st.session_state.get('feature_discovery_hints', True):
            return
        
        shown_hints = st.session_state.get('shown_hints', set())
        
        for hint_id, hint_info in self.hints.items():
            if hint_id not in shown_hints and self._check_trigger(hint_info['trigger']):
                self._show_hint(hint_id, hint_info)
                shown_hints.add(hint_id)
                st.session_state.shown_hints = shown_hints
                break  # Only show one hint at a time
    
    def _check_trigger(self, trigger: str) -> bool:
        """Check if a trigger condition is met"""
        if trigger == 'document_uploaded':
            return st.session_state.get('document_uploaded', False)
        elif trigger == 'ai_summary_completed':
            return 'ai_summary' in st.session_state.get('features_used', {})
        elif trigger.startswith('documents_processed'):
            count = int(trigger.split('>')[-1].strip())
            return st.session_state.get('documents_processed', 0) > count
        return False
    
    def _show_hint(self, hint_id: str, hint_info: Dict):
        """Show a feature discovery hint"""
        with st.container():
            st.info(f"💡 **Tip**: {hint_info['message']}")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Try it!", key=f"hint_{hint_id}"):
                    st.session_state.selected_feature = hint_info['feature']
                    st.rerun()


# Singleton instances
_disclosure_instance = None
_accordion_instance = None
_hints_instance = None

def get_progressive_disclosure() -> ProgressiveDisclosure:
    """Get singleton progressive disclosure instance"""
    global _disclosure_instance
    if _disclosure_instance is None:
        _disclosure_instance = ProgressiveDisclosure()
    return _disclosure_instance

def get_advanced_tools_accordion() -> AdvancedToolsAccordion:
    """Get singleton accordion instance"""
    global _accordion_instance
    if _accordion_instance is None:
        _accordion_instance = AdvancedToolsAccordion()
    return _accordion_instance

def get_feature_hints() -> FeatureHints:
    """Get singleton hints instance"""
    global _hints_instance
    if _hints_instance is None:
        _hints_instance = FeatureHints()
    return _hints_instance