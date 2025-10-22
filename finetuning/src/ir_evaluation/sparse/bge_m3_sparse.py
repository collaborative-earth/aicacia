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

        logger.info(f"BGE-M3 sparse evaluator initialized with {len(self.doc_sparse_embeddings)} document embeddings")

    def _compute_document_sparse_embeddings(self) -> np.ndarray:
        """Compute sparse embeddings for all documents in the corpus."""
        doc_texts = list(self.corpus.values())
        doc_ids = list(self.corpus.keys())

        # Compute sparse embeddings in batches
        output = self.model.encode(
            doc_texts,
            return_dense=False,
            return_sparse=True,
            return_colbert_vecs=False
        )

        return {doc_id: output['lexical_weights'][i] for i, doc_id in enumerate(doc_ids)}

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
