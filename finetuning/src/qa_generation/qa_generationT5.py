"""
Generate synthetic questions from a corpus using T5-based query generation.
"""

import os
import sys
import json
import yaml
import logging
import math
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from beir.datasets.data_loader import GenericDataLoader
from .gpl import (
    qgen,
    NegativeMiner,
    set_logger_format,
    resize,
)

set_logger_format()
logger = logging.getLogger("GenerateQAT5")


@dataclass
class GenerateQAT5Config:
    """Configuration for T5-based question generation."""
    
    # Required paths
    corpus_path: str
    output_dir: str
    
    # Query generation parameters
    qgen_prefix: str = "qgen"
    generator: str = "BeIR/query-gen-msmarco-t5-base-v1"
    queries_per_passage: int = -1  # -1 = auto-adjust based on corpus size
    batch_size_generation: int = 32
    
    # Negative mining parameters
    mine_negatives : bool = True
    retrievers: List[str] = None
    retriever_score_functions: List[str] = None
    negatives_per_query: int = 50
    
    # Corpus resizing
    new_size: Optional[int] = None  # None = no resize, -1 = auto
    
    def __post_init__(self):
        """Set defaults for list fields."""
        if self.retrievers is None:
            self.retrievers = ["msmarco-distilbert-base-v3", "msmarco-MiniLM-L-6-v3"]
        if self.retriever_score_functions is None:
            self.retriever_score_functions = ["cos_sim", "cos_sim"]
        
        # Validate
        if len(self.retrievers) != len(self.retriever_score_functions):
            raise ValueError(
                f"Number of retrievers ({len(self.retrievers)}) must match "
                f"number of score functions ({len(self.retriever_score_functions)})"
            )
        
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "GenerateQAT5Config":
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)
    
    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)


class GenerateQAT5:
    """
    T5-based question generation pipeline for information retrieval.
    
    Pipeline steps:
    1. Load/prepare corpus
    2. Generate synthetic queries using T5
    3. Mine hard negatives using retrievers
    4. Save results and metadata
    """
    
    def __init__(self, config: GenerateQAT5Config):
        """
        Initialize the question generator.
        
        Args:
            config: Configuration object with all parameters
        """
        self.config = config
        self.corpus: Optional[Dict] = None
        self.queries: Optional[Dict] = None
        self.qrels: Optional[Dict] = None
        
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        logger.info("="*60)
        logger.info("Initialized GenerateQAT5")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info("="*60)
    
    def load_or_prepare_corpus(self) -> Dict:
        """
        Load corpus from path and optionally resize it.
        
        Returns:
            corpus: Dictionary of doc_id -> document content
        """
        logger.info("Step 1: Loading/preparing corpus")
        
        corpus_dest = os.path.join(self.config.output_dir, "corpus.jsonl")
        
        # Handle corpus path
        if os.path.isfile(self.config.corpus_path) and self.config.corpus_path.endswith('.jsonl'):
            logger.info(f"Copying corpus from {self.config.corpus_path}")
            shutil.copy(self.config.corpus_path, corpus_dest)
            
        elif os.path.isdir(self.config.corpus_path):
            corpus_file = os.path.join(self.config.corpus_path, "corpus.jsonl")
            
            if not os.path.exists(corpus_file):
                raise FileNotFoundError(f"No corpus.jsonl found in {self.config.corpus_path}")
            
            # Copy or resize
            if self.config.new_size is not None:
                new_size = self.config.new_size
                if new_size == -1:
                    new_size = math.ceil(250e3 / 3)
                    logger.info(f"Auto-adjusting corpus size to {new_size}")
                
                logger.info(f"Resizing corpus to {new_size} passages")
                resize(self.config.corpus_path, self.config.output_dir, new_size, self.config.use_train_qrels)
            else:
                shutil.copy(corpus_file, corpus_dest)
        else:
            raise ValueError(f"Invalid corpus_path: {self.config.corpus_path}")
        
        # Load corpus
        self.corpus = GenericDataLoader(self.config.output_dir).load_corpus()
        logger.info(f"Loaded corpus with {len(self.corpus)} passages")
        
        return self.corpus
    
    def generate_queries(self) -> tuple[Dict, Dict]:
        """
        Generate synthetic queries from corpus using T5.
        
        Returns:
            (queries, qrels): Generated queries and query-relevance judgments
        """
        logger.info("Step 2: Generating queries")
        
        if self.corpus is None:
            raise ValueError("Corpus must be loaded before generating queries")
        
        # Check if already generated
        qrels_path = os.path.join(self.config.output_dir, f"{self.config.qgen_prefix}-qrels")
        queries_path = os.path.join(self.config.output_dir, f"{self.config.qgen_prefix}-queries.jsonl")
        
            
        if os.path.exists(qrels_path) and os.path.exists(queries_path):
            logger.info("Loading existing generated queries")
            corpus, self.queries, self.qrels = GenericDataLoader(
                self.config.output_dir, 
                prefix=self.config.qgen_prefix
            ).load(split="train")
            
        else:
            logger.info(f"Generating {self.config.queries_per_passage} queries per passage")
            logger.info(f"Using generator: {self.config.generator}")
            
            qgen(
                self.config.output_dir,
                self.config.output_dir,
                generator_name_or_path=self.config.generator,
                ques_per_passage=self.config.queries_per_passage,
                bsz=self.config.batch_size_generation,
                qgen_prefix=self.config.qgen_prefix,
            )
            
            corpus, self.queries, self.qrels = GenericDataLoader(
                self.config.output_dir,
                prefix=self.config.qgen_prefix
            ).load(split="train")
        
        logger.info(f"Generated {len(self.queries)} queries")
        return self.queries, self.qrels
    
    def mine_hard_negatives(self):
        """
        Mine hard negatives using specified retrievers.
        """
        logger.info("Step 3: Mining hard negatives")
        
        if self.queries is None:
            raise ValueError("Queries must be generated before mining negatives")
        
        negatives_path = os.path.join(self.config.output_dir, "hard-negatives.jsonl")
        
        if os.path.exists(negatives_path):
            logger.info("Using existing hard-negative data")
            return
        
        logger.info(f"Mining {self.config.negatives_per_query} negatives per query")
        logger.info(f"Using retrievers: {self.config.retrievers}")
        
        miner = NegativeMiner(
            self.config.output_dir,
            self.config.qgen_prefix,
            retrievers=self.config.retrievers,
            retriever_score_functions=self.config.retriever_score_functions,
            nneg=self.config.negatives_per_query
        )
        miner.run()
        
        logger.info("Hard negatives mined successfully")
    
    def save_metadata(self) -> Dict[str, Any]:
        """
        Save generation metadata to JSON file.
        
        Returns:
            metadata: Dictionary with generation statistics
        """
        logger.info("Step 4: Saving metadata")
        
        metadata = {
            "config": asdict(self.config),
            "statistics": {
                "corpus_size": len(self.corpus) if self.corpus else 0,
                "num_queries": len(self.queries) if self.queries else 0,
                "queries_per_passage_actual": (
                    len(self.queries) / len(self.corpus) 
                    if self.corpus and self.queries and len(self.corpus) > 0 
                    else 0
                ),
            },
            "output_files": {
                "corpus": "corpus.jsonl",
                "queries": f"{self.config.qgen_prefix}-queries.jsonl",
                "qrels": f"{self.config.qgen_prefix}-qrels/train.tsv",
                "hard_negatives": "hard-negatives.jsonl",
            }
        }
        
        metadata_path = os.path.join(self.config.output_dir, "generation_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Metadata saved to {metadata_path}")
        return metadata
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete question generation pipeline.
        
        Returns:
            results: Dictionary with corpus, queries, qrels, and metadata
        """
        logger.info("\n" + "="*60)
        logger.info("Starting Question Generation Pipeline")
        logger.info("="*60 + "\n")
        
        try:
            # Step 1: Load corpus
            self.load_or_prepare_corpus()
            
            # Step 2: Generate queries
            self.generate_queries()
            
            if self.config.mine_negatives:
                # Step 3: Mine hard negatives
                self.mine_hard_negatives()
            
            # Step 4: Save metadata
            metadata = self.save_metadata()
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("Pipeline Complete!")
            logger.info("="*60)
            logger.info(f"Output directory: {self.config.output_dir}")
            logger.info(f"Corpus size: {len(self.corpus)}")
            logger.info(f"Queries generated: {len(self.queries)}")
            logger.info(f"Avg queries/passage: {len(self.queries)/len(self.corpus):.2f}")
            logger.info("="*60 + "\n")
            
            return {
                "corpus": self.corpus,
                "queries": self.queries,
                "qrels": self.qrels,
                "metadata": metadata,
                "output_dir": self.config.output_dir
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise


