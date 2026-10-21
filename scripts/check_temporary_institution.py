"""Check the same adoption, a fixed short interval and every interior point."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_temporary_institution import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure,NAMES
from scripts.check_law_enactment import fixture as law_fixture,model as law_model,DOMAIN as LAW_DOMAIN
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

REPORT='reports/temporary-institution-v1.json'
DOC='docs/temporary-institution-v1.md'
READING='data/temporary-institution-reading-v1.json'
PRIORS=('reports/legislative-touchstone-v1.json','reports/institutional-criticism-v1.json','reports/law-enactment-v1.json','reports/provisional-order-v1.json')
DOMAIN=(*LAW_DOMAIN,'regime')
POINTS=('before','point','middle','late','end','after')
INTERIOR=('point','middle','late')
SCENES=('reference','candidate',*POINTS,'outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zstop[d] c.d zmilestone[] e[b point[k zstop[v point]]].'
FRAME='k zcommunity[] k zregime[] k zreference[] k zcandidate[] k zpoint[] k zend[]'
ARGS=' '.join('k z'+n+'[]' for n in NAMES)+' k zreference[] k zcandidate[] k zpoint[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),native_law=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    if native_law:
        provided=law_fixture(('r5ek',),'');ns={d['name'] for d in provided['declarations']}
        doc['declarations']=provided['declarations']+[d for d in doc['declarations'] if d['name'] not in ns]
        extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES) if 'z'+n not in ns)
    else:extra=EXTRA
    return parse(format_graph(doc,'compact')+extra+query)

def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)
def model(doc,maintained=(True,True,True),free=(True,True,True),stops=('end',),variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zstop']=lambda p:p in stops
    v['h257z']=lambda r,h,p:(r,h)==('reference','candidate') and p in POINTS and not(
        (variant=='missing_start' and p=='point') or(variant=='missing_end' and p=='end'))
    def before(a,b,h):
        if h!='candidate' or a not in POINTS or b not in POINTS:return False
        if variant=='cycle' and(a,b)==('end','point'):return True
        if variant=='missing_order' and(a,b)==('point','middle'):return False
        return POINTS.index(a)<POINTS.index(b)
    v['ic']=before
    v['h26cx']=lambda a,r,h,s,e:variant!='unspecified' and(a,r,h,s,e)==('activity','reference','candidate','point','end')
    v['h26cy']=lambda c,g,r,h,s,e:variant!='long' and(c,g,r,h,s,e)==('community','regime','reference','candidate','point','end')
    v['h26cs']=lambda g,c,r:variant!='nonreligious' and(g,c,r)==('regime','community','reference')
    v['h26cz']=lambda a,g,c,r,h,p:variant!='not_introduced' and(a,g,c,r,h,p)==('activity','regime','community','reference','candidate','point')
    v['r5ek']=lambda *a:a==('actor','people','community','law','activity','reference','candidate','point')
    def state(bits,g,c,r,h,p):
        return (g,c,r,h)==('regime','community','reference','candidate') and p in INTERIOR and bits[INTERIOR.index(p)]
    v['h26cv']=lambda g,c,r,h,p:state(maintained,g,c,r,h,p)
    v['r5fa']=lambda c,g,r,h,p:state(free,g,c,r,h,p)
    return v

def reject_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def period_checks():
    q='q[k r5fd[k zreference[] k zcandidate[] k zpoint[] k zend[]]].q[k r5fe[k zactivity[] '+FRAME+']].'
    doc=fixture(('r5fd','r5fe'),q);rows={}
    for variant in ('baseline','unspecified','long','missing_start','missing_end','cycle','missing_order','zero','reversed','foreign_start','foreign_end'):
        v=model(doc,variant=variant)
        if variant=='zero':v['zend']=lambda:'point'
        if variant=='reversed':v['zpoint']=lambda:'end';v['zend']=lambda:'point'
        if variant=='foreign_start':v['zpoint']=lambda:'outside'
        if variant=='foreign_end':v['zend']=lambda:'outside'
        expected=[variant in ('baseline','unspecified','long'),variant=='baseline']
        actual=run(doc,v);assert actual==expected,(variant,actual);rows[variant]=actual
    matrix=[]
    for specified,short in product((False,True),repeat=2):
        v=model(doc);cx,cy=v['h26cx'],v['h26cy']
        v['h26cx']=lambda *a:specified and cx(*a);v['h26cy']=lambda *a:short and cy(*a)
        actual=run(doc,v);assert actual==[True,specified and short];matrix.append(actual)
    return dict(ordered_nonzero_bounded_term=rows,determination_and_shortness_independent=matrix,
        unknown_rejected=reject_unknown(doc,('h257z','ic','h26cx','h26cy')))

@lru_cache(None)
def introduction_checks():
    doc=fixture(('r5ff',),'q[k r5ff['+ARGS+']].',native_law=True);rows={}
    for variant in ('baseline','reconfirmation','no_activity','no_effect','split_effect_activity','split_times','other_law','not_introduced','nonreligious'):
        v=law_model(doc,variant,actor='actor');v['zregime']=lambda:'regime'
        v['h26cs']=lambda g,c,r:variant!='nonreligious' and(g,c,r)==('regime','community','reference')
        v['h26cz']=lambda a,g,c,r,h,p:variant!='not_introduced' and(a,g,c,r,h,p)==('activity','regime','community','reference','candidate','point')
        actual=run(doc,v);assert actual==[variant in ('baseline','reconfirmation')],(variant,actual);rows[variant]=actual[0]
    mismatches=[]
    expected=('activity','regime','community','reference','candidate','point')
    for i in range(6):
        target=list(expected);target[i]='other' if i<3 else 'outside'
        v=law_model(doc,actor='actor');v['zregime']=lambda:'regime'
        v['h26cs']=lambda *a:a==('regime','community','reference');v['h26cz']=lambda *a:a==tuple(target)
        actual=run(doc,v);assert actual==[False];mismatches.append(actual[0])
    return dict(native_law_and_same_introduction=rows,all_six_introduction_positions=mismatches,
        all_legal_clauses_evaluated=True,no_definition_boundaries=True)

@lru_cache(None)
def continuity_checks():
    doc=fixture(('r5fg',),'q[k r5fg['+FRAME+']].',('r5fa',));rows=[]
    for bits in product((False,True),repeat=6):
        actual=run(doc,model(doc,bits[:3],bits[3:]));assert actual==[all(bits)]
        rows.append(dict(bits=list(bits),value=actual[0]))
    v=model(doc);assert run(doc,v)==[True] # False before/at end/after does not hurt.
    contrasts={}
    for name in ('h26cv','r5fa'):
        for i,label in enumerate(('community','regime','reference','candidate')):
            v=model(doc);old=v[name]
            # For cv regime/community are reversed; change the selected frame field.
            pos=(1,0,2,3)[i] if name=='h26cv' else i
            def changed(*a,old=old,pos=pos):
                a=list(a);a[pos]='other' if pos<2 else 'outside';return old(*a)
            v[name]=changed;actual=run(doc,v);assert actual==[False];contrasts[name+'_'+label]=actual[0]
    return dict(three_points_order_and_freedom=rows,same_frame=contrasts,
        half_open_interval=True,no_forced_abolition_after_end=True,
        boundary='r5fa only; institutional-criticism report checks every citizen, candidate and permission',
        unknown_rejected=reject_unknown(doc,('h257z','ic','h26cv','r5fa')))

@lru_cache(None)
def milestone_checks():
    q='q[k r5fh['+ARGS+' k zend[]]].q[k r5fi['+ARGS+' k zend[] k zmilestone[]]].'
    doc=fixture(('r5fh','r5fi'),q,('r5ek','r5fa'));rows=[]
    for bits in product((False,True),repeat=4):
        stops=tuple(p for p,b in zip((*INTERIOR,'end'),bits) if b)
        actual=run(doc,model(doc,stops=stops));expected=[True,bits== (False,False,False,True)]
        assert actual==expected,(bits,actual);rows.append(dict(bits=list(bits),values=actual))
    contrasts={}
    for variant in ('unspecified','long','not_introduced','nonreligious','missing_start','missing_end','cycle','missing_order'):
        actual=run(doc,model(doc,variant=variant));assert actual==[False,False];contrasts[variant]=actual
    for name in ('h26cx','h26cy','h26cz','r5ek'):
        v=model(doc);old=v[name]
        # Same act for designation/adoption/introduction; same regime for duration.
        pos=1 if name=='h26cy' else 0
        def changed(*a,old=old,pos=pos):
            a=list(a);a[pos]='other';return old(*a)
        v[name]=changed;actual=run(doc,v);assert actual==[False,False];contrasts['split_'+name]=actual
    for bits in ((False,True,True),(True,False,True),(True,True,False)):
        for slot in ('maintained','free'):
            actual=run(doc,model(doc,**{slot:bits}));assert actual==[False,False]
    v=model(doc,stops=('before','end','after'));assert run(doc,v)==[True,True]
    # Endpoint and later truth are unconstrained, not required to be false.
    v=model(doc);v['h26cv']=lambda *a:True;v['r5fa']=lambda *a:True
    assert run(doc,v)==[True,True]
    return dict(first_milestone_at_same_determined_end=rows,same_adoption_and_short_term=contrasts,
        all_three_interior_failures_rejected=True,prior_and_later_milestones_allowed=True,
        endpoint_and_later_continuation_allowed=True,boundaries=['r5ek','r5fa'],
        unknown_rejected=reject_unknown(doc,('h26cx','h26cy','h26cz','r5ek','h26cv','r5fa','zstop')))

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='temporary_institution_and_continuous_criticism_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['r5ek complete same-act law adoption','r5fc same religious order and every current citizen',
            'ta ordered complete history','rkh first attained milestone'],
        remaining=['expectation of a better arrangement and purpose of introducing order','public insight and corroboration sufficient for united proposal',
            'protection of reformed congregations and nonhindrance of retainers','clerical focus, possibility, discourse and whole-sentence review'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('period',period_checks),('introduction',introduction_checks),('continuity',continuity_checks),('milestone',milestone_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_temporary_institution.py','scripts/check_temporary_institution.py','tests/test_temporary_institution.py',
        'scripts/check_law_enactment.py','scripts/check_scoped_counts.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='temporary_institution_and_continuous_criticism_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
