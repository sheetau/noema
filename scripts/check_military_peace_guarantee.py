"""Check causal peace guarantees and the complete same-person condition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_military_peace_guarantee import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,STATE,EQUATIONS,WORLDS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/military-peace-guarantee-v1.md';READING='data/military-peace-guarantee-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/disciplined-availability-v1.json','reports/civic-peace-concord-v1.json',
        'reports/community-protection-v1.json','reports/enlightened-person-conditions-v1.json')
DOMAIN=('a','b','c');ROWS=tuple(product((False,True),repeat=3))
SCENES=('reference','anchor','background','secondbackground',*('w'+''.join(str(int(x)) for x in r) for r in ROWS))
CONSTANTS=dict(chief='a',institution='b',group='c',community='b',threat='a',topic='c',person='a',
               reference='reference',anchor='anchor',background='background')
FRAME=('chief','institution','group','community');CONTEXT=FRAME+('threat','reference','anchor','background')
ST={'kind':'function','parameters':['individual'],'result':'truth'}
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def bits(t):return tuple(c=='1' for c in t[1:]) if t.startswith('w') else (True,False,True)
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def state(row):return FunctionValue(('individual',),'truth',lambda n:row[DOMAIN.index(n)] if n in DOMAIN else False)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zvars[] j[a].r zeq[a '+STATE+'] c.r zfactor[] a.r zthreatfactor[] a.r zpeacefactor[] a.r zworld['+STATE+'] d.'
    extra+='r zarmy[d] c.r zpeace[d] c.r zdanger[d] c.'
    extra+='d zarmycontent[] e[b point[k zarmy[v point]]].d zpeacecontent[] e[b point[k zpeace[v point]]].d zthreatcontent[] e[b point[k zdanger[v point]]].'
    return parse(format_graph(d,'compact')+extra+query)

def model(d,table=(True,False,True,True)):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    v.update(zvars=lambda:SequenceValue(DOMAIN,'"individual"'),zeq=lambda n,s:table[2*int(s('a'))+int(s('b'))] if n=='c' else s(n),
      zfactor=lambda:'a',zthreatfactor=lambda:'b',zpeacefactor=lambda:'c',zworld=lambda s:'w'+''.join(str(int(s(n))) for n in DOMAIN),
      zarmy=lambda t:bits(t)[0],zpeace=lambda t:bits(t)[2],zdanger=lambda t:bits(t)[1])
    v.update(h26vr=lambda *a:v['zvars'](),h26vs=lambda *a:FunctionValue(('individual',ST),'truth',v['zeq']),
      h26vt=lambda *a:'a',h26vu=lambda *a:'b',h26vv=lambda *a:'c',h26vw=lambda *a:FunctionValue((ST,),'situation',v['zworld']),
      h26vx=lambda c,th,r:content(lambda t:(c,r)==('b','reference') and th in ('a','b') and bits(t)[1]),
      r6fh=lambda *a:content(lambda t:a==('a','b','c','b','reference') and bits(t)[0]),
      aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),
      dg=lambda e,t:e=='c' and not bits(t)[2],h26qq=lambda e,r:(e,r)==('c','reference'),
      h26qp=lambda e,c,r,t:(e,c,r)==('c','b','reference') and not bits(t)[2],
      h26vp=lambda c,th,r:(c,r)==('b','reference') and th in ('a','b'),
      h26vq=lambda c,th,r,a,bg:(c,r,a)==('b','reference','anchor') and th in ('a','b') and bg in ('background','secondbackground'))
    return v
def run(d,v,people=DOMAIN,scenes=SCENES):return evaluate(d,v,people,scenes,True)
def rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def causal_checks():
    call='k zvars[] p zeq k zfactor[] k zthreatfactor[] k zpeacefactor[] p zworld k zarmycontent[] k zpeacecontent[] k zthreatcontent[]'
    d=fixture(('r6fk',),'q[k r6fk['+call+']].');rows=[]
    for table in product((False,True),repeat=4):
        solutions={(p,t):[(p,t,s) for s in (False,True) if s==table[2*int(p)+int(t)]] for p,t in product((False,True),repeat=2)}
        expected=all(sol and all(r[2]==(r[0] or not r[1]) for r in sol) for sol in solutions.values())
        got=run(d,model(d,table));assert got==[expected],(table,got)
        rows.append(dict(table=list(table),guarantee=expected))
    v=model(d);cases={}
    for variant in ('empty_variables','duplicate_variables','missing_peace','same_peace_army','same_peace_threat','same_army_threat',
                    'no_solutions','multiple_solutions','wrong_worlds','wrong_army','wrong_peace','wrong_threat'):
        w=dict(v)
        if variant=='empty_variables':w['zvars']=lambda:SequenceValue((),'"individual"')
        if variant=='duplicate_variables':w['zvars']=lambda:SequenceValue(('a','b','c','a'),'"individual"')
        if variant=='missing_peace':w['zvars']=lambda:SequenceValue(('a','b'),'"individual"')
        if variant=='same_peace_army':w['zpeacefactor']=lambda:'a'
        if variant=='same_peace_threat':w['zpeacefactor']=lambda:'b'
        if variant=='same_army_threat':w['zthreatfactor']=lambda:'a'
        if variant=='no_solutions':w['zeq']=lambda n,s:not s(n) if n=='c' else s(n)
        if variant=='multiple_solutions':w['zeq']=lambda n,s:s(n)
        if variant=='wrong_worlds':w['zworld']=lambda s:'w111'
        if variant=='wrong_army':w['zarmy']=lambda t:not bits(t)[0]
        if variant=='wrong_peace':w['zpeace']=lambda t:not bits(t)[2]
        if variant=='wrong_threat':w['zdanger']=lambda t:not bits(t)[1]
        assert run(d,w)==[False],variant;cases[variant]=False
    for n in ('zeq','zworld','zarmy','zpeace','zdanger'):
        w=dict(v);w[n]=unknown;rejected(d,w)
    return dict(memoryless_boolean_tables=rows,contrasts=cases,independent_solution_enumeration=True,
      native='r6fk/rks/rku/rw/ru/rs; three variables, four interventions, eight possible assignments.',
      reused_cyclic_table_evidence=PRIORS[2],unknown_rejected=True)

@lru_cache(None)
def content_binding_checks():
    q='q[k r6fl['+args(CONTEXT)+']].';d=fixture(('r6fl',),q,('r6fh',));v=model(d);assert run(d,v)==[True];cases={}
    for variant in ('empty_community','uncontained_disturbance','wrong_army','wrong_threat','unknown_peace','actual_disorder_only'):
        w=dict(v);want=variant=='actual_disorder_only'
        if variant=='empty_community':w['h237c']=lambda *a:False
        if variant=='uncontained_disturbance':w['dg']=lambda e,t:e=='c';w['h26qp']=lambda *a:True
        if variant=='wrong_army':w['r6fh']=lambda *a:content(lambda t:not bits(t)[0])
        if variant=='wrong_threat':w['h26vx']=lambda *a:content(lambda t:not bits(t)[1])
        if variant=='unknown_peace':w['h26qp']=unknown;rejected(d,w);cases[variant]='rejected';continue
        if variant=='actual_disorder_only':
            w['dg']=lambda e,t:e=='c' and (t=='anchor' or not bits(t)[2])
            w['h26qp']=lambda e,c,r,t:(e,c,r)==('c','b','reference') and (t=='anchor' or not bits(t)[2])
        got=run(d,w);assert got==[want],(variant,got);cases[variant]=want
    # Record every actual provider call rather than inferring bindings from a
    # false conjunction whose other half may mask an incorrect argument.
    bound=fixture(('r6fl',),q,('r6fh','r6fk'));v=model(bound);calls=[]
    providers=('h26vr','h26vs','h26vt','h26vu','h26vv','h26vw','h26vx','r6fh')
    for n in providers:
        f=v[n]
        def recorded(*a,n=n,f=f):calls.append((n,a));return f(*a)
        v[n]=recorded
    def check_values(vs,eq,p,t,s,world,army,peace,threat):
        sample=state((True,True,True))
        return vs.items==DOMAIN and (p,t,s)==DOMAIN and eq('c',sample) and world(sample)=='w111' and army.values==tuple(bits(t)[0] for t in SCENES) and peace.values==tuple(bits(t)[2] for t in SCENES) and threat.values==tuple(bits(t)[1] for t in SCENES)
    v['r6fk']=check_values;assert run(bound,v)==[True]
    def expected(constants):
        whole=tuple(constants[n] for n in CONTEXT)
        return {n:whole for n in providers[:6]}|{'h26vx':tuple(constants[n] for n in ('community','threat','reference')),'r6fh':tuple(constants[n] for n in FRAME+('reference',))}
    assert len(calls)==8 and dict(calls)==expected(CONSTANTS),calls
    for name in CONTEXT:
        calls.clear();w=dict(v);new=dict(CONSTANTS);new[name]='secondbackground' if name in ('reference','anchor','background') else ('b' if new[name]=='a' else 'a')
        w['z'+name]=lambda name=name,new=new:new[name];w['r6fk']=lambda *a:True
        run(bound,w);assert len(calls)==8 and dict(calls)==expected(new),(name,calls)
    for n in providers:
        w=model(d);w[n]=unknown;rejected(d,w)
    return dict(cases=cases,all_eight_context_slots_and_provider_arities_checked=True,native_public_peace_body=True,
      boundary='r6fh only in causal/content tests; its native body is pinned. r6fk only in the additional argument-recording test.',unknown_rejected=True)

@lru_cache(None)
def scope_checks():
    q='q[t[k r6fm['+args(FRAME+('reference',))+']]['+z('anchor')+']].'
    d=fixture(('r6fm',),q,('r6fh','r6fl'));v=model(d)
    v['r6fl']=lambda *a:a[:4]==('a','b','c','b') and a[4] in ('a','b') and a[5:7]==('reference','anchor') and a[-1] in ('background','secondbackground')
    assert run(d,v)==[True];cases={}
    for variant in ('no_current_army','empty_threats','empty_backgrounds','second_threat_no_background','second_threat_fails','second_background_fails','irrelevant_comparison_fails'):
        w=dict(v);want=variant=='irrelevant_comparison_fails'
        if variant=='no_current_army':w['r6fh']=lambda *a:content(lambda t:t!='anchor')
        if variant=='empty_threats':w['h26vp']=lambda *a:False
        if variant=='empty_backgrounds':w['h26vq']=lambda *a:False
        if variant=='second_threat_no_background':w['h26vq']=lambda c,th,r,a,b:th=='a' and v['h26vq'](c,th,r,a,b)
        if variant=='second_threat_fails':w['r6fl']=lambda *a:a[4]=='a'
        if variant=='second_background_fails':w['r6fl']=lambda *a:a[-1]=='background'
        if variant=='irrelevant_comparison_fails':w['r6fl']=lambda *a:a[4]!='c' and a[-1] in ('background','secondbackground')
        assert run(d,w)==[want],variant;cases[variant]=want
    for n in ('h26vp','h26vq','r6fl','r6fh'):
        w=dict(v);w[n]=unknown;rejected(d,w)
    for n in FRAME+('reference','anchor'):
        w=dict(v);w['z'+n]=lambda n=n:'secondbackground' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a')
        assert run(d,w)==[False],n
    # Integrate actual quantifiers, causal comparison and peace with two threats
    # and two backgrounds; only the already-checked army body is bounded.
    integrated=fixture(('r6fm',),q,('r6fh',));assert run(integrated,model(integrated))==[True]
    return dict(cases=cases,all_fixed_frame_slots_checked=True,nonempty_all_threats_and_backgrounds=True,
      native_integration_with_two_threats_two_backgrounds=True,boundary='r6fl for scope contrasts only; one full native causal/peace integration keeps only r6fh bounded.',unknown_rejected=True)

@lru_cache(None)
def witness_checks():
    rows={};small=('a','b');expected=('a','b','b','a','reference')
    for root,fields,free in (('r6fn',('chief','group','community','reference'),(1,)),('r6fo',('chief','community','reference'),(1,2))):
        d=fixture((root,),'q[t[k '+root+'['+args(fields)+']]['+z('anchor')+']].',('r6fm',));v=model(d)
        v.update(zchief=lambda:'a',zgroup=lambda:'b',zcommunity=lambda:'a')
        v['r6fm']=lambda *a:content(lambda t:t=='anchor' and a==expected)
        assert run(d,v,small)==[True]
        for i in range(5):
            other=list(expected);other[i]='background' if i==4 else ('b' if other[i]=='a' else 'a')
            w=dict(v);w['r6fm']=lambda *a,other=tuple(other):content(lambda t:t=='anchor' and a==other)
            assert run(d,w,small)==[i in free],(root,i)
        w=dict(v);w['r6fm']=lambda *a:content(lambda t:False);assert run(d,w,small)==[False]
        rows[root]=dict(existential_slots=list(free),all_fixed_slots_checked=True)
    return dict(cases=rows,domain_size=2,boundary='r6fm only; its native scope/causal/peace composition is tested separately.')

@lru_cache(None)
def person_checks():
    direct='k r6fp['+args(('topic','community','reference'))+']'
    constructed='k r6fq['+' '.join('r['+z(n)+']' for n in ('topic','community','reference'))+']'
    q=''.join('q[t[c['+f+']['+z('person')+']]['+z('anchor')+']].' for f in (direct,'s['+constructed+']'))
    d=fixture(('r6fp','r6fq'),q,('r6ez','r6fo'));rows={}
    def values(mental=True,military=True):
        v=model(d)
        v['r6ez']=lambda t,r:FunctionValue(('individual',),'content',lambda p:content(lambda point:mental and(t,r,p,point)==('c','reference','a','anchor')))
        v['r6fo']=lambda p,c,r:content(lambda point:military and(p,c,r,point)==('a','b','reference','anchor'))
        return v
    for a,b in product((False,True),repeat=2):
        assert run(d,values(a,b))==[a and b]*2;rows[str((a,b))]=a and b
    for n in ('topic','community','reference','person','anchor'):
        w=values();w['z'+n]=lambda n=n:'background' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a')
        assert run(d,w)==[False,False],n
    for variant in ('other_person','other_reference','other_point'):
        w=values();target={'other_person':('b','b','reference','anchor'),'other_reference':('a','b','background','anchor'),'other_point':('a','b','reference','background')}[variant]
        w['r6fo']=lambda p,c,r:content(lambda point:(p,c,r,point)==target)
        assert run(d,w)==[False,False],variant
    for n in ('r6ez','r6fo'):
        w=values();w[n]=unknown;rejected(d,w)
    literal='r h[c[p r6fp]['+args(('topic','community','reference'))+']]'
    quoted=fixture(('r6fq',),'q[e['+constructed+']['+literal+']].')
    assert run(quoted,{r['name']:unknown for r in quoted['declarations'] if r['kind']=='primitive'})==[True]
    return dict(combinations=rows,same_person_point_and_reference=True,exact_three_name_quote=True,quotation_does_not_execute=True,
      boundaries='r6ez and r6fo for conjunction. Prior native mental-condition report is pinned; military guarantee body and witnesses checked above.',unknown_rejected=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='zum Bürgen der öffentlichen Ruhe';a=u['text'].index(phrase)
    return dict(status='same_army_public_peace_guarantee_and_complete_person_profile_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for source in parents():
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:0 if n=='r6fk' else 1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_bodies_and_meanings_unchanged=True,minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('causal',causal_checks),('content_binding',content_binding_checks),('scope',scope_checks),('witnesses',witness_checks),('person',person_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_military_peace_guarantee.py','scripts/check_military_peace_guarantee.py','tests/test_military_peace_guarantee.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_qualified_prince_frame.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_army_public_peace_guarantee_and_person_profile_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
