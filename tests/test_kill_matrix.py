"""
tests/test_kill_matrix.py
Unit tests for harness/kill_matrix.py, using the worked example from the step 2 explanation:

    6 tests t1..t6, t6 catches the bug.   m1 killed by t1        m2 killed by t2, t6
    5 mutants:                             m3 killed by t6        m4 killed by t3
                                           m5 killed by nobody (run by t4, t5)
"""

import itertools
import unittest

import numpy as np

from harness.kill_matrix import KillMatrix, a12, random_subsets
from harness.pit_parser import key_from_test_name

TESTS = ["t1", "t2", "t3", "t4", "t5", "t6"]
KILLERS = [{"t1"}, {"t2", "t6"}, {"t6"}, {"t3"}, set()]
COVERING = [{"t2"}, set(), {"t1"}, set(), {"t4", "t5"}]
OPERATORS = ["MATH", "MATH", "CONDITIONALS_BOUNDARY", "NULL_RETURNS", "NULL_RETURNS"]


class TestKillMatrix(unittest.TestCase):
    def setUp(self):
        self.km = KillMatrix.from_lists(TESTS, KILLERS, COVERING, OPERATORS)

    def test_scores_of_single_subsets(self):
        subsets = np.array([self.km.mask({"t1", "t6"}), self.km.mask({"t4", "t5"})])
        np.testing.assert_allclose(self.km.scores(subsets), [60.0, 0.0])
        # coverage: {t1,t6} runs m1, m2, m3; {t4,t5} runs only m5
        np.testing.assert_allclose(self.km.scores(subsets, matrix="covers"), [60.0, 20.0])
        # MATH-only score: {t1,t6} kills both MATH mutants (m1, m2)
        np.testing.assert_allclose(self.km.scores(subsets, rows=self.km.operator_rows({"MATH"})), [100.0, 0.0])

    def test_worked_example_all_pairs(self):
        subsets = np.array([self.km.mask(c) for c in itertools.combinations(TESTS, 2)])
        ms = self.km.scores(subsets)
        detects = subsets[:, TESTS.index("t6")]
        self.assertEqual(int(detects.sum()), 5)
        self.assertAlmostEqual(ms[detects].mean(), 48.0)
        self.assertAlmostEqual(ms[~detects].mean(), 24.0)
        self.assertAlmostEqual(a12(ms[detects], ms[~detects]), 0.91)

    def test_old_design_base_vs_aug(self):
        base = self.km.mask({"t1", "t2", "t3", "t4", "t5"})
        aug = self.km.mask(TESTS)
        np.testing.assert_allclose(self.km.scores(np.array([base, aug])), [60.0, 80.0])

    def test_random_subsets_have_exact_size(self):
        subsets = random_subsets(n_tests=6, size=2, count=500, rng=np.random.default_rng(1))
        self.assertTrue((subsets.sum(axis=1) == 2).all())
        # every one of the 15 possible pairs shows up
        self.assertEqual(len({tuple(np.flatnonzero(s)) for s in subsets}), 15)

    def test_a12_edge_cases(self):
        self.assertIsNone(a12(np.array([]), np.array([1.0])))
        self.assertAlmostEqual(a12(np.array([1.0, 1.0]), np.array([1.0])), 0.5)

    def test_key_from_test_name(self):
        name = ("org.apache.commons.lang3.StringUtilsContainsTest.[engine:junit-jupiter]"
                "/[class:org.apache.commons.lang3.StringUtilsContainsTest]/[method:testContainsAny_StringCharArray()]")
        self.assertEqual(key_from_test_name(name), "org.apache.commons.lang3.StringUtilsContainsTest#testContainsAny_StringCharArray")
        nested = "a.FooTest.[engine:junit-jupiter]/[class:a.FooTest]/[nested-class:Inner]/[method:bar()]"
        self.assertEqual(key_from_test_name(nested), "a.FooTest$Inner#bar")
        self.assertEqual(key_from_test_name("a.FooTest.bar(a.FooTest)"), "a.FooTest#bar")


if __name__ == "__main__":
    unittest.main()
