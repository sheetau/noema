"""Check shared quoted policy, representation, ability and necessary conditions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_political_quoted_speech import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/political-quoted-speech-v1.md';READING='data/political-quoted-speech-reading-v1.json'
SOURCE='data/tenth-paragraph-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v203.json'
PRIORS=('reports/free-choice-obedience-v1.json','reports/single-ruler-v1.json','reports/military-peace-guarantee-v1.json','reports/civic-peace-concord-v1.json')
DOMAIN=('a','b','c');SCENES=('reference','start','done','failed')
CONSTANTS=dict(performer='a',principal='c',call='b',community='c',topic='a',reference='reference',start='start',point='done',other='failed')
REF='r[k zreference[]]'
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def code(c):return c.rank,json.loads(c.syntax)
def refcode(n='reference'):return 0,dict(kind='call',symbol='z'+n,arguments=[])
def message(n):return 1,dict(kind='apply',function=dict(kind='function_ref',symbol=n),arguments=[dict(kind='call',symbol='zreference',arguments=[])])
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),restricted=True):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    constants=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    constants+='r zrefpick[d i[d] i[d]] i[d].d h223h[point d] i[d][k zrefpick[v point r[k zreference[]] r[k zother[]]]].'
    prefix=parse('p:'+constants)['declarations'];names={r['name'] for r in prefix}
    d['declarations']=prefix+[r for r in d['declarations'] if r['name'] not in names]
    d['declarations']=closure(d,(*roots,*names))
    if restricted:
        for row in d['declarations']:
            if row['name']!='r6fv':continue
            def visit(node):
                if isinstance(node,dict):
                    if node.get('kind')=='forall' and isinstance(node.get('sort'),dict) and node['sort'].get('kind')=='description':
                        instances=[]
                        for n in ('r2ug','r2uh'):
                            instances.append(dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
                              arguments=[dict(kind='quote',rank=1,body=message(n)[1])]))
                        node.clear();node.update(kind='and',arguments=instances);return 1
                    return sum(visit(v) for v in list(node.values()))
                if isinstance(node,list):return sum(visit(v) for v in node)
                return 0
            assert visit(row['body'])==1
    return parse(format_graph(d,'compact')+query)

def model(d,variant='baseline'):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    principal='a' if variant=='personal' else 'c'
    if variant=='personal':v['zprincipal']=lambda:'a'
    def audience(p,r,a):return (p,r)==(principal,'reference') and a in (('a',) if variant=='single_recipient' else ('a','b'))
    def presents(call,recipient,source,m,t):
        names=('r2ug',) if variant=='missing_command' else ('r2uh',) if variant=='missing_permission' else ('r2ug','r2uh')
        return (call,source,t)==('b','a' if variant=='other_source' else principal,'done') and recipient in ('a','b') and code(m) in tuple(message(n) for n in names)
    def reserve(call,performer,recipient,source,first,second,t):
        if variant=='missing_reservation':return False
        a,b=('r2uh','r2ug') if variant=='reversed' else ('r2ug','r2uh')
        return (call,performer,source,t)==('b','a',principal,'done') and recipient in ('a','b') and code(first)==message(a) and (code(second)==message(b) or variant=='extra_reservation' and code(second)==message('r2ug'))
    def available(p,c,r,m,start):return (p,c,r,start)==(principal,'c','reference','start') and m in ('a','b') and variant!='no_method'
    def selected(p,c,r,m,start,end):
        return (p,c,r,start)==(principal,'c','reference','start') and m in ('a','b') and variant!='empty_results' and end in (
          ('done','failed') if variant=='second_result_failed' or variant=='one_bad_method' and m=='a' else ('done',))
    v.update(aa=lambda p:p in (('a',) if variant=='nonhuman_recipient' else ('a','b')),
      dg=lambda call,t:(call,t)==('b','done') and variant!='unoccurred',
      f3=lambda p,call,t:(p,call,t)==('b' if variant=='other_performer' else 'a','b','done'),
      h233p=audience,h234g=presents,h234h=reserve,
      h26v3=lambda p,source,call,r,t:(p,source,call,r,t)==('a',principal,'b','reference','done') and variant!='no_mandate',
      h26v4=lambda call,source,r,t:(call,source,r,t)==('b',principal,'reference','done') and variant!='private_statement',
      h237c=lambda p,c,r:p in ('a','b') and (c,r)==('c','reference') and not(variant=='foreign_recipient' and p=='b'),
      r2ue=lambda p,r:content(lambda t:(p,r,t)==(principal,'reference','done') and variant!='permission_not_established'),
      r572=lambda c,r:content(lambda t:(c,r,t)==('c','reference','done') and variant!='peace_lost'),
      h26v5=available,h26v6=lambda p,c,r,m,s,e:(p,c,r,s)==(principal,'c','reference','start') and m in ('a','b') and e in (('failed',) if variant=='outside_results' else ('done','failed')),
      h26v7=selected,zrefpick=lambda r,a,b:a if r=='reference' else b)
    return v
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejected(d,v,part='Unknown'):
    try:run(d,v)
    except ValueError as e:assert part in str(e),str(e)
    else:raise AssertionError('Unsupported input accepted')

@lru_cache(None)
def speech_checks():
    q='q[k r6fw['+args(('performer','principal','call'))+' '+REF+' '+z('point')+']].'
    d=fixture(('r6fw',),q);assert run(d,model(d))==[True];rows={}
    for variant in ('single_recipient','nonhuman_recipient','missing_command','missing_permission','missing_reservation','extra_reservation','reversed','other_source','other_performer','unoccurred','personal'):
        want=variant=='personal';got=run(d,model(d,variant));assert got==[want],(variant,got);rows[variant]=want
    for name in ('performer','principal','call','reference','point'):
        w=model(d);w['z'+name]=lambda name=name:'failed' if name in ('reference','point') else ('b' if CONSTANTS[name]=='a' else 'a')
        assert run(d,w)==[False],name
    for n in ('aa','dg','f3','h233p','h234g','h234h'):
        w=model(d);w[n]=unknown;rejected(d,w)
    full=fixture(('r6fw',),q,restricted=False);rejected(full,model(full),'description domain')
    quoted=fixture(('r6fz',),'q[e[r b[p r6fz]][r b[p r6fz]]].',restricted=False)
    assert run(quoted,{r['name']:unknown for r in quoted['declarations'] if r['kind']=='primitive'})==[True]
    return dict(cases=rows,all_five_reference_slots_checked=True,same_two_message_families_and_all_recipients=True,
      full_reservation_description_domain_retained=True,full_description_domain_refused=True,full_description_domain_verified=False,
      diagnostic_families=['r2ug(reference)','r2uh(reference)'],quoted_permission_and_compliance_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def representation_checks():
    q='q[t[k r6fy['+args(('principal','call'))+' '+REF+']]['+z('point')+']].'
    d=fixture(('r6fy',),q);assert run(d,model(d))==[True];rows={}
    for variant in ('personal','no_mandate','private_statement','other_performer'):
        want=variant=='personal';got=run(d,model(d,variant));assert got==[want],(variant,got);rows[variant]=want
    v=model(d,'personal');v['h26v3']=lambda *a:False;v['h26v4']=lambda *a:False;assert run(d,v)==[True]
    for n in ('h26v3','h26v4'):
        w=model(d);w[n]=unknown;rejected(d,w)
    role=fixture(('r6fx',),'q[k r6fx['+args(('performer','principal','call','reference','point'))+']].');v=model(role)
    for n in ('performer','principal','call','reference','point'):
        w=dict(v);w['z'+n]=lambda n=n:'failed' if n in ('reference','point') else ('a' if n=='call' else 'b')
        assert run(role,w)==[False],n
    return dict(cases=rows,direct_person_does_not_need_delegation=True,same_performer_call_and_principal=True,all_five_representation_slots_checked=True,unknown_rejected=True)

@lru_cache(None)
def ability_checks():
    q='q[k r6f3['+args(('principal','community'))+' '+REF+' '+z('start')+']].'
    d=fixture(('r6f3',),q,('r2ue','r572'));assert run(d,model(d))==[True];rows={}
    for variant in ('no_method','empty_results','outside_results','second_result_failed','one_bad_method','permission_not_established','peace_lost',
                    'foreign_recipient','no_mandate','private_statement','extra_reservation'):
        want=variant=='one_bad_method';got=run(d,model(d,variant));assert got==[want],(variant,got);rows[variant]=want
    for n in ('h26v5','h26v6','h26v7','r2ue','r572','h237c'):
        w=model(d);w[n]=unknown;rejected(d,w)
    # Actual fulfillment and motive of the obedience command are quoted only.
    v=model(d)
    for n in ('h233z','h234b','h7a'):v[n]=unknown
    assert run(d,v)==[True]
    return dict(cases=rows,native_official_speech_and_xa_xd=True,one_successful_method_suffices_but_all_its_selected_results_required=True,
      speech_alone_not_policy_or_peace=True,actual_obedience_not_required=True,
      boundaries='r2ue and r572 only: their actual contents are pinned in the prior free-choice and civic-peace reports. The r6fv description binder alone is instantiated to two closed families.',unknown_rejected=True)

@lru_cache(None)
def provider_checks():
    q='q[k r6f3['+args(('principal','community'))+' '+REF+' '+z('start')+']].'
    d=fixture(('r6f3',),q,('r6f2','xd'));v=model(d);calls=[]
    def goal(p,c,r):calls.append(('goal',(p,c,code(r))));return content(lambda t:t=='done')
    v['r6f2']=goal
    for n in ('h26v5','h26v6','h26v7'):
        def record(*a,n=n):calls.append((n,a));return True
        v[n]=record
    def invoke(actor,target,start,available,outcomes,selected):
        assert target.values==(False,False,True,False)
        assert (actor,start)==('c','start')
        available('c','a','start');available('a','b','failed')
        outcomes('c','a','start','done');selected('a','b','failed','reference')
        return True
    v['xd']=invoke;assert run(d,v)==[True]
    assert calls==[('goal',('c','c',refcode())),('h26v5',('c','c','reference','a','start')),('h26v5',('a','c','reference','b','failed')),
      ('h26v6',('c','c','reference','a','start','done')),('h26v7',('a','c','reference','b','failed','reference'))],calls
    # Fixed community/reference are captured while actor, method, start/end are
    # supplied by the actual xd adapter. Check each outer slot without a false
    # goal masking a bad method binding.
    for name in ('principal','community','reference','start'):
        calls.clear();w=dict(v);change='failed' if name in ('reference','start') else 'b';w['z'+name]=lambda change=change:change
        def altered(actor,target,start,a,o,s,name=name,change=change):
            assert actor==(change if name=='principal' else 'c') and start==(change if name=='start' else 'start')
            a(actor,'a',start);o(actor,'a',start,'done');s(actor,'a',start,'done');return True
        w['xd']=altered;assert run(d,w)==[True]
        actual={n:change if n==name else CONSTANTS[n] for n in ('principal','community','reference','start')}
        assert calls[0]==('goal',(actual['principal'],actual['community'],refcode()))
        prefix=(actual['principal'],actual['community'],actual['reference'],'a',actual['start'])
        assert calls[1:]==[('h26v5',prefix),('h26v6',(*prefix,'done')),('h26v7',(*prefix,'done'))],(name,calls)
    return dict(all_context_and_callback_slots_and_arities_checked=True,same_exact_goal_content=True,boundaries='r6f2 and xd only for argument recording; both actual connection and ability bodies run in ability_checks.')

@lru_cache(None)
def necessity_checks():
    q='q[t[k r6f4['+args(('topic','community','reference'))+']]['+z('point')+']].'
    d=fixture(('r6f4',),q,('r6f3','r6fp'));rows={}
    def values(capable=('a','b'),qualified=('a','b')):
        v=model(d)
        v['r6f3']=lambda p,c,r,start:p in capable and (c,code(r),start)==('c',refcode(),'done')
        v['r6fp']=lambda topic,c,r:FunctionValue(('individual',),'content',lambda p:content(lambda t:p in qualified and(topic,c,r,t)==('a','c','reference','done')))
        return v
    for name,cap,qual,want in (('both_qualified',('a','b'),('a','b'),True),('unqualified_speaker',('a','b'),('a',),False),
      ('qualified_but_incapable',(),('a','b'),True),('no_qualified_people',(),(),True),('only_nonhuman_capable',('c',),(),True)):
        assert run(d,values(cap,qual))==[want],name;rows[name]=want
    for name in ('r6f3','r6fp','h223h'):
        if name=='h223h':continue # Actual name constructor runs; test its selector below.
        v=values();v[name]=unknown;rejected(d,v)
    v=values();v['zrefpick']=lambda r,a,b:b;assert run(d,v)==[False]
    v=values();v['zrefpick']=unknown;rejected(d,v)
    for variant in ('other_topic','other_person','other_point','other_reference'):
        v=values()
        v['r6fp']=lambda topic,c,r:FunctionValue(('individual',),'content',lambda p:content(lambda t:
          (topic,c,r,p,t)==('b' if variant=='other_topic' else 'a','c','failed' if variant=='other_reference' else 'reference','b' if variant=='other_person' else 'a','failed' if variant=='other_point' else 'done')))
        assert run(d,v)==[False],variant
    return dict(cases=rows,necessary_not_sufficient_or_existential=True,bad_reference_name_not_hidden_in_false_antecedent=True,
      same_person_point_reference_and_topic=True,boundaries='r6f3 and r6fp only for universal implication. Native ability above; the complete personal profile is pinned in military-peace-guarantee.',unknown_rejected=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');segments=[]
    for phrase in ('nur derjenige','kann das sagen','räsonnirt so viel ihr wollt, und worüber ihr wollt; nur gehorcht!'):
        a=u['text'].index(phrase);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='same_official_quoted_policy_and_political_ability_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),
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
    t=format_graph(c.document,'compact');ranks={}
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:0 if n in ('r6fv','r6fx') else 1 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_bodies_and_meanings_unchanged=True,minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('speech',speech_checks),('representation',representation_checks),('ability',ability_checks),('providers',provider_checks),('necessity',necessity_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_political_quoted_speech.py','scripts/check_political_quoted_speech.py','tests/test_political_quoted_speech.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='same_official_quoted_policy_political_ability_and_necessary_person_conditions_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
