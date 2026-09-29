"""Finite counterexamples for first-class definitions and the linked Kant draft."""
import argparse
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_kant_v011 import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/written-v011.json'


def check_linked_draft():
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored linked document differs')
    if json.loads((ROOT / 'data/kant-linked-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored linked basis differs')
    doc = parse(text)
    audit = audit_basis(doc, basis)
    if 'an' in audit['definition_dependencies']['primitive_symbols']:
        raise ValueError('Unlinked enlightenment symbol must be absent')
    cases = {}
    for capable in (False, True):
        observed = {}
        def motto(message, property_):
            observed['message_force'] = message.force
            observed['message_content'] = list(message.content.values)
            observed['change_content'] = list(property_('change').values)
            observed['unrelated_object_content'] = list(property_('act').values)
            return True
        predicates = {
            'aa': lambda person: person == 'person',
            'ab': lambda faculty, person, s: faculty == 'faculty' and person == 'person',
            'ac': lambda person, faculty, act, s: (person, faculty, act, s) == ('person', 'faculty', 'act', 'end'),
            'ad': lambda guide, person, act, s: False,
            'ae': lambda person, plan, s: capable and (person, plan, s) == ('person', 'plan', 'end'),
            'af': lambda person, plan, s, outcome: (person, plan, s, outcome) == ('person', 'plan', 'end', 'end'),
            'ag': lambda change, before, after: (change, before, after) == ('change', 'start', 'end'),
            'ah': lambda factor, effect, s: s == 'start' and factor.values == (True, False) and effect.values == (True, not capable),
            'ai': lambda person, s: s == 'end',
            'aj': lambda person, s: s == 'end',
            'ak': lambda person, s: True,
            'al': lambda person, goal, s: False,
            'am': motto, 'ao': lambda: 'person'}
        result = evaluate_document(doc, individuals=('person', 'faculty', 'act', 'plan', 'change'),
                                   situations=('start', 'end'), primitives=predicates, max_steps=2000000)
        expected = {'message_force': 'direct', 'message_content': [False, False],
                    'change_content': [False, capable], 'unrelated_object_content': [False, False]}
        if observed != expected or result != [{'kind': 'assert', 'value': True}]:
            raise ValueError('Linked property or quoted directive changed')
        cases['capable_after_' + str(capable).lower()] = {'observed': observed, 'statements': result}
    return audit, cases


def build_report():
    audit, cases = check_linked_draft()
    paths = sorted((ROOT / 'examples/v011').glob('*.noema'))
    roundtrips = {}
    for path in paths:
        doc = parse(path.read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
                raise ValueError('Function language round trip differs')
        roundtrips[path.name] = True
    arithmetic = parse((ROOT / 'examples/v011/function-composition.noema').read_text(encoding='utf-8'))
    if evaluate_document(arithmetic, individuals=('object',), situations=('now',),
                         primitives={'aa': lambda a, b: a + b}) != [{'kind': 'assert', 'value': True}]:
        raise ValueError('Rational function composition differs')
    files = [p.relative_to(ROOT).as_posix() for p in paths] + [
        'data/kant-linked-basis-v1.json', 'data/kant-opening-basis-v1.json', 'data/kant-motto-basis-v1.json',
        'examples/v09/kant-opening-draft.noema', 'examples/v010/kant-motto-draft.noema',
        'scripts/compose_kant_v011.py', 'scripts/check_written_v011.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'noema/meaning_basis.py',
        'noema/grammar.py', 'noema/semantics.py', 'noema/language.py', 'noema/render.py', 'noema/script.py', 'noema/cli.py']
    return {'status': 'partial_semantic_draft', 'edition': '0.11', 'roundtrips': roundtrips,
            'basis_audit': audit, 'interpretations': cases, 'rational_composition': True,
            'verified_full_units': 0,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Written 0.11 verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Written 0.11: definition references and rational functions reproduced; full source coverage remains incomplete')


if __name__ == '__main__':
    main()
