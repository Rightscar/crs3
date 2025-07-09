"""
GPT Configuration Interface Module
Provides customizable GPT prompts and configuration per file processing.
"""

import streamlit as st
import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import time

@dataclass
class GPTConfig:
    """Configuration for GPT dialogue generation"""
    system_prompt: str
    user_prompt_template: str
    temperature: float
    max_tokens: int
    model: str
    dialogue_style: str
    tone: str
    custom_instructions: str
    output_format: str
    quality_threshold: float

class GPTConfigInterface:
    """
    Interface for configuring GPT prompts and settings per file.
    Allows users to customize dialogue generation parameters.
    """
    
    def __init__(self):
        """Initialize the GPT configuration interface"""
        self.config_presets = self._load_config_presets()
        self.current_config = None
        
    def _load_config_presets(self) -> Dict[str, GPTConfig]:
        """Load predefined configuration presets"""
        return {
            "Educational": GPTConfig(
                system_prompt="""You are an expert educational dialogue creator. Your task is to convert text content into engaging educational conversations between a teacher and student. Focus on:
- Clear explanations of key concepts
- Logical progression of ideas
- Encouraging critical thinking
- Making complex topics accessible""",
                user_prompt_template="""Convert the following text into an educational dialogue between a teacher and student. The dialogue should capture the main concepts and encourage learning:

Text: {content}

Format the output as:
Teacher: [question or explanation]
Student: [response or follow-up question]
Teacher: [further explanation or new concept]

Ensure the dialogue is natural, educational, and engaging.""",
                temperature=0.7,
                max_tokens=1000,
                model="gpt-4",
                dialogue_style="Educational",
                tone="Encouraging and Clear",
                custom_instructions="Focus on learning outcomes and comprehension",
                output_format="Teacher-Student Dialogue",
                quality_threshold=0.8
            ),
            
            "Conversational": GPTConfig(
                system_prompt="""You are a skilled conversation designer. Create natural, flowing dialogues that capture the essence of the source material. Focus on:
- Natural speech patterns
- Engaging back-and-forth exchanges
- Maintaining the original meaning
- Creating relatable conversations""",
                user_prompt_template="""Transform this text into a natural conversation between two people discussing the topic. Make it engaging and authentic:

Text: {content}

Format as:
Person A: [statement or question]
Person B: [response or insight]
Person A: [follow-up or new point]

Keep the conversation natural and true to the source material.""",
                temperature=0.8,
                max_tokens=1200,
                model="gpt-4",
                dialogue_style="Conversational",
                tone="Natural and Engaging",
                custom_instructions="Maintain authenticity and natural flow",
                output_format="Two-Person Conversation",
                quality_threshold=0.7
            ),
            
            "Q&A Format": GPTConfig(
                system_prompt="""You are an expert at creating comprehensive Q&A pairs from text content. Focus on:
- Extracting key information
- Creating clear, specific questions
- Providing complete, accurate answers
- Covering all important points""",
                user_prompt_template="""Create comprehensive Q&A pairs from this text. Extract the most important information and present it as questions and answers:

Text: {content}

Format as:
Q: [specific question about the content]
A: [complete, accurate answer]

Ensure all key points are covered and answers are informative.""",
                temperature=0.6,
                max_tokens=1500,
                model="gpt-4",
                dialogue_style="Q&A",
                tone="Informative and Precise",
                custom_instructions="Extract all key information comprehensively",
                output_format="Question-Answer Pairs",
                quality_threshold=0.9
            ),
            
            "Interview Style": GPTConfig(
                system_prompt="""You are creating interview-style dialogues where an interviewer asks insightful questions about the content and an expert provides detailed responses. Focus on:
- Thoughtful, probing questions
- Expert-level responses
- Deep exploration of topics
- Professional interview format""",
                user_prompt_template="""Create an interview-style dialogue about this content, with an interviewer asking insightful questions and an expert providing detailed answers:

Text: {content}

Format as:
Interviewer: [thoughtful question]
Expert: [detailed, knowledgeable response]
Interviewer: [follow-up question]

Make the interview engaging and informative.""",
                temperature=0.7,
                max_tokens=1300,
                model="gpt-4",
                dialogue_style="Interview",
                tone="Professional and Insightful",
                custom_instructions="Create thought-provoking questions and expert responses",
                output_format="Interview Format",
                quality_threshold=0.8
            ),
            
            "Custom": GPTConfig(
                system_prompt="You are a helpful AI assistant that creates dialogues from text content.",
                user_prompt_template="Convert this text into a dialogue: {content}",
                temperature=0.7,
                max_tokens=1000,
                model="gpt-4",
                dialogue_style="Custom",
                tone="Neutral",
                custom_instructions="",
                output_format="Custom Format",
                quality_threshold=0.7
            )
        }
    
    def render_config_interface(self) -> GPTConfig:
        """
        Render the GPT configuration interface
        
        Returns:
            Configured GPTConfig object
        """
        st.subheader("⚙️ GPT Configuration")
        
        # Preset selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_preset = st.selectbox(
                "Choose a configuration preset",
                options=list(self.config_presets.keys()),
                index=0,
                help="Select a predefined configuration or choose 'Custom' to create your own"
            )
        
        with col2:
            if st.button("💾 Save as Preset"):
                self._save_custom_preset()
        
        # Load selected preset
        config = self.config_presets[selected_preset]
        
        # Configuration tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Prompts", "⚙️ Model Settings", "🎨 Style & Tone", "📊 Quality Control"])
        
        with tab1:
            st.subheader("Prompt Configuration")
            
            # System prompt
            config.system_prompt = st.text_area(
                "System Prompt",
                value=config.system_prompt,
                height=150,
                help="Instructions that define the AI's role and behavior"
            )
            
            # User prompt template
            config.user_prompt_template = st.text_area(
                "User Prompt Template",
                value=config.user_prompt_template,
                height=200,
                help="Template for the user prompt. Use {content} as placeholder for the text content"
            )
            
            # Validate prompt template
            if "{content}" not in config.user_prompt_template:
                st.warning("⚠️ User prompt template should include {content} placeholder")
            
            # Custom instructions
            config.custom_instructions = st.text_area(
                "Additional Instructions",
                value=config.custom_instructions,
                height=100,
                help="Any additional specific instructions for dialogue generation"
            )
        
        with tab2:
            st.subheader("Model Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                config.model = st.selectbox(
                    "Model",
                    options=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    index=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"].index(config.model),
                    help="Choose the GPT model to use"
                )
                
                config.temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=config.temperature,
                    step=0.1,
                    help="Controls randomness. Lower = more focused, Higher = more creative"
                )
            
            with col2:
                config.max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=4000,
                    value=config.max_tokens,
                    step=100,
                    help="Maximum length of generated response"
                )
                
                config.quality_threshold = st.slider(
                    "Quality Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=config.quality_threshold,
                    step=0.1,
                    help="Minimum quality score for accepting generated dialogues"
                )
        
        with tab3:
            st.subheader("Style & Tone Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                config.dialogue_style = st.selectbox(
                    "Dialogue Style",
                    options=["Educational", "Conversational", "Q&A", "Interview", "Debate", "Storytelling", "Custom"],
                    index=["Educational", "Conversational", "Q&A", "Interview", "Debate", "Storytelling", "Custom"].index(config.dialogue_style) if config.dialogue_style in ["Educational", "Conversational", "Q&A", "Interview", "Debate", "Storytelling", "Custom"] else 6,
                    help="Overall style of the dialogue"
                )
                
                config.tone = st.selectbox(
                    "Tone",
                    options=[
                        "Professional", "Casual", "Academic", "Friendly", 
                        "Formal", "Encouraging", "Neutral", "Enthusiastic",
                        "Thoughtful", "Analytical", "Creative", "Custom"
                    ],
                    index=0 if config.tone not in [
                        "Professional", "Casual", "Academic", "Friendly", 
                        "Formal", "Encouraging", "Neutral", "Enthusiastic",
                        "Thoughtful", "Analytical", "Creative", "Custom"
                    ] else [
                        "Professional", "Casual", "Academic", "Friendly", 
                        "Formal", "Encouraging", "Neutral", "Enthusiastic",
                        "Thoughtful", "Analytical", "Creative", "Custom"
                    ].index(config.tone),
                    help="Tone of voice for the dialogue"
                )
            
            with col2:
                config.output_format = st.selectbox(
                    "Output Format",
                    options=[
                        "Teacher-Student Dialogue", "Two-Person Conversation",
                        "Question-Answer Pairs", "Interview Format",
                        "Panel Discussion", "Debate Format", "Custom Format"
                    ],
                    index=0 if config.output_format not in [
                        "Teacher-Student Dialogue", "Two-Person Conversation",
                        "Question-Answer Pairs", "Interview Format",
                        "Panel Discussion", "Debate Format", "Custom Format"
                    ] else [
                        "Teacher-Student Dialogue", "Two-Person Conversation",
                        "Question-Answer Pairs", "Interview Format",
                        "Panel Discussion", "Debate Format", "Custom Format"
                    ].index(config.output_format),
                    help="Structure and format of the output dialogue"
                )
        
        with tab4:
            st.subheader("Quality Control")
            
            # Quality metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Quality Checks:**")
                enable_length_check = st.checkbox("Minimum length validation", value=True)
                enable_format_check = st.checkbox("Format validation", value=True)
                enable_content_check = st.checkbox("Content relevance check", value=True)
                
                if enable_length_check:
                    min_words = st.number_input("Minimum words per dialogue", min_value=10, max_value=1000, value=50)
            
            with col2:
                st.write("**Auto-corrections:**")
                auto_fix_format = st.checkbox("Auto-fix formatting issues", value=True)
                auto_enhance_quality = st.checkbox("Auto-enhance low quality outputs", value=False)
                retry_on_failure = st.checkbox("Retry on quality failure", value=True)
                
                if retry_on_failure:
                    max_retries = st.number_input("Max retries", min_value=1, max_value=5, value=2)
        
        # Preview section
        with st.expander("🔍 Preview Configuration", expanded=False):
            st.write("**Current Configuration Summary:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"• **Model:** {config.model}")
                st.write(f"• **Style:** {config.dialogue_style}")
                st.write(f"• **Tone:** {config.tone}")
                st.write(f"• **Format:** {config.output_format}")
            
            with col2:
                st.write(f"• **Temperature:** {config.temperature}")
                st.write(f"• **Max Tokens:** {config.max_tokens}")
                st.write(f"• **Quality Threshold:** {config.quality_threshold}")
            
            # Sample prompt preview
            sample_content = "This is a sample text about artificial intelligence and machine learning."
            sample_prompt = config.user_prompt_template.format(content=sample_content)
            
            st.write("**Sample Generated Prompt:**")
            st.code(f"System: {config.system_prompt[:100]}...\n\nUser: {sample_prompt[:200]}...", language="text")
        
        # Save configuration to session state
        st.session_state.gpt_config = config
        
        return config
    
    def _save_custom_preset(self):
        """Save current configuration as a custom preset"""
        if hasattr(st.session_state, 'gpt_config'):
            preset_name = st.text_input("Preset name:", key="preset_name_input")
            if preset_name and st.button("Save", key="save_preset_btn"):
                self.config_presets[preset_name] = st.session_state.gpt_config
                st.success(f"Preset '{preset_name}' saved!")
    
    def export_config(self, config: GPTConfig) -> str:
        """
        Export configuration as JSON string
        
        Args:
            config: GPTConfig object to export
            
        Returns:
            JSON string representation
        """
        return json.dumps(asdict(config), indent=2)
    
    def import_config(self, config_json: str) -> GPTConfig:
        """
        Import configuration from JSON string
        
        Args:
            config_json: JSON string representation
            
        Returns:
            GPTConfig object
        """
        config_dict = json.loads(config_json)
        return GPTConfig(**config_dict)
    
    def validate_config(self, config: GPTConfig) -> List[str]:
        """
        Validate configuration and return any issues
        
        Args:
            config: GPTConfig object to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        if not config.system_prompt.strip():
            issues.append("System prompt cannot be empty")
        
        if not config.user_prompt_template.strip():
            issues.append("User prompt template cannot be empty")
        
        if "{content}" not in config.user_prompt_template:
            issues.append("User prompt template must include {content} placeholder")
        
        if config.temperature < 0 or config.temperature > 2:
            issues.append("Temperature must be between 0 and 2")
        
        if config.max_tokens < 1 or config.max_tokens > 4000:
            issues.append("Max tokens must be between 1 and 4000")
        
        if config.quality_threshold < 0 or config.quality_threshold > 1:
            issues.append("Quality threshold must be between 0 and 1")
        
        return issues
    
    def get_optimized_config_for_content(self, content_type: str, content_length: int) -> GPTConfig:
        """
        Get optimized configuration based on content characteristics
        
        Args:
            content_type: Type of content (e.g., "academic", "narrative", "technical")
            content_length: Length of content in characters
            
        Returns:
            Optimized GPTConfig
        """
        # Base configuration
        if content_type.lower() in ["academic", "research", "scientific"]:
            base_config = self.config_presets["Q&A Format"]
        elif content_type.lower() in ["story", "narrative", "fiction"]:
            base_config = self.config_presets["Conversational"]
        elif content_type.lower() in ["interview", "discussion"]:
            base_config = self.config_presets["Interview Style"]
        else:
            base_config = self.config_presets["Educational"]
        
        # Adjust based on content length
        if content_length > 5000:  # Long content
            base_config.max_tokens = min(1500, base_config.max_tokens)
            base_config.temperature = max(0.6, base_config.temperature - 0.1)
        elif content_length < 500:  # Short content
            base_config.max_tokens = max(500, base_config.max_tokens)
            base_config.temperature = min(0.8, base_config.temperature + 0.1)
        
        return base_config

# Global instance
gpt_config_interface = GPTConfigInterface()

def render_gpt_config_interface() -> GPTConfig:
    """
    Convenience function to render the GPT configuration interface
    
    Returns:
        Configured GPTConfig object
    """
    return gpt_config_interface.render_config_interface()

