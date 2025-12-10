
from typing import Sequence
from sqlmodel import Session, select
from core.db_manager import get_db_session
from data_ingestion.types.current_status_enum import CurrentStatusEnum
from db.models.sourced_documents import SourcedDocument
from db.repositories.base_model_repo import BaseModelRepository


class SourcedDocumentRepository(BaseModelRepository[SourcedDocument]):
    def __init__(self) -> None:
        super().__init__(SourcedDocument)

    def get_ready_to_parse_files(self, session: Session) -> Sequence[SourcedDocument]:
        stmt = (
            select(SourcedDocument)
            .where(
                SourcedDocument.current_status == CurrentStatusEnum.DOWNLOADED.value,
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
