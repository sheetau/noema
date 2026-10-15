from itertools import product
import json
import pytest
from noema.extraction import _references
from scripts.check_cover_reference import generic_values,source_values,attribution,integrated_values,review_report,document
from scripts.compose_cover_reference import ROOT,PARENT,SOURCE,BASIS,READING,REVIEW,build,basis,reading,review,manuscript


@pytest.mark.parametrize('record,forward,reverse,mapping',list(product((False,True),repeat=4)))
def test_backreference_requires_record_order_and_correspondence(record,forward,reverse,mapping):
    assert generic_values(record,forward,reverse,mapping)==[record and forward and not reverse and mapping]


def test_no_self_reference_and_no_execution_of_quoted_content():
    assert generic_values(same_node=True)==[False]
    assert generic_values(memoize=False)==generic_values()==[True]


@pytest.mark.parametrize('variant',('wrong_author','wrong_prior_scope','wrong_context','wrong_content',
    'missing_order','reverse_order','wrong_mapped_cover','wrong_current_scope','wrong_regime','no_mapping'))
def test_reference_preserves_both_scopes_and_the_same_prior_regime(variant):
    assert source_values(variant,indices=(3,4))==[False,False]


def test_linked_cover_must_be_the_one_surrounding_the_growing_object():
    assert source_values()==[True]*5
    # The old existential still finds a cover, and the new reference is valid,
    # but this referenced cover does not surround the object in the depiction.
    assert source_values('split_cover')==[True,True,False,True,True]


def test_growth_still_requires_persistent_cover_and_affectionate_care():
    assert source_values('switched_cover')==[False,False,False,True,True]
    assert source_values('no_care')==[True,False,False,True,True]


def test_reference_uses_discourse_anchor_and_depiction_keeps_its_own_time():
    calls=[]
    assert source_values(calls=calls)==[True]*5
    assert calls and all(row==('selected','node','author','scope','utterance') for row in calls)


@pytest.mark.parametrize('variant',('unknown_cover','unknown_mapping'))
def test_unknown_reference_is_not_filled_by_an_arbitrary_object(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant,indices=(3,))


def test_family_changes_depiction_code_and_attribution_does_not_run_it():
    assert source_values('old_depiction',indices=(3,4))==[True,False]
    assert attribution()==[True] and attribution('old')==[False]


def test_actual_integrated_schema_checks_the_new_reference():
    assert integrated_values()==[True]
    assert integrated_values('wrong_regime')==[False]


def test_previous_source_is_preserved_and_new_cover_is_reachable():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert len(new['statements'])==len(old['statements'])==22
    assert new['statements'][:-1]==old['statements'][:-1]
    _,mapping=manuscript()
    assert _references(new['statements'][-1])=={mapping['iayattribution']}
    packet=review_report();rows={r['id']:r for r in packet['obligations']}
    for name in ('hard_cover','tender_care','more_than_machine','dignified_treatment'):
        assert rows[name]['unconnected_candidate_roots']==[]
    assert packet['templates'][0]['symbol']==mapping['iayschema']
    assert len(packet['templates'][0]['parameters'])==8
    assert not packet['semantic_completion'] and not packet['counts_as_translated_coverage']


def test_reproducible_text_and_explicit_reading_limits():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    for path,value in ((BASIS,basis()),(READING,reading()),(REVIEW,review(files))):
        assert json.loads((ROOT/path).read_text(encoding='utf-8'))==value
