"""Check shared constants, current contexts and normalized remaining candidates."""
from functools import lru_cache
from fractions import Fraction as Q
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
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_translated_light_trial import expose
from scripts.check_four_coordinate_claim import model as previous_model,RS,RECORDS
from scripts.compose_origin_constants_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,build

DOC='docs/origin-constants-claim-v1.md';SOURCE='data/einstein-origin-constants-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-four-coordinate-u0084-review-v1.json'
DEPENDENCIES=('reports/origin-constants-v1.json','reports/four-coordinate-claim-v1.json','reports/translated-light-trial-v1.json','reports/affine-time-claim-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zfp':'unknown','zfq':'constants','zfk':'beta','ra':'rest','zbm':'moving','zee':'agent','zfm':'stage'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'event','other_event','first','second','other')))
SITUATIONS=('stage','context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'sje','sjd','sky','eiyx'}
    if name=='ei7m':boundaries|={'ei3a','ei26','ei27'}
    if name=='ei7n' and mode=='instance':boundaries.add('ei7m')
    if name=='ei7o':boundaries.add('ei7n')
    if name=='sqd':boundaries|={'smq','smb'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'}))=={'ei7n':4,'sqd':2,'smq':1,'smb':3}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jocc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='joccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='joccpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='joccapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='joccapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('joccpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=900000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def translated(offsets=(4,1,2,3)):
    cuts,m,coords,scopes,original,seen=previous_model();shift=tuple(map(Q,(offsets[1],offsets[2],offsets[3],offsets[0])))
    def result(point):return [v+d for v,d in zip(original(point),shift)]
    coords['y']=result(coords['x']);coords['z']=coords['y'][:];coords['time']=[v+1 for v in coords['y']]
    m|={'ei3a':lambda ctx:ctx=='other','ei27':lambda r,f,ctx:ctx=='other' and r in scopes['left' if f=='rest' else 'right'] if f in ('rest','moving') else forbidden(),'ei26':lambda a,b,ctx:ctx=='other' and (a,b) in scopes['pairs']}
    return cuts,m,coords,scopes,result,seen

@lru_cache(None)
def numeric_checks():
    count=0
    for offsets in ((4,1,2,3),(0,0,0,0),(4,0,0,0),(0,1,0,0),(0,0,2,0),(0,0,0,3),(-4,-1,-2,-3)):
        cuts,m,coords,scopes,result,seen=translated(offsets);args=['x','y',*map(cuts.make,map(Q,offsets))]
        assert run('spu',args,m);count+=1
        for slot in range(4):
            coords['y'][slot]+=1;assert not run('spu',args,m);coords['y'][slot]-=1;count+=1
            bad=args.copy();bad[slot+2]=cuts.make(Q(offsets[slot])+1);assert not run('spu',bad,m);count+=1
        assert set(seen)=={Q(3)}
    cuts,m,coords,scopes,result,seen=translated()
    for wrong in ((0,0,0,0),(4,4,4,4)):
        assert not run('spu',['x','y',*map(cuts.make,map(Q,wrong))],m);count+=1
    unknowns(lambda mm:run('spu',['x','y',*map(cuts.make,map(Q,(4,1,2,3)))],mm),m,('zc6','zc5','tc','zb7','zeq','sky','sjd','sje','ba','sca'))
    return dict(cases=count,four_independent_offsets_zero_negative_and_same_phi_checked=True,each_rhs_and_each_constant_distinguished=True)

@lru_cache(None)
def graph_checks():
    count=0
    cuts,m,coords,scopes,result,seen=translated();args=[*map(cuts.make,map(Q,(4,1,2,3))),'other']
    # All four test individuals have explicitly supplied coordinates. The
    # native forall body may inspect non-selected pairs under eager evaluation.
    m|={'ra':lambda:'x','zbm':lambda:'y','ei27':lambda r,f,ctx:ctx=='other' and r in scopes['left' if f=='x' else 'right'] if f in ('x','y') else forbidden()}
    for label in ('baseline','missing_alias','extra_relation','missing_pair','empty_left','wrong_context','no_current_correspondence'):
        scopes.update(left={'x'},right={'y','z','time'},pairs={('x','y'),('x','z')});mm=m
        if label=='missing_alias':scopes['pairs'].remove(('x','z'))
        if label=='extra_relation':scopes['pairs'].add(('x','time'))
        if label=='missing_pair':scopes['pairs']=set()
        if label=='empty_left':scopes['left']=set();mm=m|{'ei3a':lambda ctx:False}
        if label=='wrong_context':args[-1]='context'
        if label=='no_current_correspondence':mm=m|{'ei3a':lambda ctx:False}
        assert run('ei7m',args,mm,domain=RECORDS)==(label=='baseline'),label;count+=1;args[-1]='other'
    coords['y']=list(map(Q,(2,1,3,1)));coords['z']=result(coords['x']);coords['time']=result(coords['y'])
    scopes.update(left={'x','y'},right={'z','time'},pairs={('x','z'),('y','time')})
    assert run('ei7m',args,m,domain=RECORDS);count+=1
    for slot in range(4):
        coords['time'][slot]+=1;assert not run('ei7m',args,m,domain=RECORDS);coords['time'][slot]-=1;count+=1
    unknowns(lambda mm:run('ei7m',args,mm,domain=RECORDS),m,('ei3a','ei26','ei27','zc6','ba','sca'))
    rows={'ei7m':{(Q(4),Q(1),Q(2),Q(3),'other')}}
    norm=lambda xs:tuple(x if isinstance(x,str) else cuts.read(x) for x in xs)
    mm=m|{'ei7m':lambda *xs:norm(xs) in rows['ei7m']}
    count+=perturb(lambda mm:run('ei7n',['other',*args[:4]],mm,'instance'),mm,rows,norm)
    for slot in range(4):
        bad=['other',*args[:4]];bad[slot+1]=cuts.make(Q(9));assert not run('ei7n',bad,mm,'instance');count+=1
    try:run('ei7n',['other'],m)
    except ValueError as error:assert 'Cannot finitely quantify' in str(error)
    else:raise AssertionError('Four real constants sampled')
    return dict(cases=count,full_pair_body_two_inputs_and_alias_checked=True,common_four_constants_outside_all_pairs=True,current_measurement_scope_is_a_separately_checked_boundary=True,real_constant_existence_refused=True)

@lru_cache(None)
def context_checks():
    count=0
    rows={'eiyx':{('event','first','rest','other'),('event','second','moving','other')},'zc4':{('event',)}}
    m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ei26',['first','second','other'],mm),m,rows)
    for frame,record in (('rest','first'),('moving','second')):
        local={'eiyx':{('event',record,frame,'other')},'zc4':{('event',)}};mm={n:relation(rs) for n,rs in local.items()}
        count+=perturb(lambda mm:run('ei27',[record,frame,'other'],mm),mm,local)
    assert not run('ei26',['first','second','context'],m);count+=1
    assert not run('ei26',['first','second','other'],m|{'zc4':lambda e:e in ('event','other_event'),'eiyx':relation({('event','first','rest','other'),('other_event','second','moving','other')})});count+=1
    for ctx in ('context','other'):
        local={'zfn':{(ctx,)},'zfo':{('stage',ctx)}};mm={n:relation(rs) for n,rs in local.items()}|{'joccpoint':lambda ctx=ctx:ctx}
        count+=perturb(lambda mm:run('sqa',[],mm),mm,local)
        count+=perturb(lambda mm:run('ei7o',[],mm),{'ei7n':relation({(ctx,)}),'joccpoint':lambda ctx=ctx:ctx},{'ei7n':{(ctx,)}})
    return dict(cases=count,same_current_event_frame_and_supplied_context_checked=True,nonadoption_not_origin_inequality=True,conclusion_uses_evaluation_context=True)

def uncertainty_model():
    cuts,m,coords,scopes,result,seen=previous_model();c=cuts.make;r=cuts.read
    def family(stage):
        if stage not in SITUATIONS:forbidden()
        return FunctionValue((RS,),RS,lambda speed:c(Q(2)+(r(speed)-3)**2 if stage=='other' else Q(2)))
    fam=FunctionValue(('situation',),dict(kind='function',parameters=[RS],result=RS),family)
    alternatives=lambda agent,stage,alt:agent=='agent' and stage=='stage' and alt in ('stage','other')
    m|={'zer':lambda:fam,'zet':alternatives}
    return cuts,m

def captured(name,m):
    out=[];assert run(name,[],m|{'joccapture':lambda value:out.append(value) is None});assert len(out)==1;return out[0]

@lru_cache(None)
def uncertainty_checks():
    cuts,m=uncertainty_model();c=cuts.make;r=cuts.read;count=0
    for speed,expected in ((3,False),(4,True),(0,True),(-3,False)):
        assert run('sqe',['stage','other',c(Q(speed))],m)==expected;count+=1
        for symbol,callback in (('zet',lambda *xs:False),('zfm',lambda:'context')):
            assert not run('sqe',['stage','other',c(Q(speed))],m|{symbol:callback});count+=1
        assert run('sqf',[c(Q(speed))],m);count+=1
        wrong=m|{'zeq':lambda:FunctionValue((RS,),RS,lambda v:c(Q(7)))}
        assert not run('sqf',[c(Q(speed))],wrong);count+=1
    family=captured('sqc',m);coefficient=captured('spc',m)
    domain=FunctionValue((RS,),'truth',lambda x:0<=r(x)<5);same=FunctionValue((RS,RS),'truth',lambda a,b:r(a)==r(b))
    alt=FunctionValue(('individual','situation','situation'),'truth',m['zet'])
    for speed in (0,3,4):
        assert run('smq',[coefficient,family,'stage',domain,c(Q(speed))],m,'instance');count+=1
        assert run('smq',[coefficient,family,'other',domain,c(Q(speed))],m,'instance')==(speed==3);count+=1
        assert run('smb',['agent','stage',domain,alt,family,same,'stage','other',c(Q(speed))],m,'instance')==(speed!=3);count+=1
    def fingerprint(f):return tuple(tuple(r(f(ctx)(c(Q(v)))) for v in (0,3,4)) for ctx in SITUATIONS)
    def one(f):return tuple(r(f(c(Q(v)))) for v in (0,3,4))
    def scope(f):return tuple(f(c(Q(v))) for v in (-3,0,3,4,5))
    expected_family=fingerprint(family);expected_current=one(coefficient)
    m|={'smq':lambda f,fam,stage,dom:one(f)==expected_current and fingerprint(fam)==expected_family and stage=='stage' and scope(dom)==(False,True,True,True,False),
        'smb':lambda agent,stage,dom,alternatives,fam,same:agent=='agent' and stage=='stage' and scope(dom)==(False,True,True,True,False) and alternatives(agent,stage,'stage') and alternatives(agent,stage,'other') and fingerprint(fam)==expected_family and same(c(Q(2)),c(Q(2))) and not same(c(Q(2)),c(Q(3)))}
    for ctx in SITUATIONS:
        assert run('sqd',[ctx,c(Q(3))],m,'instance');count+=1
    for symbol in ('smq','smb'):
        assert not run('sqd',['other',c(Q(3))],m|{symbol:lambda *xs:False},'instance');count+=1
    assert not run('sqd',['other',c(Q(3))],m|{'zet':lambda a,s,t:t=='other'},'instance');count+=1
    unknowns(lambda mm:run('sqd',['other',c(Q(3))],mm,'instance'),m,('zer','zet','zeq','smq','smb','tc','sky'))
    try:run('sqd',[],m)
    except ValueError as error:assert 'Cannot finitely quantify' in str(error)
    else:raise AssertionError('Whole candidate functions sampled')
    return dict(cases=count,normalized_family_and_same_current_stage_speed_checked=True,agreement_at_one_speed_not_function_identity=True,native_witness_and_current_membership_checked=True,real_function_scope_refused=True,finite_function_fingerprints_only_at_explicit_boundaries=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ei7p',{'uh':{('unknown','author','sqd','section','discourse')}}),('ei7s',{'zc':{('constants','author','sqa','ei7o','section','discourse')}})]
    for body,message,author,node,previous in GROUPS:rows.append((author,{'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    count=0
    for name,relations in rows:
        m={n:relation(rs) for n,rs in relations.items()};count+=perturb(lambda mm:run(name,[],mm),m,relations)
        assert run(name,[],m|{n:forbidden for n in ('sqd','sqa','ei7o','spu','ei7n')});count+=1
    return dict(cases=count,unknown_function_and_conditional_consequence_distinct=True,same_author_paper_section_and_beta_order=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};u=inv['units'][84]
    assert u['id']=='einstein-1905:u0085' and u['text_sha256']=='b535ff072428fe122e7bd1948027a3d49d43ce3e9be5a1e2c97dae869dbd1806'
    readings={'M0137':'φ','M0138':'v','M0139':'τ'}
    for mid,flat in readings.items():assert ''.join(ET.fromstring(math[mid]['mathml']).itertext())==flat
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']])
    retrieval='artifacts/einstein-longitudinal-elimination-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']})
    paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-origin-constants-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['900'],segments=[segment],observations=['原刊900頁のβの式に続くund φからzuzufügenまで、二文全体を前後とともに通読した。','φはvorläufig unbekannte Funktion von vとされる。現在段階で異なる候補が残る読みを明示し、既出の正規化後の同じφへ接続する。','Anfangslageは運動系の初期空間位置、Nullpunktはτの零点。keinerlei Voraussetzungはこれらの仮定を採らないという条件であり、零点の不一致を断定しない。','rechten Seiten dieser Gleichungen je eineは直前の四式の各右辺への一つずつの加法定数。全記録対で共有する独立な四定数と読む。','原刊の改行は一つの条件文の途中にあり、固定本文の二文構成を変更しない。次のWir haben nun zu beweisenは後続単位である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==304
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[300,301])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    selected=extract_document(doc,roots=['ei7o'],statement_indices=[])
    assert not set(selected.retained_symbols)&{'shd','spv','spw','spx','spy','spz','zb6','ei46','ei4l'}
    assert {'spu','ei26','ei27','ei3a','eiyx'}<=set(selected.retained_symbols)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,existing_contextual_measurement_definitions_reused=True,zero_origin_and_old_measurements_not_reintroduced=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('scope',graph_checks),('context',context_checks),('uncertainty',uncertainty_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_origin_constants_claim.py','scripts/check_origin_constants_claim.py','tests/test_origin_constants_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_translated_light_trial.py','scripts/compose_origin_constants.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_origin_constants_and_normalized_uncertainty_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0085の全文通読判断登録','u0086以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
