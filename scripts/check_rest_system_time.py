"""Check definitional clock constraints, same convention and reasoned naming."""
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
from scripts.check_event_time_summary import setup as prior_setup,DOMAIN as PRIOR_DOMAIN
from scripts.compose_rest_system_time import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_rest_system_time import SOURCE,INVENTORY,DOC,READING,PRIORS,source_record

POINTS=('now','other');DOMAIN=PRIOR_DOMAIN+('node','name','law')


def forbidden(*args):raise ValueError('Unknown rest-system-time input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows
def changed(row,i):return tuple('other' if j==i else x for j,x in enumerate(row))


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    modes={'native':NUM|{'qo'},'boundary':{'eing'},'content':{'einy'},'logic':{'ein2','ein3'}}
    abstract(doc,modes.get(mode,set()))
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrst'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrstcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrstcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jrstcontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})[0]['value']


def reject_unknown(name,args,m,symbols,mode='native'):
    for symbol in symbols:
        try:run(name,args,m|{symbol:forbidden},mode)
        except ValueError as e:assert 'Unknown rest-system-time' in str(e)
        else:raise AssertionError(('Unknown input accepted',symbol))


@lru_cache(None)
def definitional_checks():
    """Conjunction elimination after unfolding only the local timestamp chain.

    No quantified, disjunctive, negative or conditional branch contributes an atom.
    The argument holds for arbitrary arguments, including all real-cut predicates.
    """
    doc=parse(read(CORE));decls={d['name']:d for d in doc['declarations']};visited=set()
    allowed={'eing','qu','qt','saf','sae'}
    def substitute(node,env):
        if isinstance(node,list):return [substitute(x,env) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable':return env.get(node['name'],node)
        return {key:substitute(x,env) for key,x in node.items()}
    def atoms(node,env):
        kind=node['kind']
        if kind=='and':return set().union(*(atoms(x,env) for x in node['arguments']))
        if kind=='call':name=node['symbol'];arguments=[substitute(x,env) for x in node['arguments']]
        elif kind=='apply':
            fn=substitute(node['function'],env)
            if fn.get('kind')!='function_ref':return set()
            name=fn['symbol'];arguments=[substitute(x,env) for x in node['arguments']]
        else:return set()
        if name in allowed:
            d=decls[name];visited.add(name);assert d['kind']=='definition'
            return atoms(d['body'],{p['name']:x for p,x in zip(d['parameters'],arguments,strict=True)})
        return {json.dumps(dict(kind='call',symbol=name,arguments=arguments),sort_keys=True)}
    d=decls['einx'];assert d['body']['kind']=='implies'
    symbolic=[dict(kind='variable',name=n) for n in ('event','clock','place')]+[dict(kind='call',symbol='ra',arguments=[])]+[dict(kind='variable',name=n) for n in ('reading','context')]
    env={p['name']:x for p,x in zip(d['parameters'],symbolic,strict=True)}
    premise=atoms(d['body']['arguments'][0],env);required=atoms(d['body']['arguments'][1],env)
    assert len(required)==4 and required<=premise and visited==allowed
    assert {json.loads(x)['symbol'] for x in required}=={'ca','cb','cc'}
    # The same inference is not licensed for a different frame.
    alternate=env|{d['parameters'][3]['name']:dict(kind='call',symbol='otherframe',arguments=[])}
    assert not atoms(d['body']['arguments'][1],alternate)<=premise
    # A clause cannot be certified merely because its predicate name occurs elsewhere.
    for atom in required:assert not required<=(premise-{atom})
    return dict(unfolded_definitions=sorted(visited),required_clock_atoms=[json.loads(x) for x in sorted(required)],implication_by_definition_unfolding_and_conjunction_elimination=True,independent_of_sampled_domain_or_numeric_values=True,different_frame_conclusion_not_entailed=True)


@lru_cache(None)
def clock_checks():
    cuts,m,rows,*_=prior_setup();args=['eventa','clocka','placea','frame',cuts.make(Q(7)),'now'];count=0
    assert run('eing',args[:3]+args[4:],m);count+=1
    assert run('einx',args,m);count+=1
    other=args.copy();other[3]='other'
    assert not run('einx',other,m);count+=1
    # When the underlying assignment is invalid, the implication does not invent one.
    moving=m|{'cc':relation(rows['cc']-{('clocka','frame')})}
    assert not run('eing',args[:3]+args[4:],moving);count+=1
    assert run('einx',args,moving);count+=1
    # Separately check each consequence with the rule treated as an explicit boundary.
    boundary=m|{'eing':lambda *xs:True}
    required={'ca':{('clocka',)},'cc':{('clocka','frame'),('clockb','frame')},'cb':{('clocka','placea','frame')}}
    for symbol,rs in required.items():
        for row in rs:
            assert not run('einx',args,boundary|{symbol:relation(rows[symbol]-{row})},'boundary');count+=1
    seen=[]
    def capture(*xs):seen.append((*xs[:3],cuts.read(xs[3]),xs[4]));return True
    assert run('einx',args,m|{'eing':capture},'boundary');count+=1
    assert seen==[('eventa','clocka','placea',Q(7),'now')]
    reject_unknown('einx',args,m,('cc','cb','ce','qo','eisgm'))
    try:run('einy',[],m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e) or 'unbounded' in str(e)
    else:raise AssertionError('Universal real-predicate domain silently sampled')
    return dict(cases=count,stationary_clock_rule_and_same_frame_checked=True,invalid_assignment_not_invented_by_implication=True,unbounded_general_property_not_finitely_sampled=True)


def setup():
    cuts,m,*_=prior_setup();names={'eisks':'name','eiskt':'node','tm':'law'}
    m|={n:(lambda x=x:x) for n,x in names.items()}
    rows={'uj':{('definition','author','eing','paper','now')},'eisku':{('time','eing','frame','unit','paper','now')},'eisd4':{('node','author','name','time','paper','now')},'eiskv':{('node','author','ein2','paper','now')},'eisdk':{('paper','einz','ein3','now')}}
    m|={n:relation(rs) for n,rs in rows.items()}|{'einy':lambda:Content(POINTS,(True,True))}
    return m,rows


@lru_cache(None)
def reference_and_naming_checks():
    assert definitional_checks()['implication_by_definition_unfolding_and_conjunction_elimination']
    m,rows=setup();count=0
    for name in ('einz','ein2','ein3','ein4'):
        assert run(name,[],m,'content');count+=1
    targets={'uj':'ein2','eisku':'einz','eisd4':'ein3','eiskv':'ein4','eisdk':'ein4'}
    for symbol,rs in rows.items():
        row=next(iter(rs))
        for i in range(len(row)):
            assert not run(targets[symbol],[],m|{symbol:relation({changed(row,i)})},'content');count+=1
    assert not run('einz',[],m|{'einy':lambda:Content(POINTS,(False,False))},'content');count+=1
    assert not run('ein4',[],m|{'eisd4':relation({('node','author','name','localA','paper','now')})},'content');count+=1
    physics={n:forbidden for n in ('ca','cc','cb','ce','qo','eisgm','ba')}
    for name in ('ein2','ein3','ein4'):
        assert run(name,[],m|physics,'content');count+=1
    reject_unknown('ein4',[],m,('uj','eisku','eisd4','eiskv','eisdk'),'content')
    return dict(cases=count,same_just_defined_time_rule_frame_unit_and_designation=True,naming_local_time_or_other_frame_rejected=True,reason_runs_from_frame_dependence_to_naming=True,physical_execution_separate_from_definition_and_naming=True)


@lru_cache(None)
def logic_checks():
    m,rows=setup();count=0
    for defined,named,important,reason in product((False,True),repeat=4):
        mm=m|{'ein2':lambda p=defined:Content(POINTS,(p,p)),'ein3':lambda p=named:Content(POINTS,(p,p)),'eiskv':relation(rows['eiskv'] if important else set()),'eisdk':relation(rows['eisdk'] if reason else set())}
        assert run('ein4',[],mm,'logic')==(defined and named and important and reason);count+=1
    return dict(cases=count,definition_naming_importance_and_reason_all_retained=True)


@lru_cache(None)
def presentation_checks():
    m,_=setup();rows={'eir3':{('node','author','paper','ein5','now')},'eiskq':{('node','author','definition','paper','now')},'ue':{('law','node','now')}};m|={n:relation(rs) for n,rs in rows.items()};count=0
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        assert evaluate(doc,m)[0]['value'];count+=1
        for symbol,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                assert not evaluate(doc,m|{symbol:relation({changed(row,i)})})[0]['value'];count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('uj','eisku','eisd4','eiskv','eisdk','cc','ce')})[0]['value'];count+=1
    return dict(cases=count,just_defined_reference_and_source_order_preserved=True,presentation_does_not_execute_quoted_rule_or_unbounded_property=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==247
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([243,244],[245])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    entries=json.loads(read(ANNOTATIONS))['entries'];prior=json.loads(read('data/empirical-light-constant-identifiers-v1.json'))['entries']
    assert entries[:-1]==prior and entries[-1]['symbol']=='eisks' and entries[-1]['forms'][0]['text']=='die Zeit des ruhenden Systems'
    doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256']);assert source['segments'][0]['nonblank_characters']==177 and not source['editorial_annotations'][0]['adds_proposition']
    rec=json.loads(read(READING));validate_hashes(ROOT,rec['source_sha256']);assert rec['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=246,previous_time_and_constant_judgments_preserved=True,exact_printed_name_and_page_break_checked=True,whole_177_character_source_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_rest_system_time import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('definitional_implication',definitional_checks),('clock_rule',clock_checks),('reference_and_naming',reference_and_naming_checks),('logic',logic_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    s=source_record()['segments'][0]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_rest_system_time.py','scripts/check_rest_system_time.py','scripts/review_rest_system_time.py','tests/test_rest_system_time.py','scripts/check_event_time_summary.py','scripts/check_synchrony_laws.py','scripts/check_light_roundtrip_definition.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='stationary_clock_frame_dependence_and_reasoned_time_naming_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、第二節u0023以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
