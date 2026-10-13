"""Check restriction measures without turning ungranted activity into prohibition."""
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
from scripts.check_described_norms import GENERIC_EXTRA, GENERIC_ARGS
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_restriction_degree import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/restriction-degree-v1.json'


def classification_checks():
    doc = parse(generic_composed()[0] + GENERIC_EXTRA + ''.join(
        'q[k ' + name + '[' + GENERIC_ARGS + ']].' for name in ('rdx', 'rdy', 'rdz')))
    rows = []
    for rp, rn, ap, an, sign in product((False, True), repeat=5):
        required, allowed = {True: rp, False: rn}, {True: ap, False: an}
        model = guarded(doc)
        model.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'activity',
            ze=lambda: 'now', zf=lambda: sign,
            zg=lambda *args: required[args[-2]], zh=lambda *args: allowed[args[-2]])
        actual = values(doc, model, ('source', 'person', 'role', 'activity'), ('now',))
        conflict = rp and rn or ap and rn or an and rp
        banned = required[not sign] and not required[sign] and not allowed[sign]
        resolved = not conflict and (allowed[sign] or banned)
        if actual != [conflict, banned, resolved]:
            raise ValueError('Normative classification differs')
        rows.append({'required_positive': rp, 'required_negative': rn, 'allowed_positive': ap,
            'allowed_negative': an, 'polarity': sign, 'results': actual})
    return {'truth_table': rows, 'execution_always_guarded': True}


def source_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    extra = '''r za[] a.r zb[] a.r zc[] a.r zd[] j[a].r ze[] b.r zf[b] c.r zg[] d.
q[k h74[k za[] k zb[] k zc[] k zd[] k ze[] p zf k zg[]]].
'''
    doc = candidate(text, extra)
    activities = ('first', 'second')
    domain = ('source', 'person', 'role', *activities, 'third', 'other')
    scenes = ('now', 'elsewhere')
    states = {'permitted': (False, False, True, False), 'banned': (False, True, False, False),
        'conflict': (False, True, True, False), 'unclassified': (False, False, False, False)}

    def run(labels=('banned', 'permitted'), population=activities, scope=activities, ratio=Fraction(1, 2),
            threshold=Fraction(1, 2), strict=False, variant='baseline'):
        assignment = dict(zip((*activities, 'third'), (states[label] for label in labels)))
        def bound(source, person, role, activity, desc, sign, context):
            actual = [source, person, role, symbol(desc), context]
            expected = ['source', 'person', 'role', mapping['dc'], 'now']
            names = ('source', 'person', 'role', 'description', 'context')
            if variant in names:
                expected[names.index(variant)] = 'elsewhere' if variant == 'context' else 'other'
            return actual == expected
        def rule(kind, *args):
            if not bound(*args) or args[3] not in assignment:
                return False
            if variant == 'unknown_norm':
                raise ValueError('Unassessed norm is not a negative fact')
            return assignment[args[3]][kind + (0 if args[-2] else 1)]
        model = guarded(doc)
        model.update(arithmetic(variant == 'bad_indicator'))
        model.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role',
            zd=lambda: SequenceValue(tuple(population), '"individual"'), ze=lambda: Fraction(ratio),
            zf=lambda x: x > threshold if strict else x >= threshold, zg=lambda: 'now',
            h7a=lambda *args: rule(0, *args), h7b=lambda *args: rule(2, *args))
        model[mapping['ca']] = lambda person, activity, context: person == 'person' and activity in scope and context == 'now'
        model[mapping['cb']] = lambda person, activity, role, context: (person, role, context) == ('person', 'role', 'now') and activity in scope
        model[mapping['cf']] = lambda person, role, context: (person, role, context) == ('person', 'role', 'now') and variant != 'wrong_office'
        return values(doc, model, domain, scenes)[0]

    rows = []
    for labels in product(states, repeat=2):
        for ratio in (Fraction(0), Fraction(1, 2), Fraction(1)):
            actual = run(labels=labels, ratio=ratio)
            expected = all(s in ('permitted', 'banned') for s in labels) and ratio == Fraction(labels.count('banned'), 2) and ratio >= Fraction(1, 2)
            if actual != expected:
                raise ValueError('Restriction degree differs: ' + str((labels, ratio, actual)))
            rows.append({'states': list(labels), 'ratio': str(ratio), 'result': actual})
    contrasts = {}
    for name, options, expected in (
        ('reordered', {'population': tuple(reversed(activities))}, True),
        ('missing_permitted_activity', {'population': ('first',), 'ratio': 1}, False),
        ('missing_banned_activity', {'population': ('second',), 'ratio': 0, 'threshold': 0}, False),
        ('duplicate', {'population': ('first', 'first', 'second')}, False),
        ('empty', {'population': (), 'scope': (), 'ratio': 0, 'threshold': 0}, False),
        ('out_of_scope', {'population': (*activities, 'other')}, False),
        ('unlisted_scope_member', {'scope': (*activities, 'other')}, False),
        ('negative_ratio', {'ratio': -1, 'threshold': -1}, False),
        ('ratio_over_one', {'ratio': 2}, False),
        ('all_permitted_zero', {'labels': ('permitted',) * 2, 'ratio': 0, 'threshold': 0}, True),
        ('all_banned_one', {'labels': ('banned',) * 2, 'ratio': 1}, True),
        ('strict_boundary', {'strict': True}, False),
        ('stricter_context', {'threshold': Fraction(3, 4)}, False),
        ('narrowed_scope', {'population': ('first',), 'scope': ('first',), 'ratio': 1}, True),
        ('banned_class_split', {'population': (*activities, 'third'), 'scope': (*activities, 'third'),
            'labels': ('banned', 'banned', 'permitted'), 'ratio': Fraction(2, 3)}, True),
        ('permitted_class_split', {'population': (*activities, 'third'), 'scope': (*activities, 'third'),
            'labels': ('banned', 'permitted', 'permitted'), 'ratio': Fraction(1, 3)}, False),
        *((name, {'variant': name}, False) for name in ('source', 'person', 'role', 'description', 'context', 'wrong_office', 'bad_indicator')),
    ):
        actual = run(**options)
        if actual != expected:
            raise ValueError('Restriction contrast differs: ' + str((name, actual)))
        contrasts[name] = actual
    try:
        run(variant='unknown_norm')
    except ValueError as exc:
        if 'Unassessed norm' not in str(exc):
            raise
    else:
        raise ValueError('Unknown norm accepted')
    return {'state_and_ratio_cases': rows, 'contrasts': contrasts, 'unknown_norm_refused': True,
        'actual_execution_and_author_meta_norms_guarded': True,
        'scope_narrowing_requires_independent_source_justification': True}


def alignment():
    old = json.loads((ROOT / 'reports/policy-norms-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(next(row for row in old['segments'] if 'Privatgebrauch' in row['source']))
    row['definitions'] = ['h7y', 'h7z', 'h72', 'h73', 'h74']
    row['review_ja'] = '明示的な禁止割合を、全対象の分類と固定した範囲・基準から記述する候補。活動の粒度と尺度の妥当性、頻度・程度の全意味・許可・留保への接続は未確定。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'restriction-degree'), (source_composed, 'kant-restriction-degree')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored restriction degree differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Restriction degree roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = [*documents, PARENT, 'data/restriction-degree-basis-v1.json', 'data/kant-restriction-degree-basis-v1.json',
        'scripts/compose_restriction_degree.py', 'scripts/check_restriction_degree.py', 'reports/policy-norms-v1.json',
        'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_finite_restriction_measure_not_complete_degree_semantics',
        'documents': documents, 'classification': classification_checks(), 'source': source_checks(),
        'alignment': alignment(), 'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
        'new_primitives': 0, 'notation_size': {'canonical_source_document_characters': len(text),
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
            raise ValueError('Restriction degree report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Explicit normative classification and independently scoped restriction degree checked')


if __name__ == '__main__':
    main()
