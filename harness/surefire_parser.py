"""
harness/surefire_parser.py

Reads Maven Surefire XML reports (target/surefire-reports/TEST-*.xml) to find out
which test methods ran, passed, failed or errored.

The experiment runner uses this to:
- count the tests in a suite (the suite-size variable the analysis controls for),
- check that a suite is green before PIT runs,
- check that the added regression tests are absent from T_base and present in T_aug,
- find which tests fail on the buggy version V_bug (the fault-revealing tests).
"""

from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

_METHOD_NAME = re.compile(r"[A-Za-z_$][\w$]*")


def method_name(testcase_name: str) -> str:
    """Strips JUnit 5 parameter and invocation suffixes: 'testFoo(int)[2]' -> 'testFoo'."""
    m = _METHOD_NAME.match(testcase_name.strip())
    return m.group(0) if m else testcase_name.strip()


@dataclass(frozen=True)
class TestCaseResult:
    class_name: str
    name: str      # name as reported, may include parameters and an invocation index
    outcome: str   # "passed", "failed", "error" or "skipped"

    @property
    def method(self) -> str:
        return method_name(self.name)


class SurefireResults:
    def __init__(self, cases: List[TestCaseResult]):
        self.cases = cases

    @classmethod
    def from_files(cls, files: Iterable[str | Path]) -> "SurefireResults":
        cases: List[TestCaseResult] = []
        for path in files:
            root = ET.parse(path).getroot()
            for tc in root.iter("testcase"):
                if tc.find("failure") is not None:
                    outcome = "failed"
                elif tc.find("error") is not None:
                    outcome = "error"
                elif tc.find("skipped") is not None:
                    outcome = "skipped"
                else:
                    outcome = "passed"
                cases.append(TestCaseResult(tc.get("classname", ""), tc.get("name", ""), outcome))
        return cls(cases)

    @classmethod
    def from_dir(cls, reports_dir: str | Path, class_names: Optional[Iterable[str]] = None) -> "SurefireResults":
        """Loads TEST-<class>.xml reports, optionally only for the given fully qualified test classes."""
        reports_dir = Path(reports_dir)
        if class_names is None:
            files = sorted(reports_dir.glob("TEST-*.xml"))
        else:
            files = [reports_dir / f"TEST-{c}.xml" for c in class_names]
            files = [f for f in files if f.exists()]
        return cls.from_files(files)

    @property
    def total(self) -> int:
        """Number of executed test cases (parameterized invocations count separately, skipped ones do not)."""
        return sum(1 for c in self.cases if c.outcome != "skipped")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.cases if c.outcome in ("failed", "error"))

    @property
    def is_green(self) -> bool:
        return self.total > 0 and self.failed == 0

    def methods(self, outcomes: Optional[Iterable[str]] = None) -> Set[str]:
        """Method names that ran, optionally restricted to the given outcomes."""
        wanted = set(outcomes) if outcomes is not None else {"passed", "failed", "error"}
        return {c.method for c in self.cases if c.outcome in wanted}

    def failing_methods(self) -> Set[str]:
        return self.methods(("failed", "error"))

    def keys(self, outcomes: Optional[Iterable[str]] = None) -> Set[str]:
        """'Class#method' identifiers of the tests that ran (unique even across several test classes)."""
        wanted = set(outcomes) if outcomes is not None else {"passed", "failed", "error"}
        return {f"{c.class_name}#{c.method}" for c in self.cases if c.outcome in wanted}
