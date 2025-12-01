class DBManager:
    # TODO. Implement actual DB manager
    def __init__(self) -> None:
        pass

    def connect(self, db_type: str) -> None:
        pass

    def get_ready_to_parse_files(self) -> list[str]:
        # TODO. Implement actual logic to get filepaths from DB
        return [
            "s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c.pdf",
            "s3://k-bckt/aer/04c6508e-7332-11f0-bc9a-0242ac1c000c_copy.pdf"
        ]

    def get_ready_to_ingest_files(self) -> list[str]:
        # TODO. Implement actual logic to get parsed filepaths from DB
        return [
            "s3://k-bckt/parsed_outputs/04c6508e-7332-11f0-bc9a-0242ac1c000c.grobid.tei.xml",
            "s3://k-bckt/parsed_outputs/04c6508e-7332-11f0-bc9a-0242ac1c000c_copy.grobid.tei.xml"
        ]


# TODO. Load config from env
db_manager = DBManager()
