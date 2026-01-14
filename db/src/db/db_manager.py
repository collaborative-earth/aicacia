from contextlib import contextmanager

from sqlmodel import Session, create_engine

from core.app_config import configs

# Reference: originally from api.server.db.session.py
engine = create_engine(configs.get_database_url(), echo=False)


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
