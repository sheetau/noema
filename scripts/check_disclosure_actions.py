"""Check permission for composed disclosure independently of its performance."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_disclosure_actions import ROOT, PARENT, PARENT_EXAMPLE, LIBRARY, EXAMPLE, BASIS, BUNDLE, FIXED, build, basis
from scripts.compose_candid_assessments import DISCLOSURE
from scripts.compose_described_norms import TRUE
from scripts.check_candid_assessments import PEOPLE, POINTS, RECORDS, setup as assessment_setup

REPORT = ROOT / 'reports/disclosure-actions-v1.json'
FALSE = 'u[' + TRUE + ']'
REFS = dict(role='k jdrole[]', audience='p jdaudience', subject='k jdsubject[]', recipient='k jdrecipient[]',
            channel='k jdchannel[]', voices='p jdvoices', judgments='p jdjudgments', matters='p jdmatters',
            linked='p jdlinked', candidates='p jdcandidates')


def explicit_target(records, signs, critical):
    """Write the closed expression separately, without running rsi--rso."""
    sequence, negative = 'l[a][]', FALSE
    for name in records:
        sign = TRUE if signs[0 if name in ('first', 'outside') else 1] else FALSE
        sequence = 'c[i[prefix j[a] item a][m[v prefix][l[a][v item]]]][' + sequence + ' k jd' + name + '[]]'
        negative = 'c[i[previous c sign c][x[v previous][u[v sign]]]][' + negative + ' ' + sign + ']'
    result = 'c[p rsm][' + sequence + ' p jdscope ' + (TRUE if critical else FALSE) + ' ' + negative + ']'
    for name in records:
        index = 0 if name in ('first', 'outside') else 1
        criterion = 'p ' + ('jdstandardone', 'jdstandardtwo')[index]
        sign = TRUE if signs[index] else FALSE
        item = 'c[p rsh][' + criterion + ' r[' + criterion + '] ' + sign + ' k jd' + name + '[] '
        item += 'r[c[p rsa][' + criterion + ' ' + sign + ']] ' + ' '.join(REFS[n] for n, _ in FIXED) + ']'
        result = 'c[p rsj][' + result + ' ' + item + ']'
    return result


@lru_cache(maxsize=1)
def setup():
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))
    doc['declarations'].insert(0, parse('p:r jdoutside[] a.')['declarations'][0])
    original = next(d for d in doc['declarations'] if d['name'] == 'jdstandardone')
    alias = deepcopy(original)
    alias['name'] = 'jdstandardalias'
    doc['declarations'].append(alias)
    return parse(format_graph(doc, 'compact'))


def values(records=RECORDS, scope=RECORDS, signs=(True, False), candidate=(True, False), actual=(True, True),
           delivered=(True, True), judgments=(True, True), candidates=(True, True), critical=True,
           permission=True, opposed=False, variant='baseline', indices=None, memoize=True):
    doc = deepcopy(setup())
    for decl in doc['declarations']:
        if decl['name'] in ('jdcomplete', 'jdcritical'):
            seq = decl['body']['arguments'][[n for n, _ in DISCLOSURE].index('records')]
            seq['items'] = [dict(kind='call', symbol='jd' + name, arguments=[]) for name in records]
        if decl['name'] == 'jdaction':
            seq = decl['body']['arguments'][0]
            seq['items'] = [dict(kind='quote', body=dict(kind='call', symbol='jd' + name, arguments=[])) for name in records]
            crit = decl['body']['arguments'][[n for n, _ in BUNDLE].index('critical')]
            crit['body'] = assessment_setup()['signs'][0 if critical else 1]
    if not critical:
        doc['statements'][2]['body']['symbol'] = 'jdcomplete'
    text = explicit_target(records, signs, critical)
    doc = parse(format_graph(doc, 'compact') + 'q[e[k jdaction[]][r[' + text + ']]].')
    target = doc['statements'][-1]['body']['arguments'][1]['body']
    if variant == 'wrong_target':
        changed = parse(format_graph(doc, 'compact') + 'q[e[r[' + explicit_target(tuple(reversed(records)), signs, critical) + ']][r[' + text + ']]].')
        target = changed['statements'][-1]['body']['arguments'][0]['body']
    if indices is not None:
        doc['statements'] = [doc['statements'][i] for i in indices]
    sign_nodes = assessment_setup()['signs']
    record_index = {'first': 0, 'second': 1, 'outside': 0}

    def forbidden(*args):
        raise AssertionError('Unexpected primitive in disclosure action')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def truth(index, subject, point):
        if variant == 'unknown_truth':
            raise ValueError('Unknown criterion evaluation')
        return subject == 'topic' and (actual[index] if point == 'anchor' else candidate[index])
    def choose(record, left, right):
        return (left, right)[record_index[record]]
    def sign(record, positive, negative):
        return positive if signs[record_index[record]] else negative
    def from_code(code):
        if variant == 'unknown_selector':
            raise ValueError('Unknown assessment selector')
        body = json.loads(code.syntax)
        return body['symbol'][2:]
    def selected(record, point):
        if variant == 'unknown_scope':
            raise ValueError('Unknown disclosure scope')
        return record in scope and point == 'anchor'
    def owner(person, record, point):
        if record not in record_index:
            return False
        index = record_index[record]
        return judgments[index] and (person, point) == ('other' if variant == 'other_person' and index == 1 else 'person', 'anchor')
    def matters(record, subject, point):
        return record in record_index and (subject, point) == ('othertopic' if variant == 'other_subject' and record_index[record] == 1 else 'topic', 'anchor')
    def linked(record, code, polarity, point):
        if record not in record_index:
            return False
        index = record_index[record]
        symbol = 'jdstandardalias' if variant == 'other_criterion' and index == 0 else ('jdstandardone', 'jdstandardtwo')[index]
        expected = not signs[index] if variant == 'wrong_polarity' and index == 1 else signs[index]
        return point == 'anchor' and polarity == expected and json.loads(code.syntax) == dict(kind='function_ref', symbol=symbol)
    def chosen(record, context, point):
        if variant == 'unknown_candidates':
            raise ValueError('Unknown judgment candidates')
        return record in record_index and candidates[record_index[record]] and (context, point) == ('anchor', 'candidate')
    messages = []
    for index in (0, 1):
        message_sign = not signs[index] if variant == 'wrong_message' and index == 1 else signs[index]
        messages.append(dict(kind='apply', function=dict(kind='function_ref', symbol='rsa'), arguments=[
            dict(kind='function_ref', symbol=('jdstandardone', 'jdstandardtwo')[index]), sign_nodes[0 if message_sign else 1]]))
    def message_index(code):
        syntax = json.loads(code.syntax)
        return next((i for i, message in enumerate(messages) if syntax == message), None)
    def conveys(act, reader, subject, code, point):
        if variant == 'unknown_presentation':
            raise ValueError('Unknown public presentation')
        index = message_index(code)
        return index is not None and delivered[index] and (act, reader, subject, point) == (
            'otheract' if variant == 'other_activity' and index == 1 else 'act', 'reader', 'topic', 'anchor')
    def voices(person, act, principal, role, subject, code, point):
        index = message_index(code)
        return index is not None and (person, act, principal, role, subject, point) == ('person', 'act',
            'other' if variant == 'other_principal' and index == 1 else 'person', 'role', 'topic', 'anchor')
    def allowed(ruler, person, role, act, code, positive, point):
        return permission and (ruler, person, role, act, positive, point) == (
            'ruler', 'person', 'other' if variant == 'wrong_role' else 'role', 'act', True, 'anchor') and json.loads(code.syntax) == target
    def required(ruler, person, role, act, code, positive, point):
        return opposed and (ruler, person, role, act, positive, point) == (
            'ruler', 'person', 'role', 'act', False, 'anchor') and json.loads(code.syntax) == target
    def first_record():
        if variant == 'unknown_record':
            raise ValueError('Unknown judgment record')
        return 'first'
    model.update(jdfirst=first_record, jdsecond=lambda: 'second', jdoutside=lambda: 'outside', jdperson=lambda: 'person',
        jdact=lambda: 'act', jdsubject=lambda: 'topic', jdrole=lambda: 'role', jdrecipient=lambda: 'world', jdchannel=lambda: 'channel', jdcontext=lambda: 'anchor',
        jdruler=lambda: 'ruler', jdallowed=allowed, jdrequired=required,
        jdmetone=lambda subject, point: truth(0, subject, point), jdmettwo=lambda subject, point: truth(1, subject, point),
        jdscope=selected, jdchoosecriterion=choose, jdchoosepolarity=sign,
        jdselectcriterion=lambda code, left, right: choose(from_code(code), left, right),
        jdselectpolarity=lambda code, positive, negative: sign(from_code(code), positive, negative),
        jdjudgments=owner, jdmatters=matters, jdlinked=linked, jdcandidates=chosen,
        jdaudience=lambda reader: reader == 'reader', jdvoices=voices,
        dg=lambda act, point: (act, point) == ('act', 'anchor'), f3=lambda person, act, point: (person, act, point) == ('person', 'act', 'anchor'), f2=conveys,
        ca=lambda person, act, point: (person, act, point) == ('person', 'act', 'anchor'),
        cb=lambda person, act, role, point: (person, act, role, point) == ('person', 'act', 'role', 'anchor'),
        cc=lambda act, recipient, point: (act, recipient, point) == ('act', 'world', 'anchor'), cd=lambda role, point: role == 'role',
        ce=lambda recipient, point: recipient == 'world', aa=lambda person: person in ('person', 'reader'),
        h6n=lambda reader, point: reader == 'reader', h6t=lambda recipient, reader, point: (recipient, reader) == ('world', 'reader'),
        h6u=lambda act, channel, subject, code, point: message_index(code) is not None and (act, channel, subject, point) == ('act', 'channel', 'topic', 'anchor'))
    return [r['value'] for r in evaluate_document(doc, individuals=PEOPLE + ('ruler',), situations=POINTS, primitives=model,
        max_steps=10_000_000, memoize_definitions=memoize, memoize_expressions=memoize)]


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    library = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    assert library['declarations'][:len(parent['declarations'])] == parent['declarations']
    additions = library['declarations'][len(parent['declarations']):]
    assert len(additions) == 8 and all(d['kind'] == 'definition' for d in additions)
    matrix = []
    for first, second, deliver1, deliver2, permit, oppose in product((False, True), repeat=6):
        result = values(candidate=(first, second), delivered=(deliver1, deliver2), permission=permit, opposed=oppose)
        performed = first and not second and deliver1 and deliver2
        assert result == [permit and not oppose, performed, performed, True]
        matrix.append(dict(candidate=[first, second], delivered=[deliver1, deliver2], permission=permit, opposed=oppose, result=result))
    contrasts = {}
    for variant in ('other_person', 'other_subject', 'other_criterion', 'wrong_polarity', 'wrong_message', 'other_activity', 'other_principal'):
        result = values(variant=variant)
        assert result == [True, False, False, True]
        contrasts[variant] = result
    for variant in ('wrong_target', 'wrong_role'):
        result = values(variant=variant)
        assert result == [False, True, True, True]
        contrasts[variant] = result
    unknown = {}
    for variant in ('unknown_truth', 'unknown_scope', 'unknown_candidates', 'unknown_presentation', 'unknown_record'):
        result = values(variant=variant, indices=(0, 3))
        assert result == [True, True]
        unknown[variant] = result
    uncached = values(memoize=False)
    assert uncached == values() == [True] * 4
    paths = [PARENT, PARENT_EXAMPLE, LIBRARY, EXAMPLE, BASIS, 'examples/v016/kant-comparative-speech.noema',
        'scripts/compose_disclosure_actions.py', 'scripts/check_disclosure_actions.py', 'tests/test_disclosure_actions.py',
        'scripts/compose_candid_assessments.py', 'scripts/check_candid_assessments.py',
        'scripts/compose_described_norms.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py']
    return dict(status='constructed_disclosure_permission_separate_from_performance', documents=documents,
        inherited_definitions_unchanged=True, new_library_primitives=0, roundtrips=True,
        finite_interpretation=dict(matrix=matrix, contrasts=contrasts, unknown_unexecuted=unknown, uncached=uncached),
        limitations=basis()['limitations'], verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == result
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Constructed disclosure actions and permission checked independently')


if __name__ == '__main__':
    main()
