import os

import pdfplumber
from bs4 import BeautifulSoup


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