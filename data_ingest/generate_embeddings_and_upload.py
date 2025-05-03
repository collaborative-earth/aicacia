import re
import boto3

from typing import Sequence, Any

from data_ingest.entities.postprocess_models import PostprocessResult
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.schema import Document, BaseNode, TransformComponent
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

PARAGRAPH_SEPARATOR = "\n\n"
BUCKET_NAME = 'aicacia-extracted-data'

client = boto3.client("s3")


def _is_box_header(text: str) -> bool:
    if not text.upper().startswith("BOX"):
        return False

    if re.match(r"BOX \w?-?\d+", text.upper()) and "|" in text:
        return True
    else:
        return False


def _join_paragraphs(postprocess_result: PostprocessResult) -> str:
    paragraphs = []

    temp_last_text_fragment = None

    pages = postprocess_result.pages

    for page in pages:
        for zone in page.zones:
            if zone.paragraphs:
                for paragraph in zone.paragraphs:
                    if temp_last_text_fragment and not _is_box_header(paragraph):
                        paragraphs.append(f'{temp_last_text_fragment} {paragraph}')
                        temp_last_text_fragment = None
                    else:
                        paragraphs.append(paragraph)

            if zone.last_text_fragment:
                if temp_last_text_fragment:
                    temp_last_text_fragment = f'{temp_last_text_fragment} {zone.last_text_fragment}'
                else:
                    temp_last_text_fragment = zone.last_text_fragment

    return PARAGRAPH_SEPARATOR.join(paragraphs)


class S3DownloadAndTextJoining(TransformComponent):
    def __call__(self, docs: Sequence[BaseNode], **kwargs: Any) -> Sequence[BaseNode]:
        for doc in docs:
            response = client.get_object(Bucket=BUCKET_NAME, Key=f'wri/postprocess_output/{doc.doc_id}.json')
            raw_bytes = response["Body"].read()
            postprocess_result = PostprocessResult.from_json(raw_bytes.decode("utf-8"))
            full_text = _join_paragraphs(postprocess_result)
            doc.set_content(full_text)

        return docs


if __name__ == '__main__':
    paginator = client.get_paginator('list_objects_v2')

    page_iterator = paginator.paginate(Bucket=BUCKET_NAME, Prefix='wri/postprocess_output')

    docs = []

    for page in page_iterator:
        for element in page['Contents']:
            key = element['Key']
            doc_id = key[key.rindex('/')+1:-5]
            docs.append(Document(doc_id=doc_id))

    downloader = S3DownloadAndTextJoining()
    splitter = SentenceSplitter(chunk_size=256, chunk_overlap=40, paragraph_separator=PARAGRAPH_SEPARATOR)
    embedding_model = HuggingFaceEmbedding("BAAI/bge-m3")

    vector_store = QdrantVectorStore(
        url="<URL>",
        collection_name="aicacia",
        api_key='<KEY>'
    )

    pipeline = IngestionPipeline(
        transformations=[downloader, splitter, embedding_model],
        vector_store=vector_store,
    )

    nodes = pipeline.run(documents=docs, show_progress=True)
