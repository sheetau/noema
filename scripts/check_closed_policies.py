"""Verify that typed closed targets preserve identity without implying execution."""
import argparse
import hashlib
from fractions import Fraction
from itertools import product
import json

from noema.finite_semantics import SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.policy_descriptions import close_policy_description
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_closed_policies import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/closed-policies-v1.json'
SCENES = ('first', 'middle', 'last')
DOMAIN = ('source', 'person', 'role', 'frame', 'one', 'two', 'assessor', 'regulator', 'office')
EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[d] j[a].r zf[d] b.r zg[b] c.
r zh[] j[d].r zi[d] b.r zj[] b.r zk[b] c.r zl[] d.r zm[] a.r zn[] a.r zo[] a.
d zp[value b] c[k zk[v value]].
'''


def quoted(kind, name):
    body = {'kind': kind, 'symbol': name}
    if kind == 'call':
        body['arguments'] = []
    return {'kind': 'quote', 'body': body}


def source_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    base = candidate(text, EXTRA)
    template = quoted('function_ref', 'h77')
    arguments = [quoted(kind, name) for kind, name in (
        ('call', 'za'), ('call', 'zb'), ('call', 'zc'), ('call', 'zd'), ('function_ref', 'ze'),
        ('function_ref', 'zf'), ('function_ref', 'zg'), ('call', 'zh'), ('function_ref', 'zi'),
        ('call', 'zj'), ('function_ref', 'zk'))]
    target = close_policy_description(base, template, arguments)
    target_syntax = json.dumps(target['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    def make_doc(selected=target, full=False):
        expressions = []
        for name in ('hza', 'hzb', 'hzc', 'hzd') if full else ('hza', 'hzb'):
            fields = ([quoted('call', name)['body'] for name in ('zm', 'zn', 'zo')] if name != 'hzc' else [])
            expressions.append({'kind': 'ask', 'body': {'kind': 'call', 'symbol': name,
                'arguments': [*fields, selected, quoted('call', 'zl')['body']]}})
        return {**base, 'statements': expressions}
    def model(doc, allowed=True, opposed=False, actual=True, variant='baseline', evaluate=False):
        result = guarded(doc)
        def bound(source, person, role, description, bindings, sign, context):
            return (source, person, role, description.syntax, bindings.items, context) == (
                'assessor', 'regulator', 'office', target_syntax, (), 'first')
        result.update(zm=lambda: 'source' if variant == 'outer_source' else 'assessor',
            zn=lambda: 'person' if variant == 'outer_addressee' else 'regulator',
            zo=lambda: 'role' if variant == 'outer_role' else 'office',
            zl=lambda: 'middle' if variant == 'outer_context' else 'first',
            h7k=lambda *args: opposed and not args[-2] and bound(*args),
            h7l=lambda *args: allowed and args[-2] and bound(*args))
        if not evaluate:
            return result
        counts = (2, 1, 0) if actual else (0, 0, 0)
        result.update(arithmetic())
        result.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'frame',
            ze=lambda point: SequenceValue(('one', 'two'), '"individual"'),
            zf=lambda point: Fraction(counts[SCENES.index(point)], 2), zg=lambda ratio: ratio >= Fraction(1, 2),
            zh=lambda: SequenceValue(SCENES, '"situation"'), zi=lambda point: Fraction(1), zj=lambda: Fraction(2, 3),
            zk=lambda ratio: ratio >= Fraction(1, 2), h7q=lambda frame, anchor, point: frame == 'frame',
            h7r=lambda frame, anchor, point: frame == 'frame',
            ic=lambda first, last, anchor: SCENES.index(first) < SCENES.index(last))
        def norm(kind, source, person, role, activity, desc, sign, context):
            if (source, person, role, symbol(desc)) != ('source', 'person', 'role', mapping['dc']) or activity not in ('one', 'two'):
                return False
            banned = ('one', 'two').index(activity) < counts[SCENES.index(context)]
            return kind == 'required' and not sign and banned or kind == 'allowed' and sign and not banned
        result.update(h7a=lambda *args: norm('required', *args), h7b=lambda *args: norm('allowed', *args))
        result[mapping['ca']] = lambda person, activity, point: person == 'person' and activity in ('one', 'two')
        result[mapping['cb']] = lambda person, activity, role, point: (person, role) == ('person', 'role') and activity in ('one', 'two')
        result[mapping['cf']] = lambda person, role, point: (person, role) == ('person', 'role')
        return result
    guarded_rows = []
    doc = make_doc()
    for allowed, opposed in product((False, True), repeat=2):
        actual = values(doc, model(doc, allowed, opposed), DOMAIN, SCENES)
        if actual != [allowed, allowed and not opposed]:
            raise ValueError('Permission evaluated its typed target or collapsed opposition')
        guarded_rows.append({'allowed': allowed, 'opposed': opposed, 'results': actual})
    bindings = {}
    variants = {'inner_source': (0, arguments[1]), 'inner_person': (1, arguments[2]),
        'inner_role': (2, arguments[1]), 'frame': (3, arguments[0]),
        'criterion_alias': (10, quoted('function_ref', 'zp')),
        'frequency_value': (9, {'kind': 'quote', 'body': {'kind': 'number', 'numerator': 1, 'denominator': 2}})}
    for name, (index, replacement) in variants.items():
        changed = list(arguments)
        changed[index] = replacement
        other = close_policy_description(base, template, changed)
        changed_doc = make_doc(other)
        actual = values(changed_doc, model(changed_doc), DOMAIN, SCENES)
        if actual != [False, False]:
            raise ValueError('Permission transferred to another typed target')
        bindings[name] = actual
    for name in ('outer_source', 'outer_addressee', 'outer_role', 'outer_context'):
        actual = values(doc, model(doc, variant=name), DOMAIN, SCENES)
        if actual != [False, False]:
            raise ValueError('Outer norm binding transferred')
        bindings[name] = actual
    # Nonempty bindings must not satisfy the same norm relation.
    wrong = model(doc)
    wrong['h7l'] = lambda source, person, role, description, bindings, sign, context: bindings.items == ('person',)
    if values(doc, wrong, DOMAIN, SCENES) != [False, False]:
        raise ValueError('Closed target used nonempty external bindings')
    unknown = model(doc)
    unknown['h7l'] = guarded(doc)['h7l']
    try:
        values(doc, unknown, DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown permission became false')
    full = make_doc(full=True)
    state_rows = []
    for allowed, opposed, actual in product((False, True), repeat=3):
        observed = values(full, model(full, allowed, opposed, actual, evaluate=True), DOMAIN, SCENES)
        if observed != [allowed, allowed and not opposed, actual, allowed and not actual]:
            raise ValueError('Allowed degree/frequency collapsed with actual policy')
        state_rows.append({'allowed': allowed, 'opposed': opposed, 'actual': actual, 'results': observed})
    try:
        values(full, model(full), DOMAIN, SCENES)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown actual policy became a known result')
    # The generated target remains ordinary parsed Noema in either notation.
    normalized = parse(format_graph(full))
    for notation in ('compact', 'full'):
        form = format_graph(normalized, notation)
        if parse(form) != normalized or parse(decode(encode(form, 'v2'))) != normalized:
            raise ValueError('Constructed target roundtrip differs')
    return {'guarded_permissions': guarded_rows, 'binding_contrasts': bindings, 'actual_policy_cases': state_rows,
        'empty_external_bindings_required': True, 'unknown_permission_and_actual_policy_refused': True,
        'all_typed_arguments_remain_unevaluated_when_only_permission_is_queried': True,
        'generated_description_roundtrips': True, 'closed_target_characters': len(target_syntax)}


def alignment():
    old = json.loads((ROOT / 'reports/restriction-frequency-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(old['segments'][0])
    row['definitions'] = ['h77', 'hza', 'hzb', 'hzc', 'hzd']
    row['review_ja'] = '型付き引数を保持した程度・頻度の記述を、同じ規範の許可対象へ接続した。実際の政策状態との独立性を検査。原文の数値・範囲を確定せず、候補全体の量化と進歩への留保、意味一致は未完。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'closed-policies'), (source_composed, 'kant-closed-policies')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored closed policy differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Closed policy roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = [*documents, PARENT, 'data/closed-policies-basis-v1.json', 'data/kant-closed-policies-basis-v1.json',
        'scripts/compose_closed_policies.py', 'scripts/check_closed_policies.py', 'reports/restriction-frequency-v1.json',
        'noema/policy_descriptions.py', 'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_typed_policy_permission_not_complete_private_use_clause',
        'documents': documents, 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0, 'new_primitives': 0,
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
            raise ValueError('Closed policy report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Typed targets, normative identity and independent actual policy checked')


if __name__ == '__main__':
    main()
