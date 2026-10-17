"""
tests/test_run_experiment.py
Unit tests for the pure helper functions of scripts/run_experiment.py (no Maven or git needed).
"""

import csv
import tempfile
import unittest
from pathlib import Path
from scripts.run_experiment import (
    classify_bug_run,
    declared_methods,
    disable_test_methods,
    parse_pit_timings,
    upsert_rows,
)

TEST_CLASS = """
class CalcTest {
    @Test
    void testAdd() {
        assertEquals(2, add(1, 1));
    }

    @ParameterizedTest
    @ValueSource(ints = {1, 2, 3})
    public void testPositive(final int x) {
        assertTrue(x > 0);
    }

    private void assertNear(double a, double b) {
        assertTrue(Math.abs(a - b) < 1e-9);
    }

    @Test
    @Timeout(5)
    void testNewRegression() throws Exception {
        assertNear(1.0, 1.0);
    }
}
"""


class TestDisableTestMethods(unittest.TestCase):
    def test_disables_only_the_named_tests(self):
        code, not_tests = disable_test_methods(TEST_CLASS, ["testNewRegression", "testPositive"])
        self.assertEqual(not_tests, [])
        self.assertIn("/* @Test */\n    @Timeout(5)\n    void testNewRegression()", code)
        self.assertIn("/* @ParameterizedTest */\n    @ValueSource(ints = {1, 2, 3})\n    public void testPositive(", code)
        # testAdd keeps its annotation
        self.assertIn("    @Test\n    void testAdd()", code)

    def test_helper_method_is_reported_and_previous_test_untouched(self):
        # The old version commented out the last @Test before the name, which here is testPositive's.
        code, not_tests = disable_test_methods(TEST_CLASS, ["assertNear"])
        self.assertEqual(not_tests, ["assertNear"])
        self.assertEqual(code, TEST_CLASS)

    def test_declared_methods(self):
        self.assertEqual(declared_methods(TEST_CLASS), {"testAdd", "testPositive", "assertNear", "testNewRegression"})


class TestClassifyBugRun(unittest.TestCase):
    def test_added_test_reveals_fault(self):
        r = classify_bug_run({"testNewRegression"}, {"testNewRegression"})
        self.assertEqual(r["detected_aug"], 1)
        self.assertEqual(r["detected_base"], 0)
        self.assertEqual(r["fault_revealing_tests"], ["testNewRegression"])

    def test_bug_not_reproduced(self):
        r = classify_bug_run(set(), {"testNewRegression"})
        self.assertEqual((r["detected_aug"], r["detected_base"]), (0, 0))

    def test_existing_test_also_fails(self):
        r = classify_bug_run({"testAdd", "testNewRegression"}, {"testNewRegression"})
        self.assertEqual((r["detected_aug"], r["detected_base"]), (1, 1))


class TestPitTimings(unittest.TestCase):
    def test_parse_timing_table(self):
        out = (
            "================================================================================\n"
            "- Timings\n"
            "================================================================================\n"
            "> pre-scan for mutations : < 1 second\n"
            "> coverage and dependency analysis : 3 seconds\n"
            "> run mutation analysis : 2 minutes and 13 seconds\n"
            "--------------------------------------------------------------------------------\n"
            "> Total  : 2 minutes and 17 seconds\n"
        )
        t = parse_pit_timings(out)
        self.assertEqual(t["pit_analysis_seconds"], 133.0)
        self.assertEqual(t["pit_total_seconds"], 137.0)

    def test_missing_table(self):
        self.assertEqual(parse_pit_timings("BUILD FAILURE"), {"pit_total_seconds": None, "pit_analysis_seconds": None})


class TestUpsertRows(unittest.TestCase):
    def test_rerun_replaces_rows(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runs.csv"
            fields = ["bug_id", "suite_type", "mutation_score"]
            upsert_rows(path, fields, [{"bug_id": "a", "suite_type": "base", "mutation_score": 1.0}], ("bug_id", "suite_type"))
            upsert_rows(path, fields, [{"bug_id": "b", "suite_type": "base", "mutation_score": 2.0}], ("bug_id", "suite_type"))
            upsert_rows(path, fields, [{"bug_id": "a", "suite_type": "base", "mutation_score": 3.0}], ("bug_id", "suite_type"))
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([(r["bug_id"], r["mutation_score"]) for r in rows], [("b", "2.0"), ("a", "3.0")])


if __name__ == "__main__":
    unittest.main()
