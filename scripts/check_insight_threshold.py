"""Check relevant cognition sufficiency, non-vacuous contrast and bounded until."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_insight_threshold import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure,NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

REPORT='reports/insight-threshold-v1.json'
DOC='docs/insight-threshold-v1.md'
READING='data/insight-threshold-reading-v1.json'
PRIORS=('reports/public-insight-v1.json','reports/protective-petition-v1.json','reports/temporary-institution-v1.json','reports/institutional-outlook-v1.json')
DOMAIN=('base','new','extra','noise','alias')
SCENES=('reference','assessment','candidate','start','middle','end','after','oldcase','oldpoint','richcase','richpoint','outside')
POINTS=('start','middle','end','after')
OBJECTS=dict(zip(NAMES,('base','new','extra','noise','alias','base','new')))
EXTRA=''.join('r z'+n+'[] a.' for n in (*NAMES,'item','actor','people','law','activity'))+''.join('r z'+n+'[] d.' for n in SCENES)
BASE=' '.join('k z'+n+'[]' for n in (*NAMES,'reference','assessment'))
FRAME=BASE+' k zcandidate[]'
UNTIL='k zactor[] k zpeople[] k zcommunity[] k zlaw[] k zregime[] k zactivity[] k zreference[] k zcandidate[] k zstart[] k zend[] k zfield[] k zaudience[] k zgroup[] k zrecipient[] k zpolicy[] k zassessment[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,query,boundaries=('r5fu','r5gk')):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[root]),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda value=value:value for n,value in OBJECTS.items()})
    v.update({'z'+n:lambda n=n:n for n in SCENES})
    v.update(zitem=lambda:'new',zactor=lambda:'base',zpeople=lambda:'new',zlaw=lambda:'noise',zactivity=lambda:'alias')
    canonical=lambda i:'base' if i=='alias' else i
    v['h26ag']=lambda i,r:canonical(i)
    v['h26d4']=lambda p,c,g,f,i,r:(p,c,g,f,r)==('new','new','extra','noise','reference') and i in ('base','new','extra') and variant!='empty_relevant_scope'
    def profile(candidate,point):
        if(candidate,point)==('oldcase','oldpoint'):return {'base','new'} if variant=='already_enough' else {'base'}
        if(candidate,point)==('richcase','richpoint'):return {'base','new','extra'}
        if candidate!='candidate' or point not in POINTS:return set()
        if point in ('end','after') or(variant=='earlier_threshold' and point=='middle'):
            if variant=='unrelated_gain':return {'base','noise'}
            if variant=='alias_gain':return {'base'}
            return {'base','new'}
        return {'base','new'} if variant=='already_enough' else {'base'}
    v['r5fu']=lambda i,c,g,f,a,r,assessment,h,t:(c,g,f,a,r,assessment)==('new','extra','noise','alias','reference','outside' if variant=='wrong_truth_assessment' else 'assessment') and canonical(i) in profile(h,t)
    def compare(group,c,g,f,a,recipient,p,r,h,anchor,alternative,point):
        if(group,c,g,f,a,recipient,p,r,h)!=('base','new','extra','noise','alias','base','new','reference','candidate') or anchor not in POINTS:return False
        if(alternative,point)==('candidate',anchor):return variant!='missing_actual_comparison'
        if(alternative,point)==('oldcase','oldpoint'):return variant!='no_old_comparison'
        return(alternative,point)==('richcase','richpoint')
    v['h26d3']=compare
    def ability(group,c,recipient,p,r,h,t):
        if(group,c,recipient,p,r)!=('base','new','base','new','reference'):return False
        if(h,t)==('oldcase','oldpoint'):return variant=='old_also_able'
        if(h,t)==('richcase','richpoint'):return variant!='higher_failure'
        return h=='candidate' and(t in ('end','after') or(variant=='earlier_threshold' and t=='middle')) and variant!='actual_failure'
    v['r5gk']=ability
    v['h257z']=lambda r,h,t:(r,h)==('reference','candidate') and t in POINTS and not(variant=='missing_start' and t=='start')
    v['ic']=lambda a,b,h:h=='candidate' and a in POINTS and b in POINTS and(POINTS.index(a)<POINTS.index(b) or(variant=='cycle' and(a,b)==('end','start')))
    intro=('base','new','new','noise','extra','alias','reference','candidate','start','end')
    v['r5fh']=lambda *a:a==intro and variant!='wrong_introduction'
    v['r5fm']=lambda *a:a==('base','alias','new','extra','reference','candidate','start') and variant!='missing_purpose'
    v['r5fc']=lambda c,g,r,h:Content(SCENES,tuple((c,g,r,h)==('new','extra','reference','candidate') and t in ('start','middle') and not(variant=='freedom_gap' and t=='middle') for t in SCENES))
    return v

def unknowns(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def profile_checks():
    q=''.join('q[k '+n+'['+BASE+' k zcandidate[] k zend[] k zrichcase[] k zrichpoint[]]].' for n in ('r5gm','r5gn'))
    # Include both declarations because r5gn calls r5gm.
    doc=fixture('r5gn',q);rows={}
    for variant,expected in (('baseline',[True,False]),('equal',[True,True]),('missing_new',[False,False])):
        v=model(doc)
        if variant!='baseline':
            old=v['r5fu']
            def public(i,c,g,f,a,r,ass,h,t):
                if(h,t)==('richcase','richpoint'):
                    return i in (('base','new','alias') if variant=='equal' else ('base','alias')) and(c,g,f,a,r,ass)==('new','extra','noise','alias','reference','assessment')
                return old(i,c,g,f,a,r,ass,h,t)
            v['r5fu']=public
        actual=run(doc,v);assert actual==expected;rows[variant]=actual
    one=fixture('r5gl','q[k r5gl[k zitem[] '+FRAME+' k zend[]]].');item_rows={}
    for item in DOMAIN:
        v=model(one);v['zitem']=lambda item=item:item;actual=run(one,v)
        assert actual==[item in ('base','new','alias')];item_rows[item]=actual[0]
    return dict(public_content_inclusion_and_equivalence=rows,only_relevant_corroborated_items=item_rows,
        aliases_not_counted_as_gain=True,boundary='r5fu; native cognition/publicity/corroboration evidence preserved',unknown_rejected=unknowns(one,('h26ag','h26d4','r5fu')))

@lru_cache(None)
def threshold_checks():
    doc=fixture('r5gp','q[k r5gp['+FRAME+' k zstart[] k zend[]]].');rows={}
    for variant in ('baseline','unrelated_gain','alias_gain','already_enough','no_old_comparison','old_also_able','higher_failure','actual_failure','missing_actual_comparison','empty_relevant_scope','wrong_truth_assessment','missing_start','cycle'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(nonvacuous_same_background_threshold_crossing=rows,
        previous_public_profile_tested_in_later_background=True,
        all_at_least_current_profiles_allow_same_proposal=True,
        unknown_rejected=unknowns(doc,('h26d3','h26d4','r5fu','r5gk','h257z','ic')))

@lru_cache(None)
def identity_checks():
    doc=fixture('r5gp','q[k r5gp['+FRAME+' k zstart[] k zend[]]].');rows={}
    for name,length in (('h26d3',12),('h26d4',6),('r5gk',7),('r5fu',9)):
        for pos in range(length):
            v=model(doc);old=v[name]
            # A position already equal to noise must still change; use another marker.
            def changed(*a,old=old,pos=pos):
                a=list(a);a[pos]='outside' if a[pos] in SCENES else ('extra' if a[pos]=='noise' else 'noise');return old(*a)
            v[name]=changed;actual=run(doc,v);assert actual==[False],(name,pos,actual);rows[name+'_'+str(pos)]=actual[0]
    return dict(same_objects_truth_assessment_and_candidate_points=rows)

@lru_cache(None)
def until_checks():
    boundaries=('r5fu','r5gk','r5fh','r5fm','r5fc')
    doc=fixture('r5gr','q[k r5gr['+UNTIL+']].',boundaries);rows={}
    for variant in ('baseline','earlier_threshold','actual_failure','higher_failure','no_old_comparison','freedom_gap','wrong_introduction','missing_purpose','cycle'):
        actual=run(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(first_threshold_at_same_bounded_endpoint=rows,
        native_threshold_and_rkh_r5fi_r5fp=True,endpoint_maintenance_not_required=True,
        boundaries=['r5fu and r5gk; separately checked content and proposal','r5fh and r5fm; preserved short introduction and purpose','r5fc; same order and public freedom checked by prior evidence'])

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='insight_threshold_and_bounded_until_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['r5fu grasped public corroborated cognition','r5gk same protective proposal','r5fp same short introduction and purpose','rkh first attained milestone'],
        remaining=['purpose emphasis concession and metonymy discourse','whole possibility and figurative expectation','whole-sentence author attribution and reading'],
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
    for n,f in [('profiles',profile_checks),('threshold',threshold_checks),('identity',identity_checks),('until',until_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_insight_threshold.py','scripts/check_insight_threshold.py','tests/test_insight_threshold.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_temporary_institution.py'}
    return dict(status='insight_threshold_and_bounded_until_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
