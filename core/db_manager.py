from contextlib import contextmanager
from sqlmodel import create_engine, Session
from core.app_config import configs


# Reference: originally from api.server.db.session.py
engine = create_engine(configs.get_database_url(), echo=True)


def get_db_session():
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope():
    """Provide a transactional scope around a block of code.
    sample usage:
    with session_scope() as session:
        # do stuff with session
    """
    # for the CLI and other non-request uses

    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise


class DBManager:
    # TODO. Implement actual DB manager
    def __init__(self) -> None:
        pass

    def connect(self, db_type: str) -> None:
        pass

    def get_ready_to_ingest_files(self) -> list[str]:
        # TODO. Implement actual logic to get parsed filepaths from DB
        return [
            "s3://k-bckt/parsed_outputs/04c6508e-7332-11f0-bc9a-0242ac1c000c.grobid.tei.xml",
            "s3://k-bckt/parsed_outputs/04c6508e-7332-11f0-bc9a-0242ac1c000c_copy.grobid.tei.xml"
        ]


# TODO. Load config from env
db_manager = DBManager()
