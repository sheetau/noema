"""Check rod geometry, complete-history bindings and unsampled time domains."""
from copy import deepcopy
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
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.compose_rod_geometry import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,FIELDS,AXIS,build

DOC='docs/rod-geometry-v1.md';SOURCE='data/einstein-rod-geometry-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/einstein-second-principle-u0026-review-v1.json','data/einstein-second-principle-u0027-review-v1.json','data/einstein-second-principle-u0028-review-v1.json')
DOMAIN=('body','frame','lengthunit','timeunit','p','q','r','left','right','other');POINTS=('context','other')
NUM={'ba','bb','bc','bd','bf','shv','sca','bg','sah','zzba','zzbc'}
BASE={'p':(0,1,0),'q':(4,-1,0),'r':(2,0,1),'left':(0,0,0),'right':(4,0,0)}

def forbidden(*xs):raise ValueError('Unknown rod-geometry input')


def instantiate(d):
    """Expose every quantifier in this definition's own body as a parameter."""
    added=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='forall':
            added.append(dict(name=node['variable'],sort=node['sort']))
            return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=added
    return [p['sort'] for p in added]


@lru_cache(None)
def fixture(name,mode='local'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries={'eiad','se','eiah','eigy'}
    if name in ('eipd','eipe'):boundaries.add('eipc')
    if name=='eipg':boundaries|={'eipf','eipd'}
    if mode!='real_arithmetic':abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name)
    sorts=instantiate(d) if mode=='local' else []
    slots=[];callargs=[]
    for i,p in enumerate(d['parameters']):
        n='jrg'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        callargs.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=callargs)
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots,sorts


def run(name,values,m,mode='local'):
    doc,slots,_=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots))
    m=dict(m)
    for (n,s),x in zip(slots,values):
        if isinstance(s,dict) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        m[n]=lambda x=x:x
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=False,memoize_expressions=False)[0]['value']


def setup(profile='rest'):
    cuts,m=arithmetic();c=cuts.make;r=cuts.read
    m|={'bg':lambda a,b:r(a)<r(b),'sah':lambda a,b:c(r(a)*r(b))}
    def point(p,t):
        if p not in DOMAIN:forbidden()
        xyz=tuple(map(Q,BASE[p] if p in BASE else (7,8,9)))
        x,y,z=xyz
        if profile in ('translation','hidden','accelerating'):x+=2*t
        if profile=='hidden' and p=='r':y+=t
        if profile=='accelerating':x+=t*(2-t)
        if profile=='offset' and p in ('left','right'):y+=1
        if profile=='tilted' and p=='right':y+=1
        if profile=='collapsed' and p=='right':x=0
        return x,y,z
    tracks={(a,p):FunctionValue((RS,),RS,lambda t,a=a,p=p:c(point(p,r(t))[a])) for a in range(3) for p in DOMAIN}
    def track(a,p):
        if (a,p) not in tracks:forbidden()
        return tracks[a,p]
    families=[FunctionValue(('individual',),FS,lambda p,a=a:track(a,p)) for a in range(3)]
    members=FunctionValue(('individual',),'truth',lambda p:p in ('p','q','r'))
    fields=['body','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2)),members,*families]
    axis=fields+['left','right']
    def same(xs,ys):
        if len(xs)!=len(ys):return False
        def equal(x,y):
            if not isinstance(x,FunctionValue):return x==y
            if x.parameters==('number',):return r(x)==r(y)
            # Explicit finite interpretation of a history boundary, not a proof
            # of extensional function equality or completeness of a real history.
            if x.parameters==('individual',) and x.result=='truth':return all(x(p)==y(p) for p in DOMAIN)
            if x.parameters==('individual',) and x.result==FS:
                return all(r(x(p)(c(Q(t))))==r(y(p)(c(Q(t)))) for p in DOMAIN for t in (0,1,2))
            forbidden()
        return all(equal(x,y) for x,y in zip(xs,ys))
    def history(*xs):return same(xs,fields)
    def trajectory(*xs):
        p=xs[0]
        return p in ('left','right') and same(xs[1:7],fields[1:7]) and all(xs[7+a] is tracks[a,p] for a in range(3))
    m|={'eiad':history,'eiah':history,'eigy':history,'eipc':lambda *xs:same(xs,axis),'eipd':lambda *xs:same(xs,axis),'eipf':lambda *xs:same(xs,fields+[c(Q(2))]),'se':trajectory,'eisdd':lambda *xs:xs==('frame','lengthunit','timeunit','context'),'eislq':lambda *xs:same(xs,fields[:7]+['left','right'])}
    return cuts,m,fields,axis,families,point


def unknowns(check,m,names):
    for name in names:
        try:check(m|{name:forbidden})
        except ValueError as e:assert 'Unknown rod-geometry' in str(e)
        else:raise AssertionError(('Unknown input accepted',name))


@lru_cache(None)
def axis_checks():
    cuts,m,fields,axis,families,point=setup();c=cuts.make;count=0
    for a,b in product((-4,0,4),repeat=2):
        for yz in ((0,0,0,0),(1,0,1,0),(0,1,0,1),(0,0,1,0)):
            ax,az,bx,bz=yz
            vals=(a,ax,az,b,bx,bz)
            assert run('eio7',[c(Q(x)) for x in vals],m)==(a!=b and yz==(0,0,0,0));count+=1
    for profile in ('rest','translation','offset','tilted','collapsed'):
        cuts,m,fields,axis,families,point=setup(profile);c=cuts.make
        for t in (Q(0),Q(1,3),Q(2)):
            for ends in (('left','right'),('right','left')):
                assert run('eipb',[*ends,c(t),*families],m)==(profile in ('rest','translation'));count+=1
                ds=sum((a-b)**2 for a,b in zip(point(ends[0],t),point(ends[1],t)))
                for length in (-4,0,3,4,5):
                    assert run('eipa',[*ends,c(t),*families,c(Q(length))],m)==(length>0 and length*length==ds);count+=1
    cuts,m,fields,axis,families,point=setup()
    unknowns(lambda mm:run('eipa',['left','right',cuts.make(Q(1)),*families,cuts.make(Q(4))],mm),m,('ba','bg','bf','bd','shv','sca'))
    return dict(cases=count,axis_on_line_not_merely_parallel=True,reversed_end_labels_allowed=True,positive_length_not_squared_sign_ambiguity=True,finite_thickness_not_rejected=True)


@lru_cache(None)
def motion_checks():
    count=0
    for profile in ('rest','translation','hidden','accelerating'):
        cuts,m,fields,axis,families,point=setup(profile);c=cuts.make
        for p in ('p','q','r','other'):
            for first,second in ((0,1),(0,2),(1,2),(1,1),(2,0),(-1,1),(1,3)):
                selected=p in ('p','q','r') and 0<=first<=2 and 0<=second<=2 and first<=second
                before=point(p,Q(first));after=point(p,Q(second))
                numeric=after[0]-before[0]==2*(second-first) and after[1:]==before[1:]
                assert run('eipf',fields+[c(Q(2)),p,c(Q(first)),c(Q(second))],m)==(not selected or numeric);count+=1
    cuts,m,fields,axis,families,point=setup('translation');c=cuts.make
    for speed in (-2,0,1,2,3):
        assert run('eipf',fields+[c(Q(speed)),'r',c(Q(0)),c(Q(1))],m)==(speed==2);count+=1
    for lower,upper in ((0,0),(2,0)):
        narrowed=list(fields);narrowed[5:7]=[c(Q(lower)),c(Q(upper))]
        assert not run('eipf',narrowed+[c(Q(2)),'p',c(Q(0)),c(Q(0))],m|{'eiad':lambda *xs:True});count+=1
    unknowns(lambda mm:run('eipf',fields+[c(Q(2)),'r',c(Q(0)),c(Q(1))],mm),m,('eiad','eisdd','bg','bc','sah','bf'))
    # The same endpoint displacement can conceal an excursion or internal deformation.
    cuts,m,fields,axis,_,_=setup('accelerating');c=cuts.make
    assert run('eipf',fields+[c(Q(2)),'p',c(Q(0)),c(Q(2))],m)
    assert not run('eipf',fields+[c(Q(2)),'p',c(Q(0)),c(Q(1))],m)
    cuts,m,fields,axis,_,_=setup('hidden');c=cuts.make
    assert run('eipf',fields+[c(Q(2)),'p',c(Q(0)),c(Q(1))],m)
    assert not run('eipf',fields+[c(Q(2)),'r',c(Q(0)),c(Q(1))],m)
    return dict(cases=count+4,all_material_members_and_time_pairs=True,internal_deformation_and_acceleration_distinguished=True,positive_speed_and_nonzero_interval=True)


@lru_cache(None)
def history_checks():
    cuts,m,fields,axis,families,point=setup();c=cuts.make;count=0
    check=lambda mm:run('eipc',axis+[c(Q(1))],mm)
    assert check(m);count+=1
    for n in ('eiad','eisdd','eislq','se'):
        assert not check(m|{n:lambda *xs:False});count+=1
    unknowns(check,m,('eiad','eisdd','eislq','se'))
    # Each outer argument must reach the same physical history/axis boundary.
    for slot in range(len(axis)):
        bad=list(axis)
        if slot in (5,6):bad[slot]=c(Q(9))
        elif slot==7:bad[slot]=FunctionValue(('individual',),'truth',lambda p:False)
        elif slot in (8,9,10):bad[slot]=families[(slot-8+1)%3]
        else:bad[slot]='other'
        assert not run('eipc',bad+[c(Q(1))],m);count+=1
    # Check trajectory arguments independently of the full-history gate.
    seen=[]
    def observe(*xs):seen.append(xs);return m['se'](*xs)
    assert check(m|{'se':observe}) and len(seen)==2
    assert [x[0] for x in seen]==['left','right']
    for xs in seen:
        assert xs[1:5]==tuple(fields[1:5])
        assert [cuts.read(x) for x in xs[5:7]]==[Q(0),Q(2)]
        assert all(xs[7+i] is families[i](xs[0]) for i in range(3))
    for profile in ('rest','offset','tilted','collapsed'):
        cuts,mm,ff,aa,_,_=setup(profile);cc=cuts.make
        assert run('eipc',aa+[cc(Q(1))],mm)==(profile!='collapsed');count+=1
        assert run('eipd',aa+[cc(Q(1))],mm)==(profile=='rest');count+=1
    cuts,m,fields,axis,families,_=setup();c=cuts.make
    assert run('eipe',axis+[c(Q(4)),c(Q(1))],m)
    for n in ('eipc','eiah','eigy'):
        assert not run('eipe',axis+[c(Q(4)),c(Q(1))],m|{n:lambda *xs:False});count+=1
    assert not run('eipe',axis+[c(Q(3)),c(Q(1))],m);count+=1
    assert run('eipg',axis+[c(Q(2))],m)
    for n in ('eipf','eigy','eipd'):
        assert not run('eipg',axis+[c(Q(2))],m|{n:lambda *xs:False});count+=1
    unknowns(lambda mm:run('eipg',axis+[c(Q(2))],mm),m,('eipf','eigy','eipd'))
    return dict(cases=count,complete_history_shape_metric_and_both_axis_traces_required=True,all_outer_slots_bound=True,virtual_axis_markers_need_not_be_material=True,rest_and_motion_lengths_not_identified=True,boundary_predicates_explicitly_interpreted_not_proved=True)


@lru_cache(None)
def domain_checks():
    cuts,m,fields,axis,families,_=setup();c=cuts.make
    for n,vals in (('eipc',axis),('eipd',axis),('eipe',axis+[c(Q(4))]),('eipf',fields+[c(Q(2))])):
        try:run(n,vals,m,'whole')
        except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
        else:raise AssertionError(('All times finitely sampled',n))
    unknown=FunctionValue(('number',),'truth',lambda q:q<4)
    try:run('eipa',['left','right',c(Q(1)),*families,unknown],m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut accepted')
    try:run('eio7',[c(Q(x)) for x in (0,0,0,4,0,0)],m,'real_arithmetic')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Unbounded cut arithmetic finitely sampled')
    assert fixture('eipc')[2]==[RS]
    assert fixture('eipf')[2]==['individual',RS,RS]
    return dict(full_real_time_domains_refused=4,unknown_cut_and_unbounded_arithmetic_refused=True,local_instantiations_not_domain_replacements=True)


def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][28]
    assert u['id']=='einstein-1905:u0029' and len(u['text'])==496
    assert sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']))==395
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']}
    forms=dict(zip(('M0043','M0044','M0045','M0046','M0047'),('l','X','v','X','x')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    paths=[INVENTORY,DOC,'scripts/check_rod_geometry.py','artifacts/einstein-rest-time-v1/retrieval.json']
    for row in json.loads(read(paths[-1]))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.append(row['path'])
    return dict(version='einstein-rod-geometry-source-reading-v1',reviewer='assistant_visual_and_text_review',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,496],text=u['text'],source_nonblank_characters=395,pages=['895'],math=[dict(id=n,sha256=math[n]['sha256'],printed=s) for n,s in forms.items()],observations=['原刊895頁のEs seiから二操作を導入するコロンまでを照合した。','初期静止棒と静止物差しによるl、長軸のX軸上への配置、その後の正のx方向の速度v、運動する棒の長さへの問いの順である。','初期設定・その後の運動・二つの想定操作を区別し、移動前後の同じ長さや測定実行を補わない。'],semantic_completion=False,remaining=['同じ棒・物差し・測定値への接続','想定した操作の順序と二方法への問い','著者帰属・全文単位の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==252
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([250,251],[251],[251])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));assert not doc['statements']
    ds={d['name']:d for d in doc['declarations']}
    # The moving configuration has no initial-length parameter or reference to ya.
    def symbols(x):
        if isinstance(x,dict):return ({x['symbol']} if x.get('kind')=='call' else set())|set().union(*(symbols(v) for v in x.values()))
        if isinstance(x,list):return set().union(*(symbols(v) for v in x))
        return set()
    assert len(ds['eipg']['parameters'])==len(AXIS)+1 and symbols(ds['eipg']['body'])=={'eipf','eigy','eipd'}
    assert len(ds['eipf']['parameters'])==len(FIELDS)+1
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=252,prior_reviews_preserved=True,new_source_collation=True,no_new_author_assertion=True,whole_unit_completion=False)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('axis',axis_checks),('motion',motion_checks),('history',history_checks),('domains',domain_checks),('structure',structure_checks)]}
    source=source_record();u=json.loads(read(INVENTORY))['units'][28]
    phrases=('ruhender starrer Stab','die Länge [M0043]','die Stabachse in die [M0044]-Achse','gleichförmige Paralleltranslationsbewegung (Geschwindigkeit [M0045]) längs der [M0046]-Achse im Sinne der wachsenden [M0047]')
    segments=[]
    for phrase in phrases:
        start=u['text'].index(phrase);segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,start+len(phrase)],source=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_rod_geometry.py','scripts/check_rod_geometry.py','tests/test_rod_geometry.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_rigid_body_kinematics.py','scripts/compose_limits.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py'}
    return dict(status='rod_geometry_dependency_checked_source_integration_pending',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
