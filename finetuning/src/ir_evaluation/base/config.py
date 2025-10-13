"""
Configuration management for evaluation system.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    model_id: str
    trust_remote_code: bool = True
    device: Optional[str] = None
    batch_size: int = 32
    max_length: int = 512
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    """Main configuration for evaluation."""
    dataset_path: str
    max_queries: Optional[int] = None
    k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10, 20])
    
    # Model configurations
    dense_models: List[ModelConfig] = field(default_factory=list)
    sparse_models: List[ModelConfig] = field(default_factory=list)
    hybrid_models: List[ModelConfig] = field(default_factory=list)
    reranking_models: List[ModelConfig] = field(default_factory=list)
    
    # Output configuration
    results_dir: str = "results"
    save_embeddings: bool = False
    generate_plots: bool = True
    generate_report: bool = True
    
    # Performance configuration
    show_progress: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'EvaluationConfig':
        """Load configuration from YAML file."""
        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path_obj, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls._from_dict(config_data)
    
    @classmethod
    def _from_dict(cls, config_data: Dict[str, Any]) -> 'EvaluationConfig':
        """Create configuration from dictionary."""
        # Extract dataset configuration
        dataset_config = config_data.get('dataset', {})
        
        # Extract methods configuration
        methods_config = config_data.get('methods', {})
        
        # Extract output configuration
        output_config = config_data.get('output', {})
        
        # Extract performance configuration
        performance_config = config_data.get('performance', {})
        
        # Create model configurations
        dense_models = []
        for model_data in methods_config.get('dense', []):
            dense_models.append(ModelConfig(
                name=model_data['name'],
                model_id=model_data['model_id'],
                trust_remote_code=model_data.get('trust_remote_code', True),
                device=model_data.get('device'),
                batch_size=model_data.get('batch_size', 32),
                max_length=model_data.get('max_length', 512),
                additional_params=model_data.get('additional_params', {})
            ))
        
        sparse_models = []
        for model_data in methods_config.get('sparse', []):
            sparse_models.append(ModelConfig(
                name=model_data['name'],
                model_id=model_data.get('model_id', ''),
                trust_remote_code=model_data.get('trust_remote_code', True),
                device=model_data.get('device'),
                batch_size=model_data.get('batch_size', 32),
                max_length=model_data.get('max_length', 512),
                additional_params=model_data.get('additional_params', {})
            ))
        
        hybrid_models = []
        for model_data in methods_config.get('hybrid', []):
            hybrid_models.append(ModelConfig(
                name=model_data['name'],
                model_id=model_data['model_id'],
                trust_remote_code=model_data.get('trust_remote_code', True),
                device=model_data.get('device'),
                batch_size=model_data.get('batch_size', 32),
                max_length=model_data.get('max_length', 512),
                additional_params=model_data.get('additional_params', {})
            ))
        
        reranking_models = []
        for model_data in methods_config.get('reranking', []):
            reranking_models.append(ModelConfig(
                name=model_data['name'],
                model_id=model_data['model_id'],
                trust_remote_code=model_data.get('trust_remote_code', True),
                device=model_data.get('device'),
                batch_size=model_data.get('batch_size', 32),
                max_length=model_data.get('max_length', 512),
                additional_params=model_data.get('additional_params', {})
            ))
        
        return cls(
            dataset_path=dataset_config.get('path', 'data/qa_dataset/qa_finetune_dataset.json'),
            max_queries=dataset_config.get('max_queries'),
            k_values=config_data.get('metrics', {}).get('k_values', [1, 3, 5, 10, 20]),
            dense_models=dense_models,
            sparse_models=sparse_models,
            hybrid_models=hybrid_models,
            reranking_models=reranking_models,
            results_dir=output_config.get('results_dir', 'results'),
            save_embeddings=output_config.get('save_embeddings', False),
            generate_plots=output_config.get('generate_plots', True),
            generate_report=output_config.get('generate_report', True),
            show_progress=performance_config.get('show_progress', True),
            log_level=performance_config.get('log_level', 'INFO')
        )
    
    def to_yaml(self, output_path: str):
        """Save configuration to YAML file."""
        config_data = {
            'dataset': {
                'path': self.dataset_path,
                'max_queries': self.max_queries
            },
            'methods': {
                'dense': [
                    {
                        'name': model.name,
                        'model_id': model.model_id,
                        'trust_remote_code': model.trust_remote_code,
                        'device': model.device,
                        'batch_size': model.batch_size,
                        'max_length': model.max_length,
                        'additional_params': model.additional_params
                    }
                    for model in self.dense_models
                ],
                'sparse': [
                    {
                        'name': model.name,
                        'model_id': model.model_id,
                        'trust_remote_code': model.trust_remote_code,
                        'device': model.device,
                        'batch_size': model.batch_size,
                        'max_length': model.max_length,
                        'additional_params': model.additional_params
                    }
                    for model in self.sparse_models
                ],
                'hybrid': [
                    {
                        'name': model.name,
                        'model_id': model.model_id,
                        'trust_remote_code': model.trust_remote_code,
                        'device': model.device,
                        'batch_size': model.batch_size,
                        'max_length': model.max_length,
                        'additional_params': model.additional_params
                    }
                    for model in self.hybrid_models
                ],
                'reranking': [
                    {
                        'name': model.name,
                        'model_id': model.model_id,
                        'trust_remote_code': model.trust_remote_code,
                        'device': model.device,
                        'batch_size': model.batch_size,
                        'max_length': model.max_length,
                        'additional_params': model.additional_params
                    }
                    for model in self.reranking_models
                ]
            },
            'metrics': {
                'k_values': self.k_values
            },
            'output': {
                'results_dir': self.results_dir,
                'save_embeddings': self.save_embeddings,
                'generate_plots': self.generate_plots,
                'generate_report': self.generate_report
            },
            'performance': {
                'show_progress': self.show_progress,
                'log_level': self.log_level
            }
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {output_path}")


def create_default_config(output_path: str):
    """Create a default configuration file."""
    config = EvaluationConfig(
        dataset_path="data/qa_dataset/qa_finetune_dataset.json",
        k_values=[1, 3, 5, 10, 20],
        dense_models=[
            ModelConfig(
                name="bge-m3",
                model_id="BAAI/bge-m3",
                trust_remote_code=True
            ),
            ModelConfig(
                name="bge-m3-finetuned",
                model_id="your-org/bge-m3-finetuned",  # Replace with actual model ID
                trust_remote_code=True
            ),
            ModelConfig(
                name="jina-v3",
                model_id="jinaai/jina-embeddings-v3",
                trust_remote_code=True
            )
        ],
        sparse_models=[
            ModelConfig(
                name="bm25",
                model_id="",  # BM25 doesn't need a model ID
                additional_params={"k1": 1.2, "b": 0.75}
            ),
            ModelConfig(
                name="bge-m3-sparse",
                model_id="BAAI/bge-m3",
                trust_remote_code=True
            )
        ],
        hybrid_models=[
            ModelConfig(
                name="bge-m3-hybrid",
                model_id="BAAI/bge-m3",
                trust_remote_code=True,
                additional_params={"dense_weight": 0.7, "sparse_weight": 0.3}
            )
        ],
        reranking_models=[
            ModelConfig(
                name="bge-m3-reranker",
                model_id="BAAI/bge-reranker-v2-m3",
                trust_remote_code=True,
                additional_params={"top_k_candidates": 100}
            )
        ]
    )
    
    config.to_yaml(output_path)
    logger.info(f"Default configuration created at {output_path}")
