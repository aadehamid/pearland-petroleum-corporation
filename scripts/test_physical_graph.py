#!/usr/bin/env python3
"""Tests for physical_graph.py. Installed from the consistency-graph skill.

Keeps the generic core tests and covers every PPC physical-model source form
and finding kind required by ADR-0060 (C1-C7, Q1-Q3).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "physical_graph.py")
sys.path.insert(0, HERE)
import physical_graph  # noqa: E402


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


MINIMAL_REVIEW_002 = """# PPC-REVIEW-002

### Locked flowsheet closure (`ADR-0054`, Option A)

1. **Internal bounded interfaces:** **Steam Methane Reformer (SMR)**, **Naphtha Hydrotreater (NHT)**, **Catalytic Reformer**, **FCC Naphtha Selective HDS**, **Diesel Hydrotreater (DHT)**, **Sulfur Recovery Unit (SRU)**, and **Steam and Power** are declared bounded mass, element, and utility interfaces inside Refinery A v1.

```mermaid
flowchart LR
    CDU["3. CDU + VDU"] --> FCC["4A. FCC Unit"]
    CDU --> HCU["4B. Hydrocracker"]
    CDU --> DHT["5A. DHT Interface"]
    CDU --> NHT["5D. NHT Interface"]
    FCC --> FDS["5B. FCC Selective HDS"]
    NHT --> REF["5C. Catalytic Reformer"]
    SMR["6. SMR"] --> HCU
    NHT --> BL["7. Product Blending"]
    BL --> FT["8. Finished Tankage"]
    CDU --> EX["9. Priced Boundary & SRU Sinks"]
```

### Complete Refinery A v1 stream-to-sink closure table (`PO-02`, `ADR-0054`)

| Source unit | Output stream | Declared v1 destination / sink |
|---|---|---|
| CDU + VDU | Light Straight-Run (LSR) Naphtha | NHT (`5D`) -> Blending (`BL`) or Export (`9`) |
| CDU + VDU | Vacuum Gas Oil (VGO) | Split between FCC (`4A`) and Hydrocracker (`4B`) |
| FCC (`4A`) | FCC Naphtha (Gasoline) | FCC Selective HDS (`5B`) -> Blending (`BL`) |
| Hydrocracker (`4B`) | ULSD | Blending & Tankage (`BL` -> `FT`) |
| NHT / DHT / FDS (`5A`/`5B`/`5D`) | Sour off-gas (`H2S`) | SRU (`9`) |

### Refinery A v1 nominal design basis, interface limits, tank register, and transfer paths

All figures below are `SYNTHETIC` design-basis specifications locked by ADR-0054 and ADR-0056:

- **Crude charge & assay slate:** Nominal crude charge `180,000 bbl/day` on a `30 / 50 / 20 vol%` design blend of three `>= 12`-point TBP assays.

| Hydrogen header term (`t/day`, `SYNTHETIC`) | `SCN-A-T125` (normal) | `SCN-A-H2CONT` (SMR turndown) |
|---|---:|---:|
| SMR H2 production | 107.00 | 57.00 |

- **Bounded interface rules (`G1-4`):**

| Interface | Inputs | Outputs and closure rule | Capacity & operating limits |
|---|---|---|---|
| SMR | Natural gas | H2 | 120.00 t/day |
| NHT | LSR & heavy naphtha | 99.7 wt% | 36,000 bbl/day |
| Catalytic Reformer | Heavy naphtha | Reformate | 30,000 bbl/day |
| FCC Selective HDS | FCC naphtha | 99.5 wt% | 18,000 bbl/day |
| DHT | Kerosene, AGO, LCO | ULSD | 60,000 bbl/day |
| SRU | H2S, NH3 | Elemental sulfur | 250 t/day |
| Steam and power | Fuel gas | Utilities | 2.5-4.5 GJ/t |
| Terminal ethanol | Denatured ethanol | 10.0 vol% | Per terminal (`TERM-01`..`03`) |

- **Refinery A v1 tank register & `EQ-03` hydraulic transfer paths (`B5`):**

| Tank ID | Service | Working min / max (`bbl`) | Notes & primary `EQ-03` transfer path |
|---|---|---|---|
| `TK-101` | Paper arithmetic / active crude test tank | `1,000` / `12,000` | Preserved for T125 |
| `TK-101H` | Segregated crude receipt hold tank | `0` / `150,000` | Hold tank |
| `TK-102`, `TK-103`, `TK-104` | Active crude blend charge tanks (3x) | `30,000` / `300,000` each | Path `LINE-CRUDE-CHG` (pump `P-101`) -> CDU charge |
| `TK-201` | VGO intermediate feed tank | `15,000` / `150,000` | Path `LINE-VGO-HCU` (`P-201`) -> Hydrocracker |
| `TK-202` | Catalytic Reformer intermediate feed tank | `15,000` / `150,000` | Feed tank |
| `TK-301`, `TK-302` | Finished ULSD blend & release tanks (2x) | `20,000` / `200,000` each | Path `LINE-ULSD-DISP` (`P-301`) -> dispatch (`TERM-01`..`03`) |
| `TK-303`, `TK-304` | Finished RBOB/CBOB blend & release tanks (2x) | `20,000` / `200,000` each | Path `LINE-BOB-DISP` (`P-302`) -> terminal (`TERM-01`..`03`) |
| `TK-401` | Finished Jet A-1 export tank | `10,000` / `120,000` | Path `LINE-JET-EXP` (`P-401`) -> export |
| `TK-402` | Heavy Resid / Slurry export tank | `10,000` / `120,000` | Path `LINE-RESID-EXP` (`P-402`) -> export |

*Holdup and hydraulic parameters (`N4`):* Pipe diameters, lengths, fitting K-factors, and pump curve coefficients for `LINE-CRUDE-CHG`, `LINE-VGO-HCU`, `LINE-ULSD-DISP`, `LINE-BOB-DISP`, `LINE-JET-EXP`, and `LINE-RESID-EXP` are populated in `fixtures/golden/refinery_a_design_basis.yaml` during `WP-1`.
"""

MINIMAL_WORLD_001 = """# PPC-WORLD-001

The existing World v0.1 charter covers one fictional PADD 3 Gulf Coast refinery with simplified CDU, FCC and hydrocracker units, three terminals, pipeline/truck/marine logistics, gasoline and ULSD, twelve customers, and twelve months of daily history.

| Rule | Operational consequence and expected check |
|---|---|
| Preserve model and data lineage | Record source and category (OBSERVED, DERIVED, ESTIMATED, SYNTHETIC or SCENARIO_ASSUMPTION). |
"""

MINIMAL_PPC_017 = """# PPC-017

EPM defines downstream design and meaning. PPC instantiates, executes, measures, and tests that design without becoming a competing semantic authority.
"""

MINIMAL_REG_002_CLEAN = """# PPC-REG-002 --- Data Source and Integration Register

  ----------------------------------------------------------------------------------------------------------------------
  Source       Authority     Main objects                        Integration           Latency     Durable replay
  ------------ ------------- ----------------------------------- --------------------- ----------- ---------------------
  PostgreSQL   commercial    contracts/trades/positions/hedges   Outbox→NATS           A           NATS + R2 raw

  MySQL        logistics     nominations/shipments/deliveries    Outbox→NATS           A           NATS + R2 raw

  SQLite       refinery edge unit status/production/events       micro-batch→R2        B           R2

  PostgreSQL   workflow      alerts/recommendations/approvals    API/event             A           PG WAL + R2

  Delta Lake   analytical    Silver/Gold/KPI                     Dagster/delta-rs      B/C/D       R2 Delta snapshots
  ----------------------------------------------------------------------------------------------------------------------
"""

MINIMAL_REG_002_LEGACY = """# PPC-REG-002 --- Data Source and Integration Register

  ----------------------------------------------------------------------------------------------------------------------
  Source       Authority     Main objects                        Integration           Latency     Durable replay
  ------------ ------------- ----------------------------------- --------------------- ----------- ---------------------
  PostgreSQL   commercial    contracts/trades/positions/hedges   Debezium→Kafka        A           Kafka + R2 CDC

  MySQL        logistics     nominations/shipments/deliveries    Debezium→Kafka        A           Kafka + R2 CDC

  D1           workflow      alerts/recommendations/approvals    API/event             A           extracts as needed

  DuckLake     analytical    Silver/Gold/KPI                     Dagster/DuckDB        B/C/D       R2-backed
  ----------------------------------------------------------------------------------------------------------------------
"""

MINIMAL_REG_003 = """# PPC-REG-003 --- KPI, Metric, and Data Product Register

## Data products

  ----------------------------------------------------------------------------
  Product                 Type                         Main purpose
  ----------------------- ---------------------------- -----------------------
  Event                   Foundational/cross-cutting   normalized events

  Commercial Margin       Derived                      realized margin
  ----------------------------------------------------------------------------

## Initial KPI candidates

  -----------------------------------------------------------------------
  KPI                     Area                    Typical drivers
  ----------------------- ----------------------- -----------------------
  ULSD Netback CPG        Commercial              diesel market

  Refinery Utilization    Refining                throughput/capacity
  -----------------------------------------------------------------------
"""

MINIMAL_EPM_ADAPTER = json.dumps({
    "schema_version": "1.0.0",
    "adapter_id": "ppc-adapter-epm",
    "adapter_version": "0.1.0",
    "upstream_short_name": "EPM",
    "pinned_commit": "511a9e8db4008ef43a0dda0f92cef17664e4c995",
    "maturity_status": "PROVISIONAL_COMMIT_PIN",
    "approved_upstream_release": None,
    "qualification_cap": "QUALIFIED_PROVISIONAL",
    "consumed_artifacts": [
        {
            "name": "KPI Ontology Class Hierarchy",
            "upstream_path": "ontology/kpi_ontology_class_hierarchy.md",
            "contract_role": "Tall KPI fact semantic model",
            "status": "CONSUMED_PROVISIONAL",
        },
        {
            "name": "Generalized DS_Business_Process Ontology",
            "upstream_path": "ontology/PROPOSED-release-packaging.md",
            "contract_role": "Pending generalized downstream process IRIs",
            "status": "PENDING_UPSTREAM_RELEASE",
        },
    ],
    "provenance_class": "OBSERVED",
}, indent=2)

MINIMAL_CORE_TTL = """@prefix ppc: <https://ppc.local/ontology/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ppc:RefineryA a ppc:Site ;
    rdfs:label "Refinery A"@en ;
    ppc:siteId "SITE-REF-A" ;
    ppc:provenanceClass "SYNTHETIC" .
"""

MINIMAL_PREFIX_MAP = """schema_version: "1.0.0"
provenance_class: "OBSERVED"
buckets:
  operational:
    bucket_name: "pearland-petroleum-corp"
    prefixes:
      delta_tables: "delta/{silver,gold,kpi_store}/"
      probe: "_probe/"
  hidden_truth:
    bucket_name: "pearland-petroleum-hidden"
    permitted_writers:
      - "generators/"
      - "verification/"
    permitted_probe_scripts:
      - "lakehouse/delta/wp0_probes.py"
    forbidden_consumers:
      - "integration_pipelines"
      - "operational_retrieval_agents"
    prefixes:
      canonical_world_snapshots: "evaluation/hidden/world_version=.../"
      probe: "evaluation/hidden/_probe/"
"""

MINIMAL_POLICY = """policy_version: "1.0.0"
provenance_class: "SYNTHETIC"
"""

MINIMAL_RUNTIME_FREEZE = """schema_version: "1.0.0"
provenance_class: "SYNTHETIC"
"""

MINIMAL_COMPOSE = """services:
  postgres:
    image: postgres:16
  nats:
    image: nats:2.10
"""

MINIMAL_WP0_PROBE = '''"""WP-0 isolation probe referencing only declared probe prefix."""
def run_r2_isolation_probe(std_env, hid_env):
    canary_key = "evaluation/hidden/_probe/wp0_iso_test.txt"
    return canary_key
'''

BUILT_DESIGN_BASIS = """schema_version: "1.0.0"
provenance_class: "SYNTHETIC"
facility_id: "SITE-REF-A"
crude_assays:
  - {id: "ASSAY-LIGHT-SWEET", provenance_class: "SYNTHETIC"}
  - {id: "ASSAY-MEDIUM-SOUR", provenance_class: "SYNTHETIC"}
  - {id: "ASSAY-HEAVY-SOUR", provenance_class: "SYNTHETIC"}
terminals:
  - {id: "TERM-01", provenance_class: "SYNTHETIC"}
  - {id: "TERM-02", provenance_class: "SYNTHETIC"}
  - {id: "TERM-03", provenance_class: "SYNTHETIC"}
customers:
  - {id: "CUST-01", provenance_class: "SYNTHETIC"}
  - {id: "CUST-02", provenance_class: "SYNTHETIC"}
  - {id: "CUST-03", provenance_class: "SYNTHETIC"}
  - {id: "CUST-04", provenance_class: "SYNTHETIC"}
  - {id: "CUST-05", provenance_class: "SYNTHETIC"}
  - {id: "CUST-06", provenance_class: "SYNTHETIC"}
  - {id: "CUST-07", provenance_class: "SYNTHETIC"}
  - {id: "CUST-08", provenance_class: "SYNTHETIC"}
  - {id: "CUST-09", provenance_class: "SYNTHETIC"}
  - {id: "CUST-10", provenance_class: "SYNTHETIC"}
  - {id: "CUST-11", provenance_class: "SYNTHETIC"}
  - {id: "CUST-12", provenance_class: "SYNTHETIC"}
units:
  - {id: "CDU", facility: "SITE-REF-A", provenance_class: "SYNTHETIC"}
  - {id: "4A", facility: "SITE-REF-A", provenance_class: "SYNTHETIC"}
  - {id: "4B", facility: "SITE-REF-A", aliases: ["Hydrocracker", "HCU"], provenance_class: "SYNTHETIC"}
  - {id: "5B", facility: "SITE-REF-A", aliases: ["FCC Selective HDS", "FDS"], provenance_class: "SYNTHETIC"}
  - {id: "9", facility: "SITE-REF-A", provenance_class: "SYNTHETIC"}
  - {id: "FT", facility: "SITE-REF-A", provenance_class: "SYNTHETIC"}
tanks:
  - {id: "TK-101", provenance_class: "SYNTHETIC"}
  - {id: "TK-101H", provenance_class: "SYNTHETIC"}
  - {id: "TK-102", provenance_class: "SYNTHETIC"}
  - {id: "TK-103", provenance_class: "SYNTHETIC"}
  - {id: "TK-104", provenance_class: "SYNTHETIC"}
  - {id: "TK-201", provenance_class: "SYNTHETIC"}
  - {id: "TK-202", provenance_class: "SYNTHETIC"}
  - {id: "TK-301", provenance_class: "SYNTHETIC"}
  - {id: "TK-302", provenance_class: "SYNTHETIC"}
  - {id: "TK-303", provenance_class: "SYNTHETIC"}
  - {id: "TK-304", provenance_class: "SYNTHETIC"}
  - {id: "TK-401", provenance_class: "SYNTHETIC"}
  - {id: "TK-402", provenance_class: "SYNTHETIC"}
transfer_lines:
  - {id: "LINE-CRUDE-CHG", source: "TK-102", destination: "CDU", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "LINE-VGO-HCU", source: "TK-201", destination: "4B", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "LINE-ULSD-DISP", source: "TK-301", destination: "TERM-01", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "LINE-BOB-DISP", source: "TK-303", destination: "TERM-01", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "LINE-JET-EXP", source: "TK-401", destination: "FT", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "LINE-RESID-EXP", source: "TK-402", destination: "FT", phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
streams:
  - {id: "STR-VGO-HCU", source: "CDU", destination: "4B", source_phase: "liquid", destination_phase: "liquid", mass_unit: "t/day", volume_unit: "bbl_60F/day", provenance_class: "SYNTHETIC"}
  - {id: "STR-ACID-GAS", source: "4B", destination: "9", source_phase: "gas", destination_phase: "gas", mass_unit: "t/day", volume_unit: null, provenance_class: "SYNTHETIC"}
"""


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        write(self.root, physical_graph.PPC_REVIEW_002, MINIMAL_REVIEW_002)
        write(self.root, physical_graph.PPC_WORLD_001, MINIMAL_WORLD_001)
        write(self.root, physical_graph.PPC_017, MINIMAL_PPC_017)
        write(self.root, physical_graph.PPC_REG_002, MINIMAL_REG_002_CLEAN)
        write(self.root, physical_graph.PPC_REG_003, MINIMAL_REG_003)
        write(self.root, physical_graph.EPM_ADAPTER, MINIMAL_EPM_ADAPTER)
        write(self.root, physical_graph.PPC_CORE_TTL, MINIMAL_CORE_TTL)
        write(self.root, physical_graph.R2_PREFIX_MAP, MINIMAL_PREFIX_MAP)
        write(self.root, physical_graph.POLICY_THRESHOLDS, MINIMAL_POLICY)
        write(self.root, physical_graph.RUNTIME_FREEZE, MINIMAL_RUNTIME_FREEZE)
        write(self.root, physical_graph.DOCKER_COMPOSE, MINIMAL_COMPOSE)
        write(self.root, "lakehouse/delta/wp0_probes.py", MINIMAL_WP0_PROBE)

    def tearDown(self):
        self.tmp.cleanup()

    def findings(self):
        return physical_graph.check(physical_graph.build(self.root))

    def cli(self, *args):
        env = dict(os.environ, PHYSICAL_GRAPH_ROOT=self.root)
        return subprocess.run([sys.executable, SCRIPT, *args], env=env, capture_output=True, text=True, timeout=60)


class Generic(Fixture):
    def test_markdown_tables_read_rows_by_header(self):
        tables = physical_graph.markdown_tables("| A | B |\n|:-|-:|\n| 1 | 2 |\n")
        self.assertEqual([h for h, _ in tables], [["A", "B"]])
        self.assertEqual(tables[0][1][0]["B"], "2")

    def test_an_empty_last_cell_with_no_space_is_kept(self):
        tables = physical_graph.markdown_tables("| A | B | C |\n|---|---|---|\n| 1 | 2 ||\n")
        row = tables[0][1][0]
        self.assertEqual((row["_cells"], row["C"]), (3, ""))

    def test_a_separator_needs_dashes(self):
        self.assertEqual(physical_graph.markdown_tables("| P | Q |\n| : | : |\n| r | s |\n"), [])

    def test_tables_in_fenced_code_are_skipped(self):
        text = "```\n| X | Y |\n|---|---|\n| in | code |\n```\n| A |\n|---|\n| 1 |\n"
        self.assertEqual([h for h, _ in physical_graph.markdown_tables(text)], [["A"]])

    def test_clashes_compare_type_as_well_as_value(self):
        g = physical_graph.Graph(self.root)
        g.node("Valve", "V-1", "a.md", size="3", open=True)
        g.node("Valve", "V-1", "b.json", size=3, open=1)
        self.assertEqual(len(g.clashes()), 2)

    def test_one_source_stating_a_value_twice_compares_type(self):
        g = physical_graph.Graph(self.root)
        g.node("Valve", "V-1", "a.json", open=True, n=1)
        g.node("Valve", "V-1", "a.json", open=1, n=1.0)
        self.assertEqual(len([p for p in g.problems if "states" in p and "twice" in p]), 2)

    def test_one_source_stating_a_list_twice_compares_element_types(self):
        g = physical_graph.Graph(self.root)
        g.node("Valve", "V-1", "a.json", nums=[1], flags=[True], same=[1, "a"])
        g.node("Valve", "V-1", "a.json", nums=[1.0], flags=[1], same=[1, "a"])
        self.assertEqual(sorted(p.split(" states ")[1].split(" ")[0] for p in g.problems), ["flags", "nums"])

    def test_list_properties_reach_the_cypher_and_other_shapes_are_refused(self):
        g = physical_graph.Graph(self.root)
        g.node("Pump", "P-1", "a.md", tags=["a", "b"], size=3, spec={"x": 1})
        self.assertIn('`tags`: ["a", "b"]', physical_graph.cypher_seed(g))
        self.assertEqual([p for p in g.problems if "gives spec a dict" in p], [
            "P-1: a.md gives spec a dict; use text, a number, true/false or a list of those"])

    def test_labels_and_link_types_must_be_plain_names(self):
        g = physical_graph.Graph(self.root)
        g.node("Work Request", "WR-1", "a.md")
        g.node("Pump", "P-1", "a.md")
        g.node("Pump", "P-2", "a.md")
        g.link("P-1", "clarified by", "P-2", "a.md")
        self.assertIn("WR-1: a.md gives the label 'Work Request'; use letters, digits and _", g.problems)
        self.assertIn("P-1: a.md gives the link type 'clarified by'; use letters, digits and _", g.problems)

    def test_missing_sources_are_reported_once_each(self):
        empty = tempfile.TemporaryDirectory()
        try:
            findings = physical_graph.check(physical_graph.build(empty.name))
        finally:
            empty.cleanup()
        missing = [f for f in findings if "source is missing" in f]
        self.assertGreaterEqual(len(missing), 5)
        self.assertEqual(len(missing), len(set(missing)))

    def test_reserved_property_names_are_refused(self):
        g = physical_graph.Graph(self.root)
        g.node("Pump", "P-1", "a.md", id="other", sources="x")
        self.assertEqual(len([p for p in g.problems if "reserved property" in p]), 2)

    def test_argument_errors_come_before_reading_sources(self):
        empty = tempfile.TemporaryDirectory()
        try:
            env = dict(os.environ, PHYSICAL_GRAPH_ROOT=empty.name)
            for args in (("nonsense",), ("summary", "x"), ("impact",)):
                with self.subTest(args):
                    p = subprocess.run([sys.executable, SCRIPT, *args], env=env, capture_output=True, text=True, timeout=60)
                    self.assertEqual(p.returncode, 2, p.stderr)
                    self.assertNotIn("Traceback", p.stderr)
        finally:
            empty.cleanup()

    def test_cli_arguments(self):
        self.assertEqual(self.cli("summary").returncode, 0)
        for args in (("summary", "x"), ("check", "--strict"), ("export", "x"), ("impact",),
                     ("impact", "nope"), ("query",), ("nonsense",), ("help", "x")):
            with self.subTest(args):
                self.assertEqual(self.cli(*args).returncode, 2, args)


class PhysicalModelChecks(Fixture):
    def test_clean_planned_fixture_reports_only_declared_c2_spelling_and_pending(self):
        # MINIMAL_REVIEW_002 intentionally has `FDS` + `FCC Selective HDS` on code 5B (1 C2 finding)
        # Replace FDS -> FCC Selective HDS to make a zero-finding baseline
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("NHT / DHT / FDS (`5A`/`5B`/`5D`)", "NHT / DHT / FCC Selective HDS (`5A`/`5B`/`5D`)"))
        self.assertEqual(self.findings(), [])
        p = self.cli("check")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("physical_graph: the sources agree", p.stdout)
        summary = json.loads(self.cli("summary").stdout)
        self.assertEqual(summary["nodes"]["Tank"], 13)
        self.assertEqual(summary["nodes"]["TransferLine"], 6)
        self.assertEqual(summary["modes"]["design_basis"], "planned")
        self.assertIn("ot/", summary["pending"])
        self.assertIn("api/", summary["pending"])
        self.assertIn("verification/", summary["pending"])

    def test_finding1_closure_table_does_not_mint_unknown_destinations(self):
        # Unknown endpoint code `99` in closure table MUST fail Check 2 (never minted)
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("SRU (`9`)", "Ghost Unit (`99`)"))
        findings = self.findings()
        self.assertTrue(any("99 is not defined by any source" in f for f in findings), findings)

        # Multi-destination row `Split between FCC (4A) and Hydrocracker (4B)` creates TWO clean links, not prose unit
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("NHT / DHT / FDS (`5A`/`5B`/`5D`)", "NHT / DHT / FCC Selective HDS (`5A`/`5B`/`5D`)"))
        g = physical_graph.build(self.root)
        self.assertIn(("CDU :: Vacuum Gas Oil (VGO)", "TO_ENDPOINT", "4A"), g.edges)
        self.assertIn(("CDU :: Vacuum Gas Oil (VGO)", "TO_ENDPOINT", "4B"), g.edges)
        self.assertIn(("4B :: ULSD", "TO_ENDPOINT", "BL"), g.edges)
        self.assertIn(("4B :: ULSD", "TO_ENDPOINT", "FT"), g.edges)

    def test_finding2_c2_reports_name_stated_two_ways_for_units_and_pump_pairs(self):
        # Default MINIMAL_REVIEW_002 has FDS vs FCC Selective HDS on 5B
        findings = self.findings()
        self.assertTrue(any("5B" in f and "name stated two ways" in f for f in findings), findings)

        # Adding HCU alongside Hydrocracker on 4B reports 4B stated two ways
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("-> Hydrocracker", "-> HCU"))
        findings2 = self.findings()
        self.assertTrue(any("4B" in f and "HCU" in f and "Hydrocracker" in f for f in findings2), findings2)

        # Grouping pumps as P-101A/B without alias table reports C2 finding
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("`P-101`", "`P-101A/B`"))
        findings3 = self.findings()
        self.assertTrue(any("P-101A/B" in f and "name stated two ways" in f for f in findings3), findings3)

    def test_c3_interface_count_7_plus_1_and_terminal_ethanol_not_in_refinery(self):
        g = physical_graph.build(self.root)
        self.assertNotIn(("Terminal ethanol", "LOCATED_AT", "SITE-REF-A"), g.edges)
        self.assertIn(("SMR", "LOCATED_AT", "SITE-REF-A"), g.edges)
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("| SRU | H2S, NH3 | Elemental sulfur | 250 t/day |\n", ""))
        self.assertTrue(any("internal bounded interface" in f.lower() for f in self.findings()))

    def test_c4_tank_multiplicity_and_line_count_checks(self):
        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace("`TK-102`, `TK-103`, `TK-104`", "`TK-102`, `TK-103`"))
        self.assertTrue(any("3x" in f or "TK-102" in f for f in self.findings()))

        write(self.root, physical_graph.PPC_REVIEW_002,
              MINIMAL_REVIEW_002.replace(", and `LINE-RESID-EXP`", ""))
        self.assertTrue(any("LINE-RESID-EXP" in f or "TransferLine" in f for f in self.findings()))

    def test_c5_permitted_writers_and_probe_exemption_must_come_from_source(self):
        # Removing permitted_writers or permitted_probe_scripts from r2_prefix_map.yaml MUST be reported
        no_writers = MINIMAL_PREFIX_MAP.replace(
            '    permitted_writers:\n      - "generators/"\n      - "verification/"\n', ""
        )
        write(self.root, physical_graph.R2_PREFIX_MAP, no_writers)
        self.assertTrue(any("permitted_writers" in f for f in self.findings()))

        no_probes = MINIMAL_PREFIX_MAP.replace(
            '    permitted_probe_scripts:\n      - "lakehouse/delta/wp0_probes.py"\n', ""
        )
        write(self.root, physical_graph.R2_PREFIX_MAP, no_probes)
        findings = self.findings()
        self.assertTrue(any("permitted_probe_scripts" in f for f in findings), findings)
        # Without source exemption, wp0_probes.py referencing evaluation/hidden/_probe/ is flagged too
        self.assertTrue(any("READS_OR_WRITES" in f for f in findings), findings)

        # Integration pipeline reading evaluation/hidden/world_version=... MUST fail
        write(self.root, physical_graph.R2_PREFIX_MAP, MINIMAL_PREFIX_MAP)
        write(self.root, "integration/dagster/bad_asset.py",
              'def load():\n    return "s3://pearland-petroleum-hidden/evaluation/hidden/world_version=v1/ckpt.json"\n')
        self.assertTrue(any("READS_OR_WRITES" in f for f in self.findings()))

    def test_c7_invalid_or_missing_provenance_class_fails(self):
        write(self.root, physical_graph.POLICY_THRESHOLDS, 'policy_version: "1.0.0"\nprovenance_class: "MADE_UP"\n')
        self.assertTrue(any("provenance_class" in f and "MADE_UP" in f for f in self.findings()))

        write(self.root, physical_graph.POLICY_THRESHOLDS, 'policy_version: "1.0.0"\n')
        self.assertTrue(any("provenance_class" in f and "policy_thresholds.yaml" in f for f in self.findings()))

    def test_q1_strict_epm_bindings_completeness_and_pending_state(self):
        clean_r2 = MINIMAL_REVIEW_002.replace("NHT / DHT / FDS (`5A`/`5B`/`5D`)", "NHT / DHT / FCC Selective HDS (`5A`/`5B`/`5D`)")
        write(self.root, physical_graph.PPC_REVIEW_002, clean_r2)

        # 1. PPC_EXTENSION is rejected (Q1)
        write(self.root, physical_graph.EPM_KPI_BINDINGS,
              'schema_version: "1.0.0"\nprovenance_class: "OBSERVED"\nbindings:\n  - kpi: "ULSD Netback CPG"\n    status: "PPC_EXTENSION"\n')
        self.assertTrue(any("PPC_EXTENSION" in f for f in self.findings()))

        # 2. Partial bindings file fails strict completeness for uncovered KPIs and DataProducts (Finding 3 fix)
        write(self.root, physical_graph.EPM_KPI_BINDINGS,
              'schema_version: "1.0.0"\nprovenance_class: "OBSERVED"\nbindings:\n'
              '  - kpi: "ULSD Netback CPG"\n    status: "CONSUMED_PROVISIONAL"\n    epm_artifact: "ontology/kpi_ontology_class_hierarchy.md"\n')
        findings = self.findings()
        self.assertTrue(any("Refinery Utilization" in f and "strict mode" in f for f in findings), findings)
        self.assertTrue(any("Commercial Margin" in f and "strict mode" in f for f in findings), findings)

        # 3. Complete bindings file using CONSUMED_PROVISIONAL and literal "pending" passes (Finding 5 fix)
        write(self.root, physical_graph.EPM_KPI_BINDINGS,
              'schema_version: "1.0.0"\nprovenance_class: "OBSERVED"\nbindings:\n'
              '  - kpi: "ULSD Netback CPG"\n    status: "CONSUMED_PROVISIONAL"\n    epm_artifact: "ontology/kpi_ontology_class_hierarchy.md"\n'
              '  - kpi: "Refinery Utilization"\n    status: "pending"\n'
              '  - data_product: "Event"\n    status: "PENDING_UPSTREAM_RELEASE"\n    epm_artifact: "ontology/PROPOSED-release-packaging.md"\n'
              '  - data_product: "Commercial Margin"\n    status: "pending"\n')
        self.assertEqual(self.findings(), [])

        # 4. Code defining a KPI without bindings file fails from run 1
        os.remove(os.path.join(self.root, physical_graph.EPM_KPI_BINDINGS))
        write(self.root, "lakehouse/delta/kpi_calc.py",
              'def compute_kpi(x, y):\n    return {"measure_class": "KPI", "val": x / y}\n')
        self.assertTrue(any("EPM binding" in f for f in self.findings()))

    def test_q2_reports_stale_ppc_reg_002_and_obsolete_scaffold_folders(self):
        write(self.root, physical_graph.PPC_REG_002, MINIMAL_REG_002_LEGACY)
        findings = self.findings()
        self.assertTrue(any("Debezium" in f or "Kafka" in f for f in findings), findings)
        self.assertTrue(any("D1" in f for f in findings), findings)
        self.assertTrue(any("DuckLake" in f for f in findings), findings)

        write(self.root, physical_graph.PPC_REG_002, MINIMAL_REG_002_CLEAN)
        write(self.root, "integration/kafka/.gitkeep", "")
        write(self.root, "lakehouse/ducklake/.gitkeep", "")
        findings2 = self.findings()
        self.assertTrue(any("integration/kafka" in f for f in findings2), findings2)
        self.assertTrue(any("lakehouse/ducklake" in f for f in findings2), findings2)

    def test_built_design_basis_checks_provenance_endpoints_units_phase_and_counts(self):
        write(self.root, physical_graph.DESIGN_BASIS, BUILT_DESIGN_BASIS)
        self.assertEqual(self.findings(), [])
        summary = json.loads(self.cli("summary").stdout)
        self.assertEqual(summary["modes"]["design_basis"], "built")

        # 1. Generator-invented tank not in PPC-REVIEW-002 fails Check 1
        bad_invented = BUILT_DESIGN_BASIS.replace(
            '  - {id: "TK-402", provenance_class: "SYNTHETIC"}',
            '  - {id: "TK-402", provenance_class: "SYNTHETIC"}\n  - {id: "TK-999", provenance_class: "SYNTHETIC"}',
        )
        write(self.root, physical_graph.DESIGN_BASIS, bad_invented)
        self.assertTrue(any("TK-999" in f for f in self.findings()))

        # 2. Stream with nonexistent destination fails Check 2
        write(self.root, physical_graph.DESIGN_BASIS, BUILT_DESIGN_BASIS.replace('destination: "9"', 'destination: "GHOST-UNIT"'))
        self.assertTrue(any("GHOST-UNIT" in f for f in self.findings()))

        # 3. Gas stream declaring liquid bbl volume fails Check 2
        write(self.root, physical_graph.DESIGN_BASIS, BUILT_DESIGN_BASIS.replace(
            'source_phase: "gas", destination_phase: "gas", mass_unit: "t/day", volume_unit: null',
            'source_phase: "gas", destination_phase: "gas", mass_unit: "t/day", volume_unit: "bbl_60F/day"',
        ))
        self.assertTrue(any("STR-ACID-GAS" in f and "gas" in f.lower() for f in self.findings()))

        # 4. Endpoint phase disagreement fails Check 2
        write(self.root, physical_graph.DESIGN_BASIS, BUILT_DESIGN_BASIS.replace(
            'source_phase: "liquid", destination_phase: "liquid"',
            'source_phase: "liquid", destination_phase: "gas"',
        ))
        self.assertTrue(any("STR-VGO-HCU" in f and "phase" in f.lower() for f in self.findings()))

        # 5. Customer count mismatch against PPC-WORLD-001 ("twelve customers") fails Check 3
        write(self.root, physical_graph.DESIGN_BASIS,
              BUILT_DESIGN_BASIS.replace('  - {id: "CUST-12", provenance_class: "SYNTHETIC"}\n', ''))
        self.assertTrue(any("Customer" in f and "12" in f for f in self.findings()))


@unittest.skipUnless(shutil.which("relate"), "relate is not installed")
class Queries(Fixture):
    def test_impact_and_read_only_query_work(self):
        p = self.cli("impact", "TK-102")
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = {r["id"]: r["hops"] for r in map(json.loads, p.stdout.splitlines())}
        self.assertEqual(rows["SITE-REF-A"], 1)
        self.assertEqual(rows["LINE-CRUDE-CHG"], 1)

        q = self.cli("query", "MATCH (t:Tank) RETURN count(t) AS n")
        self.assertEqual(q.returncode, 0, q.stderr)
        self.assertEqual(json.loads(q.stdout.splitlines()[0]), {"n": 13})
        self.assertNotEqual(self.cli("query", "MATCH (t:Tank) DETACH DELETE t").returncode, 0)


if __name__ == "__main__":
    unittest.main()
