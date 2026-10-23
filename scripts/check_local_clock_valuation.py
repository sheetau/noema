"""Check local coincidence, finding indications, and shared possible execution."""
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
from scripts.compose_local_clock_valuation import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_local_clock_valuation import SOURCE,INVENTORY,DOC,source_record

READING='data/local-clock-valuation-reading-v1.json';PRIOR='data/einstein-reception-alternative-paragraph-review-v1.json'
DOMAIN=('task','observer','clock','hand','place','near','frame','unit','paper','event','event2','display','author','prior','node','other')
POINTS=('now','possible','other')
BASE=['observer','clock','hand','place','frame','unit','possible']
METHOD=['task','observer','clock','hand','place','frame','unit','paper','now']

def forbidden(*args):raise ValueError('Unknown local-clock-valuation input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundary={'record':{'eik3'},'method':{'eik2','eikz','eik4'},'modal':{'eik5'},'conditional':{'eiky','eik6'}}.get(mode,set())
    abstract(doc,(set() if mode=='real' else NUM)|boundary)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jlc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jlccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jlccontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)

def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown local-clock-valuation' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))

def setup():
    cuts,m=arithmetic();r=cuts.read
    rows={'ca':{('clock',)},'va':{('frame',)},'ci':{('unit',)},'eisgf':{('clock','place',s,'now') for s in ()},'cb':{(x,'place','frame') for x in ('clock','observer','display')}|{('event','near','frame'),('event2','near','frame')},'zbd':{(x,) for x in ('event','event2','display')},'eisge':{('task','event','now'),('task','event2','now')},'eish7':{('task','place','frame','paper','now')},'eisia':{tuple(METHOD+['possible'])}}
    rows['eisgf']={('clock','place','frame',s) for s in ('now','possible')}
    rows|={'eisgr':{('observer','possible')},'eisdf':{('clock','possible')},'eisgs':{('hand','clock','possible')},'eisfp':{('near','place','frame',s) for s in ('now','possible')},'eisgm':{(e,'display','clock','frame','possible') for e in ('event','event2')},'eish3':{('observer',e,'display','hand','clock','frame','possible') for e in ('event','event2')}}
    m|={n:relation(rs) for n,rs in rows.items()}
    reads={('clock',e,'frame','unit',Q(9)) for e in ('event','event2','display')}
    marks={('display','hand','clock',Q(9),'possible')};assigns={('observer',e,'clock','frame','unit',Q(9),'possible') for e in ('event','event2')}
    m|={'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in reads,'eisgt':lambda d,h,c,x,s:(d,h,c,r(x),s) in marks,'eish4':lambda o,e,c,f,u,x,s:(o,e,c,f,u,r(x),s) in assigns}
    fields={(e,c,s):('near','display') for e in DOMAIN for c in DOMAIN for s in POINTS}
    candidates={(e,c,u,s):Q(9) for e in DOMAIN for c in DOMAIN for u in DOMAIN for s in POINTS}
    def project(e,c,slot,s):
        if (e,c,s) not in fields or slot.denominator!=1 or not 1<=slot<=2:raise ValueError('Unknown local-clock-valuation field')
        return fields[e,c,s][int(slot)-1]
    def reading(e,c,u,s):
        if (e,c,u,s) not in candidates:raise ValueError('Unknown local-clock-valuation reading')
        return cuts.make(candidates[e,c,u,s])
    m|={'eish5':project,'eish6':reading}
    return cuts,m,rows,reads,marks,assigns,fields,candidates

@lru_cache(None)
def local_checks():
    cuts,m,rows,reads,marks,assigns,*_=setup();args=BASE+['event','near','display',cuts.make(Q(9))];count=0
    for name,aa in (('eiky',['clock','place','frame','possible']),('eikz',['event','place','frame','possible']),('eik2',BASE),('eik3',args)):
        assert run(name,aa,m);count+=1
    for i in range(len(args)):
        bad=args.copy();bad[i]=cuts.make(Q(3)) if i==len(args)-1 else 'other';assert not run('eik3',bad,m);count+=1
    for name in ('ca','va','ci','eisgf','eisgr','eisdf','eisgs','eisfp','eisgm','eish3'):
        assert not run('eik3',args,m|{name:relation(set())});count+=1
    for row in rows['cb']-{('event2','near','frame')}:
        assert not run('eik3',args,m|{'cb':relation(rows['cb']-{row})});count+=1
    # Exact location is also allowed without the near-place relation.
    exact=args.copy();exact[8]='place'
    assert run('eik3',exact,m|{'cb':relation(rows['cb']|{('event','place','frame')}),'eisfp':relation(set())});count+=1
    for reading,indication,event_value in product((Q(9),Q(3)),repeat=3):
        mm=m|{'eisgt':lambda d,h,c,x,s,i=indication:(d,h,c,cuts.read(x),s)==('display','hand','clock',i,'possible'),'ce':lambda c,e,f,u,x,i=event_value:(c,e,f,u,cuts.read(x)) in {('clock','event','frame','unit',i),('clock','display','frame','unit',Q(9))}}
        assert run('eik3',BASE+['event','near','display',cuts.make(reading)],mm)==(reading==indication==event_value==Q(9));count+=1
    for name,rs in (('eish3',rows['eish3']),('eisgm',rows['eisgm'])):
        row=next(x for x in rs if 'event' in x)
        for i in range(len(row)):
            bad=tuple('other' if i==j else x for j,x in enumerate(row));assert not run('eik3',args,m|{name:relation((rs-{row})|{bad})});count+=1
    assert run('eik3',args,m|{n:forbidden for n in ('zbv','qo','eisgu','eisgv','eisg2','eise6','eise7')});count+=1
    reject_unknown('eik3',args,m,('ba','eisgt','ce','eisgm','eish3','eish4'))
    try:run('eik3',args,m,'real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real validation silently sampled')
    return dict(cases=count,near_and_same_place_both_allowed=True,native_indication_and_event_readings_bound=True,finding_and_valuation_required=True,no_receiving_signal_or_remote_sync_added=True,full_real_domain_refused=True)

@lru_cache(None)
def record_checks():
    cuts,m,rows,reads,marks,assigns,fields,candidates=setup();args=BASE+['event'];count=0
    assert run('eik4',args,m);count+=1
    for i in range(2):
        old=fields['event','clock','possible'];changed=list(old);changed[i]='other';fields['event','clock','possible']=tuple(changed)
        assert not run('eik4',args,m);count+=1;fields['event','clock','possible']=old
    fields['event','clock','possible']=('display','near');assert not run('eik4',args,m);count+=1;fields['event','clock','possible']=('near','display')
    candidates['event','clock','unit','possible']=Q(3);assert not run('eik4',args,m);count+=1;candidates['event','clock','unit','possible']=Q(9)
    for slot in (Q(0),Q(3),Q(1,2)):
        try:m['eish5']('event','clock',slot,'possible')
        except ValueError:pass
        else:raise AssertionError('Invalid field accepted')
    # Inspect each selector's role without conflating rejection with downstream validity.
    seen=[]
    mm=m|{'eik3':lambda *xs:seen.append(tuple(value(x) if not hasattr(x,'parameters') else x for x in xs)) or True}
    assert run('eik4',args,mm,'record');assert seen[0][:10]==tuple(BASE+['event','near','display']);count+=1
    reject_unknown('eik4',args,m,('eish5','eish6'))
    return dict(cases=count,two_fields_same_event_clock_context=True,unknown_candidates_not_defaulted=True)

@lru_cache(None)
def method_checks():
    _,m,rows,*_=setup();count=0
    for a,b,va,vb in product((False,True),repeat=4):
        selected={('task',e,'now') for e,on in (('event',a),('event2',b)) if on}
        valid={tuple(BASE+[e]) for e,on in (('event',va),('event2',vb)) if on}
        mm=m|{'eisge':relation(selected),'eik2':relation({tuple(BASE)}),'eikz':relation({(e,'place','frame','now') for e in ('event','event2')}),'eik4':relation(valid)}
        assert run('eik5',METHOD+['possible'],mm,'method')==((not a or va) and (not b or vb));count+=1
    assert run('eik5',METHOD+['possible'],m);count+=1
    # Both native event bodies must succeed in the same possible execution.
    bad=m|{'eish3':relation(rows['eish3']-{('observer','event2','display','hand','clock','frame','possible')})}
    assert not run('eik5',METHOD+['possible'],bad);count+=1
    assert not run('eik6',METHOD,bad);count+=1
    assert run('eik6',METHOD,m);count+=1
    for name in ('eish7','eisia'):
        row=next(iter(rows[name]))
        for i in range(len(row)):
            changed=tuple('other' if i==j else x for j,x in enumerate(row));assert not run('eik5',METHOD+['possible'],m|{name:relation({changed})});count+=1
    reject_unknown('eik5',METHOD+['possible'],m,('eish7','eisia','eisge'))
    return dict(cases=count,fixed_reference_scope_and_all_targets=True,native_two_event_method_executed=True,no_actual_event_existence_added=True,one_common_candidate_required=True)

def references():
    return {n:(lambda x=x:x) for n,x in zip(('eisib','ziq','ra','rb','eisie','eisic','eisid','eirf','rd','eishs','eish2'),('clock','place','frame','unit','task','observer','hand','paper','author','prior','node'))}|{'ri':lambda:'now'}

@lru_cache(None)
def modal_checks():
    count=0
    for bits in product((False,True),repeat=3):
        rows={tuple(METHOD+[s]) for s,on in zip(POINTS,bits) if on}
        assert run('eik6',METHOD,{'eik5':relation(rows)},'modal')==any(bits);count+=1
    for i in range(len(METHOD)):
        row=METHOD+['possible'];row[i]='other';assert not run('eik6',METHOD,{'eik5':relation({tuple(row)})},'modal');count+=1
    for premise,ability in product((False,True),repeat=2):
        m=references()|{'eiky':relation({('clock','place','frame','now')} if premise else set()),'eik6':relation({tuple(METHOD)} if ability else set())}
        assert run('eik7',[],m,'conditional')==((not premise) or ability);count+=1
    _,m,*_=setup();assert run('eik7',[],m|references());count+=1
    reject_unknown('eik7',[],references()|{'eiky':lambda *xs:False,'eik6':lambda *xs:True},('eiky','eik6'),'conditional')
    return dict(cases=count,conditional_not_unconditional_actual_success=True,possible_execution_not_all_candidates=True,native_conditional_content_executed=True)

@lru_cache(None)
def presentation_checks():
    rows={'eir3':{('node','author','paper','eila','now')},'ue':{('prior','node','now')}};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=references()|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m);count+=1
        for n,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                bad=tuple('other' if i==j else x for j,x in enumerate(row));assert not evaluate(doc,m|{n:relation({bad})});count+=1
        assert not evaluate(doc,m|{n:lambda *xs:True for n in rows}|{'eishs':lambda:'node'});count+=1
        assert evaluate(doc,m|{'ca':forbidden,'eisia':forbidden,'ce':forbidden});count+=1
    return dict(cases=count,existing_forward_reference_begin_reused=True,attribution_not_actual_clock_experiment=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==235
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[231,232,233])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==197
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX]) and rec['source_nonblank_characters']==197
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=234,prior_paragraph_binding_preserved=True,three_A_symbols_same_place=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_local_clock_valuation import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('local',local_checks),('record',record_checks),('method',method_checks),('modal',modal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][12]
    segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,251],source=u['text'][:251],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]
    segments.extend(dict(unit=u['id'],unit_sha256=u['text_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eik7'],status='explicit_interpretive_annotation') for m in source_record()['segments'][0]['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,PRIOR,'scripts/compose_local_clock_valuation.py','scripts/check_local_clock_valuation.py','scripts/review_local_clock_valuation.py','tests/test_local_clock_valuation.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='conditional_local_clock_valuation_and_corresponding_indications_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['点Bの時計以降とu0013全体の判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
