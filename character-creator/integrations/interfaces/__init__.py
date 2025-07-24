"""
Integration Interfaces
=====================

Abstract base classes defining the contracts for integration adapters.
"""

from .document_interface import DocumentProcessorInterface
from .nlp_interface import NLPProcessorInterface
from .llm_interface import LLMInterface

__all__ = [
    'DocumentProcessorInterface',
    'NLPProcessorInterface', 
    'LLMInterface'
]