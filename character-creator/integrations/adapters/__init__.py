"""
Integration Adapters
===================

Concrete implementations of integration interfaces that wrap existing modules.
"""

from .document_adapter import UniversalDocumentAdapter, EnhancedDocumentAdapter
from .nlp_adapter import IntelligentProcessorAdapter
from .llm_adapter import GPTDialogueAdapter
from .export_adapter import ExportAdapter
from .analytics_adapter import AnalyticsAdapter

__all__ = [
    'UniversalDocumentAdapter',
    'EnhancedDocumentAdapter',
    'IntelligentProcessorAdapter',
    'GPTDialogueAdapter',
    'ExportAdapter',
    'AnalyticsAdapter'
]