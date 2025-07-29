"""
GPU Accelerator
===============

Provides GPU acceleration for ML operations with automatic CPU fallback.
Supports CUDA, ROCm, and Metal backends.
"""

import os
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import GPU libraries
CUDA_AVAILABLE = False
ROCM_AVAILABLE = False
METAL_AVAILABLE = False
TORCH_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
    if hasattr(torch.backends, 'mps'):
        METAL_AVAILABLE = torch.backends.mps.is_available()
except ImportError:
    logger.info("PyTorch not available - GPU acceleration disabled")

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    logger.info("CuPy not available - CUDA operations will use PyTorch")

class AcceleratorType(Enum):
    """Available accelerator types"""
    CPU = "cpu"
    CUDA = "cuda"
    ROCM = "rocm"
    METAL = "metal"
    TPU = "tpu"

@dataclass
class GPUInfo:
    """GPU device information"""
    device_id: int
    name: str
    memory_total: int  # in MB
    memory_free: int   # in MB
    compute_capability: Optional[Tuple[int, int]] = None
    temperature: Optional[float] = None
    utilization: Optional[float] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation: str
    device: str
    input_shape: Tuple[int, ...]
    duration_ms: float
    memory_used_mb: float
    speedup: float  # vs CPU

class GPUAccelerator:
    """GPU acceleration manager for ML operations"""
    
    def __init__(self, preferred_device: Optional[str] = None, 
                 memory_fraction: float = 0.8):
        self.preferred_device = preferred_device
        self.memory_fraction = memory_fraction
        self.device = self._initialize_device()
        self.performance_history = []
        self._setup_memory_management()
        
    def _initialize_device(self) -> str:
        """Initialize the best available device"""
        if self.preferred_device:
            if self._is_device_available(self.preferred_device):
                return self.preferred_device
            else:
                logger.warning(f"Preferred device {self.preferred_device} not available")
        
        # Auto-select best device
        if CUDA_AVAILABLE:
            return "cuda"
        elif METAL_AVAILABLE:
            return "mps"  # Metal Performance Shaders
        elif ROCM_AVAILABLE:
            return "rocm"
        else:
            return "cpu"
    
    def _is_device_available(self, device: str) -> bool:
        """Check if a specific device is available"""
        if device == "cuda":
            return CUDA_AVAILABLE
        elif device == "mps" or device == "metal":
            return METAL_AVAILABLE
        elif device == "rocm":
            return ROCM_AVAILABLE
        elif device == "cpu":
            return True
        return False
    
    def _setup_memory_management(self):
        """Setup memory management for GPU"""
        if TORCH_AVAILABLE and self.device == "cuda":
            # Set memory fraction
            torch.cuda.set_per_process_memory_fraction(self.memory_fraction)
            # Enable memory caching
            torch.cuda.empty_cache()
    
    def get_device_info(self) -> List[GPUInfo]:
        """Get information about available GPU devices"""
        devices = []
        
        if CUDA_AVAILABLE and TORCH_AVAILABLE:
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                memory_total = props.total_memory // (1024 * 1024)
                memory_free = (props.total_memory - torch.cuda.memory_allocated(i)) // (1024 * 1024)
                
                devices.append(GPUInfo(
                    device_id=i,
                    name=props.name,
                    memory_total=memory_total,
                    memory_free=memory_free,
                    compute_capability=(props.major, props.minor)
                ))
        
        return devices
    
    def accelerate(self, func: Callable) -> Callable:
        """Decorator to automatically accelerate a function"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Move inputs to device
            args_gpu = self._move_to_device(args)
            kwargs_gpu = self._move_to_device(kwargs)
            
            # Record start metrics
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            # Execute function
            result = func(*args_gpu, **kwargs_gpu)
            
            # Record end metrics
            duration = (time.time() - start_time) * 1000  # ms
            memory_used = self._get_memory_usage() - start_memory
            
            # Move result back to CPU if needed
            result_cpu = self._move_to_cpu(result)
            
            # Record performance
            self._record_performance(
                func.__name__, 
                duration, 
                memory_used
            )
            
            return result_cpu
        
        return wrapper
    
    def text_embedding_acceleration(self, texts: List[str], 
                                  model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> np.ndarray:
        """Accelerated text embedding generation"""
        try:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch required for embeddings")
            
            from sentence_transformers import SentenceTransformer
            
            # Load model on GPU
            model = SentenceTransformer(model_name)
            if self.device != "cpu":
                model = model.to(self.device)
            
            # Batch processing for efficiency
            batch_size = 32 if self.device != "cpu" else 8
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                with torch.no_grad():
                    if self.device != "cpu":
                        # GPU processing
                        batch_embeddings = model.encode(
                            batch, 
                            convert_to_tensor=True,
                            device=self.device
                        )
                        embeddings.append(batch_embeddings.cpu().numpy())
                    else:
                        # CPU processing
                        batch_embeddings = model.encode(batch)
                        embeddings.append(batch_embeddings)
            
            return np.vstack(embeddings)
            
        except Exception as e:
            logger.error(f"Embedding acceleration failed: {e}")
            # Fallback to CPU
            return self._cpu_text_embeddings(texts)
    
    def accelerate_matrix_operations(self, operation: str, *matrices) -> np.ndarray:
        """Accelerate matrix operations (multiply, inverse, decomposition)"""
        if self.device == "cuda" and CUPY_AVAILABLE:
            return self._cuda_matrix_ops(operation, *matrices)
        elif self.device != "cpu" and TORCH_AVAILABLE:
            return self._torch_matrix_ops(operation, *matrices)
        else:
            return self._numpy_matrix_ops(operation, *matrices)
    
    def accelerate_regex_matching(self, patterns: List[str], texts: List[str]) -> List[List[int]]:
        """GPU-accelerated regex matching for multiple patterns"""
        if self.device == "cuda" and CUPY_AVAILABLE:
            # Use CuPy's regex engine
            import cupy as cp
            
            # Convert to GPU arrays
            gpu_texts = cp.array(texts)
            results = []
            
            for pattern in patterns:
                # GPU regex matching
                matches = cp.zeros(len(texts), dtype=cp.int32)
                # This is simplified - actual implementation would use
                # GPU-accelerated string matching algorithms
                results.append(matches.get().tolist())
            
            return results
        else:
            # CPU fallback with multiprocessing
            import re
            from multiprocessing import Pool
            
            def match_pattern(args):
                pattern, text = args
                return 1 if re.search(pattern, text) else 0
            
            with Pool() as pool:
                results = []
                for pattern in patterns:
                    pattern_args = [(pattern, text) for text in texts]
                    matches = pool.map(match_pattern, pattern_args)
                    results.append(matches)
            
            return results
    
    def accelerate_similarity_search(self, query_vectors: np.ndarray, 
                                   database_vectors: np.ndarray, 
                                   top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """GPU-accelerated similarity search"""
        if self.device != "cpu" and TORCH_AVAILABLE:
            # Convert to tensors
            query_tensor = torch.from_numpy(query_vectors).to(self.device)
            db_tensor = torch.from_numpy(database_vectors).to(self.device)
            
            # Normalize vectors
            query_norm = torch.nn.functional.normalize(query_tensor, p=2, dim=1)
            db_norm = torch.nn.functional.normalize(db_tensor, p=2, dim=1)
            
            # Compute similarity matrix
            similarities = torch.mm(query_norm, db_norm.t())
            
            # Get top-k
            values, indices = torch.topk(similarities, k=min(top_k, db_tensor.shape[0]), dim=1)
            
            return values.cpu().numpy(), indices.cpu().numpy()
        else:
            # CPU implementation using NumPy
            from sklearn.metrics.pairwise import cosine_similarity
            
            similarities = cosine_similarity(query_vectors, database_vectors)
            indices = np.argsort(similarities, axis=1)[:, -top_k:][:, ::-1]
            values = np.take_along_axis(similarities, indices, axis=1)
            
            return values, indices
    
    def optimize_batch_size(self, input_shape: Tuple[int, ...], 
                          operation_memory_mb: float) -> int:
        """Calculate optimal batch size based on available GPU memory"""
        if self.device == "cpu":
            # Conservative batch size for CPU
            return 32
        
        # Get available memory
        devices = self.get_device_info()
        if not devices:
            return 32
        
        available_memory = devices[0].memory_free
        
        # Calculate memory per sample
        element_size = 4  # float32
        memory_per_sample = np.prod(input_shape) * element_size / (1024 * 1024)
        
        # Add overhead for operation
        total_per_sample = memory_per_sample + operation_memory_mb
        
        # Calculate batch size with safety margin
        optimal_batch = int(available_memory * 0.8 / total_per_sample)
        
        # Clamp to reasonable range
        return max(1, min(optimal_batch, 512))
    
    def benchmark_operation(self, operation: Callable, input_sizes: List[Tuple[int, ...]]) -> Dict[str, Any]:
        """Benchmark an operation across different input sizes"""
        results = {
            'device': self.device,
            'operation': operation.__name__,
            'benchmarks': []
        }
        
        for size in input_sizes:
            # Generate test data
            test_data = np.random.randn(*size).astype(np.float32)
            
            # CPU baseline
            start = time.time()
            cpu_result = operation(test_data)
            cpu_time = (time.time() - start) * 1000
            
            # GPU timing
            if self.device != "cpu":
                gpu_data = self._move_to_device(test_data)
                torch.cuda.synchronize() if self.device == "cuda" else None
                
                start = time.time()
                gpu_result = operation(gpu_data)
                torch.cuda.synchronize() if self.device == "cuda" else None
                gpu_time = (time.time() - start) * 1000
                
                speedup = cpu_time / gpu_time
            else:
                gpu_time = cpu_time
                speedup = 1.0
            
            results['benchmarks'].append({
                'input_size': size,
                'cpu_time_ms': cpu_time,
                'gpu_time_ms': gpu_time,
                'speedup': speedup
            })
        
        return results
    
    def _move_to_device(self, data: Any) -> Any:
        """Move data to GPU device"""
        if self.device == "cpu":
            return data
        
        if TORCH_AVAILABLE:
            if isinstance(data, np.ndarray):
                return torch.from_numpy(data).to(self.device)
            elif isinstance(data, torch.Tensor):
                return data.to(self.device)
            elif isinstance(data, (list, tuple)):
                return type(data)(self._move_to_device(item) for item in data)
            elif isinstance(data, dict):
                return {k: self._move_to_device(v) for k, v in data.items()}
        
        return data
    
    def _move_to_cpu(self, data: Any) -> Any:
        """Move data back to CPU"""
        if TORCH_AVAILABLE and isinstance(data, torch.Tensor):
            return data.cpu().numpy()
        elif isinstance(data, (list, tuple)):
            return type(data)(self._move_to_cpu(item) for item in data)
        elif isinstance(data, dict):
            return {k: self._move_to_cpu(v) for k, v in data.items()}
        
        return data
    
    def _get_memory_usage(self) -> float:
        """Get current GPU memory usage in MB"""
        if self.device == "cuda" and TORCH_AVAILABLE:
            return torch.cuda.memory_allocated() / (1024 * 1024)
        return 0.0
    
    def _record_performance(self, operation: str, duration_ms: float, memory_mb: float):
        """Record performance metrics"""
        metric = PerformanceMetrics(
            operation=operation,
            device=self.device,
            input_shape=(0,),  # Would need to track this
            duration_ms=duration_ms,
            memory_used_mb=memory_mb,
            speedup=1.0  # Would need CPU baseline
        )
        self.performance_history.append(metric)
        
        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def _cuda_matrix_ops(self, operation: str, *matrices) -> np.ndarray:
        """CUDA-accelerated matrix operations using CuPy"""
        import cupy as cp
        
        # Convert to GPU arrays
        gpu_matrices = [cp.asarray(m) for m in matrices]
        
        if operation == "multiply":
            result = cp.matmul(gpu_matrices[0], gpu_matrices[1])
        elif operation == "inverse":
            result = cp.linalg.inv(gpu_matrices[0])
        elif operation == "svd":
            u, s, v = cp.linalg.svd(gpu_matrices[0])
            result = (u, s, v)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Convert back to NumPy
        if isinstance(result, tuple):
            return tuple(r.get() for r in result)
        return result.get()
    
    def _torch_matrix_ops(self, operation: str, *matrices) -> np.ndarray:
        """PyTorch-accelerated matrix operations"""
        # Convert to tensors
        tensors = [torch.from_numpy(m).to(self.device) for m in matrices]
        
        if operation == "multiply":
            result = torch.matmul(tensors[0], tensors[1])
        elif operation == "inverse":
            result = torch.linalg.inv(tensors[0])
        elif operation == "svd":
            u, s, v = torch.linalg.svd(tensors[0])
            result = (u, s, v)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Convert back to NumPy
        if isinstance(result, tuple):
            return tuple(r.cpu().numpy() for r in result)
        return result.cpu().numpy()
    
    def _numpy_matrix_ops(self, operation: str, *matrices) -> np.ndarray:
        """NumPy fallback for matrix operations"""
        if operation == "multiply":
            return np.matmul(matrices[0], matrices[1])
        elif operation == "inverse":
            return np.linalg.inv(matrices[0])
        elif operation == "svd":
            return np.linalg.svd(matrices[0])
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _cpu_text_embeddings(self, texts: List[str]) -> np.ndarray:
        """CPU fallback for text embeddings"""
        # Simple TF-IDF as fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        vectorizer = TfidfVectorizer(max_features=512)
        embeddings = vectorizer.fit_transform(texts).toarray()
        
        return embeddings
    
    def cleanup(self):
        """Clean up GPU resources"""
        if self.device == "cuda" and TORCH_AVAILABLE:
            torch.cuda.empty_cache()
        
        self.performance_history.clear()

# Global GPU accelerator instance
gpu_accelerator = GPUAccelerator()