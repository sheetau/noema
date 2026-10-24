"""Check nonvacuous relational divergence and attribution of a false claim."""
from functools import lru_cache
from itertools import product
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden,relation,perturb
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_distant_direction_geometry import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_doppler_specialization import CONSTANTS,DOMAIN
from scripts.compose_doppler_infinity import *

CONSTANTS=CONSTANTS|{'eisst':'infinityclaim','eissu':'aside'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values(),'view','body']))
DOC='docs/doppler-infinity-v1.md';SOURCE='data/einstein-doppler-infinity-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/doppler-specialization-v1.json','reports/observed-doppler-v1.json')
BOUNDS={'ekfh':{'ekfg'},'ekfi':{'ekfg'},'ekfk':{'ekfj'},'ekfl':{'ekfk'},'ekfm':{'ekfi','ekfk'},'ekfn':{'ekey','ekez'},'ekfo':{'ekfn'},'ekfp':{'ekfo'},'ekfq':{'ekfo'},'ekfr':{'ekfq','ekfp','ekfm'},'ekfs':{'ekfq'},'ekfu':{'ekft'},'ekfw':{'ekfu'}}

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'bg','sjd','sky','soy'}|BOUNDS.get(name,set())
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='finite':
        def replace(node):
            if node==RS:return 'individual'
            if isinstance(node,list):return [replace(x) for x in node]
            if isinstance(node,dict):return {k:replace(x) for k,x in node.items()}
            return node
        doc=replace(doc)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name)
        inside=d['result']=='content';body=d['body']['body'] if inside else d['body'];pivot=int(mode.split(':')[1]);retained=None
        count=len(WITNESSES) if name=='ekfo' else len(VARIABLES)
        for i in range(count):
            assert body['kind']==('exists' if name=='ekfo' else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if inside:d['body']['body']=retained|{'body':body}
        else:d['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='witness':
        assert name=='ekfu'
        node=d['body']['body']
        for _ in range(2):
            assert node['kind']=='exists';d['parameters'].append(dict(name=node['variable'],sort=node['sort']));node=node['body']
        d['body']['body']=node
    slots=[];actual=[]
    for i,p in enumerate(d['parameters']):
        n='jdinf'+number_word(i);s=p['sort'];slots.append((n,s))
        if isinstance(s,dict) and s.get('kind')=='description':
            assert s['result']=='content'
            doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result='content'))
            actual.append(dict(kind='quote',body=dict(kind='call',symbol=n,arguments=[])))
        else:
            doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=s));actual.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=actual)
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jdinfcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdinfcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jdinfcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def point_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    graph=FunctionValue((RS,RS),'truth',lambda x,y:r(y)==-r(x))
    for x,y,B,M in product((-3,0,3),(-3,0,3),(-4,0,4),(-4,0,4)):
        point=y==-x;below=point and x<B
        assert run('ekff',[graph,c(x),c(y)],m)==point
        assert run('ekfg',[graph,c(B),c(x),c(y)],m)==below
        assert run('ekfj',[graph,c(M),c(B),c(x),c(y)],m)==(not below or M<y);cases+=3
    # Equal bounds are excluded; reversing the input or output inequality fails.
    assert not run('ekfg',[graph,c(-3),c(-3),c(3)],m);cases+=1
    assert not run('ekfj',[graph,c(3),c(0),c(-3),c(3)],m);cases+=1
    assert not run('ekff',[graph,c(-3),c(3)],m|{'ba':lambda x:False});cases+=1
    unknowns(lambda mm:run('ekfj',[graph,c(2),c(0),c(-3),c(3)],mm),m,('ba','bg'))
    empty=FunctionValue((RS,RS),'truth',lambda *xs:False)
    assert run('ekfj',[empty,c(2),c(0),c(-3),c(3)],m);cases+=1
    return dict(cases=cases,strict_input_tail_and_all_output_thresholds=True,empty_point_implication_not_a_divergence_certificate=True)

@lru_cache(None)
def quantifier_checks():
    domain=('a','b');graph=FunctionValue(('individual','individual'),'truth',lambda *xs:True);cases=0
    triples=list(product(domain,repeat=3));pairs=list(product(domain,repeat=2))
    # These are abstract order tables, not finite approximations to real infinity.
    for bits in product((False,True),repeat=8):
        table=dict(zip(triples,bits));m={'ba':lambda x:True,'ekfg':lambda G,B,x,y:table[B,x,y]}
        for B in domain:
            assert run('ekfh',[graph,B],m,'finite',domain)==any(table[B,x,y] for x,y in pairs);cases+=1
        assert run('ekfi',[graph],m,'finite',domain)==all(any(table[B,x,y] for x,y in pairs) for B in domain);cases+=1
    for bits in product((False,True),repeat=4):
        table=dict(zip(pairs,bits));m={'ba':lambda x:True,'ekfk':lambda G,M,B:table[M,B],'ekfi':lambda G:True}
        for M in domain:
            assert run('ekfl',[graph,M],m,'finite',domain)==any(table[M,B] for B in domain);cases+=1
        expected=all(any(table[M,B] for B in domain) for M in domain)
        assert run('ekfm',[graph],m,'finite',domain)==expected;cases+=1
        assert not run('ekfm',[graph],m|{'ekfi':lambda G:False},'finite',domain);cases+=1
        assert not run('ekfk',[graph,'a','b'],{'ba':lambda x:True,'ekfj':lambda *xs:False},'finite',domain);cases+=1
    diagonal={'ba':lambda x:True,'ekfi':lambda G:True,'ekfk':lambda G,M,B:M==B}
    assert run('ekfm',[graph],diagonal,'finite',domain);cases+=1
    assert not any(all(M==B for M in domain) for B in domain);cases+=1
    for bad in pairs:
        assert not run('ekfk',[graph,'a','b'],{'ba':lambda x:True,'ekfj':lambda G,M,B,x,y,bad=bad:(x,y)!=bad},'finite',domain);cases+=1
    unknowns(lambda mm:run('ekfm',[graph],mm,'finite',domain),diagonal,('ba','ekfi','ekfk'))
    # Native quantification remains over real cuts, never silently this table.
    cuts,m=arithmetic();realgraph=FunctionValue((RS,RS),'truth',lambda *xs:True)
    for root in ('ekfi','ekfm'):
        refused(lambda root=root:run(root,[realgraph],m|{'ekfi':lambda G:True,'ekfk':lambda *xs:True}));cases+=1
    return dict(cases=cases,cofinality_prevents_empty_domain_vacuity=True,for_each_bound_its_own_cutoff=True,every_output_of_a_relation_tested=True,finite_tables_not_real_limit_proofs=True)

def typed_values(fields,slots,cuts):
    return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,slots))]

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    slots=fixture('ekfn')[1];values=typed_values(EXTENDED,slots,cuts)
    # Individual placeholders must belong to this interpretation.
    domain=tuple(dict.fromkeys([*DOMAIN,*(n for n,t in BACKGROUND if t=='a')]))
    gate=lambda *xs:all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values,slots))
    mm=m|{'ekey':gate,'ekez':gate}
    assert run('ekfn',values,mm,domain=domain);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts)
        assert not run('ekfn',changed,mm,domain=domain);cases+=1
    unknowns(lambda model:run('ekfn',values,model,domain=domain),mm,('ekey','ekez'))
    gslots=fixture('ekfp')[1];background=typed_values(BACKGROUND,gslots,cuts)
    def relation_point(*xs):
        return all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs[:-2],background,gslots)) and r(xs[-2])==-3 and r(xs[-1])==7
    mapped=run('ekfp',background,m|{'ekfo':relation_point},domain=domain)
    assert mapped(c(-3),c(7));assert not mapped(c(7),c(-3));cases+=2
    for i,(n,s) in enumerate(gslots):
        changed=background[:];changed[i]=sentinel(s,100+i,cuts)
        assert not run('ekfp',changed,m|{'ekfo':relation_point},domain=domain)(c(-3),c(7));cases+=1
    # Every existential slot is retained in turn, with two distinguishing values.
    for pivot,(name,t) in enumerate(WITNESSES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in EXTENDED};expected['context']='case';expected[name]=target
            row=tuple(expected[n] for n,t in EXTENDED)
            vals=[expected[n] for n,t in BACKGROUND+[('speed',R),('frequency',R)]]+[expected[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot]
            mm={'ekfn':lambda *xs,row=row:tuple(xs)==row}
            assert run('ekfo',vals,mm,'slot:'+str(pivot),('a','b'))==(target!='unavailable');cases+=1
            assert not run('ekfo',vals,{'ekfn':lambda *xs:False},'slot:'+str(pivot),('a','b'));cases+=1
    for pivot,(name,t) in enumerate(VARIABLES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in BACKGROUND};expected.update(context='case',scope='b');expected[name]=target
            row=tuple(expected[n] for n,t in BACKGROUND);vals=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekfq':lambda *xs,row=row:tuple(xs)==row,'ekfp':lambda *xs,row=row:'a' if tuple(xs)==row else 'b','ekfm':lambda G:False}
            assert run('ekfr',vals,mm,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
            assert run('ekfr',vals,mm|{'ekfm':lambda G:G=='a'},'slot:'+str(pivot),('a','b'));cases+=1
    return dict(cases=cases,all_60_roles_share_condition_and_equation=True,background_roles=15,all_existential_slots=len(WITNESSES),all_universal_background_slots=len(VARIABLES),printed_unprimed_frequency_is_graph_output=True)

@lru_cache(None)
def domain_checks():
    from scripts.check_doppler_specialization import run as prior
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    # Necessary domain factor of ekey is evaluated natively, no invalid radical.
    for V,speed in product((1,5,13),(-100,-5,-1,0,1,3,5,20)):
        admitted=prior('ekev',[c(V),c(speed)],m)
        assert admitted==(0<speed<V)
        assert not(admitted and speed<0);cases+=2
    core=parse(read(CORE));ds={d['name']:d for d in core['declarations']}
    from noema.meaning_catalog import _references
    assert {'ekey','ekez'}<=_references(ds['ekfn']['body'])
    assert 'ekev' in _references(ds['ekey']['body'])
    assert 'ekfi' in _references(ds['ekfm']['body'])
    assert all(_references(ds[n]['body'])<={'ba','bg','ekff','ekfg','ekfh','ekfi','ekfj','ekfk','ekfl'} for n in ('ekfi','ekfm'))
    return dict(cases=cases,zero_cutoff_has_no_points_in_prior_positive_speed_domain=True,no_invalid_square_root_or_infinite_cut_added=True,printed_claim_not_certified_true=True)

@lru_cache(None)
def presentation_checks():
    rows={
     'ekft':{'eisah':{('view','paper','case')},'eisai':{('view','jdinfb','case')},'eisnp':{('aside','author','aside','jdinfb','infinityclaim','ekfr','ekfs','case')}},
     'ekfv':{'uh':{('infinityclaim','author','ekfr','scope','case')},'zdg':{('infinityclaim','author','ekfr','scope','case')},'zc':{('infinityclaim','author','eke3','ekfr','scope','case')}},
     'ekfy':{'eir3':{('infinityclaim','author','paper','ekfx','case')},'ue':{('axialdisplay','infinityclaim','case')}}}
    cases=0
    for root,rs in rows.items():
        values=['view',None,'case'] if root=='ekft' else []
        cases+=perturb(lambda model:run(root,values,model),{n:relation(vs) for n,vs in rs.items()},rs)
    rs=rows['ekfv']|{'eisa5':{('aside','author','ekfr','ekfu','case')}}
    model={n:relation(vs) for n,vs in rs.items()}|{'ekfu':lambda:None}
    # Content primitives return a checked Content value; construct the abstract aside
    # as a native content with an explicit truth probe for this one fixture.
    doc,slots=fixture('ekfw')
    doc=deepcopy(doc)
    ix=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ekfu')
    doc['declarations'][ix:ix+1]=parse('n:\nr jdinfaside[d] c.\nd ekfu[] e[b p[k jdinfaside[v p]]].')['declarations']
    def whole(mm):
        mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|mm
        return evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000)[0]['value']
    cases+=perturb(whole,model|{'jdinfaside':lambda p:p=='case'},rs)
    assert not whole(model|{'jdinfaside':lambda p:False});cases+=1
    witness={'ekft':lambda view,description,p:view=='view' and p=='case'}
    assert run('ekfu',['view',None],witness,'witness');cases+=1
    assert not run('ekfu',['view',None],{'ekft':lambda *xs:False},'witness');cases+=1
    # The real existential over closed descriptions cannot be finitely evaluated.
    try:run('ekfu',[],witness)
    except ValueError as e:assert 'description domain' in str(e)
    else:raise AssertionError('Full description domain silently enumerated')
    return dict(cases=cases,usual_view_content_is_shared_and_not_invented=True,claim_consequence_obviousness_contrast_and_aside_preserved=True,no_quoted_infinity_or_physics_evaluated_by_attribution=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};u=inv['units'][191]
    assert digest(u['text'].encode())==u['text_sha256']
    for n,expected in [('M0336',['v','=','−','∞']),('M0337',['ν','=','∞'])]:
        tokens=[x.text.strip() for x in ET.fromstring(math[n]['mathml']).iter() if x.text and x.text.strip()]
        assert tokens==expected,(n,tokens)
    segment=dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],statements=[INDEX],math=[dict(id=n,sha256=math[n]['sha256'],reading=r) for n,r in [('M0336','v=−∞'),('M0337','ν=∞')]],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])))
    return dict(status='printed_infinities_preserved_under_explicit_relational_boundary_reading',segments=[segment],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==375 and new.document['statements'][:374]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_references=2,old_374_statements_and_judgments_preserved=True,printed_infinities_and_frequency_roles_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('point',point_checks),('quantifier',quantifier_checks),('binding',binding_checks),('domain',domain_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_distant_direction_geometry','check_wave_cycle_frequency','check_resting_charge_force','check_doppler_specialization','compose_doppler_specialization','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_doppler_infinity.py','scripts/check_doppler_infinity.py','tests/test_doppler_infinity.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='literal_infinity_claim_composed_without_factive_evaluation',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
