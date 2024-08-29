from config import settings
from sqlmodel import Session, create_engine


def get_db_session() -> Session:
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    host = settings.POSTGRES_HOST
    port = settings.POSTGRES_PORT
    db = settings.POSTGRES_DB

    database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    print(database_url)

    engine = create_engine(database_url)

    with Session(engine) as session:
        return session
