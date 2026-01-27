import os
import yaml
import json
import uuid
from typing import Dict, List, Optional, Any, Sequence
from pathlib import Path
from dataclasses import dataclass, field

from llama_index.core.schema import TextNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from ragas.testset.graph import KnowledgeGraph, Node, NodeType
from ragas.testset.transforms import apply_transforms
from ragas.testset.transforms.extractors import EmbeddingExtractor
from ragas.embeddings.huggingface_provider import HuggingFaceEmbeddings
from ragas.testset.transforms.extractors.llm_based import ThemesExtractor
from ragas.testset.transforms.relationship_builders import CosineSimilarityBuilder
from ragas.run_config import RunConfig


@dataclass
class CorpusConfig:
    """Unified configuration for corpus generation and optional KG building."""
    
    # S3 Configuration (optional - can work with pre-loaded documents/nodes)
    bucket_name: Optional[str] = None
    prefix: Optional[str] = None
    aws_key: Optional[str] = None
    aws_secret: Optional[str] = None
    
    # Processing Configuration
    chunk_size: int = 256
    chunk_overlap: int = 40
    paragraph_separator: str = "\n\n"
    min_len: int = 50
    max_nodes: Optional[int] = None
    
    # Output Configuration
    output_dir: str = "data/corpus"
    auto_version: bool = False
    
    # Filtering Configuration
    apply_filter: bool = False
    valid_tags: Optional[List[str]] = None
    
    # Knowledge Graph Configuration
    generate_kg: bool = False
    kg_output_dir: str = "kg"
    
    # KG: Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # KG: Relationship Building Configuration
    cosine_threshold: float = 0.7
    overlap_threshold: float = 0.24
    distance_threshold: float = 0.9
    
    # KG: LLM Configuration
    llm_provider: str = "openai"
    openai_async: bool = False
    llm_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    
    # KG: Pipeline Configuration
    use_ecocontext_extractor: bool = True
    use_themes_extractor: bool = True
    use_embedding_extractor: bool = True
    use_cosine_similarity: bool = True
    use_ecocontext_overlap: bool = True
    synonym_score_cutoff: int = 90
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'CorpusConfig':
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Load secrets from environment if not in YAML
        if 'aws_key' not in config_dict or not config_dict['aws_key']:
            config_dict['aws_key'] = os.getenv('AWS_KEY')
        if 'aws_secret' not in config_dict or not config_dict['aws_secret']:
            config_dict['aws_secret'] = os.getenv('AWS_SECRET')
        if 'openai_api_key' not in config_dict or not config_dict['openai_api_key']:
            config_dict['openai_api_key'] = os.getenv('OPENAI_API_KEY')
        
        return cls(**config_dict)
    
    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file (excluding secrets)."""
        config_dict = self.__dict__.copy()
        # Don't save secrets to file
        config_dict['aws_key'] = None
        config_dict['aws_secret'] = None
        config_dict['openai_api_key'] = None
        
        with open(yaml_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)


class CorpusGenerator:
    """
    Unified class for corpus generation with optional knowledge graph building.
    
    Can work with:
    - S3 data (download and process)
    - Pre-loaded documents
    - Pre-loaded nodes
    
    Always produces: corpus_xx.jsonl
    Optionally produces: kg_xx.json (if generate_kg=True)
    """
    
    def __init__(self, config: CorpusConfig):
        """
        Initialize corpus generator with configuration.
        
        Args:
            config: CorpusConfig object containing all parameters
        """
        self.config = config
        self.kg: Optional[KnowledgeGraph] = None
        self.llm = None
        
        if self.config.generate_kg:
            self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM for knowledge graph generation."""
        if self.config.llm_provider == "openai":
            from ragas.llms import llm_factory
            if self.config.openai_async:
                from openai import AsyncOpenAI
                openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
            else:
                from openai import OpenAI
                openai_client = OpenAI(api_key=self.config.openai_api_key)
            self.llm = llm_factory(self.config.llm_model, provider="openai", client=openai_client)
    
    def _get_dataset_name(self) -> str:
        """Extract dataset name from prefix."""
        if self.config.prefix:
            return self.config.prefix.split('/')[0]
        return "default"
    
    def _generate_corpus_path(self, output_dir: Optional[str] = None) -> str:
        """Generate output path for corpus JSONL file."""
        out_dir = Path(output_dir or self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        dataset_name = self._get_dataset_name()
        
        if not self.config.auto_version:
            return str(out_dir / f"corpus_{dataset_name}.jsonl")
        
        # Find next version number
        version = 1
        while True:
            path = out_dir / f"corpus_{dataset_name}_v{version}.jsonl"
            if not path.exists():
                return str(path)
            version += 1
    
    def _generate_kg_path(self) -> str:
        """Generate output path for knowledge graph JSON file."""
        output_dir = Path(self.config.kg_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset_name = self._get_dataset_name()
        base_name = f"kg_{dataset_name}"
        
        if not self.config.auto_version:
            return str(output_dir / f"{base_name}.json")
        
        # Find next version number
        version = 1
        while True:
            path = output_dir / f"{base_name}_v{version}.json"
            if not path.exists():
                return str(path)
            version += 1
    
    def load_from_s3(self):
        """Load documents from S3."""
        if not self.config.bucket_name or not self.config.prefix:
            raise ValueError("bucket_name and prefix must be set in config to download from S3.")
        
        from data_io.custom_readers import S3ReaderBase
        
        print(f"Downloading from S3: {self.config.bucket_name}/{self.config.prefix}")
        reader = S3ReaderBase(
            bucket_name=self.config.bucket_name,
            aws_key=self.config.aws_key,
            aws_secret=self.config.aws_secret,
            prefix=self.config.prefix
        )
        documents = reader.load_documents()
        print(f"Downloaded {len(documents)} documents")
        return documents
    
    def parse_documents(self, documents):
        """Parse documents using TEI parser."""
        from data_io.custom_parsers import TEINodeParser
        
        parser = TEINodeParser()
        return parser.get_nodes_from_documents(documents)
    
    def process_documents(self, documents: Sequence) -> Sequence[TextNode]:
        """Process raw documents into TextNodes with optional filtering."""
        from data_io.custom_parsers import TEINodeParser
        
        parser = TEINodeParser()
        splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            paragraph_separator=self.config.paragraph_separator,
        )
        
        # Optional filtering
        node_filter = None
        if self.config.apply_filter and self.config.valid_tags:
            from data_io.custom_parsers import TEINodeFilter
            node_filter = TEINodeFilter(valid_tags=self.config.valid_tags, reverse=False)
        
        # First pipeline: parse and optionally filter
        transformations = [parser]
        if node_filter:
            transformations.append(node_filter)
        pipeline = IngestionPipeline(transformations=transformations)
        nodes = pipeline.run(documents=documents, show_progress=True)
        
        # HACK: Fix tag metadata
        for n in nodes:
            tag = n.metadata.get("tag")
            if isinstance(tag, str) and len(tag) > 100:
                n.metadata["tag"] = tag.split("\n", 1)[0][:50]
        
        # Second pipeline: split
        pipeline2 = IngestionPipeline(transformations=[splitter])
        nodes = pipeline2.run(documents=nodes, show_progress=True)
        
        # Filter by minimum length
        if self.config.min_len:
            print(f"Filtering nodes with length < {self.config.min_len}")
            nodes = [node for node in nodes if len(node.get_text()) >= self.config.min_len]
        
        print(f"Created {len(nodes)} nodes from {len(documents)} documents")
        return nodes
    
    def save_corpus_jsonl(self, nodes: Sequence[TextNode], output_path: Optional[str] = None) -> str:
        """Save nodes to a BEIR-compatible JSONL file."""
        corpus_path = output_path or self._generate_corpus_path()
        
        with open(corpus_path, "w", encoding="utf-8") as f:
            for node in nodes:
                doc = {
                    "_id": node.id_,
                    "title": node.metadata.get("title", ""),
                    "text": node.get_text(),
                }
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        
        print(f"Corpus saved: {corpus_path}")
        return str(corpus_path)
    
    def create_ragas_nodes(self, nodes: Sequence[TextNode]) -> List[Node]:
        """Convert LlamaIndex nodes to RAGAS nodes for KG."""
        ragas_nodes = [
            Node(
                type=NodeType.DOCUMENT,
                id=node.id_,
                properties={
                    "page_content": node.text,
                    "document_metadata": node.metadata,
                },
            )
            for node in nodes
            if len(node.text.strip()) >= self.config.min_len
        ]
        
        if self.config.max_nodes is not None:
            ragas_nodes = ragas_nodes[:self.config.max_nodes]
        
        return ragas_nodes
    
    def repair_ecocontext_nodes(self):
        """Repair and enhance ecocontext fields in KG nodes."""
        from ragas_ext import build_ecocontext_sets, merge_synonyms, repair_node_ecocontext
        
        vocab_sets = build_ecocontext_sets(self.kg)
        
        for key in vocab_sets:
            vocab_sets[key] = merge_synonyms(
                vocab_sets[key],
                score_cutoff=self.config.synonym_score_cutoff
            )
        
        for node in self.kg.nodes:
            content = node.properties.get("page_content", "")
            node.properties["ecocontext"] = repair_node_ecocontext(node, vocab_sets)
    
    def build_kg_transforms(self) -> List:
        """Build transformation pipeline for knowledge graph."""
        transforms = []
        
        if self.config.use_themes_extractor:
            te = ThemesExtractor(llm=self.llm, property_name="themes", max_num_themes=5)
            transforms.append(te)
        
        if self.config.use_embedding_extractor:
            embedding_model = HuggingFaceEmbeddings(
                model=self.config.embedding_model
            )
            emb_extractor = EmbeddingExtractor(
                embedding_model=embedding_model,
                property_name="embedding",
                embed_property_name="page_content"
            )
            transforms.append(emb_extractor)
        
        if self.config.use_cosine_similarity:
            cosine_sim_builder = CosineSimilarityBuilder(
                property_name="embedding",
                new_property_name="cosine_sim",
                threshold=self.config.cosine_threshold
            )
            transforms.append(cosine_sim_builder)
        
        if self.config.use_ecocontext_overlap:
            from ragas_ext import EcoContextOverlapBuilder
            
            rels = EcoContextOverlapBuilder(
                property_name="ecocontext",
                new_property_name="overlap_score",
                threshold=self.config.overlap_threshold,
                distance_threshold=self.config.distance_threshold,
            )
            transforms.append(rels)
        
        return transforms
    
    def build_knowledge_graph(self, nodes: Sequence[TextNode]) -> KnowledgeGraph:
        """Build knowledge graph from nodes."""
        print("Creating RAGAS nodes for knowledge graph...")
        ragas_nodes = self.create_ragas_nodes(nodes)
        
        print("Initializing knowledge graph...")
        self.kg = KnowledgeGraph(nodes=ragas_nodes)
        
        if self.config.use_ecocontext_extractor:
            print("Extracting context...")
            from ragas_ext import ContextExtractor
            ce = ContextExtractor(llm=self.llm)
            apply_transforms(self.kg, transforms=[ce], run_config=RunConfig(max_workers=2))
            
            print("Repairing ecocontext nodes...")
            self.repair_ecocontext_nodes()
        
        print("Building and applying transforms...")
        transforms = self.build_kg_transforms()
        apply_transforms(self.kg, transforms=transforms, run_config=RunConfig(max_workers=2))
        
        print(f"Knowledge graph created: {len(self.kg.nodes)} nodes, {len(self.kg.relationships)} edges")
        
        return self.kg
    
    def save_knowledge_graph(self, output_path: Optional[str] = None) -> str:
        """Save knowledge graph to disk."""
        if self.kg is None:
            raise ValueError("No knowledge graph to save.")
        
        kg_path = output_path or self._generate_kg_path()
        self.kg.save(kg_path)
        print(f"Knowledge graph saved: {kg_path}")
        return kg_path
    
    def generate_corpus(
        self,
        documents: Optional[Sequence] = None,
        nodes: Optional[Sequence[TextNode]] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        High-level interface to generate corpus and optionally knowledge graph.
        
        Args:
            documents: Optional pre-loaded documents (if not provided, loads from S3)
            nodes: Optional pre-loaded nodes (skips document processing)
            output_dir: Optional output directory for corpus
        
        Returns:
            Dict with paths to generated files:
                - 'corpus': path to corpus JSONL file
                - 'kg': path to knowledge graph JSON file (if generate_kg=True)
        """
        results = {}
        
        # Get or create nodes
        if nodes is not None:
            print("Using provided nodes...")
            final_nodes = nodes
        elif documents is not None:
            print("Processing provided documents...")
            final_nodes = self.process_documents(documents)
        else:
            print("Loading documents from S3...")
            documents = self.load_from_s3()
            print("Processing documents...")
            final_nodes = self.process_documents(documents)
        
        # Save corpus
        corpus_path = self.save_corpus_jsonl(final_nodes, output_path=None)
        results['corpus'] = corpus_path
        
        # Optionally build and save knowledge graph
        if self.config.generate_kg:
            print("\nBuilding knowledge graph...")
            self.build_knowledge_graph(final_nodes)
            kg_path = self.save_knowledge_graph()
            results['kg'] = kg_path
        
        print("\n=== Generation Complete ===")
        print(f"Corpus: {results['corpus']}")
        if 'kg' in results:
            print(f"Knowledge Graph: {results['kg']}")
        print("===========================\n")
        
        return results


# Convenience function for simple usage
def generate_corpus_from_config(config_path: str) -> Dict[str, str]:
    """
    Generate corpus (and optionally KG) from a YAML config file.
    
    Args:
        config_path: Path to YAML configuration file
    
    Returns:
        Dict with paths to generated files
    """
    config = CorpusConfig.from_yaml(config_path)
    generator = CorpusGenerator(config)
    return generator.generate_corpus()