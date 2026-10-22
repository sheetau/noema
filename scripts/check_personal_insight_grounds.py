"""Check subjective appraisal, exact content and reasons for the same assent."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_insight_grounds import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_congregational_choices import model as choice_model,DOMAIN as CHOICE_DOMAIN,SCENES,FRAME,CONTEXT

REPORT='reports/personal-insight-grounds-v1.json'
DOC='docs/personal-insight-grounds-v1.md'
READING='data/personal-insight-grounds-reading-v1.json'
PRIORS=('reports/congregational-choices-v1.json','reports/public-insight-v1.json','reports/cognitive-acquisition-v1.json')
DOMAIN=(*CHOICE_DOMAIN,'judgment','standard','baseline','preferred','alias')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)+'r zbindings[] j[a].'
BIND=('newer','field','standard','baseline','preferred')
APPRAISAL='k znewer[] k zfield[] k zstandard[] k zbaseline[] k zpreferred[] k zreference[] k zbefore[]'
ASSENT='k zp[] k zactone[] k zjudgment[] k zagreement[] '+FRAME+' k znewer[] k zstandard[] k zbaseline[] k zpreferred[] '+CONTEXT+' k zbefore[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,[root]),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def model(doc):
    v=choice_model(doc);v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(BIND,'"individual"')
    v['h26ag']=lambda item,ref:'preferred' if item=='alias' else item
    v['h26ad']=lambda item,ref:item in ('baseline','preferred','alias') and ref=='reference'
    v['h26c5']=lambda item,f,r:item in ('baseline','preferred') and(f,r)==('field','reference')
    v['h26dn']=lambda s,f,left,right,r,t:(s,f,r,t)==('standard','field','reference','comparison') and(left,right) in (('baseline','baseline'),('preferred','preferred'),('preferred','baseline'))
    v['h26dp']=lambda config,item,f,r,t:(config,item,f,r,t)==('newer','preferred','field','reference','comparison')
    v['h26do']=lambda p,s,base,f,r,t:(p,s,base,f,r,t)==('p','standard','baseline','field','reference','before')
    v['h26dq']=lambda j,target,b,r,sign,t:normalized((j,target,b,r,sign,t))==('judgment',('r5gb',0),BIND,'reference',True,'before')
    v['h26ai']=lambda p,j,r,t:(p,j,r,t)==('p','judgment','reference','before')
    v['h26dr']=lambda p,a,j,r,c,t:(p,a,j,r,c,t)==('p','actone','judgment','reference','candidate','before')
    return v

def unknowns(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def comparative_checks():
    q='q[t[k r5ga[k zbaseline[] k zpreferred[] k zfield[] k zstandard[] k zreference[]]][k zcomparison[]]].'
    doc=fixture('r5ga',q);rows=[]
    for bits in product((False,True),repeat=4):
        v=model(doc);pairs=dict(zip((('baseline','baseline'),('preferred','preferred'),('preferred','baseline'),('baseline','preferred')),bits))
        v['h26dn']=lambda s,f,l,r,ref,t:(s,f,ref,t)==('standard','field','reference','comparison') and pairs.get((l,r),False)
        actual=run(doc,v);expected=bits==(True,True,True,False);assert actual==[expected];rows.append(dict(bits=bits,value=actual[0]))
    contrasts={}
    for variant in ('alias_preserved','same_content','out_of_scope','wrong_field','wrong_assessment','no_content_domain'):
        v=model(doc)
        if variant=='alias_preserved':v['zpreferred']=lambda:'alias'
        if variant=='same_content':v['zbaseline']=lambda:'alias'
        if variant=='out_of_scope':v['h26c5']=lambda *a:False
        if variant=='wrong_field':v['zfield']=lambda:'other'
        if variant=='wrong_assessment':v['zcomparison']=lambda:'outside'
        if variant=='no_content_domain':v['h26ad']=lambda *a:False
        actual=run(doc,v);assert actual==[variant=='alias_preserved'];contrasts[variant]=actual[0]
    return dict(strict_comparison=rows,canonical_same_domain=contrasts,unknown_rejected=unknowns(doc,('h26ag','h26ad','h26c5','h26dn')))

@lru_cache(None)
def content_checks():
    q='q[t[k r5gb[k zbindings[] k zreference[]]][k zcomparison[]]].'
    # Small native evaluation verifies comparison and configuration fit together.
    native=fixture('r5gb',q);rows={}
    for variant in ('baseline','no_fit','not_configuration','no_comparison'):
        v=model(native)
        # Two cognitive markers also serve the remaining independent slots.
        v['zbindings']=lambda:SequenceValue(('alpha','alpha','alpha','alpha','beta'),'"individual"')
        v['h26ag']=lambda i,r:i;v['h26ad']=lambda i,r:r=='reference'
        v['h26c5']=lambda i,f,r:f=='alpha' and r=='reference'
        v['h26dn']=lambda s,f,l,r,ref,t:(s,f,ref,t)==('alpha','alpha','reference','comparison') and(l,r) in (('alpha','alpha'),('beta','beta'),('beta','alpha')) and variant!='no_comparison'
        v['h246w']=lambda i,f,r:(i,f,r)==('alpha','alpha','reference') and variant!='not_configuration'
        v['h26dp']=lambda i,item,f,r,t:(i,item,f,r,t)==('alpha','beta','alpha','reference','comparison') and variant!='no_fit'
        actual=run(native,v,('alpha','beta'));assert actual==[variant=='baseline'];rows[variant]=actual[0]
    # All slots vary independently, using a separately checked comparison boundary.
    doc=fixture('r5gb',q,('r5ga',));counts=[]
    from noema.constructed_semantics import Content
    for expected in product(('alpha','beta'),repeat=5):
        count=0
        for offered in product(('alpha','beta'),repeat=5):
            v=model(doc);v['zbindings']=lambda offered=offered:SequenceValue(offered,'"individual"')
            v['h26ag']=lambda i,r:i
            v['h246w']=lambda i,f,r:(i,f,r)==(*expected[:2],'reference')
            v['h26dp']=lambda i,item,f,r,t:(i,item,f,r,t)==(expected[0],expected[4],expected[1],'reference','comparison')
            v['r5ga']=lambda base,pref,f,s,r:Content(SCENES,tuple((base,pref,f,s,r)==(expected[3],expected[4],expected[1],expected[2],'reference') and t=='comparison' for t in SCENES))
            actual=run(doc,v,('alpha','beta'));assert actual==[offered==expected];count+=actual[0]
        counts.append(count)
    for bad in ((),('alpha',)*4,('alpha',)*6):
        v['zbindings']=lambda bad=bad:SequenceValue(bad,'"individual"');assert run(doc,v,('alpha','beta'))==[False]
    return dict(native_comparison_and_same_configuration_fit=rows,exact_binding_cases=1024,one_exact_binding_per_pattern=counts,wrong_lengths_rejected=True)

@lru_cache(None)
def held_appraisal_checks():
    doc=fixture('r5gc','q[k r5gc[k zp[] k zjudgment[] '+APPRAISAL+']].');rows={}
    for missing in (None,'h26ai','h26do','h26dq'):
        v=model(doc);v['h26dn']=unknown;v['h26dp']=unknown
        if missing:v[missing]=lambda *a:False
        actual=run(doc,v);assert actual==[missing is None];rows[missing or 'baseline']=actual[0]
    mismatches={}
    for name,length in (('h26ai',4),('h26do',6),('h26dq',6)):
        for pos in range(length):
            v=model(doc);old=v[name]
            def changed(*a,name=name,pos=pos,old=old):
                if name=='h26dq' and pos in (1,2):return False
                a=list(a);a[pos]=False if name=='h26dq' and pos==4 else 'outside' if a[pos] in SCENES else 'other';return old(*a)
            v[name]=changed;actual=run(doc,v);assert actual==[False];mismatches[name+'_'+str(pos)]=actual[0]
    return dict(held_own_appraisal=rows,exact_owner_standard_baseline_content=mismatches,
        objective_comparison_not_executed=True,no_current_judging_act_required=True,unknown_rejected=unknowns(doc,('h26ai','h26do','h26dq','h26ag')))

@lru_cache(None)
def grounded_assent_checks():
    doc=fixture('r5gd','q[k r5gd['+ASSENT+']].');rows={}
    for missing in (None,'h26dl','h26ai','h26do','h26dq','h26dr','dg','f3'):
        v=model(doc)
        if missing:v[missing]=lambda *a:False
        v['h26dn']=unknown;v['h26dp']=unknown;v['h246x']=unknown
        actual=run(doc,v);assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    contrast={}
    for pos in range(6):
        v=model(doc);old=v['h26dr']
        def changed(*a,pos=pos,old=old):
            a=list(a);a[pos]='outside' if pos>=3 else 'other';return old(*a)
        v['h26dr']=changed;actual=run(doc,v);assert actual==[False];contrast[str(pos)]=actual[0]
    return dict(native_same_assent_and_held_reason=rows,same_reason_person_activity_judgment_time=contrast,
        native_definitions_without_boundaries=True,new_arrangement_and_epistemic_success_not_executed=True,
        unknown_rejected=unknowns(doc,('h26dr','h26dl','h26ai','h26do','h26dq')))

@lru_cache(None)
def all_parties_checks():
    query='q[k r5ge[k zagreement[] '+FRAME+' k zolder[] k znewer[] '+CONTEXT+']].'
    doc=fixture('r5ge',query,('r5f5','r5gd'));rows={}
    for variant in ('different_criteria','same_criterion','missing_second_reason','split_activity','split_point','wrong_configuration','wrong_agreement','no_collective_agreement'):
        v=model(doc);v.update({'z'+n:lambda:'alpha' for n in DOMAIN})
        v['r5f5']=lambda *a:a==('alpha',)*7+('reference','candidate','anchor') and variant!='no_collective_agreement'
        v['h26dj']=lambda g,p,r,c,t:(g,r,c,t)==('alpha','reference','candidate','anchor') and p in ('alpha','beta')
        def witness(p,act,j,g,c,cong,f,sub,new,s,base,pref,r,h,anchor,point):
            if variant=='missing_second_reason' and p=='beta':return False
            expected_standard='alpha' if variant=='same_criterion' else p
            if(g,c,cong,f,sub,new,r,h,anchor)!=('beta' if variant=='wrong_agreement' else 'alpha','alpha','alpha','alpha','alpha','beta' if variant=='wrong_configuration' else 'alpha','reference','candidate','anchor'):return False
            return (act,j,s,base,pref,point)==(p,p,expected_standard,'alpha','beta','before' if p=='alpha' else 'anchor') and variant not in ('split_activity','split_point')
        v['r5gd']=witness
        actual=run(doc,v,('alpha','beta'));assert actual==[variant in ('different_criteria','same_criterion')],(variant,actual);rows[variant]=actual[0]
    return dict(all_fixed_parties_personal_ground=rows,boundaries=['r5f5 preserved and checked in prior report','r5gd natively checked above'])

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='personal_insight_grounds_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        supporting_source='https://korpora.org/kant/aa08/039.html',adopted_readings=LIMITS,
        reuse=['h26ai presently held judgment','h26ad/h26ag/h26ae canonical explicit cognition contents','h26c5 same institutional field','r5f4 exact assent witness','r5f5 complete fixed agreement parties'],
        remaining=['protection and nonhindrance of the same arrangement','public insight sufficient for proposal','temporal milestone and whole attribution'],
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
    for n,f in [('comparative',comparative_checks),('content',content_checks),('held_appraisal',held_appraisal_checks),('grounded_assent',grounded_assent_checks),('all_parties',all_parties_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_personal_insight_grounds.py','scripts/check_personal_insight_grounds.py','tests/test_personal_insight_grounds.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/check_congregational_choices.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_congregational_choices.py'}
    return dict(status='personal_insight_grounds_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
