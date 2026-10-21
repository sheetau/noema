"""Check nonvacuous state-conditioned necessity and exact future goal bindings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_necessary_cohort_state import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/necessary-cohort-state-v1.json'
DOC='docs/necessary-cohort-state-v1.md'
READING='data/necessary-cohort-state-reading-v1.json'
PRIORS=('reports/cohort-progress-options-v1.json','reports/epoch-undertakings-v1.json','reports/necessary-futures-v1.json')
DOMAIN=('oldgroup','group','early','late','agreement','condition','aspect','second','method')
SCENES=('reference','assessment','candidate','branch','point','aligned','anchor','end','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r zholds[a a d d d] c.r zquote[i[h[j[a] d] e]] c.'
PROVIDER='d h26am[aspect a group a reference d candidate d] e[b point[k zholds[v aspect v group v reference v candidate v point]]].'
STATE='k zcondition[] k zgroup[] k ztreference[] k ztcandidate[] k ztpoint[]'
BLOCK='k zgroup[] k ztreference[] k ztassessment[] k ztcandidate[] k ztpoint[]'
NECESSARY='k zcondition[] '+BLOCK
FUTURE='k zoldgroup[] k zgroup[] k zearly[] k zlate[] k zagreement[] k zcondition[] k ztreference[] k ztassessment[] k ztcandidate[]'
BINDINGS=('oldgroup','group','early','late','agreement','condition')

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    provider=any(d['name']=='h26am' for d in doc['declarations'])
    doc['declarations']=parse('p:'+EXTRA+(PROVIDER if provider else ''))['declarations']+[d for d in doc['declarations'] if d['name']!='h26am']
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def model(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v['h26al']=lambda c,a,r:(c,r)==('condition','reference') and a in ('aspect','second')
    v['zholds']=lambda a,g,r,c,p:a in ('aspect','second') and(g,r)==('group','reference') and(c,p) in (('candidate','point'),('branch','aligned'))
    v['h26an']=lambda c,g,r,b,s,t:(c,g,r,b,s)==('condition','group','reference','candidate','point') and t in ('candidate','branch')
    v['h26ao']=lambda b,s,c:'aligned' if c=='branch' else s
    v['r5cy']=lambda g,r,a,c,p:(g,r,a)==('group','reference','assessment') and(c,p) in (('candidate','point'),('branch','aligned'))
    v['h26ap']=lambda *a:a==('group','method','reference','candidate','point')
    v['h26aq']=lambda *a:a==('group','method','reference','candidate','point','end')
    v['h254z']=lambda ag:'anchor'
    v['h26ar']=lambda r:'assessment'
    v['h26ab']=lambda *a:a==('late','reference','candidate','point')
    v['ic']=lambda *a:a==('anchor','point','candidate')
    v['r5bz']=lambda *a:a==('oldgroup','group','early','late','agreement','reference','candidate')
    v['r5cz']=lambda *a:a==('condition','group','reference','assessment','candidate','point')
    return v

def reject_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)

@lru_cache(None)
def state_checks():
    doc=fixture(('r5cx',),'q[k r5cx['+STATE+']].');rows={}
    for variant in ('baseline','one_false','empty','wrong_group','wrong_reference','wrong_history','wrong_point','unselected_false'):
        v=model(doc)
        if variant=='empty':v['h26al']=lambda *a:False
        original=v['zholds']
        if variant=='one_false':v['zholds']=lambda a,*rest:a!='second' and original(a,*rest)
        replacements={'wrong_group':(1,'oldgroup'),'wrong_reference':(2,'outside'),'wrong_history':(3,'outside'),'wrong_point':(4,'outside')}
        if variant in replacements:
            i,wanted=replacements[variant];v['zholds']=lambda *a:a[i]==wanted
        actual=run(doc,v);assert actual==[variant in ('baseline','unselected_false')],(variant,actual);rows[variant]=actual[0]
    reject_unknown(doc,('h26al','zholds'))
    return dict(nonempty_all_components=rows,native_content_evaluation=True,unknown_rejected=True)

@lru_cache(None)
def method_binding_checks():
    doc=fixture(('r5cy',),'q[k r5cy['+BLOCK+']].',('r5cw',));rows={}
    for accepted in (False,True):
        v=model(doc)
        def blocked(g,r,a,c,p,available,outcomes):
            assert(g,r,a,c,p)==('group','reference','assessment','candidate','point')
            for owner,method,start in product(('group','oldgroup'),('method','aspect'),('point','outside')):
                assert available(owner,method,start)==((owner,method,start)==('group','method','point'))
                for end in ('end','outside'):
                    assert outcomes(owner,method,start,end)==((owner,method,start,end)==('group','method','point','end'))
            return accepted
        v['r5cw']=blocked;actual=run(doc,v);assert actual==[accepted];rows[str(accepted)]=actual[0]
    return dict(exact_method_and_result_arguments=True,dependency_truth_preserved=rows,boundary='r5cw')

@lru_cache(None)
def necessity_checks():
    doc=fixture(('r5cz',),'q[k r5cz['+NECESSARY+']].',('r5cy',));rows={}
    for actual_state,base_block,other_state,other_block in product((False,True),repeat=4):
        v=model(doc)
        v['zholds']=lambda a,g,r,c,p:a in ('aspect','second') and(g,r)==('group','reference') and ((c,p)==('candidate','point') and actual_state or(c,p)==('branch','aligned') and other_state)
        v['r5cy']=lambda g,r,a,c,p:(g,r,a)==('group','reference','assessment') and ((c,p)==('candidate','point') and base_block or(c,p)==('branch','aligned') and other_block)
        want=actual_state and base_block and (not other_state or other_block)
        actual=run(doc,v);assert actual==[want];rows[str((actual_state,base_block,other_state,other_block))]=actual[0]
    contrasts={}
    for variant in ('empty','base_missing','shifted_base','wrong_group','wrong_reference','wrong_assessment','unaligned_block','extra_counterexample'):
        v=model(doc)
        if variant=='empty':v['h26an']=lambda *a:False
        if variant=='base_missing':v['h26an']=lambda *a:a==('condition','group','reference','candidate','point','branch')
        if variant=='shifted_base':v['h26ao']=lambda *a:'aligned'
        if variant in ('wrong_group','wrong_reference','wrong_assessment'):
            index={'wrong_group':0,'wrong_reference':1,'wrong_assessment':2}[variant];v['r5cy']=lambda *a:a[index]=='outside'
        if variant=='unaligned_block':v['r5cy']=lambda g,r,a,c,p:p=='point'
        if variant=='extra_counterexample':
            v['h26an']=lambda c,g,r,b,s,t:(c,g,r,b,s)==('condition','group','reference','candidate','point') and t in ('candidate','branch','outside')
            v['zholds']=lambda a,g,r,c,p:a in ('aspect','second') and(g,r)==('group','reference')
        actual=run(doc,v);assert actual==[False],(variant,actual);contrasts[variant]=actual[0]
    reject_unknown(doc,('h26al','zholds','h26an','h26ao','r5cy'))
    return dict(conditional_oracle=rows,invalid_comparisons=contrasts,native_rjk_and_state=True,unknown_rejected=True,boundary='r5cy')

@lru_cache(None)
def future_checks():
    doc=fixture(('r5c2',),'q[k r5c2['+FUTURE+']].',('r5bz','r5cz'));rows={}
    for variant in ('baseline','wrong_frame','outside_later','not_after','wrong_state','wrong_cohort','wrong_reference','wrong_assessment','wrong_history','wrong_point'):
        v=model(doc)
        if variant=='wrong_frame':v['r5bz']=lambda *a:False
        if variant=='outside_later':v['h26ab']=lambda *a:False
        if variant=='not_after':v['ic']=lambda *a:False
        mismatches={'wrong_state':0,'wrong_cohort':1,'wrong_reference':2,'wrong_assessment':3,'wrong_history':4,'wrong_point':5}
        if variant in mismatches:
            expected=['condition','group','reference','assessment','candidate','point'];expected[mismatches[variant]]='outside';v['r5cz']=lambda *a:a==tuple(expected)
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    reject_unknown(doc,('r5bz','r5cz','h26ab','ic','h254z'))
    return dict(same_agreement_later_epoch_and_condition=rows,unknown_rejected=True,boundaries=['r5bz','r5cz'])

@lru_cache(None)
def content_checks():
    rows={}
    # Two individuals distinguish adjacent roles without enumerating 6**6
    # inert assignments. The position matrix below checks every role separately.
    aliases={n:BINDINGS[i%2] for i,n in enumerate(BINDINGS)}
    for variant in ('baseline','short','long','swapped','repeated','wrong_reference','wrong_assessment','false_achievement'):
        names=list(BINDINGS)
        if variant=='short':names.pop()
        if variant=='long':names.append('condition')
        if variant=='swapped':names[:2]=reversed(names[:2])
        if variant=='repeated':names[1]='oldgroup'
        seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
        doc=fixture(('r5c3',),'q[t[k r5c3['+seq+' k ztreference[]]][k ztcandidate[]]].',('r5c2',));v=model(doc)
        v.update({'z'+n:lambda n=n:aliases[n] for n in BINDINGS})
        expected=(*(aliases[n] for n in BINDINGS),'outside' if variant=='wrong_reference' else 'reference','outside' if variant=='wrong_assessment' else 'assessment','candidate')
        v['r5c2']=lambda *a:variant!='false_achievement' and a==expected
        actual=run(doc,v,BINDINGS[:2]);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    seq='l[a]['+' '.join('k z'+n+'[]' for n in BINDINGS)+']'
    doc=fixture(('r5c3',),'q[t[k r5c3['+seq+' k ztreference[]]][k ztcandidate[]]].',('r5c2',));matrix=[]
    for selected,expected_position in product(range(6),repeat=2):
        v=model(doc);v.update({'z'+n:lambda i=i:BINDINGS[int(i==selected)] for i,n in enumerate(BINDINGS)})
        wanted=tuple(BINDINGS[int(i==expected_position)] for i in range(6))+('reference','assessment','candidate')
        v['r5c2']=lambda *a:a==wanted
        actual=run(doc,v,BINDINGS[:2]);assert actual==[selected==expected_position];matrix.append(actual[0])
    doc=fixture(('r5c3',),'q[k zquote[r[p r5c3]]].');v=model(doc)
    v['zquote']=lambda code:code.rank==0 and symbol(code)=='r5c3'
    assert run(doc,v)==[True]
    # All achievement primitives may be unknown: a closed code value does not execute them.
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'};v['zquote']=lambda code:code.rank==0 and symbol(code)=='r5c3'
    assert run(doc,v)==[True]
    return dict(exact_six_bindings=rows,position_matrix=matrix,binding_model_individuals=2,closed_quote_without_achievement=True,boundary='r5c2 for achieved content only')

@lru_cache(None)
def integrated_checks():
    doc=fixture(('r5cy',),'q[k r5cy['+BLOCK+']].',('r2qm','r5co','r5ci','r5cr'));rows={}
    for success in (False,True):
        v=model(doc)
        v['h257z']=lambda r,c,p:r=='reference' and ((c=='candidate' and p=='point') or(c=='branch' and p in ('point','end')))
        v['ic']=lambda a,b,c:(a,b,c)==('point','end','branch')
        v['aa']=lambda p:p=='oldgroup'
        v['h246c']=lambda g,p,c:(g,p)==('group','oldgroup') and c in ('candidate','branch')
        v['h256o']=lambda p,c,t:p=='oldgroup' and ((c=='candidate' and t=='point') or(c=='branch' and t in ('point','end')))
        v['r2qm']=lambda p,r,t:(p,r)==('oldgroup','reference') and t in ('point','end')
        v['h26ak']=lambda *a:a==('group','method','reference','candidate','point','end','branch')
        v['r5co']=lambda *a:success and a==('group','reference','assessment','branch','point','end')
        v['r5ci']=lambda *a:False;v['r5cr']=lambda *a:False
        actual=run(doc,v);assert actual==[not success];rows[str(success)]=actual[0]
    return dict(native_r5cw_with_same_available_methods_and_results=rows,boundaries=['r2qm','r5co','r5ci','r5cr'],prior_native_progress_evidence=PRIORS[0])

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='later_cohort_state_conditioned_necessity_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[713,1004],text=unit['text'][713:1004]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['同じ先行合意の因果的な目的・条項・宣誓との接続','規範的否認・重要性・総括・共謀的提示・全文帰属'],
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
    for n,f in [('state',state_checks),('methods',method_binding_checks),('necessity',necessity_checks),('future',future_checks),('content',content_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_necessary_cohort_state.py','scripts/check_necessary_cohort_state.py','tests/test_necessary_cohort_state.py',
        'scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='later_cohort_state_conditioned_necessity_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
