# Dataset generation
Classes and functions for generating testsets.

## CorpusGenerator

Unified class for generating text corpora and optional knowledge graphs from S3 or local data.
Default pipeline:
1. Download documents from S3 and convert them into llama-index documents
2. Parse them using TEINodeParser and split into nodes. Save the results as BEIR corpus
3. Optionally generate knowledge graph RAGAS-style

Note that 

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