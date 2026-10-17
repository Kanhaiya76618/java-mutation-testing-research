"""
tests/test_surefire_parser.py
Unit test verifying surefire_parser.py reads Surefire XML reports correctly.
"""

import tempfile
import unittest
from pathlib import Path
from harness.surefire_parser import SurefireResults, method_name

SAMPLE_SUREFIRE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="org.example.CalcTest" tests="6" errors="1" skipped="1" failures="1">
  <testcase name="testAdd" classname="org.example.CalcTest" time="0.01"/>
  <testcase name="testOverflow" classname="org.example.CalcTest" time="0.01">
    <failure message="expected: &lt;1&gt; but was: &lt;2&gt;" type="org.opentest4j.AssertionFailedError"/>
  </testcase>
  <testcase name="testDivide" classname="org.example.CalcTest" time="0.01">
    <error message="/ by zero" type="java.lang.ArithmeticException"/>
  </testcase>
  <testcase name="testIgnored" classname="org.example.CalcTest" time="0">
    <skipped/>
  </testcase>
  <testcase name="testRange(int)[1]" classname="org.example.CalcTest" time="0.01"/>
  <testcase name="testRange(int)[2]" classname="org.example.CalcTest" time="0.01"/>
</testsuite>
"""


class TestSurefireParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.reports = Path(self.temp_dir.name)
        (self.reports / "TEST-org.example.CalcTest.xml").write_text(SAMPLE_SUREFIRE_XML, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_method_name_strips_parameters(self):
        self.assertEqual(method_name("testRange(int)[2]"), "testRange")
        self.assertEqual(method_name("testHashCodeNotEquals(int, int, int, int)[10]"), "testHashCodeNotEquals")
        self.assertEqual(method_name("testAdd"), "testAdd")

    def test_outcomes_and_counts(self):
        results = SurefireResults.from_dir(self.reports, ["org.example.CalcTest"])
        # Skipped tests do not count as executed; parameterized invocations count separately
        self.assertEqual(results.total, 5)
        self.assertEqual(results.failed, 2)
        self.assertFalse(results.is_green)
        self.assertEqual(results.failing_methods(), {"testOverflow", "testDivide"})
        self.assertEqual(results.methods(), {"testAdd", "testOverflow", "testDivide", "testRange"})

    def test_missing_report_means_nothing_ran(self):
        results = SurefireResults.from_dir(self.reports, ["org.example.OtherTest"])
        self.assertEqual(results.total, 0)
        self.assertFalse(results.is_green)


if __name__ == "__main__":
    unittest.main()
