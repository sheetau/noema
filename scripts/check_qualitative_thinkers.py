"""Counterexamples for a nonnumerical disposition and its source connection."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_shared_future_period as prior
from scripts.compose_subject_bound_departure import closure
from scripts.compose_qualitative_thinkers import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,PROVIDERS,build

REPORT=ROOT/'reports/qualitative-thinkers-v1.json'
RESEARCH='artifacts/qualitative-thinkers-reading-v1/klm.pdf'
POINTS=('first','second','third')
UNKNOWN=prior.UNKNOWN


def evaluate(doc,values):
    selected={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=('person',),situations=POINTS,primitives=selected,
        memoize_definitions=True,memoize_expressions=True,max_steps=2000000)]


@lru_cache(maxsize=1)
def generic_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r zcases[d] c.r zpreferred[d d] c.r zresponse[d] c.'+
        'q[k rqt3[p zcases p zpreferred]].q[k rqt4[p zcases p zpreferred p zresponse]].')


def generic_values(relation,truth=POINTS,cases=POINTS):
    return dict(zcases=lambda p:p in cases,zpreferred=lambda a,b:(a,b) in relation,zresponse=lambda p:p in truth)


def preference_checks():
    doc=generic_document();orders=[]
    for bits in product((False,True),repeat=9):
        relation={pair for pair,flag in zip(product(POINTS,repeat=2),bits) if flag}
        composed={(a,c) for a,b in relation for middle,c in relation if b==middle}
        valid=not any(a==b for a,b in relation) and composed<=relation
        assert evaluate(doc,generic_values(relation))==[valid,valid],bits
        if valid:orders.append(relation)
    assert len(orders)==19
    count=0
    for relation in orders:
        minimal=set(POINTS)-{b for a,b in relation}
        for bits in product((False,True),repeat=3):
            truth={p for p,flag in zip(POINTS,bits) if flag}
            assert evaluate(doc,generic_values(relation,truth))==[True,minimal<=truth]
            count+=1
    return dict(three_scene_relations=512,strict_partial_orders=len(orders),valid_order_response_combinations=count,
        graph_composition_oracle=True,all_checks_eager=True)


def contrast_checks():
    doc=generic_document();rows={}
    variants={
        'exception_fails':({('first','second'),('first','third')},{'first'},POINTS,[True,True]),
        'incomparable_failure':({('first','second')},{'first'},POINTS,[True,False]),
        'normal_failure':({('first','second'),('first','third')},{'second','third'},POINTS,[True,False]),
        'cycle':({('first','second'),('second','first')},set(POINTS),POINTS,[False,False]),
        'empty':(set(),set(POINTS),(),[True,False]),
        'outside_does_not_dominate':({('third','first')},{'first'},('first',),[True,True]),
        'no_preference_requires_all':(set(),{'first','second'},POINTS,[True,False]),
    }
    for name,(relation,truth,cases,wanted) in variants.items():
        actual=evaluate(doc,generic_values(relation,truth,cases));assert actual==wanted,(name,actual);rows[name]=actual
    for symbol in ('zcases','zpreferred','zresponse'):
        values=generic_values(set());values[symbol]=UNKNOWN
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(symbol)
    return dict(contrasts=rows,unknown_inputs_refused=3,no_finite_list_or_numerical_score_required=True)


@lru_cache(maxsize=1)
def native_document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=prior.native_document()
    existing={d['name']:d for d in doc['declarations']}
    for d in old['declarations']:
        if d['name'] in existing:assert existing[d['name']]==d
        else:doc['declarations'].append(deepcopy(d))
    text='r zpreferred[a d d d] c.r ztestperson[] a.r ztestpoint[] d.'
    text+='q[k hzq3[k ztestperson[] k ztestpoint[] p zthinkcases p zpreferred p zthinktopics p zthinkpresented]].'
    text+='q[k hzhg[k ztestperson[] k zthinktopics[k ztestperson[] k ztestpoint[] k ztestpoint[]] k ztestpoint[] p zthinkpresented]].'
    return parse(format_graph(doc,'compact')+text)


def native_checks():
    doc=native_document();rows={}
    variants={'baseline':[True,False],'guided_thinking':[False,False],'unsupported_thinking':[False,False],
        'wrong_thinking_topic':[False,False],'actual_episode_only':[False,True]}
    for variant,wanted in variants.items():
        values=prior.conditional.prior.native_model(doc,variant)
        values.update(ztestperson=lambda:'sender',ztestpoint=lambda:'freed',
            zthinkcases=lambda p,a,s:(p,a)==('sender','freed') and s in ('trialgood','trialbad'),
            zpreferred=lambda p,a,x,y:(p,a,x,y)==('sender','freed','trialgood','trialbad'))
        if variant=='actual_episode_only':values['zthinkpresented']=lambda p,t,s:(p,t,s)==('sender','topic','freed')
        actual=prior.conditional.prior.evaluate(doc,values);assert actual==wanted,(variant,actual);rows[variant]=actual
    values=prior.conditional.prior.native_model(doc)
    values.update(ztestperson=lambda:'sender',ztestpoint=lambda:'freed',
        zthinkcases=lambda p,a,s:(p,a)==('sender','freed') and s in ('trialgood','trialbad'),
        zpreferred=lambda p,a,x,y:False)
    assert prior.conditional.prior.evaluate(doc,values)==[False,False]
    for key in ('zthinkpoints','zthinkassessed','zthinkweights','zthinkthreshold'):values[key]=UNKNOWN
    values['zpreferred']=lambda p,a,x,y:(p,a,x,y)==('sender','freed','trialgood','trialbad')
    assert prior.conditional.prior.evaluate(doc,values)==[True,False]
    values['fd']=UNKNOWN
    try:prior.conditional.prior.evaluate(doc,values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown supporting reason filled')
    return dict(native_judgment_contrasts=rows,actual_h5c_and_hzhg_executed=True,unranked_exception_not_ignored=True,
        numerical_profile_inputs_unused=True,unknown_reason_refused=True,all_checks_eager=True)


def attribution_checks():
    doc=deepcopy(native_document());doc['statements']=[]
    values,_=prior.conditional.closed.arguments();values['thinkpreferred']='p zpreferred'
    values['members']='i[person a point d][k zbranchmembers[v branch v person v point]]'
    supplied=' '.join('i[branch d]['+values[n]+']' for n,t in PROVIDERS)
    frame='r b[k rqt6['+prior.attributed.previous.prior.CONDITION_ARGS+' '+supplied+']]'
    doc=parse(format_graph(doc,'compact')+'q[k hzpy['+frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]]].')
    rows={}
    for report,background in product((False,True),repeat=2):
        seen=[];model=prior.attributed.previous.unknown_values(doc)
        model.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        model.update(prior.attributed.relation_values(report,background,seen))
        actual=prior.attributed.evaluate(doc,model);assert actual==[report and background]
        assert {'rqt6','zpreferred','zthinkcases','hzhb'}<=_references(seen[0][3]);assert seen[0][3]==seen[1][3]
        assert {'rqt6','hzpt','rqts'}<=_references(seen[1][4]);rows[str((report,background))]=actual
    return dict(native_scoped_attribution=rows,world_and_preference_inputs_not_executed=True,
        unrestricted_dissemination_truth_not_claimed=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-8]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    independent={d['name'] for d in closure(new.document,['hzq3'])}
    assert not independent&{'hzhh','rqa','rqb','rd4','rd5'}
    assert {'h5c','hzhg','rqt2','rqt3','rqt4'}<=independent
    assert len(PROVIDERS)==17
    return dict(new_compositions=8,new_primitives=0,independent_disposition_has_no_scoring_dependency=True,
        branch_provider_count=17,old_weighted_profile_preserved=True,existing_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/shared-future-period-v1.json').read_text(encoding='utf-8'))
    for p,sha in previous['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha
    assert digest((ROOT/RESEARCH).read_bytes())=='681ce1e3836ebf9e0b0e073ef01626f8db0692b9f761cdefb00f648c9a4c0989'
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|{RESEARCH,
        'reports/shared-future-period-v1.json','scripts/compose_qualitative_thinkers.py','scripts/check_qualitative_thinkers.py',
        'tests/test_qualitative_thinkers.py','docs/qualitative-thinkers-v1.md'}
    results={}
    for name,fn in [('preferences',preference_checks),('contrasts',contrast_checks),('native',native_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    source=prior.attributed.previous.source_checks()
    return dict(status='nonnumerical_response_disposition_candidate_with_native_judgments',document=FULL,**results,roundtrips=True,
        new_source_assertions=0,new_covered_characters=0,
        research=dict(url='https://arxiv.org/abs/cs/0202021',artifact=RESEARCH,reference='Definitions 4 and 8; not a claim to implement all KLM rules'),
        alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],start=162,end=176,source='Selbstdenkende',
            definitions=['hzq3','rqt6'],status='partial_qualitative_disposition_candidate',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Qualitative disposition and source connection checked',flush=True)


if __name__=='__main__':main()
