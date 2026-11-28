#!/usr/bin/env python3
"""A graph of PPC's architecture decisions, built fresh from the records.

Usage:
  scripts/adr_graph.py changed ADR-0045     later decisions that changed it, through any chain
  scripts/adr_graph.py basis ADR-0055       what it builds on, through any chain
  scripts/adr_graph.py summary              counts of decisions, documents and links
  scripts/adr_graph.py check                where the records disagree or cannot be read (exit 1 if so)
  scripts/adr_graph.py query 'CYPHER'       any Cypher, run on a read-only copy of the graph
  scripts/adr_graph.py export               the graph as a Cypher script for relate or Neo4j

Sources, read every run, so the graph never goes stale:
  docs/PPC-REG-001_Architecture_Decision_Register.md   ADR-001 to ADR-039 (baseline)
  docs/adr/README.md                                    ADR-0040 onward: title, status, date,
                                                        and the "Amends / clarifies" links
  docs/adr/NNNN-*.md                                    frontmatter: status, date, amends, authority

The graph has (:Decision {id, title, status, date, authority, baseline, file}),
(:Document {id}) for records such as PPC-001, and links named for the index's
verbs: (:Decision)-[:AMENDS|CLARIFIES|EXTENDS|STAGES]->(:Decision|:Document).
The index is the only source of links; a link to a decision no record defines
stays out of the graph and is reported by check. The status column's notes
("amended by ADR-0054") and each file's `amends:` frontmatter are only compared
with the links, by check. changed, basis and query need relate; summary, check
and export do not. ADR_GRAPH_ROOT points the tool at another checkout.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.environ.get("ADR_GRAPH_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = "docs/PPC-REG-001_Architecture_Decision_Register.md"
INDEX = "docs/adr/README.md"
VERBS = {"amends": "AMENDS", "clarifies": "CLARIFIES", "extends": "EXTENDS", "stages": "STAGES"}
PAST = {"amended": "AMENDS", "clarified": "CLARIFIES", "extended": "EXTENDS", "staged": "STAGES"}
PAST_OF = {v: k for k, v in PAST.items()}
LINKS = "AMENDS|CLARIFIES|EXTENDS|STAGES"
# Ids are upper case and end at a word boundary that is not a hyphen, so
# ADR-0042a or ADR-0042-draft is not read as ADR-0042.
ID = r"(?:ADR-\d{1,4}|[A-Z]+(?:-[A-Z]+)*-\d{3})(?![\w-])"
ID_RE = re.compile(r"(?<![\w-])" + ID)
SEP = r"\s*(?:,\s*and\b|,|\band\b)\s*"
ID_LIST = re.compile(ID + r"(?:" + SEP + ID + r")*")
CLAUSE = re.compile(r"[;,]\s*(?=(?i:amends|clarifies|extends|stages)\b)")
NOTE = re.compile(r"\b((?i:amended|clarified|extended|staged)) by (" + ID + r"(?:" + SEP + ID + r")*)")
ROW = re.compile(r"\| \[(ADR-\d{1,4})\]\(([^)|]+)\) \| ([^|]+) \| ([^|]+) \| (\d{4}-\d{2}-\d{2}) \| ([^|]*) \|")


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


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


def parse_links(cell):
    """The "Amends / clarifies" cell: clauses that each start with a verb and list ids."""
    links, unread = [], []
    if cell.strip().lower() in ("", "none"):
        return links, unread
    for part in re.split(r";", cell):
        for clause in CLAUSE.split(part):
            clause = clause.strip()
            if not clause:
                continue
            verb, _, rest = clause.partition(" ")
            if verb.lower() in VERBS and ID_LIST.fullmatch(rest.strip()):
                links += [(VERBS[verb.lower()], norm(t)) for t in ID_RE.findall(rest)]
            else:
                unread.append(clause)
    return links, unread


def parse_index(text):
    """ADR-0040 onward from the index table: one row per decision."""
    rows, problems = {}, []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s|:-]*\|", line) or line.startswith("| ADR | Title"):
            continue
        m = ROW.fullmatch(line)
        if not m:
            problems.append(f"index row not understood: {line[:80]!r}")
            continue
        identifier, file, title, status, date, relations = m.groups()
        identifier = norm(identifier)
        links, unread = parse_links(relations)
        notes = [(PAST[v.lower()], norm(t)) for v, targets in NOTE.findall(status) for t in ID_RE.findall(targets)]
        if identifier in rows:
            problems.append(f"{identifier}: the index has more than one row for it; the first is used")
            continue
        if int(identifier.split("-")[1]) < 40:
            problems.append(f"{identifier}: a baseline decision belongs in {REGISTER}, not the index")
            continue
        seen, dupes = set(), []
        for link in links:
            if link in seen:
                dupes.append(link)
            seen.add(link)
        for verb, target in dupes:
            problems.append(f"{identifier}: the index lists {verb.lower()} {target} more than once")
        links = list(dict.fromkeys(links))
        rows[identifier] = {"file": "docs/adr/" + file, "title": title, "status": status.split(" (")[0],
                            "date": date, "links": links, "unread": unread, "notes": notes}
    return rows, problems


def parse_frontmatter(text):
    """The leading --- block: simple `key: value` lines and `- item` lists. None if absent."""
    m = re.match(r"---[ \t]*\n(.*?)^---[ \t]*$", text.replace("\r\n", "\n"), re.DOTALL | re.MULTILINE)
    if not m:
        return None
    fields, key = {}, None
    for line in m.group(1).splitlines():
        if line.strip().startswith("#"):
            continue
        item = re.fullmatch(r"\s*-\s+(.*)", line)
        if item and key:
            fields[key] = (fields[key] + ", " if fields[key] else "") + item.group(1).strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            fields[key] = value.strip().strip("'\"")
    amends = fields.get("amends", "")
    fields["amends_unread"] = None
    if amends.lower() in ("", "none", "[]"):
        fields["amends"] = []
    elif ID_LIST.fullmatch(amends):
        fields["amends"] = [norm(t) for t in ID_RE.findall(amends)]
    else:
        fields["amends"], fields["amends_unread"] = [], amends
    return fields


def build(root=ROOT):
    baseline = parse_register(read(root, REGISTER))
    index, problems = parse_index(read(root, INDEX))
    known = set(baseline) | set(index)
    nodes, documents, edges = [], set(), []
    for identifier, d in sorted(baseline.items()):
        nodes.append({"id": identifier, "title": d["title"], "status": "Decided", "date": None,
                      "authority": None, "baseline": True, "file": REGISTER})
    frontmatter = {}
    for identifier, row in sorted(index.items()):
        path = os.path.join(root, row["file"])
        fm = parse_frontmatter(read(root, row["file"])) if os.path.exists(path) else None
        frontmatter[identifier] = fm
        nodes.append({"id": identifier, "title": row["title"], "status": row["status"], "date": row["date"],
                      "authority": (fm or {}).get("authority"), "baseline": False, "file": row["file"]})
        for verb, target in row["links"]:
            if target.startswith("ADR-") and target not in known:
                continue  # reported by check; kept out so summary, export and queries agree
            edges.append({"source": identifier, "verb": verb, "target": target})
            if not target.startswith("ADR-"):
                documents.add(target)
    return {"root": root, "nodes": nodes, "documents": sorted(documents), "edges": edges,
            "index": index, "problems": problems, "frontmatter": frontmatter, "baseline": baseline}


def check(graph):
    """Each place where the records cannot be read, or the index links, status notes and frontmatter disagree."""
    findings = list(graph["problems"])
    known = {n["id"] for n in graph["nodes"]}
    links = {(s, v, t) for s, row in graph["index"].items() for v, t in row["links"]}
    mismatched = set()
    for identifier, row in sorted(graph["index"].items()):
        for text in row["unread"]:
            findings.append(f"{identifier}: index link not understood: {text!r}")
        for verb, target in row["links"]:
            if target.startswith("ADR-") and target not in known:
                findings.append(f"{identifier}: links to {target}, which no record defines")
        for verb, source in row["notes"]:
            said = sorted(v for s, v, t in links if s == source and t == identifier)
            if verb not in said:
                mismatched.add((source, identifier))
                findings.append(f"{identifier}: status says {PAST_OF[verb]} by {source}, but {source}'s index "
                                f"row says it {', '.join(v.lower() for v in said) or 'does nothing to'} {identifier}")
        fm = graph["frontmatter"].get(identifier)
        if not os.path.exists(os.path.join(graph["root"], row["file"])):
            findings.append(f"{identifier}: index points at {row['file']}, which does not exist")
            continue
        if fm is None:
            findings.append(f"{identifier}: {row['file']} has no frontmatter")
            continue
        if fm.get("amends_unread"):
            findings.append(f"{identifier}: frontmatter amends not understood: {fm['amends_unread']!r}")
            continue
        indexed = {t for v, t in row["links"] if v == "AMENDS"}
        for target in fm["amends"]:
            if target not in indexed:
                other = sorted(v.lower() for v, t in row["links"] if t == target)
                findings.append(f"{identifier}: frontmatter amends {target}, but the index says it "
                                f"{', '.join(other) or 'does nothing to'} {target}")
        for target in sorted(indexed - set(fm["amends"])):
            findings.append(f"{identifier}: index amends {target}, but the frontmatter does not list it")
        if fm.get("status") and fm["status"] != row["status"]:
            findings.append(f"{identifier}: frontmatter status {fm['status']!r}, index status {row['status']!r}")
        if fm.get("date") and fm["date"] != row["date"]:
            findings.append(f"{identifier}: frontmatter date {fm['date']}, index date {row['date']}")
    for source, verb, target in sorted(links):
        if target in graph["index"] and (verb, source) not in graph["index"][target]["notes"] \
                and (source, target) not in mismatched:
            findings.append(f"{target}: {source} {verb.lower()} it, but its status does not say so")
    return findings


def cypher_seed(graph):
    """The graph as one Cypher script with literal values, one statement per line."""
    def lit(v):
        return "null" if v is None else json.dumps(v, ensure_ascii=False)
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
    """Load the graph into a scratch store, then run the statement on it read-only."""
    if not shutil.which("relate"):
        sys.exit("adr_graph: relate is not installed. Install it with: curl -sSfL https://relatedb.ai/install.sh | bash")
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
        # --command takes the statement as its value, so a statement starting with - is never a flag.
        p = subprocess.run(args + ["--command", statement], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        sys.stderr.write(p.stdout + p.stderr)
        sys.exit(p.returncode)
    return [line for line in p.stdout.splitlines() if line.startswith("{")]


def usage(text):
    print("usage: scripts/adr_graph.py " + text, file=sys.stderr)
    return 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd, args = (argv[0], argv[1:]) if argv else ("help", [])
    if cmd in ("help", "-h", "--help"):
        if args:
            return usage("help takes no arguments")
        print(__doc__.split("\n\nSources")[0].strip())
        return 0
    graph = build()
    if cmd in ("changed", "basis"):
        if len(args) != 1:
            return usage(f"{cmd} ADR-NNNN")
        target = norm(args[0].upper())
        if target not in {n["id"] for n in graph["nodes"]}:
            print(f"adr_graph: no decision {target} in the register or the index", file=sys.stderr)
            return 2
        arrow = ("<-[:%s*1..]-(x)" if cmd == "changed" else "-[:%s*1..]->(x)") % LINKS
        statement = (f"MATCH p = (d:Decision {{id: $id}}){arrow} "
                     "RETURN x.id AS id, coalesce(x.title, '') AS title, length(p) AS hops, "
                     "[rel IN relationships(p) | type(rel)] AS via, "
                     "[n IN nodes(p) | n.id] AS chain ORDER BY hops, id")
        for row in run_relate(graph, statement, {"id": target}):
            print(row)
        return 0
    if cmd == "query":
        if len(args) != 1:
            return usage("query 'CYPHER'")
        for row in run_relate(graph, args[0], {}):
            print(row)
        return 0
    if cmd not in ("summary", "check", "export"):
        return usage("changed|basis|summary|check|query|export, or help")
    if args:
        return usage(f"{cmd} takes no arguments")
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
        if findings:
            print(f"adr_graph: {len(findings)} finding(s)", file=sys.stderr)
        else:
            print("adr_graph: the index links, status notes and frontmatter agree")
        return 1 if findings else 0
    if cmd == "export":
        sys.stdout.write(cypher_seed(graph))
        return 0
    return usage("changed|basis|summary|check|query|export, or help")


if __name__ == "__main__":
    sys.exit(main())
