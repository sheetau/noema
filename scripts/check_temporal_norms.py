"""Distinguish a requirement for a whole period from requirements at each time."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_temporal_norms import ROOT, PARENT, source_composed

REPORT = ROOT / 'reports/temporal-norms-v1.json'
DOMAIN = ('regime', 'person', 'role', 'frame', 'activity', 'audience')
SCENES = ('first', 'middle', 'last', 'outside')
EXTRA = 'r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.\n'
ARGS = 'k za[] k zb[] k zc[] k za[] k zb[] k zc[] k zd[] k ze[]'
TARGET = 'k za[] k zb[] k zc[] k zd[] k ze[]'


def model_for(doc, mapping, *, whole=True, local=(True,) * 3, permissions=None, variant='baseline'):
    model = guarded(doc)
    def history(frame, anchor, point):
        return variant != 'empty_history' and frame == 'frame' and point in SCENES[:3]
    def scope(frame, anchor, point):
        if frame != 'frame' or variant == 'empty_scope':
            return False
        if variant == 'scope_outside':
            return point in SCENES
        if variant == 'gap':
            return point in ('first', 'last')
        if variant == 'narrowed_to_first':
            return point == 'first'
        if variant == 'different_scope_in_other_contexts' and anchor != 'first':
            return point == 'last'
        return point in SCENES[:3]
    def before(first, last, anchor):
        return SCENES.index(first) < SCENES.index(last) or variant == 'cyclic_order' and (first, last) == ('last', 'first')
    def required(source, person, role, desc, bindings, sign, context):
        if (source, person, role, sign) != ('regime', 'person', 'role', True):
            return False
        inner = ('audience' if variant == 'wrong_inner_source' else 'regime', 'person', 'role')
        name = symbol(desc)
        if name == 'h7t':
            return whole and bindings.items == (*inner, 'audience' if variant == 'other_required_frame' else 'frame') and context == (
                'outside' if variant == 'other_requirement_context' else 'first')
        return name == 'h7i' and bindings.items == inner and context in SCENES[:3] and local[SCENES.index(context)]
    model.update(za=lambda: 'regime', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'frame', ze=lambda: 'first',
        h7q=history, h7r=scope, ic=before, h7k=required)
    if permissions is not None:
        old = {
            'ca': lambda person, activity, context: (person, activity) == ('person', 'activity'),
            'cb': lambda person, activity, role, context: (person, activity, role) == ('person', 'activity', 'role'),
            'cc': lambda activity, audience, context: (activity, audience) == ('activity', 'audience'),
            'cd': lambda role, context: role == 'role', 'ce': lambda audience, context: audience == 'audience'}
        model.update({mapping[name]: callback for name, callback in old.items()})
        model.update(h7a=lambda *args: False,
            h7b=lambda source, person, role, activity, desc, sign, context: (
                source, person, role, activity, symbol(desc), sign) == ('regime', 'person', 'role', 'activity', mapping['dc'], True)
                and context in SCENES[:3] and permissions[SCENES.index(context)])
    return model


def requirement_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    doc = candidate(text, EXTRA + 'q[k h7u[' + ARGS + ']].q[k h7v[' + ARGS + ']].')
    rows = []
    for whole, first, middle, last in product((False, True), repeat=4):
        local = (first, middle, last)
        actual = values(doc, model_for(doc, mapping, whole=whole, local=local), DOMAIN, SCENES)
        if actual != [whole, all(local)]:
            raise ValueError('Temporal quantification commuted with a requirement')
        rows.append({'whole_period_requirement': whole, 'point_requirements': list(local), 'results': actual})
    contrasts = {}
    for variant in ('empty_scope', 'gap', 'scope_outside', 'empty_history', 'cyclic_order',
            'other_required_frame', 'other_requirement_context', 'wrong_inner_source'):
        actual = values(doc, model_for(doc, mapping, variant=variant), DOMAIN, SCENES)
        expected = [True, False] if variant in ('empty_scope', 'gap', 'scope_outside', 'empty_history', 'cyclic_order') else (
            [False, False] if variant == 'wrong_inner_source' else [False, True])
        if actual != expected:
            raise ValueError('Requirement frame or binding differs: ' + str((variant, actual)))
        contrasts[variant] = actual
    only_whole = candidate(text, EXTRA + 'q[k h7u[' + ARGS + ']].')
    model = model_for(only_whole, mapping)
    for name in ('h7q', 'h7r', 'ic'):
        model[name] = guarded(only_whole)[name]
    if values(only_whole, model, DOMAIN, SCENES) != [True]:
        raise ValueError('Stating a requirement evaluated its temporal target')
    model['h7k'] = guarded(only_whole)['h7k']
    try:
        values(only_whole, model, DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown requirement became a known result')
    return {'truth_table': rows, 'contrasts': contrasts, 'inner_permissions_always_guarded': True,
        'whole_period_requirement_does_not_evaluate_its_frame': True, 'unassessed_requirement_refused': True}


def permission_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    doc = candidate(text, EXTRA + 'q[k h7u[' + ARGS + ']].q[k h7w[' + TARGET + ']].q[k h7x[' + ARGS + ']].')
    rows = []
    for flags in product((False, True), repeat=3):
        actual = values(doc, model_for(doc, mapping, permissions=flags), DOMAIN, SCENES)
        if actual != [True, all(flags), not all(flags)]:
            raise ValueError('Permission at the endpoints replaced whole-period permission')
        rows.append({'point_permissions': list(flags), 'results': actual})
    contrasts = {}
    for variant, flags, whole, expected in (
        ('no_requirement_but_permissions', (True, True, True), False, [False, True, False]),
        ('no_requirement_and_no_permissions', (False, False, False), False, [False, False, False]),
        ('empty_scope', (True, True, True), True, [True, False, True]),
        ('gap', (True, False, True), True, [True, False, True]),
        ('scope_outside', (True, True, True), True, [True, False, True]),
        ('cyclic_order', (True, True, True), True, [True, False, True]),
        ('narrowed_to_first', (True, False, False), True, [True, True, False]),
        ('different_scope_in_other_contexts', (True, False, True), True, [True, False, True]),
    ):
        actual = values(doc, model_for(doc, mapping, permissions=flags, whole=whole, variant=variant), DOMAIN, SCENES)
        if actual != expected:
            raise ValueError('Temporal permission contrast differs: ' + str((variant, actual)))
        contrasts[variant] = actual
    return {'truth_table': rows, 'contrasts': contrasts, 'all_world_situations_are_not_automatically_target_times': True,
        'a_narrowed_period_is_not_proof_of_source_scope_completeness': True}


def alignment():
    previous = json.loads((ROOT / 'reports/policy-norms-v1.json').read_text(encoding='utf-8'))['alignment']
    old = next(row for row in previous['segments'] if 'muß jederzeit frei sein' in row['source'])
    row = dict(old)
    row['definitions'] = ['h7t', 'h7u', 'h7v', 'h7w', 'h7x']
    row['review_ja'] = '規範の内外の時間量化と実際の全期間の許可を区別した。期間の完全性、唯一の作用範囲、自由の全意味は未確定。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    text, basis = source_composed()
    doc = parse(text)
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
            (ROOT / 'data/kant-temporal-norms-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored temporal norms differ')
    for notation in ('compact', 'full'):
        form = format_graph(doc, notation)
        if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
            raise ValueError('Temporal norm roundtrip differs')
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = [basis['document'], PARENT, 'data/kant-temporal-norms-basis-v1.json', 'scripts/compose_temporal_norms.py',
        'scripts/check_temporal_norms.py', 'reports/policy-norms-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py']
    return json.loads(json.dumps({'status': 'partial_temporal_scope_of_norms_not_complete_public_freedom',
        'documents': {basis['document']: audit_basis(doc, basis)}, 'requirements': requirement_checks(),
        'permissions': permission_checks(), 'alignment': alignment(), 'roundtrips': True,
        'parent_preserved': True, 'new_source_assertions': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Temporal norms report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Temporal scope, normative scope and actual sustained permission checked')


if __name__ == '__main__':
    main()
