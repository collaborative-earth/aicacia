import json

from aicacia_document_exporter.Document import Document
from bs4 import Tag

from .html_io import read_html


class WriSimpleExtractor:
    def __init__(self):
        self.base_url = 'https://www.wri.org'
        self.base_search_url = 'https://www.wri.org/resources/type/research-65'
        self.allowed_file_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]

    def extract(self, start_page=1, page_limit=-1):
        if page_limit <= 0:
            last_page = -1
        else:
            last_page = start_page + page_limit - 1

        return self.traverse_and_extract(start_page, last_page)

    def traverse_and_extract(self, start_page, last_page):
        page = start_page

        while last_page < 0 or page <= last_page:
            projects = read_html(f'{self.base_search_url}?page={page}').find_all('div', class_='search-results-text')
            if len(projects) == 0:
                break
            else:
                print(f'Extracting {len(projects)} docs from page #{page}...')
                for i, project in enumerate(projects):
                    if (project_url_doc := project.find('a', href=True)) is not None:
                        yield self.__extract(project_url_doc['href'])
                        print(f'Extracted {i + 1} of {len(projects)}')
                page += 1

    def __extract(self, url):
        article_link = self.base_url + url

        doc = read_html(article_link)

        title = None
        if (title_doc := doc.find('h1')) is not None:
            title = title_doc.get_text().strip()

        downloadable_sources = []

        if (download_button_doc := doc.find('a', string='Download')) is not None:
            download_page_doc = read_html(self.base_url + download_button_doc['href'])

            downloadable_source_docs = download_page_doc.find_all(self.__downloadable_source_search_condition)

            for downloadable_source_doc in downloadable_source_docs:
                download_link = downloadable_source_doc['href']
                file_type = self.__extract_file_type(downloadable_source_doc.find('span').get_text())

                if file_type is not None:
                    downloadable_sources.append(json.dumps({
                        'link': download_link,
                        'type': file_type
                    }))

        doi = None
        if (doi_doc := doc.find('div', class_='doi')) is not None:
            if (doi_a_doc := doi_doc.find('a')) is not None:
                doi = doi_a_doc['href']

        authors = self.__extract_authors(doc)

        return Document(
            title=title,
            sections=[],
            doi=doi,
            authors=authors,
            sources=downloadable_sources,
            corpus_name='WRI',
            metadata={
                'article_link': article_link
            }
        )

    @staticmethod
    def __downloadable_source_search_condition(tag: Tag):
        if tag.name != 'a':
            return False
        if tag.find('span') is None:
            return False

        return True

    def __extract_file_type(self, text):
        for file_type in self.allowed_file_types:
            if file_type in text:
                return file_type

        return None

    @staticmethod
    def __extract_authors(doc: Tag):
        if (authors_doc := doc.find('div', class_='field-name-field-authors')) is not None:
            content = [sub_doc.get_text() for sub_doc in authors_doc.find_all() if sub_doc.get_text() != 'Authors']
            return content

        return []
