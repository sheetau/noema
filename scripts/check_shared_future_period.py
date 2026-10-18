"""Test a shared scenario period, without reducing native route quantifiers."""
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
from scripts import check_attributed_focus as attributed
from scripts import check_conditional_dissemination as conditional
from scripts.compose_shared_future_period import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,PROVIDERS,build

REPORT=ROOT/'reports/shared-future-period-v1.json'
POINTS=('base','first','last','other')
UNKNOWN=attributed.UNKNOWN


def evaluate(doc,values,points=POINTS):
    selected={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=('person','authority'),situations=points,
        primitives=selected,memoize_definitions=True,memoize_expressions=True,max_steps=5000000)]


@lru_cache(maxsize=1)
def generic_document():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    text='r zframe[] a.r zbranch[] d.r zbase[] d.r zholds[d] c.'
    text+='q[k hzne[k zframe[] k zbase[] k zbranch[]]].'
    text+='q[k rqtj[k rqtw[k zframe[] k zbranch[]] k rqtx[k zbranch[]] k zbase[] p zholds]].'
    return parse(format_graph(doc,'compact')+text)


def model(doc,history=('base','first','last'),truth=('first','last'),variant='baseline'):
    values=attributed.previous.unknown_values(doc)
    def period(frame,branch,point):
        if variant=='wrong_frame':return frame=='authority' and point in history
        if variant=='wrong_branch':return branch=='last' and point in history
        return frame=='person' and branch=='other' and point in history
    def before(first,last,branch):
        if variant=='wrong_order_branch':return branch=='last' and first in POINTS[:3] and last in POINTS[:3] and POINTS.index(first)<POINTS.index(last)
        return branch=='other' and first in POINTS[:3] and last in POINTS[:3] and POINTS.index(first)<POINTS.index(last)
    values.update(zframe=lambda:'person',zbranch=lambda:'other',zbase=lambda:'base',h7q=period,ic=before,zholds=lambda point:point in truth)
    return values


def period_checks():
    doc=generic_document();count=0
    for bits in product((False,True),repeat=6):
        history={p for p,flag in zip(POINTS[:3],bits[:3]) if flag}
        truth={p for p,flag in zip(POINTS[:3],bits[3:]) if flag}
        future=history-{'base'};valid='base' in history and bool(future)
        assert evaluate(doc,model(doc,history,truth))==[valid,valid and future<=truth],bits
        count+=1
    rows={}
    for variant in ('wrong_frame','wrong_branch','wrong_order_branch'):
        result=evaluate(doc,model(doc,variant=variant));assert result==[False,False];rows[variant]=result
    # Success only outside the selected period cannot make its future hold.
    assert evaluate(doc,model(doc,history=('base','first'),truth=('last',)))==[True,False]
    assert evaluate(doc,model(doc,history=('base',),truth=POINTS))==[False,False]
    assert evaluate(doc,model(doc,truth=('first','last')))==[True,True] # no truth at base required
    for name in ('h7q','ic','zframe','zbranch','zbase','zholds'):
        values=model(doc);values[name]=UNKNOWN
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(history_and_truth_combinations=count,contrasts=rows,outside_success_not_borrowed=True,
        singleton_period_refused=True,base_truth_not_required=True,required_unknowns_refused=6,all_checks_eager=True)


@lru_cache(maxsize=1)
def conditional_document():
    doc=conditional.document();doc=deepcopy(doc);doc['statements']=[]
    helpers=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    existing={d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in helpers['declarations'] if d['name'] not in existing]
    text='r zopportunity[d d] c.'
    text+='d zforecast[branch d] e[b base[k rqtj[k rqtw[k zpermissionframe[] v branch] k rqtx[v branch] v base i[point d][k zopportunity[v branch v point]]]]].'
    args=attributed.previous.prior.CONDITION_ARGS
    text+='q[k hzp7['+args+' p zforecast]].'
    return parse(format_graph(doc,'compact')+text)


def conditional_checks():
    doc=conditional_document();count=0
    for permit_bad,good,bad in product((False,True),repeat=3):
        values=conditional.model(doc,'permitted_bad_branch' if permit_bad else 'baseline')
        values['zopportunity']=lambda branch,point:(branch,point)==('trialgood','freed') and good or (branch,point)==('trialbad','now') and bad
        result=conditional.prior.evaluate(doc,values)
        assert result==[good and (bad or not permit_bad)],(permit_bad,good,bad,result);count+=1
    values=conditional.model(doc);values['zopportunity']=lambda branch,point:point=='outside'
    assert conditional.prior.evaluate(doc,values)==[False]
    return dict(permission_and_forecast_combinations=count,actual_permission_definitions_executed=True,
        candidate_forecast_is_a_test_predicate_not_full_dissemination=True,all_checks_eager=True)


@lru_cache(maxsize=1)
def native_document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=attributed.native_document()
    names={d['name']:d for d in doc['declarations']}
    for d in old['declarations']:
        if d['name'] in names:assert names[d['name']]==d
        else:doc['declarations'].append(deepcopy(d))
    values,_=conditional.closed.arguments()
    values['members']='i[person a point d][k zbranchmembers[v branch v person v point]]'
    supplied=' '.join('i[branch d]['+values[n]+']' for n,t in PROVIDERS)
    frame='r b[k rqtz['+attributed.previous.prior.CONDITION_ARGS+' '+supplied+']]'
    return parse(format_graph(doc,'compact')+'q[k hzpy['+frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]]].')


def native_checks():
    doc=native_document();rows={}
    for reported,backgrounded in product((False,True),repeat=2):
        seen=[];values=attributed.previous.unknown_values(doc)
        values.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        values.update(attributed.relation_values(reported,backgrounded,seen))
        actual=attributed.evaluate(doc,values);assert actual==[reported and backgrounded]
        claim,marked=seen;assert claim[3]==marked[3]
        assert {'rqtz','hzhb','zpermissionframe','zorigins','zbranches'}<=_references(claim[3])
        assert {'rqtz','hzpt','rqts'}<=_references(marked[4]);rows[str((reported,backgrounded))]=actual
    return dict(native_attribution=rows,all_world_and_expectation_values_unknown=True,twenty_supplied_branch_fields=len(PROVIDERS),
        full_dissemination_truth_not_claimed=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-4]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    defs={d['name']:d for d in new.document['declarations']}
    wrapper=defs['rqtz'];call=wrapper['body'];assert call['symbol']=='rqtp'
    assert call['arguments'][3]==call['arguments'][-1]['arguments'][0]
    assert call['arguments'][-1]['symbol']=='rqty'
    family=defs['rqty'];args=family['body']['arguments'];assert family['body']['symbol']=='hzps' and len(args)==22
    assert args[0]['body']['symbol']=='rqtw' and args[1]['body']['symbol']=='rqtx'
    for index,(name,sort) in enumerate(PROVIDERS,start=1):
        assert args[index+1]==dict(kind='variable',name=family['parameters'][index]['name'])
    assert len(PROVIDERS)==20
    return dict(shared_permission_period_verified=True,derived_provider_count=2,remaining_provider_count=20,
        new_compositions=4,new_primitives=0,existing_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/attributed-focus-v1.json').read_text(encoding='utf-8'))
    for p,sha in previous['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha,p
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|{
        'reports/attributed-focus-v1.json','scripts/compose_shared_future_period.py','scripts/check_shared_future_period.py',
        'tests/test_shared_future_period.py','docs/shared-future-period-v1.md'}
    results={}
    for name,fn in [('periods',period_checks),('conditional',conditional_checks),('native',native_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    source=attributed.previous.source_checks()
    return dict(status='permission_and_forecast_share_scenario_period',document=FULL,**results,roundtrips=True,
        new_source_assertions=0,new_covered_characters=0,
        alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],start=137,end=176,
            source='werden sich immer einige Selbstdenkende',
            definitions=['rqtz'],status='partial_shared_future_period',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Shared scenario period and scoped attribution checked',flush=True)


if __name__=='__main__':main()
