"""Check coincident indications, one reference clock and retrospective adoption."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM
from scripts.check_synchrony_laws import native_model,DOMAIN as PRIOR_DOMAIN
from scripts.compose_event_time_summary import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_event_time_summary import SOURCE,INVENTORY,DOC,READING,PRIORS,source_record

POINTS=('now','other');DOMAIN=PRIOR_DOMAIN+('eventa','eventb','displaya','displayb','summary','definition','material','task','assumption')


def forbidden(*args):raise ValueError('Unknown event-time-summary input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode=='boundary':abstract(doc,NUM|{'qo'})
    elif mode=='native':abstract(doc,NUM|{'bi'})
    elif mode=='logic':abstract(doc,{'einl','einm'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jets'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jetscontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jetscontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jetscontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})[0]['value']


def reject_unknown(name,args,m,symbols,mode='boundary'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown event-time-summary' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def references():
    names={'eiskk':'summary','rj':'definition','eiskl':'material','eisjf':'task','eiskc':'assumption','eiske':'secondlaw','rc':'clockb'}
    return {n:(lambda x=x:x) for n,x in names.items()}


def setup(second_value=7,forward_end=4):
    cuts,m,rows=native_model(forward_end);m|=references();r=cuts.read
    rows['ca'].add(('clockc',));rows['cc'].add(('clockc','frame'))
    rows['cb']|={(obj,p,'frame') for obj,p in (('eventa','placea'),('displaya','placea'),('eventb','placeb'),('displayb','placeb'),('clockc','placec'))}
    rows['zbd']|={(e,) for e in ('eventa','eventb','displaya','displayb')}
    rows['eisgm']={(e,d,c,'frame','now') for e,d,c in (('eventa','displaya','clocka'),('eventb','displayb','clockb'))}
    rows['qo']={(c,'clockb','frame','unit','now') for c in ('clocka','clockb')}
    reads={(c,e,'frame','unit',Q(x)) for c,es,x in (('clocka',('eventa','displaya'),7),('clockb',('eventb','displayb'),second_value)) for e in es}
    previous=m['ce'];m|={n:relation(rs) for n,rs in rows.items()}
    m['ce']=lambda c,e,f,u,x:previous(c,e,f,u,x) or (c,e,f,u,r(x)) in reads
    return cuts,m,rows,reads,previous


def time_args(cuts,second=False,value=7):
    return (['eventb','clockb','placeb'] if second else ['eventa','clocka','placea'])+[cuts.make(Q(value)),'now']


@lru_cache(None)
def indication_checks():
    cuts,m,rows,reads,previous=setup();args=time_args(cuts);count=0
    assert run('eing',args,m);count+=1
    for i in range(len(args)):
        a=args.copy();a[i]=cuts.make(Q(9)) if i==3 else 'other';assert not run('eing',a,m);count+=1
    required={'ca':{('clocka',),('clockb',)},'cc':{('clocka','frame'),('clockb','frame')},'ci':{('unit',)},'cb':{(x,'placea','frame') for x in ('clocka','eventa','displaya')},'zbd':{('eventa',),('displaya',)},'eisgm':{('eventa','displaya','clocka','frame','now')},'qo':{('clocka','clockb','frame','unit','now')}}
    for symbol,rs in required.items():
        for row in rs:
            assert not run('eing',args,m|{symbol:relation(rows[symbol]-{row})});count+=1
    for row in (('clocka','eventa','frame','unit',Q(7)),('clocka','displaya','frame','unit',Q(7))):
        remaining=reads-{row}
        assert not run('eing',args,m|{'ce':lambda c,e,f,u,x:previous(c,e,f,u,x) or (c,e,f,u,cuts.read(x)) in remaining});count+=1
    # Numerically equal displays at a different moment cannot replace coincidence.
    assert not run('eing',args,m|{'eisgm':relation({('eventb','displaya','clocka','frame','now')})});count+=1
    # All five roles of the local coincidence relation are necessary.
    row=('eventa','displaya','clocka','frame','now')
    for i in range(len(row)):
        assert not run('eing',args,m|{'eisgm':relation({changed(row,i)})});count+=1
    assert not run('eing',args,m|{'ba':lambda *xs:False});count+=1
    reject_unknown('eing',args,m,('zbd','ca','cc','cb','ci','ce','qo','eisgm','ba'))
    return dict(cases=count,same_event_and_local_indication_not_just_same_number=True,each_coincidence_role_and_both_readings_checked=True,local_and_reference_clocks_stationary=True)


@lru_cache(None)
def reference_checks():
    cuts,m,rows,*_=setup();a=time_args(cuts);b=time_args(cuts,True);sim=a[:3]+b[:3]+[a[3],b[3],'now'];count=0
    assert run('eing',a,m) and run('eing',b,m);count+=2
    assert run('einh',sim,m);count+=1
    # Distinct cut objects carry the same number, so object identity is irrelevant.
    assert a[3] is not b[3]
    cuts2,mm,*_=setup(9);bb=time_args(cuts2,True,9);aa=time_args(cuts2)
    assert run('eing',aa,mm) and run('eing',bb,mm);count+=2
    assert not run('einh',aa[:3]+bb[:3]+[aa[3],bb[3],'now'],mm);count+=1
    split={('clocka','clockb','frame','unit','now'),('clockb','clockc','frame','unit','now')}
    mm=m|{'qo':relation(split)}
    assert run('eing',a,mm);count+=1
    assert not run('eing',b,mm);count+=1
    assert not run('einh',sim,mm);count+=1
    assert not run('eing',a,m|{'rc':lambda:'clockc'});count+=1
    seen=[];sync=m['qo'];mm=m|{'qo':lambda *xs:seen.append(xs) or sync(*xs)}
    assert run('einh',sim,mm);count+=1
    assert set(seen)=={(c,'clockb','frame','unit','now') for c in ('clocka','clockb')}
    # Two individually acceptable assignments cease to establish simultaneity if one display is missing.
    assert not run('einh',sim,m|{'eisgm':relation({('eventa','displaya','clocka','frame','now')})});count+=1
    reject_unknown('einh',sim,m,('eisgm','qo','sca'))
    return dict(cases=count,one_closed_reference_for_distinct_events_and_local_clocks=True,separate_reference_per_assignment_rejected=True,numeric_equality_not_function_identity=True)


@lru_cache(None)
def native_checks():
    cuts,m,*_=setup();a=time_args(cuts);b=time_args(cuts,True);sim=a[:3]+b[:3]+[a[3],b[3],'now'];count=0
    for name,args in (('eing',a),('eing',b),('einh',sim)):
        assert run(name,args,m,'native');count+=1
    badcuts,bad,*_=setup(forward_end=5);bad_a=time_args(badcuts);bad_b=time_args(badcuts,True)
    bad_sim=bad_a[:3]+bad_b[:3]+[bad_a[3],bad_b[3],'now']
    assert not run('eing',bad_a,bad,'native');count+=1
    assert run('eing',bad_b,bad,'native');count+=1
    assert not run('einh',bad_sim,bad,'native');count+=1
    for symbol in ('ql','qb','qa','cg','ce','bi'):
        assert not run('eing',a,m|{symbol:lambda *xs:False},'native');count+=1
    reject_unknown('eing',a,m,('ql','qb','qi','qj','qk','bi'),'native')
    try:run('eing',a,m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real domain silently sampled')
    return dict(cases=count,native_qu_qt_saf_qo_qn_db_connections_checked=True,self_reference_and_distinct_clock_synchrony_distinguished=True,numeric_boundaries_explicit_and_full_real_sampling_refused=True)


def discourse_model():
    _,m,*_=setup()
    rows={'eisju':{('sixth','author','clocka','clockb','placea','placeb','frame','unit','proposal','time','trial','eims','eimk','paper','now')},'eiskn':{('material','paper','now')},'eisko':{('material','paper','now')},'eiskm':{('material',n,'paper','now') for n in ('eik7','eiml')},'eishy':{('author','material','task','time','paper','now')},'uj':{(n,'author','eing','paper','now') for n in ('summary','definition')},'eiskp':{('summary','author','einh','paper','now')},'eisdk':{('paper','einl','einm','now')},'zdg':{('summary','author','einm','paper','now')}}
    m|={n:relation(rs) for n,rs in rows.items()};return m,rows


@lru_cache(None)
def adoption_checks():
    m,rows=discourse_model();count=0
    for name in ('einl','einm','einn','eini'):
        assert run(name,[],m);count+=1
    targets={'eisju':'einl','eiskn':'einl','eisko':'einl','eiskm':'einl','eishy':'einl','uj':None,'eiskp':'einm','eisdk':'einn','zdg':'einn'}
    for symbol,rs in rows.items():
        for row in rs:
            name=targets[symbol] or ('einm' if row[0]=='summary' else 'eini')
            for i in range(len(row)):
                assert not run(name,[],m|{symbol:relation((rs-{row})|{changed(row,i)})});count+=1
    physics={n:forbidden for n in ('ca','cb','cc','ce','cg','qa','qb','ba','qo','eisgm')}
    for name in ('einl','einm','einn','eini'):
        assert run(name,[],m|physics);count+=1
    reject_unknown('einn',[],m,('eisju','eiskn','eisko','eiskm','eishy','uj','eiskp','eisdk','zdg'))
    return dict(cases=count,thought_physical_material_and_definitional_means_separate=True,both_time_and_simultaneity_adopted=True,all_closed_rules_attributed_without_executing_physics=True,reason_direction_and_obviousness_attribution_preserved=True)


@lru_cache(None)
def summary_logic_checks():
    m,rows=discourse_model();count=0
    for grounds,result,reason,obvious in product((False,True),repeat=4):
        mm=m|{'einl':lambda p=grounds:Content(POINTS,(p,p)),'einm':lambda p=result:Content(POINTS,(p,p)),'eisdk':relation(rows['eisdk'] if reason else set()),'zdg':relation(rows['zdg'] if obvious else set())}
        assert run('einn',[],mm,'logic')==(grounds and result and reason and obvious);count+=1
    return dict(cases=count,grounds_result_reason_and_obviousness_all_required=True)


@lru_cache(None)
def presentation_checks():
    m,_=discourse_model();rows={'eir3':{('summary','author','paper','eino','now'),('definition','author','paper','einj','now')},'eiskq':{('summary','author',n,'paper','now') for n in ('sixth','assumption')},'ue':{('secondlaw','summary','now'),('summary','definition','now')}};m|={n:relation(rs) for n,rs in rows.items()};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-2:]
        def go(extra=None):return [r['value'] for r in evaluate(doc,m|(extra or {}))]
        assert go()==[True,True];count+=1
        for symbol,rs in rows.items():
            for row in rs:
                target=1 if row[0]=='definition' or row==('summary','definition','now') else 0;expected=[True,True];expected[target]=False
                for i in range(len(row)):
                    assert go({symbol:relation((rs-{row})|{changed(row,i)})})==expected;count+=1
        assert go({n:forbidden for n in ('uj','eisju','eisgm','ce','ba')})==[True,True];count+=1
    return dict(cases=count,retrospective_definition_and_assumption_references_preserved=True,source_order_and_existing_definition_node_preserved=True,attribution_nonfactive=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==245
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,(list(range(234,240)),[240],[242])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert [s['nonblank_characters'] for s in source['segments']]==[233,214]
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX,INDEX+1])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=243,previous_synchrony_judgments_preserved=True,whole_447_character_two_sentence_source_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_event_time_summary import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('indications',indication_checks),('common_reference',reference_checks),('native',native_checks),('adoption',adoption_checks),('summary_logic',summary_logic_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_event_time_summary.py','scripts/check_event_time_summary.py','scripts/review_event_time_summary.py','tests/test_event_time_summary.py','scripts/check_synchrony_laws.py','scripts/check_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='retrospective_definition_and_coincident_common_reference_event_time_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、u0019以降の光速度の定数設定'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
