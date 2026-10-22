"""Check native dispositions and independent weighted trajectory oracles."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_disposition_profile import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/civic-disposition-profile-v1.md';READING='data/civic-disposition-profile-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
ARTIFACT='artifacts/civic-disposition-profile-v1'
PRIORS=('reports/germ-figurative-connection-v1.json','reports/cohort-response-v1.json','reports/thinking-impulse-development-v1.json')
DOMAIN=('a','b');PAIRS=tuple(product(DOMAIN,repeat=2));TIMES=('start','middle','end')
SCENES=(*TIMES,'hold','later','outside','reference','other',*('probe'+str(i) for i in range(5)),'peer','exception')
CONSTANTS=dict(community='b',reference='reference',person='a',feature='a',anchor='end',start='start',end='end',left='start',right='end',point='end')
SCOPE='k zcommunity[] k zreference[]';PAIR=SCOPE+' k zperson[] k zfeature[]';SPAN=SCOPE+' k zstart[] k zend[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+extra+query)

def model(d,profile=(0,1,3),weights=(1,1,1,1),bound=1):
    times=('start','middle','end') if len(profile)==3 else ('start','middle','hold','end') if len(profile)==4 else ('start','middle','hold','later','end')
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update(arithmetic());v.update({'z'+n:lambda v=v:v for n,v in CONSTANTS.items()})
    valid=lambda c,r:(c,r)==('b','reference')
    pair=lambda c,r,p,f:valid(c,r) and (p,f) in PAIRS
    def candidate(c,r,p,f,a,s):
        return pair(c,r,p,f) and a in times and s in ('probe'+str(times.index(a)),*(['peer','exception'] if a=='end' else []))
    def response(c,r,p,f,s):
        if not pair(c,r,p,f):return False
        i=times.index('end') if s=='peer' else int(s[5:]) if s.startswith('probe') and int(s[5:])<len(profile) else None
        return i is not None and bool(profile[i]&(1<<PAIRS.index((p,f))))
    v.update(aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:valid(c,r) and p in DOMAIN,
      h27b5=lambda c,r:seq(DOMAIN if valid(c,r) else ()),h27b6=lambda c,r,p:seq(DOMAIN if valid(c,r) and p in DOMAIN else ()),
      h27b7=pair,h27ca=candidate,h27cb=candidate,h27ce=candidate,
      h27cc=lambda c,r,p,f,s:pair(c,r,p,f) and s in tuple('probe'+str(i) for i in range(len(profile)))+('peer','exception'),
      h27cd=lambda c,r,p,f,a,l,h:candidate(c,r,p,f,a,l) and candidate(c,r,p,f,a,h) and a=='end' and l in ('probe'+str(len(profile)-1),'peer') and h=='exception',
      h27cf=response,h27cg=lambda c,r,p,f:Fraction(weights[PAIRS.index((p,f))]) if pair(c,r,p,f) else Fraction(0),
      h27ch=lambda c,r,s,e,t:valid(c,r) and(s,e)==('start','end') and t in times,
      h27ci=lambda c,r,s,e,l,h:valid(c,r) and(s,e)==('start','end') and l in times and h in times and times.index(l)<times.index(h),
      h27cj=lambda c,r:Fraction(bound) if valid(c,r) else Fraction(0))
    if 'r6jy' in v:v['r6jy']=lambda c,r,p,f,t:pair(c,r,p,f) and t in times and bool(profile[times.index(t)]&(1<<PAIRS.index((p,f))))
    if 'r6jx' in v:v['r6jx']=lambda c,r,p,f,t:pair(c,r,p,f) and t in times
    v['_scenes']=(*times,'reference','other','outside',*(tuple('probe'+str(i) for i in range(len(profile)))+('peer','exception') if 'h27ca' in v else ()))
    return v,times

def run(d,v):return evaluate(d,v,DOMAIN,v['_scenes'],True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def disposition_checks():
    d=fixture(('r6jx','r6jy'),'q[k r6jx['+PAIR+' k zanchor[]]].q[k r6jy['+PAIR+' k zanchor[]]].')
    v,_=model(d);v['_scenes']=('start','end','reference','other','probe2','peer','exception');assert run(d,v)==[True,True]
    rows=[]
    for mask in range(8):
        w=dict(v);w['h27cf']=lambda c,r,p,f,s: s in ('probe2','peer','exception') and bool(mask&(1<<('probe2','peer','exception').index(s)))
        actual=run(d,w);assert actual==[True,mask&3==3];rows.append(dict(mask=mask,result=actual))
    cases={}
    for name in ('empty_candidates','missing_preservation','missing_trigger','missing_classification','reflexive_priority','priority_cycle','no_normal_response','wrong_person','wrong_feature','wrong_reference'):
        w=dict(v)
        if name=='empty_candidates':w['h27ca']=lambda *a:False
        if name=='missing_preservation':w['h27cb']=lambda *a:False
        if name=='missing_trigger':w['h27cc']=lambda *a:False
        if name=='missing_classification':w['h27ce']=lambda *a:False
        if name=='reflexive_priority':w['h27cd']=lambda *a:a[-1]==a[-2]
        if name=='priority_cycle':w['h27cd']=lambda *a:a[-1]!=a[-2]
        if name=='no_normal_response':w['h27cf']=lambda *a:a[-1]=='exception'
        if name=='wrong_person':w['h237c']=lambda p,c,r:p=='b'
        if name=='wrong_feature':w['h27b7']=lambda c,r,p,f:f=='b'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        out=run(d,w);assert out[-1] is False,name;cases[name]=out
    for n in ('h27ca','h27cb','h27cc','h27cd','h27ce','h27cf'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # A response at the actual anchor is neither needed nor enough.
    w=dict(v);w['h27cf']=lambda *a:a[-1]=='end';assert run(d,w)==[True,False]
    q='q[t[c[k r6j6['+SCOPE+']][k zperson[] k zfeature[]]][k zpoint[]]].'
    d=fixture(('r6j6',),q);v,_=model(d);v['_scenes']=('start','end','reference','other','probe2','peer','exception');assert run(d,v)==[True]
    d=fixture(('r6j6',),q,('r6jy',));v,_=model(d)
    for c,r,p,f,t in product(DOMAIN,('reference','other'),DOMAIN,DOMAIN,('start','end')):
        w=dict(v)
        for n,x in zip(('community','reference','person','feature','point'),(c,r,p,f,t)):w['z'+n]=lambda x=x:x
        expected=(c,r,t)==('b','reference','end') and p=='a'
        assert run(d,w)==[expected],(c,r,p,f,t)
    return dict(normal_response_rows=rows,contrasts=cases,unknown_rejected=True,actual_anchor_response_not_required=True,content_family_all_32_bindings=True,
      boundary='Only the 32-row content-family binding oracle replaces r6jy. Native content application and native dispositions execute separately.')

@lru_cache(None)
def inventory_checks():
    d=fixture(('r6jz',),'q[k r6jz['+SCOPE+']].');v,_=model(d);assert run(d,v)==[True];cases={}
    for name in ('empty_people','omitted_person','duplicate_person','empty_features','omitted_feature','duplicate_feature','nonhuman','zero_weight','negative_weight','bad_indicator'):
        w=dict(v)
        if name=='empty_people':w['h27b5']=lambda *a:seq(())
        if name=='omitted_person':w['h27b5']=lambda *a:seq(('a',))
        if name=='duplicate_person':w['h27b5']=lambda *a:seq(('a','a','b'))
        if name=='empty_features':w['h27b6']=lambda *a:seq(())
        if name=='omitted_feature':w['h27b6']=lambda *a:seq(('a',))
        if name=='duplicate_feature':w['h27b6']=lambda *a:seq(('a','b','b'))
        if name=='nonhuman':w['aa']=lambda p:p=='a'
        if name=='zero_weight':w['h27cg']=lambda *a:Fraction(0 if a[-2:]==('b','b') else 1)
        if name=='negative_weight':w['h27cg']=lambda *a:Fraction(-1 if a[-2:]==('b','b') else 1)
        if name=='bad_indicator':w.update(arithmetic(True))
        assert run(d,w)==[False],name;cases[name]=False
    w=dict(v);w['h27b5']=lambda *a:seq(reversed(DOMAIN));w['h27b6']=lambda *a:seq(reversed(DOMAIN));assert run(d,w)==[True]
    for n in ('h237c','h27b5','h27b6','h27b7','h27cg'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(contrasts=cases,order_independent=True,unknown_rejected=True)

def distance(a,b,weights):return sum((Fraction(w) for i,w in enumerate(weights) if (a^b)&(1<<i)),Fraction(0))
@lru_cache(None)
def distance_checks():
    q='r zexpected[] b.q[e[k r6j2['+SCOPE+' k zleft[] k zright[]]][k zexpected[]]].'
    d=fixture(('r6j2',),q,('r6jy',));weights=(Fraction(1,2),1,2,3);rows=0
    for a,b in product(range(16),repeat=2):
        v,_=model(d,(a,0,b),weights);v['zexpected']=lambda a=a,b=b:distance(a,b,weights);assert run(d,v)==[True];rows+=1
    # Equal numbers of true components are not equal profiles.
    assert distance(1,2,(1,1,1,1))==2
    # The same construction executes native dispositions, not just an oracle stub.
    d=fixture(('r6j2',),q)
    v,_=model(d,(1,3,2),weights);v['zexpected']=lambda:Fraction(3,2);assert run(d,v)==[True]
    v['h27cf']=unknown;rejects(d,v)
    return dict(independent_all_256_profile_pairs=True,weighted_rows=rows,same_true_count_swap_detected=True,native_distance=Fraction(3,2).__str__(),boundary='Only the 256-row numeric oracle replaces r6jy; the separate distance and trajectory examples execute its native body.')

def gradual(profile,weights,bound):
    dist=lambda i,j:distance(profile[i],profile[j],weights)
    def middle(i,j):return any(0<dist(i,k)<dist(i,j) and 0<dist(k,j)<dist(i,j) for k in range(i+1,j))
    return bool(bound>0 and dist(0,len(profile)-1)>0 and middle(0,len(profile)-1) and all(dist(i,j)<=bound or middle(i,j) for i in range(len(profile)) for j in range(i+1,len(profile))))

@lru_cache(None)
def trajectory_checks():
    q=''.join('q[k '+n+'['+SPAN+']].' for n in ('r6j3','r6j4','r6j5'))
    d=fixture(('r6j3','r6j4','r6j5'),q,('r6jx','r6jy'));rows=0
    for profile in product(range(4),repeat=3):
        v,_=model(d,profile);expect=[True,profile[0]!=profile[-1],gradual(profile,(1,1,1,1),1)]
        assert run(d,v)==expect,(profile,run(d,v),expect);rows+=1
    examples={}
    for label,profile,bound in (
      ('growth',(0,1,3),1),('decline',(3,1,0),1),('swap_same_count',(1,3,2),1),
      ('plateau',(0,1,1,3),1),('local_reversal',(0,1,0,1,3),1),('hidden_jump',(0,0,3),1),
      ('single_change',(0,0,1),1),('no_net_change',(0,1,0),1),('too_small_bound',(0,1,3),Fraction(1,2)),
      ('zero_bound',(0,1,3),0),('jump_with_middle_elsewhere',(0,1,7),1)):
        v,_=model(d,profile,bound=bound);out=run(d,v);assert out==[True,profile[0]!=profile[-1],gradual(profile,(1,1,1,1),bound)],(label,out)
        examples[label]=out
    assert examples['decline'][-1] and examples['swap_same_count'][-1] and examples['local_reversal'][-1]
    # Every conjunct also executes with real normal alternatives and responses.
    native=fixture(('r6j3','r6j4','r6j5'),q);v,_=model(native);assert run(native,v)==[True,True,True]
    w=dict(v);w['h27ce']=lambda c,r,p,f,a,s:v['h27ce'](c,r,p,f,a,s) and not (p=='b' and f=='b' and a=='middle')
    assert run(native,w)==[False,False,False]
    v,_=model(d)
    cases={}
    for name in ('missing_middle_assessment','missing_second_person','wrong_history','missing_endpoint','reflexive_time','empty_normal_middle','unknown_response'):
        w=dict(v)
        if name=='missing_middle_assessment':w['r6jx']=lambda c,r,p,f,a:v['r6jx'](c,r,p,f,a) and not (p=='b' and f=='b' and a=='middle')
        if name=='missing_second_person':w['h27b5']=lambda *a:seq(('a',))
        if name=='wrong_history':w['h27ci']=lambda *a:False
        if name=='missing_endpoint':w['h27ch']=lambda *a:v['h27ch'](*a) and a[-1]!='end'
        if name=='reflexive_time':w['h27ci']=lambda *a:v['h27ci'](*a) or a[-1]==a[-2]
        if name=='empty_normal_middle':w['r6jx']=lambda c,r,p,f,a:a!='middle' and v['r6jx'](c,r,p,f,a)
        if name=='unknown_response':w['r6jy']=unknown;rejects(d,w);cases[name]='rejected';continue
        out=run(d,w);assert out==[False,False,False],(name,out);cases[name]=out
    for n in ('h27ch','h27ci','h27cj','h27cg'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(independent_64_three_point_paths=rows,examples=examples,native_contrasts=cases,unknown_rejected=True,
      boundary='Trajectory oracle and structural contrasts replace only r6jx/r6jy. Native inventory, weighted folds, order, interval and intermediate constraints execute throughout. A full native success and missing second-person intermediate assessment execute all native dispositions too.')

def artifacts():return sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/ARTIFACT).iterdir() if p.is_file())
def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='empirical_civic_dispositions_and_change_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[871,931],text=u['text'][871:931],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      lexical_sources=[dict(url=r['url'],artifact=ARTIFACT+'/'+r['text'],role='lexical_comparison_not_unique_1784_definition') for r in read(ARTIFACT+'/fetch.json')['sources']],
      rejected_shortcuts=['Sinnesartを理由ある独立判断の成功件数だけへ還元する','各人の変化を失わない強い単調性を原文の必須条件とする','プロフィールの変化だけから前件の因果的作用を導く'],
      unresolved=['同じ前件からの因果的寄与とzurükの戻り先','作用過程の漸進性・人口・時点への量化','行為能力・政府原則・自己利益・機械以上の人間・尊厳・著者注'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS,*artifacts())})

@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    for row in read(ARTIFACT+'/fetch.json')['sources']:
        for ext in ('html','text'):assert digest((ROOT/ARTIFACT/row[ext]).read_bytes())==row[ext+'_sha256']
    text=format_graph(c.document,'compact')
    for n in MEANINGS:parse(text+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks={n:0 for n in MEANINGS},
      inherited_bodies_and_meanings_unchanged=True,roundtrips=True,source_artifacts_verified=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('disposition',disposition_checks),('inventory',inventory_checks),('distance',distance_checks),('trajectory',trajectory_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,*artifacts(),
      'scripts/compose_civic_disposition_profile.py','scripts/check_civic_disposition_profile.py','tests/test_civic_disposition_profile.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='fixed_empirical_disposition_profile_and_trajectory_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
