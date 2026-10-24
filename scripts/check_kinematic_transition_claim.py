"""Check content identity, collective use, fixed reference and prospective force."""
from copy import deepcopy
from functools import lru_cache
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
from scripts.compose_kinematic_transition_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/kinematic-transition-claim-v1.md'
SOURCE='data/einstein-kinematic-transition-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILES=('artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg')
PRIORS=('data/einstein-parallel-group-u0149-review-v1.json',)
DEPENDENCIES=('reports/parallel-group-claim-v1.json','reports/first-principle-v1.json','reports/second-principle-v1.json','reports/kinematic-foundation-v1.json','reports/electrodynamics-title-v1.json')
CONSTANTS={'rd':'author','zm7':'task','znc':'theory','znb':'scope','ri':'now','eirf':'paper','zni':'summary','znj':'transition','zlu':'group'}
DOMAIN=tuple(dict.fromkeys(CONSTANTS.values()))+('a','b','inquiry','application','proof','extra')
POINTS=('before','now','later')
CHOICES=('jktone','jkttwo')


def finite_descriptions(node):
    """Diagnostic substitution only; production still quantifies all descriptions."""
    if isinstance(node,list):return [finite_descriptions(x) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='exists' and node.get('sort')==dict(kind='description',result='content'):
        def replace(x,term):
            if isinstance(x,list):return [replace(y,term) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind')=='variable' and x['name']==node['variable']:return deepcopy(term)
            return {k:replace(y,term) for k,y in x.items()}
        return dict(kind='or',arguments=[finite_descriptions(replace(node['body'],dict(kind='quote',body=dict(kind='call',symbol=n,arguments=[])))) for n in CHOICES])
    return {k:finite_descriptions(x) for k,x in node.items()}


@lru_cache(None)
def fixture(name,mode='finite'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    # The field classifiers have their own physical tests; keep eiscm native.
    abstract(doc,{'eihn','eie5'})
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode!='native':doc=finite_descriptions(doc)
    doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in CHOICES]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jkta'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jktpoint',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jktpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='finite',point='now'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jktpoint':lambda:point}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def summary_rows():
    return {'zna':{('author','task',i,'now') for i in ('a','b')},'eisox':{('a','jktone','now'),('b','jkttwo','now')},'zfr':{('proof','author',c,'now','scope') for c in CHOICES},'eiscr':{('theory',i,'now') for i in ('a','b')}}


def application_rows():
    return {'zna':{('author','task',i,'now') for i in ('a','b')},'eisox':{('a','jktone','now'),('b','jkttwo','now')},'eiscm':{('application','inquiry','later')},'eie5':{('inquiry','later')},'zt':{('application',c,'application','later') for c in CHOICES},'zng':{('author','application','later')}}


@lru_cache(None)
def summary_checks():
    rows=summary_rows();m={n:relation(rs) for n,rs in rows.items()}
    args=['author','task','theory','scope','now'];check=lambda pp:run('ejr6',args,pp)
    # Removing a requirement changes the contextual set rather than falsifying
    # a derivation, so its coverage is checked by additions and empty scope.
    count=perturb(check,m,{n:rs for n,rs in rows.items() if n!='zna'})
    for patch in ({'zna':lambda *xs:False},{'zna':relation(rows['zna']|{('author','task','extra','now')})},{'eisox':relation({('a','jkttwo','now'),('b','jkttwo','now')}),'zfr':relation({('proof','author','jktone','now','scope')})}):
        assert not check(m|patch);count+=1
    for i in (0,1,3,4):
        changed=args.copy();changed[i]='extra' if i!=4 else 'later';assert not run('ejr6',changed,m);count+=1
    # A separately described unused item is not added to the selected set.
    assert check(m|{'eisox':relation(rows['eisox']|{('extra','jktone','now')})});count+=1
    unknowns(check,m,('zna',))
    try:run('ejr4',['a','author','scope','now'],m,'native')
    except ValueError as e:assert 'description domain' in str(e),str(e)
    else:raise AssertionError('All closed contents silently reduced to two examples')
    return dict(cases=count,nonempty_all_task_relative_items_required=True,exact_item_content_and_same_derivation_scope=True,native_description_domain_refused=True,finite_substitution_is_diagnostic_only=True)


@lru_cache(None)
def application_checks():
    rows=application_rows();m={n:relation(rs) for n,rs in rows.items()}
    args=['author','task','application','application','now','later'];check=lambda pp:run('ejsa',args,pp)
    count=perturb(check,m,{n:rs for n,rs in rows.items() if n!='zna'})
    for patch in ({'zna':lambda *xs:False},{'zna':relation(rows['zna']|{('author','task','extra','now')})},{'zt':relation({('application','jktone','application','later'),('extra','jkttwo','extra','later')})}):
        assert not check(m|patch);count+=1
    assert run('ejsb',[],m,point='later');assert not run('ejsb',[],m,point='now');count+=2
    # Changes at the future stage cannot replace the present antecedent set.
    m2=m|{'zna':relation(rows['zna']|{('author','task','extra','later')})}
    assert run('ejsb',[],m2,point='later');count+=1
    assert not run('ejsb',[],m|{'zna':relation({('author','task','a','later')})},point='later');count+=1
    assert not check(m|{'eisox':relation({('a','jktone','later'),('b','jkttwo','later')})});count+=1
    unknowns(check,m,('zna',))
    try:run('ejr5',['a','application','application','now','later'],m,'native')
    except ValueError as e:assert 'description domain' in str(e)
    else:raise AssertionError('All application descriptions silently enumerated')
    return dict(cases=count,shared_application_can_contain_all_results=True,one_item_cannot_be_replaced_by_another=True,application_and_display_must_share_framework=True,current_requirements_fixed_across_future_evaluation=True,goal_can_be_unachieved_now=True)


@lru_cache(None)
def presentation_checks():
    groups=(('ejsc',{'uh':{('summary','author','ejr7','scope','now')}}),('ejsd',{'znh':{('transition','author','task','ejsb','now','scope','now')}}),('ejsg',{'eir3':{('summary','author','paper','ejse','now')},'ue':{('group','summary','now')}}),('ejsh',{'eir3':{('transition','author','paper','ejsf','now')},'ue':{('summary','transition','now')}}))
    count=0
    for name,rows in groups:
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda pp:run(name,[],pp),m,rows)
    rows=summary_rows()|{'eiscm':{('theory','inquiry','now')},'eihn':{('inquiry','now')},'zt':{('theory',p,'scope','now') for p in ('eion','eiot')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda pp:run('ejr7',[],pp),m,{n:rows[n] for n in ('eiscm','eihn','zt')})
    for name,symbol,previous in (('ejsg','zni','group'),('ejsh','znj','summary')):
        assert not run(name,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,symbol:lambda previous=previous:previous});count+=1
    return dict(cases=count,current_two_principles_and_kinematic_field_connected=True,same_author_task_stage_and_order=True,summary_and_goal_quotes_not_executed=True)


@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][149]
    assert u['id']=='einstein-1905:u0150' and not u['math_ids']
    assert digest(u['text'].encode())==u['text_sha256']
    s=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=[],source_nonblank_characters=len(re.sub(r'\s','',u['text'])))
    paths={INVENTORY,DOC,*FACSIMILES}
    return dict(version='einstein-kinematic-transition-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['907'],segments=[s],observations=['全文を原刊907頁の群の記述と第二部見出しの間に照合した。Wir haben nunからhergeleitetまでの総括、und gehen dazu überからzu zeigenまでの課題への移行を一文として保持する。','für uns notwendigenの課題相対性、unseren zwei Prinzipien、entsprechenden Kinematik、derenの同じ命題群への参照、Elektrodynamikの分野を確認した。','必要命題群の共同利用という読みを採り、原文にない有限一覧や各項目専用の一例を補わない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert not any(d['kind']=='primitive' for d in new.document['declarations'][len(old.document['declarations']):])
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[146,147,149])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,list(INDICES))['dependencies'])
    assert set(MEANINGS)|{'eion','eiot','eihn','eie5','eibf','eibs','eico','eisox','zfr','zna','zt','zng','znh'}<=names
    assert not names&{'s5r','s5s','zm5','zm6','zne','znf','saw','sbd'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=354,prior_judgments_preserved=True,old_unfinished_mapping_and_application_not_used=True,physical_fields_and_current_principles_transitively_connected=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('summary',summary_checks),('application',application_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_parallel_group_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_coordinate_correspondence','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_kinematic_transition_claim.py','scripts/check_kinematic_transition_claim.py','tests/test_kinematic_transition_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record()['segments'][0]
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation')])
    return dict(status='kinematic_summary_and_collective_application_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0150の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
