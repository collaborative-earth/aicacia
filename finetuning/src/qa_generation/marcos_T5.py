import re
import torch
from typing import Dict, List, Tuple
from llama_index.finetuning import EmbeddingQAFinetuneDataset
from transformers import T5ForConditionalGeneration, T5Tokenizer

def generate_qa_embedding_pairs_fromT5(
    nodes: List[TextNode],
    num_questions_per_chunk: int = 2,
    save_every: int = 500,
    output_path: str = "qa_finetune_dataset.json",
    max_length_paragraph: int = 512,  # Max length for paragraph
    max_length_query: int = 64,  # Max length for output query,
    verbose: bool = True,
) -> EmbeddingQAFinetuneDataset:
    """Generate QA pairs from a set of nodes using T5 model for query generation and save periodically.

    Args:
        nodes (List[TextNode]): List of TextNode objects to process.
        num_questions_per_chunk (int): Number of questions to generate per chunk of text.
        retry_limit (int): Number of times to retry on failure.
        on_failure (str): Action to take on repeated failures ('fail' or 'continue').
        save_every (int): Number of nodes to process before saving the dataset.
        output_path (str): The file path to save the JSON output.
        verbose (bool): If True, print debugging messages.

    Returns:
        EmbeddingQAFinetuneDataset: The generated dataset.
    """
    queries, corpus, relevant_docs = load_existing_data(output_path)

    node_dict = {
        node.node_id: node.get_content(metadata_mode=MetadataMode.NONE)
        for node in nodes
    }

    tokenizer = T5Tokenizer.from_pretrained("BeIR/query-gen-msmarco-t5-large-v1")
    model = T5ForConditionalGeneration.from_pretrained("BeIR/query-gen-msmarco-t5-large-v1")
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    start_index = len(corpus)

    save_counter = start_index

    for node_id, text in tqdm(
        list(node_dict.items())[start_index:], initial=start_index
    ):
        para = text

        input_ids = tokenizer.encode(para, return_tensors="pt").to(device)

        outputs = model.generate(input_ids = input_ids, max_length=max_length_query, do_sample=True, top_p=0.95, num_return_sequences=num_questions_per_chunk)

        questions = [re.sub(r"^\d+[\).\s]", "", tokenizer.decode(output, skip_special_tokens=True)).strip() for output in outputs]
        questions = [question for question in questions if len(question) > 0][
            :num_questions_per_chunk
        ]

        num_questions_generated = len(questions)
        for question in questions:
            question_id = str(uuid.uuid4())
            queries[question_id] = question
            relevant_docs[question_id] = [node_id]

        corpus[node_id] = text

        save_counter += 1
        if save_counter % save_every == 0:
            dataset = EmbeddingQAFinetuneDataset(
                queries=queries, corpus=corpus, relevant_docs=relevant_docs
            )
            dataset.save_json(output_path)
            if verbose:
                print(f"Saved progress at {save_counter} entries.")

    # Save final dataset
    dataset = EmbeddingQAFinetuneDataset(
        queries=queries, corpus=corpus, relevant_docs=relevant_docs
    )
    dataset.save_json(output_path)
    if verbose:
        print("Final dataset saved.")

    return dataset