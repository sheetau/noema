"""Check dated populations, public ruler identity and common priority criteria."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_humanity_release import ROOT,LIBRARY,BASIS,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/humanity-release-v1.md';READING='data/humanity-release-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/government-release-v1.json','reports/qualified-prince-frame-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','data/government-release-reading-v1.json')
DOMAIN=('actor','person','already','dead','newborn','other','firstgroup','lastgroup','government','othergovernment','community','othercommunity','activity','otheractivity','office','otheroffice')
HUMANS={'actor','person','already','dead','newborn','other'}
FIRST={'actor','person','already','dead'};LAST={'actor','person','already','newborn'}
SCENES=('reference','candidate','early','before','acted','last','now','later')
ORDER=('early','before','acted','last','now','later')
ENAMES=('actor','activity','government','firstgroup','lastgroup','community','reference','candidate','before','acted','last')

def z(n):return 'k z'+n+'[]'
def names(ns):return ' '.join(z(n) for n in ns)
EPISODE=names(ENAMES)
SELECTED=EPISODE+' '+names(('office','now'))+' p zassessed'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),state_boundary=False):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:
            x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r zassessed[a d] c.'
    if state_boundary:
        extra+='r zfree[a a a d d] c.'
        stub='d zstub[government a community a reference d] h[a] e[i[person a][b point[k zfree[v government v person v community v reference v point]]]].'
        next(x for x in d['declarations'] if x['name']=='r5zn')['body']=parse('p:'+extra+stub)['declarations'][-1]['body']
    additions=parse('p:'+extra)['declarations'];d['declarations']=additions+d['declarations']
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in additions))),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p in HUMANS,
        h246c=lambda g,p,r:r=='reference' and p in (FIRST if g=='firstgroup' else LAST if g=='lastgroup' else set()),
        h256o=lambda p,c,t:c=='candidate' and p in (FIRST if t=='before' else LAST if t=='last' else {'actor'} if t=='acted' else set()),
        h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in ORDER,
        ic=lambda a,b,c:c=='candidate' and a in ORDER and b in ORDER and ORDER.index(a)<ORDER.index(b),
        h237n=lambda g,c,t:(g,c)==('government','community'),h256s=lambda g,c,t:(g,c)==('government','community'),
        ag=lambda a,f,l:(a,f,l)==('activity','before','last'),dg=lambda a,t:(a,t)==('activity','acted'),
        df=lambda p,a,t:(p,a,t)==('actor','activity','acted'),
        h26n2=lambda p,a,g,t:(p,a,g,t)==('actor','activity','government','acted'),
        zfree=lambda g,p,c,r,t:(g,c,r)==('government','community','reference') and ((t=='last' and p in LAST) or (t=='before' and p in ('actor','already'))),
        r5ze=lambda g,p,c,r,t:(g,c,r,t)==('government','community','reference','before') and p in FIRST,
        r5zr=lambda g,p,c,r,t:(g,c,r,t)==('government','community','reference','before') and p in ('person','dead'),
        r5zs=lambda a,x,g,p,c,r,h,f,t,l:(a,x,g,p,c,r,h,f,t,l)==('actor','activity','government','person','community','reference','candidate','before','acted','last'),
        zassessed=lambda *a:True)
    return v

@lru_cache(None)
def population_checks():
    q=''.join('q[k r5z3['+names((g,'reference','candidate',t))+']].' for g,t in (('firstgroup','before'),('lastgroup','last')))
    d=fixture(('r5z3',),q);rows={}
    for case in ('baseline','missing_dead_before','missing_newborn_after','dead_in_last','newborn_in_first','nonhuman','empty','wrong_reference','wrong_history','outside_history'):
        v=base(d);old=v['h246c']
        if case=='missing_dead_before':v['h246c']=lambda g,p,r:old(g,p,r) and p!='dead'
        if case=='missing_newborn_after':v['h246c']=lambda g,p,r:old(g,p,r) and p!='newborn'
        if case=='dead_in_last':v['h246c']=lambda g,p,r:old(g,p,r) or (g,p,r)==('lastgroup','dead','reference')
        if case=='newborn_in_first':v['h246c']=lambda g,p,r:old(g,p,r) or (g,p,r)==('firstgroup','newborn','reference')
        if case=='nonhuman':v['h246c']=lambda g,p,r:old(g,p,r) or p=='government'
        if case=='empty':v['h246c']=lambda *a:False;v['h256o']=lambda *a:False
        if case=='wrong_reference':v['zreference']=lambda:'now'
        if case=='wrong_history':v['zcandidate']=lambda:'now'
        if case=='outside_history':v['h257z']=lambda *a:False
        got=run(d,v);want=[case in ('baseline','missing_newborn_after','dead_in_last'),case in ('baseline','missing_dead_before','newborn_in_first')]
        assert got==want,(case,got);rows[case]=got
    # Stable populations may use one and the same group identity.
    same=fixture(('r5z3',),q.replace(z('lastgroup'),z('firstgroup')))
    v=base(same);v['h256o']=lambda p,c,t:c=='candidate' and t in ('before','last') and p in FIRST
    assert run(same,v)==[True,True]
    for n in ('aa','h246c','h256o','h257z'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,same_group_allowed_for_stable_population=True,all_living_humans_exactly=True,unknown_rejected=True)

@lru_cache(None)
def episode_checks():
    d=fixture(('r5z4',),'q[k r5z4['+EPISODE+']].',('r5ze','r5zr','r5zs'),True);rows={}
    for case in ('baseline','no_surviving_release','death_only','missing_newborn_freedom','missing_dead_assessment','missing_survivor_effect','missing_previously_free_freedom','actor_not_alive','private_action','no_process','action_after_result','cyclic_order','missing_newborn_membership'):
        v=base(d)
        if case=='no_surviving_release':v['r5zr']=lambda g,p,c,r,t:p=='dead'
        if case=='death_only':
            old=v['zfree'];v['zfree']=lambda g,p,c,r,t:old(g,p,c,r,t) or (p=='person' and t=='before');v['r5zr']=lambda g,p,c,r,t:p=='dead'
        if case in ('missing_newborn_freedom','missing_previously_free_freedom'):
            old=v['zfree'];excluded='newborn' if case=='missing_newborn_freedom' else 'already'
            v['zfree']=lambda g,p,c,r,t:old(g,p,c,r,t) and not(p==excluded and t=='last')
        if case=='missing_dead_assessment':v['r5ze']=lambda g,p,c,r,t:p!='dead'
        if case=='missing_survivor_effect':v['r5zs']=lambda *a:False
        if case=='actor_not_alive':
            old=v['h256o'];v['h256o']=lambda p,c,t:old(p,c,t) and t!='acted'
        if case=='private_action':v['h26n2']=lambda *a:False
        if case=='no_process':v['ag']=lambda *a:False
        if case=='action_after_result':v['zacted']=lambda:'later'
        if case=='cyclic_order':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ORDER and b in ORDER
        if case=='missing_newborn_membership':
            old=v['h246c'];v['h246c']=lambda g,p,r:old(g,p,r) and p!='newborn'
        got=run(d,v);assert got==[case=='baseline'],(case,got);rows[case]=got[0]
    for pos in range(10):
        v=base(d);old=v['r5zs']
        def wrong(*a):
            b=list(a);b[pos]='other' if pos<5 else 'later';return old(*b)
        v['r5zs']=wrong;assert run(d,v)==[False],pos
    for n in ('h256o','h246c','r5ze','r5zr','r5zs','zfree','h26n2','ic'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,newborn_has_no_prebirth_transition=True,dead_has_no_postmortem_state=True,
        all_ten_personal_transition_arguments_bound=True,unknown_rejected=True,
        boundary='Previously checked assessment r5ze, active tutelage r5zr and transition r5zs are exact scalar boundaries. r5zn uses a native function body with a five-argument truth boundary. Dated populations, temporal order, public act and final collective freedom execute natively; previous native norm/cause integration is pinned.')

@lru_cache(None)
def ruler_checks():
    d=fixture(('r5z6',),'q[k r5z6['+names(('actor','office','government','community','acted'))+']].');rows={}
    def model():
        v=base(d);v.update(cf=lambda p,o,t:(p,o,t)==('actor','office','acted'),hzwn=lambda p,o,t:(p,o,t)==('actor','office','acted'),
            hzxf=lambda p,o,c,t:(p,o,c,t)==('actor','office','community','acted'),h234d=lambda o,c,t:(o,c,t)==('office','community','acted'),
            h234e=lambda *a:False,h234f=lambda o,c,t:(o,c,t)==('office','community','acted'),
            h256p=lambda o,g,t:(o,g,t)==('office','government','acted'),h256q=lambda *a:False,
            h256r=lambda p,o,g,t:(p,o,g,t)==('actor','office','government','acted'))
        return v
    v=model();assert run(d,v)==[True]
    for n in ('cf','hzwn','hzxf','h234d','h234f','h256p','h256r','h237n','h256s'):
        v=model();v[n]=lambda *a:False;assert run(d,v)==[False],n;rows[n]=False
    for kind in ('higher','incomparable'):
        v=model();v['h256p']=lambda o,g,t:o in ('office','otheroffice') and (g,t)==('government','acted')
        v['h256q']=lambda a,b,g,t:kind=='higher' and (a,b,g,t)==('otheroffice','office','government','acted')
        assert run(d,v)==[False];rows[kind]=False
    for pos in range(4):
        v=model();old=v['h256r']
        def wrong(*a):
            b=list(a);b[pos]='other' if pos<3 else 'now';return old(*b)
        v['h256r']=wrong;assert run(d,v)==[False]
    for n in ('cf','h256r','h256q','h256p','h256s'):
        v=model();v[n]=unknown;rejects(d,v)
    return dict(rejected=rows,native_monarch_and_highest_institutional_office=True,same_holder_office_government_time=True,unknown_rejected=True)

@lru_cache(None)
def first_checks():
    domain=('actor','other','activity','otheractivity','government','othergovernment','community','othercommunity')
    d=fixture(('r52b',),'q[k r52b['+names(('actor','activity','reference','candidate','now','last'))+' p zassessed]].',('r5z5',));rows={}
    key=('actor','activity','government','community','reference','candidate','last')
    for case in ('baseline','earlier_other_government','earlier_same_person','simultaneous','later','incomplete_assessment','only_later_unassessed','no_achievement','result_after_anchor','cyclic_order'):
        v=base(d);events={key}
        if case in ('earlier_other_government','earlier_same_person','simultaneous','later'):
            events.add(('actor' if case=='earlier_same_person' else 'other','otheractivity','othergovernment','othercommunity','reference','candidate',
                'last' if case=='simultaneous' else 'later' if case=='later' else 'early'))
        if case=='incomplete_assessment':v['zassessed']=lambda p,t:(p,t)!=('other','early')
        if case=='only_later_unassessed':v['zassessed']=lambda p,t:t!='later'
        if case=='no_achievement':events=set()
        if case=='result_after_anchor':v['znow']=lambda:'before'
        if case=='cyclic_order':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ORDER and b in ORDER
        v['r5z5']=lambda *a:a in events
        got=run(d,v,domain);assert got==[case in ('baseline','simultaneous','later','only_later_unassessed')],(case,got);rows[case]=got[0]
    for n in ('r5z5','zassessed'):
        v=base(d);v['r5z5']=lambda *a:a==key;v[n]=unknown;rejects(d,v,domain)
    # Independently invert the specialization and recover the entire original AST.
    old=parents()[0].entries['rob']['declaration'];new=deepcopy(catalog().entries['r5z7']['declaration'])
    inserted=deepcopy(old['parameters'][3:5])
    for p,n in zip(inserted,('restoredtarget','restoredgoal')):p['name']=n
    def restore(x):
        if isinstance(x,list):return [restore(y) for y in x]
        if isinstance(x,dict):
            y={k:restore(v) for k,v in x.items()}
            if y.get('kind')=='apply' and y.get('function')==dict(kind='variable',name=new['parameters'][3]['name']):
                a=y['arguments'];assert len(a)==3
                y['arguments']=a[:2]+[dict(kind='variable',name=p['name']) for p in inserted]+a[2:]
            return y
        return x
    new['body']=restore(new['body']);new['parameters'][3]['sort']=deepcopy(old['parameters'][5]['sort'])
    new['parameters'][3:3]=inserted;new['name']='rob'
    # Formatting assigns canonical binder names after the two inserted binders.
    recovered=deepcopy(parents()[0].document)
    recovered.update(declarations=[new if d['name']=='rob' else d for d in closure(recovered,('rob',))],statements=[])
    assert next(d for d in parse(format_graph(recovered,'compact'))['declarations'] if d['name']=='rob')==old
    # The existential event wrapper shares every supplied argument with its witness.
    q='q[k r5z5['+names(key)+']].'
    wrapper=fixture(('r5z5',),q,('r5z4',));v=base(wrapper);v['r5z4']=lambda *a:a==ENAMES
    assert run(wrapper,v)==[True]
    for pos in (0,1,2,5,6,7,10):
        v=base(wrapper)
        shifted=list(ENAMES);shifted[pos]='other' if pos<6 else 'later'
        v['r5z4']=lambda *a:a==tuple(shifted);assert run(wrapper,v)==[False],pos
    return dict(cases=rows,rob_entire_ast_recovered_by_inverse_specialization=True,dated_populations_inside_each_event=True,
        same_event_existential_wrapper=True,unknown_rejected=True,
        boundary='Priority executes native r5z7/r52a/r52b with r5z5 event boundaries. No fixed population is passed across dates. r5z5 existential binding is separately checked against exact r5z4 arguments; dated population/event semantics are checked above.')

@lru_cache(None)
def selected_checks():
    q='q[k r52c['+SELECTED+']].q[k r52d['+SELECTED+' '+z('person')+']].'
    d=fixture(('r52c','r52d'),q,('r5z4','r5z6','r52b','r5zv'),True);rows=[]
    expected={
        'r5z4':ENAMES,'r5z6':('actor','office','government','community','acted'),
        'r52b':('actor','activity','reference','candidate','now','last'),
        'r5zv':('actor','activity','government','person','community','reference','candidate','now')}
    def model(bits=(True,)*4):
        v=base(d)
        for (n,key),on in zip(expected.items(),bits):
            if n=='r52b':v[n]=lambda *a,key=key,on=on:on and a[:-1]==key and a[-1]('other','early') is True
            else:v[n]=lambda *a,key=key,on=on:on and a==key
        return v
    for bits in product((False,True),repeat=4):
        got=run(d,model(bits));assert got==[all(bits[:3]),all(bits)],(bits,got)
        rows.append(dict(episode=bits[0],ruler=bits[1],first=bits[2],benefit=bits[3],result=got))
    for person in ('dead','newborn','already'):
        v=model();v['zperson']=lambda:person;v['r5zv']=lambda *a:True
        assert run(d,v)==[True,False],person
    v=model();v['zassessed']=lambda *a:False;assert run(d,v)==[False,False]
    for n in expected:
        v=model();v[n]=unknown;rejects(d,v)
    return dict(sixteen_cases=rows,same_selected_ruler_event_and_personal_benefit=True,nonbeneficiary_cohorts_rejected=True,
        assessment_function_preserved=True,unknown_rejected=True,
        boundary='The independently checked episode, ruler, priority and benefit are scalar boundaries with exact argument tuples. Native r52c/d retain common bindings, before/after membership and prior nonfreedom. No actual gratitude is asserted.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('der zuerst');end=u['text'].index('zu bedienen.')+len('zu bedienen.')
    return dict(status='dated_humanity_and_same_public_ruler_release_dependency',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=list(SOURCES),
        unresolved=['前件の同じ君主・役職・共同体と具体的功績の本文束縛','比較評価の供給、恩恵・功績の記述と両集団からの称揚の全基準',
            'wenigstens等の提示・独立した名称評価・著者帰属・sondern・一文全体と後続'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[2].document['statements'])==112
    assert all(n not in MEANINGS for n,e in c.entries.items() if e['kind']=='primitive')
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,parent_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('population',population_checks),('episode',episode_checks),('ruler',ruler_checks),('first',first_checks),('selected',selected_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_humanity_release.py','scripts/check_humanity_release.py','tests/test_humanity_release.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='dated_human_populations_same_ruler_and_first_release_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
