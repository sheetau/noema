"""Check normative target identity even when execution contents coincide."""
import argparse
from itertools import product
import hashlib
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_described_norms import ROOT, PARENT, TRUE, generic_composed, source_composed

REPORT = ROOT / 'reports/described-norms-v1.json'
GENERIC_EXTRA = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.r zf[] c.
r zg[a a a a i[h[a a] e] c d] c.r zh[a a a a i[h[a a] e] c d] c.r zi[a a d] c.
d zj[person a activity a] e[b scene[k zi[v person v activity v scene]]].
d zk[person a activity a] e[k zj[v person v activity]].
'''
GENERIC_ARGS = 'k za[] k zb[] k zc[] k zd[] r[p zj] k zf[] k ze[] p zg p zh'


def generic_checks():
    text = generic_composed()[0]
    doc = candidate(text, GENERIC_EXTRA + ''.join('q[k ' + name + '[' + GENERIC_ARGS + ']].' for name in ('rdm', 'rdn', 'rdo', 'rdp', 'rdq')))
    domain, scenes = ('source', 'person', 'role', 'activity', 'other'), ('now', 'elsewhere')
    count = 0
    def model(required, allowed, actual, sign, variant='baseline'):
        def bound(source, person, role, activity, desc, polarity, context):
            row = [source, person, role, activity, symbol(desc), context]
            expected = ['source', 'person', 'role', 'activity', 'zj', 'now']
            fields = ('source', 'person', 'role', 'activity', 'description', 'context')
            for i, field in enumerate(fields):
                if variant == field:
                    expected[i] = 'zk' if field == 'description' else 'elsewhere' if field == 'context' else 'other'
            return row == expected
        result = guarded(doc)
        result.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'activity',
            ze=lambda: 'now', zf=lambda: sign,
            zg=lambda *args: required[args[-2]] and bound(*args),
            zh=lambda *args: allowed[args[-2]] and bound(*args),
            zi=lambda person, activity, scene: actual and (person, activity, scene) == ('person', 'activity', 'now'))
        return result
    for rp, rn, ap, an, actual, sign in product((False, True), repeat=6):
        required, allowed = {True: rp, False: rn}, {True: ap, False: an}
        observed = values(doc, model(required, allowed, actual, sign), domain, scenes)
        expected = [allowed[sign] and not required[not sign], required[sign] and required[not sign],
            allowed[sign] and required[not sign], not required[not sign], required[sign] and actual != sign]
        if observed != expected:
            raise ValueError('Normative polarity or performance collapsed')
        count += 1
    bindings = {}
    for variant in ('source', 'person', 'role', 'activity', 'description', 'context'):
        observed = values(doc, model({True: True, False: False}, {True: True, False: False}, False, True, variant), domain, scenes)
        if observed != [False, False, False, True, False]:
            raise ValueError('Described normative target mismatch: ' + variant)
        bindings[variant] = observed
    no_evaluation = candidate(text, GENERIC_EXTRA + ''.join('q[k ' + name + '[' + GENERIC_ARGS + ']].' for name in ('rdm', 'rdn', 'rdo', 'rdp')))
    test_model = model({True: True, False: False}, {True: True, False: True}, False, True)
    def unknown(*args):
        raise ValueError('Unassessed execution')
    test_model['zi'] = unknown
    if values(no_evaluation, test_model, domain, scenes) != [True, False, False, True]:
        raise ValueError('Permission required execution knowledge')
    try:
        values(doc, test_model, domain, scenes)
    except ValueError as exc:
        if 'Unassessed execution' not in str(exc):
            raise
    else:
        raise ValueError('Unknown execution became known nonperformance')
    aliases = candidate(text, GENERIC_EXTRA + '''
q[e[k zj[k zb[] k zd[]]][k zk[k zb[] k zd[]]]].q[u[e[r[p zj]][r[p zk]]]].''')
    alias_result = values(aliases, model({True: False, False: False}, {True: False, False: False}, False, True), domain, scenes)
    if alias_result != [True, True]:
        raise ValueError('Equivalent execution contents collapsed described targets')
    return {'polarity_state_cases': count, 'binding_cases': bindings,
        'norms_without_execution_assessment': True, 'unassessed_fulfillment_refused': True,
        'equal_contents_with_distinct_descriptions': alias_result}


def source_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    dc = mapping['dc']
    extra = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] a.r zf[] a.r zg[] d.r zh[] a.r zj[] a.r zk[] a.
r zl[a d] c.d zi[person a] f[j s[b scene[k zl[v person v scene]]]].
d zm[person a activity a] e[k ''' + dc + '''[v person v activity]].
'''
    def args(activity):
        return 'k za[] k ' + activity + '[] k zc[] k zd[] k ze[] k zf[] r[p zi] k zg[] k zh[]'
    queries = ''.join('q[k ' + name + '[' + args(activity) + ']].' for name, activity in (
        ('h6y', 'zb'), ('h6y', 'zj'), ('h7c', 'zb'), ('h7c', 'zj')))
    queries += 'q[t[k h7d[k zh[] k za[] k zc[]]][k zg[]]].q[t[k h7e[k zh[] k za[] k zk[]]][k zg[]]].'
    queries += 'q[e[k ' + dc + '[k za[] k zb[]]][k ' + dc + '[k za[] k zj[]]]].'
    doc = candidate(text, extra + queries)
    domain = ('person', 'reader', 'scholar', 'officer', 'first', 'second', 'duty', 'audience', 'channel', 'topic', 'authority')
    scenes = ('now', 'other')
    def model_for(target_doc, variant):
        permitted = {'first'} if variant not in ('both_allowed', 'both_allowed_one_forbidden', 'only_second', 'no_permission') else (
            {'first', 'second'} if variant.startswith('both_allowed') else {'second'} if variant == 'only_second' else set())
        forbidden = {'first'} if variant == 'both_allowed_one_forbidden' else set()
        def bound(source, person, role, activity, desc, polarity, context):
            return (source, person, symbol(desc), context) == (
                'topic' if variant == 'wrong_source' else 'authority', 'person',
                'zm' if variant == 'different_execution_description' else dc,
                'other' if variant == 'wrong_context' else 'now') and role == ('officer' if activity == 'duty' else 'scholar')
        def require(source, person, role, activity, desc, polarity, context):
            return bound(source, person, role, activity, desc, polarity, context) and not polarity and (
                activity in forbidden or activity == 'duty' and variant != 'no_private_prohibition')
        def allow(source, person, role, activity, desc, polarity, context):
            return bound(source, person, role, activity, desc, polarity, context) and polarity and activity in permitted
        def execution(person, activity, scene):
            return False
        old_binding = ('topic' if variant == 'wrong_source' else 'authority', 'person', 'scholar',
            'other' if variant == 'wrong_context' else 'now')
        old = {
            'aa': lambda source, person, role, content, scene: (source, person, role, scene) == old_binding
                and bool(forbidden) and content.values == (True, True),
            'ab': lambda source, person, role, content, scene: (source, person, role, scene) == old_binding
                and bool(permitted) and content.values == (False, False),
            'ca': lambda person, activity, scene: person == 'person' and activity in ('first', 'second', 'duty'),
            'cb': lambda person, activity, role, scene: person == 'person' and (
                activity in ('first', 'second') and role == 'scholar' or activity == 'duty' and role == 'officer'),
            'cc': lambda activity, audience, scene: variant != 'no_public_activities' and activity in ('first', 'second') and audience == 'audience',
            'cd': lambda role, scene: role == 'scholar', 'ce': lambda audience, scene: audience == 'audience',
            'cf': lambda person, role, scene: (person, role) == ('person', 'officer'), 'cg': execution}
        result = guarded(target_doc)
        result.update(za=lambda: 'person', zb=lambda: 'first', zc=lambda: 'scholar', zd=lambda: 'audience',
            ze=lambda: 'channel', zf=lambda: 'topic', zg=lambda: 'now', zh=lambda: 'authority', zj=lambda: 'second', zk=lambda: 'officer',
            aa=lambda person: person in ('person', 'reader'),
            h6n=lambda person, context: (person, context) == ('reader', 'now'),
            h6t=lambda audience, person, context: (audience, person, context) == ('audience', 'reader', 'now'),
            h6u=lambda activity, channel, subject, desc, context: activity in ('first', 'second') and (
                channel, subject, symbol(desc), context) == ('channel', 'topic', 'zi', 'now'), h7a=require, h7b=allow)
        result.update({mapping[name]: callback for name, callback in old.items()})
        return result
    rows = {}
    expected_rows = {
        'baseline': [True, True, True, False, False, True, True],
        'both_allowed': [True, True, True, True, True, True, True],
        'only_second': [True, True, False, True, False, True, True],
        'both_allowed_one_forbidden': [False, False, False, True, False, True, True],
        'no_permission': [False, False, False, False, False, True, True],
        'different_execution_description': [True, True, False, False, False, False, True],
        'wrong_source': [False, False, False, False, False, False, True],
        'wrong_context': [False, False, False, False, False, False, True],
        'no_public_activities': [False, False, False, False, True, True, True],
        'no_private_prohibition': [True, True, True, False, False, False, True],
    }
    for variant, expected in expected_rows.items():
        actual = values(doc, model_for(doc, variant), domain, scenes)
        if actual != expected:
            raise ValueError('Normative target identity differs: ' + str((variant, actual)))
        rows[variant] = actual
    only_new = candidate(text, extra + 'q[k h7c[' + args('zb') + ']].')
    model = model_for(only_new, 'baseline')
    def unavailable(*args):
        raise ValueError('Unassessed old content norm or execution')
    for name in (mapping['aa'], mapping['ab'], mapping['cg']):
        model[name] = unavailable
    if values(only_new, model, domain, scenes) != [True]:
        raise ValueError('Described permission required extensional norms')
    model['h7b'] = unavailable
    try:
        values(only_new, model, domain, scenes)
    except ValueError as exc:
        if 'Unassessed old content norm' not in str(exc):
            raise
    else:
        raise ValueError('Unknown described permission became a known value')
    return {'cases': rows, 'new_permission_does_not_evaluate_old_norms_or_execution': True,
        'unknown_described_permission_refused': True,
        'comparison_order': ['old_first', 'old_second', 'new_first', 'new_second', 'all_public_allowed', 'some_private_prohibited', 'same_execution_content']}


def alignment():
    prior = json.loads((ROOT / 'reports/public-use-link-v1.json').read_text(encoding='utf-8'))['alignment']
    rows = []
    for old in prior['segments']:
        if 'muß jederzeit frei sein' in old['source'] or old['source'].startswith('der Privatgebrauch'):
            row = dict(old)
            row['definitions'] = ['h7d'] if 'muß jederzeit frei sein' in old['source'] else ['h7e']
            row['review_ja'] = '行為と実行記述を保持する許可・禁止へ接続した。著者の要求・制限への許可、頻度・程度・留保の全文意味は未完。'
            rows.append(row)
    return {'segments': rows, 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'described-norms'), (source_composed, 'kant-described-norms')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored described norms differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Described norm roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/described-norms-basis-v1.json', 'data/kant-described-norms-basis-v1.json',
        'scripts/compose_described_norms.py', 'scripts/check_described_norms.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'reports/public-use-link-v1.json']
    return json.loads(json.dumps({'status': 'partial_description_sensitive_norms_not_complete_public_freedom',
        'documents': documents, 'generic': generic_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
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
            raise ValueError('Described norms report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Action identity, description, polarity and fulfillment checked separately')


if __name__ == '__main__':
    main()
