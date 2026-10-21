"""Check same-content, reasoned correction and genuine absence of possible success."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_cognitive_correction import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/cognitive-correction-v1.json'
DOC='docs/cognitive-correction-v1.md'
READING='data/cognitive-correction-reading-v1.json'
PRIORS=('reports/epoch-undertakings-v1.json','reports/epistemic-revision-v1.json','reports/blocked-revision-v1.json')
DOMAIN=('person','other','group','item','alias','spare','judgment','reason','method')
SCENES=('first','middle','last','scope','assessment','candidate','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r ztruth[a d d] c.r zavailable[a a d] c.r zoutcomes[a a d d] c.'
PROVIDER='d h26ae[item a scope d] e[b at[k ztruth[v item v scope v at]]].'
CHANGE='k ztscope[] k ztassessment[] k ztcandidate[] k ztfirst[] k ztlast[]'
BLOCK='k zgroup[] k ztscope[] k ztassessment[] k ztcandidate[] k ztfirst[] p zavailable p zoutcomes'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    provider=parse('p:'+EXTRA+PROVIDER)
    doc['declarations']=provider['declarations']+[d for d in doc['declarations'] if d['name']!='h26ae']
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    history=('first','middle','last')
    v['h257z']=lambda s,c,t:(s,c)==('scope','candidate') and t in history
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else history.index(a)<history.index(b))
    v['h26ad']=lambda i,s:variant!='wrong_scope' and s=='scope' and i in ('item','alias','spare')
    v['h26ag']=lambda i,s:'item' if i=='alias' else i
    def accepted(p,i,s,t):
        if (p,s)!=('person','scope'):return False
        first={'item','spare'};last={'spare'}
        if variant=='no_previous_error':first={'spare'}
        if variant in ('retained','world_changed'):last.add('item')
        if variant=='alias_retained':last.add('alias')
        if variant=='alias_before':first={'alias','spare'}
        if variant=='other_error_gained':first={'item'}
        if variant=='all_discarded':last=set()
        return i in (first if t=='first' else last if t=='last' else set())
    v['h26af']=accepted
    v['ztruth']=lambda i,s,t:(s=='scope' and i in ('item','alias') and (variant=='true_target' or variant=='world_changed' and t=='last'))
    v['aa']=lambda p:p in ('person','other') and variant!='not_human'
    v['h256o']=lambda p,c,t:p in ('person','other') and c=='candidate' and t in history and not(variant=='died' and p=='person' and t=='last') and not(variant=='born_after' and p=='person' and t=='first')
    v['h246c']=lambda g,p,c:(g,p,c)==('group','other' if variant=='outsider' else 'person','candidate')
    event={'before_interval':'first','after_interval':'outside','at_end':'last'}.get(variant,'middle')
    v['fa']=lambda p,j,t:variant not in ('forgetting','all_discarded','no_judgment') and (p,j,t)==('other' if variant=='other_person' else 'person','judgment',event)
    def judged(j,item,code,scope,polarity,point):
        wanted=('judgment','spare' if variant=='other_content' else 'item','h26ae','outside' if variant=='other_reference' else 'scope',variant=='positive_judgment',event)
        return code.rank==0 and (j,item,symbol(code),scope,polarity,point)==wanted
    v['h245q']=judged
    v['fc']=lambda j,r,t:variant!='unused_reason' and (j,r,t)==('judgment','reason',event)
    v['fd']=lambda r,j,t:variant!='unsupported' and (r,j,t)==('reason','other' if variant=='other_judgment_support' else 'judgment',event)
    v['zavailable']=lambda g,m,s:(g,m,s)==('group','method','first')
    v['zoutcomes']=lambda g,m,s,e:(g,m,s,e)==('group','method','first','last')
    if variant=='same_stage':v['ztlast']=lambda:'first'
    return v

@lru_cache(None)
def error_checks():
    doc=fixture(('r5ce',),'q[k r5ce[k zperson[] k zitem[] k ztscope[] k ztassessment[] k ztfirst[]]].');rows={}
    for variant in ('baseline','alias_before','no_previous_error','true_target','not_human','wrong_scope'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','alias_before')],(variant,actual);rows[variant]=actual[0]
    return dict(native_accepted_false_content=rows,assessment_distinct_from_stage=True)

@lru_cache(None)
def judgment_checks():
    doc=fixture(('r5cf',),'q[k r5cf[k zperson[] k zalias[] k ztscope[] k ztmiddle[]]].');rows={}
    for variant in ('baseline','other_person','other_content','other_reference','positive_judgment','unused_reason','unsupported','other_judgment_support','no_judgment'):
        v=model(doc,variant);v['ztruth']=unknown
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_ya_and_same_negative_content=rows,judgment_does_not_execute_its_content=True)

@lru_cache(None)
def correction_checks():
    doc=fixture(('r5cg',),'q[k r5cg[k zperson[] k zitem[] '+CHANGE+']].');rows={}
    positives=('baseline','alias_before','at_end','other_error_gained')
    negatives=('retained','alias_retained','no_previous_error','true_target','not_human','wrong_scope','died','born_after','forgetting','all_discarded','world_changed','before_interval','after_interval','same_stage','other_person','unsupported')
    for variant in positives+negatives:
        actual=run(doc,model(doc,variant));assert actual==[variant in positives],(variant,actual);rows[variant]=actual[0]
    for n in ('h26af','h26ag','ztruth','h245q','fd','h256o'):
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(native_correction_contrasts=rows,unknown_rejected=True,remaining_errors_do_not_cancel_one_correction=True)

@lru_cache(None)
def collective_checks():
    doc=fixture(('r5ci',),'q[k r5ci[k zgroup[] '+CHANGE+']].');rows={}
    for variant in ('baseline','outsider','cycle','alias_retained'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_single_member_correction_with_valid_history=rows,unanimous_revision_not_required=True)

@lru_cache(None)
def impossibility_checks():
    doc=fixture(('r5cj',),'q[k r5cj['+BLOCK+']].',('r5ci',));rows={}
    for available,first_success,last_success in product((False,True),repeat=3):
        v=model(doc);v['zavailable']=lambda g,m,s:available and (g,m,s)==('group','method','first')
        v['zoutcomes']=lambda g,m,s,e:(g,m,s)==('group','method','first') and e in ('middle','last')
        v['r5ci']=lambda g,s,a,c,f,l:(g,s,a,c,f)==('group','scope','assessment','candidate','first') and ((l=='middle' and first_success) or(l=='last' and last_success))
        want=not(available and(first_success or last_success));actual=run(doc,v);assert actual==[want];rows[str((available,first_success,last_success))]=actual[0]
    contrasts={}
    for variant in ('empty_results','wrong_group','wrong_start','wrong_scope','wrong_assessment','wrong_candidate'):
        v=model(doc);v['zoutcomes']=lambda *args:variant!='empty_results' and args==('group','method','first','last')
        wanted=['group','scope','assessment','candidate','first','last']
        index={'wrong_group':0,'wrong_scope':1,'wrong_assessment':2,'wrong_candidate':3,'wrong_start':4}.get(variant)
        if index is not None:wanted[index]='other' if index==0 else 'outside'
        v['r5ci']=lambda *args:args==tuple(wanted)
        actual=run(doc,v);assert actual==[variant!='empty_results'];contrasts[variant]=actual[0]
    return dict(possible_success_table=rows,binding_contrasts=contrasts,boundary='r5ci',no_possible_success_not_no_guaranteed_success=True)

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5cj',),'q[k r5cj['+BLOCK+']].');rows={}
    domain=('person','group','item','judgment','reason','method')
    for variant in ('baseline','unsupported'):
        actual=run(doc,model(doc,variant),domain);assert actual==[variant=='unsupported'],(variant,actual);rows[variant]=actual[0]
    return dict(native_cohort_correction_through_rjb=rows,no_definition_boundaries=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='individual_reasoned_error_correction_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        prior_difference='旧ri6の正しい情報の無損失・新たな誤りの全面的不在を、個別の訂正の必要条件にしない。単なる消失を数えず、同じ内容への理由ある否定判断と別名も含む受容の撤回を要求する。',
        remaining=['知識の新規獲得・根拠・理解と、その拡大の不能性','啓蒙進展の不能性','前後集団と合意の同じ条項への目的・状態・必然性','規範的否認・重要性・総括・共謀的提示・全文帰属'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new=catalog();old,epoch=parents();imported=old.entries|epoch.entries
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
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
    for n,f in [('error',error_checks),('judgment',judgment_checks),('correction',correction_checks),('collective',collective_checks),('impossibility',impossibility_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_cognitive_correction.py','scripts/check_cognitive_correction.py','tests/test_cognitive_correction.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='individual_reasoned_correction_and_cohort_impossibility_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
