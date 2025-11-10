"""
Test script for sparse retrieval methods only.
"""
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from ir_evaluation.base.config import create_default_config
from ir_evaluation.comprehensive_evaluator import ComprehensiveEvaluator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sparse_evaluation():
    """Test evaluation with sparse methods only."""
    logger.info("Testing sparse retrieval methods")
    
    try:
        # Create a test config with only sparse methods
        test_config_path = "test_sparse_config.yaml"
        create_default_config(test_config_path)
        
        # Modify config to test only sparse methods
        import yaml
        with open(test_config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        config_data['dataset']['max_queries'] = 5  # Limit to 5 queries for faster testing
        config_data['methods']['dense'] = []  # Skip dense methods
        config_data['methods']['sparse'] = [config_data['methods']['sparse'][0]]  # Only test BM25
        config_data['methods']['hybrid'] = []  # Skip hybrid for now
        config_data['methods']['reranking'] = []  # Skip reranking for now
        
        with open(test_config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        # Initialize evaluator
        evaluator = ComprehensiveEvaluator(test_config_path)
        
        # Run evaluation
        results = evaluator.evaluate_all()
        
        # Check results
        assert len(results) > 0, "No results generated"
        
        for method_name, result in results.items():
            assert result.method_name == method_name, f"Method name mismatch: {result.method_name} != {method_name}"
            assert len(result.metrics) > 0, f"No metrics for {method_name}"
            assert 'mrr@10' in result.metrics, f"Missing MRR@10 metric for {method_name}"
            assert result.execution_time > 0, f"Invalid execution time for {method_name}"
        
        logger.info("Sparse test completed successfully!")
        logger.info(f"Evaluated {len(results)} methods:")
        for method_name, result in results.items():
            logger.info(f"  {method_name}: MRR@10={result.metrics['mrr@10']:.4f}")
        
        # Clean up test config
        Path(test_config_path).unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"Sparse test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_sparse_evaluation()
    if success:
        print("✅ Sparse retrieval tests passed!")
        sys.exit(0)
    else:
        print("❌ Sparse retrieval tests failed!")
        sys.exit(1)


