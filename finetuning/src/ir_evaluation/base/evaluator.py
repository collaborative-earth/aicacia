"""
Base evaluator class for all retrieval methods.
"""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import psutil

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Container for evaluation results."""
    method_name: str
    metrics: Dict[str, float]
    performance: Dict[str, float]
    query_results: Dict[str, List[str]]  # query_id -> ranked_doc_ids
    execution_time: float
    memory_usage: float


class BaseEvaluator(ABC):
    """
    Abstract base class for all retrieval evaluators.
    
    This class provides a common interface for evaluating different retrieval methods
    and includes performance profiling capabilities.
    """
    
    def __init__(
        self,
        queries: Dict[str, str],
        corpus: Dict[str, str], 
        relevant_docs: Dict[str, Set[str]],
        method_name: str,
        k_values: List[int] = [1, 3, 5, 10, 20],
        show_progress: bool = True
    ):
        """
        Initialize the base evaluator.
        
        Args:
            queries: Dictionary mapping query IDs to query text
            corpus: Dictionary mapping document IDs to document text
            relevant_docs: Dictionary mapping query IDs to sets of relevant document IDs
            method_name: Name of the retrieval method
            k_values: List of k values for evaluation metrics
            show_progress: Whether to show progress bars
        """
        self.queries = queries
        self.corpus = corpus
        self.relevant_docs = relevant_docs
        self.method_name = method_name
        self.k_values = k_values
        self.show_progress = show_progress
        
        # Performance tracking
        self.start_time = None
        self.start_memory = None
        
        logger.info(f"Initialized {method_name} evaluator with {len(queries)} queries and {len(corpus)} documents")
    
    def _start_profiling(self):
        """Start performance profiling."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Started profiling for {self.method_name}")
    
    def _end_profiling(self) -> Tuple[float, float]:
        """End performance profiling and return execution time and memory usage."""
        execution_time = time.time() - (self.start_time or 0)
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_usage = end_memory - (self.start_memory or 0)
        
        logger.info(f"Completed profiling for {self.method_name}: {execution_time:.2f}s, {memory_usage:.2f}MB")
        return execution_time, memory_usage
    
    def _get_query_results(self, top_k: int = 100) -> Dict[str, List[str]]:
        """
        Retrieve all top-k documents for all queries in the datasets.
        
        Args:
            top_k: Number of documents to retrieve for each query
            
        Returns:
            List of document IDs ranked by relevance
        """
        query_results = {}
        for query_id, query in self.queries.items():
            if self.show_progress and len(self.queries) > 10:
                if query_id == list(self.queries.keys())[0]:
                    logger.info(f"Processing {len(self.queries)} queries...")
            
            retrieved_docs = self._retrieve(query, top_k)
            query_results[query_id] = retrieved_docs
        return query_results
    
    @abstractmethod
    def _retrieve(self, query: str, top_k: int = 100) -> List[str]:
        """
        Retrieve top-k documents for a given query.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            
        Returns:
            List of document IDs ranked by relevance
        """
        pass
    
    def evaluate(self, top_k: int = 100) -> EvaluationResult:
        """
        Evaluate the retrieval method.
        
        Args:
            top_k: Maximum number of documents to retrieve per query
            
        Returns:
            EvaluationResult containing metrics and performance data
        """
        logger.info(f"Starting evaluation for {self.method_name}")
        self._start_profiling()
        
        # Retrieve documents for all queries
        #query_results = {}
        #for query_id, query in self.queries.items():
        #    if self.show_progress and len(self.queries) > 10:
        #        if query_id == list(self.queries.keys())[0]:
        #            logger.info(f"Processing {len(self.queries)} queries...")
        #    
        #    retrieved_docs = self._retrieve(query, top_k)
        #   query_results[query_id] = retrieved_docs
        query_results = self._get_query_results(top_k)
        # Calculate metrics
        metrics = self._calculate_metrics(query_results)
        
        # End profiling
        execution_time, memory_usage = self._end_profiling()
        
        # Calculate performance metrics
        performance = {
            'execution_time': execution_time,
            'memory_usage': memory_usage,
            'queries_per_second': len(self.queries) / execution_time if execution_time > 0 else 0
        }
        
        logger.info(f"Evaluation completed for {self.method_name}")
        return EvaluationResult(
            method_name=self.method_name,
            metrics=metrics,
            performance=performance,
            query_results=query_results,
            execution_time=execution_time,
            memory_usage=memory_usage
        )
    
    def _calculate_metrics(self, query_results: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate all evaluation metrics."""
        from .metrics import MetricsCalculator
        
        calculator = MetricsCalculator(self.relevant_docs, self.k_values)
        return calculator.calculate_all_metrics(query_results)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model/method being evaluated."""
        return {
            'method_name': self.method_name,
            'num_queries': len(self.queries),
            'num_documents': len(self.corpus),
            'k_values': self.k_values
        }
