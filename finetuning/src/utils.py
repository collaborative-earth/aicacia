
import random
from typing import Dict, List, Tuple
from llama_index.core.evaluation import EmbeddingQAFinetuneDataset

def split_dataset(dataset: EmbeddingQAFinetuneDataset, train_ratio: float = 0.8) -> Tuple[EmbeddingQAFinetuneDataset, EmbeddingQAFinetuneDataset]:
    """
    Split a QA dataset into training and validation sets.

    Args:
        dataset (EmbeddingQAFinetuneDataset): The dataset to split.
        train_ratio (float): Proportion of the dataset to include in the training set (default is 0.8).

    Returns:
        Tuple[EmbeddingQAFinetuneDataset, EmbeddingQAFinetuneDataset]: A tuple containing the training and validation datasets.
    """
    query_ids = list(dataset.queries.keys())
    random.shuffle(query_ids)
    split_index = int(len(query_ids) * train_ratio)
    train_query_ids = query_ids[:split_index]
    val_query_ids = query_ids[split_index:]

    train_queries = {qid: dataset.queries[qid] for qid in train_query_ids}
    train_relevant_docs = {qid: dataset.relevant_docs[qid] for qid in train_query_ids}


    val_queries = {qid: dataset.queries[qid] for qid in val_query_ids}
    val_relevant_docs = {qid: dataset.relevant_docs[qid] for qid in val_query_ids}

    # Create corpus data (assuming it is shared between train and val)
    train_corpus = dataset.corpus
    val_corpus = dataset.corpus

    # Create new dataset instances
    train_dataset = EmbeddingQAFinetuneDataset(queries=train_queries,
                                               corpus = train_corpus,
                                               relevant_docs = train_relevant_docs)
    val_dataset = EmbeddingQAFinetuneDataset(queries=val_queries,
                                             corpus = val_corpus,
                                             relevant_docs = val_relevant_docs)

    return train_dataset, val_dataset