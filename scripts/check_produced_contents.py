"""Check one causal/result description and statically quotable causal goals."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_continuing_institutions as continuing
from scripts import check_purposive_undertakings as purpose
from scripts.compose_limits import call as k
from scripts.compose_produced_contents import ROOT,PARENT,BUILDERS,ACT,CONTENT
from scripts.compose_continuing_institutions import SOURCE as RETENTION,SCALED

REPORT=ROOT/'reports/produced-contents-v1.json'
EXTRA=('r jzagents[a] c.r jzact[] a.r jzctx[] d.r jzoccurs[a d] c.r jzpart[a a d] c.'
    'r jzcause[a i[e] d] c.r jztruth[d] c.'
    'd jzresult[] e[b scene[k jztruth[v scene]]].d jzalias[] e[b scene[k jztruth[v scene]]].')
REFS=dict(agents='p jzagents',act='k jzact[]',result='r[k jzresult[]]',context='k jzctx[]',occurs='p jzoccurs',participates='p jzpart',produces='p jzcause')


def setup(text):
    return candidate(text,EXTRA+'q['+k('rig',*(REFS[n] for n,_ in ACT))+'].q[t['+k('rih',*(REFS[n] for n,_ in CONTENT))+'][k jzctx[]]].')


def model_for(doc,bits=(True,)*5,variant='baseline'):
    occurs,first,second,causes,result=bits;model=guarded(doc)
    expected=syntax(description(doc,'k '+('jzalias' if variant=='alias' else 'jzresult')+'[]'))
    members=() if variant=='empty_agents' else ('alpha','beta','other') if variant=='extra_agent' else ('alpha','beta')
    def occurrence(act,scene):return occurs and scene=='now' and (act=='acta' or variant=='alternative' and act=='actb')
    def participates(person,act,scene):
        target='actb' if variant=='split_act' else act if variant=='alternative' else 'acta'
        return (person=='alpha' and first or person=='beta' and second) and act==target and scene=='now'
    def produces(act,desc,scene):
        target='actb' if variant=='alternative' else 'acta'
        point='future' if variant=='split_time' else 'now'
        return causes and (act,scene)==(target,point) and desc.syntax==expected
    model.update(jzagents=lambda p:p in members,jzact=lambda:'acta',jzctx=lambda:'now',jzoccurs=occurrence,
        jzpart=participates,jzcause=produces,jztruth=lambda scene:result)
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:model[n] for n in names}


def generic_checks(texts):
    docs=[setup(t) for t in texts];cases=[]
    for bits in product((False,True),repeat=5):
        rows=[values(d,model_for(d,bits),purpose.mutual.PEOPLE,purpose.mutual.SCENES) for d in docs]
        if rows!=[[all(bits),all(bits)]]*len(docs):raise ValueError('Co-occurrence became causal production')
        cases.append(dict(bits=list(bits),results=rows[0]))
    contrasts={}
    for variant in ('alias','empty_agents','extra_agent','split_act','split_time','alternative'):
        rows=[values(d,model_for(d,variant=variant),purpose.mutual.PEOPLE,purpose.mutual.SCENES) for d in docs]
        want=[False,True] if variant=='alternative' else [False,False]
        if rows!=[want]*len(docs):raise ValueError('Causal content contrast '+variant+': '+repr(rows))
        contrasts[variant]=want
    for d in docs:
        for name in ('jzagents','jzoccurs','jzpart','jzcause','jztruth'):
            model=model_for(d);model[name]=guarded(d)[name]
            try:values(d,model,purpose.mutual.PEOPLE,purpose.mutual.SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown causal or result interpretation guessed')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,unknown_relations_refused=True,
        same_description_for_causation_and_result=True)


def source_setup(text,retention='hzcn'):
    doc,original=purpose.source_setup(text)
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+EXTRA+continuing.LIMIT_EXTRA);doc['statements']=statements
    refs=purpose.TIER_REFS|dict(horizons='p jxhorizons')
    effect=apply_description(doc,quoted('function_ref',retention),[description(doc,refs[n]) for n,_ in (SCALED if retention=='hzcp' else RETENTION)])
    specialized=specialize_definition(doc,'hzcq','jzclosed',{1:effect});doc=specialized.document
    goal=apply_description(doc,quoted('function_ref','jzclosed'),[quoted('function_ref','jzagents'),quoted('function_ref','jzcause')])
    def replace(x):
        if isinstance(x,list):return [replace(y) for y in x]
        if not isinstance(x,dict):return x
        if x==original:return deepcopy(goal)
        return {k:replace(v) for k,v in x.items()}
    doc['statements']=replace(doc['statements'])
    direct=dict(kind='call',symbol='hzcq',arguments=[dict(kind='function_ref',symbol='jzagents'),effect,dict(kind='function_ref',symbol='jzcause')])
    doc['statements'].append(dict(kind='ask',body=dict(kind='evaluate',content=direct,situation=dict(kind='call',symbol='je',arguments=[]))))
    trace=dict(bound_positions=specialized.bound_positions,expanded_definitions=specialized.expanded_definitions,disquotations_removed=specialized.disquotations_removed)
    return parse(format_graph(doc,'compact')),goal,effect,trace


def source_model(s,aimed=True,caused=True,retained=True,variant='baseline'):
    doc,goal,effect,_=s;model=purpose.source_model((doc,goal),aimed=aimed)
    dynamic=continuing.model_for(doc,bits=(retained,)*4,variant='stable')
    model.update({n:dynamic[n] for n in ('jwmembers','jwsubjects','jwhist','jwrange','jwbefore','jwcontrols')})
    model['dc']=dynamic['jwcontrols'];model['ic']=lambda a,b,c:dynamic['jwbefore'](c,a,b)
    selected=('alpha','acta') if variant=='nonhuman' else ('alpha','beta')
    model['jzagents']=lambda p:p in selected
    previous=model['dg'];model['dg']=lambda a,c:previous(a,c) or variant!='no_occurrence' and (a,c)==('other','now')
    model['df']=lambda p,a,c:p in selected and (a,c)==('other','now') and not(variant=='missing_participant' and p=='beta')
    target=syntax(effect)
    model['jzcause']=lambda a,r,c:caused and (a,c)==('other','now') and r.syntax==target
    return model


def source_checks(texts):
    setups=[source_setup(t) for t in texts];cases=[]
    for aimed,caused,retained in product((False,True),repeat=3):
        rows=[values(s[0],source_model(s,aimed,caused,retained),purpose.mutual.PEOPLE,purpose.mutual.SCENES) for s in setups]
        want=[aimed,True,caused and retained,caused and retained]
        if rows!=[want]*len(setups):raise ValueError('Causal aim asserted successful perpetuation')
        cases.append(dict(aimed=aimed,caused=caused,retained=retained,results=want))
    contrasts={}
    for variant in ('nonhuman','no_occurrence','missing_participant'):
        rows=[values(s[0],source_model(s,variant=variant),purpose.mutual.PEOPLE,purpose.mutual.SCENES) for s in setups]
        if rows!=[[True,True,False,False]]*len(setups):raise ValueError('Source causal agents changed')
        contrasts[variant]=rows[0]
    for s in setups:
        model=source_model(s);model['jzcause']=guarded(s[0])['jzcause'];doc=deepcopy(s[0]);doc['statements']=doc['statements'][:2]
        if values(doc,model,purpose.mutual.PEOPLE,purpose.mutual.SCENES)!=[True,True]:raise ValueError('Unknown causation blocked a purpose')
        try:values(s[0],model,purpose.mutual.PEOPLE,purpose.mutual.SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown achieved causation filled in')
        for notation in ('full','compact'):
            form=format_graph(s[0],notation)
            if parse(form)!=s[0] or parse(decode(encode(form,'v2')))!=s[0]:raise ValueError('Specialized causal goal changed')
    stronger={}
    for retention in ('hzco','hzcp'):
        for text in texts:
            s=source_setup(text,retention);doc=deepcopy(s[0]);doc['statements']=doc['statements'][:2]
            if values(doc,source_model(s),purpose.mutual.PEOPLE,purpose.mutual.SCENES)!=[True,True]:raise ValueError('Unending causal purpose could not be stated')
            if retention=='hzco':
                if values(s[0],source_model(s),purpose.mutual.PEOPLE,purpose.mutual.SCENES)!=[True,True,False,False]:raise ValueError('Finite history became eternal effect')
            else:
                try:values(s[0],source_model(s),purpose.mutual.PEOPLE,purpose.mutual.SCENES)
                except ValueError as exc:
                    if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
                else:raise ValueError('All numeric horizons sampled')
        stronger[retention]='finite_goal_false' if retention=='hzco' else 'numeric_evaluation_refused'
    return dict(cases=cases,contrasts=contrasts,stronger_goals=stronger,specialization=[s[3] for s in setups],
        standalone_agrees=True,dynamic_and_specialized_agree=True,closed_goal_roundtrips=True,
        unknown_causation_not_inferred=True,normative_absence_is_explicit_oracle=True)


def refusal_checks(text):
    doc=candidate(text,EXTRA);result={}
    try:parse(format_graph(doc,'compact')+'q[e[r[p hzcq]][r[p hzcq]]].')
    except ValueError as exc:
        if 'disquot' not in str(exc).lower():raise
        result['dynamic_constructor_unquotable']=str(exc)
    else:raise ValueError('Dynamic disquotation became quotable')
    try:specialize_definition(doc,'hzcq','jzclosed',{})
    except ValueError as exc:
        if 'Disquotation is not statically' not in str(exc):raise
        result['unknown_result_not_specialized']=str(exc)
    else:raise ValueError('Unknown causal result specialized')
    return result


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored produced content differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Produced content roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    phrase='zu verewigen'
    if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
    start=unit['text'].index(phrase)
    segment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=['rig','rih','hzcq'])
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_produced_contents.py','scripts/check_produced_contents.py','scripts/check_continuing_institutions.py','scripts/check_purposive_undertakings.py',
        'noema/finite_semantics.py','noema/extraction.py','noema/description_templates.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_produced_content_and_causal_goal',documents=documents,sizes=sizes,
        generic=generic_checks([texts[0],texts[2]]),source=source_checks(texts[1:]),refusals=refusal_checks(texts[2]),
        alignment=dict(segments=[segment],semantic_completion=False),new_definitions=3,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Produced content report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same described causal result, shared acts, specialization and unfulfilled perpetuation goals checked')


if __name__=='__main__':main()
