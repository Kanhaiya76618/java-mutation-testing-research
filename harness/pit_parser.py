"""
harness/pit_parser.py

Parses PIT (PITest) XML mutation reports (mutations.xml) into structured Python
dictionaries and pandas DataFrames for statistical analysis.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List


class PitMutationReport:
    def __init__(self, xml_path: str | Path):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"PIT mutations file not found: {self.xml_path}")
        self.tree = ET.parse(self.xml_path)
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
            killing_test = mutation.findtext("killingTest", None)
            description = mutation.findtext("description", "")

            self.mutations.append({
                "detected": detected,
                "status": status,
                "tests_run": tests_run,
                "source_file": source_file,
                "mutated_class": mutated_class,
                "mutated_method": mutated_method,
                "line_number": line_number,
                "mutator": mutator,
                "killing_test": killing_test,
                "description": description,
            })

    def summary(self) -> Dict[str, Any]:
        """Calculates aggregate metrics across all mutants."""
        total = len(self.mutations)
        if total == 0:
            return {
                "total_mutants": 0,
                "killed": 0,
                "survived": 0,
                "no_coverage": 0,
                "timed_out": 0,
                "mutation_score": 0.0,
                "by_mutator": {},
            }

        killed = sum(1 for m in self.mutations if m["status"] == "KILLED")
        survived = sum(1 for m in self.mutations if m["status"] == "SURVIVED")
        no_coverage = sum(1 for m in self.mutations if m["status"] == "NO_COVERAGE")
        timed_out = sum(1 for m in self.mutations if m["status"] in ("TIMED_OUT", "MEMORY_ERROR"))

        # Mutation score = killed / (total - non_viable)
        # In PIT standard: killed / total mutants considered
        mutation_score = (killed / total) * 100.0

        by_mutator: Dict[str, Dict[str, Any]] = {}
        for m in self.mutations:
            op = m["mutator"]
            if op not in by_mutator:
                by_mutator[op] = {"total": 0, "killed": 0, "survived": 0}
            by_mutator[op]["total"] += 1
            if m["status"] == "KILLED":
                by_mutator[op]["killed"] += 1
            elif m["status"] == "SURVIVED":
                by_mutator[op]["survived"] += 1

        for op, data in by_mutator.items():
            data["score"] = (data["killed"] / data["total"]) * 100.0 if data["total"] > 0 else 0.0

        return {
            "total_mutants": total,
            "killed": killed,
            "survived": survived,
            "no_coverage": no_coverage,
            "timed_out": timed_out,
            "mutation_score": round(mutation_score, 2),
            "by_mutator": by_mutator,
        }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        report = PitMutationReport(sys.argv[1])
        print(json.dumps(report.summary(), indent=2))
    else:
        print("Usage: python3 pit_parser.py <path_to_mutations.xml>")
