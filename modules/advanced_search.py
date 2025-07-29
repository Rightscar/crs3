"""
Advanced Search and Filtering
=============================

Provides advanced search capabilities with full-text search, faceted filtering,
real-time results, and search analytics.
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import json
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import search libraries
try:
    from whoosh import index, fields, qparser, scoring
    from whoosh.filedb.filestore import RamStorage
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False
    logger.info("Whoosh not available - using basic search")

class SearchField(Enum):
    """Available search fields"""
    CONTENT = "content"
    TITLE = "title"
    AUTHOR = "author"
    TAGS = "tags"
    CATEGORY = "category"
    DATE = "date"
    METADATA = "metadata"
    ALL = "all"

@dataclass
class SearchFilter:
    """Search filter definition"""
    field: str
    operator: str  # 'equals', 'contains', 'range', 'in'
    value: Any
    label: Optional[str] = None

@dataclass
class SearchResult:
    """Individual search result"""
    id: str
    title: str
    content: str
    score: float
    highlights: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    facets: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SearchQuery:
    """Search query with filters and options"""
    query_text: str
    filters: List[SearchFilter] = field(default_factory=list)
    fields: List[SearchField] = field(default_factory=list)
    page: int = 1
    page_size: int = 10
    sort_by: str = "relevance"
    sort_order: str = "desc"
    highlight: bool = True
    facets: List[str] = field(default_factory=list)

class AdvancedSearchUI:
    """Advanced search and filtering user interface"""
    
    def __init__(self):
        self.search_engine = SearchEngine()
        self.search_history = []
        self.saved_searches = {}
        self.current_results = []
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize search-related session state"""
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'search_filters' not in st.session_state:
            st.session_state.search_filters = []
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'search_page' not in st.session_state:
            st.session_state.search_page = 1
        if 'search_facets' not in st.session_state:
            st.session_state.search_facets = {}
    
    def render_search_interface(self):
        """Render the complete search interface"""
        st.markdown("## 🔍 Advanced Search")
        
        # Search tabs
        tab1, tab2, tab3 = st.tabs(["Search", "Filters", "Saved Searches"])
        
        with tab1:
            self._render_search_box()
            self._render_quick_filters()
            
        with tab2:
            self._render_advanced_filters()
            
        with tab3:
            self._render_saved_searches()
        
        # Results section
        if st.session_state.search_results:
            self._render_search_results()
        else:
            self._render_search_suggestions()
    
    def _render_search_box(self):
        """Render the main search input box"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Search input with autocomplete
            search_query = st.text_input(
                "Search",
                value=st.session_state.search_query,
                placeholder="Search documents, Q&A, dialogues...",
                key="search_input",
                label_visibility="collapsed"
            )
            
            # Real-time search as user types
            if search_query != st.session_state.search_query:
                st.session_state.search_query = search_query
                if len(search_query) >= 3:  # Minimum 3 characters
                    self._perform_search()
        
        with col2:
            # Search button
            if st.button("🔍 Search", type="primary", use_container_width=True):
                self._perform_search()
        
        # Search options
        with st.expander("Search Options", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.multiselect(
                    "Search in fields",
                    options=[field.value for field in SearchField],
                    default=["content", "title"],
                    key="search_fields"
                )
            
            with col2:
                st.selectbox(
                    "Sort by",
                    options=["relevance", "date", "title", "author"],
                    key="sort_by"
                )
            
            with col3:
                st.number_input(
                    "Results per page",
                    min_value=5,
                    max_value=50,
                    value=10,
                    step=5,
                    key="page_size"
                )
    
    def _render_quick_filters(self):
        """Render quick filter buttons"""
        st.markdown("### Quick Filters")
        
        # Get facets from search results
        facets = st.session_state.get('search_facets', {})
        
        if facets:
            # Document type filters
            if 'doc_type' in facets:
                st.markdown("**Document Type**")
                cols = st.columns(len(facets['doc_type']))
                for i, (doc_type, count) in enumerate(facets['doc_type'].items()):
                    with cols[i]:
                        if st.button(f"{doc_type} ({count})", key=f"filter_type_{doc_type}"):
                            self._add_filter('doc_type', 'equals', doc_type)
            
            # Date range filters
            st.markdown("**Date Range**")
            date_cols = st.columns(4)
            date_ranges = [
                ("Today", 0),
                ("Last 7 days", 7),
                ("Last 30 days", 30),
                ("All time", None)
            ]
            
            for i, (label, days) in enumerate(date_ranges):
                with date_cols[i]:
                    if st.button(label, key=f"filter_date_{label}"):
                        if days is not None:
                            start_date = datetime.now() - timedelta(days=days)
                            self._add_filter('date', 'range', (start_date, datetime.now()))
                        else:
                            self._remove_filter('date')
    
    def _render_advanced_filters(self):
        """Render advanced filtering options"""
        st.markdown("### Advanced Filters")
        
        # Active filters
        if st.session_state.search_filters:
            st.markdown("**Active Filters**")
            for i, filter_obj in enumerate(st.session_state.search_filters):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{filter_obj.label or filter_obj.field}: {filter_obj.value}")
                with col2:
                    if st.button("❌", key=f"remove_filter_{i}"):
                        st.session_state.search_filters.pop(i)
                        self._perform_search()
        
        # Add new filter
        st.markdown("**Add Filter**")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            field = st.selectbox(
                "Field",
                options=["content", "title", "author", "tags", "category", "date"],
                key="filter_field"
            )
        
        with col2:
            operator = st.selectbox(
                "Operator",
                options=["contains", "equals", "starts with", "ends with", "range"],
                key="filter_operator"
            )
        
        with col3:
            if operator == "range" and field == "date":
                date_range = st.date_input(
                    "Date range",
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    key="filter_date_range"
                )
                filter_value = date_range
            else:
                filter_value = st.text_input("Value", key="filter_value")
        
        with col4:
            if st.button("Add", key="add_filter"):
                if filter_value:
                    self._add_filter(field, operator, filter_value)
    
    def _render_search_results(self):
        """Render search results with pagination"""
        results = st.session_state.search_results
        total_results = len(results)
        page = st.session_state.search_page
        page_size = st.session_state.get('page_size', 10)
        
        # Results summary
        st.markdown(f"### 📊 Results ({total_results} found)")
        
        # Results grid
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_results)
        
        for i, result in enumerate(results[start_idx:end_idx]):
            self._render_result_card(result, start_idx + i)
        
        # Pagination
        if total_results > page_size:
            self._render_pagination(total_results, page, page_size)
    
    def _render_result_card(self, result: SearchResult, index: int):
        """Render individual search result card"""
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Title with relevance score
                st.markdown(f"### {result.title}")
                st.caption(f"Relevance: {result.score:.2f}")
                
                # Highlighted content
                if result.highlights and 'content' in result.highlights:
                    for highlight in result.highlights['content'][:2]:
                        st.markdown(f"...{highlight}...")
                else:
                    # Show snippet
                    content_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                    st.write(content_preview)
                
                # Metadata
                metadata_cols = st.columns(4)
                if 'author' in result.metadata:
                    metadata_cols[0].caption(f"👤 {result.metadata['author']}")
                if 'date' in result.metadata:
                    metadata_cols[1].caption(f"📅 {result.metadata['date']}")
                if 'category' in result.metadata:
                    metadata_cols[2].caption(f"📁 {result.metadata['category']}")
                if 'tags' in result.metadata:
                    metadata_cols[3].caption(f"🏷️ {', '.join(result.metadata['tags'])}")
            
            with col2:
                # Actions
                if st.button("View", key=f"view_{result.id}"):
                    self._view_document(result.id)
                
                if st.button("📌", key=f"pin_{result.id}"):
                    self._pin_result(result)
        
        st.divider()
    
    def _render_pagination(self, total: int, current_page: int, page_size: int):
        """Render pagination controls"""
        total_pages = (total + page_size - 1) // page_size
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=current_page == 1):
                st.session_state.search_page = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", disabled=current_page == 1):
                st.session_state.search_page = current_page - 1
                st.rerun()
        
        with col3:
            st.write(f"Page {current_page} of {total_pages}")
        
        with col4:
            if st.button("Next ▶️", disabled=current_page == total_pages):
                st.session_state.search_page = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", disabled=current_page == total_pages):
                st.session_state.search_page = total_pages
                st.rerun()
    
    def _render_search_suggestions(self):
        """Render search suggestions when no results"""
        st.markdown("### 💡 Search Suggestions")
        
        # Popular searches
        st.markdown("**Popular Searches**")
        popular_searches = self._get_popular_searches()
        
        cols = st.columns(3)
        for i, search in enumerate(popular_searches):
            with cols[i % 3]:
                if st.button(search, key=f"suggest_{search}"):
                    st.session_state.search_query = search
                    self._perform_search()
        
        # Recent searches
        if self.search_history:
            st.markdown("**Recent Searches**")
            for search in self.search_history[-5:]:
                if st.button(f"🕐 {search}", key=f"recent_{search}"):
                    st.session_state.search_query = search
                    self._perform_search()
    
    def _render_saved_searches(self):
        """Render saved searches management"""
        st.markdown("### 💾 Saved Searches")
        
        # Save current search
        if st.session_state.search_query:
            col1, col2 = st.columns([3, 1])
            with col1:
                search_name = st.text_input(
                    "Save current search as",
                    placeholder="Enter a name for this search",
                    key="save_search_name"
                )
            with col2:
                if st.button("Save", key="save_search_btn"):
                    if search_name:
                        self._save_search(search_name)
        
        # List saved searches
        if self.saved_searches:
            st.markdown("**Your Saved Searches**")
            for name, search_data in self.saved_searches.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Query: {search_data['query']}")
                    if search_data.get('filters'):
                        st.caption(f"Filters: {len(search_data['filters'])}")
                
                with col2:
                    if st.button("Load", key=f"load_{name}"):
                        self._load_saved_search(search_data)
                
                with col3:
                    if st.button("Delete", key=f"delete_{name}"):
                        del self.saved_searches[name]
                        st.rerun()
    
    def _perform_search(self):
        """Execute search with current query and filters"""
        query = SearchQuery(
            query_text=st.session_state.search_query,
            filters=st.session_state.search_filters,
            fields=[SearchField(f) for f in st.session_state.get('search_fields', ['content', 'title'])],
            page=st.session_state.search_page,
            page_size=st.session_state.get('page_size', 10),
            sort_by=st.session_state.get('sort_by', 'relevance'),
            facets=['doc_type', 'category', 'author']
        )
        
        # Execute search
        results, facets = self.search_engine.search(query)
        
        # Update session state
        st.session_state.search_results = results
        st.session_state.search_facets = facets
        
        # Add to history
        if st.session_state.search_query not in self.search_history:
            self.search_history.append(st.session_state.search_query)
    
    def _add_filter(self, field: str, operator: str, value: Any):
        """Add a new filter"""
        filter_obj = SearchFilter(
            field=field,
            operator=operator,
            value=value,
            label=field.title()
        )
        
        # Remove existing filter for same field
        st.session_state.search_filters = [
            f for f in st.session_state.search_filters 
            if f.field != field
        ]
        
        st.session_state.search_filters.append(filter_obj)
        self._perform_search()
    
    def _remove_filter(self, field: str):
        """Remove filter for a field"""
        st.session_state.search_filters = [
            f for f in st.session_state.search_filters 
            if f.field != field
        ]
        self._perform_search()
    
    def _view_document(self, doc_id: str):
        """Navigate to document view"""
        st.session_state.current_document_id = doc_id
        st.session_state.page = "document_viewer"
        st.rerun()
    
    def _pin_result(self, result: SearchResult):
        """Pin a search result"""
        if 'pinned_results' not in st.session_state:
            st.session_state.pinned_results = []
        
        if result.id not in [r.id for r in st.session_state.pinned_results]:
            st.session_state.pinned_results.append(result)
            st.success("Result pinned!")
    
    def _save_search(self, name: str):
        """Save current search configuration"""
        self.saved_searches[name] = {
            'query': st.session_state.search_query,
            'filters': st.session_state.search_filters,
            'fields': st.session_state.get('search_fields', ['content', 'title']),
            'sort_by': st.session_state.get('sort_by', 'relevance'),
            'saved_at': datetime.now().isoformat()
        }
        st.success(f"Search '{name}' saved!")
    
    def _load_saved_search(self, search_data: Dict[str, Any]):
        """Load a saved search"""
        st.session_state.search_query = search_data['query']
        st.session_state.search_filters = search_data.get('filters', [])
        st.session_state.search_fields = search_data.get('fields', ['content', 'title'])
        st.session_state.sort_by = search_data.get('sort_by', 'relevance')
        self._perform_search()
    
    def _get_popular_searches(self) -> List[str]:
        """Get popular search terms"""
        # In production, this would come from analytics
        return [
            "Python tutorial",
            "Machine learning",
            "Data analysis",
            "Best practices",
            "API documentation",
            "Error handling"
        ]

class SearchEngine:
    """Search engine implementation"""
    
    def __init__(self):
        self.index = self._create_index()
        self.documents = {}
        
    def _create_index(self):
        """Create search index"""
        if WHOOSH_AVAILABLE:
            # Create schema
            schema = fields.Schema(
                id=fields.ID(stored=True),
                title=fields.TEXT(stored=True),
                content=fields.TEXT(stored=True),
                author=fields.TEXT(stored=True),
                tags=fields.KEYWORD(stored=True, commas=True),
                category=fields.TEXT(stored=True),
                date=fields.DATETIME(stored=True),
                metadata=fields.TEXT(stored=True)
            )
            
            # Create in-memory index
            storage = RamStorage()
            return storage.create_index(schema)
        else:
            # Fallback to simple dict-based index
            return {}
    
    def add_document(self, doc_id: str, title: str, content: str, **metadata):
        """Add document to search index"""
        self.documents[doc_id] = {
            'id': doc_id,
            'title': title,
            'content': content,
            **metadata
        }
        
        if WHOOSH_AVAILABLE:
            writer = self.index.writer()
            writer.add_document(
                id=doc_id,
                title=title,
                content=content,
                **metadata
            )
            writer.commit()
    
    def search(self, query: SearchQuery) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Execute search query"""
        if WHOOSH_AVAILABLE:
            return self._whoosh_search(query)
        else:
            return self._simple_search(query)
    
    def _whoosh_search(self, query: SearchQuery) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Search using Whoosh"""
        with self.index.searcher(weighting=scoring.BM25F) as searcher:
            # Build query
            parser = qparser.MultifieldParser(
                [f.value for f in query.fields],
                self.index.schema
            )
            whoosh_query = parser.parse(query.query_text)
            
            # Apply filters
            filter_query = None
            for filter_obj in query.filters:
                # Build filter queries
                pass
            
            # Execute search
            results = searcher.search_page(
                whoosh_query,
                query.page,
                pagelen=query.page_size,
                filter=filter_query
            )
            
            # Convert to SearchResult objects
            search_results = []
            for hit in results:
                search_results.append(SearchResult(
                    id=hit['id'],
                    title=hit['title'],
                    content=hit['content'],
                    score=hit.score,
                    highlights={'content': [hit.highlights('content')]},
                    metadata={
                        'author': hit.get('author'),
                        'date': hit.get('date'),
                        'category': hit.get('category'),
                        'tags': hit.get('tags', '').split(',')
                    }
                ))
            
            # Get facets
            facets = self._calculate_facets(results)
            
            return search_results, facets
    
    def _simple_search(self, query: SearchQuery) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Simple search implementation"""
        results = []
        query_lower = query.query_text.lower()
        
        for doc_id, doc in self.documents.items():
            # Simple text matching
            score = 0
            if query_lower in doc.get('title', '').lower():
                score += 2
            if query_lower in doc.get('content', '').lower():
                score += 1
            
            if score > 0:
                results.append(SearchResult(
                    id=doc_id,
                    title=doc.get('title', ''),
                    content=doc.get('content', ''),
                    score=score,
                    metadata={
                        k: v for k, v in doc.items() 
                        if k not in ['id', 'title', 'content']
                    }
                ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Simple faceting
        facets = self._calculate_simple_facets(results)
        
        # Pagination
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        
        return results[start:end], facets
    
    def _calculate_facets(self, results) -> Dict[str, Any]:
        """Calculate facets from search results"""
        facets = defaultdict(Counter)
        
        for result in results:
            if hasattr(result, 'fields'):
                for field in ['category', 'author', 'doc_type']:
                    if field in result.fields():
                        facets[field][result[field]] += 1
        
        return dict(facets)
    
    def _calculate_simple_facets(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Calculate facets for simple search"""
        facets = defaultdict(Counter)
        
        for result in results:
            metadata = result.metadata
            if 'category' in metadata:
                facets['category'][metadata['category']] += 1
            if 'author' in metadata:
                facets['author'][metadata['author']] += 1
            if 'doc_type' in metadata:
                facets['doc_type'][metadata['doc_type']] += 1
        
        return dict(facets)

# Global search UI instance
advanced_search = AdvancedSearchUI()