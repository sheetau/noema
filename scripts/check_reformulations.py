"""Countermodels for reformulation direction and bound use participants."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_reformulations import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/reformulations-v1.json'
SCENES = ('now', 'other')
DOMAIN = ('person', 'faculty', 'act', 'author', 'node', 'other')


def values(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=500_000, memoize_definitions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[] a.r zb[] a.r zc[] d.r zd[a a a] e.r ze[a a a] e.
q[t[k zd[k za[] k za[] k za[]]][k zc[]]].q[t[k ze[k za[] k za[] k za[]]][k zc[]]].
q[k rbg[k za[] k zb[] r[p zd] r[p ze] k zc[]]].
q[k rbg[k za[] k zb[] r[p ze] r[p zd] k zc[]]].
q[k rbg[k za[] k zb[] r[p zd] r[p zd] k zc[]]].
''')
    rows = []
    for first, second, adopted in product((False, True), repeat=3):
        model = {'za': lambda: 'node', 'zb': lambda: 'author', 'zc': lambda: 'now',
            'zd': lambda *args: Content(SCENES, (first, False)), 'ze': lambda *args: Content(SCENES, (second, False)),
            'rbf': lambda node, author, earlier, replacement, ctx: adopted and (
                node, author, symbol(earlier), symbol(replacement), ctx) == ('node', 'author', 'zd', 'ze', 'now')}
        actual = values(doc, model)
        if actual != [first, second, adopted, False, False]:
            raise ValueError('Reformulation was confused with negation or co-occurrence')
        rows.append(dict(first=first, second=second, adopted=adopted, result=actual))
    # Repeating the same description is not this form of replacement, even
    # when the external relation would label every pair a correction.
    model['rbf'] = lambda *args: True
    if values(doc, model)[-1]:
        raise ValueError('Identical-description repetition became replacement')
    return rows


QUERIES = '''
r za[] a.r zb[] a.r zc[] a.r zd[] d.
q[t[k hm2[k za[] k zb[] k zc[]]][k zd[]]].q[t[k hn2[k za[] k zb[] k zc[]]][k zd[]]].
'''


def source_model(doc, natural=True, used=True, rational=True, misuse=True, variant='baseline'):
    model = guarded(doc)
    model.update(za=lambda: 'person', zb=lambda: 'faculty', zc=lambda: 'act', zd=lambda: 'now',
        hh2=lambda faculty, person, ctx: natural and (faculty, person, ctx) == (
            'other' if variant == 'different_owned_faculty' else 'faculty',
            'other' if variant == 'different_owner' else 'person', 'now'),
        hi2=lambda person, faculty, act, ctx: used and (person, faculty, act, ctx) == (
            'other' if variant == 'different_user' else 'person',
            'other' if variant == 'different_used_faculty' else 'faculty',
            'other' if variant == 'different_use_act' else 'act', 'now'),
        hj2=lambda act, positive, ctx: (rational if positive else misuse) and (act, ctx) == (
            'other' if variant == 'different_assessed_act' else 'act',
            'other' if variant == 'different_assessment_context' else 'now'))
    return {name: fn for name, fn in model.items() if name in guarded(doc)}


def usage_checks():
    doc = candidate(source_composed()[0], QUERIES)
    rows = []
    for natural, used, rational, misuse in product((False, True), repeat=4):
        actual = values(doc, source_model(doc, natural, used, rational, misuse))
        if actual != [natural and used and rational, natural and used and misuse]:
            raise ValueError('Misuse was treated as absence of rational use or actual use')
        rows.append(dict(natural=natural, used=used, rational=rational, misuse=misuse, result=actual))
    return rows


def binding_checks():
    doc = candidate(source_composed()[0], QUERIES)
    rows = {}
    for variant in ('baseline', 'different_owner', 'different_owned_faculty', 'different_user',
            'different_used_faculty', 'different_use_act', 'different_assessed_act', 'different_assessment_context'):
        actual = values(doc, source_model(doc, variant=variant))
        if actual != [variant == 'baseline', variant == 'baseline']:
            raise ValueError('Actor, faculty, use and assessment were cross-bound')
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'node', 'author', 'earlier', 'replacement', 'context', 'reverse'):
        model = guarded(doc)
        expected = ['node', 'author', 'hm2', 'hn2', 'now']
        if variant in ('node', 'author', 'earlier', 'replacement', 'context'):
            expected[('node', 'author', 'earlier', 'replacement', 'context').index(variant)] = 'other'
        elif variant == 'reverse':
            expected[2:4] = ['hn2', 'hm2']
        model.update(hk2=lambda: 'node', wa=lambda: 'author', wh=lambda: 'now',
            rbf=lambda node, author, earlier, replacement, ctx: [
                node, author, symbol(earlier), symbol(replacement), ctx] == expected)
        actual = values(doc, model)
        if actual != [variant == 'baseline']:
            raise ValueError('Authored reformulation identity or direction changed')
        rows[variant] = actual
    return {'cases': rows, 'use_and_appraisal_primitives_never_executed': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(u for u in json.loads(path.read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0010')
    if hashlib.sha256(unit['text'].encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Reformulation source changed')
    text = unit['text']
    start = text.index('eines vernünftigen Gebrauchs')
    end = text.index(', sind die Fußschellen')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end,
        'source': text[start:end], 'definitions': ['hm2', 'hn2', 'ho2'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False, 'remaining': ['grounding of natural faculties', 'rationality and misuse criteria',
            'mechanical instruments and their purpose', 'fetters metaphor and enduring immaturity']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'reformulations'), (source_composed, 'kant-reformulations')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored reformulation differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Reformulation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Earlier Kant content changed')
    paths = list(documents) + [PARENT, 'data/reformulations-basis-v1.json', 'data/kant-reformulations-basis-v1.json',
        'scripts/compose_reformulations.py', 'scripts/check_reformulations.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return {'status': 'partial_authored_reformulation_of_faculty_use', 'documents': documents,
        'generic': generic_checks(), 'usage': usage_checks(), 'bindings': binding_checks(), 'attribution': attribution_checks(),
        'alignment': alignment(), 'reading_review': {'comparison_url': 'https://korpora.org/kant/aa08/036.html',
            'location': 'AA VIII 36, lines 8–10', 'method': '固定版と電子本文の対象節を確認。原刊画像の照合ではない。',
            'interpretation': 'oder vielmehrを方向を持つ表現修正として読む。真偽の反転を補わない。'},
        'roundtrips': True, 'parent_preserved': True, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Reformulation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Reformulation direction, participant bindings and non-execution checked')


if __name__ == '__main__':
    main()
