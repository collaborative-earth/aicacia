import os
import yaml
import json
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

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
class KGConfig:
    """Configuration for Knowledge Graph generation from S3."""
    
    # S3 Configuration
    bucket_name: str
    prefix: str
    aws_key: Optional[str] = None
    aws_secret: Optional[str] = None
    
    # Processing Configuration
    chunk_size: int = 256
    chunk_overlap: int = 40
    paragraph_separator: str = "\n\n"
    min_content_length: int = 50
    max_nodes: Optional[int] = None
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Relationship Building Configuration
    cosine_threshold: float = 0.7
    overlap_threshold: float = 0.24
    distance_threshold: float = 0.9
    
    # Output Configuration
    output_path: Optional[str] = None
    auto_version: bool = True
    
    # LLM Configuration
    llm_provider: str = "openai"  # or "anthropic", etc.
    openai_async: bool = False
    llm_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    
    # Pipeline Configuration
    use_ecocontext_extractor: bool = True
    use_themes_extractor: bool = True
    use_embedding_extractor: bool = True
    use_cosine_similarity: bool = True
    use_ecocontext_overlap: bool = True
    synonym_score_cutoff: int = 90
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'KGConfig':
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


class KG_fromS3:
    """Generate Knowledge Graph from S3 data with configurable pipeline."""
    
    def __init__(self, config: KGConfig):
        """
        Initialize KG generator with configuration.
        
        Args:
            config: KGConfig object containing all parameters
        """
        self.config = config
        self.kg: Optional[KnowledgeGraph] = None
        self._setup_llm()
        
    def _setup_llm(self):
        """Setup LLM based on configuration."""
        # This is a placeholder - adjust based on your actual LLM setup
        if self.config.llm_provider == "openai":
            from ragas.llms import llm_factory
            if self.config.openai_async:
                from openai import AsyncOpenAI
                openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
            else:
                from openai import OpenAI
                openai_client = OpenAI(api_key=self.config.openai_api_key)
            self.llm = llm_factory(self.config.llm_model, provider="openai", client=openai_client)
        
    def _generate_output_path(self) -> str:
        """Generate output path based on prefix and versioning."""
        if self.config.output_path and not self.config.auto_version:
            return self.config.output_path
        
        # Extract dataset name from prefix (e.g., "aer/tei_output_2" -> "kg_aer")
        dataset_name = self.config.prefix.split('/')[0]
        base_name = f"kg_{dataset_name}"
        
        # Create output directory
        output_dir = Path("kg")  # or whatever folder name you want
        output_dir.mkdir(exist_ok=True)  # Creates the folder if it doesn't exist
        
        if not self.config.auto_version:
            return str(output_dir / f"{base_name}.json")
        
        # Find next version number
        version = 1
        while True:
            path = output_dir / f"{base_name}_v{version}.json"
            if not path.exists():
                return str(path)
            version += 1
    
    def log_graph_info(self, label: str):
        """Log information about the knowledge graph."""
        if self.kg is None:
            print("No knowledge graph loaded")
            return
            
        print(f"\n=== {label} ===")
        print(f"Nodes: {len(self.kg.nodes)}")
        print(f"Edges: {len(self.kg.relationships)}")
        
        try:
            n_overlap = sum(
                1 for n in self.kg.nodes.values()
                if "overlap_score" in (n.properties or {})
            )
            print(f"Nodes with overlap_score: {n_overlap}")
        except Exception:
            pass
        print("=====================\n")
    
    def load_documents(self):
        """Load documents from S3."""
        from data_io.custom_readers import S3ReaderBase
        
        reader = S3ReaderBase(
            bucket_name=self.config.bucket_name,
            aws_key=self.config.aws_key,
            aws_secret=self.config.aws_secret,
            prefix=self.config.prefix
        )
        return reader.load_documents()
    
    def parse_documents(self, documents):
        """Parse documents into chunks."""
        from data_io.custom_parsers import TEINodeParser
        
        parser = TEINodeParser()
        return parser.get_nodes_from_documents(documents)
    
    def split_chunks(self, chunks):
        """Split chunks into smaller nodes."""
        splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            paragraph_separator=self.config.paragraph_separator
        )
        pipeline = IngestionPipeline(transformations=[splitter])
        return pipeline.run(documents=chunks, show_progress=True)
    
    def create_ragas_nodes(self, nodes) -> List[Node]:
        """Convert LlamaIndex nodes to RAGAS nodes."""
        ragas_nodes = [
            Node(
                type=NodeType.DOCUMENT,
                id=node.id_,
                properties={
                    "page_content": node.text,
                    "document_metadata": None,
                },
            )
            for node in nodes
            if len(node.text.strip()) >= self.config.min_content_length
        ]
        if getattr(self.config, "max_nodes", None) is not None:
            ragas_nodes = ragas_nodes[: self.config.max_nodes]

        return ragas_nodes
        
    
    def repair_ecocontext_nodes(self):
        """Repair and enhance ecocontext fields in nodes."""
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
        
    
    def build_transforms(self) -> List:
        """Build transformation pipeline based on configuration."""
        transforms = []
        
        if self.config.use_themes_extractor:
            te = ThemesExtractor(llm=self.llm, property_name="themes",max_num_themes=5)
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
    
    def generate(self) -> KnowledgeGraph:
        """
        Generate the knowledge graph from S3 data.
        
        Returns:
            KnowledgeGraph: The generated knowledge graph
        """
        if self.kg is None:
            print("Loading documents from S3...")
            documents = self.load_documents()
            
            print("Parsing documents...")
            chunks = self.parse_documents(documents)
            
            print("Splitting chunks...")
            nodes = self.split_chunks(chunks)
            
            print("Creating RAGAS nodes...")
            ragas_nodes = self.create_ragas_nodes(nodes)
            
            print("Initializing knowledge graph...")
            self.kg = KnowledgeGraph(nodes=ragas_nodes)
            
        if self.config.use_ecocontext_extractor:
            print("Extracting context...")
            from ragas_ext import ContextExtractor
            ce = ContextExtractor(llm=self.llm)
            apply_transforms(self.kg, transforms=[ce],run_config = RunConfig(max_workers=2))
    
            self.repair_ecocontext_nodes()
        
        print("Building and applying all other transforms...")
        transforms = self.build_transforms()
        apply_transforms(self.kg, transforms=transforms,run_config = RunConfig(max_workers=2))
        
        self.log_graph_info("KG after transforms")
        
        return self.kg
    
    def save_nodes_to_jsonl(self, output_dir: Optional[str] = None) -> str:
        """Save nodes to a BEIR-compatible JSONL file."""
        out_dir = Path(output_dir or self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        dataset_name = self.config.prefix.split('/')[0]
        corpus_path = out_dir / f"corpus_{dataset_name}.jsonl"
        def to_serializable(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return obj
        
        with open(corpus_path, "w", encoding="utf-8") as f:
            for node in self.kg.nodes:
                doc = {
                    "_id": to_serializable(node.id),
                    "title": "",
                    "text": node.properties.get("page_content", ""),
                }
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        return str(corpus_path)
    
    def save(self, output_path: Optional[str] = None):
        """
        Save the knowledge graph to disk.
        
        Args:
            output_path: Optional custom output path. If not provided, uses config.
        """
        if self.kg is None:
            raise ValueError("No knowledge graph to save. Run generate() first.")
        
        path = output_path or self._generate_output_path()
        self.kg.save(path)
        print(f"Saved knowledge graph to {path}")
        self.save_nodes_to_jsonl()
        return path
    
    def load(self, path: str):
        """Load an existing knowledge graph."""
        self.kg = KnowledgeGraph().load(path)
        self.log_graph_info("Loaded knowledge graph")
        return self.kg
    
    def generate_and_save(self) -> str:
        """
        Generate and save the knowledge graph in one step.
        
        Returns:
            str: Path where the graph was saved
        """
        self.generate()
        return self.save()