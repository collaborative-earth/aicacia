"""
Cross-encoder reranker for improving retrieval results.
"""
import logging
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import CrossEncoder

from .base_reranker import BaseReranker

logger = logging.getLogger(__name__)


class CrossEncoderReranker(BaseReranker):
    """Reranker using cross-encoder models."""
    
    def __init__(
        self,
        model_id: str = "BAAI/bge-reranker-v2-m3",
        trust_remote_code: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_id: HuggingFace model ID for the cross-encoder
            trust_remote_code: Whether to trust remote code
            device: Device to run the model on
            batch_size: Batch size for reranking
        """
        super().__init__("Cross-Encoder")
        
        self.model_id = model_id
        self.trust_remote_code = trust_remote_code
        self.device = device
        self.batch_size = batch_size
        
        # Initialize cross-encoder model
        logger.info(f"Loading cross-encoder model: {model_id}")
        self.model = CrossEncoder(
            model_id, 
            trust_remote_code=trust_remote_code,
            device=device
        )
        
        logger.info(f"Cross-encoder reranker initialized with batch_size={batch_size}")
    
    def rerank(
        self, 
        query: str, 
        candidate_docs: List[str], 
        doc_texts: Dict[str, str],
        top_k: Optional[int] = None
    ) -> List[str]:
        """
        Rerank candidate documents using cross-encoder.
        
        Args:
            query: Query text
            candidate_docs: List of candidate document IDs
            doc_texts: Dictionary mapping document IDs to document texts
            top_k: Number of top documents to return (None for all)
            
        Returns:
            List of reranked document IDs
        """
        if not candidate_docs:
            return []
        
        # Prepare query-document pairs
        query_doc_pairs = []
        for doc_id in candidate_docs:
            doc_text = doc_texts.get(doc_id, "")
            query_doc_pairs.append([query, doc_text])
        
        # Compute relevance scores in batches
        scores = []
        for i in range(0, len(query_doc_pairs), self.batch_size):
            batch_pairs = query_doc_pairs[i:i + self.batch_size]
            batch_scores = self.model.predict(batch_pairs)
            scores.extend(batch_scores)
        
        # Create list of (doc_id, score) tuples
        doc_scores = list(zip(candidate_docs, scores))
        
        # Sort by score (descending)
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract reranked document IDs
        reranked_docs = [doc_id for doc_id, score in doc_scores]
        
        # Return top_k if specified
        if top_k is not None:
            reranked_docs = reranked_docs[:top_k]
        
        return reranked_docs
    
    def get_method_info(self) -> Dict:
        """Get information about the cross-encoder reranker."""
        info = super().get_method_info()
        info.update({
            'model_id': self.model_id,
            'device': str(self.model.device),
            'batch_size': self.batch_size
        })
        return info
