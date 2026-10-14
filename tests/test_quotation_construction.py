from copy import deepcopy
import json
from pathlib import Path

import pytest

from noema.constructed import parse, format_graph, promote
from noema.constructed_semantics import evaluate_document, DescriptionValue
from noema.ranked import parse as old_parse
from noema.script import transcribe
from noema.semantics import SemanticError
from scripts.check_runtime_quotation import route_document, ROUTES

TRUE = 'e[n p a b][n p a b]'


def values(doc, model=None, **options):
    return [r['value'] for r in evaluate_document(doc, individuals=('alice', 'bob'), situations=('now',), primitives=model or {}, **options)]


def test_constructed_application_is_identical_to_closed_literal_and_does_not_execute():
    text = 'p:r call[a] c.r name[] a.q[e[o a[r[p call]][r[k name[]]]][r[c[p call][k name[]]]]].'
    def forbidden(*args):
        raise AssertionError('Construction executed its input')
    assert values(parse(text), {'call': forbidden, 'name': forbidden}) == [True]
    assert values(parse(text + 'q[s[o a[r[p call]][r[k name[]]]]].'), {'call': lambda who: who == 'alice', 'name': lambda: 'alice'}) == [True, True]


def test_lifting_preserves_the_exact_local_description():
    doc = parse('p:d code[] i[c][r[' + TRUE + ']].q[e[o r[k code[]]][r[r[' + TRUE + ']]]].q[e[s[o r[k code[]]]][k code[]]].')
    assert values(doc) == [True, True]


def test_binders_are_canonical_and_closed_arguments_do_not_capture():
    # Both operands initially use the same canonical binder name. Application
    # construction must re-normalize siblings without capturing either binder.
    text = 'p:d code[] i[h[a] a][o a[r[i[f h[a] a][i[x a][c[v f][v x]]]]][r[i[x a][v x]]]].'
    text += 'q[e[k code[]][r[c[i[fn h[a] a][i[person a][c[v fn][v person]]]][i[other a][v other]]]]].'
    text += 'q[f person a[e[c[s[k code[]]][v person]][v person]]].'
    doc = parse(text)
    assert values(doc) == [True, True]
    for notation in ('compact', 'full'):
        formatted = format_graph(doc, notation)
        assert parse(formatted) == doc
        assert parse(transcribe(formatted, alphabet='v2')) == doc


@pytest.mark.parametrize('expression', [
    'o a[r[' + TRUE + ']][]',
    'o a[r[i[x a][v x]]][]',
    'o a[r[i[x a][v x]]][r[' + TRUE + ']]',
    'o a[r[i[x c][v x]]][' + TRUE + ']',
    'o r[' + TRUE + ']',
])
def test_wrong_constructor_types_and_arities_are_rejected(expression):
    with pytest.raises(SemanticError):
        parse('p:q[e[' + expression + '][' + expression + ']].')


def test_construction_rank_is_the_maximum_and_cannot_be_lowered():
    text = 'p:d low[] i[c][r[' + TRUE + ']].d template[] i b[h[c] c][r b[i[x c][w[v x][s[k low[]]]]]].'
    body = 'o a[k template[]][r[' + TRUE + ']]'
    doc = parse(text + 'd result[] i b[c][' + body + '].q[s[k result[]]].')
    assert values(doc) == [True]
    with pytest.raises(SemanticError, match='result sort mismatch'):
        parse(text + 'd result[] i[c][' + body + '].')
    # Lifting retains the conservative rank of the source quote.
    assert values(parse(text + 'd lifted[] i b[i b[h[c] c]][o r[k template[]]].q[e[s[k lifted[]]][k template[]]].')) == [True]


def test_foreign_and_forged_descriptions_cannot_be_constructed():
    captured = []
    values(parse('p:r save[i[c]] c.s[k save[r[' + TRUE + ']]].'), {'save': lambda d: captured.append(d) is None})
    doc = parse('p:r foreign[] i[c].q[e[o r[k foreign[]]][o r[k foreign[]]]].')
    for value in (captured[0], DescriptionValue(captured[0].syntax, captured[0].result_type)):
        with pytest.raises(SemanticError, match='wrong result sort'):
            values(doc, {'foreign': lambda: value})


def test_unissued_json_rank_or_extra_constructor_fields_are_rejected():
    doc = parse('p:q[e[o r[r[' + TRUE + ']]][o r[r[' + TRUE + ']]]].')
    bad = deepcopy(doc); bad['statements'][0]['body']['arguments'][0]['rank'] = 0
    with pytest.raises(SemanticError):
        values(bad)


def test_ordinary_message_content_syntax_is_unchanged():
    assert values(parse('p:q[e[o[j s[b scene[' + TRUE + ']]]][b scene[' + TRUE + ']]].')) == [True]


@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('target', (None, 0, 1, 2))
def test_runtime_ceilings_still_cover_higher_order_routes(route, target):
    doc = promote(route_document(route, 1, target))
    model = {'touch': lambda: True}
    if route == 'callback':
        model['bridge'] = lambda fn: fn()
    if target is None or target == 0:
        assert values(doc, model) == [True]
    else:
        with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
            values(doc, model)


def test_syntax_growth_is_charged_to_the_budget():
    text = 'p:d grow[x i[c]] i[c][o a[r[i[a c b c][w[v a][v b]]]][v x v x]].'
    term = 'r[' + TRUE + ']'
    for _ in range(12):
        term = 'k grow[' + term + ']'
    doc = parse(text + 'q[e[' + term + '][' + term + ']].')
    with pytest.raises(SemanticError, match='step budget'):
        values(doc, max_steps=500)


@pytest.mark.parametrize('name', ('examples/v015/kant-quantified-permissions.noema', 'examples/v015/runtime-quotation-accepted.noema'))
def test_previous_documents_promote_without_mutation(name):
    text = Path(name).read_text(encoding='utf-8')
    old = old_parse(text); before = deepcopy(old)
    assert parse(text) == old
    new = promote(old)
    assert old == before and new['schema_version'] == '0.16'
    assert new['declarations'] == old['declarations'] and new['statements'] == old['statements']


def test_older_editions_do_not_accept_new_constructor_syntax():
    with pytest.raises(SemanticError):
        parse('o:q[e[o r[r[' + TRUE + ']]][o r[r[' + TRUE + ']]]].')


def test_personal_message_and_purpose_are_exactly_derived_without_execution():
    from scripts.check_constructed_purposes import construction_checks
    assert [r['person'] for r in construction_checks()] == ['alice', 'bob']


def test_equal_profiles_cannot_substitute_other_message_or_purpose_syntax():
    from scripts.check_constructed_purposes import collision_checks
    assert collision_checks() == dict(equal_purpose_profiles=True, same_purpose_description=False,
        wrong_purpose_accepted=False, equal_message_profiles=True, other_persons_message_accepted=False)


def test_guarded_predecessor_call_cannot_reset_the_construction_engines_ceiling():
    from noema.guarded_ranked_semantics import evaluate_document as guarded_evaluate
    captured = []
    source = old_parse('o:r save[h[] c] c.d low[] i[c][r[' + TRUE + ']].s[k save[i[][s[k low[]]]]].')
    guarded_evaluate(source, individuals=('alice',), situations=('now',), primitives={'save': lambda fn: captured.append(fn) is None})
    target = parse('p:r check[] c.q[s[r[k check[]]]].')
    with pytest.raises(SemanticError, match='Runtime quotation ceiling'):
        values(target, {'check': captured[0]})
    assert captured[0]() is True
