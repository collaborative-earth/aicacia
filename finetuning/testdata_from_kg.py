#!/usr/bin/env python3
import os
import sys
import json
import re
import uuid
import argparse
from pathlib import Path
from ragas.testset.graph import KnowledgeGraph
from ragas.testset import TestsetGenerator
from ragas.run_config import RunConfig
from ragas.cost import get_token_usage_for_openai

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from ragas_ext import volunteer, manager, technician, researcher
from ragas_ext import SingleHopScenarioEco, MultiHopQueryEco
from ragas.llms import llm_factory

def log_graph_info(kg: KnowledgeGraph, label: str):
    print(f"\n=== {label} ===")
    print(f"Nodes: {len(kg.nodes)}")
    print(f"Edges: {len(kg.relationships)}")
    print("=====================\n")

def setup_llm(model: str, provider: str = "openai", async_mode: bool = False, api_key: str = None):
    if provider == "openai":
        if async_mode:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
        else:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        return llm_factory(model, provider="openai", client=client)
    raise ValueError(f"Unsupported LLM provider: {provider}")

def save_ragasjsonl_to_llamaindexjson(file_path, kg_path, output_dir="."):
    """
    Convert a RAGAS JSONL dataset into a LlamaIndex-style JSON file.

    Reads queries and reference contexts using a KG for the corpus.
    Saves a JSON file with 'queries', 'relevant_docs', and 'corpus'.
    
    Args:
        file_path (str): Path to the RAGAS JSONL file.
        kg_path (str): Path to a knowledge graph JSON file (required).
        output_dir (str, optional): Directory to save the output JSON. Defaults to current directory.

    Returns:
        dict: The converted dataset.
    """
    
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    data = []
    with open(file_path, "r") as f:
        for line in f:
            data.append(json.loads(line))

    # --- Build corpus from KG ---
    with open(kg_path, "r") as f:
        kg = json.load(f)
    corpus = {node["id"]: node["properties"]["page_content"] for node in kg["nodes"]}

    # --- Build queries and relevant_docs ---
    queries = {}
    relevant_docs = {}

    for d in data:
        qid = str(uuid.uuid4())
        queries[qid] = d["user_input"]

        valid_ids = [cid for cid in d.get("reference_context_ids", []) if any(cid in k for k in corpus.keys())]

        if valid_ids:
            relevant_docs[qid] = valid_ids
        else:
            print(f"Warning: query '{d['user_input'][:50]}...' has no matching contexts in corpus")

    dataset = {
        "queries": queries,
        "relevant_docs": relevant_docs,
        "corpus": corpus,
    }
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{file_name}_llama.json")

    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSaved LlamaIndex dataset to: {out_path}")
    print(f"   Queries: {len(queries)} | Corpus: {len(corpus)} | With relevant_docs: {len(relevant_docs)}")

    return dataset

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg_path", type=str, required=True)
    parser.add_argument("--output_prefix", type=str, required=True,
                        help="Prefix for output files (metadata.json and testset.jsonl will be created)")
    parser.add_argument("--num_queries", type=int, default=30)
    parser.add_argument("--llm_model", type=str, default="gpt-3.5-turbo")
    parser.add_argument("--llm_provider", type=str, default="openai")
    parser.add_argument("--openai_api_key", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--convert_to_llamaindex", action="store_false",
                        help="Also convert the testset to LlamaIndex format")
    args = parser.parse_args()

    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load KG
    if not os.path.exists(args.kg_path):
        print(f"KG file not found: {args.kg_path}")
        sys.exit(1)
    kg = KnowledgeGraph().load(args.kg_path)
    log_graph_info(kg, "Loaded Knowledge Graph")

    # Setup LLM
    llm = setup_llm(
        model=args.llm_model,
        provider=args.llm_provider,
        async_mode=True,
        api_key=args.openai_api_key or os.getenv("OPENAI_API_KEY")
    )

    # Define personas
    persona_list = [volunteer, manager, technician, researcher]

    # Initialize generator
    gen = TestsetGenerator(
        llm=llm,
        knowledge_graph=kg,
        embedding_model=None,
        persona_list=persona_list
    )

    # Generate queries
    single_query = SingleHopScenarioEco(llm=llm)
    multi_query = MultiHopQueryEco(llm=llm)
    query_distribution = [(single_query, 0.6), (multi_query, 0.4)]

    testdata = gen.generate(
        testset_size=args.num_queries,
        query_distribution=query_distribution,
        run_config=RunConfig(max_workers=1),
        with_debugging_logs=True,
        batch_size=args.batch_size,
        raise_exceptions=True,
        return_executor=False,
        token_usage_parser=get_token_usage_for_openai
    )

    # Compute cost
    cost_cb = testdata.cost_cb
    if cost_cb.usage_data:
        per_model_costs = {
            "gpt-4o-mini": (0.0015, 0.006),
            "gpt-4o": (0.03, 0.06),
            "gpt-3.5-turbo": (0.0005, 0.0015),
            # add more models if needed
        }
        total_cost = cost_cb.total_cost(per_model_costs=per_model_costs)
        print(f"\nEstimated total cost for {args.llm_model}: ${total_cost:.4f}")
    else:
        total_cost = "unknown"

    # Save metadata
    metadata_path = f"{args.output_prefix}_metadata.json"
    metadata = {
        "kg_file": os.path.basename(args.kg_path),
        "num_nodes": len(kg.nodes),
        "num_relationships": len(kg.relationships),
        "personas": [p.name for p in persona_list],
        "num_queries": args.num_queries,
        "batch_size": args.batch_size,
        "llm_model": args.llm_model,
        "llm_provider": args.llm_provider,
        "estimated_cost_usd": total_cost
    }
    with open(metadata_path, "w", encoding="utf-8") as fout:
        json.dump(metadata, fout, ensure_ascii=False, indent=2)
    print(f"\nMetadata saved to {metadata_path}")

    # Save testset as JSONL
    testset_path = f"{args.output_prefix}_testset.jsonl"
    testdata.to_jsonl(testset_path)
    print(f"Testset saved to {testset_path}")
    
    # Convert to LlamaIndex format if requested
    if args.convert_to_llamaindex:
        print("\n" + "="*50)
        print("Converting to LlamaIndex format...")
        print("="*50)
        
        output_dir = output_path.parent if output_path.parent != Path('.') else '.'
        save_ragasjsonl_to_llamaindexjson(
            file_path=testset_path,
            kg_path=args.kg_path,
            output_dir=str(output_dir)
        )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())