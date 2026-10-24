"""Check the concrete law identity, common-law requirements and authored inference."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb,forbidden
from scripts.compose_convective_relativity_claim import *

DOC='docs/convective-relativity-claim-v1.md';SOURCE='data/einstein-convective-relativity-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/convective-velocity-interpretation-v1.json','reports/convective-transformation-claim-v1.json','reports/conjecture-laws-v1.json','reports/velocity-composition-claim-v1.json')
CONSTANTS={'eiswq':'claim','eisv5':'lorentz','eisbf':'electro','eisbg':'optics','eisbl':'mechanics','eisbk':'rest','eisv6':'ninth','eisoq':'fifth','eiscg':'principle','eiswk':'foundation','zqb':'five','rd':'author','eirf':'paper','ri':'case'}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),'a','b','law','common','inquiry','other','wrong']))
POINTS=('case','other')
PARTS={'ek2r':('eifj','eify'),'ek2s':('ejnp','ejpc'),'ek2t':('ekz7','ek2j')}
BOUNDS={'ek2n':{'ekyv','ekyo','ekyq','ek2l'},'ek2o':{'eifb'},'ek2p':{'ek2o'},'ek2q':{'ek2n','ek2p'},'ek2u':{'ek2r','ek2q'},'ek2x':{'ek2s','ek2j','ek2r','eifj','ekyx','ek2t','ek2u'},'ek2z':{'ek2y'}}|{n:set(parts) for n,parts in PARTS.items()}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document;d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jcrarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jcrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jcrpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,vs,m,domain=PEOPLE):
    doc,slots=fixture(root);assert len(vs)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jcrpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def law_checks():
    rows={'ekyv':{('lorentz','case')},'eiswa':{('lorentz','inquiry','ekyo','ekyq','case')},'eisdi':{('lorentz','inquiry','case')},'eisbe':{('law','electro','lorentz','case')},'eiswp':{('law','ek2l','ekyq','case')}}
    good={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('ek2n',['law','lorentz','case'],m),good,rows)
    # Distinct witnesses cannot split the adoption from its foundation status.
    assert not run('ek2n',['law','lorentz','case'],good|{'eisdi':relation({('lorentz','other','case')})});cases+=1
    rows={'ek2n':{('law','lorentz','case')},'ek2p':{('law','case')}}
    good={n:relation(rs) for n,rs in rows.items()}|{'eisbm':lambda *xs:False}
    cases+=perturb(lambda m:run('ek2q',[],m),good,rows)
    assert not run('ek2q',[],good|{'ek2p':relation({('other','case')})});cases+=1
    for branch in ('electro','mechanics'):
        assert not run('ek2q',[],good|{'eisbm':relation({('rest',branch,'a','case')})});cases+=1
    assert run('ek2p',['law','case'],{'ek2o':relation({('law','common','case')})})
    assert not run('ek2p',['law','case'],{'ek2o':relation({('other','common','case')})});cases+=2
    for name in ('ek2n','ek2p','eisbm'):
        try:run('ek2q',[],good|{name:forbidden})
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown foundation accepted')
        cases+=1
    return dict(cases=cases,same_concrete_conditional_law_and_inquiry=True,common_theory_not_fixed_to_lorentz=True,absolute_rest_part_retained=True)

@lru_cache(None)
def common_law_checks():
    # Native eiff/eife/eifd/sar, with only frame eligibility abstracted.
    # Two values distinguish every law/frame/representation binder without N^arity expansion.
    domain=('a','b');ctx='case';law='a';theory='a'
    rows={'eisbe':{('a','a',theory,ctx),('b','b',theory,ctx)},'eisbh':{(theory,ctx)},'eifb':{(a,ctx) for a in domain},'eisbi':{(l,f,ctx) for l in domain for f in domain},'eisbj':{(h,ctx) for h in domain},'vh':{(h,f,f,ctx) for h in domain for f in domain},'vi':{('a',r,ctx) for r in domain}}
    base={'eisbf':lambda:'a','eisbg':lambda:'b'}|{n:relation(rs) for n,rs in rows.items()}
    check=lambda m:run('ek2o',[law,theory,ctx],m,domain)
    assert check(base);cases=1
    for n in ('eisbe','eisbh','eifb','eisbi','eisbj','vh'):
        assert not check(base|{n:lambda *xs:False});cases+=1
    # Every law governs in every frame. The one basis law alone is insufficient.
    for row in rows['eisbi']:
        assert not check(base|{'eisbi':relation(rows['eisbi']-{row})});cases+=1
    for row in rows['vh']:
        assert not check(base|{'vh':relation(rows['vh']-{row})});cases+=1
    # Candidate nonconformity in all representations is allowed; only mismatch fails.
    assert check(base|{'vi':lambda *xs:False});cases+=1
    for row in rows['vi']:
        assert not check(base|{'vi':relation(rows['vi']-{row})});cases+=1
    # A surplus corresponding representation also belongs to the all-pairs comparison.
    assert not check(base|{'vh':lambda *xs:xs[-1]==ctx,'vi':relation({('a','a',ctx)})});cases+=1
    for n in rows:
        try:check(base|{n:forbidden})
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(('Unknown common-law input',n))
        cases+=1
    return dict(cases=cases,native_complete_common_law_body=True,both_branches_and_frames_and_histories_nonempty=True,all_laws_all_frames_all_corresponding_representations=True,nonconforming_candidates_not_excluded=True)

@lru_cache(None)
def content_checks():
    cases=0
    for root,parts in PARTS.items():
        for a,b in product((False,True),repeat=2):
            m={n:lambda x=x:Content(POINTS,(x,not x)) for n,x in zip(parts,(a,b))}
            assert run(root,[],m)==(a and b);cases+=1
    for a,b in product((False,True),repeat=2):
        m={n:lambda x=x:Content(POINTS,(x,not x)) for n,x in zip(('ek2r','ek2q'),(a,b))}
        assert run('ek2u',[],m)==((not a) or b);cases+=1
    return dict(cases=cases,all_contents_share_one_context=True,kinematic_principles_are_contents_not_adoption_actions=True,conditional_conclusion_not_unconditional=True)

@lru_cache(None)
def presentation_checks():
    rows={'eisov':{('claim','author','fifth','ek2s','paper','case')},'zc':{('claim','author','ek2s','ek2j','ninth','case'),('claim','author','ek2t','ek2u','ninth','case')},'uh':{('claim','author','ek2j','ninth','case'),('claim','author','ek2u','ninth','case')},'ug':{('claim','author','ek2r','ninth','case')},'eisch':{('principle','eifj','ninth','case')},'eiswm':{('claim','author','foundation','ekyx','paper','case')},'ui':{('author','claim','case')}}
    good={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('ek2x',[],m),good,rows)
    assert run('ek2x',[],good|{n:forbidden for n in BOUNDS['ek2x']});cases+=1
    rows={'eir3':{('claim','author','paper','ek2y','case')},'ue':{('five','claim','case')}};good={n:relation(rs) for n,rs in rows.items()}
    cases+=perturb(lambda m:run('ek2z',[],m),good,rows)
    assert not run('ek2z',[],{n:lambda *xs:True for n in rows}|{'zqb':lambda:'claim'});cases+=1
    return dict(cases=cases,fifth_section_inference_and_same_velocity_identification=True,assumed_principles_and_qualified_conclusion=True,same_foundation_anaphora_and_proven_status=True,quoted_physics_not_evaluated=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][236];math={m['id']:m for m in inv['math']};ms=[math[n] for n in u['math_ids']]
    assert u['id']=='einstein-1905:u0237' and digest(u['text'].encode())==u['text_sha256']
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    return dict(version='einstein-convective-relativity-reading-v1',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s','',re.sub(r'\[M\d+\]','',u['text']))),observations=['原刊917頁の先頭段落を視認した。Da、§5の挿入、三速度、nichts anderes、kで測った電気的担体の速度、so ... damit gezeigt、unter Zugrundelegung unserer、Lorentz理論の電気力学の基礎、相対性原理への適合を一文として確認した。','原理の仮定を保持し、示されたという著者提示とその物理的な正しさを区別する。基礎法則の同じ内容を完全な共通体系へ結ぶ採用読解を明示し、Lorentz理論全体への帰結へ拡張しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements'][:INDEX]==before.document['statements'] and len(after.document['statements'])==INDEX+1
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[410])==selection_binding(before,[410]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/convective-velocity-interpretation-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert len(GLOBAL)==32 and len(MEANINGS)==13 and len(PRIMITIVES)==2
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=13,new_general_relations=1,new_reference_constants=1,added_statement=INDEX,all_411_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('law',law_checks),('common_law',common_law_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_convective_relativity_claim.py','scripts/check_convective_relativity_claim.py','tests/test_convective_relativity_claim.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py'}
    return dict(status='convective_relativity_claim_connected_for_whole_unit_review',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
