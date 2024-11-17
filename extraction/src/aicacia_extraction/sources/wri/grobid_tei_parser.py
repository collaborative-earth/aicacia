from aicacia_extraction.sources.io_utils import read_local_xml


def __parse_references(doc):
    reference_docs = doc.find_all('biblStruct')

    for reference_doc in reference_docs:
        title = None
        if (title_doc := reference_doc.find('title')) is not None:
            title = title_doc.get_text()

        authors = []
        author_docs = reference_doc.find_all('author')
        for author_doc in author_docs:
            sub_docs = author_doc.find_all(string=True)
            authors.append(' '.join([sub_doc.get_text().strip() for sub_doc in sub_docs]).strip())

        published_date = None
        if (published_date_doc := reference_doc.find('date', type='published')) is not None:
            published_date = published_date_doc.get_text()

        publisher = None
        if (publisher_doc := reference_doc.find('publisher')) is not None:
            publisher = publisher_doc.get_text()

        doi = None
        if (doi_doc := reference_doc.find('idno', type='DOI')) is not None:
            doi = doi_doc.get_text()

        yield {
            'title': title,
            'doi': doi,
            'publisher': publisher,
            'published_date': published_date,
            'authors': authors
        }


def __parse_raw_references(doc):
    reference_docs = doc.find_all('biblStruct')

    for reference_doc in reference_docs:
        raw_reference = None
        if (raw_reference_doc := reference_doc.find('note', type='raw_reference')) is not None:
            raw_reference = raw_reference_doc.get_text()

        if raw_reference:
            yield raw_reference


def __parse_text(doc):
    if (abstract_doc := doc.find('abstract')) is not None:
        abstract = abstract_doc.prettify()
        yield {
            'type': 'abstract',
            'content': abstract
        }

    if (body_doc := doc.find('body')) is not None:
        div_docs = body_doc.find_all('div')
        for div_doc in div_docs:
            div = div_doc.prettify()
            yield {
                'type': 'div',
                'content': div
            }

        table_docs = body_doc.find_all('figure', type='table')
        for table_doc in table_docs:
            table = table_doc.prettify()
            yield {
                'type': 'table',
                'content': table
            }


def parse_grobid(path):
    doc = read_local_xml(path)

    return {
        'refs': list(__parse_references(doc)),
        'raw_refs': list(__parse_raw_references(doc)),
        'content': list(__parse_text(doc))
    }
