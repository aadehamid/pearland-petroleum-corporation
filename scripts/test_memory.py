#!/usr/bin/env python3
"""Tests for scripts/memory.sh, the shared Relate project memory.

Each test uses its own store in a temporary directory through PPC_MEMORY_DB,
so the tests never touch the real memory. They skip when relate is not
installed, as on CI runners.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

MEMORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.sh")


def episode(eid, at, agent, facts):
    return {
        "episode": {"id": eid, "session": "s-" + eid, "agent": agent,
                    "kind": "decision", "at": at, "text": "evidence for " + eid},
        "mentions": [{"key": "r2", "name": "Cloudflare R2"}],
        "facts": facts,
    }


def fact(fid, text, slot="r2/hidden-truth-bucket"):
    return {"id": fid, "text": text, "slot": slot, "about": ["r2"]}


@unittest.skipUnless(shutil.which("relate"), "relate is not installed")
class MemoryScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, PPC_MEMORY_DB=os.path.join(self.tmp.name, "memory"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_memory(self, *args, stdin=None):
        return subprocess.run(["bash", MEMORY, *args], input=stdin, env=self.env,
                              capture_output=True, text=True, timeout=60)

    def remember(self, payload):
        p = self.run_memory("remember", "-", stdin=json.dumps(payload))
        self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def rows(self, *args):
        p = self.run_memory(*args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return [json.loads(line) for line in p.stdout.splitlines() if line.startswith("{")]

    def test_reads_before_init_report_no_memory(self):
        p = self.run_memory("recall", "bucket")
        self.assertEqual(p.returncode, 0)
        self.assertIn("no memory yet", p.stderr)

    def test_correction_supersedes_and_keeps_history(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "claude-code",
                              [fact("f1", "Hidden truth lives in bucket pearland-petroleum-hidden.")]))
        self.remember(episode("e2", "2026-11-28T10:00:00Z", "codex",
                              [fact("f2", "Hidden truth moved to bucket ppc-hidden.")]))

        current = self.rows("recall", "hidden", "bucket")
        self.assertEqual([r["memory"] for r in current], ["Hidden truth moved to bucket ppc-hidden."])
        self.assertEqual(current[0]["agent"], "codex")

        history = self.rows("history", "r2/hidden-truth-bucket")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["closed"], "2026-11-28T10:00:00Z")
        self.assertIsNone(history[1]["closed"])

        self.assertEqual(len(self.rows("about", "r2")), 1)
        self.assertEqual(self.run_memory("check").returncode, 0)

    def test_repeating_an_episode_changes_nothing(self):
        payload = episode("e1", "2026-11-27T10:00:00Z", "claude-code", [fact("f1", "One bucket fact.")])
        self.remember(payload)
        self.remember(payload)
        self.assertEqual(len(self.rows("history", "r2/hidden-truth-bucket")), 1)

    def test_invalid_episode_is_rejected_before_writing(self):
        p = self.run_memory("remember", "-", stdin=json.dumps({"episode": {"id": "x"}, "facts": []}))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("episode.agent: missing string", p.stderr)
        self.assertFalse(os.path.exists(self.env["PPC_MEMORY_DB"]))

    def test_concurrent_writers_all_land(self):
        self.assertEqual(self.run_memory("init").returncode, 0)
        procs = []
        for i in range(4):
            payload = episode(f"e{i}", f"2026-11-27T1{i}:00:00Z", f"agent-{i}",
                              [fact(f"f{i}", f"Fact number {i}.", slot=f"test/slot-{i}")])
            procs.append(subprocess.Popen(["bash", MEMORY, "remember", "-"], stdin=subprocess.PIPE,
                                          env=self.env, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE, text=True))
            procs[-1].stdin.write(json.dumps(payload))
            procs[-1].stdin.close()
            procs[-1].stdin = None
        for proc in procs:
            _, err = proc.communicate(timeout=60)
            self.assertEqual(proc.returncode, 0, err)
        self.assertEqual(len(self.rows("slots")), 4)


if __name__ == "__main__":
    unittest.main()
