"""Check candidates, shared presuppositions, rejection and discourse scope."""
from functools import lru_cache
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_seat_questions import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,build

DOC='docs/seat-questions-v1.md';SOURCE='data/einstein-seat-questions-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p910-0.jpg'
DEPENDENCIES=('reports/unipolar-machine-v1.json','reports/asymmetry-resolution-v1.json','reports/auxiliary-role-v1.json')
CONSTANTS={'ri':'case','rd':'author','eirf':'paper','zno':'scope','eisqw':'theory','eisak':'oldview','eisri':'parenthesis','eisq7':'first','eisrs':'second'}
DOMAIN=('a','b');POINTS=('case','other')

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds={'ejzt'}
    if mode=='scope':bounds|={'ekan'}
    if mode=='binding':bounds|={'ekao'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jsq'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    individuals=DOMAIN+tuple(x for x in CONSTANTS.values() if x!='case')+('other',)
    row=evaluate_document(doc,individuals=individuals,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=100000,memoize_definitions=True,memoize_expressions=True)[0]
    return row.get('value',row.get('answers'))

def model(rows):return {n:relation(rs) for n,rs in rows.items()}
def signature(question,premise):
    assert isinstance(question,QuestionValue) and isinstance(premise,Content)
    return tuple(question.function(x) for x in DOMAIN),premise.values

@lru_cache(None)
def question_checks():
    cases=0
    for bits in product((False,True),repeat=2):
        rows={('a','b',x,'case') for x,yes in zip(DOMAIN,bits) if yes};m={'eisrl':relation(rows)}
        assert run('ekal',['a','b','case'],m)==[[x] for x,yes in zip(DOMAIN,bits) if yes];cases+=1
        for args in (['b','b','case'],['a','a','case'],['a','b','other']):
            assert run('ekal',args,m)==[];cases+=1
    unknowns(lambda m:run('ekal',['a','b','case'],m),{'eisrl':lambda *xs:True},('eisrl',))
    return dict(cases=cases,native_question_candidates_not_request_or_existence=True)

@lru_cache(None)
def premise_checks():
    cases=0;subsets=[{x for x,y in zip(DOMAIN,b) if y} for b in product((False,True),repeat=2)]
    for sources,located in product(subsets,repeat=2):
        rs={'eisrm':{(x,'a','b','case') for x in sources},'eisrn':{(x,'a','b','case') for x in located}}
        assert run('ekam',['a','b'],model(rs))==bool(sources&located);cases+=1
    rs={'eisrm':{('a','a','b','case')},'eisrn':{('a','b','b','case')}};m=model(rs)
    cases+=perturb(lambda mm:run('ekam',['a','b'],mm),m,rs)
    assert not run('ekam',['a','b'],m|{'ri':lambda:'other'});cases+=1
    unknowns(lambda mm:run('ekam',['a','b'],mm),m,rs)
    return dict(cases=cases,same_bearer_concept_setting_and_world_required=True)

@lru_cache(None)
def transition_checks():
    cases=0
    # Rejecting a premise is an attributed theoretical stance, independent of
    # how the finite interpretation assigns its truth or proposed candidates.
    for answers,present,needed,old,rejected in product((False,True),repeat=5):
        expected=((answers,False),(present,False))
        def need(qq,pp,ctx):return ctx=='case' and signature(qq,pp)==expected and needed
        def prior(view,qq,pp,ctx):return view=='oldview' and ctx=='case' and signature(qq,pp)==expected and old
        def reject(theory,pp,ctx):return theory=='theory' and ctx=='case' and pp.values==expected[1] and rejected
        m={'eisrl':lambda c,s,site,ctx:answers and (c,s,site,ctx)==('a','b','a','case'),
           'eisrm':lambda src,c,s,ctx:present and (src,c,s,ctx)==('a','a','b','case'),
           'eisrn':relation({('a','a','b','case')}),'eisro':need,'eisrq':prior,'eisrp':reject}
        assert run('ekan',['theory','oldview','a','b','case'],m)==(needed and old and rejected);cases+=1
        if all((answers,present,needed,old,rejected)):
            for i in range(5):
                args=['theory','oldview','a','b','case'];args[i]='other' if i==4 else 'b'
                if i==3:args[i]='a'
                assert not run('ekan',args,m);cases+=1
            unknowns(lambda mm:run('ekan',['theory','oldview','a','b','case'],mm),m,m)
    subsets=[{x for x,y in zip(DOMAIN,b) if y} for b in product((False,True),repeat=2)]
    for settings,judged in product(subsets,repeat=2):
        rs={'eisrk':{('a',s,'case') for s in settings},'ekan':{('theory','oldview','a',s,'case') for s in judged}}
        assert run('ekao',['theory','oldview','a','case'],model(rs),'scope')==bool(settings and settings<=judged);cases+=1
    # The concept of the force, all inquiries and the parenthesis share one witness.
    base={'eisqy':{('theory','paper','eigj','scope','case')}}
    for concept,topic,example in product(DOMAIN,repeat=3):
        rs=base|{'ejzt':{('theory',concept,'case')},'ekao':{('theory','oldview',topic,'case')},'eisrr':{('eisrk',example,'ekaj','paper','parenthesis','case')}}
        assert run('ekap',[],model(rs),'binding')==(concept==topic==example);cases+=1
    rs=base|{'ejzt':{('theory','a','case')},'ekao':{('theory','oldview','a','case')},'eisrr':{('eisrk','a','ekaj','paper','parenthesis','case')}}
    cases+=perturb(lambda mm:run('ekap',[],mm,'binding'),model(rs),rs)
    assert run('ekap',[],model(rs)|{'ekaj':forbidden},'binding');cases+=1
    return dict(cases=cases,rejection_distinct_from_empty_answers_false_premise_or_ignorance=True,nonempty_all_settings_and_shared_concept=True,prior_view_and_new_theory_not_physical_time=True)

@lru_cache(None)
def presentation_checks():
    fixtures={'ekaq':{'uh':{('second','author','ekap','scope','case')},'eisrb':{('first','second','author','ekac','ekap','scope','case')}},'ekas':{'eir3':{('second','author','paper','ekar','case')},'ue':{('first','second','case')}}};cases=0
    for n,rs in fixtures.items():cases+=perturb(lambda mm:run(n,[],mm),model(rs),rs)
    assert run('ekaq',[],model(fixtures['ekaq'])|{'ekap':forbidden,'ekac':forbidden});cases+=1
    assert not run('ekas',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'eisrs':lambda:'first'});cases+=1
    return dict(cases=cases,author_claim_and_additive_content_bound_not_question_utterance=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][176];text=u['text'];assert u['id']=='einstein-1905:u0177' and digest(text.encode())==u['text_sha256']
    ranges=[(0,178),(178,266),(266,285),(285,len(text))]
    return dict(status='whole_unit_source_collated_semantic_judgment_separate',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(text)],text=text,math=[],clauses=[dict(range=[a,b],text=text[a:b]) for a,b in ranges],source_nonblank_characters=len(re.sub(r'\s','',text)),observations=['原刊910頁と固定転記で第一文の非対称性解消から第二文まで照合する。','Sitzの引用符を保持し、本来的な発生源という前提を要する問いとして明示的に読む。問いへの言及と著者の発問は区別する。','括弧の単極機は問題の適用先として取り上げる。Auchと理論の交替によるwerden、前提の拒絶によるgegenstandslosを接続する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==363 and new.document['statements'][:INDEX]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[360,361])==selection_binding(old,[360,361])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ejzt','ejyg','eisqs','eisrr','ekaj','eisrb','ekac'}<=names
    core=parse(read(CORE))
    for style in ('compact','full'):
        b=format_graph(core,style);assert parse(b)==parse(transcribe(b,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=8,new_references=1,old_362_statements_preserved=True,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('question',question_checks),('premise',premise_checks),('transition',transition_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_rod_methods','compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_seat_questions.py','scripts/check_seat_questions.py','tests/test_seat_questions.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=[178,len(s['text'])],source=s['text'][178:],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    return dict(status='seat_question_presupposition_rejection_and_additive_presentation_connected',document=FULL,**results,alignment=dict(segments=[row]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
