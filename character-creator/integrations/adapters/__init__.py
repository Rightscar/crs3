"""
Integration Adapters
===================

Concrete implementations of integration interfaces that wrap existing modules.
"""

from .document_adapter import UniversalDocumentAdapter
from .nlp_adapter import IntelligentProcessorAdapter
from .llm_adapter import GPTDialogueAdapter

__all__ = [
    'UniversalDocumentAdapter',
    'IntelligentProcessorAdapter',
    'GPTDialogueAdapter'
]