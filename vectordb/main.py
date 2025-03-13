import argparse
import os
from glob import glob

from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import HTMLNodeParser, MarkdownNodeParser
from tqdm import tqdm
sys.path.append("..")
from utils import *
from custom_parsers import *
from qdrant_client import QdrantClient
sys.path.append("..")
#from finetuning.src.node_parsers.tei_parser import TEINodeParser


def parse_args():
    parser = argparse.ArgumentParser(description="VectorDB Arguments")
    parser.add_argument('-c', '--collection', help="Collection Name")
    parser.add_argument('-m', '--embedding-model', default="mxbai-embed-large", help="Embedding model")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # Dictionary mapping file extensions to their respective functions
    extraction_functions = {
            #'.md': MarkdownNodeParser(),
            '.html': HTMLNodeParser(),
            #'.pdf': MarkdownNodeParser(),
            '.xml': TEINodeParser(),
            '.json': MyJSONNodeParser()
        }
        
    args = parse_args()
    collection_name = args.collection
    file_paths = glob('../data/**/*', recursive=True)
    file_paths = [file_path for file_path in file_paths if os.path.isfile(file_path)]

    config = load_config('config.yaml')
    text_splitter = create_text_splitter(config)
    embed_model = create_embedding_class(config)
    client = QdrantClient( location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name="aicacia")
    #vector_store = create_vectordb_client(config, collection_name)
    metadata_df = read_db(input_dir)[['id', 'title', 'doi', 'authors',
                                   'corpus_name', 'sources', 'location', 
                                   'sourced_date', 'revision_date',
                                   'provided_tags', 'generated_tags','metadata']]
    metadata_df["extracted_file_name"] = metadata_df["metadata"].apply(extract_file_name)
    
    for ext, file_parser in extraction_functions.items():
        
        try:
            reader = SimpleDirectoryReader(input_dir=input_dir,
                                           recursive=True,
                                           required_exts=[ext],
                                           file_extractor = create_file_extractor(config),
                                           num_files_limit=100)
        except Exception as e:
            if 'No files found' in str(e):
                continue
            else:
                raise Exception(e)
        
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

        pipeline = IngestionPipeline(transformations=[file_parser, text_splitter, MetadataCleanupTransformation(),embed_model], vector_store=vector_store)
        nodes = pipeline.run(documents=docs, show_progress=True)
