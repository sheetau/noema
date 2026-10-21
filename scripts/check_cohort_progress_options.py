"""Check cohort restriction, disjunctive progress and method-specific futures."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_cohort_progress_options import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

REPORT='reports/cohort-progress-options-v1.json'
DOC='docs/cohort-progress-options-v1.md'
READING='data/cohort-progress-options-reading-v1.json'
PRIORS=('reports/cognitive-acquisition-v1.json','reports/cognitive-correction-v1.json','reports/human-enlightenment-block-v1.json')
DOMAIN=('group','old','young','outsider','topic','second','method','othermethod')
SCENES=('first','last','scope','assessment','candidate','branch','otherbranch','otherend','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r zavailable[a a d] c.r zoutcomes[a a d d] c.'
ARGS='k zgroup[] k ztscope[] k ztassessment[] k ztcandidate[] k ztfirst[] p zavailable p zoutcomes'
FRAME='k zgroup[] k ztscope[] k ztcandidate[] k ztfirst[] p zavailable p zoutcomes'
CHANGE='k zgroup[] k ztscope[] k ztbranch[] k ztfirst[] k ztlast[]'

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
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    histories={'candidate':('first',),'branch':('first','last'),'otherbranch':('first','otherend')}
    if variant=='backwards':histories['branch']=('last','first')
    v['h257z']=lambda s,c,t:s=='scope' and t in histories.get(c,())
    v['ic']=lambda a,b,c:a in histories.get(c,()) and b in histories.get(c,()) and (a!=b if variant=='cycle' and c=='branch' else histories[c].index(a)<histories[c].index(b))
    v['aa']=lambda p:p in ('old','young','outsider')
    v['h246c']=lambda g,p,c:g=='group' and p in ('old','young') and c in histories
    def alive(p,c,t):
        if t not in histories.get(c,()):return False
        if variant=='different_initial' and c=='branch' and t=='first':return p=='young'
        if variant=='extinction' and t!='first':return False
        if p=='outsider':return True
        if p=='old':return not(variant=='turnover' and t!='first')
        return p=='young' and t!='first'
    v['h256o']=alive
    v['r2qm']=lambda p,s,t:s=='scope' and p in ('old','young','outsider') and not(variant=='missing_evaluation' and p=='old' and t=='last')
    v['h226u']=lambda p,s,t:p in ('old','young','outsider') and s=='scope' and t in ('topic','second')
    def judgment(p,t,s,at):
        if s!='scope' or p not in ('old','young','outsider'):return False
        if t=='topic':return not(variant=='loss' and p=='old' and at=='last')
        return t=='second' and at=='last' and ((variant=='partial_gain' and p=='old') or(variant=='new_generation' and p=='young') or(variant=='outsider_gain' and p=='outsider'))
    v['r5aa']=judgment
    v['zavailable']=lambda g,m,s:variant!='no_methods' and (g,s)==('group','first') and m in (('method','othermethod') if variant=='two_methods' else ('method',))
    def outcomes(g,m,s,e):
        if variant=='empty_results' or (g,s)!=('group','first'):return False
        return (m,e)==('method','last') or variant in ('mixed_results','two_branches') and (m,e)==('method','otherend') or variant=='two_methods' and(m,e)==('othermethod','otherend')
    v['zoutcomes']=outcomes
    def branch(g,m,s,b,f,e,c):
        if (g,s,b,f)!=('group','scope','candidate','first') or variant=='missing_branch':return False
        ordinary=('othermethod' if variant=='wrong_method_link' else 'method','otherend' if variant=='wrong_result_link' else 'last','branch')
        return (m,e,c)==ordinary or variant in ('mixed_results','two_branches') and(m,e,c)==('method','otherend','otherbranch') or variant=='two_methods' and(m,e,c)==('othermethod','otherend','otherbranch')
    v['h26ak']=branch
    return v

@lru_cache(None)
def enlightenment_checks():
    doc=fixture(('r5cr',),'q[k r5cr['+CHANGE+']].',('r2qm','r5aa'));rows={}
    for variant in ('baseline','partial_gain','new_generation','turnover','loss','outsider_gain','missing_evaluation','extinction','cycle','backwards'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('partial_gain','new_generation')],(variant,actual);rows[variant]=actual[0]
    for n in ('h246c','h256o','r2qm','r5aa'):
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(native_cohort_and_individual_or_collective_progress=rows,unknown_rejected=True,
        boundaries=['r2qm','r5aa; unchanged normal judgment evaluation pinned in human-enlightenment-block-v1'])

@lru_cache(None)
def union_checks():
    args='k zgroup[] k ztscope[] k ztassessment[] k ztbranch[] k ztfirst[] k ztlast[]'
    doc=fixture(('r5cs',),'q[k r5cs['+args+']].',('r5co','r5ci','r5cr'));rows={}
    for flags in product((False,True),repeat=3):
        v=model(doc)
        v['r5co']=lambda *a:flags[0] and a==('group','scope','assessment','branch','first','last')
        v['r5ci']=lambda *a:flags[1] and a==('group','scope','assessment','branch','first','last')
        v['r5cr']=lambda *a:flags[2] and a==('group','scope','branch','first','last')
        actual=run(doc,v);assert actual==[any(flags)];rows[str(flags)]=actual[0]
    return dict(three_way_disjunction=rows,same_arguments=True,boundaries=['r5co','r5ci','r5cr'])

@lru_cache(None)
def frame_checks():
    doc=fixture(('r5cv',),'q[k r5cv['+FRAME+']].',('r2qm',));rows={}
    accepted=('baseline','no_methods','mixed_results','two_methods')
    for variant in accepted+('empty_results','missing_branch','wrong_method_link','wrong_result_link','backwards','cycle','different_initial','missing_evaluation','extinction'):
        actual=run(doc,model(doc,variant));assert actual==[variant in accepted],(variant,actual);rows[variant]=actual[0]
    # A valid continuation cannot conceal another selected invalid continuation.
    v=model(doc);original=v['h26ak'];v['h26ak']=lambda g,m,s,b,f,e,c:original(g,m,s,b,f,e,c) or(g,m,s,b,f,e,c)==('group','method','scope','candidate','first','last','outside')
    assert run(doc,v)==[False];rows['additional_invalid_branch']=False
    for n in ('zavailable','zoutcomes','h26ak'):
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(all_results_all_continuations_validated=rows,unknown_rejected=True,boundary='r2qm')

@lru_cache(None)
def impossibility_checks():
    doc=fixture(('r5cw',),'q[k r5cw['+ARGS+']].',('r2qm','r5co','r5ci','r5cr'));rows={}
    for flags in product((False,True),repeat=3):
        v=model(doc)
        v['r5co']=lambda g,s,a,c,f,l:flags[0] and(g,s,a,c,f,l)==('group','scope','assessment','branch','first','last')
        v['r5ci']=lambda g,s,a,c,f,l:flags[1] and(g,s,a,c,f,l)==('group','scope','assessment','branch','first','last')
        v['r5cr']=lambda g,s,c,f,l:flags[2] and(g,s,c,f,l)==('group','scope','branch','first','last')
        actual=run(doc,v);assert actual==[not any(flags)],(flags,actual);rows[str(flags)]=actual[0]
    contrasts={}
    for variant in ('mixed_results','two_methods','wrong_group','wrong_scope','wrong_assessment','wrong_start','unselected_continuation'):
        v=model(doc,variant);expected=['group','scope','assessment','otherbranch' if variant in ('mixed_results','two_methods','unselected_continuation') else 'branch','first','otherend' if variant in ('mixed_results','two_methods','unselected_continuation') else 'last']
        index={'wrong_group':0,'wrong_scope':1,'wrong_assessment':2,'wrong_start':4}.get(variant)
        if index is not None:expected[index]='outsider' if index==0 else 'outside'
        v['r5co']=lambda *a:a==tuple(expected);v['r5ci']=lambda *a:False;v['r5cr']=lambda *a:False
        actual=run(doc,v);want=variant not in ('mixed_results','two_methods');assert actual==[want],(variant,actual);contrasts[variant]=actual[0]
    return dict(no_kind_of_possible_progress=rows,method_result_branch_binding=contrasts,
        no_joint_success_requirement=True,boundaries=['r2qm','r5co','r5ci','r5cr'])

@lru_cache(None)
def integrated_checks():
    # Execute all new definitions and native cognition/correction. Only the
    # already checked independent-judgment assessment is a typed boundary.
    from scripts import check_cognitive_acquisition as acquisition
    doc=fixture(('r5cw',),'',('r2qm','r5aa'))
    supplied=acquisition.fixture(('r5cp',),'')
    ds={d['name']:d for d in supplied['declarations']}
    for d in doc['declarations']:
        if d['name'] in ds and d['name']!='h26ae':assert d==ds[d['name']],d['name']
    doc['declarations']=supplied['declarations']+[d for d in doc['declarations'] if d['name'] not in ds]
    doc=parse(format_graph(doc,'compact')+'q[k r5cw['+ARGS+']].q[k r5cp['+ARGS+']].');rows={}
    domain=('person','group','item','judgment','reason','method')
    for variant in ('baseline','already_known'):
        v=model(doc);v.update(acquisition.model(doc,variant))
        v.update({'zt'+n:lambda n=n:n for n in SCENES})
        v['h257z']=lambda s,c,t:s=='scope' and ((c=='candidate' and t=='first') or(c=='branch' and t in ('first','last')))
        v['ic']=lambda a,b,c:(a,b,c)==('first','last','branch')
        v['h246c']=lambda g,p,c:(g,p)==('group','person') and c in ('candidate','branch')
        v['h256o']=lambda p,c,t:p=='person' and ((c=='candidate' and t=='first') or(c=='branch' and t in ('first','last')))
        v['r2qm']=lambda p,s,t:(p,s)==('person','scope') and t in ('first','last')
        v['h226u']=lambda p,s,t:(p,s,t)==('person','scope','item');v['r5aa']=lambda *a:False
        v['h26ak']=lambda *a:a==('group','method','scope','candidate','first','last','branch')
        v['fa']=lambda *a:False
        actual=run(doc,v,domain);expected=[variant=='already_known',True];assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(native_different_continuation_and_old_fixed_history_contrast=rows,
        boundaries=['r2qm','r5aa'],native_acquisition_correction_and_modal_binding=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='cohort_three_progress_kinds_and_method_continuations_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['同じ先行合意の目的と後代を置く状態','状態からの不能性の必然性と規範的否認','重要性・総括・共謀的提示・全文帰属'],
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
    for n,f in [('enlightenment',enlightenment_checks),('union',union_checks),('frame',frame_checks),('impossibility',impossibility_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_cohort_progress_options.py','scripts/check_cohort_progress_options.py','tests/test_cohort_progress_options.py',
        'scripts/check_cognitive_acquisition.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='cohort_progress_disjunction_and_method_specific_possible_continuations',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
