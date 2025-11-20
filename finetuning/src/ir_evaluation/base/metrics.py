"""
Metrics calculation for retrieval evaluation.
"""
import logging
from typing import Dict, List, Set

import numpy as np

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculator for various retrieval evaluation metrics."""
    
    def __init__(self, relevant_docs: Dict[str, Set[str]], k_values: List[int]):
        """
        Initialize metrics calculator.
        
        Args:
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            k_values: List of k values for evaluation
        """
        self.relevant_docs = relevant_docs
        self.k_values = k_values
    
    def calculate_all_metrics(self, query_results: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Calculate all metrics for the given query results.
        
        Args:
            query_results: Dictionary mapping query IDs to ranked document lists
            
        Returns:
            Dictionary of metric names to values
        """
        metrics = {}
        
        # Calculate metrics for each k value
        for k in self.k_values:
            # MRR@k
            metrics[f'mrr@{k}'] = self._calculate_mrr_at_k(query_results, k)
            
            # NDCG@k
            metrics[f'ndcg@{k}'] = self._calculate_ndcg_at_k(query_results, k)
            
            # Precision@k
            metrics[f'precision@{k}'] = self._calculate_precision_at_k(query_results, k)
            
            # Recall@k
            metrics[f'recall@{k}'] = self._calculate_recall_at_k(query_results, k)
            
            # Hit Rate@k
            metrics[f'hit_rate@{k}'] = self._calculate_hit_rate_at_k(query_results, k)
        
        # Calculate MAP
        metrics['map'] = self._calculate_map(query_results)
        
        logger.info(f"Calculated {len(metrics)} metrics")
        return metrics
    
    def _calculate_mrr_at_k(self, query_results: Dict[str, List[str]], k: int) -> float:
        """Calculate Mean Reciprocal Rank at k."""
        reciprocal_ranks = []
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            for rank, doc_id in enumerate(retrieved_docs[:k]):
                if doc_id in relevant_docs:
                    reciprocal_ranks.append(1.0 / (rank + 1))
                    break
            else:
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    def _calculate_ndcg_at_k(self, query_results: Dict[str, List[str]], k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain at k."""
        ndcg_scores = []
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            # Calculate DCG@k
            dcg = 0.0
            for rank, doc_id in enumerate(retrieved_docs[:k]):
                if doc_id in relevant_docs:
                    dcg += 1.0 / np.log2(rank + 2)  # rank + 2 because log2(1) = 0
            
            # Calculate IDCG@k (ideal DCG)
            idcg = 0.0
            num_relevant = len(relevant_docs)
            for rank in range(min(k, num_relevant)):
                idcg += 1.0 / np.log2(rank + 2)
            
            # Calculate NDCG@k
            if idcg > 0:
                ndcg_scores.append(dcg / idcg)
            else:
                ndcg_scores.append(0.0)
        
        return np.mean(ndcg_scores) if ndcg_scores else 0.0
    
    def _calculate_precision_at_k(self, query_results: Dict[str, List[str]], k: int) -> float:
        """Calculate Precision at k."""
        precisions = []
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            # Count relevant documents in top-k
            relevant_in_top_k = sum(1 for doc_id in retrieved_docs[:k] if doc_id in relevant_docs)
            precision = relevant_in_top_k / k if k > 0 else 0.0
            precisions.append(precision)
        
        return np.mean(precisions) if precisions else 0.0
    
    def _calculate_recall_at_k(self, query_results: Dict[str, List[str]], k: int) -> float:
        """Calculate Recall at k."""
        recalls = []
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            if len(relevant_docs) == 0:
                recalls.append(0.0)
                continue
            
            # Count relevant documents in top-k
            relevant_in_top_k = sum(1 for doc_id in retrieved_docs[:k] if doc_id in relevant_docs)
            recall = relevant_in_top_k / len(relevant_docs)
            recalls.append(recall)
        
        return np.mean(recalls) if recalls else 0.0
    
    def _calculate_hit_rate_at_k(self, query_results: Dict[str, List[str]], k: int) -> float:
        """Calculate Hit Rate at k (fraction of queries with at least one relevant doc in top-k)."""
        hits = 0
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            # Check if any relevant document is in top-k
            if any(doc_id in relevant_docs for doc_id in retrieved_docs[:k]):
                hits += 1
        
        return hits / len(query_results) if query_results else 0.0
    
    def _calculate_map(self, query_results: Dict[str, List[str]]) -> float:
        """Calculate Mean Average Precision."""
        average_precisions = []
        
        for query_id, retrieved_docs in query_results.items():
            relevant_docs = self.relevant_docs.get(query_id, set())
            
            if len(relevant_docs) == 0:
                average_precisions.append(0.0)
                continue
            
            # Calculate average precision for this query
            relevant_ranks = []
            for rank, doc_id in enumerate(retrieved_docs):
                if doc_id in relevant_docs:
                    relevant_ranks.append(rank + 1)
            
            if not relevant_ranks:
                average_precisions.append(0.0)
                continue
            
            # Calculate precision at each relevant document
            precisions = []
            for i, rank in enumerate(relevant_ranks):
                precision = (i + 1) / rank
                precisions.append(precision)
            
            average_precisions.append(np.mean(precisions))
        
        return np.mean(average_precisions) if average_precisions else 0.0


