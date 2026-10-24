"""Check hypothesis/law separation, shared binders and quoted theory roles."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,FunctionValue,QuestionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_carrier_field_correspondence as prior
from scripts.check_problem_series_reduction import collapse
from scripts.check_clock_site_time import relation,perturb
from scripts.check_rod_methods import value
from scripts.compose_convective_foundation_reading import *

old=prior.old
forbidden=old.forbidden
DOC='docs/convective-foundation-reading-v1.md';SOURCE='data/einstein-convective-foundation-reading-obligations-v1.json'
HISTORY='data/historical-carrier-reading-v1.json'
DEPENDENCIES=('reports/carrier-field-correspondence-v1.json','reports/convective-charge-setting-v1.json','reports/complete-material-attachment-v1.json','reports/optical-problem-method-v1.json')
BOUNDS={'ekym':{'ejsn'},'ekyn':{'ekxg','ekye'},'ekyo':{'ekym','ekyc','ekyj','ejsj','ekyn','ekxk','ekxl'},'ekyp':{'semh'},'ekyq':{'ejsj','ekyp'},'ekyr':{'ekx3'},'ekys':{'ekyr'},'ekyt':{'ekwm'},'ekyu':{'eie6','ekyt'},'ekyv':{'ekyu'},'ekyw':{'ekyv','ekyo','ekyq'},'ekyx':{'ekys','ekyw'}}
CONSTANTS={'eisv3':'ions','eisv4':'electrons','eisv5':'lorentz','eisv6':'section'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'scope','reference','inquiry','theory','problem','wrong']))

@lru_cache(None)
def core():return parse(read(CORE))

def walk(x):
    if isinstance(x,dict):
        yield x
        for y in x.values():yield from walk(y)
    elif isinstance(x,list):
        for y in x:yield from walk(y)

def chain(node,target,count):
    for start in walk(node):
        item=start;binders=[]
        for i in range(count):
            if item.get('kind')!='exists':break
            binders.append(item);item=item['body']
        if len(binders)==count and item.get('kind')=='call' and item.get('symbol')==target:return start,binders,item
    raise AssertionError(('No witness chain',target))

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi','sjd'}|BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    if root in ('ekyo','ekyq') and mode=='sample':
        target,count,helper=('ekyn',len(PHYSICAL_WITNESSES),'jfyphysical') if root=='ekyo' else ('ekyp',2,'jfylaw')
        start,binders,call=chain(d['body'],target,count)
        width=len(LOCAL) if root=='ekyo' else len(SETTING)+1
        targetd=next(x for x in doc['declarations'] if x['name']==target)
        start.clear();start.update(kind='call',symbol=helper,arguments=call['arguments'][:width])
        doc['declarations'].append(dict(kind='primitive',name=helper,parameters=targetd['parameters'][:width],result='truth'))
    extras={}
    if mode=='sample':
        samples=[(old.PS,('jfypa','jfypb')),(old.sort(LABELS),('jfyparta','jfypartb','jfypartc','jfypartd'))]
        def sampled(node):
            if isinstance(node,list):return [sampled(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall'):
                names=next((ns for s,ns in samples if s==node['sort']),None)
                if names:
                    extras.update({n:node['sort'] for n in names})
                    terms=[sampled(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names]
                    result=terms[0]
                    for term in terms[1:]:result=dict(kind='and' if node['kind']=='forall' else 'or',arguments=[result,term])
                    return result
            return {k:sampled(x) for k,x in node.items()}
        d['body']=sampled(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jfyarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jfypoint',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jfypoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,values,model,mode='sample'):
    doc,slots=fixture(root,mode);assert len(slots)==len(values)
    m={n:lambda x=x:x for n,x in (old.CONSTANTS|CONSTANTS).items()}
    m|={'jfypoint':lambda:'case'};m|=model|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup():
    by,m,c,r,parts,points,key,mask=prior.setup()
    by|=dict(light=c(5),electricconversion=c(1),magneticconversion=c(Fraction(1,5)))
    m|={n:lambda p=p:p for n,p in zip(('jfypa','jfypb'),points)}|{n:lambda p=p:p for n,p in zip(('jfyparta','jfypartb','jfypartc','jfypartd'),parts)}
    m|={'ra':lambda:by['frame'],'ta':lambda:by['lengthunit'],'rb':lambda:by['timeunit'],'tc':lambda:by['light'],'sjd':lambda x:c(1/r(x))}
    return by,m,c,r,parts,points,key,mask

def contrasts(root,vs,m,rows,key):
    good=m|{n:old.rel(rs,key) for n,rs in rows.items()};cases=1;assert run(root,vs,good),root
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,good|{n:old.rel(rs-{row},key)}),(root,n);cases+=1
            for i in range(len(row)):
                bad=list(row);bad[i]='wrong'
                assert not run(root,vs,good|{n:old.rel((rs-{row})|{tuple(bad)},key)}),(root,n,i);cases+=1
        prior.prior.reject(lambda:run(root,vs,good|{n:forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def physical_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    rows={'ejsn':{key([by[n] for n,t in FIELD_SETTING])}}
    cases+=contrasts('ekym',[by[n] for n,t in GLOBAL],m,rows,key)
    good=m|{'ejsn':lambda *xs:True}
    for n,x in [('frame','other'),('lengthunit','other'),('timeunit','other'),('light',c(7)),('electricconversion',c(2)),('magneticconversion',c(1))]:
        changed=by|{n:x};assert not run('ekym',[changed[n] for n,t in GLOBAL],good);cases+=1
    loc=by|{'density':by['chargefield'](*(by['point'](a) for a in ('x','y','z','t'))),'normalized':by['densityfield'](*(by['point'](a) for a in ('x','y','z','t')))}
    rows={n:{key([loc[x] for x,t in fs])} for n,fs in [('ekxg',NORMAL),('ekye',TOTAL)]}
    cases+=contrasts('ekyn',[by[n] for n,t in PHYSICAL_LOCAL],m,rows,key)
    vel=old.fn(old.PS,lambda axis:by['velocityfield'](axis)(*(by['point'](a) for a in ('x','y','z','t'))))
    row=key([by['electricfield'],by['magneticfield'],by['region'],by['point'],by['light'],loc['normalized'],vel,by['electricjet'],by['magneticjet']])
    cases+=contrasts('ekyp',[by[n] for n,t in LAW_LOCAL],m,{'semh':{row}},key)
    return dict(cases=cases,source_units_and_both_conversions_fixed=True,same_local_density_charge_velocity_fields_and_jets=True)

@lru_cache(None)
def global_checks():
    by,m,c,r,parts,points,key,mask=setup();cases=0
    rows={n:{key([by[x] for x,t in fs])} for n,fs in [('ekym',GLOBAL),('ekyc',ATTACHED),('ekyj',TRANSFER),('ekxl',FLOW)]}
    rows|={'jfyphysical':set(),'ekxk':set()}
    for p in points:
        loc=by|dict(point=p,normalized=by['densityfield'](*(p(a) for a in ('x','y','z','t'))))
        rows['jfyphysical'].add(key([loc[n] for n,t in LOCAL]));rows['ekxk'].add(key([loc[n] for n,t in SUPPORT]))
    cases+=contrasts('ekyo',[by[n] for n,t in GLOBAL],m|{'ejsj':lambda *xs:True},rows,key)
    good=m|{n:old.rel(rs,key) for n,rs in rows.items()}|{'ejsj':lambda *xs:True}
    assert not run('ekyo',[by[n] for n,t in GLOBAL],good|{'ejsj':lambda *xs:False});cases+=1
    lawrows={key([*(by[n] for n,t in SETTING),p]) for p in points}
    for condition,law in ((True,False),(False,True),(True,True),(False,False)):
        assert run('ekyo',[by[n] for n,t in GLOBAL],good|{'jfyphysical':lambda *xs:condition,'semh':lambda *xs:law})==condition;cases+=1
        assert run('ekyq',[by[n] for n,t in GLOBAL],m|{'ejsj':lambda *xs:True,'jfylaw':lambda *xs:law,'ekyc':lambda *xs:condition})==law;cases+=1
    cases+=contrasts('ekyq',[by[n] for n,t in GLOBAL],m|{'ejsj':lambda *xs:True},{'jfylaw':lawrows},key)
    assert not run('ekyq',[by[n] for n,t in GLOBAL],m|{'ejsj':lambda *xs:False,'jfylaw':lambda *xs:True});cases+=1
    for root in ('ekyo','ekyq'):
        prior.prior.reject(lambda:run(root,[by[n] for n,t in GLOBAL],good,'native'));cases+=1
    return dict(cases=cases,interpretation_does_not_require_equation_truth=True,equations_not_replaced_by_attachment=True,both_points_and_nonempty_domain_required=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for root,target,fields in [('ekyo','ekyn',PHYSICAL_WITNESSES),('ekyq','ekyp',JETS)]:
        source=next(d for d in core()['declarations'] if d['name']==root)
        targetd=next(d for d in core()['declarations'] if d['name']==target)
        start,binders,call=chain(source['body'],target,len(fields));width=len(call['arguments'])-len(fields)
        assert len({x['name'] for x in call['arguments']})==len(call['arguments'])
        for pivot in range(len(fields)):
            params=[dict(name=x['name'],sort=p['sort']) for x,p in zip(call['arguments'][:width],targetd['parameters'][:width])]
            params += [dict(name=b['variable'],sort=b['sort']) for i,b in enumerate(binders) if i!=pivot]
            body={k:binders[pivot][k] for k in ('kind','variable','sort')}|dict(body=call)
            doc=collapse(dict(schema_version=core()['schema_version'],lexicon_version=core()['lexicon_version'],declarations=[dict(kind='primitive',name=target,parameters=[p['sort'] for p in targetd['parameters']],result='truth'),dict(kind='definition',name='jfyw',parameters=params,result='truth',body=body)],statements=[]))
            slots=['jfyslot'+number_word(i) for i in range(len(params))]
            doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=p['sort']) for n,p in zip(slots,doc['declarations'][1]['parameters'])]
            doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='jfyw',arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
            doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in params};env[binders[pivot]['variable']]='b'
            def evaluate(env,expected):
                row=tuple(expected[a['name']] for a in call['arguments'])
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,params)}|{target:lambda *xs:xs==row}
                return evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=10000)[0]['value']
            assert evaluate(env,env);cases+=1
            assert not evaluate(env,env|{binders[pivot]['variable']:'unavailable'});cases+=1
            for p in params:
                altered=env|{p['name']:'other' if p['sort']=='situation' else 'b'}
                assert evaluate(altered,altered);assert not evaluate(altered,env);cases+=2
    return dict(cases=cases,all_eight_physical_and_two_jet_slots_checked=True,fixed_arguments_and_one_shared_witness_tuple_preserved=True)

@lru_cache(None)
def naming_checks():
    base,m,c,r,parts,spaces,key,mask=old.setup();cases=0
    m|={n:lambda p=p:p for n,p in zip(('jfyparta','jfypartb','jfypartc','jfypartd'),parts)}
    for positive,negative,want in ((2,-1,True),(2,-2,True),(0,0,False),(-3,-2,True)):
        total=old.fn(old.sort(dict(ALL)['total']),lambda p,a=positive,b=negative:c((a if p('a') else 0)+(b if p('b') else 0)))
        loc=base|dict(total=total);assert run('ekyr',[loc[n] for n,t in ALL],m|{'ekx3':lambda *xs:True})==want;cases+=1
    assert not run('ekyr',[base[n] for n,t in ALL],m|{'ekx3':lambda *xs:False});cases+=1
    prior.prior.reject(lambda:run('ekyr',[base[n] for n,t in ALL],m|{'ekx3':forbidden}),True);cases+=1
    rows={'eisv2':{('ions','ekyr','scope','case'),('electrons','ekyr','scope','case')}}
    cases+=perturb(lambda model:run('ekys',['scope','case'],model),{n:relation(rs) for n,rs in rows.items()},rows)
    assert not run('ekys',['scope','case'],{'eisv2':lambda *xs:True,'eisv4':lambda:'ions'});cases+=1
    return dict(cases=cases,two_names_share_scoped_model_without_species_identity=True,nonzero_portion_not_net_charge_required=True)

@lru_cache(None)
def foundation_checks():
    cases=0
    question=lambda answer:QuestionValue(FunctionValue(('individual',),'truth',lambda x:x==answer))
    def optical(problem,query,topic,scope,reference):
        return (problem,value(topic),scope,reference)==('problem','ekwm','section','case') and query.function('a') and not query.function('b')
    goodquestion={'eisvm':lambda problem,reference:question('a') if (problem,reference)==('problem','case') else question('b'),'eisvk':optical}
    assert run('ekyt',['problem','case'],goodquestion);cases+=1
    for args in (['other','case'],['problem','other']):assert not run('ekyt',args,goodquestion);cases+=1
    assert not run('ekyt',['problem','case'],goodquestion|{'eisvm':lambda *xs:question('b')});cases+=1
    for name in ('eisvm','eisvk'):
        prior.prior.reject(lambda:run('ekyt',['problem','case'],goodquestion|{name:forbidden}),True);cases+=1
    rows={'eie6':{('inquiry','case')},'eisv7':{('inquiry','ekyt','case')}}
    cases+=perturb(lambda m:run('ekyu',['inquiry','case'],m),{n:relation(rs) for n,rs in rows.items()},rows)
    rows={'eiscm':{('theory','inquiry','case')},'ekyu':{('inquiry','case')}}
    cases+=perturb(lambda m:run('ekyv',['theory','case'],m),{n:relation(rs) for n,rs in rows.items()},rows)
    rows={'ekyv':{('theory','case')},'eiswa':{('theory','inquiry','ekyo','ekyq','case')},'eisdi':{('theory','inquiry','case')}}
    good={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda m:run('ekyw',['theory','case'],m),good,rows)
    assert not run('ekyw',['theory','case'],good|{'eiswa':relation({('theory','inquiry','ekyq','ekyo','case')})});cases+=1
    # Distinct witnesses for foundation and dependency cannot satisfy the same existential.
    assert not run('ekyw',['theory','case'],good|{'eisdi':relation({('theory','other','case')})});cases+=1
    rows={'ekys':{('section','case')},'ekyw':{('lorentz','case')}}
    cases+=perturb(lambda m:run('ekyx',[],m),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=cases,condition_and_law_quoted_in_correct_order=True,same_theory_inquiry_and_discourse_reference=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read('data/einstein-carrier-field-correspondence-obligations-v1.json'))
    return dict(version='einstein-convective-foundation-reading-obligations-v1',kind='dependency_scope_not_semantic_review',unit=previous['unit'],unit_sha256=previous['unit_sha256'],text=previous['text'],resolved_dependencies=list(MEANINGS),reading='二つの歴史的担体種を共通の古典的モデルで表す。方程式を含まない物理的解釈条件と、同じ全設定についての原系方程式を分け、同じLorentz理論の二主題と条件付きの基礎へ結ぶ。',unresolved=['u0227–u0232の出発点・where説明・式・著者提示・見出しの本文統合と通読判断'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (old.INVENTORY,old.FACSIMILE,DOC,HISTORY)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==408 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[407])==selection_binding(before,[407]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-2]==json.loads(read('data/carrier-field-correspondence-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    hypothesis={d['name'] for d in extract_document(core(),roots=['ekyo'],statement_indices=[]).document['declarations']}
    assert not hypothesis&{'semh','semf','ekxj','ekyf','ekyl','eiah','ekbw','ekbx','ekby','ekbz'}
    ds={d['name']:d for d in core()['declarations']}
    assert [p['sort'] for p in ds['ekyo']['parameters']]==[p['sort'] for p in ds['ekyq']['parameters']]
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=12,new_general_relations=3,new_reference_constants=4,all_408_statements_and_prior_meanings_preserved=True,equations_absent_from_entire_hypothesis_dependency_closure=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('physical',physical_checks),('global',global_checks),('witness',witness_checks),('naming',naming_checks),('foundation',foundation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_convective_foundation_reading.py','scripts/check_convective_foundation_reading.py','tests/test_convective_foundation_reading.py','scripts/check_carrier_field_correspondence.py','scripts/check_problem_series_reduction.py','scripts/check_clock_site_time.py'}
    return dict(status='conditional_foundation_and_historical_carrier_model_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
