"""
Fixes for RAG Integration Issues
================================

Implements proper vector search, retrieval, and reranking for RAG.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import hashlib
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pathlib import Path

from config.logging_config import logger
from core.models import KnowledgeChunk, KnowledgeBase


@dataclass
class RetrievalResult:
    """Result from retrieval operation"""
    chunk: KnowledgeChunk
    score: float
    rank: int
    metadata: Dict[str, Any]


class VectorStore:
    """Vector store for similarity search"""
    
    def __init__(self, embedding_dim: int = 1536):
        """Initialize vector store"""
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunk_map = {}  # chunk_id -> chunk
        self.embeddings = []
        self.initialized = False
    
    def build_index(self, chunks: List[KnowledgeChunk]):
        """Build FAISS index from chunks"""
        if not chunks:
            return
        
        # Extract embeddings
        embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if chunk.embedding and len(chunk.embedding) == self.embedding_dim:
                embeddings.append(chunk.embedding)
                valid_chunks.append(chunk)
                self.chunk_map[chunk.id] = chunk
        
        if not embeddings:
            logger.warning("No valid embeddings found")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Build FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        self.embeddings = embeddings_array
        self.initialized = True
        
        logger.info(f"Built index with {len(valid_chunks)} chunks")
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """Search for similar chunks"""
        if not self.initialized or not self.index:
            return []
        
        # Normalize query
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        # Build results
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score >= threshold:
                # Get chunk from map
                chunk_id = list(self.chunk_map.keys())[idx]
                chunk = self.chunk_map[chunk_id]
                
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=float(score),
                    rank=rank,
                    metadata={'index': idx}
                ))
        
        return results
    
    def save(self, path: Path):
        """Save index to disk"""
        if not self.initialized:
            return
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save chunk map
        with open(path / "chunks.pkl", 'wb') as f:
            pickle.dump(self.chunk_map, f)
        
        logger.info(f"Saved index to {path}")
    
    def load(self, path: Path) -> bool:
        """Load index from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(path / "index.faiss"))
            
            # Load chunk map
            with open(path / "chunks.pkl", 'rb') as f:
                self.chunk_map = pickle.load(f)
            
            self.initialized = True
            logger.info(f"Loaded index from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False


class HybridRetriever:
    """Hybrid retrieval combining dense and sparse methods"""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize retriever"""
        self.embedding_model = SentenceTransformer(embedding_model)
        self.vector_store = VectorStore(self.embedding_model.get_sentence_embedding_dimension())
        self.bm25_index = None  # For sparse retrieval
    
    def index_chunks(self, chunks: List[KnowledgeChunk]):
        """Index chunks for retrieval"""
        # Generate embeddings if missing
        for chunk in chunks:
            if not chunk.embedding:
                chunk.embedding = self.embedding_model.encode(chunk.content).tolist()
        
        # Build vector index
        self.vector_store.build_index(chunks)
        
        # Build BM25 index (simplified)
        self._build_bm25_index(chunks)
    
    def _build_bm25_index(self, chunks: List[KnowledgeChunk]):
        """Build BM25 index for sparse retrieval"""
        # Simplified TF-IDF based approach
        from collections import Counter
        import math
        
        self.bm25_docs = []
        self.bm25_idf = {}
        
        # Tokenize documents
        for chunk in chunks:
            tokens = chunk.content.lower().split()
            self.bm25_docs.append({
                'chunk': chunk,
                'tokens': tokens,
                'tf': Counter(tokens)
            })
        
        # Calculate IDF
        doc_count = len(chunks)
        all_tokens = set()
        for doc in self.bm25_docs:
            all_tokens.update(doc['tokens'])
        
        for token in all_tokens:
            doc_freq = sum(1 for doc in self.bm25_docs if token in doc['tf'])
            self.bm25_idf[token] = math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5))
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.5,  # Weight for dense vs sparse
        rerank: bool = True
    ) -> List[RetrievalResult]:
        """Hybrid retrieval with optional reranking"""
        
        # Dense retrieval
        query_embedding = self.embedding_model.encode(query).tolist()
        dense_results = self.vector_store.search(query_embedding, k=k*2)
        
        # Sparse retrieval (BM25)
        sparse_results = self._bm25_search(query, k=k*2)
        
        # Combine results
        combined_results = self._combine_results(
            dense_results, 
            sparse_results, 
            alpha=alpha
        )
        
        # Rerank if requested
        if rerank:
            combined_results = self._rerank_results(query, combined_results)
        
        # Return top k
        return combined_results[:k]
    
    def _bm25_search(self, query: str, k: int) -> List[RetrievalResult]:
        """BM25 search"""
        if not self.bm25_docs:
            return []
        
        query_tokens = query.lower().split()
        scores = []
        
        for doc in self.bm25_docs:
            score = 0.0
            for token in query_tokens:
                if token in doc['tf']:
                    tf = doc['tf'][token]
                    idf = self.bm25_idf.get(token, 0)
                    score += tf * idf
            
            scores.append((doc['chunk'], score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to results
        results = []
        for rank, (chunk, score) in enumerate(scores[:k]):
            results.append(RetrievalResult(
                chunk=chunk,
                score=score,
                rank=rank,
                metadata={'method': 'bm25'}
            ))
        
        return results
    
    def _combine_results(
        self,
        dense_results: List[RetrievalResult],
        sparse_results: List[RetrievalResult],
        alpha: float
    ) -> List[RetrievalResult]:
        """Combine dense and sparse results"""
        # Normalize scores
        max_dense = max([r.score for r in dense_results], default=1.0)
        max_sparse = max([r.score for r in sparse_results], default=1.0)
        
        # Create combined scores
        chunk_scores = {}
        
        for result in dense_results:
            chunk_id = result.chunk.id
            normalized_score = result.score / max_dense if max_dense > 0 else 0
            chunk_scores[chunk_id] = alpha * normalized_score
        
        for result in sparse_results:
            chunk_id = result.chunk.id
            normalized_score = result.score / max_sparse if max_sparse > 0 else 0
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id] += (1 - alpha) * normalized_score
            else:
                chunk_scores[chunk_id] = (1 - alpha) * normalized_score
        
        # Sort by combined score
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build results
        results = []
        chunk_map = {r.chunk.id: r.chunk for r in dense_results + sparse_results}
        
        for rank, (chunk_id, score) in enumerate(sorted_chunks):
            if chunk_id in chunk_map:
                results.append(RetrievalResult(
                    chunk=chunk_map[chunk_id],
                    score=score,
                    rank=rank,
                    metadata={'method': 'hybrid'}
                ))
        
        return results
    
    def _rerank_results(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Rerank results using cross-encoder or other method"""
        # Simple reranking based on query-document similarity
        reranked = []
        
        for result in results:
            # Calculate more precise similarity
            doc_embedding = self.embedding_model.encode(result.chunk.content)
            query_embedding = self.embedding_model.encode(query)
            
            # Cosine similarity
            similarity = np.dot(doc_embedding, query_embedding) / (
                np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
            )
            
            # Adjust score
            result.score = float(similarity)
            reranked.append(result)
        
        # Sort by new scores
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        # Update ranks
        for rank, result in enumerate(reranked):
            result.rank = rank
        
        return reranked


class RAGContextBuilder:
    """Build context for RAG from retrieved chunks"""
    
    def __init__(self, max_context_length: int = 2000):
        """Initialize context builder"""
        self.max_context_length = max_context_length
    
    def build_context(
        self,
        query: str,
        retrieved_chunks: List[RetrievalResult],
        include_metadata: bool = True
    ) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []
        current_length = 0
        
        for result in retrieved_chunks:
            chunk = result.chunk
            
            # Build chunk text
            chunk_text = chunk.content
            
            if include_metadata:
                # Add source info
                if chunk.source_page:
                    chunk_text = f"[Page {chunk.source_page}] {chunk_text}"
                
                # Add relevance score
                chunk_text = f"[Relevance: {result.score:.2f}] {chunk_text}"
            
            # Check if we can add this chunk
            chunk_length = len(chunk_text)
            if current_length + chunk_length > self.max_context_length:
                # Truncate if needed
                remaining = self.max_context_length - current_length
                if remaining > 100:  # Only add if meaningful
                    chunk_text = chunk_text[:remaining] + "..."
                    context_parts.append(chunk_text)
                break
            
            context_parts.append(chunk_text)
            current_length += chunk_length
        
        # Join with separators
        context = "\n\n---\n\n".join(context_parts)
        
        # Add query context
        context = f"Query: {query}\n\nRelevant Context:\n{context}"
        
        return context


# Example usage in character chat
def enhance_character_response_with_rag(
    character: Any,
    user_message: str,
    retriever: HybridRetriever,
    k: int = 3
) -> Tuple[str, List[RetrievalResult]]:
    """Enhance character response with RAG"""
    
    # Retrieve relevant chunks
    results = retriever.retrieve(user_message, k=k)
    
    # Build context
    context_builder = RAGContextBuilder()
    context = context_builder.build_context(user_message, results)
    
    # Generate response with context
    enhanced_prompt = f"""
{context}

Based on the above context, respond as {character.name} would.
User: {user_message}
{character.name}:"""
    
    # Use LLM to generate response
    # response = llm.generate(enhanced_prompt)
    
    return enhanced_prompt, results


# Test RAG implementation
def test_rag_fixes():
    """Test RAG fixes"""
    # Create test chunks
    chunks = [
        KnowledgeChunk(
            content="The character loves adventure and exploring new places.",
            embedding=None,
            metadata={'topic': 'personality'}
        ),
        KnowledgeChunk(
            content="In chapter 3, the character saves a village from bandits.",
            embedding=None,
            metadata={'topic': 'actions'},
            source_page=3
        ),
        KnowledgeChunk(
            content="The character's main weakness is their fear of water.",
            embedding=None,
            metadata={'topic': 'weaknesses'}
        )
    ]
    
    # Initialize retriever
    retriever = HybridRetriever()
    retriever.index_chunks(chunks)
    
    # Test retrieval
    results = retriever.retrieve("What are the character's weaknesses?", k=2)
    
    assert len(results) > 0
    assert results[0].chunk.content.lower().find('weakness') >= 0
    
    print("✅ RAG fixes tested successfully")


if __name__ == "__main__":
    test_rag_fixes()