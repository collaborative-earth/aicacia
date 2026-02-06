"""
Format converters for QA datasets.

Supports conversions between:
- LlamaIndex → BEIR
- BEIR + Hard Negatives → BGE-M3
"""

import os
import json
import glob
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

def llamaindex_to_beir(
    input_path: str,
    output_dir: str,
    qgen_prefix: str = "qgen"
) -> Dict:
    """
    Convert LlamaIndex format to BEIR format.
    
    Args:
        input_path: Path to LlamaIndex JSON file
        output_dir: Output directory for BEIR files
        qgen_prefix: Prefix for queries/qrels files
        
    Returns:
        Statistics dict
    """
    # Load LlamaIndex data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = data.get("queries", {})
    corpus = data.get("corpus", {})
    relevant_docs = data.get("relevant_docs", {})
    
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    qrels_dir = os.path.join(output_dir, f"{qgen_prefix}-qrels")
    os.makedirs(qrels_dir, exist_ok=True)
    
    # Write corpus
    corpus_path = os.path.join(output_dir, "corpus.jsonl")
    with open(corpus_path, 'w', encoding='utf-8') as f:
        for doc_id, doc_text in corpus.items():
            entry = {
                "_id": doc_id,
                "title": "",
                "text": doc_text,
                "metadata": {}
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Write queries
    queries_path = os.path.join(output_dir, f"{qgen_prefix}-queries.jsonl")
    with open(queries_path, 'w', encoding='utf-8') as f:
        for qid, query_text in queries.items():
            entry = {
                "_id": qid,
                "text": query_text,
                "metadata": {}
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Write qrels
    qrels_path = os.path.join(qrels_dir, "train.tsv")
    num_qrels = 0
    with open(qrels_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("query-id\tcorpus-id\tscore\n")
        
        for qid, doc_ids in relevant_docs.items():
            for doc_id in doc_ids:
                f.write(f"{qid}\t{doc_id}\t1\n")
                num_qrels += 1
    
    stats = {
        "num_queries": len(queries),
        "num_corpus": len(corpus),
        "num_qrels": num_qrels
    }
    
    # Save metadata
    metadata_path = os.path.join(output_dir, "conversion_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats


def beir_to_bgem3(
    beir_dir: str,
    output_path: str,
    beir_str  = "train",
    qgen_prefix: str = "qgen",
    sep: str = " ",
    retriever: Optional[str] = None,
    prompt: str = "Query",
    require_hard_negatives: bool = True,
) -> Dict:
    """
    Convert BEIR format with hard negatives to BGE-M3 format.
    
    Args:
        beir_dir: Directory with BEIR files
        output_path: Output BGE-M3 jsonl path
        qgen_prefix: Prefix for queries/qrels
        sep: Separator for title and text
        retriever: Specific retriever for negatives (None = first)
        prompt: Query prompt
        require_hard_negatives: Skip queries without negatives
        
    Returns:
        Statistics dict
    """
    # Load corpus
    corpus = {}
    corpus_path = os.path.join(beir_dir, "corpus.jsonl")
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            doc_id = item["_id"]
            title = item.get("title", "")
            text = item.get("text", "")
            corpus[doc_id] = sep.join([title, text]).strip()
    
    # Load queries
    queries = {}
    queries_path = os.path.join(beir_dir, f"{qgen_prefix}-queries.jsonl")
    with open(queries_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            queries[item["_id"]] = item["text"]
    
    # Load qrels
    qrels = {}
    qrels_path = os.path.join(beir_dir, f"{qgen_prefix}-qrels", f"{beir_str}.tsv")
    with open(qrels_path, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                qid, doc_id = parts[0], parts[1]
                if qid not in qrels:
                    qrels[qid] = []
                qrels[qid].append(doc_id)
    
    # Load hard negatives
    hn_path = next(Path(beir_dir).glob("hard-negatives*.jsonl"), None)
    hard_negatives = {}
    
    if os.path.exists(hn_path):
        with open(hn_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                qid = item["qid"]
                neg_dict = item.get('neg', {})
                
                if retriever and retriever in neg_dict:
                    negs = neg_dict[retriever]
                elif neg_dict:
                    negs = list(neg_dict.values())[0]
                else:
                    negs = []
                
                hard_negatives[qid] = negs
    elif require_hard_negatives:
        raise FileNotFoundError(f"Hard negatives not found: {hn_path}")
    
    # Convert to BGE-M3
    stats = {
        "total_queries": 0,
        "queries_with_negatives": 0,
        "skipped_queries": 0,
        "avg_positives": 0,
        "avg_negatives": 0
    }
    
    total_pos = 0
    total_neg = 0
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for qid, query_text in queries.items():
            # Get positives
            pos_ids = qrels.get(qid, [])
            if not pos_ids:
                stats["skipped_queries"] += 1
                continue
            
            positives = [corpus[pid] for pid in pos_ids if pid in corpus]
            if not positives:
                stats["skipped_queries"] += 1
                continue
            
            # Get negatives
            neg_ids = hard_negatives.get(qid, [])
            negatives = [corpus[nid] for nid in neg_ids if nid in corpus]
            
            if require_hard_negatives and not negatives:
                stats["skipped_queries"] += 1
                continue
            
            # Write entry
            entry = {
                "query": query_text,
                "pos": positives,
                "neg": negatives,
                "pos_scores": [],
                "neg_scores": [],
                "prompt": prompt,
                "type": "normal"
            }
            
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            stats["total_queries"] += 1
            total_pos += len(positives)
            total_neg += len(negatives)
            
            if negatives:
                stats["queries_with_negatives"] += 1
    
    # Calculate averages
    if stats["total_queries"] > 0:
        stats["avg_positives"] = total_pos / stats["total_queries"]
        stats["avg_negatives"] = total_neg / stats["total_queries"]
    
    # Save metadata
    metadata_path = output_path.replace('.jsonl', '_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats

def beir_to_llamaindex(
    beir_dir: str,
    output_path: str,
    qgen_prefix: str = "qgen",
    beir_str:str = "train"
) -> Dict:
    """
    Convert BEIR format to LlamaIndex format.

    Expected BEIR structure:
      - corpus.jsonl
      - {qgen_prefix}-queries.jsonl
      - {qgen_prefix}-qrels/train.tsv

    Output LlamaIndex JSON structure:
      {
        "queries": {qid: query_text},
        "corpus": {doc_id: doc_text},
        "relevant_docs": {qid: [doc_id, ...]}
      }

    Args:
        beir_dir: Directory containing BEIR files
        output_path: Path to output LlamaIndex JSON
        qgen_prefix: Prefix for queries/qrels files

    Returns:
        Statistics dict
    """
    # Load corpus
    corpus = {}
    corpus_path = os.path.join(beir_dir, "corpus.jsonl")
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            doc_id = item["_id"]
            text = item.get("text", "")
            corpus[doc_id] = text

    # Load queries
    queries = {}
    queries_path = os.path.join(beir_dir, f"{qgen_prefix}-queries.jsonl")
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            queries[item["_id"]] = item["text"]

    # Load qrels
    relevant_docs = {}
    qrels_path = os.path.join(beir_dir, f"{qgen_prefix}-qrels", f"{beir_str}.tsv")
    with open(qrels_path, "r", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            qid, doc_id, *_ = line.strip().split("\t")
            relevant_docs.setdefault(qid, []).append(doc_id)

    # Assemble LlamaIndex structure
    llamaindex_data = {
        "queries": queries,
        "corpus": corpus,
        "relevant_docs": relevant_docs,
    }

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(llamaindex_data, f, indent=2, ensure_ascii=False)

    stats = {
        "num_queries": len(queries),
        "num_corpus": len(corpus),
        "num_qrels": sum(len(v) for v in relevant_docs.values()),
    }

    return stats

def split_beir(dataset_path, train_ratio=0.7, seed=42):
    """
    Split qrels/train.tsv of a beir dataset into finetune.tsv and validation.tsv

    Args:
        dataset_path: Path to BEIR dataset folder (contains qrels/train.tsv)
        train_ratio: Proportion for training (e.g., 0.7 = 70% train, 30% val)
        seed: Random seed for reproducibility
    """
    dataset_path = Path(dataset_path)
    qrels_path = dataset_path / "qgen-qrels" / "train.tsv"

    if not qrels_path.exists():
        print(f"Error: {qrels_path} does not exist")
        return

    # Load qrels
    qrels_df = pd.read_csv(qrels_path, sep="\t")
    print(f"Total data points: {len(qrels_df)}")

    # Split
    train_df, val_df = train_test_split(
        qrels_df,
        train_size=train_ratio,
        random_state=seed,
        shuffle=True
    )

    # Save splits in the same qrels folder
    output_dir = dataset_path / "qgen-qrels"
    train_df.to_csv(output_dir / "finetune.tsv", sep="\t", index=False)
    val_df.to_csv(output_dir / "validation.tsv", sep="\t", index=False)

    print(f"Finetune: {len(train_df)} ({len(train_df)/len(qrels_df)*100:.1f}%)")
    print(f"Validation: {len(val_df)} ({len(val_df)/len(qrels_df)*100:.1f}%)")
    print(f"Saved to: {output_dir}")

    return train_df, val_df