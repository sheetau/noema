"""Check a staffed military formation, real readiness and exact numerosity."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_numerous_armed_formation import ROOT,LIBRARY,BASIS,OLD,OLD_BASES,MEANINGS,PRIMITIVES,LEGACY,LIMITS,parent,legacy,build,closure
from scripts import check_armed_readiness as armed
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/numerous-armed-formation-v1.md';READING='data/numerous-armed-formation-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
INDEX='data/semantic-review-index-v203.json';PRIORS=('reports/armed-readiness-v1.json','reports/assigned-formation-v1.json','reports/joint-readiness-v1.json')
DOMAIN=armed.DOMAIN;SCENES=(*armed.SCENES,'reference')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def mission(c):return c.rank==0 and json.loads(c.syntax)==dict(kind='function_ref',symbol='hzzmission')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d,assigned=True,ready=True):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    a=armed.interpretation((True,ready,True,True,True,True,True))
    v.update({'hzz'+n:a['jq'+n] for n,_ in armed.RELATIONS})
    old=v['hzzmembers'];v['hzzmembers']=lambda g,p,t:old(g,p,t) or(g,p,t)==('group','other','anchor')
    v.update(aa=lambda p:p in ('chief','operator','other','target'),h233d=lambda g,t:(g,t)==('group','anchor'),
      hzyconstituted=lambda i,g,t:(i,g,t)==('institution','group','anchor'),
      hzyassigned=lambda i,g,c,m,t:assigned and(i,g,c,t)==('institution','group','community','anchor') and mission(m),
      hzyoffices=lambda r,i,g,t:r in ('memberrole','commandrole') and(i,g,t)==('institution','group','anchor'),
      hzyholders=lambda p,r,i,g,t:(p,r) in (('operator','memberrole'),('other','memberrole'),('chief','commandrole')) and(i,g,t)==('institution','group','anchor'),
      hzyresponsibilities=lambda r,i,g,c,m,t:r in ('memberrole','commandrole') and(i,g,c,t)==('institution','group','community','anchor') and mission(m),
      hzydirects=lambda r,i,g,t:(r,i,g,t)==('commandrole','institution','group','anchor'),
      h26ve=lambda g,c,r:Fraction(2) if(g,c,r)==('group','community','reference') else Fraction(100),
      h26vf=lambda g,r,t:SequenceValue(('operator','other') if(g,r,t)==('group','reference','anchor') else (),'"individual"'),
      ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)))
    return v

FRAME=('chief','institution','group','community')
@lru_cache(None)
def formation_checks():
    d=fixture(('r6e6',),'q[k r6e6['+args(FRAME+('anchor',))+']].');v=model(d);assert run(d,v)==[True];cases={}
    for n in ('hzyconstituted','hzyassigned','hzyoffices','hzyholders','hzyresponsibilities','hzydirects','h233d'):
        w=dict(v);w[n]=lambda *a:False;assert run(d,w)==[False];cases[n]=False
        w[n]=unknown;rejects(d,w)
    for variant in ('nonhuman_member','nonhuman_commander','missing_member_role','other_institution_command','different_mission','empty_members','unrelated_role_responsibility'):
        w=dict(v)
        if variant=='nonhuman_member':w['aa']=lambda p:p in ('chief','operator','target')
        if variant=='nonhuman_commander':w['aa']=lambda p:p in ('operator','other','target')
        if variant=='missing_member_role':w['hzyholders']=lambda p,r,i,g,t:p!='other' and v['hzyholders'](p,r,i,g,t)
        if variant=='other_institution_command':w['hzydirects']=lambda r,i,g,t:(r,i,g,t)==('commandrole','other','group','anchor')
        if variant=='different_mission':w['hzyassigned']=lambda i,g,c,m,t:json.loads(m.syntax)==dict(kind='function_ref',symbol='rwf')
        if variant=='empty_members':w['hzzmembers']=lambda *a:False
        if variant=='unrelated_role_responsibility':w['hzyresponsibilities']=lambda r,*a:r=='other'
        assert run(d,w)==[False],variant;cases[variant]=False
    # A commander can be outside the troop membership; no present operation is needed.
    assert not v['hzzmembers']('group','chief','anchor') and not v['hzzoccurs']('event','anchor')
    return dict(cases=cases,native_rwb_all_member_roles_and_command=True,commander_need_not_be_troop_member=True,
      mission_quote_not_executed_by_assignment=True,military_identity_separate_from_armed_success=True,unknown_rejected=True)

@lru_cache(None)
def readiness_checks():
    q='q[k r6e7['+args(FRAME+('anchor',))+']].'
    d=fixture(('r6e7',),q);rows={}
    for assigned,ready in ((True,True),(False,True),(True,False)):
        got=run(d,model(d,assigned,ready));assert got==[assigned and ready];rows[str((assigned,ready))]=got
    v=model(d);v['h233d']=lambda *a:False;assert run(d,v)==[False]
    v=model(d);v['hzzunitselected']=lambda *a:False;assert run(d,v)==[False]
    v=model(d);v['hzzunitmethods']=unknown;rejects(d,v)
    return dict(cases=rows,no_current_combat_required=True,assignment_not_readiness=True,
      armed_police_not_accepted_by_military_classification=True,empty_selected_outcomes_rejected=True,
      native='r6e7, r6e6, rwb, hzzmission, rwf/rwe/rwd/rwc and xa/xd execute with two current troop members. Prior detailed method/tool/target contrasts are pinned, not repeated.')

@lru_cache(None)
def count_checks():
    d=fixture(('r6fa',),'q[t[k r6fa['+args(('group','community','reference'))+']]['+z('anchor')+']].')
    v=model(d);assert run(d,v)==[True];rows={}
    for variant in ('too_few','duplicate','missing','extra','empty','wrong_group','wrong_point','wrong_reference','reordered','threshold_one','threshold_zero','threshold_negative','greater_threshold'):
        w=dict(v);want=variant=='reordered'
        lists={'too_few':('operator',),'duplicate':('operator','other','other'),'missing':('operator',),'extra':('operator','other','chief'),'empty':(),'reordered':('other','operator')}
        if variant in lists:w['h26vf']=lambda *a:SequenceValue(lists[variant],'"individual"')
        if variant=='too_few':w['hzzmembers']=lambda g,p,t:(g,p,t)==('group','operator','anchor')
        if variant=='empty':w['hzzmembers']=lambda *a:False
        if variant in ('wrong_group','wrong_point','wrong_reference'):
            slot={'wrong_group':'zgroup','wrong_point':'zanchor','wrong_reference':'zreference'}[variant]
            w[slot]=lambda:'other' if variant=='wrong_group' else 'safe'
        if variant in ('threshold_one','threshold_zero','threshold_negative','greater_threshold'):
            w['h26ve']=lambda *a:Fraction({'threshold_one':1,'threshold_zero':0,'threshold_negative':-1,'greater_threshold':3}[variant])
        got=run(d,w);assert got==[want],(variant,got);rows[variant]=got[0]
    for n in ('h26ve','h26vf','hzzmembers'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,exact_nonempty_duplicate_free_membership=True,fixed_contextual_threshold=True,unknown_rejected=True)

@lru_cache(None)
def connection_checks():
    # Two values distinguish all witness slots without multiplying the deep body.
    d=fixture(('r6fc',),'q[t[k r6fc['+args(('chief','group','community','reference'))+']]['+z('anchor')+']].',('r6fb',))
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:('b' if n=='group' else 'a') if n in DOMAIN else('anchor' if n=='anchor' else'reference') for n in (*DOMAIN,*SCENES)})
    states=('reference','anchor');expected=('a','b','b','a','reference')
    def value(*a):return Content(states,(False,tuple(a)==expected))
    v['r6fb']=value
    assert run(d,v,('a','b'),states)==[True]
    for i in range(5):
        w=dict(v);other=list(expected);other[i]='anchor' if i==4 else('b' if expected[i]=='a' else'a')
        w['r6fb']=lambda *a,other=tuple(other):Content(states,(False,tuple(a)==other))
        # Changing only the existential institution is permitted; changing a fixed slot is not.
        assert run(d,w,('a','b'),states)==[i==1],i
    g=fixture(('r6fd',),'q[t[k r6fd['+args(('chief','community','reference'))+']]['+z('anchor')+']].',('r6fb',))
    assert run(g,v,('a','b'),states)==[True]
    w=dict(v);w['r6fb']=lambda *a:Content(states,(False,False));assert run(g,w,('a','b'),states)==[False]
    # Check the real conjunction separately with native numerosity and a bounded formation body.
    c=fixture(('r6fb',),'q[t[k r6fb['+args(FRAME+('reference',))+']]['+z('anchor')+']].',('r6e7',));m=model(c)
    for military,numerous in product((False,True),repeat=2):
        w=dict(m);w['r6e7']=lambda *a:military and a==tuple(FRAME)+('anchor',)
        w['h26ve']=lambda *a:Fraction(2 if numerous else 3)
        assert run(c,w)==[military and numerous]
    return dict(two_value_witness_domain=True,all_fixed_argument_slots_checked=True,same_institution_witness=True,
      same_group_conjunction_native_count=True,boundary='r6fb only for witness tests; r6e7 only for conjunction. Their actual bodies are tested separately above.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');phrase='zahlreiches Heer';a=u['text'].index(phrase)
    return dict(status='same_numerous_armed_formation_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();ds,meanings,_=legacy();assert not c.document['statements']
    for d in ds:
        assert c.entries[d['name']]['declaration']==d
        if d['kind']=='definition':assert c.entries[d['name']]['meaning_ja']==meanings[d['name']]
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact')
    for n in MEANINGS:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),legacy_input_declarations_retained=len(LEGACY),
      inherited_bodies_and_meanings_unchanged=True,minimum_quote_ranks={n:0 for n in MEANINGS},roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('formation',formation_checks),('readiness',readiness_checks),('count',count_checks),('connection',connection_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,*OLD_BASES,*PRIORS,
      'scripts/compose_numerous_armed_formation.py','scripts/check_numerous_armed_formation.py','tests/test_numerous_armed_formation.py',
      'scripts/compose_assigned_formation.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
      'scripts/check_armed_readiness.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_numerous_armed_formation_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
