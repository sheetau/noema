"""Check shared quantified settings and the full transformation presentation."""
from copy import deepcopy
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_ninth_section_opening import lifted
from scripts.check_convective_foundation_reading import walk
from scripts.check_problem_series_reduction import collapse
from scripts.check_clock_site_time import relation,perturb,forbidden
from scripts.compose_convective_transformation_claim import *

DOC='docs/convective-transformation-claim-v1.md';SOURCE='data/einstein-convective-transformation-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p916-0.jpg'
DEPENDENCIES=('reports/convective-transformed-quantities-v1.json','reports/ninth-section-opening-v1.json','reports/field-transformation-application-v1.json','reports/field-symmetry-conclusion-v1.json')
CONSTANTS={'eiswn':'intro','zqa':'six','eiswo':'where','zqb':'five','eiswf':'opening','eiswk':'foundation','eisms':'third','zno':'sixth','eisv6':'ninth','rd':'author','eirf':'paper','ri':'case'}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),'a','b','other','wrong']))
LAWS={'ekz3':'ekyq','ekz4':'ekzz','ekz5':'ekz2','ekz7':'ekz6'}
BOUNDS={n:{'ekzx',law} for n,law in LAWS.items()}|{'ekz6':{'ekzz','ekz2'},'ek2c':{'ekzc','ekz3','ekz4','ekz5','ekz7','ejeh','ejvm'},'ek2e':{'ek2d'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,flatten=False):
    doc=deepcopy(boundary(root));doc=collapse(doc) if flatten else doc;d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jctcarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jctcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jctcpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,vs,m,flatten=False):
    doc,slots=fixture(root,flatten);assert len(vs)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jctcpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=40000)[0]['value']

@lru_cache(None)
def binder_checks():
    cases=0
    for root,law in LAWS.items():
        for pivot in range(len(CASES)):
            doc,d,slots,var,body=lifted(boundary(root),root,pivot,len(CASES),'forall')
            calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'}
            hyp=calls['ekzx']['arguments'];con=calls[law]['arguments']
            assert (hyp[:-1] if root=='ekz3' else hyp)==con
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            def rows(args,picks,values=env):return {tuple((values|{var:pick})[x['name']] for x in args) for pick in picks}
            def evaluate(selected,allowed,values=env,lawcontext=None):
                hs=rows(hyp,selected,values);ls=rows(con,allowed,values if lawcontext is None else lawcontext)
                m={n:lambda x=values[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ekzx':lambda *xs:xs in hs,law:lambda *xs:xs in ls}
                return evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=m,max_steps=20000)[0]['value']
            for selected,allowed in [(('a','b'),('a','b')),(('a','b'),('a',)),(('b',),('a',)),((),()),(('a','b'),())]:
                assert evaluate(selected,allowed)==(rows(con,selected)<=rows(con,allowed));cases+=1
            # Context belongs to the one physical setting in both sides.
            ctx=next(p['name'] for p in d['parameters'] if p['sort']=='situation')
            assert not evaluate(('a','b'),('a','b'),lawcontext=env|{ctx:'other'});cases+=1
        try:run(root,[],{'ekzx':lambda *xs:True,law:lambda *xs:True})
        except ValueError as e:assert any(s in str(e) for s in ('Finite function domain','rational number domain'))
        else:raise AssertionError('Unbounded settings accepted')
        cases+=1
    vs=['case' if t=='d' else 'a' for n,t in SETTING];rows={'ekzz':{tuple(vs)},'ekz2':{tuple(vs)}}
    good={n:lambda *xs,rs=rs:xs in rs for n,rs in rows.items()};assert run('ekz6',vs,good,True);cases+=1
    for i in range(len(vs)):
        changed=vs.copy();changed[i]='other' if SETTING[i][1]=='d' else 'b'
        assert not run('ekz6',changed,good,True)
        assert run('ekz6',changed,{n:lambda *xs:xs==tuple(changed) for n in rows},True);cases+=2
    for n in rows:assert not run('ekz6',vs,good|{n:lambda *xs:False},True);cases+=1
    return dict(cases=cases,all_32_binders_in_four_contents_checked=True,old_law_projects_same_global_without_speed=True,same_33_parameters_in_both_results=True,one_physical_context_preserved=True,unbounded_settings_rejected=True)

@lru_cache(None)
def presentation_checks():
    nodes=('intro','six','where','five')
    rows={'ug':{('intro','author','ekzc','ninth','case')},'eiswm':{('intro','author','opening','ekzc','paper','case')},'zc':{('intro','author','ekz3','ekz7','ninth','case')},'eisov':{('intro','author','third','ejeh','paper','case'),('intro','author','sixth','ejvm','paper','case')},'eisox':{('six','ekz4','case'),('five','ekz5','case')},'uh':{('five','author','ekz5','ninth','case')},'uf':{('author',a,b,'case') for a,b in zip(nodes,nodes[1:])},'ue':{(a,b,'case') for a,b in zip(nodes,nodes[1:])}}
    good={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('ek2c',[],m),good,rows)
    constants=('eiswn','zqa','eiswo','zqb')
    for i,a in enumerate(constants):
        for b in constants[i+1:]:assert not run('ek2c',[],{n:lambda *xs:True for n in rows}|{a:lambda b=b:CONSTANTS[b]});cases+=1
    # Quoted physics can be false or unavailable without changing its attribution.
    assert run('ek2c',[],good|{n:forbidden for n in BOUNDS['ek2c']});cases+=1
    outer={'eir3':{('intro','author','paper','ek2d','case')},'ue':{('foundation','intro','case')}}
    cases+=perturb(lambda m:run('ek2e',[],m),{n:relation(rs) for n,rs in outer.items()},outer)
    assert not run('ek2e',[],{n:lambda *xs:True for n in outer}|{'eiswk':lambda:'intro'});cases+=1
    return dict(cases=cases,assumption_anaphora_two_sections_inference_and_displays_connected=True,where_explanation_and_order_preserved=True,attribution_does_not_execute_physics=True,no_bidirectional_rewrite_added=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][232:236]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[math[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    ns='{http://www.w3.org/1998/Math/MathML}'
    fractions=lambda mid:[tuple(''.join(x.itertext()) for x in f) for f in ET.fromstring(math[mid]['mathml']).iter(ns+'mfrac')]
    curl=fractions('M0389');expected=[('∂X′','∂τ'),('∂N′','∂η'),('∂M′','∂ζ'),('∂L′','∂τ'),('∂Y′','∂ζ'),('∂Z′','∂η'),('∂Y′','∂τ'),('∂L′','∂ζ'),('∂N′','∂ξ'),('∂M′','∂τ'),('∂Z′','∂ξ'),('∂X′','∂ζ'),('∂Z′','∂τ'),('∂M′','∂ξ'),('∂L′','∂η'),('∂N′','∂τ'),('∂X′','∂η'),('∂Y′','∂ξ')]
    assert [i for i,f in enumerate(curl) if f==('1','V')]==[0,7,14]
    assert [f for f in curl if f!=('1','V')]==expected
    ops=[''.join(n.itertext()) for n in ET.fromstring(math['M0389']['mathml']).iter(ns+'mo')];assert ops.count('=')==ops.count('−')==6
    formula=fractions('M0390');assert formula==[('ux−v','1−uxvV2'),('uxv','V2'),('uy','β(1−uxvV2)'),('uxv','V2'),('∂X′','∂ξ'),('∂Y′','∂η'),('∂Z′','∂ζ'),('v\xa0ux','V2'),('uz','β(1−uxvV2)'),('uxv','V2')]
    assert [''.join(n.itertext()) for n in ET.fromstring(math['M0390']['mathml']).iter(ns+'mo')].count('=')==5
    for mid,want in [('M0387','K'),('M0388','k')]:assert ''.join(ET.fromstring(math[mid]['mathml']).itertext())==want
    return dict(version='einstein-convective-transformation-reading-v1',reviewer='assistant_visual_and_text_review',pages=['916'],segments=segments,curl_derivative_order=[list(x) for x in expected],formula_fraction_order=[list(x) for x in formula],observations=['原刊916頁下半分でTransformiert manからコロンまで、三行二列の六式、wobei、三速度の縦配置とρ′の連鎖等式を視認した。先行の原系方程式と次頁のDaから始まる物理的解釈の間にある一文として読む。','welche im System K gelten mögenという仮定、§3と§6への二つの参照、kを行先とする変換、so erhält manの結果導入を保持する。','M0389の磁気側には原刊でも1/Vがなく、電気側の三箇所だけにある。M0390は三速度と同じρ′の二関係の五等式であり、MathML内の行順は三速度の意味上の順序を変えない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==411 and after.document['statements'][:INDEX]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[408,409])==selection_binding(before,[408,409]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/convective-transformed-quantities-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    hypothesis={d['name'] for d in extract_document(core(),roots=['ekzx'],statement_indices=[]).document['declarations']}
    assert not hypothesis&{'semf','semd','seme','sent','ekx3','ekyc','eiah','ekzu','ekzv'}
    current=next(d for d in core()['declarations'] if d['name']=='ek2a')
    assert {x['symbol'] for x in walk(current['body']) if x.get('kind')=='call'}=={'ug','eiswn','rd','ekzc','eisv6','eiswm','eiswf','eirf','zc','ekz3','ekz7','eisov','eisms','ejeh','zno','ejvm'}
    assert len(CASES)==32 and all(not fs for fs,_ in PRIMITIVES.values())
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_constants=2,added_statement=INDEX,all_410_prior_statements_and_meanings_preserved=True,quoted_inference_and_unmodified_printed_equations=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binder',binder_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_convective_transformation_claim.py','scripts/check_convective_transformation_claim.py','tests/test_convective_transformation_claim.py','scripts/check_ninth_section_opening.py','scripts/check_clock_site_time.py','scripts/check_convective_foundation_reading.py','scripts/check_problem_series_reduction.py'}
    return dict(status='convective_transformation_connected_for_whole_unit_review',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
