"""Check deficiency claims, intended assessment and actual judgment separately."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_closed_policies import quoted
from scripts.check_rod_setup import guarded
from scripts import check_office_speech as office
from scripts.compose_public_assessment import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/public-assessment-v1.json'


def syntax(quotation):
    return json.dumps(quotation['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def finite_checks():
    text = generic_composed()[0]
    rows = []
    lists = ((), ('zc',), ('zd',), ('zc', 'zd'), ('zd', 'zc'), ('zc', 'zc', 'zd'))
    for satisfied in product((False, True), repeat=2):
        for names in lists:
            criteria = 'l[h[a] e][' + ' '.join('p ' + name for name in names) + ']'
            doc = parse(text + 'r za[] a.r zb[] d.r zc[a] e.r zd[a] e.'
                'q[t[k ret[k za[] ' + criteria + ']][k zb[]]].'
                'q[u[e[c[k reu[' + criteria + ']][k za[]]][c[k rev[' + criteria + ']][k za[]]]]].')
            model = {'za': lambda: 'object', 'zb': lambda: 'now',
                'zc': lambda subject: Content(('now',), (satisfied[0] if subject == 'object' else True,)),
                'zd': lambda subject: Content(('now',), (satisfied[1] if subject == 'object' else True,))}
            actual = values(doc, model, ('object', 'other'), ('now',))
            expected = [any(not satisfied[('zc', 'zd').index(name)] for name in names), True]
            if actual != expected:
                raise ValueError('Criterion failures or message force collapsed')
            rows.append({'satisfied': list(satisfied), 'criteria': list(names), 'results': actual})
    # With an unknown second condition, even a known failure is not silently
    # treated as a fully assessed criterion list by this eager evaluator.
    unknown = {**model, 'zc': lambda subject: Content(('now',), (False,)), 'zd': guarded(doc)['zd']}
    try:
        values(doc, unknown, ('object', 'other'), ('now',))
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):
            raise
    else:
        raise ValueError('Unknown criterion was silently filled in')
    return {'cases': rows, 'unknown_criterion_refused': True}


def source_setup():
    text = source_composed()[0]
    base = candidate(text, office.EXTRA + 'r zs[a] e.r zt[a] e.')
    probe = candidate(text, office.EXTRA + 'r zs[a] e.r zt[a] e.q[e[r[l[h[a] e][p zs p zt]]][r[l[h[a] e][p zs p zt]]]].')
    criteria = probe['statements'][0]['body']['arguments'][0]
    message = apply_description(base, quoted('function_ref', 'reu'), [criteria])
    goal = apply_description(base, quoted('function_ref', 'hzx'), [quoted('call', 'zg'), quoted('call', 'zi'),
        {'kind': 'quote', 'body': message}])
    fields = [quoted('call', n)['body'] for n in ('za', 'ze', 'zf', 'zg', 'zh', 'zi')]
    ctx = quoted('call', 'zk')['body']
    statement = {'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'hzy',
        'arguments': [*fields, message, goal, ctx]}}
    # Use ordinary surface syntax for truth application to avoid relying on
    # internal spellings of content evaluation nodes.
    temp = {**base, 'statements': [statement]}
    doc = parse(format_graph(temp, 'compact') + 'q[t[k ret[k zi[] l[h[a] e][p zs p zt]]][k zk[]]].'
        'q[t[k zzq[k za[] k ze[]]][k zk[]]].')
    # Build the goal truth query with the parser and replace only its quote.
    query = candidate(text, 'q[t[s[r[b scene[e[n p a b][n p a b]]]]][k wh[]]].')['statements'][0]
    # The actual AST shape is obtained from a parsed expression, not invented.
    query['body']['content']['description'] = goal
    query['body']['situation'] = ctx
    doc['statements'].insert(1, query)
    return parse(format_graph(doc, 'compact')), message, goal


def source_checks():
    doc, message, goal = source_setup()
    domain = (*office.DOMAIN, 'judgment')
    def model_for(bits=(True, False, False, False), variant='baseline'):
        intended, judged, defective, performed = bits
        model = office.model_for(doc, (True, False, False, False, performed))
        model.update(
            zs=lambda subject: Content(office.SCENES, (not defective if subject == 'topic' else True, True)),
            zt=lambda subject: Content(office.SCENES, (True, True)))
        def publication(activity, channel, subject, description, context):
            return (activity, channel, subject, description.syntax, context) == ('speech', 'channel', 'topic', syntax(message), 'now')
        def intention(actor, activity, description, context):
            expected = ['person', 'speech', syntax(goal), 'now']
            for i, field in enumerate(('purpose_actor', 'purpose_activity', 'purpose_description', 'purpose_context')):
                if variant == field:
                    expected[i] = 'elsewhere' if i == 3 else 'other'
            return intended and [actor, activity, description.syntax, context] == expected
        def assess(judgment, subject, description, context):
            expected = ['judgment', 'topic', syntax(message), 'now']
            for i, field in enumerate(('judgment_event', 'judgment_subject', 'judgment_description', 'judgment_context')):
                if variant == field:
                    expected[i] = 'elsewhere' if i == 3 else 'other'
            return [judgment, subject, description.syntax, context] == expected
        model.update(h6u=publication, hzu=intention, hzv=assess,
            fa=lambda person, judgment, context: judged and (person, judgment, context) == (
                'other' if variant == 'nonreader_judges' else 'reader', 'judgment', 'now'),
            fb=lambda judgment, subject, context: (judgment, subject, context) == ('judgment', 'topic', 'now'))
        return model
    rows = []
    for bits in product((False, True), repeat=4):
        actual = values(doc, model_for(bits), domain, office.SCENES)
        if actual != list(bits):
            raise ValueError('Purpose, judgment, truth and performance collapsed: ' + str((bits, actual)))
        rows.append({'states': list(bits), 'results': actual})
    contrasts = {}
    for variant in ('purpose_actor', 'purpose_activity', 'purpose_description', 'purpose_context',
            'judgment_event', 'judgment_subject', 'judgment_description', 'judgment_context', 'nonreader_judges'):
        actual = values(doc, model_for((True, True, False, False), variant), domain, office.SCENES)
        expected = [False, True, False, False] if variant.startswith('purpose_') else [True, False, False, False]
        if actual != expected:
            raise ValueError('Judgment or purpose target differs: ' + str((variant, actual)))
        contrasts[variant] = actual
    only_purpose = {**doc, 'statements': doc['statements'][:1]}
    model = model_for()
    for name in ('fa', 'fb', 'hzv', 'zs', 'zt', 'cg', 'f2', 'h6e', 'h6g'):
        model[name] = guarded(doc)[name]
    if values(only_purpose, model, domain, office.SCENES) != [True]:
        raise ValueError('Publication purpose implied assessment, receipt or truth')
    for selected, name in ((only_purpose, 'hzu'), ({**doc, 'statements': doc['statements'][1:2]}, 'hzv')):
        missing = model_for((True, True, False, False))
        missing[name] = guarded(doc)[name]
        try:
            values(selected, missing, domain, office.SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown intention or judgment target was silently completed')
    return {'cases': rows, 'contrasts': contrasts, 'message_description': message, 'goal_description': goal,
        'purpose_without_execution_receipt_judgment_or_truth': True, 'unknown_intention_and_judgment_refused': True}


def alignment():
    row = deepcopy(json.loads((ROOT / 'reports/office-speech-v1.json').read_text(encoding='utf-8'))['alignment']['segments'][0])
    row['definitions'] = ['ret', 'reu', 'rev', 'hzw', 'hzx', 'hzy']
    row['review_ja'] = '欠陥の一つの読みを、明示した達成条件の不充足を述べる発話として構成する。同じ発話を公衆の判断へ示す目的と実際の判断を分けた。軍務の概念、条件の適切さ、注記の全内容、原文の全意味との一致は未確認。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'criterion-failures'), (source_composed, 'kant-public-assessment')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored public assessment differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Public assessment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, 'data/criterion-failures-basis-v1.json', 'data/kant-public-assessment-basis-v1.json',
        'scripts/compose_public_assessment.py', 'scripts/check_public_assessment.py', 'scripts/check_office_speech.py',
        'scripts/check_closed_policies.py', 'reports/office-speech-v1.json',
        'noema/description_templates.py', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_criterion_failure_and_purpose_of_public_assessment',
        'documents': documents, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_primitives': 2, 'new_source_assertions': 0,
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
            raise ValueError('Public assessment report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Criterion failures, publication purpose and actual assessment checked')


if __name__ == '__main__':
    main()
