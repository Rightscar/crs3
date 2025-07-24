"""
Mobile Memory Optimizer
=======================

Optimizes memory usage for mobile devices, especially for large PDFs.
Implements lazy loading and automatic panel management.
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import gc
import psutil
import os

logger = logging.getLogger(__name__)

class MobileOptimizer:
    """Optimize for mobile devices and memory constraints"""
    
    def __init__(self):
        self.device_info = self._detect_device()
        self.is_mobile = self.device_info.get('is_mobile', False)
        self.memory_limit_mb = 100 if self.is_mobile else 500
        self.viewport = self.device_info.get('viewport', {'width': 1200, 'height': 800})
        
        # Apply optimizations on init
        if self.is_mobile:
            self._apply_mobile_optimizations()
    
    def _detect_device(self) -> Dict[str, Any]:
        """Detect device type and capabilities"""
        # Inject device detection JavaScript
        device_detection = """
        <script>
        (function() {
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            const isTablet = /iPad|Android/i.test(navigator.userAgent) && 
                           Math.min(window.innerWidth, window.innerHeight) >= 768;
            const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
            
            const deviceInfo = {
                is_mobile: isMobile,
                is_tablet: isTablet,
                is_safari: isSafari,
                user_agent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                screen: {
                    width: screen.width,
                    height: screen.height,
                    pixel_ratio: window.devicePixelRatio || 1
                },
                memory: navigator.deviceMemory || 4, // GB
                connection: navigator.connection ? {
                    type: navigator.connection.effectiveType,
                    downlink: navigator.connection.downlink,
                    rtt: navigator.connection.rtt
                } : null
            };
            
            // Send to Streamlit
            window.parent.postMessage({
                type: 'device_info',
                data: deviceInfo
            }, '*');
            
            // Store in session
            sessionStorage.setItem('device_info', JSON.stringify(deviceInfo));
            
            console.log('Device info:', deviceInfo);
        })();
        </script>
        """
        
        components.html(device_detection, height=0)
        
        # Get from session state or use defaults
        return st.session_state.get('device_info', {
            'is_mobile': False,
            'is_tablet': False,
            'viewport': {'width': 1200, 'height': 800},
            'memory': 4
        })
    
    def _apply_mobile_optimizations(self):
        """Apply mobile-specific optimizations"""
        logger.info("Applying mobile optimizations")
        
        # Auto-collapse panels on mobile
        st.session_state.nav_panel_collapsed = True
        st.session_state.processor_panel_collapsed = True
        
        # Reduce default quality settings
        st.session_state.image_quality = 'medium'
        st.session_state.cache_size = 5  # Smaller cache
        
        # Apply mobile CSS
        mobile_css = """
        <style>
        /* Mobile optimizations */
        @media (max-width: 768px) {
            /* Single column layout */
            .main-container {
                flex-direction: column !important;
            }
            
            /* Full-width panels */
            .nav-panel, .processor-panel {
                width: 100% !important;
                position: fixed !important;
                z-index: 1000 !important;
            }
            
            /* Larger touch targets */
            .stButton > button {
                min-height: 44px !important;
                font-size: 16px !important;
            }
            
            /* Optimize document container */
            .document-container {
                padding: 0.5rem !important;
                margin: 0 !important;
            }
            
            /* Hide non-essential elements */
            .hide-on-mobile {
                display: none !important;
            }
        }
        
        /* iOS Safari fixes */
        @supports (-webkit-touch-callout: none) {
            /* Fix viewport height */
            .main-container {
                height: -webkit-fill-available !important;
            }
            
            /* Prevent zoom on input focus */
            input, select, textarea {
                font-size: 16px !important;
            }
        }
        </style>
        """
        
        st.markdown(mobile_css, unsafe_allow_html=True)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0
            }
    
    def check_memory_pressure(self) -> bool:
        """Check if under memory pressure"""
        memory = self.get_memory_usage()
        
        # Check if using too much memory
        if memory['rss_mb'] > self.memory_limit_mb:
            return True
        
        # Check if system memory is low
        if memory['available_mb'] < 100:
            return True
        
        return False
    
    def optimize_document_loading(self, file_path: str, total_pages: int) -> 'DocumentLoader':
        """Return optimized document loader based on device"""
        memory = self.get_memory_usage()
        
        # Show optimization notice
        if self.is_mobile and total_pages > 50:
            st.info(f"""
            📱 **Mobile Optimization Active**
            
            - Document has {total_pages} pages
            - Using memory-efficient loading
            - Panels auto-collapsed for better viewing
            - Swipe gestures enabled
            """)
        
        # Determine loading strategy
        if self.is_mobile or memory['available_mb'] < 200 or total_pages > 100:
            return LazyDocumentLoader(file_path, cache_size=5, quality='medium')
        else:
            return StandardDocumentLoader(file_path)
    
    def garbage_collect(self):
        """Force garbage collection to free memory"""
        collected = gc.collect()
        logger.info(f"Garbage collected {collected} objects")
        
        # Clear Streamlit caches if needed
        if self.check_memory_pressure():
            st.cache_data.clear()
            logger.warning("Cleared Streamlit cache due to memory pressure")
    
    def render_mobile_navigation(self):
        """Render mobile-optimized navigation"""
        if not self.is_mobile:
            return
        
        # Bottom navigation bar for mobile
        st.markdown("""
        <div class="mobile-nav-bar">
            <button onclick="showPanel('nav')">📚 Nav</button>
            <button onclick="goHome()">🏠 Home</button>
            <button onclick="showPanel('processor')">🧠 AI</button>
            <button onclick="showSearch()">🔍 Search</button>
        </div>
        
        <style>
        .mobile-nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--secondary-bg);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-around;
            align-items: center;
            z-index: 1000;
            padding: 0 1rem;
        }
        
        .mobile-nav-bar button {
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 0.875rem;
            padding: 0.5rem;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.25rem;
        }
        
        .mobile-nav-bar button:active {
            background: var(--accent-primary);
            border-radius: 8px;
        }
        </style>
        
        <script>
        function showPanel(panel) {
            window.parent.postMessage({
                type: 'toggle_panel',
                panel: panel
            }, '*');
        }
        
        function goHome() {
            window.parent.postMessage({
                type: 'navigate',
                view: 'home'
            }, '*');
        }
        
        function showSearch() {
            window.parent.postMessage({
                type: 'show_search'
            }, '*');
        }
        </script>
        """, unsafe_allow_html=True)
    
    def optimize_image(self, image_data: bytes, target_size_kb: int = 100) -> bytes:
        """Optimize image for mobile display"""
        if not self.is_mobile:
            return image_data
        
        try:
            from PIL import Image
            import io
            
            # Load image
            img = Image.open(io.BytesIO(image_data))
            
            # Reduce size for mobile
            max_dimension = 800 if self.is_mobile else 1200
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save with optimization
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=70, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            return image_data


class LazyDocumentLoader:
    """Load document pages on demand to save memory"""
    
    def __init__(self, file_path: str, cache_size: int = 5, quality: str = 'medium'):
        self.file_path = Path(file_path)
        self.cache_size = cache_size
        self.quality = quality
        self.page_cache = {}
        self.access_history = []
        
    def get_page(self, page_num: int) -> Dict[str, Any]:
        """Load a specific page with caching"""
        # Check cache first
        if page_num in self.page_cache:
            self._update_access(page_num)
            return self.page_cache[page_num]
        
        # Evict old pages if cache is full
        if len(self.page_cache) >= self.cache_size:
            self._evict_least_used()
        
        # Load page
        try:
            page_data = self._load_page(page_num)
            self.page_cache[page_num] = page_data
            self._update_access(page_num)
            
            # Garbage collect after loading
            gc.collect()
            
            return page_data
            
        except Exception as e:
            logger.error(f"Failed to load page {page_num}: {e}")
            return {'error': str(e)}
    
    def _load_page(self, page_num: int) -> Dict[str, Any]:
        """Load a single page from document"""
        # This would be implemented based on document type
        # For now, return placeholder
        return {
            'page_num': page_num,
            'content': f'Page {page_num} content',
            'image': None  # Would load actual page image
        }
    
    def _update_access(self, page_num: int):
        """Update access history for LRU"""
        if page_num in self.access_history:
            self.access_history.remove(page_num)
        self.access_history.append(page_num)
    
    def _evict_least_used(self):
        """Evict least recently used page"""
        if self.access_history:
            lru_page = self.access_history[0]
            del self.page_cache[lru_page]
            self.access_history.remove(lru_page)
            logger.debug(f"Evicted page {lru_page} from cache")
    
    def preload_pages(self, start: int, end: int):
        """Preload a range of pages"""
        for page_num in range(start, min(end + 1, start + self.cache_size)):
            if page_num not in self.page_cache:
                self.get_page(page_num)
    
    def clear_cache(self):
        """Clear page cache to free memory"""
        self.page_cache.clear()
        self.access_history.clear()
        gc.collect()
        logger.info("Cleared document cache")


class StandardDocumentLoader:
    """Standard document loader for desktop"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.pages = {}
        
    def get_page(self, page_num: int) -> Dict[str, Any]:
        """Get page (simplified for example)"""
        return {
            'page_num': page_num,
            'content': f'Page {page_num} content'
        }


# Singleton instance
_optimizer_instance = None

def get_mobile_optimizer() -> MobileOptimizer:
    """Get singleton mobile optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = MobileOptimizer()
    return _optimizer_instance


def is_mobile_device() -> bool:
    """Check if running on mobile device"""
    optimizer = get_mobile_optimizer()
    return optimizer.is_mobile


def optimize_for_device(file_path: str, total_pages: int) -> Any:
    """Get optimized document loader for device"""
    optimizer = get_mobile_optimizer()
    return optimizer.optimize_document_loading(file_path, total_pages)


def render_memory_status():
    """Render memory usage status"""
    optimizer = get_mobile_optimizer()
    memory = optimizer.get_memory_usage()
    
    if optimizer.is_mobile:
        st.caption(f"Memory: {memory['rss_mb']:.0f}MB / {optimizer.memory_limit_mb}MB")
        
        if optimizer.check_memory_pressure():
            st.warning("⚠️ Low memory - some features may be limited")
            if st.button("🧹 Free Memory"):
                optimizer.garbage_collect()
                st.rerun()