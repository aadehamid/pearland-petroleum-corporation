#!/usr/bin/env python3
"""Tests for scripts/hooks/pre-push and scripts/check.sh hook-environment guards."""
import os
import shutil
import subprocess
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks", "pre-push")
CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check.sh")
HOOK_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_PREFIX")
ZERO = "0" * 40
SHA = "1" * 40


def run(stdin, check_status=0):
    with tempfile.TemporaryDirectory() as repo:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        subprocess.run(["git", "init", "-q", repo], env=env, check=True)
        os.makedirs(os.path.join(repo, "scripts", "hooks"))
        hook = os.path.join(repo, "scripts", "hooks", "pre-push")
        shutil.copy(HOOK, hook)
        check = os.path.join(repo, "scripts", "check.sh")
        with open(check, "w") as f:
            f.write(f"#!/usr/bin/env bash\necho CHECKS RAN\nexit {check_status}\n")
        os.chmod(check, 0o755)
        p = subprocess.run(
            ["bash", hook, "origin", "git@example:repo.git"],
            input=stdin,
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        return p.returncode, p.stdout


class CheckScriptGuards(unittest.TestCase):
    def setUp(self):
        with open(CHECK) as f:
            self.text = f.read()

    def test_the_hook_variables_are_cleared_before_the_first_check(self):
        unset = next(line for line in self.text.splitlines() if line.startswith("unset GIT_"))
        self.assertEqual(set(unset.split()[1:]), set(HOOK_VARS))
        self.assertLess(self.text.index(unset), self.text.index("check_package.py"))

    def test_a_bare_repository_after_the_checks_fails_them(self):
        self.assertIn('if [ "$(git config --get core.bare || true)" = "true" ]; then', self.text)
        self.assertLess(self.text.index("core.bare || true"), self.text.index("All checks passed."))


class PrePushHook(unittest.TestCase):
    def test_a_delete_only_push_skips_the_checks(self):
        status, out = run(f"(delete) {ZERO} refs/heads/a {SHA}\n(delete) {ZERO} refs/heads/b {SHA}\n")
        self.assertEqual(status, 0)
        self.assertNotIn("CHECKS RAN", out)

    def test_a_sha256_delete_skips_the_checks(self):
        status, out = run(f"(delete) {'0' * 64} refs/heads/a {'1' * 64}\n")
        self.assertEqual(status, 0)
        self.assertNotIn("CHECKS RAN", out)

    def test_a_push_with_commits_runs_the_checks(self):
        status, out = run(f"refs/heads/a {SHA} refs/heads/a {ZERO}\n")
        self.assertEqual(status, 0)
        self.assertIn("CHECKS RAN", out)

    def test_a_delete_with_an_update_runs_the_checks(self):
        _, out = run(f"(delete) {ZERO} refs/heads/a {SHA}\nrefs/heads/b {SHA} refs/heads/b {SHA}\n")
        self.assertIn("CHECKS RAN", out)

    def test_no_ref_lines_runs_the_checks(self):
        status, out = run("")
        self.assertEqual(status, 0)
        self.assertIn("CHECKS RAN", out)

    def test_a_failing_check_fails_the_push(self):
        status, out = run(f"refs/heads/a {SHA} refs/heads/a {ZERO}\n", check_status=1)
        self.assertEqual(status, 1)
        self.assertIn("CHECKS RAN", out)


if __name__ == "__main__":
    unittest.main()
