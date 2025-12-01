from data_ingestion.parsing.parsers.pymupdf_parser import PyMuPDFParser
from data_ingestion.parsing.parsing_handler import ParsingHandler


def main():
    print("In main!")

    filepaths = ["data/wri_paper1.pdf"]
    default_parser = PyMuPDFParser()
    output_folder: str = "data/"

    parsing_handler = ParsingHandler(fs=None, local_folder='', default_parser=default_parser)

    documents = parsing_handler.parse_filepaths(filepaths, output_folder)
    return documents


# if __name__ == "__main__":
#     main()
