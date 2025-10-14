# `data_io` Module

`data_io` provides **reusable utilities for reading documents from S3 and parsing them into structured nodes** for downstream pipelines such as LlamaIndex embeddings, retrieval, or fine-tuning.

It is independent of task-specific logic and focuses purely on **data access and transformation**.


##  Folder Structure

```text
data_io/
├── __init__.py
├── s3_reader.py
├── pdf_lajson_parser.py
└── tei_parser.py
```


## Responsibilities

- **S3Reader (`s3_reader.py`)**  
  - Connects to an S3 bucket using AWS credentials.  
  - Lists and loads documents under a specified prefix.  
  - Returns raw llama-index document content for downstream parsing.

- **Node Parsers**  
  - Convert raw documents into `LlamaIndex` `Node`s.  Depend on the specific of files in S3
  - Handle optional chunking, metadata extraction, and post-processing.  
  - Can be extended for additional document formats or parsing logic.

---

## Dependencies

- External libraries:
  - `boto3` for S3 access
  - `llama_index` for Node and Document abstractions
- Internal modules:
  - `data_ingest` for optional postprocessing utilities
  - `extraction` for TEI document representation

---

## Usage Example

```python
from data_io.s3_reader import S3ReaderBase
from data_io.pdf_lajson_parser import PDFLAJSONNodeParser
from data_io.tei_parser import TEINodeParser

BUCKET_NAME = ***

# Load WRI documents from S3 and parse
wri_docs = S3ReaderBase(
    bucket_name=BUCKET_NAME,
    aws_key=***,
    aws_secret=***,
    prefix="wri/postprocess_output"
).load_documents()
wri_chunks = PDFLAJSONNodeParser().get_nodes_from_documents(wri_docs)

# Load AER TEI documents from S3 and parse
aer_docs = S3ReaderBase(
    bucket_name=BUCKET_NAME,
    aws_key=***,
    aws_secret=***,
    prefix="aer/tei_output_2"
).load_documents()
aer_chunks = TEINodeParser().get_nodes_from_documents(aer_docs)
```
## Data Pipeline 
```python
(Before: raw documents -> .json or .tei.xml files in S3)
S3 Bucket
   │
   ▼
S3ReaderBase  --> raw documents
   │
   ▼
Node Parsers (PDFLAJSONNodeParser / TEINodeParser)
   │
   ▼
LlamaIndex Nodes
   │
   ▼
Downstream pipelines (embeddings, vector DB, fine-tuning)