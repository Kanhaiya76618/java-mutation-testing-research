"""
tests/test_git_miner.py

Unit test for harness/git_miner.py using a simulated git repository.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from harness.git_miner import GitMiner


class TestGitMiner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        self.env = {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        }
        self._run_git(["init"])
        self._run_git(["config", "user.name", "Test User"])
        self._run_git(["config", "user.email", "test@example.com"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_git(self, args):
        subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_path),
            env=self.env,
            check=True,
            capture_output=True,
        )

    def test_mine_bug_candidate(self):
        # 1. Base commit
        prod_dir = self.repo_path / "src" / "main" / "java" / "org" / "example"
        test_dir = self.repo_path / "src" / "test" / "java" / "org" / "example"
        prod_dir.mkdir(parents=True)
        test_dir.mkdir(parents=True)

        calc_file = prod_dir / "Calculator.java"
        calc_file.write_text("package org.example;\npublic class Calculator { public int divide(int a, int b) { return a / b; } }")

        test_file = test_dir / "CalculatorTest.java"
        test_file.write_text("package org.example;\npublic class CalculatorTest { public void testDivide() {} }")

        self._run_git(["add", "-A"])
        self._run_git(["commit", "-m", "Initial implementation"])

        # 2. Bug-fix commit with added test
        calc_file.write_text("package org.example;\npublic class Calculator { public int divide(int a, int b) { if (b == 0) throw new IllegalArgumentException(); return a / b; } }")
        test_file.write_text("package org.example;\npublic class CalculatorTest { public void testDivide() {}\n public void testDivideByZero() {} }")

        self._run_git(["add", "-A"])
        self._run_git(["commit", "-m", "fix: handle division by zero bug in calculator"])

        # 3. Mine with GitMiner
        miner = GitMiner(self.repo_path)
        candidates = miner.mine_candidates(max_commits=10, limit=5)

        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertIn("fix: handle division by zero bug", c.message)
        self.assertIn("org.example.Calculator", c.target_classes)
        self.assertIn("org.example.CalculatorTest", c.target_tests)
        self.assertIn("testDivideByZero", c.added_test_methods)


if __name__ == "__main__":
    unittest.main()
