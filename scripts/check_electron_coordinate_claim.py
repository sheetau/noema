"""Check same-setting bindings and authored presentation of u0245."""
from copy import deepcopy
from functools import lru_cache
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_moving_law_task as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_coordinate_claim import *

DOC='docs/electron-coordinate-claim-v1.md';SOURCE='data/einstein-electron-coordinate-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DEPENDENCIES=('reports/electron-representative-scope-v1.json','reports/electron-comoving-history-v1.json','reports/electron-coordinate-normalization-v1.json','reports/electron-moving-law-task-v1.json')
old=prior.old;forbidden=old.forbidden
CONSTANTS=prior.CONSTANTS|{'eisxv':'event','eisxw':'choice','eisxx':'restclaim','eisxy':'comoving','eisx4':'kname','eisx5':'xname','eisnb':'Kname','eism5':'tname','yn':'x'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values()]))
BOUNDS={'ek6f':{'ek56'},'ek6g':{'ek6f'},'ek6i':{'ek6f','ek4r','ek6h'},'ek6j':{'ek6g'},'ek6k':{'ek6e','ek6j','ek6g','ek4y','ek6i'},'ek6m':{'ek6l'},'ek6n':{'ek6f','ek5w'},'ek6o':{'ek5x'},'ek6p':{'ek6n'},'ek6q':{'ek6n','ek6o'},'ek6r':{'ek6p','ek6q'},'ek6s':{'ek6r','ek6k','ek6u'},'ek6t':{'ek6h'},'ek6u':{'ek6n','ek6t'},'ek6w':{'ek6v'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jecarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jecpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jecpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jeccapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jeccapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,vs,m):
    doc,slots=fixture(root);assert len(vs)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jecpoint':lambda:'case','jeccapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def connection_checks():
    by,m,c,r,key=old.setup();by=by.copy();by.update(frame='frame',event='event');vs=[by[n] for n,t in SETTING];sk=key(vs);cases=0
    mm=m|{'ra':lambda:'frame','ek56':lambda *xs:key(xs)==sk}
    assert run('ek6f',vs,mm);cases+=1
    for name in ('frame','event'):
        altered=vs.copy();altered[[n for n,t in SETTING].index(name)]='other'
        assert not run('ek6f',altered,mm|{'ek56':lambda *xs:True});cases+=1
    assert not run('ek6f',vs,mm|{'ek56':lambda *xs:False});cases+=1
    old.old.reject(lambda:run('ek6f',vs,mm|{'ek56':forbidden}),unknown=True);cases+=1
    refs={'eisxy':'comoving','tc':c(5),'eisxz':old.old.point(c,(2,-1,4,3)),'eisx2':by['domain'],'eisx3':by['curve']}
    combined=[*vs,*(refs[n] for n in ('eisxy','tc','eisxz','eisx2','eisx3'))];ck=key(combined)
    mm=m|{n:lambda x=x:x for n,x in refs.items()}|{'ek6f':lambda *xs:key(xs)==sk,'ek5w':lambda *xs:key(xs)==ck,'ek5x':lambda *xs:key(xs)==ck}
    for root in ('ek6n','ek6o'):
        assert run(root,vs,mm);cases+=1
        for n in ('eisxy','tc','eisxz','eisx2','eisx3'):
            changed='other' if n=='eisxy' else c(7) if n=='tc' else old.old.point(c,(9,9,9,9)) if n=='eisxz' else old.fn(old.sort(DOMAIN),lambda t:False) if n=='eisx2' else old.fn(old.sort(CURVE),lambda t:old.old.point(c,(9,9,9,9)))
            assert not run(root,vs,mm|{n:lambda x=changed:x});cases+=1
        for part in BOUNDS[root]:
            assert not run(root,vs,mm|{part:lambda *xs:False});cases+=1
            old.old.reject(lambda:run(root,vs,mm|{part:forbidden}),unknown=True);cases+=1
        for i,(name,typ) in enumerate(SETTING):
            if typ in ('a','d'):changed='other'
            elif typ=='b':changed=prior.Q(17)
            elif typ==R:changed=c(17)
            else:
                def different(spec):
                    if spec==old.old.RS:return c(17)
                    if spec=='truth':return False
                    return old.fn(spec,lambda *xs:different(spec['result']))
                changed=different(old.sort(typ))
            altered=vs.copy();altered[i]=changed
            assert not run(root,altered,mm);cases+=1
    for time in (-3,0,2):
        altered=vs.copy();altered[[n for n,t in SETTING].index('point')]=old.old.point(c,(7,8,9,time))
        assert r(run('ek6h',altered,m))==time;cases+=1
        assert run('ek6t',altered,m|{'ek6h':lambda *xs:c(time)})==(time==0);cases+=1
    for existence in (False,True):
        for implication in (False,True):
            assert run('ek6r',[],{'ek6p':lambda:Content(('case','other'),(existence,False)),'ek6q':lambda:Content(('case','other'),(implication,False))})==(existence and implication);cases+=1
    return dict(cases=cases,same_event_frame_and_all_setting_slots=True,one_chosen_frame_light_offset_and_histories_in_both_sides=True,nonzero_offset_not_forced_to_zero=True,nonempty_premise_distinct_from_rest_conclusion=True)

@lru_cache(None)
def presentation_checks():
    groups=[
     ('ek6i',{'eisd4':{('choice','author','xname','x','paper','case'),('choice','author','Kname','frame','paper','case')},'eiswy':{('speedname','ek6f','ek4r','paper','tenth','case'),('tname','ek6f','ek6h','paper','tenth','case')}}),
     ('ek6j',{'ug':{('choice','author','ek6g','tenth','case')}}),
     ('ek6k',{'uh':{('choice','author','ek6e','tenth','case')},'eism4':{('author','ek6j','tenth','paper','case')},'eisnx':{('choice','author','matter','ek6g','tenth','case')},'zct':{('choice','author','ek6e','choice','tenth','case')},'eisra':{('choice','author','paper','task','ek4y','ek6g','tenth','case')}}),
     ('ek6s',{'uh':{('restclaim','author','ek6r','tenth','case')},'zdg':{('restclaim','author','ek6r','tenth','case')},'eisra':{('restclaim','author','paper','choice','ek6k','ek6r','tenth','case')},'eisa5':{('restclaim','author','ek6r','ek6u','case')},'eisd4':{('restclaim','author','kname','comoving','paper','case')}}),
     ('ek6m',{'eir3':{('choice','author','paper','ek6l','case')},'ue':{('task','choice','case')}}),
     ('ek6w',{'eir3':{('restclaim','author','paper','ek6v','case')},'ue':{('choice','restclaim','case')}}),
    ];cases=0
    for root,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'frame','ek6j':lambda:Content(('case','other'),(True,False)),'ek6i':lambda:Content(('case','other'),(True,False))}
        cases+=perturb(lambda patch:run(root,[],patch),mm,rows)
        assert run(root,[],mm|{n:forbidden for n in BOUNDS[root] if not(root=='ek6k' and n in ('ek6j','ek6i'))});cases+=1
        if root=='ek6k':
            for n in ('ek6j','ek6i'):
                assert not run(root,[],mm|{n:lambda:Content(('case','other'),(False,True))});cases+=1
    for root,name in [('ek6m','eisxs'),('ek6w','eisxw')]:
        assert not run(root,[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,name:lambda:'choice' if root=='ek6m' else 'restclaim'});cases+=1
    return dict(cases=cases,permission_adoption_consideration_reason_and_evidence_distinct=True,quoted_physics_not_executed=True,same_conclusion_asserted_and_presented_as_evident=True,notation_parenthesis_and_authored_order_connected=True)

@lru_cache(None)
def binder_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jecunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    cases=0
    for root,kind,leftname,rightname in [('ek6g','exists','ek6f',None),('ek6p','exists','ek6n',None),('ek6q','forall','ek6n','ek6o'),('ek6u','forall','ek6n','ek6t')]:
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jecunit',parameters=[],result='individual'));doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc=extract_document(doc,roots=[root],statement_indices=[]).document
        binding=next(d for d in doc['declarations'] if d['name']==root)['body']
        original=binding['body'];names=[]
        while original['kind'] in ('exists','forall'):names.append(original['variable']);original=original['body']
        # Compact formatting alpha-renames binders. Check positions against
        # SETTING's independent field order, not their original Python names.
        assert len(names)==len(BOUND) and len(set(names))==len(names)
        bound_names=dict(zip((n for n,t in BOUND),names))
        expected=[dict(kind='call',symbol='ra',arguments=[]) if n=='frame' else dict(kind='variable',name=binding['variable']) if n=='context' else dict(kind='call',symbol='jecunit',arguments=[]) if n=='electricconversion' else dict(kind='call',symbol='eisxv',arguments=[]) if n=='event' else dict(kind='variable',name=bound_names['location' if n=='point' else n]) for n,t in SETTING]
        originalcall=original if kind=='exists' else original['arguments'][0]
        assert originalcall['arguments']==expected
        if rightname:assert original['arguments'][1]['arguments']==expected
        for pivot in range(len(BOUND)):
            f,d,slots,var,body=lifted(doc,root,pivot,len(BOUND),kind)
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            call=body if kind=='exists' else body['arguments'][0];assert call['symbol']==leftname
            if rightname:assert body['arguments'][1]['symbol']==rightname and body['arguments'][1]['arguments']==call['arguments']
            def rows(picks):return {tuple((env|{var:p})[x['name']] if x['kind']=='variable' else 'a' for x in call['arguments']) for p in picks}
            scenarios=[((),(),False),(('a',),(),True),(('b',),(),True)] if kind=='exists' else [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]
            for selected,allowed,want in scenarios:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ra':lambda:'a','eisxv':lambda:'a','jecunit':lambda:'a',leftname:lambda *xs:xs in rows(selected)}
                if rightname:mm[rightname]=lambda *xs:xs in rows(allowed)
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
        old.old.reject(lambda:run(root,[],{}));cases+=1
    return dict(cases=cases,all_29_witness_slots_and_33_argument_positions_checked=True,one_binder_at_a_time_two_value_diagnostics=True,native_full_function_domains_refused=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][244];assert u['id']=='einstein-1905:u0245';assert digest(u['text'].encode())==u['text_sha256']
    ms=[m for m in inv['math'] if m['id'] in u['math_ids']]
    assert len(ms)==7
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    collation='data/einstein-electron-coordinate-obligations-v1.json';priorreading=json.loads(read(collation));validate_hashes(ROOT,priorreading['source_sha256']);assert priorreading['text']==u['text']
    return dict(version='einstein-electron-coordinate-reading-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,collation,*priorreading['source_sha256'])})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==419 and after.document['statements'][:417]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[415,416])==selection_binding(before,[415,416]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-2]==json.loads(read('data/electron-representative-scope-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert len(MEANINGS)==18 and len(REFERENCES)==9
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=18,new_general_relations=0,new_reference_constants=9,new_statements=2,all_417_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('connection',connection_checks),('presentation',presentation_checks),('binders',binder_checks),('structure',structure_checks)]}
    helpers=('compose_point_particle_dynamics','compose_material_velocity','compose_limits','compose_material_relative_frame','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','check_electron_moving_law_task','check_electron_rest_law_claim','check_point_particle_dynamics','check_attached_material_charge','check_clock_site_time','check_rod_methods','check_ninth_section_opening','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_coordinate_claim.py','scripts/check_electron_coordinate_claim.py','tests/test_electron_coordinate_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='electron_coordinate_choice_and_comoving_rest_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
