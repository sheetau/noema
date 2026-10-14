"""Check purpose witness identity, tier coverage and unachieved goals."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_assessed_payments import description
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_mutual_undertakings as mutual
from scripts.compose_limits import call as k
from scripts.compose_purposive_undertakings import ROOT,PARENT,BUILDERS,ACT,PURPOSE,PURPOSIVE,SOURCE,CONTENT,TIER,ENDURING,TIER_SOURCE

REPORT=ROOT/'reports/purposive-undertakings-v1.json'
PURPOSE_EXTRA=('r jwproponents[a d] c.r jwaims[a a i[e] d] c.r jwtruth[d] c.'
    'd jwcontent[] e[b scene[k jwtruth[v scene]]].d jwother[] e[b scene[k jwtruth[v scene]]].')
TIER_EXTRA=('r jwcontroller[] a.r jwmembers[a d] c.r jwsubjects[a d] c.r jwhist[d d] c.r jwrange[d d] c.'
    'r jwbefore[d d d] c.r jwcontrols[a a d] c.r jwnow[] d.'
    'd jwhistory[anchor d] h[d] c[i[scene d][k jwhist[v anchor v scene]]].'
    'd jwscope[anchor d] h[d] c[i[scene d][k jwrange[v anchor v scene]]].'
    'd jworder[anchor d] h[d d] c[i[first d second d][k jwbefore[v anchor v first v second]]].')
TIER_REFS=dict(controller='k jwcontroller[]',members='p jwmembers',subjects='p jwsubjects',histories='p jwhistory',scopes='p jwscope',orders='p jworder',controls='p jwcontrols')


def purpose_setup(text):
    d=mutual.setup(text);d['statements']=[]
    refs=mutual.REFS|dict(proponents='p jwproponents',goal='r[k jwcontent[]]',aims='p jwaims')
    q=''.join('q['+k(name,*(refs[n] for n,_ in fields))+'].' for name,fields in (('rh6',ACT+PURPOSE),('rh7',PURPOSIVE)))
    return parse(format_graph(d,'compact')+PURPOSE_EXTRA+q+'q[t[k jwcontent[]][k je[]]].')


def purpose_model(doc,aimed=True,actual=False,variant='baseline'):
    old_variant='alternative_witness' if variant in ('separate_witness','matching_alternative') else 'baseline'
    model=mutual.model_for(doc,variant=old_variant)
    selected=() if variant=='empty' else ('other',) if variant=='outsider' else ('alpha','beta') if variant=='everyone' else ('alpha',)
    goal=syntax(description(doc,'k '+('jwother' if variant=='alias' else 'jwcontent')+'[]'))
    record=('beta','actb','second') if variant=='person' else ('alpha','actb','first') if variant=='act' else ('alpha','acta','second') if variant=='time' else ('alpha','other','second') if variant=='matching_alternative' else ('alpha','acta','first')
    model.update(jwproponents=lambda p,c:c=='now' and p in selected,
        jwaims=lambda p,a,g,c:aimed and (p,a,c)==record and g.syntax==goal,jwtruth=lambda c:actual)
    return model


def purpose_checks(texts):
    docs=[purpose_setup(t) for t in texts];cases=[]
    for aimed,actual in product((False,True),repeat=2):
        rows=[values(d,purpose_model(d,aimed,actual),mutual.PEOPLE,mutual.SCENES) for d in docs]
        if rows!=[[aimed,aimed,actual]]*len(docs):raise ValueError('Purpose implies achievement')
        cases.append(dict(aimed=aimed,actual=actual,results=rows[0]))
    contrasts={}
    for variant in ('person','act','time','alias','empty','outsider','everyone','separate_witness','matching_alternative'):
        rows=[values(d,purpose_model(d,variant=variant),mutual.PEOPLE,mutual.SCENES) for d in docs]
        want=[False,True,False] if variant=='matching_alternative' else [True,False,False] if variant in ('empty','outsider','everyone') else [False,False,False]
        if rows!=[want]*len(docs):raise ValueError('Purpose witness contrast '+variant+': '+repr(rows))
        contrasts[variant]=want
    for d in docs:
        model=purpose_model(d);model['jwtruth']=guarded(d)['jwtruth'];only=deepcopy(d);only['statements']=only['statements'][:2]
        if values(only,model,mutual.PEOPLE,mutual.SCENES)!=[True,True]:raise ValueError('Purpose evaluated the goal')
        for name in ('jwaims','jwproponents'):
            model=purpose_model(d);model[name]=guarded(d)[name]
            try:values(only,model,mutual.PEOPLE,mutual.SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown purpose guessed')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,goal_truth_not_executed=True,unknown_purposes_refused=True)


def tier_setup(text):
    point=TIER_REFS|dict(scene='k jwnow[]',members='i[person a][k jwmembers[v person k jwnow[]]]',subjects='i[person a][k jwsubjects[v person k jwnow[]]]')
    return candidate(text,TIER_EXTRA+'q['+k('ria',*(point[n] for n,_ in TIER))+'].q[t['+k('rib',*(TIER_REFS[n] for n,_ in ENDURING))+'][k jwnow[]]].')


def tier_model(doc,bits=(True,)*6,variant='baseline'):
    model=guarded(doc);order=('first','second','now','future')
    edges=(('pact','alpha'),('pact','beta'),('alpha','acta'),('alpha','actb'),('beta','acta'),('beta','actb'))
    def member(p,c):return c=='now' and p in (() if variant=='empty_members' else ('pact','alpha','beta') if variant=='self_upper' else ('alpha','beta'))
    def subject(p,c):return c=='now' and p in (() if variant=='empty_subjects' else ('acta','actb'))
    def controls(a,b,c):
        if variant=='direct_only':return (a,b) in (('pact','acta'),('pact','actb'))
        if variant=='outside_intermediary':return (a,b) in (('pact','alpha'),('pact','beta'),('other','acta'),('other','actb'))
        if variant=='self_upper' and (a,b)==('pact','pact'):return True
        if variant=='future_loss' and c=='future' and b=='actb':return False
        if variant=='changing_delegate':return (a,b) in ((('pact','alpha'),('pact','beta'),('alpha','acta'),('alpha','actb')) if c=='now' else (('pact','alpha'),('pact','beta'),('beta','acta'),('beta','actb')))
        return (a,b) in edges and bits[edges.index((a,b))]
    model.update(jwcontroller=lambda:'pact',jwnow=lambda:'now',jwmembers=member,jwsubjects=subject,
        jwhist=lambda anchor,scene:scene in order,jwrange=lambda anchor,scene:scene in (() if variant=='empty_scope' else ('future',) if variant=='no_anchor' else ('first','now','future') if variant=='gap' else ('now','future')),
        jwbefore=lambda anchor,a,b:a in order and b in order and order.index(a)<order.index(b),jwcontrols=controls)
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:model[n] for n in names}


def tier_checks(texts):
    docs=[tier_setup(t) for t in texts];cases=[]
    for bits in product((False,True),repeat=6):
        rows=[values(d,tier_model(d,bits),mutual.PEOPLE,mutual.SCENES) for d in docs]
        want=bits[0] and bits[1] and (bits[2] or bits[4]) and (bits[3] or bits[5])
        if rows!=[[want,want]]*len(docs):raise ValueError('Tier coverage became all pairs or transitive direct control')
        cases.append(dict(edges=list(bits),results=rows[0]))
    contrasts={}
    for variant in ('empty_members','empty_subjects','self_upper','direct_only','outside_intermediary','future_loss','changing_delegate','empty_scope','no_anchor','gap'):
        rows=[values(d,tier_model(d,variant=variant),mutual.PEOPLE,mutual.SCENES) for d in docs]
        want=[True,True] if variant=='changing_delegate' else [True,False] if variant in ('future_loss','empty_scope','no_anchor','gap') else [False,False]
        if rows!=[want]*len(docs):raise ValueError('Tier contrast '+variant+': '+repr(rows))
        contrasts[variant]=want
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,scopes_fixed_at_anchor=True,delegates_may_change=True,transitivity_not_assumed=True)


def source_setup(text,variant='baseline'):
    d=mutual.abstract(candidate(text,mutual.EXTRA+'r jsa[d d] c.r jsb[a] c.r jsc[a a d] c.'+PURPOSE_EXTRA+TIER_EXTRA),{'rhq'})
    refs=[description(d,TIER_REFS[n]) for n,_ in TIER_SOURCE]
    goal=apply_description(d,quoted('function_ref','hzcm'),refs)
    if variant=='controller':refs[0]=description(d,'k jc[]') # Same value, different referring expression.
    elif variant=='members':refs[1]=description(d,'p jwsubjects')
    target=apply_description(d,quoted('function_ref','hzcm'),refs)
    arguments={n:description(d,e)['body'] for n,e in (mutual.REFS|dict(proponents='p jwproponents',candidates='p jsa',authorities='p jsb',confirms='p jsc')).items()}
    arguments['goal']=target
    call=lambda name,fields:dict(kind='call',symbol=name,arguments=[arguments[n] for n,_ in fields])
    evaluate=lambda content:dict(kind='evaluate',content=content,situation=arguments['context'])
    d['statements']=[dict(kind='ask',body=body) for body in (call('hzck',SOURCE),evaluate(call('hzcl',CONTENT)),evaluate(dict(kind='disquote',description=target)))]
    return parse(format_graph(d,'compact')),goal


def source_model(setup,aimed=True,achieved=True,absence=True):
    d,goal=setup;model=mutual.model_for(d,absence=absence);tier=tier_model(d,bits=(achieved,)*6)
    model.update({n:tier[n] for n in tier if n.startswith('jw') and n not in ('jwproponents','jwaims','jwtruth')})
    model['dc']=tier['jwcontrols'];model['ic']=lambda a,b,context:tier['jwbefore'](context,a,b)
    model['jwproponents']=lambda p,c:(p,c)==('alpha','now')
    model['hzu']=lambda p,a,g,c:aimed and (p,a,c)==('alpha','acta','first') and g.syntax==syntax(goal)
    return model


def source_checks(texts):
    setups=[source_setup(t) for t in texts];cases=[]
    for aimed,achieved,absence in product((False,True),repeat=3):
        rows=[values(s[0],source_model(s,aimed,achieved,absence),mutual.PEOPLE,mutual.SCENES) for s in setups]
        expected=[aimed,not aimed or absence,achieved]
        if rows!=[expected]*len(setups):raise ValueError('Source purpose asserted the oversight goal')
        cases.append(dict(aimed=aimed,achieved=achieved,no_normative_effect=absence,results=expected))
    for variant in ('controller','members'):
        for text in texts:
            s=source_setup(text,variant);d=deepcopy(s[0]);d['statements']=d['statements'][:2]
            if values(d,source_model(s),mutual.PEOPLE,mutual.SCENES)!=[False,True]:raise ValueError('Other goal accepted')
    for s in setups:
        d=deepcopy(s[0]);model=source_model(s);model['dc']=guarded(d)['dc'];d['statements']=d['statements'][:2]
        if values(d,model,mutual.PEOPLE,mutual.SCENES)!=[True,True]:raise ValueError('Unknown achievement blocked attributed purpose')
        for notation in ('full','compact'):
            form=format_graph(s[0],notation)
            if parse(form)!=s[0] or parse(decode(encode(form,'v2')))!=s[0]:raise ValueError('Closed goal instance changed')
    return dict(cases=cases,goal_binding_contrasts=['controller','members'],standalone_agrees=True,
        unknown_achievement_not_inferred=True,closed_goal_roundtrips=True,global_normative_absence_is_explicit_oracle=True)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored purposive undertaking differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Purpose roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    segments=[]
    for phrase in ('um so','über jedes ihrer Glieder und vermittelst ihrer über das Volk'):
        if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=['rh7','ria','rib','hzck','hzcm']))
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_purposive_undertakings.py','scripts/check_purposive_undertakings.py','noema/finite_semantics.py','noema/extraction.py','noema/description_templates.py',
        'scripts/check_mutual_undertakings.py','scripts/check_assessed_payments.py','scripts/check_public_assessment.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_purposive_undertaking_and_tiered_oversight',documents=documents,sizes=sizes,
        purposes=purpose_checks([texts[0],texts[2]]),tiers=tier_checks([texts[0],texts[2]]),source=source_checks(texts[1:]),
        alignment=dict(segments=segments,semantic_completion=False),new_definitions=7,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Purposive undertaking report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Purpose witnesses, tier coverage, persistence and unachieved goals checked')


if __name__=='__main__':main()
