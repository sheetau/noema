"""Check a single native roundtrip, all-trial scope and quoted adoption."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM,arithmetic
from scripts.compose_light_roundtrip_definition import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_light_roundtrip_definition import SOURCE,INVENTORY,DOC,source_record

READING='data/light-roundtrip-definition-reading-v1.json'
PRIORS={234:'data/local-clock-valuation-reading-v1.json',235:'data/second-local-clock-reading-v1.json',236:'data/local-times-only-reading-v1.json',237:'data/equal-light-times-reading-v1.json'}
POINTS=('now','other')
DOMAIN=('clocka','clockb','placea','placeb','depart','reflect','arrive','ray','d2','r2','a2','ray2','frame','unit','paper','trial','trial2','author','prior','fifth','sixth','proposal','time','localA','localB','nameA','nameB','other')
TRIP=['clocka','clockb','placea','placeb','depart','reflect','arrive','ray','frame','unit']
SYNC=['clocka','clockb','placea','placeb','frame','unit','paper','now']


def forbidden(*args):raise ValueError('Unknown light-roundtrip-definition input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if mode!='full_real':abstract(doc,NUM|{'eild'}|({'eimj'} if mode=='scope' else set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jlrt'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlrtcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jlrtcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(slots)==len(args)
    return evaluate(doc,m|{'jlrtcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})[0]['value']


def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown light-roundtrip-definition' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


def references(cuts):
    names={'eisib':'clocka','eisik':'clockb','ziq':'placea','zir':'placeb','eisjk':'depart','eisjl':'reflect','eisjm':'arrive','eisjn':'ray','ra':'frame','rb':'unit','eirf':'paper','rd':'author','eisjj':'trial','eisjh':'prior','eisjr':'fifth','eisjs':'sixth','eisje':'proposal','eisjd':'time','eisiw':'localA','eisix':'localB','eisi2':'nameA','eisi3':'nameB'}
    return {n:(lambda x=x:x) for n,x in names.items()}|{'ri':lambda:'now'}|{n:(lambda x=x:cuts.make(Q(x))) for n,x in (('eisjo',0),('eisjp',2),('eisjq',4))}


def setup(second_middle=12):
    cuts,m=arithmetic();r=cuts.read
    rows={'ca':{('clocka',),('clockb',)},'cc':{(c,'frame') for c in ('clocka','clockb')},'cd':{('clocka','clockb')},'ci':{('unit',)},'cf':{('ray',),('ray2',)},'zbd':{(e,) for e in ('depart','reflect','arrive','d2','r2','a2')},'cb':{(e,p,'frame') for e,p in (('clocka','placea'),('clockb','placeb'),('depart','placea'),('reflect','placeb'),('arrive','placea'),('d2','placea'),('r2','placeb'),('a2','placea'))},'cg':{(ray,a,b,'frame') for ray,a,b in (('ray','depart','reflect'),('ray','reflect','arrive'),('ray2','d2','r2'),('ray2','r2','a2'))},'ch':{('ray','reflect','frame'),('ray2','r2','frame')},'eild':{('clockb','clocka','paper','now')},'qa':{(c,'frame','now') for c in ('clocka','clockb')},'ql':{('clocka','clockb','frame','unit','now')},'qb':{('clocka','clockb','frame','unit','now',t) for t in ('trial','trial2')}}
    readings={(c,e,'frame','unit',Q(x)) for c,e,x in (('clocka','depart',0),('clockb','reflect',2),('clocka','arrive',4),('clocka','d2',10),('clockb','r2',second_middle),('clocka','a2',14))}
    m|=references(cuts)|{n:relation(rs) for n,rs in rows.items()}|{'ce':lambda c,e,f,u,x:(c,e,f,u,r(x)) in readings}
    records={t:('placea','placeb',*es) for t,es in (('trial',('depart','reflect','arrive','ray')),('trial2',('d2','r2','a2','ray2')))}
    values={'trial':(0,2,4),'trial2':(10,second_middle,14)}
    for i,n in enumerate(('qc','qd','qe','qf','qg','qh')):m[n]=lambda t,i=i:records.get(t,records['trial'])[i]
    for i,n in enumerate(('qi','qj','qk')):m[n]=lambda t,i=i:cuts.make(Q(values.get(t,values['trial'])[i]))
    return cuts,m,rows,readings,records,values


@lru_cache(None)
def physical_checks():
    cuts,m,rows,readings,records,values=setup();args=TRIP+[cuts.make(Q(x)) for x in (0,2,4)]+['paper','now'];count=0
    assert run('eimh',args,m);count+=1
    assert run('eimj',args,m);count+=1
    for i in list(range(10))+[13,14]:
        a=args.copy();a[i]='other';assert not run('eimh',a,m);count+=1
    for symbol in ('ca','cc','cd','ci','cf','zbd','cb','cg','ch','eild'):
        for row in rows[symbol]:
            if any(x in ('d2','r2','a2','ray2') for x in row):continue
            assert not run('eimh',args,m|{symbol:relation(rows[symbol]-{row})});count+=1
    for row in readings:
        if row[1] in ('d2','r2','a2'):continue
        bad=readings-{row};assert not run('eimh',args,m|{'ce':lambda c,e,f,u,x:(c,e,f,u,cuts.read(x)) in bad});count+=1
    assert not run('eimh',args,m|{'ba':lambda *xs:False});count+=1
    reject_unknown('eimh',args,m,('ca','cb','cc','cd','cf','cg','ch','ci','ce','zbd','eild','ba'))
    return dict(cases=count,same_ray_reflection_and_A_B_A_readings=True,all_physical_roles_checked=True,exact_constitution_reused_as_checked_boundary=True)


@lru_cache(None)
def equation_checks():
    cuts,m,*_=setup();count=0
    for a,b,c in product((Q(-2),Q(0),Q(1,2),Q(2),Q(4)),repeat=3):
        assert run('eimi',[cuts.make(x) for x in (a,b,c)],m)==(2*b==a+c);count+=1
    assert run('eims',[],m);count+=1
    assert not run('eims',[],m|{'eisjp':lambda:cuts.make(Q(3))});count+=1
    assert not run('eims',[],m|{'eisjq':lambda:cuts.make(Q(2))});count+=1
    assert not run('eimi',[cuts.make(Q(x)) for x in (0,2,4)],m|{'ba':lambda *xs:False});count+=1
    reject_unknown('eims',[],m,('eisjo','eisjp','eisjq','ba','bf','sca'))
    try:run('eimi',[cuts.make(Q(x)) for x in (0,2,4)],m,'full_real')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e)
    else:raise AssertionError('Full real domain silently sampled')
    return dict(cases=count,exact_two_differences_match_three_named_readings=True,distinct_cut_objects_compared_numerically=True,full_real_domain_not_sampled=True)


@lru_cache(None)
def scope_checks():
    cuts,m,rows,readings,records,values=setup();count=0
    assert run('eimk',SYNC,m);count+=1
    _,bad,*_=setup(13);assert not run('eimk',SYNC,bad);count+=1
    for symbol in ('ql','qb','qa'):
        assert not run('eimk',SYNC,m|{symbol:relation(set())});count+=1
    for selected,accepted in product(product((False,True),repeat=2),repeat=2):
        trials={r for r in rows['qb'] if selected[0 if r[-1]=='trial' else 1]}
        mm=m|{'qb':relation(trials),'eimj':lambda *xs,ok=accepted:ok[0 if xs[4]=='depart' else 1]}
        assert run('eimk',SYNC,mm,'scope')==(any(selected) and all(not x or y for x,y in zip(selected,accepted)));count+=1
    # The complete qn adapter, including all three real-valued slots, is observed.
    seen=[]
    def criterion(*xs):seen.append(xs);return True
    assert run('eimk',SYNC,m|{'eimj':criterion},'scope');count+=1
    expected=[]
    for t in DOMAIN:
        fs=records.get(t,records['trial']);vs=values.get(t,values['trial'])
        expected.append(('clocka','clockb',*fs[:2],*fs[2:],'frame','unit',*map(Q,vs),'paper','now'))
    actual=[tuple(cuts.read(x) if i in (10,11,12) else x for i,x in enumerate(xs)) for xs in seen]
    assert set(actual)==set(expected)
    for i,n in enumerate(('qc','qd','qe','qf','qg','qh')):
        base=m[n];assert not run('eimk',SYNC,m|{n:lambda t,base=base:'other' if t=='trial2' else base(t)});count+=1
    for n in ('qi','qj','qk'):
        base=m[n];assert not run('eimk',SYNC,m|{n:lambda t,base=base:cuts.make(Q(99)) if t=='trial2' else base(t)});count+=1
    for i in range(len(SYNC)):
        a=SYNC.copy();a[i]='other';assert not run('eimk',a,m);count+=1
    reject_unknown('eimk',SYNC,m,('ql','qb','qa','qc','qd','qe','qf','qg','qh','qi','qj','qk'))
    return dict(cases=count,native_all_trial_condition_executed=True,single_success_and_empty_trials_insufficient=True,all_thirteen_adapter_roles_and_fixed_places_checked=True)


@lru_cache(None)
def hypothetical_checks():
    cuts,m,rows,*_=setup();count=0
    assert run('eiml',[],m);count+=1
    for n in ('qc','qd','qe','qf','qg','qh'):
        base=m[n];assert not run('eiml',[],m|{n:lambda t:'other'});count+=1
    for n in ('qi','qj','qk'):
        assert not run('eiml',[],m|{n:lambda t:cuts.make(Q(99))});count+=1
    # An asymmetric, physically bound trial is a valid supposition but does not meet the definition.
    mm=m|{'eisjp':lambda:cuts.make(Q(3)),'qj':lambda t:cuts.make(Q(3)),'ce':lambda c,e,f,u,x:(c,e,f,u,cuts.read(x)) in {('clocka','depart','frame','unit',Q(0)),('clockb','reflect','frame','unit',Q(3)),('clocka','arrive','frame','unit',Q(4))}}
    assert run('eiml',[],mm);count+=1
    assert not run('eims',[],mm);count+=1
    ug=('fifth','author','eiml','paper','now');definition=('sixth','author','clocka','clockb','placea','placeb','frame','unit','proposal','time','trial','eims','eimk','paper','now')
    m|={'ug':relation({ug}),'eisju':relation({definition})}
    for name,symbol,row in (('eimm','ug',ug),('eimp','eisju',definition)):
        assert run(name,[],m);count+=1
        for i in range(len(row)):
            assert not run(name,[],m|{symbol:relation({changed(row,i)})});count+=1
        assert run(name,[],m|{n:forbidden for n in ('ce','cg','eisjo','qb','ba')});count+=1
        reject_unknown(name,[],m,(symbol,))
    return dict(cases=count,supposition_does_not_assert_synchrony=True,assumption_and_definition_do_not_execute_quoted_physics=True,formula_and_general_rule_bound_to_same_trial_clocks_and_proposal=True)


@lru_cache(None)
def presentation_checks():
    cuts,m,*_=setup();rows={'eir3':{('fifth','author','paper','eimn','now'),('sixth','author','paper','eimq','now')},'eisjt':{('fifth','author','eime','eiml','paper','now')},'eisi4':{('nameA','localA','placea','paper','now'),('nameB','localB','placeb','paper','now')},'ue':{('prior','fifth','now'),('fifth','sixth','now')}};m|={n:relation(rs) for n,rs in rows.items()};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-2:]
        def go(extra=None):return [r['value'] for r in evaluate(doc,m|(extra or {}))]
        assert go()==[True,True];count+=1
        for symbol,rs in rows.items():
            for row in rs:
                target=1 if row[0]=='sixth' or row==('fifth','sixth','now') else 0;expected=[True,True];expected[target]=False
                for i in range(len(row)):
                    assert go({symbol:relation((rs-{row})|{changed(row,i)})})==expected;count+=1
        assert go({n:forbidden for n in ('ug','eisju','ce','cg','ba')})==[True,True];count+=1
    return dict(cases=count,hypothetical_example_explains_previous_definition=True,two_native_presentations_and_local_names_checked=True,attribution_nonfactive=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==240
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index,path in PRIORS.items():
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert [s['nonblank_characters'] for s in source['segments']]==[162,0]
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX,INDEX+1]) and rec['source_nonblank_characters']==162
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=238,four_prior_sentence_bindings_preserved=True,twelve_math_occurrences_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_light_roundtrip_definition import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('physical',physical_checks),('equation',equation_checks),('scope',scope_checks),('hypothetical',hypothetical_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    segments=[]
    for s in source_record()['segments']:
        segments.append(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
        segments.extend(dict(unit=s['unit'],unit_sha256=s['unit_sha256'],math_id=m['id'],math_sha256=m['sha256'],definitions=['eiml','eims','eimp'],status='explicit_interpretive_annotation') for m in s['math'])
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS.values(),'scripts/compose_light_roundtrip_definition.py','scripts/check_light_roundtrip_definition.py','scripts/review_light_roundtrip_definition.py','tests/test_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py','reports/second-local-clock-v1.json'}
    return dict(status='hypothetical_light_roundtrip_and_definitional_synchrony_equation_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['前四文を合わせたu0013・u0014全単位の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
