#!/usr/bin/env python3
"""Tests for scripts/memory.sh, the shared Relate project memory.

Each test uses its own store in a temporary directory through PPC_MEMORY_DB,
except the worktree test, which runs a copy of the script in a temporary git
repository. No test touches the real memory. They skip when relate is not
installed, as on CI runners.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(HERE, "memory.sh")
SLOT = "r2/hidden-truth-bucket"


def episode(eid, at, agent, facts, **extra):
    payload = {
        "episode": {"id": eid, "session": "s-" + eid, "agent": agent,
                    "kind": "decision", "at": at, "text": "evidence for " + eid},
        "mentions": [{"key": "r2", "name": "Cloudflare R2"}],
        "facts": facts,
    }
    payload.update(extra)
    return payload


def fact(fid, text, slot=SLOT, **extra):
    return {"id": fid, "text": text, "slot": slot, "about": ["r2"], **extra}


def git_env():
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


@unittest.skipUnless(shutil.which("relate"), "relate is not installed")
class MemoryScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "memory")
        self.env = dict(git_env(), PPC_MEMORY_DB=self.db, TMPDIR=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_memory(self, *args, stdin=None, script=MEMORY, env=None):
        return subprocess.run(["bash", script, *args], input=stdin, env=env or self.env,
                              capture_output=True, text=True, timeout=60)

    def remember(self, payload):
        p = self.run_memory("remember", "-", stdin=json.dumps(payload))
        self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def rejected(self, payload):
        p = self.run_memory("remember", "-", stdin=json.dumps(payload))
        self.assertNotEqual(p.returncode, 0, p.stdout)
        return p.stderr

    def rows(self, *args):
        p = self.run_memory(*args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return [json.loads(line) for line in p.stdout.splitlines() if line.startswith("{")]

    def assert_check_passes(self):
        p = self.run_memory("check")
        self.assertEqual(p.returncode, 0, p.stderr)

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
        self.assertEqual((current[0]["agent"], current[0]["episode"]), ("codex", "e2"))
        self.assertEqual(current[0]["evidence"], "evidence for e2")

        history = self.rows("history", SLOT)
        self.assertEqual([h["episode"] for h in history], ["e2", "e1"])
        self.assertIsNone(history[0]["closed"])
        self.assertIsNotNone(history[1]["closed"])

        self.assertEqual([r["episode"] for r in self.rows("about", "r2")], ["e2"])
        self.assert_check_passes()

    def test_later_write_wins_whatever_the_learned_time(self):
        self.remember(episode("e1", "2026-11-28T10:05:00Z", "codex", [fact("f1", "Newer by clock.")]))
        self.remember(episode("e2", "2026-11-28T10:00:00Z", "kimi", [fact("f2", "Written later.")]))
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Written later."])
        self.assert_check_passes()

    def test_replaying_episodes_changes_nothing(self):
        first = episode("e1", "2026-11-27T10:00:00Z", "claude-code", [fact("f1", "First value.")])
        second = episode("e2", "2026-11-27T10:00:00Z", "codex", [fact("f2", "Second value.")])
        self.remember(first)
        self.remember(second)
        self.remember(first)
        self.remember(second)
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Second value."])
        self.assertEqual(len(self.rows("history", SLOT)), 2)
        self.assert_check_passes()

    def test_brief_orders_newest_first_and_validates_n(self):
        for i in range(3):
            self.remember(episode(f"e{i}", "2026-11-27T10:00:00Z", "pi",
                                  [fact(f"f{i}", f"Fact {i}.", slot=f"test/slot-{i}")]))
        self.assertEqual([r["memory"] for r in self.rows("brief", "2")], ["Fact 2.", "Fact 1."])
        for bad in ("0", "-1", "two", "1; MATCH (n) DETACH DELETE n"):
            self.assertEqual(self.run_memory("brief", bad).returncode, 2, bad)

    def test_string_parameters_stay_strings(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "cursor",
                              [{"id": "f1", "text": "Flag 42 is true.", "slot": "true/42", "about": ["true"]}],
                              mentions=[]))
        self.assertEqual(len(self.rows("about", "true")), 1)
        self.assertEqual(len(self.rows("history", "true/42")), 1)
        self.assertEqual(len(self.rows("recall", "42")), 1)

    def test_invalid_episodes_are_rejected_before_any_write(self):
        good = fact("f1", "A fact.")
        cases = {
            "episode.agent: missing string": {"episode": {"id": "x"}, "facts": [good]},
            "facts: needs at least one fact": episode("e1", "2026-11-27T10:00:00Z", "pi", []),
            "episode.at: not a UTC": episode("e1", "yesterday", "pi", [good]),
            "facts[0].validFrom: not a UTC": episode("e1", "2026-11-27T10:00:00Z", "pi",
                                                     [fact("f1", "A fact.", validFrom="2026-11-27")]),
            "facts[0].validFrom: not a UTC ": episode("e1", "2026-11-27T10:00:00Z", "pi",
                                                      [fact("f1", "A fact.", validFrom="2026-13-45T10:00:00Z")]),
            "episode.at: not a UTC ": episode("e1", "2026-11-27T10:00:00+99:99", "pi", [good]),
            "episode.at: not a UTC  ": episode("e1", "\u0662\u0660\u0662\u0666-11-27T10:00:00Z", "pi", [good]),
            "episode.kind: one of": dict(episode("e1", "2026-11-27T10:00:00Z", "pi", [good]),
                                         episode={"id": "e1", "session": "s", "agent": "pi",
                                                  "kind": "musing", "at": "2026-11-27T10:00:00Z", "text": "t"}),
            "episode.kind: one of ": dict(episode("e1", "2026-11-27T10:00:00Z", "pi", [good]),
                                          episode={"id": "e1", "session": "s", "agent": "pi",
                                                   "kind": ["decision"], "at": "2026-11-27T10:00:00Z", "text": "t"}),
            "mentions: not a list": episode("e1", "2026-11-27T10:00:00Z", "pi", [good], mentions=None),
            "mentions[0].key: missing string": episode("e1", "2026-11-27T10:00:00Z", "pi", [good],
                                                       mentions=[{"key": " ", "name": "x"}]),
            "facts[0].about: needs": episode("e1", "2026-11-27T10:00:00Z", "pi",
                                             [dict(good, about=[""])]),
            "facts[1].slot: repeats": episode("e1", "2026-11-27T10:00:00Z", "pi",
                                              [good, fact("f2", "Same slot.")]),
            "facts[1].id: repeats": episode("e1", "2026-11-27T10:00:00Z", "pi",
                                            [good, fact("f1", "Other slot.", slot="x/y")]),
        }
        for message, payload in cases.items():
            with self.subTest(message):
                stderr = self.rejected(payload)
                self.assertIn(message.strip(), stderr)
                self.assertNotIn("Traceback", stderr)
                self.assertFalse(os.path.exists(self.db))
        self.assertEqual([f for f in os.listdir(self.tmp.name) if f.startswith("ppc-memory.")], [])

    def test_fact_id_reused_by_another_episode_is_rejected(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f1", "Original.")]))
        stderr = self.rejected(episode("e2", "2026-11-28T10:00:00Z", "pi", [fact("f1", "Reused id.")]))
        self.assertIn("fact id belongs to episode e1", stderr)
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Original."])

    def test_guards_inside_the_transaction_roll_back_the_episode(self):
        # Run remember.cypher straight through relate, past the script's own
        # checks, as a writer that raced another would.
        self.remember(episode("e0", "2026-11-27T09:00:00Z", "pi", [fact("f0", "Kept.", slot="keep/me")]))
        payload = episode("e1", "2026-11-27T10:00:00Z", "pi",
                          [fact("f1", "New fact.", slot="new/slot"), fact("f0", "Stolen id.", slot="other/slot")])
        payload["fingerprint"] = "x"
        path = os.path.join(self.tmp.name, "race.json")
        with open(path, "w") as fh:
            json.dump(payload, fh)
        with open(os.path.join(HERE, "memory", "remember.cypher")) as script:
            p = subprocess.run(["relate", "query", "--database", self.db, "--mode", "jsonl",
                                "--fetch-params", "m=" + path], stdin=script,
                               capture_output=True, text=True, timeout=30)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("by zero", p.stdout + p.stderr)
        self.assertEqual([r["slot"] for r in self.rows("slots")], ["keep/me"])
        count = subprocess.run(["relate", "query", "--database", self.db, "--read-only", "--mode", "jsonl",
                                "MATCH (e:Episode {id: 'e1'}) RETURN count(e) AS n"],
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(count.stdout.splitlines()[0]), {"n": 0}, count.stderr)
        self.assert_check_passes()

    def test_episode_id_reused_for_different_content_is_rejected(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f1", "Original.")]))
        stderr = self.rejected(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f2", "Sneaked in.")]))
        self.assertIn("episode id already used for different content", stderr)
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Original."])
        self.assertEqual(len(self.rows("history", SLOT)), 1)

    def test_missing_arguments_are_usage_errors(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f1", "A fact.")]))
        for args in (("about",), ("about", ""), ("history",), ("history", ""), ("recall",), ("recall", "")):
            with self.subTest(args):
                p = self.run_memory(*args)
                self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
                self.assertIn("usage:", p.stderr)

    def test_locked_store_is_retried(self):
        self.assertEqual(self.run_memory("init").returncode, 0)
        holder = subprocess.Popen(["relate", "query", "--database", self.db, "--mode", "jsonl"],
                                  stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, text=True)
        try:
            holder.stdin.write("CREATE (:Holder);\n")
            holder.stdin.flush()
            time.sleep(1)
            writer = subprocess.Popen(["bash", MEMORY, "remember", "-"], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      env=self.env, text=True)
            writer.stdin.write(json.dumps(episode("e1", "2026-11-27T10:00:00Z", "pi",
                                                  [fact("f1", "Waited for the lock.")])))
            writer.stdin.close()
            writer.stdin = None
            time.sleep(2)
            self.assertIsNone(writer.poll(), "the writer should still be retrying")
        finally:
            holder.stdin.close()
            holder.stdin = None
            holder.wait(timeout=30)
        _, err = writer.communicate(timeout=60)
        self.assertEqual(writer.returncode, 0, err)
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Waited for the lock."])

    def test_concurrent_writers_all_land(self):
        self.assertEqual(self.run_memory("init").returncode, 0)
        procs = []
        for i in range(4):
            payload = episode(f"e{i}", f"2026-11-27T1{i}:00:00Z", f"agent-{i}",
                              [fact(f"f{i}", f"Fact number {i}.", slot=f"test/slot-{i}")])
            proc = subprocess.Popen(["bash", MEMORY, "remember", "-"], stdin=subprocess.PIPE,
                                    env=self.env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            proc.stdin.write(json.dumps(payload))
            proc.stdin.close()
            proc.stdin = None
            procs.append(proc)
        for proc in procs:
            _, err = proc.communicate(timeout=60)
            self.assertEqual(proc.returncode, 0, err)
        self.assertEqual(len(self.rows("slots")), 4)

    def test_worktrees_share_one_store(self):
        env = git_env()
        repo = os.path.join(self.tmp.name, "repo")
        subprocess.run(["git", "init", "-q", repo], env=env, check=True)
        shutil.copytree(HERE + "/memory", os.path.join(repo, "scripts", "memory"))
        shutil.copy(MEMORY, os.path.join(repo, "scripts", "memory.sh"))
        git = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(git + ["add", "."], env=env, check=True)
        subprocess.run(git + ["commit", "-q", "-m", "init"], env=env, check=True)
        tree = os.path.join(self.tmp.name, "tree")
        subprocess.run(git + ["worktree", "add", "-q", tree], env=env, check=True)

        main_script = os.path.join(repo, "scripts", "memory.sh")
        tree_script = os.path.join(tree, "scripts", "memory.sh")
        paths = {self.run_memory("path", script=s, env=env).stdout.strip() for s in (main_script, tree_script)}
        self.assertEqual(paths, {os.path.join(os.path.realpath(repo), ".relate-memory")})

        payload = json.dumps(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f1", "Shared.")]))
        p = self.run_memory("remember", "-", stdin=payload, script=tree_script, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        p = self.run_memory("brief", script=main_script, env=env)
        self.assertIn("Shared.", p.stdout)

    def test_dropbox_conflicted_copies_stop_saves_and_check(self):
        self.remember(episode("e1", "2026-11-27T10:00:00Z", "pi", [fact("f1", "Before the conflict.")]))
        conflict = os.path.join(self.db, "manifest (Laptop's conflicted copy 2026-11-28).json")
        with open(conflict, "w") as fh:
            fh.write("{}")
        p = self.run_memory("remember", "-", stdin=json.dumps(
            episode("e2", "2026-11-28T10:00:00Z", "pi", [fact("f2", "After the conflict.")])))
        self.assertEqual(p.returncode, 4, p.stderr)
        self.assertIn("conflicted copies", p.stderr)
        self.assertEqual(self.run_memory("check").returncode, 4)
        os.remove(conflict)
        self.assertEqual([r["memory"] for r in self.rows("brief")], ["Before the conflict."])
        self.assert_check_passes()

    def test_store_path_outside_git_fails(self):
        outside = os.path.join(self.tmp.name, "loose")
        shutil.copytree(HERE + "/memory", os.path.join(outside, "memory"))
        shutil.copy(MEMORY, os.path.join(outside, "memory.sh"))
        env = dict(git_env(), GIT_CEILING_DIRECTORIES=self.tmp.name)
        p = self.run_memory("path", script=os.path.join(outside, "memory.sh"), env=env)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_skill_example_runs_as_written(self):
        skill = os.path.join(HERE, "..", ".agents", "skills", "project-memory", "SKILL.md")
        with open(skill, encoding="utf-8") as fh:
            body = fh.read()
        example = body.split("<<'JSON'\n", 1)[1].split("\nJSON\n", 1)[0]
        p = self.run_memory("remember", "-", stdin=example)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("memory: saved episode", p.stdout)


if __name__ == "__main__":
    unittest.main()
