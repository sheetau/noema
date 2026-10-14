from copy import deepcopy
from pathlib import Path

import pytest

from noema.grammar import parse as historical_parse
from noema.ranked import parse, format_graph, promote
from noema.ranked_discourse import normalize_document
from noema.ranked_semantics import evaluate_document, DescriptionValue
from noema.script import transcribe
from noema.semantics import SemanticError

ROOT = Path(__file__).resolve().parents[1]
TRUE = 'e[n p a b][n p a b]'
BASE = 'o:d aa[] i[c][r[' + TRUE + ']].'
CHAIN = BASE + 'd ab[] i b[c][r b[s[k aa[]]]].d ac[] i c[c][r c[s[k ab[]]]].'


def values(doc, primitives=None):
    return [row['value'] for row in evaluate_document(doc, individuals=('alice', 'bob'), situations=('now',), primitives=primitives or {})]


def test_explicitly_nested_evaluation_descends_ranks():
    doc = parse(CHAIN + 'q[s[k ac[]]].')
    assert values(doc) == [True]
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == doc
        assert parse(transcribe(text, alphabet='v2')) == doc


@pytest.mark.parametrize('text', [
    BASE + 'q[e[r[s[k aa[]]]][r[s[k aa[]]]]].',
    CHAIN + 'q[e[r b[s[k ab[]]]][r b[s[k ab[]]]]].',
    CHAIN + 'q[e[r b[s[k ac[]]]][r b[s[k ac[]]]]].',
    BASE + 'd later[] c[s[k aa[]]].q[e[r[p later]][r[p later]]].',
])
def test_same_higher_and_transitive_rank_evaluation_are_rejected(text):
    with pytest.raises(SemanticError, match='strictly lower ranks'):
        parse(text)


def test_argument_effect_is_not_hidden_by_the_called_definitions_lower_effect():
    low = 'd lower[x c] c[w[s[k aa[]]][v x]].'
    with pytest.raises(SemanticError, match='strictly lower ranks'):
        parse(CHAIN + low + 'q[e[r b[k lower[s[k ab[]]]]][r b[k lower[s[k ab[]]]]]].')
    assert values(parse(CHAIN + low + 'q[s[r c[k lower[s[k ab[]]]]]].')) == [True]


@pytest.mark.parametrize('text', ['o:q[e[r b[v missing]][r b[v missing]]].',
    'o:d self[] i b[c][r b[s[k self[]]]].'])
def test_rank_does_not_enable_free_capture_or_forward_recursion(text):
    with pytest.raises(SemanticError):
        parse(text)


@pytest.mark.parametrize('word', ['aa', 'ab'])
def test_rank_numerals_have_no_leading_zero(word):
    with pytest.raises(SemanticError, match='leading zero'):
        parse('o:r test[] i ' + word + '[c].')


def test_rank_is_part_of_type_and_interned_identity():
    seen = []
    text = BASE + 'd high[] i b[c][r b[' + TRUE + ']].r check[i[c] i b[c]] c.q[k check[k aa[] k high[]]].'
    def check(low, high):
        seen.extend([low, high])
        return low.syntax == high.syntax and low.rank == 0 and high.rank == 1 and low is not high
    assert values(parse(text), {'check': check}) == [True]
    with pytest.raises(SemanticError):
        parse(BASE + 'r check[i b[c]] c.q[k check[k aa[]]].')


def test_forged_or_foreign_ranked_descriptions_are_rejected():
    captured = []
    text = CHAIN + 'r capture[i b[c]] c.q[k capture[k ab[]]].'
    assert values(parse(text), {'capture': lambda d: captured.append(d) is None}) == [True]
    other = parse('o:r external[] i b[c].q[s[k external[]]].')
    for value in (captured[0], DescriptionValue(captured[0].syntax, captured[0].result_type, 1)):
        with pytest.raises(SemanticError, match='wrong result sort'):
            values(other, {'external': lambda value=value: value})


def test_json_cannot_lie_about_disquotation_rank():
    doc = parse(CHAIN + 'q[s[k ab[]]].')
    for fake in (0, 2, True):
        bad = deepcopy(doc); bad['statements'][0]['body']['rank'] = fake
        with pytest.raises(SemanticError, match='annotation differs'):
            normalize_document(bad)


def test_description_domains_still_cannot_be_replaced_with_known_literals():
    with pytest.raises(SemanticError, match='description domain'):
        values(parse('o:q[f value i b[c][e[v value][v value]]].'))


@pytest.mark.parametrize('stem', ['examples/v014/coordinate-witness-coherence.noema',
    'examples/v014/kant-unrestricted-others.noema', 'examples/v014/einstein-density-time.noema'])
def test_historical_documents_still_parse_identically_and_promote_explicitly(stem):
    text = (ROOT / stem).read_text(encoding='utf-8')
    old = historical_parse(text); before = deepcopy(old)
    assert parse(text) == old
    new = promote(old)
    assert old == before
    assert new['schema_version'] == new['lexicon_version'] == '0.15'
    assert new['declarations'] == old['declarations'] and new['statements'] == old['statements']


def test_old_editions_do_not_accept_rank_syntax():
    for text in ('n:r item[] i b[c].', 'n:q[e[r a[' + TRUE + ']][r a[' + TRUE + ']]].'):
        with pytest.raises(SemanticError):
            parse(text)
        with pytest.raises(SemanticError):
            historical_parse(text)


@pytest.mark.parametrize('alice,bob', [(False, False), (False, True), (True, False), (True, True)])
def test_each_person_can_supply_a_different_description_and_attribution_is_not_factive(alice, bob):
    doc = parse((ROOT / 'examples/v015/person-dependent-reports.noema').read_text(encoding='utf-8'))
    issued = {}; calls = []
    def register(first, second):
        issued.update(alice=first, bob=second); return True
    def selected(person):
        calls.append(person); return issued[person]
    def attributed(description):
        assert calls == []  # Quoting/reporting did not evaluate the selected contents.
        return description.rank == 1
    model = dict(register=register, selected=selected, attributed=attributed, anchor=lambda: 'now',
        satisfied=lambda person, context: alice if person == 'alice' else not bob,
        frustrated=lambda person, context: bob if person == 'bob' else not alice)
    assert values(doc, model) == [True, True, alice and bob]
    assert calls == (['alice', 'bob'] if alice else ['alice'])


def test_higher_order_latent_effect_is_an_explicit_prototype_limit():
    # Rank checking follows explicit syntax and named definitions. It is NOT
    # an effect system for an arbitrary function supplied as a value.
    text = CHAIN + 'd run[] h[] c[i[][s[k ab[]]]].'
    text += 'd template[] i[h[h[] c] c][r[i[fn h[] c][c[v fn][]]]].'
    text += 'q[c[s[k template[]]][k run[]]].'
    assert values(parse(text)) == [True]
