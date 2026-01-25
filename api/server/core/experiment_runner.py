import json
import random
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Sequence

from langchain_openai import ChatOpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from openai import APIError
from qdrant_client import QdrantClient
from server.core.config import settings
from server.db.models.experiment import Experiment
from server.db.models.sourced_documents import SourcedDocument
from server.dtos.experiment import ConfigurationResponse, ExperimentConfiguration
from server.dtos.query import Reference
from sqlmodel import Session, select

# Global cache for embedding models (loaded once at first use)
_embedding_model_cache: dict[str, HuggingFaceEmbedding] = {}

# Global cache for LLM instances
_llm_cache: dict[str, ChatOpenAI] = {}

# Shared Qdrant client
_vectordb_client = QdrantClient(
    url=settings.QDRANT_URL, https=True, api_key=settings.QDRANT_API_KEY
)


def get_embedding_model(model_name: str) -> HuggingFaceEmbedding:
    """Get cached embedding model or create and cache it."""
    if model_name not in _embedding_model_cache:
        _embedding_model_cache[model_name] = HuggingFaceEmbedding(model_name=model_name)
    return _embedding_model_cache[model_name]


def get_llm(model_name: str, temperature: float) -> ChatOpenAI:
    """Get cached LLM or create and cache it."""
    cache_key = f"{model_name}:{temperature}"
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=2,
            api_key=settings.OPENAI_API_KEY,
        )
    return _llm_cache[cache_key]


class ConfigurationRunner:
    """Runs a single experiment configuration against a question."""

    def __init__(self, config: ExperimentConfiguration):
        self.config = config
        self.embedding_model = get_embedding_model(config.embedding_model)

    def run(self, question: str, db: Session) -> ConfigurationResponse:
        """Execute the configuration: embed, search vectordb, optionally generate summary."""
        # 1. Search vectordb
        references, rag_context = self._search_vectordb(question, db)

        # 2. Generate summary if LLM is configured
        summary = None
        if self.config.llm_model:
            summary = self._generate_summary(question, rag_context)

        return ConfigurationResponse(
            configuration_id=self.config.configuration_id,
            references=references,
            summary=summary,
        )

    def _search_vectordb(
        self, question: str, db: Session
    ) -> tuple[list[Reference], list[dict]]:
        """Embed question and search the configured collection."""
        query_embedding = self.embedding_model.get_text_embedding(question)

        vectordb_results = _vectordb_client.query_points(
            collection_name=self.config.collection_name,
            query=query_embedding,
            with_payload=["_node_content", "doc_id"],
            limit=self.config.limit,
        )

        if not vectordb_results.points:
            return [], []

        # Retrieve document metadata
        doc_ids = list({p.payload["doc_id"] for p in vectordb_results.points})
        docs: Sequence[SourcedDocument] = db.exec(
            select(SourcedDocument).where(SourcedDocument.doc_id.in_(doc_ids))
        ).all()

        references = []
        rag_context = []
        duplicate_chunk_counter: dict[str, int] = {}

        for point in vectordb_results.points:
            point_doc_id = uuid.UUID(point.payload["doc_id"])
            doc = next((d for d in docs if d.doc_id == point_doc_id), None)
            title = doc.title if doc else "Unknown"
            url = doc.page_link if doc else "Unknown"
            doi = doc.doi if doc else "Unknown"

            if (not url or url == "Unknown") and doi and doi != "Unknown":
                url = f"https://doi.org/{doi}"

            url = url or "Unknown"
            text = json.loads(point.payload["_node_content"])["text"]

            # Skip duplicate chunks
            if text in duplicate_chunk_counter:
                duplicate_chunk_counter[text] += 1
                continue
            duplicate_chunk_counter[text] = 1

            rag_context.append({"title": title, "url": url, "text": text})
            references.append(
                Reference(title=title, url=url, score=point.score, chunk=text)
            )

        return references, rag_context

    def _generate_summary(self, question: str, rag_context: list[dict]) -> Optional[str]:
        """Generate summary using the configured LLM."""
        if not self.config.llm_model:
            return None

        llm = get_llm(self.config.llm_model, self.config.temperature)
        rag_context_str = json.dumps(rag_context)

        messages = [
            (
                "system",
                f"""\
You are an environment restoration expert. Users come to you with questions about \
the environment and how to restore it.

Using the context provided, answer the user's question comprehensively.
If the context doesn't contain enough information to fully answer the question, \
indicate what information is missing.

Output should be in markdown format.

context: {rag_context_str}
""",
            ),
            ("human", question),
        ]

        try:
            ai_msg = llm.invoke(messages)
            return ai_msg.content
        except APIError as e:
            print(f"LLM call failed for config {self.config.configuration_id}: {e}")
            return None


class ExperimentRunner:
    """Orchestrates running all configurations for an experiment in parallel."""

    def run(
        self, experiment: Experiment, question: str, db: Session
    ) -> list[ConfigurationResponse]:
        """Run all configurations in parallel and return randomized responses."""
        configs = [ExperimentConfiguration(**c) for c in experiment.configurations]

        if not configs:
            return []

        # Validate no duplicate configuration IDs
        config_ids = [c.configuration_id for c in configs]
        if len(config_ids) != len(set(config_ids)):
            duplicates = [id for id in config_ids if config_ids.count(id) > 1]
            raise ValueError(
                f"Experiment '{experiment.name}' has duplicate configuration_ids: {set(duplicates)}"
            )

        # Run configurations in parallel
        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            futures = []
            for config in configs:
                runner = ConfigurationRunner(config)
                futures.append(executor.submit(runner.run, question, db))

            responses = [f.result() for f in futures]

        # Randomize order before returning
        random.shuffle(responses)
        return responses
