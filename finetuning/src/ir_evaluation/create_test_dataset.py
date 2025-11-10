"""
Create a small test dataset for quick evaluation testing.
"""
import json
from pathlib import Path

def create_small_test_dataset():
    """Create a very small test dataset."""
    
    # Create a minimal dataset
    test_dataset = {
        "queries": {
            "q1": "What is machine learning?"
        },
        "corpus": {
            "d1": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            "d2": "Deep learning uses neural networks with multiple layers.",
            "d3": "Natural language processing deals with text and speech.",
            "d4": "Computer vision enables machines to interpret visual information.",
            "d5": "Machine learning algorithms learn from data without explicit programming."
        },
        "relevant_docs": {
            "q1": ["d1", "d5"]  # d1 and d5 are relevant to the query
        }
    }
    
    # Save the test dataset
    test_dataset_path = Path("data/qa_dataset/test_small_dataset.json")
    test_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_dataset_path, 'w') as f:
        json.dump(test_dataset, f, indent=2)
    
    print(f"Created small test dataset with:")
    print(f"  - {len(test_dataset['queries'])} queries")
    print(f"  - {len(test_dataset['corpus'])} documents")
    print(f"  - Saved to: {test_dataset_path}")
    
    return str(test_dataset_path)

if __name__ == "__main__":
    create_small_test_dataset()


