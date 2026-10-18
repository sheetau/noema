"""Check unrestricted route syntax and explicit native route witnesses."""
import argparse
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.existential_witnesses import instantiate_witnesses, verify_witnesses
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts import check_emancipated_transmission as prior
from scripts import check_conditional_dissemination as conditional
from scripts.compose_existential_dissemination import (
    ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,MEANINGS,ROUTE,WITNESSES,FUTURE,build)

REPORT=ROOT/'reports/existential-dissemination-v1.json'


@lru_cache(maxsize=1)
def fixture():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'))
    old=prior.document('route',True)
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    args={n:'k z'+n+'[]' for n,t in ROUTE}
    args.update(message='r[p zmessage]',state=prior.prior.STATE,
                **{n:'p z'+n for n in ('sender','recipient','activity','point')})
    text='q[k hzpb['+' '.join(args[n] for n,t in ROUTE)+']].'
    temporary=''.join('d zw'+n+'[] '+t+'[k z'+n+'[]].' for n,t in WITNESSES)
    checked=parse(format_graph(doc,'compact')+temporary+text)
    witnesses=[deepcopy(d['body']) for d in checked['declarations'][-len(WITNESSES):]]
    checked['declarations']=checked['declarations'][:-len(WITNESSES)]
    return checked,witnesses


def options(doc,variant='baseline'):
    values=prior.model(doc,variant,native=True)
    return dict(individuals=prior.NATIVE,situations=prior.POINTS,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=24000000,memoize_definitions=True,memoize_expressions=True)


def native_checks():
    doc,witnesses=fixture();rows={}
    variants=('baseline','other_origin','other_departure_subject','no_self_work','no_departure_cause',
              'late_departure','missing_receipt','wrong_causal_property','independent_message','lost_after',
              'first_send_outside_frame','recipient_start_outside_frame','recipient_end_outside_frame',
              'completed_at_initial','started_before_initial')
    for variant in variants:
        result=verify_witnesses(doc,witnesses,**options(doc,variant))
        expected=variant in ('baseline','started_before_initial')
        assert result['instance_value']==expected,(variant,result)
        assert not result['theorem_disproved']
        rows[variant]=result['status']
    # The same unrestricted claim has a good witness even if a supplied one is bad.
    bad=deepcopy(witnesses);bad[0]=deepcopy(doc['statements'][0]['body']['arguments'][0])
    assert verify_witnesses(doc,bad,**options(doc))['status']=='uncertified'
    assert verify_witnesses(doc,witnesses,**options(doc))['status']=='valid'
    return dict(contrasts=rows,failed_witness_does_not_disprove_claim=True,
        native_departure_receipt_acquisition_and_retention_executed=True,
        state_description_is_concrete_assessed_response_profile=True,all_evaluations_eager=True)


def boundary_checks():
    doc,witnesses=fixture();count=0
    for name in ('h4n','g3','h7q','h6e'):
        interpretation=options(doc);interpretation['primitives'][name]=prior.unknown
        try: verify_witnesses(doc,witnesses,**interpretation)
        except ValueError as error: assert 'Unknown' in str(error),(name,error)
        else: raise AssertionError(name)
        count+=1
    try: evaluate_document(doc,**options(doc))
    except ValueError as error: assert 'unbounded sequence' in str(error),error
    else: raise AssertionError('Unbounded sequence domain silently restricted')
    instance=instantiate_witnesses(doc,witnesses)
    assert instance['declarations']==doc['declarations']
    assert doc['statements'][0]['body']['kind']=='call'
    return dict(unknown_inputs_refused=count,unrestricted_enumeration_explicitly_refused=True,
                original_definitions_unchanged_by_instantiation=True)


def closed_content_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=conditional.document()
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    values,_=conditional.closed.arguments()
    values.update(history='i[point d][k zbranchhistory[v branch v point]]',
        before='i[first d last d][k ic[v first v last v branch]]',
        members='i[person a point d][k zbranchmembers[v branch v person v point]]')
    subgroup='i[person a opportunity d][k hzhb[v person k zgoverned[] v opportunity p zappointed p zguardian]]'
    text='d zexistentialcontents[branch d] e[k hzpf['+' '.join(values[n] for n,t in FUTURE)+' '+subgroup+']].'
    args='k zpermissionaudience[] k zpermissionreference[] k zpermissionsource[] k zpermissionframe[] p zorigins p zbranches p zexistentialcontents'
    text+='q[k hzon[k hzp5[] k wa[] r b[k hzpa['+args+']] k hzp3[]]].'
    doc=parse(format_graph(doc,'compact')+text)
    interpretations={d['name']:prior.unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def attributed(node,author,description,context):
        body=json.loads(description.syntax)
        return (node,author,context)==('claim','author','context') and description.rank==1 and body['symbol']=='hzpa' and body['arguments'][-1]==dict(kind='function_ref',symbol='zexistentialcontents')
    interpretations.update(hzon=attributed,hzp5=lambda:'claim',wa=lambda:'author',hzp3=lambda:'context')
    options=dict(individuals=('claim','author'),situations=('context',),primitives=interpretations)
    assert evaluate_document(doc,**options)[0]['value'] is True
    interpretations['hzon']=lambda *args:False
    assert evaluate_document(doc,**options)[0]['value'] is False
    return dict(existential_future_content_connects_to_permission_condition=True,
        closed_ranked_attribution_without_world_evaluation=True,
        full_existential_truth_not_inferred_from_attribution=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-5]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==33
    for name,entry in old.entries.items(): assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31): assert selection_binding(old,[index])==selection_binding(new,[index])
    definitions={d['name']:d for d in new.document['declarations']}
    def prefix(node):
        binders=[]
        while node['kind']=='exists':
            binders.append((node['variable'],node['sort']));node=node['body']
        return binders,node
    local,matrix=prefix(definitions['hzpb']['body'])
    assert [t for n,t in local]==['individual',{'kind':'sequence','element':'individual'},'individual','situation','situation']
    shared,body=prefix(definitions['hzpd']['body'])
    assert [t for n,t in shared]==['individual','situation','situation'] and body['symbol']=='hzpc'
    def calls(node,symbol):
        result=[]
        if isinstance(node,dict):
            if node.get('kind')=='call' and node['symbol']==symbol: result.append(node)
            for item in node.values(): result+=calls(item,symbol)
        elif isinstance(node,list):
            for item in node: result+=calls(item,symbol)
        return result
    target_call,=calls(definitions['hzpc']['body'],'hzpb')
    shared_positions=[i for i,(n,t) in enumerate(ROUTE) if n in ('departure','prior','attained')]
    # Parameters of hzpc keep the same names as their enclosing existential arguments.
    for position,binder in zip(shared_positions,shared,strict=True):
        actual=target_call['arguments'][position]
        parameter_index=next(i for i,p in enumerate(definitions['hzpc']['parameters']) if p['name']==actual['name'])
        assert body['arguments'][parameter_index]==dict(kind='variable',name=binder[0])
    assert len(calls(definitions['hzpe']['body'],'hzhh'))==1 and len(calls(definitions['hzpe']['body'],'hzpd'))==1
    return dict(new_compositions=5,new_primitives=0,existing_statements=33,
        seven_review_bindings_preserved=True,unbounded_sequence_sort_preserved=True,
        departure_witnesses_shared_outside_recipient_scope=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items(): assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/conditional-dissemination-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items(): assert digest((ROOT/path).read_bytes())==sha,path
    alignment=deepcopy(previous['alignment'])
    for row in alignment['segments']:
        row.update(definitions=list(MEANINGS),status='partial_existential_dissemination',
            remaining=['source-appropriate interpretation parameters and full-content binding',
                       'comparison and metaphor','whole-unit meaning review'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/conditional-dissemination-v1.json','noema/existential_witnesses.py',
        'scripts/compose_existential_dissemination.py','scripts/check_existential_dissemination.py',
        'tests/test_existential_witnesses.py','tests/test_existential_dissemination.py','docs/existential-dissemination-v1.md'}
    results={}
    for name,check in [('native',native_checks),('boundary',boundary_checks),
                       ('closed_content',closed_content_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='unrestricted_route_existence_with_local_native_witness_certificates',document=FULL,
        **results,roundtrips=True,alignment=alignment,new_source_assertions=0,
        whole_group_existential_truth_certified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream: stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Existential route syntax and native witness certificates checked',flush=True)


if __name__=='__main__': main()
