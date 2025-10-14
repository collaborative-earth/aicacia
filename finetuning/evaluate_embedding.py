import random
import os
import argparse
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sentence_transformers.evaluation import InformationRetrievalEvaluator
from src.bm25evaluator import InformationRetrievalEvaluatorBM25
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset

# Constants for default paths and model IDs
BASE_DIR = Path(__file__).resolve().parents[0]  # Current script directory
DEFAULT_QADATASET_FILE = "/Users/smalerba/Projects/AICACIA/aicacia/finetuning/qa_dataset/merged_qa_dataset.json"
DEFAULT_OUTPUT_DIR = "ir_results/"
DEFAULT_MODEL2EVALUATE = {
    "BM25": "BM25",
    "jinav3": "jinaai/jina-embeddings-v3",
    "bge=m3": "BAAI/bge-m3",
}

def evaluate_st(dataset, model_id, name, output_dir):
    """
    Function to evaluate the information retrieval performance for a model.

    Args:
        dataset (EmbeddingQAFinetuneDataset): The dataset containing queries and documents.
        model_id (str): Model identifier or name.
        name (str): The name of the model for evaluation purposes.
        output_dir (str): The directory to store evaluation results.

    Returns:
        None
    """
    # Extract corpus, queries, and relevant documents from the dataset
    corpus = dataset.corpus
    queries = dataset.queries
    relevant_docs = dataset.relevant_docs
 
        
        
    print(f"Evaluating information retrieval of model {name} on {len(queries)} q-a pairs.")

    # Conditional evaluator setup based on model type
    if name == "BM25":
        evaluator = InformationRetrievalEvaluatorBM25(
            queries, corpus, relevant_docs, name=name, show_progress_bar=True
        )
        model = None  # BM25 does not require a model
    else:
        evaluator = InformationRetrievalEvaluator(
            queries, corpus, relevant_docs, name=name, show_progress_bar=True
        )
        model = SentenceTransformer(model_id, trust_remote_code=True)

    # Output path setup for evaluation results
    output_path = Path(output_dir) 
    output_path.mkdir(exist_ok=True, parents=True)

    # Perform evaluation
    return evaluator(model, output_path=output_path)



def main():
    """
    Main function to load the dataset and evaluate models.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Evaluate information retrieval models.")
    
    # Add arguments for the dataset, model selection, and output directory
    parser.add_argument('--qa_dataset', type=str, default=DEFAULT_QADATASET_FILE, help="Path to the QA dataset file.")
    parser.add_argument('--output_dir', type=str, default=DEFAULT_OUTPUT_DIR, help="Directory to store evaluation results.")
    parser.add_argument('--models', type=str, nargs='*', default=list(DEFAULT_MODEL2EVALUATE.keys()), help="List of model names to evaluate (space-separated).")
    args = parser.parse_args()
    # Set up the QA dataset path and load the dataset
    qa_dataset_path = Path(args.qa_dataset)
    qa_dataset = EmbeddingQAFinetuneDataset.from_json(qa_dataset_path)
    
    # Iterate over models provided or use the default ones
    for model_name in args.models:
        if model_name in DEFAULT_MODEL2EVALUATE:
            model_id = DEFAULT_MODEL2EVALUATE[model_name]
            print(f"Evaluating model: {model_name} with model ID: {model_id}")
            evaluate_st(qa_dataset, model_id, model_name, args.output_dir)
        else:
            print(f"Model {model_name} is not in the evaluation list. Skipping.")
            
if __name__ == "__main__":
    main()

