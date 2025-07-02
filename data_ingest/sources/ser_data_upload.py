import boto3
import psycopg
import urllib.request

def upload_ser_jsons_to_s3(pg_url, bucket_name):
    query = """
        select doc_id, id, link 
        from source_links 
        where type = 'application/json' and link like '%app.ser-rrc.org%'
    """

    s3_client = boto3.client("s3")

    with psycopg.connect(pg_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            links = cur.fetchall()

            for i, (doc_id, link_id, link) in enumerate(links):
                print(f"Downloading and saving file: {link} ({i}/{len(links)})")

                object_key = f'ser/{doc_id}.json'

                try:
                    urllib.request.urlretrieve(link, './temp.json')

                    with open("./temp.json", "rb") as f:
                        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=f)
                        cur.execute("update source_links set s3_location = %s where id = %s", (object_key, link_id,))
                        conn.commit()

                except Exception as error:
                    print(f"Exception occurred for: {link}")
                    print(error)


if __name__ == '__main__':
    upload_ser_jsons_to_s3("<DB_URL>", "aicacia-extracted-data")
