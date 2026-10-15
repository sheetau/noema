from copy import deepcopy
from itertools import product
import json
import pytest

from noema.constructed import parse,format_graph
from scripts.check_ordered_contrast import (values,content_values,document,VARIANTS,UNKNOWNS,CONTENT_CASES,alignment)
from scripts.compose_ordered_contrast import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('flags',list(product((False,True),repeat=6)))
def test_ordered_contrast_requires_both_records_forward_only_order_and_the_presentation(flags):
    a,b,f,r,c,combined=flags
    assert values(flags=flags)==[a and b and f and not r and c]
    assert values(CORE,flags=flags)==[a and b and f and not r and c and combined]


@pytest.mark.parametrize('path',(None,CORE,SOURCE))
@pytest.mark.parametrize('variant',VARIANTS)
def test_records_cannot_change_author_scope_context_content_or_order(path,variant):
    assert values(path,variant=variant)==[False]


@pytest.mark.parametrize('path',(None,CORE,SOURCE))
def test_attribution_never_executes_content_and_survives_without_caches(path):
    # All content primitives raise. Generic left/right have identical bodies but
    # distinct descriptions; syntactic attribution must still retain their roles.
    assert values(path)==[True]
    assert values(path,memoize=False)==[True]


@pytest.mark.parametrize('path',(None,CORE,SOURCE))
@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_discourse_evidence_is_not_assumed(path,variant):
    with pytest.raises(ValueError,match='Unknown'): values(path,variant=variant)


@pytest.mark.parametrize('options',CONTENT_CASES)
def test_separate_sides_keep_the_previous_actual_semantic_conditions(options):
    left,right,combined=content_values(**options)
    assert combined==(left and right)
    if options in ({},dict(joint=True)): assert (left,right,combined)==(True,True,True)
    if options==dict(variant='empty_faculties'): assert (left,right,combined)==(True,False,False)
    if options==dict(table=0): assert (left,right,combined)==(False,False,False)
    if options==dict(table=15): assert (left,right,combined)==(False,True,False)


def test_quote_rank_cannot_be_reduced():
    doc=deepcopy(document(CORE))
    decl=next(d for d in doc['declarations'] if d['name']=='iafparallel')
    code=decl['body']['arguments'][4];assert code['rank']==3;code['rank']=2
    with pytest.raises(ValueError): parse(format_graph(doc,'compact'))


def test_source_history_and_semantic_candidate_are_retained():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    annotation=next(d for d in new['declarations'] if d['name']=='iafannotation')
    assert 'iaeattribution' in json.dumps(annotation)
    assert not alignment()['adds_new_text_coverage'] and not alignment()['semantic_completion']


def test_artifacts_reproduce():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
