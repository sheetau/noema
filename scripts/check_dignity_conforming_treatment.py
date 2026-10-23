"""Check intrinsic standing, all actual public dealings and exact policy adoption."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_dignity_conforming_treatment import ROOT,LIBRARY,BASIS,CODE,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/dignity-conforming-treatment-v1.md';READING='data/dignity-conforming-treatment-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
PRIORS=('reports/government-principle-profile-v1.json','reports/government-release-v1.json','reports/civic-human-agency-v1.json')
ARTIFACT='artifacts/dignity-conforming-treatment-v1'
ARTIFACTS=tuple(ARTIFACT+'/'+n for n in ('fetch.json','kant-aa04-434.html','kant-aa04-434.txt','kant-aa04-435.html','kant-aa04-435.txt'))
DOMAIN=('a','b');PAIRS=tuple(product(DOMAIN,repeat=2));SCENES=('reference','other','start','end')
CONSTANTS=dict(government='a',community='b',reference='reference',person='b',activity='a',rule='a',point='end')
ARGS='k zgovernment[] k zcommunity[] k zreference[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,(*roots,'r6lm','r6ll'))
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r za[] a.r zb[] a.r zref[] d.r zother[] d.r zbenefit[] c.'
    extra+='r zcapturenames[i[a] i[a] i[d] i[d]] c.r zcapturecodes['+CODE+' '+CODE+'] c.'
    extra+='d zpolicyalias[bindings j[a]] e[c[k r6ll[k za[] k zb[] k zref[]]][v bindings]].'
    prelude='q[k zcapturenames[r[k za[]] r[k zb[]] r[k zref[]] r[k zother[]]]].'
    prelude+='q[k zcapturecodes[k r6lm[r[k za[]] r[k zb[]] r[k zref[]]] r[p zpolicyalias]]].'
    return parse(format_graph(d,'compact')+extra+prelude+query)

def good(g,c,r):return(g,c,r)==('a','b','reference')
def model(d,deals=15,grounds=15,substitutions=0):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic());names=[];codes=[];calls=[]
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()})
    def capture_names(*xs):names[:]=xs;return True
    def capture_codes(*xs):codes[:]=xs;return True
    def bit(mask,a,p):return bool(mask&(1<<PAIRS.index((a,p))))
    def norm(source,actor,office,code,bindings,positive,point):
        calls.append((source,actor,office,code,bindings,positive,point))
        return (source,actor,office)==('a','a','b') and code==codes[0] and bindings.items==() and positive and point=='end'
    v.update(za=lambda:'a',zb=lambda:'b',zref=lambda:'reference',zother=lambda:'other',zbenefit=lambda:False,
      zcapturenames=capture_names,zcapturecodes=capture_codes,
      h223g=lambda x:names[DOMAIN.index(x)],h223h=lambda x:names[2 if x=='reference' else 3],
      aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:(c,r)==('b','reference') and p in DOMAIN,
      h237n=good,h256s=good,h27c6=lambda c,r:'a',h27c7=lambda *a:'b',h27df=lambda g,o,c,r:good(g,c,r) and o=='b',
      h27db=lambda g,c,r,rule:good(g,c,r) and rule=='a',h27dc=lambda *a:codes[0],h7k=norm,
      h27b5=lambda c,r:seq(DOMAIN if(c,r)==('b','reference') else ()),
      dg=lambda a,t:a in DOMAIN and t=='end',df=lambda p,a,t:p=='a' and a in DOMAIN and t=='end',
      h26n2=lambda p,a,g,t:(p,g,t)==('a','a','end') and a in DOMAIN,
      h27dg=lambda p,r:p in DOMAIN and r=='reference',h27dh=lambda *a:False,
      h27di=lambda a,p,t:t=='end' and bit(deals,a,p),h27dj=lambda a,p,r,t:r=='reference',
      h27dk=lambda a,p,r,t:r=='reference' and bit(grounds,a,p),
      h27dl=lambda a,p,x,r,t:r=='reference' and x!=p and bit(substitutions,a,p))
    return v,names,codes,calls
def run(d,v):
    out=evaluate(d,v,DOMAIN,SCENES,True);assert out[:2]==[True,True];return out[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def standing_checks():
    d=fixture(('r6lg',),'q[k r6lg[k zperson[] k zreference[]]].');rows=0
    for positive,replacements,p in product(range(4),range(16),DOMAIN):
        v,_,_,_=model(d);v['zperson']=lambda p=p:p
        v['h27dg']=lambda x,r:bool(positive&(1<<DOMAIN.index(x))) and r=='reference'
        v['h27dh']=lambda x,y,r:bool(replacements&(1<<PAIRS.index((x,y)))) and r=='reference'
        expected=bool(positive&(1<<DOMAIN.index(p))) and not any(x!=p and replacements&(1<<PAIRS.index((p,x))) for x in DOMAIN)
        assert run(d,v)==[expected],(positive,replacements,p);rows+=1
    v,_,_,_=model(d);v['aa']=lambda *a:False;assert run(d,v)==[False]
    for n in ('h27dg','h27dh'):
        v,_,_,_=model(d);v[n]=unknown;rejects(d,v)
    return dict(all_128_positive_value_replacement_and_subject_rows=rows,self_identity_not_a_forbidden_replacement=True,
      no_capacity_achievement_or_utility_argument=True,unknown_rejected=True)

@lru_cache(None)
def public_dealing_checks():
    d=fixture(('r6lh','r6li'),'q[k r6lh['+ARGS+' k zactivity[] k zperson[] k zpoint[]]].q[k r6li[k zactivity[] k zperson[] k zreference[] k zpoint[]]].')
    v,_,_,_=model(d);assert run(d,v)==[True,True];cases={}
    for label in ('no_occurrence','no_agent','wrong_public_capacity','no_subject_contact','no_assessment','no_independent_ground','value_replaced','wrong_person','wrong_community','wrong_reference','wrong_point'):
        w,_,_,_=model(d)
        if label=='no_occurrence':w['dg']=lambda *a:False
        if label=='no_agent':w['df']=lambda *a:False
        if label=='wrong_public_capacity':w['h26n2']=lambda p,a,g,t:g=='b'
        if label=='no_subject_contact':w['h27di']=lambda *a:False
        if label=='no_assessment':w['h27dj']=lambda *a:False
        if label=='no_independent_ground':w['h27dk']=lambda *a:False
        if label=='value_replaced':w['h27dl']=lambda a,p,x,r,t:x!=p
        if label=='wrong_person':w['h27di']=lambda a,p,t:p=='a'
        if label=='wrong_community':w['zcommunity']=lambda:'a'
        if label=='wrong_reference':w['zreference']=lambda:'other'
        if label=='wrong_point':w['zpoint']=lambda:'start'
        result=run(d,w);assert not all(result),(label,result);cases[label]=result
    for n in ('df','h26n2','h27di','h27dj','h27dk','h27dl'):
        w,_,_,_=model(d);w[n]=unknown;rejects(d,w)
    return dict(native_occurrence_human_agent_public_capacity_and_same_subject=True,contrasts=cases,unknown_rejected=True)

@lru_cache(None)
def treatment_checks():
    d=fixture(('r6lk','r6ll'),'q[k r6lk['+ARGS+' k zpoint[]]].q[t[c[k r6ll['+ARGS+']][l[a][]]][k zpoint[]]].q[t[c[k r6ll['+ARGS+']][l[a][k za[]]]][k zpoint[]]].')
    rows=0
    for deals,grounds in product(range(16),repeat=2):
        v,_,_,_=model(d,deals,grounds);expected=(deals&~grounds)==0
        assert run(d,v)==[expected,expected,False],(deals,grounds);rows+=1
    for mask in range(16):
        v,_,_,_=model(d,substitutions=mask);assert run(d,v)==[mask==0,mask==0,False]
    cases={}
    for label in ('empty_people','omitted_person','duplicate_people','missing_value','replaceable_person','extra_bad_activity','no_actual_dealings','government_not_human'):
        v,_,_,_=model(d)
        if label=='empty_people':v['h27b5']=lambda *a:seq(());v['h237c']=lambda *a:False
        if label=='omitted_person':v['h27b5']=lambda *a:seq(('a',))
        if label=='duplicate_people':v['h27b5']=lambda *a:seq(('a','b','b'))
        if label=='missing_value':v['h27dg']=lambda p,r:p=='a'
        if label=='replaceable_person':v['h27dh']=lambda p,x,r:(p,x)==('b','a')
        if label=='extra_bad_activity':v['h27dk']=lambda a,p,r,t:a=='a'
        if label=='no_actual_dealings':v['dg']=lambda *a:False;v['h27dk']=lambda *a:False
        if label=='government_not_human':
            v['aa']=lambda p:p=='b';v['h237c']=lambda p,c,r:p=='b' and(c,r)==('b','reference');v['h27b5']=lambda *a:seq(('b',))
            v['df']=lambda p,a,t:p=='b' and t=='end';v['h26n2']=lambda p,a,g,t:(p,g,t)==('b','a','end')
        expected=label in ('no_actual_dealings','government_not_human');result=run(d,v)
        assert result==[expected,expected,False],(label,result);cases[label]=result
    return dict(all_256_contact_and_conformance_rows=rows,all_16_substitution_profiles=True,contrasts=cases,
      all_new_treatment_and_policy_bodies_native=True,empty_outer_binding_required=True)

@lru_cache(None)
def adoption_checks():
    d=fixture(('r6lo','r6lp','r6lq'),'q[k r6lo['+ARGS+' k zrule[]]].q[k r6lp['+ARGS+' k zrule[] k zpoint[]]].q[k r6lq['+ARGS+' k zrule[] k zpoint[]]].')
    v,names,codes,calls=model(d);assert run(d,v)==[True,True,True]
    assert calls and all(row[:3]==('a','a','b') and row[3]==codes[0] and row[4].items==() and row[5] for row in calls)
    cases={}
    for label in ('adopted_but_violated','conforms_not_adopted','same_extension_alias','wrong_name','wrong_rule','wrong_office'):
        v,names,codes,_=model(d)
        if label=='adopted_but_violated':v['h27dk']=lambda *a:False
        if label=='conforms_not_adopted':v['h7k']=lambda *a:False
        if label=='same_extension_alias':v['h27dc']=lambda *a:codes[1]
        if label=='wrong_name':v['h223g']=lambda p:names[1-DOMAIN.index(p)]
        if label=='wrong_rule':v['zrule']=lambda:'b'
        if label=='wrong_office':v['h27c7']=lambda *a:'a'
        result=run(d,v);expected=[True,True,False] if label=='adopted_but_violated' else [True,False,False] if label=='conforms_not_adopted' else [False,False,False]
        assert result==expected,(label,result);cases[label]=result
    # The closed concrete policy can be named/adopted without executing it.
    b=fixture(('r6lp',),'q[k r6lp['+ARGS+' k zrule[] k zpoint[]]].');v,_,_,_=model(b)
    for n in ('h27dg','h27dh','h27dk','h27dl'):v[n]=unknown
    assert run(b,v)==[True]
    # Direct execution of either syntactically distinct description has the
    # same extension, although only the exact target is accepted above.
    b=fixture(('r6ll',),'q[t[c[s[k r6lm[r[k za[]] r[k zb[]] r[k zref[]]]]][l[a][]]][k zpoint[]]].q[t[k zpolicyalias[l[a][]]][k zpoint[]]].')
    for grounds in (0,15):
        w,_,_,_=model(b,grounds=grounds);assert run(b,w)==[grounds==15,grounds==15]
    return dict(exact_target_and_norm_binding=True,contrasts=cases,same_extension_alias_executed_but_not_substituted=True,
      opaque_adoption_does_not_execute_concrete_content=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='concrete_non_substitutable_standing_and_public_treatment_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[1139,1172],text=u['text'][1139:1172],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      unresolved=['同じ政府自身の非事実的な有益さの判断','原則への因果作用、時間・強調、Wenn/so、著者注・全文帰属・通読判断'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,*ARTIFACTS)})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for prior in parents():
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    for row in read(ARTIFACTS[0])['sources']:
        assert digest((ROOT/ARTIFACT/row['raw']).read_bytes())==row['raw_sha256'];assert digest((ROOT/ARTIFACT/row['text']).read_bytes())==row['text_sha256']
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};text=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:1 if n in ('r6ln','r6lo','r6lp','r6lq') else 0 for n in MEANINGS},ranks
    assert not {'r6lc','r6km','r6kr','rx7','iatappraisal'}&set(c.entries)
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,
      imported_bodies_and_meanings_unchanged=True,no_capacity_or_utility_gate=True,roundtrips=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('standing',standing_checks),('public_dealings',public_dealing_checks),('treatment',treatment_checks),('adoption',adoption_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,*ARTIFACTS,
      'scripts/compose_dignity_conforming_treatment.py','scripts/check_dignity_conforming_treatment.py','tests/test_dignity_conforming_treatment.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='concrete_non_substitutable_standing_and_public_treatment_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
