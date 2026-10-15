from itertools import product
import pytest
from noema.constructed import parse
from scripts.check_public_reason_claim import values, source_values, document, alignment
from scripts.compose_public_reason_claim import ROOT, PARENT, SOURCE, CORE, build
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('allowed,prohibited', list(product(range(4), repeat=2)))
def test_all_permissions_and_prohibitions_including_a_second_public_role(allowed, prohibited):
    good = allowed == 3 and prohibited == 0
    assert values(allowed, prohibited) == [good, good, good, True]


@pytest.mark.parametrize('norms', range(8))
def test_current_and_comparison_requirements_are_separate_from_permission(norms):
    assert values(norms=norms) == [True, norms == 7, norms == 7, True]


@pytest.mark.parametrize('variant', ('source','person','role','activity','description','context','polarity','nonhuman','missing_current'))
def test_permission_and_person_binding_failures(variant):
    assert values(variant=variant) == [False, False, False, True]


@pytest.mark.parametrize('variant', ('norm_person','norm_description','wrong_scope','empty_cases'))
def test_outer_norm_and_catalogue_failures(variant):
    assert values(variant=variant) == [True, False, False, True]


@pytest.mark.parametrize('variant', ('unknown_permission','unknown_requirement'))
def test_unassessed_is_not_false_or_permission(variant):
    with pytest.raises(ValueError, match='Unassessed'): values(variant=variant)


def test_vacuous_permission_does_not_claim_activity_existence_and_execution_is_never_called():
    assert values(allowed=0, variant='empty_public') == [True, True, True, True]
    # cg is forbidden in the model: permission does not require actual execution.
    assert values(memoize=False) == values() == [True, True, True, True]


def test_two_norm_levels_keep_their_own_sources_and_ordered_bindings():
    calls = []; assert values(calls=calls) == [True, True, True, True]
    outer = [row for row in calls if row[0] == 'requirement']
    inner = [row for row in calls if row[0] == 'permission']
    assert outer and all(row[1:4] == ('norm','government','office') and row[5] == ('government','person') and code_is(row[4], 'iavclaim') for row in outer)
    assert inner and all(row[1:3] == ('government','person') and code_is(row[5], 'zzq') for row in inner)
    assert {row[3] for row in inner} == {'scholar','secondrole'}


@pytest.mark.parametrize('variant,expected', [('baseline',True),('missing_requirement',False),('missing_permission',False)])
def test_concrete_policy_in_norm_replacement(variant, expected):
    assert source_values(variant=variant) == [expected]


def test_concrete_policy_in_full_collective_conditional():
    assert source_values(indices=(3,)) == [True]


def test_reproducibility_and_no_invented_author_assertions_or_coverage():
    old, new = document(PARENT), document(SOURCE)
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert new['statements'] == old['statements']
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())
    assert not alignment()['semantic_completion'] and not alignment()['adds_new_text_coverage']
    # The human criterion and compiled policy can be quoted without a rank escape.
    core = (ROOT / CORE).read_text(encoding='utf-8')
    parse(core + 'q[e[r[p iavclaim]][r[p iavclaim]]].q[e[r[p iavpolicy]][r[p iavpolicy]]].')
