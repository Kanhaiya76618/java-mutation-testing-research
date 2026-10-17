"""
tests/test_pitfall_analysis.py
Unit tests for scripts/pitfall_analysis.py and harness/paper_numbers.py, using the worked
example of tests/test_kill_matrix.py (t6 reveals the bug and is the test the fix added).
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from harness import paper_numbers
from harness.kill_matrix import KillMatrix
from scripts.pitfall_analysis import placebo_deltas, sign_test
from tests.test_kill_matrix import COVERING, KILLERS, OPERATORS, TESTS


class TestPitfallAnalysis(unittest.TestCase):
    def setUp(self):
        self.pair = {
            "matrix": KillMatrix.from_lists(TESTS, KILLERS, COVERING, OPERATORS),
            "added": ["t6"],
            "fault_revealing": ["t6"],
        }

    def test_placebo_removes_only_non_revealing_tests(self):
        # Removing t1 or t3 loses a mutant only they kill (-20 points); removing t2, t4 or t5 loses nothing,
        # so the placebo gain is 20 in 2 of 5 cases, and the real gain (removing t6) is 20 as well.
        deltas = placebo_deltas(self.pair, draws=5000, rng=np.random.default_rng(7))
        self.assertEqual(set(np.round(deltas, 6)), {0.0, 20.0})
        self.assertAlmostEqual((deltas >= 20.0).mean(), 0.4, delta=0.03)

    def test_sign_test(self):
        self.assertAlmostEqual(sign_test(np.array([1.0] * 10)), 2 / 1024)
        self.assertEqual(sign_test(np.zeros(5)), 1.0)
        self.assertAlmostEqual(sign_test(np.array([1.0, -1.0])), 1.0)


class TestPaperNumbers(unittest.TestCase):
    def test_macros_are_written_and_validated(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(paper_numbers, "GENERATED_DIR", Path(d)):
            path = paper_numbers.write_macros("x.tex", {"NaiveSignP": "0.002"}, "test")
            self.assertIn("\\newcommand{\\NaiveSignP}{0.002}", path.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                paper_numbers.write_macros("y.tex", {"Bad1Name": "1"}, "test")

    def test_tex_escape(self):
        self.assertEqual(paper_numbers.tex_escape("RC_EQUAL_IF 5%"), r"RC\_EQUAL\_IF 5\%")


if __name__ == "__main__":
    unittest.main()
