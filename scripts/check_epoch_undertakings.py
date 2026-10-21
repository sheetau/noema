"""Check covered periods, complete cohorts and earlier same-act mutual oaths."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_epoch_undertakings import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/epoch-undertakings-v1.json'
DOC='docs/epoch-undertakings-v1.md'
READING='data/epoch-undertakings-reading-v1.json'
PRIORS=('reports/successive-cohorts-v1.json','reports/promissory-oath-v1.json','reports/covenant-nullity-v1.json')
DOMAIN=('oldgroup','newgroup','early','late','agreement','alpha','beta','extra','future','act','otheract')
SCENES=('old','anchor','later','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)+'r zterms[j[a]] e.'
PAIR='k zoldgroup[] k znewgroup[] k zearly[] k zlate[] k zagreement[] k ztoutside[] k ztlater[]'
COHORT='k zoldgroup[] k znewgroup[] k zearly[] k zlate[] k ztoutside[] k ztlater[]'
FORM='q[k r5cb['+PAIR+' r[p zterms] i[person a][l[a][v person k zagreement[]]]]].'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v['h254z']=lambda agreement:'anchor'
    return v
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def frame(v,variant='baseline'):
    history=('old','anchor','later')
    v['h257z']=lambda ref,c,p:(ref,c)==('outside','later') and p in history
    v['ic']=lambda a,b,c:c=='later' and a in history and b in history and (a!=b if variant=='cycle' else history.index(a)<history.index(b))
    v['h26aa']=lambda ep,ref:ep in ('early','late') and ref==('anchor' if variant=='wrong_reference' else 'outside')
    spans={'early':{'old','anchor'},'late':{'later'}}
    if variant=='between_gap':spans['early']={'old'}
    if variant=='overlap':spans['late'].add('anchor')
    if variant=='inside_gap':spans={'early':{'old','later'},'late':{'anchor'}}
    if variant=='outside_history':spans['early'].add('outside')
    if variant=='reverse':spans={'early':{'later'},'late':{'old','anchor'}}
    v['h26ab']=lambda ep,ref,c,p:ref=='outside' and c==('anchor' if variant=='wrong_candidate' else 'later') and p in spans.get(ep,set())
    humans={'alpha','beta','extra','future'}
    alive={'old':{'alpha','beta','extra'},'anchor':{'alpha','beta','extra'},'later':{'beta','future'}}
    if variant=='same_members':alive['later']=set(alive['old'])
    if variant=='disjoint_members':alive['later']={'future'}
    if variant=='empty_next':alive['later']=set()
    v['aa']=lambda p:p in humans
    v['h256o']=lambda p,c,t:c=='later' and p in alive.get(t,set())
    members={'oldgroup':set(alive['old']),'newgroup':set(alive['later'])}
    if variant=='missing_member':members['oldgroup'].remove('extra')
    if variant=='nonhuman_member':members['oldgroup'].add('act')
    if variant=='extra_member':members['newgroup'].add('alpha')
    v['h246c']=lambda g,p,c:c=='later' and p in members.get(g,set())
    parties={'alpha','beta'}
    if variant=='future_party':parties.add('future')
    if variant=='single_party':parties={'alpha'}
    v['h26ac']=lambda ag,p,r:ag=='agreement' and p in parties and r=='anchor'
    if variant=='late_anchor':v['h254z']=lambda ag:'later'

@lru_cache(None)
def period_checks():
    doc=fixture(('r5bw',),'q[k r5bw[k ztoutside[] k ztlater[]]].');rows={}
    # Independent oracle: three ordered points partitioned into nonempty convex epochs.
    for assignment in product(('early','late',None),repeat=3):
        v=base(doc);frame(v)
        spans={ep:{p for p,e in zip(SCENES[:3],assignment) if e==ep} for ep in ('early','late')}
        v['h26ab']=lambda ep,ref,c,p:ref=='outside' and c=='later' and p in spans.get(ep,set())
        want=None not in assignment and all(ep in assignment for ep in ('early','late')) and sum(a!=b for a,b in zip(assignment,assignment[1:]))==1
        result=run(doc,v,('early','late'));assert result==[want],(assignment,result,want);rows[str(assignment)]=result[0]
    old='k rjh[k zoldgroup[] k znewgroup[] k zearly[] k zlate[] i[ep a][k h26aa[v ep k ztoutside[]]] i[p d][k h257z[k ztoutside[] k ztlater[] v p]] i[a d b d][k ic[v a v b k ztlater[]]] i[ep a p d][k h26ab[v ep k ztoutside[] k ztlater[] v p]] k ztlater[] p aa p aa i[person a at d][k h256o[v person k ztlater[] v at]] p h246c]'
    gap=fixture(('r5bx',),'q['+old+'].q[k r5bx['+COHORT+']].');v=base(gap);frame(v,'between_gap')
    assert run(gap,v)==[True,False]
    return dict(partition_oracle_models=len(rows),partitions=rows,uncovered_between_epochs_old_and_new=[True,False])

@lru_cache(None)
def cohort_checks():
    doc=fixture(('r5bx',),'q[k r5bx['+COHORT+']].');rows={}
    for variant in ('baseline','same_members','disjoint_members','between_gap','overlap','inside_gap','outside_history','reverse','cycle','wrong_reference','wrong_candidate','empty_next','missing_member','nonhuman_member','extra_member'):
        v=base(doc);frame(v,variant);actual=run(doc,v)
        assert actual==[variant in ('baseline','same_members','disjoint_members')],(variant,actual);rows[variant]=actual[0]
    same=fixture(('r5bx',),'q[k r5bx['+COHORT.replace('k znewgroup[]','k zoldgroup[]')+']].');v=base(same);frame(v,'same_members');assert run(same,v)==[False]
    rows['same_group']=False
    for n in ('h257z','h26aa','h26ab','h256o','h246c'):
        v=base(doc);frame(v);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(native_cohort_contrasts=rows,unknown_rejected=True)

@lru_cache(None)
def party_checks():
    doc=fixture(('r5bz',),'q[k r5bz['+PAIR+']].');rows={}
    for variant in ('baseline','future_party','late_anchor'):
        v=base(doc);frame(v,variant);actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_parties_and_formation_anchor=rows,earlier_nonparty_member_allowed=True,later_cohort_consent_not_assumed=True)

def declarations(v,variant='baseline',parties=('alpha','beta')):
    def matches(p,a,code,bindings,t):
        wanted=(p,'act','zterms',(p,'agreement'),'anchor')
        observed=(p,a,symbol(code),tuple(bindings.items),t)
        return p in parties and code.rank==0 and observed==wanted
    v['h255a']=lambda ag,code,r:variant!='unassigned' and code.rank==0 and (ag,symbol(code),r)==('agreement','zterms','anchor')
    v['dg']=lambda a,t:variant!='no_occurrence' and (a,t)==('act','anchor')
    v['f3']=lambda p,a,t:variant!='no_performer' and p in parties and (a,t)==('act','anchor')
    v['h255b']=lambda p,a,ag,code,bindings,t:ag=='agreement' and matches(p,a,code,bindings,t) and not(variant=='missing_self' and p=='alpha')
    def mutual(p,other,a,ag,code,bindings,t):
        if variant=='missing_counterparty' and (p,other)==('alpha',parties[-1]):return False
        if variant=='reverse_missing' and p=='beta':return False
        if variant=='different_act':return a=='otheract'
        if variant=='different_agreement':return ag=='extra'
        if variant=='different_terms':return symbol(code)=='r46w'
        if variant=='different_binding':return tuple(bindings.items)==('agreement',p)
        if variant=='different_point':return t=='later'
        return ag=='agreement' and other in parties and p!=other and matches(p,a,code,bindings,t)
    v['h255d']=mutual
    v['h255f']=lambda p,a,t:variant!='not_solemn' and p in parties and (a,t)==('act','anchor')
    def invokes(p,a,authority,code,bindings,t):
        if variant=='separate_oath_act':return a=='otheract'
        return authority.rank==0 and symbol(authority)==('zterms' if variant=='wrong_authority' else 'r46w') and matches(p,a,code,bindings,t)
    v['h255g']=lambda *a:variant!='no_witness' and invokes(*a)
    v['h255h']=lambda *a:variant!='no_judge' and invokes(*a)

@lru_cache(None)
def declaration_checks():
    query='q[k r5ca[k zearly[] k ztoutside[] k ztlater[] k zalpha[] k zact[] k zagreement[] r[p zterms] l[a][k zalpha[] k zagreement[]] k ztanchor[]]].'
    doc=fixture(('r5ca',),query);rows={}
    for variant in ('baseline','missing_self','missing_counterparty','different_act','different_agreement','different_terms','different_binding','different_point','not_solemn','separate_oath_act','wrong_authority','no_witness','no_judge','outside_period'):
        v=base(doc);frame(v);parties=('alpha','beta','extra')
        v['h26ac']=lambda ag,p,r:ag=='agreement' and p in parties and r=='anchor'
        declarations(v,variant,parties)
        if variant=='outside_period':v['h26ab']=lambda *a:False
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['zterms'] is unknown and v['h255e'] is unknown
    return dict(native_same_mutual_act_and_oath=rows,unrealized_terms_and_deity_property_not_executed=True)

@lru_cache(None)
def formation_checks():
    doc=fixture(('r5cb',),FORM,('r5bz','r5ca'));rows={}
    for variant in ('baseline','wrong_frame','single_party','unassigned','missing_party_act','swapped_arguments','later_act','unknown_point','no_occurrence','no_performer'):
        v=base(doc);frame(v,variant);declarations(v,variant)
        v['r5bz']=lambda *a:variant!='wrong_frame' and a==('oldgroup','newgroup','early','late','agreement','outside','later')
        def declare(ep,ref,c,p,a,ag,code,bindings,t):
            binding=('agreement',p) if variant=='swapped_arguments' else (p,'agreement')
            point={'later_act':'later','unknown_point':'outside'}.get(variant,'anchor')
            return p in ('alpha','beta') and not(variant=='missing_party_act' and p=='beta') and code.rank==0 and (ep,ref,c,a,ag,symbol(code),tuple(bindings.items),t)==('early','outside','later','act','agreement','zterms',binding,point)
        v['r5ca']=declare
        if variant in ('later_act','unknown_point'):v['dg']=lambda *a:True;v['f3']=lambda *a:True
        actual=run(doc,v,('oldgroup','newgroup','early','late','alpha','beta','agreement','act'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_rhz_and_exact_dependency_arguments=rows,boundaries=['r5bz','r5ca'])

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5cb',),FORM);rows={}
    domain=('oldgroup','newgroup','early','late','agreement','alpha','beta','act')
    for variant in ('baseline','reverse_missing','separate_oath_act','unassigned'):
        v=base(doc);frame(v);declarations(v,variant)
        actual=run(doc,v,domain);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['zterms'] is unknown and v['h255e'] is unknown
    for n in ('h26ac','h255d','h255g'):
        v=base(doc);frame(v);declarations(v);v[n]=unknown
        try:run(doc,v,domain)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(all_definitions_native_without_boundaries=rows,unknown_rejected=True,quotes_not_executed=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='epoch_cohorts_and_same_earlier_mutual_oath_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['後続集団の知識の拡大・誤りの除去・啓蒙進展の不能性','その状態を生じさせる目的と必然性','共謀的提示・kann nichtの規範的否認','括弧内の重要性・überhauptの総括・全文帰属'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new=catalog();old=parent()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record();p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==99
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=99)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('periods',period_checks),('cohorts',cohort_checks),('parties',party_checks),('declarations',declaration_checks),('formation',formation_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_epoch_undertakings.py','scripts/check_epoch_undertakings.py','tests/test_epoch_undertakings.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='epoch_cohorts_and_same_earlier_mutual_oath_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
