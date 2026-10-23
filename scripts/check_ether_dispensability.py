"""Check two scoped negations, velocity records and a noncompleted forecast."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_two_postulates import relation
from scripts.check_material_relative_frame import arithmetic,RS
from scripts.compose_ether_dispensability import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/ether-dispensability-v1.md';SOURCE='data/einstein-principles-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/ether-dispensability-reading-v1.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/relativity-conjecture-reading-v1.json','data/two-postulates-reading-v1.json','data/sufficient-postulates-reading-v1.json')
DOMAIN=('a','b');POINTS=DOMAIN
def forbidden(*args):raise ValueError('Unknown ether input')

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    names=set() if mode=='full' else {'ba'}
    if name!='eigm' and mode=='native':names.add('eigm')
    abstract(doc,names)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jed'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jedpoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jedpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,model,point='a',domain=DOMAIN):
    m=dict(model,jedpoint=lambda:point)
    return evaluate_document(doc,individuals=domain,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,values,model,point='a',mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    return evaluate(doc,model|{n:(lambda x=x:x) for n,x in zip(slots,values)},point,domain)
def base():return dict(rd=lambda:'b',eirf=lambda:'a',eisbk=lambda:'a',eisby=lambda:'b',eiscu=lambda:'a',eisdc=lambda:'b',ri=lambda:'a')

def model():
    rows={'eiscx':{('b','a','a')},'eiscw':set(),'eiscy':{('a','b','a','a')},
        'eiscz':{('b','a')},'eisc2':{('a','b','a'),('b','b','a')},'eisc3':{('a','b','eibf','eibs','eico','a')},
        'eigm':{('b','a')},'eisc6':set(),'eisc7':{('b','a','a')},
        'eiscv':{('a','a','eigj','a')},'eisdb':{('a','eigr','a','a')},'eisda':{('a','eigq','eigr','a')}}
    return base()|{n:relation(rs) for n,rs in rows.items()},rows

def vectors(coords=(0,0,0)):
    cuts,m=arithmetic();axes=('a','b','c')
    f=FunctionValue(('individual',),RS,lambda axis:cuts.make(Q(coords[axes.index(axis)])))
    m.update(yn=lambda:'a',yo=lambda:'b',yp=lambda:'c',eisc4=relation({('b','a')}),eisc5=lambda vector,point:f)
    return cuts,m

@lru_cache(None)
def vector_checks():
    count=0
    for coords in ((0,0,0),(1,-2,3),(0,0,-5)):
        cuts,m=vectors(coords);assert run('eigm',['b','a'],m,domain=('a','b','c'));count+=1
        assert not run('eigm',['b','a'],m|{'eisc4':lambda *xs:False},domain=('a','b','c'));count+=1
        assert not run('eigm',['b','a'],m|{'yp':lambda:'a'},domain=('a','b','c'));count+=1
    for slot in (0,1):
        cuts,m=vectors();values=['b','a'];values[slot]='a' if slot==0 else 'b'
        assert not run('eigm',values,m,domain=('a','b','c'));count+=1
    cuts,m=vectors()
    for name in ('eisc4','eisc5'):
        try:run('eigm',['b','a'],m|{name:forbidden},domain=('a','b','c'))
        except ValueError as e:assert 'Unknown ether' in str(e)
        else:raise AssertionError('Unknown vector input accepted')
    try:run('eigm',['b','a'],m,mode='full',domain=('a','b','c'))
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full real cut validity finitely sampled')
    return dict(cases=count,zero_vector_included=True,native_three_component_validity=True,unknown_inputs_rejected=2,full_real_domain_refused=True)

@lru_cache(None)
def negation_checks():
    count=0
    for bits in product((False,True),repeat=3):
        m,_=model();rows={'eiscx':{('b','a','a')},'eiscw':{('a','b','a')},'eiscy':{('a','b','a','a')}}
        for (n,rs),on in zip(rows.items(),bits):m[n]=relation(rs if on else set())
        assert run('eigo',['a','a'],m)==(not all(bits));count+=1
    for name,rs in rows.items():
        row=next(iter(rs));m,_=model();m.update({n:relation(r) for n,r in rows.items()})
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert run('eigo',['a','a'],m|{name:relation({bad})});count+=1
    # A property assigned to a different space does not qualify the introduced space.
    assert run('eigo',['a','a'],m|{'eiscy':relation({('a','a','a','a')})});count+=1
    keys=('eiscz','eisc2','eisc3','eigm','eisc6')
    for bits in product((False,True),repeat=5):
        m,rs=model();rs['eisc6']={('a','a','b','a')}
        for n,on in zip(keys,bits):m[n]=relation(rs[n] if on else set())
        assert run('eigp',['a','a'],m)==(not all(bits));count+=1
    # Either spatial point, not only the process record's location, is covered.
    for point in DOMAIN:
        m,_=model();m['eisc6']=relation({('a',point,'b','a')});assert not run('eigp',['a','a'],m);count+=1
    m,rs=model();rs['eisc6']={('a','a','b','a')};rs['eisc2']={('a','b','a')};m.update({n:relation(r) for n,r in rs.items()})
    for name in keys:
        row=next(iter(rs[name]))
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert run('eigp',['a','a'],m|{name:relation({bad})});count+=1
    for name in ('eiscx','eiscw','eiscy','eiscz','eisc2','eisc3','eigm','eisc6'):
        good,_=model()
        try:run('eigq',['a','a'],good|{name:forbidden})
        except ValueError as e:assert 'Unknown ether' in str(e)
        else:raise AssertionError('Unknown relation treated as absence: '+name)
    # Native vector validity, electromagnetic schema and all scoped negations compose together.
    m,_=model();_,vm=vectors();m.update(vm)
    assert run('eigq',['a','a'],m,mode='vector',domain=('a','b','c'));count+=1
    m['eisc6']=relation({('a','a','b','a')})
    assert not run('eigq',['a','a'],m,mode='vector',domain=('a','b','c'));count+=1
    return dict(cases=count,both_negations_and_shared_bindings=True,spatial_region_not_only_active_point=True,zero_velocity_assignment_rejected=True,native_local_integration=True,unknown_inputs_rejected=8)

@lru_cache(None)
def dispensability_checks():
    count=0
    for alternatives,introduced in product(product((False,True),repeat=2),product((False,True),repeat=2)):
        allowed={a for a,on in zip(DOMAIN,alternatives) if on};uses={a for a,on in zip(DOMAIN,introduced) if on}
        m=base()|dict(eisc7=relation({(a,'a','a') for a in allowed}),eiscw=relation({(a,'b','a') for a in uses}))
        assert run('eigr',['a','a'],m)==bool(allowed-uses);count+=1
    for name,row in (('eisc7',('b','a','a')),('eiscw',('b','b','a'))):
        for slot in range(len(row)):
            m,_=model();m['eiscw']=relation({('b','b','a')});bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
            assert run('eigr',['a','a'],m|{name:relation({bad})})==(name=='eiscw');count+=1
        m,_=model()
        try:run('eigr',['a','a'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown ether' in str(e)
        else:raise AssertionError('Unknown alternative or introduction accepted')
    return dict(cases=count,same_descriptive_capacity_without_introduction=True,no_empty_alternative_scope=True,not_a_nonexistence_claim=True,unknown_inputs_rejected=2)

@lru_cache(None)
def forecast_checks():
    count=0;m,rows=model();assert run('eigt',[],m);count+=1
    # The predicted result is not evaluated as a completed result at this point.
    assert run('eigt',[],m|{'eisc7':forbidden});count+=1
    assert not run('eigr',['a','a'],m|{'eisc7':lambda *xs:False})
    assert run('eigt',[],m|{'eisc7':lambda *xs:False});count+=2
    for name in ('eiscv','eisdb','eisda'):
        row=next(iter(rows[name]))
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eigt',[],m|{name:relation({bad})});count+=1
        try:run('eigt',[],m|{name:forbidden})
        except ValueError as e:assert 'Unknown ether' in str(e)
        else:raise AssertionError('Unknown forecast input accepted')
    for extra in ({'eiscw':relation({('a','b','a')})},{'eisc6':relation({('a','a','b','a')})}):
        assert not run('eigt',[],m|extra);count+=1
    # Existential view must also be the view of the forecast and limited explanation.
    for view,point in product(DOMAIN,repeat=2):
        n,_=model();n.update(eiscv=relation({(view,'a','eigj',point)}),eisdb=relation({(view,'eigr','a',point)}),eisda=relation({(view,'eigq','eigr',point)}))
        assert run('eigt',[],n,point=point);count+=1
        n['eisdb']=relation({('b' if view=='a' else 'a','eigr','a',point)})
        assert not run('eigt',[],n,point=point);count+=1
    return dict(cases=count,future_establishment_not_completed_proof=True,same_prospective_view_project_and_qualified_reason=True,grounds_not_omitted=True,unknown_inputs_rejected=3)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==217
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213],[214],[215])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eigu']['body']['force']=='assert'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0;expected={'eir3':{('b','b','a','eigu','a')},'ue':{('a','b','a')}}
    for path in (CORE,FULL):
        p=parse(read(path));p['statements']=p['statements'][-1:]
        for first,second in product((False,True),repeat=2):
            m=base()|{n:relation(rs if on else set()) for (n,rs),on in zip(expected.items(),(first,second))};assert evaluate(p,m)==(first and second);count+=1
        m=base()|{n:relation(rs) for n,rs in expected.items()}
        for name,rs in expected.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(p,m|{name:relation({bad})});count+=1
        assert not evaluate(p,base()|dict(eisdc=lambda:'a',eir3=lambda *xs:True,ue=lambda *xs:True));count+=1
    unit=json.loads(read(INVENTORY))['units'][3];reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256'])
    assert reading['source']==unit['text'][1082:1425] and reading['source_nonblank_characters']==303 and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=216,presentation_cases=count,prior_reviews_preserved=True,source_range=[1082,1425])

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_ether_dispensability import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(vectors=vector_checks(),negations=negation_checks(),dispensability=dispensability_checks(),forecast=forecast_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][3]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,READING,INVENTORY,*PRIORS,
        'reports/sufficient-postulates-v1.json','scripts/compose_ether_dispensability.py','scripts/check_ether_dispensability.py','scripts/review_ether_dispensability.py','tests/test_ether_dispensability.py',
        'scripts/compose_sufficient_postulates.py','scripts/compose_two_postulates.py','scripts/compose_electrodynamics_title.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py','scripts/check_two_postulates.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py'}
    return dict(status='ether_dispensability_sentence_checked_under_explicit_reading',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[1082,1425],source=unit['text'][1082:1425],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
