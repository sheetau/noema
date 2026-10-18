"""Execute shared-frame scalar comparisons separately from native claim truth."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts import check_described_dissemination as closed
from scripts.compose_subject_bound_departure import closure
from scripts.compose_focused_dissemination import ROOT, PARENT, PARENT_BASIS, FULL, CORE, LIBRARY, BASIS, BASE, PREDICATE, FRAME, MEANINGS, scalar, imported, build

prior = closed.prior
REPORT = ROOT / 'reports/focused-dissemination-v1.json'
META = 'r zobserver[] a.r zranking[' + scalar.ORDER[2:scalar.ORDER.rfind(']')] + '] c.'


def queries(package, point, alternative=None):
    text = 'd zpackage[] '+scalar.PAIR+'['+package+'].'
    text += 'q[k rsy[k zpackage[] '+point+']].q[k rsx[k zpackage[] '+point+']].'
    text += 'q[k rsy[k rsw[k zpackage[]] '+point+']].q[k rsx[k rsw[k zpackage[]] '+point+']].'
    text += 'q[e[k rsv[k zpackage[]]][k rsv[k rsw[k zpackage[]]]]].'
    if alternative is not None: text += 'q[t[s['+alternative+']]['+point+']].'
    return text


@lru_cache(maxsize=5)
def generic_document(alternatives='other'):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));doc['statements']=[]
    doc['declarations']=closure(doc,['rqtm','rsx','rsy','rsw','rqti'])
    text='r zmembers[a d] c.r zqualified[a d] c.r zguard[a d] c.r zother[a d] c.r zpoint[] d.'+META
    text+='d zframe[subgroup '+PREDICATE+'] e[b context[k rqti[v context p zmembers s[v subgroup] p zqualified]]].'
    items={'other':'r[p zother]','self':'r[p zguard]','empty':'','duplicate':'r[p zother] r[p zother]'}[alternatives]
    package='k rqtm[r b[p zframe] r[p zguard] l['+PREDICATE+']['+items+'] r[k zobserver[]] r[k zpoint[]] r[p zranking]]'
    return parse(format_graph(doc,'compact')+text+queries(package,'k zpoint[]'))


def subgroup(description):
    body=json.loads(description.syntax)
    assert description.rank==1 and body['kind']=='apply' and len(body['arguments'])==1
    code=body['arguments'][0];assert code['kind']=='quote'
    return body['function'],code['body']


def generic_values(doc,guard=True,other=True,plural=True,ranked=True,variant='baseline',seen=None):
    values={d['name']:prior.unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def rank(observer,left,right,anchor):
        frame,a=subgroup(left);otherframe,b=subgroup(right)
        assert frame==otherframe==dict(kind='function_ref',symbol='zframe')
        if seen is not None:seen.append((a,b))
        return ranked and (observer,anchor)==('speaker','first') and a['symbol']=='zguard' and b['symbol']=='zother'
    values.update(zmembers=lambda person,point:person in ('p','q'),
        zqualified=lambda person,point:person=='p' or (person=='q' and plural),
        zguard=lambda person,point:person=='p' and guard,zother=lambda person,point:person=='q' and other,
        zpoint=lambda:'first',zobserver=lambda:'speaker',zranking=rank)
    if variant=='wrong_observer':values['zobserver']=lambda:'other'
    if variant=='wrong_context':values['zpoint']=lambda:'second'
    return values


def scalar_checks():
    doc=generic_document();count=0
    for guard,other,plural,ranked in product((False,True),repeat=4):
        seen=[];values=generic_values(doc,guard,other,plural,ranked,seen=seen)
        actual=prior.evaluate(doc,values,('p','q','speaker','other'),('first','second'))
        assert actual==[ranked,guard and plural,ranked,not(guard and plural),True],actual
        assert seen;count+=1
    rows={}
    for alternative in ('self','empty','duplicate'):
        doc=generic_document(alternative);actual=prior.evaluate(doc,generic_values(doc),('p','q','speaker'),('first',))
        assert actual==[alternative=='duplicate',True,alternative=='duplicate',False,True],actual
        rows[alternative]=actual
    for variant in ('wrong_observer','wrong_context'):
        doc=generic_document();actual=prior.evaluate(doc,generic_values(doc,variant=variant),('p','q','speaker','other'),('first','second'))
        assert actual==[False,True,False,False,True],actual;rows[variant]=actual
    return dict(truth_and_ranking_combinations=count,contrasts=rows,
        background_preserved_by_foreground_negation=True,alternative_truth_not_required=True,
        all_checks_eager=True)


@lru_cache(maxsize=1)
def native_document():
    old=closed.document('both');doc=parse((ROOT/CORE).read_text(encoding='utf-8'))
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names]
    values,oldclaim=closed.arguments()
    args=' '.join(values[n] if n=='state' else 'r['+values[n]+']' for n,t in BASE)
    frame='k hzp2['+args+']'
    guardian='k hzhb[v person k zgoverned[] v context p zappointed p zguardian]'
    focus='r[i[person a context d]['+guardian+']]'
    other='r[i[person a context d][u['+guardian+']]]'
    text=META+'d zcomparisonframe[] '+FRAME+'['+frame+'].'
    package='k rqtm[k zcomparisonframe[] '+focus+' l['+PREDICATE+']['+other+'] r[k zobserver[]] r[k zcontext[]] r[p zranking]]'
    text+=queries(package,'k zcontext[]','k rqtk[k zcomparisonframe[] '+other+']')
    text+='q[t[s['+oldclaim.replace('k hzoq[','k hzow[',1)+']][k zcontext[]]].'
    return parse(format_graph(doc,'compact')+text)


def native_values(doc,variant='baseline',ranked=True,seen=None):
    values=closed.native_model(doc,'baseline' if variant=='no_appointment' else variant)
    def rank(observer,left,right,anchor):
        frame,a=subgroup(left);otherframe,b=subgroup(right)
        assert frame==otherframe and frame['kind']=='apply'
        assert frame['function']==dict(kind='function_ref',symbol='hzoz') and len(frame['arguments'])==len(BASE)==30
        state=frame['arguments'][[n for n,t in BASE].index('state')]
        assert state==dict(kind='quote',body=prior.profiles.described_state())
        assert a['kind']==b['kind']=='lambda'
        if seen is not None:seen.append((frame,a,b))
        return ranked and (observer,anchor)==('authority','before') and a['body']['kind']=='call' and b['body']['kind']=='not'
    values.update(zobserver=lambda:'authority',zranking=rank)
    if variant=='no_appointment':values['zappointed']=lambda *args:False
    return values


def native_checks():
    doc=native_document();rows={}
    for variant in ('baseline','missing_appointment','no_appointment','borrowed_route'):
        selected=dict(doc,statements=[doc['statements'][i] for i in (0,1,5,6)])
        seen=[];values=native_values(selected,variant,seen=seen)
        actual=prior.evaluate(selected,values,diagnostic=True)
        expected={'baseline':[True,True,False],'missing_appointment':[True,True,True],
                  'no_appointment':[True,False,True],'borrowed_route':[True,False,False]}[variant]
        assert actual==expected+[expected[1]],(variant,actual);assert seen;rows[variant]=actual
    selected=dict(doc,statements=doc['statements'][:2])
    actual=prior.evaluate(selected,native_values(selected,ranked=False),diagnostic=True)
    assert actual==[False,True];rows['background_fails_content_true']=actual
    return dict(contrasts=rows,common_closed_arguments=30,
        native_appointment_thinking_departure_and_dissemination_executed=True,
        foreground_agrees_with_previous_closed_subgroup_content=True,
        full_future_content_uses_explicit_short_circuit_diagnostic=True,
        alternative_truth_not_required_even_when_all_qualified_people_are_guardians=True)


def unknown_checks():
    doc=generic_document();count=0
    # Reading the background does not evaluate either subgroup/world predicate.
    selected=dict(doc,statements=[doc['statements'][0]])
    values=generic_values(selected)
    for name in ('zmembers','zqualified','zguard','zother'):values[name]=prior.unknown
    assert prior.evaluate(selected,values,('p','q','speaker'),('first',))==[True]
    selected=dict(doc,statements=[doc['statements'][1]])
    values=generic_values(selected);values['zranking']=values['zobserver']=prior.unknown
    assert prior.evaluate(selected,values,('p','q','speaker'),('first',))==[True]
    for index,name in ((0,'zranking'),(0,'zobserver'),(1,'zguard'),(1,'zqualified')):
        selected=dict(doc,statements=[doc['statements'][index]]);values=generic_values(selected);values[name]=prior.unknown
        try:prior.evaluate(selected,values,('p','q','speaker'),('first',))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
        count+=1
    native=native_document();selected=dict(native,statements=[native['statements'][0]])
    values=native_values(selected)
    for name in values:
        if name not in ('zobserver','zranking','zcontext'):values[name]=prior.unknown
    assert prior.evaluate(selected,values)==[True]
    return dict(unknown_inputs_refused=count,background_does_not_execute_world_predicates=True,
        foreground_does_not_execute_ranking=True,native_background_with_unknown_world_evaluated_without_lowering=True)


def future_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));doc['declarations']=closure(doc,['rqtj'])
    doc=parse(format_graph(doc,'compact')+'r zhistory[d] c.r zbefore[d d] c.r zbase[] d.r zcondition[d] c.'
              'q[k rqtj[p zhistory p zbefore k zbase[] p zcondition]].')
    points=('past','first','second');rows={}
    for variant in ('baseline','initial_false','late_false','empty_future','base_missing','unordered'):
        values=dict(zhistory=lambda p:p in points,zbefore=lambda a,b:points.index(a)<points.index(b),
                    zbase=lambda:'past',zcondition=lambda p:True)
        if variant=='initial_false':values['zcondition']=lambda p:p!='past'
        if variant=='late_false':values['zcondition']=lambda p:p!='second'
        if variant=='empty_future':values['zhistory']=lambda p:p=='past'
        if variant=='base_missing':values['zhistory']=lambda p:p!='past'
        if variant=='unordered':values['zbefore']=lambda a,b:False
        actual=prior.evaluate(doc,values,('person',),points)
        assert actual==[variant in ('baseline','initial_false')],(variant,actual)
        rows[variant]=actual
    return dict(contrasts=rows,initial_condition_not_asserted=True,all_checks_eager=True)


def rank_checks():
    text=(ROOT/CORE).read_text(encoding='utf-8');count=0
    for extra in ('q[e[r[p hzoz]][r[p hzoz]]].',
                  'q[e[k rqtk[r b[i[subgroup '+PREDICATE+'][b context[e[v context][v context]]]] r[b context[e[v context][v context]]]]][r b[b context[e[v context][v context]]]]].'):
        try:parse(text+extra)
        except ValueError:count+=1
        else:raise AssertionError('Invalid rank or subgroup type accepted')
    return dict(unsafe_rank_and_wrong_argument_type_refused=count)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    added=len(imported())+len(MEANINGS)
    assert new.document['declarations'][:-added]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==32
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_compositions=len(MEANINGS),reused_scalar_definitions=len(imported()),new_primitives=0,
        existing_statements=32,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/subgroup-dissemination-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    alignment=deepcopy(previous['alignment'])
    for row in alignment['segments']:
        row.update(definitions=list(MEANINGS),status='partial_shared_frame_scalar_background_candidate',
            remaining=['source-appropriate focus, alternatives and ranking','modality, causal discourse, metaphor and actual author attribution'])
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        scalar.LIBRARY,scalar.BASIS,'scripts/compose_scalar_backgrounds.py','reports/subgroup-dissemination-v1.json',
        'scripts/compose_focused_dissemination.py','scripts/check_focused_dissemination.py',
        'tests/test_focused_dissemination.py','docs/focused-dissemination-v1.md'}
    results={}
    for name,check in [('scalar',scalar_checks),('native',native_checks),('unknown',unknown_checks),('future',future_checks),('ranks',rank_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='shared_frame_and_separate_background_not_whole_unit_completion',document=FULL,**results,
        roundtrips=True,alignment=alignment,new_source_assertions=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Focused future dissemination and scalar background checked separately',flush=True)


if __name__=='__main__':main()
