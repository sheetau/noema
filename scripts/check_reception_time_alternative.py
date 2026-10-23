"""Check reception/evidence/indication bindings and nonfactive adoption."""
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
from scripts.compose_reception_time_alternative import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/reception-time-alternative-v1.md';SOURCE='data/einstein-reception-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/reception-time-alternative-reading-v1.json'
PRIOR='data/einstein-clock-definition-paragraph-review-v1.json'
DOMAIN=('scheme','task','observer','clock','hand','origin','frame','unit','paper','event','signal','departure','reception','display','record','record2','author','prior','node','other')
POINTS=('now','possible','other')
BASE=['observer','clock','hand','origin','frame','unit','now']
ARRIVAL=['task']+BASE+['event','signal','departure','reception']
METHOD=['scheme','task','observer','clock','hand','origin','frame','unit','paper','now']

def forbidden(*args):raise ValueError('Unknown reception-time-alternative input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries={'record':{'eikc'},'method':{'eikd'},'modal':{'eike'}}.get(mode,set())
    abstract(doc,(set() if mode=='real' else NUM)|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrtcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrtcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,mode='native',context='now'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jrtcontext':lambda:context}|{n:(lambda x=x:x) for n,x in zip(slots,args)})

def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown reception-time-alternative' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

def setup():
    cuts,m=arithmetic();r=cuts.read
    rows={'eisgr':{('observer','now')},'ca':{('clock',)},'ci':{('unit',)},'va':{('frame',)},'eisdf':{('clock','now')},'eisgs':{('hand','clock','now')},'zbv':{('frame','origin','now')},
        'cb':{(x,'origin','frame') for x in ('observer','clock','reception','display')},'eisgf':{('clock','origin','frame','now')},'eisge':{('task','event','now')},'zbd':{(x,) for x in ('event','departure','reception','display')},
        'eisb5':{('signal','frame','now')},'eisgu':{('event','signal','departure','observer','frame','now')},'eisgv':{('signal','departure','reception','observer','frame','now')},'eisca':{('signal','departure','reception','frame','now')},'eisgm':{('reception','display','clock','frame','now')},
        'eisgy':{('record','task','observer','frame','now')},'eisgw':{('task','record','observer','frame','now')},'eisg3':{tuple(METHOD[:-1]+['eikd','now'])}}
    m|={n:relation(rs) for n,rs in rows.items()}
    reads={('clock','event','frame','unit',Q(3)),('clock','reception','frame','unit',Q(9)),('clock','display','frame','unit',Q(9))}
    indications={('display','hand','clock',Q(9),'now')}
    assignments={('observer','task','event','signal','reception','display','clock','frame','unit',Q(9),'now')}
    m|={'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in reads,'eisgt':lambda d,h,c,x,s:(d,h,c,r(x),s) in indications,'eisg2':lambda o,t,e,l,rc,d,c,f,u,x,s:(o,t,e,l,rc,d,c,f,u,r(x),s) in assignments}
    # The finite fixture explicitly supplies candidates even for nonselected rows.
    # These are candidates only; eisgy and the native body determine validity.
    fields={(rec,s):('event','signal','departure','reception','display') for rec in DOMAIN for s in POINTS}
    candidates={(rec,c,u,s):Q(9) for rec in DOMAIN for c in DOMAIN for u in DOMAIN for s in POINTS}
    def project(rec,slot,s):
        if (rec,s) not in fields or slot.denominator!=1 or not 1<=slot<=5:raise ValueError('Unknown reception-time-alternative field')
        return fields[rec,s][int(slot)-1]
    def reading(rec,c,u,s):
        if (rec,c,u,s) not in candidates:raise ValueError('Unknown reception-time-alternative reading')
        return cuts.make(candidates[rec,c,u,s])
    m|={'eisgx':project,'eisgz':reading}
    return cuts,m,rows,reads,indications,assignments,fields,candidates

@lru_cache(None)
def setup_and_arrival_checks():
    _,m,rows,*_=setup();count=0
    for name,args in (('eika',BASE),('eikb',ARRIVAL)):
        assert run(name,args,m);count+=1
        for i in range(len(args)):
            bad=args.copy();bad[i]='other';assert not run(name,bad,m);count+=1
    for name in ('eisgr','ca','ci','va','eisdf','eisgs','zbv','eisgf','eisge','eisb5','eisgu','eisgv','eisca'):
        for row in rows[name]:
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikb',ARRIVAL,m|{name:relation({bad})});count+=1
    for row in rows['cb']- {('display','origin','frame')}:
        assert not run('eikb',ARRIVAL,m|{'cb':relation(rows['cb']-{row})});count+=1
    assert run('eikb',ARRIVAL,m|{n:forbidden for n in ('eise6','eise7','cc','saf','qo','eihm')});count+=1
    reject_unknown('eikb',ARRIVAL,m,('eisgr','eisgs','zbv','eisge','eisb5','eisgu','eisgv','eisca'))
    return dict(cases=count,same_origin_observer_clock_and_signal=True,evidence_departure_and_reception_roles_distinct=True,vacuum_on_same_path_required=True,no_ownership_hour_hand_or_prior_remote_sync_added=True)

@lru_cache(None)
def assignment_checks():
    cuts,m,rows,reads,indications,assignments,*_=setup();r=cuts.read;args=ARRIVAL+['display',cuts.make(Q(9))];count=0
    assert run('eikc',args,m);count+=1
    # The source event's local reading is 3; receipt and indication are 9.
    assert run('eikc',args,m|{'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in reads-{('clock','event','frame','unit',Q(3))}});count+=1
    for reading,mark,receipt in product((Q(9),Q(3)),repeat=3):
        mm=m|{'eisgt':lambda d,h,c,x,s,mark=mark:(d,h,c,r(x),s)==('display','hand','clock',mark,'now'),'ce':lambda c,e,f,u,x,rc=receipt:(c,e,f,u,r(x)) in {('clock','display','frame','unit',Q(9)),('clock','reception','frame','unit',rc)}}
        assert run('eikc',ARRIVAL+['display',cuts.make(reading)],mm)==(reading==mark==receipt==Q(9));count+=1
    for i in range(len(args)-1):
        bad=args.copy();bad[i]='other';assert not run('eikc',bad,m);count+=1
    for symbol,row in (('eisgt',next(iter(indications))),('eisg2',next(iter(assignments)))):
        for i in range(len(row)):
            bad=tuple((Q(3) if isinstance(x,Q) else 'other') if j==i else x for j,x in enumerate(row))
            fn=(lambda d,h,c,x,s,bad=bad:(d,h,c,r(x),s)==bad) if symbol=='eisgt' else (lambda o,t,e,l,rc,d,c,f,u,x,s,bad=bad:(o,t,e,l,rc,d,c,f,u,r(x),s)==bad)
            assert not run('eikc',args,m|{symbol:fn});count+=1
    for name in ('eisgm',):
        row=next(iter(rows[name]))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikc',args,m|{name:relation({bad})});count+=1
    assert not run('eikc',args,m|{'ba':lambda *xs:False});count+=1
    reject_unknown('eikc',args,m,('eisgt','eisgm','eisg2','ce','ba'))
    try:run('eikc',args,m,mode='real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real validity silently sampled')
    return dict(cases=count,reception_and_corresponding_indication_match=True,assignment_to_signal_keeps_original_event=True,original_event_time_not_set_equal_to_reception=True,full_real_validity_not_sampled=True)

@lru_cache(None)
def record_checks():
    cuts,m,rows,*rest=setup();fields,candidates=rest[-2:];count=0;args=['task','record']+BASE
    assert run('eikd',args,m);count+=1
    for i in range(5):
        original=fields['record','now'];changed=list(original);changed[i]='other';fields['record','now']=tuple(changed)
        assert not run('eikd',args,m);count+=1;fields['record','now']=original
    for left in range(5):
        for right in range(left+1,5):
            original=fields['record','now'];changed=list(original);changed[left],changed[right]=changed[right],changed[left];fields['record','now']=tuple(changed)
            assert not run('eikd',args,m);count+=1;fields['record','now']=original
    candidates['record','clock','unit','now']=Q(3);assert not run('eikd',args,m);count+=1;candidates['record','clock','unit','now']=Q(9)
    for i in range(len(args)):
        bad=args.copy();bad[i]='other';assert not run('eikd',bad,m);count+=1
    for i in range(5):
        row=next(iter(rows['eisgy']));bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikd',args,m|{'eisgy':relation({bad})});count+=1
    for badslot in (Q(0),Q(6),Q(3,2)):
        try:m['eisgx']('record',badslot,'now')
        except ValueError:pass
        else:raise AssertionError('Invalid record field accepted')
    reject_unknown('eikd',args,m,('eisgy','eisgx','eisgz'))
    return dict(cases=count,all_five_roles_and_candidate_value_bound=True,role_swaps_and_wrong_context_rejected=True,no_default_value_for_unknown_or_missing_field=True)

@lru_cache(None)
def all_records_checks():
    _,m,rows,*_=setup();count=0
    for first,second,validfirst,validsecond in product((False,True),repeat=4):
        selected={('task',r,'observer','frame','now') for r,on in (('record',first),('record2',second)) if on}
        valid={tuple(['task',r]+BASE) for r,on in (('record',validfirst),('record2',validsecond)) if on}
        mm=m|{'eisgw':relation(selected),'eikd':relation(valid)}
        assert run('eike',METHOD,mm,'method')==((first or second) and (not first or validfirst) and (not second or validsecond));count+=1
    good=m|{'eikd':relation({tuple(['task','record']+BASE)})}
    assert run('eike',METHOD,good,'method');count+=1
    row=next(iter(rows['eisg3']))
    for i in range(len(row)):
        bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eike',METHOD,good|{'eisg3':relation({bad})},'method');count+=1
    for i in range(len(METHOD)):
        bad=METHOD.copy();bad[i]='other';assert not run('eike',bad,good,'method');count+=1
    # The native record checker is tested above; here distinguish every forwarded slot.
    row=tuple(['task','record']+BASE)
    for i in range(len(row)):
        bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eike',METHOD,m|{'eikd':relation({bad})},'method');count+=1
    reject_unknown('eike',METHOD,good,('eisgw','eisg3','eikd'),'method')
    return dict(cases=count,every_eligible_arrival_not_only_successes=True,nonempty_arrival_scope=True,same_rule_and_observer_for_all_records=True,record_body_checked_separately=True)

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eisg7','eishe','eisha','eishb','eishc','eishd','ra','eishf','eirf','rd','eishg','eisgq'),('scheme','task','observer','clock','hand','origin','frame','unit','paper','author','node','prior'))}|{'ri':lambda:'now'}

@lru_cache(None)
def possibility_checks():
    count=0;method=tuple(METHOD[:-1]+['possible'])
    rows={'eisg4':{('author','scheme','task','paper','now','possible')},'eisg5':{('author','scheme','task','paper','possible')},'eike':{method}}
    m=references()|{n:relation(r) for n,r in rows.items()}
    for adopt,procedure,contented in product((False,True),repeat=3):
        mm=m|{n:relation(rows[n] if on else set()) for n,on in (('eisg4',adopt),('eike',procedure),('eisg5',contented))}
        assert run('eikh',[],mm,'modal')==(adopt and procedure and contented);count+=1
    assert run('eikh',[],m,'modal') and not run('eikf',[],m,'modal',context='now');count+=2
    for name,rowset in rows.items():
        row=next(iter(rowset))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not run('eikh',[],m|{name:relation({bad})},'modal');count+=1
    for symbol in references():
        if symbol in ('eishg','eisgq','ri'):continue
        assert not run('eikh',[],m|{symbol:lambda:'other'},'modal');count+=1
    # Procedure and contentment in different candidates do not satisfy one choice.
    assert not run('eikh',[],m|{'eisg5':relation({('author','scheme','task','paper','other')})},'modal');count+=1
    reject_unknown('eikh',[],m,('eisg4','eisg5','eike'),'modal')
    return dict(cases=count,possible_adoption_not_actual_execution=True,contentment_is_limited_method_choice_not_optimality=True,same_candidate_scheme_and_task=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eiki','now')},'eisg6':{('node','author','eij5','eikh','paper','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=3):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for name,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eisgq':lambda:'node'});count+=1
        assert evaluate(doc,m|{'eisg4':forbidden,'eisg5':forbidden,'ce':forbidden});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eiki']['body']['force']=='assert'
    return dict(cases=count,concession_to_previous_limit=True,possibility_quoted_not_executed_by_attribution=True,main_text_order_preserved=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==232
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[229,230])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));validate_hashes(ROOT,source['source_sha256']);u=json.loads(read(INVENTORY))['units'][11];seg=source['segments'][0]
    assert seg['unit']==u['id'] and seg['range']==[0,309] and seg['text']==u['text'][:309] and seg['unit_sha256']==u['text_sha256'] and seg['nonblank_characters']==269
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,[INDEX]) and reading['source_nonblank_characters']==269
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=231,prior_paragraph_binding_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_reception_time_alternative import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('setup_and_arrival',setup_and_arrival_checks),('assignment',assignment_checks),('record',record_checks),('all_records',all_records_checks),('possibility',possibility_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][11]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'scripts/compose_reception_time_alternative.py','scripts/check_reception_time_alternative.py','scripts/review_reception_time_alternative.py','tests/test_reception_time_alternative.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='optional_reception_clock_assignment_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,309],source=u['text'][:309],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['観測者位置への依存と経験からの知識','より実用的な取り決めへの導入','三文全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
