"""Distinguish all-use auxiliary roles, shared concepts and explanatory scope."""
from functools import lru_cache
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_auxiliary_role import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,MEANINGS,build

DOC='docs/auxiliary-role-v1.md';SOURCE='data/einstein-auxiliary-role-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/physical-field-dependence-v1.json','reports/magnetomotive-wording-v1.json','reports/electromotive-wording-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','eisqw':'theory','eisqs':'expression','zpt':'dependence','zpv':'role','zpw':'reason'}
DOMAIN=tuple(CONSTANTS.values())+('a','b','other')

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds={'ejzo'}
    if mode=='binding':bounds|={'ejzt','ejzu'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jar'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(rows):return {n:relation(rs) for n,rs in rows.items()}

@lru_cache(None)
def designation_checks():
    rows={'eisqz':{('a','expression','ejyg','case')},'eiscw':{('theory','a','case')}};m=model(rows)
    cases=perturb(lambda mm:run('ejzt',['theory','a','case'],mm),m,rows)
    assert run('ejzt',['theory','a','case'],m|{'ejyg':forbidden});cases+=1
    for i in range(3):
        args=['theory','a','case'];args[i]='other';assert not run('ejzt',args,m);cases+=1
    return dict(cases=cases,same_expression_physical_role_concept_and_theory_introduction=True,quoted_role_not_executed=True)

@lru_cache(None)
def role_checks():
    # Every pair of use/substitution subsets over two distinguishable uses.
    subsets=[{x for x,yes in zip(('a','b'),bits) if yes} for bits in product((False,True),repeat=2)]
    cases=0
    for uses,expanded in product(subsets,repeat=2):
        rows={'eisq2':{('theory','a',u,'case') for u in uses},'eisq3':{('theory','a',u,'ejx4','case') for u in expanded}}
        assert run('ejzu',['theory','a','case'],model(rows))==bool(uses and uses<=expanded),(uses,expanded);cases+=1
    rows={'eisq2':{('theory','a',u,'case') for u in ('a','b')},'eisq3':{('theory','a',u,'ejx4','case') for u in ('a','b')}};m=model(rows)
    # Removing a use is allowed, but losing or misbinding any required expansion is not.
    cases+=perturb(lambda mm:run('ejzu',['theory','a','case'],mm),m,{'eisq3':rows['eisq3']})
    unknowns(lambda mm:run('ejzu',['theory','a','case'],mm),m,('eisq2','eisq3'))
    for i in range(3):
        args=['theory','a','case'];args[i]='other';assert not run('ejzu',args,m);cases+=1
    # Unused concepts/other theories are outside the quantifier's antecedent.
    extra=rows['eisq2']|{('other','a','other','case'),('theory','b','other','case'),('theory','a','other','other')}
    assert run('ejzu',['theory','a','case'],m|{'eisq2':relation(extra)});cases+=1
    assert run('ejzu',['theory','a','case'],m|{'ejx4':forbidden});cases+=1
    return dict(cases=cases,nonempty_all_uses_not_just_one_success=True,independent_role_and_wrong_construction_rejected=True,two_use_finite_domain_diagnostic=True,construction_not_executed_from_quote=True)

def full_rows(concept='a'):
    return {'eisqy':{('theory','paper','eigj','scope','case')},'eisqz':{(concept,'expression','ejyg','case')},'eiscw':{('theory',concept,'case')},'eisq2':{('theory',concept,'a','case'),('theory',concept,'b','case')},'eisq3':{('theory',concept,u,'ejx4','case') for u in ('a','b')},'ejzo':{('theory','case')},'eisq4':{('theory',concept,'ejzo','eiscw','case')}}

@lru_cache(None)
def explanation_checks():
    rows=full_rows();m=model(rows)
    targets={n:rs for n,rs in rows.items() if n!='eisq2'}
    cases=perturb(lambda mm:run('ejzw',[],mm),m,targets)
    for c in ('a','b'):
        assert run('ejzw',[],model(full_rows(c)));cases+=1
    # A good auxiliary role for a and an introduction reason for b cannot be combined.
    assert not run('ejzw',[],m|{'eisq4':relation({('theory','b','ejzo','eiscw','case')})});cases+=1
    assert run('ejzv',[],m|{'eisq4':forbidden,'ejzo':forbidden});cases+=1
    assert not run('ejzw',[],m|{'ejzo':lambda *xs:False});cases+=1
    # Explanatory reference to introduction is not a substitute for actual introduction.
    assert not run('ejzw',[],m|{'eiscw':lambda *xs:False});cases+=1
    # Check the shared existential independently of its concept/role internals.
    base={'eisqy':rows['eisqy'],'ejzo':rows['ejzo']}
    for identified,auxiliary,reasoned in product(('a','b'),repeat=3):
        rs=base|{'ejzt':{('theory',identified,'case')},'ejzu':{('theory',auxiliary,'case')},'eisq4':{('theory',reasoned,'ejzo','eiscw','case')}}
        assert run('ejzw',[],model(rs),'binding')==(identified==auxiliary==reasoned);cases+=1
    return dict(cases=cases,same_concept_through_role_and_introduction_reason=True,grounds_and_introduction_separately_required=True,explanation_not_replaced_by_material_implication=True,physical_dependence_is_prior_pinned_boundary=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    fixtures={
      'ejzx':{'uh':{('role','author','ejzv','scope','case')}},
      'ejz2':{'uh':{('reason','author','ejzw','scope','case')},'zdg':{('reason','author','ejzw','scope','case')}},
      'ejzz':{'eir3':{('role','author','paper','ejzy','case')},'ue':{('dependence','role','case')}},
      'ejz4':{'eir3':{('reason','author','paper','ejz3','case')},'ue':{('role','reason','case')}},
    }
    for n,rs in fixtures.items():cases+=perturb(lambda mm:run(n,[],mm),model(rs),rs)
    for n,alias in (('ejzz',{'zpv':lambda:'dependence'}),('ejz4',{'zpw':lambda:'role'})):
        # Accept all attribution/order rows to isolate explicit node inequality.
        assert not run(n,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True}|alias);cases+=1
    assert run('ejz2',[],model(fixtures['ejz2'])|{'ejzw':forbidden});cases+=1
    return dict(cases=cases,author_man_sieht_and_same_whole_content_bound=True,source_nodes_and_order_distinct=True,quoted_content_not_executed=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][175];text=u['text'];assert u['id']=='einstein-1905:u0176' and digest(text.encode())==u['text_sha256']
    starts=[0,text.index('Man sieht'),text.index('welcher'),text.index('daß die elektrischen'),len(text)]
    clauses=[dict(range=[a,b],text=text[a:b]) for a,b in zip(starts,starts[1:])]
    return dict(status='whole_unit_source_collated_semantic_judgment_separate',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,math=[],clauses=clauses,source_nonblank_characters=len(re.sub(r'\s','',text)),observations=['原刊910頁と固定転記で、磁動力への類推から補助的な役割・導入理由・系依存性まで続けて読んだ。','Man siehtは第二文全体の著者による明白さの提示。welcherとseineは同じ電動力概念を指す。','展開した同じ理論、全ての構成的使用での補助的な役割だけという限定、理論上の導入理由を合成する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==INDICES
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[167,168,169,170])==selection_binding(old,[167,168,169,170])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'eisqz','eisq2','eisq3','eisq4','ejzo','ejx4','ejyg','eiscw','zdg','eisqy'}<=names
    assert not names&{'sdf2','sdg2','zpu'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=4,other_358_statements_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('designation',designation_checks),('role',role_checks),('explanation',explanation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_rod_methods','compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_auxiliary_role.py','scripts/check_auxiliary_role.py','tests/test_auxiliary_role.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=[52,len(s['text'])],source=s['text'][52:],statements=INDICES,definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='exclusive_auxiliary_role_introduction_reason_and_presentation_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
