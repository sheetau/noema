"""Check shared metaphor roles, bodily bindings and scoped persistence."""
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
from scripts.compose_relational_fetters import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/relational-fetters-v1.json'
DOMAIN = ('object', 'person', 'limb', 'move', 'other', 'method', 'faculty', 'act', 'node', 'author')
SCENES = ('past', 'now', 'middle', 'later')


def values(doc, model):
    return [row['value'] for row in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=3_000_000, memoize_definitions=True, memoize_expressions=True)]


def pair_checks():
    prefix = generic_composed()[0] + 'r za[a a] e.r zb[] a.r zc[] a.r zd[] d.'
    rows = []
    cases = ((), ('zb',), ('zb', 'zc'), ('zc', 'zb'), ('zb', 'zb'), ('zb', 'zc', 'zb'))
    for items in cases:
        text = ' '.join(f'k {name}[]' for name in items)
        doc = parse(prefix + f'q[t[k rbv[p za l[a][{text}]]][k zd[]]].')
        model = guarded(doc)
        model.update(za=lambda left, right: Content(SCENES, (False, (left, right) == ('object', 'person'), False, False)),
            zb=lambda: 'object', zc=lambda: 'person', zd=lambda: 'now')
        actual = values(doc, model)
        if actual != [items == ('zb', 'zc')]:
            raise ValueError('Pair lifting changed roles or allowed extra participants')
        rows.append({'participants': items, 'result': actual})
    # Two roles may be occupied by one individual when the relation allows it.
    doc = parse(prefix + 'q[t[k rbv[p za l[a][k zb[] k zb[]]]][k zd[]]].')
    model = guarded(doc)
    model.update(za=lambda left, right: Content(SCENES, (False, left == right, False, False)),
        zb=lambda: 'object', zc=lambda: 'person', zd=lambda: 'now')
    if values(doc, model) != [True]:
        raise ValueError('Pair lifting imposed unintended distinctness')
    return {'cases': rows, 'same_individual_can_fill_two_roles': True}


def bodily_document():
    return candidate(source_composed()[0], 'r za[] a.r zb[] a.r zc[] d.q[t[k h2j[k za[] k zb[]]][k zc[]]].')


def bodily_model(doc, lower=True, fastens=True, possible=True, blocked=True, variant=''):
    model = guarded(doc)
    def matches(actual, expected, prefix, fields):
        expected = list(expected)
        for index, field in enumerate(fields):
            if variant == prefix + '_' + field:
                expected[index] = 'other'
        return list(actual) == expected
    model.update(za=lambda: 'object', zb=lambda: 'person', zc=lambda: 'now',
        h2f=lambda limb, person, ctx: lower and matches((limb, person, ctx), ('limb', 'person', 'now'), 'lower', ('limb', 'person', 'context')),
        h2e=lambda obj, limb, person, ctx: fastens and matches((obj, limb, person, ctx),
            ('object', 'limb', 'person', 'now'), 'fastens', ('object', 'limb', 'person', 'context')),
        h2g=lambda person, movement, ctx: possible and matches((person, movement, ctx),
            ('person', 'move', 'now'), 'possible', ('person', 'movement', 'context')),
        h2h=lambda obj, limb, person, movement, ctx: blocked and matches((obj, limb, person, movement, ctx),
            ('object', 'limb', 'person', 'move', 'now'), 'blocked', ('object', 'limb', 'person', 'movement', 'context')))
    return model


def bodily_checks():
    doc = bodily_document()
    rows = []
    for flags in product((False, True), repeat=4):
        actual = values(doc, bodily_model(doc, *flags))
        if actual != [all(flags)]:
            raise ValueError('A bodily restraint lost one of its conditions')
        rows.append({'lower_fastens_possible_blocked': flags, 'result': actual})
    bindings = {}
    for prefix, fields in (('lower', ('limb', 'person', 'context')),
        ('fastens', ('object', 'limb', 'person', 'context')), ('possible', ('person', 'movement', 'context')),
        ('blocked', ('object', 'limb', 'person', 'movement', 'context'))):
        for field in fields:
            key = prefix + '_' + field
            actual = values(doc, bodily_model(doc, variant=key))
            if actual != [False]:
                raise ValueError('A different limb/person/object/movement supplied the constraint: ' + key)
            bindings[key] = actual
    return {'cases': rows, 'bindings': bindings}


def persistence_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k h26[k za[]]][k zb[]]].')
    cases = {
        'baseline': (('now', 'middle', 'later'), SCENES, SCENES, 'person', False, True),
        'lost_in_middle': (('now', 'middle', 'later'), ('past', 'now', 'later'), SCENES, 'person', False, False),
        'empty_scope': ((), SCENES, SCENES, 'person', False, False),
        'scope_skips_middle': (('now', 'later'), SCENES, SCENES, 'person', False, False),
        'anchor_missing': (('middle', 'later'), SCENES, SCENES, 'person', False, False),
        'outside_history': (SCENES, SCENES, ('past', 'now', 'middle'), 'person', False, False),
        'cyclic_order': (SCENES, SCENES, SCENES, 'person', True, False),
        'other_person_scope': (SCENES, SCENES, SCENES, 'other', False, False),
        'loss_outside_scope': (('now', 'middle'), ('now', 'middle'), SCENES, 'person', False, True),
        'scope_includes_prior_time': (SCENES, SCENES, SCENES, 'person', False, False),
    }
    rows = {}
    for name, (scope, immature, history, subject, cyclic, expected) in cases.items():
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'now',
            ia=lambda person, anchor, point: person == 'person' and point in history,
            ib=lambda person, anchor, point: (person, anchor) == (subject, 'now') and point in scope,
            ic=lambda first, second, anchor: SCENES.index(first) < SCENES.index(second) or (cyclic and first == 'later' and second == 'past'),
            aa=lambda person: person == 'person',
            ae=lambda person, method, start: (person, method) == ('person', 'method') and start not in immature,
            af=lambda person, method, start, end: (person, method) == ('person', 'method') and start == end,
            ap=lambda person, method, start, end: (person, method) == ('person', 'method') and start == end,
            ab=lambda faculty, person, ctx: (faculty, person) == ('faculty', 'person'),
            ac=lambda person, faculty, act, ctx: (person, faculty, act) == ('person', 'faculty', 'act'),
            ad=lambda *args: False)
        actual = values(doc, model)
        if actual != [expected]:
            raise ValueError('Scoped persistence was inferred from endpoints or enlarged beyond its scope: ' + name)
        rows[name] = actual
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'node', 'author', 'target', 'depiction', 'context', 'reversed'):
        expected = ['node', 'author', 'h2a', 'h2b', 'now']
        if variant in ('node', 'author', 'target', 'depiction', 'context'):
            expected[('node', 'author', 'target', 'depiction', 'context').index(variant)] = 'other'
        if variant == 'reversed':
            expected[2:4] = ['h2b', 'h2a']
        model = guarded(doc)
        model.update(h2d=lambda: 'node', wa=lambda: 'author', wh=lambda: 'now',
            rbt=lambda node, author, target, depiction, ctx: [node, author, symbol(target), symbol(depiction), ctx] == expected)
        actual = values(doc, model)
        if actual != [variant == 'baseline']:
            raise ValueError('Relational metaphor attribution changed or evaluated its contents')
        rows[variant] = actual
    return {'cases': rows, 'all_content_primitives_guarded_against_execution': True}


def framing_checks():
    doc = parse(generic_composed()[0] + '''
r za[j[a]] e.r zb[j[a]] e.r zc[] a.r zd[] d.
q[t[k za[l[a][k zc[]]]][k zd[]]].q[t[k zb[l[a][k zc[]]]][k zd[]]].
q[k rbu[k zc[] k zc[] r[p za] r[p zb] k zd[]]].
q[k rbu[k zc[] k zc[] r[p za] r[p za] k zd[]]].
''')
    rows = []
    for target, depiction, framed in product((False, True), repeat=3):
        model = guarded(doc)
        model.update(za=lambda items: Content(SCENES, (False, target, False, False)),
            zb=lambda items: Content(SCENES, (False, depiction, False, False)),
            zc=lambda: 'object', zd=lambda: 'now', rbt=lambda *args: framed)
        actual = values(doc, model)
        if actual != [target, depiction, framed, False]:
            raise ValueError('Relational attribution was identified with a literal truth or identical description')
        rows.append({'target': target, 'depiction': depiction, 'framed': framed, 'result': actual})
    return rows


def category_refusal():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k h27[k za[]]][k zb[]]].')
    model = guarded(doc)
    model.update(za=lambda: 'object', zb=lambda: 'now')
    try:
        values(doc, model)
    except ValueError as error:
        if 'Cannot finitely quantify the description domain' not in str(error):
            raise
        return {'refused': True, 'reason': str(error)}
    raise ValueError('A few known descriptions substituted for the entire expression domain')


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source text changed')
    start = text.index('Fußschellen')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start + len('Fußschellen'),
        'source': 'Fußschellen', 'definitions': ['h2i', 'h2j', 'h2a', 'h2b', 'h2c'],
        'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['noun coordination and deictic scope', 'strength of immerwährenden',
            'causal mechanism', 'physical and evaluative basis of fetters', 'subsequent conditional release and movement']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'relational-fetters'), (source_composed, 'kant-relational-fetters')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored relational fetters differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Relational metaphor notation roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Earlier Kant content changed')
    paths = list(documents) + [PARENT, 'data/relational-fetters-basis-v1.json', 'data/kant-relational-fetters-basis-v1.json',
        'scripts/compose_relational_fetters.py', 'scripts/check_relational_fetters.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    report = {'status': 'partial_relational_fetter_metaphor_not_literal_physical_claim', 'documents': documents,
        'pairs': pair_checks(), 'bodily': bodily_checks(), 'persistence': persistence_checks(), 'attribution': attribution_checks(),
        'framing': framing_checks(), 'category_refusal': category_refusal(),
        'alignment': alignment(), 'roundtrips': True, 'parent_preserved': True,
        'reading_review': {'comparison_url': 'https://korpora.org/kant/aa08/036.html', 'location': 'AA VIII 36, line 10',
            'method': '固定本文と電子本文を比較。原刊画像の照合ではない。',
            'interpretation': '規定・定型表現とその利用者を、拘束物と被拘束者の位置へ対応させる。無期限の持続は今回の記述で確定しない。'},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
    return json.loads(json.dumps(report, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Relational fetter report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Metaphor role positions, physical bindings and scoped persistence checked')


if __name__ == '__main__':
    main()
