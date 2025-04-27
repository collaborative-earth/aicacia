from sqlmodel import SQLModel, create_engine, Session, select
from data_ingest.entities.Document import SourcedDocumentMetadata
from data_ingest.sources.wri_metadata import extract_wri_metadata, stream_relevant_links
from api.server.models import SourcedDocument, SourceLink

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

def extract_and_save_articles_metadata(db_url: str):
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        batch = []

        for doc in extract_wri_metadata(start_page=0, page_limit=70, reversed_traversal=False): #type: SourcedDocumentMetadata
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
