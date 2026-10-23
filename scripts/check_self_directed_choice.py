"""Check positive acting/refraining goals, liberty background and stable capacity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from fractions import Fraction
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from noema.constructed_semantics import SequenceValue
from scripts.compose_self_directed_choice import ROOT,LIBRARY,BASIS,TRUE,FALSE,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/self-directed-choice-v1.md';READING='data/self-directed-choice-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v206.json'
ARTIFACT='artifacts/self-directed-choice-v1';PRIORS=('reports/civic-feedback-v1.json','reports/civic-intellectual-options-v1.json','reports/civic-disposition-profile-v1.json')
DOMAIN=('a','b');SCENES=('reference','other','anchor','normal','peer','exception','do','refrain')
CONSTANTS=dict(community='b',reference='reference',person='a',activity='b',anchor='anchor',point='normal')
FIELDS=tuple(CONSTANTS)[:4];ARGS=' '.join('k z'+n+'[]' for n in FIELDS)
CODE='i[h[a a] e]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def norm(c):return (c.rank,json.dumps(json.loads(c.syntax),sort_keys=True))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=('r6fr',)):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,(*roots,'r6kg'))
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    extra+='r zgrowthend[] d.r zexpected[] b.r zcapture['+CODE+' '+CODE+'] c.d zalias[person a activity a] e[k r6kg[v person v activity]].'
    return parse(format_graph(d,'compact')+extra+'q[k zcapture[r[p r6kg] r[p zalias]]].'+query)

def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*xs):codes[:]=xs;return True
    v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()});v['zcapture']=capture
    valid=lambda c,r,p,a:(c,r,p,a)==('b','reference','a','b')
    legal=('normal','peer','exception')
    def allowed(s,p,r,a,code,flag,t):return(s,p,r,a)==('a','a','b','b') and t in legal and norm(code)==norm(codes[0])
    def available(c,r,a,p,m,t):return valid(c,r,p,a) and m in DOMAIN and(t in('normal','peer') or(t=='exception' and m=='a'))
    def prospect(c,r,a,p,m,t,o):return available(c,r,a,p,m,t) and o==('do' if m=='a' else 'refrain')
    v.update(aa=lambda p:p=='a',h237c=lambda p,c,r:(p,c,r)==('a','b','reference'),h26yo=lambda c,p,a,r:valid(c,r,p,a),
      dg=lambda a,t:(a,t)==('b','do'),df=lambda p,a,t:(p,a,t)==('a','b','do'),
      ab=lambda f,p,t:(f,p)==('b','a') and t in ('do','refrain'),
      ac=lambda p,f,j,t:(p,f,j)==('a','b','b') and t in('do','refrain'),fa=lambda p,j,t:(p,j)==('a','b') and t in('do','refrain'),
      fb=lambda j,m,t:(j,m)==('b','b') and t in('do','refrain'),fc=lambda j,r,t:(j,r)==('b','a') and t in('do','refrain'),
      fd=lambda r,j,t:(r,j)==('a','b') and t in('do','refrain'),ad=lambda *a:False,
      h27cr=lambda p,a,j,sign,r,t:(p,a,j,r)==('a','b','b','reference') and t==('do' if sign else 'refrain'),
      h27cs=lambda p,j,a,sign,r,t:(p,j,a,r)==('a','b','b','reference') and t==('do' if sign else 'refrain'),
      h27cw=lambda *a:'b',r6fr=lambda c,o,r,t:(c,o,r)==('b','b','reference') and t in legal,
      h26yp=lambda o,c,r,t:'a' if(o,c,r)==('b','b','reference') else 'b',
      h26yq=lambda c,p,r:'b' if(c,p,r)==('b','a','reference') else 'a',h7a=lambda *a:False,h7b=allowed,
      h27cx=available,h27cy=prospect,h27cz=prospect,
      h27ct=lambda c,r,p,a,anchor,t:valid(c,r,p,a) and anchor=='anchor' and t in legal,
      h27cu=lambda c,r,p,a,anchor,t:valid(c,r,p,a) and anchor=='anchor' and t in legal,
      h27cv=lambda c,r,p,a,anchor,l,h:valid(c,r,p,a) and anchor=='anchor' and l in('normal','peer') and h=='exception')
    return v,codes
def run(d,v):
    xs=evaluate(d,v,DOMAIN,SCENES,True);assert xs[0] is True;return xs[1:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def goal_checks():
    q=''.join('q[t[k r6kh[k zperson[] k zactivity[] k zreference[] '+sign+']][k zpoint[]]].' for sign in (TRUE,FALSE))
    d=fixture(('r6kh',),q);v,_=model(d);rows={}
    for t,expected in (('do',[True,False]),('refrain',[False,True]),('anchor',[False,False])):
        w=dict(v);w['zpoint']=lambda t=t:t;assert run(d,w)==expected;rows[t]=expected
    cases={}
    for name in ('no_own_faculty','unsupported_reason','other_guidance','wrong_subject','no_conclusion','no_control','no_occurrence','other_actor','wrong_person','wrong_activity','wrong_reference'):
        w=dict(v);w['zpoint']=lambda:'do'
        if name=='no_own_faculty':w['ab']=lambda *a:False
        if name=='unsupported_reason':w['fd']=lambda *a:False
        if name=='other_guidance':w['ad']=lambda guide,p,j,t:guide!=p
        if name=='wrong_subject':w['fb']=lambda j,m,t:m=='a'
        if name=='no_conclusion':w['h27cr']=lambda *a:False
        if name=='no_control':w['h27cs']=lambda *a:False
        if name=='no_occurrence':w['dg']=lambda *a:False
        if name=='other_actor':w['df']=lambda p,a,t:p=='b'
        if name=='wrong_person':w['zperson']=lambda:'b'
        if name=='wrong_activity':w['zactivity']=lambda:'a'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        assert run(d,w)==[False,False],name;cases[name]=[False,False]
    for n in ('h27cr','h27cs','df','fd'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Intentionally refraining needs a positive deliberation/control, even when execution is false.
    w=dict(v);w['zpoint']=lambda:'refrain';w['h27cs']=lambda *a:False;assert run(d,w)==[False,False]
    return dict(native_signed_goals=rows,contrasts=cases,mere_nonexecution_not_refraining=True,unknown_rejected=True)

@lru_cache(None)
def liberty_checks():
    d=fixture(('r6ki',),'q[k r6ki['+ARGS+' k zpoint[]]].');v,cs=model(d);assert run(d,v)==[True];cases={}
    for name in ('only_positive_permission','only_negative_permission','positive_requirement','negative_requirement','wrong_source','wrong_role','wrong_code','wrong_order','wrong_community','wrong_reference','wrong_activity'):
        w=dict(v)
        if name=='only_positive_permission':w['h7b']=lambda *a:v['h7b'](*a) and a[-2]
        if name=='only_negative_permission':w['h7b']=lambda *a:v['h7b'](*a) and not a[-2]
        if name=='positive_requirement':w['h7a']=lambda *a:a[-2]
        if name=='negative_requirement':w['h7a']=lambda *a:not a[-2]
        if name=='wrong_source':w['h26yp']=lambda *a:'b'
        if name=='wrong_role':w['h26yq']=lambda *a:'a'
        if name=='wrong_code':w['h7b']=lambda s,p,r,a,c,flag,t:norm(c)==norm(cs[1])
        if name=='wrong_order':w['h27cw']=lambda *a:'a'
        if name=='wrong_community':w['zcommunity']=lambda:'a'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        if name=='wrong_activity':w['zactivity']=lambda:'a'
        assert run(d,w)==[False],name;cases[name]=False
    for n in ('h7a','h7b','h26yp','h27cw','r6fr'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(contrasts=cases,real_same_closed_execution_code=True,unknown_rejected=True,
      boundary='Only unchanged r6fr is a law-order boundary; its body is pinned by the prior civic review. Native rdm and both polarities, roles, actors, actions and code identity execute here.')

@lru_cache(None)
def opportunity_checks():
    q='q[k r6kj['+ARGS+' k zpoint[]]].q[k r6kk['+ARGS+' k zpoint[]]].'
    d=fixture(('r6kj','r6kk'),q);v,_=model(d);assert run(d,v)==[True,True];cases={}
    for name in ('only_act_method','only_refrain_method','no_methods','no_candidates','no_evaluated_results','evaluated_outside_candidates','uncontrolled_act','accidental_refrain','wrong_actor_methods','wrong_activity_methods','wrong_reference_methods'):
        w=dict(v)
        if name=='only_act_method':w['h27cx']=lambda *a:v['h27cx'](*a) and a[-2]=='a'
        if name=='only_refrain_method':w['h27cx']=lambda *a:v['h27cx'](*a) and a[-2]=='b'
        if name=='no_methods':w['h27cx']=lambda *a:False
        if name=='no_candidates':w['h27cy']=lambda *a:False
        if name=='no_evaluated_results':w['h27cz']=lambda *a:False
        if name=='evaluated_outside_candidates':w['h27cz']=lambda *a:a[-1]=='anchor'
        if name=='uncontrolled_act':w['h27cs']=lambda *a:v['h27cs'](*a) and not a[3]
        if name=='accidental_refrain':w['h27cs']=lambda *a:v['h27cs'](*a) and a[3]
        if name=='wrong_actor_methods':w['h27cx']=lambda c,r,a,p,m,t:p=='b'
        if name=='wrong_activity_methods':w['h27cx']=lambda c,r,a,p,m,t:a=='a'
        if name=='wrong_reference_methods':w['h27cx']=lambda c,r,a,p,m,t:r=='other'
        actual=run(d,w);assert actual[-1] is False,name;cases[name]=actual
    for n in ('h27cx','h27cy','h27cz','h27cs','fa'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Both goals use exactly the same providers and reference, actor and activity.
    calls=[]
    for n in ('h27cx','h27cy','h27cz'):
        old=v[n]
        def spy(*a,n=n,old=old):calls.append((n,a));return old(*a)
        v[n]=spy
    assert run(d,v)==[True,True]
    assert all(a[:4]==('b','reference','b','a') for _,a in calls)
    return dict(native_xd_xf_and_both_positive_goals=True,contrasts=cases,same_provider_scope=True,unknown_rejected=True)

@lru_cache(None)
def standing_checks():
    q='q[k r6kl['+ARGS+' k zanchor[]]].q[k r6km['+ARGS+' k zanchor[]]].'
    native=fixture(('r6kl','r6km'),q);v,_=model(native);assert run(native,v)==[True,True]
    # Actual anchor has no executed action and is not granted the comparison liberty.
    assert not v['dg']('b','anchor') and not v['r6fr']('b','b','reference','anchor')
    # At the exceptional candidate, refraining is unavailable, but the standing ability remains.
    d=fixture(('r6kl','r6km'),q,('r6kj','r6kk'));base,_=model(d)
    base['r6kj']=lambda *a:a==('b','reference','a','b','normal') or a==('b','reference','a','b','peer') or a==('b','reference','a','b','exception')
    rows=[]
    for mask in range(8):
        w=dict(base);w['r6kk']=lambda c,r,p,a,t: t in('normal','peer','exception') and bool(mask&(1<<('normal','peer','exception').index(t)))
        actual=run(d,w);assert actual==[True,mask&3==3];rows.append(dict(mask=mask,result=actual))
    base['r6kk']=lambda *a:a[-1] in('normal','peer')
    cases={}
    for name in ('empty_candidates','unpreserved','invalid_exception','priority_cycle','reflexive_priority','other_person','unknown_candidate','unknown_ability'):
        w=dict(base)
        if name=='empty_candidates':w['h27ct']=lambda *a:False
        if name=='unpreserved':w['h27cu']=lambda *a:False
        if name=='invalid_exception':w['r6kj']=lambda *a:a[-1]!='exception'
        if name=='priority_cycle':w['h27cv']=lambda *a:a[-2]!=a[-1]
        if name=='reflexive_priority':w['h27cv']=lambda *a:a[-2]==a[-1]
        if name=='other_person':w['zperson']=lambda:'b'
        if name=='unknown_candidate':w['h27ct']=unknown;rejects(d,w);cases[name]='rejected';continue
        if name=='unknown_ability':w['r6kk']=unknown;rejects(d,w);cases[name]='rejected';continue
        actual=run(d,w);assert actual==[False,False],name;cases[name]=actual
    # Explicit function-value binding check; no exponential rerun of the lower body.
    q='q[t[c[k r6kn[k zcommunity[] k zreference[]]][k zperson[] k zactivity[]]][k zanchor[]]].'
    d=fixture(('r6kn',),q,('r6km',));v,_=model(d);calls=[]
    def ability(*a):calls.append(a);return a==('b','reference','a','b','anchor')
    v['r6km']=ability
    for c,r,p,a,t in product(DOMAIN,('reference','other'),DOMAIN,DOMAIN,('anchor','normal')):
        w=dict(v)
        for n,x in zip(('community','reference','person','activity','anchor'),(c,r,p,a,t)):w['z'+n]=lambda x=x:x
        calls.clear();assert run(d,w)==[(c,r,p,a,t)==('b','reference','a','b','anchor')];assert(c,r,p,a,t)in calls
    return dict(native_standing_capacity=True,actual_permission_and_execution_not_required=True,normal_ability_rows=rows,contrasts=cases,all_32_content_family_bindings=True,
      boundary='Native r6kl/r6km execute once with native xd/xf and goals. The truth-table replaces only r6kj/r6kk, checked separately above; the final binding oracle replaces only r6km.')

def growth_model(d,values=(0,1,3),bound=1,weights=(1,1,1,1)):
    v,_=model(d);v.update(arithmetic());pairs=tuple(product(DOMAIN,repeat=2))
    times=('anchor','normal','peer') if len(values)==3 else ('anchor','normal','exception','peer') if len(values)==4 else ('anchor','normal','exception','do','peer')
    valid=lambda c,r:(c,r)==('b','reference')
    v.update(zgrowthend=lambda:'peer',aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:valid(c,r),
      h26yo=lambda c,p,a,r:valid(c,r),h27b5=lambda c,r:SequenceValue(DOMAIN,'"individual"'),
      h27c2=lambda c,r,p:SequenceValue(DOMAIN,'"individual"'),h27c3=lambda c,r,p,a:Fraction(weights[pairs.index((p,a))]),h27c4=lambda c,r:Fraction(bound),
      h27ch=lambda c,r,s,e,t:valid(c,r) and(s,e)==('anchor','peer') and t in times,
      h27ci=lambda c,r,s,e,l,h:valid(c,r) and(s,e)==('anchor','peer') and l in times and h in times and times.index(l)<times.index(h),
      r6kl=lambda c,r,p,a,t:valid(c,r) and(p,a)in pairs and t in times,
      r6km=lambda c,r,p,a,t:valid(c,r) and(p,a)in pairs and t in times and bool(values[times.index(t)]&(1<<pairs.index((p,a)))))
    return v

def expected_growth(values,bound):
    scores=[x.bit_count() for x in values]
    def middle(i,j):return any(min(scores[i],scores[j])<scores[k]<max(scores[i],scores[j]) for k in range(i+1,j))
    return bool(bound>0 and scores[0]<scores[-1] and middle(0,len(scores)-1) and all(abs(scores[i]-scores[j])<=bound or middle(i,j) for i in range(len(scores)) for j in range(i+1,len(scores))))

@lru_cache(None)
def growth_checks():
    q='q[k r6kq[k zcommunity[] k zreference[] k zanchor[] k zgrowthend[]]].q[k r6kr[k zcommunity[] k zreference[] k zanchor[] k zgrowthend[]]].'
    d=fixture(('r6kq','r6kr'),q,('r6kl','r6km'));rows=0
    for values in product(range(4),repeat=3):
        v=growth_model(d,values);assert run(d,v)==[True,expected_growth(values,1)],values;rows+=1
    cases={}
    for label,values,bound in (('plateau',(0,1,1,3),1),('local_loss',(0,1,0,1,3),1),('decline',(3,1,0),1),
      ('single_jump',(0,0,3),1),('same_score_exchange',(1,2,4),1),('one_person_improves',(0,1,3),1),('different_people_improve',(0,1,5),1),('zero_bound',(0,1,3),0)):
        v=growth_model(d,values,bound);actual=run(d,v);assert actual==[True,expected_growth(values,bound)],label;cases[label]=actual
    v=growth_model(d)
    for name in ('omitted_person','duplicate_action','zero_weight','unassessed_middle','missing_end','reversed_time'):
        w=dict(v)
        if name=='omitted_person':w['h27b5']=lambda *a:SequenceValue(('a',),'"individual"')
        if name=='duplicate_action':w['h27c2']=lambda *a:SequenceValue(('a','b','b'),'"individual"')
        if name=='zero_weight':w['h27c3']=lambda *a:Fraction(0 if a[-2:]==('b','b') else 1)
        if name=='unassessed_middle':w['r6kl']=lambda c,r,p,a,t:v['r6kl'](c,r,p,a,t) and not(p=='b' and a=='a' and t=='normal')
        if name=='missing_end':w['h27ch']=lambda *a:v['h27ch'](*a) and a[-1]!='peer'
        if name=='reversed_time':w['h27ci']=lambda c,r,s,e,l,h:v['h27ci'](c,r,s,e,h,l)
        assert run(d,w)==[False,False],name;cases[name]=[False,False]
    for n in ('r6kl','r6km','h27c2','h27c3','h27c4','h27ch'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    q='q[e[k r6kp[k zcommunity[] k zreference[] k zpoint[]]][k zexpected[]]].'
    d=fixture(('r6kp',),q,('r6km',));weights=(Fraction(1,2),1,2,3)
    for mask in range(16):
        v=growth_model(d,(0,mask,mask),weights=weights);v['zexpected']=lambda mask=mask:sum((Fraction(w) for i,w in enumerate(weights) if mask&(1<<i)),Fraction(0))
        assert run(d,v)==[True]
    # Check the content wrapper separately from the native aggregate body.
    q='q[t[k r6ks[k zcommunity[] k zreference[] k zanchor[]]][k zpoint[]]].'
    d=fixture(('r6ks',),q,('r6kr',));v,_=model(d);calls=[]
    def body(*a):calls.append(a);return a==('b','reference','anchor','normal')
    v['r6kr']=body
    for c,r,s,e in product(DOMAIN,('reference','other'),('anchor','normal'),('normal','peer')):
        w=dict(v)
        for n,x in zip(('community','reference','anchor','point'),(c,r,s,e)):w['z'+n]=lambda x=x:x
        calls.clear();assert run(d,w)==[(c,r,s,e)==('b','reference','anchor','normal')];assert(c,r,s,e)in calls
    return dict(independent_64_paths=rows,all_16_unequally_weighted_profiles=True,contrasts=cases,all_16_content_bindings=True,unknown_rejected=True,
      boundary='Only r6kl/r6km are ability boundaries in aggregate checks. Their native bodies execute above. Inventory, positive weights, full intervals, score and gradual increase execute natively; the content wrapper separately bounds r6kr.')

def artifacts():return sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/ARTIFACT).iterdir() if p.is_file())
def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
    return dict(status='self_directed_choice_capacity_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[931,1000],text=u['text'][931:1000],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      lexical_comparison=dict(url=read(ARTIFACT+'/fetch.json')['url'],artifact=ARTIFACT+'/religion-188.txt',role='later_comparison_not_unique_1784_definition'),
      unresolved=['同じ心的変化によるwodurchの媒介','Wenn/so全体・政府原則以降・全文帰属'],
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
    r=read(ARTIFACT+'/fetch.json')
    for ext in ('html','text'):assert digest((ROOT/ARTIFACT/r[ext]).read_bytes())==r[ext+'_sha256']
    text=format_graph(c.document,'compact')
    for n in MEANINGS:parse(text+'q[e[r[p '+n+']][r[p '+n+']]].')
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks={n:0 for n in MEANINGS},
      imported_bodies_and_meanings_unchanged=True,roundtrips=True,source_snapshot_verified=True,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('goals',goal_checks),('liberty',liberty_checks),('opportunity',opportunity_checks),('standing',standing_checks),('growth',growth_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,*artifacts(),
      'scripts/compose_self_directed_choice.py','scripts/check_self_directed_choice.py','tests/test_self_directed_choice.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='reason_directed_standing_choice_capacity_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
