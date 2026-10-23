"""Check time independence, full-frame rest, current identity and attributed inference."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_four_coordinate_claim import model as previous_model,RS
from scripts.check_first_principle import frame_model,DOMAIN as FRAME_DOMAIN,POINTS as FRAME_POINTS
from scripts.compose_reciprocal_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/reciprocal-claim-v1.md';SOURCE='data/einstein-reciprocal-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-third-frame-claim-u0093-review-v1.json'
DEPENDENCIES=('reports/third-frame-geometry-v1.json','reports/third-frame-claim-v1.json','reports/first-principle-v1.json','reports/reverse-transform-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','ra':'K','zbm':'k','zgi':'third','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zb6':'context','zgp':'previous','zgq':'rest','zgr':'identity','zgs':'reciprocal'}
DOMAIN=tuple(dict.fromkeys((*[x for n,x in CONSTANTS.items() if n not in ('ri','zb6')],'other')));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    if name=='ejbq' and mode!='native':bounds.add('eioj')
    if name in ('ejbs','ejbu'):bounds|={'eja4','eja5','ejbr','ejbk','shh','srh'}
    if name=='ejbt':bounds.add('ejbq')
    if name=='ejbv':bounds|={'ejbk','ejbu'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrcp'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrcppoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrcppoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m,domain=DOMAIN,points=POINTS,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jrcppoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=points,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def numeric_checks():
    count=0
    for plus,minus,origin in ((2,Q(1,2),False),(-2,Q(-1,2),False),(2,3,False),(2,3,True)):
        cuts,m,coords,*_=previous_model();c=cuts.make;r=cuts.read;scale=Q(plus)*Q(minus)
        m['zeq']=lambda:FunctionValue((RS,),RS,lambda speed:c(Q(plus if r(speed)==3 else minus)/Q(5,4)) if r(speed) in (3,-3) else forbidden())
        if origin:coords['x']=[Q(0)]*4
        coords['z']=[scale*x for x in coords['x']];coords['time']=coords['z'].copy()
        assert run('ejbr',['x','z',c(scale)],m);count+=1
        # shh quantifies roles eagerly; use exactly the four declared roles,
        # rather than inventing coordinate values for discourse/frame objects.
        assert run('shh',['x','z'],m,('x','y','z','time'))==(scale==1 or origin);count+=1
        assert run('shh',['z','time'],m,('x','y','z','time'));count+=1
        assert run('sro',[],m)==(scale==1);count+=1
        for record in ('x','z'):
            saved=coords[record][3]
            for time in (-17,0,23):
                coords[record][3]=Q(time);assert run('ejbr',['x','z',c(scale)],m);count+=1
            coords[record][3]=saved
        for slot in range(4):
            coords['time'][slot]+=1;assert not run('shh',['z','time'],m,('x','y','z','time'));coords['time'][slot]-=1;count+=1
        for slot in range(3):
            coords['z'][slot]+=1;assert not run('ejbr',['x','z',c(scale)],m);coords['z'][slot]-=1;count+=1
        unknowns(lambda mm:run('ejbr',['x','z',c(scale)],mm),m,('zc5','zc6','shv','ba','sca'))
        unknowns(lambda mm:run('sro',[],mm),m,('tc','zb7','zeq','sky','ba','sca'))
    return dict(cases=count,all_three_spatial_outputs_independent_of_both_record_times=True,identity_checks_all_four_values_and_allows_alias_records=True,reciprocity_not_each_phi_one_or_origin_identity=True)


@lru_cache(None)
def rest_checks():
    cuts,m,*_=previous_model();c=cuts.make;count=0
    rows={'eioj':{('K','third','length','duration','context')}}
    speeds={('K','third','length','duration',axis,'context'):Q(0) for axis in ('x','y','z')}
    m|={n:relation(rs) for n,rs in rows.items()};m['eislc']=lambda *xs:c(speeds[xs]) if xs in speeds else forbidden()
    check=lambda mm:run('ejbq',['K','third','context'],mm)
    count+=perturb(check,m,rows)
    for key in speeds:
        for value in (-3,2):speeds[key]=Q(value);assert not check(m);count+=1
        speeds[key]=Q(0)
    unknowns(check,m,('eislc',))
    # Native eioj: every fixed placement and every comparison moment, not just the origin.
    cuts,m,_=frame_model(speed=(0,0,0));c=cuts.make;r=cuts.read;m|={'ta':lambda:'e','rb':lambda:'f','bg':lambda a,b:r(a)<r(b)}
    check=lambda mm:run('ejbq',['a','b','now'],mm,FRAME_DOMAIN,FRAME_POINTS,'native')
    assert check(m);count+=1
    old=m['ym']
    for axis in ('a','b','c'):
        def moving(*xs,axis=axis):
            return c(r(old(*xs))+(1 if xs==('b','d','a','e',axis,'now') else 0))
        assert not check(m|{'ym':moving});count+=1
    for missing in ('eisk7','eisla','eislb','zce','zcf'):
        assert not check(m|{missing:lambda *xs:False});count+=1
    rows={'ejbq':{('K','third','context'),('third','K','context')}}
    count+=perturb(lambda mm:run('ejbt',[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,zero_in_every_component_and_both_frame_directions=True,native_all_placements_all_moments_and_availability_required=True)


@lru_cache(None)
def scope_checks():
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read;count=0;small=('a','b','c')
    m|={'ra':lambda:'a','zbm':lambda:'b','zgi':lambda:'c'}
    for row in product(('a','b'),repeat=4):
        selected=(*row,'context')
        base=m|{'ejbk':lambda:Content(POINTS,(False,True,False)),'eja5':lambda ctx:ctx=='context','eja4':lambda *xs,selected=selected:xs==selected,'ejbr':lambda a,b,scale,row=row:(a,b)==(row[1],row[3]) and r(scale)==6,'srh':lambda:c(Q(6)),'shh':lambda a,b,row=row:(a,b)==(row[1],row[3])}
        for name,relation_name in (('ejbs','ejbr'),('ejbu','shh')):
            assert run(name,[],base,small);count+=1
            assert not run(name,[],base|{relation_name:lambda *xs:False},small);count+=1
            assert not run(name,[],base|{'zgi':lambda:'a'},small);count+=1
        assert not run('ejbs',[],base|{'ejbk':lambda:Content(POINTS,(True,False,True))},small);count+=1
        assert not run('ejbu',[],base|{'eja5':lambda ctx:False},small);count+=1
    for bits in product((False,True),repeat=2):
        m={n:lambda on=on:Content(POINTS,(False,on,False)) for n,on in zip(('ejbk','ejbu'),bits)}
        assert run('ejbv',[],m,small)==all(bits);count+=1
    return dict(cases=count,current_nonempty_three_record_scope_and_all_four_tuple_slots=True,identity_requires_record_existence_and_distinct_frames=True,premise_is_current_chains_and_identity_without_extra_witness=True)


@lru_cache(None)
def presentation_checks():
    count=0
    for name,node,before,after in (('ejbw','rest','ejbs','ejbt'),('ejbx','identity','ejbt','ejbu'),('ejby','reciprocal','ejbv','sro')):
        rows={'zc':{(node,'author',before,after,'section','discourse')}}
        if name=='ejbx':rows['zdg']={(node,'author',after,'section','discourse')}
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in (before,after,'sro','ejbk','eioj','shh')});count+=1
    for name,node,previous,message in (('ejb2','rest','previous','ejbz'),('ejb4','identity','rest','ejb3'),('ejb6','reciprocal','identity','ejb5')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}}
        count+=perturb(lambda mm:run(name,[],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,three_ordered_inferences_and_same_identity_obviousness=True,necessity_is_author_attribution_not_checker_proof=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    expected={'M0162':'x′,y′,z′','M0163':'x,y,z','M0164':'t','M0165':'K','M0166':'K′','M0167':'K','M0168':'K′','M0169':'φ(v)φ(−v)=1'}
    for i,sha in ((94,'4bb7b78603e9658bafa8852cd3257339aff4e7d7c370ae6374daaf0449ef2b5d'),(95,'e8f2d073881ee4ef444daccf08b5c2105ce1f96bc05bbd40909e06d68b10615e')):
        u=inv['units'][i];assert u['text_sha256']==sha;elements=[]
        for n in u['math_ids']:
            flat=''.join(ET.fromstring(math[n]['mathml']).itertext());assert flat==expected[n]
            elements.append(dict(id=n,sha256=math[n]['sha256'],reading=flat))
        segments.append(dict(unit=u['id'],unit_sha256=sha,range=[0,len(u['text'])],text=u['text'],math=elements,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    paths={DOC,INVENTORY}
    for retrieval in ('artifacts/einstein-light-proof-task-v1/retrieval.json','artifacts/einstein-reciprocal-claim-v1/retrieval.json'):
        saved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in saved['sources']});paths|={retrieval,*(r['path'] for r in saved['sources'])}
    return dict(version='einstein-reciprocal-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901','902'],segments=segments,observations=['901頁末のDa die Beziehungenから相互静止の結論を読み、902頁冒頭のund es ist klarから恒等変換の必要性、Es ist alsoと積1の表示・句点まで照合した。','M0162直後に固定本文では空白がないが、原刊のundと二組の三位置座標の対応は同じ。固定本文は変更しない。','時間tを含まないのは前の四連鎖等式の最終三位置関係。時間変換式を削除することや、全座標が不変であるという結論そのものではない。','KとK′が互いに静止することと、K→K′が恒等変換でなければならないという明白さを伴う推論を分ける。','積1は同じφ(v)とφ(−v)の積である。後続でφの意味を問う段落と棒の長さの議論へ進む前の結論として読む。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==315
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[310,311])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    spatial=extract_document(doc,roots=['ejbr'],statement_indices=[]).document
    assert 'zc7' not in {d['name'] for d in spatial['declarations']}
    assert all(ds[n]['body']['force']=='assert' for n in ('ejbz','ejb3','ejb5'))
    assert {'eioj','eiyx','eja4','eja5','ejbk','shh','sro','spc'}<=set(ds)
    assert not set(ds)&{'shd','smk','sri','srj','srk','srn','srr','srs'}
    assert '従わなければならない' in new.entries['zc']['meaning_ja']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=312,prior_whole_unit_judgment_preserved=True,time_role_absent_from_spatial_rhs_dependencies=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('rest',rest_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_reciprocal_claim.py','scripts/check_reciprocal_claim.py','tests/test_reciprocal_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/check_first_principle.py','scripts/check_moving_trip_geometry.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES if i==0 else [INDICES[-1]]),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='time_free_relations_rest_identity_and_reciprocity_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,relative_rest_alone_proves_identity=False,remaining=['u0095–u0096の全文通読判断と登録','u0097以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
