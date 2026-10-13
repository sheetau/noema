"""Check nested normative targets without asserting the targeted policies."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_policy_norms import ROOT, PARENT, TRUE, generic_composed, source_composed

REPORT = ROOT / 'reports/policy-norms-v1.json'


def seq(items):
    return SequenceValue(tuple(items), '"individual"')


def generic_checks():
    extra = '''r za[] a.r zb[] a.r zc[] a.r zd[] j[a].r ze[] c.r zf[] d.r zg[j[a]] c.
r zh[a a a i[h[j[a]] e] j[a] c d] c.r zi[a a a i[h[j[a]] e] j[a] c d] c.
r zj[j[a] d] c.d zk[bindings j[a]] e[b scene[k zj[v bindings v scene]]].
'''
    args = 'k za[] k zb[] k zc[] r[p zk] k zd[] k ze[] k zf[] p zg p zh p zi'
    doc = candidate(generic_composed()[0], extra + ''.join('q[k ' + name + '[' + args + ']].' for name in ('rds', 'rdt', 'rdu', 'rdv', 'rdw')))
    domain, scenes = ('source', 'person', 'role'), ('now',)
    for valid, rp, rn, ap, an, actual, sign in product((False, True), repeat=7):
        required, allowed = {True: rp, False: rn}, {True: ap, False: an}
        def bound(source, person, role, desc, bindings, polarity, context):
            return (source, person, role, symbol(desc), bindings.items, context) == ('source', 'person', 'role', 'zk', ('person', 'role'), 'now')
        model = guarded(doc)
        model.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: seq(('person', 'role')),
            ze=lambda: sign, zf=lambda: 'now', zg=lambda bindings: valid,
            zh=lambda *args: bound(*args) and required[args[-2]], zi=lambda *args: bound(*args) and allowed[args[-2]],
            zj=lambda bindings, context: actual)
        observed = values(doc, model, domain, scenes)
        expected = [valid and required[sign], valid and allowed[sign], valid and allowed[sign] and not required[not sign],
            valid and required[sign] and required[not sign], valid and required[sign] and actual != sign]
        if observed != expected:
            raise ValueError('Policy norm polarity or validity differs')
    length_doc = candidate(generic_composed()[0], 'r za[] j[a].r zb[] b.q[k rdr[k za[] k zb[]]].')
    length_cases = 0
    for length in (0, 1, 2, 3, 5, 17):
        for size in (-1, 0, 1, 2, 3, 5, 17, Fraction(1, 2)):
            model = {'za': lambda: seq(('person',) * length), 'zb': lambda: Fraction(size)}
            if values(length_doc, model, ('person',), ('now',)) != [length == size]:
                raise ValueError('Binding length truncated or rounded')
            length_cases += 1
    return {'polarity_and_validity_cases': 128, 'binding_length_cases': length_cases}


EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] a.r zg[] d.r zh[] a.r zi[] j[a].
'''
ARGS = 'k za[] k zb[] k zc[] k zd[] k ze[] k zf[] k zg[]'


def constants(model, small=False):
    model.update(za=lambda: 'regime' if small else 'assessor', zb=lambda: 'person' if small else 'regulator',
        zc=lambda: 'role' if small else 'office', zd=lambda: 'regime', ze=lambda: 'person', zf=lambda: 'role', zg=lambda: 'now',
        zh=lambda: 'activity', zi=lambda: seq(('regime', 'person', 'role')))


def reference_checks():
    doc = candidate(source_composed()[0], EXTRA + 'q[k h7m[' + ARGS + ']].q[k h7n[' + ARGS + ']].')
    domain = ('assessor', 'regulator', 'office', 'regime', 'person', 'role', 'other')
    rows = {}
    variants = ('baseline', 'no_requirement', 'no_permission', 'other_assessor', 'other_regulator', 'other_office',
        'other_regime', 'other_person', 'other_role', 'reordered_bindings', 'extra_binding', 'missing_binding',
        'other_context', 'negative_polarity', 'swapped_policy', 'other_target_description')
    for variant in variants:
        model = guarded(doc)
        constants(model)
        def match(source, person, role, desc, bindings, sign, context, target):
            expected = ['assessor', 'regulator', 'office', 'regime', 'person', 'role']
            fields = ('assessor', 'regulator', 'office', 'regime', 'person', 'role')
            for i, field in enumerate(fields):
                if variant == 'other_' + field:
                    expected[i] = 'other'
            target_bindings = tuple(expected[3:])
            if variant == 'reordered_bindings':
                target_bindings = ('person', 'regime', 'role')
            elif variant == 'extra_binding':
                target_bindings += ('other',)
            elif variant == 'missing_binding':
                target_bindings = target_bindings[:2]
            target = ('h7j' if target == 'h7i' else 'h7i') if variant == 'swapped_policy' else (
                'h7h' if variant == 'other_target_description' else target)
            return (source, person, role, symbol(desc), bindings.items, sign, context) == (
                *expected[:3], target, target_bindings, variant != 'negative_polarity', 'later' if variant == 'other_context' else 'now')
        model['h7k'] = lambda *args: variant != 'no_requirement' and match(*args, 'h7i')
        model['h7l'] = lambda *args: variant != 'no_permission' and match(*args, 'h7j')
        actual = values(doc, model, domain, ('now', 'later'))
        expected = [True, True] if variant == 'baseline' else [False, True] if variant == 'no_requirement' else (
            [True, False] if variant == 'no_permission' else [False, False])
        if actual != expected:
            raise ValueError('Outer norm or inner policy binding differs: ' + str((variant, actual)))
        rows[variant] = actual
    model = guarded(doc)
    constants(model)
    model['h7l'] = lambda *args: False
    try:
        values(doc, model, domain, ('now', 'later'))
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('An unassessed outer requirement became a known value')
    return {'cases': rows, 'all_inner_norms_execution_and_public_classification_guarded': True,
        'unassessed_outer_requirement_refused': True}


def fulfillment_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    doc = candidate(text, EXTRA + 'q[k h7m[' + ARGS + ']].q[k h7o[' + ARGS + ''']].
q[e[k h7i[k zi[]]][k h7d[k zd[] k ze[] k zf[]]]].q[t[k h7i[k zi[]]][k zg[]]].''')
    domain, scenes = ('regime', 'person', 'role', 'activity', 'audience'), ('now', 'later')
    def inner_model(target_doc, demanded, granted):
        model = guarded(target_doc)
        constants(model, small=True)
        model.update(h7k=lambda source, person, role, desc, bindings, sign, context: demanded and (
            source, person, role, symbol(desc), bindings.items, sign, context) == ('regime', 'person', 'role', 'h7i', ('regime', 'person', 'role'), True, 'now'),
            h7a=lambda *args: False,
            h7b=lambda source, person, role, activity, desc, sign, context: granted and (
                source, person, role, activity, symbol(desc), sign) == ('regime', 'person', 'role', 'activity', mapping['dc'], True))
        for name, callback in {
            'ca': lambda person, activity, context: (person, activity) == ('person', 'activity'),
            'cb': lambda person, activity, role, context: (person, activity, role) == ('person', 'activity', 'role'),
            'cc': lambda activity, audience, context: (activity, audience) == ('activity', 'audience'),
            'cd': lambda role, context: role == 'role', 'ce': lambda audience, context: audience == 'audience',
        }.items():
            model[mapping[name]] = callback
        return model
    rows = {}
    for demanded, granted in product((False, True), repeat=2):
        actual = values(doc, inner_model(doc, demanded, granted), domain, scenes)
        if actual != [demanded, demanded and not granted, True, granted]:
            raise ValueError('Requiring public permission asserted the permission itself')
        rows[str(int(demanded)) + str(int(granted))] = actual
    shapes = {}
    shape_doc = candidate(text, EXTRA + 'q[k h7g[k zi[]]].q[t[k h7i[k zi[]]][k zg[]]].')
    for items in ((), ('regime', 'person'), ('regime', 'person', 'role'), ('regime', 'person', 'role', 'activity')):
        model = inner_model(shape_doc, True, True)
        model['zi'] = lambda: seq(items)
        actual = values(shape_doc, model, domain, scenes)
        if actual != [len(items) == 3, len(items) == 3]:
            raise ValueError('Policy adapter accepted the wrong arity')
        shapes[str(len(items))] = actual
    private_doc = candidate(text, EXTRA + '''q[e[k h7j[k zi[]]][k h7e[k zd[] k ze[] k zf[]]]].
q[t[k h7j[k zi[]]][k zg[]]].''')
    private = {}
    for prohibited in (False, True):
        model = inner_model(private_doc, False, False)
        model[mapping['cf']] = lambda person, role, context: (person, role) == ('person', 'role')
        model['h7a'] = lambda source, person, role, activity, desc, sign, context: prohibited and (
            source, person, role, activity, symbol(desc), sign) == ('regime', 'person', 'role', 'activity', mapping['dc'], False)
        actual = values(private_doc, model, domain, scenes)
        if actual != [True, prohibited]:
            raise ValueError('Private restriction adapter changed its target')
        private[str(int(prohibited))] = actual
    return {'cases': rows, 'policy_adapter_arity_cases': shapes, 'private_policy_cases': private,
        'adapter_matches_existing_public_permission_content': True}


def action_checks():
    text, basis = source_composed()
    dc = basis['role_linkage']['symbols']['roles']['dc']
    doc = candidate(text, EXTRA + 'q[k h7p[k zd[] k ze[] k zf[] k zh[] k zg[]]].q[k rdm[k zd[] k ze[] k zf[] k zh[] r[p '
        + dc + '] ' + TRUE + ' k zg[] p h7a p h7b]].')
    domain, rows = ('regime', 'person', 'role', 'activity'), {}
    for granted, prohibited in product((False, True), repeat=2):
        model = guarded(doc)
        constants(model, small=True)
        def mapped(source, person, role, desc, bindings, sign, context):
            return (source, person, role, symbol(desc), bindings.items, context) == ('regime', 'person', 'role', 'h7h', ('person', 'activity'), 'now')
        def old(source, person, role, activity, desc, sign, context):
            return (source, person, role, activity, symbol(desc), context) == ('regime', 'person', 'role', 'activity', dc, 'now')
        model.update(h7k=lambda *args: prohibited and not args[-2] and mapped(*args),
            h7l=lambda *args: granted and args[-2] and mapped(*args),
            h7a=lambda *args: prohibited and not args[-2] and old(*args), h7b=lambda *args: granted and args[-2] and old(*args))
        actual = values(doc, model, domain, ('now',))
        if actual != [granted and not prohibited] * 2:
            raise ValueError('The same norm interface failed for a two-argument action')
        rows[str(int(granted)) + str(int(prohibited))] = actual
    execution_doc = candidate(text, EXTRA + 'q[t[k h7h[k zi[]]][k zg[]]].')
    execution = {}
    for name, items, expected in (
        ('correct', ('person', 'activity'), True), ('reordered', ('activity', 'person'), False),
        ('empty', (), False), ('missing', ('person',), False), ('extra', ('person', 'activity', 'role'), False)):
        model = guarded(execution_doc)
        constants(model, small=True)
        model['zi'] = lambda: seq(items)
        model[basis['role_linkage']['symbols']['roles']['cg']] = lambda person, activity, context: (person, activity, context) == ('person', 'activity', 'now')
        actual = values(execution_doc, model, domain, ('now',))
        if actual != [expected]:
            raise ValueError('Action adapter order or arity differs')
        execution[name] = actual
    return {'cases': rows, 'permission_does_not_evaluate_execution': True, 'action_adapter_cases': execution,
        'norm_interpretations_explicitly_correspond_not_automatically_identified': True}


def alignment():
    previous = json.loads((ROOT / 'reports/described-norms-v1.json').read_text(encoding='utf-8'))['alignment']
    rows = []
    for old in previous['segments']:
        row = dict(old)
        row['definitions'] = ['h7i', 'h7m', 'h7o'] if 'muß jederzeit frei sein' in old['source'] else ['h7j', 'h7n']
        row['review_ja'] = '評価側の要求・許可を内側の政策状態の記述と引数へ結び付けた。常に・頻度・程度・留保と自由の全意味は未完。'
        rows.append(row)
    return {'segments': rows, 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'policy-norms'), (source_composed, 'kant-policy-norms')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored policy norms differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Policy norm roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/policy-norms-basis-v1.json', 'data/kant-policy-norms-basis-v1.json',
        'scripts/compose_policy_norms.py', 'scripts/check_policy_norms.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'reports/described-norms-v1.json']
    return json.loads(json.dumps({'status': 'partial_parameterized_norms_about_policies_not_complete_freedom',
        'documents': documents, 'generic': generic_checks(), 'references': reference_checks(),
        'fulfillment': fulfillment_checks(), 'action_correspondence': action_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
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
            raise ValueError('Policy norms report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Policy requirements, permission, fulfillment and action correspondence checked')


if __name__ == '__main__':
    main()
