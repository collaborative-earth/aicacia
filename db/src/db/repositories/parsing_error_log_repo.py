from typing import Any
from db.repositories.base_model_repo import BaseModelRepository
from db.models.sourced_documents import DataPipelineErrorLog
from sqlmodel import Session, insert


class DataPipelineErrorLogRepository(BaseModelRepository[DataPipelineErrorLog]):
    def __init__(self) -> None:
        super().__init__(DataPipelineErrorLog)

    def bulk_create(
        self,
        session: Session,
        logs: list[dict[Any, Any]]
    ) -> int:
        stmt = (
            insert(DataPipelineErrorLog)
            .values(logs)
        )
        res = session.exec(stmt)
        return res.rowcount
        # session.commit()  # Commit should be handled by the caller
