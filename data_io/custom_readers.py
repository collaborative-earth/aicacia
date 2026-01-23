from tqdm import tqdm
import os
import boto3
from llama_index.core.schema import Document

class S3ReaderBase:
    def __init__(self, bucket_name: str, aws_key: str, aws_secret: str, prefix: str):
        self.bucket_name = bucket_name
        self.client = boto3.client(
            "s3",
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
        )
        self.prefix = prefix

    def list_keys(self) -> list[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)
        return [el["Key"] for page in page_iterator for el in page.get("Contents", [])]

    def read_bytes(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def load_documents(self) -> list[Document]:
        documents = []
        for key in tqdm(self.list_keys(), desc="Downloading S3 documents"):
            raw = self.read_bytes(key)
            filename = os.path.basename(key)
            doc_id, *_ = filename.split(".", 1)
            documents.append(
                Document(
                    doc_id=doc_id,
                    text=raw.decode("utf-8"),
                    metadata={"source": self.prefix},
                )
            )
        return documents