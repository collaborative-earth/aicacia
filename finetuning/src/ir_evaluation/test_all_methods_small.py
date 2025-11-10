"""
Test all retrieval methods with a very small dataset.
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


def test_all_methods_small():
    """Test all retrieval methods with a small dataset."""
    logger.info("Testing all methods with small dataset (1 query, 5 documents)")
    
    try:
        # Create a test config with small dataset
        test_config_path = "test_all_small_config.yaml"
        create_default_config(test_config_path)
        
        # Modify config to use small dataset and test all methods
        import yaml
        with open(test_config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Use the small test dataset
        config_data['dataset']['path'] = "data/qa_dataset/test_small_dataset.json"
        config_data['dataset']['max_queries'] = None  # Use all queries (just 1)
        
        # Test all methods
        config_data['methods']['dense'] = [config_data['methods']['dense'][0]]  # BGE-M3
        config_data['methods']['sparse'] = [config_data['methods']['sparse'][0]]  # BM25
        config_data['methods']['hybrid'] = [config_data['methods']['hybrid'][0]]  # BGE-M3 hybrid
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
        
        logger.info("All methods test completed successfully!")
        logger.info(f"Evaluated {len(results)} methods:")
        for method_name, result in results.items():
            logger.info(f"  {method_name}: MRR@10={result.metrics['mrr@10']:.4f}, Time={result.execution_time:.2f}s")
        
        # Generate report
        report = evaluator.generate_report(results)
        print("\n" + "="*50)
        print("EVALUATION REPORT")
        print("="*50)
        print(report)
        
        # Clean up test config
        Path(test_config_path).unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"All methods test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_all_methods_small()
    if success:
        print("\n✅ All methods tests passed!")
        sys.exit(0)
    else:
        print("\n❌ All methods tests failed!")
        sys.exit(1)


