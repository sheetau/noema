"""Check common existential frames and conditional scalar scope separately."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_conditional_dissemination as conditional
from scripts import check_focused_dissemination as focused
from scripts.compose_existential_focus import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,MEANINGS,FUTURE,PREDICATE,FRAME,FAMILY,build

prior=conditional.prior
REPORT=ROOT/'reports/existential-focus-v1.json'
CONDITION_ARGS='k zpermissionaudience[] k zpermissionreference[] k zpermissionsource[] k zpermissionframe[] p zorigins p zbranches'
META='r zfocus[a d] c.r zother[a d] c.r zobserver[] a.r zranking['+focused.scalar.ORDER[2:focused.scalar.ORDER.rfind(']')]+'] c.'


def merged():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=conditional.document()
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    return doc


def package(frame,focus='r[p zfocus]',other='r[p zother]'):
    return 'k rqtm['+frame+' '+focus+' l['+PREDICATE+']['+other+'] r[k zobserver[]] r[k zactual[]] r[p zranking]]'


@lru_cache(maxsize=1)
def generic_document():
    doc=merged()
    text=META+'r zexpected[d] d.'
    text+='d ztestfamily[subgroup '+PREDICATE+' branch d] e[b point[w[e[v point][k zexpected[v branch]]][c[s[v subgroup]][k zorigin[] v branch]]]].'
    frame='r b[k rqtp['+CONDITION_ARGS+' p ztestfamily]]'
    return parse(format_graph(doc,'compact')+text+focused.queries(package(frame),'k zactual[]',
        'k rqtk['+frame+' r[p zother]]'))


def ranking(observer,left,right,anchor,ranked=True,kind='generic'):
    frame,a=focused.subgroup(left);otherframe,b=focused.subgroup(right)
    assert frame==otherframe
    if kind=='single':
        assert frame['kind']=='apply' and frame['function']==dict(kind='function_ref',symbol='hzpq')
        assert len(frame['arguments'])==len(FUTURE)==22
        assert frame['arguments'][[n for n,t in FUTURE].index('state')]==dict(kind='quote',body=prior.profiles.described_state())
    else:
        assert frame['kind']=='call' and frame['symbol']=='rqtp' and len(frame['arguments'])==7
        assert frame['arguments'][:6]==[dict(kind='call',symbol='zpermission'+n,arguments=[]) for n in ('audience','reference','source','frame')]+[
            dict(kind='function_ref',symbol='zorigins'),dict(kind='function_ref',symbol='zbranches')]
    if kind=='generic':
        directed=a==dict(kind='function_ref',symbol='zfocus') and b==dict(kind='function_ref',symbol='zother')
    else:
        directed=(a['kind']==b['kind']=='lambda' and a['parameters']==b['parameters']
            and a['body']['kind']=='call' and a['body']['symbol']=='hzhb'
            and b['body']['kind']=='not' and b['body']['arguments']==[a['body']])
    return ranked and (observer,anchor)==('authority','outside') and directed


def generic_model(doc,focus=(True,True),other=(True,False),ranked=True,permitted_bad=False,variant='baseline'):
    values=conditional.model(doc,'permitted_bad_branch' if permitted_bad else variant)
    values.update(zobserver=lambda:'authority',zranking=lambda a,b,c,d:ranking(a,b,c,d,ranked),
        zexpected=lambda branch:'outside' if variant=='wrong_content_origin' else 'before' if branch=='trialgood' else 'second',
        zfocus=lambda person,branch:person=='sender' and branch in ('trialgood','trialbad') and focus[('trialgood','trialbad').index(branch)],
        zother=lambda person,branch:person=='sender' and branch in ('trialgood','trialbad') and other[('trialgood','trialbad').index(branch)])
    return values


def conditional_checks():
    doc=generic_document();count=0
    for first,last,other,ranked,permitted_bad in product((False,True),repeat=5):
        values=generic_model(doc,(first,last),(other,False),ranked,permitted_bad)
        actual=prior.evaluate(doc,values,diagnostic=True)
        foreground=first and (last or not permitted_bad);alternative=other and not permitted_bad
        assert actual==[ranked,foreground,ranked,not foreground,True,alternative],(first,last,other,ranked,permitted_bad,actual)
        count+=1
    rows={}
    for variant in ('baseline','no_freedom','invalid_unpermitted_branch','wrong_origin','wrong_content_origin'):
        actual=prior.evaluate(doc,generic_model(doc,variant=variant),diagnostic=True)
        foreground=variant=='baseline'
        assert actual==[True,foreground,True,not foreground,True,foreground],(variant,actual)
        rows[variant]=actual
    return dict(condition_content_comparison_combinations=count,scope_contrasts=rows,
        original_permission_and_period_definitions_executed=True,
        candidate_contents_are_generic_test_predicates_not_native_dissemination=True,
        conditional_checks_use_explicit_short_circuit_diagnostics=True,
        comparison_background_survives_negation=True,alternative_truth_not_required=True)


@lru_cache(maxsize=2)
def native_document(kind='conditional'):
    doc=merged();values,_=conditional.closed.arguments()
    if kind=='single':
        args=' '.join(values[n] if n=='state' else 'r['+values[n]+']' for n,t in FUTURE)
        frame='k hzpr['+args+']';text=''
    else:
        values.update(history='i[point d][k zbranchhistory[v branch v point]]',
            before='i[first d last d][k ic[v first v last v branch]]',
            members='i[person a point d][k zbranchmembers[v branch v person v point]]')
        providers=' '.join('i[branch d]['+values[n]+']' for n,t in FUTURE)
        text='d znativefamily[] '+FAMILY+'[k hzps['+providers+']].'
        frame='r b[k rqtp['+CONDITION_ARGS+' k znativefamily[]]]'
    guardian='k hzhb[v person k zgoverned[] v context p zappointed p zguardian]'
    focus='r[i[person a context d]['+guardian+']]'
    other='r[i[person a context d][u['+guardian+']]]'
    return parse(format_graph(doc,'compact')+META+text+focused.queries(package(frame,focus,other),'k zactual[]'))


def native_background_checks():
    rows={};unknowns=0
    for kind in ('single','conditional'):
        doc=native_document(kind);selected=dict(doc,statements=[doc['statements'][i] for i in (0,2,4)])
        for ranked in (False,True):
            values={d['name']:prior.unknown for d in selected['declarations'] if d['kind']=='primitive'}
            values.update(zobserver=lambda:'authority',zactual=lambda:'outside',
                zranking=lambda a,b,c,d:ranking(a,b,c,d,ranked,kind))
            actual=prior.evaluate(selected,values)
            assert actual==[ranked,ranked,True],(kind,actual)
            rows[kind+':'+str(ranked)]=actual
        for name in ('zranking','zobserver','zactual'):
            bad=dict(values);bad[name]=prior.unknown
            try:prior.evaluate(selected,bad)
            except ValueError as error:assert 'Unknown' in str(error),(name,error)
            else:raise AssertionError(name)
            unknowns+=1
    return dict(contrasts=rows,unknown_metadata_refused=unknowns,
        common_existential_arguments=22,world_and_subgroups_never_evaluated=True,
        actual_guardian_predicate_and_complement_compared=True,
        all_background_checks_eager_without_lowering=True,
        unrestricted_native_foreground_truth_not_claimed=True)


def separation_checks():
    doc=generic_document();selected=dict(doc,statements=[doc['statements'][1]])
    values=generic_model(doc);values['zranking']=values['zobserver']=prior.unknown
    assert prior.evaluate(selected,values,diagnostic=True)==[True]
    for name in ('zfocus','zexpected','h7b','zorigins'):
        bad=dict(values);bad[name]=prior.unknown
        try:prior.evaluate(selected,bad,diagnostic=True)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
    return dict(foreground_does_not_execute_comparison_metadata=True,selected_unknowns_refused=4)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-4]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    definitions={d['name']:d for d in new.document['declarations']}
    body=definitions['hzps']['body'];assert body['kind']=='lambda'
    subgroup,branch=[p['name'] for p in body['parameters']]
    call=body['body'];assert call['kind']=='call' and call['symbol']=='hzpf'
    for parameter,argument in zip(definitions['hzps']['parameters'],call['arguments'][:-1],strict=True):
        assert argument==dict(kind='apply',function=dict(kind='variable',name=parameter['name']),
            arguments=[dict(kind='variable',name=branch)])
    assert call['arguments'][-1]==dict(kind='disquote',description=dict(kind='variable',name=subgroup))
    assert definitions['hzpq']['body']['body']['symbol']=='hzpf'
    # Preserve the actual unbounded route existential, not a restricted candidate menu.
    route=definitions['hzpb']['body']['body']
    assert route['kind']=='exists' and route['sort']==dict(kind='sequence',element='individual')
    return dict(new_compositions=4,new_primitives=0,existing_statements=34,seven_review_bindings_preserved=True,
        same_branch_supplied_to_all_22_fields=True,unbounded_route_existence_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/yoke-depiction-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    source=json.loads((ROOT/'reports/focused-dissemination-v1.json').read_text(encoding='utf-8'))
    alignment=deepcopy(source['alignment'])
    for row in alignment['segments']:
        row.update(definitions=list(MEANINGS),status='partial_existential_conditional_focus',
            remaining=['source-appropriate comparison scale and alternatives','full source content assertion','whole-unit meaning review'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        'reports/yoke-depiction-v1.json','reports/focused-dissemination-v1.json',
        'scripts/compose_existential_focus.py','scripts/check_existential_focus.py','tests/test_existential_focus.py','docs/existential-focus-v1.md'}
    results={}
    for name,check in [('conditional',conditional_checks),('native_background',native_background_checks),
                       ('separation',separation_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='shared_existential_and_conditional_frames_with_separate_scalar_background',document=FULL,
        **results,roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Common existential frames and conditional comparison scopes checked',flush=True)


if __name__=='__main__':main()
