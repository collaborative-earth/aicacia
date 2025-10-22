"""
BGE-M3 dense retrieval evaluator.
"""
import logging
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..base.evaluator import BaseEvaluator

logger = logging.getLogger(__name__)


class BGEM3Evaluator(BaseEvaluator):
    """Evaluator for BGE-M3 dense retrieval."""
    
    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, set],
        model_id: str = "BAAI/bge-m3",
        method_name: Optional[str] = "bge-m3",
        trust_remote_code: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32,
        **kwargs
    ):
        """
        Initialize BGE-M3 evaluator.
        
        Args:
            queries: Dictionary mapping query IDs to query text
            corpus: Dictionary mapping document IDs to document text
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            model_id: HuggingFace model ID for BGE-M3
            trust_remote_code: Whether to trust remote code
            device: Device to run the model on
            batch_size: Batch size for encoding
        """
        super().__init__(queries, corpus, relevant_docs, method_name, **kwargs)
        
        self.model_id = model_id
        self.trust_remote_code = trust_remote_code
        self.device = device
        self.batch_size = batch_size
        
        # Initialize model
        logger.info(f"Loading BGE-M3 model: {model_id}")
        self.model = SentenceTransformer(model_id, trust_remote_code=trust_remote_code, device=device)
        
        # Pre-compute document embeddings
        logger.info("Computing document embeddings...")
        self.doc_embeddings = self._compute_document_embeddings()
        
        logger.info(f"BGE-M3 evaluator initialized with {len(self.doc_embeddings)} document embeddings")
    
    def _compute_document_embeddings(self) -> np.ndarray:
        """Compute embeddings for all documents in the corpus."""
        doc_texts = list(self.corpus.values())
        doc_ids = list(self.corpus.keys())
        
        # Compute embeddings in batches
        embeddings = []
        for i in range(0, len(doc_texts), self.batch_size):
            batch_texts = doc_texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=self.show_progress)
            embeddings.append(batch_embeddings)
        
        # Concatenate all embeddings
        all_embeddings = np.vstack(embeddings)
        
        # Store mapping from doc_id to index
        self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(doc_ids)}
        
        return all_embeddings
    
    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query using BGE-M3 dense embeddings.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            
        Returns:
            List of document IDs ranked by relevance
        """
        # Compute query embedding
        query_embedding = self.model.encode([query])
        
        # Compute similarities
        similarities = cosine_similarity(query_embedding, self.doc_embeddings)[0]
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Convert indices to document IDs
        doc_ids = list(self.corpus.keys())
        top_k_docs = [doc_ids[idx] for idx in top_k_indices]
        
        return top_k_docs
    
    def get_model_info(self) -> Dict:
        """Get information about the BGE-M3 model."""
        info = super().get_model_info()
        info.update({
            'model_id': self.model_id,
            'embedding_dim': self.doc_embeddings.shape[1],
            'device': str(self.model.device),
            'batch_size': self.batch_size
        })
        return info
