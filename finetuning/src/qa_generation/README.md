# Dataset generation

Classes and functions for generating testsets of questions and answers for finetuning and evaluation.

## CorpusGenerator

Unified class for generating text corpora and optional knowledge graphs from S3 or local data.
Default pipeline:
1. Download documents from S3 and convert them into llama-index documents
2. Parse them using TEINodeParser and split into nodes. Save the results as BEIR corpus
3. Optionally generate knowledge graph RAGAS-style

Note that,
**Output**: Always `corpus_xx.jsonl` (BEIR format), optionally `kg_xx.json` (knowledge graph, ragas compatible)

## Usage
```python
from corpus_generator import CorpusGenerator, CorpusConfig

# Corpus only
config = CorpusConfig(
    bucket_name="my-bucket",
    prefix="dataset/xml_files",
    output_dir="data/corpus",
    generate_kg=False  # Just corpus
)

generator = CorpusGenerator(config)
results = generator.generate_corpus()
# → {'corpus': 'data/corpus/corpus_dataset.jsonl'}

# Corpus + Knowledge Graph
config.generate_kg = True
results = generator.generate_corpus()
# → {'corpus': '...corpus_dataset.jsonl', 'kg': 'kg/kg_dataset.json'}

# From YAML config
from corpus_generator import generate_corpus_from_config
results = generate_corpus_from_config("config.yaml")
```

## Config (config.yaml)
```yaml
bucket_name: "my-bucket"
prefix: "dataset/xml_files"
generate_kg: false  # Set true for KG
```

## Question Generation 

### From knowledge graph

Generate synthetic test queries from a knowledge graph using RAGAS with custom personas and scenarios.

python testdata_from_kg.py \
  --kg_path kg/kg_dataset.json \
  --output_prefix output/testset \
  --num_queries 50 \
  --llm_model gpt-4o

Parameters:
- `--kg_path`: Path to knowledge graph JSON file (required)
- `--output_prefix`: Prefix for output files (required)
- `--num_queries`: Number of queries to generate (default: 30)
- `--llm_model`: LLM model to use (default: gpt-3.5-turbo)
- `--llm_provider`: LLM provider (default: openai)
- `--batch_size`: Batch size for generation (default: 32)
- `--convert_to_llamaindex`: Flag to also generate LlamaIndex format

Output files:

- `{prefix}_metadata.json`: Generation metadata (cost, parameters, etc.)
- `{prefix}_testset.jsonl`: RAGAS format testset: jsonl with entries
    * user_inoput
    * reference_context
- `{prefix}_testset_llama.json`: LlamaIndex form. A dict of 
    * `queries`: Dictionary of query_id → query_text
    * `relevant_docs`: Dictionary of query_id → list of relevant document IDs
    * `corpus`: Dictionary of doc_id → document text
