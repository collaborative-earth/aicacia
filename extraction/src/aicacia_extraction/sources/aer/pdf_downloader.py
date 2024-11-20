import sqlite3
import urllib.request

from urllib.request import urlretrieve

DB_FILE_PATH = 'aer.db'
OUTPUT_DIR = '.'
WILEY_API_TOKEN = 'YOUR_TOKEN'  # it seems like Wiley API works even with empty token :)

opener = urllib.request.build_opener()
opener.addheaders = [('Wiley-TDM-Client-Token', WILEY_API_TOKEN)]
urllib.request.install_opener(opener)


def get_downloadable_docs(db_path):
    query = ("select id, json_extract(sources, '$.pdf_download_link') as pdf_download_link from docs "
             "where sources <> '' and json_extract(sources, '$.pdf_download_link') is not null")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    conn.close()
    return result


def download_pdf(doc_id, download_link, output_dir):
    try:
        urlretrieve(download_link, f'{output_dir}/{doc_id}.pdf')
        print(f"Downloaded pdf source for {doc_id} ({download_link})")
    except Exception as e:
        print(f"Couldn't retrieve pdf from url, skipping: doc_id={doc_id}, url={download_link}, e={e}")


if __name__ == '__main__':
    docs = get_downloadable_docs(DB_FILE_PATH)

    print(f"Found {len(docs)} docs with potentially downloadable pdf files!")

    for document_id, pdf_download_link in docs:
        download_pdf(document_id, pdf_download_link, OUTPUT_DIR)
