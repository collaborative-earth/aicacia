import argparse
import os
from glob import glob

from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import HTMLNodeParser, MarkdownNodeParser
from tqdm import tqdm

from utils import *


def extract_text_from_pdf(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text()
    return full_text


def parse_args():
    parser = argparse.ArgumentParser(description="VectorDB Arguments")
    parser.add_argument('-c', '--collection', help="Collection Name")
    parser.add_argument('-m', '--embedding-model', default="mxbai-embed-large", help="Embedding model")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # Dictionary mapping file extensions to their respective functions
    extraction_functions = {
        '.html': extract_text_from_html,
        '.pdf': extract_text_from_pdf,
    }

    args = parse_args()
    collection_name = args.collection
    file_paths = glob('../data/**/*', recursive=True)
    file_paths = [file_path for file_path in file_paths if os.path.isfile(file_path)]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    client = QdrantClient("localhost", port=6333)
        
    delete_collection_if_exists(client, collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    unique_id = 0

    for doc_id, file_path in tqdm(enumerate(file_paths), total=len(file_paths)):        
        # Call the appropriate function based on the extension
        file_name = file_path.split('/')[-1]
        try:
            text = extraction_functions[get_file_extension(file_path).lower()](file_path)
        except KeyError:
            raise ValueError(f"Unsupported file type: {extension}")

        chunks = text_splitter.split_text(text)
        points = []

        for chunk_id, chunk in enumerate(chunks):
            response = ollama.embeddings(
                model=args.embedding_model,
                prompt=chunk,
            )
            chunk_embedding = response["embedding"]

            metadata = {"doc_id": doc_id, "chunk_id": chunk_id, "doc_name": file_name, "text": chunk}
            client.upsert(collection_name=collection_name,
                                 points=[PointStruct(id=unique_id, payload=metadata, vector=chunk_embedding)])
            unique_id += 1

        client.upload_points(collection_name, points)
