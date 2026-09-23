"""
tests/test_pit_parser.py
Unit test verifying pit_parser.py correctly parses sample PIT mutations.xml content.
"""

import tempfile
import unittest
from pathlib import Path
from harness.pit_parser import PitMutationReport

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

if __name__ == "__main__":
    unittest.main()
