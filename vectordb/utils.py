import os
import sqlite3
from glob import glob
from typing import Dict, List

import pandas as pd
import yaml
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TransformComponent
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import FlatReader, HTMLTagReader, PDFReader
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


class MetadataCleanupTransformation(TransformComponent):
    """Transformation to remove unwanted metadata fields."""
    def __init__(self):
        super().__init__()

    def __call__(self, nodes: List[BaseNode], **kwargs) -> List[BaseNode]:
        for node in nodes:
            # Remove any unwanted metadata keys"
            node.metadata = {k: v for k, v in node.metadata.items() 
                           if not k.startswith("Header_")
                           and k != 'filename'
                           and k != 'file_path'}
        return nodes


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

def read_db(input_dir):
    dbs = glob(f'{input_dir}**/*.db', recursive=True)
    df_list = []
    for db in dbs:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        df_list.append(pd.read_sql_query('SELECT * FROM docs', conn))
        conn.close()
    final_df = pd.concat(df_list, ignore_index=True)
    return final_df
