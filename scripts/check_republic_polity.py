"""Check public polity, actual office holders and collective highest authority."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.constructed_discourse import sequence_sort
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_republic_polity import ROOT,LIBRARY,BASIS,OLD,OLD_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/republic-polity-v1.md';READING='data/republic-polity-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';LEXICAL='data/republic-reading-review-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/collective-office-v1.json','reports/civic-compatibility-v1.json','reports/single-ruler-v1.json')
DOMAIN=('a','b','c');SCENES=('reference','now','other')
CONSTANTS=dict(community='c',office='a',order='b',person='b',reference='reference',point='now')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    return parse(format_graph(d,'compact')+''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())+query)

def model(d,variant='baseline',table=8):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    people=('a',) if variant=='single_holder' else ('a','b')
    listed={'missing_holder':('a',),'extra_holder':('a','b','c'),'duplicate_holder':('a','b','a'),'empty_holders':(),
            'reverse_order':('b','a')}.get(variant,people)
    def decision(votes):return len(votes.items)==len(people) and bool(table&(1<<sum(int(b)<<i for i,b in enumerate(votes.items))))
    def roles(r,c,t):return (c,t)==('c','now') and (r in ('a','b') or variant=='uncovered_superior' and r=='c')
    def above(a,b,c,t):
        return (c,t)==('c','now') and ((a,b)==('a','b') and variant!='incomparable' or variant=='cycle' and (a,b)==('b','a') or variant=='reflexive' and a==b=='a')
    v.update(aa=lambda p:p in people or variant=='human_polity' and p=='c',
      h237c=lambda p,c,r:p in people and (c,r)==('c','reference') and variant!='empty_population',
      h257d=lambda c,r:(c,r)==('c','reference') and variant!='private_body',
      h26hb=lambda o,c,r:(o,c,r)==('b','c','reference') and variant!='private_order',
      h26hc=lambda o,item,r:(o,item,r)==('b','c','reference') and variant!='empty_conditions',
      h26vy=lambda o,c,r,t:(o,c,r,t)==('b','c','reference','now') and variant!='unoperated_order',
      h234d=roles,h234e=above,
      hzwn=lambda p,role,t:p in people and (role,t)==('a','now') and variant!='empty_holders',
      hzxf=lambda p,role,c,t:p in people and (role,c,t)==('a','c','now') and not(variant=='missing_appointment' and p=='b'),
      cf=lambda p,role,t:p in people and (role,t)==('a','now') and not(variant=='missing_commission' and p=='b'),
      h26vz=lambda c,o,r,t:SequenceValue(listed if(c,o,r,t)==('c','a','reference','now') else (),'"individual"'),
      h26v2=lambda *a:FunctionValue((sequence_sort('truth'),),'truth',decision),
      ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda b:Fraction(int(b)))
    if variant=='nonhuman_holder':v['aa']=lambda p:p=='a'
    return v
def run(d,v,people=DOMAIN):return evaluate(d,v,people,SCENES,True)
def rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def civic_checks():
    fields=('community','order','reference','point');d=fixture(('r6fr',),'q[k r6fr['+args(fields)+']].');v=model(d);assert run(d,v)==[True];cases={}
    for variant in ('human_polity','empty_population','private_body','private_order','empty_conditions','unoperated_order'):
        assert run(d,model(d,variant))==[False],variant;cases[variant]=False
    for name in fields:
        w=dict(v);w['z'+name]=lambda name=name:'other' if name in ('reference','point') else ('a' if CONSTANTS[name]!='a' else 'b')
        assert run(d,w)==[False],name
    for n in ('aa','h237c','h257d','h26hb','h26hc','h26vy'):
        w=dict(v);w[n]=unknown;rejected(d,w)
    # The actual condition contents and episodes of disturbance are not evaluated
    # when recognizing that the public legal framework is in operation.
    assert not {'h246e','dg','h26qp'}&{r['name'] for r in d['declarations']}
    return dict(cases=cases,all_four_context_slots_checked=True,framework_operation_not_perfect_compliance=True,unknown_rejected=True)

@lru_cache(None)
def office_checks():
    fields=('community','office','reference','point');d=fixture(('r6fs',),'q[k r6fs['+args(fields)+']].');assert run(d,model(d))==[True];cases={}
    for variant in ('single_holder','missing_holder','extra_holder','duplicate_holder','empty_holders','nonhuman_holder',
                    'incomparable','cycle','reflexive','uncovered_superior','missing_appointment','missing_commission','reverse_order'):
        want=variant=='reverse_order';got=run(d,model(d,variant));assert got==[want],(variant,got);cases[variant]=want
    rows=[]
    for table in range(16):
        pivotal=[any(bool(table&(1<<row))!=bool(table&(1<<(row^(1<<i)))) for row in range(4)) for i in range(2)]
        got=run(d,model(d,table=table));assert got==[all(pivotal)],(table,got,pivotal)
        rows.append(dict(table=table,influence=pivotal,shared=all(pivotal)))
    for n in ('h234d','h234e','hzwn','hzxf','cf','h26vz','h26v2'):
        w=model(d);w[n]=unknown;rejected(d,w)
    # Reordering positions must also reorder an asymmetric rule. A first-only
    # rule cannot qualify even with two entries in the complete holder census.
    assert not next(r['shared'] for r in rows if r['table']==10)
    for name in fields:
        w=model(d);w['z'+name]=lambda name=name:'other' if name in ('reference','point') else ('a' if CONSTANTS[name]!='a' else 'b')
        assert run(d,w)==[False],name
    return dict(cases=cases,all_two_holder_decision_tables=rows,all_four_context_slots_checked=True,
      actual_holders_not_filtered_by_appointment=True,native='r6fs/rwp/rwo/rwn/rwm/rcm/rex/r2ui; complete holder census, official rule and each appointment/commission.',unknown_rejected=True)

@lru_cache(None)
def provider_checks():
    fields=('community','office','reference','point');d=fixture(('r6fs',),'q[k r6fs['+args(fields)+']].',('rwp',));v=model(d);calls=[]
    for n in ('h26vz','h26v2'):
        f=v[n]
        def record(*a,n=n,f=f):calls.append((n,a));return f(*a)
        v[n]=record
    def boundary(office,community,point,roles,above,participants,holders,persons,rule):
        return (office,community,point)==('a','c','now') and roles('a','c','now') and not roles('a','a','now') and above('a','b','c','now') and not above('b','a','c','now') and participants.items==('a','b') and all(holders(p,'a','c','now') and persons(p) for p in ('a','b')) and not holders('c','a','c','now') and not holders('a','a','a','now') and not holders('a','b','c','now') and rule(SequenceValue((True,True),'"truth"')) and not rule(SequenceValue((True,False),'"truth"'))
    v['rwp']=boundary;assert run(d,v)==[True];assert len(calls)==2 and all(a==('c','a','reference','now') for _,a in calls)
    for name in fields:
        calls.clear();w=dict(v);new=dict(CONSTANTS);new[name]='other' if name in ('reference','point') else ('a' if new[name]!='a' else 'b')
        w['z'+name]=lambda name=name,new=new:new[name];w['rwp']=lambda *a:True
        run(d,w);assert len(calls)==2 and all(a==tuple(new[n] for n in fields) for _,a in calls),(name,calls)
    return dict(all_provider_slots_and_arities_recorded=True,structured_role_order_holder_census_and_rule_arguments_checked=True,
      boundary='rwp only for adapter recording; its full body runs in office_checks.')

@lru_cache(None)
def connection_checks():
    d=fixture(('r6fu',),'q[t[k r6fu['+args(('community','reference'))+']]['+z('point')+']].');assert run(d,model(d))==[True];cases={}
    for variant in ('private_body','unoperated_order','single_holder','missing_appointment','uncovered_superior'):
        assert run(d,model(d,variant))==[False],variant;cases[variant]=False
    # Two values for exact witness positions; native civic and collective bodies
    # are exercised above without multiplying deep bodies into a large domain.
    b=fixture(('r6fu',),'q[t[k r6fu['+args(('community','reference'))+']]['+z('point')+']].',('r6ft',));v=model(b)
    v['zcommunity']=lambda:'a';expected=('a','b','a','reference')
    v['r6ft']=lambda *a:Content(SCENES,tuple(t=='now' and a==expected for t in SCENES));assert run(b,v,('a','b'))==[True]
    for i in range(4):
        other=list(expected);other[i]='other' if i==3 else ('b' if other[i]=='a' else 'a')
        w=dict(v);w['r6ft']=lambda *a,other=tuple(other):Content(SCENES,tuple(t=='now' and a==other for t in SCENES))
        assert run(b,w,('a','b'))==[i in (1,2)],i
    w=dict(v);w['r6ft']=lambda *a:Content(SCENES,(False,False,False));assert run(b,w,('a','b'))==[False]
    w=dict(v);w['zpoint']=lambda:'other';assert run(b,w,('a','b'))==[False]
    return dict(cases=cases,native_polity_and_highest_office_integration=True,same_community_order_office_reference_point=True,
      witness_domain_size=2,all_witness_slots_checked=True,boundary='r6ft only for the separate witness binding check.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='ein Freistaat';a=u['text'].index(phrase)
    return dict(status='civic_republic_with_shared_highest_office_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,LEXICAL,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];ds,means=legacy()
    for d in ds:assert c.entries[d['name']]['declaration']==d
    for n,m in means.items():assert c.entries[n]['meaning_ja']==m
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    for row in read(LEXICAL)['sources']:assert digest((ROOT/row['artifact']).read_bytes())==row['artifact_sha256']
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for n in MEANINGS:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),legacy_and_current_bodies_and_meanings_preserved=True,
      primary_lexical_transcription_hashes_checked=True,facsimile_checked=False,minimum_quote_ranks={n:0 for n in MEANINGS},roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('civic',civic_checks),('office',office_checks),('providers',provider_checks),('connection',connection_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,LEXICAL,INVENTORY,INDEX,OLD,OLD_BASIS,*PRIORS,
      'scripts/compose_republic_polity.py','scripts/check_republic_polity.py','tests/test_republic_polity.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    paths.update(row['artifact'] for row in read(LEXICAL)['sources'])
    return dict(status='public_civic_polity_and_shared_highest_office_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
