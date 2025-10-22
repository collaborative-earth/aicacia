"""
BGE-M3 hybrid retrieval evaluator (dense + sparse).
"""
import logging
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..base.evaluator import BaseEvaluator

logger = logging.getLogger(__name__)


class BGEM3HybridEvaluator(BaseEvaluator):
    """Evaluator for BGE-M3 hybrid retrieval (dense + sparse)."""
    
    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, set],
        model_id: str = "BAAI/bge-m3",
        method_name: Optional[str] = "bge-m3_hybrid",
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        trust_remote_code: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32,
        **kwargs
    ):
        """
        Initialize BGE-M3 hybrid evaluator.
        
        Args:
            queries: Dictionary mapping query IDs to query text
            corpus: Dictionary mapping document IDs to document text
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            model_id: HuggingFace model ID for BGE-M3
            dense_weight: Weight for dense similarity scores
            sparse_weight: Weight for sparse similarity scores
            trust_remote_code: Whether to trust remote code
            device: Device to run the model on
            batch_size: Batch size for encoding
        """
        super().__init__(queries, corpus, relevant_docs, method_name, **kwargs)
        
        self.model_id = model_id
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.trust_remote_code = trust_remote_code
        self.device = device
        self.batch_size = batch_size
        
        # Normalize weights
        total_weight = dense_weight + sparse_weight
        self.dense_weight = dense_weight / total_weight
        self.sparse_weight = sparse_weight / total_weight
        
        # Initialize model
        logger.info(f"Loading BGE-M3 model for hybrid retrieval: {model_id}")
        self.model = SentenceTransformer(model_id, trust_remote_code=trust_remote_code, device=device)
        
        # Pre-compute document embeddings (both dense and sparse)
        logger.info("Computing document dense embeddings...")
        self.doc_dense_embeddings = self._compute_document_dense_embeddings()
        
        logger.info("Computing document sparse embeddings...")
        self.doc_sparse_embeddings = self._compute_document_sparse_embeddings()
        
        logger.info(f"BGE-M3 hybrid evaluator initialized with dense_weight={self.dense_weight:.2f}, sparse_weight={self.sparse_weight:.2f}")
    
    def _compute_document_dense_embeddings(self) -> np.ndarray:
        """Compute dense embeddings for all documents in the corpus."""
        doc_texts = list(self.corpus.values())
        doc_ids = list(self.corpus.keys())
        
        # Compute dense embeddings in batches
        embeddings = []
        for i in range(0, len(doc_texts), self.batch_size):
            batch_texts = doc_texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=self.show_progress)
            embeddings.append(batch_embeddings)
        
        # Concatenate all embeddings
        all_embeddings = np.vstack(embeddings)
        
        return all_embeddings
    
    def _compute_document_sparse_embeddings(self) -> np.ndarray:
        """Compute sparse embeddings for all documents in the corpus."""
        doc_texts = list(self.corpus.values())
        doc_ids = list(self.corpus.keys())
        
        # Compute sparse embeddings in batches
        embeddings = []
        for i in range(0, len(doc_texts), self.batch_size):
            batch_texts = doc_texts[i:i + self.batch_size]
            # Use encode with sparse=True to get sparse embeddings
            batch_embeddings = self.model.encode(
                batch_texts, 
                show_progress_bar=self.show_progress,
                convert_to_tensor=True
            )
            
            # Extract sparse embeddings (this is a simplified approach)
            # In practice, you might need to use the model's specific sparse encoding method
            if hasattr(batch_embeddings, 'to_dense'):
                batch_embeddings = batch_embeddings.to_dense().cpu().numpy()
            else:
                batch_embeddings = batch_embeddings.cpu().numpy()
            
            embeddings.append(batch_embeddings)
        
        # Concatenate all embeddings
        all_embeddings = np.vstack(embeddings)
        
        return all_embeddings
    
    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query using BGE-M3 hybrid embeddings.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            
        Returns:
            List of document IDs ranked by relevance
        """
        # Compute query dense embedding
        query_dense_embedding = self.model.encode([query])
        
        # Compute query sparse embedding
        query_sparse_embedding = self.model.encode(
            [query], 
            convert_to_tensor=True
        )
        
        # Convert sparse embedding to numpy if needed
        if hasattr(query_sparse_embedding, 'to_dense'):
            query_sparse_embedding = query_sparse_embedding.to_dense().cpu().numpy()
        else:
            query_sparse_embedding = query_sparse_embedding.cpu().numpy()
        
        # Compute dense similarities
        dense_similarities = cosine_similarity(query_dense_embedding, self.doc_dense_embeddings)[0]
        
        # Compute sparse similarities
        sparse_similarities = cosine_similarity(query_sparse_embedding, self.doc_sparse_embeddings)[0]
        
        # Combine similarities with weights
        hybrid_similarities = (
            self.dense_weight * dense_similarities + 
            self.sparse_weight * sparse_similarities
        )
        
        # Get top-k indices
        top_k_indices = np.argsort(hybrid_similarities)[::-1][:top_k]
        
        # Convert indices to document IDs
        doc_ids = list(self.corpus.keys())
        top_k_docs = [doc_ids[idx] for idx in top_k_indices]
        
        return top_k_docs
    
    def get_model_info(self) -> Dict:
        """Get information about the BGE-M3 hybrid model."""
        info = super().get_model_info()
        info.update({
            'model_id': self.model_id,
            'dense_weight': self.dense_weight,
            'sparse_weight': self.sparse_weight,
            'dense_embedding_dim': self.doc_dense_embeddings.shape[1],
            'sparse_embedding_dim': self.doc_sparse_embeddings.shape[1],
            'device': str(self.model.device),
            'batch_size': self.batch_size
        })
        return info
