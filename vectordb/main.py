import argparse
import os
from glob import glob
import sys
import ollama
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import HTMLNodeParser, MarkdownNodeParser
sys.path.append("..")
from finetuning.src.node_parsers.tei_parser import TEINodeParser
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

    config = load_config('config.yaml')
    text_splitter = create_text_splitter(config)
    embed_model = create_embedding_class(config)
    vector_store = create_vectordb_client(config, collection_name)

    for ext, file_parser in extraction_functions.items():
        try:
            reader = SimpleDirectoryReader(input_dir='../data/',
                                           recursive=True,
                                           required_exts=[ext],
                                           file_extractor = create_file_extractor(config),
                                           num_files_limit=100)
        except Exception as e:
            if 'No files found' in str(e):
                continue
            else:
                raise Exception(e)
        docs = reader.load_data()

        pipeline = IngestionPipeline(transformations=[file_parser, text_splitter, embed_model], vector_store=vector_store)
        nodes = pipeline.run(documents=docs, show_progress=True)
