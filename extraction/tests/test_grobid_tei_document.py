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
        self.assertEqual(
            [
                "We describe in this paper a new method for building an efficient algorithm for scheduling jobs in a cluster. Jobs are considered as parallel tasks (PT) which can be scheduled on any number of processors. The main feature is to consider two criteria that are optimized together. These criteria are the makespan and the weighted minimal average completion time (minsum). They are chosen for their complementarity, to be able to represent both user-oriented objectives and system administrator objectives.",
                "We propose an algorithm based on a batch policy with increasing batch sizes, with a smart selection of jobs in each batch. This algorithm is assessed by intensive simulation results, compared to a new lower bound (obtained by a relaxation of ILP) of the optimal schedules for both criteria separately. It is currently implemented in an actual real-size cluster platform."
            ],
            tei_document.abstract
        )
        self.assertEqual(["Lionel Eyraud", "Gr Égory Mouni", "Denis Trystram"], tei_document.authors)
        self.assertEqual(
            [
                "F.2.2 [Analysis of Algorithms and Problem Complexity]: Nonnumerical Algorithms and Problems-Sequencing and scheduling; D.4.1 [Operating Systems]: Process management-Scheduling",
                "Concurrency General Terms Algorithms",
                "Management Parallel Computing",
                "Algorithms",
                "Scheduling",
                "Parallel Tasks",
                "Moldable Tasks",
                "Bi-criteria"
            ],
            tei_document.keywords
        )
        self.assertEqual(IDNOType.MD5, tei_document.idno.type)
        self.assertEqual("5F0BE4D19AC38AC86BE01245CF0BEAF4", tei_document.idno.value)
        self.assertEqual("Bi-criteria Algorithm for Scheduling Jobs on Cluster Platforms", tei_document.title)


if __name__ == '__main__':
    unittest.main()
