"""
Base reranker class for all reranking methods.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """
    Abstract base class for all reranking methods.
    
    Reranking is applied to a set of candidate documents retrieved by an initial
    retrieval method to improve the ranking quality.
    """
    
    def __init__(self, method_name: str):
        """
        Initialize the base reranker.
        
        Args:
            method_name: Name of the reranking method
        """
        self.method_name = method_name
        logger.info(f"Initialized {method_name} reranker")
    
    @abstractmethod
    def rerank(
        self, 
        query: str, 
        candidate_docs: List[str], 
        doc_texts: Dict[str, str],
        top_k: Optional[int] = None
    ) -> List[str]:
        """
        Rerank candidate documents for a given query.
        
        Args:
            query: Query text
            candidate_docs: List of candidate document IDs
            doc_texts: Dictionary mapping document IDs to document texts
            top_k: Number of top documents to return (None for all)
            
        Returns:
            List of reranked document IDs
        """
        pass
    
    
    def rerank_all(
        self,
        queries: Dict[str, str],
        base_results: Dict[str, List[str]],
        doc_texts: Dict[str, str],
        top_k_candidates: int = 100,
        top_k_output: int = None,
    ) -> Dict[str, List[str]]:
        """Rerank documents for multiple queries."""
        
        for query_id, query in queries.items():
            # Get top candidates from base method
            top_candidates = base_results[query_id][:top_k_candidates]
            # Rerank using cross-encoder
            reranked_docs = self.rerank(
                query=query,
                candidate_docs=top_candidates,
                doc_texts= doc_texts
            )
            
            reranked_results[query_id] = reranked_docs
        
        return reranked_docs
    
    def get_method_info(self) -> Dict:
        """Get information about the reranking method."""
        return {
            'method_name': self.method_name
        }
