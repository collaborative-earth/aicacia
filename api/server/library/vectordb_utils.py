import yaml
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient


def create_vectordb_client(config):
    vectordb_config = config.get('vectordb', {})
    params = {
        "host": vectordb_config["host"],
        "port": vectordb_config["port"],
    }

    try:
        return QdrantClient(**params)
    except:
        raise ValueError(f"Unsupported vectordb client")


def create_embedding_class(config):
    embedding_config = config.get('embedding', {})
    if embedding_config is None or len(embedding_config) != 1:
        raise Exception('Define one embedding function!')
    embedding_class = next(iter(embedding_config))
    params = embedding_config[embedding_class]

    try:
        return globals()[embedding_class](**params)
    except Exception:
        raise ValueError(f"Unsupported embedding class: {embedding_class}")


def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
