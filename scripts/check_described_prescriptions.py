"""Separate adopted rule schemas, applicability, compliance and violations."""
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
from scripts.compose_described_prescriptions import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/described-prescriptions-v1.json'
SCENES = ('now', 'other')
DOMAIN = ('rule', 'second', 'source', 'person', 'role', 'other')
EXTRA = '''
r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.r zf[a d] c.r zg[a d] c.r zh[a a d] c.r zi[] c.
d zj[person a] e[b scene[k zf[v person v scene]]].
d zk[person a] e[b scene[k zg[v person v scene]]].
d zl[person a] e[k zk[v person]].d zm[person a] e[k zj[v person]].
'''
ARGS = 'k za[] k zb[] k zc[] k zd[] r[p zj] r[p zk] k zi[] k ze[] p zh'
RECORD = 'k rba[k za[] k zb[] k zd[] r[p zj] r[p zk] k zi[] k ze[]]'
QUERIES = 'q[' + RECORD + '].' + ''.join('q[k ' + name + '[' + ARGS + ']].' for name in ('rbb', 'rbc', 'rbd'))


def values(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=500_000, memoize_definitions=True)]


def model_for(doc, adopted=True, holding=True, condition=True, goal=True, positive=True, variant='baseline'):
    model = guarded(doc)
    expected = ['rule', 'source', 'role', 'zj', 'zk', positive, 'now']
    wrong = {'rule': 0, 'source': 1, 'role': 2, 'condition': 3, 'goal': 4, 'polarity': 5, 'context': 6}
    if variant in wrong:
        expected[wrong[variant]] = not positive if variant == 'polarity' else 'other'
    model.update(za=lambda: 'rule', zb=lambda: 'source', zc=lambda: 'person', zd=lambda: 'role', ze=lambda: 'now',
        zi=lambda: positive,
        zf=lambda person, point: condition and (person, point) == ('person', 'now'),
        zg=lambda person, point: goal and (person, point) == ('person', 'now'),
        zh=lambda person, role, point: holding and (person, role, point) == (
            'other' if variant == 'holder' else 'person', 'other' if variant == 'held_role' else 'role', 'now'),
        rba=lambda rule, source, role, cond, target, sign, point: adopted and [
            rule, source, role, symbol(cond), symbol(target), sign, point] == expected)
    return {key: fn for key, fn in model.items() if key in guarded(doc)}


def truth_checks():
    doc = parse(generic_composed()[0] + EXTRA + QUERIES)
    rows = []
    for adopted, holding, condition, goal, positive in product((False, True), repeat=5):
        actual = values(doc, model_for(doc, adopted, holding, condition, goal, positive))
        active = adopted and holding and condition
        if actual != [adopted, active, active and goal == positive, active and goal != positive]:
            raise ValueError('Rule existence, applicability or fulfillment was conflated')
        rows.append(dict(adopted=adopted, holding=holding, condition=condition, goal=goal, positive=positive, result=actual))
    return rows


def binding_checks():
    doc = candidate(source_composed()[0], EXTRA + QUERIES)
    rows = {}
    for variant in ('baseline', 'rule', 'source', 'role', 'condition', 'goal', 'polarity', 'context', 'holder', 'held_role'):
        actual = values(doc, model_for(doc, variant=variant))
        expected = [variant in ('baseline', 'holder', 'held_role'), variant == 'baseline', variant == 'baseline', False]
        if actual != expected:
            raise ValueError('Prescription binding changed: ' + variant)
        rows[variant] = actual
    return rows


def description_checks():
    doc = parse(generic_composed()[0] + EXTRA + '''
q[e[k zk[k zc[]]][k zl[k zc[]]]].q[e[k zj[k zc[]]][k zm[k zc[]]]].
q[k rba[k za[] k zb[] k zd[] r[p zj] r[p zk] k zi[] k ze[]]].
q[k rba[k za[] k zb[] k zd[] r[p zm] r[p zk] k zi[] k ze[]]].
q[k rba[k za[] k zb[] k zd[] r[p zj] r[p zl] k zi[] k ze[]]].
''')
    rows = []
    for condition, goal in product((False, True), repeat=2):
        actual = values(doc, model_for(doc, condition=condition, goal=goal))
        if actual != [True, True, True, False, False]:
            raise ValueError('Equal content profiles replaced an adopted description')
        rows.append(dict(condition=condition, goal=goal, result=actual))
    return rows


def conflicting_checks():
    truth, false = 'e[k za[]][k za[]]', 'u[e[k za[]][k za[]]]'
    text = generic_composed()[0] + EXTRA + 'r zn[] a.'
    for rule, positive in (('za', truth), ('zn', false)):
        args = f'k {rule}[] k zb[] k zc[] k zd[] r[p zj] r[p zk] {positive} k ze[] p zh'
        text += ''.join('q[k ' + name + '[' + args + ']].' for name in ('rbb', 'rbc', 'rbd'))
    doc = parse(text)
    rows = []
    for goal in (False, True):
        model = model_for(doc, goal=goal)
        model['zn'] = lambda: 'second'
        model['rba'] = lambda rule, source, role, cond, target, sign, point: (
            source, role, symbol(cond), symbol(target), point) == ('source', 'role', 'zj', 'zk', 'now') and (
                rule == 'rule' and sign or rule == 'second' and not sign)
        actual = values(doc, model)
        if actual != [True, goal, not goal, True, not goal, goal]:
            raise ValueError('Conflicting norms asserted both goal and its negation as facts')
        rows.append(dict(goal=goal, result=actual))
    return rows


def limits_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k hd2[k za[]]][k zb[]]].')
    model = guarded(doc)
    model.update(za=lambda: 'rule', zb=lambda: 'now')
    try:
        values(doc, model)
    except ValueError as exc:
        if 'Cannot finitely quantify the description domain' not in str(exc):
            raise
        refused = str(exc)
    else:
        raise ValueError('All descriptions were replaced with a finite sample')
    parse(generic_composed()[0] + 'q[e[r[p rbe]][r[p rbe]]].')
    try:
        parse(generic_composed()[0] + 'q[e[r[p rbb]][r[p rbb]]].')
    except ValueError as exc:
        if 'disquot' not in str(exc).lower():
            raise
        quote_refused = str(exc)
    else:
        raise ValueError('Transitive disquotation was silently made quotable')
    return {'unbounded_description_quantification_refused': refused,
        'rule_schema_classification_can_be_mentioned_without_execution': True,
        'quoting_applicability_with_disquotation_refused': quote_refused}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0010')
    if hashlib.sha256(unit['text'].encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Third paragraph changed')
    start = unit['text'].index('Satzungen')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start + len('Satzungen'),
        'source': 'Satzungen', 'definitions': ['rbe', 'hd2'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False, 'word_meaning_not_complete': True,
        'remaining': ['fixed wording and institution of norms', 'binding force and scope', 'Formeln',
            'mechanical instruments', 'use and misuse of natural gifts', 'fetters metaphor and enduring immaturity']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'described-prescriptions'), (source_composed, 'kant-described-prescriptions')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored prescription differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Prescription roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['statements'] != parent['statements'] or doc['declarations'][:len(parent['declarations'])] != parent['declarations']:
        raise ValueError('Linked Kant parent changed')
    paths = list(documents) + [PARENT, 'data/described-prescriptions-basis-v1.json', 'data/kant-described-prescriptions-basis-v1.json',
        'scripts/compose_described_prescriptions.py', 'scripts/check_described_prescriptions.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return {'status': 'partial_described_conditional_prescriptions', 'documents': documents,
        'truth': truth_checks(), 'binding': binding_checks(), 'descriptions': description_checks(),
        'conflicting': conflicting_checks(), 'limits': limits_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Prescription report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Adopted syntax, role and condition, compliance and conflicting norms distinguished')


if __name__ == '__main__':
    main()
