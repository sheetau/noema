"""Check exact public grounds and corroboration, including non-vacuous witnesses."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_public_insight import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/public-insight-v1.json'
DOC='docs/public-insight-v1.md'
READING='data/public-insight-reading-v1.json'
PRIORS=('reports/cognitive-acquisition-v1.json','reports/institutional-criticism-v1.json','reports/institutional-outlook-v1.json')
DOMAIN=('person','item','alias','judgment','reason','review','evidence','community','regime','field','audience','other')
SCENES=('reference','assessment','candidate','first','last','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
EXTRA+='r ztruth[a d d] c.d h26ae[item a scope d] e[b point[k ztruth[v item v scope v point]]].'
FRAME='k zcommunity[] k zregime[] k zfield[] k zaudience[] k ztreference[] k ztassessment[] k ztcandidate[]'
SUFFIX=('reference','candidate','last')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    provider=parse('p:'+EXTRA);ns={d['name'] for d in provider['declarations']}
    doc['declarations']=provider['declarations']+[d for d in doc['declarations'] if d['name'] not in ns]
    return parse(format_graph(doc,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)

def model(doc,variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v['h26ag']=lambda i,r:'item' if i=='alias' else i
    v['h26ad']=lambda i,r:i in ('item','alias') and r=='reference'
    v['aa']=lambda p:p=='person';v['ztruth']=lambda i,r,t:(i,r,t)==('item','reference','assessment')
    v['h26af']=lambda p,i,r,t:(p,r,t)==('person','reference','last') and i=='item'
    v['h26ah']=lambda p,i,r,t:(p,i,r,t)==('person','item','reference','last')
    v['h26ai']=lambda p,j,r,t:(p,j,r,t)==('person','judgment','reference','last')
    v['h26aj']=lambda r,j,ref,t:(r,j,ref,t)==('reason','judgment','reference','last')
    v['h245q']=lambda j,i,c,r,sign,t:j in ('judgment','review') and(i,r,sign,t)==('item','reference',True,'last') and c.rank==0 and symbol(c)=='h26ae'
    v['fc']=lambda j,r,t:t=='last' and(j,r) in (('judgment','reason'),('review','evidence'))
    v['fd']=lambda r,j,t:t=='last' and(r,j) in (('reason','judgment'),('evidence','review'))
    v['dg']=lambda a,t:(a,t)==('review','last')
    v['h26cs']=lambda g,c,r:(g,c,r)==('regime','community','reference')
    v['h26ct']=lambda f,g,r:(f,g,r)==('field','regime','reference')
    v['h26c5']=lambda i,f,r:(i,f,r)==('item','field','reference')
    v['h26c6']=lambda a,p,j,i,r,c,t:(a,p,j,i,r,c,t)==('audience','person','judgment','item',*SUFFIX)
    v['h26c7']=lambda a,reason,j,r,c,t:(a,r,c,t)==('audience',*SUFFIX) and(reason,j) in (('reason','judgment'),('evidence','review'))
    v['h26da']=lambda rev,j,r,c,t:(rev,j,r,c,t)==('review','judgment',*SUFFIX)
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in ('first','last')
    v['ic']=lambda a,b,c:(a,b,c)==('first','last','candidate')
    return v

def unknowns(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def scope_checks():
    doc=fixture(('r5fq',),'q[k r5fq[k zitem[] k zcommunity[] k zregime[] k zfield[] k ztreference[]]].');rows={}
    for missing in (None,'h26cs','h26ct','h26ad','h26c5'):
        v=model(doc)
        if missing:v[missing]=lambda *a:False
        actual=run(doc,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    v=model(doc);v['zitem']=lambda:'alias';assert run(doc,v)==[True]
    return dict(all_same_subject_relations=rows,canonical_alias_preserved=True,
        unknown_rejected=unknowns(doc,('h26cs','h26ct','h26ad','h26c5','h26ag')))

@lru_cache(None)
def grounding_checks():
    q='q[k r5fr[k zperson[] k zitem[] k zjudgment[] k zreason[] k zaudience[] k ztreference[] k ztcandidate[] k ztlast[]]].'
    doc=fixture(('r5fr',),q);names=('h26ai','h245q','fc','fd','h26aj','h26c6','h26c7');rows=[]
    for bits in product((False,True),repeat=7):
        v=model(doc)
        for n,yes in zip(names,bits):
            if not yes:v[n]=lambda *a:False
        v['ztruth']=unknown;actual=run(doc,v);assert actual==[all(bits)];rows.append(dict(bits=list(bits),value=actual[0]))
    contrasts={}
    for n,length in (('h26c6',7),('h26c7',6)):
        for pos in range(length):
            v=model(doc);old=v[n]
            def changed(*a,old=old,pos=pos):
                a=list(a);a[pos]='other' if pos<len(a)-3 else 'outside';return old(*a)
            v[n]=changed;actual=run(doc,v);assert actual==[False];contrasts[n+'_'+str(pos)]=actual[0]
    return dict(seven_conditions=rows,exact_public_judgment_and_ground=contrasts,content_not_executed_here=True,
        unknown_rejected=unknowns(doc,names))

@lru_cache(None)
def corroboration_checks():
    q='q[k r5fs[k zitem[] k zjudgment[] k zreview[] k zevidence[] k zaudience[] k ztreference[] k ztcandidate[] k ztlast[]]].'
    doc=fixture(('r5fs',),q);names=('h26da','dg','h245q','fc','fd','h26c7');rows=[]
    for bits in product((False,True),repeat=6):
        v=model(doc)
        for n,yes in zip(names,bits):
            if not yes:v[n]=lambda *a:False
        actual=run(doc,v);assert actual==[all(bits)];rows.append(dict(bits=list(bits),value=actual[0]))
    contrasts={}
    for variant in ('negative_conclusion','different_item','different_provider','other_review_target','unused_evidence','other_evidence_support','private_evidence'):
        v=model(doc)
        if variant in ('negative_conclusion','different_item','different_provider'):
            v['h245q']=lambda j,i,c,r,sign,t:j=='review' and (i==('alias' if variant=='different_item' else 'item')) and sign==(variant!='negative_conclusion') and symbol(c)==('r5cc' if variant=='different_provider' else 'h26ae')
        if variant=='other_review_target':v['h26da']=lambda rev,j,r,c,t:(rev,j,r,c,t)==('review','other',*SUFFIX)
        if variant=='unused_evidence':v['fc']=lambda *a:False
        if variant=='other_evidence_support':v['fd']=lambda r,j,t:(r,j,t)==('reason','review','last')
        if variant=='private_evidence':v['h26c7']=lambda *a:False
        actual=run(doc,v);assert actual==[False];contrasts[variant]=actual[0]
    return dict(six_conditions=rows,same_content_confirmed_with_public_evidence=contrasts,
        unknown_rejected=unknowns(doc,names))

@lru_cache(None)
def connection_checks():
    q='q[k r5ft[k zperson[] k zitem[] '+FRAME+' k ztlast[]]].'
    doc=fixture(('r5ft',),q,('r5fq','r5cl','r5fr','r5fs'));rows=[]
    def small(bits):
        v=model(doc);v.update({'z'+n:lambda:'alpha' for n in DOMAIN})
        v['r5fq']=lambda *a:bits[0] and a==('alpha',)*4+('reference',)
        v['r5cl']=lambda *a:bits[1] and a==('alpha','alpha','reference','assessment','last')
        v['r5fr']=lambda *a:bits[2] and a==('alpha','alpha','alpha','alpha','alpha',*SUFFIX)
        v['r5fs']=lambda *a:bits[3] and a==('alpha','alpha','beta','beta','alpha',*SUFFIX)
        return v
    for bits in product((False,True),repeat=4):
        actual=run(doc,small(bits),('alpha','beta'));assert actual==[all(bits)];rows.append(dict(bits=list(bits),value=actual[0]))
    v=small((True,)*4);v['r5fs']=lambda *a:a==('alpha','beta','beta','beta','alpha',*SUFFIX)
    assert run(doc,v,('alpha','beta'))==[False]
    return dict(same_nonempty_grounding_and_confirmation_witnesses=rows,different_judgment_confirmation_rejected=True,
        boundaries=['r5fq','r5cl','r5fr','r5fs'])

@lru_cache(None)
def native_insight_checks():
    q='q[k r5ft[k zperson[] k zitem[] '+FRAME+' k ztlast[]]].'
    doc=fixture(('r5ft',),q);rows={}
    def small():
        v=model(doc);v.update({'z'+n:lambda:'alpha' for n in DOMAIN})
        v['h26ag']=lambda i,r:i;v['h26ad']=lambda i,r:i=='alpha' and r=='reference'
        v['aa']=lambda p:p=='alpha';v['ztruth']=lambda i,r,t:(i,r,t)==('alpha','reference','assessment')
        v['h26af']=lambda p,i,r,t:(p,i,r,t)==('alpha','alpha','reference','last')
        v['h26ah']=v['h26af'];v['h26ai']=v['h26af']
        v['h26aj']=lambda reason,j,r,t:(reason,j,r,t)==('beta','alpha','reference','last')
        v['h245q']=lambda j,i,c,r,sign,t:j in ('alpha','beta') and(i,r,sign,t)==('alpha','reference',True,'last') and c.rank==0 and symbol(c)=='h26ae'
        v['fc']=lambda j,r,t:t=='last' and(j,r) in (('alpha','beta'),('beta','alpha'))
        v['fd']=lambda r,j,t:t=='last' and(r,j) in (('beta','alpha'),('alpha','beta'))
        v['dg']=lambda a,t:(a,t)==('beta','last')
        for n in ('h26cs','h26ct','h26c5'):v[n]=lambda x,y,r:(x,y,r)==('alpha','alpha','reference')
        v['h26c6']=lambda *a:a==('alpha',)*4+SUFFIX
        v['h26c7']=lambda aud,r,j,ref,c,t:aud=='alpha' and(ref,c,t)==SUFFIX and(r,j) in (('beta','alpha'),('alpha','beta'))
        v['h26da']=lambda *a:a==('beta','alpha',*SUFFIX)
        return v
    for missing in (None,'h26af','h26ah','h26ai','h26aj','ztruth','h26c6','h26c7','h26da','dg'):
        v=small()
        if missing:v[missing]=lambda *a:False
        actual=run(doc,v,('alpha','beta'));assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    return dict(native_cognition_publicity_and_corroboration=rows,no_definition_boundaries=True)

@lru_cache(None)
def progress_checks():
    q='q[k r5fv['+FRAME+' k ztfirst[] k ztlast[]]].'
    doc=fixture(('r5fv',),q,('r5ft',));rows={}
    for variant in ('new_public_insight','only_private_before','already_public','new_person_same_insight','alias_only','missing_truth_assessment','wrong_candidate','wrong_field','cycle','reversed'):
        v=model(doc)
        def public(p,i,c,g,f,a,r,assessment,h,t):
            if (c,g,f,a,r,assessment,h)!=('community','regime','field','audience','reference','assessment','outside' if variant=='wrong_candidate' else 'candidate'):return False
            if variant=='missing_truth_assessment' or(variant=='wrong_field' and f=='field'):return False
            if i not in ('item','alias'):return False
            if t=='last':return p=='person'
            if t=='first' and variant in ('already_public','new_person_same_insight','alias_only'):return p==('other' if variant=='new_person_same_insight' else 'person')
            return False
        v['r5ft']=public
        if variant=='cycle':v['ic']=lambda a,b,c:c=='candidate' and a!=b and a in ('first','last') and b in ('first','last')
        if variant=='reversed':v['ztfirst']=lambda:'last';v['ztlast']=lambda:'first'
        actual=run(doc,v);expected=variant in ('new_public_insight','only_private_before')
        assert actual==[expected],(variant,actual);rows[variant]=actual[0]
    return dict(public_insight_gain_without_unanimity=rows,boundary='r5ft; all components checked natively',
        fixed_content_and_assessment=True,does_not_assert_proposal_sufficiency=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='public_grasp_ground_and_corroboration_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['r5cl grasped and grounded cognition','h26ag fixed canonical items','h245q same positive content','fc/fd used and supporting reasons'],
        remaining=['so weit: sufficiency for a common proposal','united voices and throne recipient','protection and nonhindrance proposal content',
            'temporal milestone, possibility and whole-sentence discourse'],new_verified_characters=0,whole_sentence_semantically_verified=False)

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
    for n,f in [('scope',scope_checks),('grounding',grounding_checks),('corroboration',corroboration_checks),('connection',connection_checks),
            ('native_insight',native_insight_checks),('progress',progress_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_public_insight.py','scripts/check_public_insight.py','tests/test_public_insight.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='public_grasp_ground_and_corroboration_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
