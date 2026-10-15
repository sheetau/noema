"""Check scalar backgrounds without treating their failure as foreground falsity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, Message
from noema.script import transcribe
from scripts.compose_scalar_backgrounds import ROOT, LIBRARY, EXAMPLE, PERMISSIONS, BASIS, PC, build, basis

REPORT = ROOT / 'reports/scalar-backgrounds-v1.json'
EDGES = ((0, 1), (0, 2))


@lru_cache(maxsize=1)
def setup():
    doc = parse((ROOT / EXAMPLE).read_text(encoding='utf-8'))
    alias = deepcopy(next(d for d in doc['declarations'] if d['name'] == 'jdone'))
    alias['name'] = 'jdalias'
    # The extra name precedes the package that may refer to it.
    index = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'jdpackage')
    doc['declarations'].insert(index, alias)
    text = format_graph(doc, 'compact')
    text += 'q[e[k rsv[k jdpackage[]]][k rsv[k jdnegated[]]]].'
    text += 'q[u[e[k rsu[k jdpackage[]]][k rsu[k jdnegated[]]]]].'
    question = 'c[i[content e][j q[v content]]][c[i[value ' + PC + '][s[v value]]][r b[k jdfocus[]]]]'
    text += 'q[e[k rsz[k jdpackage[]]][r c[' + question + ']]].'
    return parse(text)


def values(truths=(True, True, False), additive=True, alternatives=('one', 'two'), edges=EDGES,
           variant='baseline', indices=None, memoize=True, order_only=False):
    doc = deepcopy(setup())
    package = next(d for d in doc['declarations'] if d['name'] == 'jdpackage')
    package['body']['symbol'] = 'rth' if additive else 'rtg'
    sequence = package['body']['arguments'][1]['body']
    sequence['items'] = [dict(kind='quote', rank=1, body=dict(kind='call', symbol='jd' + name, arguments=[])) for name in alternatives]
    doc = parse(format_graph(doc, 'compact'))
    if order_only:
        doc['statements'] = []
        options = 'l[' + PC + '][r b[k jdfocus[]] ' + ' '.join('r b[k jd' + name + '[]]' for name in alternatives) + ']'
        doc = parse(format_graph(doc, 'compact') + 'q[k rta[' + options + ' k jdview[] k jdanchor[] p jdranking]].')
    elif indices is not None:
        doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args):
        raise AssertionError('Unexpected primitive in scalar package')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    symbols = {'jdfocus': 0, 'jdone': 1, 'jdtwo': 2, 'jdalias': 3}
    def rank(observer, left, right, anchor):
        if variant == 'unknown_ranking':
            raise ValueError('Unknown scalar ranking')
        assert left.rank == right.rank == 1
        a = symbols[json.loads(left.syntax)['symbol']]
        b = symbols[json.loads(right.syntax)['symbol']]
        expected = ('other' if variant == 'wrong_observer' else 'speaker', 'elsewhere' if variant == 'wrong_context' else 'anchor')
        return (observer, anchor) == expected and (a, b) in edges
    def truth(index, point):
        if variant == 'unknown_focus' and index == 0:
            raise ValueError('Unknown foreground truth')
        if variant == 'unknown_alternative' and index == 1:
            raise ValueError('Unknown alternative truth')
        return truths[index] if point == 'anchor' else not truths[index]
    model.update(jdview=lambda: 'speaker', jdanchor=lambda: 'anchor', jdranking=rank,
        jdforeground=lambda point: truth(0, point), jdfirst=lambda point: truth(1, point), jdsecond=lambda point: truth(2, point))
    result = evaluate_document(doc, individuals=('speaker', 'other'), situations=('anchor', 'elsewhere'), primitives=model,
        max_steps=2_000_000, memoize_definitions=memoize, memoize_expressions=memoize)
    return [dict(force=row['value'].force, values=list(row['value'].content.values)) if isinstance(row['value'], Message)
            else row['value'] for row in result]


@lru_cache(maxsize=1)
def permission_setup():
    doc = parse((ROOT / PERMISSIONS).read_text(encoding='utf-8'))
    alias = deepcopy(next(d for d in doc['declarations'] if d['name'] == 'jdpermission'))
    alias['name'] = 'jdotherpermission'
    doc['declarations'].append(alias)
    foreground = 'c[i[value ' + PC + '][s[v value]]][r b[c[p jdpermission][r[p jdcompound]]]]'
    return parse(format_graph(doc, 'compact') + 'q[e[k rsu[k jdpackage[]]][r c[' + foreground + ']]].')


def permission_values(plain=True, compound=True, ranked=True, oppose_plain=False, oppose_compound=False,
                      variant='baseline', indices=None):
    doc = deepcopy(permission_setup())
    if indices is not None:
        doc['statements'] = [doc['statements'][i] for i in indices]
    def forbidden(*args):
        raise AssertionError('Permission focus executed the described action')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def target(code):
        syntax = json.loads(code.syntax)
        assert syntax['kind'] == 'function_ref'
        return syntax['symbol']
    def allowed(ruler, person, role, act, code, positive, point):
        if variant == 'unknown_compound' and target(code) == 'jdcompound':
            raise ValueError('Unknown compound permission')
        fields = ('other' if variant == 'wrong_ruler' else 'ruler',
                  'other' if variant == 'wrong_person' else 'person',
                  'other' if variant == 'wrong_role' else 'role',
                  'other' if variant == 'wrong_act' else 'act', True)
        return (ruler, person, role, act, positive) == fields and (plain if target(code) == 'jdplain' else compound)
    def required(ruler, person, role, act, code, positive, point):
        return (ruler, person, role, act, positive) == ('ruler', 'person', 'role', 'act', False) and (
            oppose_plain if target(code) == 'jdplain' else oppose_compound)
    def ranking(observer, left, right, anchor):
        if variant == 'unknown_ranking':
            raise ValueError('Unknown permission ranking')
        frame = 'jdotherpermission' if variant == 'different_frame' else 'jdpermission'
        def matches(code, action):
            return code.rank == 1 and json.loads(code.syntax) == dict(kind='apply', function=dict(kind='function_ref', symbol=frame),
                arguments=[dict(kind='quote', body=dict(kind='function_ref', symbol=action))])
        return ranked and (observer, anchor) == ('author', 'anchor') and matches(left, 'jdcompound') and matches(right, 'jdplain')
    model.update(jdruler=lambda: 'ruler', jdperson=lambda: 'person', jdrole=lambda: 'role', jdact=lambda: 'act',
        jdauthor=lambda: 'author', jdanchor=lambda: 'anchor', jdallowed=allowed, jdrequired=required, jdranking=ranking)
    return [row['value'] for row in evaluate_document(doc, individuals=('ruler', 'person', 'role', 'act', 'author', 'other'),
        situations=('anchor', 'elsewhere'), primitives=model, max_steps=2_000_000)]


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
    library = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    assert len(library['declarations']) == 19 and all(d['kind'] == 'definition' for d in library['declarations'])
    matrix = []
    for focus, first, second, additive, ranked in product((False, True), repeat=5):
        edges = EDGES if ranked else ((0, 1),)
        background = ranked and (not additive or first or second)
        result = values((focus, first, second), additive, edges=edges)
        assert result == [background, focus, background, not focus, dict(force='ask', values=[focus, not focus]), True, True, True]
        matrix.append(dict(truths=[focus, first, second], additive=additive, ranked=ranked, result=result))
    contrasts = {}
    for variant in ('wrong_observer', 'wrong_context'):
        result = values(variant=variant)
        assert result[:4] == [False, True, False, False]
        contrasts[variant] = result
    orders = []
    for edges, expected in ((EDGES, True), (((0, 1), (1, 2)), False), (EDGES + ((1, 0),), False), (EDGES + ((0, 0),), False)):
        result = values(edges=edges, order_only=True)
        assert result == [expected]
        orders.append(dict(edges=edges, result=result))
    constructions = values(variant='unknown_focus', indices=(5, 6, 7))
    assert constructions == [True] * 3
    uncached = values(memoize=False)
    assert uncached == values()
    permissions = []
    for plain, compound, ranked, oppose_plain, oppose_compound in product((False, True), repeat=5):
        foreground = compound and not oppose_compound
        result = permission_values(plain, compound, ranked, oppose_plain, oppose_compound)
        assert result == [ranked and plain and not oppose_plain, foreground, not foreground, True]
        permissions.append(dict(plain=plain, compound=compound, ranked=ranked, oppose_plain=oppose_plain,
            oppose_compound=oppose_compound, result=result))
    paths = [LIBRARY, EXAMPLE, PERMISSIONS, BASIS, 'examples/v016/kant-prior-criticism.noema',
        'scripts/compose_scalar_backgrounds.py', 'scripts/check_scalar_backgrounds.py',
        'tests/test_scalar_backgrounds.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/guarded_ranked_semantics.py']
    result = dict(status='explicit_background_separation_and_scalar_scope_not_complete_even_semantics', documents=documents,
        new_library_primitives=0, roundtrips=True, finite_interpretation=dict(matrix=matrix, contrasts=contrasts,
            orders=orders, construction_without_foreground=constructions, uncached=uncached, same_frame_permissions=permissions),
        limitations=basis()['limitations'], references=basis()['references'],
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths})
    return json.loads(json.dumps(result))


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
    print('Foreground, scalar background, explicit negation and question projection verified')


if __name__ == '__main__':
    main()
