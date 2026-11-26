#!/usr/bin/env python3
"""Check architecture routing against the register and local document links."""
import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTER = ROOT / 'registers/PPC-Discussion-Decision-Traceability.md'
CSV = ROOT / 'registers/PPC-Discussion-Source-Locators.csv'
DRAFT_IDS = ('GRAPH-001', 'DATA-001', 'INT-001', 'EVID-001', 'ANALYTICS-001',
             'UX-001', 'AGENT-001', 'PLATFORM-001', 'VERIFY-001',
             'SCENARIO-001', 'PLAN-001', 'KNOWLEDGE-001')


def ranges(numbers):
    groups = []
    for n in sorted(numbers):
        if groups and n == groups[-1][-1] + 1:
            groups[-1].append(n)
        else:
            groups.append([n])
    return ', '.join('T%d' % g[0] if len(g) == 1 else 'T%d–%d' % (g[0], g[-1])
                     for g in groups)


def routes():
    result = {}
    for line in REGISTER.read_text().splitlines():
        if not re.match(r'^\| T\d', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        match = re.match(r'T(\d+)(?:[–-]T?(\d+))?', cells[0])
        if not match:
            continue
        for n in range(int(match[1]), int(match[2] or match[1]) + 1):
            for document in re.findall(r'\b[A-Z]+-\d{3}\b', cells[3]):
                result.setdefault(document, set()).add(n)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-routing', action='store_true')
    args = parser.parse_args()
    errors = []
    route = routes()
    for docid in DRAFT_IDS:
        matches = list(ROOT.rglob('PPC-' + docid + '_*.md'))
        if len(matches) != 1:
            errors.append('%s: expected one specification, found %d' % (docid, len(matches)))
            continue
        path = matches[0]
        source = path.read_text()
        expected = 'The [exchange register](../registers/PPC-Discussion-Decision-Traceability.md) routes %s to this draft.' % ranges(route[docid])
        actual = re.search(r'The \[exchange register\]\([^)]*\) routes .*? to this draft\.', source)
        if args.write_routing and actual:
            path.write_text(source.replace(actual.group(), expected))
        elif not actual or actual.group() != expected:
            errors.append('%s: routing differs from register; expected %s' % (docid, ranges(route[docid])))
    register_text = REGISTER.read_text()
    for docid in DRAFT_IDS:
        expected = ranges(route[docid])
        row = re.search(r'(^\| \[' + docid + r'\]\([^)]*\) \| )([^|]*?)( → §§[^|]*? \|)', register_text, re.M)
        if not row:
            errors.append('%s: missing crosswalk row' % docid)
        elif args.write_routing:
            register_text = register_text[:row.start(2)] + expected + register_text[row.end(2):]
        elif row.group(2).strip() != expected:
            errors.append('%s: crosswalk differs from register' % docid)
    if args.write_routing:
        REGISTER.write_text(register_text)
    with CSV.open(newline='') as handle:
        for row in csv.DictReader(handle):
            exchange = int(row['exchange'])
            csv_dest = set(re.findall(r'\b[A-Z]+-\d{3}\b', row['destination_documents']))
            register_dest = {name for name, numbers in route.items() if exchange in numbers}
            if csv_dest != register_dest:
                errors.append('CSV exchange T%d differs from register' % exchange)
                break
    for path in ROOT.rglob('*.md'):
        if 'archive' in path.parts:
            continue
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https:', 'http:', 'mailto:', '#')):
                continue
            local = (path.parent / target.split('#')[0]).resolve()
            if not local.exists():
                errors.append('%s: missing link %s' % (path.relative_to(ROOT), target))
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print('Routing, CSV destinations, and local Markdown links: passed')


if __name__ == '__main__':
    main()
