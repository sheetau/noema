"""Check specialized values and non-executing reference to their definitions."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_prescription_mentions import ROOT, PARENT, TARGETS, composed

REPORT = ROOT / 'reports/prescription-mentions-v1.json'
SCENES = ('now', 'future')
DOMAIN = ('person', 'method', 'ability', 'act', 'rule', 'source', 'role')
PARAMS = 'r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] c.r zf[] d.r zg[a a d] c.'
ARGS = 'k za[] k zb[] k zc[] k zd[] k ze[] k zf[] p zg'
ORIGINAL_ARGS = 'k za[] k zb[] k zc[] k zd[] r[p bf] r[p bm] k ze[] k zf[] p zg'


def values(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=2_000_000, memoize_definitions=True, memoize_expressions=True)]


def equivalence_checks():
    queries = PARAMS
    for before, after in TARGETS.items():
        queries += f'q[k {before}[{ORIGINAL_ARGS}]].q[k {after}[{ARGS}]].'
    doc = candidate(composed()[0], queries)
    rows = []
    for adopted, capable, performed, holding, positive in product((False, True), repeat=5):
        model = guarded(doc)
        model.update(za=lambda: 'rule', zb=lambda: 'source', zc=lambda: 'person', zd=lambda: 'role',
            ze=lambda: positive, zf=lambda: 'now', zg=lambda person, role, ctx: holding and (person, role, ctx) == ('person', 'role', 'now'),
            aa=lambda person: person == 'person',
            ae=lambda person, method, start: capable and (person, method, start) == ('person', 'method', 'now'),
            af=lambda person, method, start, end: (person, method, start, end) == ('person', 'method', 'now', 'future'),
            ap=lambda person, method, start, end: (person, method, start, end) == ('person', 'method', 'now', 'future'),
            ab=lambda ability, person, ctx: (ability, person) == ('ability', 'person') and (ctx == 'future' or performed),
            ac=lambda person, ability, act, ctx: (person, ability, act) == ('person', 'ability', 'act') and (ctx == 'future' or performed),
            ad=lambda *args: False,
            rba=lambda rule, source, role, condition, goal, sign, ctx: adopted and (
                rule, source, role, symbol(condition), symbol(goal), sign, ctx) == ('rule', 'source', 'role', 'bf', 'bm', positive, 'now'))
        actual = values(doc, model)
        active = adopted and holding and not capable
        expected = [active, active, active and performed == positive, active and performed == positive,
                    active and performed != positive, active and performed != positive]
        if actual != expected:
            raise ValueError('Specialization changed an applicability/compliance/violation value: ' + repr(actual))
        rows.append(dict(adopted=adopted, capable=capable, performed=performed, holding=holding, positive=positive, values=actual))
    return rows


def mention_checks():
    doc = candidate(composed()[0], 'r za[i[h[a a a a c d h[a a d] c] c]] c.' +
        ''.join(f'q[k za[r[p {name}]]].' for name in TARGETS.values()))
    rows = {}
    for intended in TARGETS.values():
        model = guarded(doc)
        model['za'] = lambda description: symbol(description) == intended
        actual = values(doc, model)
        expected = [name == intended for name in TARGETS.values()]
        if actual != expected:
            raise ValueError('Mention evaluated the rule or confused its derived definitions')
        rows[intended] = actual
    return {'cases': rows, 'all_primitives_except_mention_relation_guarded_against_execution': True}


def build_report():
    text, basis = composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-prescription-mentions-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored prescription mentions differ')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Mention roundtrip differs')
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Previous prescription draft changed')
    paths = [basis['document'], 'data/kant-prescription-mentions-basis-v1.json', PARENT,
        'noema/specialization.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'scripts/compose_prescription_mentions.py', 'scripts/check_prescription_mentions.py']
    return {'status': 'quotable_fixed_prescription_instances_not_new_source_translation',
        'documents': {basis['document']: audit_basis(doc, basis)}, 'equivalence': equivalence_checks(),
        'mentions': mention_checks(), 'derivations': basis['specialization']['derivations'],
        'parent_preserved': True, 'roundtrips': True,
        'alignment': {'segments': [], 'new_source_ranges': False, 'example_rule_not_attributed_to_kant': True},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Prescription mention report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Fixed prescription values agree and their definitions can be mentioned without execution')


if __name__ == '__main__':
    main()
