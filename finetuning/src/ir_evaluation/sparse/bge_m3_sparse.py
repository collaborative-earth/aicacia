"""
BGE-M3 sparse retrieval evaluator.
"""
import logging
from typing import Dict, List, Optional
from FlagEmbedding import BGEM3FlagModel
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..base.evaluator import BaseEvaluator

logger = logging.getLogger(__name__)


class BGEM3SparseEvaluator(BaseEvaluator):
    """Evaluator for BGE-M3 sparse retrieval."""

    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, set],
        model_id: str = "BAAI/bge-m3",
        method_name: Optional[str] = "bge-m3_sparse",
        trust_remote_code: bool = True,
        device: Optional[str] = None,
        batch_size: int = 256,
        **kwargs
    ):
        """
        Initialize BGE-M3 sparse evaluator.

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
        logger.info(f"Loading BGE-M3 model for sparse retrieval: {model_id}")
        self.model = BGEM3FlagModel(self.model_id,  use_fp16=True,device=device,batch_size = batch_size)

        # Pre-compute document sparse embeddings
        logger.info("Computing document sparse embeddings...")
        self.doc_sparse_embeddings = self._compute_document_sparse_embeddings()
        self.query_sparse_embeddings = self._compute_query_sparse_embeddings()
        logger.info(f"BGE-M3 sparse evaluator initialized with {len(self.doc_sparse_embeddings)} document embeddings")

    def _compute_sparse_embeddings(self, texts: list[str], ids: list[str], label: str) -> dict:
        """
        Generic helper to compute sparse embeddings for a list of texts.

        Args:
            texts: List of input strings to encode
            ids: List of corresponding IDs
            label: Label for logging (e.g. "Corpus" or "Queries")

        Returns:
            dict: Mapping from ID to sparse embedding
        """
        logger.info(f"Encoding {len(texts)} {label.lower()} into sparse embeddings...")

        # Model encode call for sparse embeddings
        output = self.model.encode(
            texts,
            return_dense=False,
            return_sparse=True,
            return_colbert_vecs=False
        )

        id_to_embedding = {id_: output['lexical_weights'][i] for i, id_ in enumerate(ids)}

        if label.lower() == "corpus":
            self.doc_id_to_idx = {id_: i for i, id_ in enumerate(ids)}
            self.doc_sparse_embeddings = id_to_embedding
        elif label.lower() == "queries":
            self.query_id_to_idx = {id_: i for i, id_ in enumerate(ids)}
            self.query_sparse_embeddings = id_to_embedding

        return id_to_embedding


    def _compute_document_sparse_embeddings(self) -> dict:
        """Compute sparse embeddings for all documents in the corpus."""
        return self._compute_sparse_embeddings(
            texts=list(self.corpus.values()),
            ids=list(self.corpus.keys()),
            label="Corpus"
        )


    def _compute_query_sparse_embeddings(self) -> dict:
        """Compute sparse embeddings for all queries."""
        return self._compute_sparse_embeddings(
            texts=list(self.queries.values()),
            ids=list(self.queries.keys()),
            label="Queries"
        )

    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query using BGE-M3 sparse embeddings.

        Args:
            query: Query text
            top_k: Number of documents to retrieve

        Returns:
            List of document IDs ranked by relevance
        """
        # Compute query sparse embedding
        q_output = self.model.encode(
            [query],
            return_dense=False,
            return_sparse=True,
            return_colbert_vecs=False
        )
        
        # Use official BGE-M3 scoring function
        scores = {
            doc_id: self.model.compute_lexical_matching_score(q_output['lexical_weights'][0], d_vec)
            for doc_id, d_vec in  self.doc_sparse_embeddings.items()
        }

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return  [doc_id for doc_id, _ in ranked[:top_k]]

    def _get_query_results(self, top_k: int = 100) -> Dict[str, List[str]]:
        """
        Retrieve all top-k documents for all queries in the datasets.
        
        Args:
            top_k: Number of documents to retrieve for each query
            
        Returns:
            List of document IDs ranked by relevance
        """
        query_results = {}
        for query_id, q_vec in self.query_sparse_embeddings.items():
            # Compute scores against all documents
            scores = {
                doc_id: self.model.compute_lexical_matching_score(q_vec, d_vec)
                for doc_id, d_vec in self.doc_sparse_embeddings.items()
            }

            # Get top-k sorted
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            query_results[query_id] = [doc_id for doc_id, _ in ranked[:top_k]]
        
        return query_results
    
    def get_model_info(self) -> Dict:
        """Get information about the BGE-M3 sparse model."""
        info = super().get_model_info()
        info.update({
            'model_id': self.model_id,
            'embedding_dim': self.doc_sparse_embeddings.shape[1],
            'device': str(self.model.device),
            'batch_size': self.batch_size
        })
        return info
