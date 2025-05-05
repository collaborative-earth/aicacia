from sqlmodel import create_engine, Session
from server.core.config import settings

user = settings.POSTGRES_USER
password = settings.POSTGRES_PASSWORD
host = settings.POSTGRES_HOST
port = settings.POSTGRES_PORT
db = settings.POSTGRES_DB

database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(database_url, echo=True)


def get_db_session():
    with Session(engine) as session:
        yield session