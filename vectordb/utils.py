import os

import pdfplumber
import yaml
from bs4 import BeautifulSoup
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import FlatReader, HTMLTagReader, PDFReader
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


def extract_text_from_pdf(path):
    full_text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text()
    return full_text


def get_file_extension(file_path):
    _, extension = os.path.splitext(file_path)
    return extension

    
def extract_text_from_html(path):
    full_text = ""
    with open(path, 'r', encoding='utf-8') as file:
        html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        # Extract text from all tags
        full_text = soup.get_text()
    return full_text


def delete_collection_if_exists(client, collection_name):
    # Check if the collection exists
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print(f"Collection '{collection_name}' has been deleted.")
    else:
        print(f"Collection '{collection_name}' does not exist.")


def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def create_text_splitter(config):
    splitter_config = config.get('text-splitter', {})
    if splitter_config is None or len(splitter_config) != 1:
        raise Exception('Define one text splitter function!')
    splitter_class = next(iter(splitter_config))
    params = splitter_config[splitter_class]

    try:
        return globals()[splitter_class](**params)
    except:
        raise ValueError(f"Unsupported text splitter: {splitter_class}")


def create_vectordb_client(config, collection_name):
    vectordb_mapping = {
        'QdrantClient': QdrantVectorStore,
    }

    vectordb_config = config.get('vectordb', {})
    if vectordb_config is None or len(vectordb_config) != 1:
        raise Exception('Define one vectordb function!')
    vectordb_class = next(iter(vectordb_config))
    params = vectordb_config[vectordb_class]

    try:
        client = globals()[vectordb_class](**params)
        delete_collection_if_exists(client, collection_name=collection_name)
        return vectordb_mapping[type(client).__name__](client=client, collection_name=collection_name)
    except:
        raise ValueError(f"Unsupported vectordb client: {vectordb_class}")


def create_embedding_class(config):
    embedding_config = config.get('embedding', {})
    if embedding_config is None or len(embedding_config) != 1:
        raise Exception('Define one embedding function!')
    embedding_class = next(iter(embedding_config))
    params = embedding_config[embedding_class]

    try:
        return globals()[embedding_class](**params)
    except:
        raise ValueError(f"Unsupported embedding class: {embedding_class}")


def create_file_extractor(config):
    file_extractor_config = config.get('file_extractor', {})
    extractors = {}

    for file_type, file_type_class in file_extractor_config.items():
        try:
            extractor_class = getattr(__import__('llama_index.readers.file', fromlist=[file_type_class]), file_type_class)
            extractors[f'.{file_type}'] = extractor_class()
        except AttributeError:
            raise ValueError(f"Unsupported extractor class: {file_type_class}")
    
    return extractors
