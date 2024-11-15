import csv
import os

from aicacia_document_exporter.Document import Document
from aicacia_document_exporter.PreprocessingModel import PreprocessingModel
from aicacia_document_exporter.SimpleFileDocumentExporter import (
    SimpleFileDocumentExporter,
)
from bs4 import BeautifulSoup
from markdownify import markdownify as md

data_dir = "../../../../../scrapping/implementation_fao_good_practices/temp/"
db_file_name = "fao_good_practices_metadata.db"

if not os.path.exists(f"{data_dir}markdown"):
    os.makedirs(f"{data_dir}markdown")

if not os.path.exists(f"{data_dir}markdown/fao_good_practices"):
    os.makedirs(f"{data_dir}markdown/fao_good_practices")

if not os.path.exists(f"{data_dir}markdown/fao_good_practices/lifegopro"):
    os.makedirs(f"{data_dir}markdown/fao_good_practices/lifegopro")

if not os.path.exists(f"{data_dir}markdown/fao_good_practices/qcat_wocat"):
    os.makedirs(f"{data_dir}markdown/fao_good_practices/qcat_wocat")

if not os.path.exists(f"{data_dir}markdown/fao_good_practices/panorama_solutions"):
    os.makedirs(f"{data_dir}markdown/fao_good_practices/panorama_solutions")


class GoodPractice:
    def __init__(self, title, description, url, domain):
        self.title = title
        self.description = description
        self.url = url
        self.domain = domain


def _extract_metadata_from_panorama_solutions(html, metadata):
    soup = BeautifulSoup(html, "html.parser")

    # Extract location (Country and Region)
    location_div = soup.find("div", class_="solution-location")
    if location_div:
        country = (
            location_div.find("div", class_="field--name-field-location").get_text(
                strip=True
            )
            if location_div.find("div", class_="field--name-field-location")
            else "Country not found"
        )
        region = (
            location_div.find("div", class_="field--name-field-region").get_text(
                strip=True
            )
            if location_div.find("div", class_="field--name-field-region")
            else "Region not found"
        )
    else:
        country = "Location section not found"
        region = ""

    # Extract tags
    tags_div = soup.find("div", class_="solution-tags tags-list")
    if tags_div:
        tags = [
            tag.get_text(strip=True)
            for tag in tags_div.find_all("div", class_="field__item")
        ]
    else:
        tags = []

    # Extract author/organisation
    author_div = soup.find("div", class_="hero-author-org")
    if author_div:
        author_div = author_div.find(
            "div", class_="field--name-field-solution-organisation"
        )
        if author_div:
            author = author_div.get_text(strip=True)
        else:
            author = "Author not found"
    else:
        author = "Author not found"

    # Extract last updated date
    last_update_div = soup.find("div", class_="solution-statistics h-wrapper-small")
    if last_update_div:
        last_updated = (
            last_update_div.find("b").get_text(strip=True)
            if last_update_div.find("b")
            else "Last update not found"
        )
    else:
        last_updated = "Last update section not found"

    metadata["country"] = country
    metadata["region"] = region
    metadata["tags"] = tags
    metadata["author"] = author
    metadata["last_updated"] = last_updated

    return metadata


def _extract_metadata_from_qcat_wocat(html, metadata):
    soup = BeautifulSoup(html, "html.parser")

    # Extract Creation Date
    creation_time = (
        soup.find("span", text="Creation:").find_next("time").get_text(strip=True)
    )

    # Extract Update Date
    update_time = (
        soup.find("span", text="Update:").find_next("time").get_text(strip=True)
    )

    # Extract Editor
    editor_li = soup.find("span", text="Editor:")
    editor = (
        editor_li.get_text(strip=True).replace("Editor:", "").strip()
        if editor_li
        else "No editor found"
    )

    metadata["creation_time"] = creation_time
    metadata["update_time"] = update_time
    metadata["editor"] = editor

    return metadata


class Preprocess(PreprocessingModel):
    def preprocess_batch(self, docs: list[Document]):
        pass


class FaoGoodPracticesExtractor:

    def _list_files(self, path):
        files = os.listdir(path)
        return files

    def _remove_special_characters(self, filename):
        return "".join(e for e in filename if e.isalnum())

    def _document_to_source_maps(self):
        map = {}
        with open(f"{data_dir}/good_practices_list.csv", newline="") as csvfile:
            good_practices = csv.reader(csvfile, delimiter=",", quotechar="|")
            for i, good_practice in enumerate(good_practices):
                if i == 0:
                    continue
                gp = GoodPractice(
                    title=good_practice[0],
                    description=good_practice[1],
                    url=good_practice[-2],
                    domain=good_practice[-1],
                )
                map[self._remove_special_characters(f"{i}_{gp.title}")] = gp

        return map

    def _extract_metadata(self, html, doc):
        metadata = {"document_url": doc.source}
        if doc.corpus_name == "fao_good_practices/lifegopro":
            doc.metadata = metadata
        if doc.corpus_name == "fao_good_practices/qcat_wocat":
            doc.metadata = _extract_metadata_from_qcat_wocat(html, metadata)
        if doc.corpus_name == "fao_good_practices/panorama_solutions":
            doc.metadata = _extract_metadata_from_panorama_solutions(html, metadata)
        return metadata

    def _extract_doc(self, file, directory, corpus_name, document_map):
        with open(data_dir + directory + file, "r") as f:
            html = f.read()
            markdown = md(html)

            file_name_without_extension = " ".join(file.split(".")[:-1])

            doc = Document(
                title=file_name_without_extension,
                chunks=[],
            )

            if "Too many requests" in html:
                print(f"Too many requests for {file}")

            doc.raw_content = markdown
            source = None

            sanitized_filename = self._remove_special_characters(
                file_name_without_extension
            )

            if sanitized_filename in document_map:
                source = document_map[sanitized_filename].url

            doc.source = source
            doc.corpus_name = corpus_name
            doc.metadata = self._extract_metadata(html, doc)
            return doc

    def extract(self):
        documents = []
        document_map = self._document_to_source_maps()
        missing_sources = []
        duplicate_files = {}
        directory = "lifegopro/"
        corpus_name = "fao_good_practices/lifegopro"
        for file in self._list_files(data_dir + directory):
            documents.append(
                self._extract_doc(file, directory, corpus_name, document_map)
            )
            if documents[-1].source is None:
                missing_sources.append(file)

        corpus_name = "fao_good_practices/qcat_wocat"
        directory = "qcat_wocat/html/"
        for file in self._list_files(data_dir + directory):
            documents.append(
                self._extract_doc(file, directory, corpus_name, document_map)
            )
            if documents[-1].source is None:
                missing_sources.append(file)

        corpus_name = "fao_good_practices/panorama_solutions"
        directory = "panorama_solutions/"
        for file in self._list_files(data_dir + directory):
            documents.append(
                self._extract_doc(file, directory, corpus_name, document_map)
            )
            if documents[-1].source is None:
                missing_sources.append(file)

        for missing in missing_sources:
            print(self._remove_special_characters(missing.split(".")[0]))

        for doc in documents:
            if doc.source in duplicate_files:
                duplicate_files[doc.source].append(doc)
            else:
                duplicate_files[doc.source] = [doc]

        docs_to_return = []
        for source, docs in duplicate_files.items():
            count = len(docs)
            if count > 1:
                print(f"Duplicate sources: {source}, count: {count}")
            docs_to_return.append(docs[0])

        print(
            f"Total documents: {len(documents)}, documents to return: {len(docs_to_return)}"
        )

        for doc in docs_to_return:
            with open(
                f"{data_dir}/markdown/{doc.corpus_name}/{doc.title}.md", "w"
            ) as f:
                f.write(doc.raw_content)

        return docs_to_return


extractor = FaoGoodPracticesExtractor()

with SimpleFileDocumentExporter(
    f"{data_dir}/{db_file_name}", preprocessing_model=Preprocess()
) as exporter:
    for doc in extractor.extract():
        exporter.insert([doc])

print("Finished extraction!")
