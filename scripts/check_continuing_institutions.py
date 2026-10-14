"""Check role turnover and distinguish finite tails from unending goals."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

import z3
from noema.description_templates import apply_description
from noema.first_order_proofs import verify
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_unending_persistence import numerical_witnesses
from scripts import check_purposive_undertakings as old
from scripts.compose_limits import call as k
from scripts.compose_continuing_institutions import ROOT,PARENT,BUILDERS,POINT,TAIL,NUMERIC,SOURCE,SCALED

REPORT=ROOT/'reports/continuing-institutions-v1.json'
REFS=old.TIER_REFS|dict(scene='k jwnow[]',history='k jwhistory[k jwnow[]]',before='k jworder[k jwnow[]]',anchor='k jwnow[]',beyond='p jxlimit')
LIMIT_EXTRA=('r jxbeyond[d b d] c.d jxhorizons[anchor d] h[b d] c[i[horizon b scene d][k jxbeyond[v anchor v horizon v scene]]].')


def setup(text):
    q=''.join('q['+k(name,*(REFS[n] for n,_ in fields))+'].' for name,fields in (('ric',POINT),('rid',TAIL),('rie',TAIL)))
    return candidate(text,old.TIER_EXTRA+q)


def model_for(doc,bits=(True,)*4,variant='turnover'):
    model=old.tier_model(doc)
    def members(p,c):
        if variant=='empty_current_members' and c=='now' or variant=='empty_future_members' and c=='future':return False
        wanted='alpha' if c=='now' or variant in ('stable','target_turnover') else 'beta'
        return c in ('now','future') and p==wanted
    def subjects(p,c):
        if variant=='empty_current_subjects' and c=='now' or variant=='empty_future_subjects' and c=='future':return False
        wanted='acta' if c=='now' or variant in ('stable','member_turnover') else 'actb'
        return c in ('now','future') and p==wanted
    def controls(a,b,c):
        if c not in ('now','future'):return False
        member='alpha' if c=='now' or variant in ('stable','target_turnover') else 'beta'
        subject='acta' if c=='now' or variant in ('stable','member_turnover') else 'actb'
        upper,lower=bits[:2] if c=='now' else bits[2:]
        if c=='future' and variant in ('future_loss','short_scope'):lower=False
        return upper and (a,b)==('pact',member) or lower and (a,b)==(member,subject)
    model.update(jwmembers=members,jwsubjects=subjects,jwcontrols=controls)
    if variant=='short_scope':model['jwrange']=lambda anchor,scene:scene=='now'
    if variant=='empty_scope':model['jwrange']=lambda anchor,scene:False
    if variant=='missing_anchor':model['jwhist']=lambda anchor,scene:scene in ('first','second','future')
    if variant=='cycle':
        before=model['jwbefore'];model['jwbefore']=lambda anchor,a,b:before(anchor,a,b) or (a,b)==('future','now')
    return model


def finite_checks(texts):
    docs=[setup(t) for t in texts];cases=[]
    for bits in product((False,True),repeat=4):
        rows=[values(d,model_for(d,bits),old.mutual.PEOPLE,old.mutual.SCENES) for d in docs]
        expected=[bits[0] and bits[1],all(bits),False]
        if rows!=[expected]*len(docs):raise ValueError('Turnover confused point, tail or endless history')
        cases.append(dict(edges=list(bits),results=expected))
    contrasts={}
    for variant in ('stable','member_turnover','target_turnover','turnover','future_loss','short_scope','empty_scope',
        'empty_current_members','empty_current_subjects','empty_future_members','empty_future_subjects','missing_anchor','cycle'):
        rows=[values(d,model_for(d,variant=variant),old.mutual.PEOPLE,old.mutual.SCENES) for d in docs]
        expected=[False,False,False] if variant.startswith('empty_current') else [True,True,False] if variant in ('stable','member_turnover','target_turnover','turnover','empty_scope') else [True,False,False]
        if rows!=[expected]*len(docs):raise ValueError('Future tail contrast '+variant+': '+repr(rows))
        contrasts[variant]=expected
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,no_finite_history_claimed_endless=True,
        observed_scope_not_used_as_whole_history=True)


def general_laws(text):
    args=[REFS[n] for n,_ in TAIL]
    tail=k('rid',*args);endless=k('rie',*args);point=k('ric',*(REFS[n] for n,_ in POINT))
    future='c[k rby['+' '.join(REFS[n] for n in ('history','before','anchor'))+']][v scene]'
    same_people='f person a[y[k jwmembers[v person k jwnow[]]][f scene d[y['+future+'][k jwmembers[v person v scene]]]]]'
    last='w[k jwhist[k jwnow[] k jxlast[]]][f scene d[y[k jwhist[k jwnow[] v scene]][u[k jwbefore[k jwnow[] k jxlast[] v scene]]]]]'
    claims={
        'endless_implies_future_tail':'y['+endless+']['+tail+']',
        'future_tail_includes_current_roles':'y['+tail+']['+point+']',
        'a_last_point_blocks_endlessness':'y['+last+'][u['+endless+']]',
        'point_implies_whole_future':'y['+point+']['+tail+']',
        'whole_future_implies_endlessness':'y['+tail+']['+endless+']',
        'whole_future_requires_original_people':'y['+tail+']['+same_people+']',
    }
    doc=candidate(text,old.TIER_EXTRA+'r jxlast[] d.'+''.join('s['+expr+'].' for expr in claims.values()))
    rows=verify(doc,timeout_ms=10000,max_expansion=500_000)
    if [r['status'] for r in rows]!=['valid']*3+['invalid']*3:raise ValueError('Temporal law statuses: '+repr([r['status'] for r in rows]))
    return dict(domain='arbitrary nonempty individual and situation domains',solver_version=z3.get_version_string(),
        claims={n:dict(status=r['status'],formula_sha256=hashlib.sha256(r['formula'].encode()).hexdigest(),countermodel_found=r['countermodel'] is not None) for n,r in zip(claims,rows,strict=True)})


def horizon_refusal(text):
    doc=candidate(text,old.TIER_EXTRA+'r jxlimit[b d] c.q['+k('rif',*(REFS[n] for n,_ in NUMERIC))+'].')
    model=model_for(doc);model['jxlimit']=lambda h,p:False
    try:values(doc,model,old.mutual.PEOPLE,old.mutual.SCENES)
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
        return dict(refused=True,reason=str(exc))
    raise ValueError('All time limits became finite samples')


def source_setup(text,target='hzco'):
    doc,original=old.source_setup(text)
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+LIMIT_EXTRA);doc['statements']=statements
    refs=old.TIER_REFS|dict(horizons='p jxhorizons')
    goal=apply_description(doc,quoted('function_ref',target),[description(doc,refs[n]) for n,_ in (SCALED if target=='hzcp' else SOURCE)])
    def replace(x):
        if isinstance(x,list):return [replace(y) for y in x]
        if not isinstance(x,dict):return x
        if x==original:return deepcopy(goal)
        return {k:replace(v) for k,v in x.items()}
    doc['statements']=replace(doc['statements'])
    return parse(format_graph(doc,'compact')),goal


def source_model(setup,aimed=True,absence=True,variant='turnover'):
    doc,goal=setup;model=old.source_model(setup,aimed=aimed,absence=absence);dynamic=model_for(doc,variant=variant)
    model.update({n:dynamic[n] for n in ('jwmembers','jwsubjects','jwhist','jwrange','jwbefore','jwcontrols')})
    model['dc']=dynamic['jwcontrols'];model['ic']=lambda a,b,c:dynamic['jwbefore'](c,a,b)
    return model


def source_checks(texts):
    cases=[]
    for target in ('hzcn','hzco','hzcp'):
        setups=[source_setup(t,target) for t in texts]
        for aimed,absence in product((False,True),repeat=2):
            for s in setups:
                d=deepcopy(s[0]);d['statements']=d['statements'][:2]
                got=values(d,source_model(s,aimed,absence),old.mutual.PEOPLE,old.mutual.SCENES)
                if got!=[aimed,not aimed or absence]:raise ValueError('Unending purpose became achieved fact')
            cases.append(dict(target=target,aimed=aimed,no_normative_effect=absence,results=got))
        for s in setups:
            for notation in ('full','compact'):
                form=format_graph(s[0],notation)
                if parse(form)!=s[0] or parse(decode(encode(form,'v2')))!=s[0]:raise ValueError('Closed continuing goal changed')
            if target=='hzcp':
                try:values(s[0],source_model(s),old.mutual.PEOPLE,old.mutual.SCENES)
                except ValueError as exc:
                    if 'Cannot finitely quantify the rational number domain' not in str(exc):raise
                else:raise ValueError('All numeric horizons were guessed')
            else:
                got=values(s[0],source_model(s),old.mutual.PEOPLE,old.mutual.SCENES)
                if got!=[True,True,target=='hzcn']:raise ValueError('Temporal strengths collapsed')
    comparisons={}
    for variant in ('stable','turnover','short_scope','empty_scope'):
        for text in texts:
            d=old.tier_setup(text);d['statements']=d['statements'][1:]
            refs=old.TIER_REFS
            q='q[t['+k('hzcn',*(refs[n] for n,_ in SOURCE))+'][k jwnow[]]].'
            d=parse(format_graph(d,'compact')+q);model=model_for(d,variant=variant)
            model['dc']=model['jwcontrols'];model['ic']=lambda a,b,c:model['jwbefore'](c,a,b)
            got=values(d,model,old.mutual.PEOPLE,old.mutual.SCENES)
            expected={'stable':[True,True],'turnover':[False,True],'short_scope':[True,False],'empty_scope':[False,True]}[variant]
            if got!=expected:raise ValueError('Fixed and continuing role scopes conflated')
        comparisons[variant]=got
    return dict(cases=cases,comparisons=comparisons,standalone_agrees=True,closed_goal_roundtrips=True,
        numeric_goal_can_be_quoted_without_evaluation=True,numeric_evaluation_refused=True,
        normative_absence_is_explicit_oracle=True)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored continuing institution differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Continuing institution roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    phrase='unaufhörliche'
    if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
    start=unit['text'].index(phrase)
    segment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=['rid','rie','rif','hzcn','hzco','hzcp'])
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_continuing_institutions.py','scripts/check_continuing_institutions.py','scripts/check_purposive_undertakings.py',
        'scripts/check_unending_persistence.py','scripts/compose_unending_persistence.py','noema/first_order_proofs.py','noema/rational_proofs.py',
        'noema/finite_semantics.py','noema/extraction.py','noema/description_templates.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_continuing_roles_and_unending_goals',documents=documents,sizes=sizes,
        finite=finite_checks([texts[0],texts[2]]),laws=general_laws(texts[0]),numeric_witnesses=numerical_witnesses(),
        horizon_refusal=horizon_refusal(texts[0]),source=source_checks(texts[1:]),
        alignment=dict(segments=[segment],semantic_completion=False),new_definitions=7,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Continuing institution report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Role turnover, temporal strengths, first-order laws and unending purpose descriptions checked')


if __name__=='__main__':main()
