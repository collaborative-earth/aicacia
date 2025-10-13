# Comprehensive Retrieval Evaluation System

This module provides a comprehensive evaluation framework for multiple retrieval methods including dense, sparse, hybrid, and reranking approaches.

## Features

- **Dense Retrieval**: BGE-M3, Jina v3, and custom models
- **Sparse Retrieval**: BM25 and BGE-M3 sparse vectors
- **Hybrid Retrieval**: BGE-M3 hybrid (dense + sparse)
- **Reranking**: Cross-encoder reranking
- **Comprehensive Metrics**: MRR@k, NDCG@k, Precision@k, Recall@k, MAP, Hit Rate@k
- **Performance Profiling**: Execution time, memory usage, throughput
- **Automated Reporting**: Text-based evaluation reports

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/guru/aicacia/finetuning
pipenv install
```

### 2. Configure Evaluation

Edit `evaluation_config.yaml` to specify which methods to evaluate:

```yaml
methods:
  dense:
    - name: "bge-m3"
      model_id: "BAAI/bge-m3"
    - name: "bge-m3-finetuned"
      model_id: "your-org/bge-m3-finetuned"  # Replace with actual model ID
  sparse:
    - name: "bm25"
  hybrid:
    - name: "bge-m3-hybrid"
```

### 3. Run Evaluation

```bash
cd /Users/guru/aicacia/finetuning
python src/ir_evaluation/run_comprehensive_evaluation.py
```

### 4. View Results

Results will be saved to `results/evaluation_report.txt` with detailed metrics and performance comparisons.

## Configuration

The evaluation system uses YAML configuration files. Key configuration options:

### Dataset Configuration
```yaml
dataset:
  path: "data/qa_dataset/qa_finetune_dataset.json"
  max_queries: null  # null for all queries, or specify a number
```

### Method Configuration
```yaml
methods:
  dense:
    - name: "bge-m3"
      model_id: "BAAI/bge-m3"
      trust_remote_code: true
      device: null  # null for auto, or "cuda", "cpu"
      batch_size: 32
      max_length: 512
      additional_params: {}
```

### Metrics Configuration
```yaml
metrics:
  k_values: [1, 3, 5, 10, 20]  # K values for evaluation
```

### Output Configuration
```yaml
output:
  results_dir: "results"
  save_embeddings: false
  generate_plots: true
  generate_report: true
```

## Available Methods

### Dense Retrieval
- **BGE-M3**: `BAAI/bge-m3`
- **BGE-M3 Finetuned**: Your custom finetuned model
- **Jina v3**: `jinaai/jina-embeddings-v3`
- **Custom Models**: Any SentenceTransformer model

### Sparse Retrieval
- **BM25**: Classical term-frequency based retrieval
- **BGE-M3 Sparse**: Sparse vector component of BGE-M3

### Hybrid Retrieval
- **BGE-M3 Hybrid**: Combination of dense and sparse vectors with configurable weights

### Reranking
- **Cross-Encoder**: `BAAI/bge-reranker-v2-m3` applied to top-k candidates

## Evaluation Metrics

The system calculates the following metrics:

- **MRR@k**: Mean Reciprocal Rank at k
- **NDCG@k**: Normalized Discounted Cumulative Gain at k
- **Precision@k**: Precision at k
- **Recall@k**: Recall at k
- **MAP**: Mean Average Precision
- **Hit Rate@k**: Fraction of queries with at least one relevant doc in top-k

## Performance Metrics

- **Execution Time**: Total time for evaluation
- **Memory Usage**: Peak memory consumption
- **Throughput**: Queries per second

## Usage Examples

### Basic Evaluation
```python
from ir_evaluation.comprehensive_evaluator import ComprehensiveEvaluator

# Initialize evaluator
evaluator = ComprehensiveEvaluator("evaluation_config.yaml")

# Run evaluation
results = evaluator.evaluate_all()

# Generate report
report = evaluator.generate_report(results)
```

### Individual Method Evaluation
```python
from ir_evaluation.dense import BGEM3Evaluator
from ir_evaluation.sparse import BM25Evaluator

# Load dataset
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset
dataset = EmbeddingQAFinetuneDataset.from_json("data/qa_dataset/qa_finetune_dataset.json")

# Evaluate specific methods
bge_evaluator = BGEM3Evaluator(
    queries=dataset.queries,
    corpus=dataset.corpus,
    relevant_docs=dataset.relevant_docs
)
bge_results = bge_evaluator.evaluate()

bm25_evaluator = BM25Evaluator(
    queries=dataset.queries,
    corpus=dataset.corpus,
    relevant_docs=dataset.relevant_docs
)
bm25_results = bm25_evaluator.evaluate()
```

### Custom Configuration
```python
from ir_evaluation.base.config import EvaluationConfig, ModelConfig

# Create custom configuration
config = EvaluationConfig(
    dataset_path="data/qa_dataset/qa_finetune_dataset.json",
    k_values=[1, 3, 5, 10],
    dense_models=[
        ModelConfig(
            name="my-model",
            model_id="my-org/my-model",
            trust_remote_code=True
        )
    ]
)

# Save configuration
config.to_yaml("my_config.yaml")
```

## Testing

Run the test suite to validate the implementation:

```bash
cd /Users/guru/aicacia/finetuning
python src/ir_evaluation/test_evaluation.py
```

## File Structure

```
src/ir_evaluation/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── evaluator.py          # Base evaluator class
│   ├── metrics.py            # Metrics calculation
│   └── config.py             # Configuration management
├── dense/
│   ├── __init__.py
│   ├── bge_m3.py            # BGE-M3 dense evaluator
│   ├── jina_v3.py           # Jina v3 evaluator
│   └── custom.py            # Custom dense models
├── sparse/
│   ├── __init__.py
│   ├── bm25.py              # BM25 evaluator
│   └── bge_m3_sparse.py     # BGE-M3 sparse evaluator
├── hybrid/
│   ├── __init__.py
│   └── bge_m3_hybrid.py     # BGE-M3 hybrid evaluator
├── reranking/
│   ├── __init__.py
│   ├── base_reranker.py     # Base reranker class
│   └── cross_encoder.py     # Cross-encoder reranker
├── comprehensive_evaluator.py  # Main evaluator
├── run_comprehensive_evaluation.py  # Main script
├── test_evaluation.py       # Test script
└── README.md               # This file
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**: Reduce `batch_size` in configuration or use CPU
2. **Model Loading Errors**: Check `trust_remote_code` setting and model ID
3. **Slow Evaluation**: Reduce `max_queries` for testing or increase `batch_size`

### Logging

The system uses Python's logging module. Set log level in configuration:

```yaml
performance:
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

Logs are written to both console and `evaluation.log` file.

## Contributing

To add new retrieval methods:

1. Create a new evaluator class inheriting from `BaseEvaluator`
2. Implement the `_retrieve` method
3. Add the method to the appropriate module (`dense/`, `sparse/`, `hybrid/`, `reranking/`)
4. Update the `ComprehensiveEvaluator` to support the new method
5. Add configuration options if needed

## License

This evaluation system is part of the Aicacia project.

