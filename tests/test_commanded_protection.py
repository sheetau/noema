from itertools import product
import pytest
from scripts.check_commanded_protection import values,full_domain_refused
from scripts.compose_commanded_protection import ROOT,build


@pytest.mark.parametrize('flags',list(product((False,True),repeat=3)))
def test_actual_requirements_and_each_members_execution_control_joint_conformity(flags):
    present,first,second=flags
    assert values(flags)==[present and first,False,present and first and second]


@pytest.mark.parametrize('variant',('wrong_source','wrong_group','wrong_plan','wrong_anchor','wrong_person',
    'omit_record','unlisted_description','wrong_description','wrong_polarity'))
def test_requirements_cannot_be_borrowed_from_other_commands_or_dropped(variant):
    assert values(variant=variant)==[False]*3


def test_negative_commands_are_satisfied_by_their_actual_polarity():
    assert values(variant='negative')==[True,False,True]


def test_empty_commands_can_be_vacuously_complied_with():
    assert values(variant='empty_commands')==[True]*3


@pytest.mark.parametrize('variant,threshold,expected',[
    ('baseline',1,[True,True]),('baseline',2,[True,False]),('empty_commands',1,[False,False]),
    ('other_plan_failed',1,[True,False])])
def test_full_community_protection_keeps_commands_count_and_causal_comparison(variant,threshold,expected):
    assert values(variant=variant,threshold=threshold,indices=(4,5))==expected


@pytest.mark.parametrize('variant',('unknown_orders','unknown_execution'))
def test_unknown_commands_and_execution_can_be_quoted_but_not_evaluated(variant):
    assert values(variant=variant,restricted=False,indices=(6,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(10,))


def test_full_description_quantification_is_not_replaced_by_the_finite_diagnostic():
    assert full_domain_refused()


def test_uncached_member_conformity_agrees():
    assert values(indices=(10,),memoize=False)==[True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
