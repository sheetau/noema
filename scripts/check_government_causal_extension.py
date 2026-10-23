"""Check extended clocks, signed adoption contrasts and shared interventions."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_government_causal_extension import ROOT,LIBRARY,BASIS,STATE,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/government-causal-extension-v1.md';READING='data/government-causal-extension-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('civic-choice-mediation','government-principle-profile','government-benefit-appraisal','civic-human-agency'))
DOMAIN=('a','b','c','d');RULES=('a','b')
ON=('start','middle','end','late');OFF=tuple('off'+p for p in ON);MIX=tuple('mix'+p for p in ON)
SCENES=(*ON,*OFF,*MIX,'reference','other');CLOCK_SCENES=(*ON,*OFF,'reference','other')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',reference='reference',start='start',end='end',government='a',late='late')
CTX=tuple(CONSTANTS.values())[:6];FULL=tuple(CONSTANTS.values());ARGS=' '.join('k z'+n+'[]' for n in CONSTANTS)
LOWER=('r6kz','r6kw','r6k6','r6k7','r6la','r6ld','r6ly')
CODE='i[h[j[a]] e]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def state(a=True,b=False,c=True,d=True):return FunctionValue(('individual',),'truth',lambda x:dict(a=a,b=b,c=c,d=d)[x])
def bits(s):return tuple(s(x) for x in DOMAIN)
def context(*a):return tuple(a)==CTX
def full(*a):return tuple(a)==FULL
def good(g,c,r):return(g,c,r)==('a','b','reference')
def history(s,e):
    for h in (ON,OFF,MIX):
        if s==h[0] and e in (h[2],h[3]):return h[:h.index(e)+1]
    return ()
def timeline(s):return ON if s('a') else MIX if s('d') else OFF
def adopted(rule,point):return point in ('late','mixlate') and rule in RULES or point=='offlate' and rule=='b'

@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=LOWER):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if value in DOMAIN else 'd')+'.' for n,value in CONSTANTS.items())+'r zstate[] '+STATE+'.'
    extra+='r zfirstvalue[d] c.r zsecondvalue[d] c.r zcapture['+CODE+' '+CODE+'] c.'
    extra+='d zpolicyfirst[bindings j[a]] e[b at[w[e[d[v bindings]][n p a b]][k zfirstvalue[v at]]]].'
    extra+='d zpolicysecond[bindings j[a]] e[b at[w[e[d[v bindings]][n p a b]][k zsecondvalue[v at]]]].'
    return parse(format_graph(d,'compact')+extra+'q[k zcapture[r[p zpolicyfirst] r[p zpolicysecond]]].'+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic());codes=[]
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()});v['zstate']=lambda:state(False,False,True,False)
    def capture(*xs):codes[:]=xs;return True
    def mapped(*args):
        *given,s,t=args
        if not full(*given):return 'other'
        return timeline(s)[ON.index(t)] if t in ON else t
    def prior_map(*args):
        *given,s,t=args
        if not context(*given):return 'other'
        return timeline(s)[ON.index(t)] if t in ON else t
    v.update(zcapture=capture,zfirstvalue=lambda p:p=='start',zsecondvalue=lambda p:p=='late',
      h27ch=lambda c,r,s,e,t:(c,r)==('b','reference') and t in history(s,e),
      h27ci=lambda c,r,s,e,l,h:(c,r)==('b','reference') and l in history(s,e) and h in history(s,e) and history(s,e).index(l)<history(s,e).index(h),
      h27cq=prior_map,h27dy=mapped,h27cm=lambda *a:seq(DOMAIN),h27co=lambda *a:'a',h27cp=lambda *a:state(),
      h27cn=lambda *a:True if a[-2] in ('a','c') else False if a[-2]=='b' else a[-1]('a'),
      h27dz=lambda *a:'b' if a[-1]=='start' else 'd' if a[-2]=='a' else 'c',
      h27db=lambda g,c,r,rule:good(g,c,r) and rule in RULES,
      r6kz=lambda *a:context(*a),r6kw=lambda *a:context(*a[:-1]) and not a[-1]('b') and a[-1]('c'),
      r6k7=lambda g,c,r,p:good(g,c,r) and p in (*ON,*OFF,*MIX),
      r6k6=lambda g,c,r,rule,p:good(g,c,r) and adopted(rule,p),
      r6la=lambda g,c,r,s,e:good(g,c,r) and any(adopted(rule,s)!=adopted(rule,e) for rule in RULES),
      r6ld=lambda c,r,p:(c,r,p)==('b','reference','late'),r6ly=lambda g,c,r,p:(g,c,r,p)==('a','b','reference','late'),
      h237n=good,h256s=good,h27c6=lambda *a:'a',h27c7=lambda *a:'b',h27df=lambda g,o,c,r:good(g,c,r) and o=='b',
      h27da=lambda *a:seq(RULES if good(*a) else ()),h27dc=lambda g,c,r,rule:codes[RULES.index(rule)] if rule in RULES else codes[0],
      h27dd=lambda g,c,r,rule,p:good(g,c,r) and rule in RULES and p in (*ON,*OFF,*MIX),
      h27de=lambda g,c,r,p:good(g,c,r) and p in ('start','late'))
    def norm(source,actor,office,code,bindings,positive,point):
        return(source,actor,office)==('a','a','b') and bindings.items==() and positive and any(code==codes[i] and adopted(rule,point) for i,rule in enumerate(RULES))
    v['h7k']=norm
    return v
def run(d,v,scenes=SCENES):
    out=evaluate(d,v,DOMAIN,scenes,True);assert out[0] is True;return out[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def clock_checks():
    d=fixture(('r6l2',),'q[k r6l2['+ARGS+' k zstate[]]].');v=model(d);assert run(d,v,CLOCK_SCENES)==[True]
    v['zstate']=lambda:state();assert run(d,v,CLOCK_SCENES)==[True];cases={}
    for label in ('same_endpoint','earlier_endpoint','collapsed_clock','missing_image','reversed_order','changed_original_map','changed_original_order','extra_prefix_point'):
        v=model(d)
        if label=='same_endpoint':v['zlate']=lambda:'end'
        if label=='earlier_endpoint':v['zlate']=lambda:'middle'
        if label=='collapsed_clock':v['h27dy']=lambda *a:'offstart'
        if label=='missing_image':
            original=v['h27ch'];v['h27ch']=lambda c,r,s,e,t:original(c,r,s,e,t) or(s,e,t)==('offstart','offlate','other')
        if label=='reversed_order':
            original=v['h27ci'];v['h27ci']=lambda c,r,s,e,l,h:original(c,r,s,e,h,l) if(s,e)==('offstart','offlate') else original(c,r,s,e,l,h)
        if label=='changed_original_map':v['h27cq']=lambda *a:'offstart'
        if label=='changed_original_order':
            original=v['h27ci'];v['h27ci']=lambda c,r,s,e,l,h:original(c,r,s,e,h,l) if(s,e)==('start','end') else original(c,r,s,e,l,h)
        if label=='extra_prefix_point':
            original=v['h27ch'];v['h27ch']=lambda c,r,s,e,t:original(c,r,s,e,t) and not((s,e,t)==('start','end','middle'))
        result=run(d,v,CLOCK_SCENES);assert result==[False],(label,result);cases[label]=False
    # Distinguish every context slot without an N-to-the-arity tuple domain.
    for name,value in CONSTANTS.items():
        v=model(d);v['z'+name]=lambda value=value:'a' if value=='b' else 'b' if value in DOMAIN else 'other'
        assert run(d,v,CLOCK_SCENES)==[False],name
    for n in ('h27ch','h27ci','h27cq','h27dy'):
        v=model(d);v[n]=unknown;rejects(d,v)
    return dict(native_complete_clock_extension=True,contrasts=cases,all_eight_context_slots_distinguished=True,unknown_rejected=True)

@lru_cache(None)
def content_checks():
    d=fixture(('r6l3','r6l4'),'q[k r6l3['+ARGS+']].q[k r6l4['+ARGS+' k zstate[]]].');v=model(d);assert run(d,v,CLOCK_SCENES)==[True,True]
    cases={}
    for label in ('cause_alias','outside_model','false_adoption_label','missing_start_assessment','missing_late_assessment','missing_prior_content'):
        v=model(d)
        if label=='cause_alias':v['h27dz']=lambda *a:'a'
        if label=='outside_model':v['h27cm']=lambda *a:seq(('a','b','c'))
        if label=='false_adoption_label':v['r6k6']=lambda *a:False
        if label=='missing_start_assessment':v['r6k7']=lambda *a:a[-1]!='offstart'
        if label=='missing_late_assessment':v['r6k7']=lambda *a:a[-1]!='offlate'
        if label=='missing_prior_content':v['r6kw']=lambda *a:False
        result=run(d,v,CLOCK_SCENES);assert not all(result),(label,result);cases[label]=result
    # Exercise unchanged r6k6/k7 and their normative/description bodies natively
    # in the new state/content connection, for both actual and off worlds.
    d=fixture(('r6l4',),'q[k r6l4['+ARGS+' k zstate[]]].',tuple(n for n in LOWER if n not in ('r6k6','r6k7')))
    for s in (state(),state(False,False,True,False)):
        v=model(d);v['zstate']=lambda s=s:s;assert run(d,v,CLOCK_SCENES)==[True]
        v['h27dd']=lambda *a:a[-1] not in ('late','offlate');assert run(d,v,CLOCK_SCENES)==[False]
    # Every rule/end-point slot gets a distinct mismatch in turn.
    d=fixture(('r6l4',),'q[k r6l4['+ARGS+' k zstate[]]].',(*LOWER,'r6l2'));rows=0
    for rule,point in product(RULES,('start','late')):
        v=model(d);v['r6l2']=lambda *a:True
        original=v['h27dz'];v['h27dz']=lambda *a:('c' if point=='start' or rule=='a' else 'b') if a[-2:]==(rule,point) else original(*a)
        assert run(d,v)==[False],(rule,point);rows+=1
    for n in ('h27dz','h27cm','r6k6','r6k7','r6kw'):
        d=fixture(('r6l4','r6l3'),'q[k r6l3['+ARGS+']].q[k r6l4['+ARGS+' k zstate[]]].');v=model(d);v[n]=unknown;rejects(d,v)
    return dict(contrasts=cases,native_normative_content_in_both_worlds=True,all_four_rule_endpoint_bindings=rows,
      boundary='r6kw is the pinned prior mental/ability state check. New clock, scope and adoption equality run natively; r6k6/k7 and their old norm bodies are additionally executed in both worlds.',unknown_rejected=True)

@lru_cache(None)
def contrast_checks():
    d=fixture(('r6l5',),'q[k r6l5['+ARGS+' k zstate[]]].');rows=0
    for profile in range(256):
        v=model(d)
        points=('start','late','offstart','offlate')
        def status(g,c,r,rule,p):return good(g,c,r) and rule in RULES and p in points and bool(profile&(1<<(4*RULES.index(rule)+points.index(p))))
        v['r6k6']=status
        differences=[]
        for rule in RULES:
            a,b,c,e=[int(status('a','b','reference',rule,p)) for p in points];differences.append(b-a!=e-c)
        assert run(d,v)==[any(differences)],profile;rows+=1
    cases={}
    for label,values,expected in (
      ('shared_change',(0,1,0,1),False),('constant_existing_difference',(1,1,0,0),False),
      ('opposite_directions',(0,1,1,0),True),('addition_vs_unchanged',(0,1,0,0),True),
      ('withdrawal_vs_unchanged',(1,0,1,1),True)):
        v=model(d);v['r6k6']=lambda g,c,r,rule,p:rule=='a' and p in ('start','late','offstart','offlate') and bool(values[('start','late','offstart','offlate').index(p)])
        assert run(d,v)==[expected];cases[label]=expected
    return dict(all_256_signed_adoption_profiles=rows,contrasts=cases,other_counterfactual_changes_allowed=True)

def bounded(v):
    # The following adapters match the bodies checked above and keep each
    # structural fixed-point check from multiplying full clock quantification.
    def scope(*a):
        return full(*a) and all(v['h27dz'](*a,r,p) in v['h27cm'](*CTX).items and v['h27dz'](*a,r,p)!=v['h27co'](*CTX) for r,p in product(RULES,('start','late')))
    def checked(*a):
        *ctx,s=a
        if not full(*ctx):return False
        mapped=lambda p:v['h27dy'](*ctx,s,p)
        return v['r6kw'](*CTX,s) and all(v['r6k7']('a','b','reference',mapped(p)) for p in ('start','late')) and all(s(v['h27dz'](*ctx,r,p))==v['r6k6']('a','b','reference',r,mapped(p)) for r,p in product(RULES,('start','late')))
    def contrast(*a):
        *ctx,s=a
        if not full(*ctx):return False
        obs=v['h27cp'](*CTX);status=lambda world,r,p:int(v['r6k6']('a','b','reference',r,v['h27dy'](*ctx,world,p)))
        return any(status(obs,r,'late')-status(obs,r,'start')!=status(s,r,'late')-status(s,r,'start') for r in RULES)
    v.update(r6l3=scope,r6l4=checked,r6l5=contrast);return v

@lru_cache(None)
def causal_checks():
    d=fixture(('r6l6',),'q[k r6l6['+ARGS+']].',(*LOWER,'r6l3','r6l4','r6l5'))
    v=bounded(model(d));assert run(d,v)==[True];cases={}
    for label in ('missing_prior_cause','no_actual_change','bad_scope','bad_actual_content','bad_off_content','no_off_solution','one_off_solution_no_contrast','one_on_solution_unassessed','observed_clock_shift'):
        v=bounded(model(d));old=v['h27cn']
        if label=='missing_prior_cause':v['r6kz']=lambda *a:False
        if label=='no_actual_change':v['r6la']=lambda *a:False
        if label=='bad_scope':v['h27cm']=lambda *a:seq(('a','b','c'))
        if label=='bad_actual_content':v['r6kw']=lambda *a:not a[-1]('a')
        if label=='bad_off_content':v['r6kw']=lambda *a:a[-1]('a')
        if label=='no_off_solution':v['h27cn']=lambda *a:not a[-1]('d') if a[-2]=='d' and not a[-1]('a') else old(*a)
        if label=='one_off_solution_no_contrast':v['h27cn']=lambda *a:a[-1]('d') if a[-2]=='d' and not a[-1]('a') else old(*a)
        if label=='one_on_solution_unassessed':
            v['h27cn']=lambda *a:a[-1]('b') if a[-2]=='b' and a[-1]('a') else old(*a)
        if label=='observed_clock_shift':
            original=v['h27dy'];v['h27dy']=lambda *a:'offlate' if a[-2]('a') and a[-1]=='late' else original(*a)
        assert run(d,v)==[False],label;cases[label]=False
    # Exhaust all Boolean equations for the varying downstream variable in
    # the off branch; accept iff every existing fixed point has the contrast.
    tables=[]
    for table in range(4):
        v=bounded(model(d));old=v['h27cn']
        v['h27cn']=lambda *a,table=table:bool(table&(1<<int(a[-1]('d')))) if a[-2]=='d' and not a[-1]('a') else old(*a)
        solutions=[x for x in (False,True) if x==bool(table&(1<<int(x)))]
        expected=bool(solutions and all(not x for x in solutions));assert run(d,v)==[expected]
        tables.append(dict(table=table,solutions=solutions,result=expected))
    for n in ('h27cn','r6kz','r6la','r6l4','r6l5'):
        v=bounded(model(d));v[n]=unknown;rejects(d,v)
    return dict(native_ru_rw_interventions=True,contrasts=cases,all_four_off_fixed_point_tables=tables,
      actual_and_off_world_both_change=True,unknown_rejected=True,
      boundary='r6l3/l4/l5 are bounded after native body checks to avoid repeated clock enumeration for every structural assignment; r6kz is the unchanged pinned civic causal boundary. No adapter tests claim the lower corpus to be one fully enumerated finite social model.')

@lru_cache(None)
def binding_checks():
    d=fixture(('r6l6',),'q[k r6l6['+ARGS+']].',(*LOWER,'r6l3','r6l4','r6l5','rw'));v=model(d);calls=[]
    v['r6l3']=lambda *a:full(*a)
    def checked(*a):assert full(*a[:-1]);calls.append(('checked',bits(a[-1])));return True
    def contrast(*a):assert full(*a[:-1]);calls.append(('contrast',bits(a[-1])));return True
    v['r6l4']=checked;v['r6l5']=contrast
    def rw(variables,equations,mask,assigned,predicate):
        assert variables.items==DOMAIN
        assert tuple(mask(x) for x in DOMAIN)==(True,False,False,False)
        flag=assigned('a');assert all(assigned(x)==flag for x in DOMAIN)
        for s in (state(flag,False,True,False),state(flag,False,True,True)):
            for x in DOMAIN:assert equations(x,s)==v['h27cn'](*CTX,x,s)
            before=len(calls);assert predicate(s)
            assert calls[before:]==[('checked',bits(s))]+([] if flag else [('contrast',bits(s))])
        calls.append(('intervention',flag));return True
    v['rw']=rw;assert run(d,v)==[True];assert {c[1] for c in calls if c[0]=='intervention'}=={False,True}
    d=fixture(('r6l7','r6ma'),'q[k r6l7['+ARGS+']].q[t[k r6ma['+' '.join('k z'+n+'[]' for n in CONSTANTS if n!='late')+']][k zlate[]]].',(*LOWER,'r6l6'))
    rows=0
    for flags in product((False,True),repeat=3):
        v=model(d)
        v['r6l6']=lambda *a:full(*a) and flags[0]
        v['r6ld']=lambda c,r,p:(c,r,p)==('b','reference','late') and flags[1]
        v['r6ly']=lambda g,c,r,p:(g,c,r,p)==('a','b','reference','late') and flags[2]
        assert run(d,v)==[all(flags)]*2;rows+=1
    for name,value in CONSTANTS.items():
        v=model(d);v['r6l6']=lambda *a:full(*a);v['z'+name]=lambda value=value:'a' if value=='b' else 'b' if value in DOMAIN else 'other'
        assert run(d,v)==[False]*2,name
    return dict(exact_same_model_equations_cause_mask_and_all_solution_callbacks=True,all_eight_endpoint_conjunctions=rows,
      all_eight_parameter_slots_preserved=True,same_government_population_reference_and_late_point=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_collective_cause_extended_to_later_government_principle_changes_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[1000,1057],text=u['text'][1000:1057],definitions=list(MEANINGS),status='partial_dependency_annotation_emphasis_pending')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['auch/sogarの談話上の追加・期待上の強調','Wenn/soの全事例量化、前件の比喩、著者注参照・全文帰属・通読判断'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for prior in parents():
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};text=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:0 if n in ('r6l2','r6l3') else 1 for n in MEANINGS},ranks
    assert not {'rx3','rx5','r6lp','r6lq'}&set(c.entries)
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      unchanged_imports=True,roundtrips=True,no_forced_replacement_or_total_extinction_or_dignity_adoption=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('clock',clock_checks),('contents',content_checks),('contrast',contrast_checks),('cause',causal_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_government_causal_extension.py','scripts/check_government_causal_extension.py','tests/test_government_causal_extension.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='same_collective_cause_extended_to_later_government_principle_changes_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
