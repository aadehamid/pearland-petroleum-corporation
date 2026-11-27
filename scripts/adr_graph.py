#!/usr/bin/env python3
"""A graph of PPC's architecture decisions, built fresh from the records.

Usage:
  scripts/adr_graph.py changed ADR-0045     later decisions that changed it, through any chain
  scripts/adr_graph.py basis ADR-0055       what it builds on, through any chain
  scripts/adr_graph.py summary              counts of decisions, documents and links
  scripts/adr_graph.py check                where the three records disagree (exit 1 if they do)
  scripts/adr_graph.py query 'CYPHER'       any read-only Cypher over the graph
  scripts/adr_graph.py export               the graph as a Cypher script for relate or Neo4j

Sources, read every run, so the graph never goes stale:
  docs/PPC-REG-001_Architecture_Decision_Register.md   ADR-001 to ADR-039 (baseline)
  docs/adr/README.md                                    ADR-0040 onward: title, status, date,
                                                        and the "Amends / clarifies" links
  docs/adr/NNNN-*.md                                    frontmatter: status, date, amends, authority

The graph has (:Decision {id, title, status, date, authority, baseline, file}),
(:Document {id}) for records such as PPC-001, and links named for the index's
verbs: (:Decision)-[:AMENDS|CLARIFIES|EXTENDS|STAGES]->(:Decision|:Document).
The index is the source of the links. The "amended by" notes in its status
column and each file's `amends:` frontmatter are only compared with it, by
`check`. `changed`, `basis`, `query` and `export --run` need relate;
`summary`, `check` and plain `export` do not.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = "docs/PPC-REG-001_Architecture_Decision_Register.md"
INDEX = "docs/adr/README.md"
VERBS = {"amends": "AMENDS", "clarifies": "CLARIFIES", "extends": "EXTENDS", "stages": "STAGES"}
PAST = {"amended": "AMENDS", "clarified": "CLARIFIES", "extended": "EXTENDS", "staged": "STAGES"}
ID = re.compile(r"\b(ADR-\d{3,4}|[A-Z]+-\d{3})\b")
LINKS = "AMENDS|CLARIFIES|EXTENDS|STAGES"
PAST_OF = {v: k for k, v in PAST.items()}


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def norm(identifier):
    """ADR-0007 and ADR-007 name the same baseline decision; keep one spelling."""
    m = re.fullmatch(r"ADR-0*(\d+)", identifier)
    if m:
        number = int(m.group(1))
        return f"ADR-{number:03d}" if number < 40 else f"ADR-{number:04d}"
    return identifier


def parse_register(text):
    """ADR-001 to ADR-039: a fixed-width table, then markdown tables."""
    decisions = {}
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.fullmatch(r"\s*-{3,}(\s+-{3,})+\s*", line):
            spans = [m.span() for m in re.finditer(r"-+", line)]
            current = None
            for row in lines[i + 1:]:
                if re.fullmatch(r"\s*-{3,}\s*", row) or row.startswith("#"):
                    break
                cells = [row[a:b if k < len(spans) - 1 else None].strip() for k, (a, b) in enumerate(spans)]
                if not any(cells):
                    current = None
                    continue
                if re.fullmatch(r"\d{3}", cells[0]):
                    current = norm("ADR-" + cells[0])
                    decisions[current] = {"title": [], "rationale": []}
                if current:
                    decisions[current]["title"].append(cells[1])
                    decisions[current]["rationale"].append(cells[2] if len(cells) > 2 else "")
            break
    for d in decisions.values():
        d["title"] = " ".join(t for t in d["title"] if t)
        d["rationale"] = " ".join(t for t in d["rationale"] if t)
    for m in re.finditer(r"^\| (ADR-\d{3}) \| (.*?) \| (.*?) \|$", text, re.MULTILINE):
        decisions[norm(m.group(1))] = {"title": m.group(2), "rationale": m.group(3)}
    return decisions


def parse_index(text):
    """ADR-0040 onward from the index table: one row per decision."""
    rows = {}
    for line in text.splitlines():
        m = re.fullmatch(r"\| \[(ADR-\d{4})\]\(([^)]+)\) \| (.*?) \| (.*?) \| (\d{4}-\d{2}-\d{2}) \| (.*?) \|", line.strip())
        if not m:
            continue
        identifier, file, title, status, date, relations = m.groups()
        links = []
        for part in relations.split(";"):
            part = part.strip()
            verb = part.split(" ", 1)[0].lower()
            if verb in VERBS:
                links += [(VERBS[verb], norm(t)) for t in ID.findall(part)]
            elif part and part.lower() != "none":
                links.append(("UNPARSED", part))
        notes = []
        for verb, targets in re.findall(r"\b(amended|clarified|extended|staged) by ([^;)]*)", status):
            notes += [(PAST[verb], norm(t)) for t in ID.findall(targets)]
        rows[identifier] = {"file": "docs/adr/" + file, "title": title, "status": status.split(" (")[0],
                            "status_text": status, "date": date, "links": links, "notes": notes}
    return rows


def parse_frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    fields = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    amends = fields.get("amends", "")
    fields["amends"] = [] if amends.lower() in ("", "none") else [norm(t) for t in ID.findall(amends)]
    return fields


def build(root=ROOT):
    baseline = parse_register(read(root, REGISTER))
    index = parse_index(read(root, INDEX))
    nodes, documents, edges = [], set(), []
    for identifier, d in sorted(baseline.items()):
        nodes.append({"id": identifier, "title": d["title"], "status": "Decided", "date": None,
                      "authority": None, "baseline": True, "file": REGISTER})
    frontmatter = {}
    for identifier, row in sorted(index.items()):
        path = os.path.join(root, row["file"])
        fm = parse_frontmatter(read(root, row["file"])) if os.path.exists(path) else {}
        frontmatter[identifier] = fm
        nodes.append({"id": identifier, "title": row["title"], "status": row["status"], "date": row["date"],
                      "authority": fm.get("authority"), "baseline": False, "file": row["file"]})
        for verb, target in row["links"]:
            if verb == "UNPARSED":
                continue
            edges.append({"source": identifier, "verb": verb, "target": target})
            if not target.startswith("ADR-"):
                documents.add(target)
    return {"root": root, "nodes": nodes, "documents": sorted(documents), "edges": edges,
            "index": index, "frontmatter": frontmatter, "baseline": baseline}


def check(graph):
    """Each place where the index links, the status notes and the frontmatter disagree."""
    findings = []
    known = {n["id"] for n in graph["nodes"]}
    links = {(e["source"], e["verb"], e["target"]) for e in graph["edges"]}
    for identifier, row in sorted(graph["index"].items()):
        for verb, text in row["links"]:
            if verb == "UNPARSED":
                findings.append(f"{identifier}: index link not understood: {text!r}")
        for verb, target in row["links"]:
            if verb != "UNPARSED" and target.startswith("ADR-") and target not in known:
                findings.append(f"{identifier}: links to {target}, which no record defines")
        for verb, source in row["notes"]:
            said = sorted(v for s, v, t in links if s == source and t == identifier)
            if verb not in said:
                findings.append(f"{identifier}: status says {PAST_OF[verb]} by {source}, but {source}'s index "
                                f"row says it {', '.join(v.lower() for v in said) or 'does nothing to'} {identifier}")
        if not os.path.exists(os.path.join(graph["root"], row["file"])):
            findings.append(f"{identifier}: index points at {row['file']}, which does not exist")
        fm = graph["frontmatter"].get(identifier, {})
        indexed = {t for v, t in row["links"] if v == "AMENDS"}
        for target in fm.get("amends", []):
            if target not in indexed:
                other = sorted(v.lower() for v, t in row["links"] if t == target)
                findings.append(f"{identifier}: frontmatter amends {target}, but the index says it "
                                f"{', '.join(other) or 'does nothing to'} {target}")
        for target in sorted(indexed - set(fm.get("amends", []))):
            findings.append(f"{identifier}: index amends {target}, but the frontmatter does not list it")
        if fm and fm.get("status") and fm["status"] != row["status"]:
            findings.append(f"{identifier}: frontmatter status {fm['status']!r}, index status {row['status']!r}")
        if fm and fm.get("date") and fm["date"] != row["date"]:
            findings.append(f"{identifier}: frontmatter date {fm['date']}, index date {row['date']}")
    for e in graph["edges"]:
        if e["target"].startswith("ADR-") and e["target"] in graph["index"]:
            notes = graph["index"][e["target"]]["notes"]
            # A note from the same source with another verb is already reported above.
            if not any(source == e["source"] for _, source in notes):
                findings.append(f"{e['target']}: {e['source']} {e['verb'].lower()} it, but its status does not say so")
    return findings


def cypher_seed(graph):
    """The graph as one Cypher script with literal values."""
    lit = lambda v: json.dumps(v) if v is not None else "null"
    out = ["CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;",
           "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;"]
    for n in graph["nodes"]:
        props = ", ".join(f"{k}: {lit(n[k])}" for k in ("id", "title", "status", "date", "authority", "baseline", "file"))
        out.append(f"CREATE (:Decision {{{props}}});")
    for d in graph["documents"]:
        out.append(f"CREATE (:Document {{id: {lit(d)}}});")
    for e in graph["edges"]:
        out.append(f"MATCH (a:Decision {{id: {lit(e['source'])}}}), (b {{id: {lit(e['target'])}}}) "
                   f"CREATE (a)-[:{e['verb']}]->(b);")
    return "\n".join(out) + "\n"


def run_relate(graph, statement, params):
    if not shutil.which("relate"):
        sys.exit("adr_graph: relate is not installed. Install it with: curl -sSfL https://relatedb.ai/install.sh | bash")
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "graph.cypher")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(cypher_seed(graph) + statement.rstrip().rstrip(";") + ";\n")
        args = ["relate", "query", "--database", ":memory:", "--mode", "jsonl", "--max-rows", "0"]
        for key, value in params.items():
            args += ["--param", f"{key}={json.dumps(value)}"]
        with open(script, encoding="utf-8") as fh:
            p = subprocess.run(args, stdin=fh, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout + p.stderr)
        sys.exit(p.returncode)
    return [line for line in p.stdout.splitlines() if line.startswith("{")]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "help"
    graph = build()
    known = {n["id"] for n in graph["nodes"]}
    if cmd in ("changed", "basis"):
        if len(argv) != 2:
            print(f"usage: scripts/adr_graph.py {cmd} ADR-NNNN", file=sys.stderr)
            return 2
        target = norm(argv[1].upper())
        if target not in known:
            print(f"adr_graph: no decision {target} in the register or the index", file=sys.stderr)
            return 2
        arrow = ("<-[r:%s*1..]-(x)" if cmd == "changed" else "-[r:%s*1..]->(x)") % LINKS
        statement = (f"MATCH p = (d:Decision {{id: $id}}){arrow} "
                     "RETURN x.id AS id, coalesce(x.title, '') AS title, length(p) AS hops, "
                     "[rel IN relationships(p) | type(rel)] AS via, "
                     "[n IN nodes(p) | n.id] AS chain ORDER BY hops, id")
        for row in run_relate(graph, statement, {"id": target}):
            print(row)
        return 0
    if cmd == "query":
        if len(argv) != 2:
            print("usage: scripts/adr_graph.py query 'CYPHER'", file=sys.stderr)
            return 2
        if re.search(r"\b(CREATE|MERGE|DELETE|SET|REMOVE|DROP|LOAD)\b", argv[1], re.IGNORECASE):
            print("adr_graph: query is read-only; the graph is rebuilt from the records each run", file=sys.stderr)
            return 2
        for row in run_relate(graph, argv[1], {}):
            print(row)
        return 0
    if cmd == "summary":
        verbs = {}
        for e in graph["edges"]:
            verbs[e["verb"]] = verbs.get(e["verb"], 0) + 1
        print(json.dumps({"baseline_decisions": sum(n["baseline"] for n in graph["nodes"]),
                          "indexed_decisions": sum(not n["baseline"] for n in graph["nodes"]),
                          "documents": len(graph["documents"]), "links": dict(sorted(verbs.items()))}))
        return 0
    if cmd == "check":
        findings = check(graph)
        for f in findings:
            print("adr_graph: " + f, file=sys.stderr)
        if not findings:
            print("adr_graph: the index links, status notes and frontmatter agree")
        return 1 if findings else 0
    if cmd == "export":
        sys.stdout.write(cypher_seed(graph))
        return 0
    print(__doc__.split("\n\nSources")[0].strip())
    return 0 if cmd in ("help", "-h", "--help") else 2


if __name__ == "__main__":
    sys.exit(main())
