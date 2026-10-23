"""Check the same person's capacity, full population and passive-role compatibility."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_human_agency import ROOT,LIBRARY,BASIS,MEANINGS,LIMITS,parent,main_catalog,build,closure
from scripts import check_self_directed_choice as choice
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/civic-human-agency-v1.md';READING='data/civic-human-agency-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/self-directed-choice-v1.json','reports/scholarly-compatibility-v1.json','reports/reasoned-variation-v1.json')
ARTIFACTS=tuple('artifacts/civic-human-agency-v1/'+n for n in ('fetch.json','kant-aa08-037.html','kant-aa08-037.txt'))
DOMAIN=('a','b');SCENES=('reference','other','start','end');PAIRS=tuple(product(DOMAIN,repeat=2))
CONSTANTS=dict(community='b',reference='reference',person='a',point='end')
ARGS='k zcommunity[] k zreference[]';PERSON=ARGS+' k zperson[] k zpoint[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=('r6kl','r6km')):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+extra+query)
def model(d,capacity=15,assessed=15):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic())
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()})
    good=lambda c,r:(c,r)==('b','reference')
    v.update(aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:good(c,r) and p in DOMAIN,
      h26yo=lambda c,p,a,r:good(c,r) and (p,a) in PAIRS,
      h27b5=lambda c,r:seq(DOMAIN if good(c,r) else ()),h27c2=lambda c,r,p:seq(DOMAIN if good(c,r) else ()),
      r6kl=lambda c,r,p,a,t:good(c,r) and t=='end' and bool(assessed&(1<<PAIRS.index((p,a)))),
      r6km=lambda c,r,p,a,t:good(c,r) and t=='end' and bool(capacity&(1<<PAIRS.index((p,a)))))
    return v
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def native_capacity_checks():
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name']=='r6fr':row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,('r6lc','r6ld','r2zu','r6kg'))
    seed=choice.fixture(('r6km',),'')
    d['declarations'].extend(row for row in seed['declarations'] if row['name'].startswith('z'))
    d['statements']=seed['statements']
    q='q[k r6lc[k zcommunity[] k zreference[] k zperson[] k zanchor[]]].q[k r6ld[k zcommunity[] k zreference[] k zanchor[]]].'
    q+='q[t[k r2zu[k zperson[] k zperson[] k zactivity[]]][k zanchor[]]].q[t[k r6kg[k zperson[] k zactivity[]]][k zanchor[]]].'
    d=parse(format_graph(d,'compact')+q);v,_=choice.model(d);v.update(arithmetic())
    v.update(h27b5=lambda c,r:seq(('a',)),h27c2=lambda c,r,p:seq(('b',)),
      h237a=lambda p,role,work,t:(p,role,work,t)==('a','a','b','anchor'),h237b=lambda *a:False)
    assert choice.run(d,v)==[True,True,True,False]
    cases={}
    for label in ('no_available_method','only_execution_method','external_guidance','no_intentional_refraining','missing_assessment','empty_actions'):
        w=dict(v)
        if label=='no_available_method':w['h27cx']=lambda *a:False
        if label=='only_execution_method':w['h27cx']=lambda *a:a[-2]=='a' and v['h27cx'](*a)
        if label=='external_guidance':w['ad']=lambda *a:True
        if label=='no_intentional_refraining':w['h27cs']=lambda *a:a[3] and v['h27cs'](*a)
        if label=='missing_assessment':w['h27cu']=lambda *a:False
        if label=='empty_actions':w['h27c2']=lambda *a:seq(());w['h26yo']=lambda *a:False
        result=choice.run(d,w);assert result[:2]==[False,False],(label,result);assert result[2:]==[True,False];cases[label]=result
    w=dict(v);w['h27cs']=unknown
    try:choice.run(d,w)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
    return dict(native_deliberation_methods_norms_normality_and_passive_role=True,capacity_without_current_execution=True,
      passive_duty_execution_and_independent_capacity_compatible=True,contrasts=cases,unknown_rejected=True,
      boundary='Only prior r6fr institutional-order validity is bounded, as in the pinned self-directed-choice fixture. r6kl/r6km, rcr, rdm, xd/xf and r2zu execute natively.')

@lru_cache(None)
def population_checks():
    d=fixture(('r6lc','r6ld'),'q[k r6lc['+PERSON+']].q[k r6ld['+ARGS+' k zpoint[]]].');rows=0
    for capacity,assessed in product(range(16),repeat=2):
        v=model(d,capacity,assessed)
        eligible=[all(assessed&(1<<(2*p+a)) for a in range(2)) and any(capacity&(1<<(2*p+a)) for a in range(2)) for p in range(2)]
        assert run(d,v)==[bool(eligible[0]),all(eligible)],(capacity,assessed);rows+=1
    cases={};v=model(d,capacity=5)
    assert run(d,v)==[True,True] # different people need not master every activity
    for label in ('no_people','duplicate_people','omitted_person','duplicate_action','omitted_action','nonhuman','wrong_community','wrong_reference','wrong_point'):
        w=dict(v)
        if label=='no_people':w['h27b5']=lambda *a:seq(());w['h237c']=lambda *a:False
        if label=='duplicate_people':w['h27b5']=lambda *a:seq(('a','a','b'))
        if label=='omitted_person':w['h27b5']=lambda *a:seq(('a',))
        if label=='duplicate_action':w['h27c2']=lambda *a:seq(('a','a','b'))
        if label=='omitted_action':w['h27c2']=lambda *a:seq(('a',))
        if label=='nonhuman':w['aa']=lambda p:p=='a'
        if label=='wrong_community':w['zcommunity']=lambda:'a'
        if label=='wrong_reference':w['zreference']=lambda:'other'
        if label=='wrong_point':w['zpoint']=lambda:'start'
        result=run(d,w);assert result[-1] is False,(label,result);cases[label]=result
    for n in ('h27b5','h27c2','r6kl','r6km','h26yo'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_256_capacity_assessment_rows=rows,at_least_one_activity_per_person_suffices=True,contrasts=cases,unknown_rejected=True,
      boundary='r6kl/r6km are bounded to isolate all-person/all-activity scope. Their native bodies are exercised separately above and pinned by the prior report.')

@lru_cache(None)
def family_checks():
    d=fixture(('r6le','r6lf'),'q[t[c[k r6le['+ARGS+']][k zperson[]]][k zpoint[]]].q[t[k r6lf['+ARGS+']][k zpoint[]]].',('r6lc','r6ld'))
    v=model(d);calls=[]
    def person(*a):calls.append(a);return a==('b','reference','a','end')
    v['r6lc']=person;v['r6ld']=lambda *a:a==('b','reference','end');rows=0
    for c,r,p,t in product(DOMAIN,('reference','other'),DOMAIN,('start','end')):
        w=dict(v)
        for n,x in zip(CONSTANTS,(c,r,p,t)):w['z'+n]=lambda x=x:x
        calls.clear();assert run(d,w)==[(c,r,p,t)==('b','reference','a','end'),(c,r,t)==('b','reference','end')]
        assert(c,r,p,t)in calls;rows+=1
    return dict(all_16_family_and_whole_population_bindings=rows,boundary='Only r6lc/r6ld are bounded; their native bodies are checked separately.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_population_deliberative_human_relative_clause_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[1094,1139],text=u['text'][1094:1139],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['尊厳に応じた扱いの具体的内容','政府自身の利益判断、原則への作用、同じ政治的終点へのnunの束縛','Wenn/soと全対象・全文帰属・通読判断'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,*ARTIFACTS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for prior in (parent(),main_catalog()):
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    fetch=read(ARTIFACTS[0]);assert digest((ROOT/ARTIFACTS[1]).read_bytes())==fetch['raw_sha256'];assert digest((ROOT/ARTIFACTS[2]).read_bytes())==fetch['text_sha256']
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    text=format_graph(c.document,'compact')
    for n in MEANINGS:parse(text+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=0,minimum_quote_ranks={n:0 for n in MEANINGS},
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('native_capacity',native_capacity_checks),('population',population_checks),('family',family_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,*ARTIFACTS,
      'scripts/compose_civic_human_agency.py','scripts/check_civic_human_agency.py','tests/test_civic_human_agency.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_self_directed_choice.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='same_population_deliberative_human_relative_clause_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
