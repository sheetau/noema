"""Check shared terms, distinct witnesses and independently assessed effects."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json

from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_policy_norms import seq
from scripts.check_rod_setup import guarded
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_limits import call as k
from scripts.compose_mutual_undertakings import ROOT,PARENT,BUILDERS,DESCRIPTION,DECLARES,ASSIGNED,ACT,PAST,FORM,SOURCE,CONTENT

REPORT=ROOT/'reports/mutual-undertakings-v1.json'
PEOPLE=('alpha','beta','acta','actb','pact','other')
SCENES=('first','second','now','future','elsewhere')
EXTRA=('r juaa[] a.r juab[] a.r jc[] a.r jd[] d.r je[] d.r jf[] j[a].'
    'r jg[a d] c.r jh[a] j[a].r ji[a] c.r jj[d] c.r jk[d d] c.'
    'r jl[a '+DESCRIPTION+' d] c.r jm[a d] c.r jn[a a d] c.'
    'r jo[a a a '+DESCRIPTION+' j[a] d] c.r jp[j[a] d] c.'
    'd jq[bindings j[a]] e[b scene[k jp[v bindings v scene]]].'
    'd jr[bindings j[a]] e[b scene[k jp[v bindings v scene]]].')
REFS=dict(person='k juaa[]',act='k juab[]',agreement='k jc[]',terms='r[p jq]',bindings='k jf[]',scene='k jd[]',context='k je[]',
    parties='p jg',arguments='p jh',eligible='p ji',history='p jj',before='p jk',assigned='p jl',occurs='p jm',performs='p jn',declares='p jo')
ARGS=lambda fields:[REFS[n] for n,_ in fields]


def setup(text,source=False):
    if source:
        extra=EXTRA+'r jsa[d d] c.r jsb[a] c.r jsc[a a d] c.'
        refs=REFS|dict(candidates='p jsa',authorities='p jsb',confirms='p jsc')
        query='q['+k('hzcg',*(refs[n] for n,_ in SOURCE))+'].q['+k('hzch',*(refs[n] for n,_ in SOURCE))+'].'
        query+='q[t['+k('hzci',*(refs[n] for n,_ in CONTENT))+'][k je[]]].'
    else:
        extra=EXTRA
        query=''.join('q['+k(name,*ARGS(fields))+'].' for name,fields in (('rhx',ACT),('rhy',PAST),('rhz',FORM)))
    return abstract(candidate(text,extra+query),{'rhq'})


def model_for(doc,first=True,second=True,assigned=True,absence=True,variant='baseline',components=(True,True,True)):
    model=guarded(doc)
    def allocation(person):
        result=('alpha','beta') if person=='alpha' else ('beta','alpha') if person=='beta' else (person,)
        if variant=='wrong_owner' and person in ('alpha','beta'):result=tuple(reversed(result))
        if variant=='extra_arguments':result+=('pact',)
        return result
    timea='first';timeb='future' if variant=='future_second' else 'now' if variant=='current_second' else 'elsewhere' if variant=='foreign_second' else 'second'
    def records():
        result=[('alpha','acta',timea,first),('beta','actb',timeb,second)]
        if variant=='alternative_witness':result.append(('alpha','other','second',first))
        return result
    def occurs(act,scene):
        return any(on and a==act and t==scene and (p!='alpha' or components[0]) for p,a,t,on in records())
    def performs(person,act,scene):
        return any(on and (p,a,t)==(person,act,scene) and (p!='alpha' or components[1]) for p,a,t,on in records())
    def declares(person,act,agreement,terms,bindings,scene):
        for p,a,t,on in records():
            if p=='alpha' and a=='acta' and variant=='alternative_witness':continue
            if p=='alpha' and variant=='split_act':a='actb'
            if p=='alpha' and variant=='split_time':t='second'
            target='other' if p=='beta' and variant=='other_agreement' else 'pact'
            desc='jr' if p=='beta' and variant=='alias_terms' else 'jq'
            expected=allocation(p)
            if p=='beta' and variant=='different_arguments':expected=(p,'other')
            if on and (p!='alpha' or components[2]) and (person,act,agreement,scene)==(p,a,target,t) and symbol(terms)==desc and bindings.items==expected:return True
        return False
    def parties(person,context):
        selected=() if variant=='empty_parties' else ('alpha',) if variant=='one_party' else ('alpha','beta','other') if variant=='uncommitted_party' else ('alpha','beta')
        return context=='now' and person in selected
    def history(scene):return scene in (('first','second','future') if variant=='missing_anchor' else ('first','now','future') if variant=='missing_second' else ('first','second','now','future'))
    def before(a,b):
        order=('first','second','now','future')
        if variant=='cyclic' and (a,b)==('now','first'):return True
        return a in order and b in order and order.index(a)<order.index(b)
    model.update(juaa=lambda:'alpha',juab=lambda:'acta',jc=lambda:'pact',jd=lambda:'first',je=lambda:'now',jf=lambda:seq(allocation('alpha')),
        jg=parties,jh=lambda p:seq(allocation(p)),ji=lambda p:p in ('alpha','beta','other') and not(variant=='ineligible' and p=='beta'),jj=history,jk=before,
        jl=lambda pact,terms,context:assigned and (pact,context)==('pact','now') and symbol(terms)==('jr' if variant=='revised_assignment' else 'jq'),
        jm=occurs,jn=performs,jo=declares,
        rhq=lambda pact,context,required,allowed:absence and pact=='pact' and context in SCENES)
    model.update(aa=model['ji'],dg=occurs,f3=performs,ic=lambda a,b,context:context=='now' and before(a,b),
        jsa=lambda anchor,scene:anchor=='now' and scene in ('first','future'),jsb=lambda a:a in ('alpha','beta'),
        jsc=lambda authority,pact,scene:authority in ('alpha','beta') and pact=='pact')
    used={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return {n:model[n] for n in used}


def generic_checks(texts):
    docs=[setup(text) for text in texts];cases=[]
    def run(**options):
        rows=[values(doc,model_for(doc,**options),PEOPLE,SCENES) for doc in docs]
        if any(row!=rows[0] for row in rows):raise ValueError('Extracted undertaking differs')
        return rows[0]
    for first,second,assigned in product((False,True),repeat=3):
        row=run(first=first,second=second,assigned=assigned)
        if row!=[first,first,first and second and assigned]:raise ValueError('Mutual undertaking combined different facts')
        cases.append(dict(first=first,second=second,assigned=assigned,results=row))
    components=[]
    # The action clause is evaluated independently of the global party search.
    for bits in product((False,True),repeat=3):
        rows=[]
        for base in docs:
            doc=deepcopy(base);doc['statements']=doc['statements'][:1]
            rows.append(values(doc,model_for(doc,components=bits),PEOPLE,SCENES))
        if rows!=[[all(bits)]]*len(docs):raise ValueError('Occurrence, actor and undertaking were conflated')
        components.append(dict(bits=list(bits),result=all(bits)))
    contrasts={}
    for variant in ('empty_parties','one_party','uncommitted_party','ineligible','future_second','current_second','foreign_second',
        'missing_anchor','missing_second','cyclic','revised_assignment','alias_terms','other_agreement','different_arguments','wrong_owner',
        'split_act','split_time','alternative_witness','extra_arguments'):
        row=run(variant=variant)
        if variant in ('current_second','extra_arguments'):want=[True,True,True]
        elif variant=='alternative_witness':want=[False,False,True]
        elif variant in ('wrong_owner','split_act','split_time'):want=[False,False,False]
        elif variant in ('missing_anchor','cyclic'):want=[True,False,False]
        else:want=[True,True,False]
        if row!=want:raise ValueError('Undertaking contrast '+variant+': '+repr(row))
        contrasts[variant]=row
    for doc in docs:
        for name in ('jg','jh','ji','jj','jk','jl','jm','jn','jo'):
            model=model_for(doc);model[name]=guarded(doc)[name]
            try:values(doc,model,PEOPLE,SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc):raise
            else:raise ValueError('Unknown undertaking record was filled in')
    return dict(cases=cases,action_components=components,contrasts=contrasts,standalone_agrees=True,
        unknown_records_refused=True,terms_not_executed=True,parties_fixed_at_anchor=True)


def source_checks(texts):
    docs=[setup(text,True) for text in texts];rows=[]
    for formed,absence in product((False,True),repeat=2):
        results=[values(doc,model_for(doc,second=formed,absence=absence),PEOPLE,SCENES) for doc in docs]
        expected=[formed,formed and absence,not formed or absence]
        if results!=[expected]*len(docs):raise ValueError('Formation became validity or actual occurrence of a hypothetical contract')
        rows.append(dict(formed=formed,no_normative_effect=absence,results=expected))
    return dict(cases=rows,standalone_agrees=True,global_normative_absence_is_explicit_oracle=True,
        formation_does_not_imply_normative_effect_or_truth=True)


def structural_checks(doc):
    ds={d['name']:d for d in doc['declarations']}
    def flatten(n):return flatten(n['arguments'][0])+flatten(n['arguments'][1]) if n.get('kind')=='and' else [n]
    group=ds['rhz'];refs={n:dict(kind='variable',name=p['name']) for (n,_),p in zip(FORM,group['parameters'],strict=True)}
    every=flatten(group['body'])[-1]
    if every['kind']!='forall':raise ValueError('All selected parties must undertake')
    person=dict(kind='variable',name=every['variable']);implication=every['body']
    expected=dict(kind='apply',function=refs['parties'],arguments=[person,refs['context']])
    if implication['kind']!='implies' or implication['arguments'][0]!=expected:raise ValueError('Parties were not fixed at the anchor')
    witness=implication['arguments'][1]['arguments'][1]
    for _ in range(2):
        if witness['kind']!='exists':raise ValueError('Each party needs its own action/time witnesses')
        witness=witness['body']
    if witness.get('symbol')!='rhy':raise ValueError('History of undertaking omitted')
    if witness['arguments'][0]!=person or witness['arguments'][2]!=refs['agreement'] or witness['arguments'][3]!=refs['terms']:
        raise ValueError('Shared party, agreement or terms changed')
    expected_args=dict(kind='apply',function=refs['arguments'],arguments=[person])
    if witness['arguments'][4]!=expected_args:raise ValueError('Personal binding allocation changed')
    wrapper=ds['hzcg'];refs={n:dict(kind='variable',name=p['name']) for (n,_),p in zip(SOURCE,wrapper['parameters'],strict=True)}
    body=wrapper['body']
    if body.get('symbol')!='rhz':raise ValueError('Source formation bypassed mutual undertaking')
    before=body['arguments'][7]
    if before['kind']!='lambda' or len(before['parameters'])!=2:raise ValueError('Missing contextual time order')
    expected_before=dict(kind='lambda',parameters=deepcopy(before['parameters']),body=dict(kind='call',symbol='ic',arguments=[
        *[dict(kind='variable',name=p['name']) for p in before['parameters']],refs['context']]))
    fixed=dict(eligible=dict(kind='function_ref',symbol='aa'),before=expected_before,
        occurs=dict(kind='function_ref',symbol='dg'),performs=dict(kind='function_ref',symbol='f3'))
    if body!=dict(kind='call',symbol='rhz',arguments=[fixed.get(n,refs.get(n)) for n,_ in FORM]):raise ValueError('Source formation lost its action or actor bindings')
    var=lambda name:dict(kind='variable',name=name)
    call=lambda name,items:dict(kind='call',symbol=name,arguments=items)
    for name,fields,left,right in (('rh2',FORM+[('required',''),('allowed','')],'rhz','rhq'),('hzch',SOURCE,'hzcg','hzce')):
        definition=ds[name];local={n:var(p['name']) for (n,_),p in zip(fields,definition['parameters'],strict=True)}
        right_args=[local['agreement'],local['context']]
        if name=='rh2':right_args += [local['required'],local['allowed']]
        body=definition['body']
        if body!=dict(kind='and',arguments=[call(left,[local[n] for n,_ in (FORM if name=='rh2' else SOURCE)]),call(right,right_args)]):
            raise ValueError('Formation and normative effects changed agreement or context')
    definition=ds['hzci'];content=definition['body']
    if content['kind']!='content' or content['body']['kind']!='implies':raise ValueError('Hypothetical formation was asserted as actual')
    local={n:var(p['name']) for (n,_),p in zip(CONTENT,definition['parameters'],strict=True)}
    local['context']=var(content['variable'])
    consequence=dict(kind='evaluate',content=call('hzcf',[local[n] for n in ('agreement','candidates','authorities','confirms')]),situation=local['context'])
    expected=dict(kind='implies',arguments=[call('hzcg',[local[n] for n,_ in SOURCE]),consequence])
    if content['body']!=expected:raise ValueError('Conditional formation changed the agreement, anchor or judgment')

    return dict(all_parties_at_same_anchor=True,shared_terms_with_personal_arguments=True,
        independent_action_time_witnesses=True,existing_action_relations_reused=True,formation_is_conditional=True)


def build_report():
    texts=[];documents={};sizes={}
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored mutual undertakings differ')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Undertaking roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=dict(characters=len(text),statements=len(doc['statements']))
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:raise ValueError('Parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0013')
    segments=[]
    for phrase in ('unter einander','zu verpflichten'):
        if unit['text'].count(phrase)!=1:raise ValueError('Source phrase is not unique')
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='explicit_interpretive_annotation',range=[start,start+len(phrase)],text=phrase,definitions=['rhz','hzcg','hzch','hzci']))
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_mutual_undertakings.py','scripts/check_mutual_undertakings.py','noema/finite_semantics.py','noema/extraction.py',
        'scripts/check_conditional_release.py','scripts/check_described_appraisals.py','scripts/check_described_explanations.py',
        'scripts/check_policy_norms.py','scripts/check_rod_setup.py','scripts/check_coordinate_correspondence.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_mutual_undertakings_and_terms',documents=documents,sizes=sizes,
        generic=generic_checks([texts[0],texts[2]]),source=source_checks(texts[1:]),structure=structural_checks(doc),
        alignment=dict(segments=segments,semantic_completion=False),new_definitions=7,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');options=parser.parse_args();report=build_report()
    if options.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Mutual undertakings report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Shared terms, fixed parties, action/time witnesses and independent normative effects checked')


if __name__=='__main__':main()
