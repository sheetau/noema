from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_mediated_choice import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_mediated_choice import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('mtable,ytable',list(product(range(4),range(16))))
def test_all_acyclic_two_stage_boolean_equations_keep_the_mediator_required(mtable,ytable):
    assert values(mtable,ytable,indices=(0,))==[mtable==2 and ytable in (8,10)]


def test_total_dependence_can_hold_while_the_intermediate_variable_is_only_correlated():
    assert values(ytable=12)==[False,True]
    assert values(ytable=10)==[True,True]


def test_a_joint_direct_contribution_is_not_mistakenly_excluded_as_nonmediation():
    # Y=F and M is admitted as well as Y=M; full mediation is not asserted.
    assert values(ytable=8)==[True,True]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_same_or_missing_variable_bad_meaning_assessment_or_solution_scope_is_rejected(variant):
    assert values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',('coincidence_only_meaning','unreviewed_joint','unchecked_joint','no_joint_solution'))
def test_defects_visible_only_under_joint_intervention_cannot_be_hidden_by_natural_solutions(variant):
    assert values(variant=variant)==[False,True]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_inputs_do_not_become_false_mediator_states(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


def test_source_runs_the_actual_development_and_capacity_comparison_with_the_mediator():
    calls=[]
    assert source_values(calls=calls)==[True,True]
    meanings=[row for row in calls if row[0]=='meaning']
    assert meanings and all(row[1:4]==('person','end','after') for row in meanings)
    assert any(row[4:]==(True,False,False) for row in meanings)
    assert any(row[4:]==(True,True,True) for row in meanings)


def test_source_distinguishes_total_dependence_from_mediated_dependence():
    assert source_values(ytable=12)==[False,True]
    assert source_values(ytable=8)==[True,True]


@pytest.mark.parametrize('variant',('other_person','coincidence_only_meaning','unreviewed_joint','no_joint_solution'))
def test_source_requires_same_subject_and_reviewed_meaning_even_in_forced_mediator_worlds(variant):
    assert source_values(variant=variant)==[False,True]


def test_unknown_mediator_in_a_joint_intervention_remains_unknown():
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_joint_meaning',indices=(0,))


def test_both_reading_candidates_keep_identity_through_the_full_conditional_and_remainder():
    calls=[]
    assert source_values(indices=(2,3),calls=calls)==[True,True]
    rest=[row for row in calls if row[0]=='remaining']
    assert rest and all(row[2:]==('person','end','after') for row in rest)
    assert any(code_is(row[1],'iahinner',1) for row in rest)
    assert any(code_is(row[1],'iahvocation',1) for row in rest)
    assert source_values(remaining=False,indices=(2,))==[False]


def test_false_premise_does_not_require_the_unknown_joint_intervention():
    assert source_values(urge=False,assigned=False,variant='unknown_joint_meaning',indices=(2,3))==[True,True]


def test_attribution_preserves_context_without_executing_unfilled_mediator_content():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_template_quote_rank_cannot_be_lowered():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='ialattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_generic_baseline_and_preserved_source_and_reproducible_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['mediator_content_unfilled'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
