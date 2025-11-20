"""
Main script for running comprehensive retrieval evaluation.
"""
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from ir_evaluation.comprehensive_evaluator import ComprehensiveEvaluator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('evaluation.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run comprehensive evaluation."""
    logger.info("Starting comprehensive retrieval evaluation")
    
    try:
        # Initialize evaluator
        evaluator = ComprehensiveEvaluator("evaluation_config.yaml")
        
        # Run evaluation
        logger.info("Running evaluation for all configured methods...")
        results = evaluator.evaluate_all()
        
        # Generate report
        logger.info("Generating evaluation report...")
        report = evaluator.generate_report(results)
        
        # Print summary
        print("\n" + "="*80)
        print("EVALUATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"Evaluated {len(results)} methods:")
        for method_name in results.keys():
            print(f"  - {method_name}")
        
        print(f"\nReport saved to: {evaluator.config.results_dir}/evaluation_report.txt")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()


