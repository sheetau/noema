"""Audit partial draft associations without treating them as semantic coverage."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from noema.grammar import parse

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/written-progress-v1.json'
WORKS = ('kant-1784', 'einstein-1905')
ALIGNMENT_KEYS = ('source_alignment', 'source_ranges', 'alignment')
MATH_MARKER = re.compile(r'\[(M\d{4})\]')
CHILD_KEYS = ('segments', 'selection', 'selections', 'fragments', 'units')
PENDING = {'pending', 'unwritten', 'not_yet_translated'}


def digest(data):
    return sha256(data).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def merge_ranges(ranges):
    merged = []
    for start, end in sorted(set(tuple(pair) for pair in ranges)):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def collect_alignment(report, units, known_symbols, report_name):
    """Only walk declared alignment structures, never arbitrary mentions of IDs."""
    records = []
    default_unit = report.get('source_unit')
    if default_unit:
        if default_unit not in units:
            raise ValueError('Unknown source unit: ' + default_unit)
        expected = report.get('source_text_sha256')
        if expected and expected != units[default_unit]['text_sha256']:
            raise ValueError('Root source hash differs: ' + report_name)

    def walk(node, unit_id=None, status=None, location='$'):
        if isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, unit_id, status, location + '/' + str(i))
            return
        if not isinstance(node, dict):
            raise ValueError('Unexpected alignment structure: ' + location)
        explicit_unit = node.get('unit', node.get('source_unit'))
        unit_id = explicit_unit or unit_id
        status = node.get('status', status)
        if status in PENDING:
            return
        if unit_id and unit_id not in units:
            raise ValueError('Unknown alignment unit: ' + unit_id)
        if explicit_unit:
            for key in ('unit_sha256', 'source_sha256', 'text_sha256', 'sha256'):
                value = node.get(key)
                if isinstance(value, str) and value != units[unit_id]['text_sha256']:
                    raise ValueError('Alignment unit hash differs: ' + location)
        partial = isinstance(status, str) and ('partial' in status or status == 'explicit_interpretive_annotation')
        # Some historical reports have no status on the enclosing object; its
        # children carry the actual statuses. Never infer coverage from a parent.
        span = node.get('range')
        if 'start' in node or 'end' in node:
            if 'start' not in node or 'end' not in node:
                raise ValueError('Incomplete source range: ' + location)
            span = [node['start'], node['end']]
        math_id = node.get('math_id')
        references = node.get('definitions', [])
        if isinstance(references, dict):
            references = []  # Named roles in a summary are not a symbol list.
        if 'definition' in node:
            references = [*references, node['definition']]
        if not isinstance(references, list) or any(not isinstance(s, str) for s in references):
            raise ValueError('Malformed definition references: ' + location)
        if partial and unit_id and (span is not None or math_id or references):
            if any(name not in known_symbols for name in references):
                raise ValueError('Unknown Noema definition at ' + location)
            unit = units[unit_id]
            if unit['kind'] == 'editorial':
                raise ValueError('Editorial material is not author coverage')
            if span is not None:
                if not (isinstance(span, list) and len(span) == 2 and all(type(x) is int for x in span)
                        and 0 <= span[0] < span[1] <= len(unit['text'])):
                    raise ValueError('Invalid source range: ' + location)
                excerpt = unit['text'][span[0]:span[1]]
                for key in ('source', 'text'):
                    if key in node and node[key] != excerpt:
                        raise ValueError('Source excerpt differs: ' + location)
                if not explicit_unit and 'text_sha256' in node and node['text_sha256'] != digest(excerpt.encode('utf-8')):
                    raise ValueError('Source excerpt hash differs: ' + location)
            if math_id and math_id not in unit['math_ids']:
                raise ValueError('Math object is not part of this source unit')
            records.append({'report': report_name, 'pointer': location, 'unit': unit_id,
                'status': 'partial', 'source_status': status, 'range': span, 'math_id': math_id,
                'math_sha256': node.get('math_sha256'), 'definitions': references})
        elif status and not partial and any(k in node for k in ('start', 'range', 'math_id', 'definitions', 'definition')):
            raise ValueError('Unsupported alignment status; review it explicitly: ' + str(status))
        for key in CHILD_KEYS:
            if key in node:
                walk(node[key], unit_id, status, location + '/' + key)

    for key in ALIGNMENT_KEYS:
        if key in report:
            walk(report[key], default_unit, None, '/' + key)
    return records


def summarize(units, math_objects, records):
    works = {}
    for work in WORKS:
        author_units = [u for u in units.values() if u['id'].startswith(work + ':') and u['kind'] != 'editorial']
        by_unit = []
        touched_math = set()
        text_total = text_assigned = 0
        for unit in author_units:
            associated = [r for r in records if r['unit'] == unit['id']]
            ranges = merge_ranges(r['range'] for r in associated if r['range'] is not None)
            markers = list(MATH_MARKER.finditer(unit['text']))
            excluded = {i for match in markers for i in range(match.start(), match.end())}
            prose = {i for i, char in enumerate(unit['text']) if not char.isspace() and i not in excluded}
            assigned = {i for start, end in ranges for i in range(start, end)}
            math_ids = {r['math_id'] for r in associated if r['math_id']}
            math_ids.update(match.group(1) for match in markers if all(i in assigned for i in range(match.start(), match.end())))
            for math_id in math_ids:
                if (work, math_id) not in math_objects:
                    raise ValueError('Unknown math object in a source range')
                touched_math.add(math_id)
            text_total += len(prose)
            text_assigned += len(prose & assigned)
            by_unit.append({'unit': unit['id'], 'kind': unit['kind'], 'has_partial_draft': bool(associated),
                'explicit_ranges': ranges, 'nonblank_text_characters': len(prose),
                'nonblank_text_characters_in_partial_ranges': len(prose & assigned),
                'math_objects_with_partial_associations': sorted(math_ids),
                'reports': sorted({r['report'] for r in associated}),
                'has_association_without_text_range': any(r['range'] is None for r in associated)})
        touched = sum(u['has_partial_draft'] for u in by_unit)
        math_total = sum(key[0] == work for key in math_objects)
        works[work] = {'author_unit_count': len(author_units), 'units_with_partial_drafts': touched,
            'unit_touch_percent': round(100 * touched / len(author_units), 2),
            'nonblank_text_characters': text_total, 'text_characters_in_explicit_partial_ranges': text_assigned,
            'explicit_text_range_percent': round(100 * text_assigned / text_total, 2) if text_total else None,
            'math_object_count': math_total, 'math_objects_with_partial_associations': len(touched_math),
            'math_object_touch_percent': round(100 * len(touched_math) / math_total, 2) if math_total else None,
            'verified_semantic_units': 0, 'verified_semantic_percent': 0.0, 'units': by_unit}
    return works


def build_report(root=ROOT):
    source_hashes, units, math_objects = {}, {}, {}
    source_hashes['scripts/audit_written_progress.py'] = digest((root / 'scripts/audit_written_progress.py').read_bytes())
    inventory = load_json(root / 'reports/written-units-v1.json')
    source_hashes['reports/written-units-v1.json'] = digest((root / 'reports/written-units-v1.json').read_bytes())
    for work in WORKS:
        name = 'artifacts/written-units-v1/' + work + '.json'
        artifact = load_json(root / name)
        source_hashes[name] = digest((root / name).read_bytes())
        pinned = {u['id']: u for u in inventory['works'][work]['inventory']}
        if len(pinned) != len(inventory['works'][work]['inventory']):
            raise ValueError('Duplicate source inventory unit')
        for unit in artifact['units']:
            if unit['id'] in units or unit['id'] not in pinned:
                raise ValueError('Duplicate or unknown source unit: ' + unit['id'])
            if digest(unit['text'].encode('utf-8')) != unit['text_sha256'] or pinned[unit['id']]['text_sha256'] != unit['text_sha256']:
                raise ValueError('Inventory source hash differs: ' + unit['id'])
            if any(unit[key] != pinned[unit['id']][key] for key in ('kind', 'math_ids')):
                raise ValueError('Inventory source classification differs: ' + unit['id'])
            units[unit['id']] = unit
        if set(pinned) != {u['id'] for u in artifact['units']}:
            raise ValueError('Source inventory membership differs')
        for item in artifact['math']:
            if (work, item['id']) in math_objects:
                raise ValueError('Duplicate math object')
            if digest(item['mathml'].encode('utf-8')) != item['sha256']:
                raise ValueError('MathML hash differs')
            math_objects[work, item['id']] = item
        for unit in artifact['units']:
            if any((work, item) not in math_objects for item in unit['math_ids']):
                raise ValueError('Unknown math object in source inventory')
    records, documents, inspected = [], {}, []
    for path in sorted((root / 'reports').glob('*.json')):
        report = load_json(path)
        if not isinstance(report, dict) or not any(key in report for key in ALIGNMENT_KEYS):
            continue
        hashes = report.get('source_sha256', {})
        if not isinstance(hashes, dict):
            raise ValueError('Alignment report lacks input hashes: ' + path.name)
        noema_files = {name: value for name, value in hashes.items() if name.endswith('.noema')}
        if not noema_files:
            raise ValueError('Alignment report lacks a pinned Noema document: ' + path.name)
        known_symbols = set()
        for name, expected in noema_files.items():
            raw = (root / name).read_bytes()
            if digest(raw) != expected:
                raise ValueError('Historical Noema document changed: ' + name)
            if name not in documents:
                documents[name] = parse(raw.decode('utf-8'))
            known_symbols.update(d['name'] for d in documents[name]['declarations'])
            source_hashes[name] = digest(raw)
        counts = report.get('verified_full_units', 0)
        if isinstance(counts, dict):
            counts = sum(counts.values())
        if counts != 0:
            raise ValueError('Positive completion count requires a unit-level semantic review protocol')
        name = path.relative_to(root).as_posix()
        found = collect_alignment(report, units, known_symbols, name)
        for item in found:
            if item['math_id'] and item['math_sha256']:
                if math_objects[item['unit'].split(':')[0], item['math_id']]['sha256'] != item['math_sha256']:
                    raise ValueError('Alignment math hash differs: ' + name)
        records.extend(found)
        inspected.append(name)
        source_hashes[name] = digest(path.read_bytes())
    return {'status': 'audited_partial_draft_inventory_not_expression_rate',
        'method': {'deduplicate': 'union of explicit source ranges and unique source unit/math IDs',
            'exclude': ['editorial units', 'pending/unwritten ranges', 'mere mentions of source IDs', 'math placeholders from prose counts'],
            'text_metric_limit': 'Only explicitly bounded ranges; associations without ranges do not count as whole text.',
            'semantic_metric_limit': 'No unit-level semantic completion review is currently recorded. Tests and draft associations do not certify equivalence.',
            'universal_expression_rate': None},
        'works': summarize(units, math_objects, records), 'evidence_records': records,
        'inspected_alignment_reports': inspected, 'parsed_noema_documents': len(documents),
        'source_sha256': source_hashes}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        if result != load_json(REPORT):
            raise ValueError('Written progress snapshot differs; inspect new evidence before updating it')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for work, row in result['works'].items():
        print(work + ': partial associations ' + str(row['units_with_partial_drafts']) + '/' + str(row['author_unit_count'])
            + '; explicit text ranges ' + str(row['explicit_text_range_percent']) + '%; semantically verified 0')


if __name__ == '__main__':
    main()
