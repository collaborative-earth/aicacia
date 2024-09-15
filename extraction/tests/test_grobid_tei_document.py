import os
import unittest

from aicacia_extraction.grobid import IDNO, IDNOType, TEIDocument
from pathlib import Path


class TestGROBIDTEIDocument(unittest.TestCase):

    def test_tei_document(self):
        # Given
        tests_path = Path(os.path.dirname(__file__))
        tei_path = tests_path / "../example/grobid/sample.grobid.tei.xml"

        # When
        tei_document = TEIDocument(tei_path)

        # Then
        self.assertEqual(["Lionel Eyraud", "Gr Égory Mouni", "Denis Trystram"], tei_document.authors)
        self.assertEqual(IDNOType.MD5, tei_document.idno.type)
        self.assertEqual("5F0BE4D19AC38AC86BE01245CF0BEAF4", tei_document.idno.value)
        self.assertEqual("Bi-criteria Algorithm for Scheduling Jobs on Cluster Platforms", tei_document.title)


if __name__ == '__main__':
    unittest.main()
