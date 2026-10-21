"""Check cognition beyond truth-table growth, canonical aliases and new grounds."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.extraction import _references
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_cognitive_acquisition import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/cognitive-acquisition-v1.json'
DOC='docs/cognitive-acquisition-v1.md'
READING='data/cognitive-acquisition-reading-v1.json'
PROOF='examples/v016/scoped-identity-example.noema'
PRIORS=('reports/cognitive-correction-v1.json','reports/epistemic-revision-v1.json','reports/scoped-reasons-v1.json')
DOMAIN=('person','other','group','item','alias','spare','judgment','otherjudgment','reason','method','proof','firststep','secondstep')
SCENES=('first','last','scope','assessment','candidate','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r ztruth[a d d] c.r zavailable[a a d] c.r zoutcomes[a a d d] c.'
PROVIDER='d h26ae[item a scope d] e[b at[k ztruth[v item v scope v at]]].'
CHANGE='k ztscope[] k ztassessment[] k ztcandidate[] k ztfirst[] k ztlast[]'
BLOCK='k zgroup[] k ztscope[] k ztassessment[] k ztcandidate[] k ztfirst[] p zavailable p zoutcomes'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),proof=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    prefix=parse('p:'+EXTRA+('' if proof else PROVIDER))
    if proof:
        example=parse((ROOT/PROOF).read_text(encoding='utf-8'))
        body=next(s['body'] for s in example['statements'] if s['kind']=='ask' and s['body'].get('symbol')=='rre')
        prefix['declarations']+=closure(example,list(_references(body)))
        prefix['declarations'].append(dict(kind='definition',name='zproofcontent',parameters=[],result='content',body=dict(kind='content',variable='at',body=deepcopy(body))))
        # The previously known item is the SAME false-P implication proved by
        # the record, rather than an unrelated proposition with a true flag.
        p='b point[u[e[n p a b][n p a b]]]'
        known='d zknowncontent[] e[b at[y[t['+p+'][v at]][t['+p+'][v at]]]].'
        provider=known+'r zchoose[a d e e e] e.d h26ae[item a scope d] e[k zchoose[v item v scope b at[k ztruth[v item v scope v at]] k zknowncontent[] k zproofcontent[]]].'
        prefix=parse(format_graph(prefix,'compact')+provider)
    names={d['name'] for d in prefix['declarations']}
    doc['declarations']=prefix['declarations']+[d for d in doc['declarations'] if d['name'] not in names]
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def model(doc,variant='baseline',flags=(True,True,True,True,True,True)):
    accepted,grasped,held,used,supported,grounded=flags
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    history=('first','last')
    v['h257z']=lambda s,c,t:(s,c)==('scope','candidate') and t in history
    v['ic']=lambda a,b,c:c=='candidate' and a in history and b in history and (a!=b if variant=='cycle' else history.index(a)<history.index(b))
    items=('item','alias','spare','proof')
    v['h26ad']=lambda i,s:variant!='wrong_scope' and s=='scope' and i in items
    v['h26ag']=lambda i,s:'item' if i=='alias' else i
    def accepts(p,i,s,t):
        if not accepted or (p,s)!=('person','scope'):return False
        first={'spare'};last={'item','spare'}
        if variant in ('already_known','alias_only','grasp_acquired','ground_acquired','new_proof','invalid_proof'):first.add('item')
        if variant=='alias_only':last={'alias','spare'}
        if variant=='loss_elsewhere':last={'item'}
        if variant in ('new_proof','invalid_proof'):last.add('proof')
        return i in (first if t=='first' else last if t=='last' else set())
    v['h26af']=accepts
    v['ztruth']=lambda i,s,t:variant!='false_content' and s=='scope' and i in items
    v['aa']=lambda p:variant!='not_human' and p in ('person','other')
    v['h256o']=lambda p,c,t:p in ('person','other') and c=='candidate' and t in history and not(variant=='died' and p=='person' and t=='last') and not(variant=='born_later' and p=='person' and t=='first')
    v['h246c']=lambda g,p,c:(g,p,c)==('group','other' if variant=='outsider' else 'person','candidate')
    v['h26ah']=lambda p,i,s,t:grasped and (p,s)==('person','scope') and i in items and t in history and not(variant=='grasp_acquired' and i=='item' and t=='first')
    v['h26ai']=lambda p,j,s,t:held and (p,s)==('other' if variant=='other_holder' else 'person','scope') and j in ('judgment','otherjudgment') and t in history
    def judged(j,i,code,s,polarity,t):
        wanted='spare' if j=='otherjudgment' else 'item'
        allowed=(wanted,) if variant not in ('new_proof','invalid_proof') else (wanted,'proof')
        if variant=='other_content':allowed=('proof',)
        return code.rank==0 and symbol(code)=='h26ae' and j in ('judgment','otherjudgment') and i in allowed and s==('outside' if variant=='other_reference' else 'scope') and polarity==(variant!='negative_judgment') and t in history
    v['h245q']=judged
    v['fc']=lambda j,r,t:used and j in ('judgment','otherjudgment') and r=='reason' and t in history
    v['fd']=lambda r,j,t:supported and r=='reason' and j in ('judgment','otherjudgment') and t in history
    v['h26aj']=lambda r,j,s,t:grounded and (r,s)==('reason','scope') and j in ('judgment','otherjudgment') and t in history and not(variant=='ground_acquired' and j=='judgment' and t=='first')
    v['zavailable']=lambda g,m,s:(g,m,s)==('group','method','first')
    v['zoutcomes']=lambda g,m,s,e:(g,m,s,e)==('group','method','first','last')
    if variant=='same_stage':v['ztlast']=lambda:'first'
    if variant=='unknown_end':v['ztlast']=lambda:'outside'
    return v

@lru_cache(None)
def holding_checks():
    doc=fixture(('r5cl',),'q[k r5cl[k zperson[] k zitem[] k ztscope[] k ztassessment[] k ztlast[]]].');rows={}
    for flags in product((False,True),repeat=6):
        actual=run(doc,model(doc,flags=flags));assert actual==[all(flags)],(flags,actual);rows[str(flags)]=actual[0]
    contrasts={}
    for variant in ('false_content','not_human','wrong_scope','other_holder','other_content','other_reference','negative_judgment'):
        actual=run(doc,model(doc,variant));assert actual==[False],(variant,actual);contrasts[variant]=actual[0]
    for n in ('h26af','h26ah','h26ai','h26aj','fd','ztruth'):
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(independent_conditions=rows,same_content_and_ground=contrasts,unknown_rejected=True)

@lru_cache(None)
def acquisition_checks():
    doc=fixture(('r5cm',),'q[k r5cm[k zperson[] k zitem[] '+CHANGE+']].');rows={}
    positive=('baseline','grasp_acquired','ground_acquired','loss_elsewhere')
    for variant in positive+('already_known','alias_only','false_content','died','born_later','same_stage','unknown_end'):
        actual=run(doc,model(doc,variant));assert actual==[variant in positive],(variant,actual);rows[variant]=actual[0]
    # The content is true in every scene: actual new cognition is still a gain.
    v=model(doc);assert all(v['ztruth']('item','scope',s) for s in SCENES)
    return dict(native_individual_gain=rows,new_tautological_content_can_be_learned=True,no_global_losslessness_requirement=True)

@lru_cache(None)
def collective_checks():
    doc=fixture(('r5co',),'q[k r5co[k zgroup[] '+CHANGE+']].',('r5cl',));rows={}
    for variant in ('individual','newborn_new_content','newborn_old_content','outsider','no_earlier_members','no_later_members','cycle'):
        v=model(doc,variant)
        v['h246c']=lambda g,p,c:g=='group' and c=='candidate' and p in ('person','other') and not(variant=='outsider' and p=='person')
        v['h256o']=lambda p,c,t:c=='candidate' and p in ('person','other') and t in ('first','last') and not(variant=='no_earlier_members' and t=='first') and not(variant=='no_later_members' and t=='last') and (p=='other' or t=='last' or variant=='individual')
        def holding(p,i,s,a,t):
            if (s,a)!=('scope','assessment') or i!='item':return False
            return (p,t)==('person','last') or variant=='newborn_old_content' and(p,t)==('other','first')
        v['r5cl']=holding
        actual=run(doc,v);assert actual==[variant in ('individual','newborn_new_content')],(variant,actual);rows[variant]=actual[0]
    return dict(native_population_and_gain_with_holding_boundary=rows,boundary='r5cl',same_level_replacement_is_not_expansion=True)

@lru_cache(None)
def proof_checks():
    query='q[t[k zproofcontent[]][k ztassessment[]]].q[k r5cn[k zperson[] '+CHANGE+']].q[k r5cl[k zperson[] k zitem[] k ztscope[] k ztassessment[] k ztfirst[]]].'
    doc=fixture(('r5cn',),query,proof=True);rows={}
    for variant in ('new_proof','invalid_proof','proof_without_grasp','proof_without_acceptance'):
        v=model(doc,'invalid_proof' if variant=='invalid_proof' else 'new_proof')
        v.update(jrfirst=lambda:'firststep',jrsecond=lambda:'secondstep',
            jrrule=lambda step:Fraction(5 if step=='firststep' else (0 if variant=='invalid_proof' else 6)),
            jrselect=lambda step,p,imp:p if step=='firststep' else imp,
            jrscopeselect=lambda step,p:SequenceValue((p,) if step=='firststep' else (),json.dumps({'kind':'description','result':'content'},sort_keys=True,separators=(',',':'))),
            zchoose=lambda i,s,ordinary,known,proof:proof if i=='proof' else known if i in ('item','alias') else ordinary)
        if variant=='proof_without_grasp':
            previous=v['h26ah'];v['h26ah']=lambda p,i,s,t:i!='proof' and previous(p,i,s,t)
        if variant=='proof_without_acceptance':
            previous=v['h26af'];v['h26af']=lambda p,i,s,t:i!='proof' and previous(p,i,s,t)
        actual=run(doc,v);assert actual==[variant!='invalid_proof',variant=='new_proof',True],(variant,actual);rows[variant]=actual
    return dict(native_rre_content_as_new_cognition=rows,known_conclusion_new_ground_relation=True,
        proof_validity_does_not_supply_personal_grasp_or_acceptance=True)

@lru_cache(None)
def impossibility_checks():
    doc=fixture(('r5cp',),'q[k r5cp['+BLOCK+']].',('r5co',));rows={}
    for variant in ('possible','no_gain','mixed_results','empty_results','wrong_group','wrong_scope','wrong_assessment','wrong_candidate','wrong_start'):
        v=model(doc)
        v['zoutcomes']=lambda g,m,s,e:variant!='empty_results' and (g,m,s)==('group','method','first') and e in (('last','outside') if variant=='mixed_results' else ('last',))
        expected=['group','scope','assessment','candidate','first','last']
        index={'wrong_group':0,'wrong_scope':1,'wrong_assessment':2,'wrong_candidate':3,'wrong_start':4}.get(variant)
        if index is not None:expected[index]='other' if index==0 else 'outside'
        v['r5co']=lambda *a:variant!='no_gain' and a==tuple(expected)
        actual=run(doc,v);want=variant not in ('possible','mixed_results','empty_results');assert actual==[want],(variant,actual);rows[variant]=actual[0]
    return dict(native_rjb_and_fixed_gain_arguments=rows,boundary='r5co')

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5cp',),'q[k r5cp['+BLOCK+']].');rows={}
    domain=('person','group','item','judgment','reason','method')
    for variant in ('baseline','already_known'):
        actual=run(doc,model(doc,variant),domain);assert actual==[variant=='already_known'],(variant,actual);rows[variant]=actual[0]
    return dict(all_definitions_native=rows,no_definition_boundaries=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='grasped_grounded_cognitive_acquisition_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['啓蒙進展の不能性と三つの不能性を同じ状態へ接続','同じ先行合意の目的・状態の必然性・規範的否認','重要性・総括・共謀的提示・全文帰属'],
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
    assert not new.document['statements'] and len(load_catalog(ROOT,'data/covenant-nullity-basis-v1.json').document['statements'])==99
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=99)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('holding',holding_checks),('acquisition',acquisition_checks),('collective',collective_checks),('proof',proof_checks),('impossibility',impossibility_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,PROOF,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_cognitive_acquisition.py','scripts/check_cognitive_acquisition.py','tests/test_cognitive_acquisition.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='grasped_grounded_cognitive_acquisition_and_cohort_impossibility_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
