"""Countermodels for the composed opening definitions, not a translator."""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from noema.grammar import parse, format_graph
from noema.script import encode, decode
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis

DOCUMENT = Path('examples/v09/kant-opening-draft.noema')
BASIS = Path('data/kant-opening-basis-v1.json')
ALIGNMENT = Path('data/kant-opening-alignment-v1.json')
REPORT = Path('reports/kant-opening-v1.json')
INDIVIDUALS = ('person', 'other', 'own', 'borrowed', 'act', 'another', 'plan', 'change')
SITUATIONS = ('start', 'end', 'faculty', 'resolve', 'courage')


def model(*, faculty='own', performance=True, guidance=None, capable_after=True,
          motivation_cause=True, faculty_cause=False, transition=True, adequate_faculty_start=True):
    """An explicitly stipulated interpretation; not facts inferred from the source."""
    motivation = tuple(s == 'start' for s in SITUATIONS)
    lack_faculty = tuple(s == 'faculty' or s == 'start' and not adequate_faculty_start for s in SITUATIONS)
    return {
        'aa': lambda person: person in ('person', 'other'),
        'ab': lambda f, person, s: f == 'own' and person == 'person',
        'ac': lambda person, f, act, s: performance and person == 'person' and f == faculty and act == 'act' and s == 'end',
        'ad': lambda guide, person, act, s: person == 'person' and s == 'end' and (guide, act) == guidance,
        'ae': lambda person, plan, s: capable_after and person == 'person' and plan == 'plan' and s == 'end',
        'af': lambda person, plan, s, out: person == 'person' and plan == 'plan' and s == out == 'end',
        'ag': lambda change, before, after: transition and change == 'change' and before == 'start' and after == 'end',
        'ah': lambda factor, effect, s: s == 'start' and effect.values[0]
                and (motivation_cause and factor.values == motivation or faculty_cause and factor.values == lack_faculty),
        'ai': lambda person, s: s not in ('start', 'resolve'),
        'aj': lambda person, s: s not in ('start', 'courage'),
        'ak': lambda person, s: s != 'faculty' and (s != 'start' or adequate_faculty_start),
    }


def query(document, symbol, arguments, primitives, *, evaluate_at=None):
    """Ground only test queries with declared constants; leave the draft intact."""
    doc, mapping, args = deepcopy(document), dict(primitives), []
    for i, (sort, value) in enumerate(arguments):
        name = 'z' + chr(ord('a') + i)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        mapping[name] = lambda value=value: value
        args.append({'kind': 'call', 'symbol': name, 'arguments': []})
    body = {'kind': 'call', 'symbol': symbol, 'arguments': args}
    if evaluate_at is not None:
        doc['declarations'].append({'kind': 'primitive', 'name': 'zz', 'parameters': [], 'result': 'situation'})
        mapping['zz'] = lambda: evaluate_at
        body = {'kind': 'evaluate', 'content': body, 'situation': {'kind': 'call', 'symbol': 'zz', 'arguments': []}}
    doc['statements'] = [{'kind': 'ask', 'body': body}]
    return evaluate_document(doc, individuals=INDIVIDUALS, situations=SITUATIONS,
                             primitives=mapping, max_steps=2000000)[0]['value']


def run_checks():
    doc = parse(DOCUMENT.read_text(encoding='utf-8'))
    basis = json.loads(BASIS.read_text(encoding='utf-8'))
    audit = audit_basis(doc, basis)
    checks = {}

    def check(label, symbol, arguments, expected, *, evaluate_at=None, **kwargs):
        actual = query(doc, symbol, arguments, model(**kwargs), evaluate_at=evaluate_at)
        if actual != expected:
            raise ValueError('Countermodel failed: ' + label)
        checks[label] = {'symbol': symbol, 'arguments': arguments, 'interpretation_changes': kwargs,
                         'evaluate_at': evaluate_at, 'expected': expected, 'actual': actual}

    person = [('individual', 'person')]
    for label, kwargs, expected in (
        ('own_unguided', {}, True), ('borrowed_faculty', {'faculty': 'borrowed'}, False),
        ('owned_but_unused', {'performance': False}, False),
        ('other_guides_this_act', {'guidance': ('other', 'act')}, False),
        ('other_guides_another_act', {'guidance': ('other', 'another')}, True),
        ('self_guidance', {'guidance': ('person', 'act')}, True),
    ):
        check(label, 'bb', person, expected, evaluate_at='end', **kwargs)
    check('not_performing_now', 'bb', person, False, evaluate_at='start')
    at_start = person + [('situation', 'start')]
    check('self_incurred', 'bd', at_start, True)
    check('cooccurring_deficits_without_causal_attribution', 'bd', at_start, False, motivation_cause=False)
    check('also_attributed_to_faculty_deficit', 'bd', at_start, False, faculty_cause=True)
    check('faculty_deficit_present_but_not_explanatory_cause', 'bd', at_start, True, adequate_faculty_start=False)
    change = person + [('individual', 'change'), ('situation', 'start'), ('situation', 'end')]
    check('exit_from_immaturity', 'be', change, True)
    check('blame_disappears_but_inability_remains', 'be', change, False, capable_after=False)
    check('inability_remains_after', 'bc', person + [('situation', 'end')], True, capable_after=False)
    check('self_incurred_classification_no_longer_applies', 'bd', person + [('situation', 'end')], False, capable_after=False)
    check('unrelated_before_and_after', 'be', change, False, transition=False)
    check('reversed_transition', 'be', person + [('individual', 'change'), ('situation', 'end'), ('situation', 'start')], False)
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
            raise ValueError('Draft round trip failed')
    return audit, checks


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    audit, checks = run_checks()
    source_path = Path('artifacts/written-units-v1/kant-1784.json')
    inventory = json.loads(Path('reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source units artifact changed')
    source = json.loads(source_path.read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0008')
    alignment = json.loads(ALIGNMENT.read_text(encoding='utf-8'))
    if alignment['source_unit'] != unit['id'] or alignment['document'] != DOCUMENT.as_posix():
        raise ValueError('Alignment source or document differs')
    covered, ranges, previous = set(), [], 0
    definitions = set(json.loads(BASIS.read_text(encoding='utf-8'))['definitions'])
    for segment in alignment['segments']:
        excerpt = segment['source']
        if not excerpt or unit['text'].count(excerpt) != 1:
            raise ValueError('Source alignment excerpt missing or ambiguous')
        start = unit['text'].index(excerpt)
        end = start + len(excerpt)
        if start < previous or not set(segment['definitions']) <= definitions:
            raise ValueError('Overlapping alignment or missing definition')
        if segment['status'] not in ('partial', 'pending'):
            raise ValueError('This draft does not establish full semantic equivalence')
        covered.update(range(start, end))
        previous = end
        ranges.append({'id': segment['id'], 'start': start, 'end': end, 'status': segment['status'],
                       'definitions': segment['definitions']})
    if any(i not in covered for i, char in enumerate(unit['text']) if not char.isspace()):
        raise ValueError('Unaccounted source passage')
    paths = [DOCUMENT, BASIS, ALIGNMENT, Path(__file__), Path('noema/discourse.py'), Path('noema/finite_semantics.py'),
             Path('noema/meaning_basis.py'), Path('reports/written-units-v1.json')]
    report = {'status': 'partial_semantic_draft', 'source_unit': unit['id'], 'source_text_sha256': unit['text_sha256'],
              'basis_audit': audit, 'countermodels': checks, 'roundtrip': True, 'verified_full_units': 0,
              'source_alignment': ranges, 'all_nonblank_source_characters_accounted_for': True,
              'source_sha256': {str(p.relative_to(Path.cwd()) if p.is_absolute() else p).replace('\\', '/'):
                                hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    # Serialize tuples as JSON arrays before comparing a stored report.
    report = json.loads(json.dumps(report))
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Kant draft verification differs')
        print(f'Kant draft: all {len(checks)} countermodels, basis and round trips reproduced')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(f'Kant draft: {len(checks)} countermodels passed; full source coverage remains incomplete')


if __name__ == '__main__':
    main()
