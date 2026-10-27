"""Typed lookup retains the function and closed role without executing either."""
import json
import pytest
from noema.constructed_semantics import DescriptionValue,FunctionValue
from scripts import velocity_magnitude_angle_visible_profile as profile


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))


def test_profile_preserves_parent_and_all_four_distinct_contracts():
    current=profile.VelocityMagnitudeAngleVisibleVocabulary();prior=profile.VelocityAdditionSettingVisibleVocabulary()
    assert len(current._words)==859 and len(profile.CONTRACTS)==3 and len(profile.EXTRA)==1
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current.document()[field][n]==row for n,row in prior.document()[field].items())
    assert len(set(current._symbols.values()))==859


def test_truth_cut_function_reference_preserves_value_without_execution():
    calls=[]
    def forbidden(*args):
        calls.append(args)
        raise AssertionError('Lookup evaluated a quoted role or candidate function')
    candidate=FunctionValue(('truth',),profile.CUT,forbidden)
    role=DescriptionValue(canonical(dict(kind='function_ref',symbol='knownrole')),canonical(profile.ROLE))
    args=['document','node',role,'context']
    refs=profile.TruthCutFunctionReferences({('document','node',role.syntax,'context'):candidate})
    assert refs.described(*args) is candidate
    for slot in range(4):
        changed=args[:];changed[slot]='unknown'
        with pytest.raises(ValueError):refs.described(*changed)
    for changed in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),
                    DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):refs.described(*args[:2],changed,args[3])
    assert calls==[]


@pytest.mark.parametrize('candidate',[
    'untyped',
    FunctionValue(('individual',),profile.CUT,lambda x:x),
    FunctionValue(('truth',),'truth',lambda x:x),
    FunctionValue(('truth',),profile.CUT,None),
])
def test_truth_cut_reference_rejects_wrong_candidate_type(candidate):
    with pytest.raises(ValueError):profile.TruthCutFunctionReferences({('document','node','role','context'):candidate})
