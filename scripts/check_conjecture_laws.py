"""Check qualified-frame quantifiers, law validity and the negative conjunct."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.compose_conjecture_laws import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build

DOC='docs/conjecture-laws-v1.md';SOURCE='data/einstein-principles-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json')
DOMAIN=('a','b')
def forbidden(*xs):raise ValueError('Unknown conjecture input')

def source_record():
    inventory=json.loads(read(INVENTORY));unit=inventory['units'][3];text=unit['text'];spans=((0,522),(523,889),(890,1081),(1082,1425))
    assert unit['id']=='einstein-1905:u0004' and text[704:].startswith('Voraussetzung einführen')
    math=[m for m in inventory['math'] if m['id'] in unit['math_ids']]
    assert len(math)==1 and '<mi>V</mi>' in math[0]['mathml']
    paths={INVENTORY,DOC,'scripts/check_conjecture_laws.py','artifacts/written-sources-v1/einstein-1905.html'}
    for path in ('artifacts/einstein-opening-v1/retrieval.json','artifacts/einstein-principles-v1/retrieval.json'):
        paths.add(path)
        for row in json.loads(read(path))['sources']:
            assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-principles-source-reading-v1',reviewer='assistant_visual_and_text_review',source_unit=unit['id'],unit_sha256=unit['text_sha256'],text=text,range=[0,len(text)],source_nonblank_characters=sum(not c.isspace() for c in text),pages=['891','892'],images=['artifacts/einstein-opening-v1/page-891.jpg','artifacts/einstein-principles-v1/page-892.jpg'],sentence_ranges=[dict(range=[a,b],text=text[a:b],nonblank_characters=sum(not c.isspace() for c in text[a:b])) for a,b in spans],math=math,observations=[
        '原刊891頁下段と892頁上段を視認し、四文を固定転記と照合した。行末分綴と頁跨ぎを除き語句・否定・留保・括弧・数式記号を保持する。',
        '頁跨ぎは第二文[704]のVoraussetzungの直前である。A0002は頁境界で、著者の脚注ではない。',
        'M0001は大文字V。vや数値へ置換せず、元のMathMLとハッシュを保持する。',
        '第四文末zugeordnet wird.までが同じ段落。次のDie zu entwickelnde Theorieはu0005で別に始まる。',
        'wie dies für die Größen erster Ordnung bereits erwiesen istの既証の範囲を、推測全体の無限定な証明へ広げない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    if name=='eifj':abstract(doc,{'eifi','eifg'})
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='jaas'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));calls.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=calls)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jaactx',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jaactx',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,values,model,context='a'):
    doc,slots=fixture(name);assert len(values)==len(slots)
    m=dict(model,jaactx=lambda:context);m.update({n:(lambda x=x:x) for n,x in zip(slots,values)})
    return evaluate_document(doc,individuals=DOMAIN,situations=DOMAIN,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(qualified=DOMAIN,valid=None,conforms=None,available=None,histories=DOMAIN,branches=DOMAIN,complete=True,theory='a',context='a'):
    valid=set(product(DOMAIN,repeat=2)) if valid is None else valid
    conforms=set(product(DOMAIN,repeat=2)) if conforms is None else conforms
    available={(frame,rep) for frame,rep in zip(DOMAIN,DOMAIN)} if available is None else available
    return dict(va=lambda frame:frame in DOMAIN,eisbd=lambda frame,ctx:frame in qualified and ctx==context,
        eisbf=lambda:'a',eisbg=lambda:'b',eisbe=lambda law,branch,t,ctx:branch in branches and law==branch and t==theory and ctx==context,
        eisbh=lambda t,ctx:complete and (t,ctx)==(theory,context),eisbi=lambda law,frame,ctx:(law,frame) in valid and ctx==context,
        eisbj=lambda h,ctx:h in histories and ctx==context,vh=lambda h,frame,rep,ctx:h in histories and (frame,rep) in available and ctx==context,
        vi=lambda law,rep,ctx:(law,rep) in conforms and ctx==context,eisbk=lambda:'a',eisbl=lambda:'b',eisbm=lambda *xs:False)

@lru_cache(None)
def frame_and_law_checks():
    count=0;cells=list(product(DOMAIN,repeat=2))
    for mask in product((False,True),repeat=2):
        qualified={x for x,on in zip(DOMAIN,mask) if on}
        for bits in product((False,True),repeat=4):
            valid={cell for cell,on in zip(cells,bits) if on}
            expected=bool(qualified) and all((law,frame) in valid for law in DOMAIN for frame in qualified)
            assert run('eiff',['a','a'],model(qualified=qualified,valid=valid))==expected;count+=1
    for branches in ((),('a',),('b',)):
        assert not run('eiff',['a','a'],model(branches=branches));count+=1
    for changes in (dict(complete=False),dict(histories=()),dict(available=set())):
        assert not run('eiff',['a','a'],model(**changes));count+=1
    # Moving the same quantified theory or context does not hard-code the default witness.
    for theory,context in product(DOMAIN,repeat=2):
        m=model(theory=theory,context=context)
        assert run('eiff',[theory,context],m)
        assert not run('eiff',['b' if theory=='a' else 'a',context],m)
        assert not run('eiff',[theory,'b' if context=='a' else 'a'],m)
        assert run('eifg',[],m,context=context);count+=4
    for bits in product((False,True),repeat=2):
        m=model();m['va']=lambda frame:bits[0] and frame=='a';m['eisbd']=lambda frame,ctx:bits[1] and (frame,ctx)==('a','a')
        assert run('eifb',['a','a'],m)==all(bits);count+=1
    # Both family memberships may apply to the same law; this is inclusive union.
    for bits in product((False,True),repeat=2):
        for law,theory,context in product(DOMAIN,repeat=3):
            m=model();m['eisbe']=lambda l,b,t,c:(l,t,c)==(law,theory,context) and bits[DOMAIN.index(b)]
            assert run('eifc',[law,theory,context],m)==any(bits);count+=1
    return dict(cases=count,all_qualified_frames_not_one_pair=True,physical_validity_distinct_from_invariance=True,empty_scope_rejected=True,overlapping_branches_allowed=True,existential_theory_and_shared_context=True)

@lru_cache(None)
def representation_checks():
    cells=list(product(DOMAIN,repeat=2));count=0
    patterns=(set(),{('a','a')},{('b','b')},{('a','a'),('b','b')},{('a','b'),('b','a')},set(cells))
    for available in patterns:
        left={rep for frame,rep in available if frame=='a'};right={rep for frame,rep in available if frame=='b'}
        for bits in product((False,True),repeat=4):
            conforms={cell for cell,on in zip(cells,bits) if on}
            expected=bool(left and right) and all(((law,a) in conforms)==((law,b) in conforms) for law in DOMAIN for a in left for b in right)
            m=model(available=available,conforms=conforms,histories=('a',))
            assert run('eifd',['a','a','b','a'],m)==expected
            assert run('eiff',['a','a'],m)==expected;count+=2
    # Equally disallowed candidate histories still preserve a law's condition.
    assert run('eiff',['a','a'],model(conforms=set()))
    # Equal conditions alone are insufficient if the purported laws do not hold.
    assert not run('eiff',['a','a'],model(conforms=set(),valid=set()))
    return dict(cases=count,all_representations_not_coordinate_identity=True,missing_representation_rejected=True,disallowed_candidates_retained=True,native_sar_saq_sap=True)

@lru_cache(None)
def negative_and_content_checks():
    cells=list(product(DOMAIN,repeat=2));count=0
    for bits in product((False,True),repeat=4):
        properties={cell for cell,on in zip(cells,bits) if on};m=model()
        m['eisbm']=lambda concept,branch,prop,ctx:concept=='a' and ctx=='a' and (branch,prop) in properties
        for branch in DOMAIN:
            assert run('eifh',[branch,'a'],m)==not_any(properties,branch);count+=1
        assert run('eifi',[],m)==(not properties);count+=1
        assert run('eifi',[],m,context='b');count+=1
    for left,right in product((False,True),repeat=2):
        m=dict(eifi=lambda:Content(DOMAIN,(left,not left)),eifg=lambda:Content(DOMAIN,(right,not right)))
        assert run('eifj',[],m)==(left and right)
        assert run('eifj',[],m,context='b')==((not left) and (not right));count+=2
    for name in ('eisbd','eisbe','eisbh','eisbi','eisbj','vh','vi'):
        m=model();m[name]=forbidden
        try:run('eiff',['a','a'],m)
        except ValueError as e:assert 'Unknown conjecture' in str(e)
        else:raise AssertionError('Unknown law input accepted: '+name)
    m=model();m['eisbm']=forbidden
    try:run('eifi',[],m)
    except ValueError as e:assert 'Unknown conjecture' in str(e)
    else:raise AssertionError('Unknown property input treated as absence')
    return dict(cases=count,unknown_inputs_rejected=8,both_branches_have_no_corresponding_property=True,negation_not_failed_detection=True,shared_content_point=True)

def not_any(properties,branch):return not any(b==branch for b,p in properties)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==213
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'sar','saq','sap'}<=names and not names&{'sat','saw','vb','vc','eisax','eisak'}
    assert not doc['statements']
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=213,no_new_author_assertion=True,prior_reviews_preserved=True,same_law_composition_reused_without_pair_restriction=True,source_collated_pages=['891','892'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    result=dict(scope=frame_and_law_checks(),representations=representation_checks(),negative=negative_and_content_checks(),structure=structure_checks())
    unit=json.loads(read(INVENTORY))['units'][3];span=[148,460];assert unit['text'][span[0]:span[1]].startswith('daß dem') and unit['text'][span[0]:span[1]].endswith('gelten')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_conjecture_laws.py','scripts/check_conjecture_laws.py','tests/test_conjecture_laws.py','scripts/check_coordinate_correspondence.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py','scripts/compose_electrodynamics_title.py'}
    return dict(status='conjecture_internal_content_composed_presentation_pending',document=FULL,**result,alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,source=unit['text'][span[0]:span[1]],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),remaining=['類似例と地球の運動検出失敗が推測へ導く関係','推測・対照としての提示','一次の量では既証という範囲','第一文全体と段落全体の意味判断'],verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
