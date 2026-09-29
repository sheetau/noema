"""Reproduce message/scope examples and the partial source alignment, model-free."""
import argparse
from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import Content, Message, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/written-v010.json'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_report():
    documents, roundtrips = {}, {}
    for path in sorted((ROOT / 'examples/v010').glob('*.noema')):
        doc = parse(path.read_text(encoding='utf-8'))
        documents[path.name] = doc
        for notation in ('full', 'compact'):
            text = format_graph(doc, notation)
            if parse(text) != doc:
                raise ValueError('Notation round trip differs')
            for alphabet in ('v1', 'v2'):
                if parse(decode(encode(text, alphabet))) != doc:
                    raise ValueError('Alphabet round trip differs')
        roundtrips[path.name] = True
    basis = read('data/kant-motto-basis-v1.json')
    audit = audit_basis(documents['kant-motto-draft.noema'], basis)
    model = {'individuals': ['reader'], 'situations': ['now', 'later']}
    cases = {}
    for raining in (False, True):
        actual = evaluate_document(documents['conditional-directive.noema'], **model, primitives={
            'aa': lambda s: raining, 'ab': lambda actor, s: False,
            'ac': lambda: 'reader', 'ad': lambda: 'now'})
        expected = [
            {'kind': 'suppose', 'condition_value': raining, 'statements': [
                {'kind': 'perform', 'value': Message('direct', Content(('now', 'later'), (False, False)))}]},
            {'kind': 'ask', 'value': False}]
        if actual != expected:
            raise ValueError('Assumption or directive meaning changed')
        cases['conditional_rain_' + str(raining).lower()] = actual
    for courageous in (False, True):
        seen = []
        def courage(person, goal, scene):
            seen.append(goal)
            return courageous
        expected_message = Message('direct', Content(('now', 'later'), (courageous, courageous)))
        actual = evaluate_document(documents['kant-motto-draft.noema'], **model, primitives={
            'ab': lambda faculty, person, scene: True,
            'ac': lambda person, faculty, act, scene: scene == 'later',
            'ad': lambda guide, person, act, scene: False,
            'al': courage, 'am': lambda message, subject: message == expected_message,
            'an': lambda: 'reader', 'ao': lambda: 'reader'})
        if actual != [{'kind': 'assert', 'value': True}] or not seen or any(
                goal != Content(('now', 'later'), (False, True)) for goal in seen):
            raise ValueError('Motto must mention a directive with the independent goal content')
        cases['motto_courage_' + str(courageous).lower()] = actual

    unit_path = 'artifacts/written-units-v1/kant-1784.json'
    if sha(unit_path) != read('reports/written-units-v1.json')['works']['kant-1784']['units_sha256']:
        raise ValueError('Source unit artifact changed')
    unit = next(u for u in read(unit_path)['units'] if u['id'] == 'kant-1784:u0008')
    alignment = read('data/kant-motto-alignment-v1.json')
    previous = read(alignment['previous_alignment'])
    if alignment['source_unit'] != previous['source_unit'] or alignment['source_unit'] != unit['id']:
        raise ValueError('Alignment source differs')
    if alignment['document'] != basis['document']:
        raise ValueError('Alignment document differs')
    replacements = {s['id']: s for s in alignment['segments']}
    if len(replacements) != len(alignment['segments']) or not set(replacements) <= {s['id'] for s in previous['segments']}:
        raise ValueError('Invalid alignment replacement inventory')
    segments, covered, end = [], set(), 0
    for old in previous['segments']:
        segment = replacements.get(old['id'], old)
        if segment['source'] != old['source'] or unit['text'].count(segment['source']) != 1:
            raise ValueError('Alignment source excerpt changed or ambiguous')
        if segment['id'] in replacements and not set(segment['definitions']) <= set(basis['definitions']):
            raise ValueError('Unknown aligned definition')
        start = unit['text'].index(segment['source'])
        if start < end or segment['status'] not in ('partial', 'pending'):
            raise ValueError('Invalid draft status or overlapping source range')
        end = start + len(segment['source'])
        covered.update(range(start, end))
        segments.append({'id': segment['id'], 'start': start, 'end': end, 'status': segment['status'],
                         'document': alignment['document'] if segment['id'] in replacements else previous['document']})
    if any(i not in covered for i, char in enumerate(unit['text']) if not char.isspace()):
        raise ValueError('Source passage omitted from accounting')
    paths = ['noema/discourse.py', 'noema/finite_semantics.py', 'noema/meaning_basis.py',
             'noema/grammar.py', 'noema/semantics.py', 'noema/language.py', 'noema/script.py',
             'noema/render.py', 'noema/cli.py', 'scripts/check_written_v010.py',
             'data/kant-motto-basis-v1.json', 'data/kant-motto-alignment-v1.json',
             'data/kant-opening-alignment-v1.json', 'reports/written-units-v1.json']
    paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'examples/v010').glob('*.noema'))]
    return {'status': 'partial_semantic_draft', 'edition': '0.10', 'roundtrips': roundtrips,
            'interpretations': cases, 'basis_audit': audit, 'source_unit': unit['id'],
            'source_alignment': segments, 'verified_full_units': 0,
            'all_nonblank_source_characters_accounted_for': True,
            'source_sha256': {p: sha(p) for p in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = json.loads(json.dumps(build_report(), default=lambda value: asdict(value) if is_dataclass(value) else value))
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Written 0.10 verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Written 0.10: examples, interpretations and partial alignment reproduced; no full unit certified')


if __name__ == '__main__':
    main()
