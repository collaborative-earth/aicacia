from pathlib import Path
from typing import Optional, List, Sequence
from dataclasses import dataclass
import yaml
import json
import os

from llama_index.core.schema import TextNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline

from data_io.custom_readers import S3ReaderBase
from data_io.custom_parsers import TEINodeParser


@dataclass
class DataLoaderConfig:
    bucket_name: Optional[str] = None
    prefix: Optional[str] = None
    aws_key: Optional[str] = None
    aws_secret: Optional[str] = None

    chunk_size: int = 256
    chunk_overlap: int = 40
    min_len: Optional[int] = 50
    
    output_dir: str = "data/corpus"

    apply_filter: bool = False
    valid_tags: Optional[List[str]] = None
    
    

    @classmethod
    def from_yaml(cls, yaml_path: str):
        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)
        # Load secrets from environment if not in YAML
        if 'aws_key' not in config_dict or not config_dict['aws_key']:
            config_dict['aws_key'] = os.getenv('AWS_KEY')
        if 'aws_secret' not in config_dict or not config_dict['aws_secret']:
            config_dict['aws_secret'] = os.getenv('AWS_SECRET')
        return cls(**config_dict)

class S3CorpusLoader:
    """Download/process from S3 or handle pre-loaded nodes, saving to BEIR JSONL."""

    def __init__(self, config: DataLoaderConfig):
        self.config = config

    def save_nodes_to_jsonl(self, nodes: Sequence[TextNode], output_dir: Optional[str] = None) -> str:
        """Save nodes to a BEIR-compatible JSONL file."""
        out_dir = Path(output_dir or self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        dataset_name = self.config.prefix.split('/')[0]
        corpus_path = out_dir / f"corpus_{dataset_name}.jsonl"

        with open(corpus_path, "w", encoding="utf-8") as f:
            for node in nodes:
                doc = {
                    "_id": node.id_,
                    "title": node.metadata.get("title", ""),
                    "text": node.get_text(),
                }
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        return str(corpus_path)

    def download_and_process(self) -> Sequence[TextNode]:
        """Download from S3 and return nodes."""
        if not self.config.bucket_name or not self.config.prefix:
            raise ValueError("bucket_name and prefix must be set in config to download from S3.")

        print(f"Downloading from S3: {self.config.bucket_name}/{self.config.prefix}")
        reader = S3ReaderBase(
            bucket_name=self.config.bucket_name,
            aws_key=self.config.aws_key,
            aws_secret=self.config.aws_secret,
            prefix=self.config.prefix,
        )
        documents = reader.load_documents()
        print(f"Downloaded {len(documents)} documents")

        nodes = self.process_documents(documents)
        return nodes

    def process_documents(self, documents: Sequence) -> Sequence[TextNode]:
        """Process raw documents (from S3 or local) into TextNodes."""
        parser = TEINodeParser()
        splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            paragraph_separator=self.config.paragraph_separator if hasattr(self.config, 'paragraph_separator') else "\n\n",
        )

        # Optional filtering
        node_filter = None
        if self.config.apply_filter and self.config.valid_tags:
            from data_io.custom_parsers import TEINodeFilter
            node_filter = TEINodeFilter(valid_tags=self.config.valid_tags, reverse=False)

        transformations = [parser]
        if node_filter:
            transformations.append(node_filter)
        pipeline = IngestionPipeline(transformations=transformations)
        nodes = pipeline.run(documents=documents, show_progress=True)
        # TERRIBLE HACK MUST BE FIXED AT THE LEVEL OF PARSING
        for n in nodes:
            tag = n.metadata.get("tag")
            if isinstance(tag, str) and len(tag) > 100:
                # keep only first line / label
                n.metadata["tag"] = tag.split("\n", 1)[0][:50]
                
        transformations2 = [splitter]
        pipeline2 = IngestionPipeline(transformations=transformations2)
        nodes = pipeline2.run(documents=nodes, show_progress=True)
        if self.config.min_len:
            print(f"Filtering nodes with length < {self.config.min_len}")
            nodes = [node for node in nodes if len(node.get_text()) >= self.config.min_len]
        print(f"Created {len(nodes)} nodes from {len(documents)} documents")
        return nodes

    def generate_corpus(self, documents: Optional[Sequence] = None, nodes: Optional[Sequence[TextNode]] = None,
                        output_dir: Optional[str] = None) -> str:
        """
        High-level interface:
        - If nodes are provided, save them.
        - Else if documents are provided, process and save.
        - Else download from S3, process, and save.
        """
        if nodes is not None:
            nodes_to_save = nodes
        elif documents is not None:
            nodes_to_save = self.process_documents(documents)
        else:
            nodes_to_save = self.download_and_process()

        path = self.save_nodes_to_jsonl(nodes_to_save, output_dir=output_dir)
        print(f"Corpus saved: {path}")
        return path