import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import sqlite3
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server import models


def __map_ref(record: dict):
    return record["reference"]


def __map_document(cur, record: dict):
    doc_id = record["id"]

    result = [models.Document(
        doc_id=doc_id,
        title=record["title"],
        raw_content=record["raw_content"],
        authors=[author.strip() for author in record["authors"].split(";")],
        doi=record["doi"],
        link=record.get("link", None),
        content_hash=record["content_hash"],
        corpus_name=record["corpus_name"],
        sources=[source for source in record["sources"].split(";")],
        location=record["location"],
        sourced_date=record["sourced_date"],
        revision_date=record["revision_date"],
        references=[__map_ref(ref) for ref in __fetch_all(cur, "refs", doc_id=doc_id)],
        generated_metadata=record["metadata"]
    )]

    for tag in [s for s in record["provided_tags"].split(";") if s]:
        result.append(models.DocumentTag(
            doc_id=doc_id,
            value=tag,
            generated=False
        ))

    for tag in [s for s in record["generated_tags"].split(";") if s]:
        result.append(models.DocumentTag(
            doc_id=doc_id,
            value=tag,
            generated=True
        ))

    return result


def __map_section(record: dict):
    return models.DocumentChunk(
        doc_id=record["doc_id"],
        sequence_number=None,
        content=record["content"],
        media_type=record["media_type"],
        token_offset_position=record["token_offset_position"],
        generated_metadata=record["metadata"]
    )


def __map_chunk(record: dict):
    return models.DocumentChunk(
        doc_id=record["doc_id"],
        sequence_number=record["sequence_number"],
        content=record["content"],
        media_type=record["media_type"],
        token_offset_position=record["token_offset_position"],
        generated_metadata=record["metadata"]
    )


def __fetch_all(cur, table, doc_id=None):
    if doc_id is None:
        cur.execute(f"SELECT * FROM {table}")
    else:
        cur.execute(f"SELECT * FROM {table} WHERE doc_id=?", (doc_id,))
    return sqlite_cur.fetchall()


def __check_sqlite_table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    result = cur.fetchone()
    return result is not None


parser = argparse.ArgumentParser(description="sqlite -> postgresql migration script")

parser.add_argument('input_dir', type=str, help='Path to the dir with sqlite files')
parser.add_argument('--db_user', type=str, default='postgres')
parser.add_argument('--db_pass', type=str)
parser.add_argument('--db_host', type=str, default='localhost:5432')
parser.add_argument('--db_name', type=str, default='aicacia_db')

args = parser.parse_args()

input_dir = args.input_dir
db_user = args.db_user
db_pass = args.db_pass
db_host = args.db_host
db_name = args.db_name

database_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"

engine = create_engine(database_url)

session = sessionmaker(bind=engine)()

for input_file in os.listdir(input_dir):
    if not input_file.endswith(".db"):
        continue

    input_file = os.path.join(input_dir, input_file)

    print(f"Adding {input_file}...")

    with sqlite3.connect(input_file) as sqlite_conn:
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        print(f"Parsing docs table ({input_file})...")

        for doc_record in __fetch_all(sqlite_cur, "docs"):
            for obj in __map_document(sqlite_cur, dict(doc_record)):
                session.add(obj)

        session.commit()

        print(f"Parsing chunks table ({input_file})...")

        # Old version
        if __check_sqlite_table_exists(sqlite_cur, "sections"):
            for section_record in __fetch_all(sqlite_cur, "sections"):
                session.add(__map_section(dict(section_record)))
        # New version
        else:
            for chunk_record in __fetch_all(sqlite_cur, "chunks"):
                session.add(__map_chunk(dict(chunk_record)))

        session.commit()

        print(f"Successfully added data ({input_file})!")

session.close()
