"""Check full comparative prospects, exact policy identity and public appraisal."""
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
from scripts.compose_government_benefit_appraisal import ROOT,LIBRARY,BASIS,CODE,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure,TRUE,FALSE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/government-benefit-appraisal-v1.md';READING='data/government-benefit-appraisal-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/dignity-conforming-treatment-v1.json','reports/government-principle-profile-v1.json')
DOMAIN=('a','b');RESULTS=('p0','p1','n0','n1');SCENES=('reference','actual','view','other',*RESULTS,'p2','n2')
CONSTANTS=dict(government='a',community='b',reference='reference',person='b',judgment='a',point='actual',candidate='view',beneficiary='a')
ARGS='k zgovernment[] k zcommunity[] k zreference[]'
BASE='k zgovernment[] k zbeneficiary[] k zcode[] p zpolicy k zreference[] k zcandidate[]'
DEFAULT=1+4+32+128  # Heavy goal gained; light goal lost, on both outcome branches.

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,(*roots,'r6lm','r6lw')),statements=[])
    extra=''.join('r z'+n+'[] '+('a' if value in DOMAIN else 'd')+'.' for n,value in CONSTANTS.items())
    extra+='r za[] a.r zb[] a.r zref[] d.r zother[] d.r zcode[] '+CODE+'.r zpolicy[j[a]] e.'
    extra+='r zcapturenames[i[a] i[a] i[d] i[d]] c.r zcapturecodes['+' '.join([CODE]*4)+'] c.'
    extra+='d zpolicyalias[bindings j[a]] e[c[k r6ll[k za[] k zb[] k zref[]]][v bindings]].'
    extra+='d zbenefitalias[bindings j[a]] e[c[k r6lv[k za[] k zb[] k zref[]]][v bindings]].'
    prelude='q[k zcapturenames[r[k za[]] r[k zb[]] r[k zref[]] r[k zother[]]]].'
    prelude+='q[k zcapturecodes[k r6lm[r[k za[]] r[k zb[]] r[k zref[]]] r[p zpolicyalias] k r6lw[r[k za[]] r[k zb[]] r[k zref[]]] r[p zbenefitalias]]].'
    return parse(format_graph(d,'compact')+extra+prelude+query)

def model(d,pattern=DEFAULT,weights=(3,1),positive_mass=Fraction(1,2),negative_mass=Fraction(1,2)):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic());names=[];codes=[];calls=[]
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()})
    def capture_names(*xs):names[:]=xs;return True
    def capture_codes(*xs):codes[:]=xs;return True
    def key(actor,code,reference,candidate):return actor=='a' and code==codes[0] and reference=='reference' and candidate in ('view','other','actual')
    def outcome(actor,code,reference,candidate,sign,item):
        # The actual forecast favors the opposite of the judgment's forecast.
        if candidate=='actual':return 'p2' if sign else 'n2'
        offset=0 if sign else 2
        return RESULTS[offset+DOMAIN.index(item)]
    def target(beneficiary,goal,reference):
        return Content(SCENES,tuple(beneficiary=='a' and reference=='reference' and (p=='n2' or p in RESULTS and bool(pattern&(1<<(2*RESULTS.index(p)+DOMAIN.index(goal))))) for p in SCENES))
    def forecast(actor,code,reference,candidate,sign):
        calls.append(('forecast',actor,code,reference,candidate,sign))
        return seq(DOMAIN if key(actor,code,reference,candidate) else ())
    def linked(judgment,code,bindings,point):
        calls.append(('judgment',judgment,code,bindings,point))
        return judgment=='a' and code==codes[2] and bindings.items==() and point=='actual'
    v.update(za=lambda:'a',zb=lambda:'b',zref=lambda:'reference',zother=lambda:'other',zcode=lambda:codes[0],
      zcapturenames=capture_names,zcapturecodes=capture_codes,
      zpolicy=lambda bindings:Content(SCENES,tuple(bindings.items==() and p in ('p0','p1','p2') for p in SCENES)),
      h223g=lambda x:names[DOMAIN.index(x)],h223h=lambda x:names[2 if x=='reference' else 3],
      aa=lambda p:p=='b',h237c=lambda p,c,r:(p,c,r)==('b','b','reference'),h27b5=lambda *a:seq(('b',)),
      h237n=lambda g,c,r:(g,c,r)==('a','b','reference'),h256s=lambda g,c,r:(g,c,r)==('a','b','reference'),
      h27c6=lambda *a:'a',h27c7=lambda *a:'b',h27df=lambda g,o,c,r:(g,o,c,r)==('a','b','b','reference'),
      dg=lambda act,p:act=='a',df=lambda person,act,p:(person,act)==('b','a'),h26n2=lambda person,act,g,p:(person,act,g)==('b','a','a'),
      h27dg=lambda person,r:person=='b' and r=='reference',h27dh=lambda *a:False,
      h27di=lambda act,person,p:(act,person)==('a','b'),h27dj=lambda *a:True,
      h27dk=lambda act,person,r,p:(act,person,r)==('a','b','reference') and p in ('p0','p1','p2'),h27dl=lambda *a:False,
      h27dm=lambda b,r:seq(DOMAIN if(b,r)==('a','reference') else ()),h27dn=lambda b,g,r:(b,r)==('a','reference') and g in DOMAIN,
      h27do=lambda b,g,r:Fraction(weights[DOMAIN.index(g)]),h27dp=target,
      h27dq=forecast,h27dr=lambda a,c,r,v,s,o:key(a,c,r,v) and o in DOMAIN,
      h27ds=outcome,h27dt=lambda a,c,r,v,s,o:(positive_mass if s else negative_mass) if o=='a' else 1-(positive_mass if s else negative_mass),
      h27du=lambda b,g,r,c,p:(b,r)==('a','reference') and g in DOMAIN and p in (*RESULTS,'p2','n2'),
      fa=lambda p,j,t:(p,j,t)==('b','a','actual'),fb=lambda j,g,t:(j,g,t)==('a','a','actual'),
      h27dv=linked,h27dw=lambda j,t,c:(j,t)==('a','actual') and c=='view',h27dx=lambda g,j,t:(g,j,t)==('a','a','actual'))
    return v,names,codes,calls

def run(d,v):
    out=evaluate(d,v,DOMAIN,SCENES,True);assert out[:2]==[True,True];return out[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def comparison_checks():
    d=fixture(('r6lu',),'q[k r6lu['+BASE+']].');rows=0
    for pattern in range(256):
        v,_,_,_=model(d,pattern)
        scores=[sum((3,1)[j]*int(bool(pattern&(1<<(2*i+j)))) for j in range(2)) for i in range(4)]
        assert run(d,v)==[sum(scores[:2])>sum(scores[2:])],(pattern,scores);rows+=1
    risks={}
    # No newly guaranteed goal: the positive side offers a chance of the heavy
    # goal but loses a guaranteed light goal. Vary that chance around the threshold.
    for chance in (Fraction(0),Fraction(1,4),Fraction(1,3),Fraction(1,2),Fraction(1)):
        v,_,_,_=model(d,1+32+128,positive_mass=chance)
        result=run(d,v);assert result==[3*chance>1];risks[str(chance)]=result[0]
    v,_,_,_=model(d,weights=(1,3));assert run(d,v)==[False]
    return dict(all_256_goal_outcome_profiles=rows,uncertain_gain_with_guaranteed_loss=risks,
      strict_threshold_and_equal_value_rejected=True,fixed_weights_change_comparison=True)

@lru_cache(None)
def completeness_checks():
    d=fixture(('r6lu',),'q[k r6lu['+BASE+']].');cases={}
    mutations={
      'empty_goals':('h27dm',lambda *a:seq(())),
      'omitted_goal':('h27dm',lambda *a:seq(('a',))),
      'duplicate_goal':('h27dm',lambda *a:seq(('a','a','b'))),
      'zero_goal_weight':('h27do',lambda b,g,r:Fraction(0 if g=='a' else 1)),
      'negative_goal_weight':('h27do',lambda b,g,r:Fraction(-1 if g=='a' else 1)),
      'empty_outcomes':('h27dq',lambda *a:seq(())),
      'omitted_outcome':('h27dq',lambda *a:seq(('a',))),
      'duplicate_outcome':('h27dq',lambda *a:seq(('a','b','b'))),
      'wrong_mass_sum':('h27dt',lambda *a:Fraction(1)),
      'negative_mass':('h27dt',lambda a,c,r,v,s,o:Fraction(-1 if o=='a' else 2)),
      'wrong_policy_polarity':('zpolicy',lambda *a:Content(SCENES,(True,)*len(SCENES))),
      'unassessed_goal':('h27du',lambda b,g,r,c,p:g=='a'),
      'wrong_actor':('zgovernment',lambda:'b'),
      'wrong_beneficiary':('zbeneficiary',lambda:'b'),
      'wrong_reference':('zreference',lambda:'other'),
      'wrong_candidate':('zcandidate',lambda:'reference'),
    }
    for label,(name,value) in mutations.items():
        v,_,_,_=model(d);v[name]=value;result=run(d,v);assert result==[False],(label,result);cases[label]=False
    for name in ('h27dn','h27do','h27dp','h27dr','h27ds','h27dt','h27du'):
        v,_,_,_=model(d);v[name]=unknown;rejects(d,v)
    return dict(contrasts=cases,unknown_inputs_rejected=True,all_generic_comparison_bodies_native=True)

@lru_cache(None)
def concrete_policy_checks():
    query='q[t[c[k r6lv['+ARGS+']][l[a][]]][k zcandidate[]]].q[t[c[k r6lv['+ARGS+']][l[a][k za[]]]][k zcandidate[]]].'
    query+='q[t[c[s[k r6lw[r[k za[]] r[k zb[]] r[k zref[]]]]][l[a][]]][k zcandidate[]]].'
    d=fixture(('r6lv','r6lw'),query);v,_,codes,calls=model(d);assert run(d,v)==[True,False,True]
    assert calls and all(row[1:4]==('a',codes[0],'reference') for row in calls if row[0]=='forecast')
    cases={}
    for label in ('wrong_community','wrong_name','failed_treatment','wrong_target_code','alias_code'):
        v,names,codes,_=model(d)
        if label=='wrong_community':v['zcommunity']=lambda:'a'
        if label=='wrong_name':v['h223g']=lambda p:names[1-DOMAIN.index(p)]
        if label=='failed_treatment':v['h27dk']=lambda *a:False
        if label=='wrong_target_code':v['h27dq']=lambda *a:seq(())
        if label=='alias_code':
            v['h27dr']=lambda a,c,r,w,s,o:c==codes[1] and o in DOMAIN
        result=run(d,v);assert result[0] is False,(label,result);cases[label]=result
    # Both descriptions really have the same extension; recognition below still
    # binds to the exact original description.
    d=fixture(('r6lv',),'q[t[k zbenefitalias[l[a][]]][k zcandidate[]]].q[t[c[k r6lv['+ARGS+']][l[a][]]][k zcandidate[]]].')
    for pattern in (0,DEFAULT):
        v,_,_,_=model(d,pattern);assert run(d,v)==[pattern==DEFAULT]*2
    return dict(native_dignity_and_benefit_execution=True,empty_binding_only=True,exact_same_actor_beneficiary_policy_reference=True,contrasts=cases,same_extension_alias_checked=True)

@lru_cache(None)
def institutional_checks():
    query='q[k r6lx['+ARGS+' k zperson[] k zjudgment[] k zpoint[]]].q[k r6ly['+ARGS+' k zpoint[]]].q[t[k r6lz['+ARGS+']][k zpoint[]]].'
    d=fixture(('r6lx','r6ly','r6lz'),query);v,_,codes,calls=model(d);assert run(d,v)==[True]*3
    assert any(row[0]=='judgment' and row[1]=='a' and row[2]==codes[2] and row[3].items==() and row[4]=='actual' for row in calls)
    cases={}
    mutations={
      'no_human':('aa',lambda *a:False),'no_occurrence':('dg',lambda *a:False),
      'other_person_acts':('df',lambda p,j,t:(p,j)==('a','a')),
      'private_judgment':('h26n2',lambda *a:False),'not_institution_view':('h27dx',lambda *a:False),
      'no_judging':('fa',lambda *a:False),'other_subject':('fb',lambda j,g,t:g=='b'),
      'empty_views':('h27dw',lambda *a:False),'not_affirmative_link':('h27dv',lambda *a:False),
      'wrong_government':('zgovernment',lambda:'b'),'wrong_community':('zcommunity',lambda:'a'),
      'wrong_reference':('zreference',lambda:'other'),'wrong_point':('zpoint',lambda:'view'),
      'wrong_office':('h27c7',lambda *a:'a'),
    }
    for label,(name,value) in mutations.items():
        v,_,_,_=model(d);v[name]=value;result=run(d,v);assert result==[False]*3,(label,result);cases[label]=result
    for label,alter in (('wrong_person','zperson'),('wrong_judgment','zjudgment')):
        v,_,_,_=model(d);v[alter]=lambda alter=alter:'a' if alter=='zperson' else 'b'
        assert run(d,v)==[False,True,True];cases[label]=[False,True,True]
    for index,label in ((0,'treatment_instead_of_benefit'),(3,'same_extension_benefit_alias')):
        v,_,codes,_=model(d);v['h27dv']=lambda j,c,b,t:c==codes[index] and b.items==() and(j,t)==('a','actual')
        assert run(d,v)==[False]*3;cases[label]=[False]*3
    v,_,_,_=model(d);v['h27dw']=lambda j,t,c:(j,t)==('a','actual') and c in ('view','actual')
    assert run(d,v)==[False]*3  # One adverse candidate must not be discarded.
    for name in ('fa','df','h26n2','h27dx','h27dv','h27dw'):
        v,_,_,_=model(d);v[name]=unknown;rejects(d,v)
    return dict(contrasts=cases,all_institutional_bodies_native=True,one_adverse_candidate_rejected=True,
      same_human_same_judgment_same_institution=True,unknown_rejected=True)

@lru_cache(None)
def nonfactivity_checks():
    d=fixture(('r6ly','r6lv','r6lk'),'q[k r6ly['+ARGS+' k zpoint[]]].q[t[c[k r6lv['+ARGS+']][l[a][]]][k zpoint[]]].q[k r6lk['+ARGS+' k zpoint[]]].')
    v,_,_,_=model(d);assert run(d,v)==[True,False,False]
    # A second favorable view is allowed; its inclusion is never confused with
    # actual realization or adoption. No norm predicate is in this closure.
    v,_,_,_=model(d);v['h27dw']=lambda j,t,c:(j,t)==('a','actual') and c in ('view','other')
    assert run(d,v)==[True,False,False]
    # The adverse actual comparison is fully assessed and normalized; its
    # falsity is not caused by missing inputs or an invalid policy forecast.
    d=fixture(('r6ls',),'q[k r6ls['+BASE+' '+TRUE+']].q[k r6ls['+BASE+' '+FALSE+']].')
    v,_,_,_=model(d);v['zcandidate']=lambda:'actual';assert run(d,v)==[True,True]
    return dict(affirmed_despite_actual_nonbenefit_and_nonperformance=True,actual_comparison_valid_on_both_sides=True,two_favorable_views_allowed=True,no_norm_adoption_inferred=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='same_government_nonfactive_comparative_policy_appraisal_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[1057,1094],text=u['text'][1057:1094],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['原則への因果作用と時間・強調','同じ政治的終点のnun、Wenn/so全体、著者注・全文帰属・通読判断'],
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
    assert ranks=={n:1 if n in ('r6lx','r6ly','r6lz') else 0 for n in MEANINGS},ranks
    assert not {'h7k','r6lp','r6lq','rx7','r6lc','r6kr'}&set(c.entries)
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      unchanged_imports=True,roundtrips=True,no_performance_or_adoption_or_capacity_gate=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('comparison',comparison_checks),('completeness',completeness_checks),('concrete_policy',concrete_policy_checks),('institution',institutional_checks),('nonfactivity',nonfactivity_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_government_benefit_appraisal.py','scripts/check_government_benefit_appraisal.py','tests/test_government_benefit_appraisal.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='same_government_nonfactive_comparative_policy_appraisal_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
