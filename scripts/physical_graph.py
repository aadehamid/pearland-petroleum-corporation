#!/usr/bin/env python3
"""A consistency graph of PPC's physical, semantic, and pipeline sources, rebuilt on every run.

Usage:
  physical_graph.py summary          counts of nodes by label, links by type, modes, and pending items
  physical_graph.py check            where the sources disagree or cannot be read (exit 1 if so)
  physical_graph.py impact ID        everything linked to ID within three hops (needs relate)
  physical_graph.py query 'CYPHER'   any Cypher, run on a read-only copy of the graph (needs relate)
  physical_graph.py export           the graph as a Cypher script for relate or Neo4j

Installed from the consistency-graph skill and governed by ADR-0060 (under ADR-0059).
Keep the generic core below as it is; the PROJECT section holds PPC's sources, parsers,
and checks. PHYSICAL_GRAPH_ROOT points the tool at another checkout, which the tests use.
"""
import ast
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml


def repo_root(start):
    """The nearest folder above start that holds .git, wherever the tool sits in the repository."""
    path = start
    while not os.path.exists(os.path.join(path, ".git")):
        parent = os.path.dirname(path)
        if parent == path:
            return os.path.dirname(start)
        path = parent
    return path


ROOT = os.environ.get("PHYSICAL_GRAPH_ROOT") or repo_root(os.path.dirname(os.path.abspath(__file__)))
RESERVED = {"id", "sources"}
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")  # a label or link type; the seed backtick-quotes it, so reserved words are safe
SCALAR = (str, int, float, bool)


# ----------------------------------------------------------------------------
# Generic core: reading sources, recording what each one says, finding clashes.
# ----------------------------------------------------------------------------

def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def outside_fences(text):
    """The text with every line inside fenced code blanked, so line numbers stay true."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            out.append("")
        else:
            out.append("" if fenced else line)
    return "\n".join(out)


def same(a, b):
    """Equal in type and value, element by element in a list, so True and 1, or [1] and [1.0], differ."""
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def cells(line):
    """The cells of one table row: one outer pipe is removed from each end, never more."""
    line = line.strip()
    line = line[1:] if line.startswith("|") else line
    line = line[:-1] if line.endswith("|") else line
    return [c.strip() for c in line.split("|")]


SEPARATOR = re.compile(r"\|(\s*:?-+:?\s*\|)+")


def markdown_tables(text):
    """Every pipe table in a markdown text, outside fenced code, as (header, rows) with rows by header cell."""
    tables, lines = [], outside_fences(text).split("\n")
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].strip().startswith("|") \
                and SEPARATOR.fullmatch(lines[i + 1].strip()):
            header = cells(lines[i])
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                row = cells(lines[j])
                rows.append({"_line": j + 1, "_cells": len(row), **dict(zip(header, row))})
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


class Graph:
    """Nodes and links with the source that stated each, and the problems met while reading."""

    def __init__(self, root):
        self.root = root
        self.nodes = {}       # id -> {"label", "props", "sources": {source: {prop: value}}}
        self.edges = {}       # (source_id, type, target_id) -> set of sources that state it
        self.problems = []
        self.meta = {"modes": {}, "pending": [], "derived_counts": {}}

    def read(self, rel):
        """A source's text, outside fenced code; a missing source is a problem and reads as None."""
        try:
            return outside_fences(read(self.root, rel))
        except FileNotFoundError:
            message = f"{rel}: source is missing"
            if message not in self.problems:
                self.problems.append(message)
            return None

    def read_raw(self, rel):
        """Read a structured file verbatim; a missing source is a problem and reads as None."""
        try:
            return read(self.root, rel)
        except FileNotFoundError:
            message = f"{rel}: source is missing"
            if message not in self.problems:
                self.problems.append(message)
            return None

    def node(self, label, ident, source, **props):
        if not NAME.fullmatch(label):
            self.problems.append(f"{ident}: {source} gives the label {label!r}; use letters, digits and _")
            return ident
        n = self.nodes.setdefault(ident, {"label": label, "props": {}, "sources": {}, "labels": {}})
        n["labels"].setdefault(label, set()).add(source)
        stated = n["sources"].setdefault(source, {})
        for key, value in props.items():
            if key in RESERVED:
                self.problems.append(f"{ident}: {source} sets the reserved property {key!r}; rename it")
                continue
            if value is None or value == "":
                continue
            if not (isinstance(value, SCALAR) or (isinstance(value, list) and all(isinstance(v, SCALAR) for v in value))):
                self.problems.append(f"{ident}: {source} gives {key} a {type(value).__name__}; "
                                     "use text, a number, true/false or a list of those")
                continue
            if key in stated and not same(stated[key], value):
                self.problems.append(f"{ident}: {source} states {key} twice: {stated[key]!r} and {value!r}")
                continue
            stated[key] = value
            n["props"].setdefault(key, value)
        return ident

    def link(self, source_id, kind, target_id, source):
        if not NAME.fullmatch(kind):
            self.problems.append(f"{source_id}: {source} gives the link type {kind!r}; use letters, digits and _")
            return
        self.edges.setdefault((source_id, kind, target_id), set()).add(source)

    def problem(self, message):
        if message not in self.problems:
            self.problems.append(message)

    def clashes(self):
        """A property or label two sources state differently is a clash: report both, choose neither."""
        found = []
        for ident, n in sorted(self.nodes.items()):
            if len(n["labels"]) > 1:
                said = "; ".join(f"{', '.join(sorted(srcs))} {'calls' if len(srcs) == 1 else 'call'} it a {lab}"
                                 for lab, srcs in sorted(n["labels"].items()))
                found.append(f"{ident}: sources disagree on its label: {said}")
            values = {}
            for source, props in n["sources"].items():
                for key, value in props.items():
                    values.setdefault(key, {}).setdefault((type(value).__name__, repr(value)), []).append(source)
            for key, seen in sorted(values.items()):
                if len(seen) > 1:
                    said = "; ".join(f"{', '.join(sorted(s))} says {v}" for (_, v), s in sorted(seen.items()))
                    found.append(f"{ident}: sources disagree on {key}: {said}")
        return found


def check(graph):
    """Every finding: unreadable sources, clashes, broken or missing links, wrong counts, and project rules."""
    counts = EXPECTED_COUNTS(graph)
    findings = list(graph.problems) + graph.clashes()
    for (src, kind, dst), sources in sorted(graph.edges.items()):
        for end in (src, dst):
            if end not in graph.nodes:
                findings.append(f"{src} -{kind}-> {dst}: {end} is not defined by any source "
                                f"(stated in {', '.join(sorted(sources))})")
    for label, kind, direction, why in REQUIRED_LINKS:
        if direction not in ("out", "in"):
            findings.append(f"REQUIRED_LINKS: {label} {kind} has direction {direction!r}; use 'out' or 'in'")
            continue
        for ident, n in sorted(graph.nodes.items()):
            if n["label"] != label:
                continue
            ends = [e for e in graph.edges if e[1] == kind and (e[0] if direction == "out" else e[2]) == ident]
            if not ends:
                findings.append(f"{ident}: a {label} with no {kind} link ({why})")
    for label, expected, where in counts:
        actual = sum(1 for n in graph.nodes.values() if n["label"] == label)
        if actual != expected:
            findings.append(f"{label}: the sources define {actual}, but {where} says {expected}")
    findings.extend(PROJECT_CHECKS(graph))
    return findings


def cypher_seed(graph):
    """The graph as one Cypher script, one statement per line."""
    def lit(v):
        return "null" if v is None else json.dumps(v, ensure_ascii=False)
    out = []
    for label in sorted({n["label"] for n in graph.nodes.values()}):
        out.append(f"CREATE CONSTRAINT `{label.lower()}_id` IF NOT EXISTS FOR (n:`{label}`) REQUIRE n.id IS UNIQUE;")
    for ident, n in sorted(graph.nodes.items()):
        props = {"id": ident, **n["props"], "sources": sorted(n["sources"])}
        body = ", ".join(f"`{k}`: {lit(v)}" for k, v in props.items())
        out.append(f"CREATE (:`{n['label']}` {{{body}}});")
    for (src, kind, dst), sources in sorted(graph.edges.items()):
        if src in graph.nodes and dst in graph.nodes:
            out.append(f"MATCH (a {{id: {lit(src)}}}), (b {{id: {lit(dst)}}}) "
                       f"CREATE (a)-[:`{kind}` {{sources: {lit(sorted(sources))}}}]->(b);")
    return "\n".join(out) + "\n"


def run_relate(graph, statement, params):
    """Load the graph into a scratch store, then run the statement on it read-only."""
    if not shutil.which("relate"):
        sys.exit("physical_graph: relate is not installed. Install it with: curl -sSfL https://relatedb.ai/install.sh | bash")
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "graph")
        seed = subprocess.run(["relate", "query", "--database", db, "--mode", "jsonl"],
                              input=cypher_seed(graph), capture_output=True, text=True)
        if seed.returncode != 0:
            sys.stderr.write(seed.stdout + seed.stderr)
            sys.exit(seed.returncode)
        args = ["relate", "query", "--database", db, "--read-only", "--mode", "jsonl", "--max-rows", "0"]
        for key, value in params.items():
            args += ["--param", f"{key}={json.dumps(value)}"]
        p = subprocess.run(args + ["--command", statement], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        sys.stderr.write(p.stdout + p.stderr)
        sys.exit(p.returncode)
    return [line for line in p.stdout.splitlines() if line.startswith("{")]


def usage(text):
    print("usage: physical_graph.py " + text, file=sys.stderr)
    return 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd, args = (argv[0], argv[1:]) if argv else ("help", [])
    if cmd in ("help", "-h", "--help"):
        if args:
            return usage("help takes no arguments")
        print(__doc__.split("\n\nInstalled")[0].strip())
        return 0
    wanted = {"impact": 1, "query": 1, "summary": 0, "check": 0, "export": 0}
    if cmd not in wanted:
        return usage("summary|check|impact|query|export, or help")
    if len(args) != wanted[cmd]:
        return usage({"impact": "impact ID", "query": "query 'CYPHER'"}.get(cmd, f"{cmd} takes no arguments"))
    graph = build(ROOT)
    if cmd == "impact":
        if args[0] not in graph.nodes:
            print(f"physical_graph: no node {args[0]}", file=sys.stderr)
            return 2
        statement = ("MATCH p = (n {id: $id})-[*1..3]-(m) WHERE m <> n "
                     "RETURN m.id AS id, labels(m)[0] AS label, min(length(p)) AS hops ORDER BY hops, id")
        for row in run_relate(graph, statement, {"id": args[0]}):
            print(row)
        return 0
    if cmd == "query":
        for row in run_relate(graph, args[0], {}):
            print(row)
        return 0
    if cmd == "summary":
        labels, kinds = {}, {}
        for n in graph.nodes.values():
            labels[n["label"]] = labels.get(n["label"], 0) + 1
        for (_, kind, _) in graph.edges:
            kinds[kind] = kinds.get(kind, 0) + 1
        out = {
            "nodes": dict(sorted(labels.items())),
            "links": dict(sorted(kinds.items())),
            "modes": dict(sorted(graph.meta["modes"].items())),
            "pending": sorted(set(graph.meta["pending"])),
            "derived_counts": dict(sorted(graph.meta["derived_counts"].items())),
        }
        print(json.dumps(out))
        return 0
    if cmd == "check":
        findings = check(graph)
        mode_str = ", ".join(f"{k}={v}" for k, v in sorted(graph.meta["modes"].items()))
        pending = sorted(set(graph.meta["pending"]))
        for f in findings:
            print("physical_graph: " + f, file=sys.stderr)
        if findings:
            print(f"physical_graph: {len(findings)} finding(s) (mode: {mode_str}; pending: {len(pending)})",
                  file=sys.stderr)
        else:
            print(f"physical_graph: the sources agree (mode: {mode_str}; pending: {len(pending)})")
        return 1 if findings else 0
    sys.stdout.write(cypher_seed(graph))
    return 0


# ----------------------------------------------------------------------------
# PROJECT: Pearland Petroleum Corporation physical-model consistency graph.
# Governed by ADR-0060 (Claude Fable 5.2 stand-in ruling under ADR-0059).
# ----------------------------------------------------------------------------

PPC_REVIEW_002 = "docs/enterprise-architecture/independent-review/PPC-REVIEW-002_Governing_Refinery_Equations_and_Balances.md"
PPC_WORLD_001 = "docs/enterprise-architecture/01-enterprise-world/PPC-WORLD-001_Canonical_Enterprise_World.md"
PPC_017 = "docs/PPC-017_EPM_Dependency_Semantic_Authority_and_Process_Conformance_Contract.md"
PPC_REG_002 = "docs/PPC-REG-002_Data_Source_and_Integration_Register.md"
PPC_REG_003 = "docs/PPC-REG-003_KPI_Metric_and_Data_Product_Register.md"
EPM_ADAPTER = "semantic/adapters/epm.adapter.json"
PPC_CORE_TTL = "semantic/ontology/ppc_core.ttl"
R2_PREFIX_MAP = "infra/r2/r2_prefix_map.yaml"
POLICY_THRESHOLDS = "schemas/policy_thresholds.yaml"
RUNTIME_FREEZE = "schemas/runtime_freeze.yaml"
DOCKER_COMPOSE = "infra/docker-compose.yml"

# Planned WP-1+ sources (detected automatically when present; reported as pending until then)
DESIGN_BASIS = "fixtures/golden/refinery_a_design_basis.yaml"
CFG0_TOPOLOGY = "fixtures/golden/cfg0_dexpi_topology.json"
OT_TAGS = "fixtures/golden/refinery_a_ot_tags.yaml"
EPM_KPI_BINDINGS = "semantic/mappings/epm_kpi_bindings.yaml"

REQUIRED_LINKS = [
    ("Tank", "LOCATED_AT", "out", "every storage tank belongs to a facility"),
    ("TransferLine", "LOCATED_AT", "out", "every hydraulic transfer line belongs to a facility"),
    ("TransferLine", "CONNECTS_FROM", "out", "every transfer line connects from a declared tank or unit"),
    ("Pump", "DRIVES", "out", "every pump drives a declared transfer line"),
    ("Stream", "FROM_ENDPOINT", "out", "every stream must have a declared source endpoint"),
    ("Stream", "TO_ENDPOINT", "out", "every stream must have a declared destination endpoint"),
]

WORD_TO_INT = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

PIPELINE_SCAN_DIRS = ("integration", "source-systems", "ot", "lakehouse", "api", "apps")
PENDING_CHECK_DIRS = ("ot", "api", "apps", "verification")
OBSOLETE_SCAFFOLD_DIRS = (
    ("integration/debezium", "ADR-0046 replaces Debezium with transactional source outboxes"),
    ("integration/kafka", "ADR-0046 replaces Apache Kafka with NATS JetStream for Slice 1"),
    ("lakehouse/ducklake", "ADR-0045 replaces DuckLake with Delta Lake on Cloudflare R2"),
)
ALLOWED_EPM_ADAPTER_STATES = {"CONSUMED_PROVISIONAL", "PENDING_UPSTREAM_RELEASE"}
ALLOWED_EPM_BINDING_STATES = {"CONSUMED_PROVISIONAL", "PENDING_UPSTREAM_RELEASE", "pending"}
LEGAL_PHASES = {"liquid", "gas", "solid", "utility"}
LIQUID_VOLUME_UNITS = {"bbl", "bbl_60F", "bbl/day", "bbl_60F/day", "bbl/h", "m3", "m3/h"}

# Code regex matching KPI formula / registration definitions in runtime modules (Q1)
KPI_CODE_PATTERN = re.compile(
    r"\b(KPI_DEFINITIONS|KPIDefinition|define_kpi|compute_kpi)\b|"
    r"['\"]measure_class['\"]\s*:\s*['\"]KPI['\"]"
)
# Non-endpoint parenthesized references (rules, proof obligations, equations, ADRs, chemicals)
NON_ENDPOINT_TOKEN_RE = re.compile(
    r"^(?:G\d+-\d+|PO-\d+[a-z]?|ADR-\d+|EQ-\d+|T\d+|N\d+|B\d+|C\d+|H2S?|NH3|SO2|N2|CO2|CH4)$"
)


def _word_or_int(token):
    tok = token.strip().lower()
    if tok.isdigit():
        return int(tok)
    return WORD_TO_INT.get(tok)


def _parse_pandoc_simple_table(text, section_heading=None):
    """Parse Pandoc simple/multiline tables delimited by dashed horizontal rules."""
    lines = text.split("\n")
    start = 0
    if section_heading is not None:
        found = False
        for idx, line in enumerate(lines):
            if line.strip() == section_heading:
                start = idx + 1
                found = True
                break
        if not found:
            return []

    rule_re = re.compile(r"^\s*-{5,}(\s+-{3,})*\s*$")
    sublines = lines[start:]
    if section_heading is not None:
        end = len(sublines)
        for idx, line in enumerate(sublines):
            if line.startswith("## "):
                end = idx
                break
        sublines = sublines[:end]

    rule_idxs = [i for i, ln in enumerate(sublines) if rule_re.match(ln)]
    if len(rule_idxs) < 3:
        return []

    header_line = sublines[rule_idxs[0] + 1]
    col_rule = sublines[rule_idxs[1]]
    col_spans = [(m.start(), m.end()) for m in re.finditer(r"-+", col_rule)]
    headers = [header_line[s:e].strip() for s, e in col_spans]

    body_lines = sublines[rule_idxs[1] + 1:rule_idxs[2]]
    records = []
    cur = None
    for ln in body_lines:
        if not ln.strip():
            if cur is not None:
                records.append(cur)
                cur = None
            continue
        vals = [ln[s:e].strip() if idx < len(col_spans) - 1 else ln[s:].strip()
                for idx, (s, e) in enumerate(col_spans)]
        if cur is None:
            cur = dict(zip(headers, vals))
        else:
            for h, v in zip(headers, vals):
                if v:
                    cur[h] = (cur[h] + " " + v).strip() if cur[h] else v
    if cur is not None:
        records.append(cur)
    return records


def _parse_legal_classifications(graph, world_text):
    """Read the 5 allowed provenance classes from PPC-WORLD-001 (never typed silently)."""
    if world_text is None:
        return set()
    m = re.search(
        r"\((OBSERVED,\s*DERIVED,\s*ESTIMATED,\s*SYNTHETIC\s+or\s+SCENARIO_ASSUMPTION)\)",
        world_text,
    )
    if not m:
        graph.problem(f"{PPC_WORLD_001}: could not parse the five allowed provenance classifications")
        return set()
    tokens = re.findall(r"[A-Z][A-Z_]+", m.group(1))
    for cls in tokens:
        graph.node("Classification", cls, PPC_WORLD_001)
    return set(tokens)


def _check_provenance(graph, legal_classes, source_rel, record_id, value):
    if not value:
        graph.problem(f"{source_rel}: {record_id} is missing provenance_class")
        return
    if legal_classes and value not in legal_classes:
        graph.problem(f"{source_rel}: {record_id} has invalid provenance_class {value!r}; "
                      f"allowed: {', '.join(sorted(legal_classes))}")
        return
    if record_id in graph.nodes:
        graph.link(record_id, "CLASSIFIED_AS", value, source_rel)


def _parse_ppc_core_ttl(graph, legal_classes):
    text = graph.read_raw(PPC_CORE_TTL)
    if text is None:
        return
    site_m = re.search(r'ppc:siteId\s+"([^"]+)"', text)
    prov_m = re.search(r'ppc:provenanceClass\s+"([^"]+)"', text)
    if not site_m:
        graph.problem(f"{PPC_CORE_TTL}: missing ppc:siteId declaration")
        return
    site_id = site_m.group(1)
    graph.node("Facility", site_id, PPC_CORE_TTL)
    _check_provenance(graph, legal_classes, PPC_CORE_TTL, site_id, prov_m.group(1) if prov_m else None)


def _parse_epm_adapter(graph, legal_classes):
    raw = graph.read_raw(EPM_ADAPTER)
    if raw is None:
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        graph.problem(f"{EPM_ADAPTER}: invalid JSON ({exc})")
        return
    _check_provenance(graph, legal_classes, EPM_ADAPTER, EPM_ADAPTER, data.get("provenance_class"))
    artifacts = data.get("consumed_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        graph.problem(f"{EPM_ADAPTER}: consumed_artifacts must be a non-empty list")
        return
    for art in artifacts:
        path = art.get("upstream_path")
        status = art.get("status")
        if not path or status not in ALLOWED_EPM_ADAPTER_STATES:
            graph.problem(f"{EPM_ADAPTER}: unreadable EPM artifact entry {art!r}")
            continue
        graph.node("EPMArtifact", path, EPM_ADAPTER, name=art.get("name", path), status=status)


def _parse_world_001_promises(graph, text):
    promises = {}
    if text is None:
        return promises
    patterns = {
        "refineries": r"\b(one|\d+)\s+fictional\s+PADD\s+3\s+Gulf\s+Coast\s+refinery",
        "terminals": r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+terminals\b",
        "customers": r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+customers\b",
        "history_months": r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)\s+months\s+of\s+daily\s+history\b",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if not m:
            graph.problem(f"{PPC_WORLD_001}: could not parse promised count for {key}")
        else:
            val = _word_or_int(m.group(1))
            if val is None:
                graph.problem(f"{PPC_WORLD_001}: unreadable count word {m.group(1)!r} for {key}")
            else:
                promises[key] = val
    return promises


def _extract_flowsheet_endpoints(cell_text):
    """Extract parenthesized flowsheet endpoint codes from a PPC-REVIEW-002 table cell."""
    codes = []
    # Match only inside parenthesized endpoint expressions like (`4A`), (`5A`/`5B`/`5D`), (`BL` -> `FT`), (`SRU`, `9`)
    for paren in re.finditer(r"\(([^)]*)\)", cell_text):
        inner = paren.group(1)
        for m in re.finditer(r"`([A-Za-z0-9_-]+)`", inner):
            tok = m.group(1)
            if NON_ENDPOINT_TOKEN_RE.fullmatch(tok):
                continue
            if tok not in codes:
                codes.append(tok)
    return codes


def _parse_mermaid_flowsheet_nodes(raw_text):
    """Read declared flowsheet numbered/sink codes from PPC-REVIEW-002's mermaid flowchart without minting variable aliases."""
    declared = {}
    in_mermaid = False
    for line in raw_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid and stripped.startswith("```"):
            in_mermaid = False
            continue
        if not in_mermaid:
            continue
        for m in re.finditer(r'\b([A-Z0-9_]+)\["([^"]+)"\]', line):
            box_id, label = m.group(1), m.group(2).replace("\\n", " ")
            m_num = re.match(r"^([0-9]+[A-D]?)\.\s+", label)
            if m_num:
                code = m_num.group(1)
                declared[code] = label
                # Register the explicit text codes used in the closure table (CDU for 3, BL for 7, FT for 8)
                if box_id in ("CDU", "BL", "FT"):
                    declared[box_id] = label
            else:
                declared[box_id] = label
    return declared


def _parse_review_002(graph, legal_classes, declared_aliases=None):
    """Parse PPC-REVIEW-002 flowsheet, bounded interfaces, tank register, lines, and C2 spelling checks."""
    text = graph.read(PPC_REVIEW_002)
    raw_text = graph.read_raw(PPC_REVIEW_002)
    declared_aliases = declared_aliases or {}
    info = {
        "promised_tanks": 0,
        "promised_lines": [],
        "promised_internal_interfaces": 0,
        "promised_assays": None,
        "doc_tanks": set(),
        "doc_lines": set(),
        "doc_units": set(),
        "doc_pumps": set(),
        "spellings_by_code": {},
    }
    if text is None or raw_text is None:
        return info

    # 0. Declared flowsheet nodes from the mermaid diagram (the authoritative unit/sink code inventory in PPC-REVIEW-002)
    mermaid_nodes = _parse_mermaid_flowsheet_nodes(raw_text)
    for code, label in sorted(mermaid_nodes.items()):
        graph.node("Unit", code, PPC_REVIEW_002, flowsheet_label=label)
        info["doc_units"].add(code)

    # 1. Parse internal bounded interface count from locked flowsheet closure item 1 (C3)
    m_internal = re.search(r"1\.\s+\*\*Internal bounded interfaces:\*\*\s+([^\n]+)", text)
    if not m_internal:
        graph.problem(f"{PPC_REVIEW_002}: missing numbered item 1 listing internal bounded interfaces")
    else:
        bold_names = re.findall(r"\*\*([^*]+)\*\*", m_internal.group(1))
        info["promised_internal_interfaces"] = len(bold_names)

    # 2. Parse assay count promise ("three `>= 12`-point TBP assays")
    m_assay = re.search(
        r"\b(one|two|three|four|five|six|\d+)\s+`?>=\s*12`?-point\s+TBP\s+assays",
        text,
        re.IGNORECASE,
    )
    if m_assay:
        info["promised_assays"] = _word_or_int(m_assay.group(1))
    else:
        graph.problem(f"{PPC_REVIEW_002}: could not parse promised crude assay count")

    # 3. Parse table-level classification statement in section 1 (C7)
    m_cls = re.search(r"All figures below are `([A-Z_]+)` design-basis specifications", text)
    if not m_cls:
        graph.problem(f"{PPC_REVIEW_002}: design-basis section is missing a classification statement")
    elif legal_classes and m_cls.group(1) not in legal_classes:
        graph.problem(f"{PPC_REVIEW_002}: invalid design-basis classification {m_cls.group(1)!r}")

    # 4. Parse N4 paragraph listing EQ-03 transfer lines (C4)
    m_n4 = re.search(r"\*Holdup and hydraulic parameters \(`N4`\):\*([^\n]+)", text)
    if not m_n4:
        graph.problem(f"{PPC_REVIEW_002}: missing N4 paragraph listing EQ-03 transfer lines")
    else:
        info["promised_lines"] = re.findall(r"`(LINE-[A-Z0-9-]+)`", m_n4.group(1))

    # 5. Walk markdown pipe tables (process bounded interfaces FIRST so declared units exist before stream table checks!)
    tables = markdown_tables(text)
    found_stream_table = False
    found_iface_table = False
    found_tank_table = False
    stream_rows_to_check = []
    interface_names = set()
    surface_names_by_code = {}

    def record_spelling(code, surface):
        cleaned = surface.strip()
        if cleaned:
            surface_names_by_code.setdefault(code, set()).add(cleaned)

    for header, rows in tables:
        if header and "Hydrogen header term" in header[0]:
            m_h2_cls = re.search(r"`([A-Z_]+)`\)", header[0])
            if not m_h2_cls or (legal_classes and m_h2_cls.group(1) not in legal_classes):
                graph.problem(f"{PPC_REVIEW_002}: Hydrogen header table header has missing/invalid classification")
            for r in rows:
                term = r.get(header[0], "")
                if "HCU" in term:
                    record_spelling("4B", "HCU")

        elif header == ["Interface", "Inputs", "Outputs and closure rule", "Capacity & operating limits"]:
            found_iface_table = True
            internal_count = 0
            terminal_count = 0
            for r in rows:
                if r["_cells"] != len(header):
                    graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: interface row has {r['_cells']} cells, header {len(header)}")
                    continue
                name = r["Interface"].replace("`", "").strip()
                limits = r["Capacity & operating limits"]
                is_terminal = "terminal" in name.lower() or "per terminal" in limits.lower()
                graph.node("Unit", name, PPC_REVIEW_002,
                           interface_scope="terminal" if is_terminal else "refinery_internal")
                info["doc_units"].add(name)
                interface_names.add(name)
                # Map interface table short names to flowsheet codes for C2 spelling check
                code_hint = {
                    "DHT": "5A", "FCC Selective HDS": "5B", "Catalytic Reformer": "5C",
                    "NHT": "5D", "SMR": "6", "SRU": "9",
                }.get(name)
                if code_hint:
                    record_spelling(code_hint, name)
                if is_terminal:
                    terminal_count += 1
                    # C3: Terminal Ethanol sits in terminals, NEVER linked to SITE-REF-A
                else:
                    internal_count += 1
                    graph.link(name, "LOCATED_AT", "SITE-REF-A", PPC_REVIEW_002)
            if info["promised_internal_interfaces"] and internal_count != info["promised_internal_interfaces"]:
                graph.problem(
                    f"{PPC_REVIEW_002}: bounded interface table defines {internal_count} internal bounded interfaces, "
                    f"but item 1 lists {info['promised_internal_interfaces']}"
                )
            if terminal_count != 1:
                graph.problem(
                    f"{PPC_REVIEW_002}: expected 1 terminal ethanol interface row alongside internal interfaces (C3), "
                    f"found {terminal_count}"
                )

        elif header == ["Source unit", "Output stream", "Declared v1 destination / sink"]:
            found_stream_table = True
            stream_rows_to_check.extend((header, rows))

        elif len(header) == 4 and header[0] == "Tank ID" and header[1] == "Service":
            found_tank_table = True
            for r in rows:
                if r["_cells"] != len(header):
                    graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: tank row has {r['_cells']} cells, header {len(header)}")
                    continue
                tank_ids = re.findall(r"`(TK-[A-Z0-9]+)`", r["Tank ID"])
                if not tank_ids:
                    graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: tank row defines no TK-* identifiers")
                    continue
                m_mult = re.search(r"\((\d+)x\)", r["Service"])
                expected_row_tanks = int(m_mult.group(1)) if m_mult else len(tank_ids)
                if len(tank_ids) != expected_row_tanks:
                    graph.problem(
                        f"{PPC_REVIEW_002}:{r['_line']}: tank row {r['Tank ID']} defines {len(tank_ids)} tanks "
                        f"but Service says ({expected_row_tanks}x)"
                    )
                info["promised_tanks"] += expected_row_tanks

                notes = r[header[3]]
                if "-> HCU" in notes:
                    record_spelling("4B", "HCU")
                lines_in_row = re.findall(r"`(LINE-[A-Z0-9-]+)`", notes)
                pumps_in_row = re.findall(r"`(P-[A-Z0-9/]+)`", notes)
                for tid in tank_ids:
                    graph.node("Tank", tid, PPC_REVIEW_002, service=r["Service"])
                    graph.link(tid, "LOCATED_AT", "SITE-REF-A", PPC_REVIEW_002)
                    info["doc_tanks"].add(tid)
                    for lid in lines_in_row:
                        graph.link(lid, "CONNECTS_FROM", tid, PPC_REVIEW_002)
                for lid in lines_in_row:
                    graph.node("TransferLine", lid, PPC_REVIEW_002)
                    graph.link(lid, "LOCATED_AT", "SITE-REF-A", PPC_REVIEW_002)
                    info["doc_lines"].add(lid)
                for pid in pumps_in_row:
                    # C2: Detect slash-grouped pump pairs like P-101A/B vs individual pumps
                    if "/" in pid:
                        base_match = re.fullmatch(r"(P-\d+)([A-Z])/([A-Z])", pid)
                        if base_match:
                            p_a = f"{base_match.group(1)}{base_match.group(2)}"
                            p_b = f"{base_match.group(1)}{base_match.group(3)}"
                            if pid not in declared_aliases:
                                graph.problem(
                                    f"{PPC_REVIEW_002}:{r['_line']}: pump pair {pid!r} groups two physical pumps "
                                    f"({p_a}, {p_b}) under one label (name stated two ways, ADR-0060 C2)"
                                )
                    graph.node("Pump", pid, PPC_REVIEW_002)
                    graph.link(pid, "LOCATED_AT", "SITE-REF-A", PPC_REVIEW_002)
                    info["doc_pumps"].add(pid)
                    for lid in lines_in_row:
                        graph.link(pid, "DRIVES", lid, PPC_REVIEW_002)

    # Now validate stream-to-sink closure table rows WITHOUT minting destination nodes from prose!
    # Every endpoint code must already exist as a declared flowsheet/interface unit (Finding 1 fix).
    if stream_rows_to_check:
        s_header, s_rows = stream_rows_to_check[0], stream_rows_to_check[1]
        for r in s_rows:
            if r["_cells"] != len(s_header):
                graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: stream row has {r['_cells']} cells, header {len(s_header)}")
                continue
            src_cell = r["Source unit"]
            out_stream = r["Output stream"].replace("`", "").strip()
            dest_cell = r["Declared v1 destination / sink"]
            if not src_cell.strip() or not out_stream or not dest_cell.strip():
                graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: empty cell in stream-to-sink closure table")
                continue

            # Resolve source endpoint code(s): CDU + VDU -> CDU, or backticked codes (`4A`, `4B`, `5A`/`5B`/`5D`)
            src_codes = _extract_flowsheet_endpoints(src_cell)
            if not src_codes and "CDU" in src_cell:
                src_codes = ["CDU"]
            if not src_codes:
                graph.problem(f"{PPC_REVIEW_002}:{r['_line']}: unreadable stream source unit {src_cell!r}")
                continue
            # Record surface spelling for C2 check (e.g. Hydrocracker vs HCU, FDS vs FCC Selective HDS)
            src_surface = re.sub(r"\([^)]*\)", "", src_cell).replace("`", "").strip()
            if len(src_codes) == 1 and src_surface:
                record_spelling(src_codes[0], src_surface)
            elif "FDS" in src_cell:
                record_spelling("5B", "FDS")

            dest_codes = _extract_flowsheet_endpoints(dest_cell)
            if not dest_codes:
                graph.problem(
                    f"{PPC_REVIEW_002}:{r['_line']}: stream {out_stream!r} destination {dest_cell!r} "
                    f"names no declared flowsheet endpoint code"
                )
                continue
            # Record destination surface spellings right before parenthesized unit codes (`4A`..`5D`)
            for chunk in re.split(r"->|;|\band\b|\bbetween\b|\bor\b", dest_cell):
                m_ds = re.search(r"([A-Z][A-Za-z0-9 /-]{1,35}?)\s*\(`([45][A-D])`", chunk.strip())
                if m_ds:
                    record_spelling(m_ds.group(2), m_ds.group(1).strip())

            # Emit Stream node and link to EVERY source and destination code WITHOUT minting unknown targets
            stream_id = f"{'+'.join(src_codes)} :: {out_stream}"
            graph.node("Stream", stream_id, PPC_REVIEW_002, output_stream=out_stream)
            for sc in src_codes:
                graph.link(stream_id, "FROM_ENDPOINT", sc, PPC_REVIEW_002)
            for dc in dest_codes:
                # Map SRU alias in destination text (`SRU`, `9`) only to declared unit if present; never mint unknown!
                graph.link(stream_id, "TO_ENDPOINT", dc, PPC_REVIEW_002)

    # C2: Report "name stated two ways" whenever one flowsheet code has multiple distinct surface spellings
    # not covered by an explicit source alias map
    info["spellings_by_code"] = surface_names_by_code
    for code, spellings in sorted(surface_names_by_code.items()):
        unresolved = sorted(s for s in spellings if s != code and s not in declared_aliases.get(code, set()))
        if len(unresolved) > 1:
            graph.problem(
                f"{PPC_REVIEW_002}: unit code {code!r} is stated {len(unresolved)} ways without a source alias table: "
                f"{', '.join(repr(s) for s in unresolved)} (name stated two ways, ADR-0060 C2)"
            )

    if not found_stream_table:
        graph.problem(f"{PPC_REVIEW_002}: stream-to-sink closure table not found")
    if not found_iface_table:
        graph.problem(f"{PPC_REVIEW_002}: bounded interface table not found")
    if not found_tank_table:
        graph.problem(f"{PPC_REVIEW_002}: tank register table not found")

    if info["promised_lines"] and set(info["promised_lines"]) != info["doc_lines"]:
        missing_in_tbl = sorted(set(info["promised_lines"]) - info["doc_lines"])
        missing_in_n4 = sorted(info["doc_lines"] - set(info["promised_lines"]))
        graph.problem(
            f"{PPC_REVIEW_002}: TransferLine mismatch between tank table and N4 paragraph "
            f"(only in N4: {missing_in_tbl}; only in table: {missing_in_n4})"
        )

    return info


def _parse_reg_003(graph):
    text = graph.read(PPC_REG_003)
    kpis, dps = [], []
    if text is None:
        return kpis, dps
    dp_rows = _parse_pandoc_simple_table(text, "## Data products")
    kpi_rows = _parse_pandoc_simple_table(text, "## Initial KPI candidates")
    if not dp_rows:
        graph.problem(f"{PPC_REG_003}: could not parse Data products table")
    if not kpi_rows:
        graph.problem(f"{PPC_REG_003}: could not parse Initial KPI candidates table")
    for row in dp_rows:
        name = row.get("Product", "").strip()
        if name:
            graph.node("DataProduct", name, PPC_REG_003, product_type=row.get("Type", "").strip())
            dps.append(name)
    for row in kpi_rows:
        name = row.get("KPI", "").strip()
        if name:
            graph.node("KPI", name, PPC_REG_003, area=row.get("Area", "").strip())
            kpis.append(name)
    # C4: report unpromised counts as derived
    graph.meta["derived_counts"]["DataProduct"] = len(dps)
    graph.meta["derived_counts"]["KPI"] = len(kpis)
    return kpis, dps


def _parse_reg_002_and_scaffolds(graph):
    """Q2 (ADR-0060): Retain PPC-REG-002 as a source and flag legacy Kafka/D1/DuckLake rows & empty folders."""
    text = graph.read(PPC_REG_002)
    if text is not None:
        rows = _parse_pandoc_simple_table(text)
        if not rows:
            graph.problem(f"{PPC_REG_002}: could not parse Data Source and Integration Register table")
        for row in rows:
            src = row.get("Source", "").strip()
            integ = row.get("Integration", "").strip()
            replay = row.get("Durable replay", "").strip()
            combined = f"{src} | {integ} | {replay}"
            if "Debezium" in combined or "Kafka" in combined:
                graph.problem(
                    f"{PPC_REG_002}: row '{src}' still specifies '{integ}' / '{replay}', "
                    f"disagreeing with ADR-0046 (transactional outbox + NATS JetStream)"
                )
            if src == "D1" or re.search(r"\bD1\b", combined):
                graph.problem(
                    f"{PPC_REG_002}: row '{src}' still specifies Cloudflare D1, "
                    f"disagreeing with ADR-0055 (PostgreSQL workflow state, no D1)"
                )
            if "DuckLake" in combined:
                graph.problem(
                    f"{PPC_REG_002}: row '{src}' still specifies DuckLake, "
                    f"disagreeing with ADR-0045 (Delta Lake on Cloudflare R2)"
                )

    for rel_dir, reason in OBSOLETE_SCAFFOLD_DIRS:
        full_dir = os.path.join(graph.root, rel_dir)
        if os.path.isdir(full_dir):
            graph.problem(f"{rel_dir}/: obsolete scaffold folder disagrees with {reason}")


def _parse_r2_prefix_map_and_configs(graph, legal_classes):
    """Parse R2 prefix map (including C5 permitted writers and probe scripts) and config provenance (C7)."""
    hidden_cfg = {
        "bucket": None,
        "probe_prefix": None,
        "prefixes": [],
        "permitted_writers": [],
        "permitted_probe_scripts": [],
    }
    for rel in (R2_PREFIX_MAP, POLICY_THRESHOLDS, RUNTIME_FREEZE):
        raw = graph.read_raw(rel)
        if raw is None:
            continue
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            graph.problem(f"{rel}: invalid YAML ({exc})")
            continue
        if not isinstance(data, dict):
            graph.problem(f"{rel}: top-level YAML must be a mapping")
            continue
        _check_provenance(graph, legal_classes, rel, rel, data.get("provenance_class"))
        if rel == R2_PREFIX_MAP:
            hid = data.get("buckets", {}).get("hidden_truth", {})
            hidden_cfg["bucket"] = hid.get("bucket_name")
            prefixes = hid.get("prefixes", {})
            hidden_cfg["probe_prefix"] = prefixes.get("probe")
            hidden_cfg["prefixes"] = [v for v in prefixes.values() if isinstance(v, str)]
            forbidden_consumers = hid.get("forbidden_consumers")
            if not isinstance(forbidden_consumers, list) or not forbidden_consumers:
                graph.problem(f"{R2_PREFIX_MAP}: missing buckets.hidden_truth.forbidden_consumers list")

            # C5: Read permitted writers from source; report if unstated!
            permitted_writers = hid.get("permitted_writers")
            if not isinstance(permitted_writers, list) or not permitted_writers:
                graph.problem(
                    f"{R2_PREFIX_MAP}: missing buckets.hidden_truth.permitted_writers list "
                    f"(no source states permitted hidden-bucket writers, ADR-0060 C5)"
                )
            else:
                hidden_cfg["permitted_writers"] = [str(w) for w in permitted_writers]

            if hidden_cfg["bucket"]:
                graph.node(
                    "HiddenWorld",
                    hidden_cfg["bucket"],
                    R2_PREFIX_MAP,
                    forbidden_consumers=forbidden_consumers if isinstance(forbidden_consumers, list) else [],
                    permitted_writers=hidden_cfg["permitted_writers"],
                )
            else:
                graph.problem(f"{R2_PREFIX_MAP}: missing buckets.hidden_truth.bucket_name")

    # Check all adapters & JSON fixtures for provenance_class (C7)
    for pattern in ("semantic/adapters/*.adapter.json", "fixtures/golden/*.json"):
        for abs_path in sorted(glob.glob(os.path.join(graph.root, pattern))):
            rel = os.path.relpath(abs_path, graph.root).replace(os.sep, "/")
            try:
                data = json.loads(read(graph.root, rel))
            except json.JSONDecodeError as exc:
                graph.problem(f"{rel}: invalid JSON ({exc})")
                continue
            if isinstance(data, dict):
                _check_provenance(graph, legal_classes, rel, rel, data.get("provenance_class"))

    compose_raw = graph.read_raw(DOCKER_COMPOSE)
    if compose_raw is not None:
        try:
            yaml.safe_load(compose_raw)
        except yaml.YAMLError as exc:
            graph.problem(f"{DOCKER_COMPOSE}: invalid YAML ({exc})")

    return hidden_cfg


def _scan_pipelines_and_kpi_code(graph, hidden_cfg, has_epm_bindings):
    """Check 5 (hidden-world isolation, C5/C6) + Q1 (no unbound KPI definitions in code)."""
    hidden_bucket = hidden_cfg.get("bucket")
    probe_prefix = hidden_cfg.get("probe_prefix")

    for d in PENDING_CHECK_DIRS:
        if not os.path.isdir(os.path.join(graph.root, d)):
            graph.meta["pending"].append(f"{d}/")

    graph.meta["modes"]["pipelines"] = "planned"
    scanned_files = 0
    for top in PIPELINE_SCAN_DIRS:
        base = os.path.join(graph.root, top)
        if not os.path.isdir(base):
            continue
        for dirpath, _, filenames in os.walk(base):
            for fname in sorted(filenames):
                if not fname.endswith((".py", ".yaml", ".yml", ".json", ".sql")):
                    continue
                abs_path = os.path.join(dirpath, fname)
                rel = os.path.relpath(abs_path, graph.root).replace(os.sep, "/")
                scanned_files += 1
                graph.meta["modes"]["pipelines"] = "built"
                graph.node("Pipeline", rel, rel)
                content = read(graph.root, rel)

                strings_to_check = []
                imports = []
                if fname.endswith(".py"):
                    try:
                        tree = ast.parse(content, filename=rel)
                    except SyntaxError as exc:
                        graph.problem(f"{rel}: Python syntax error ({exc})")
                        continue
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Constant) and isinstance(node.value, str):
                            strings_to_check.append(node.value)
                        elif isinstance(node, ast.Import):
                            imports.extend(alias.name for alias in node.names)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            imports.append(node.module)
                else:
                    strings_to_check.append(content)

                # Check forbidden imports of generators/ canonical world internals
                for imp in imports:
                    if imp == "generators" or imp.startswith("generators."):
                        graph.node("HiddenWorld", imp, rel)
                        graph.link(rel, "READS_OR_WRITES", imp, rel)

                # C5: Allow ONLY strings inside the declared probe_prefix from r2_prefix_map.yaml
                # (plus the exact root prefix "evaluation/hidden/" used solely for 403 AccessDenied checks).
                is_access_denied_probe = ("AccessDenied" in content and bool(probe_prefix))
                for s in strings_to_check:
                    if "evaluation/hidden/" in s:
                        if probe_prefix and s.startswith(probe_prefix):
                            continue
                        if is_access_denied_probe and s == "evaluation/hidden/":
                            continue
                        target = hidden_bucket or "evaluation/hidden/"
                        graph.node("HiddenWorld", target, rel)
                        graph.link(rel, "READS_OR_WRITES", target, rel)
                    if hidden_bucket and hidden_bucket in s:
                        graph.node("HiddenWorld", hidden_bucket, rel)
                        graph.link(rel, "READS_OR_WRITES", hidden_bucket, rel)

                # Q1: Code defining KPIs without an EPM binding or claiming PPC_EXTENSION fails from run 1
                if "PPC_EXTENSION" in content:
                    graph.problem(f"{rel}: uses rejected KPI disposition 'PPC_EXTENSION' (forbidden by ADR-0060 Q1)")
                if fname.endswith(".py"):
                    if KPI_CODE_PATTERN.search(content):
                        if not has_epm_bindings:
                            graph.problem(
                                f"{rel}: defines KPI records/formulas without an EPM binding file "
                                f"({EPM_KPI_BINDINGS} is absent; forbidden by ADR-0060 Q1 / PPC-017)"
                            )

    if scanned_files == 0:
        graph.meta["pending"].append("pipeline runtime modules")


def _load_declared_aliases(root):
    """Read explicit unit/pump aliases from fixtures/golden/refinery_a_design_basis.yaml when built."""
    db_abs = os.path.join(root, DESIGN_BASIS)
    if not os.path.isfile(db_abs):
        return {}
    try:
        db = yaml.safe_load(read(root, DESIGN_BASIS))
    except yaml.YAMLError:
        return {}
    if not isinstance(db, dict):
        return {}
    aliases = {}
    for u in db.get("units", []):
        uid = u.get("id")
        if uid and isinstance(u.get("aliases"), list):
            aliases[uid] = set(str(a) for a in u["aliases"])
    for p in db.get("pumps", []):
        pair = p.get("doc_pair_label")
        if pair:
            aliases[pair] = {str(p.get("id", ""))}
    return aliases


def _parse_optional_built_sources(graph, legal_classes, review_info, world_promises, kpis, dps):
    """Parse WP-1+ built sources automatically when present; report pending otherwise (Q3)."""
    # 1. Design basis YAML (WP-1)
    db_abs = os.path.join(graph.root, DESIGN_BASIS)
    if not os.path.isfile(db_abs):
        graph.meta["modes"]["design_basis"] = "planned"
        graph.meta["pending"].append(DESIGN_BASIS)
        graph.meta["pending"].append("WP-1 promised counts: crude_assays, terminals, customers")
    else:
        graph.meta["modes"]["design_basis"] = "built"
        try:
            db = yaml.safe_load(read(graph.root, DESIGN_BASIS))
        except yaml.YAMLError as exc:
            graph.problem(f"{DESIGN_BASIS}: invalid YAML ({exc})")
            db = None
        if isinstance(db, dict):
            _check_provenance(graph, legal_classes, DESIGN_BASIS, DESIGN_BASIS, db.get("provenance_class"))

            assays = db.get("crude_assays", [])
            for a in assays:
                aid = a.get("id")
                if aid:
                    graph.node("CrudeAssay", aid, DESIGN_BASIS)
                    _check_provenance(graph, legal_classes, DESIGN_BASIS, aid, a.get("provenance_class"))

            terminals = db.get("terminals", [])
            for t in terminals:
                tid = t.get("id")
                if tid:
                    graph.node("Terminal", tid, DESIGN_BASIS)
                    _check_provenance(graph, legal_classes, DESIGN_BASIS, tid, t.get("provenance_class"))

            customers = db.get("customers", [])
            for c in customers:
                cid = c.get("id")
                if cid:
                    graph.node("Customer", cid, DESIGN_BASIS)
                    _check_provenance(graph, legal_classes, DESIGN_BASIS, cid, c.get("provenance_class"))

            for u in db.get("units", []):
                uid = u.get("id")
                if uid:
                    graph.node("Unit", uid, DESIGN_BASIS)
                    if u.get("facility"):
                        graph.link(uid, "LOCATED_AT", u["facility"], DESIGN_BASIS)
                    comp_id = u.get("recycle_compressor_id")
                    if comp_id:
                        graph.node("Equipment", comp_id, DESIGN_BASIS, parent_unit=uid)
                        graph.link(comp_id, "PART_OF", uid, DESIGN_BASIS)
                        if u.get("facility"):
                            graph.link(comp_id, "LOCATED_AT", u["facility"], DESIGN_BASIS)
                        _check_provenance(graph, legal_classes, DESIGN_BASIS, comp_id, u.get("provenance_class"))
                    _check_provenance(graph, legal_classes, DESIGN_BASIS, uid, u.get("provenance_class"))

            for t in db.get("tanks", []):
                tid = t.get("id")
                if not tid:
                    continue
                if review_info["doc_tanks"] and tid not in review_info["doc_tanks"]:
                    graph.problem(f"{DESIGN_BASIS}: Tank {tid!r} is not declared in {PPC_REVIEW_002}")
                graph.node("Tank", tid, DESIGN_BASIS)
                graph.link(tid, "LOCATED_AT", db.get("facility_id", "SITE-REF-A"), DESIGN_BASIS)
                _check_provenance(graph, legal_classes, DESIGN_BASIS, tid, t.get("provenance_class"))

            for ln in db.get("transfer_lines", []):
                lid = ln.get("id")
                if not lid:
                    continue
                if review_info["doc_lines"] and lid not in review_info["doc_lines"]:
                    graph.problem(f"{DESIGN_BASIS}: TransferLine {lid!r} is not declared in {PPC_REVIEW_002}")
                graph.node("TransferLine", lid, DESIGN_BASIS)
                graph.link(lid, "LOCATED_AT", db.get("facility_id", "SITE-REF-A"), DESIGN_BASIS)
                if ln.get("source"):
                    graph.link(lid, "CONNECTS_FROM", ln["source"], DESIGN_BASIS)
                if ln.get("destination"):
                    graph.link(lid, "CONNECTS_TO", ln["destination"], DESIGN_BASIS)
                _check_provenance(graph, legal_classes, DESIGN_BASIS, lid, ln.get("provenance_class"))

            for st in db.get("streams", []):
                sid = st.get("id")
                if not sid:
                    graph.problem(f"{DESIGN_BASIS}: stream entry missing id")
                    continue
                src_ep = st.get("source")
                dst_ep = st.get("destination")
                sp = st.get("source_phase")
                dp = st.get("destination_phase")
                mu = st.get("mass_unit")
                vu = st.get("volume_unit")
                graph.node("Stream", sid, DESIGN_BASIS, phase=sp or dp or "unknown")
                if src_ep:
                    graph.link(sid, "FROM_ENDPOINT", src_ep, DESIGN_BASIS)
                if dst_ep:
                    graph.link(sid, "TO_ENDPOINT", dst_ep, DESIGN_BASIS)
                if sp not in LEGAL_PHASES or dp not in LEGAL_PHASES:
                    graph.problem(f"{DESIGN_BASIS}: Stream {sid} has invalid phase ({sp!r} -> {dp!r})")
                elif sp != dp:
                    graph.problem(f"{DESIGN_BASIS}: Stream {sid} phase disagrees across ends ({sp!r} vs {dp!r})")
                if not mu:
                    graph.problem(f"{DESIGN_BASIS}: Stream {sid} is missing SI mass_unit")
                if (sp == "gas" or dp == "gas") and vu in LIQUID_VOLUME_UNITS:
                    graph.problem(f"{DESIGN_BASIS}: gas Stream {sid} cannot declare liquid volume_unit {vu!r}")
                _check_provenance(graph, legal_classes, DESIGN_BASIS, sid, st.get("provenance_class"))

            if review_info["promised_assays"] is not None and len(assays) != review_info["promised_assays"]:
                graph.problem(
                    f"CrudeAssay: {DESIGN_BASIS} defines {len(assays)}, "
                    f"but {PPC_REVIEW_002} promises {review_info['promised_assays']}"
                )
            if "terminals" in world_promises and len(terminals) != world_promises["terminals"]:
                graph.problem(
                    f"Terminal: {DESIGN_BASIS} defines {len(terminals)}, "
                    f"but {PPC_WORLD_001} promises {world_promises['terminals']}"
                )
            if "customers" in world_promises and len(customers) != world_promises["customers"]:
                graph.problem(
                    f"Customer: {DESIGN_BASIS} defines {len(customers)}, "
                    f"but {PPC_WORLD_001} promises {world_promises['customers']}"
                )

    # 1b. CFG-0 DEXPI topology JSON (WP-1)
    cfg0_abs = os.path.join(graph.root, CFG0_TOPOLOGY)
    if os.path.isfile(cfg0_abs):
        graph.meta["modes"]["cfg0_topology"] = "built"
        try:
            cfg0 = json.loads(read(graph.root, CFG0_TOPOLOGY))
        except json.JSONDecodeError as exc:
            graph.problem(f"{CFG0_TOPOLOGY}: invalid JSON ({exc})")
            cfg0 = None
        if isinstance(cfg0, dict):
            _check_provenance(graph, legal_classes, CFG0_TOPOLOGY, CFG0_TOPOLOGY, cfg0.get("provenance_class"))
            cfg0_tags = set()
            for eq in cfg0.get("equipment", []):
                tag = eq.get("tag")
                if not tag:
                    continue
                cfg0_tags.add(tag)
                cls_name = eq.get("class", "")
                if tag in graph.nodes:
                    label = graph.nodes[tag]["label"]
                elif cls_name in ("StorageTank", "SegregatedHoldTank"):
                    label = "Tank"
                elif cls_name == "CentrifugalPump":
                    label = "Pump"
                elif cls_name == "DistributionTerminal":
                    label = "Terminal"
                elif eq.get("parent_unit"):
                    label = "Equipment"
                else:
                    label = "Unit"
                graph.node(label, tag, CFG0_TOPOLOGY)
                if eq.get("parent_unit"):
                    graph.link(tag, "PART_OF", eq["parent_unit"], CFG0_TOPOLOGY)
            for conn in cfg0.get("piping_connections", []):
                cid = conn.get("id")
                src = conn.get("from")
                dst = conn.get("to")
                if not cid:
                    continue
                if src not in cfg0_tags:
                    graph.problem(f"{CFG0_TOPOLOGY}: piping connection {cid!r} has dangling 'from' endpoint {src!r}")
                if dst not in cfg0_tags:
                    graph.problem(f"{CFG0_TOPOLOGY}: piping connection {cid!r} has dangling 'to' endpoint {dst!r}")
                graph.node("TransferLine", cid, CFG0_TOPOLOGY)
                if src:
                    graph.link(cid, "CONNECTS_FROM", src, CFG0_TOPOLOGY)
                if dst:
                    graph.link(cid, "CONNECTS_TO", dst, CFG0_TOPOLOGY)
                for pid in conn.get("pumps", []):
                    if pid not in cfg0_tags:
                        graph.problem(f"{CFG0_TOPOLOGY}: piping connection {cid!r} references undeclared pump {pid!r}")
                    else:
                        graph.link(pid, "DRIVES", cid, CFG0_TOPOLOGY)

    # 2. OT tags YAML (WP-1)
    if not os.path.isfile(os.path.join(graph.root, OT_TAGS)):
        graph.meta["modes"]["ot_tags"] = "planned"
        graph.meta["pending"].append(OT_TAGS)
    else:
        graph.meta["modes"]["ot_tags"] = "built"
        try:
            ot_data = yaml.safe_load(read(graph.root, OT_TAGS))
        except yaml.YAMLError as exc:
            graph.problem(f"{OT_TAGS}: invalid YAML ({exc})")
            ot_data = None
        if isinstance(ot_data, dict):
            _check_provenance(graph, legal_classes, OT_TAGS, OT_TAGS, ot_data.get("provenance_class"))
            for tag in ot_data.get("tags", []):
                tid = tag.get("tag_id")
                eq = tag.get("equipment_id")
                if tid:
                    graph.node("OTTag", tid, OT_TAGS, unit=tag.get("native_unit", ""))
                    if eq:
                        graph.link(tid, "MEASURES", eq, OT_TAGS)
                    _check_provenance(graph, legal_classes, OT_TAGS, tid, tag.get("provenance_class"))

    # 3. EPM KPI bindings YAML (Q1 strict completeness check when file exists; Finding 3 & 5 fix)
    if not os.path.isfile(os.path.join(graph.root, EPM_KPI_BINDINGS)):
        graph.meta["modes"]["epm_kpi_bindings"] = "planned"
        graph.meta["pending"].append(f"{EPM_KPI_BINDINGS} ({len(kpis)} KPI candidates and {len(dps)} data products pending EPM bindings)")
    else:
        graph.meta["modes"]["epm_kpi_bindings"] = "built"
        try:
            bdata = yaml.safe_load(read(graph.root, EPM_KPI_BINDINGS))
        except yaml.YAMLError as exc:
            graph.problem(f"{EPM_KPI_BINDINGS}: invalid YAML ({exc})")
            bdata = None
        if isinstance(bdata, dict):
            _check_provenance(graph, legal_classes, EPM_KPI_BINDINGS, EPM_KPI_BINDINGS, bdata.get("provenance_class"))
            covered_kpis = set()
            covered_dps = set()
            for item in bdata.get("bindings", []):
                kpi = item.get("kpi")
                dp = item.get("data_product")
                name = kpi or dp
                status = item.get("status")
                artifact = item.get("epm_artifact")
                if status == "PPC_EXTENSION":
                    graph.problem(f"{EPM_KPI_BINDINGS}: {name!r} uses rejected disposition 'PPC_EXTENSION' (ADR-0060 Q1)")
                    continue
                if status not in ALLOWED_EPM_BINDING_STATES:
                    graph.problem(f"{EPM_KPI_BINDINGS}: {name!r} has invalid EPM binding status {status!r}")
                    continue
                if status != "pending":
                    if not artifact:
                        graph.problem(f"{EPM_KPI_BINDINGS}: {name!r} with status {status!r} is missing epm_artifact")
                        continue
                    graph.link(name, "DEFINED_BY_EPM", artifact, EPM_KPI_BINDINGS)
                if kpi:
                    covered_kpis.add(kpi)
                if dp:
                    covered_dps.add(dp)
            # Strict completeness: every KPI and DataProduct in PPC-REG-003 must be covered!
            for missing_kpi in sorted(set(kpis) - covered_kpis):
                graph.problem(
                    f"{missing_kpi}: a KPI with no EPM binding entry in {EPM_KPI_BINDINGS} (ADR-0060 Q1 strict mode)"
                )
            for missing_dp in sorted(set(dps) - covered_dps):
                graph.problem(
                    f"{missing_dp}: a DataProduct with no EPM binding entry in {EPM_KPI_BINDINGS} (ADR-0060 Q1 strict mode)"
                )


def EXPECTED_COUNTS(graph):
    counts = []
    promised_tanks = graph.meta.get("promised_tanks", 0)
    if promised_tanks:
        counts.append(("Tank", promised_tanks, PPC_REVIEW_002))
    promised_lines = graph.meta.get("promised_lines_count", 0)
    if promised_lines:
        counts.append(("TransferLine", promised_lines, PPC_REVIEW_002))
    return counts


def PROJECT_CHECKS(graph):
    findings = []
    for (src, kind, dst), sources in sorted(graph.edges.items()):
        if kind == "READS_OR_WRITES":
            findings.append(
                f"{src} -READS_OR_WRITES-> {dst}: integration/runtime pipeline must not access hidden canonical world "
                f"(found in {', '.join(sorted(sources))})"
            )
    return findings


def build(root):
    graph = Graph(root)
    world_text = graph.read(PPC_WORLD_001)
    graph.read(PPC_017)
    legal_classes = _parse_legal_classifications(graph, world_text)
    world_promises = _parse_world_001_promises(graph, world_text)
    declared_aliases = _load_declared_aliases(root)

    _parse_ppc_core_ttl(graph, legal_classes)
    _parse_epm_adapter(graph, legal_classes)
    review_info = _parse_review_002(graph, legal_classes, declared_aliases=declared_aliases)
    graph.meta["promised_tanks"] = review_info["promised_tanks"]
    graph.meta["promised_lines_count"] = len(review_info["promised_lines"])
    graph.meta["derived_counts"]["Pump"] = sum(1 for n in graph.nodes.values() if n["label"] == "Pump")

    kpis, dps = _parse_reg_003(graph)
    _parse_reg_002_and_scaffolds(graph)
    hidden_cfg = _parse_r2_prefix_map_and_configs(graph, legal_classes)
    has_epm_bindings = os.path.isfile(os.path.join(root, EPM_KPI_BINDINGS))
    _scan_pipelines_and_kpi_code(graph, hidden_cfg, has_epm_bindings)
    _parse_optional_built_sources(graph, legal_classes, review_info, world_promises, kpis, dps)
    return graph


if __name__ == "__main__":
    sys.exit(main())
