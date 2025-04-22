import boto3
import psycopg
import urllib.request

def upload_wri_pdfs_to_s3(pg_url, bucket_name):
    query = """
        select distinct on (doc_id) doc_id, link 
        from source_links 
        where type = 'application/pdf' 
        order by doc_id, updated_at
    """

    with psycopg.connect(pg_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            links = cur.fetchall()

            for doc_id, link in links:
                print(doc_id, link)

if __name__ == '__main__':
    upload_wri_pdfs_to_s3("postgresql://postgres:aicacia@3.137.35.87:5432/aicacia_db", "aicacia-extracted-data")
