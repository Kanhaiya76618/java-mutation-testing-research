"""
harness/pit_parser.py

Parses PIT (PITest) XML mutation reports (mutations.xml, optionally gzip-compressed)
into structured Python dictionaries for statistical analysis.

Score definitions (these match PIT's own HTML report, so every number can be
checked against PIT directly):
- mutation_score    = detected / total * 100. "detected" is PIT's own `detected`
                      flag, which is true for KILLED, TIMED_OUT, MEMORY_ERROR,
                      RUN_ERROR and NON_VIABLE mutants.
- test_strength     = detected / (total - no_coverage) * 100, the score over the
                      mutants that at least one test executes.
- killed_only_score = KILLED / total * 100, the definition used by the first
                      version of this harness (kept to compare with old results).

When PIT runs with fullMutationMatrix=true, every mutant lists all of its killing
tests and all of its succeeding tests. That "kill matrix" makes it possible to
recompute the score of any subset of the test suite without re-running PIT.
"""

from __future__ import annotations
import gzip
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


# PIT mutator class name -> mutator name used in PIT configuration and in
# config/pit-mutators.json. Class names not listed here are kept unchanged,
# so an unexpected mutator is never silently dropped from the counts.
MUTATOR_NAMES: Dict[str, str] = {
    "ConditionalsBoundaryMutator": "CONDITIONALS_BOUNDARY",
    "IncrementsMutator": "INCREMENTS",
    "InvertNegsMutator": "INVERT_NEGS",
    "MathMutator": "MATH",
    "NegateConditionalsMutator": "NEGATE_CONDITIONALS",
    "VoidMethodCallMutator": "VOID_METHOD_CALLS",
    "EmptyObjectReturnValsMutator": "EMPTY_RETURNS",
    "BooleanFalseReturnValsMutator": "FALSE_RETURNS",
    "BooleanTrueReturnValsMutator": "TRUE_RETURNS",
    "NullReturnValsMutator": "NULL_RETURNS",
    "PrimitiveReturnsMutator": "PRIMITIVE_RETURNS",
    "RemoveConditionalMutator_EQUAL_IF": "REMOVE_CONDITIONALS_EQUAL_IF",
    "RemoveConditionalMutator_EQUAL_ELSE": "REMOVE_CONDITIONALS_EQUAL_ELSE",
    "RemoveConditionalMutator_ORDER_IF": "REMOVE_CONDITIONALS_ORDER_IF",
    "RemoveConditionalMutator_ORDER_ELSE": "REMOVE_CONDITIONALS_ORDER_ELSE",
}

# Separator PIT uses between test names in <killingTests> / <succeedingTests>.
TEST_LIST_SEPARATOR = "|"


_JUNIT5_METHOD = re.compile(r"\[(?:method|test-template|test-factory):([A-Za-z_$][\w$]*)")


def mutator_name(class_name: str) -> str:
    """Maps a PIT mutator class name (e.g. 'MathMutator') to its config name ('MATH')."""
    return MUTATOR_NAMES.get(class_name, class_name)


def method_from_test_name(pit_test_name: str) -> str:
    """Method name of a test as PIT names it, so kill-matrix entries can be matched with Surefire results.

    JUnit 5: 'pkg.FooTest.[engine:junit-jupiter]/[class:pkg.FooTest]/[method:testBar()]' -> 'testBar'
    JUnit 4: 'pkg.FooTest.testBar(pkg.FooTest)' -> 'testBar'
    """
    m = _JUNIT5_METHOD.search(pit_test_name)
    if m:
        return m.group(1)
    return pit_test_name.split("(", 1)[0].rsplit(".", 1)[-1]


def key_from_test_name(pit_test_name: str) -> str:
    """'Class#method' identifier of a PIT test name, matching SurefireResults.keys().

    JUnit 5: the class comes from the [class:...] segment ([nested-class:...] is appended with '$').
    JUnit 4: 'pkg.FooTest.testBar(pkg.FooTest)' -> 'pkg.FooTest#testBar'.
    """
    classes = re.findall(r"\[(class|nested-class):([^\]]+)\]", pit_test_name)
    if classes:
        cls = classes[0][1] + "".join("$" + name for kind, name in classes[1:] if kind == "nested-class")
    elif "(" in pit_test_name and pit_test_name.endswith(")"):
        cls = pit_test_name[pit_test_name.index("(") + 1:-1]
    else:
        cls = pit_test_name.split(".[engine", 1)[0]
    return f"{cls}#{method_from_test_name(pit_test_name)}"


def _split_tests(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return [t.strip() for t in text.split(TEST_LIST_SEPARATOR) if t.strip()]


def _empty_counts() -> Dict[str, Any]:
    return {"total": 0, "detected": 0, "killed": 0, "survived": 0, "no_coverage": 0, "timed_out": 0, "other": 0}


def _add_status(counts: Dict[str, Any], status: str, detected: bool) -> None:
    counts["total"] += 1
    if detected:
        counts["detected"] += 1
    if status == "KILLED":
        counts["killed"] += 1
    elif status == "SURVIVED":
        counts["survived"] += 1
    elif status == "NO_COVERAGE":
        counts["no_coverage"] += 1
    elif status == "TIMED_OUT":
        counts["timed_out"] += 1
    else:
        # MEMORY_ERROR, RUN_ERROR, NON_VIABLE and anything newer
        counts["other"] += 1


def _percent(numerator: int, denominator: int) -> Optional[float]:
    """Returns None (not 0.0) when there is nothing to divide, so 'no mutants' is never mistaken for '0% killed'."""
    return (numerator / denominator) * 100.0 if denominator > 0 else None


class PitMutationReport:
    def __init__(self, xml_path: str | Path):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"PIT mutations file not found: {self.xml_path}")
        opener = gzip.open if self.xml_path.suffix == ".gz" else open
        with opener(self.xml_path, "rb") as f:
            self.tree = ET.parse(f)
        self.root = self.tree.getroot()
        self.mutations: List[Dict[str, Any]] = []
        self._parse()

    def _parse(self) -> None:
        """Parses all <mutation> elements from the XML tree."""
        for mutation in self.root.findall("mutation"):
            detected = mutation.get("detected", "false").lower() == "true"
            status = mutation.get("status", "UNKNOWN")
            tests_run = int(mutation.get("numberOfTestsRun", "0"))

            source_file = mutation.findtext("sourceFile", "")
            mutated_class = mutation.findtext("mutatedClass", "")
            mutated_method = mutation.findtext("mutatedMethod", "")
            line_number = int(mutation.findtext("lineNumber", "0"))
            mutator = mutation.findtext("mutator", "").split(".")[-1]
            killing_test = mutation.findtext("killingTest", None) or None
            description = mutation.findtext("description", "")

            # Full mutation matrix (only written when PIT runs with fullMutationMatrix=true)
            succeeding_el = mutation.find("succeedingTests")
            killing_tests = _split_tests(mutation.findtext("killingTests", None))
            if not killing_tests and killing_test:
                killing_tests = [killing_test]

            self.mutations.append({
                "detected": detected,
                "status": status,
                "tests_run": tests_run,
                "source_file": source_file,
                "mutated_class": mutated_class,
                "mutated_method": mutated_method,
                "line_number": line_number,
                "mutator": mutator,
                "operator": mutator_name(mutator),
                "killing_test": killing_test,
                "killing_tests": killing_tests,
                "succeeding_tests": _split_tests(succeeding_el.text) if succeeding_el is not None else None,
                "description": description,
            })

    @property
    def has_full_matrix(self) -> bool:
        """True when the report lists succeeding tests per mutant (PIT fullMutationMatrix=true)."""
        return any(m["succeeding_tests"] is not None for m in self.mutations)

    def summary(self) -> Dict[str, Any]:
        """Calculates aggregate metrics across all mutants and per mutator."""
        totals = _empty_counts()
        by_mutator: Dict[str, Dict[str, Any]] = {}
        for m in self.mutations:
            _add_status(totals, m["status"], m["detected"])
            op = m["mutator"]
            if op not in by_mutator:
                by_mutator[op] = {"operator": m["operator"], **_empty_counts()}
            _add_status(by_mutator[op], m["status"], m["detected"])

        for data in by_mutator.values():
            data["score"] = _percent(data["detected"], data["total"])

        return {
            "total_mutants": totals["total"],
            "detected": totals["detected"],
            "killed": totals["killed"],
            "survived": totals["survived"],
            "no_coverage": totals["no_coverage"],
            "timed_out": totals["timed_out"],
            "other": totals["other"],
            "mutation_score": _percent(totals["detected"], totals["total"]),
            "test_strength": _percent(totals["detected"], totals["total"] - totals["no_coverage"]),
            "killed_only_score": _percent(totals["killed"], totals["total"]),
            "has_full_matrix": self.has_full_matrix,
            "by_mutator": by_mutator,
        }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        report = PitMutationReport(sys.argv[1])
        print(json.dumps(report.summary(), indent=2))
    else:
        print("Usage: python3 pit_parser.py <path_to_mutations.xml[.gz]>")
