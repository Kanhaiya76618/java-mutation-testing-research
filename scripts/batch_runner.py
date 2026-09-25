"""
scripts/batch_runner.py

Executes mutation testing experiments across a batch of mined bugs.
Handles timeouts, compile issues, and ensures PIT configuration is intact.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_experiment import ExperimentRunner, run_cmd


PIT_POM_SNIPPET = """
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


def ensure_pit_plugin(pom_path: Path) -> None:
    """Ensures pitest-maven with junit5 plugin is configured in pom.xml."""
    content = pom_path.read_text(encoding="utf-8")
    if "pitest-maven" in content and "pitest-junit5-plugin" in content:
        return

    # Insert under <plugins>
    match = re.search(r"<plugins>", content)
    if match:
        idx = match.end()
        new_content = content[:idx] + PIT_POM_SNIPPET + content[idx:]
        pom_path.write_text(new_content, encoding="utf-8")
        print("  [pom.xml] Injected pitest-maven plugin configuration.")


class RobustBatchRunner:
    def __init__(self, repo_path: str | Path, bugs_json: str | Path, results_csv: str | Path):
        self.repo_path = Path(repo_path).resolve()
        self.bugs_json = Path(bugs_json).resolve()
        self.results_csv = Path(results_csv).resolve()
        self.runner = ExperimentRunner(self.repo_path, self.results_csv)

    def run_all(self, start_idx: int = 0, limit: int = 10, mutators: str = "STRONGER"):
        with open(self.bugs_json, "r", encoding="utf-8") as f:
            bugs = json.load(f)

        total = min(len(bugs), start_idx + limit)
        print(f"\n==================================================")
        print(f"Starting Batch Experiment: Bugs {start_idx} to {total - 1} (Total: {total - start_idx})")
        print(f"==================================================\n")

        successes = 0
        failures = 0

        for i in range(start_idx, total):
            candidate = bugs[i]
            desc = candidate.get("message", "").split("\n")[0][:45]
            print(f"\n>>> [{i + 1}/{total}] Processing Candidate: {desc} ({candidate['commit_hash'][:8]})")

            try:
                # Ensure POM has PIT
                ensure_pit_plugin(self.repo_path / "pom.xml")

                # Run experiment trial
                res = self.runner.run_trial(candidate, mutators=mutators)
                print(f"  [✓] Candidate {i} Finished: Delta MS = {res['delta_ms']:+.2f}%, Detected = {res['real_bug_detected']}")
                successes += 1
            except Exception as e:
                print(f"  [✗] Candidate {i} Failed: {e}")
                failures += 1
                # Reset working directory
                run_cmd(["git", "reset", "--hard", "HEAD"], self.repo_path)

        print(f"\n==================================================")
        print(f"Batch Run Finished: {successes} Succeeded, {failures} Failed.")
        print(f"Results stored in: {self.results_csv}")
        print(f"==================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch mutation testing experiments.")
    parser.add_argument("--repo", default="benchmarks/commons-lang", help="Repository path")
    parser.add_argument("--mined-bugs", default="data/mined_bugs_commons_lang.json", help="Mined bugs JSON")
    parser.add_argument("--results-csv", default="data/processed_results.csv", help="Results CSV")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--limit", type=int, default=5, help="Number of bugs to evaluate")
    parser.add_argument("--mutators", default="STRONGER", help="Mutators set")
    args = parser.parse_args()

    batch = RobustBatchRunner(args.repo, args.mined_bugs, args.results_csv)
    batch.run_all(start_idx=args.start, limit=args.limit, mutators=args.mutators)
