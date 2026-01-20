
from typing import Sequence
from sqlmodel import Session, select, col, update
from data_ingestion.custom_types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import SourcedDocument
from db.repositories.base_model_repo import BaseModelRepository


class SourcedDocumentRepository(BaseModelRepository[SourcedDocument]):
    def __init__(self) -> None:
        super().__init__(SourcedDocument)

    def get_ready_to_parse_files(self, session: Session) -> Sequence[SourcedDocument]:
        '''Get all documents with status NEW and s3_path is not None'''
        stmt = (
            select(SourcedDocument)
            .where(
                SourcedDocument.current_status == CurrentStatusEnum.NEW.value,  # TODO: should it be DOWNLOADED?
                SourcedDocument.s3_path is not None
            )
        )

        results: Sequence[SourcedDocument] = session.exec(stmt).all()
        return results

    def update_status_by_s3_path(
        self,
        session: Session,
        s3_path: str,
        new_status: str
    ) -> None:
        stmt = (
            select(SourcedDocument)
            .where(SourcedDocument.s3_path == s3_path)
        )
        document: SourcedDocument | None = session.exec(stmt).first()
        if document:
            document.current_status = new_status
            session.add(document)
            # session.commit()  # Commit should be handled by the caller

    def get_document_by_s3_path(self, session: Session, s3_path: str) -> SourcedDocument | None:
        stmt = (
            select(SourcedDocument)
            .where(SourcedDocument.s3_path == s3_path)
        )

        sourced_document = session.exec(stmt).first()
        return sourced_document

    def get_documents_by_filepaths(
        self,
        session: Session,
        filepaths: Sequence[str | None]
    ) -> Sequence[SourcedDocument]:

        if not filepaths:
            return []

        stmt = (
            select(SourcedDocument)
            .where(col(SourcedDocument.s3_path).in_(filepaths))
        )

        sourced_documents = session.exec(stmt).all()
        return sourced_documents

    def get_documents_by_doc_ids(
        self,
        session: Session,
        doc_ids: Sequence[str]
    ) -> Sequence[SourcedDocument]:
        stmt = (
            select(SourcedDocument)
            .where(col(SourcedDocument.doc_id).in_(doc_ids))
        )
        sourced_documents = session.exec(stmt).all()
        return sourced_documents

    def bulk_update_status_by_doc_ids(
        self,
        session: Session,
        doc_ids: Sequence[str],
        new_status: str
    ) -> int:
        stmt = (
            update(SourcedDocument)
            .where(col(SourcedDocument.doc_id).in_(doc_ids))
            .values(current_status=new_status)
        )
        res = session.exec(stmt)
        return res.rowcount or 0
        # session.commit()  # Commit should be handled by the caller

