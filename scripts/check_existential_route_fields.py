"""Check recipient-local route witnesses without enumerating function domains."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.existential_witnesses import instantiate_witnesses,verify_witnesses
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_existential_dissemination as routes
from scripts import check_qualitative_receipt as receipt
from scripts.compose_existential_route_fields import (
    ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,METADATA,SPECS,SUCCESSORS,SOURCE_PROVIDERS,build)

REPORT=ROOT/'reports/existential-route-fields-v1.json'


def merge(doc,other):
    existing={d['name']:d for d in doc['declarations']}
    for declaration in other['declarations']:
        if declaration['name'] in existing:assert declaration==existing[declaration['name']]
        else:doc['declarations'].append(deepcopy(declaration))


@lru_cache(maxsize=1)
def fixture():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    old,witnesses=routes.fixture();merge(doc,old);merge(doc,receipt.document())
    doc['statements']=[]
    args={n:'k z'+n+'[]' for n,t in SPECS['hzpb'] if n not in METADATA}
    args.update(message='r[p zmessage]',state=receipt.STATE)
    doc=parse(format_graph(doc,'compact')+'q[k hzr3['+' '.join(args.values())+']].')
    return doc,[dict(kind='function_ref',symbol='z'+n) for n in METADATA]+deepcopy(witnesses)


def options(doc,variant='baseline'):
    # Preserve the actual self-departure history and causal event; only replace
    # the recipient's old numerical disposition by its qualitative description.
    values=routes.prior.model(doc,variant,native=True)
    recipient=receipt.model(doc,variant)
    departure_cause=values['g3']
    for name in ('zcases','zpreferred','zpoints','zassessed','zweights','zthreshold'):
        values[name]=recipient[name]
    values['g3']=lambda act,person,state,point:departure_cause(act,person,state,point) if act=='departure' else recipient['g3'](act,person,state,point)
    return dict(individuals=routes.prior.NATIVE,situations=routes.prior.POINTS,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=24000000,memoize_definitions=True,memoize_expressions=True)


def native_checks():
    doc,witnesses=fixture();rows={}
    for variant in ('baseline','missing_receipt','no_self_work','no_departure_cause',
        'wrong_causal_preference','lost_after','first_send_outside_frame','recipient_end_outside_frame',
        'completed_at_initial','started_before_initial'):
        result=verify_witnesses(doc,witnesses,**options(doc,variant))
        assert result['instance_value']==(variant in ('baseline','started_before_initial')),(variant,result)
        assert result['witnesses_checked']==9 and not result['theorem_disproved']
        rows[variant]=result['status']
    wrong=[]
    for index,replacement in enumerate((witnesses[1],witnesses[0],
        dict(kind='lambda',parameters=[dict(name='step',sort='individual')],body=dict(kind='call',symbol='zsubject',arguments=[])),
        dict(kind='lambda',parameters=[dict(name='step',sort='individual')],body=dict(kind='call',symbol='zinitial',arguments=[])))):
        chosen=deepcopy(witnesses);chosen[index]=deepcopy(replacement)
        result=verify_witnesses(doc,chosen,**options(doc))
        assert result['status']=='uncertified' and not result['theorem_disproved'];wrong.append(result['status'])
    assert verify_witnesses(doc,witnesses,**options(doc))['status']=='valid'
    return dict(native_contrasts=rows,wrong_sender_recipient_activity_and_time=wrong,
        failed_witness_does_not_disprove_claim=True,native_departure_receipt_causality_retention_executed=True,
        explicit_function_terms_checked_without_enumeration=True,all_evaluations_eager=True)


def boundary_checks():
    doc,witnesses=fixture()
    for name in ('h4n','g3','h7q','h6e','zsender'):
        interpretation=options(doc);interpretation['primitives'][name]=receipt.UNKNOWN
        try:verify_witnesses(doc,witnesses,**interpretation)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    try:evaluate_document(doc,**options(doc))
    except ValueError as error:assert 'Finite function domain exceeds 4096 tables' in str(error),error
    else:raise AssertionError('Unrestricted function domain silently restricted')
    wrong=deepcopy(witnesses);wrong[0]=deepcopy(witnesses[3])
    try:instantiate_witnesses(doc,wrong)
    except ValueError:pass
    else:raise AssertionError('Situation-valued function accepted as person-valued')
    assert instantiate_witnesses(doc,witnesses)['declarations']==doc['declarations']
    return dict(unknown_inputs_refused=5,function_type_mismatch_refused=True,
        unrestricted_enumeration_explicitly_refused=True,original_definitions_unchanged_by_instantiation=True)


def attribution_checks():
    thinkers=receipt.thinkers
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));merge(doc,thinkers.native_document())
    doc=parse(format_graph(doc,'compact')+'r zresponsepreferred[a d d d] c.')
    state=receipt.STATE.replace('r[p zpreferred]','r[p zresponsepreferred]')
    values,_=thinkers.prior.conditional.closed.arguments()
    values.update(state=state,thinkpreferred='p zpreferred',
        members='i[person a point d][k zbranchmembers[v branch v person v point]]')
    supplied=' '.join('i[branch d]['+values[n]+']' for n,t in SOURCE_PROVIDERS)
    frame='r b[k rqu2['+thinkers.prior.attributed.previous.prior.CONDITION_ARGS+' '+supplied+']]'
    doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+'q[k hzpy['+frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]]].')
    rows={}
    for reported,backgrounded in product((False,True),repeat=2):
        seen=[];model=thinkers.prior.attributed.previous.unknown_values(doc)
        model.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        model.update(thinkers.prior.attributed.relation_values(reported,backgrounded,seen))
        actual=thinkers.prior.attributed.evaluate(doc,model);assert actual==[reported and backgrounded]
        refs=_references(seen[0][3])
        assert {'rqu2','hzr2','hzhb','zpreferred','zresponsepreferred'}<=refs
        assert not {'z'+n for n in METADATA}&refs
        assert seen[0][3]==seen[1][3] and {'rqts','hzpt'}<=_references(seen[1][4])
        rows[str((reported,backgrounded))]=actual
    return dict(closed_attribution_contrasts=rows,external_route_field_providers=0,
        remaining_branch_providers=len(SOURCE_PROVIDERS),world_truth_not_executed=True,
        whole_group_existential_truth_not_inferred=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-7]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    definitions={d['name']:d for d in new.document['declarations']}
    def prefix(node):
        bound=[]
        while node['kind']=='exists':bound.append((node['variable'],node['sort']));node=node['body']
        return bound,node
    def calls(node,name):
        if isinstance(node,list):return sum((calls(x,name) for x in node),[])
        if not isinstance(node,dict):return []
        return ([node] if node.get('kind')=='call' and node['symbol']==name else [])+sum((calls(v,name) for v in node.values()),[])
    local,matrix=prefix(definitions['hzr3']['body'])
    assert len(local)==9 and local[5][1]==dict(kind='sequence',element='individual')
    for index,target in enumerate(('individual','individual','individual','situation')):
        assert local[index][1]==dict(kind='function',parameters=['individual'],result=target),local[index]
    shared,body=prefix(definitions['hzr5']['body'])
    assert [t for n,t in shared]==['individual','situation','situation'] and body['symbol']=='hzr4'
    target,=calls(definitions['hzr4']['body'],'hzr3')
    remaining=[n for n,t in SPECS['hzpb'] if n not in METADATA]
    for field,binder in zip(('departure','prior','attained'),shared,strict=True):
        actual=target['arguments'][remaining.index(field)]
        position=next(i for i,p in enumerate(definitions['hzr4']['parameters']) if p['name']==actual['name'])
        assert body['arguments'][position]==dict(kind='variable',name=binder[0])
    for oldname,newname in SUCCESSORS.items():assert len(definitions[newname]['parameters'])==len(SPECS[oldname])-4
    assert len(SOURCE_PROVIDERS)==13 and len(calls(matrix,'hzoe'))==1
    return dict(new_compositions=7,new_primitives=0,existing_statements=34,seven_review_bindings_preserved=True,
        route_function_witnesses_recipient_local=True,departure_witnesses_shared=True,unbounded_path_sort_preserved=True,
        source_branch_providers_before=17,source_branch_providers_after=13,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/qualitative-receipt-v1.json').read_text(encoding='utf-8'))
    for p,sha in previous['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)|set(previous['source_sha256'])|{
        'reports/qualitative-receipt-v1.json','scripts/compose_existential_route_fields.py',
        'scripts/check_existential_route_fields.py','tests/test_existential_route_fields.py','docs/existential-route-fields-v1.md'}
    results={}
    for name,fn in [('native',native_checks),('boundary',boundary_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0011')
    return dict(status='recipient_local_existential_route_fields_checked',document=FULL,**results,roundtrips=True,
        new_source_assertions=0,new_covered_characters=0,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=422,end=440,source=unit['text'][422:440],
            definitions=['hzr3','hzr4','hzr5'],status='partial_existential_route_fields',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Recipient-local route fields checked',flush=True)


if __name__=='__main__':main()
