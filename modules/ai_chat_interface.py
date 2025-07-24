"""
AI Chat Interface Module
========================

Interactive AI chat interface for document querying and assistance.
Provides conversational AI capabilities for document analysis and Q&A.

Features:
- Document-grounded chat responses
- Interactive Q&A with context
- Chat history management
- AI response confidence scoring
- Multi-turn conversations
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

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat message container"""
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    confidence: float = 0.0
    source_page: Optional[int] = None
    context_used: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ChatSession:
    """Chat session container"""
    session_id: str
    document_id: Optional[str]
    document_title: str
    messages: List[ChatMessage]
    created_at: str
    last_activity: str
    total_messages: int

class AIChatInterface:
    """AI-powered chat interface for document interaction"""
    
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        self.api_key = None
        self.client = None
        
        # Initialize OpenAI if available
        if OPENAI_AVAILABLE:
            import os
            self.api_key = os.getenv('OPENAI_API_KEY')
            if self.api_key:
                try:
                    self.client = openai.OpenAI(api_key=self.api_key)
                    logger.info("OpenAI client initialized for chat interface")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.openai_available = False
        
        # Chat state management
        self.current_session = None
        self.chat_history = []
        self.context_memory = {}
        
        # Demo responses for when OpenAI is not available
        self.demo_responses = {
            'greeting': "Hello! I'm your AI document assistant. I can help you analyze and understand your document. What would you like to know?",
            'summary': "Based on the document content, here's a summary: [This would be generated from the actual document content using AI analysis]",
            'question': "That's an interesting question about the document. Let me analyze the relevant sections...",
            'clarification': "Could you provide more specific details about what aspect of the document you'd like me to focus on?",
            'default': "I understand your query. In a full implementation, I would analyze the document content and provide a detailed response based on the specific text you're asking about."
        }
    
    def initialize_chat_session(self, document_id: str = None, document_title: str = "Document") -> str:
        """Initialize a new chat session"""
        session_id = str(uuid.uuid4())[:8]
        
        self.current_session = ChatSession(
            session_id=session_id,
            document_id=document_id,
            document_title=document_title,
            messages=[],
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            total_messages=0
        )
        
        # Add system message
        system_message = ChatMessage(
            id=str(uuid.uuid4())[:8],
            role='system',
            content=f"You are an AI assistant helping users understand and analyze the document: '{document_title}'. Provide helpful, accurate responses based on the document content.",
            timestamp=datetime.now().isoformat(),
            confidence=1.0,
            metadata={'type': 'system_init'}
        )
        
        self.current_session.messages.append(system_message)
        
        logger.info(f"Chat session initialized: {session_id} for document: {document_title}")
        return session_id
    
    def send_message(self, user_message: str, document_context: str = "", 
                    current_page: int = None) -> ChatMessage:
        """Send a message and get AI response"""
        
        if not self.current_session:
            self.initialize_chat_session()
        
        # Add user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4())[:8],
            role='user',
            content=user_message,
            timestamp=datetime.now().isoformat(),
            source_page=current_page,
            metadata={'type': 'user_query'}
        )
        
        self.current_session.messages.append(user_msg)
        
        # Generate AI response
        ai_response = self._generate_ai_response(user_message, document_context, current_page)
        
        self.current_session.messages.append(ai_response)
        self.current_session.last_activity = datetime.now().isoformat()
        self.current_session.total_messages += 2
        
        return ai_response
    
    def _generate_ai_response(self, user_message: str, document_context: str = "", 
                             current_page: int = None) -> ChatMessage:
        """Generate AI response to user message"""
        
        if self.openai_available and self.client:
            return self._generate_openai_response(user_message, document_context, current_page)
        else:
            return self._generate_demo_response(user_message, document_context, current_page)
    
    def _generate_openai_response(self, user_message: str, document_context: str = "", 
                                 current_page: int = None) -> ChatMessage:
        """Generate response using OpenAI"""
        try:
            # Prepare conversation history
            messages = []
            
            # Add system context
            system_prompt = f"""You are an AI document assistant. You are helping a user understand and analyze their document.

Document context (current page {current_page or 'unknown'}):
{document_context[:2000] if document_context else 'No specific context provided'}

Guidelines:
- Provide helpful, accurate responses based on the document content
- If you don't have enough context, ask for clarification
- Keep responses concise but informative
- Reference specific parts of the document when relevant
- If the question is about something not in the provided context, say so clearly
"""
            
            messages.append({"role": "system", "content": system_prompt})
            
            # Add recent conversation history (last 6 messages)
            recent_messages = self.current_session.messages[-6:] if self.current_session else []
            for msg in recent_messages:
                if msg.role in ['user', 'assistant']:
                    messages.append({"role": msg.role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_content = response.choices[0].message.content
            confidence = 0.9  # High confidence for OpenAI responses
            
            return ChatMessage(
                id=str(uuid.uuid4())[:8],
                role='assistant',
                content=ai_content,
                timestamp=datetime.now().isoformat(),
                confidence=confidence,
                source_page=current_page,
                context_used=document_context[:200] + "..." if document_context else None,
                metadata={
                    'type': 'openai_response',
                    'model': 'gpt-3.5-turbo',
                    'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI response generation error: {e}")
            return self._generate_demo_response(user_message, document_context, current_page)
    
    def _generate_demo_response(self, user_message: str, document_context: str = "", 
                               current_page: int = None) -> ChatMessage:
        """Generate demo response when OpenAI is not available"""
        
        message_lower = user_message.lower()
        
        # Determine response type based on user message
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            response_content = self.demo_responses['greeting']
        elif any(word in message_lower for word in ['summary', 'summarize', 'overview']):
            response_content = f"📄 **Document Summary**: {self.demo_responses['summary']}"
            if document_context:
                response_content += f"\n\nBased on the current page content: *{document_context[:100]}...*"
        elif '?' in user_message:
            response_content = f"🤔 **Question Analysis**: {self.demo_responses['question']}"
            if current_page:
                response_content += f"\n\nI'm focusing on page {current_page} for this analysis."
        elif any(word in message_lower for word in ['explain', 'what', 'how', 'why']):
            response_content = f"💡 **Explanation**: {self.demo_responses['clarification']}"
        else:
            response_content = self.demo_responses['default']
        
        # Add contextual information if available
        if document_context:
            response_content += f"\n\n📖 *Context from current page*: {document_context[:150]}..."
        
        response_content += "\n\n🔧 *Note: This is a demo response. With OpenAI API configured, you'll get intelligent, context-aware responses.*"
        
        return ChatMessage(
            id=str(uuid.uuid4())[:8],
            role='assistant',
            content=response_content,
            timestamp=datetime.now().isoformat(),
            confidence=0.6,  # Lower confidence for demo responses
            source_page=current_page,
            context_used=document_context[:100] + "..." if document_context else None,
            metadata={
                'type': 'demo_response',
                'triggered_by': self._classify_message_type(user_message)
            }
        )
    
    def _classify_message_type(self, message: str) -> str:
        """Classify user message type for demo responses"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return 'greeting'
        elif any(word in message_lower for word in ['summary', 'summarize']):
            return 'summary_request'
        elif '?' in message:
            return 'question'
        elif any(word in message_lower for word in ['explain', 'what', 'how']):
            return 'explanation_request'
        else:
            return 'general_query'
    
    def get_chat_history(self) -> List[ChatMessage]:
        """Get current chat history"""
        if self.current_session:
            # Filter out system messages for display
            return [msg for msg in self.current_session.messages if msg.role != 'system']
        return []
    
    def clear_chat_history(self):
        """Clear current chat history"""
        if self.current_session:
            # Keep system message, clear the rest
            system_messages = [msg for msg in self.current_session.messages if msg.role == 'system']
            self.current_session.messages = system_messages
            self.current_session.total_messages = len(system_messages)
            logger.info("Chat history cleared")
    
    def get_suggested_questions(self, document_context: str = "") -> List[str]:
        """Get suggested questions based on document content"""
        
        # Basic suggested questions
        suggestions = [
            "What is the main topic of this document?",
            "Can you summarize this page?",
            "What are the key points mentioned here?",
            "Are there any important dates or numbers?",
            "What's the conclusion or main finding?"
        ]
        
        # Context-aware suggestions if document content is available
        if document_context:
            context_lower = document_context.lower()
            
            if any(word in context_lower for word in ['analysis', 'study', 'research']):
                suggestions.extend([
                    "What methodology was used in this analysis?",
                    "What are the main findings?",
                    "What are the limitations of this study?"
                ])
            
            if any(word in context_lower for word in ['company', 'business', 'market']):
                suggestions.extend([
                    "What are the business implications?",
                    "What market trends are discussed?",
                    "What are the financial highlights?"
                ])
            
            if any(word in context_lower for word in ['process', 'procedure', 'method']):
                suggestions.extend([
                    "Can you explain the process described here?",
                    "What are the steps involved?",
                    "What are the requirements?"
                ])
        
        return suggestions[:6]  # Return top 6 suggestions
    
    def export_chat_session(self) -> Dict[str, Any]:
        """Export current chat session"""
        if not self.current_session:
            return {}
        
        return {
            'session_info': {
                'session_id': self.current_session.session_id,
                'document_id': self.current_session.document_id,
                'document_title': self.current_session.document_title,
                'created_at': self.current_session.created_at,
                'last_activity': self.current_session.last_activity,
                'total_messages': self.current_session.total_messages
            },
            'messages': [asdict(msg) for msg in self.current_session.messages if msg.role != 'system'],
            'export_timestamp': datetime.now().isoformat()
        }
    
    def get_chat_analytics(self) -> Dict[str, Any]:
        """Get chat session analytics"""
        if not self.current_session:
            return {}
        
        messages = self.current_session.messages
        user_messages = [msg for msg in messages if msg.role == 'user']
        ai_messages = [msg for msg in messages if msg.role == 'assistant']
        
        return {
            'session_duration': self._calculate_session_duration(),
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'ai_messages': len(ai_messages),
            'avg_confidence': sum(msg.confidence for msg in ai_messages) / max(len(ai_messages), 1),
            'pages_discussed': len(set(msg.source_page for msg in messages if msg.source_page)),
            'openai_available': self.openai_available
        }
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration"""
        if not self.current_session:
            return "0 minutes"
        
        try:
            start_time = datetime.fromisoformat(self.current_session.created_at)
            end_time = datetime.fromisoformat(self.current_session.last_activity)
            duration = end_time - start_time
            
            total_minutes = int(duration.total_seconds() / 60)
            if total_minutes < 1:
                return "< 1 minute"
            elif total_minutes < 60:
                return f"{total_minutes} minutes"
            else:
                hours = total_minutes // 60
                minutes = total_minutes % 60
                return f"{hours}h {minutes}m"
                
        except Exception:
            return "Unknown"

# Global instance
ai_chat = AIChatInterface()

def get_ai_chat_interface() -> AIChatInterface:
    """Get the global AI chat interface instance"""
    return ai_chat