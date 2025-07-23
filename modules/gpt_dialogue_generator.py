"""
GPT Dialogue Generator Module
============================

Converts text chunks into dialogue/Q&A format using OpenAI GPT.
Takes spaCy-processed chunks and generates high-quality conversations.

Features:
- Topic-guided dialogue generation
- Multiple dialogue styles (Q&A, conversation, interview)
- Batch processing for multiple chunks
- Error handling and retry logic
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Optional streamlit import for UI components
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
import os

# OpenAI dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DialogueItem:
    """Represents a generated dialogue item"""
    id: str
    question: str
    answer: str
    source_chunk_id: str
    dialogue_type: str
    topics: List[str]
    confidence: float = 0.8

class GPTDialogueGenerator:
    """Generate dialogues from text chunks using GPT"""
    
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # Initialize OpenAI client if API key is available
        if self.api_key and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_available = False
        else:
            logger.warning("OpenAI API key not found or OpenAI not available - using demo mode")
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI API - now handled in __init__"""
        # This method is now redundant but kept for compatibility
        pass
    
    def generate_dialogue_real(self, chunk_text: str, 
                             dialogue_style: str = "Q&A",
                             questions_count: int = 3,
                             model: str = "gpt-3.5-turbo",
                             temperature: float = 0.7) -> Dict[str, Any]:
        """Generate real dialogue using OpenAI API"""
        
        if not self.client:
            logger.warning("OpenAI client not available, falling back to demo mode")
            return self._generate_demo_dialogue(chunk_text, questions_count)
        
        try:
            # Build prompt based on dialogue style
            prompt = self._build_dialogue_prompt(chunk_text, dialogue_style, questions_count)
            
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating educational dialogues from text content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            # Parse the response safely
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("OpenAI API returned empty response")
            
            choice = response.choices[0]
            if not choice or not hasattr(choice, 'message') or not hasattr(choice.message, 'content'):
                raise ValueError("OpenAI API returned malformed response")
                
            generated_content = choice.message.content
            
            # Calculate quality score based on content
            quality_score = self._calculate_quality_score(generated_content, chunk_text)
            
            return {
                "content": generated_content,
                "word_count": len(generated_content.split()),
                "quality_score": quality_score,
                "model_used": model,
                "temperature": temperature,
                "questions_count": questions_count,
                "style": dialogue_style,
                "api_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to demo mode
            return self._generate_demo_dialogue(chunk_text, questions_count)
    
    def _build_dialogue_prompt(self, chunk_text: str, style: str, questions_count: int) -> str:
        """Build prompt for OpenAI based on dialogue style"""
        
        base_prompt = f"""Please create {questions_count} high-quality questions and answers based on the following text content.

Text Content:
{chunk_text}

Requirements:
- Generate exactly {questions_count} question-answer pairs
- Make questions thought-provoking and educational
- Ensure answers are accurate and based only on the provided text
- """
        
        if style == "Q&A":
            base_prompt += """- Format as: Q: [question] A: [answer]
- Questions should test comprehension and analysis"""
            
        elif style == "Interview":
            base_prompt += """- Format as: Interviewer: [question] Expert: [answer]
- Questions should be conversational and exploratory"""
            
        elif style == "Socratic":
            base_prompt += """- Format as: Q: [question] A: [answer]
- Questions should be probing and lead to deeper thinking"""
            
        elif style == "Academic":
            base_prompt += """- Format as: Q: [question] A: [answer]
- Questions should be scholarly and analytical"""
        
        base_prompt += "\n\nGenerate the dialogue now:"
        
        return base_prompt
    
    def _calculate_quality_score(self, generated_content: str, source_text: str) -> float:
        """Calculate quality score for generated dialogue"""
        try:
            # Basic quality metrics
            word_count = len(generated_content.split())
            source_word_count = len(source_text.split())
            
            # Length ratio (should be reasonable)
            length_ratio = word_count / max(source_word_count, 1)
            length_score = min(1.0, max(0.0, 1.0 - abs(length_ratio - 0.5)))
            
            # Question count detection
            question_count = generated_content.count('Q:') + generated_content.count('?')
            question_score = min(1.0, question_count / 3.0)
            
            # Answer presence
            answer_indicators = ['A:', 'Expert:', 'Answer:', 'Response:']
            answer_count = sum(generated_content.count(indicator) for indicator in answer_indicators)
            answer_score = min(1.0, answer_count / 3.0)
            
            # Overall score (weighted average)
            overall_score = (length_score * 0.3 + question_score * 0.4 + answer_score * 0.3)
            
            return max(0.1, min(1.0, overall_score))
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.7  # Default score
    
    def _generate_demo_dialogue(self, chunk_text: str, questions_count: int) -> Dict[str, Any]:
        """Generate demo dialogue when OpenAI is not available"""
        
        # Extract key concepts for demo questions
        words = chunk_text.split()
        key_words = [word for word in words if len(word) > 5][:5]
        
        demo_content = ""
        for i in range(min(questions_count, 3)):
            if i == 0:
                demo_content += f"Q: What is the main topic discussed in this content?\n"
                demo_content += f"A: The content discusses {', '.join(key_words[:2])} and related concepts.\n\n"
            elif i == 1:
                demo_content += f"Q: What are the key points mentioned?\n"
                demo_content += f"A: The key points include information about {', '.join(key_words[2:4])} among other topics.\n\n"
            else:
                demo_content += f"Q: How can this information be applied?\n"
                demo_content += f"A: This information provides insights that can be used to understand {key_words[-1] if key_words else 'the topic'} better.\n\n"
        
        return {
            "content": demo_content.strip(),
            "word_count": len(demo_content.split()),
            "quality_score": 0.75,  # Demo mode quality
            "model_used": "demo",
            "questions_count": min(questions_count, 3),
            "style": "Q&A",
            "is_demo": True
        }

    def generate_dialogues(self, chunks: List[Dict[str, Any]], 
                          dialogue_style: str = "Q&A",
                          topics: List[str] = None,
                          max_dialogues_per_chunk: int = 3) -> List[DialogueItem]:
        """
        Generate dialogues from text chunks
        
        Args:
            chunks: List of content chunks
            dialogue_style: Style of dialogue (Q&A, conversation, interview)
            topics: Optional topic guidance
            max_dialogues_per_chunk: Maximum dialogues per chunk
            
        Returns:
            List of DialogueItem objects
        """
        if not self.openai_available or not self.api_key:
            return self._generate_fallback_dialogues(chunks, dialogue_style, topics)
        
        dialogues = []
        
        for chunk in chunks:
            try:
                chunk_dialogues = self._generate_chunk_dialogues(
                    chunk, dialogue_style, topics, max_dialogues_per_chunk
                )
                dialogues.extend(chunk_dialogues)
                
                # Add small delay to respect rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error generating dialogues for chunk {chunk.get('id', 'unknown')}: {e}")
                # Generate fallback for this chunk
                fallback = self._generate_fallback_dialogues([chunk], dialogue_style, topics)
                dialogues.extend(fallback)
        
        return dialogues
    
    def _generate_chunk_dialogues(self, chunk: Dict[str, Any], 
                                 dialogue_style: str,
                                 topics: List[str],
                                 max_dialogues: int) -> List[DialogueItem]:
        """Generate dialogues for a single chunk"""
        
        # Prepare prompt
        prompt = self._create_prompt(chunk, dialogue_style, topics, max_dialogues)
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at creating educational dialogue and Q&A content from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse response safely
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("OpenAI API returned empty response for dialogue generation")
            
            choice = response.choices[0]
            if not choice or not hasattr(choice, 'message') or not hasattr(choice.message, 'content'):
                raise ValueError("OpenAI API returned malformed response for dialogue generation")
                
            content = choice.message.content
            dialogues = self._parse_gpt_response(content, chunk['id'], dialogue_style, topics)
            
            return dialogues
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_fallback_dialogues([chunk], dialogue_style, topics)
    
    def _create_prompt(self, chunk: Dict[str, Any], 
                      dialogue_style: str,
                      topics: List[str],
                      max_dialogues: int) -> str:
        """Create prompt for GPT"""
        
        text = chunk['text']
        chunk_topics = chunk.get('topics', [])
        
        # Base prompt based on style
        if dialogue_style == "Q&A":
            style_instruction = "Create clear, educational question-answer pairs"
        elif dialogue_style == "Conversation":
            style_instruction = "Create natural conversation exchanges between two people"
        elif dialogue_style == "Interview":
            style_instruction = "Create interview-style questions and detailed answers"
        else:
            style_instruction = "Create educational question-answer pairs"
        
        # Topic guidance
        topic_guidance = ""
        if topics:
            topic_guidance = f"\nFocus on these topics: {', '.join(topics)}"
        elif chunk_topics:
            topic_guidance = f"\nConsider these topics from the text: {', '.join(chunk_topics[:3])}"
        
        prompt = f"""
{style_instruction} based on the following text content.

TEXT CONTENT:
{text}

INSTRUCTIONS:
- Generate {max_dialogues} high-quality dialogue items
- Make questions thought-provoking and answers comprehensive
- Ensure answers are grounded in the provided text
- Use natural, engaging language
- Each dialogue should be self-contained{topic_guidance}

FORMAT:
Return as JSON array with this structure:
[
  {{
    "question": "Your question here",
    "answer": "Your detailed answer here"
  }}
]

Generate exactly {max_dialogues} dialogue items:
"""
        
        return prompt
    
    def _parse_text_fallback(self, content: str, chunk_id: str, topics: List[str] = None) -> List[DialogueItem]:
        """Fallback text parsing when JSON parsing fails"""
        try:
            # Simple Q&A pattern matching
            lines = content.strip().split('\n')
            results = []
            current_question = None
            
            for line in lines:
                line = line.strip()
                if line.startswith(('Q:', 'Question:', '**Q:', '**Question:')):
                    current_question = line.split(':', 1)[-1].strip()
                elif line.startswith(('A:', 'Answer:', '**A:', '**Answer:')) and current_question:
                    current_answer = line.split(':', 1)[-1].strip()
                    
                    dialogue_item = DialogueItem(
                        id=f"{chunk_id}_fallback_{len(results)}",
                        chunk_id=chunk_id,
                        question=current_question,
                        answer=current_answer,
                        dialogue_type="qa_pair",
                        confidence=0.6,  # Lower confidence for fallback
                        topics=topics if topics else [],
                        metadata={'generated_by': 'text_fallback'}
                    )
                    results.append(dialogue_item)
                    current_question = None
            
            return results
        except Exception as e:
            logger.error(f"Text fallback parsing failed: {e}")
            return []

    def _parse_gpt_response(self, content: str, chunk_id: str, 
                           dialogue_style: str, topics: List[str]) -> List[DialogueItem]:
        """Parse GPT response into DialogueItem objects"""
        
        dialogues = []
        
        try:
            # Try to parse as JSON
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                try:
                    parsed_data = json.loads(json_content)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse JSON from OpenAI response: {e}")
                    # Fallback to basic text parsing
                    return self._parse_text_fallback(content, chunk_id, topics)
                
                for i, item in enumerate(parsed_data):
                    if 'question' in item and 'answer' in item:
                        dialogue = DialogueItem(
                            id=f"{chunk_id}_dialogue_{i}",
                            question=item['question'],
                            answer=item['answer'],
                            source_chunk_id=chunk_id,
                            dialogue_type=dialogue_style,
                            topics=topics or [],
                            confidence=0.9
                        )
                        dialogues.append(dialogue)
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from GPT response for chunk {chunk_id}")
            # Try to extract Q&A pairs manually
            dialogues = self._extract_qa_manually(content, chunk_id, dialogue_style, topics)
        
        return dialogues
    
    def _extract_qa_manually(self, content: str, chunk_id: str,
                            dialogue_style: str, topics: List[str]) -> List[DialogueItem]:
        """Manually extract Q&A pairs from text"""
        
        dialogues = []
        lines = content.split('\n')
        
        current_question = ""
        current_answer = ""
        dialogue_count = 0
        
        for line in lines:
            line = line.strip()
            
            # Look for question patterns
            if any(line.startswith(prefix) for prefix in ['Q:', 'Question:', '**Q:', 'Q.']):
                if current_question and current_answer:
                    # Save previous dialogue
                    dialogue = DialogueItem(
                        id=f"{chunk_id}_dialogue_{dialogue_count}",
                        question=current_question,
                        answer=current_answer,
                        source_chunk_id=chunk_id,
                        dialogue_type=dialogue_style,
                        topics=topics or [],
                        confidence=0.7
                    )
                    dialogues.append(dialogue)
                    dialogue_count += 1
                
                # Start new question
                current_question = line.split(':', 1)[-1].strip()
                current_answer = ""
            
            # Look for answer patterns
            elif any(line.startswith(prefix) for prefix in ['A:', 'Answer:', '**A:', 'A.']):
                current_answer = line.split(':', 1)[-1].strip()
            
            # Continue building answer
            elif current_question and line and not line.startswith(('Q', 'A', '**')):
                if current_answer:
                    current_answer += " " + line
                else:
                    current_answer = line
        
        # Add final dialogue
        if current_question and current_answer:
            dialogue = DialogueItem(
                id=f"{chunk_id}_dialogue_{dialogue_count}",
                question=current_question,
                answer=current_answer,
                source_chunk_id=chunk_id,
                dialogue_type=dialogue_style,
                topics=topics or [],
                confidence=0.7
            )
            dialogues.append(dialogue)
        
        return dialogues
    
    def _generate_fallback_dialogues(self, chunks: List[Dict[str, Any]],
                                   dialogue_style: str,
                                   topics: List[str]) -> List[DialogueItem]:
        """Generate simple fallback dialogues when GPT is not available"""
        
        dialogues = []
        
        for chunk in chunks:
            text = chunk['text']
            chunk_id = chunk['id']
            
            # Simple question generation based on text content
            sentences = text.split('.')
            
            for i, sentence in enumerate(sentences[:2]):  # Max 2 per chunk
                sentence = sentence.strip()
                if len(sentence) > 20:
                    # Generate simple question
                    question = f"What can you tell me about {sentence[:50]}...?"
                    answer = sentence + "."
                    
                    dialogue = DialogueItem(
                        id=f"{chunk_id}_fallback_{i}",
                        question=question,
                        answer=answer,
                        source_chunk_id=chunk_id,
                        dialogue_type=dialogue_style,
                        topics=topics or [],
                        confidence=0.5
                    )
                    dialogues.append(dialogue)
        
        return dialogues

def render_dialogue_generation_ui(selected_chunks: List[Dict[str, Any]]) -> List[DialogueItem]:
    """
    Render dialogue generation interface
    
    Args:
        selected_chunks: List of selected content chunks
        
    Returns:
        List of generated DialogueItem objects
    """
    if not STREAMLIT_AVAILABLE:
        logging.warning("Streamlit not available - UI components disabled. Use generate_dialogue_from_chunks() for non-UI access.")
        return []
        
    if not selected_chunks:
        st.warning("No chunks selected. Please select chunks first.")
        return []
    
    st.subheader("🤖 GPT Dialogue Generation")
    
    # API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key to generate dialogues",
        placeholder="sk-..."
    )
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Generation options
    col1, col2 = st.columns(2)
    
    with col1:
        dialogue_style = st.selectbox(
            "Dialogue Style",
            ["Q&A", "Conversation", "Interview"],
            help="Choose the style of dialogue to generate"
        )
    
    with col2:
        max_per_chunk = st.slider(
            "Dialogues per Chunk",
            min_value=1,
            max_value=5,
            value=2,
            help="Number of dialogues to generate per chunk"
        )
    
    # Topic guidance
    topic_input = st.text_input(
        "Topic Guidance (Optional)",
        placeholder="Enter topics separated by commas (e.g., philosophy, consciousness, meditation)",
        help="Guide the dialogue generation towards specific topics"
    )
    
    topics = [topic.strip() for topic in topic_input.split(',') if topic.strip()] if topic_input else []
    
    # Generation summary
    st.info(f"📊 Ready to generate ~{len(selected_chunks) * max_per_chunk} dialogues from {len(selected_chunks)} chunks")
    
    # Generate button
    if st.button("🚀 Generate Dialogues", type="primary"):
        if not api_key:
            st.error("Please enter your OpenAI API key to generate dialogues")
            return []
        
        with st.spinner("Generating dialogues with GPT..."):
            generator = GPTDialogueGenerator()
            
            # Convert chunks to proper format
            chunk_dicts = []
            for chunk in selected_chunks:
                if hasattr(chunk, '__dict__'):
                    chunk_dicts.append(chunk.__dict__)
                else:
                    chunk_dicts.append(chunk)
            
            dialogues = generator.generate_dialogues(
                chunk_dicts,
                dialogue_style=dialogue_style,
                topics=topics,
                max_dialogues_per_chunk=max_per_chunk
            )
            
            if dialogues:
                st.success(f"✅ Generated {len(dialogues)} dialogues successfully!")
                
                # Show preview
                with st.expander("📋 Generated Dialogues Preview", expanded=True):
                    for i, dialogue in enumerate(dialogues[:3]):  # Show first 3
                        st.write(f"**Q{i+1}:** {dialogue.question}")
                        st.write(f"**A{i+1}:** {dialogue.answer}")
                        st.write("---")
                    
                    if len(dialogues) > 3:
                        st.write(f"... and {len(dialogues) - 3} more dialogues")
                
                return dialogues
            else:
                st.error("Failed to generate dialogues. Please check your API key and try again.")
                return []
    
    return []

def generate_dialogues_cached(chunks_data: List[Dict[str, Any]], 
                             dialogue_style: str,
                             topics: List[str],
                             max_per_chunk: int,
                             api_key_hash: str) -> List[Dict[str, Any]]:
    """
    Cached dialogue generation function
    
    Args:
        chunks_data: Chunk data
        dialogue_style: Style of dialogue
        topics: Topic guidance
        max_per_chunk: Max dialogues per chunk
        api_key_hash: Hash of API key for cache invalidation
        
    Returns:
        List of dialogue dictionaries
    """
    generator = GPTDialogueGenerator()
    dialogues = generator.generate_dialogues(
        chunks_data, dialogue_style, topics, max_per_chunk
    )
    
    # Convert to dictionaries for caching
    return [
        {
            'id': d.id,
            'question': d.question,
            'answer': d.answer,
            'source_chunk_id': d.source_chunk_id,
            'dialogue_type': d.dialogue_type,
            'topics': d.topics,
            'confidence': d.confidence
        }
        for d in dialogues
    ]

def dialogues_from_dicts(dialogue_dicts: List[Dict[str, Any]]) -> List[DialogueItem]:
    """Convert dialogue dictionaries back to DialogueItem objects"""
    return [
        DialogueItem(
            id=d['id'],
            question=d['question'],
            answer=d['answer'],
            source_chunk_id=d['source_chunk_id'],
            dialogue_type=d['dialogue_type'],
            topics=d['topics'],
            confidence=d['confidence']
        )
        for d in dialogue_dicts
    ]

