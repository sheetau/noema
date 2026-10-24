"""Check energy-value binding, two distinct topics and the eighth division."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_problem_series_reduction import collapse
from scripts.check_body_rest_field_method import numbers
from scripts.compose_eighth_section_heading import *

DOC='docs/eighth-section-heading-v1.md';SOURCE='data/einstein-eighth-section-heading-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p913-0.jpg'
DEPENDENCIES=('reports/mean-light-energy-v1.json','reports/light-energy-ratio-v1.json','reports/mirror-energy-principle-v1.json','reports/seventh-section-heading-v1.json')
CONSTANTS={'ra':'frame','zbm':'moving','eisrx':'wavescope','eistk':'section','eispb':'part','eirf':'paper','ri':'case','eisvw':'heading','eistg':'previous','eistl':'following'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),'inquiry','other','a','b']))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts={'ekmi'} if root=='ekw7' else {'ekw7','ekug','ekuf'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode.startswith('slot:'):doc=collapse(doc)
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1])
        def lift(node):
            if isinstance(node,list):return [lift(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')!='exists':return {k:lift(v) for k,v in node.items()}
            body=node;retained=None
            for i in range(len(VARIABLES)):
                assert body['kind']=='exists'
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            return retained|dict(body=body)
        d['body']=lift(d['body'])
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jesh'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    return doc,slots

def run(root,values,m,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    model={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:model.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def correspondence_checks():
    cases=0
    for pivot,(variable,sort) in enumerate(VARIABLES):
        by={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)}
        values=['a','b','a','b','case']+[by[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
        for target in ('a','b','unavailable'):
            expected=by|{variable:target,'energy':'a','newenergy':'b','frame':'a','light':'a','scope':'b','context':'case'}
            row=tuple(expected[n] for n,t in TOTAL)
            model={'ra':lambda:'a','zbm':lambda:'b','tc':lambda:'a','eisrx':lambda:'b','ekmi':lambda *xs,row=row:xs==row}
            assert run('ekw7',values,model,f'slot:{pivot}',('a','b'))==(target!='unavailable'),variable;cases+=1
        unknowns(lambda m:run('ekw7',values,m,f'slot:{pivot}',('a','b')),model,('ekmi',));cases+=1
    # Each exposed value, each frame, and the context retain their own role.
    by={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)}
    row=tuple((by|dict(energy='a',newenergy='b',frame='a',light='a',scope='b',context='case'))[n] for n,t in TOTAL)
    values=['a','b','a','b','case']+[by[n] for i,(n,t) in enumerate(VARIABLES) if i!=0]
    model={'ra':lambda:'a','zbm':lambda:'b','tc':lambda:'a','eisrx':lambda:'b','ekmi':lambda *xs:xs==row}
    assert run('ekw7',values,model,'slot:0',('a','b'));cases+=1
    for i in range(5):
        bad=values.copy();bad[i]='other' if i==4 else 'b' if bad[i]=='a' else 'a'
        assert not run('ekw7',bad,model,'slot:0',('a','b'));cases+=1
    cuts,m=numbers();c=cuts.make
    try:run('ekw7',[c(0),c(2),'frame','moving','case'],m|{'tc':lambda:c(5),'ekmi':lambda *xs:True})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Unbounded energy setting silently sampled')
    cases+=1
    return dict(cases=cases,all_64_shared_witness_slots_and_five_exposed_roles_checked=True,native_real_values_not_individual_records=True,unbounded_settings_refused=True)

@lru_cache(None)
def heading_checks():
    rows={'eisvv':{('inquiry','ekw7','case')},'eisth':{('inquiry','ekug','ekuf','case')}}
    cases=perturb(lambda model:run('ekxc',['inquiry','case'],model),{n:relation(r) for n,r in rows.items()},rows)
    for root in ('ekxa','ekxb'):assert run(root,['inquiry','case'],{n:relation(r) for n,r in rows.items()});cases+=1
    for wrong in ({('inquiry','ekuf','ekug','case')},{('other','ekug','ekuf','case')},{('inquiry','ekug','ekuf','other')}):
        assert not run('ekxc',['inquiry','case'],{'eisvv':relation(rows['eisvv']),'eisth':relation(wrong)});cases+=1
    heading={'eisdv':{('heading','section','part','paper',Q(2),Q(8),'case')},'eisdw':{('heading','section','ekxc','case')},'ue':{('previous','heading','case'),('heading','following','case')}}
    cases+=perturb(lambda model:run('ekxd',[],model),{n:relation(r) for n,r in heading.items()},heading)
    for n,x in [('eisvw','section'),('eistk','part'),('eisvw','previous'),('eisvw','following')]:
        assert not run('ekxd',[],{n:lambda *xs:True for n in heading}|{n:lambda x=x:x});cases+=1
    return dict(cases=cases,energy_transformation_and_pressure_theory_are_distinct_topics=True,same_inquiry_and_context=True,section_eight_hierarchy_and_both_order_edges=True,quoted_physics_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][201]
    assert u['text']=='§ 8. Transformation der Energie der Lichtstrahlen. Theorie des auf vollkommene Spiegel ausgeübten Strahlungsdruckes.'
    assert u['id']=='einstein-1905:u0202' and u['kind']=='heading' and not u['math_ids']
    assert digest(u['text'].encode())==u['text_sha256'] and inv['units'][226]['text'].startswith('§ 9.')
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])))
    assert s['source_nonblank_characters']==103
    return dict(version='einstein-eighth-section-heading-reading-v1',reviewer='assistant_visual_and_text_review',pages=['913'],segments=[s],division=dict(level=2,ordinal=8,parent='eispb',first=u['id'],last='einstein-1905:u0226',next_boundary='einstein-1905:u0227'),observations=['原刊913頁上端で二行の第八節見出しを視認した。第一主題後の句点と第二主題のTheorie、auf vollkommene Spiegel ausgeübtenという力を受ける対象と方向を保持する。','見出しは二主題を案内する。物理設定や印刷された法則の真理をここで断言せず、既存本文の明示した平均・完全鏡の読みへ接続する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE,'scripts/check_eighth_section_heading.py')})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==408 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[406])==selection_binding(old,[406])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/optical-problem-method-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eihq','eisdv','eisdw','ekmi','ekug','ekuf','ekq3','eisub','eisth','eistk'}<=deps
    assert not {'eir3','ekbw','ekbx','ekby','ekbz'}&deps
    for root,forbidden_names in [('ekw7',{'ekpn','ekps','ekpl'}),('ekug',{'ekt4','ekuf'})]:
        names={d['name'] for d in extract_document(new.document,roots=[root],statement_indices=[]).document['declarations']}
        assert not names&forbidden_names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=5,new_general_relations=1,new_reference_individuals=1,previous_407_statements_and_meanings_preserved=True,settings_do_not_assume_energy_ratio_or_pressure_formula=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('correspondence',correspondence_checks),('heading',heading_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_mean_light_energy','compose_doppler_infinity','compose_two_postulates','check_clock_site_time','check_problem_series_reduction','check_body_rest_field_method','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_eighth_section_heading.py','scripts/check_eighth_section_heading.py','tests/test_eighth_section_heading.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record()['segments'][0]
    return dict(status='eighth_section_energy_and_pressure_subjects_connected',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
