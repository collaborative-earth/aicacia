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

Config (config.yaml)
```yaml
bucket_name: "my-bucket"
prefix: "dataset/xml_files"
generate_kg: false  # Set true for KG
```

## Generate Questions

### From Corpus (T5)
Using a T5 model.
```bash
python generate_qa_t5.py --config config.yaml

#Output: BEIR format with hard negatives. Multiple files with queries, corpus, qrels, hn.
```

### From Knowledge Graph (RAGAS)
Generate RAGAS-style testset with question, reference and answers from a knowledge graph.

```bash
python testdata_from_kg.py \
  --kg_path kg.json \
  --output_prefix output/testset \
  --num_queries 50 \
  --convert_to_llamaindex

#Output: RAGAS jsonl + LlamaIndex json
```

### Datasets conversion 
Convert dataset between one format and the other. Remarkably, from llama index/beir to bge for finetuning.

**LlamaIndex → BEIR**
```bash
python llama2beir.py --input data.json --output_dir beir/
```
** Mine HN **

EIR → BGE-M3
```bash
python beir2bgem3.py --beir_dir beir/ --output train.jsonl
```

---

## Complete Pipeline: LlamaIndex → BGE-M3

```bash
# 1. Convert to BEIR
python llama2beir.py --input llama.json --output_dir beir/

# 2. Mine hard negatives
python generate_qa_t5.py \
  --corpus_path beir/ \
  --output_dir beir/\

# 3. Convert to BGE-M3 training format
python beir2bgem.py --beir_dir beir/ --output bge.jsonl
```

---

## Formats

**BEIR:** `corpus.jsonl`, `qgen-queries.jsonl`, `qgen-qrels/train.tsv`, `hard-negatives.jsonl`

**LlamaIndex:** `{"queries": {}, "corpus": {}, "relevant_docs": {}}`

**BGE-M3:** `{"query": str, "pos": [str], "neg": [str], "pos_scores": [], "neg_scores": [], "prompt": str, "type": str}`
