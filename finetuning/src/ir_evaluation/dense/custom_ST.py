"""
Custom dense retrieval evaluator for any SentenceTransformer model.
"""
import logging
from typing import Dict, List, Optional
from tqdm import trange
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..base.evaluator import BaseEvaluator

logger = logging.getLogger(__name__)


class STDenseEvaluator(BaseEvaluator):
    """Evaluator for custom dense retrieval models."""
    
    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, set],
        model_id: str,
        method_name: Optional[str] = None,
        trust_remote_code: bool = True,
        device: Optional[str] = None,
        batch_size: int = 32,
        **kwargs
    ):
        """
        Initialize custom dense evaluator.
        
        Args:
            queries: Dictionary mapping query IDs to query text
            corpus: Dictionary mapping document IDs to document text
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            model_id: HuggingFace model ID
            method_name: Name for this method (defaults to model_id)
            trust_remote_code: Whether to trust remote code
            device: Device to run the model on
            batch_size: Batch size for encoding
        """
        if method_name is None:
            method_name = model_id.split('/')[-1]  # Use last part of model ID as name
        
        super().__init__(queries, corpus, relevant_docs, method_name, **kwargs)
        
        self.model_id = model_id
        self.trust_remote_code = trust_remote_code
        self.device = device
        self.batch_size = batch_size
        
        # Initialize model
        logger.info(f"Loading custom model: {model_id}")
        self.model = SentenceTransformer(model_id, trust_remote_code=trust_remote_code, device=device)
        
        # Pre-compute document and query embeddings
        logger.info("Computing document and query embeddings...")
        self.doc_embeddings = self._compute_document_embeddings()
        self.query_embeddings = self._compute_query_embeddings()
        
        logger.info(f"Custom dense evaluator initialized with {len(self.doc_embeddings)} document embeddings")
    
    def _compute_embeddings(self, texts: list[str], ids: list[str], label: str) -> np.ndarray:
        """
        Generic helper to compute embeddings for a list of texts with progress tracking.

        Args:
            texts: List of input strings to encode
            ids: List of corresponding IDs
            label: Label for tqdm progress bar (e.g. "Corpus" or "Queries")

        Returns:
            np.ndarray: Stacked embeddings array
        """
        num_items = len(texts)

        logger.info(f"Encoding {num_items} {label.lower()} in batches of {self.batch_size}...")

        # SentenceTransformer handles batching internally
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=self.show_progress,
            convert_to_tensor=True,
        )

        id_to_idx = {id_: idx for idx, id_ in enumerate(ids)}

        if label.lower() == "corpus":
            self.doc_id_to_idx = id_to_idx
        elif label.lower() == "queries":
            self.query_id_to_idx = id_to_idx

        return embeddings
    
    def _compute_document_embeddings(self) -> np.ndarray:
        """Compute embeddings for all documents in the corpus."""
        return self._compute_embeddings(
            texts=list(self.corpus.values()),
            ids=list(self.corpus.keys()),
            label="Corpus"
        )

    def _compute_query_embeddings(self) -> np.ndarray:
        """Compute embeddings for all queries."""
        return self._compute_embeddings(
            texts=list(self.queries.values()),
            ids=list(self.queries.keys()),
            label="Queries"
        )
    
    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query using custom dense embeddings.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            
        Returns:
            List of document IDs ranked by relevance
        """
        # Compute query embedding
        query_embedding = self.model.encode([query])
        
        # Compute similarities
        #similarity_function = self.model.similarity
        similarities = cosine_similarity(query_embedding, self.doc_embeddings)[0]
        
        # Get top-k indices
        top_k_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Convert indices to document IDs
        doc_ids = list(self.corpus.keys())
        top_k_docs = [doc_ids[idx] for idx in top_k_indices]
        
        return top_k_docs
    
    def _get_query_results(self, top_k: int = 100) -> Dict[str, List[str]]:
        """
        Retrieve all top-k documents for all queries in the datasets.
        
        Args:
            top_k: Number of documents to retrieve for each query
            
        Returns:
            List of document IDs ranked by relevance
        """
        query_results = {}
        # Use default similarity function of the model
        similarity_function = self.model.similarity
        pair_scores = similarity_function(self.query_embeddings, self.doc_embeddings)
        top_values, top_idx = torch.topk(pair_scores, k=min(top_k, pair_scores.size(1)), dim=1, largest=True, sorted=True)
        top_values = top_values.cpu().tolist()
        top_idx = top_idx.cpu().tolist()
        doc_ids = list(self.doc_id_to_idx.keys())
        for q_idx, query_id in enumerate(self.query_id_to_idx):
            query_results[query_id] = [doc_ids[i] for i in top_idx[q_idx]]

        return query_results
    
    def get_model_info(self) -> Dict:
        """Get information about the model."""
        info = super().get_model_info()
        info.update({
            'model_id': self.model_id,
            'embedding_dim': self.doc_embeddings.shape[1],
            'device': str(self.model.device),
            'batch_size': self.batch_size,
            'similarity function' : self.model.similarity_fn_name
        })
        return info
