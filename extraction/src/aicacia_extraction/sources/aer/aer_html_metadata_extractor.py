import json
import random
from datetime import datetime
from urllib.parse import quote_plus

from aicacia_document_exporter.Document import Document, DocumentChunk

from aicacia_extraction.sources.io_utils import read_html, read_json


class AerSimpleExtractor:
    def __init__(self):
        self.base_search_url = 'https://www.britishecologicalsociety.org/applied-ecology-resources/search'
        self.wiley_api_url_base = 'https://api.wiley.com/onlinelibrary/tdm/v1/articles'
        self.crossref_api_url_base = 'https://api.crossref.org/works'

    def extract(self, start_page=1, page_limit=-1, reversed_traversal=True):
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

        return self.traverse_and_extract(
            start_page, last_page,
            (lambda page: page - 1) if reversed_traversal else (lambda page: page + 1),
            (lambda page, last: page >= last) if reversed_traversal else (lambda page, last: page <= last)
        )

    def traverse_and_extract(self, start_page, last_page, next_page_func, break_condition_func):
        page = start_page

        while last_page < 0 or break_condition_func(page, last_page):
            articles = read_html(f'{self.base_search_url}/page/{page}').find_all('div', class_='faux-block-container')
            if len(articles) == 0:
                break
            else:
                print(f'Extracting {len(articles)} docs from page #{page}...')

                for i, project in enumerate(articles):
                    if (project_url_doc := project.find('a', href=True)) is not None:
                        yield self.__extract(project_url_doc['href'])
                        print(f'Extracted {i + 1} of {len(articles)}')

                page = next_page_func(page)

    def __extract(self, url):
        doc = read_html(url)

        if doc is None:
            return None

        if (article_doc := doc.find('div', class_='bleed-area')) is not None:
            title = None
            if (title_doc := article_doc.find('h1')) is not None:
                title = title_doc.get_text().strip()

            if (meta_details_doc := article_doc.find('div', class_='document-meta__details')) is not None:
                revision_date = None
                if (label_doc := meta_details_doc.find('dt', string='Published online')) is not None:
                    revision_date = datetime.strptime(label_doc.find_next('dd').get_text(), '%d %b %Y')

                content_type = None
                if (label_doc := meta_details_doc.find('dt', string='Content type')) is not None:
                    content_type = label_doc.find_next('dd').get_text()

                journal_title = None
                if (label_doc := meta_details_doc.find('dt', string='Journal title')) is not None:
                    journal_title = label_doc.find_next('dd').get_text()

                doi = None
                if (label_doc := meta_details_doc.find('dt', string='DOI')) is not None:
                    doi = label_doc.find_next('a').get_text()

                authors = []
                if (label_doc := meta_details_doc.find('dt', string='Author(s)')) is not None:
                    authors = label_doc.find_next(lambda tag: tag.name == 'a' and tag.text.strip()).get_text()
                    authors = [author.strip() for author in authors.split('&')]

                contact_emails = None
                if (label_doc := meta_details_doc.find('dt', string='Contact email(s)')) is not None:
                    contact_emails = label_doc.find_next('dd').get_text()

                language = None
                if (label_doc := meta_details_doc.find('dt', string='Publication language')) is not None:
                    language = label_doc.find_next('dd').get_text()

                location = None
                if (label_doc := meta_details_doc.find('dt', string='Location')) is not None:
                    location = label_doc.find_next('dd').get_text()

                chunks = []
                if (label_doc := article_doc.find('h2', string='Abstract')) is not None:
                    abstract = DocumentChunk(
                        content=label_doc.find_next('p').prettify(),
                        media_type='text/html',
                        token_offset_position=0,
                        sequence_number=0,
                        metadata={
                            'semantic_position': 'Abstract'
                        }
                    )

                    chunks.append(abstract)

                provided_tags = []
                if (tags_list_doc := article_doc.find('ul', class_='key-words')) is not None:
                    for tag_doc in tags_list_doc.find_all('li'):
                        provided_tags.append(tag_doc.get_text())

                sources = []
                if (source_doc := article_doc.find('div', class_='document-meta__download')) is not None:
                    source_link_doc = source_doc.find_next('a')

                    source_button_text = source_link_doc.get_text()

                    if source_button_text in ['View', 'Download']:
                        page_link = source_link_doc['href']
                        source = {'page_link': page_link} | self.__resolve_optional_info(page_link, source_button_text)
                        sources.append(json.dumps(source))

                doc_id = f'AER_{url.rstrip("/").split("/")[-1]}_{random.randint(1, 1000)}'

                return Document(
                    id=doc_id,
                    title=title,
                    chunks=chunks,
                    revision_date=revision_date,
                    sources=sources,
                    doi=doi,
                    link=url,
                    location=location,
                    corpus_name='AER',
                    authors=authors,
                    provided_tags=provided_tags,
                    metadata={
                        'content_type': content_type,
                        'journal_title': journal_title,
                        'contact_emails': contact_emails,
                        'language': language
                    }
                )

    def __resolve_optional_info(self, page_link, source_button_text):
        if source_button_text == 'Download' and 'pdf' in page_link:
            return {'pdf_download_link': page_link}
        elif source_button_text == 'View':
            doi = "/".join(page_link.rstrip("/").split("/")[-2:])
            if doi:
                try:
                    crossref_metadata_url = f'{self.crossref_api_url_base}/{doi}'
                    crossref_metadata = read_json(crossref_metadata_url)
                    publisher = crossref_metadata['message']['publisher']
                    if publisher == 'Wiley':
                        return {
                            'pdf_download_link': f'{self.wiley_api_url_base}/{quote_plus(doi)}',
                            'publisher': publisher,
                            'crossref_metadata_url': crossref_metadata_url
                        }
                    else:
                        return {
                            'publisher': publisher,
                            'crossref_metadata_url': crossref_metadata_url
                        }
                except Exception as e:
                    print(f"Couldn't get crossref metadata: doi={doi}, ex={e}")
        return {}

    # @staticmethod
    # def __extract_source_type(source_link, source_button_text):
    #     source_type = None
    #
    #     if source_button_text == 'View':
    #         source_type = 'application/xml'
    #     elif source_button_text == 'Download' and 'pdf' in source_link:
    #         source_type = 'application/pdf'
    #
    #     return source_type
