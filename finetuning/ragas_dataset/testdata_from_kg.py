#!/usr/bin/env python3
import os
import sys
import json
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
    query_distribution = [(single_query,0.6), (multi_query, 0.4)]

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
    per_model_costs = {
        "gpt-4o-mini": (0.0015, 0.006),
        "gpt-4o": (0.03, 0.06),
        # add more models if needed
    }
    total_cost = cost_cb.total_cost(per_model_costs=per_model_costs)
    print(f"Estimated total cost for {args.llm_model}: ${total_cost:.4f}")

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
    print(f"Metadata saved to {metadata_path}")

    # Save testset as JSONL
    testset_path = f"{args.output_prefix}_testset.jsonl"
    with open(testset_path, "w", encoding="utf-8") as fout:
        for item in testdata.testset:
            fout.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Testset saved to {testset_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())