"""Check causal achievement, quoted terms and same-act common-purpose oaths."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_cohort_covenant_purpose import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts import check_epoch_undertakings as epoch

REPORT='reports/cohort-covenant-purpose-v1.json'
DOC='docs/cohort-covenant-purpose-v1.md'
READING='data/cohort-covenant-purpose-reading-v1.json'
PRIORS=('reports/necessary-cohort-state-v1.json','reports/epoch-undertakings-v1.json')
DOMAIN=(*epoch.DOMAIN,'condition')
SCENES=epoch.SCENES
EXTRA=epoch.EXTRA+'r zcondition[] a.r zquote[i[h[j[a]] e]] c.'
NAMES=('oldgroup','newgroup','early','late','agreement','condition')
ARGS=' '.join('k z'+n+'[]' for n in NAMES)
SIX='l[a]['+ARGS+']'
SEVEN='l[a][k zalpha[] '+ARGS+']'
CAUSE=ARGS+' k ztoutside[] k ztlater[]'
FORM='q[k r5da['+ARGS+' k ztlater[]]].'
DECLARE='q[k r5c7['+ARGS+' k ztlater[] k zalpha[] k zact[] r[p r5c6] '+SEVEN+' k ztanchor[]]].'

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
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def model(doc,variant='baseline'):
    v=epoch.base(doc);v['zcondition']=lambda:'condition';v['h26av']=lambda:'outside';v['h26ar']=lambda r:'old'
    epoch.frame(v)
    parties=('alpha',) if variant=='single_party' else ('alpha','beta')
    v['h26ac']=lambda ag,p,r:ag=='agreement' and p in parties and r=='anchor'
    v['r5bz']=lambda *a:variant!='wrong_frame' and a==('oldgroup','newgroup','early','late','agreement','outside','later')
    def terms(p,a,code,bindings,t):
        return p in parties and code.rank==0 and (a,symbol(code),tuple(bindings.items),t)==('act','r5c6',(p,*NAMES),'anchor')
    v['h255a']=lambda ag,code,r:variant!='unassigned' and code.rank==0 and (ag,symbol(code),r)==('agreement','r5c6','anchor')
    v['dg']=lambda a,t:variant!='no_occurrence' and (a,t)==('act','anchor')
    v['f3']=lambda p,a,t:variant!='no_performer' and p in parties and (a,t)==('act','anchor')
    v['h255b']=lambda p,a,ag,code,bs,t:ag=='agreement' and terms(p,a,code,bs,t) and not(variant=='missing_self' and p=='alpha')
    v['h255d']=lambda p,o,a,ag,code,bs,t:ag=='agreement' and o in parties and o!=p and terms(p,a,code,bs,t) and not(variant=='missing_mutual' and (p,o)==('beta','alpha'))
    v['h255f']=lambda p,a,t:variant!='not_solemn' and p in parties and (a,t)==('act','anchor')
    def invoke(p,a,authority,code,bs,t):
        return authority.rank==0 and symbol(authority)=='r46w' and terms(p,a,code,bs,t)
    v['h255g']=lambda *a:variant!='no_witness' and invoke(*a)
    v['h255h']=lambda *a:variant!='no_judge' and invoke(*a)
    def adopts(p,a,ag,code,bs,r,t):
        expected=['act','agreement','r5c5',NAMES,'outside','anchor']
        changes={'different_act':(0,'otheract'),'different_agreement':(1,'extra'),'different_goal':(2,'r5c3'),
                 'different_bindings':(3,tuple(reversed(NAMES))),'different_reference':(4,'old'),'different_point':(5,'later')}
        if variant in changes:i,value=changes[variant];expected[i]=value
        return p in parties and not(variant=='missing_purpose' and p=='beta') and code.rank==0 and (a,ag,symbol(code),tuple(bs.items),r,t)==tuple(expected)
    v['h26at']=adopts
    return v

@lru_cache(None)
def cause_checks():
    doc=fixture(('r5c4',),'q[k r5c4['+CAUSE+']].',('r5c2',));rows={}
    for causal,result in product((False,True),repeat=2):
        v=model(doc)
        v['h26as']=lambda ag,code,bs,r,c:causal and code.rank==0 and(ag,symbol(code),tuple(bs.items),r,c)==('agreement','r5c3',NAMES,'outside','later')
        v['r5c2']=lambda *a:result and a==(*NAMES,'outside','old','later')
        actual=run(doc,v);assert actual==[causal and result];rows[str((causal,result))]=actual[0]
    contrasts={}
    for variant in ('agreement','code','bindings','reference','candidate','assessment'):
        v=model(doc);expected=['agreement','r5c3',NAMES,'outside','later']
        if variant!='assessment':
            index=('agreement','code','bindings','reference','candidate').index(variant)
            expected[index]=tuple(reversed(NAMES)) if variant=='bindings' else 'other'
        v['h26as']=lambda ag,code,bs,r,c:(ag,symbol(code),tuple(bs.items),r,c)==tuple(expected)
        v['r5c2']=lambda *a:a==(*NAMES,'outside','anchor' if variant=='assessment' else 'old','later')
        actual=run(doc,v);assert actual==[False];contrasts[variant]=actual[0]
    for missing in ('h26as','r5c2','h26ar'):
        v=model(doc);v['h26as']=lambda *a:True;v['r5c2']=lambda *a:True;v[missing]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(missing)
    return dict(causation_and_actual_result=rows,wrong_result_binding=contrasts,unknown_rejected=True,boundary='r5c2')

@lru_cache(None)
def binding_checks():
    rows={};matrices={}
    for root,names,boundary in (('r5c5',NAMES,'r5c4'),('r5c6',('alpha',*NAMES),'h26au'),('r5db',NAMES,'r5da')):
        def setup(selected,expected_position,length=None):
            chosen=list(names)
            if length=='short':chosen.pop()
            if length=='long':chosen.append(names[-1])
            seq='l[a]['+' '.join('k z'+n+'[]' for n in chosen)+']'
            call='k '+root+'['+seq+(' k ztoutside[]' if root=='r5c5' else '')+']'
            doc=fixture((root,),'q[t['+call+'][k ztlater[]]].',() if root=='r5c6' else (boundary,));v=model(doc)
            for i,n in enumerate(names):v['z'+n]=lambda i=i:'beta' if i==selected else 'alpha'
            wanted=tuple('beta' if i==expected_position else 'alpha' for i in range(len(names)))
            if root=='r5c6':
                v['h26au']=lambda p,ag,code,bs,r,c:code.rank==0 and (p,ag,symbol(code),tuple(bs.items),r,c)==(wanted[0],wanted[5],'r5c5',wanted[1:],'outside','later')
            else:
                tail=('outside','later') if root=='r5c5' else ('later',)
                v[boundary]=lambda *a:a==wanted+tail
            return run(doc,v,('alpha','beta'))[0]
        matrix=[]
        for selected,expected in product(range(len(names)),repeat=2):
            actual=setup(selected,expected);assert actual==(selected==expected),(root,selected,expected,actual);matrix.append(actual)
        assert not setup(0,0,'short') and not setup(0,0,'long')
        rows[root]=dict(short=False,long=False,correct=True);matrices[root]=matrix
    return dict(exact_lengths=rows,position_matrices=matrices,two_individual_models=True,boundaries=['r5c4','h26au is a primitive','r5da'])

@lru_cache(None)
def declaration_checks():
    doc=fixture(('r5c7',),DECLARE);rows={}
    variants=('baseline','missing_self','missing_mutual','not_solemn','no_witness','no_judge','different_act','different_agreement','different_goal','different_bindings','different_reference','different_point')
    for variant in variants:
        actual=run(doc,model(doc,variant));want=variant in ('baseline','missing_mutual')
        # This query is alpha's act; the missing beta->alpha direction is
        # checked across ALL parties in formation_checks.
        assert actual==[want],(variant,actual);rows[variant]=actual[0]
    for change,replacement in (('terms','r[p zterms]'),('bindings','l[a][k zalpha[] k zagreement[]]')):
        query=DECLARE.replace('r[p r5c6]' if change=='terms' else SEVEN,replacement)
        d=fixture(('r5c7',),query);v=model(d)
        # Make lower-level inputs permissive to test the explicit equalities.
        for name in ('h255b','h255d','h255f','h255g','h255h','h26at'):v[name]=lambda *a:True
        assert run(d,v)==[False];rows['wrong_'+change]=False
    return dict(native_mutual_oath_and_same_act_purpose=rows,quote_contents_not_required=True)

@lru_cache(None)
def formation_checks():
    doc=fixture(('r5da',),FORM,('r5bz',));rows={}
    variants=('baseline','wrong_frame','single_party','unassigned','no_occurrence','no_performer','missing_self','missing_mutual','missing_purpose','not_solemn','no_witness','no_judge','different_act','different_agreement','different_goal','different_bindings','different_reference','different_point')
    for variant in variants:
        v=model(doc,variant);actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h26as'] is unknown and v['h26au'] is unknown and v['h255e'] is unknown
    for missing in ('h26at','h255d','h26ac'):
        v=model(doc);v[missing]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(missing)
    return dict(all_parties_same_terms_and_purpose=rows,unknown_rejected=True,unrealized_goal_terms_and_deity_allowed=True,boundary='r5bz')

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5da',),FORM);rows={};domain=('oldgroup','newgroup','early','late','agreement','condition','alpha','beta','act')
    for variant in ('baseline','missing_purpose','missing_mutual'):
        v=model(doc,variant);actual=run(doc,v,domain);assert actual==[variant=='baseline'];rows[variant]=actual[0]
    # Formation itself is quotable without asserting it or evaluating the goal.
    quoted=fixture(('r5db',),'q[k zquote[r[p r5db]]].');v={d['name']:unknown for d in quoted['declarations'] if d['kind']=='primitive'}
    v['zquote']=lambda code:code.rank==0 and symbol(code)=='r5db';assert run(quoted,v)==[True]
    return dict(native_frame_formation_oath_and_purpose=rows,no_definition_boundaries=True,closed_policy_quote_not_executed=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='cohort_covenant_causal_purpose_and_same_oath_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['規範的なkann nicht','共謀的提示・重要性・総括・著者帰属と一文全体の通読'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents();imported={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record();p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(sources[0].document['statements'])==99
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=99)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('cause',cause_checks),('bindings',binding_checks),('declarations',declaration_checks),('formation',formation_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_cohort_covenant_purpose.py','scripts/check_cohort_covenant_purpose.py','tests/test_cohort_covenant_purpose.py',
        'scripts/check_epoch_undertakings.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='cohort_covenant_causal_purpose_and_same_oath_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
