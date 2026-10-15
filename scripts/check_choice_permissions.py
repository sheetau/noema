"""Check independent choices, complete candidate scope and quoted force order."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_choice_permissions import ROOT, LIBRARY, EXAMPLE, BASIS, build, basis

REPORT = ROOT / 'reports/choice-permissions-v1.json'
ACTS = {'c': ('x', 'x'), 'd': ('x', 'y'), 'e': ('y', 'x'), 'f': ('y', 'y')}
DOMAIN = ('p', 'q', 'x', 'y', 'c', 'd', 'e', 'f')

@lru_cache(maxsize=1)
def setup():
    return parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))

def values(*, missing=(), denied=(), opposed=(), obeys=True, topics=('x', 'y'), extents=('x', 'y'),
           people=('p',), denied_pairs=(), variant='baseline', indices=None, memoize=True):
    doc = deepcopy(setup())
    if indices is not None: doc['statements'] = [doc['statements'][i] for i in indices]
    def select(person, activity, context):
        return person in people and activity in ACTS and activity not in missing and context == 'anchor'
    def subject(person, activity, context):
        return ACTS.get(activity, ('x', 'x'))[0] if context == 'anchor' else 'q'
    def extent(person, activity, context):
        return ACTS.get(activity, ('x', 'x'))[1] if context == 'anchor' else 'q'
    def forbidden(*args): raise AssertionError('Quoted or permitted action was executed')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def fields(source, person, role, activity, code, positive, point):
        expected = dict(source='q', person=person, role='q', activity=activity, point=point)
        if variant == 'wrong_source': expected['source'] = 'x'
        if variant == 'wrong_person': expected['person'] = 'q'
        if variant == 'wrong_role': expected['role'] = 'x'
        if variant == 'wrong_activity': expected['activity'] = 'p'
        if variant == 'wrong_point': expected['point'] = 'later'
        return (source, person, role, activity, point) == tuple(expected.values()) and person in people and activity in ACTS and \
            code.rank == 0 and json.loads(code.syntax) == dict(kind='function_ref', symbol='jdaction')
    def allowed(source, person, role, activity, code, positive, point):
        if variant == 'unknown_permission': raise ValueError('Unknown permission')
        return fields(source, person, role, activity, code, positive, point) and positive and activity not in denied and (person, activity) not in denied_pairs
    def required(source, person, role, activity, code, positive, point):
        return fields(source, person, role, activity, code, positive, point) and not positive and activity in opposed
    def obedience(point):
        if variant == 'unknown_obedience': raise ValueError('Unknown obedience')
        return obeys if point == 'anchor' else not obeys
    model.update(jdpopulation=lambda person: person in people,
        jdtopics=lambda person, topic, context: person in people and topic in topics and context == 'anchor',
        jdextents=lambda person, amount, context: person in people and amount in extents and context == 'anchor',
        jdcandidates=select, jdsubject=subject, jdextent=extent, jdanchor=lambda: 'anchor', jdsource=lambda: 'q',
        jdroles=lambda person, activity, context: 'q', jdrequired=required, jdallowed=allowed, jdobeys=obedience)
    if variant == 'unknown_scope':
        def unknown(*args): raise ValueError('Unknown scope')
        model['jdtopics'] = unknown
    result = evaluate_document(doc, individuals=DOMAIN, situations=('anchor', 'later'), primitives=model,
        max_steps=5_000_000, memoize_definitions=memoize, memoize_expressions=memoize)
    return [row['value'] for row in result]

def quotation_mutation(kind):
    doc = deepcopy(setup())
    clause = next(d for d in doc['declarations'] if d['name'] == 'rtv')
    items = clause['body']['items']
    if kind == 'reversed': items.reverse()
    elif kind == 'duplicate': items[1] = deepcopy(items[0])
    elif kind == 'omit': items.pop()
    elif kind == 'permission_as_directive': items[0]['function']['body']['body']['force'] = 'direct'
    elif kind == 'obedience_as_assertion': items[1]['function']['body']['body']['force'] = 'assert'
    elif kind == 'swapped_contents':
        items[0]['arguments'], items[1]['arguments'] = items[1]['arguments'], items[0]['arguments']
    doc = parse(format_graph(doc, 'compact'))
    doc['statements'] = [doc['statements'][3]]
    def forbidden(*args): raise AssertionError('Quoted content executed during comparison')
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=('anchor', 'later'),
        primitives={d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'})]

def build_report():
    documents = {}
    for name, text in build().items():
        assert (ROOT / name).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        documents[name] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text))
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    matrix = []
    for missing, denied, opposed, obeys in product((False, True), repeat=4):
        result = values(missing=('f',) if missing else (), denied=('f',) if denied else (),
            opposed=('f',) if opposed else (), obeys=obeys)
        allowed = missing or not (denied or opposed)
        assert result == [not missing, allowed, not missing and allowed, True, obeys]
        matrix.append(dict(missing=missing, denied=denied, opposed=opposed, obeys=obeys, result=result))
    contrasts = {name: values(variant=name) for name in ('wrong_source', 'wrong_person', 'wrong_role', 'wrong_activity', 'wrong_point')}
    assert all(r == [True, False, False, True, True] for r in contrasts.values())
    empty = values(topics=(), missing=tuple(ACTS), denied=tuple(ACTS))
    assert empty == [True, True, True, True, True]
    for unknown in ('unknown_permission', 'unknown_obedience', 'unknown_scope'):
        assert values(variant=unknown, indices=(3,)) == [True]
    mutations = {kind: quotation_mutation(kind) for kind in ('reversed', 'duplicate', 'omit', 'permission_as_directive', 'obedience_as_assertion', 'swapped_contents')}
    assert all(v == [False] for v in mutations.values())
    assert values(memoize=False) == values()
    paths = [LIBRARY, EXAMPLE, BASIS, 'examples/v016/kant-focused-permission.noema',
        'scripts/compose_choice_permissions.py', 'scripts/check_choice_permissions.py', 'tests/test_choice_permissions.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py']
    return dict(status='choice_scope_and_quoted_sequence_basis_not_source_translation', documents=documents,
        new_definitions=5, new_library_primitives=0, roundtrips=True, matrix=matrix, contrasts=contrasts,
        empty_choice_scope=empty, quote_mutations=mutations, limitations=basis()['limitations'],
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})

def main():
    cli=argparse.ArgumentParser(description=__doc__); cli.add_argument('--verify-only', action='store_true'); args=cli.parse_args()
    report=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2); stream.write('\n')
    print('Choice coverage, norm identity and ordered quoted forces verified')

if __name__ == '__main__': main()
