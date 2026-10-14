"""Check unchanged adopted descriptions and unfulfilled shared undertakings."""
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
from scripts.compose_fixed_standards import ROOT,PARENT,BUILDERS,DESCRIPTION,VERSION,POINT,INTERVAL,POLICY,SOURCE
from scripts.compose_prescribed_teaching import CRITERION,MESSAGE

REPORT=ROOT/'reports/fixed-standards-v1.json'
OLD='l['+CRITERION+'][p jvka]'
OTHER='l['+CRITERION+'][p jvkb]'
EXTRA=('r jvorg[] a.r jvstd[] a.r jvnow[] d.r jvtruth[a '+MESSAGE+' d] c.'
    'd jvka[subject a message '+MESSAGE+'] e[b scene[k jvtruth[v subject v message v scene]]].'
    'd jvkb[subject a message '+MESSAGE+'] e[b scene[k jvtruth[v subject v message v scene]]].'
    'r jvselect[a a d '+DESCRIPTION+' '+DESCRIPTION+'] '+DESCRIPTION+'.'
    'd jvversions[organization a standard a scene d] '+DESCRIPTION+'[k jvselect[v organization v standard v scene r['+OLD+'] r['+OTHER+']]].'
    'r jvadopt[a a '+DESCRIPTION+' d] c.r jvhist[d d] c.r jvrange[d d] c.r jvbefore[d d d] c.'
    'd jvhistory[context d] h[d] c[i[scene d][k jvhist[v context v scene]]].'
    'd jvscope[context d] h[d] c[i[scene d][k jvrange[v context v scene]]].'
    'd jvorder[context d] h[d d] c[i[first d second d][k jvbefore[v context v first v second]]].')
REFS=dict(organization='k jvorg[]',standard='k jvstd[]',description='r['+OLD+']',scene='k jvnow[]',
    versions='p jvversions',adopted='p jvadopt',anchor='k jvnow[]',history='c[p jvhistory][k jvnow[]]',
    scope='c[p jvscope][k jvnow[]]',before='c[p jvorder][k jvnow[]]',histories='p jvhistory',scopes='p jvscope',orders='p jvorder')


def setup(text):
    query=''.join('q['+k(name,*(REFS[n] for n,_ in fields))+'].' for name,fields in (('rh3',POINT),('rh4',INTERVAL)))
    query+='q[t[c['+k('rh5',*(REFS[n] for n,_ in POLICY))+'][l[a][]]][k jvnow[]]].'
    return candidate(text,EXTRA+query)


def model_for(doc,bits=(True,True,True,True),variant='baseline',anchor='first'):
    model=guarded(doc);old=syntax(description(doc,OLD));order=('first','second','now','future')
    def selected(context):
        if variant=='empty' or context not in order:return ()
        if variant=='singleton':return (context,)
        result=tuple(x for x in order if order.index(x)>=order.index(context))
        if variant=='gap':return tuple(x for x in result if x!='second')
        if variant=='no_anchor':return tuple(x for x in result if x!=context)
        if variant=='outside':return result+('elsewhere',)
        if variant=='past':return ('first',)+result
        return result
    def versions(org,standard,scene,original,other):
        unchanged=bits[0] if scene==anchor else bits[1] if scene=='second' or anchor=='now' and scene=='future' else True
        if variant=='organization' and org=='other':unchanged=False
        if variant=='standard' and standard=='actb':unchanged=False
        return original if unchanged else other
    def adopted(org,standard,desc,scene):
        accepted=bits[2] if scene==anchor else bits[3] if scene=='second' or anchor=='now' and scene=='future' else True
        return accepted and (org,standard)==('other','actb') and desc.syntax==old
    def before(a,b):return (a in order and b in order and order.index(a)<order.index(b)) or variant=='cycle' and (a,b)==('future','first')
    model.update(jvorg=lambda:'other',jvstd=lambda:'actb',jvnow=lambda:anchor,jvselect=versions,jvadopt=adopted,
        jvhist=lambda context,scene:scene in order and not(variant=='missing_history' and scene==context),
        jvrange=lambda context,scene:scene in selected(context),jvbefore=lambda context,a,b:before(a,b),
        ic=lambda a,b,context:before(a,b))
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:model[n] for n in names}


def generic_checks(texts):
    docs=[setup(t) for t in texts];cases=[]
    for bits in product((False,True),repeat=4):
        rows=[values(d,model_for(d,bits),mutual.PEOPLE,mutual.SCENES) for d in docs]
        expected=[bits[0] and bits[2],all(bits),all(bits)]
        if rows!=[expected]*len(docs):raise ValueError('Adoption became version identity or persistence')
        cases.append(dict(bits=list(bits),results=expected))
    contrasts={}
    for variant in ('empty','singleton','gap','no_anchor','outside','past','cycle','missing_history','organization','standard'):
        anchor='now' if variant=='past' else 'first'
        rows=[values(d,model_for(d,variant=variant,anchor=anchor),mutual.PEOPLE,mutual.SCENES) for d in docs]
        expected=[False,False,False] if variant in ('organization','standard') else [True,variant=='singleton',variant=='singleton']
        if rows!=[expected]*len(docs):raise ValueError('Scope contrast '+variant+': '+repr(rows))
        contrasts[variant]=expected
    for d in docs:
        for name in ('jvselect','jvadopt','jvhist','jvrange','jvbefore'):
            model=model_for(d);model[name]=guarded(d)[name]
            try:values(d,model,mutual.PEOPLE,mutual.SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown standard interpretation replaced')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,unknown_records_refused=True,
        criterion_truth_not_executed=True,alias_with_identical_body_distinguished=True)


def source_setup(text,variant='baseline'):
    doc=mutual.setup(text,True)
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+EXTRA+'q[t[c[s[r[p jq]]][k jf[]]][k je[]]].')
    doc['statements']=statements+doc['statements']
    refs=[description(doc,REFS[n]) for n,_ in SOURCE]
    expected=apply_description(doc,quoted('function_ref','hzcj'),refs)
    if variant=='organization':refs[0]=refs[1]
    elif variant=='standard':refs[1]=refs[0]
    elif variant=='description':refs[2]=description(doc,'r['+OTHER+']')
    target=apply_description(doc,quoted('function_ref','hzcj'),refs)
    def replace(x):
        if isinstance(x,list):return [replace(y) for y in x]
        if not isinstance(x,dict):return x
        if x==quoted('function_ref','jq'):return deepcopy(target)
        return {k:replace(v) for k,v in x.items()}
    doc['statements']=replace(doc['statements'])
    return parse(format_graph(doc,'compact')),target,expected


def source_model(setup,formed=True,retained=True,absence=True):
    doc,target,expected=setup
    model=mutual.model_for(doc,second=formed,absence=absence)
    extra=model_for(doc,bits=(retained,retained,retained,retained),anchor='now')
    model.update({n:extra[n] for n in extra if n.startswith('jv') or n=='ic'})
    expected=syntax(expected)
    model['jl']=lambda agreement,terms,context:(agreement,terms.syntax,context)==('pact',expected,'now')
    def declares(person,act,agreement,terms,bindings,scene):
        record=('alpha','acta','first',('alpha','beta')) if person=='alpha' else ('beta','actb','second',('beta','alpha'))
        return (person,act,scene,bindings.items)==record and (person=='alpha' or formed) and agreement=='pact' and terms.syntax==expected
    model['jo']=declares
    return model


def source_checks(texts):
    setups=[source_setup(t) for t in texts];cases=[]
    for formed,retained,absence in product((False,True),repeat=3):
        rows=[values(s[0],source_model(s,formed,retained,absence),mutual.PEOPLE,mutual.SCENES) for s in setups]
        expected=[formed,formed and absence,not formed or absence,retained]
        if rows!=[expected]*len(setups):raise ValueError('Undertaking asserted its performance')
        cases.append(dict(formed=formed,retained=retained,no_normative_effect=absence,results=expected))
    contrasts={}
    for variant in ('organization','standard','description'):
        rows=[]
        for text in texts:
            s=source_setup(text,variant);d=deepcopy(s[0]);d['statements']=d['statements'][:3]
            rows.append(values(d,source_model(s),mutual.PEOPLE,mutual.SCENES))
        if rows!=[[False,False,True]]*len(texts):raise ValueError('Other standard became the same undertaking')
        contrasts[variant]=rows[0]
    for s in setups:
        d,target,_=s
        for notation in ('full','compact'):
            if parse(format_graph(d,notation))!=d:raise ValueError('Closed undertaking instance changed')
        model=source_model(s);model['jvselect']=guarded(d)['jvselect']
        only=deepcopy(d);only['statements']=only['statements'][:3]
        if values(only,model,mutual.PEOPLE,mutual.SCENES)!=[True,True,True]:raise ValueError('Undertaking executed its terms')
        try:values(d,model,mutual.PEOPLE,mutual.SCENES)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):raise
        else:raise ValueError('Unknown actual retention guessed')
    return dict(cases=cases,contrasts=contrasts,standalone_agrees=True,closed_terms_roundtrip=True,
        unknown_performance_does_not_block_undertaking=True,unknown_performance_evaluation_refused=True,
        full_normative_absence_is_explicit_oracle=True)


def structural_checks(doc):
    ds={d['name']:d for d in doc['declarations']}
    variable=lambda name:dict(kind='variable',name=name)
    apply=lambda fn,items:dict(kind='apply',function=fn,arguments=items)
    call=lambda name,items:dict(kind='call',symbol=name,arguments=items)
    declaration=ds['rh5'];refs={n:variable(p['name']) for (n,_),p in zip(POLICY,declaration['parameters'],strict=True)}
    body=declaration['body'];content=body['body'];context=variable(content['variable'])
    refs.update(anchor=context,history=apply(refs['histories'],[context]),scope=apply(refs['scopes'],[context]),before=apply(refs['orders'],[context]))
    if body['kind']!='lambda' or content['kind']!='content' or content['body']!=call('rh4',[refs[n] for n,_ in INTERVAL]):raise ValueError('Policy changed standard or interval anchor')
    d=ds['hzcj'];refs={n:variable(p['name']) for (n,_),p in zip(SOURCE,d['parameters'],strict=True)}
    order=d['body']['arguments'][-1];anchor=variable(order['parameters'][0]['name']);inner=order['body']
    expected_order=dict(kind='lambda',parameters=deepcopy(order['parameters']),body=dict(kind='lambda',parameters=deepcopy(inner['parameters']),body=call('ic',[
        *[variable(p['name']) for p in inner['parameters']],anchor])))
    refs['orders']=expected_order
    if d['body']!=call('rh5',[refs[n] for n,_ in POLICY]):raise ValueError('Source order changed its anchor')
    if ds['rh4']['body']['arguments'][0].get('symbol')!='tb':raise ValueError('Convex temporal scope omitted')
    return dict(shared_standard_and_description=True,interval_fixed_at_evaluation_anchor=True,
        source_time_order_at_same_anchor=True,bindings_independent_shared_outcome=True)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored fixed standards differ')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Fixed standard roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    phrase='ein gewisses unveränderliches Symbol'
    if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
    start=unit['text'].index(phrase)
    segment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=['rh3','rh4','rh5','hzcj'])
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_fixed_standards.py','scripts/check_fixed_standards.py','noema/finite_semantics.py','noema/extraction.py','noema/description_templates.py',
        'scripts/check_mutual_undertakings.py','scripts/check_assessed_payments.py','scripts/check_public_assessment.py',
        'scripts/compose_adopted_standards.py','scripts/compose_prescribed_teaching.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_fixed_adopted_standard_as_undertaking_terms',documents=documents,sizes=sizes,
        generic=generic_checks([texts[0],texts[2]]),source=source_checks(texts[1:]),structure=structural_checks(doc),
        alignment=dict(segments=[segment],semantic_completion=False),new_definitions=4,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Fixed standards report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Adopted versions, anchored intervals and independently unfulfilled undertakings checked')


if __name__=='__main__':main()
