"""Check departure identity, matched effects, rebounds and source composition."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_departure_hindrance_trend import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/departure-hindrance-trend-v1.md';READING='data/departure-hindrance-trend-reading-v1.json';REPORT='reports/departure-hindrance-trend-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/qualified-pursuit-opening-v1.json','reports/exercise-capacity-v1.json','reports/paired-restriction-influence-v1.json','reports/declining-hindrances-v1.json','reports/sixth-paragraph-v1.json')
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
PEOPLE=('alice','bob');DOMAIN=(*PEOPLE,'process','other','group','frame','factor','result')
SCENES=('reference','low','high','initial','lowend','highend')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
TARGET='k zgroup[] k zreference[] k zframe[] k zinitial[]'
STATE={'kind':'function','parameters':['individual'],'result':'truth'}
OBSTACLES=('one','two','three');TIMES=('first','second','third','fourth','last')
TEMP_EXTRA='r zhistory[d] c.r zbefore[d d] c.r zstart[] d.r zend[] d.r zobstacles[] j[a].r zscope[a] c.r zassessed[a d] c.r zhindering[a d] c.r zbound[] b.'
TEMP='p zhistory p zbefore k zstart[] k zend[] k zobstacles[] p zscope p zassessed p zhindering p zbound'
# zbound is nullary, unlike the two predicate arguments immediately before it.
TEMP=TEMP.replace('p zbound','k zbound[]')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+extra+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v,domain=DOMAIN,scenes=SCENES):
    try:run(d,v,domain,scenes)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def content(scenes,points):return Content(scenes,tuple(s in points for s in scenes))
def arithmetic():return dict(ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda t:Fraction(int(t)),pa=lambda a,b:a/b if b else Fraction(0))
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    ends={'low':'lowend','high':'highend'}
    v.update(arithmetic());v.update(aa=lambda p:p in PEOPLE,mp=lambda g:SequenceValue(PEOPLE if g=='group' else (),'"individual"'),
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in PEOPLE,
        h7q=lambda f,c,s:f=='frame' and c in ends and s in ('initial',ends[c]),
        ic=lambda a,b,c:c in ends and (a,b)==('initial',ends[c]),h256o=lambda p,c,s:p in PEOPLE and c in ends and s in ('initial',ends[c]),
        fo=lambda p:content(SCENES,SCENES),be=lambda p,process,a,b:(p,process,a,b)==('alice','process','initial','highend'))
    return v

@lru_cache(None)
def native_departure_checks():
    from scripts import check_exercise_capacity as old
    extra='r zperson[] a.r zanchor[] d.r zprocess[] a.r zend[] d.'
    d=fixture(('be',),'q[k be[k zperson[] k zprocess[] k zanchor[] k zend[]]].',extra=extra);rows={}
    for variant in ('baseline','not_self_imputed','wrong_person','wrong_process','wrong_transition_content','missing_final_profile'):
        v=old.source_values(d,passes=(False,False));v.update(zprocess=lambda:'process',zend=lambda:'emancipated')
        available,outcomes,selected=v['ae'],v['af'],v['ap']
        v.update(ae=lambda p,m,s:available(p,m,s) or (p,m,s)==('person','method','endcase'),
            af=lambda p,m,s,t:outcomes(p,m,s,t) or (p,m,s,t)==('person','method','endcase','success'),
            ap=lambda p,m,s,t:selected(p,m,s,t) or (p,m,s,t)==('person','method','endcase','success'),
            hzsc=lambda p,a,s:p=='person' and (a=='anchor' and s in ('first','second') or variant!='missing_final_profile' and (a,s)==('emancipated','endcase')),
            hzsd=lambda p,a,s:p=='person' and a in ('anchor','emancipated'),hzse=lambda p,s:p=='person' and s in ('first','second','endcase'),
            hzsg=lambda p,m,a,s:p=='person' and m=='method' and a in ('anchor','emancipated'),hzsh=lambda p,m,a,s:p=='person' and a in ('anchor','emancipated'),
            ag=lambda r,a,b:(r,a,b)==('process','anchor','emancipated'),
            la=lambda p,r,a,b:(p,r,a,b)==('other' if variant=='wrong_person' else 'person','other' if variant=='wrong_process' else 'process','anchor','emancipated'),
            hziq=lambda p,g,s:variant!='not_self_imputed' and (p,s,normalized(g))==('person','anchor',('bf',0)),
            hzid=lambda p,r,f,t,a,b:(p,r,normalized(f),normalized(t),a,b)==('person','process',('bf' if variant=='wrong_transition_content' else 'bp',0),('up',0),'anchor','emancipated'))
        got=run(d,v,old.DOMAIN,old.SCENES);assert got==[variant=='baseline'],(variant,got);rows[variant]=got[0]
    return dict(cases=rows,native_be_imputation_and_exercise_capacity=True,boundaries=[])

@lru_cache(None)
def target_checks():
    q='q[k r5t6['+TARGET+' k zhigh[]]].q[e[k r5t7['+TARGET+' k zhigh[]]][k zexpected[]]].q[k r5ua['+TARGET+' k zhigh[] k zlow[]]].q[k r5ua['+TARGET+' k zlow[] k zhigh[]]].'
    d=fixture(('r5t6','r5t7','r5ua'),q,('be','fo'),EXTRA+'r zexpected[] b.');rows={}
    cases={'baseline':([True,True,True,False],Fraction(1,2)),
        'same_person_two_processes':([True,True,True,False],Fraction(1,2)),
        'both_people':([True,True,True,False],Fraction(1)),
        'only_nonmember':([True,True,True,True],Fraction(0)),
        'foreign_endpoint':([True,True,True,True],Fraction(0)),
        'not_living_at_departure':([True,True,True,True],Fraction(0)),
        'unassessed':([False,True,False,False],Fraction(1,2)),
        'duplicate':([False,True,False,False],Fraction(1,2)),
        'missing_member':([False,True,False,False],Fraction(1)),
        'empty':([False,True,False,False],Fraction(0)),
        'initial_outside':([False,True,False,False],Fraction(0)),
        'no_future':([False,True,False,False],Fraction(0))}
    for variant,(want,score) in cases.items():
        v=base(d);v['zexpected']=lambda:score
        if variant=='same_person_two_processes':v['be']=lambda p,r,a,b:p=='alice' and r in ('process','other') and (a,b)==('initial','highend')
        if variant=='both_people':v['be']=lambda p,r,a,b:p in PEOPLE and (r,a,b)==('process','initial','highend')
        if variant=='only_nonmember':v['be']=lambda p,r,a,b:(p,r,a,b)==('other','process','initial','highend')
        if variant=='foreign_endpoint':v['be']=lambda p,r,a,b:(p,r,a,b)==('alice','process','initial','reference')
        if variant=='not_living_at_departure':v['h256o']=lambda p,c,s:p in PEOPLE and s!='highend'
        if variant=='unassessed':v['fo']=lambda p:content(SCENES,() if p=='bob' else SCENES)
        if variant in ('duplicate','missing_member','empty'):
            members={'duplicate':('alice','alice','bob','bob'),'missing_member':('alice',),'empty':()}[variant]
            v['mp']=lambda g:SequenceValue(members,'"individual"')
        if variant=='initial_outside':v['zinitial']=lambda:'reference'
        if variant=='no_future':v['h7q']=lambda f,c,s:s=='initial';v['ic']=lambda *a:False
        got=run(d,v);assert got==want,(variant,got,want);rows[variant]=got
    for n in ('be','fo','h7q','h256o'):
        v=base(d);v['zexpected']=lambda:Fraction(1,2);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,boundaries=['be','fo'],native_departure_test='native_departure',same_process_person_history_and_fixed_denominator=True,unknown_rejected=True)

@lru_cache(None)
def paired_checks():
    extra=EXTRA+'r zvariables[] j[a].r zequation[a h[a] c] c.r zworld[h[a] c] d.r zmatch[h[a] c h[a] c] c.'
    tail='k zfactor[] '+TARGET+' k zvariables[] p zequation k zfactor[] p zworld p zmatch'
    q='q[k r5uc['+tail+']].q[k r5ud['+tail+']].'
    d=fixture(('r5uc','r5ud'),q,('be','fo'),extra);rows={}
    for variant in ('baseline','neutral','beneficial','no_match','no_off_solution','reversed_factor','other_condition','unassessed','unknown_departure'):
        v=base(d)
        v.update(zvariables=lambda:SequenceValue(('factor','result'),'"individual"'),
            zequation=lambda var,state:(not state('result') if variant=='no_off_solution' and not state('factor') else not state('factor')) if var=='result' else False,
            zworld=lambda state:'high' if state('result') else 'low',zmatch=lambda on,off:variant!='no_match',
            h26kg=lambda obstacle,r,c:(obstacle,r)==('other' if variant=='other_condition' else 'factor','reference') and c==('high' if variant=='reversed_factor' else 'low'))
        if variant=='neutral':v['be']=lambda p,r,a,b:(p,r,a)==('alice','process','initial') and b in ('highend','lowend')
        if variant=='beneficial':v['be']=lambda p,r,a,b:(p,r,a,b)==('alice','process','initial','lowend')
        if variant=='unassessed':v['fo']=lambda p:content(SCENES,())
        if variant=='unknown_departure':v['be']=unknown;rejects(d,v);rows[variant]='rejected';continue
        want=[variant in ('baseline','neutral','beneficial'),variant=='baseline']
        got=run(d,v);assert got==want,(variant,got,want);rows[variant]=got
    for n in ('h26kg','zmatch','zequation'):
        v=base(d);v.update(zvariables=lambda:SequenceValue(('factor','result'),'"individual"'),zequation=lambda var,s:not s('factor') if var=='result' else False,
            zworld=lambda s:'high' if s('result') else 'low',zmatch=lambda *a:True,h26kg=lambda o,r,c:c=='low');v[n]=unknown;rejects(d,v)
    return dict(cases=rows,native_intervention_solutions_matching_alignment_and_departure_ratios=True,boundaries=['be','fo'],unknown_rejected=True)

def temporal_values(d,profile=(3,2,3,2,1),variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};v.update(arithmetic());times=TIMES[:len(profile)]
    members=OBSTACLES if variant not in ('duplicate','omitted') else ('one','one','two','three') if variant=='duplicate' else ('one','two')
    v.update(zhistory=lambda t:t in times,zbefore=lambda a,b:a in times and b in times and (times.index(a)<times.index(b) or variant=='cycle' and (a,b)==(times[-1],times[0])),
        zstart=lambda:times[0],zend=lambda:times[-1],zobstacles=lambda:SequenceValue(members,'"individual"'),zscope=lambda o:o in OBSTACLES,
        zassessed=lambda o,t:not(variant=='unassessed' and (o,t)==('two','third')),
        zhindering=lambda o,t:o in OBSTACLES and t in times and OBSTACLES.index(o)<profile[times.index(t)],zbound=lambda:Fraction(0 if variant=='zero_bound' else 1))
    return v

@lru_cache(None)
def temporal_checks():
    d=fixture(('r5ug',),'q[k r5ug['+TEMP+']].',extra=TEMP_EXTRA);n=0
    def expected(p):
        return p[-1]<p[0] and any(p[-1]<m<p[0] for m in p[1:-1]) and all(a-b<=1 for a,b in zip(p,p[1:]))
    for p in product(range(4),repeat=4):
        got=run(d,temporal_values(d,p),OBSTACLES,TIMES[:4]);assert got==[expected(p)],(p,got);n+=1
    rows={}
    for label,p,want in (('rebound',(3,2,3,2,1),True),('monotone',(3,3,2,2,1),True),('single_jump',(3,3,3,1,1),False),('net_increase',(1,0,1,2,3),False),('no_net_drop',(3,2,1,2,3),False),('complete_removal',(3,2,1,0,0),True)):
        got=run(d,temporal_values(d,p),OBSTACLES,TIMES);assert got==[want],(label,got);rows[label]=got[0]
    for variant in ('duplicate','omitted','unassessed','cycle','zero_bound'):
        got=run(d,temporal_values(d,variant=variant),OBSTACLES,TIMES);assert got==[False],(variant,got);rows[variant]=False
    for name in ('zassessed','zhindering'):
        v=temporal_values(d);v[name]=unknown;rejects(d,v,OBSTACLES,TIMES)
    # The old monotone predicate still rejects this newly accepted rebound.
    old=deepcopy(parents()[1].document);old.update(declarations=closure(old,['rl4']),statements=[])
    old=parse(format_graph(old,'compact')+TEMP_EXTRA+'q[k rl4['+TEMP+']].')
    assert run(old,temporal_values(old),OBSTACLES,TIMES)==[False]
    return dict(exhaustive_four_point_profiles=n,cases=rows,old_rl4_rebound=False,unknown_rejected=True)

@lru_cache(None)
def source_checks():
    domain=(*OBSTACLES,'speaker','group','epoch','topic','frame','process','factor');scenes=('reference','candidate',*TIMES)
    extra=''.join('r z'+n+'[] '+('a' if n in domain else 'd')+'.' for n in (*domain,*scenes))
    extra+='r zobstacles[] j[a].r zscope[a] c.r zbound[] b.r zprocesses[a a] a.r zvariables[a] j[a].r zequations[a d] h[a h[a] c] c.r zfactors[a] a.r zworlds[a d h[a] c] d.r zmatches[a d h[a] c h[a] c] c.r zframes[d] a.'
    frame='k zspeaker[] k zgroup[] k zepoch[] k zreference[] k zcandidate[] k zlast[]'
    source=frame+' k ztopic[] k zfirst[] p zprocesses k zobstacles[] p zscope k zbound[] p zvariables p zequations p zfactors p zworlds p zmatches p zframes'
    q='q[k r5ui['+source+']].'+''.join('q[t[k r5uj['+source+']][k z'+t+'[]]].' for t in ('first','last'))
    d=fixture(('r5ui','r5uj'),q,('r5t3','r5uc','r5ud'),extra);rows={}
    for variant in ('baseline','opening_false','one_model_unassessed','foreign_group','foreign_reference','foreign_frame','no_decline','wrong_current_history'):
        v=temporal_values(d);v.update({'z'+n:lambda n=n:n for n in (*domain,*scenes)})
        v.update(zbound=lambda:Fraction(1),zobstacles=lambda:SequenceValue(OBSTACLES,'"individual"'),zprocesses=lambda p,w:'process',
            h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in TIMES and variant!='wrong_current_history',
            ic=lambda a,b,c:c=='candidate' and a in TIMES and b in TIMES and TIMES.index(a)<TIMES.index(b),
            zvariables=lambda o:SequenceValue((o,'factor'),'"individual"'),
            zequations=lambda o,t:FunctionValue(('individual',STATE),'truth',lambda var,state:var==o),zfactors=lambda o:o,
            zworlds=lambda o,t,state:t,zmatches=lambda o,t,on,off:on(o)!=off(o),zframes=lambda t:'frame')
        false=FunctionValue(('individual',),'truth',lambda _:False);true=FunctionValue(('individual',),'truth',lambda _:True)
        def model_ok(o,g,r,f,t,variables,equations,factor,worlds,matches):
            return (g,r,f)==('other' if variant=='foreign_group' else 'group','candidate' if variant=='foreign_reference' else 'reference','other' if variant=='foreign_frame' else 'frame') and o in OBSTACLES and t in TIMES and normalized(variables)==(o,'factor') and factor==o and worlds(true)==t and equations(o,true) and matches(true,false)
        v['r5uc']=lambda *a:model_ok(*a) and not(variant=='one_model_unassessed' and (a[0],a[4])==('two','third'))
        v['r5ud']=lambda *a:model_ok(*a) and (variant=='no_decline' or OBSTACLES.index(a[0])<(3,2,3,2,1)[TIMES.index(a[4])])
        def opening(s,g,e,r,c,p,topic,first,processes):
            return variant!='opening_false' and (s,g,e,r,c,p,topic,first,processes('speaker','topic'))==('speaker','group','epoch','reference','candidate','last','topic','first','process')
        v['r5t3']=opening
        got=run(d,v,domain,scenes);assert got==[variant=='baseline']*3,(variant,got);rows[variant]=got
    return dict(cases=rows,boundaries=['r5t3','r5uc','r5ud'],native_temporal_maps_and_closed_conjunction=True,outer_point_does_not_rebind_present=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0014');start=u['text'].index('Allein,');end=u['text'].index(' In diesem Betracht')
    return dict(status='departure_hindrance_trend_dependency_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),interpretation=LIMITS,
        references=[dict(url='https://korpora.org/kant/aa08/040.html',path=SOURCES[0],observation_ja='dahinの質付き能力目標と、allgemeinen AufklärungをAusgangで説明した障害の対象を分ける。allmälig wenigerの局所非単調な段階的減少を明示的に読む。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['場の比喩と現在進行の提示','oderの説明的言い換えとdochの提示','徴候と著者帰属','第一文の条件付き問答への接続','第二文の甚だしい不足と支援可能性','後続文と段落通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})
@lru_cache(None)
def structure_checks():
    c=catalog()
    for old in parents():
        for n,e in old.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==108
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=108,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('native_departure',native_departure_checks),('target',target_checks),('paired',paired_checks),('temporal',temporal_checks),('source',source_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,*PRIORS,*SOURCES,
        'scripts/compose_departure_hindrance_trend.py','scripts/check_departure_hindrance_trend.py','tests/test_departure_hindrance_trend.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_paired_influence.py','scripts/compose_present_epoch_assessment.py',
        'scripts/compose_declining_hindrances.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/check_exercise_capacity.py','scripts/check_standing_ability.py'}
    return dict(status='departure_hindrance_trend_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
