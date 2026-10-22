"""Check actual standing ability and its same-person/discourse connections."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_enlightened_person_conditions import ROOT,LIBRARY,BASIS,PROFILE,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts import check_judgment_performance_quality as quality
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/enlightened-person-conditions-v1.md';READING='data/enlightened-person-conditions-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/judgment-performance-quality-v1.json','reports/prince-conclusion-v1.json','reports/prospect-grounded-apprehension-v1.json')
DOMAIN=('person','other','topic','clause','focus','author','scope');SCENES=('reference','point','elsewhere')
def z(n):return 'k z'+n+'[]'
def code(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,mode='discourse'):
    d=deepcopy(catalog().document);ds=[]
    if mode=='native':
        extra=quality.prior.prior.EXTRA+quality.prior.REFERENCES
        replacements={
         'h26kb':'r zone[] a.r ztwo[] a.r zchoose[a i[a] i[a]] i[a].d h26kb[matter a reference d] i[a][k zchoose[v matter r[k zone[]] r[k ztwo[]]]].',
         'h223h':'r zqualitycontext[] d.d h223h[point d] i[d][r[k zqualitycontext[]]].'}
        for x in d['declarations']:
            if x['name'] in replacements:
                ds.extend(parse(format_graph(dict(d,declarations=ds,statements=[]),'compact')+replacements[x['name']])['declarations'][len(ds):])
            else:ds.append(x)
        d['declarations']=ds
        for declaration in ('r zone[] a.','r ztwo[] a.','r zchoose[a i[a] i[a]] i[a].','r zqualitycontext[] d.'):
            extra=extra.replace(declaration,'')
        roots=(*roots,'zqualitycontext')
    else:
        extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
        if mode=='connection':
            for x in d['declarations']:
                if x['name'] in ('r6ex','r6et'):x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
        else:
            extra+='r ztruth[a d] c.d zboundary[person a] e[b point[k ztruth[v person v point]]].'
            extra+='r znamepick[a i[a] i[a]] i[a].r zrefpick[d i[d] i[d]] i[d].'
            extra+='d h223g[item a] i[a][k znamepick[v item r[k ztopic[]] r[k zother[]]]].'
            extra+='d h223h[point d] i[d][k zrefpick[v point r[k zreference[]] r[k zelsewhere[]]]].'
            p=parse('p:'+extra);names={r['name'] for r in p['declarations']}
            d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in names]
            roots=(*roots,*names);extra=''
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)

def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def ability_checks():
    direct='k r6ex[k ztopic[] k zanchor[]]';quoted='s[k r6ey[r[k ztopic[]] r[k zanchor[]]]]'
    q=''.join('q[t[c['+f+'][k zperson[]]][k zcontext[]]].' for f in (direct,quoted))
    d=fixture(('r6ex','r6ey'),q,'native');rows={}
    def model(variant='baseline'):
        v=quality.ability_model(d,variant)
        v.update(h26vd=lambda t,r:variant!='wrong_domain' and(t,r)==('one','now'),h26ka=v['ztopics'])
        if variant=='empty_matters':v['h26ka']=lambda *a:False
        if variant=='guided':v['ad']=lambda *a:True
        if variant=='wrong_person':v['zperson']=lambda:'other'
        if variant=='one_failed_matter':
            original=v['h26j4']
            v['h26j4']=lambda c,p,m,j,r:original(c,p,m,j,r) if m=='one' else Content(quality.prior.SCENES,(False,)*len(quality.prior.SCENES))
        return v
    # Reuse pinned native quality/guidance/profile tests instead of repeating them.
    for variant in ('baseline','wrong_reference','wrong_domain','empty_matters','one_failed_matter'):
        got=run(d,model(variant),quality.prior.DOMAIN,quality.prior.SCENES)
        assert got==[variant=='baseline']*2,(variant,got);rows[variant]=got
    for n in ('h26vd','h26ka'):
        v=model();v[n]=unknown;rejects(d,v,quality.prior.DOMAIN,quality.prior.SCENES)
    # Assessment remains distinct from the existence of a successful performance.
    q='q[t[c[k r6ev[k ztopic[] k zanchor[] r[k zqualitycontext[]]]][k zperson[]]][k zcontext[]]].'
    a=fixture(('r6ev',),q,'native')
    for variant in ('quality_failure',):
        v=quality.ability_model(a,variant);v.update(h26vd=lambda t,r:(t,r)==('one','now'),h26ka=v['ztopics'])
        assert run(a,v,quality.prior.DOMAIN,quality.prior.SCENES)==[True]
    assert 'h26j7' not in {x['name'] for x in d['declarations']}
    return dict(cases=rows,all_matters_not_one_success=True,assessment_distinct_from_ability=True,
      no_religion_only_filter_reused=True,direct_and_rank_seven_dequotation_agree=True,unknown_rejected=True,
      reused_native_quality_guidance_and_profile_checks=PRIORS[:2],
      native='r6eu/r6ew/r6ex, r5sz, hzvs, rqwn, the standing-ability model and judgment quality all execute. Closed matter/reference names use native Noema definitions; no ability predicate is stubbed.')

def baseline(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    return v
def content(ok):return Content(SCENES,tuple(ok and t=='point' for t in SCENES))

@lru_cache(None)
def connection_checks():
    fs=('k r6ez['+z('topic')+' '+z('reference')+']','s[k r6e2[r['+z('topic')+'] r['+z('reference')+']]]')
    q=''.join('q[t[c['+f+']['+z('person')+']]['+z('point')+']].' for f in fs)
    d=fixture(('r6ez','r6e2'),q,'connection');rows={}
    def model(ability=True,fear=True):
        v=baseline(d)
        v['r6ex']=lambda topic,ref:FunctionValue(('individual',),'content',lambda p:content(ability and(topic,ref,p)==('topic','reference','person')))
        v['r6et']=lambda p,ref:content(fear and(p,ref)==('person','reference'))
        return v
    for bits in product((False,True),repeat=2):
        got=run(d,model(*bits));assert got==[all(bits)]*2;rows[str(bits)]=got
    for variant in ('different_person','different_reference','different_point','different_ability_person'):
        v=model()
        if variant=='different_person':v['r6et']=lambda p,r:content((p,r)==('other','reference'))
        if variant=='different_reference':v['r6et']=lambda p,r:content((p,r)==('person','elsewhere'))
        if variant=='different_point':v['r6et']=lambda p,r:Content(SCENES,(False,False,True))
        if variant=='different_ability_person':v['r6ex']=lambda t,r:FunctionValue(('individual',),'content',lambda p:content(p=='other'))
        assert run(d,v)==[False,False],variant
    for n in ('r6ex','r6et'):
        v=model();v[n]=unknown;rejects(d,v)
    return dict(combinations=rows,same_person_point_reference=True,unknown_rejected=True,
      boundaries='Only r6ex and r6et replaced for this conjunction test. Native ability is tested above; native fear and unbounded-domain refusal are pinned in prospect-grounded-apprehension-v1.')

BOUNDARY='r h[p zboundary]'
@lru_cache(None)
def discourse_checks():
    args=' '.join(z(n) for n in ('focus','clause','author','scope','topic','reference'))+' '+BOUNDARY+' '+z('point')
    d=fixture(('r6e5',),'q[k r6e5['+args+']].')
    def applied(n):return 7,dict(kind='apply',function=dict(kind='function_ref',symbol=n),arguments=[dict(kind='call',symbol='z'+k,arguments=[]) for k in ('topic','reference')])
    boundary=(7,dict(kind='function_ref',symbol='zboundary'))
    v=baseline(d)
    v.update(znamepick=lambda p,a,b:a if p=='topic' else b,zrefpick=lambda p,a,b:a if p=='reference' else b)
    v['h26nq']=lambda focus,author,scope,clause,b,c,t:(focus,author,scope,clause,t)==('focus','author','scope','clause','point') and code(b)==boundary and code(c)==applied('r6ex')
    v['h26nn']=lambda clause,author,scope,b,c,t:(clause,author,scope,t)==('clause','author','scope','point') and code(b)==boundary and code(c)==applied('r6ez')
    assert run(d,v)==[True]
    for name in ('focus','clause','author','scope','topic','reference','point'):
        w=dict(v);w['z'+name]=lambda name=name:'elsewhere' if name in ('reference','point') else 'other'
        assert run(d,w)==[False],name
    for name in ('h26nn','h26nq'):
        w=dict(v);w[name]=lambda *a:False;assert run(d,w)==[False]
        w[name]=unknown;rejects(d,w)
    for name in ('znamepick','zrefpick'):
        w=dict(v);w[name]=lambda p,a,b:b;assert run(d,w)==[False],name
    # Change the interpreted relation's expected quoted content, preserving the roles.
    for n in ('h26nn','h26nq'):
        w=dict(v);original=w[n]
        w[n]=lambda *a,original=original:original(*a) and code(a[-2])==boundary
        assert run(d,w)==[False]
    return dict(same_scope_and_author=True,all_seven_reference_bindings_checked=True,
      both_premise_and_self_emphasis_required=True,exact_separate_ability_and_joint_quotes=True,
      unknown_world_contents_not_executed=True,unknown_discourse_rejected=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');segments=[]
    for phrase in ('selbst aufgeklärt','sich nicht vor Schatten fürchtet'):
        a=u['text'].index(phrase);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='same_person_enlightenment_and_grounded_fear_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for old in parents():
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f','g','h','i')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks['r6ex']==ranks['r6ez']==1 and ranks['r6eu']==0,ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('ability',ability_checks),('connection',connection_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_enlightened_person_conditions.py','scripts/check_enlightened_person_conditions.py','tests/test_enlightened_person_conditions.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_qualified_prince_frame.py',
      'scripts/check_judgment_performance_quality.py','scripts/check_qualified_judgment.py','scripts/check_topical_standing.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_person_enlightenment_and_grounded_fear_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
