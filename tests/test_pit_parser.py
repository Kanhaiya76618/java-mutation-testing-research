"""
tests/test_pit_parser.py
Unit test verifying pit_parser.py correctly parses sample PIT mutations.xml content.
"""

import gzip
import tempfile
import unittest
from pathlib import Path
from harness.pit_parser import PitMutationReport, method_from_test_name, mutator_name

SAMPLE_PIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mutations>
<mutation detected='true' status='KILLED' numberOfTestsRun='3'>
    <sourceFile>Calculator.java</sourceFile>
    <mutatedClass>org.example.Calculator</mutatedClass>
    <mutatedMethod>add</mutatedMethod>
    <methodDescription>(II)I</methodDescription>
    <lineNumber>15</lineNumber>
    <mutator>org.pitest.mutationtest.engine.gregor.mutators.MathMutator</mutator>
    <killingTest>org.example.CalculatorTest.testAdd(org.example.CalculatorTest)</killingTest>
    <description>Replaced integer addition with subtraction</description>
</mutation>
<mutation detected='false' status='SURVIVED' numberOfTestsRun='2'>
    <sourceFile>Calculator.java</sourceFile>
    <mutatedClass>org.example.Calculator</mutatedClass>
    <mutatedMethod>isPositive</mutatedMethod>
    <methodDescription>(I)Z</methodDescription>
    <lineNumber>22</lineNumber>
    <mutator>org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator</mutator>
    <killingTest/>
    <description>changed conditional boundary</description>
</mutation>
<mutation detected='false' status='NO_COVERAGE' numberOfTestsRun='0'>
    <sourceFile>Calculator.java</sourceFile>
    <mutatedClass>org.example.Calculator</mutatedClass>
    <mutatedMethod>debugPrint</mutatedMethod>
    <methodDescription>()V</methodDescription>
    <lineNumber>30</lineNumber>
    <mutator>org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator</mutator>
    <killingTest/>
    <description>removed call to java/io/PrintStream::println</description>
</mutation>
</mutations>
"""

class TestPitParser(unittest.TestCase):
    def test_sample_parsing(self):
        with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_PIT_XML)
            f_path = f.name

        try:
            report = PitMutationReport(f_path)
            self.assertEqual(len(report.mutations), 3)

            summary = report.summary()
            self.assertEqual(summary["total_mutants"], 3)
            self.assertEqual(summary["killed"], 1)
            self.assertEqual(summary["survived"], 1)
            self.assertEqual(summary["no_coverage"], 1)
            self.assertAlmostEqual(summary["mutation_score"], 33.33, places=2)

            self.assertIn("MathMutator", summary["by_mutator"])
            self.assertEqual(summary["by_mutator"]["MathMutator"]["killed"], 1)
            self.assertIn("ConditionalsBoundaryMutator", summary["by_mutator"])
            self.assertEqual(summary["by_mutator"]["ConditionalsBoundaryMutator"]["survived"], 1)
        finally:
            Path(f_path).unlink(missing_ok=True)


# A PIT 1.16 report written with fullMutationMatrix=true: every mutant lists all killing
# and succeeding tests. It also has a TIMED_OUT mutant and a RemoveConditional mutator.
MATRIX_PIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mutations partial="true">
<mutation detected='true' status='KILLED' numberOfTestsRun='2'><sourceFile>Calc.java</sourceFile><mutatedClass>org.example.Calc</mutatedClass><mutatedMethod>add</mutatedMethod><methodDescription>(II)I</methodDescription><lineNumber>5</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.MathMutator</mutator><killingTests>org.example.CalcTest.testAdd|org.example.CalcTest.testSum</killingTests><succeedingTests></succeedingTests><description>Replaced integer addition with subtraction</description></mutation>
<mutation detected='true' status='TIMED_OUT' numberOfTestsRun='1'><sourceFile>Calc.java</sourceFile><mutatedClass>org.example.Calc</mutatedClass><mutatedMethod>loop</mutatedMethod><methodDescription>(I)V</methodDescription><lineNumber>9</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.RemoveConditionalMutator_ORDER_ELSE</mutator><killingTests/><succeedingTests/><description>removed conditional - replaced comparison check with false</description></mutation>
<mutation detected='false' status='SURVIVED' numberOfTestsRun='2'><sourceFile>Calc.java</sourceFile><mutatedClass>org.example.Calc</mutatedClass><mutatedMethod>isPositive</mutatedMethod><methodDescription>(I)Z</methodDescription><lineNumber>12</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.ConditionalsBoundaryMutator</mutator><killingTests/><succeedingTests>org.example.CalcTest.testAdd|org.example.CalcTest.testSum</succeedingTests><description>changed conditional boundary</description></mutation>
<mutation detected='false' status='NO_COVERAGE' numberOfTestsRun='0'><sourceFile>Calc.java</sourceFile><mutatedClass>org.example.Calc</mutatedClass><mutatedMethod>debug</mutatedMethod><methodDescription>()V</methodDescription><lineNumber>20</lineNumber><mutator>org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator</mutator><killingTests/><succeedingTests/><description>removed call</description></mutation>
</mutations>
"""


class TestPitParserScoresAndMatrix(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.xml_path = Path(self.temp_dir.name) / "mutations.xml"
        self.xml_path.write_text(MATRIX_PIT_XML, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scores_follow_pit_detected_flag(self):
        summary = PitMutationReport(self.xml_path).summary()
        self.assertEqual(summary["total_mutants"], 4)
        # KILLED and TIMED_OUT are both detected by PIT
        self.assertEqual(summary["detected"], 2)
        self.assertEqual(summary["killed"], 1)
        self.assertEqual(summary["timed_out"], 1)
        self.assertAlmostEqual(summary["mutation_score"], 50.0)
        # Test strength leaves out the NO_COVERAGE mutant: 2 detected of 3 covered
        self.assertAlmostEqual(summary["test_strength"], 200.0 / 3)
        self.assertAlmostEqual(summary["killed_only_score"], 25.0)

    def test_mutators_are_counted_not_invented(self):
        by_mutator = PitMutationReport(self.xml_path).summary()["by_mutator"]
        self.assertEqual(by_mutator["RemoveConditionalMutator_ORDER_ELSE"]["operator"], "REMOVE_CONDITIONALS_ORDER_ELSE")
        self.assertEqual(by_mutator["MathMutator"]["total"], 1)
        # A mutator with no mutants in the report is absent, never reported as 0% killed
        self.assertNotIn("NegateConditionalsMutator", by_mutator)

    def test_full_matrix_is_parsed(self):
        report = PitMutationReport(self.xml_path)
        self.assertTrue(report.has_full_matrix)
        math, _, boundary, _ = report.mutations
        self.assertEqual(math["killing_tests"], ["org.example.CalcTest.testAdd", "org.example.CalcTest.testSum"])
        self.assertEqual(math["succeeding_tests"], [])
        self.assertEqual(boundary["succeeding_tests"], ["org.example.CalcTest.testAdd", "org.example.CalcTest.testSum"])

    def test_report_without_matrix(self):
        self.xml_path.write_text(SAMPLE_PIT_XML, encoding="utf-8")
        report = PitMutationReport(self.xml_path)
        self.assertFalse(report.has_full_matrix)
        self.assertEqual(report.mutations[0]["killing_tests"], ["org.example.CalculatorTest.testAdd(org.example.CalculatorTest)"])
        self.assertIsNone(report.mutations[0]["succeeding_tests"])

    def test_gzip_report(self):
        gz_path = self.xml_path.with_suffix(".xml.gz")
        with gzip.open(gz_path, "wt", encoding="utf-8") as f:
            f.write(MATRIX_PIT_XML)
        self.assertEqual(PitMutationReport(gz_path).summary()["total_mutants"], 4)

    def test_unknown_mutator_name_is_kept(self):
        self.assertEqual(mutator_name("MathMutator"), "MATH")
        self.assertEqual(mutator_name("SomeFutureMutator"), "SomeFutureMutator")

    def test_test_method_names(self):
        # Format written by PIT 1.16 with pitest-junit5-plugin (copied from a real Commons Lang report)
        junit5 = ("org.apache.commons.lang3.time.InstantsTest.[engine:junit-jupiter]"
                  "/[class:org.apache.commons.lang3.time.InstantsTest]/[method:testToEpochMillisUnderflowReturnsMinValue()]")
        self.assertEqual(method_from_test_name(junit5), "testToEpochMillisUnderflowReturnsMinValue")
        parameterized = ("org.example.CalcTest.[engine:junit-jupiter]/[class:org.example.CalcTest]"
                         "/[test-template:testRange(int)]/[test-template-invocation:#2]")
        self.assertEqual(method_from_test_name(parameterized), "testRange")
        self.assertEqual(method_from_test_name("org.example.CalculatorTest.testAdd(org.example.CalculatorTest)"), "testAdd")


if __name__ == "__main__":
    unittest.main()
