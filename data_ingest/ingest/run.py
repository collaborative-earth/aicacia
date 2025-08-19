import json
import os
from enum import Enum

import boto3
import psycopg
from psycopg.types.json import Json
from sqlmodel import Session, SQLModel, and_, create_engine, select

from api.server.db.models.sourced_documents import SourcedDocument, SourceLink
from data_ingest.entities.Document import SourcedDocumentMetadata
from data_ingest.postprocess.page_layout_detection import detect_pages_layout
from data_ingest.postprocess.pdf_to_images import convert
from data_ingest.postprocess.pdla_output_reader import read_json
from data_ingest.postprocess.postprocess_pdla_output import postprocess
from data_ingest.sources.ser_metadata import extract_ser_metadata
from data_ingest.sources.wri_metadata import extract_wri_metadata, stream_relevant_links


def mark_articles_as_relevant(db_url: str):
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        batch = []

        for doc_link in stream_relevant_links():
            statement = select(SourcedDocument).where(SourcedDocument.page_link == doc_link)
            result: SourcedDocument | None = session.exec(statement).first()

            if result:
                result.is_relevant = True
                batch.append(result)

            if len(batch) > 10:
                session.add_all(batch)
                session.commit()
                batch.clear()

        if batch:
            session.add_all(batch)
            session.commit()
            batch.clear()

# generator is a function that yields SourcedDocumentMetadata objects
def extract_and_save_articles_metadata(db_url: str, generator):
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        batch = []

        for doc in generator: #type: SourcedDocumentMetadata
            db_entity = SourcedDocument(
                title=doc.title,
                source_corpus=doc.source_corpus.value,
                sourced_at=doc.sourced_at,
                source_links=[SourceLink(link=src.link, type=src.type) for src in doc.source_links],
                authors=doc.authors,
                doi=doc.doi,
                page_link=doc.page_link,
                abstract=doc.abstract,
                geo_location=doc.geo_location,
                revision_date=doc.revision_date,
                license=doc.license,
                tags=doc.tags,
                references=doc.references,
                other_metadata=doc.other_metadata
            )

            batch.append(db_entity)

            if len(batch) > 10:
                session.add_all(batch)
                session.commit()
                batch.clear()

        if batch:
            session.add_all(batch)
            session.commit()
            batch.clear()

def run_post_processing(db_cursor, s3_client, doc_id: str):
    bucket_name = 'aicacia-extracted-data'
    source_file = './source.pdf'
    pdla_file = './pdla.json'
    images_dir = './images'

    def recursive_serializer(obj):
        if isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return {key: recursive_serializer(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, (list, tuple)):
            return [recursive_serializer(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: recursive_serializer(value) for key, value in obj.items()}
        else:
            return obj

    print("Downloading source file...")
    with open(source_file, 'wb') as f:
        s3_client.download_fileobj(bucket_name, f'wri/{doc_id}.pdf', f)

    print("Downloading pdla_output file...")
    with open(pdla_file, 'wb') as f:
        s3_client.download_fileobj(bucket_name, f'wri/pdla_output/{doc_id}.json', f)

    print("Extracting pages from source pdf...")
    height, width = convert(source_file, images_dir)
    print("Reading pdla_output file...")
    extracted_elements = read_json(pdla_file, width)
    print("Detecting pages layouts...")
    page_layouts = detect_pages_layout(images_dir, extracted_elements)
    print("Processing...")
    postprocess_result = postprocess(extracted_elements, page_layouts, width, height)

    print("Saving result file in S3...")
    json_result = json.dumps(postprocess_result, default=recursive_serializer, indent=2).encode('utf-8')

    # with open('./result.json', 'wb') as f:
    #     f.write(json_result)

    s3_client.put_object(
        Bucket=bucket_name,
        Key=f'wri/postprocess_output/{doc_id}.json',
        Body=json_result,
        ContentType='application/json'
    )

    print("Saving references in db...")
    if postprocess_result.references:
        db_cursor.execute(
            'UPDATE sourced_documents SET "references" = %s WHERE doc_id = %s',
            [Json(postprocess_result.references), doc_id]
        )

    print("Cleaning up...")
    os.remove(source_file)
    os.remove(pdla_file)
    for f in os.listdir(images_dir):
        os.remove(os.path.join(images_dir, f))


def run_post_processing_for_all_relevant(db_url):
    conn = psycopg.connect(db_url)
    conn.autocommit = True

    cursor = conn.cursor()

    cursor.execute('SELECT doc_id FROM sourced_documents WHERE is_relevant = TRUE')
    relevant_doc_ids = [str(doc_id) for (doc_id, ) in cursor.fetchall()]

    print(f"Processing {len(relevant_doc_ids)} articles...")

    client = boto3.client("s3")

    for i, doc_id in enumerate(relevant_doc_ids):
        print(f"Processing {doc_id} ({i+1}/{len(relevant_doc_ids)}):")
        try:
            run_post_processing(cursor, client, doc_id)
        except Exception as e:
            print(f"Exception occurred: {e}")

    cursor.close()
    conn.close()
    client.close()
