"""Check local hour-hand indication, shared events, quotation and note anchors."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM
from scripts.check_motion_time_description import PRIORS
from scripts.compose_train_clock_example import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/train-clock-example-v1.md';SOURCE='data/einstein-time-continuation-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/train-clock-example-reading-v1.json'
EARLIER_READINGS=('data/motion-time-description-reading-v1.json','data/temporal-judgments-reading-v1.json')
DOMAIN=('speaker','train','clock','hand','place','frame','unit','arrival','display','paper','prior','node','note','other');POINTS=('now','other')
BASE=['speaker','train','clock','hand','place','frame','unit','now']

def forbidden(*args):raise ValueError('Unknown train-clock-example input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,native_history=False):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|({'seg'} if native_history else {'seh'}))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jtccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']

def run(name,values,m,context='now',native_history=False):
    doc,slots=fixture(name,native_history);assert len(values)==len(slots)
    return evaluate(doc,m|{'jtccontext':lambda:context}|{n:(lambda x=x:x) for n,x in zip(slots,values)})

def references():
    names=('rd','eisff','eisfg','eisfh','eisfi','ra','eisfj','eisfk','eisfl','eirf','eise3','eisfm','eisfn')
    values=('speaker','train','clock','hand','place','frame','unit','arrival','display','paper','prior','node','note')
    return {n:(lambda x=x:x) for n,x in zip(names,values)}|{'ri':lambda:'now'}

def setup(arrival_time=7,display_time=7,handmark=7):
    cuts,m=arithmetic();r=cuts.read
    rows={'eise4':{('train','now')},'ca':{('clock',)},'ci':{('unit',)},'va':{('frame',)},'eisdf':{('clock','now')},
        'eise5':{('place','speaker','now')},'eise6':{('clock','speaker','now')},'eise7':{('hand','clock','now')},'eisfa':{('clock','hand','unit','now')},
        'cb':{(x,'place','frame') for x in ('clock','arrival','display')},'eisfb':{('arrival','train','place','frame','now')},
        'zbd':{('arrival',),('display',)},'eisb7':{('frame','clock','unit','now')}}
    readings={('clock','arrival','frame','unit',Q(arrival_time)),('clock','display','frame','unit',Q(display_time))}
    indications={('display','hand','clock',Q(handmark),'now')}
    # Every member of this finite countermodel has an explicitly supplied candidate;
    # no unknown real cut or unknown event is converted into a default value.
    candidates={p:Q(0) for p in DOMAIN};candidates.update(arrival=Q(arrival_time),display=Q(display_time))
    def stamp(event,frame,unit,context):
        if event not in candidates or frame not in DOMAIN or unit not in DOMAIN or context not in POINTS:raise ValueError('Unknown candidate timestamp')
        return cuts.make(candidates[event])
    m.update({n:relation(rs) for n,rs in rows.items()});m.update(references())
    m.update(ce=lambda c,e,f,u,x:(c,e,f,u,r(x)) in readings,eisfc=lambda e,h,c,x,s:(e,h,c,r(x),s) in indications,
        zbe=stamp,zbh=lambda f,c:'clock',seh=lambda e,f,u,c,*functions:(e,f,u,c) in {(e,'frame','unit','now') for e in ('arrival','display')},seg=lambda *xs:True)
    return cuts,m,rows,readings,indications

@lru_cache(None)
def referent_checks():
    _,m,rows,_,_=setup();count=0
    assert run('eii3',BASE,m);count+=1
    for name in ('eii4','eii5'):
        args=BASE+['arrival']+(['display'] if name=='eii5' else [])
        assert run(name,args,m);count+=1
        for slot in range(len(args)):
            bad=list(args);bad[slot]='other';assert not run(name,bad,m),(name,slot);count+=1
    for name in ('eise4','ca','ci','va','eisdf','eise5','eise6','eise7','eisfa'):
        row=next(iter(rows[name]))
        for slot in range(len(row)):
            bad=tuple('other' if i==slot else x for i,x in enumerate(row));assert not run('eii3',BASE,m|{name:relation({bad})});count+=1
    # Local location does not impose the complete-worldline stationarity of the clock.
    assert run('eii5',BASE+['arrival','display'],m|{'cc':forbidden});count+=1
    for name in ('eii6','eii7'):
        assert run(name,[],m);count+=1
        for symbol in ('rd','eisff','eisfg','eisfh','eisfi','ra','eisfj','eisfk')+ (('eisfl',) if name=='eii7' else ()):
            assert not run(name,[],m|{symbol:lambda:'other'}),(name,symbol);count+=1
    return dict(cases=count,same_speaker_train_clock_hand_place_units=True,same_arrival_across_both_quotations=True,no_complete_clock_stationarity_added=True)

@lru_cache(None)
def indication_and_simultaneity_checks():
    count=0
    for arrival_time,display_time,mark in product((7,8,-5),(7,8,-5),(7,8)):
        _,m,_,_,_=setup(arrival_time,display_time,mark)
        assert run('eii4',BASE+['arrival'],m)==(arrival_time==7);count+=1
        assert run('eii5',BASE+['arrival','display'],m)==(display_time==mark==7 and arrival_time==display_time);count+=1
    cuts,m,rows,readings,indications=setup();r=cuts.read
    for name,row in (('ce',('clock','display','frame','unit',Q(7))),('eisfc',('display','hand','clock',Q(7),'now'))):
        for slot in range(len(row)):
            bad=tuple((Q(8) if isinstance(x,Q) else 'other') if i==slot else x for i,x in enumerate(row))
            if name=='ce':callback=lambda c,e,f,u,x,bad=bad:(c,e,f,u,r(x)) in (readings-{row})|{bad}
            else:callback=lambda e,h,c,x,s,bad=bad:(e,h,c,r(x),s)==bad
            assert not run('eii5',BASE+['arrival','display'],m|{name:callback}),(name,slot);count+=1
    for name in ('eisfb','cb','zbd','eisb7'):
        for row in rows[name]:
            if name=='cb' and row[0]=='clock':continue
            assert not run('eii5',BASE+['arrival','display'],m|{name:relation(rows[name]-{row})});count+=1
    for event in ('arrival','display'):
        altered=m|{'seh':lambda e,f,u,c,*fs,event=event:e!=event}
        assert not run('eii5',BASE+['arrival','display'],altered);count+=1
    # Two conceptually different events are not replaced by the same event identifier.
    args=BASE+['arrival','arrival'];assert not run('eii5',args,m);count+=1
    for name in ('ce','eisfc','eisfa','eisfb','seh','zbe'):
        try:run('eii5',BASE+['arrival','display'],m|{name:forbidden})
        except ValueError as e:assert 'Unknown train-clock-example' in str(e)
        else:raise AssertionError('Unknown physical input accepted')
    try:run('eii5',BASE+['arrival','display'],m,native_history=True)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full timestamp uniqueness silently sampled')
    return dict(cases=count,seventh_hour_indication_and_clock_reading_bound=True,native_simultaneity_value_comparison=True,valid_unique_time_assignment_required=True,unknown_inputs_rejected=6,full_real_timestamp_domain_refused=True)

@lru_cache(None)
def conditional_paraphrase_checks():
    count=0;rows={'eisfd':{('speaker','eii6','paper','now')},'eisfe':{('speaker','eii6','eii7','paper','now')}}
    base=references();m=base|{n:relation(rs) for n,rs in rows.items()}
    for speech,paraphrase in product((False,True),repeat=2):
        assert run('eija',[],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),(speech,paraphrase))})==(not speech or paraphrase);count+=1
    row=next(iter(rows['eisfe']))
    for slot in range(len(row)):
        bad=tuple('other' if i==slot else x for i,x in enumerate(row));assert not run('eija',[],m|{'eisfe':relation({bad})});count+=1
    assert not run('eija',[],m|{'eisfe':relation({('speaker','eii7','eii6','paper','now')})});count+=1
    # Neither quotation is evaluated; absent physical facts do not become assertions.
    assert run('eija',[],m|{n:forbidden for n in ('ce','eise4','eisfb','eisfc','zbe')});count+=1
    for name in rows:
        try:run('eija',[],m|{name:forbidden})
        except ValueError as e:assert 'Unknown train-clock-example' in str(e)
        else:raise AssertionError('Unknown utterance interpretation accepted')
    return dict(cases=count,speech_hypothesis_not_actual_utterance=True,approximate_paraphrase_direction_preserved=True,both_physical_contents_quoted_not_executed=True)

@lru_cache(None)
def presentation_checks():
    count=0;rows={'eir3':{('node','speaker','paper','eijb','now')},'eir5':{('node','speaker','prior','eija','now')},'ue':{('prior','node','now')},'eisfo':{('node','note','paper',Q(1),'now')}}
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=len(rows)):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for name,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple((Q(2) if isinstance(x,Q) else 'other') if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
        for symbol in ('eise3','eisfn'):
            assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{symbol:lambda:'node'});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eijb']['body']['force']=='assert'
    return dict(cases=count,same_author_document_and_source_order=True,example_points_to_temporal_judgment_sentence=True,note_one_anchor_preserved=True,quoted_conditional_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==228
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220],[221,222],[223])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    for path,indices in zip(EARLIER_READINGS,([224,225],[226])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);inv=json.loads(read(INVENTORY));u=inv['units'][9]
    segment=source['segments'][1];assert segment['unit']==u['id'] and segment['range']==[482,666] and segment['text']==u['text'][482:666] and segment['unit_sha256']==u['text_sha256']
    assert source['note_anchor']==dict(unit=u['id'],range=[482,666],printed_marker='1)',target='einstein-1905:u0279')
    note=next(u for u in inv['units'] if u['id']=='einstein-1905:u0279');assert source['segments'][2]['text']==note['text']
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==151
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=227,prior_reviews_and_three_sentences_preserved=True,source_note_reference_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_train_clock_example import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('referents',referent_checks),('indication_and_simultaneity',indication_and_simultaneity_checks),('conditional_paraphrase',conditional_paraphrase_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][9]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*EARLIER_READINGS,*PRIORS,'scripts/compose_train_clock_example.py','scripts/check_train_clock_example.py','scripts/review_train_clock_example.py','tests/test_train_clock_example.py','scripts/check_motion_time_description.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='train_clock_conditional_example_and_note_anchor_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[482,666],source=u['text'][482:666],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['脚注u0279の内容','段落全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
