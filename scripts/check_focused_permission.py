"""Check a source-bound scalar background without changing the attributed claim."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_focused_permission import ROOT, PARENT, SOURCE, CORE, BASIS, LIBRARY, build, basis
from scripts.compose_origin_clock import definition
from scripts.compose_scalar_backgrounds import PC
from scripts.compose_public_permission_risk import FIELD_SYMBOLS

REPORT = ROOT / 'reports/focused-permission-v1.json'
PEOPLE = ('person', 'act', 'role', 'ruler', 'author', 'other')
POINTS = ('anchor', 'elsewhere')


@lru_cache(maxsize=1)
def setup():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    doc['statements'] = []
    existing = {d['name']: d for d in doc['declarations']}
    for declaration in parse((ROOT / LIBRARY).read_text(encoding='utf-8'))['declarations']:
        if declaration['name'] in existing:
            assert existing[declaration['name']] == declaration
        else:
            doc['declarations'].append(declaration)
    text = ''.join('r jd' + name + '[] a.' for name in ('person', 'act', 'role', 'other', 'unknown'))
    text += 'r jdplainperformed[a a d] c.r jdcompoundperformed[a a d] c.'
    for name in ('plain', 'compound'):
        text += definition('jd' + name, 'person a activity a', 'b point[k jd' + name + 'performed[v person v activity v point]]', 'e')
    text += definition('hzrperson', 'person a anchor d', 'r[k jdperson[]]', 'i[a]')
    text += definition('hzractivity', 'person a activity a anchor d', 'r[k jdact[]]', 'i[a]')
    text += definition(FIELD_SYMBOLS['role'], 'person a activity a anchor d', 'r[k jdrole[]]', 'i[a]')
    for name, target in (('hzptarget', 'jdplain'), ('hzqtarget', 'jdcompound')):
        text += definition(name, 'person a activity a anchor d', 'r[p ' + target + ']', 'i[h[a a] e]')
    fixture = parse('p:' + text)
    replacement = {d['name']: d for d in fixture['declarations']}
    doc['declarations'] = [d for d in fixture['declarations'] if d['name'].startswith('jd')] + [replacement.get(d['name'], d) for d in doc['declarations']]
    return parse(format_graph(doc, 'compact'))


def values(selected=True, ranked=True, person_valid=True, activity_valid=True, permission=None,
           variant='baseline', indices=(0, 1, 2), memoize=True):
    doc = deepcopy(setup())
    person_symbol = 'jdunknown' if variant == 'unknown_reference' else 'jdperson' if person_valid else 'jdother'
    activity_symbol = 'jdact' if activity_valid else 'jdother'
    for declaration in doc['declarations']:
        if declaration['name'] in ('hzrperson', 'hzractivity'):
            declaration['body']['body']['symbol'] = person_symbol if declaration['name'] == 'hzrperson' else activity_symbol
    frame = 'c[p rtm][k hzmruler[] k ' + person_symbol + '[] k jdrole[] k ' + activity_symbol + '[] p h7a p h7b]'
    focal = 'c[' + frame + '][r[p jdcompound]]'
    ordinary = 'c[' + frame + '][r[p jdplain]]'
    foreground = 'c[i[value ' + PC + '][s[v value]]][r b[' + focal + ']]'
    package = 'k hzrpackage[k jdperson[] k jdact[] k wh[]]'
    queries = ['e[k rsu[' + package + ']][r c[' + foreground + ']]', 't[k hzrbackground[]][k wh[]]',
        'e[k rsv[' + package + ']][k rsv[k rsw[' + package + ']]]', 'k rsx[' + package + ' k wh[]]',
        'e[r b[' + focal + ']][r b[' + ordinary + ']]']
    doc = parse(format_graph(doc, 'compact') + ''.join('q[' + query + '].' for query in queries))
    expected = doc['statements'][4]['body']['arguments']
    focal_node, ordinary_node = [value['body'] for value in expected]
    doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args):
        raise AssertionError('Scalar background executed an action, permission or original source insight')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def ranking(observer, left, right, anchor):
        if variant == 'unknown_ranking':
            raise ValueError('Unknown source ranking')
        wanted = ('ruler' if variant == 'ruler_viewpoint' else 'author', 'elsewhere' if variant == 'wrong_context' else 'anchor')
        if variant == 'reversed_ranking':
            wanted_left, wanted_right = ordinary_node, focal_node
        else:
            wanted_left, wanted_right = focal_node, ordinary_node
        return ranked and (observer, anchor) == wanted and left.rank == right.rank == 1 and (
            json.loads(left.syntax), json.loads(right.syntax)) == (wanted_left, wanted_right)
    def unknown():
        raise ValueError('Unknown closed person reference')
    model.update(jdperson=lambda: 'person', jdact=lambda: 'act', jdrole=lambda: 'role', jdother=lambda: 'other', jdunknown=unknown,
        hzmruler=lambda: 'ruler', wa=lambda: 'author', wh=lambda: 'anchor', hzrranking=ranking,
        hzmpeople=lambda person, anchor: (person, anchor) == ('person', 'anchor'),
        hzqactivities=lambda person, act, anchor: selected and (person, act, anchor) == ('person', 'act', 'anchor'))
    if permission is not None:
        model['h7a'] = lambda *args: False
        model['h7b'] = lambda ruler, person, role, act, target, sign, point: permission and (
            ruler, person, role, act, sign) == ('ruler', 'person', 'role', 'act', True) and (
            json.loads(target.syntax) == dict(kind='function_ref', symbol='jdcompound'))
    return [row['value'] for row in evaluate_document(doc, individuals=PEOPLE, situations=POINTS, primitives=model,
        max_steps=10_000_000, memoize_definitions=memoize, memoize_expressions=memoize)]


def attribution(document, reported=True, backgrounded=True, variant='baseline'):
    doc = deepcopy(document)
    doc['statements'] = doc['statements'][-1:]
    def forbidden(*args):
        raise AssertionError('Attribution evaluated a quoted foreground or background')
    def report(node, author, code, scope, context):
        assert (node, author, scope, context) == ('node', 'author', 'foreground_scope', 'point')
        assert code.rank == 3 and json.loads(code.syntax) == dict(kind='call', symbol='hzqinsight', arguments=[])
        return reported
    def marked(node, author, foreground, background, foreground_scope, background_scope, context):
        actual = (node, author, foreground_scope, background_scope, context)
        wanted = list(('node', 'author', 'foreground_scope', 'background_scope', 'point'))
        position = {'other_node': 0, 'other_author': 1, 'other_foreground_scope': 2, 'other_background_scope': 3, 'other_context': 4}.get(variant)
        if position is not None:
            wanted[position] = 'other'
        fg_symbol = 'hzpinsight' if variant == 'old_foreground' else 'hzqinsight'
        bg_symbol = 'hzqsafety' if variant == 'other_background' else 'hzrbackground'
        return backgrounded and actual == tuple(wanted) and foreground.rank == background.rank == 3 and (
            json.loads(foreground.syntax), json.loads(background.syntax)) == (
                dict(kind='call', symbol=fg_symbol, arguments=[]), dict(kind='call', symbol=bg_symbol, arguments=[]))
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(hznreport=report, hzrbgreport=marked, hzqnode=lambda: 'node', wa=lambda: 'author',
        hzqrange=lambda: 'foreground_scope', hzrrange=lambda: 'background_scope', wh=lambda: 'point')
    return evaluate_document(doc, individuals=('node', 'author', 'foreground_scope', 'background_scope', 'other'),
        situations=('point',), primitives=model)[0]['value']


def source_invariants(parent, source):
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    lookup = {d['name']: d for d in source['declarations']}
    old = lookup['hzqattribution']['body']['arguments']
    new = lookup['hzrattribution']['body']['arguments']
    assert [new[i] for i in (0, 1, 2, 4, 6)] == old
    assert new[7] == dict(kind='function_ref', symbol='hznreport')
    package = lookup['hzrpackage']['body']
    assert package['symbol'] == 'rto'
    focus = package['arguments'][1]
    alternative = package['arguments'][2]['items'][0]
    assert focus['symbol'] == 'hzqtarget' and alternative['symbol'] == 'hzptarget'
    assert focus['arguments'] == alternative['arguments'] == package['arguments'][0]['arguments']


def build_report():
    documents = {}
    for path, text in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == doc and parse(transcribe(form, alphabet='v2')) == doc
        rows = []
        for reported, backgrounded in product((False, True), repeat=2):
            result = attribution(doc, reported, backgrounded)
            assert result == (reported and backgrounded)
            rows.append(dict(reported=reported, backgrounded=backgrounded, result=result))
        documents[path] = dict(declarations=len(doc['declarations']), statements=len(doc['statements']), characters=len(text), attribution=rows)
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    source_invariants(*(parse((ROOT / p).read_text(encoding='utf-8')) for p in (PARENT, SOURCE)))
    matrix = []
    for selected, ranked, person_valid, activity_valid, permission in product((False, True), repeat=5):
        result = values(selected, ranked, person_valid, activity_valid, permission, indices=(0, 1, 2, 3))
        background = not selected or ranked and person_valid and activity_valid
        assert result == [True, background, True, permission and person_valid and activity_valid]
        matrix.append(dict(selected=selected, ranked=ranked, person_valid=person_valid, activity_valid=activity_valid, permission=permission, result=result))
    contrasts = {}
    for variant in ('ruler_viewpoint', 'wrong_context', 'reversed_ranking'):
        result = values(variant=variant)
        assert result == [True, False, True]
        contrasts[variant] = result
    uncached = values(memoize=False)
    assert uncached == values() == [True, True, True]
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0016')
    start = unit['text'].index('sogar')
    alignment = dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
        range=[start, start + 5], text='sogar', status='explicit_interpretive_annotation',
        definitions=['rtm', 'rtn', 'rto', 'rtp', 'rtq', 'hzrframe', 'hzrpackage', 'hzrbackground', 'hzrattribution'])])
    paths = [PARENT, SOURCE, CORE, BASIS, LIBRARY, 'scripts/compose_focused_permission.py', 'scripts/check_focused_permission.py',
        'tests/test_focused_permission.py', 'scripts/compose_scalar_backgrounds.py', 'scripts/compose_public_permission_risk.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/guarded_ranked_semantics.py', 'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_source_focus_background_without_foreground_revision', documents=documents,
        parent_declarations_and_first_16_statements_preserved=True, original_foreground_attribution_arguments_preserved=True, roundtrips=True,
        finite_interpretation=dict(matrix=matrix, contrasts=contrasts, uncached=uncached,
            scope='New source frame, package, reference checks and background evaluated directly. Existing action constructors are instantiated by two closed test descriptions; action execution and the original insight are not evaluated.'),
        alignment=alignment, limitations=basis()['unresolved'], verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
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
    print('Source focus background, fixed permission frame and unchanged foreground verified')


if __name__ == '__main__':
    main()
