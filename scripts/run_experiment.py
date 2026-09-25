"""
scripts/run_experiment.py

Automates the empirical evaluation of a single bug-fix pair:
1. Verifies if the regression test detects the real bug on V_bug (pre-fix).
2. Runs PIT mutation analysis on V_fix with base test suite (T_base) -> MS_base.
3. Runs PIT mutation analysis on V_fix with augmented test suite (T_aug) -> MS_aug.
4. Computes Delta MS and logs metrics into data/processed_results.csv.
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.pit_parser import PitMutationReport


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    jdk21_path = Path("/opt/homebrew/opt/openjdk@21")
    if jdk21_path.exists():
        env["JAVA_HOME"] = str(jdk21_path)
        env["PATH"] = f"{jdk21_path}/bin:{env.get('PATH', '')}"
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class ExperimentRunner:
    def __init__(self, repo_path: str | Path, results_csv: str | Path = "data/processed_results.csv"):
        self.repo_path = Path(repo_path).resolve()
        self.results_csv = Path(results_csv).resolve()

    def _run_mvn(self, args: List[str]) -> subprocess.CompletedProcess:
        mvn_cmd = ["mvn", "-B", "-Drat.skip=true"] + args
        return run_cmd(mvn_cmd, self.repo_path)

    def _find_pit_xml(self) -> Optional[Path]:
        """Finds the most recent mutations.xml in target/pit-reports/."""
        reports_dir = self.repo_path / "target" / "pit-reports"
        if not reports_dir.exists():
            return None
        xmls = list(reports_dir.rglob("mutations.xml"))
        if not xmls:
            return None
        # Sort by modification time descending
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

        snippet = """
      <plugin>
        <groupId>org.pitest</groupId>
        <artifactId>pitest-maven</artifactId>
        <version>1.16.0</version>
        <dependencies>
          <dependency>
            <groupId>org.pitest</groupId>
            <artifactId>pitest-junit5-plugin</artifactId>
            <version>1.2.1</version>
          </dependency>
        </dependencies>
        <configuration>
          <outputFormats>
            <outputFormat>XML</outputFormat>
            <outputFormat>CSV</outputFormat>
          </outputFormats>
        </configuration>
      </plugin>
"""
        match = re.search(r"<plugins>", content)
        if match:
            idx = match.end()
            new_content = content[:idx] + snippet + content[idx:]
            pom_path.write_text(new_content, encoding="utf-8")

    def _clear_pit_reports(self) -> None:
        reports_dir = self.repo_path / "target" / "pit-reports"
        if reports_dir.exists():
            import shutil
            shutil.rmtree(reports_dir, ignore_errors=True)

    def _disable_test_methods(self, test_files: List[str], methods: List[str]) -> None:
        """Disables the added test methods by commenting out their test annotations so T_base runs green."""
        for tf in test_files:
            file_path = self.repo_path / tf
            if not file_path.exists():
                continue
            code = file_path.read_text(encoding="utf-8")
            for m in methods:
                parts = code.split(f"void {m}(")
                if len(parts) > 1:
                    prefix = parts[0]
                    matches = list(re.finditer(r'@(?:ParameterizedTest|Test)\b', prefix))
                    if matches:
                        last = matches[-1]
                        prefix = prefix[:last.start()] + "/* " + last.group(0) + " */" + prefix[last.end():]
                        code = prefix + f"void {m}(" + parts[1]
            file_path.write_text(code, encoding="utf-8")

    def run_trial(self, candidate: Dict[str, Any], mutators: str = "STRONGER") -> Dict[str, Any]:
        commit_hash = candidate["commit_hash"]
        parent_hash = candidate["parent_hash"]
        target_class = candidate["target_classes"][0]
        target_test = candidate["target_tests"][0]
        test_files = candidate["test_files"]
        added_methods = candidate.get("added_test_methods", [])
        bug_id = candidate.get("message", commit_hash[:8]).split("\n")[0][:40]

        print(f"\n=======================================================")
        print(f"Running Experiment on Bug: {bug_id}")
        print(f"Target Class: {target_class} | Target Test: {target_test}")
        print(f"Mutators: {mutators}")
        print(f"=======================================================\n")

        # -------------------------------------------------------------
        # STEP 1: Verify Real Fault Detection on V_bug
        # -------------------------------------------------------------
        print(f"[1/3] Checking real fault detection on buggy commit {parent_hash[:8]}...")
        run_cmd(["git", "checkout", "-f", parent_hash], self.repo_path)
        # Apply the test additions to the buggy version
        run_cmd(["git", "checkout", commit_hash, "--"] + test_files, self.repo_path)

        test_res = self._run_mvn(["test", f"-Dtest={target_test}"])
        # If the test suite fails on V_bug, the added test caught the real regression!
        real_bug_detected = 1 if test_res.returncode != 0 else 0
        print(f"      Real bug detected: {'YES (1)' if real_bug_detected else 'NO (0)'}")

        # -------------------------------------------------------------
        # STEP 2: Run PIT on V_fix with BASE test suite (T_base)
        # -------------------------------------------------------------
        print(f"\n[2/3] Measuring MS_base on fixed code with base tests (T_base)...")
        run_cmd(["git", "checkout", "-f", commit_hash], self.repo_path)
        self._ensure_pit_in_pom()
        # Disable the newly added test methods so existing tests run cleanly
        if added_methods:
            self._disable_test_methods(test_files, added_methods)
            self._run_mvn(["test-compile"])

        self._clear_pit_reports()
        pit_base_res = self._run_mvn([
            "org.pitest:pitest-maven:1.16.0:mutationCoverage",
            f"-DtargetClasses={target_class}",
            f"-DtargetTests={target_test}",
            f"-Dmutators={mutators}",
            "-DoutputFormats=XML,CSV",
        ])
        xml_base = self._find_pit_xml()
        if not xml_base:
            raise RuntimeError(f"PIT did not generate mutations.xml for T_base (exit {pit_base_res.returncode}):\n{pit_base_res.stdout[-1500:]}\n{pit_base_res.stderr[-1500:]}")
        report_base = PitMutationReport(xml_base).summary()
        ms_base = report_base["mutation_score"]
        print(f"      MS_base: {ms_base}% ({report_base['killed']}/{report_base['total_mutants']} killed)")

        # -------------------------------------------------------------
        # STEP 3: Run PIT on V_fix with AUGMENTED test suite (T_aug)
        # -------------------------------------------------------------
        print(f"\n[3/3] Measuring MS_aug on fixed code with augmented tests (T_aug)...")
        # Restore the added tests (removing @Disabled)
        run_cmd(["git", "checkout", "--"] + test_files, self.repo_path)
        self._ensure_pit_in_pom()
        self._run_mvn(["test-compile"])

        self._clear_pit_reports()
        pit_aug_res = self._run_mvn([
            "org.pitest:pitest-maven:1.16.0:mutationCoverage",
            f"-DtargetClasses={target_class}",
            f"-DtargetTests={target_test}",
            f"-Dmutators={mutators}",
            "-DoutputFormats=XML,CSV",
        ])
        xml_aug = self._find_pit_xml()
        if not xml_aug:
            raise RuntimeError(f"PIT did not generate mutations.xml for T_aug (exit {pit_aug_res.returncode}):\n{pit_aug_res.stdout[-1500:]}\n{pit_aug_res.stderr[-1500:]}")
        report_aug = PitMutationReport(xml_aug).summary()
        ms_aug = report_aug["mutation_score"]
        delta_ms = round(ms_aug - ms_base, 2)
        print(f"      MS_aug:  {ms_aug}% ({report_aug['killed']}/{report_aug['total_mutants']} killed)")
        print(f"      Delta MS: {delta_ms:+0.2f}%")

        # Cleanup git working directory
        run_cmd(["git", "reset", "--hard", commit_hash], self.repo_path)

        # -------------------------------------------------------------
        # Log Result Rows (both Base and Augmented)
        # -------------------------------------------------------------
        base_row = {
            "bug_id": commit_hash[:8],
            "project": "commons-lang",
            "suite_type": "base",
            "test_count": report_base.get("tests_run", 0),
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "total_mutants": report_base["total_mutants"],
            "killed_mutants": report_base["killed"],
            "survived_mutants": report_base["survived"],
            "timed_out": report_base["timed_out"],
            "no_coverage": report_base["no_coverage"],
            "mutation_score": ms_base,
            "cond_boundary_score": report_base["by_mutator"].get("ConditionalsBoundaryMutator", {}).get("score", 0.0),
            "negate_cond_score": report_base["by_mutator"].get("NegateConditionalsMutator", {}).get("score", 0.0),
            "math_score": report_base["by_mutator"].get("MathMutator", {}).get("score", 0.0),
            "void_call_score": report_base["by_mutator"].get("VoidMethodCallMutator", {}).get("score", 0.0),
            "invert_negs_score": report_base["by_mutator"].get("InvertNegsMutator", {}).get("score", 0.0),
            "real_bug_detected": 0,
        }

        aug_row = {
            "bug_id": commit_hash[:8],
            "project": "commons-lang",
            "suite_type": "augmented",
            "test_count": report_aug.get("tests_run", 0),
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "total_mutants": report_aug["total_mutants"],
            "killed_mutants": report_aug["killed"],
            "survived_mutants": report_aug["survived"],
            "timed_out": report_aug["timed_out"],
            "no_coverage": report_aug["no_coverage"],
            "mutation_score": ms_aug,
            "cond_boundary_score": report_aug["by_mutator"].get("ConditionalsBoundaryMutator", {}).get("score", 0.0),
            "negate_cond_score": report_aug["by_mutator"].get("NegateConditionalsMutator", {}).get("score", 0.0),
            "math_score": report_aug["by_mutator"].get("MathMutator", {}).get("score", 0.0),
            "void_call_score": report_aug["by_mutator"].get("VoidMethodCallMutator", {}).get("score", 0.0),
            "invert_negs_score": report_aug["by_mutator"].get("InvertNegsMutator", {}).get("score", 0.0),
            "real_bug_detected": real_bug_detected,
        }

        self._append_to_csv(base_row)
        self._append_to_csv(aug_row)
        return {
            "ms_base": ms_base,
            "ms_aug": ms_aug,
            "delta_ms": delta_ms,
            "real_bug_detected": real_bug_detected,
        }

    def _append_to_csv(self, row: Dict[str, Any]) -> None:
        self.results_csv.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.results_csv.exists() and self.results_csv.stat().st_size > 0

        with open(self.results_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        print(f"\n[✓] Results appended to {self.results_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run mutation experiment on a mined bug.")
    parser.add_argument("--repo", required=True, help="Path to git repository")
    parser.add_argument("--mined-bugs", default="data/mined_bugs_commons_lang.json", help="Path to mined bugs JSON")
    parser.add_argument("--index", type=int, default=3, help="Index of bug in mined JSON to run")
    parser.add_argument("--mutators", default="STRONGER", help="PIT mutator group")
    args = parser.parse_args()

    with open(args.mined_bugs, "r", encoding="utf-8") as f:
        mined = json.load(f)

    runner = ExperimentRunner(args.repo)
    runner.run_trial(mined[args.index], mutators=args.mutators)
