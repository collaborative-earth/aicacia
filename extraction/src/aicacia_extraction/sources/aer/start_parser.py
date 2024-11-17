import time

from aicacia_extraction.sources.aer.aer_html_metadata_extractor import AerSimpleExtractor
from aicacia_document_exporter.SimpleFileDocumentExporter import SimpleFileDocumentExporter

start_time = time.time()

start_page = 800
page_limit = -1

extractor = AerSimpleExtractor()

with SimpleFileDocumentExporter('aer.db', batch_size=30) as exporter:
    for doc in extractor.extract(start_page=start_page, page_limit=page_limit, reversed_traversal=True):
        if doc is not None:
            exporter.insert([doc])

end_time = time.time()

print(f'Finished extraction! Elapsed time: {end_time - start_time} sec')