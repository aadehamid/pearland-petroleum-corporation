#!/usr/bin/env python3
"""Tests for scripts/adr_graph.py, the graph of PPC's architecture decisions.

Most tests build a small fixture repository with every record form the
parser reads, and run the command line against it through ADR_GRAPH_ROOT.
The relate tests skip where relate is not installed, as on CI.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "adr_graph.py")
sys.path.insert(0, HERE)
import adr_graph  # noqa: E402

REGISTER = """# PPC-REG-001 --- Architecture Decision Register

  --------------------------------------------------------------------------
  ADR                     Decision                Rationale / consequence
  ----------------------- ----------------------- --------------------------
  001                     Canonical synthetic     One coherent world
                          world precedes source
                          materialization

  002                     One R2 bucket per       Simple boundary
                          project
  --------------------------------------------------------------------------

## Additional decisions
| ADR | Decision | Rationale / consequence |
|---|---|---|
| ADR-033 | Consume a versioned EPM bundle | Keep authority aligned |
"""

INDEX = """# ADRs

| ADR | Title | Status | Date | Amends / clarifies |
|---|---|---|---|---|
| [ADR-0040](0040-a.md) | First new decision | Decided (amended by ADR-0042) | 2026-11-26 | Extends PPC-001, ADR-001 |
| [ADR-0041](0041-b.md) | Second decision | Decided | 2026-11-26 | Amends ADR-002; clarifies ADR-033 |
| [ADR-0042](0042-c.md) | Third decision | Decided (owner stand-in) | 2026-11-27 | Amends ADR-0040 |
"""

FILES = {
    "0040-a.md": "---\nstatus: Decided\ndate: 2026-11-26\n---\n\n# ADR-0040\n",
    "0041-b.md": "---\nstatus: Decided\ndate: 2026-11-26\namends: ADR-002\n---\n\n# ADR-0041\n",
    "0042-c.md": "---\nstatus: Decided\ndate: 2026-11-27\namends: ADR-0040\nauthority: Owner\n---\n\n# ADR-0042\n",
}


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        write(self.root, adr_graph.REGISTER, REGISTER)
        write(self.root, adr_graph.INDEX, INDEX)
        for name, text in FILES.items():
            write(self.root, "docs/adr/" + name, text)

    def tearDown(self):
        self.tmp.cleanup()

    def reset(self):
        self.tearDown()
        self.setUp()

    def graph(self):
        return adr_graph.build(self.root)

    def cli(self, *args):
        env = dict(os.environ, ADR_GRAPH_ROOT=self.root)
        return subprocess.run([sys.executable, SCRIPT, *args], env=env, capture_output=True, text=True, timeout=60)


class Parsing(Fixture):
    def test_register_reads_wrapped_cells_and_markdown_rows(self):
        baseline = adr_graph.parse_register(REGISTER)
        self.assertEqual(sorted(baseline), ["ADR-001", "ADR-002", "ADR-033"])
        self.assertEqual(baseline["ADR-001"]["title"], "Canonical synthetic world precedes source materialization")
        self.assertEqual(baseline["ADR-002"]["title"], "One R2 bucket per project")

    def test_index_links_notes_and_none(self):
        index, problems = adr_graph.parse_index(INDEX + "| [ADR-0043](0043-d.md) | Fourth | Decided | 2026-11-27 | None |\n")
        self.assertEqual(problems, [])
        self.assertEqual(index["ADR-0040"]["links"], [("EXTENDS", "PPC-001"), ("EXTENDS", "ADR-001")])
        self.assertEqual(index["ADR-0041"]["links"], [("AMENDS", "ADR-002"), ("CLARIFIES", "ADR-033")])
        self.assertEqual(index["ADR-0040"]["notes"], [("AMENDS", "ADR-0042")])
        self.assertEqual(index["ADR-0040"]["status"], "Decided")
        self.assertEqual(index["ADR-0043"]["links"], [])

    def test_link_cells_split_on_verbs_and_flag_what_they_cannot_read(self):
        cases = {
            "Amends ADR-002, clarifies ADR-033": ([("AMENDS", "ADR-002"), ("CLARIFIES", "ADR-033")], []),
            "Amends ADR-002 and ADR-003": ([("AMENDS", "ADR-002"), ("AMENDS", "ADR-003")], []),
            "amends ADR-7": ([("AMENDS", "ADR-007")], []),
            "Extends PPC-REG-001": ([("EXTENDS", "PPC-REG-001")], []),
            "Amends": ([], ["Amends"]),
            "Amends WP-0": ([], ["Amends WP-0"]),
            "Amends ADR-002, ADR-9 typo": ([], ["Amends ADR-002, ADR-9 typo"]),
            "Replaces ADR-002": ([], ["Replaces ADR-002"]),
        }
        for cell, expected in cases.items():
            with self.subTest(cell):
                self.assertEqual(adr_graph.parse_links(cell), expected)

    def test_status_notes_ignore_case_and_stop_at_the_next_verb(self):
        index, _ = adr_graph.parse_index(
            "| [ADR-0048](x.md) | T | Decided (Staged by ADR-0055, ADR-0056 and clarified by ADR-0057) | 2026-11-26 | None |")
        self.assertEqual(index["ADR-0048"]["notes"],
                         [("STAGES", "ADR-0055"), ("STAGES", "ADR-0056"), ("CLARIFIES", "ADR-0057")])

    def test_bad_and_duplicate_rows_are_problems(self):
        _, problems = adr_graph.parse_index(INDEX + "| [ADR-0043](0043-d.md) | Fourth | Decided | 26-11-2026 | None |\n"
                                            "| [ADR-0042](0042-c.md) | Again | Decided | 2026-11-27 | None |\n")
        self.assertTrue(any("index row not understood" in p for p in problems), problems)
        self.assertTrue(any("more than one row" in p for p in problems), problems)

    def test_ids_have_one_spelling(self):
        self.assertEqual([adr_graph.norm(x) for x in ("ADR-7", "ADR-007", "ADR-0007", "ADR-40", "ADR-0040", "PPC-001")],
                         ["ADR-007", "ADR-007", "ADR-007", "ADR-0040", "ADR-0040", "PPC-001"])

    def test_frontmatter_forms(self):
        parse = adr_graph.parse_frontmatter
        self.assertEqual(parse("---\namends: none\n---\n")["amends"], [])
        self.assertEqual(parse("---\namends: ADR-003, ADR-0053\n---\n")["amends"], ["ADR-003", "ADR-0053"])
        self.assertEqual(parse("---\r\namends: ADR-003\r\n---\r\n")["amends"], ["ADR-003"])
        self.assertEqual(parse("---\namends:\n  - ADR-004\n  - ADR-010\n---\n")["amends"], ["ADR-004", "ADR-010"])
        self.assertEqual(parse("---\nstatus: \"Decided\"\n---\n")["status"], "Decided")
        self.assertIsNone(parse("# No frontmatter\n"))

    def test_graph_holds_every_decision_document_and_link(self):
        g = self.graph()
        self.assertEqual(sorted(n["id"] for n in g["nodes"]),
                         ["ADR-001", "ADR-002", "ADR-0040", "ADR-0041", "ADR-0042", "ADR-033"])
        self.assertEqual(g["documents"], ["PPC-001"])
        self.assertEqual(len(g["edges"]), 5)
        self.assertEqual(next(n for n in g["nodes"] if n["id"] == "ADR-0042")["authority"], "Owner")

    def test_links_to_unknown_decisions_stay_out_of_the_graph(self):
        write(self.root, adr_graph.INDEX, INDEX.replace("Amends ADR-0040 |", "Amends ADR-0040, ADR-0099 |"))
        g = self.graph()
        self.assertEqual(len(g["edges"]), 5)
        self.assertIn("ADR-0042: links to ADR-0099, which no record defines", adr_graph.check(g))
        self.assertNotIn("ADR-0099", adr_graph.cypher_seed(g))


class Checking(Fixture):
    def test_consistent_records_pass(self):
        self.assertEqual(adr_graph.check(self.graph()), [])

    def test_each_disagreement_is_reported(self):
        cases = {
            "status says clarified by ADR-0042, but ADR-0042's index row says it amends ADR-0040":
                (adr_graph.INDEX, INDEX.replace("Decided (amended by ADR-0042)", "Decided (clarified by ADR-0042)")),
            "ADR-0040: ADR-0042 amends it, but its status does not say so":
                (adr_graph.INDEX, INDEX.replace("Decided (amended by ADR-0042)", "Decided")),
            "frontmatter amends ADR-033, but the index says it clarifies ADR-033":
                ("docs/adr/0041-b.md", FILES["0041-b.md"].replace("amends: ADR-002", "amends: ADR-002, ADR-033")),
            "index amends ADR-002, but the frontmatter does not list it":
                ("docs/adr/0041-b.md", FILES["0041-b.md"].replace("amends: ADR-002\n", "")),
            "links to ADR-009, which no record defines":
                (adr_graph.INDEX, INDEX.replace("Amends ADR-002;", "Amends ADR-002, ADR-009;")),
            "index link not understood: 'Replaces ADR-002'":
                (adr_graph.INDEX, INDEX.replace("Amends ADR-002; clarifies ADR-033", "Replaces ADR-002")),
            "frontmatter date 2026-11-25, index date 2026-11-26":
                ("docs/adr/0040-a.md", FILES["0040-a.md"].replace("2026-11-26", "2026-11-25")),
            "frontmatter status 'Proposed', index status 'Decided'":
                ("docs/adr/0040-a.md", FILES["0040-a.md"].replace("status: Decided", "status: Proposed")),
            "docs/adr/0040-a.md has no frontmatter": ("docs/adr/0040-a.md", "# ADR-0040\n"),
            "index points at docs/adr/0042-c.md, which does not exist": (None, None),
        }
        for message, (rel, text) in cases.items():
            with self.subTest(message):
                self.reset()
                if rel is None:
                    os.remove(os.path.join(self.root, "docs/adr/0042-c.md"))
                else:
                    write(self.root, rel, text)
                findings = adr_graph.check(self.graph())
                self.assertTrue(any(message in f for f in findings), findings)
                if rel is None:
                    self.assertEqual([f for f in findings if f.startswith("ADR-0042: index amends")], [],
                                     "a missing file is not also a frontmatter mismatch")

    def test_a_second_link_to_the_same_target_needs_its_own_note(self):
        write(self.root, adr_graph.INDEX, INDEX.replace("Amends ADR-0040 |", "Amends ADR-0040; clarifies ADR-0040 |"))
        self.assertIn("ADR-0040: ADR-0042 clarifies it, but its status does not say so", adr_graph.check(self.graph()))

    def test_cli_summary_check_and_argument_errors(self):
        p = self.cli("summary")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout),
                         {"baseline_decisions": 3, "indexed_decisions": 3, "documents": 1,
                          "links": {"AMENDS": 2, "CLARIFIES": 1, "EXTENDS": 2}})
        p = self.cli("check")
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "adr_graph: the index links, status notes and frontmatter agree"))
        write(self.root, adr_graph.INDEX, INDEX.replace("Decided (amended by ADR-0042)", "Decided"))
        p = self.cli("check")
        self.assertEqual(p.returncode, 1)
        self.assertIn("1 finding(s)", p.stderr)
        for args in (("summary", "x"), ("check", "--strict"), ("export", "--run"), ("changed",),
                     ("changed", "ADR-9999"), ("query",), ("nonsense",)):
            with self.subTest(args):
                self.assertEqual(self.cli(*args).returncode, 2, args)

    def test_real_repository_parses_cleanly(self):
        index, problems = adr_graph.parse_index(adr_graph.read(adr_graph.ROOT, adr_graph.INDEX))
        self.assertEqual(problems, [])
        self.assertEqual([i for i, r in index.items() if r["unread"]], [])
        self.assertEqual(len(adr_graph.parse_register(adr_graph.read(adr_graph.ROOT, adr_graph.REGISTER))), 39)


@unittest.skipUnless(shutil.which("relate"), "relate is not installed")
class Queries(Fixture):
    def test_changed_and_basis_follow_chains(self):
        p = self.cli("changed", "ADR-001")
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = [json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual([(r["id"], r["hops"]) for r in rows], [("ADR-0040", 1), ("ADR-0042", 2)])
        p = self.cli("basis", "adr-42")
        rows = [json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual([r["id"] for r in rows], ["ADR-0040", "ADR-001", "PPC-001"])

    def test_query_is_read_only_but_any_word_is_allowed(self):
        p = self.cli("query", "MATCH (d:Decision) WHERE toLower(d.title) CONTAINS 'set' RETURN count(d) AS set")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout.splitlines()[0]), {"set": 0})
        p = self.cli("query", "MATCH (d:Decision) DETACH DELETE d")
        self.assertNotEqual(p.returncode, 0)
        p = self.cli("query", "MATCH (d:Decision) RETURN count(d) AS n // trailing comment")
        self.assertEqual(json.loads(p.stdout.splitlines()[0]), {"n": 6})

    def test_export_loads_into_relate(self):
        rows = [json.loads(r) for r in adr_graph.run_relate(self.graph(), "MATCH ()-[r]->() RETURN count(r) AS n", {})]
        self.assertEqual(rows, [{"n": 5}])


if __name__ == "__main__":
    unittest.main()
