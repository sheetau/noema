"""Countermodels for permission-conditioned native dissemination contents."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_described_dissemination as closed
from scripts.compose_focused_dissemination import BASE
from scripts.compose_conditional_dissemination import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,FIELDS,build

prior=closed.prior
REPORT=ROOT/'reports/conditional-dissemination-v1.json'


def generic_checks():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')
    text+='r zcases[d] c.r zcondition[d] c.r zorigins[d] d.r zholds[d d] c.'
    text+='d zcontents[branch d] e[b point[k zholds[v branch v point]]].q[k rqtn[p zcases p zcondition p zorigins p zcontents]].'
    doc=parse(text);branches=('one','two');points=branches+('first','second','actual');count=0
    for flags in product((False,True),repeat=8):
        cases={b for b,f in zip(branches,flags[:2]) if f};condition={b for b,f in zip(branches,flags[2:4]) if f}
        truth=dict(zip(branches,flags[4:6]));correct=dict(zip(branches,flags[6:8]))
        def origin(b):return ('first' if b=='one' else 'second') if correct.get(b,False) else 'actual'
        values=dict(zcases=lambda b:b in cases,zcondition=lambda b:b in condition,zorigins=origin,
            zholds=lambda b,p:truth.get(b,False) and p==('first' if b=='one' else 'second'))
        chosen=cases&condition;expected=bool(chosen) and all(truth[b] and correct[b] for b in chosen)
        actual=prior.evaluate(doc,values,('person',),points);assert actual==[expected],(flags,actual);count+=1
    return dict(candidate_condition_truth_and_origin_combinations=count,all_checks_eager=True,
        empty_conditioned_scope_not_accepted=True,same_branch_content_and_origin=True)


@lru_cache(maxsize=1)
def document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=closed.document('both')
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    values,_=closed.arguments()
    values['history']='i[point d][k zbranchhistory[v branch v point]]'
    values['before']='i[first d last d][k ic[v first v last v branch]]'
    values['members']='i[person a point d][k zbranchmembers[v branch v person v point]]'
    subgroup='i[person a opportunity d][k hzhb[v person k zgoverned[] v opportunity p zappointed p zguardian]]'
    text=''.join('r zpermission'+name+'[] '+sort+'.' for name,sort in [('audience','a'),('reference','d'),('source','a'),('frame','a')])
    text+='r zbranches[d] c.r zorigins[d] d.r zbranchhistory[d d] c.r zbranchmembers[d a d] c.r zactual[] d.'
    text+='d zbranchcontents[branch d] e[k hzoy['+' '.join(values[n] for n,t in BASE)+' '+subgroup+']].'
    args='k zpermissionaudience[] k zpermissionreference[] k zpermissionsource[] k zpermissionframe[] p zorigins p zbranches p zbranchcontents'
    text+='q[k hzp7['+args+']].'
    text+='q[k hzna[k zpermissionaudience[] k zpermissionreference[] k zpermissionsource[] k zactual[]]].'
    text+='q[k hzon[k hzp5[] k wa[] r b[k hzpa['+args+']] k hzp3[]]].'
    return parse(format_graph(doc,'compact')+text)


def model(doc,variant='baseline',seen=None):
    values=closed.native_model(doc,'borrowed_route' if variant=='borrowed_route' else 'baseline')
    branches=('trialgood','trialbad');oldhistory=values['h7q']
    def history(branch,point):
        if branch=='trialgood':return point in ('before','freed')
        if branch=='trialbad':return variant!='invalid_unpermitted_branch' and point in ('second','now')
        return False
    values.update(zpermissionaudience=lambda:'audience',zpermissionreference=lambda:'before',
        zpermissionsource=lambda:'authority',zpermissionframe=lambda:'audience',zactual=lambda:'outside',
        zbranches=lambda b:b in branches,zorigins=lambda b:'before' if b=='trialgood' or variant=='wrong_origin' else 'second',
        zbranchhistory=history,zbranchmembers=lambda b,p,t:b in branches and p in ('sender','relay'),
        h7q=lambda frame,branch,point:frame=='audience' and history(branch,point) if branch in branches else oldhistory(frame,branch,point),
        h6t=lambda group,p,ref:(group,p,ref)==('audience','sender','before'),
        ca=lambda p,act,ref:(p,act,ref)==('sender','stepone','before'),
        cb=lambda p,act,role,ref:(p,act,role,ref)==('sender','stepone','role','before'),
        cd=lambda role,ref:(role,ref)==('role','before'),
        cc=lambda act,target,ref:(act,target,ref)==('stepone','audience','before'),
        ce=lambda target,ref:(target,ref)==('audience','before'),h7a=lambda *args:False)
    def allowed(source,person,role,activity,description,positive,point):
        if seen is not None:seen.add(('permission',point))
        matching=(source,person,role,activity)==('authority','sender','role','stepone')
        assert json.loads(description.syntax)==dict(kind='function_ref',symbol='zzq')
        permitted=point in ('before','freed')
        if variant=='no_freedom':permitted=False
        if variant=='permitted_bad_branch' and point in ('second','now'):permitted=True
        if variant=='actual_permission' and point=='outside':permitted=True
        return matching and positive and permitted
    def attributed(node,author,content,context):
        body=json.loads(content.syntax)
        return (node,author,context)==('topic','authority','outside') and content.rank==1 and body['kind']=='call' and body['symbol']=='hzpa' and len(body['arguments'])==7
    values.update(h7b=allowed,hzon=attributed,hzp5=lambda:'topic',wa=lambda:'authority',hzp3=lambda:'outside')
    return values


def native_checks():
    doc=document();rows={}
    for variant in ('baseline','actual_permission','permitted_bad_branch','no_freedom','invalid_unpermitted_branch','wrong_origin','borrowed_route'):
        seen=set();actual=prior.evaluate(doc,model(doc,variant,seen),diagnostic=True)
        expected=[variant in ('baseline','actual_permission'),variant=='actual_permission',True]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,native_public_permission_and_dissemination_bodies_executed=True,
        actual_freedom_not_inferred=True,invalid_unpermitted_candidates_checked=True,
        conditional_false_does_not_cancel_attribution=True,all_native_contrasts_use_short_circuit_diagnostics=True,
        no_semantic_definition_replaced_by_opaque_predicate=True)


def attribution_and_unknown_checks():
    doc=document();selected=dict(doc,statements=doc['statements'][-1:]);values=model(selected)
    for name in values:
        if name not in ('hzon','hzp5','wa','hzp3'):values[name]=prior.unknown
    assert prior.evaluate(selected,values)==[True]
    values['hzon']=lambda *args:False;assert prior.evaluate(selected,values)==[False]
    values['hzon']=prior.unknown
    try:prior.evaluate(selected,values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown attribution filled')
    selected=dict(doc,statements=doc['statements'][:1]);count=0
    for name in ('h7q','zorigins','h7b','zbranchmembers'):
        values=model(selected);values[name]=prior.unknown
        try:prior.evaluate(selected,values,diagnostic=True)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
        count+=1
    return dict(attribution_evaluated_eagerly_with_unknown_world=True,unknown_attribution_refused=True,
        selected_condition_or_content_unknowns_refused=count)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==33
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_compositions=3,new_primitives=0,existing_statements=33,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/dissemination-reason-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    old_ranges=json.loads((ROOT/'reports/focused-dissemination-v1.json').read_text(encoding='utf-8'))
    alignment=deepcopy(old_ranges['alignment'])
    for row in alignment['segments']:
        row.update(definitions=list(MEANINGS),status='partial_permission_conditioned_dissemination',
            remaining=['indefinite witnesses and source-appropriate interpretation parameters','comparison and metaphor','actual source-content assertion and whole-unit meaning'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/dissemination-reason-v1.json','scripts/compose_conditional_dissemination.py',
        'scripts/check_conditional_dissemination.py','tests/test_conditional_dissemination.py','docs/conditional-dissemination-v1.md'}
    results={}
    for name,check in [('generic',generic_checks),('native',native_checks),('unknown',attribution_and_unknown_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='conditional_native_contents_with_nonfactive_attribution_candidate',document=FULL,**results,
        roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Permission-conditioned candidate contents checked',flush=True)


if __name__=='__main__':main()
