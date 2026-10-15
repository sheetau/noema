from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_covered_unfolding import values,mapping,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_covered_unfolding import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('latent,initial,final',list(product(range(4),repeat=3)))
def test_unfolding_realizes_preexisting_features_of_the_same_object(latent,initial,final):
    expected=latent==3 and initial!=3 and final==3
    assert values(latent=latent,initial=initial,final=final,indices=(0,1))==[expected]*2


@pytest.mark.parametrize('cover,hard',list(product(range(8),repeat=2)))
def test_same_hard_cover_persists_at_both_endpoints_and_every_intermediate_point(cover,hard):
    assert values(cover=cover,hard=hard,indices=(0,1))==[True,cover==hard==7]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_depiction_cannot_mix_objects_processes_times_covers_or_agents(variant):
    assert values(variant=variant)[-1] is False


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_missing_evidence_is_not_filled(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(2,))


def test_partial_initial_manifestation_and_unmanifest_intermediate_stage_are_allowed():
    assert values(initial=1)==[True]*3
    assert values(initial=2)==[True]*3
    assert values(initial=3)==[False]*3


def test_no_cover_outside_interval_is_required_and_direct_cover_cannot_be_self():
    assert values()==[True]*3
    assert values(variant='self_cover',indices=(0,1))==[True,False]
    assert values(variant='reverse_endpoints',indices=(0,1))==[False,False]


def test_mapping_and_attribution_do_not_execute_the_unfilled_target_or_depiction():
    assert mapping()==[True]
    for variant in ('author','context'):assert mapping(variant)==[False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_template_quote_requires_its_actual_rank():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iagattribution')
    code=d['body']['arguments'][2];assert code['rank']==1;code['rank']=0
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_reproduction_history_open_target_and_uncached_evaluation():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements']
    assert alignment()['unfilled_target'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==t for p,t in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
