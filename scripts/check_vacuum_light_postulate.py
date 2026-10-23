"""Check the light clause's physical bindings, local times and universal scopes."""
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
from scripts.check_material_relative_frame import arithmetic
from scripts.compose_vacuum_light_postulate import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build

DOC='docs/vacuum-light-postulate-v1.md';SOURCE='data/einstein-principles-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/relativity-conjecture-reading-v1.json')
DOMAIN=('s','t','ray','emitter','emission','start','end','clockstart','clockend','placestart','placeend','frame','reference','lengthunit','timeunit','speedunit','other')
CONTEXTS=('context','other')
NUM={'ba','bb','bc','bf','sah'}

def forbidden(*args):raise ValueError('Unknown vacuum-light input')

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    names=set(NUM)
    if mode!='full':names.add('qo')
    if mode=='frames':names|={'eifb','eifx'}
    if mode=='scope':names.add('eifw')
    if mode=='full':names=set()
    abstract(doc,names)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jvl'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvlpoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jvlpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,values,model,mode='native',context='context'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    m=dict(model,jvlpoint=lambda:context);m.update({n:(lambda x=x:x) for n,x in zip(slots,values)})
    return evaluate_document(doc,individuals=('s','t') if mode=='frames' else DOMAIN,situations=CONTEXTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup(path=6,start=1,end=3,selected=('s','t'),complete=True):
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read
    m['sah']=lambda a,b:c(r(a)*r(b))
    def normalized(xs):return tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={
        'eisb5':{('ray','frame','context')},
        'eisb6':{(s,'ray','emitter','emission','start','end','frame','lengthunit','timeunit','context') for s in ('s','t')},
        'eisca':{('ray','start','end','frame','context')},
        'eiscb':{(s,'ray','start','end','frame','lengthunit',Q(path),'context') for s in ('s','t')},
        'eisb7':{('frame','reference','timeunit','context')},
        'eiscc':{('frame','lengthunit','timeunit','speedunit','context')},
        'eisce':{('frame','lengthunit','timeunit','context')} if complete else set(),
        'eiscd':{(s,'frame','lengthunit','timeunit','context') for s in selected},
        'ca':{(x,) for x in ('clockstart','clockend','reference')},
        'cc':{(x,'frame') for x in ('clockstart','clockend','reference')},
        'ci':{('timeunit',)},
        'cb':{(x,p,'frame') for xs,p in ((('start','clockstart'),'placestart'),(('end','clockend'),'placeend')) for x in xs},
        'ce':{('clockstart','start','frame','timeunit',Q(start)),('clockend','end','frame','timeunit',Q(end))},
        'qo':{(clock,'reference','frame','timeunit','context') for clock in ('clockstart','clockend')},
    }
    for name,expected in rows.items():m[name]=lambda *xs,expected=expected:normalized(xs) in expected
    for name,value in dict(wf='ray',wg='emitter',wh='emission',wi='start',wj='end',wk='clockstart',wl='clockend',wm='placestart',wn='placeend').items():m[name]=lambda s,value=value:value
    for name,value in dict(wo=start,wp=end,wq=path).items():m[name]=lambda s,value=value:c(value)
    for name,value in dict(ta='lengthunit',rb='timeunit',tb='speedunit').items():m[name]=lambda value=value:value
    m['zbh']=lambda frame,context:'reference'
    return cuts,m,rows

@lru_cache(None)
def local_checks():
    cuts,m,rows=setup();values=['s','frame','reference',cuts.make(Q(3)),'context'];count=0
    assert run('eifw',values,m);count+=1
    # Same event, clock, place, units, context and real value must reach every slot.
    for name in ('eisb5','eisb6','eisca','eiscb','ca','cb','cc','ci','ce','qo'):
        for row in rows[name]:
            for slot in range(len(row)):
                expected=rows[name]-{row};changed=tuple(('other' if isinstance(x,str) else x+1) if i==slot else x for i,x in enumerate(row));expected=expected|{changed}
                def relation(*xs,expected=expected):return tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs) in expected
                # t is not used by this pointwise call.
                if name in ('eisb6','eiscb') and row[0]=='t':continue
                assert not run('eifw',values,m|{name:relation}),(name,slot);count+=1
        try:run('eifw',values,m|{name:forbidden})
        except ValueError as e:assert 'Unknown vacuum-light' in str(e)
        else:raise AssertionError('Unknown physical input accepted: '+name)
    for name in ('wf','wg','wh','wi','wj','wk','wl','wm','wn'):
        assert not run('eifw',values,m|{name:lambda segment:'other'});count+=1
    for name in ('wo','wp','wq'):
        assert not run('eifw',values,m|{name:lambda segment:cuts.make(Q(11))});count+=1
    for slot in (0,1,2,4):
        changed=list(values);changed[slot]='other';assert not run('eifw',changed,m);count+=1
    # Native saf/sae and sax share all metadata; qo and arithmetic remain explicit inputs.
    return dict(cases=count,unknown_inputs_rejected=10,same_ray_source_interval_and_frame=True,native_local_time_and_speed=True,synchrony_is_explicit_input=True)

@lru_cache(None)
def speed_checks():
    count=0
    for path,start,end,speed in ((6,1,3,3),(6,-7,-5,3),(6,1,3,4),(6,1,3,6),(6,1,3,Q(3,2)),(0,1,3,0),(6,3,3,3),(6,3,1,-3),(-6,1,3,-3),(Q(1,3),Q(-1,5),Q(2,15),1)):
        cuts,m,_=setup(path,start,end)
        expected=path>0 and end>start and speed>0 and path==speed*(end-start)
        assert run('eifw',['s','frame','reference',cuts.make(Q(speed)),'context'],m)==expected;count+=1
    cuts,m,_=setup()
    # Real-cut definition quantifies over all rationals, never a small numeric sample.
    try:run('sax',[cuts.make(Q(x)) for x in (6,1,3,3)],m,mode='full')
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full real arithmetic was finitely sampled')
    unknown=FunctionValue(('number',),'truth',lambda x:x<3)
    try:run('sax',[unknown]+[cuts.make(Q(x)) for x in (1,3,3)],m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut decoded by finite probes')
    return dict(cases=count,positive_distance_duration_speed=True,clock_origin_shift_preserved=True,no_emitter_velocity_or_roundtrip_factor=True,full_real_domain_refused=True,unknown_cut_refused=True)

@lru_cache(None)
def scope_checks():
    count=0
    for mask,bits,complete in product(product((False,True),repeat=2),product((False,True),repeat=2),(False,True)):
        selected={s for s,on in zip(('s','t'),mask) if on};valid={s for s,on in zip(('s','t'),bits) if on}
        cuts,m,_=setup(selected=selected,complete=complete)
        m['eifw']=lambda segment,frame,reference,value,context:segment in valid and (frame,reference,cuts.read(value),context)==('frame','reference',Q(3),'context')
        assert run('eifx',['frame',cuts.make(Q(3)),'context'],m,mode='scope')==(complete and bool(selected) and selected<=valid);count+=1
    cuts,m,rows=setup();values=['frame',cuts.make(Q(3)),'context']
    assert run('eifx',values,m);count+=1
    # One subinterval / source-state variation suffices to defeat the universal claim.
    bad=m|{'wq':lambda segment:cuts.make(Q(7 if segment=='t' else 6))}
    assert not run('eifx',values,bad);count+=1
    for name in ('eisb7','eiscc','eisce','eiscd'):
        assert not run('eifx',values,m|{name:lambda *xs:False});count+=1
        try:run('eifx',values,m|{name:forbidden})
        except ValueError as e:assert 'Unknown vacuum-light' in str(e)
        else:raise AssertionError('Unknown scope input accepted')
        for slot in range(len(next(iter(rows[name])))):
            base=m[name]
            def wrong(*xs,slot=slot,base=base):
                xs=list(xs);xs[slot]='other';return base(*xs)
            assert not run('eifx',values,m|{name:wrong});count+=1
    assert not run('eifx',values,m|{'zbh':lambda *xs:'other'});count+=1
    return dict(cases=count,native_sak_nonempty_universal_scope=True,complete_scope_required=True,all_subintervals_and_source_states_are_meaning_input=True,one_bad_selected_case_rejected=True,unknown_inputs_rejected=4)

@lru_cache(None)
def frame_checks():
    count=0
    for mask,bits,context in product(product((False,True),repeat=2),product((False,True),repeat=2),CONTEXTS):
        qualified={s for s,on in zip(('s','t'),mask) if on};valid={s for s,on in zip(('s','t'),bits) if on};cuts,m,_=setup()
        m.update(tc=lambda:cuts.make(Q(3)),eifb=lambda frame,point:frame in qualified and point==context,
            eifx=lambda frame,value,point:frame in valid and cuts.read(value)==3 and point==context)
        assert run('eify',[],m,mode='frames',context=context)==(bool(qualified) and qualified<=valid);count+=1
        m['eifx']=lambda frame,value,point:frame in valid and cuts.read(value)==4 and point==context
        assert not run('eify',[],m,mode='frames',context=context);count+=1
    return dict(cases=count,all_and_only_qualified_frames=True,nonempty_frame_scope=True,same_V_and_context=True,universal_frame_reading_explicit=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==214
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'saf','sae','sax','sak','qo','eifb'}<=names and not {'ra','sbd','saz'}&names and not doc['statements']
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=214,prior_reviews_preserved=True,no_new_author_assertion=True,second_sentence_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results=dict(local=local_checks(),speed=speed_checks(),scope=scope_checks(),frames=frame_checks(),structure=structure_checks())
    inv=json.loads(read(INVENTORY));unit=inv['units'][3];span=[unit['text'].index('daß sich das Licht'),889]
    math=next(m for m in inv['math'] if m['id']=='M0001')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,
        'scripts/compose_vacuum_light_postulate.py','scripts/check_vacuum_light_postulate.py','tests/test_vacuum_light_postulate.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py',
        'scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    alignment=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,source=unit['text'][span[0]:span[1]],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        dict(unit=unit['id'],unit_sha256=unit['text_sha256'],math_id='M0001',math_sha256=math['sha256'],definitions=['eify'],status='partial')]
    return dict(status='vacuum_light_content_composed_presentation_pending',document=FULL,**results,alignment=dict(segments=alignment),
        remaining=['同じ推測eifjを前提へ採用する意思','今後のPrinzip der Relativitätという命名','同じ二原理の見かけの不整合と実際の両立','第二文全体と段落全体の意味判断'],
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
