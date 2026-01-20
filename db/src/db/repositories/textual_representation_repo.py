from sqlalchemy import CursorResult
from sqlmodel import Session, insert
from typing import Any, Sequence
from db.repositories.base_model_repo import BaseModelRepository
from db.models.sourced_documents import TextualRepresentation


class TextualRepresentationRepository(BaseModelRepository[TextualRepresentation]):
    def __init__(self) -> None:
        super().__init__(TextualRepresentation)

    def bulk_create(
        self,
        session: Session,
        textual_representations: Sequence[dict[str, dict]]
    ) -> int:
        stmt = (
            insert(TextualRepresentation)
            .values(textual_representations)
        )
        res: CursorResult[Any] = session.exec(stmt)
        return res.rowcount
        # session.commit()  # Commit should be handled by the caller
