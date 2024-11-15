import argparse
import os
import sys
from glob import glob

import ollama
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import HTMLNodeParser, MarkdownNodeParser
from tqdm import tqdm
from utils import *

sys.path.append("..")
from finetuning.src.node_parsers.tei_parser import TEINodeParser


def parse_args():
    parser = argparse.ArgumentParser(description="VectorDB Arguments")
    parser.add_argument('-c', '--collection', help="Collection Name")
    parser.add_argument('-d', '--input-dir', help="Input Directory")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    extraction_functions = {
            '.md': MarkdownNodeParser(),
            '.html': HTMLNodeParser(),
            '.pdf': MarkdownNodeParser(),
            '.xml': TEINodeParser()
        }
        
    args = parse_args()
    collection_name = args.collection
    input_dir = args.input_dir

    config = load_config('config.yaml')
    text_splitter = create_text_splitter(config)
    embed_model = create_embedding_class(config)
    vector_store = create_vectordb_client(config, collection_name)
    metadata = read_db(input_dir)[['id', 'title', 'doi', 'authors',
                                   'corpus_name', 'sources', 'location', 
                                   'sourced_date', 'revision_date',
                                   'provided_tags', 'generated_tags']]

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
        
        docs = []
        input_files = reader.input_files
        for file_path in tqdm(input_files):
            reader.input_files = [file_path]
            file_name = str(file_path).split('/')[-1].split('.')[-2]
            try:
                file_metadata = metadata[metadata['id'] == file_name].iloc[0].to_dict()
            except:
                file_metadata = {}

            # Load the document with the file extractor
            loaded_docs = reader.load_data()
            
            # Enrich each document with metadata
            for doc in loaded_docs:
                doc.metadata.update(file_metadata)
                doc.excluded_llm_metadata_keys = list(doc.metadata.keys())
                doc.excluded_embed_metadata_keys = list(doc.metadata.keys())
            docs.extend(loaded_docs)


        pipeline = IngestionPipeline(transformations=[file_parser, text_splitter, MetadataCleanupTransformation(), embed_model], vector_store=vector_store)
        nodes = pipeline.run(documents=docs, show_progress=True)
