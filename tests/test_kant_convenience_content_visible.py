"""Convenience must preserve state, method, candidate and context bindings."""
from copy import deepcopy
from itertools import product
import pytest
from scripts import check_kant_convenience_content_visible as content


def test_generic_state_and_same_method_contrasts():content.generic_state_checks()


def test_current_convenience_composition_with_explicit_state_abstraction():content.composition_checks()


def test_candidate_and_outer_person_context_slots():
    doc=content.fixture();count=0
    for person,context,case in product(('first','second'),repeat=3):
        values,seen=content.model(doc,person=person,context=context,case=case)
        assert content.run(doc,values)==[True,True];assert seen;count+=1
        for variant in ('wrong_case_person','wrong_case_context','wrong_case_scene','wrong_standard_context'):
            values,_=content.model(doc,variant,person,context,case)
            assert content.run(doc,values)==[False,False],(person,context,case,variant)
    content.RESULTS['binding']=dict(cases=count,domain_per_sort=2,every_person_context_case_slot=True,
        criterion_context_distinguished=True,full_domain_proof=False)


def test_unknown_inputs_and_wrong_description_are_rejected():
    doc=content.fixture();values,_=content.model(doc)
    def unknown(*args):raise ValueError('Unspecified convenience input')
    for name in ('jstate','aa','stateconveniencecandidate','ae','af','ap','oc','sj','uk','um'):
        with pytest.raises(ValueError,match='Unspecified'):content.run(doc,values|{name:unknown})
    changed=deepcopy(doc)
    uj=next(d for d in changed['declarations'] if d['name']=='uj')
    uj['body']['arguments'][1]['body']['symbol']='sw'
    with pytest.raises(AssertionError,match='State description changed'):content.run(changed,values)
    content.RESULTS['unknown_inputs']=dict(all_relevant_relations_reject_unknown=True,wrong_description_rejected=True)
