"""Check finite causal solutions and exact factive cognition of the policy."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_legislative_safety_insight import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,STATE,EQUATIONS,WORLDS,POLICY,CONTENT,NAMES,TIMES,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/legislative-safety-insight-v1.md';READING='data/legislative-safety-insight-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/legislative-public-permissions-v1.json','reports/cognitive-acquisition-v1.json','reports/community-protection-v1.json')
DOMAIN=('ruler','community','group','interest','second','judgment','reason','other')
SCENES=('reference','history','anchor','now','background','secondbackground')
ST={'kind':'function','parameters':['individual'],'result':'truth'}
EQ={'kind':'function','parameters':['individual',ST],'result':'truth'}
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def codeid(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
FARGS=args((*NAMES,*TIMES))
PCODE='r c[k zpolicy[]]';TCODE='r d[k zsafe[]]'
POLICY_LITERAL=(2,dict(kind='call',symbol='zpolicy',arguments=[]))
TARGET_LITERAL=(3,dict(kind='call',symbol='zsafe',arguments=[]))
def applied(symbol,rank):return (rank,dict(kind='apply',function=dict(kind='function_ref',symbol=symbol),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in (*NAMES,*TIMES)]))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),scoped=False):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zpolicytruth[d] c.r ztruth[d] c.d zpolicy[] e[b p[k zpolicytruth[v p]]].d zsafe[] e[b p[k ztruth[v p]]].d zalias[] e[k zsafe[]].'
    if scoped:
        extra+='r zscoped['+POLICY+' a d d d] c.d r6dp[policy '+POLICY+' community a reference d anchor d] e[b assessment[k zscoped[v policy v community v reference v anchor v assessment]]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns))
    return parse(format_graph(d,'compact')+query)
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zpolicytruth=lambda t:False,ztruth=lambda t:t=='now',aa=lambda p:p=='ruler',
        h243v=lambda i,c,r:i in ('interest','second') and (c,r)==('community','reference'),
        h26to=lambda c,i,r:(c,r)==('community','reference') and i in ('interest','second'),
        h26tp=lambda p,c,i,r,a,t,b:codeid(p)==POLICY_LITERAL and(c,r,a,t)==('community','reference','anchor','now') and i in ('interest','second') and b in ('background','secondbackground'),
        r6do=lambda p,c,i,r,a,t,b:codeid(p)==POLICY_LITERAL and(c,r,a,t)==('community','reference','anchor','now') and i in ('interest','second') and b in ('background','secondbackground'),
        zscoped=lambda p,c,r,a,t:codeid(p)==applied('r6dk',2) and(c,r,a,t)==('community','reference','anchor','now'))
    cognitive(v,TARGET_LITERAL)
    return v
def cognitive(v,expected):
    v.update(h26nf=lambda p,c,t:(p,t)==('ruler','now') and codeid(c)==expected,
        h26tw=lambda p,c,r,t:(p,r,t)==('ruler','reference','now') and codeid(c)==expected,
        h26ai=lambda p,j,r,t:(p,j,r,t)==('ruler','judgment','reference','now'),
        h26tv=lambda j,c,r,s,t:(j,r,s,t)==('judgment','reference',True,'now') and codeid(c)==expected,
        fc=lambda j,g,t:(j,g,t)==('judgment','reason','now'),fd=lambda g,j,t:(g,j,t)==('reason','judgment','now'),
        h26aj=lambda g,j,r,t:(g,j,r,t)==('reason','judgment','reference','now'))
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def causal_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r6dm','r6dn')),statements=[])
    extra='r zvars[] j[a].r zeq[a '+STATE+'] c.r zfactor[] a.r zharmfactor[] a.r zworld['+STATE+'] d.r zp[d] c.r zh[d] c.d zpolicy[] e[b t[k zp[v t]]].d zharm[] e[b t[k zh[v t]]].'
    a='k zvars[] p zeq k zfactor[] k zharmfactor[] p zworld k zpolicy[] k zharm[]'
    d=parse(format_graph(d,'compact')+extra+'q[k r6dm['+a+']].q[k r6dn['+a+']].')
    people=('p','h');scenes=('actual','ff','ft','tf','tt');bits=tuple(product((False,True),repeat=2));worlds=dict(zip(scenes[1:],bits))
    def value(table):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update(zvars=lambda:SequenceValue(people,'"individual"'),zfactor=lambda:'p',zharmfactor=lambda:'h',
            zeq=lambda n,s:False if n=='p' else table[2*int(s('p'))+int(s('h'))],
            zworld=lambda s:scenes[1+2*int(s('p'))+int(s('h'))],
            zp=lambda t:False if t=='actual' else worlds[t][0],zh=lambda t:False if t=='actual' else worlds[t][1])
        return v
    rows=[]
    for table in product((False,True),repeat=4):
        off=[h for h in (False,True) if h==table[int(h)]];on=[h for h in (False,True) if h==table[2+int(h)]]
        linked=bool(off and on);risk=linked and False in off and True in on;safe=linked and not risk
        v=value(table);got=run(d,v,people,scenes);assert got==[safe,risk],(table,got,off,on)
        rows.append(dict(table=list(table),off=off,on=on,safe=safe,induced_risk=risk))
    v=value((False,False,False,False));mutants={}
    for case in ('empty_variables','duplicate_variables','missing_harm','same_factor','wrong_policy_content','wrong_harm_content','wrong_worlds'):
        w=dict(v)
        if case=='empty_variables':w['zvars']=lambda:SequenceValue((),'"individual"')
        if case=='duplicate_variables':w['zvars']=lambda:SequenceValue(('p','h','p'),'"individual"')
        if case=='missing_harm':w['zvars']=lambda:SequenceValue(('p',),'"individual"')
        if case=='same_factor':w['zharmfactor']=lambda:'p'
        if case=='wrong_policy_content':w['zp']=lambda t:False
        if case=='wrong_harm_content':w['zh']=lambda t:True
        if case=='wrong_worlds':w['zworld']=lambda s:'ff'
        got=run(d,w,people,scenes);assert got==[False,False],(case,got);mutants[case]=got
    for n in ('zeq','zp','zh','zworld'):
        w=dict(v);w[n]=unknown;rejects(d,w,people,scenes)
    return dict(all_boolean_structural_tables=rows,invalid_models=mutants,actual_policy_not_required=True,unknown_rejected=True,
        native='rkt/rkv/rv/ru and all state quantifiers execute on two Boolean variables. Independent solution lists determine expected results, including cyclic, multiple-solution and no-solution tables.')

@lru_cache(None)
def model_binding_checks():
    a=PCODE+' '+args(('community','interest','reference','anchor','now','background'))
    d=fixture(('r6do',),'q[k r6do['+a+']].',('r6dm',));v=model(d);calls=[]
    expected=(POLICY_LITERAL,'community','interest','reference','anchor','now','background')
    def record(n,result):
        def fn(*a):
            key=(codeid(a[0]),*a[1:]);calls.append((n,key));return result
        return fn
    eq=FunctionValue(('individual',ST),'truth',lambda n,s:n=='interest')
    world=FunctionValue((ST,),'situation',lambda s:'now' if s('ruler') else 'background')
    providers=dict(h26tq=SequenceValue(('ruler','interest'),'"individual"'),h26tr=eq,h26ts='ruler',h26tt='interest',h26tu=world)
    for n,result in providers.items():v[n]=record(n,result)
    v['h243u']=lambda i,c,r,t:t!='now'
    def boundary(vs,eq,p,h,world,policy,harm):
        state=FunctionValue(('individual',),'truth',lambda n:n=='ruler')
        return tuple(vs.items)==('ruler','interest') and(p,h)==('ruler','interest') and eq('interest',state) and not eq('ruler',state) and world(state)=='now' and policy.values==(False,)*len(SCENES) and harm.values==tuple(t=='now' for t in SCENES)
    v['r6dm']=boundary;assert run(d,v)==[True];assert len(calls)==5 and all(k==expected for _,k in calls),calls
    rows={}
    for n in providers:
        w=dict(v);w[n]=unknown;rejects(d,w);rows[n]='unknown rejected'
    for n in ('h243v','h243u'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Every provider receives the same entire context, including the policy code.
    for name in ('community','interest','reference','anchor','now','background'):
        calls.clear();w=dict(v);replacement='history' if name in SCENES else 'other';w['z'+name]=lambda replacement=replacement:replacement
        # Do not infer a malformed model's truth: record the native calls only.
        w['r6dm']=lambda *a:True;run(d,w)
        position=('community','interest','reference','anchor','now','background').index(name)+1
        assert len(calls)==5 and all(key[position]==replacement for _,key in calls),name
    return dict(all_five_providers_receive_exact_context=True,native_same_community_interest_harm_content=True,unknown_rejected=True,
        boundary='r6dm only; the generic causal comparison is native in causal_checks. Structured function/sequence/content arguments are exercised, not replaced by names.')

@lru_cache(None)
def scope_checks():
    q='q[t[k r6dp['+PCODE+' '+args(('community','reference','anchor'))+']]['+z('now')+']].'
    d=fixture(('r6dp',),q,('r6do',));v=model(d);assert run(d,v)==[True];rows={}
    for case in ('empty_interests','empty_backgrounds','second_interest_unsafe','second_background_unsafe','second_interest_no_background','irrelevant_unsafe','inapplicable_interest','different_policy','different_anchor','unknown_comparison'):
        w=dict(v);want=False
        if case=='empty_interests':w['h26to']=lambda *a:False
        if case=='empty_backgrounds':w['h26tp']=lambda *a:False
        if case=='second_interest_unsafe':w['r6do']=lambda p,c,i,*a:i!='second'
        if case=='second_background_unsafe':w['r6do']=lambda *a:a[-1]!='secondbackground'
        if case=='second_interest_no_background':w['h26tp']=lambda p,c,i,*a:i=='interest'
        if case=='irrelevant_unsafe':w['r6do']=lambda p,c,i,*a:i in ('interest','second');want=True
        if case=='inapplicable_interest':w['h243v']=lambda i,*a:i=='interest'
        if case=='different_policy':w['h26tp']=lambda p,*a:codeid(p)==(2,dict(kind='call',symbol='zsafe',arguments=[]))
        if case=='different_anchor':w['h26tp']=lambda p,c,i,r,a,*xs:a=='now'
        if case=='unknown_comparison':w['r6do']=unknown;rejects(d,w);rows[case]='rejected';continue
        assert run(d,w)==[want],case;rows[case]=want
    for n in ('h26to','h26tp'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,all_relevant_interests_and_backgrounds_nonempty=True,boundary='r6do only; its entire input binding and native model body checked separately')

@lru_cache(None)
def cognitive_checks():
    base=args(('ruler',))+' '+TCODE+' '+z('reference')
    d=fixture(('r6ds','r6dt'),'q[k r6ds['+base+' '+z('now')+']].q[k r6dt['+base+' '+args(('now','now'))+']].')
    v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('not_accepted','not_grasped','not_held','different_judgment','wrong_polarity','different_content','no_used_reason','unsupported_reason','insufficient_ground','different_reason','false_content','truth_at_other_point','mere_alias','truth_unknown'):
        w=dict(v);want=[False,False]
        if case=='not_accepted':w['h26nf']=lambda *a:False
        if case=='not_grasped':w['h26tw']=lambda *a:False
        if case=='not_held':w['h26ai']=lambda *a:False
        if case=='different_judgment':w['h26tv']=lambda j,*a:j=='other'
        if case=='wrong_polarity':w['h26tv']=lambda j,c,r,s,t:s is False
        if case in ('different_content','mere_alias'):w['h26tv']=lambda j,c,*a:codeid(c)==(3,dict(kind='call',symbol='zalias',arguments=[]))
        if case=='no_used_reason':w['fc']=lambda *a:False
        if case=='unsupported_reason':w['fd']=lambda *a:False
        if case=='insufficient_ground':w['h26aj']=lambda *a:False
        if case=='different_reason':w['h26aj']=lambda g,*a:g=='other'
        if case=='false_content':w['ztruth']=lambda *a:False;want=[True,False]
        if case=='truth_at_other_point':w['ztruth']=lambda t:t=='background';want=[True,False]
        if case=='truth_unknown':w['ztruth']=unknown;rejects(d,w);rows[case]='rejected';continue
        assert run(d,w)==want,case;rows[case]=want
    for n in ('h26nf','h26tw','h26ai','h26tv','fc','fd','h26aj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    held=fixture(('r6ds',),'q[k r6ds['+base+' '+z('now')+']].');w=model(held);w['ztruth']=unknown;assert run(held,w)==[True]
    return dict(cases=rows,same_judgment_and_reason_native=True,acceptance_does_not_execute_truth=True,factive_truth_separate=True,unknown_rejected=True)

@lru_cache(None)
def policy_connection_checks():
    d=fixture(('r6dq','r6du'),'q[t[k r6dq['+FARGS+']]['+z('now')+']].q[t[k r6du['+FARGS+']]['+z('now')+']].',scoped=True)
    v=model(d);cognitive(v,applied('r6dq',3));assert run(d,v)==[True,True];rows={}
    for case in ('other_policy','other_community','other_reference','other_anchor','not_safe','not_grasped','no_ground','other_safety_content','no_current_policy'):
        w=dict(v);want=[False,False]
        if case=='other_policy':w['zscoped']=lambda p,*a:codeid(p)==POLICY_LITERAL
        if case=='other_community':w['zscoped']=lambda p,c,*a:c=='other'
        if case=='other_reference':w['zscoped']=lambda p,c,r,*a:r=='history'
        if case=='other_anchor':w['zscoped']=lambda p,c,r,a,t:a=='now'
        if case=='not_safe':w['zscoped']=lambda *a:False
        if case=='not_grasped':w['h26tw']=lambda *a:False;want=[True,False]
        if case=='no_ground':w['h26aj']=lambda *a:False;want=[True,False]
        if case=='other_safety_content':w['h26nf']=lambda p,c,t:codeid(c)==TARGET_LITERAL;want=[True,False]
        if case=='no_current_policy':w['zpolicytruth']=unknown;want=[True,True]
        assert run(d,w)==want,case;rows[case]=want
    for n in (*NAMES,*TIMES):
        w=dict(v)
        if n in NAMES:w['znamepick']=lambda p,*cs,n=n:cs[DOMAIN.index('other' if p==n else p)]
        else:w['zrefpick']=lambda p,*cs,n=n:cs[SCENES.index('background' if p==n else p)]
        assert run(d,w)==[False,False],n
    # Both constructors may run without evaluating policy, safety or cognition.
    code='k r6dr['+' '.join('r['+z(n)+']' for n in (*NAMES,*TIMES))+']'
    quoted=fixture(('r6dr',),'q[e['+code+']['+code+']].',scoped=True);w=model(quoted);w['zscoped']=unknown;w['h26nf']=unknown
    assert run(quoted,w)==[True]
    return dict(cases=rows,all_six_names_checked=True,same_policy_and_safety_descriptions=True,quote_does_not_execute=True,
        boundary='r6dp is an exact policy/community/reference/anchor/assessment adapter; the scope and model bodies have independent native checks. r6dq/r6dr/r6ds/r6dt/r6du and the actual r6dl policy constructor execute natively.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016');segments=[]
    for f in ('sieht ein','es ohne Gefahr sei'):
        a=u['text'].index(f,390);segments.append(dict(unit=u['id'],range=[a,a+len(f)],text=f,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='policy_induced_danger_absence_and_grounded_insight_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),interpretation=LIMITS,
      unresolved=['国家元首の思考態度、啓蒙への照応、宗教からの拡張','実例、尊敬する君主の先行者不在、Aber/selbst/sogar、全文提示と通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();dep=dependency();assert not c.document['statements'] and len(old.document['statements'])==118
    for source in (old,dep):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    expected={n:(0 if n in ('r6dm','r6dn','r6ds') else 4 if n in ('r6dt','r6du') else 3) for n in MEANINGS}
    assert ranks==expected,ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('causal',causal_checks),('model_binding',model_binding_checks),('scope',scope_checks),('cognitive',cognitive_checks),('policy_connection',policy_connection_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_legislative_safety_insight.py','scripts/check_legislative_safety_insight.py','tests/test_legislative_safety_insight.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='policy_safety_and_grounded_factive_insight_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
