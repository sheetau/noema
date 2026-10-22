"""Check complete religious choice, exact policy duty and nonfactive self-judgment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_religious_freedom_policy import ROOT,LIBRARY,BASIS,PARENT,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure,DUTY_NAMES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

INDEX='data/semantic-review-index-v196.json';REPORT='reports/religious-freedom-policy-v1.json'
READING='data/religious-freedom-policy-reading-v1.json';DOC='docs/religious-freedom-policy-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
SOURCES=('artifacts/judgment-performance-quality-v1/kant-aa08-040.html','artifacts/royal-writing-oversight-v1/page-491.jpg')
PRIORS=('reports/personal-religious-remit-v1.json','reports/religious-collective-assessment-v1.json','reports/seventh-paragraph-v1.json')
DOMAIN=('actor','person','otherperson','group','community','topic','work','otherwork','role','source','event','other')
SCENES=('reference','now','otherpoint')
z=lambda n:'k z'+n+'[]'
EXTRA=''.join('r z'+n+'[] '+t+'.' for names,t in ((DOMAIN,'a'),(SCENES,'d')) for n in names)+'r zbindings[] j[a].'
PROVIDERS='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d i[d] i[d] i[d]] i[d].'
PROVIDERS+='r zcontentpick[a d i[e] i[e]] i[e].r ztruth[a d] c.r zinspect[i d[e]] c.'
PROVIDERS+='d zfirstbody[] e[b point[k ztruth['+z('work')+' v point]]].d zsecondbody[] e[b point[k ztruth['+z('otherwork')+' v point]]].'
PROVIDERS+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
PROVIDERS+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
PROVIDERS+='d h246e[item a reference d] i[e][k zcontentpick[v item v reference r[k zfirstbody[]] r[k zsecondbody[]]]].'
ARGS=' '.join(z(n) for n in ('actor','person','community','work','topic','reference'))
PARGS=' '.join(z(n) for n in ('actor','group','community','topic','reference'))
DNAMES=('source','actor','role','group','community','topic','reference')
DARGS=' '.join(z(n) for n in DNAMES)
CODE='k r5wc['+' '.join('r['+z(n)+']' for n in DNAMES)+']'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),providers=False):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    prefix=parse('p:'+EXTRA+(PROVIDERS if providers else ''))
    replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h','h246e')}
    d['declarations']=[x for x in prefix['declarations'] if x['name'] not in replacements]+[replacements.get(x['name'],x) for x in d['declarations']]
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p in ('actor','person','otherperson'),h26j7=lambda t,r:(t,r)==('topic','reference'),
        h26hk=lambda w,p,r:w in ('work','otherwork') and p in ('person','otherperson') and r=='reference',
        h26nc=lambda p,w,t,r:p in ('person','otherperson') and w in ('work','otherwork') and (t,r)==('topic','reference'),
        h246c=lambda g,p,r:(g,r)==('group','reference') and p in ('person','otherperson'),
        h26hn=lambda p,c,r:'role' if (c,r)==('community','reference') else 'other',
        h237z=lambda *a:False,h245c=lambda *a:True,h26ho=lambda *a:False,
        dg=lambda event,point:(event,point)==('event','now'),df=lambda actor,event,point:(actor,event,point)==('actor','event','now'),
        h26nd=lambda a,p,c,w,t,r,s:(a,c,t,r,s)==('actor','community','topic','reference','now'),
        znamepick=lambda obj,*codes:codes[DOMAIN.index(obj)],zrefpick=lambda point,*codes:codes[SCENES.index(point)],
        zcontentpick=lambda w,r,first,second:first if w=='work' else second)
    return v

@lru_cache(None)
def content_checks():
    q='q[t[k r5vx[k zbindings[] '+z('reference')+']]['+z('now')+']].'
    d=fixture(('r5vx',),q,providers=True);rows={}
    for variant in ('baseline','not_human','not_religion','not_personal','unrelated','not_performed','other_person','missing','extra'):
        v=base(d);items=('person','work','topic');v['ztruth']=lambda w,s:(w,s)==('work','now') and variant!='not_performed'
        if variant=='not_human':v['aa']=lambda *a:False
        if variant=='not_religion':v['h26j7']=lambda *a:False
        if variant=='not_personal':v['h26hk']=lambda *a:False
        if variant=='unrelated':v['h26nc']=lambda *a:False
        if variant=='other_person':items=('other','work','topic')
        if variant=='missing':items=items[:-1]
        if variant=='extra':items=(*items,'other')
        v['zbindings']=lambda:SequenceValue(items,'"individual"')
        got=run(d,v);assert got==[variant=='baseline'],(variant,got);rows[variant]=got[0]
    for n in ('h26nc','h26hk','h26j7','ztruth'):
        v=base(d);v['zbindings']=lambda:SequenceValue(('person','work','topic'),'"individual"');v['ztruth']=lambda *a:True;v[n]=unknown;rejects(d,v)
    return dict(cases=rows,native_described_undertaking_evaluated_only_when_requested=True,unknown_rejected=True)

@lru_cache(None)
def norm_checks():
    d=fixture(('r5vz','r5v2'),'q[k r5vz['+ARGS+' '+z('now')+']].q[k r5v2['+ARGS+' '+z('now')+']].');rows=[]
    key=('actor','person','role',('r5vx',1),('person','work','topic'),'reference','now')
    def relation(a,flags):
        source,p,role,code,b,r,sign,s=a
        return normalized((source,p,role,code,b,r,s))==key and flags[0 if sign else 1]
    for positive,negative,permit,abstain in product((False,True),repeat=4):
        v=base(d);v['h237z']=lambda *a:relation(a,(positive,negative));v['h245c']=lambda *a:relation(a,(permit,abstain))
        got=run(d,v);assert got==[not(positive or negative),not(positive or negative) and permit and abstain]
        rows.append(dict(require=[positive,negative],permit=[permit,abstain],result=got))
    mismatches=0
    for pos in range(len(key)):
        wanted=list(key);wanted[pos]='other';wanted=tuple(wanted);v=base(d)
        def wrong(*a):return normalized((*a[:6],a[7]))==wanted
        v['h245c']=wrong;assert run(d,v)==[True,False]
        v['h245c']=lambda *a:True;v['h237z']=wrong;assert run(d,v)==[True,True];mismatches+=1
    for n in ('h237z','h245c'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(polarity_cases=rows,argument_mismatches=mismatches,both_permissions_needed=True,quoted_conduct_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def interference_checks():
    q='q[k r5v3['+ARGS+' '+z('event')+' '+z('now')+']].q[k r5v4['+ARGS+' '+z('now')+']].'
    d=fixture(('r5v3','r5v4'),q);rows={}
    key=('event','person',('r5vy',1),('person','community','work','topic','role'),'reference','now')
    variants=('baseline','no_intervention','not_occurring','other_actor','other_event','no_permission',*('wrong'+str(i) for i in range(len(key))))
    for variant in variants:
        v=base(d);wanted=list(key)
        if variant.startswith('wrong'):wanted[int(variant[5:])]='other'
        v['h26ho']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_intervention'
        if variant=='not_occurring':v['dg']=lambda *a:False
        if variant=='other_actor':v['df']=lambda a,e,s:(a,e,s)==('other','event','now')
        if variant=='other_event':v['df']=lambda a,e,s:(a,e,s)==('actor','other','now')
        if variant=='no_permission':v['h245c']=lambda *a:False
        target=variant in ('baseline','no_permission');free=not target and variant!='no_permission'
        got=run(d,v);assert got==[target,free],(variant,got);rows[variant]=got
    for n in ('dg','df','h26ho'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,native_same_event_actor_role_and_undertaking=True,unknown_rejected=True)

@lru_cache(None)
def policy_checks():
    q='q[t[k r5v6['+PARGS+']]['+z('now')+']].q[t[k r5v7['+PARGS+']]['+z('now')+']].'
    d=fixture(('r5v6','r5v7'),q);rows={}
    variants=('baseline','one_choice_forbidden','one_choice_required','one_choice_unpermitted','one_choice_interfered',
        'empty_group','nonhuman_member','empty_person_scope','one_unassessed','no_current_execution','nonmember_rule','other_role_rule','other_point_rule')
    for variant in variants:
        v=base(d)
        def chosen(a):return a[1]=='otherperson' and normalized(a[4])==('otherperson','otherwork','topic')
        if variant in ('one_choice_forbidden','one_choice_required'):
            v['h237z']=lambda *a:chosen(a) and a[6]==(variant=='one_choice_required')
        if variant=='one_choice_unpermitted':v['h245c']=lambda *a:not(chosen(a) and a[6])
        if variant=='one_choice_interfered':v['h26ho']=lambda event,p,code,b,r,s:normalized((event,p,code,b,r,s))==('event','otherperson',('r5vy',1),('otherperson','community','otherwork','topic','role'),'reference','now')
        if variant=='empty_group':v['h246c']=lambda *a:False
        if variant=='nonhuman_member':v['aa']=lambda p:p!='otherperson'
        if variant=='empty_person_scope':v['h26nc']=lambda p,w,t,r:p=='person' and w in ('work','otherwork') and (t,r)==('topic','reference')
        if variant=='one_unassessed':v['h26nd']=lambda a,p,c,w,t,r,s:not(p=='otherperson' and w=='otherwork')
        if variant=='no_current_execution':v['ztruth']=lambda *a:False
        if variant=='nonmember_rule':v['h237z']=lambda s,p,*a:p=='actor'
        if variant=='other_role_rule':v['h237z']=lambda s,p,role,*a:role=='other'
        if variant=='other_point_rule':v['h237z']=lambda *a:a[-1]=='reference'
        want=[True,True]
        if variant in ('one_choice_forbidden','one_choice_required','empty_group','nonhuman_member','empty_person_scope','one_unassessed'):want=[False,False]
        if variant in ('one_choice_unpermitted','one_choice_interfered'):want=[True,False]
        got=run(d,v);assert got==want,(variant,got);rows[variant]=got
    for n in ('h246c','h26nc','h26nd','h237z','h245c','h26ho'):
        v=base(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,native_all_people_all_choices=True,nonprescription_weaker_than_full_freedom=True,
        fixed_reference_and_unexecuted_undertakings=True,unknown_rejected=True)

@lru_cache(None)
def duty_checks():
    q='q[k zinspect['+CODE+']].q[t[k r5wb['+DARGS+']]['+z('now')+']].q[t[s['+CODE+']]['+z('now')+']].q[k r5we['+DARGS+' '+z('now')+']].q[t[k r5v7['+PARGS+']]['+z('now')+']].'
    d=fixture(('r5wb','r5wc','r5we','r5v7'),q,providers=True);rows=[]
    normkey=('source','actor','role',('r5wa',2),('actor','group','community','topic'),'reference',True,'now')
    def values(duty,belief,policy):
        v=base(d);seen=[]
        v['zinspect']=lambda code:seen.append((code.rank,code.syntax)) is None
        v['h26ne']=lambda *a:duty and normalized(a)==normkey
        v['h26nf']=lambda person,code,point:belief and (person,point)==('actor','now') and (code.rank,code.syntax)==seen[0]
        v['h245c']=lambda *a:policy
        return v
    for duty,belief,policy in product((False,True),repeat=3):
        got=run(d,values(duty,belief,policy));assert got==[True,duty,duty,belief,policy],(duty,belief,policy,got)
        rows.append(dict(duty=duty,belief=belief,policy=policy,result=got))
    for obj in DNAMES:
        v=values(True,True,True)
        if obj=='reference':v['zrefpick']=lambda point,*codes:codes[2] if point=='reference' else codes[SCENES.index(point)]
        else:v['znamepick']=lambda item,*codes:codes[DOMAIN.index('other' if item==obj else item)]
        got=run(d,v);assert got==[True,True,True,False,True],(obj,got)
    for pos in range(len(normkey)):
        wanted=list(normkey);wanted[pos]='other';v=values(True,True,True);v['h26ne']=lambda *a:normalized(a)==tuple(wanted)
        assert run(d,v)==[True,False,False,True,True],pos
    for n in ('h26ne','h26nf','znamepick','zrefpick'):
        v=values(True,True,True);v[n]=unknown;rejects(d,v)
    return dict(all_eight_duty_belief_policy_combinations=rows,constructed_code_dequotes_to_same_duty=True,
        seven_name_bindings_checked=True,exact_norm_target=True,unknown_rejected=True)

@lru_cache(None)
def adapter_checks():
    # Binding positions need two distinguishable individuals, not the full
    # population/policy model. Keep native policy checks above on DOMAIN.
    check=lambda d,v:run(d,v,('person','other'))
    rows={}
    for root,target,length in (('r5vy','r5vx',5),('r5wa','r5v7',4)):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] '+z('reference')+']]['+z('now')+']].',(target,));positions=[]
        for i in range(length):
            b=tuple('other' if j==i else 'person' for j in range(length));v=base(d)
            v['zbindings']=lambda:SequenceValue(b,'"individual"')
            if root=='r5vy':
                v['h26hn']=lambda p,c,r:b[4] if (p,c,r)==(b[0],b[1],'reference') else ('other' if b[4]=='person' else 'person')
                def body(bindings,ref):return Content(SCENES,tuple(normalized(bindings)==(b[0],b[2],b[3]) and ref=='reference' and s=='now' for s in SCENES))
            else:
                def body(*a):return Content(SCENES,tuple(a==(*b,'reference') and s=='now' for s in SCENES))
            v[target]=body;assert check(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('person',)*length,'"individual"');assert check(d,v)==[False],(root,i);positions.append(i)
        for size in (length-1,length+1):v['zbindings']=lambda:SequenceValue(('person',)*size,'"individual"');assert check(d,v)==[False]
        rows[root]=positions
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    for old,new in (('r b[p r5vx]','r[p r5vx]'),('r b[p r5vy]','r[p r5vy]'),('r c[p r5wa]','r b[p r5wa]'),('r d[p r5wb]','r c[p r5wb]')):
        try:parse(source.replace(old,new))
        except (ValueError,TypeError):pass
        else:raise AssertionError('Insufficient quotation rank accepted: '+old)
    return dict(exact_binding_positions=rows,insufficient_quotation_ranks_rejected=True,boundaries=['r5vx','r5v7'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');end=u['text'].index('. ')+1
    fragment='daß er es für Pflicht halte, in Religionsdingen den Menschen nichts vorzuschreiben, sondern ihnen darin volle Freiheit zu lassen'
    start=u['text'].index(fragment)
    return dict(status='religious_freedom_policy_and_duty_judgment_dependency_partial',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,start+len(fragment)],text=fragment),
        sentence_context=dict(range=[0,end],text=u['text'][:end]),interpretation=LIMITS,
        primary_evidence=[dict(path=SOURCES[0],url='https://korpora.org/kant/aa08/040.html',lines='28–35',observation='品位評価の対象は義務判断の自己報告であり、判断・義務・自由政策の成立を直結しない。'),
            dict(path=SOURCES[1],observation='原刊491頁のin Religionsdingenからvolle Freiheitまでを照合。第一文は492頁へ続くため、この依存群だけで文全体を確認済みにしない。')],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['一般的な君主の範囲と同じ対象集団・共同体・基準の固定','義務判断を述べる自己報告と、その報告への本人の品位評価',
            'sondern・alsoと名称Toleranzへの高慢評価・自らの拒否','本人の啓蒙と称賛に値すること、感謝する世界と後代',
            '最初の解放の功績・政府側という限定・各人の良心事項での理性使用の自由','491–492頁の全一文照合・著者帰属・後続文と段落通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*SOURCES,*PRIORS)})
@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    assert not new.document['statements'] and len(old.document['statements'])==112
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for r in reviews:assert r['selection']==selection_binding(old,[s['index'] for s in r['selection']['statements']])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(new.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==new.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        preserved_whole_unit_reviews=17,new_verified_characters=0,compact_full_v2_roundtrips=True)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for name,fn in (('content',content_checks),('norms',norm_checks),('interference',interference_checks),('policy',policy_checks),('duty',duty_checks),('adapters',adapter_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*PRIORS,*SOURCES,
        'scripts/compose_religious_freedom_policy.py','scripts/check_religious_freedom_policy.py','tests/test_religious_freedom_policy.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='religious_freedom_policy_and_duty_judgment_dependency_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
