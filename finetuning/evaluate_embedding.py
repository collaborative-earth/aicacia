import random
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sentence_transformers.evaluation import InformationRetrievalEvaluator
from src.bm25evaluator import InformationRetrievalEvaluatorBM25
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset

BASE_DIR = Path(__file__).resolve().parents[0]  
QADATASET_FILE = "qa_finetune_dataset2.json"
QADATASET_PATH = BASE_DIR / "qa_dataset" / QADATASET_FILE

MODEL2EVALUATE = { "BM25" : "BM25",
                  "jinav3" : "jinaai/jina-embeddings-v3",
                  "bge=m3" : "BAAI/bge-m3",
                  }



def evaluate_st(
    dataset,
    model_id,
    name
):
    corpus = dataset.corpus
    queries = dataset.queries
    relevant_docs = dataset.relevant_docs
    print(f"Evaluating information retrieval of model {name} on {len(queries)} q-a pairs.")
    if name == "BM25": 
        evaluator = InformationRetrievalEvaluatorBM25(
            queries, corpus, relevant_docs, name=name,
            show_progress_bar=True)
        model = None
    else: 
        evaluator = InformationRetrievalEvaluator(
            queries, corpus, relevant_docs, name=name,
            show_progress_bar=True
        )
        model = SentenceTransformer(model_id,trust_remote_code=True)
    output_path = BASE_DIR / "ir_results" / os.path.splitext(QADATASET_FILE)[0]
    Path(output_path).mkdir(exist_ok=True, parents=True)
    return evaluator(model, output_path=output_path)

def main():
    qa_dataset =  EmbeddingQAFinetuneDataset.from_json(QADATASET_PATH)
    for model_name,model_id in MODEL2EVALUATE.items():
        evaluate_st(qa_dataset,model_id,model_name)
        
        
if __name__ == "__main__":
    main()

