#!/usr/bin/env python3
"""Check architecture routing against the register and local document links."""
import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTER = ROOT / 'registers/PPC-Discussion-Decision-Traceability.md'
CSV = ROOT / 'registers/PPC-Discussion-Source-Locators.csv'
ROUTED_DRAFT_IDS = ('GRAPH-001', 'DATA-001', 'INT-001', 'EVID-001', 'ANALYTICS-001',
             'UX-001', 'AGENT-001', 'PLATFORM-001', 'VERIFY-001',
             'SCENARIO-001', 'PLAN-001', 'KNOWLEDGE-001')
SPEC_IDS = ('ARCH-000', 'WORLD-001', 'WORLD-002', 'ENG-001', 'OT-001',
            'EDI-001', 'INFO-001') + ROUTED_DRAFT_IDS
INFO = ROOT / '03-enterprise-information/PPC-INFO-001_Enterprise_Ontology_Identity_and_Time.md'
DATA = ROOT / '03-enterprise-information/PPC-DATA-001_Data_Products_KPIs_and_Analytical_Releases.md'


def ranges(numbers):
    groups = []
    for n in sorted(numbers):
        if groups and n == groups[-1][-1] + 1:
            groups[-1].append(n)
        else:
            groups.append([n])
    return ', '.join('T%d' % g[0] if len(g) == 1 else 'T%d–%d' % (g[0], g[-1])
                     for g in groups)


def routes(errors):
    result = {}
    seen = set()
    for line in REGISTER.read_text().splitlines():
        if not re.match(r'^\| T\d', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        match = re.match(r'^T(\d+)(?:[–-]T?(\d+))?(?:\s*·.*)?$', cells[0])
        if not match:
            errors.append('invalid exchange range: ' + cells[0])
            continue
        for n in range(int(match[1]), int(match[2] or match[1]) + 1):
            if n in seen:
                errors.append('duplicate register exchange T%d' % n)
            seen.add(n)
            for document in re.findall(r'\b[A-Z]+-\d{3}\b', cells[3]):
                result.setdefault(document, set()).add(n)
    for n in sorted(set(range(1, 146)) - seen):
        errors.append('missing register exchange T%d' % n)
    for n in sorted(seen - set(range(1, 146))):
        errors.append('unexpected register exchange T%d' % n)
    return result


def anchors(source):
    """GitHub-style heading slugs for local architecture links."""
    found = set()
    counts = {}
    for line in source.splitlines():
        heading = re.match(r'^#{1,6}\s+(.+?)\s*#*\s*$', line)
        if not heading:
            continue
        label = re.sub(r'<[^>]+>', '', heading[1])
        label = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', label).lower()
        slug = re.sub(r'[^\w\- ]', '', label, flags=re.UNICODE).replace(' ', '-')
        suffix = counts.get(slug, 0)
        counts[slug] = suffix + 1
        found.add(slug if not suffix else '%s-%d' % (slug, suffix))
    return found


def fixture_rows(source, header):
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(header))
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith('|'):
            break
        rows.append([cell.strip() for cell in line.strip('|').split('|')])
    return rows


def minute(value):
    hour, minute_value = map(int, value.split(':'))
    return 60 * hour + minute_value


def temporal_fixture(source):
    """Exercise only the synthetic INFO-001 rows, not a PPC runtime reader."""
    publications = fixture_rows(source, '| Publication / ordinal')
    receipts = fixture_rows(source, '| Receipt ID')
    grants = fixture_rows(source, '| Grant ID')
    assert len(publications) == 4 and len(receipts) == 3 and len(grants) == 1

    def select(event, cutoff, rows=publications, delivered=receipts,
               permissions=grants, actor='planner', channel='workspace',
               purpose='maintenance-investigation', restricted=()):
        applicable = [row for row in permissions
                      if row[1] == ' / '.join((actor, channel, purpose))
                      and row[2] == 'OPERATIONS / baseline / slot S'
                      and minute(row[4]) <= minute(cutoff)
                      and minute(row[3].split(',')[0][1:]) <= minute(cutoff)
                      and (row[3].split(', ')[1][:-1] == '∞' or
                           minute(cutoff) < minute(row[3].split(', ')[1][:-1]))]
        if not applicable or any(row[5] == 'DENY' for row in applicable):
            return 'UNRESOLVED'
        eligible = []
        complete = {row[0].split(' / ')[0] for row in rows
                    if not any(other[0].split(' / ')[0] == row[0].split(' / ')[0]
                               and other[1] in restricted for other in rows)}
        for row in rows:
            identity, occupant, interval, recorded, published, predecessor, scope = row
            pub, ordinal = identity.split(' / ')
            if scope != 'baseline / slot S / OPERATIONS' or pub not in complete:
                continue
            if minute(recorded) > minute(cutoff) or minute(published) > minute(cutoff):
                continue
            if not any(r[1] == pub and r[2] == ' / '.join((actor, channel))
                       and minute(published) <= minute(r[3]) <= minute(cutoff)
                       for r in delivered):
                continue
            eligible.append((int(ordinal), pub, occupant, interval))
        if not eligible:
            return 'UNRESOLVED'
        highest = max(row[0] for row in eligible)
        chosen = [row for row in eligible if row[0] == highest]
        matches = [occupant for _, _, occupant, interval in chosen
                   if minute(interval.split(',')[0][1:]) <= minute(event)
                   and (interval.split(', ')[1][:-1] == '∞' or
                        minute(event) < minute(interval.split(', ')[1][:-1]))]
        if len(matches) != 1:
            return 'UNRESOLVED' if not matches else 'NON_UNIQUE'
        return matches[0]

    assert select('10:30', '12:45') == 'A'
    assert select('10:30', '13:00') == 'B'
    assert select('09:59', '13:00') == 'A'
    assert select('10:00', '13:00') == 'B'
    assert select('10:30', '12:45', delivered=[r for r in receipts if r[1] != 'P1']) == 'A'
    assert select('10:30', '12:45', delivered=[r for r in receipts if r[1] not in ('P0', 'P1')]) == 'UNRESOLVED'
    assert select('10:30', '13:00', delivered=[r for r in receipts if r[1] != 'P2']) == 'A'
    assert select('10:30', '13:00', delivered=[r for r in receipts if r[1] != 'P1']) == 'B'
    late_p1 = [[*r[:3], '13:05'] if r[1] == 'P1' else r for r in receipts]
    assert select('10:30', '13:10', delivered=late_p1) == 'B'
    assert select('10:30', '13:00', restricted=('B',)) == 'A'
    assert select('10:30', '13:00', permissions=[]) == 'UNRESOLVED'
    assert select('10:30', '13:00', channel='email') == 'UNRESOLVED'
    assert select('10:30', '13:00', purpose='dispatch') == 'UNRESOLVED'
    assert select('10:30', '13:00', permissions=grants + [[*grants[0][:5], 'DENY']]) == 'UNRESOLVED'
    assert select('10:30', '12:45', permissions=[[grants[0][0], grants[0][1], grants[0][2], '[13:00, ∞)', '08:00', 'ALLOW']]) == 'UNRESOLVED'
    assert select('10:30', '13:00', rows=publications + [publications[-1]]) == 'NON_UNIQUE'


def retraction_fixture(source):
    rows = fixture_rows(source, '| Event ID / kind')
    assert len(rows) == 2
    release, retraction = rows
    assert release[0] == 'L1 / PUBLISHED' and retraction[0] == 'X1 / RETRACTED'
    assert release[1] == retraction[1] == 'L1'

    def visible(cutoff, retraction_receipt=True):
        if not (minute(release[2]) <= minute(release[4]) <= minute(release[5]) <= minute(cutoff)):
            return 'UNRESOLVED'
        if retraction_receipt and minute(retraction[2]) <= minute(retraction[3]) <= minute(retraction[4]) <= minute(retraction[5]) <= minute(cutoff):
            return 'UNRESOLVED'
        return 'L1'

    assert visible('10:30') == 'L1'
    assert visible('11:14') == 'L1'
    assert visible('11:15') == 'UNRESOLVED'
    assert visible('11:15', retraction_receipt=False) == 'L1'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-routing', action='store_true')
    args = parser.parse_args()
    errors = []
    route = routes(errors)
    try:
        temporal_fixture(INFO.read_text())
        retraction_fixture(DATA.read_text())
    except (AssertionError, ValueError, StopIteration) as exc:
        errors.append('publication fixture failed: %s' % exc)
    for docid in SPEC_IDS:
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
    for docid in ROUTED_DRAFT_IDS:
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
    for path in ROOT.rglob('*.md'):
        if 'archive' in path.parts:
            continue
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https:', 'http:', 'mailto:')):
                continue
            filename, _, fragment = target.partition('#')
            local = (path.parent / filename).resolve() if filename else path
            if not local.exists():
                errors.append('%s: missing link %s' % (path.relative_to(ROOT), target))
            elif fragment and local.suffix == '.md' and fragment not in anchors(local.read_text()):
                errors.append('%s: missing anchor %s' % (path.relative_to(ROOT), target))
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print('19 spec routing statements, 12 draft register crosswalks, T1–T145 coverage, CSV destinations, local links and anchors, publication fixtures: passed')


if __name__ == '__main__':
    main()
