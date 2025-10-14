"""
BM25 sparse retrieval evaluator.
"""
import logging
from typing import Dict, List, Set

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi

from ..base.evaluator import BaseEvaluator

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)


class BM25Evaluator(BaseEvaluator):
    """Evaluator for BM25 sparse retrieval."""
    
    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str],
        relevant_docs: Dict[str, set],
        k1: float = 1.2,
        b: float = 0.75,
        **kwargs
    ):
        """
        Initialize BM25 evaluator.
        
        Args:
            queries: Dictionary mapping query IDs to query text
            corpus: Dictionary mapping document IDs to document text
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            k1: BM25 parameter k1
            b: BM25 parameter b
        """
        super().__init__(queries, corpus, relevant_docs, "bm25", **kwargs)
        
        self.k1 = k1
        self.b = b
        
        # Initialize BM25
        logger.info("Initializing BM25 index...")
        self.bm25 = self._build_bm25_index()
        
        logger.info(f"BM25 evaluator initialized with k1={k1}, b={b}")
    
    def _preprocess(self, text: str) -> List[str]:
        """
        Preprocess text for BM25.
        
        Args:
            text: Input text
            
        Returns:
            List of preprocessed tokens
        """
        # Tokenize and convert to lowercase
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and non-alphabetic tokens
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token.isalpha() and token not in stop_words]
        
        return tokens
    
    def _build_bm25_index(self) -> BM25Okapi:
        """Build BM25 index from corpus."""
        # Preprocess all documents
        processed_docs = []
        for doc_id, doc_text in self.corpus.items():
            processed_doc = self._preprocess(doc_text)
            processed_docs.append(processed_doc)
        
        # Create BM25 index
        bm25 = BM25Okapi(processed_docs, k1=self.k1, b=self.b)
        
        # Store document ID mapping
        self.doc_ids = list(self.corpus.keys())
        
        return bm25
    
    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query using BM25.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            
        Returns:
            List of document IDs ranked by relevance
        """
        # Preprocess query
        query_tokens = self._preprocess(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_k_indices = np.argsort(scores)[::-1][:top_k]
        
        # Convert indices to document IDs
        top_k_docs = [self.doc_ids[idx] for idx in top_k_indices]
        
        return top_k_docs
    
    def get_model_info(self) -> Dict:
        """Get information about the BM25 model."""
        info = super().get_model_info()
        info.update({
            'k1': self.k1,
            'b': self.b,
            'num_documents': len(self.corpus)
        })
        return info
