"""Distinguish each link of the rewritten equations and its physical bindings."""
from fractions import Fraction as Q
from functools import lru_cache
from copy import deepcopy
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_transformed_dynamics as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_mass_rewrite import *

DOC='docs/electron-mass-rewrite-v1.md';SOURCE='data/einstein-electron-mass-rewrite-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf'
DEPENDENCIES=('reports/electron-transformed-dynamics-v1.json',)
fn=prior.fn;sort=prior.sort;forbidden=prior.forbidden;reject=prior.reject;Model=prior.Model
CONSTANTS=prior.CONSTANTS|{'eisyp':'rewrite','eisyq':'chaindisplay'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values()]))
BOUNDS={'els':{'ek74'},'elt':{'ek63','ek66','elb','els'},'elu':{'ek63','els'},'elv':{'ek7s','elk','elu'},'elx':{'elw'}}
@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=prior.prior.base.BOUNDS|BOUNDS.get(root,set())
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root):
    doc=deepcopy(boundary(root));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expression=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmrpoint',parameters=[],result='situation'));expression=dict(kind='evaluate',content=expression,situation=dict(kind='call',symbol='jmrpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expression)];return doc,slots
def run(root,values,m):
    doc,slots=fixture(root);assert len(slots)==len(values)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jmrpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def equation_checks():
    cases=0
    for speed in (0,3):
        for A in (0,1,Q(-1,2)):
            a=Model(speed,A);c,r=a.c,a.r;mm=a.m|{'ek74':lambda *xs:a.key(xs)==a.key(a.values(SETTING))}
            for root,fields in [('elq',SETTING),('elr',PAIR),('els',PAIR)]:assert run(root,a.values(fields),mm);cases+=1
            for name,t in ACCEL:
                old=a.by[name];a.by[name]=c(r(old)+1)
                assert not run('elq',a.values(SETTING),mm) and run('elr',a.values(),mm);cases+=1;a.by[name]=old
            for axis in ('x','y','z'):
                old=a.by['newelectric'];a.by['newelectric']=a.field(lambda ax,p:r(old(ax)(*map(c,p)))+(ax==axis))
                assert run('elq',a.values(SETTING),mm) and not run('elr',a.values(),mm);cases+=1;a.by['newelectric']=old
            # Retain the actual local new-field values in this fixture's own
            # cut domain. Mixing cuts belonging to another model is refused.
            newvalues={axis:r(a.by['newelectric'](axis)(*map(c,(0,0,0,0)))) for axis in ('x','y','z')}
            a.by['newelectric']=a.field(lambda ax,p,values=newvalues:values.get(ax,0))
            for field,axes in [('electricfield',('x','y','z')),('magneticfield',('y','z') if speed else ())]:
                for axis in axes:
                    old=a.by[field];a.by[field]=a.field(lambda ax,p:r(old(ax)(*map(c,p)))+(ax==axis))
                    assert not run('elq',a.values(SETTING),mm) and not run('elr',a.values(),mm);cases+=1;a.by[field]=old
            for mass in (0,-1):
                old=a.by['mass'];a.by['mass']=c(mass);assert not run('elq',a.values(SETTING),mm);cases+=1;a.by['mass']=old
            # Signed charge is present on both links. Simultaneous charge/field
            # reversal preserves them; changing charge alone does not.
            old=a.by['charge'];a.by['charge']=c(-r(old));assert not run('elq',a.values(SETTING),mm);cases+=1
            for field in ('electricfield','magneticfield','newelectric'):
                oldfield=a.by[field];a.by[field]=a.field(lambda ax,p,f=oldfield:-r(f(ax)(*map(c,p))))
            assert run('elq',a.values(SETTING),mm) and run('elr',a.values(),mm);cases+=1
    a=Model();a.by['charge']=a.c(0);a.by['newelectric']=a.field(lambda ax,p:123)
    assert run('elr',a.values(),a.m);cases+=1
    for root,fields,key in [('elq',SETTING,'soy'),('elr',PAIR,'soy')]:reject(lambda:run(root,a.values(fields),a.m|{key:forbidden}));cases+=1
    return dict(cases=cases,all_six_equalities_independently_distinguished=True,three_axes_beta_powers_and_magnetic_signs=True,signed_charge_preserved_zero_not_cancelled=True)

@lru_cache(None)
def coordinate_checks():
    cases=0
    for offset in ((0,0,0,0),(2,-1,4,3)):
        a=Model();a.offset=tuple(map(Q,offset));a.m['eisxz']=lambda:a.point(a.offset)
        for p in ((1,2,-1,Q(1,2)),(-2,1,3,-1)):
            a.by['point']=a.point(p);mapped=a.mapped(p);assert mapped!=tuple(p)
            assert run('elr',a.values(),a.m);cases+=1
            expected=a.mixed(p)
            actual=[a.r(a.by['newelectric'](axis)(*map(a.c,mapped))) for axis in ('x','y','z')]
            assert tuple(actual)==expected;cases+=1
            # A constant field matching values at the wrong (old) coordinates
            # must fail despite the unchanged numerical labels X',Y',Z'.
            old=a.by['newelectric'];wrong={axis:a.r(old(axis)(*map(a.c,p))) for axis in ('x','y','z')}
            assert tuple(wrong.values())!=expected
            a.by['newelectric']=a.field(lambda ax,p:wrong.get(ax,0));assert not run('elr',a.values(),a.m);cases+=1
            a.by['newelectric']=old
    a=Model();a.by['newelectric']=a.field(lambda ax,p:forbidden());reject(lambda:run('elr',a.values(),a.m));cases+=1
    return dict(cases=cases,nonorigin_events_and_nonzero_coordinate_offsets=True,actual_new_field_evaluated_at_corresponding_event=True,unknown_new_field_refused=True)

@lru_cache(None)
def connection_checks():
    a=Model();key=a.key;old=key(a.values(SETTING));pair=key(a.values());cases=0
    for physical in (False,True):
        for transforms in (False,True):
            for original in (False,True):
                for rewritten in (False,True):
                    mm={'ek63':lambda *xs:key(xs)==pair and physical,'ek66':lambda *xs:key(xs)==pair and transforms,'elb':lambda *xs:key(xs)==old and original,'els':lambda *xs:key(xs)==pair and rewritten}
                    assert run('elt',a.values(),mm)==(not(physical and transforms) or original==rewritten);cases+=1
    for initial in (False,True):
        assert run('els',a.values(),a.m|{'ek74':lambda *xs:key(xs)==old and initial})==initial;cases+=1
    reject(lambda:run('els',a.values(),a.m|{'ek74':forbidden}));cases+=1
    # Independently verify the public-role contracts, including the restriction
    # of PAIR to the original SETTING, before numerical boundary diagnostics.
    for root,targets in [('els',{'elq':SETTING,'elr':PAIR,'ek74':SETTING}),('elt',{'ek63':PAIR,'ek66':PAIR,'elb':SETTING,'els':PAIR})]:
        d=next(x for x in core()['declarations'] if x['name']==root);mapping=dict(zip((n for n,t in PAIR),(p['name'] for p in d['parameters'])));seen=set()
        def walk(node):
            if isinstance(node,dict):
                if node.get('kind')=='call' and node.get('symbol') in targets:
                    symbol=node['symbol'];assert node['arguments']==[dict(kind='variable',name=mapping[n]) for n,t in targets[symbol]];seen.add(symbol)
                for value in node.values():walk(value)
            elif isinstance(node,list):
                for value in node:walk(value)
        walk(d['body']);assert seen==set(targets);cases+=1
    return dict(cases=cases,same_42_roles_and_33_old_roles_checked=True,conditional_equivalence_including_false_equations=True,old_initial_motion_retained=True)

@lru_cache(None)
def presentation_checks():
    rows={'zd3':{('rewrite','author','ek7s','elk','elu','tenth','case')},'eiswm':{('rewrite','author','Adisplay','elk','paper','case')},'eisch':{('Alabel','elk','tenth','case')},'eisox':{('chaindisplay','elu','case')},'uf':{('author','rewrite','chaindisplay','case')},'ue':{('rewrite','chaindisplay','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('elv',[],m),mm,rows)
    assert run('elv',[],mm|{n:forbidden for n in BOUNDS['elv']});cases+=1
    rows={'eir3':{('rewrite','author','paper','elw','case')},'ue':{('Adisplay','rewrite','case')}};mm={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda m:run('elx',[],m),mm,rows)
    return dict(cases=cases,same_A_label_and_prior_formula_preserved=True,conditional_rewrite_and_six_equality_display=True,quoted_physics_not_executed=True)

@lru_cache(None)
def binder_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jmrunits',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    doc=collapse(transform(boundary('elu')));doc['declarations'].append(dict(kind='primitive',name='jmrunits',parameters=[],result='individual'));doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc=extract_document(doc,roots=['elu'],statement_indices=[]).document
    d=next(x for x in doc['declarations'] if x['name']=='elu');body=d['body']['body'];names=[]
    for _ in BOUND:names.append(body['variable']);body=body['body']
    mapping=dict(zip((n for n,t in BOUND),names));variable=lambda n:dict(kind='variable',name=n);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
    fixed={'frame':constant('ra'),'event':constant('eisxv'),'electricconversion':constant('jmrunits'),'context':variable(d['body']['variable'])}
    expected=[fixed[n] if n in fixed else variable(mapping['oldpoint' if n=='point' else n]) for n,t in PAIR]
    assert body['kind']=='implies'
    assert body['arguments'][0]['symbol']=='ek63' and body['arguments'][0]['arguments']==expected
    assert body['arguments'][1]['symbol']=='els' and body['arguments'][1]['arguments']==expected
    cases=1
    for pivot in range(len(BOUND)):
        f,d,slots,var,b=lifted(doc,'elu',pivot,len(BOUND),'forall')
        env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
        calls={}
        def walk(x):
            if isinstance(x,dict):
                if x.get('kind')=='call' and x.get('symbol') in ('ek63','els'):calls[x['symbol']]=x['arguments']
                for y in x.values():walk(y)
            elif isinstance(x,list):
                for y in x:walk(y)
        walk(b)
        def row(call,value):return tuple((env|{var:value})[x['name']] if x['kind']=='variable' else 'a' for x in call)
        for accepted,want in [(('a','b'),True),(('a',),False)]:
            mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{n:lambda:'a' for n in ('ra','eisxv','jmrunits')}
            mm|={n:lambda *xs,n=n:xs in {row(calls[n],value) for value in (('a','b') if n=='ek63' else accepted)} for n in ('ek63','els')}
            primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=primitives,max_steps=25000)[0]['value']==want,(pivot,accepted);cases+=1
    reject(lambda:run('elu',[],{'ek63':lambda *xs:True,'els':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_38_actual_binders_and_independent_role_contract=True,two_value_diagnostics_not_full_domain_proofs=True)

@lru_cache(None)
def source_record():
    inventory=json.loads(read(INVENTORY));rows=[]
    for unit in inventory['units'][251:253]:
        assert digest(unit['text'].encode())==unit['text_sha256'];math=[m for m in inventory['math'] if m['id'] in unit['math_ids']]
        for m in math:assert digest(m['mathml'].encode())==m['sha256']
        start=unit['text'].index('Wir schreiben') if unit['id'].endswith('u0252') else 0
        rows.append(dict(unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[start,len(unit['text'])],math=math,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',unit['text'][start:]))))
    return dict(version='einstein-electron-mass-rewrite-reading-v1',units=rows,facsimile_pages=[919],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==423 and after.document['statements'][:422]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[421])==selection_binding(before,[421]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-transformed-dynamics-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_constants=len(REFERENCES),new_statements=1,all_422_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equations',equation_checks),('coordinates',coordinate_checks),('connections',connection_checks),('presentation',presentation_checks),('binders',binder_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_mass_rewrite.py','scripts/check_electron_mass_rewrite.py','tests/test_electron_mass_rewrite.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='same_electron_six_equalities_and_rewrite_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
