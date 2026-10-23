"""Check exact point-pair distances and unsampled all-time rigidity guards."""
from copy import deepcopy
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
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.compose_rigid_body_kinematics import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,MEANINGS,PRIMITIVES,build

DOC='docs/rigid-body-kinematics-v1.md';SOURCE='data/einstein-kinematics-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/einstein-principles-paragraph-review-v1.json')
DOMAIN=('body','frame','length','timeunit','p','q','r','other');POINTS=('context','other')
NUM={'ba','bb','bc','bd','bf','shv','sca','zzba','zzbc'}
def forbidden(*args):raise ValueError('Unknown rigidity input')

def local_body(doc):
    d=deepcopy(next(d for d in doc['declarations'] if d['name']=='eigy'));d['name']='jrbtest'
    tail=d['body']['arguments'][1]['arguments'];node=tail[1];quantified=[]
    while node['kind']=='forall':quantified.append(dict(name=node['variable'],sort=node['sort']));node=node['body']
    assert [p['sort'] for p in quantified]==['individual','individual',RS,RS]
    assert len(quantified)==4
    d['parameters']+=quantified;tail[1]=node;doc['declarations'].append(d)
    return 'jrbtest'

@lru_cache(None)
def fixture(name):
    root='eigy' if name=='local_body' else name
    doc=extract_document(parse(read(CORE)),roots=[root],statement_indices=[]).document
    abstract(doc,NUM|{'eiad'})
    if name=='local_body':name=local_body(doc)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrb'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jrbcapture',parameters=[d['result']],result='truth'))
        body=dict(kind='call',symbol='jrbcapture',arguments=[body])
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,values,model):
    doc,slots=fixture(name);assert len(values)==len(slots);m=dict(model);captured=[]
    for (n,s),x in zip(slots,values):
        if isinstance(s,dict) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        m[n]=lambda x=x:x
    def capture(x):captured.append(x);return True
    m['jrbcapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']
    return captured[0] if captured else result

BASE={'p':(0,0,0),'q':(2,0,0),'r':(1,1,0),'other':(7,8,9)}
def position(profile,point,t):
    xyz=tuple(map(Q,BASE.get(point,(7,8,9))))
    if profile=='translation':return tuple(x+s*t for x,s in zip(xyz,(1,2,-1)))
    if profile=='rotation':
        c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);x,y,z=xyz;return (c*x-s*y,s*x+c*y,z)
    if profile=='stretch':return tuple(x*(1+t) for x in xyz)
    if profile=='return_stretch':return tuple(x*(1+t*(2-t)) for x in xyz)
    if profile=='third_point' and point=='r':return (xyz[0],xyz[1],t)
    return xyz

def setup(profile='rest',members=('p','q','r')):
    cuts,m=arithmetic();r=cuts.read
    families=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:cuts.make(position(profile,p,r(t))[i]))) for i in range(3)]
    args=['body','frame','context','length','timeunit',cuts.make(Q(0)),cuts.make(Q(2)),FunctionValue(('individual',),'truth',lambda p:p in members),*families]
    def history(*xs):
        return xs[:5]==tuple(args[:5]) and r(xs[5])==0 and r(xs[6])==2 and all(xs[7](p)==(p in members) for p in DOMAIN) and all(
            r(xs[8+i](p)(cuts.make(t)))==position(profile,p,Q(t))[i] for i in range(3) for p in members for t in (0,1,2))
    m.update(eiad=history,eisdd=lambda f,l,t,c:(f,l,t,c)==('frame','length','timeunit','context'))
    return cuts,m,args,families

@lru_cache(None)
def pair_checks():
    count=0
    for profile in ('rest','translation','rotation','stretch','third_point','return_stretch'):
        cuts,m,_,families=setup(profile)
        for left,right in product(('p','q','r'),repeat=2):
            for first,second in ((0,1),(0,2),(1,2),(2,0),(1,1),(Q(1,3),Q(5,4))):
                ds=lambda t:sum((a-b)**2 for a,b in zip(position(profile,left,Q(t)),position(profile,right,Q(t))))
                assert cuts.read(run('eigw',[left,right,cuts.make(Q(first)),*families],m))==ds(first)
                assert run('eigx',[left,right,cuts.make(Q(first)),cuts.make(Q(second)),*families],m)==(ds(first)==ds(second));count+=2
    cuts,m,_,families=setup('third_point')
    assert run('eigx',['p','q',cuts.make(Q(0)),cuts.make(Q(1)),*families],m)
    assert not run('eigx',['p','r',cuts.make(Q(0)),cuts.make(Q(1)),*families],m)
    cuts,m,_,families=setup('return_stretch')
    assert run('eigx',['p','q',cuts.make(Q(0)),cuts.make(Q(2)),*families],m)
    assert not run('eigx',['p','q',cuts.make(Q(0)),cuts.make(Q(1)),*families],m)
    return dict(cases=count,translation_and_rotation_preserve_local_distances=True,stretch_and_hidden_third_point_deformation_detected=True,endpoint_agreement_not_whole_interval=True,no_three_noncollinear_marks_required=True)

@lru_cache(None)
def guard_and_binding_checks():
    count=0
    for profile,members in product(('rest','third_point'),(('p','q'),('p','q','r'))):
        cuts,m,args,families=setup(profile,members)
        for left,right in product(('p','q','r'),repeat=2):
            for first,second in ((0,1),(0,2),(-1,1),(1,3)):
                inside=left in members and right in members and 0<=first<=2 and 0<=second<=2
                ds=lambda t:sum((a-b)**2 for a,b in zip(position(profile,left,Q(t)),position(profile,right,Q(t))))
                expected=not inside or ds(first)==ds(second)
                assert run('local_body',args+[left,right,cuts.make(Q(first)),cuts.make(Q(second))],m)==expected;count+=1
    cuts,m,args,families=setup();values=args+['p','q',cuts.make(Q(0)),cuts.make(Q(1))]
    for slot in range(7):
        bad=list(values);bad[slot]='other' if slot<5 else cuts.make(Q(9))
        assert not run('local_body',bad,m);count+=1
    for slot in range(4):
        def metrology(*xs,slot=slot):return xs[slot]=='other'
        assert not run('local_body',values,m|{'eisdd':metrology});count+=1
    for name in ('eiad','eisdd'):
        assert not run('local_body',values,m|{name:lambda *xs:False});count+=1
        try:run('local_body',values,m|{name:forbidden})
        except ValueError as e:assert 'Unknown rigidity' in str(e)
        else:raise AssertionError('Unknown whole-history or metrology input accepted')
    # Reject altered complete-population or coordinate-family inputs at the history boundary.
    cuts,m,args,families=setup('third_point');values=args+['p','r',cuts.make(Q(0)),cuts.make(Q(1))]
    assert not run('local_body',values,m)
    for slot in range(7,11):
        bad=list(values)
        bad[slot]=FunctionValue(('individual',),'truth',lambda p:False) if slot==7 else families[(slot-8+1)%3]
        assert not run('local_body',bad,m);count+=1
    for name in ('ba','bf','shv','bd','sca'):
        try:run('eigx',['p','r',cuts.make(Q(0)),cuts.make(Q(1)),*families],m|{name:forbidden})
        except ValueError as e:assert 'Unknown rigidity' in str(e)
        else:raise AssertionError('Unknown numerical input accepted')
    return dict(cases=count,same_members_pair_interval_frame_and_units=True,complete_history_and_fixed_metric_required=True,instantiated_guards_not_sampled_universal_proof=True,unknown_inputs_rejected=7)

@lru_cache(None)
def domain_checks():
    cuts,m,args,families=setup()
    try:run('eigy',args,m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('All real time pairs were finitely sampled')
    unknown=FunctionValue(('number',),'truth',lambda x:x<1)
    try:run('eigx',['p','q',unknown,cuts.make(Q(1)),*families],m)
    except ValueError:pass
    else:raise AssertionError('Unknown real cut decoded from probes')
    # The universal body binds both members and both real times, without additional anchor points.
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};body=deepcopy(ds['eigy'])
    node=body['body']['arguments'][1]['arguments'][1];sorts=[]
    while node['kind']=='forall':sorts.append(node['sort']);node=node['body']
    assert sorts==['individual','individual',RS,RS] and node['kind']=='implies'
    assert len(ds['eigy']['parameters'])==len(FIELDS)==11
    return dict(full_real_time_domain_refused=True,unknown_cut_refused=True,all_two_point_two_time_quantifiers_preserved=True)

def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][4];assert u['id']=='einstein-1905:u0005' and len(u['text'])==423 and not u['math_ids']
    spans=((0,260),(261,423));paths={INVENTORY,DOC,'scripts/check_rigid_body_kinematics.py','artifacts/einstein-principles-v1/retrieval.json','artifacts/written-sources-v1/einstein-1905.html'}
    for row in json.loads(read('artifacts/einstein-principles-v1/retrieval.json'))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-kinematics-source-reading-v1',reviewer='assistant_visual_and_text_review',source_unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],source_nonblank_characters=369,pages=['892'],images=['artifacts/einstein-principles-v1/page-892.jpg'],sentence_ranges=[dict(range=[a,b],text=u['text'][a:b],nonblank_characters=sum(not c.isspace() for c in u['text'][a:b])) for a,b in spans],math=[],observations=[
        '原刊892頁中段のDie zu entwickelnde Theorieからzu kämpfen hat.までの二文を視認し、固定転記と照合した。',
        'wie jede andere Elektrodynamikはダッシュに挟まれる比較である。starre Körperの括弧はKoordinatensystemen。時計と電磁過程も同じ列挙に含まれる。',
        '第一文のdaは理由、第二文のdieses Umstandesは同じ事情を指す。gegenwärtigは論説の当時と読む。',
        '段落の直後のI. Kinematischer Teil.と§1見出しは別単位である。本段落に数式・著者脚注はない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==217
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=217,prior_reviews_preserved=True,no_new_author_assertion=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(pairs=pair_checks(),guards=guard_and_binding_checks(),domains=domain_checks(),structure=structure_checks())
    u=json.loads(read(INVENTORY))['units'][4];segments=[]
    for phrase in ('starren Körpers','starren Körpern'):
        a=u['text'].index(phrase);span=[a,a+len(phrase)]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=span,source=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,
        'scripts/compose_rigid_body_kinematics.py','scripts/check_rigid_body_kinematics.py','tests/test_rigid_body_kinematics.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_ether_dispensability.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='all_material_pair_rigidity_composed_discourse_pending',document=FULL,**results,alignment=dict(segments=segments),remaining=['剛体の運動学を理論の基礎とする関係','全理論の主張と剛体（座標系）・時計・電磁過程の関係','第一文の比較・理由・将来の理論への接続','第二文の考慮不足と当時の困難','第三段落全体の意味判断'],verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
