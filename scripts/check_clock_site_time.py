"""Check clock populations, local readings, time roles and the whole directive."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_material_relative_frame import RS
from scripts.check_rod_methods import value
from scripts.compose_clock_site_time import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,LIMITS,build

DOC='docs/clock-site-time-v1.md';SOURCE='data/einstein-clock-site-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FIRST='data/einstein-measured-space-sentence-reading-v2.json'
DEPENDENCIES=('reports/measured-space-sentence-v2.json','reports/simultaneity-conclusion-v1.json','reports/frame-instruments-v1.json')
DOMAIN=('event','display','clock','reference','place','frame','moving','moment','othermoment','unit','lengthunit','x','y','z','author','paper','section','firstsection','space','time','tname','tauname','other')
POINTS=('context','initial','discourse','other')

def forbidden(*xs):raise ValueError('Unknown clock-site-time input')
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','zbm':'moving','rb':'unit','ta':'lengthunit','yn':'x','yo':'y','yp':'z','zb4':'initial','zb6':'context','rd':'author','eirf':'paper','ri':'discourse','eisms':'section','eisdy':'firstsection','zc2':'space','zc3':'time','eism5':'tname','eisnl':'tauname'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eit2','qo'}
    if name in ('eiyf','eiyg'):boundaries.add('eiye')
    if name=='eiyh':boundaries.add('eiyg')
    if name=='eiyi':boundaries|={'eiuk','eiyh'}
    if name=='eiyk':boundaries|={'eiyf','eiyi','eiyj'}
    if name in ('eiyn','eiyo'):boundaries.add('eiyg')
    if name=='eiyp':boundaries.add('eiyk')
    if mode=='protocol':boundaries.discard('qo');boundaries.add('db')
    if mode=='native_history':boundaries.discard('eit2')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jcst'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcstpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcstpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jcstpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown clock-site-time' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def clock_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,2))
    fs={a:FunctionValue((RS,),RS,lambda t,i=i:c(Q(i))) for i,a in enumerate(('x','y','z'))}
    history=['clock','moving','context','lengthunit','unit',c(Q(0)),c(Q(2)),*fs.values()]
    rows={'ca':{('clock',)},'va':{('moving',)},'ci':{('unit',)},'cc':{('clock','moving')},'eisdf':{('clock','context')},'eit2':{norm(history)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    def tracks(cl,f,lu,tu,a,ctx):
        if (cl,f,lu,tu,ctx)!=('clock','moving','lengthunit','unit','context') or a not in fs:forbidden()
        return fs[a]
    m|={'eismh':tracks,'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2))}
    check=lambda mm:run('eiye',['clock','moving','context'],mm);count=perturb(check,m,rows,norm)
    unknowns(check,m,('eismh','eisls','eislt'))
    assert check(m|{'eipw':forbidden});count+=1
    try:run('eiye',['clock','moving','context'],m|{'eisdd':lambda *xs:True,'zzbg':lambda a,b:r(a)<r(b)},'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete representative history silently sampled')
    return dict(cases=count,own_frame_complete_representative_rest_not_clock_internals=True,native_full_real_history_refused=True)

@lru_cache(None)
def network_checks():
    domain=('a','b','c');pop={'a','b'};f='a';ctx='context'
    rows={'va':{(f,)},'ci':{('b',)},'eisb7':{(f,'a','b',ctx)},'eiye':{(cl,f,ctx) for cl in pop},'qo':{(a,b,f,'b',ctx) for a,b in product(pop,repeat=2)}}
    base={n:relation(rs) for n,rs in rows.items()}|{'rb':lambda:'b','zbh':lambda *xs:'a','zbz':lambda frame,cl,c:frame==f and cl in pop and c in (ctx,'initial'),'qa':lambda cl,frame,c:cl in pop and frame==f and c==ctx,'zcu':lambda place,frame,c:place in domain and frame==f and c==ctx,'cb':lambda cl,p,frame:cl in pop and cl==p and frame==f}
    check=lambda m:run('eiyf',[f,ctx],m,domain=domain);count=perturb(check,base,rows)
    for patch in ({'zbh':lambda *xs:'c'},{'zbz':lambda frame,cl,c:frame==f and cl in (pop if c=='initial' else {'a'})},{'qa':lambda cl,frame,c:cl in domain},{'cb':lambda cl,p,frame:cl=='a' and p=='a'},{'zcu':lambda place,frame,c:place=='a'}):
        assert not check(base|patch);count+=1
    # No clock at c is required; an extra non-member clock in qa is rejected.
    assert check(base|{'zcu':lambda place,frame,c:place in pop and frame==f and c==ctx});count+=1
    unknowns(check,base,('zbh','zbz','qa','zcu','cb'))
    return dict(cases=count,all_initial_clocks_and_all_pairs_required=True,unclocked_space_allowed=True,reference_in_same_population_and_all_locations_bound=True)

@lru_cache(None)
def protocol_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());domain=('a','b')
    m|={'qa':lambda cl,f,ctx:cl in domain and f=='a' and ctx=='context','ca':lambda cl:cl in domain,'cc':lambda cl,f:cl in domain and f=='a','cb':lambda cl,p,f:cl==p and f=='a','ci':lambda u:u=='b','ql':lambda a,b,f,u,ctx:(a,b,f,u,ctx)==('a','b','a','b','context'),'qb':lambda a,b,f,u,ctx,t:(a,b,f,u,ctx)==('a','b','a','b','context') and t in domain}
    m|={n:lambda t:t for n in ('qc','qd','qe','qf','qg','qh')};m|={'qi':lambda t:c(Q(0)),'qj':lambda t:c(Q(1)),'qk':lambda t:c(Q(2))}
    trials={('a','b',*(t for _ in range(6)),'a','b',Q(0),Q(1),Q(2)) for t in domain}
    m['db']=lambda *xs:norm(xs) in trials;check=lambda mm:run('qo',['a','b','a','b','context'],mm,'protocol',domain)
    count=perturb(check,m,{'db':trials},norm)
    for patch in ({'ql':lambda *xs:False},{'qb':lambda *xs:False}):assert not check(m|patch);count+=1
    unknowns(check,m,('ql','qb','qi','qj','qk','qc','qd','qe','qf','qg','qh'))
    return dict(cases=count,nonempty_all_trials_and_completeness_not_single_success=True,all_protocol_arguments_bound=True)

@lru_cache(None)
def local_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    rows={'zbz':{('moving','clock','context')},'zcu':{('place','moving','context')},'eiye':{('clock','moving','context')},'zbd':{('event',),('display',)},'va':{('moving',)},'eisb7':{('moving','reference','unit','context')},'ca':{('clock',),('reference',)},'cc':{('clock','moving'),('reference','moving')},'ci':{('unit',)},'cb':{(o,'place','moving') for o in ('clock','event','display')},'ce':{('clock',e,'moving','unit',Q(7)) for e in ('event','display')},'qo':{('clock','reference','moving','unit','context')},'eisgm':{('event','display','clock','moving','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};m['zbh']=lambda *xs:'reference'
    args=['event','clock','place','moving',c(Q(7)),'context'];check=lambda mm:run('eiyg',args,mm)
    count=perturb(check,m,rows,norm);unknowns(check,m,('zbh','ba'))
    assert not run('eiyg',args[:4]+[c(Q(8)),'context'],m);count+=1
    # Native existential over two individuals; every free argument is distinguished.
    for bits in product(('a','b'),repeat=4):
        e,cl,p,f=bits;row=(e,cl,p,f,Q(7),'context');mm={'eiyg':lambda *xs,row=row:norm(xs)==row}
        args=[e,p,f,c(Q(7)),'context'];assert run('eiyh',args,mm,domain=('a','b'));count+=1
        for i in (0,2,3,4,5):
            bad=list(row);bad[i]='wrong';assert not run('eiyh',args,{'eiyg':lambda *xs,bad=tuple(bad):norm(xs)==bad},domain=('a','b'));count+=1
    rows={'eiuk':{('event','moving','unit','context')},'eiyh':{('event','place','moving',Q(7),'context')}}
    mm={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{'zbe':lambda *xs:c(Q(7))}
    count+=perturb(lambda mm:run('eiyi',['event','place','moving','context'],mm),mm,rows,norm)
    unknowns(lambda mm:run('eiyi',['event','place','moving','context'],mm),mm,('zbe',))
    for name,f in (('eiyn','frame'),('eiyo','moving')):
        rows={'eiyg':{('event','clock','place',f,Q(7),'context')}};mm={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
        count+=perturb(lambda mm:run(name,['event','clock','place',c(Q(7)),'context'],mm),mm,rows,norm)
    return dict(cases=count,native_local_readout_saf_and_same_display_checked=True,population_place_clock_frame_value_and_unit_bound=True,existential_clock_selection_uses_two_individuals=True)

@lru_cache(None)
def moment_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,());moments={'moment','othermoment'}
    rows={'zbd':{('event',)},'zcf':{(t,'moving','unit','context') for t in moments}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'eisnk':relation({('event',t,'moving','context') for t in moments}),'zbe':lambda *xs:c(Q(7)),'yl':lambda *xs:c(Q(7))}
    check=lambda mm:run('eiyj',['event','moving','context'],mm);count=perturb(check,m,rows)
    assert check(m|{'eisnk':relation({('event','moment','moving','context')})});count+=1
    for patch in ({'eisnk':lambda *xs:False},{'eisnk':relation({('event','moment','frame','context')})},{'yl':lambda t,*xs:c(Q(8 if t=='othermoment' else 7))},{'zbe':lambda *xs:c(Q(8))}):assert not check(m|patch);count+=1
    unknowns(check,m,('eisnk','zbe','yl','ba','sca'))
    rows={'zcf':{('moment','moving','unit','context')}};mm={n:relation(rs) for n,rs in rows.items()};mm|={n:m[n] for n in NUM if n in m};mm['yl']=lambda *xs:c(Q(9))
    count+=perturb(lambda mm:run('eiym',['moment',c(Q(9)),'context'],mm),mm,rows)
    assert not run('eiym',['moment',c(Q(7)),'context'],mm);count+=1
    return dict(cases=count,nonempty_and_all_moment_correspondences_match_local_value=True,multiple_descriptions_of_same_time_allowed=True,existing_t_rule_unchanged_and_tau_frame_distinguished=True)

@lru_cache(None)
def coverage_checks():
    domain=('a','b','c');f='a';ctx='context';pop={'a','b'}
    base={'eiyf':relation({(f,ctx)}),'zbz':lambda frame,cl,c:frame==f and cl in pop and c==ctx,'zcu':lambda p,frame,c:p in domain and frame==f and c==ctx,'cb':lambda o,p,frame:o==p and frame==f,'zcz':lambda e,frame,c:e in domain and frame==f and c==ctx,'eiyi':relation({(e,e,f,ctx) for e in pop}),'eiyj':relation({(e,f,ctx) for e in pop})}
    check=lambda m:run('eiyk',[f,ctx],m,domain=domain)
    rows={n:{(f,ctx)} if n=='eiyf' else ({(e,e,f,ctx) for e in pop} if n=='eiyi' else {(e,f,ctx) for e in pop}) for n in ('eiyf','eiyi','eiyj')}
    count=perturb(check,base,rows)
    assert check(base|{'zcz':lambda *xs:False});count+=1
    assert not check(base|{'zbz':lambda frame,cl,c:frame==f and cl in domain and c==ctx});count+=1
    # A second event at a clock site must also receive a value there.
    assert not check(base|{'cb':lambda o,p,frame:frame==f and (o==p or (o,p)==('c','a'))});count+=1
    unknowns(check,base,('zbz','zcu','cb','zcz'))
    rows={'eiyk':{('frame','context'),('moving','context')}}
    count+=perturb(lambda mm:run('eiyp',[],mm),{'eiyk':relation(rows['eiyk'])},rows)
    return dict(cases=count,all_events_at_all_clock_sites_not_all_space=True,no_event_existence_added_to_empty_site=True,both_frames_required=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislo':{('tname','eiwt','paper','discourse'),('tauname','eiym','paper','discourse')},'eislp':{('time','author','firstsection',r,'paper','discourse') for r in ('eiyn','eiyo')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiyq',[],mm),m,rows)
    rows|={'ug':{('time','author','eiyp','section','discourse')},'zao':{('space','time','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiyr',[],mm),m,rows)
    assert run('eiyr',[],m|{n:forbidden for n in ('eiyp','eiyk','qo','eiyn','eiyo','eiym','yl')});count+=1
    rows={'eir3':{('time','author','paper','eiys','discourse')},'ue':{('space','time','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiyt',[],mm),m,rows)
    assert run('eiyt',[],m|{n:forbidden for n in ('ug','eiyr','eiyp','eiyk')});count+=1
    return dict(cases=count,two_first_section_references_and_both_time_symbols_bound=True,addition_direction_and_author_order_preserved=True,quoted_physical_content_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][44];assert u['id']=='einstein-1905:u0045' and len(u['text'])==761
    assert u['text_sha256']=='adc4984541a1599e358dba1ca4d46bf1d15b67c29cd10e4dc17fbb9f8985c31d'
    first=json.loads(read(FIRST));validate_hashes(ROOT,first['source_sha256']);assert first['source']['text']==u['text'][:240]
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=('K','k','x,y,z','ξ,η,ζ','t','τ');bindings=('ra','zbm','eixv/eixw/eixx','eixy/eixz/eix2','eiwt','eiym')
    entries=[]
    for n,s,b in zip(u['math_ids'],forms,bindings):
        assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
        entries.append(dict(id=n,sha256=math[n]['sha256'],reading=s,binding=b))
    fullcount=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert fullcount==602
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text'][241:]));assert count==426
    paths={INVENTORY,DOC,FIRST,'artifacts/einstein-frame-coordinates-v1/page-898.jpg','artifacts/einstein-frame-coordinates-v1/page-898.html','artifacts/einstein-frame-coordinates-v1/retrieval.json'}
    return dict(version='einstein-clock-site-time-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897','898'],unit=u['id'],unit_sha256=u['text_sha256'],range=[0,761],text=u['text'],source_nonblank_characters=602,math=entries,second_sentence=dict(range=[241,761],text=u['text'][241:],nonblank_characters=426),observations=['原刊898頁でt/τ、二つの§1参照、両系の時計所在地点の全範囲、fernerとebensoの追加指示を再照合した。','第一文[0,240)は修正版の判断を保持する。空白[240,241)を除き、第二文は連続した[241,761)である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==272
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    first=json.loads(read(FIRST));assert selection_binding(new,[270])==first['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/measured-space-sentence-identifiers-v2.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eiys']['body']['force']=='direct'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=271,first_sentence_and_all_prior_meanings_preserved=True,additional_setting_is_directive=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('clock',clock_checks),('network',network_checks),('protocol',protocol_checks),('local',local_checks),('moment',moment_checks),('coverage',coverage_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();second=source['second_sentence'];paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,FIRST,*DEPENDENCIES,'scripts/compose_clock_site_time.py','scripts/check_clock_site_time.py','tests/test_clock_site_time.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_rod_methods.py','scripts/compose_material_axes.py','scripts/compose_limits.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py'}
    return dict(status='clock_site_time_and_second_sentence_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=second['range'],source=second['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0045の二文全体の通読判断登録','u0046以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
