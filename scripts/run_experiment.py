"""
scripts/run_experiment.py

Runs the empirical evaluation of a single bug-fix pair and records what actually
happened at every step, so each number in the results can be traced to raw data:

1. V_bug check: applies the post-fix test file(s) to the buggy commit V_bug and runs
   the target test class(es). The fault-revealing tests are the test methods that
   fail there. If no test runs (typically because the post-fix tests do not compile
   against the buggy code) the pair is skipped: a compile error is not a detected fault.
2. T_base on V_fix: disables the test methods added by the fix, checks with Surefire
   that the suite is green and that none of the added tests ran, then runs PIT.
3. T_aug on V_fix: restores the added tests, checks that the suite is green and that
   every added test ran, then runs PIT.
4. Writes one row per suite to <results-dir>/runs.csv, one row per (suite, mutator)
   to <results-dir>/operators.csv, and archives the raw PIT and Surefire reports
   under <raw-dir>/<bug_id>/.
"""

from __future__ import annotations
import argparse
import csv
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.pit_parser import PitMutationReport
from harness.surefire_parser import SurefireResults


PIT_VERSION = "1.16.0"
PIT_JUNIT5_PLUGIN_VERSION = "1.2.1"
JDK21_HOME = Path("/opt/homebrew/opt/openjdk@21")

# XML only: PIT's full mutation matrix is written to the XML report.
PIT_POM_SNIPPET = f"""
      <plugin>
        <groupId>org.pitest</groupId>
        <artifactId>pitest-maven</artifactId>
        <version>{PIT_VERSION}</version>
        <dependencies>
          <dependency>
            <groupId>org.pitest</groupId>
            <artifactId>pitest-junit5-plugin</artifactId>
            <version>{PIT_JUNIT5_PLUGIN_VERSION}</version>
          </dependency>
        </dependencies>
        <configuration>
          <outputFormats>
            <outputFormat>XML</outputFormat>
          </outputFormats>
        </configuration>
      </plugin>
"""

RUN_FIELDS = [
    "bug_id", "commit_hash", "parent_hash", "project", "target_classes", "target_tests",
    "suite_type", "mutators", "full_matrix", "pit_version", "java_home",
    "test_count", "test_methods", "added_tests",
    "total_mutants", "detected", "killed", "survived", "no_coverage", "timed_out", "other",
    "mutation_score", "test_strength", "killed_only_score",
    "wall_seconds", "pit_total_seconds", "pit_analysis_seconds",
    "fault_detected", "fault_revealing_tests", "raw_report",
]

OPERATOR_FIELDS = [
    "bug_id", "suite_type", "mutator", "operator",
    "total", "detected", "killed", "survived", "no_coverage", "timed_out", "other", "score",
]


class TrialSkipped(Exception):
    """The bug pair cannot be evaluated; the message says why (reported, never silently dropped)."""


def run_cmd(cmd: List[str], cwd: Path, timeout: Optional[float] = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    if JDK21_HOME.exists():
        env["JAVA_HOME"] = str(JDK21_HOME)
        env["PATH"] = f"{JDK21_HOME}/bin:{env.get('PATH', '')}"
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Pure helpers (no Maven or git needed; covered by tests/test_run_experiment.py)
# ---------------------------------------------------------------------------

_TEST_ANNOTATION = (
    r"@(?:org\.junit\.jupiter\.api\.|org\.junit\.jupiter\.params\.)?"
    r"(?:Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b(?:\([^()]*\))?"
)
_OTHER_ANNOTATION = r"@[\w.]+(?:\((?:[^()]|\([^()]*\))*\))?"
_MODIFIERS = r"(?:(?:public|protected|private|static|final|synchronized)\s+)*"
_DECLARED_VOID_METHOD = re.compile(r"\bvoid\s+([A-Za-z_$][\w$]*)\s*\(")


def declared_methods(java_source: str) -> Set[str]:
    """Names of the void methods declared in a Java source file (JUnit test methods are void)."""
    return set(_DECLARED_VOID_METHOD.findall(java_source))


def disable_test_methods(code: str, methods: Iterable[str]) -> Tuple[str, List[str]]:
    """Comments out the JUnit annotation of each named test method so that it no longer runs.

    Only an annotation that belongs to the method itself is changed: between it and the
    method declaration there may only be other annotations and modifiers. (The previous
    version commented out the last @Test before the name, which could hit a different test.)

    Returns the new code and the names that have no test annotation (helper methods).
    """
    not_tests: List[str] = []
    for name in methods:
        pattern = re.compile(
            rf"(?P<ann>{_TEST_ANNOTATION})"
            rf"(?P<rest>(?:\s+{_OTHER_ANNOTATION})*\s+{_MODIFIERS}void\s+{re.escape(name)}\s*\()"
        )
        code, count = pattern.subn(lambda mt: f"/* {mt.group('ann')} */{mt.group('rest')}", code)
        if count == 0:
            not_tests.append(name)
    return code, not_tests


def classify_bug_run(failing_methods: Set[str], added_tests: Set[str]) -> Dict[str, Any]:
    """Interprets the test run on V_bug.

    A test that fails on V_bug and passes on V_fix reveals the fault. T_aug detects the
    fault if any of its tests fails on V_bug; T_base detects it if any test other than
    the added ones fails. Both are measured, not assumed.
    """
    return {
        "fault_revealing_tests": sorted(failing_methods),
        "detected_aug": int(bool(failing_methods)),
        "detected_base": int(bool(failing_methods - added_tests)),
    }


def _to_seconds(text: str) -> Optional[float]:
    parts = re.findall(r"(\d+)\s*(hour|minute|second)s?", text)
    if parts:
        unit = {"hour": 3600, "minute": 60, "second": 1}
        return float(sum(int(n) * unit[u] for n, u in parts))
    return 0.0 if text.strip().startswith("<") else None


def parse_pit_timings(output: str) -> Dict[str, Optional[float]]:
    """Reads PIT's own timing table ('> run mutation analysis : 4 seconds', '> Total  : 6 seconds')."""
    timings: Dict[str, Optional[float]] = {}
    for label, value in re.findall(r">\s*([A-Za-z][A-Za-z ]*?)\s*:\s*([^\n]+)", output):
        timings[label.strip().lower()] = _to_seconds(value)
    return {
        "pit_total_seconds": timings.get("total"),
        "pit_analysis_seconds": timings.get("run mutation analysis"),
    }


def upsert_rows(csv_path: Path, fields: List[str], rows: List[Dict[str, Any]], key: Tuple[str, ...]) -> None:
    """Writes rows to a CSV, replacing earlier rows with the same key (re-running a bug never duplicates it)."""
    existing: List[Dict[str, Any]] = []
    if csv_path.exists() and csv_path.stat().st_size > 0:
        with open(csv_path, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    new_keys = {tuple(str(r[k]) for k in key) for r in rows}
    kept = [r for r in existing if tuple(str(r.get(k, "")) for k in key) not in new_keys]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in kept + rows:
            writer.writerow({k: r.get(k, "") for k in fields})


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class ExperimentRunner:
    def __init__(
        self,
        repo_path: str | Path,
        results_dir: str | Path = "data/v2",
        raw_dir: str | Path = "data/raw",
        project: str = "commons-lang",
        timeout_minutes: Optional[float] = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.results_dir = Path(results_dir).resolve()
        self.raw_dir = Path(raw_dir).resolve()
        self.project = project
        self.timeout = timeout_minutes * 60 if timeout_minutes else None
        self.java_home = str(JDK21_HOME) if JDK21_HOME.exists() else os.environ.get("JAVA_HOME", "system")

    # -- Maven / git plumbing ------------------------------------------------

    def _run_mvn(self, args: List[str]) -> subprocess.CompletedProcess:
        mvn_cmd = ["mvn", "-B", "-Drat.skip=true"] + args
        return run_cmd(mvn_cmd, self.repo_path, timeout=self.timeout)

    def _git_show(self, rev: str, path: str) -> str:
        res = run_cmd(["git", "show", f"{rev}:{path}"], self.repo_path)
        return res.stdout if res.returncode == 0 else ""

    def _find_pit_xml(self) -> Optional[Path]:
        """Finds the most recent mutations.xml in target/pit-reports/."""
        reports_dir = self.repo_path / "target" / "pit-reports"
        if not reports_dir.exists():
            return None
        xmls = list(reports_dir.rglob("mutations.xml"))
        if not xmls:
            return None
        xmls.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return xmls[0]

    def _ensure_pit_in_pom(self) -> None:
        """Injects pitest-maven with pitest-junit5-plugin into pom.xml if missing."""
        pom_path = self.repo_path / "pom.xml"
        if not pom_path.exists():
            return
        content = pom_path.read_text(encoding="utf-8")
        if "pitest-maven" in content and "pitest-junit5-plugin" in content:
            return
        match = re.search(r"<plugins>", content)
        if match:
            idx = match.end()
            pom_path.write_text(content[:idx] + PIT_POM_SNIPPET + content[idx:], encoding="utf-8")

    def _run_tests(self, test_classes: List[str]) -> Tuple[subprocess.CompletedProcess, SurefireResults]:
        """Runs the given test classes with Surefire and reads their reports (stale reports are removed first)."""
        shutil.rmtree(self.repo_path / "target" / "surefire-reports", ignore_errors=True)
        proc = self._run_mvn([
            "test",
            f"-Dtest={','.join(test_classes)}",
            "-Dsurefire.failIfNoSpecifiedTests=false",
            "-DfailIfNoTests=false",
        ])
        results = SurefireResults.from_dir(self.repo_path / "target" / "surefire-reports", test_classes)
        return proc, results

    def _run_pit(self, target_classes: List[str], target_tests: List[str], mutators: str, full_matrix: bool) -> Dict[str, Any]:
        shutil.rmtree(self.repo_path / "target" / "pit-reports", ignore_errors=True)
        start = time.perf_counter()
        proc = self._run_mvn([
            f"org.pitest:pitest-maven:{PIT_VERSION}:mutationCoverage",
            f"-DtargetClasses={','.join(target_classes)}",
            f"-DtargetTests={','.join(target_tests)}",
            f"-Dmutators={mutators}",
            "-DtimestampedReports=false",
            f"-DfullMutationMatrix={'true' if full_matrix else 'false'}",
        ])
        wall = time.perf_counter() - start
        xml = self._find_pit_xml()
        if proc.returncode != 0 or xml is None:
            raise RuntimeError(f"PIT failed (exit {proc.returncode}):\n{proc.stdout[-2000:]}\n{proc.stderr[-1500:]}")
        return {
            "xml": xml,
            "report": PitMutationReport(xml),
            "wall_seconds": round(wall, 1),
            "output": proc.stdout,
            **parse_pit_timings(proc.stdout),
        }

    def _archive_pit_run(self, bug_id: str, suite_type: str, pit: Dict[str, Any]) -> Path:
        """Keeps the raw report and PIT's console output (with its timing table) for auditing."""
        suite_dir = self.raw_dir / bug_id / suite_type
        suite_dir.mkdir(parents=True, exist_ok=True)
        with gzip.open(suite_dir / "pit-output.log.gz", "wt", encoding="utf-8") as f:
            f.write(pit["output"])
        return self._archive(pit["xml"], suite_dir / "mutations.xml", compress=True)

    def _archive(self, src: Path, dest: Path, compress: bool = False) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if compress:
            dest = dest.with_name(dest.name + ".gz")
            with open(src, "rb") as fin, gzip.open(dest, "wb") as fout:
                shutil.copyfileobj(fin, fout)
        else:
            shutil.copy2(src, dest)
        return dest

    def _archive_surefire(self, bug_id: str, stage: str, test_classes: List[str]) -> None:
        reports = self.repo_path / "target" / "surefire-reports"
        for cls in test_classes:
            src = reports / f"TEST-{cls}.xml"
            if src.exists():
                self._archive(src, self.raw_dir / bug_id / stage / "surefire" / src.name)

    # -- Experiment ----------------------------------------------------------

    def _added_test_methods(self, commit_hash: str, parent_hash: str, test_files: List[str]) -> Tuple[List[str], List[str]]:
        """Finds the test methods that the fix commit really adds.

        Added = declared in the fixed version but not in the buggy version (so a method whose
        signature line merely changed is not counted). Methods without a JUnit test annotation
        are helpers and are returned separately.
        """
        added: Set[str] = set()
        helpers: Set[str] = set()
        for tf in test_files:
            after = self._git_show(commit_hash, tf)
            before = self._git_show(parent_hash, tf)
            new_methods = declared_methods(after) - declared_methods(before)
            _, not_tests = disable_test_methods(after, sorted(new_methods))
            helpers |= set(not_tests)
            added |= new_methods - set(not_tests)
        return sorted(added), sorted(helpers)

    def _disable_added_tests(self, test_files: List[str], added_tests: List[str]) -> None:
        for tf in test_files:
            file_path = self.repo_path / tf
            if file_path.exists():
                code, _ = disable_test_methods(file_path.read_text(encoding="utf-8"), added_tests)
                file_path.write_text(code, encoding="utf-8")

    def _suite_row(self, base: Dict[str, Any], suite_type: str, results: SurefireResults, pit: Dict[str, Any],
                   added_count: int, fault_detected: int, fault_revealing: List[str], raw_report: Path) -> Dict[str, Any]:
        s = pit["report"].summary()
        return {
            **base,
            "suite_type": suite_type,
            "test_count": results.total,
            "test_methods": len(results.methods()),
            "added_tests": added_count,
            "total_mutants": s["total_mutants"],
            "detected": s["detected"],
            "killed": s["killed"],
            "survived": s["survived"],
            "no_coverage": s["no_coverage"],
            "timed_out": s["timed_out"],
            "other": s["other"],
            "mutation_score": s["mutation_score"],
            "test_strength": s["test_strength"],
            "killed_only_score": s["killed_only_score"],
            "wall_seconds": pit["wall_seconds"],
            "pit_total_seconds": pit["pit_total_seconds"],
            "pit_analysis_seconds": pit["pit_analysis_seconds"],
            "fault_detected": fault_detected,
            "fault_revealing_tests": ";".join(fault_revealing),
            "raw_report": str(raw_report.relative_to(PROJECT_ROOT)) if raw_report.is_relative_to(PROJECT_ROOT) else str(raw_report),
        }

    def _operator_rows(self, bug_id: str, suite_type: str, pit: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows = []
        for mutator, c in sorted(pit["report"].summary()["by_mutator"].items()):
            rows.append({"bug_id": bug_id, "suite_type": suite_type, "mutator": mutator, **c})
        return rows

    def run_trial(self, candidate: Dict[str, Any], mutators: str = "STRONGER", full_matrix: bool = True) -> Dict[str, Any]:
        commit_hash = candidate["commit_hash"]
        parent_hash = candidate["parent_hash"]
        bug_id = commit_hash[:8]
        target_classes = candidate["target_classes"]
        target_tests = candidate["target_tests"]
        test_files = candidate["test_files"]
        title = candidate.get("message", "").split("\n")[0][:60]

        print(f"\n=======================================================")
        print(f"Running Experiment on Bug {bug_id}: {title}")
        print(f"Target Classes: {', '.join(target_classes)} | Target Tests: {', '.join(target_tests)}")
        print(f"Mutators: {mutators} | Full mutation matrix: {full_matrix}")
        print(f"=======================================================\n")

        added_tests, helpers = self._added_test_methods(commit_hash, parent_hash, test_files)
        miner_only = sorted(set(candidate.get("added_test_methods", [])) - set(added_tests) - set(helpers))
        print(f"Added test methods: {', '.join(added_tests) or '(none)'}")
        if helpers:
            print(f"      Ignoring added helper methods (no test annotation): {', '.join(helpers)}")
        if miner_only:
            print(f"      Ignoring {len(miner_only)} miner-listed methods that already existed before the fix: {', '.join(miner_only)}")
        if not added_tests:
            raise TrialSkipped("the fix commit adds no new test methods")

        try:
            # -------------------------------------------------------------
            # STEP 1: Which tests fail on V_bug?
            # -------------------------------------------------------------
            print(f"[1/3] Running the post-fix tests on buggy commit {parent_hash[:8]}...")
            run_cmd(["git", "checkout", "-f", parent_hash], self.repo_path)
            run_cmd(["git", "checkout", commit_hash, "--"] + test_files, self.repo_path)
            bug_proc, bug_results = self._run_tests(target_tests)
            self._archive_surefire(bug_id, "v_bug", target_tests)
            if bug_results.total == 0:
                raise TrialSkipped(
                    "no tests ran on V_bug (the post-fix tests probably do not compile against the buggy code)\n"
                    + bug_proc.stdout[-1500:]
                )
            bug = classify_bug_run(bug_results.failing_methods(), set(added_tests))
            print(f"      Failing on V_bug: {', '.join(bug['fault_revealing_tests']) or '(none: the bug is not reproduced)'}")

            # -------------------------------------------------------------
            # STEP 2: T_base on V_fix
            # -------------------------------------------------------------
            print(f"\n[2/3] T_base on fixed commit {commit_hash[:8]} (added tests disabled)...")
            run_cmd(["git", "checkout", "-f", commit_hash], self.repo_path)
            self._ensure_pit_in_pom()
            self._disable_added_tests(test_files, added_tests)
            _, base_results = self._run_tests(target_tests)
            if base_results.total == 0:
                raise TrialSkipped("T_base has no tests (the test class is new in the fix commit)")
            if not base_results.is_green:
                raise TrialSkipped(f"T_base is not green on V_fix ({base_results.failed} failing of {base_results.total})")
            leaked = sorted(set(added_tests) & base_results.methods())
            if leaked:
                raise TrialSkipped(f"added tests still ran in T_base: {', '.join(leaked)}")
            self._archive_surefire(bug_id, "base", target_tests)
            base_pit = self._run_pit(target_classes, target_tests, mutators, full_matrix)
            base_raw = self._archive_pit_run(bug_id, "base", base_pit)
            print(f"      T_base: {base_results.total} tests | MS = {base_pit['report'].summary()['mutation_score']:.2f}% | PIT {base_pit['wall_seconds']}s")

            # -------------------------------------------------------------
            # STEP 3: T_aug on V_fix
            # -------------------------------------------------------------
            print(f"\n[3/3] T_aug on fixed commit {commit_hash[:8]} (added tests restored)...")
            run_cmd(["git", "checkout", "--"] + test_files, self.repo_path)
            _, aug_results = self._run_tests(target_tests)
            if not aug_results.is_green:
                raise TrialSkipped(f"T_aug is not green on V_fix ({aug_results.failed} failing of {aug_results.total})")
            missing = sorted(set(added_tests) - aug_results.methods())
            if missing:
                raise TrialSkipped(f"added tests did not run in T_aug: {', '.join(missing)}")
            self._archive_surefire(bug_id, "augmented", target_tests)
            aug_pit = self._run_pit(target_classes, target_tests, mutators, full_matrix)
            aug_raw = self._archive_pit_run(bug_id, "augmented", aug_pit)
            print(f"      T_aug:  {aug_results.total} tests | MS = {aug_pit['report'].summary()['mutation_score']:.2f}% | PIT {aug_pit['wall_seconds']}s")
        finally:
            run_cmd(["git", "reset", "--hard", commit_hash], self.repo_path)

        # -------------------------------------------------------------
        # Record results
        # -------------------------------------------------------------
        common = {
            "bug_id": bug_id,
            "commit_hash": commit_hash,
            "parent_hash": parent_hash,
            "project": self.project,
            "target_classes": ";".join(target_classes),
            "target_tests": ";".join(target_tests),
            "mutators": mutators,
            "full_matrix": int(full_matrix),
            "pit_version": PIT_VERSION,
            "java_home": self.java_home,
        }
        base_fault_revealing = [t for t in bug["fault_revealing_tests"] if t not in added_tests]
        rows = [
            self._suite_row(common, "base", base_results, base_pit, 0, bug["detected_base"], base_fault_revealing, base_raw),
            self._suite_row(common, "augmented", aug_results, aug_pit, len(added_tests), bug["detected_aug"], bug["fault_revealing_tests"], aug_raw),
        ]
        upsert_rows(self.results_dir / "runs.csv", RUN_FIELDS, rows, ("bug_id", "suite_type"))
        upsert_rows(
            self.results_dir / "operators.csv",
            OPERATOR_FIELDS,
            self._operator_rows(bug_id, "base", base_pit) + self._operator_rows(bug_id, "augmented", aug_pit),
            ("bug_id", "suite_type", "mutator"),
        )
        print(f"\n[✓] Results written to {self.results_dir}/runs.csv and operators.csv")

        ms_base = rows[0]["mutation_score"]
        ms_aug = rows[1]["mutation_score"]
        return {
            "ms_base": ms_base,
            "ms_aug": ms_aug,
            "delta_ms": (ms_aug - ms_base) if ms_base is not None and ms_aug is not None else None,
            "real_bug_detected": bug["detected_aug"],
            "fault_revealing_tests": bug["fault_revealing_tests"],
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run mutation experiment on a mined bug.")
    parser.add_argument("--repo", required=True, help="Path to git repository")
    parser.add_argument("--mined-bugs", default="data/mined_bugs_commons_lang.json", help="Path to mined bugs JSON")
    parser.add_argument("--index", type=int, default=3, help="Index of bug in mined JSON to run")
    parser.add_argument("--mutators", default="STRONGER", help="PIT mutator group")
    parser.add_argument("--no-full-matrix", action="store_true", help="Do not ask PIT for the full mutation matrix")
    parser.add_argument("--results-dir", default="data/v2", help="Directory for runs.csv and operators.csv")
    parser.add_argument("--raw-dir", default="data/raw", help="Directory for archived raw reports")
    parser.add_argument("--timeout-minutes", type=float, default=None, help="Timeout per Maven command")
    args = parser.parse_args()

    with open(args.mined_bugs, "r", encoding="utf-8") as f:
        mined = json.load(f)

    runner = ExperimentRunner(args.repo, args.results_dir, args.raw_dir, timeout_minutes=args.timeout_minutes)
    try:
        result = runner.run_trial(mined[args.index], mutators=args.mutators, full_matrix=not args.no_full_matrix)
    except TrialSkipped as e:
        print(f"\n[skipped] {e}")
        sys.exit(2)
    print(json.dumps(result, indent=2))
