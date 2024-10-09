import os
import unittest

from pathlib import Path


class TestMarkerDocument(unittest.TestCase):
    def test_marker_document(self):
        # Given
        tests_path = Path(os.path.dirname(__file__))
        md_path = tests_path / "../example/marker/multicolcnn.md"

        # When
        document = None

if __name__ == '__main__':
    unittest.main()
