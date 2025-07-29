"""
CDN Manager
===========

Manages static asset delivery through CDN with fallback to local assets.
Supports multiple CDN providers and automatic optimization.
"""

import os
import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import mimetypes
import base64
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

@dataclass
class CDNAsset:
    """Represents a static asset managed by CDN"""
    local_path: str
    cdn_url: Optional[str]
    hash: str
    size: int
    mime_type: str
    last_modified: datetime
    cache_control: str = "public, max-age=31536000"
    is_critical: bool = False

@dataclass
class CDNConfig:
    """CDN configuration"""
    provider: str  # 'cloudflare', 'fastly', 'cloudfront', 'local'
    base_url: str
    api_key: Optional[str] = None
    zone_id: Optional[str] = None
    enable_compression: bool = True
    enable_minification: bool = True
    enable_image_optimization: bool = True
    fallback_to_local: bool = True

class CDNManager:
    """Manages CDN integration for static assets"""
    
    # CDN providers configuration
    CDN_PROVIDERS = {
        'cloudflare': {
            'base_url': 'https://cdn.cloudflare.com/',
            'api_endpoint': 'https://api.cloudflare.com/client/v4/',
            'features': ['compression', 'minification', 'image_optimization', 'http2']
        },
        'fastly': {
            'base_url': 'https://cdn.fastly.com/',
            'api_endpoint': 'https://api.fastly.com/',
            'features': ['compression', 'edge_computing', 'real_time_analytics']
        },
        'cloudfront': {
            'base_url': 'https://cdn.amazonaws.com/',
            'api_endpoint': 'https://cloudfront.amazonaws.com/',
            'features': ['compression', 'lambda_edge', 'signed_urls']
        },
        'jsdelivr': {
            'base_url': 'https://cdn.jsdelivr.net/',
            'api_endpoint': None,  # No API needed for public CDN
            'features': ['npm_integration', 'github_integration', 'auto_minification']
        }
    }
    
    def __init__(self, config: Optional[CDNConfig] = None):
        self.config = config or self._get_default_config()
        self.asset_manifest = {}
        self.asset_cache = {}
        self._load_asset_manifest()
        
    def _get_default_config(self) -> CDNConfig:
        """Get default CDN configuration"""
        # Check environment for CDN configuration
        cdn_provider = os.environ.get('CDN_PROVIDER', 'local')
        
        if cdn_provider == 'cloudflare':
            return CDNConfig(
                provider='cloudflare',
                base_url=os.environ.get('CDN_BASE_URL', 'https://cdn.example.com/'),
                api_key=os.environ.get('CLOUDFLARE_API_KEY'),
                zone_id=os.environ.get('CLOUDFLARE_ZONE_ID')
            )
        elif cdn_provider == 'jsdelivr':
            # Use jsDelivr for free CDN of public assets
            return CDNConfig(
                provider='jsdelivr',
                base_url='https://cdn.jsdelivr.net/gh/user/repo@main/'
            )
        else:
            # Local fallback
            return CDNConfig(
                provider='local',
                base_url='/static/'
            )
    
    def get_asset_url(self, asset_path: str, version: bool = True) -> str:
        """Get CDN URL for an asset with fallback to local"""
        try:
            # Normalize path
            asset_path = asset_path.strip('/')
            
            # Check if asset is in manifest
            if asset_path in self.asset_manifest:
                asset = self.asset_manifest[asset_path]
                
                # Return CDN URL if available
                if asset.cdn_url and self.config.provider != 'local':
                    return asset.cdn_url
                
                # Build versioned local URL
                if version:
                    return f"{self.config.base_url}{asset_path}?v={asset.hash[:8]}"
                else:
                    return f"{self.config.base_url}{asset_path}"
            
            # Asset not in manifest, return local URL
            return f"{self.config.base_url}{asset_path}"
            
        except Exception as e:
            logger.error(f"Error getting CDN URL for {asset_path}: {e}")
            # Fallback to local
            return f"/static/{asset_path}"
    
    def optimize_asset(self, file_path: str) -> Tuple[bytes, str]:
        """Optimize an asset based on its type"""
        mime_type, _ = mimetypes.guess_type(file_path)
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # CSS optimization
        if mime_type == 'text/css' and self.config.enable_minification:
            content = self._minify_css(content)
        
        # JavaScript optimization
        elif mime_type in ['application/javascript', 'text/javascript'] and self.config.enable_minification:
            content = self._minify_js(content)
        
        # Image optimization
        elif mime_type and mime_type.startswith('image/') and self.config.enable_image_optimization:
            content = self._optimize_image(content, mime_type)
        
        # Compression
        if self.config.enable_compression and mime_type and mime_type.startswith('text/'):
            content = self._compress_content(content)
        
        return content, mime_type or 'application/octet-stream'
    
    def upload_to_cdn(self, local_path: str, remote_path: Optional[str] = None) -> Optional[str]:
        """Upload an asset to CDN"""
        if self.config.provider == 'local':
            return None
        
        try:
            # Optimize asset
            content, mime_type = self.optimize_asset(local_path)
            
            # Calculate hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Determine remote path
            if not remote_path:
                remote_path = os.path.basename(local_path)
            
            # Provider-specific upload
            if self.config.provider == 'cloudflare':
                cdn_url = self._upload_to_cloudflare(content, remote_path, mime_type)
            elif self.config.provider == 'fastly':
                cdn_url = self._upload_to_fastly(content, remote_path, mime_type)
            elif self.config.provider == 'cloudfront':
                cdn_url = self._upload_to_cloudfront(content, remote_path, mime_type)
            else:
                logger.warning(f"Unsupported CDN provider: {self.config.provider}")
                return None
            
            # Update manifest
            if cdn_url:
                self.asset_manifest[remote_path] = CDNAsset(
                    local_path=local_path,
                    cdn_url=cdn_url,
                    hash=file_hash,
                    size=len(content),
                    mime_type=mime_type,
                    last_modified=datetime.now()
                )
                self._save_asset_manifest()
            
            return cdn_url
            
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to CDN: {e}")
            return None
    
    def preload_critical_assets(self) -> List[str]:
        """Get list of critical assets for preloading"""
        critical_assets = []
        
        for path, asset in self.asset_manifest.items():
            if asset.is_critical:
                url = self.get_asset_url(path)
                critical_assets.append({
                    'url': url,
                    'type': self._get_preload_type(asset.mime_type),
                    'crossorigin': 'anonymous' if 'font' in asset.mime_type else None
                })
        
        return critical_assets
    
    def generate_resource_hints(self) -> str:
        """Generate HTML resource hints for performance"""
        hints = []
        
        # DNS prefetch for CDN domain
        if self.config.provider != 'local':
            cdn_domain = urlparse(self.config.base_url).netloc
            hints.append(f'<link rel="dns-prefetch" href="//{cdn_domain}">')
            hints.append(f'<link rel="preconnect" href="//{cdn_domain}" crossorigin>')
        
        # Preload critical assets
        for asset in self.preload_critical_assets():
            if asset['crossorigin']:
                hints.append(
                    f'<link rel="preload" href="{asset["url"]}" '
                    f'as="{asset["type"]}" crossorigin="{asset["crossorigin"]}">'
                )
            else:
                hints.append(
                    f'<link rel="preload" href="{asset["url"]}" as="{asset["type"]}">'
                )
        
        return '\n'.join(hints)
    
    def get_integrity_hash(self, asset_path: str) -> Optional[str]:
        """Get SRI (Subresource Integrity) hash for an asset"""
        if asset_path in self.asset_manifest:
            asset = self.asset_manifest[asset_path]
            return f"sha256-{base64.b64encode(bytes.fromhex(asset.hash)).decode()}"
        return None
    
    def purge_cache(self, paths: Optional[List[str]] = None) -> bool:
        """Purge CDN cache for specific paths or all"""
        if self.config.provider == 'local':
            return True
        
        try:
            if self.config.provider == 'cloudflare':
                return self._purge_cloudflare_cache(paths)
            elif self.config.provider == 'fastly':
                return self._purge_fastly_cache(paths)
            elif self.config.provider == 'cloudfront':
                return self._purge_cloudfront_cache(paths)
            else:
                logger.warning(f"Cache purge not supported for {self.config.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to purge cache: {e}")
            return False
    
    def _minify_css(self, content: bytes) -> bytes:
        """Minify CSS content"""
        # Simple CSS minification (production would use a proper minifier)
        css_text = content.decode('utf-8', errors='ignore')
        
        # Remove comments
        import re
        css_text = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', css_text)
        
        # Remove unnecessary whitespace
        css_text = re.sub(r'\s+', ' ', css_text)
        css_text = re.sub(r'\s*([{}:;,])\s*', r'\1', css_text)
        
        return css_text.encode('utf-8')
    
    def _minify_js(self, content: bytes) -> bytes:
        """Minify JavaScript content"""
        # Simple JS minification (production would use a proper minifier)
        js_text = content.decode('utf-8', errors='ignore')
        
        # Remove single-line comments (careful with URLs)
        import re
        js_text = re.sub(r'(?<!:)//.*$', '', js_text, flags=re.MULTILINE)
        
        # Remove multi-line comments
        js_text = re.sub(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/', '', js_text)
        
        # Remove unnecessary whitespace
        js_text = re.sub(r'\s+', ' ', js_text)
        js_text = re.sub(r'\s*([{}:;,=\(\)])\s*', r'\1', js_text)
        
        return js_text.encode('utf-8')
    
    def _optimize_image(self, content: bytes, mime_type: str) -> bytes:
        """Optimize image content"""
        # In production, would use PIL/Pillow for actual optimization
        # For now, just return original content
        return content
    
    def _compress_content(self, content: bytes) -> bytes:
        """Compress content using gzip"""
        import gzip
        return gzip.compress(content, compresslevel=9)
    
    def _get_preload_type(self, mime_type: str) -> str:
        """Get preload type from MIME type"""
        if mime_type.startswith('text/css'):
            return 'style'
        elif mime_type.startswith('application/javascript'):
            return 'script'
        elif mime_type.startswith('font/'):
            return 'font'
        elif mime_type.startswith('image/'):
            return 'image'
        else:
            return 'fetch'
    
    def _load_asset_manifest(self):
        """Load asset manifest from file"""
        manifest_path = Path('static/.cdn-manifest.json')
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    data = json.load(f)
                    for path, info in data.items():
                        self.asset_manifest[path] = CDNAsset(**info)
            except Exception as e:
                logger.error(f"Failed to load asset manifest: {e}")
    
    def _save_asset_manifest(self):
        """Save asset manifest to file"""
        manifest_path = Path('static/.cdn-manifest.json')
        manifest_path.parent.mkdir(exist_ok=True)
        
        try:
            data = {}
            for path, asset in self.asset_manifest.items():
                data[path] = {
                    'local_path': asset.local_path,
                    'cdn_url': asset.cdn_url,
                    'hash': asset.hash,
                    'size': asset.size,
                    'mime_type': asset.mime_type,
                    'last_modified': asset.last_modified.isoformat(),
                    'cache_control': asset.cache_control,
                    'is_critical': asset.is_critical
                }
            
            with open(manifest_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save asset manifest: {e}")
    
    # Provider-specific methods (stubs for actual implementation)
    def _upload_to_cloudflare(self, content: bytes, path: str, mime_type: str) -> Optional[str]:
        """Upload to Cloudflare CDN"""
        # Would implement Cloudflare API calls here
        logger.info(f"Would upload {path} to Cloudflare")
        return None
    
    def _upload_to_fastly(self, content: bytes, path: str, mime_type: str) -> Optional[str]:
        """Upload to Fastly CDN"""
        # Would implement Fastly API calls here
        logger.info(f"Would upload {path} to Fastly")
        return None
    
    def _upload_to_cloudfront(self, content: bytes, path: str, mime_type: str) -> Optional[str]:
        """Upload to CloudFront"""
        # Would implement AWS S3/CloudFront upload here
        logger.info(f"Would upload {path} to CloudFront")
        return None
    
    def _purge_cloudflare_cache(self, paths: Optional[List[str]] = None) -> bool:
        """Purge Cloudflare cache"""
        # Would implement Cloudflare purge API here
        return True
    
    def _purge_fastly_cache(self, paths: Optional[List[str]] = None) -> bool:
        """Purge Fastly cache"""
        # Would implement Fastly purge API here
        return True
    
    def _purge_cloudfront_cache(self, paths: Optional[List[str]] = None) -> bool:
        """Create CloudFront invalidation"""
        # Would implement CloudFront invalidation here
        return True

# Global CDN manager instance
cdn_manager = CDNManager()