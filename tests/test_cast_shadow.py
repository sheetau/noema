from itertools import product
import pytest
from scripts.check_cast_shadow import values,oracle,ALL
from scripts.compose_cast_shadow import ROOT,build


@pytest.mark.parametrize('bits',list(product((False,True),repeat=8)))
def test_emission_other_obstacles_intersection_and_opacity(bits):assert values(bits)==oracle(bits)


@pytest.mark.parametrize('variant',('wrong_source','wrong_destination','wrong_clear_blocker','other_interceptor','other_opacity_object','other_context'))
def test_shadow_relations_share_source_blocker_route_destination_and_context(variant):
    assert values(variant=variant)==[False,False,False]


@pytest.mark.parametrize('variant',('empty_region','mixed_region'))
def test_a_shadow_region_is_nonempty_and_all_its_members_satisfy_the_condition(variant):
    assert values(variant=variant,indices=(0,3,4))==[True,False,False]


def test_a_different_shadow_region_can_exist_when_the_selected_region_is_invalid():
    assert values(variant='other_region',indices=(0,3,4))==[True,False,True]


@pytest.mark.parametrize('bits,shadow',[
    ((False,False,*ALL[2:]),False),((*ALL[:4],False,False,*ALL[6:]),False),
    (ALL,True),((*ALL[:4],True,False,*ALL[6:]),True)])
@pytest.mark.parametrize('fear',(False,True))
def test_actual_shadow_and_attitude_toward_its_description_are_independent(bits,shadow,fear):
    assert values(bits,fear=fear,indices=(3,4,5,6,7))==[shadow,shadow,fear,not fear,True]


def test_attitude_does_not_execute_the_shadow_definition():
    assert values(variant='unknown_geometry',indices=(5,6,7))==[True,False,True]
    with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_geometry',indices=(4,))


def test_knowledge_of_geometry_does_not_determine_an_unknown_emotion():
    assert values(variant='unknown_emotion',indices=(3,4,7))==[True,True,True]
    for index in (5,6):
        with pytest.raises(ValueError,match='Unknown'):values(variant='unknown_emotion',indices=(index,))


def test_uncached_evaluation():assert values(memoize=False,indices=(0,1,2,5))==[True,True,False,True]


def test_documents_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
