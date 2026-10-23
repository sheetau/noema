"""Check referent preservation, hypothetical adoption and two naming purposes."""
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_rest_frame_introduction import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDICES,build

DOC='docs/rest-frame-introduction-v1.md';SOURCE='data/einstein-rest-frame-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=('data/electrodynamics-title-review-v1.json','data/einstein-author-credit-review-v1.json','data/einstein-opening-paragraph-review-v1.json','data/einstein-principles-paragraph-review-v1.json','data/einstein-kinematics-paragraph-review-v1.json','data/einstein-kinematics-heading-review-v1.json','data/einstein-simultaneity-heading-review-v1.json')
DOMAIN=('frame','other','author','paper','first','second','heading','name')
def forbidden(*args):raise ValueError('Unknown rest-frame-introduction input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrf'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrfpoint',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrfpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,model,point='a'):
    m=dict(model,jrfpoint=lambda:point)
    return evaluate_document(doc,individuals=DOMAIN,situations=('a','b'),
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,values,model,point='a'):
    doc,slots=fixture(name);assert len(values)==len(slots)
    return evaluate(doc,model|{n:(lambda x=x:x) for n,x in zip(slots,values)},point)

def base():return dict(ra=lambda:'frame',rd=lambda:'author',eirf=lambda:'paper',ri=lambda:'a',eisec=lambda:'first',eised=lambda:'second',eisd2=lambda:'heading',eiseb=lambda:'name')
def setup(point='a'):
    rows={'eisd3':{('first','frame','paper',point)},'ug':{('first','author','eiht','paper',point)}}
    return base()|{n:relation(rs) for n,rs in rows.items()},rows
def naming(point='a'):
    rows={'eisd4':{('second','author','name','frame','paper',point)},'eisd5':{('author','eih2',goal,'paper',point) for goal in ('eihy','eihz')}}
    return base()|{n:relation(rs) for n,rs in rows.items()},rows

@lru_cache(None)
def introduction_checks():
    count=0
    for coordinates,newton in product((False,True),repeat=2):
        m=base()|{'va':relation({('frame',)} if coordinates else set()),'eisbd':relation({('frame','a')} if newton else set())}
        assert run('eiht',[],m)==(coordinates and newton);count+=1
    for row in (('other','a'),('frame','b')):
        assert not run('eiht',[],base()|{'va':lambda x:True,'eisbd':relation({row})});count+=1
    for point in ('a','b'):
        m,rows=setup(point)
        for bits in product((False,True),repeat=2):
            assert run('eihu',[],m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)},point)==all(bits);count+=1
        for n,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eihu',[],m|{n:relation({bad})},point);count+=1
            try:run('eihu',[],m|{n:forbidden},point)
            except ValueError as e:assert 'Unknown rest-frame-introduction' in str(e)
            else:raise AssertionError('Unknown adoption accepted')
        # Neither truth nor falsity of the physical condition replaces the adoption act.
        for truth in (False,True):
            assert run('eihu',[],m|{'va':lambda x:truth,'eisbd':lambda *xs:truth},point);count+=1
    return dict(cases=count,existing_newton_frame_condition_reused=True,same_introduced_referent=True,physical_condition_not_asserted_by_adoption=True,unknown_inputs_rejected=4)

@lru_cache(None)
def purpose_checks():
    count=0
    for point in ('a','b'):
        m,rows=naming(point);goals=sorted(rows['eisd5'])
        for action,first,second in product((False,True),repeat=3):
            trial=m|{'eisd4':relation(rows['eisd4'] if action else set()),'eisd5':relation({r for r,on in zip(goals,(first,second)) if on})}
            assert run('eih3',[],trial,point)==(action and first and second);count+=1
        for name,rs in rows.items():
            for row in rs:
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run('eih3',[],m|{name:relation((rs-{row})|{bad})},point);count+=1
        # Both goal propositions can be false or unknown without losing the intention to attain them.
        for truth in (False,True):
            assert run('eih3',[],m|{'eisd6':lambda *xs:truth,'eisea':lambda *xs:truth},point);count+=1
        for name in ('eisd4','eisd5'):
            try:run('eih3',[],m|{name:forbidden},point)
            except ValueError as e:assert 'Unknown rest-frame-introduction' in str(e)
            else:raise AssertionError('Unknown naming or purpose accepted')
    m,_=naming();m['ra']=lambda:'other';assert not run('eih3',[],m);count+=1
    return dict(cases=count,same_naming_act_and_both_purposes=True,same_frame_not_replaced=True,goal_achievement_not_required=True,unknown_inputs_rejected=4)

@lru_cache(None)
def goal_content_checks():
    count=0
    for coordinates,planned in product((False,True),repeat=2):
        m=base()|{'va':relation({('other',)} if coordinates else set()),'eisd7':relation({('other','paper','second','a')} if planned else set())}
        assert run('eihx',['other','a'],m)==(coordinates and planned);count+=1
    m=base()|{'va':lambda x:True,'eisd7':lambda *xs:True}
    assert not run('eihx',['frame','a'],m);count+=1
    row=('other','paper','second','a')
    for slot in range(len(row)):
        bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert not run('eihx',['other','a'],m|{'eisd7':relation({bad})});count+=1
    for target,primitive,row in (('eihy','eisd6',('name','frame','eihx','paper','a')),('eihz','eisea',('name','frame','paper','a'))):
        m=base()|{primitive:relation({row})};assert run(target,[],m);count+=1
        for slot in range(len(row)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not run(target,[],m|{primitive:relation({bad})});count+=1
        try:run(target,[],m|{primitive:forbidden})
        except ValueError as e:assert 'Unknown rest-frame-introduction' in str(e)
        else:raise AssertionError('Unknown goal content accepted')
    return dict(cases=count,prospective_other_frame_class_not_current_existence=True,distinction_and_conception_clarity_different_goals=True,unknown_inputs_rejected=2)

@lru_cache(None)
def presentation_checks():
    count=0
    for path in (CORE,FULL):
        original=parse(read(path))
        for which,node,message,before in ((0,'first','eihv','heading'),(1,'second','eih4','first')):
            doc=dict(original,statements=[original['statements'][-2+which]])
            rows={'eir3':{(node,'author','paper',message,'a')},'ue':{(before,node,'a')}};m=base()|{n:relation(rs) for n,rs in rows.items()}
            for bits in product((False,True),repeat=2):
                assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
            for name,rs in rows.items():
                row=next(iter(rs))
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{name:relation({bad})});count+=1
            assert not evaluate(doc,m|{'eir3':lambda *xs:True,'ue':lambda *xs:True,('eisec' if which==0 else 'eised'):lambda x=before:x});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']}
    assert ds['eihv']['body']['force']=='direct' and ds['eih4']['body']['force']=='assert'
    return dict(cases=count,setup_directive_and_naming_assertion_distinguished=True,same_author_document_and_order=True,quoted_contents_not_executed=True)

def source_record():
    u=json.loads(read(INVENTORY))['units'][7];assert u['id']=='einstein-1905:u0008' and len(u['text'])==266 and not u['math_ids']
    paths={INVENTORY,DOC,'scripts/check_rest_frame_introduction.py','artifacts/einstein-principles-v1/retrieval.json'}
    for row in json.loads(read('artifacts/einstein-principles-v1/retrieval.json'))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-rest-frame-source-reading-v1',reviewer='assistant_visual_and_text_review',source_unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,266],source_nonblank_characters=236,pages=['892'],images=['artifacts/einstein-principles-v1/page-892.jpg'],sentence_ranges=[dict(range=[a,b],text=u['text'][a:b],nonblank_characters=sum(not c.isspace() for c in u['text'][a:b])) for a,b in ((0,95),(96,266))],math=[],observations=['原刊892頁の第一節見出しの直後の二文を固定転記へ照合した。Es liegeからgelten.までが設定、Wir nennenからSystem“.までが命名と目的である。','原刊の行末分割Präzi-sierungは転記のPräzisierungへ対応する。引用されたruhende System、Newtonの方程式、後で導入する系との区別と観念の明確化を確認した。','この段落には数式・著者脚注はない。前の見出しと次の物質点の位置指定の文は別単位である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==223
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert ann.find('ruhende System','de')['matches'][0]['symbol']=='eiseb'
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert {'ra','eifb','eisbd','ug','eir3'}<=set(ds)
    assert ds['eiht']['body']['body']['arguments'][0]==dict(kind='call',symbol='ra',arguments=[])
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=221,prior_reviews_preserved=True,same_existing_frame_reference=True,designation_form_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(introduction=introduction_checks(),purposes=purpose_checks(),goals=goal_content_checks(),presentation=presentation_checks(),structure=structure_checks())
    u=json.loads(read(INVENTORY))['units'][7]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_rest_frame_introduction.py','scripts/check_rest_frame_introduction.py','tests/test_rest_frame_introduction.py','scripts/compose_kinematics_headings.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='rest_frame_introduction_and_purposive_naming_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[a,b],source=u['text'][a:b],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for a,b in ((0,95),(96,266))]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
