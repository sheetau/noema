"""Check the two subject classes, current equations and fourth heading."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as body_model,DOMAIN as BODY_DOMAIN
from scripts.compose_physical_meaning_heading import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/physical-meaning-heading-v1.md';SOURCE='data/einstein-physical-meaning-heading-source-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-final-transform-u0105-review-v1.json'
DEPENDENCIES=('reports/final-transform-claim-v1.json','reports/rigid-body-kinematics-v1.json','reports/material-body-motion-v1.json','reports/moving-trip-reading-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zb6':'context','rd':'author','eirf':'paper','eisdx':'part','eisn5':'section','zht':'heading','eisn4':'previous','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),*BODY_DOMAIN,'inquiry','first','second')))
POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'se'}|{'ejes':{'eigy','eiag'},'ejet':{'ejer'},'ejeu':{'eiyz','eiy2','ssn'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'exists'},only_sort=RS))==2
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jpmh'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def motion_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,1,2));count=0
    m['zzbg']=lambda a,b:r(a)<r(b)
    for axis in range(3):
        fs=[FunctionValue((RS,),RS,lambda t,i=i:c(Q(i)+(r(t)*(2-r(t)) if i==axis else 0))) for i in range(3)]
        args=['body','K','context','length','duration',c(Q(0)),c(Q(2)),*fs]
        rows={'se':{norm(args)},'eisdd':{('K','length','duration','context')}}
        model=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
        for a,b in product((-1,0,1,2,3),repeat=2):
            expected=0<=a<b<=2 and a*(2-a)!=b*(2-b)
            assert run('ejer',args+[c(Q(a)),c(Q(b))],model,'instance')==expected;count+=1
        check=lambda mm:run('ejer',args+[c(Q(0)),c(Q(1))],mm,'instance')
        count+=perturb(check,model,rows,norm)
        for index in (0,1,2,3,4):
            bad=args[:];bad[index]='other';assert not run('ejer',bad+[c(Q(0)),c(Q(1))],model,'instance');count+=1
        for lo,hi in ((2,2),(3,2)):
            bad=args[:];bad[5:7]=[c(Q(lo)),c(Q(hi))]
            assert not run('ejer',bad+[c(Q(0)),c(Q(1))],model|{'se':lambda *xs:True},'instance');count+=1
        unknowns(check,model,('se','eisdd','bg','zzba','zzbg'))
        try:run('ejer',args,model)
        except ValueError as e:assert 'Cannot finitely quantify' in str(e) or 'Finite function domain' in str(e),str(e)
        else:raise AssertionError('Full real witness domain silently sampled')
    return dict(cases=count,returning_motion_not_only_endpoint_difference=True,each_axis_and_same_complete_history_required=True,reverse_equal_outside_times_rejected=True,native_real_quantification_refused=True)

@lru_cache(None)
def subject_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;count=0
    # Both full histories use the same body/member set; the two reference
    # frames and their time intervals are not identified.
    m|={'eisls':lambda f,u,s:c(Q(0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2 if f=='k' else 3)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislu':lambda b,f,lu,tu,a,s:fs[('x','y','z').index(a)] if b=='body' and f in ('K','k') and (lu,tu,s)==('length','duration','context') and a in ('x','y','z') else forbidden()}
    rest=fields[:];moving=fields[:];moving[1]='K';moving[6]=c(Q(3))
    rows={'eigy':{norm(rest)},'eiag':{norm(moving)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejes',['body'],mm),m,rows,norm)
    unknowns(lambda mm:run('ejes',['body'],mm),m,('eisls','eislt','eirh','eislu'))
    assert not run('ejes',['body'],m|{'ra':lambda:'k','eigy':lambda *xs:True,'eiag':lambda *xs:True});count+=1
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,1,2))
    traces=[FunctionValue((RS,),RS,lambda t,i=i:c(Q(i)+r(t))) for i in range(3)]
    expected=['body','K','context','length','duration',c(Q(0)),c(Q(2)),*traces]
    rows={'ca':{('body',)},'ejer':{norm(expected)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eismh':lambda b,f,lu,tu,a,s:traces[('x','y','z').index(a)] if (b,f,lu,tu,s)==('body','K','length','duration','context') and a in ('x','y','z') else forbidden()}
    count+=perturb(lambda mm:run('ejet',['body'],mm),m,rows,norm)
    assert run('ejet',['body'],m|{'eiag':forbidden,'eigy':forbidden,'eirh':forbidden});count+=1
    unknowns(lambda mm:run('ejet',['body'],mm),m,('eismh','eisls','eislt'))
    rows={'eiyz':{('first',)},'eiy2':{('second',)},'ssn':{('first','second')}}
    count+=perturb(lambda mm:run('ejeu',['first','second'],mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,rigidity_and_motion_use_same_body_in_distinct_frames=True,clock_representative_motion_not_internal_mechanism_motion=True,current_final_equations_and_both_record_scopes_required=True)

@lru_cache(None)
def presentation_checks():
    count=0;rows={'zhr':{('inquiry','author','ejeu',('ejes','ejet'),'section','context')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejev',['inquiry','context'],mm),m,rows)
    for props in (('ejes',),('ejet',),(),('ejes','ejes')):
        assert not run('ejev',['inquiry','context'],{'zhr':relation({('inquiry','author','ejeu',props,'section','context')})});count+=1
    assert run('ejev',['inquiry','context'],m|{n:forbidden for n in ('ejeu','ejes','ejet','ejer','se','ssn')});count+=1
    rows={'eisdv':{('heading','section','part','paper',Q(2),Q(4),'discourse')},'eisdw':{('heading','section','ejev','discourse')},'ue':{('previous','heading','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejew',[],mm),m,rows)
    for n,x in (('zht','section'),('eisn5','part'),('eisn4','heading')):
        assert not run('ejew',[],m|{p:lambda *xs:True for p in rows}|{n:lambda x=x:x});count+=1
    assert run('ejew',[],m|{n:forbidden for n in ('zhr','ejeu','ejes','ejet','se','ssn')});count+=1
    return dict(cases=count,both_subjects_and_same_obtained_equations_required=True,section_four_depth_two_parent_part_one=True,heading_not_physical_assertion_or_completed_derivation=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][108];assert u['id']=='einstein-1905:u0109'
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-physical-meaning-heading-source-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],source_nonblank_characters=len(re.sub(r'\s','',u['text'])),math=[])],observations=['原刊903頁冒頭の§4の見出しを二行とも視認し、最終四式に続く位置と本文の球の設定まで通読した。','Physikalische Bedeutungは得られた同じ方程式の物理的意味、betreffendは動く剛体と動く時計の両方への限定。具体的な収縮・時計遅れの命題を見出しから追加しない。','表示番号4と第一部内の階層深さ2を区別する。次の同階層見出しu0129により第四節の末尾をu0128と同定する。','球の後の注は原刊903頁下部の著者脚注で、固定原文u0281に対応する。球の本文・脚注の意味判断は今回の見出しとは分け、後続に残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==327
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[323,324])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eigy','eiag','eiae','eiyz','eiy2','ssn','eihq'}<=names
    assert not names&{'sta','stb','zbq','xm','eir3','uh'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=INDEX,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('motion',motion_checks),('subjects',subject_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_physical_meaning_heading.py','scripts/check_physical_meaning_heading.py','tests/test_physical_meaning_heading.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_observer_contrast.py'}
    s=source_record()['segments'][0];alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')])
    return dict(status='fourth_heading_current_equations_and_two_moving_subjects_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0109の全文通読判断と登録','u0110以降と著者脚注u0281'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
