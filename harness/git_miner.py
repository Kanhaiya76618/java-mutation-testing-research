"""
harness/git_miner.py

Mines bug-fixing commits and regression test pairs from any Java Git repository.
Filters for isolated regression fixes that modify both production source code
(src/main/java) and corresponding test files (src/test/java).
"""

from __future__ import annotations
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


BUG_KEYWORDS = re.compile(
    r"\b(fix|fixes|fixed|bug|bugs|issue|issues|resolve|resolves|resolved|defect|patch)\b",
    re.IGNORECASE,
)


@dataclass
class BugFixCandidate:
    commit_hash: str
    parent_hash: str
    author_date: str
    message: str
    prod_files: List[str]
    test_files: List[str]
    target_classes: List[str]
    target_tests: List[str]
    added_test_methods: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GitMiner:
    def __init__(self, repo_path: str | Path, max_files_changed: int = 10):
        self.repo_path = Path(repo_path).resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Directory is not a Git repository: {self.repo_path}")
        self.max_files_changed = max_files_changed

    def _run_git(self, args: List[str]) -> str:
        """Executes a git command safely inside repo_path without relying on external configs."""
        cmd = ["git"] + args
        env = {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        }
        res = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def get_recent_commits(self, max_commits: int = 200) -> List[Dict[str, str]]:
        """Returns recent commit SHAs, parent SHAs, dates, and messages."""
        # Format: %H%x00%P%x00%ad%x00%s
        log_out = self._run_git([
            "log",
            f"-n{max_commits}",
            "--date=short",
            "--format=%H%x00%P%x00%ad%x00%s",
        ])
        commits = []
        if not log_out:
            return commits

        for line in log_out.splitlines():
            parts = line.split("\x00")
            if len(parts) >= 4:
                parents = parts[1].split()
                # Ignore merge commits (more than 1 parent) or root commits (0 parents)
                if len(parents) == 1:
                    commits.append({
                        "commit_hash": parts[0],
                        "parent_hash": parents[0],
                        "author_date": parts[2],
                        "message": parts[3],
                    })
        return commits

    def get_changed_files(self, commit_hash: str, parent_hash: str) -> List[str]:
        """Returns list of modified or added file paths between parent and commit."""
        diff_out = self._run_git([
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            f"{parent_hash}..{commit_hash}",
        ])
        return [f.strip() for f in diff_out.splitlines() if f.strip()]

    def extract_java_class(self, file_path: str) -> Optional[str]:
        """Converts src/main/java/org/example/Foo.java -> org.example.Foo."""
        path = Path(file_path)
        if path.suffix != ".java":
            return None
        parts = list(path.parts)
        for prefix in [("src", "main", "java"), ("src", "test", "java")]:
            for i in range(len(parts) - len(prefix)):
                if tuple(parts[i : i + len(prefix)]) == prefix:
                    package_parts = parts[i + len(prefix) : -1]
                    class_name = path.stem
                    if package_parts:
                        return ".".join(package_parts) + "." + class_name
                    return class_name
        return path.stem

    def extract_added_test_methods(self, commit_hash: str, parent_hash: str, test_files: List[str]) -> List[str]:
        """Extracts newly added @Test methods from git diff."""
        if not test_files:
            return []
        diff_out = self._run_git([
            "diff",
            "-U0",
            f"{parent_hash}..{commit_hash}",
            "--",
        ] + test_files)

        added_methods = []
        for line in diff_out.splitlines():
            # Matches added method signatures: +   public void testFoo() or +   void testBar()
            if line.startswith("+") and not line.startswith("+++"):
                match = re.search(r"void\s+([a-zA-Z0-9_]+)\s*\(", line)
                if match:
                    added_methods.append(match.group(1))
        return list(dict.fromkeys(added_methods))

    def mine_candidates(self, max_commits: int = 300, limit: int = 20) -> List[BugFixCandidate]:
        """Scans commit history for bug fix candidates."""
        all_commits = self.get_recent_commits(max_commits)
        candidates: List[BugFixCandidate] = []

        for c in all_commits:
            msg = c["message"]
            if not BUG_KEYWORDS.search(msg):
                continue

            try:
                changed_files = self.get_changed_files(c["commit_hash"], c["parent_hash"])
            except subprocess.CalledProcessError:
                continue

            if len(changed_files) == 0 or len(changed_files) > self.max_files_changed:
                continue

            prod_files = [
                f for f in changed_files
                if "src/main/java" in f and f.endswith(".java")
            ]
            test_files = [
                f for f in changed_files
                if "src/test/java" in f and f.endswith(".java")
            ]

            # Require changes in both production code and test code
            if not prod_files or not test_files:
                continue

            target_classes = [
                cls for f in prod_files if (cls := self.extract_java_class(f))
            ]
            target_tests = [
                t for f in test_files if (t := self.extract_java_class(f))
            ]

            added_tests = self.extract_added_test_methods(
                c["commit_hash"], c["parent_hash"], test_files
            )

            candidates.append(
                BugFixCandidate(
                    commit_hash=c["commit_hash"],
                    parent_hash=c["parent_hash"],
                    author_date=c["author_date"],
                    message=msg,
                    prod_files=prod_files,
                    test_files=test_files,
                    target_classes=target_classes,
                    target_tests=target_tests,
                    added_test_methods=added_tests,
                )
            )

            if len(candidates) >= limit:
                break

        return candidates


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mine bug-fixing commits from a Java Git repo.")
    parser.add_argument("--repo", required=True, help="Path to local Java git repository")
    parser.add_argument("--limit", type=int, default=15, help="Maximum number of candidates to mine")
    parser.add_argument("--output", default="data/mined_bugs.json", help="Path to save mined JSON")
    args = parser.parse_args()

    miner = GitMiner(args.repo)
    results = miner.mine_candidates(limit=args.limit)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in results], f, indent=2)

    print(f"Mined {len(results)} candidate bug fixes -> {out_path}")
