"""The typed region reference is a lookup, not a physical assertion."""
import json
import pytest
from noema.constructed_semantics import DescriptionValue, FunctionValue
from scripts.vacuum_assumption_visible_profile import CUT, ROLE, FourCutTruthFunctionReferences


def forbidden(*args):
    raise AssertionError('A quoted role or candidate must not be executed')


def fixture():
    role=DescriptionValue(json.dumps(dict(kind='function_ref',symbol='vacuumregionrole')),json.dumps(ROLE))
    candidate=FunctionValue(tuple([CUT]*4),'truth',forbidden)
    key=('document','node',role.syntax,'context')
    return FourCutTruthFunctionReferences({key:candidate}),role,candidate


def test_region_lookup_preserves_candidate_without_execution():
    refs,role,candidate=fixture()
    assert refs.handlers()['describedfourcuttruthfunctionreference']('document','node',role,'context') is candidate


@pytest.mark.parametrize('slot',range(4))
def test_region_lookup_checks_every_reference_slot(slot):
    refs,role,_=fixture()
    args=['document','node',role,'context']
    args[slot]=DescriptionValue('{}',role.result_type) if slot==2 else 'unknown'
    with pytest.raises(ValueError):refs.described(*args)


@pytest.mark.parametrize('bad',[
    FunctionValue(tuple([CUT]*3),'truth',forbidden),
    FunctionValue(tuple([CUT]*4),'individual',forbidden),
    FunctionValue(tuple(['number']*4),'truth',forbidden),
    FunctionValue(tuple([CUT]*4),'truth',None),
    'untyped',
])
def test_region_lookup_rejects_wrong_candidate_type(bad):
    with pytest.raises(ValueError):FourCutTruthFunctionReferences({('document','node','role','context'):bad})


@pytest.mark.parametrize('kind',['sort','rank','untyped'])
def test_region_lookup_rejects_wrong_description_type(kind):
    refs,role,_=fixture()
    bad={'sort':DescriptionValue(role.syntax,'"individual"'),
         'rank':DescriptionValue(role.syntax,role.result_type,1),'untyped':role.syntax}[kind]
    with pytest.raises(ValueError):refs.described('document','node',bad,'context')
