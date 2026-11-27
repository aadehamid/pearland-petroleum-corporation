#!/usr/bin/env python3
"""Tests for scripts/adr_graph.py, the graph of PPC's architecture decisions.

Most tests build a small fixture repository with every record form the
parser reads. The relate tests skip where relate is not installed, as on CI.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
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

    def graph(self):
        return adr_graph.build(self.root)


class Parsing(Fixture):
    def test_register_reads_wrapped_cells_and_markdown_rows(self):
        baseline = adr_graph.parse_register(REGISTER)
        self.assertEqual(sorted(baseline), ["ADR-001", "ADR-002", "ADR-033"])
        self.assertEqual(baseline["ADR-001"]["title"], "Canonical synthetic world precedes source materialization")
        self.assertEqual(baseline["ADR-002"]["title"], "One R2 bucket per project")

    def test_index_reads_links_notes_and_none(self):
        index = adr_graph.parse_index(INDEX + "| [ADR-0043](0043-d.md) | Fourth | Decided | 2026-11-27 | None |\n")
        self.assertEqual(index["ADR-0040"]["links"], [("EXTENDS", "PPC-001"), ("EXTENDS", "ADR-001")])
        self.assertEqual(index["ADR-0041"]["links"], [("AMENDS", "ADR-002"), ("CLARIFIES", "ADR-033")])
        self.assertEqual(index["ADR-0040"]["notes"], [("AMENDS", "ADR-0042")])
        self.assertEqual(index["ADR-0040"]["status"], "Decided")
        self.assertEqual(index["ADR-0043"]["links"], [])

    def test_ids_have_one_spelling(self):
        self.assertEqual([adr_graph.norm(x) for x in ("ADR-7", "ADR-007", "ADR-0007", "ADR-40", "ADR-0040", "PPC-001")],
                         ["ADR-007", "ADR-007", "ADR-007", "ADR-0040", "ADR-0040", "PPC-001"])

    def test_frontmatter_amends_none_and_lists(self):
        self.assertEqual(adr_graph.parse_frontmatter("---\namends: none\n---\n")["amends"], [])
        self.assertEqual(adr_graph.parse_frontmatter("---\namends: ADR-003, ADR-0053\n---\n")["amends"],
                         ["ADR-003", "ADR-0053"])

    def test_graph_holds_every_decision_document_and_link(self):
        g = self.graph()
        self.assertEqual(sorted(n["id"] for n in g["nodes"]),
                         ["ADR-001", "ADR-002", "ADR-0040", "ADR-0041", "ADR-0042", "ADR-033"])
        self.assertEqual(g["documents"], ["PPC-001"])
        self.assertEqual(len(g["edges"]), 5)
        self.assertEqual(next(n for n in g["nodes"] if n["id"] == "ADR-0042")["authority"], "Owner")


class Checking(Fixture):
    def test_consistent_records_pass(self):
        self.assertEqual(adr_graph.check(self.graph()), [])

    def test_each_disagreement_is_reported(self):
        cases = {
            "status says clarified by ADR-0042, but ADR-0042's index row says it amends ADR-0040":
                (adr_graph.INDEX, INDEX.replace("Decided (amended by ADR-0042)", "Decided (clarified by ADR-0042)")),
            "ADR-0042 amends it, but its status does not say so":
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
            "index points at docs/adr/0042-c.md, which does not exist": (None, None),
        }
        for message, (rel, text) in cases.items():
            with self.subTest(message):
                self.tearDown()
                self.setUp()
                if rel is None:
                    os.remove(os.path.join(self.root, "docs/adr/0042-c.md"))
                else:
                    write(self.root, rel, text)
                findings = adr_graph.check(self.graph())
                self.assertTrue(any(message in f for f in findings), findings)

    def test_check_command_exit_codes(self):
        script = os.path.join(HERE, "adr_graph.py")
        p = subprocess.run([sys.executable, script, "summary"], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        summary = json.loads(p.stdout)
        with open(os.path.join(os.path.dirname(HERE), adr_graph.INDEX), encoding="utf-8") as fh:
            rows = sum(1 for line in fh if line.startswith("| [ADR-"))
        self.assertEqual(summary["indexed_decisions"], rows, "every index row parses")
        self.assertEqual(summary["baseline_decisions"], 39)


@unittest.skipUnless(shutil.which("relate"), "relate is not installed")
class Queries(Fixture):
    def run_graph(self, statement, params=None):
        return [json.loads(r) for r in adr_graph.run_relate(self.graph(), statement, params or {})]

    def test_changed_follows_chains(self):
        rows = self.run_graph(
            "MATCH p = (d:Decision {id: $id})<-[:AMENDS|CLARIFIES|EXTENDS|STAGES*1..]-(x) "
            "RETURN x.id AS id, length(p) AS hops ORDER BY hops, id", {"id": "ADR-001"})
        self.assertEqual(rows, [{"id": "ADR-0040", "hops": 1}, {"id": "ADR-0042", "hops": 2}])

    def test_export_loads_into_relate(self):
        rows = self.run_graph("MATCH (d:Decision) RETURN count(d) AS n")
        self.assertEqual(rows, [{"n": 6}])
        rows = self.run_graph("MATCH ()-[r]->() RETURN count(r) AS n")
        self.assertEqual(rows, [{"n": 5}])

    def test_cli_changed_basis_and_read_only_query(self):
        script = os.path.join(HERE, "adr_graph.py")
        run = lambda *a: subprocess.run([sys.executable, script, *a], capture_output=True, text=True, timeout=60)
        p = run("changed", "ADR-017")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('"id":"ADR-0045"', p.stdout)
        p = run("basis", "adr-0055")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('"id":"ADR-0045"', p.stdout)
        self.assertEqual(run("changed", "ADR-9999").returncode, 2)
        self.assertEqual(run("query", "MATCH (d:Decision) DETACH DELETE d").returncode, 2)
        p = run("query", "MATCH (d:Decision {baseline: true}) RETURN count(d) AS n")
        self.assertEqual(json.loads(p.stdout.splitlines()[0]), {"n": 39})


if __name__ == "__main__":
    unittest.main()
