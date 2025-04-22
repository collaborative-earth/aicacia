from bs4 import Tag
from datetime import datetime
from data_ingest.utils.html import read_html
from data_ingest.entities.Document import SourcedDocumentMetadata, SourceLink, DocumentSourceCorpus

BASE_URL = 'https://www.wri.org'
BASE_SEARCH_URL = 'https://www.wri.org/resources/type/research-65'
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]

def extract(start_page=1, page_limit=-1, reversed_traversal=True):
    if page_limit <= 0:
        if not reversed_traversal:
            last_page = -1
        else:
            last_page = 0
    else:
        if not reversed_traversal:
            last_page = start_page + page_limit - 1
        else:
            last_page = max(0, start_page - page_limit + 1)

    return __traverse_and_extract(
        start_page, last_page,
        (lambda page: page - 1) if reversed_traversal else (lambda page: page + 1),
        (lambda page, last: page >= last) if reversed_traversal else (lambda page, last: page <= last)
    )

def __traverse_and_extract(start_page, last_page, next_page_func, break_condition_func):
    page = start_page

    while last_page < 0 or break_condition_func(page, last_page):
        projects = read_html(f'{BASE_SEARCH_URL}?page={page}').find_all('div', class_='search-results-text')
        if len(projects) == 0:
            break
        else:
            print(f'Extracting {len(projects)} docs from page #{page}...')
            for i, project in enumerate(projects):
                if (project_url_doc := project.find('a', href=True)) is not None:
                    yield __extract(project_url_doc['href'])
                    print(f'Extracted {i + 1} of {len(projects)}')

            page = next_page_func(page)

def __extract(url):
    article_link = BASE_URL + url

    doc = read_html(article_link)

    title = None
    if (title_doc := doc.find('h1')) is not None:
        title = title_doc.get_text().strip()

    source_links = []

    if (download_button_doc := doc.find('a', string='Download')) is not None:
        download_page_doc = read_html(BASE_URL + download_button_doc['href'])

        downloadable_source_docs = download_page_doc.find_all(__downloadable_source_search_condition)

        for downloadable_source_doc in downloadable_source_docs:
            download_link = downloadable_source_doc['href']
            file_type = __extract_file_type(downloadable_source_doc.find('span').get_text())

            if file_type is not None:
                source_links.append(SourceLink(download_link, file_type))

    doi = None
    if (doi_doc := doc.find('div', class_='doi')) is not None:
        if (doi_a_doc := doi_doc.find('a')) is not None:
            doi = doi_a_doc['href']

    revision_date = None
    if (revision_date_doc := doc.find('span', class_='article-date')) is not None:
        revision_date = revision_date_doc.get_text()

    authors = __extract_authors(doc)

    doc_license = __extract_license(doc)

    abstract = __extract_abstract(doc)

    return SourcedDocumentMetadata(
        title=title,
        source_corpus=DocumentSourceCorpus.WRI,
        sourced_at=datetime.now(),
        source_links=source_links,
        authors=authors,
        doi=doi,
        page_link=article_link,
        abstract=abstract,
        revision_date=revision_date,
        license=doc_license
    )

def __downloadable_source_search_condition(tag: Tag):
    if tag.name != 'a':
        return False
    if tag.find('span') is None:
        return False

    return True

def __extract_file_type(text):
    for file_type in ALLOWED_FILE_TYPES:
        if file_type in text:
            return file_type

    return None

def __extract_abstract(doc: Tag):
    if (abstract_doc := doc.find('div', class_='main-content')) is not None:
        for tag in abstract_doc.find_all(["figure", "iframe"]):
            tag.decompose()

        text_parts = []
        for el in abstract_doc.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = el.get_text(strip=True)
            if text:
                text_parts.append(text)

        clean_text = "\n\n".join(text_parts)
        return clean_text

    return None

def __extract_authors(doc: Tag):
    if (authors_doc := doc.find('div', class_='field-name-field-authors')) is not None:
        content = [sub_doc.get_text() for sub_doc in authors_doc.find_all() if sub_doc.get_text() != 'Authors']
        return content

    return []

def __extract_license(doc: Tag):
    if (license_doc := doc.find('div', class_='field-name-field-license')) is not None:
        return license_doc.find(text=True, recursive=False).strip()

    return None

