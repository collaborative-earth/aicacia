"""
Comprehensive evaluator for all retrieval methods.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
import pandas as pd
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset

from .base.config import EvaluationConfig, create_default_config
from .base.evaluator import EvaluationResult
from .dense import BGEM3Evaluator, CustomDenseEvaluator, JinaV3Evaluator, STDenseEvaluator
from .hybrid import BGEM3HybridEvaluator
from .reranking import CrossEncoderReranker
from .sparse import BGEM3SparseEvaluator, BM25Evaluator

logger = logging.getLogger(__name__)


class ComprehensiveEvaluator:
    """
    Comprehensive evaluator that can run multiple retrieval methods and compare results.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize comprehensive evaluator.
        
        Args:
            config_path: Path to YAML configuration file
        """
        if config_path is None:
            # Create default config
            config_path = "evaluation_config.yaml"
            create_default_config(config_path)
        
        # Load configuration
        self.config = EvaluationConfig.from_yaml(config_path)
        
        # Load dataset
        logger.info(f"Loading dataset from {self.config.dataset_path}")
        self.dataset = EmbeddingQAFinetuneDataset.from_json(self.config.dataset_path)
        
        # Limit queries if specified
        if self.config.max_queries is not None:
            query_ids = list(self.dataset.queries.keys())[:self.config.max_queries]
            self.dataset.queries = {qid: self.dataset.queries[qid] for qid in query_ids}
            self.dataset.relevant_docs = {qid: self.dataset.relevant_docs[qid] for qid in query_ids}
        
        logger.info(f"Loaded dataset with {len(self.dataset.queries)} queries and {len(self.dataset.corpus)} documents")
        
        # Create results directory
        Path(self.config.results_dir).mkdir(exist_ok=True, parents=True)
    
    def evaluate_all(self) -> Dict[str, EvaluationResult]:
        """
        Evaluate all configured retrieval methods.
        
        Returns:
            Dictionary mapping method names to evaluation results
        """
        results = {}
        
        # Evaluate dense methods
        for model_config in self.config.dense_models:
            logger.info(f"Evaluating dense method: {model_config.name}")
            evaluator = self._create_dense_evaluator(model_config)
            result = evaluator.evaluate()
            results[model_config.name] = result
        
        # Evaluate sparse methods
        for model_config in self.config.sparse_models:
            logger.info(f"Evaluating sparse method: {model_config.name}")
            evaluator = self._create_sparse_evaluator(model_config)
            result = evaluator.evaluate()
            results[model_config.name] = result
        
        # Evaluate hybrid methods
        for model_config in self.config.hybrid_models:
            logger.info(f"Evaluating hybrid method: {model_config.name}")
            evaluator = self._create_hybrid_evaluator(model_config)
            result = evaluator.evaluate()
            results[model_config.name] = result
        
        # Evaluate reranking methods (applied to top candidates from other methods)
        for model_config in self.config.reranking_models:
            logger.info(f"Evaluating reranking method: {model_config.name}")
            result = self._evaluate_reranking(model_config, results)
            results[f"{model_config.name}-reranked"] = result
        
        return results
    
    def _create_dense_evaluator(self, model_config) -> Any:
        """Create a dense evaluator based on model configuration."""
        return STDenseEvaluator(
            queries=self.dataset.queries,
            corpus=self.dataset.corpus,
            relevant_docs=self.dataset.relevant_docs,
            model_id=model_config.model_id,
            method_name=model_config.name,
            trust_remote_code=model_config.trust_remote_code,
            device=model_config.device,
            batch_size=model_config.batch_size,
            k_values=self.config.k_values,
            show_progress=self.config.show_progress
        )
    
    def _create_sparse_evaluator(self, model_config) -> Any:
        """Create a sparse evaluator based on model configuration."""
        if "bm25" in model_config.name.lower():
            return BM25Evaluator(
                queries=self.dataset.queries,
                corpus=self.dataset.corpus,
                relevant_docs=self.dataset.relevant_docs,
                k_values=self.config.k_values,
                show_progress=self.config.show_progress,
                **model_config.additional_params
            )
        elif "bge-m3" in model_config.name.lower() and "sparse" in model_config.name.lower():
            return BGEM3SparseEvaluator(
                queries=self.dataset.queries,
                corpus=self.dataset.corpus,
                relevant_docs=self.dataset.relevant_docs,
                model_id=model_config.model_id,
                method_name = model_config.name,
                trust_remote_code=model_config.trust_remote_code,
                device=model_config.device,
                batch_size=model_config.batch_size,
                k_values=self.config.k_values,
                show_progress=self.config.show_progress,
            )
        else:
            raise ValueError(f"Unknown sparse method: {model_config.name}")
    
    def _create_hybrid_evaluator(self, model_config) -> Any:
        """Create a hybrid evaluator based on model configuration."""
        if "bge-m3" in model_config.name.lower() and "hybrid" in model_config.name.lower():
            return BGEM3HybridEvaluator(
                queries=self.dataset.queries,
                corpus=self.dataset.corpus,
                relevant_docs=self.dataset.relevant_docs,
                model_id=model_config.model_id,
                trust_remote_code=model_config.trust_remote_code,
                method_name=model_config.name,
                device=model_config.device,
                batch_size=model_config.batch_size,
                k_values=self.config.k_values,
                show_progress=self.config.show_progress,
                **model_config.additional_params
            )
        else:
            raise ValueError(f"Unknown hybrid method: {model_config.name}")
    
    def _evaluate_reranking(self, model_config, existing_results: Dict[str, EvaluationResult]) -> EvaluationResult:
        """Evaluate reranking applied to existing results."""
        # Create reranker
        reranker = CrossEncoderReranker(
            model_id=model_config.model_id,
            trust_remote_code=model_config.trust_remote_code,
            device=model_config.device,
            batch_size=model_config.batch_size
        )
        
        # Get top-k candidates from existing results (use the best performing method)
        # For simplicity, we'll use the first available result
        if not existing_results:
            raise ValueError("No existing results available for reranking")
        
        base_method_name = list(existing_results.keys())[0]
        base_result = existing_results[base_method_name]
        
        # Get top-k candidates for reranking
        top_k_candidates = model_config.additional_params.get('top_k_candidates', 100)
        top_k_output = model_config.additional_params.get('top_k_output', None)

        reranked_results = reranker.rerank_all(
            queries=self.dataset.queries,
            base_results=base_result.query_results,
            doc_texts=self.dataset.corpus,
            top_k_candidates=top_k_candidates,
            top_k_output=top_k_output,
        )
        
        # Calculate metrics for reranked results
        from .base.metrics import MetricsCalculator
        calculator = MetricsCalculator(self.dataset.relevant_docs, self.config.k_values)
        metrics = calculator.calculate_all_metrics(reranked_results)
        
        # Create evaluation result
        return EvaluationResult(
            method_name=f"{model_config.name}-reranked",
            metrics=metrics,
            performance={
                'execution_time': 0.0,  # Would need to track this separately
                'memory_usage': 0.0,
                'queries_per_second': 0.0
            },
            query_results=reranked_results,
            execution_time=0.0,
            memory_usage=0.0
        )
    
    def generate_report(self, results: Dict[str, EvaluationResult], output_path: Optional[str] = None) -> str:
        """
        Generate a text report of evaluation results.
        
        Args:
            results: Dictionary of evaluation results
            output_path: Path to save the report (optional)
            
        Returns:
            Report text
        """
        if output_path is None:
            output_path = Path(self.config.results_dir) / "evaluation_report.txt"
        else:
            output_path = Path(output_path)
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("COMPREHENSIVE RETRIEVAL EVALUATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Dataset information
        report_lines.append("DATASET INFORMATION:")
        report_lines.append(f"  Queries: {len(self.dataset.queries)}")
        report_lines.append(f"  Documents: {len(self.dataset.corpus)}")
        report_lines.append(f"  K values: {self.config.k_values}")
        report_lines.append("")
        
        # Results summary
        report_lines.append("RESULTS SUMMARY:")
        report_lines.append("-" * 40)
        
        # Sort methods by MRR@10 for summary
        sorted_methods = sorted(
            results.items(),
            key=lambda x: x[1].metrics.get('mrr@10', 0),
            reverse=True
        )
        
        for method_name, result in sorted_methods:
            report_lines.append(f"\n{method_name.upper()}:")
            report_lines.append(f"  MRR@10: {result.metrics.get('mrr@10', 0):.4f}")
            report_lines.append(f"  NDCG@10: {result.metrics.get('ndcg@10', 0):.4f}")
            report_lines.append(f"  Precision@5: {result.metrics.get('precision@5', 0):.4f}")
            report_lines.append(f"  Recall@10: {result.metrics.get('recall@10', 0):.4f}")
            report_lines.append(f"  Execution time: {result.execution_time:.2f}s")
            report_lines.append(f"  Memory usage: {result.memory_usage:.2f}MB")
        
        # Detailed metrics
        report_lines.append("\n" + "=" * 80)
        report_lines.append("DETAILED METRICS")
        report_lines.append("=" * 80)
        
        # Create a dataframe with metrics
        rows = []
        for method_name, result in results.items():
            report_lines.append(f"\n{method_name.upper()}:")
            report_lines.append("-" * len(method_name))
            
            row = {'method':method_name}
            
            for metric_name, value in result.metrics.items():
                report_lines.append(f"  {metric_name}: {value:.4f}")
                row[metric_name] = value
            row["execution_time_s"] = getattr(result, "execution_time", float("nan"))
            row["memory_usage_mb"] = getattr(result, "memory_usage", float("nan"))
            qps = getattr(result, "performance", {}).get("queries_per_second", float("nan"))
            row["queries_per_second"] = qps
            rows.append(row)    
            
        df = pd.DataFrame(rows)
        
        # Performance comparison
        report_lines.append("\n" + "=" * 80)
        report_lines.append("PERFORMANCE COMPARISON")
        report_lines.append("=" * 80)
        
        report_lines.append("\nExecution Time (seconds):")
        for method_name, result in sorted(results.items(), key=lambda x: x[1].execution_time):
            report_lines.append(f"  {method_name}: {result.execution_time:.2f}s")
        
        report_lines.append("\nMemory Usage (MB):")
        for method_name, result in sorted(results.items(), key=lambda x: x[1].memory_usage):
            report_lines.append(f"  {method_name}: {result.memory_usage:.2f}MB")
        
        report_lines.append("\nQueries per Second:")
        for method_name, result in sorted(results.items(), key=lambda x: x[1].performance.get('queries_per_second', 0), reverse=True):
            qps = result.performance.get('queries_per_second', 0)
            report_lines.append(f"  {method_name}: {qps:.2f}")
        
        report_text = "\n".join(report_lines)
        
        # Save report
        with open(output_path, 'w') as f:
            f.write(report_text)
            
        table_path = output_path.with_suffix(".csv")
        df.to_csv(table_path, index=False)
        logger.info(f"Structured results saved to {table_path}")
            
        logger.info(f"Report saved to {output_path}")
            
        return report_text
