"""Check same-role, same-plan military availability with bounded diagnostics."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_disciplined_availability import ROOT,LIBRARY,BASIS,OLD,OLD_BASES,MEANINGS,PRIMITIVES,LIMITS,DESCRIPTION,parent,legacy,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/disciplined-availability-v1.md';READING='data/disciplined-availability-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/numerous-armed-formation-v1.json','reports/commanded-protection-v1.json','reports/joint-readiness-v1.json')
DOMAIN=('a','b');SCENES=('reference','anchor','done','failed')
CONSTANTS=dict(chief='a',institution='b',group='b',community='a',person='a',plan='b',role='a',
               reference='reference',anchor='anchor',done='done',failed='failed')
FRAME=('chief','institution','group','community')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def mission(c):return c.rank==0 and json.loads(c.syntax)==dict(kind='function_ref',symbol='hzzmission')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(root,query,restricted=True,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,root if isinstance(root,tuple) else (root,))
    # Real, closed syntax objects; a native selector returns one of these quotes.
    extra='r zacta[a a d] c.r zactb[a a d] c.r zchoose[a '+DESCRIPTION+' '+DESCRIPTION+'] '+DESCRIPTION+'.'
    extra+='d za[person a activity a] e[b point[k zacta[v person v activity v point]]].'
    extra+='d zb[person a activity a] e[b point[k zactb[v person v activity v point]]].'
    blank=deepcopy(d);blank['declarations']=[]
    prefix=parse('p:'+extra)['declarations']
    for index,row in enumerate(d['declarations']):
        if row['name']=='h26vm':
            fields='institution a community a reference d chief a group a person a plan a item a anchor d'
            replacement='d h26vm['+fields+'] '+DESCRIPTION+'[k zchoose[v item r[p za] r[p zb]]].'
            d['declarations'][index]=parse(format_graph(dict(blank,declarations=prefix),'compact')+replacement)['declarations'][-1]
        if restricted and row['name']=='rtx':
            node=row['body']['body']['body'];assert node['kind']=='forall' and node['sort']['kind']=='description'
            instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
                arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=n))]) for n in ('za','zb')]
            node.clear();node.update(kind='and',arguments=instances)
    d['declarations']=prefix+d['declarations']
    constants=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+constants+query)

def model(d,variant='baseline'):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    def frame(i,c,r,chief,g,plan,t):return (i,c,r,chief,g,t)==('b','a','reference','a','b','anchor') and plan in DOMAIN
    def item(i,c,r,chief,g,p,plan,it,t):
        return frame(i,c,r,chief,g,plan,t) and p in DOMAIN and it in DOMAIN and variant!='empty_commands' and not(variant=='missing_record' and it=='b')
    def plans(i,c,r,chief,g,plan,t):return frame(i,c,r,chief,g,plan,t) and variant!='no_plans'
    def selected(i,c,r,chief,g,plan,t,end):
        return frame(i,c,r,chief,g,plan,t) and variant!='empty_results' and end in (('done','failed') if variant=='second_result_failed' else ('done',))
    def orders(i,c,r,chief,g,plan,p,role,activity,code,sign,t):
        expected=['b','a','reference','a','b',plan,p,'a',activity,t]
        slots={'wrong_institution':0,'wrong_community':1,'wrong_reference':2,'wrong_source':3,'wrong_group':4,'wrong_plan':5,'wrong_person':6,'wrong_role':7,'wrong_activity':8,'wrong_anchor':9}
        if variant in slots:
            slot=slots[variant];expected[slot]='done' if slot in (2,9) else ('b' if expected[slot]=='a' else 'a')
        if (i,c,r,chief,g,plan,p,role,activity,t)!=tuple(expected):return False
        if p not in DOMAIN or activity not in DOMAIN or variant=='empty_commands':return False
        name=json.loads(code.syntax).get('symbol')
        if variant=='contradictory':return activity=='a' and name=='za'
        if variant=='unlisted_description' and activity=='a' and name=='zb':return sign
        return name==('za' if activity=='a' else 'zb') and sign==(variant not in ('negative','wrong_polarity'))
    def performed(kind,p,activity,t):
        ok=t=='done' and activity==kind and not(variant=='member_failed' and p=='b')
        return not ok if variant=='negative' else ok
    v.update(h26vg=plans,h26vh=lambda *a:frame(*a[:-1]) and a[-1] in (('done','failed') if variant=='second_result_failed' else ('done',)) and variant!='result_outside',h26vi=selected,
      h26vj=item,h26vk=lambda *a:'b' if variant=='unrelated_role' else 'a',
      h26vl=lambda *a:'a' if variant=='contradictory' else a[-2],
      h26vn=lambda *a:a[-2]=='a' if variant=='contradictory' else variant!='negative',h26vo=orders,
      zchoose=lambda it,a,b:a if it=='a' or variant=='contradictory' else b,
      zacta=lambda p,a,t:performed('a',p,a,t),zactb=lambda p,a,t:performed('b',p,a,t),
      hzyoffices=lambda role,i,g,t:(role,i,g,t)==('a','b','b','anchor'),
      hzyholders=lambda p,role,i,g,t:p in DOMAIN and (role,i,g,t)==('a','b','b','anchor') and not(variant=='missing_holder' and p=='b'),
      hzyresponsibilities=lambda role,i,g,c,m,t:(role,i,g,c,t)==('a','b','b','a','anchor') and mission(m) and variant!='different_mission',
      hzzmembers=lambda g,p,t:(g,t)==('b','anchor') and p in DOMAIN,
      h26vf=lambda g,r,t:SequenceValue(('a',) if variant=='missing_member' else ('a','a') if variant=='duplicate_member' else DOMAIN,'"individual"'),
      r6fb=lambda *a:Content(SCENES,tuple(t=='anchor' and a==('a','b','b','a','reference') and variant!='no_army' for t in SCENES)),
      ha=lambda a,b:a+b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)))
    if variant=='second_plan_failed':
        # The second plan asks for the opposite sign; records agree with its
        # requirements but the same actual result does not fulfil that plan.
        original=v['h26vo'];v['h26vn']=lambda *a:a[6]!='b'
        v['h26vo']=lambda *a:original(*a[:-2],not a[-2] if a[5]=='b' else a[-2],a[-1])
    return v

def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejected(d,v,part='Unknown'):
    try:run(d,v)
    except ValueError as e:assert part in str(e),str(e)
    else:raise AssertionError('Unsupported input accepted')

@lru_cache(None)
def roles_checks():
    q='q[k r6fg['+args(FRAME+('person','plan','reference','anchor'))+']].'
    d=fixture('r6fg',q);v=model(d);assert run(d,v)==[True]
    cases={}
    for variant in ('empty_commands','unrelated_role','different_mission'):
        assert run(d,model(d,variant))==[False];cases[variant]=False
    for n in ('hzyoffices','hzyholders','hzyresponsibilities','h26vj','h26vk'):
        w=dict(v);w[n]=unknown;rejected(d,w)
    # Every role-binding slot is distinguished, including a second person/role.
    q='q[k r6fe['+args(('institution','group','community','person','role','anchor'))+']].'
    r=fixture('r6fe',q);v=model(r)
    v['hzyholders']=lambda p,role,i,g,t:(p,role,i,g,t)==('a','a','b','b','anchor')
    assert run(r,v)==[True]
    for n in ('institution','group','community','person','role','anchor'):
        w=dict(v);w['z'+n]=lambda n=n:'done' if n=='anchor' else ('b' if CONSTANTS[n]=='a' else 'a')
        assert run(r,w)==[False],n
    return dict(nonempty_records=True,scope_derived_from_actual_roles=True,all_six_role_slots_checked=True,cases=cases,unknown_rejected=True)

@lru_cache(None)
def commands_checks():
    q='q[t[k r6ff['+args(FRAME+('person','plan','reference','anchor'))+']]['+z('done')+']].'
    d=fixture('r6ff',q);assert run(d,model(d))==[True];cases={}
    for variant in ('wrong_institution','wrong_community','wrong_reference','wrong_source','wrong_group','wrong_plan',
                    'wrong_person','wrong_role','wrong_activity','wrong_anchor','missing_record','unlisted_description',
                    'wrong_polarity','contradictory','negative'):
        want=variant=='negative';got=run(d,model(d,variant));assert got==[want],(variant,got);cases[variant]=want
    call=args(FRAME+('person','plan','reference','anchor'))
    strict=fixture(('r6fg','r6ff'),'q[w[k r6fg['+call+']][t[k r6ff['+call+']]['+z('done')+']]].')
    for n in FRAME+('person','plan','reference','anchor'):
        w=model(strict);w['z'+n]=lambda n=n:'failed' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a')
        # Both members and both plans really exist in this fixture; the other
        # fixed bindings cannot be supplied from an unrelated frame.
        assert run(strict,w)==[n in ('person','plan')],n
    assert run(d,model(d,'empty_commands'))==[True]  # Preserved generic empty conformity.
    assert run(strict,model(strict,'empty_commands'))==[False]
    for n in ('h26vo','zacta'):
        w=model(d);w[n]=unknown;rejected(d,w)
    full=fixture('r6ff',q,False);rejected(full,model(full),'description domain')
    quoted=fixture('r6ff','q[e[r b[p r6ff]][r b[p r6ff]]].',False)
    assert run(quoted,{r['name']:unknown for r in quoted['declarations'] if r['kind']=='primitive'})==[True]
    return dict(cases=cases,all_fixed_frame_slots_checked=True,closed_code_identity_preserved=True,
      original_all_description_domain_retained=True,full_description_domain_refused=True,full_description_domain_verified=False,
      diagnostics=['za','zb'],quotation_does_not_execute=True,unknown_rejected=True)

@lru_cache(None)
def availability_checks():
    q='q[t[k r6fh['+args(FRAME+('reference',))+']]['+z('anchor')+']].'
    d=fixture('r6fh',q,True,('r6fb',));assert run(d,model(d))==[True];cases={}
    for variant in ('no_army','no_plans','empty_results','result_outside','second_result_failed','member_failed',
                    'second_plan_failed','missing_member','duplicate_member','missing_holder','empty_commands','unrelated_role','negative'):
        want=variant=='negative';got=run(d,model(d,variant));assert got==[want],(variant,got);cases[variant]=want
    for n in ('h26vg','h26vh','h26vi','h26vf','hzzmembers','r6fb'):
        w=model(d);w[n]=unknown;rejected(d,w)
    # A different fixed frame cannot borrow commands, army or availability.
    for n in FRAME+('reference','anchor'):
        w=model(d);w['z'+n]=lambda n=n:'failed' if n in ('reference','anchor') else ('b' if CONSTANTS[n]=='a' else 'a')
        assert run(d,w)==[False],n
    return dict(cases=cases,two_members_two_plans_two_descriptions=True,all_fixed_slots_checked=True,
      native='r6fh, r6fg/r6fe, rvf/rty/rtw/rpm/rpl, rut/ruq and rcm. Only the rtx description binder is instantiated to za/zb.',
      boundary='r6fb only: military identity, assignment, armed readiness and numerosity were checked natively in the pinned numerous-armed-formation report.',unknown_rejected=True)

@lru_cache(None)
def witness_checks():
    expected=('a','b','b','a','reference');cases={}
    for root,fields,free in (('r6fi',('chief','group','community','reference'),(1,)),('r6fj',('chief','community','reference'),(1,2))):
        d=fixture(root,'q[t[k '+root+'['+args(fields)+']]['+z('anchor')+']].',True,('r6fh',))
        v=model(d);v['r6fh']=lambda *a:Content(SCENES,tuple(t=='anchor' and a==expected for t in SCENES))
        assert run(d,v)==[True]
        for i in range(5):
            other=list(expected);other[i]='failed' if i==4 else ('b' if other[i]=='a' else 'a')
            w=dict(v);w['r6fh']=lambda *a,other=tuple(other):Content(SCENES,tuple(t=='anchor' and a==other for t in SCENES))
            assert run(d,w)==[i in free],(root,i)
        w=dict(v);w['r6fh']=lambda *a:Content(SCENES,(False,)*len(SCENES));assert run(d,w)==[False]
        cases[root]=dict(existential_slots=list(free),all_fixed_slots_checked=True,empty_witness_rejected=True)
    return dict(cases=cases,domain_size=2,boundary='r6fh for witness binding only; actual body tested separately.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');segments=[]
    for phrase in ('wohldisciplinirtes','zur Hand hat'):
        a=u['text'].index(phrase);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='disciplined_current_availability_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements'];ds,means,_=legacy()
    for d in ds:assert c.entries[d['name']]['declaration']==d
    for n,m in means.items():assert c.entries[n]['meaning_ja']==m
    for n,e in parent().entries.items():assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={n:0 if n in ('r6fe','r6fg') else 1 for n in MEANINGS};t=format_graph(c.document,'compact')
    for n,rank in ranks.items():
        quote='r'+(' b' if rank else '')+'[p '+n+']';parse(t+'q[e['+quote+']['+quote+']].')
        if rank:
            try:parse(t+'q[e[r[p '+n+']][r[p '+n+']]].')
            except ValueError:pass
            else:raise AssertionError('Rank understated: '+n)
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_bodies_and_meanings_unchanged=True,
      minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in (('roles',roles_checks),('commands',commands_checks),('availability',availability_checks),('witnesses',witness_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,OLD,*OLD_BASES,*PRIORS,
      'scripts/compose_disciplined_availability.py','scripts/check_disciplined_availability.py','tests/test_disciplined_availability.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_described_norms.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='disciplined_present_army_availability_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
