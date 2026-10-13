"""Check formulation identity, actual use and specifically bound examination."""
import argparse
from functools import lru_cache
import hashlib
from itertools import product
import json

from noema.description_templates import is_description_instance
from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_described_routines import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/described-routines-v1.json'
DOMAIN = ('person', 'form', 'act', 'faculty', 'judgment', 'other')
SCENES = ('now', 'other')
PARAMS = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a] e.r zg[] a.d zh[x a] e[k zf[v x]].r zi[] a.
r zl[a i[h[a] e] d] c.r zm[a a a d] c.r zn[a i[e] a d] c.
r zo[a a d] c.r zp[a a d] c.r zq[a a d] c.
'''
ARGS = 'k za[] k zb[] k zc[] r[p zf] r[k zg[]] r[c[p zf][k zg[]]] k ze[]'
INSTANCE = {'kind': 'apply', 'function': {'kind': 'function_ref', 'symbol': 'zf'},
    'arguments': [{'kind': 'call', 'symbol': 'zg', 'arguments': []}]}


def values(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=1_000_000, memoize_definitions=True)]


def matcher(doc):
    @lru_cache(maxsize=128)
    def checked(pattern, argument, instance):
        return is_description_instance(doc, {'kind': 'quote', 'body': json.loads(pattern)},
            [{'kind': 'quote', 'body': json.loads(argument)}], {'kind': 'quote', 'body': json.loads(instance)})
    return lambda pattern, argument, instance: checked(pattern.syntax, argument.syntax, instance.syntax)


def document(source=False):
    text = source_composed()[0] if source else generic_composed()[0]
    extra = PARAMS
    if source:
        extra += f'q[k h23[{ARGS}]].q[k h24[{ARGS}]].q[k h25[k zd[] {ARGS}]].'
    else:
        extra += f'q[k rbq[{ARGS} p zl p zm p zn]].q[k rbr[{ARGS} p zl p zm p zn p zo p zp p zq]].'
    return candidate(text, extra)


def model_for(doc, structural, stored=True, used=True, applied=True, reviewed=False, natural=True, faculty_use=True, variant=''):
    model = guarded(doc)
    def target(values, expected, prefix, fields):
        expected = list(expected)
        for i, field in enumerate(fields):
            if variant == prefix + '_' + field:
                expected[i] = 'other'
        return list(values) == expected
    carries = lambda form, pattern, ctx: stored and target((form, symbol(pattern), ctx),
        ('form', 'zf', 'now'), 'stored', ('form', 'pattern', 'context'))
    use = lambda person, form, act, ctx: used and target((person, form, act, ctx),
        ('person', 'form', 'act', 'now'), 'use', ('person', 'form', 'act', 'context'))
    def adoption(person, instance, act, ctx):
        wanted = dict(INSTANCE)
        if variant == 'applied_instance':
            wanted['function'] = {'kind': 'function_ref', 'symbol': 'zh'}
        return applied and json.loads(instance.syntax) == wanted and target((person, act, ctx),
            ('person', 'act', 'now'), 'applied', ('person', 'act', 'context'))
    judgment = lambda person, judgment, ctx: reviewed and target((person, judgment, ctx),
        ('person', 'judgment', 'now'), 'judgment', ('person', 'judgment', 'context'))
    matter = lambda judgment, form, ctx: target((judgment, form, ctx),
        ('judgment', 'form', 'now'), 'matter', ('judgment', 'form', 'context'))
    review = lambda judgment, act, ctx: target((judgment, act, ctx),
        ('judgment', 'act', 'now'), 'review', ('judgment', 'act', 'context'))
    model.update(za=lambda: 'person', zb=lambda: 'form', zc=lambda: 'act', zd=lambda: 'faculty', ze=lambda: 'now',
        rbo=structural, zl=carries, hw2=carries, zm=use, hx2=use, zn=adoption, hy2=adoption,
        zo=judgment, fa=judgment, zp=matter, fb=matter, zq=review, hz2=review,
        hh2=lambda faculty, person, ctx: natural and target((faculty, person, ctx),
            ('faculty', 'person', 'now'), 'natural', ('faculty', 'person', 'context')),
        hi2=lambda person, faculty, act, ctx: faculty_use and target((person, faculty, act, ctx),
            ('person', 'faculty', 'act', 'now'), 'facultyuse', ('person', 'faculty', 'act', 'context')))
    inventory = guarded(doc)
    return {key: value for key, value in model.items() if key in inventory}


def instance_checks():
    doc = candidate(generic_composed()[0], PARAMS + '''
q[k rbo[r[p zf] r[k zg[]] r[c[p zf][k zg[]]]]].
q[k rbo[r[p zh] r[k zg[]] r[c[p zf][k zg[]]]]].
q[k rbo[r[p zf] r[k zi[]] r[c[p zf][k zg[]]]]].
q[k rbo[r[p zf] r[k zg[]] r[c[p zh][k zg[]]]]].
q[k rbo[r[p zf] r[k zg[]] r[k zf[k zg[]]]]].
''')
    model = guarded(doc)
    model['rbo'] = matcher(doc)
    result = values(doc, model)
    if result != [True, False, False, False, False]:
        raise ValueError('Template syntax was replaced by an equivalent alias or another argument')
    return {'result': result, 'all_interpretations_except_structural_matcher_unexecuted': True}


def use_checks():
    generic, source = document(), document(True)
    match_generic, match_source = matcher(generic), matcher(source)
    rows = []
    for stored, used, applied, reviewed, natural, faculty_use in product((False, True), repeat=6):
        args = (stored, used, applied, reviewed, natural, faculty_use)
        actual = values(generic, model_for(generic, match_generic, *args))
        native = values(source, model_for(source, match_source, *args))
        adopted_use = stored and used and applied
        routine = adopted_use and not reviewed
        if actual != [adopted_use, routine] or native != actual + [routine and natural and faculty_use]:
            raise ValueError('Formulation use, examination or own faculty use was conflated')
        rows.append(dict(stored=stored, used=used, applied=applied, reviewed=reviewed,
            natural=natural, faculty_use=faculty_use, result=native))
    return rows


def binding_checks():
    doc = document(True)
    structural = matcher(doc)
    fields = {'stored': ('form', 'pattern', 'context'), 'use': ('person', 'form', 'act', 'context'),
        'applied': ('person', 'instance', 'act', 'context'), 'judgment': ('person', 'judgment', 'context'),
        'matter': ('judgment', 'form', 'context'), 'review': ('judgment', 'act', 'context'),
        'natural': ('faculty', 'person', 'context'), 'facultyuse': ('person', 'faculty', 'act', 'context')}
    rows = {}
    for prefix, names in fields.items():
        for name in names:
            variant = prefix + '_' + name
            reviewed = prefix in ('judgment', 'matter', 'review')
            actual = values(doc, model_for(doc, structural, reviewed=reviewed, variant=variant))
            expected = [True, True, True] if reviewed else [True, True, False] if prefix in ('natural', 'facultyuse') else [False] * 3
            if actual != expected:
                raise ValueError('A different use or examination was borrowed: ' + variant)
            rows[variant] = actual
    return rows


def unbounded_refusal():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k h22[k za[]]][k zb[]]].')
    model = guarded(doc)
    model.update(za=lambda: 'form', zb=lambda: 'now')
    try:
        values(doc, model)
    except ValueError as error:
        if 'Cannot finitely quantify the description domain' not in str(error):
            raise
        return {'refused': True, 'reason': str(error)}
    raise ValueError('A finite fixture substituted for all descriptions')


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source text changed')
    segments = []
    for phrase, definitions in (('Formeln', ['h22']), ('diese mechanischen Werkzeuge', ['h23', 'h24', 'h25'])):
        start = text.index(phrase)
        segments.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start,
            'end': start + len(phrase), 'source': phrase, 'definitions': definitions, 'status': 'partial_explicit_reading',
            'full_semantic_equivalence': False})
    return {'segments': segments, 'remaining': ['all senses of fixed formulations', 'deictic reference and noun coordination',
        'general instrumental role', 'reasonableness and misuse criteria', 'fetters and enduring immaturity']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'described-routines'), (source_composed, 'kant-described-routines')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored routines differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Routine notation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier Kant statements or declarations changed')
    paths = list(documents) + [PARENT, 'data/described-routines-basis-v1.json', 'data/kant-described-routines-basis-v1.json',
        'scripts/compose_described_routines.py', 'scripts/check_described_routines.py', 'noema/description_templates.py',
        'noema/discourse.py', 'noema/finite_semantics.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return {'status': 'partial_typed_formulation_use_and_unexamined_application', 'documents': documents,
        'instances': instance_checks(), 'use': use_checks(), 'bindings': binding_checks(), 'unbounded': unbounded_refusal(),
        'alignment': alignment(), 'roundtrips': True, 'parent_preserved': True,
        'reading_review': {'comparison_url': 'https://korpora.org/kant/aa08/036.html', 'location': 'AA VIII 36, lines 8–10',
            'method': '固定本文と電子本文を照合。原刊画像の確認ではない。',
            'interpretation': 'Formelnを再利用できる型、mechanischenをその使用の適用を本人が吟味しないという部分的な読みで記述する。'},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Described routine report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Formulation instances, same-use examination and finite refusal checked')


if __name__ == '__main__':
    main()
