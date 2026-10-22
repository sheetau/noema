"""Check normative identity, all offer binders and the complete subject scope."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_legislative_public_permissions import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,CODE,CRITERIA,NAMES,OFFER,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/legislative-public-permissions-v1.md';READING='data/legislative-public-permissions-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/frank-legal-criticism-v1.json','reports/legislative-thoughts-v1.json','reports/legislative-formulations-v1.json','reports/all-offered-freedoms-v1.json','reports/topical-guardian-interest-v1.json')
DOMAIN=(*NAMES,'group','one','two','other','faculty','otherscholar')
SCENES=('reference','anchor','possible','bad','history','evaluation')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def seq(ns):return 'l[a]['+args(ns)+']'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
J=seq(('one',));K=seq(('two',));BIND=seq(NAMES)
THOUGHT='k r6cy[k r543['+J+']]'
CRITIC='k r6c7[k r543['+J+'] k r543['+K+'] r[p zcriteria] k h223h['+z('history')+'] k h223h['+z('anchor')+']]'
SAVE='q[k zsavethought['+THOUGHT+']].q[k zsavecritic['+CRITIC+']].'
TARGS=args(OFFER)+' '+J+' '+args(('reference','anchor'))
CARGS=args(OFFER)+' '+J+' '+K+' r[p zcriteria] '+args(('reference','anchor','history'))
LOCAL=args(('ruler','community','person','scholar','reference','anchor'))
GENERAL=args(('person','activity','scholar','ruler','community','reference'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def bounded(row):
    samples=parse('p:r zone[] a.r ztwo[] a.r zcriteria[a] a.r zothercriteria[a] a.'+
        'q[e[l[j[a]][l[a][] l[a][k zone[]] l[a][k ztwo[]]]][l[j[a]][]]].'+
        'q[e[l['+CRITERIA+'][r[p zcriteria] r[p zothercriteria]]][l['+CRITERIA+'][]]].q[e[n p a b][n p a b]].')['statements']
    lists=samples[0]['body']['arguments'][0];codes=samples[1]['body']['arguments'][0];truth=samples[2]['body'];count=0
    def walk(x):
        nonlocal count
        if isinstance(x,list):return [walk(v) for v in x]
        if not isinstance(x,dict):return x
        if x.get('kind') in ('forall','exists') and isinstance(x['sort'],dict) and x['sort']['kind'] in ('sequence','description'):
            count+=1;acc='sampleacc'+chr(96+count);all_=x['kind']=='forall';body=walk(x['body'])
            return dict(kind='fold',sequence=deepcopy(lists if x['sort']['kind']=='sequence' else codes),
                initial=deepcopy(truth) if all_ else dict(kind='not',arguments=[deepcopy(truth)]),
                step=dict(kind='lambda',parameters=[dict(name=acc,sort='truth'),dict(name=x['variable'],sort=x['sort'])],
                    body=dict(kind='and' if all_ else 'or',arguments=[dict(kind='variable',name=acc),body])))
        return {k:walk(v) for k,v in x.items()}
    row['body']=walk(row['body']);assert count=={'r6dg':2,'r6dj':6}[row['name']]

@lru_cache(None)
def fixture(roots,query,mode='general',limited=False):
    d=deepcopy(catalog().document);d['statements']=[]
    boundaries={'general':('r6ck',),'offers':(), 'quantifiers':('r6de','r6df','r6dh','r6di'),
        'population':('r2uj','r5ni','r6dd','r6dg','r6dj'),'policy':('r6dk',)}[mode]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
        elif limited and row['name'] in ('r6dg','r6dj'):bounded(row)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zcriteria[a] a.r zothercriteria[a] a.r zsavethought['+CODE+'] c.r zsavecritic['+CODE+'] c.'
    if mode=='offers':
        extra+='r zplain[j[a] j[a] d d] c.r zcritical[j[a] j[a] h[a] a d d j[a] d d] c.'
        extra+='d r6cx[items j[a] bindings j[a] reference d] e[b point[k zplain[v items v bindings v reference v point]]].'
        extra+='d r6c6[thoughts j[a] criticisms j[a] criteria h[a] a candidate d anchor d bindings j[a] reference d] e[b point[k zcritical[v thoughts v criticisms v criteria v candidate v anchor v bindings v reference v point]]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns,'r6cy','r6c7','r543'))
    return parse(format_graph(d,'compact')+SAVE+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)[2:]
def rejects(d,v,domain=DOMAIN):
    try:run(d,v,domain)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)])
    for n in ('thought','critic'):v['zsave'+n]=lambda c,n=n:saved.update({n:codeid(c)}) is None
    v.update(aa=lambda p:p in ('person','other','ruler'),ca=lambda p,a,r:(p,a,r)==('person','activity','reference'),
        cb=lambda p,a,s,r:(p,a,s,r)==('person','activity','scholar','reference'),cd=lambda s,r:s in ('scholar','otherscholar') and r=='reference',
        cc=lambda a,au,r:(a,au,r)==('activity','audience','reference'),ce=lambda au,r:(au,r)==('audience','reference'),
        r6ck=lambda r,c,l,ref:(r,c,l,ref)==('ruler','community','baseline','reference'),
        h26tn=lambda a,l,r:(a,l,r)==('activity','baseline','reference'),cg=lambda p,a,t:(p,a,t)==('person','activity','possible'),
        ab=lambda f,p,t:(f,p,t)==('faculty','person','possible'),ac=lambda p,f,a,t:(p,f,a,t)==('person','faculty','activity','possible'),
        zcriteria=lambda x:'two' if x=='one' else 'one',zothercriteria=lambda x:x,
        h237z=lambda *a:False)
    def permitted(source,p,role,target,b,r,sign,t):
        key='thought' if codeid(target)==saved['thought'] else 'critic' if codeid(target)==saved['critic'] else None
        general=codeid(target)==(1,dict(kind='function_ref',symbol='r6da'))
        return (source,p,role,r,sign,t)==('ruler','person','scholar','reference',True,'evaluation') and (tuple(b.items)==('person','activity') if general else key is not None and tuple(b.items)==NAMES)
    v['h245c']=permitted
    v['h26o4']=lambda p,t,b,r,a,point:p=='person' and codeid(t) in saved.values() and tuple(b.items)==NAMES and (r,a)==('reference','anchor') and point in ('possible','bad')
    v['zplain']=lambda items,b,r,t:(tuple(items.items),tuple(b.items),r,t)==(('one',),NAMES,'reference','possible')
    v['zcritical']=lambda j,k,f,h,a,b,r,t:(tuple(j.items),tuple(k.items),h,a,tuple(b.items),r,t)==(('one',),('two',),'history','anchor',NAMES,'reference','possible') and f('one')=='two' and f('two')=='one'
    return v,saved

@lru_cache(None)
def general_checks():
    q='q[k r6db['+GENERAL+']].q[k r6dd['+LOCAL+' '+z('evaluation')+']].'
    d=fixture(('r6db','r6dd'),q);v,_=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('no_permission','prohibited','wrong_issuer','wrong_role','wrong_target','wrong_binding','wrong_norm_time','not_public','different_law','different_ruler','different_community','no_candidates','no_current_execution','another_public_activity_denied'):
        w=dict(v);want=[True,False]
        if case=='no_permission':w['h245c']=lambda *a:False
        if case=='prohibited':w['h237z']=lambda *a:True
        if case=='wrong_issuer':w['h245c']=lambda source,*a:source=='other'
        if case=='wrong_role':w['h245c']=lambda source,p,s,*a:s=='other'
        if case=='wrong_target':w['h245c']=lambda s,p,role,c,*a:codeid(c)==(1,dict(kind='function_ref',symbol='r44u'))
        if case=='wrong_binding':w['h245c']=lambda s,p,role,c,b,*a:tuple(b.items)==('activity','person')
        if case=='wrong_norm_time':w['h245c']=lambda *a:a[-1]=='anchor'
        if case in ('not_public','different_law','different_ruler','different_community','no_candidates'):want=[False,False]
        if case=='not_public':w['ce']=lambda *a:False
        if case=='different_law':w['h26tn']=lambda a,l,r:l=='other'
        if case=='different_ruler':w['r6ck']=lambda r,*a:r=='other'
        if case=='different_community':w['r6ck']=lambda r,c,*a:c=='other'
        if case=='no_candidates':w['ca']=lambda *a:False
        if case=='no_current_execution':w['cg']=unknown;w['ab']=unknown;w['ac']=unknown;want=[True,True]
        if case=='another_public_activity_denied':
            w['ca']=lambda p,a,r:(p,r)==('person','reference') and a in ('activity','other')
            w['cb']=lambda p,a,s,r:(p,s,r)==('person','scholar','reference') and a in ('activity','other')
            w['cc']=lambda a,au,r:(au,r)==('audience','reference') and a in ('activity','other')
            w['h26tn']=lambda a,l,r:(l,r)==('baseline','reference') and a in ('activity','other')
        assert run(d,w)==want,case;rows[case]=want
    for n in ('h26tn','r6ck','h245c','h237z'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # The two-object body can execute on the native domain without the ten-slot explosion.
    body=fixture(('r6da',),'q[t[k r6da['+seq(('person','activity'))+' '+z('reference')+']]['+z('possible')+']].')
    w,_=model(body);assert run(body,w)==[True]
    for n in ('cg','ab','ac'):
        bad=dict(w);bad[n]=lambda *a:False;assert run(body,bad)==[False]
        bad[n]=unknown;rejects(body,bad)
    return dict(cases=rows,native_public_classification_own_faculty_and_norm=True,unknown_rejected=True,
        boundary='r6ck exact royal legislative scope only; its institutional definition retains legislative-formulations evidence.')

@lru_cache(None)
def offer_checks():
    q='q[k r6de['+TARGS+']].q[k r6dh['+CARGS+']].q[k r6df['+TARGS+' '+z('evaluation')+']].q[k r6di['+CARGS+' '+z('evaluation')+']].'
    d=fixture(('r6de','r6dh','r6df','r6di'),q,'offers');v,saved=model(d);assert run(d,v)==[True]*4;rows={}
    for case in ('thought_denied','criticism_denied','both_prohibited','wrong_issuer','wrong_people','wrong_baseline','wrong_standard','wrong_ref','wrong_norm_time','empty_comparison','no_execution_candidate','execution_only_outside_comparison','criticism_only_later_anchor','wrong_condition_function','misnamed_item','misnamed_history','misnamed_anchor','no_current_offer'):
        w=dict(v);want=[True,True,True,True]
        if case=='thought_denied':w['h245c']=lambda s,p,role,c,*a:codeid(c)==saved['critic'];want[2]=False
        if case=='criticism_denied':w['h245c']=lambda s,p,role,c,*a:codeid(c)==saved['thought'];want[3]=False
        if case=='both_prohibited':w['h237z']=lambda *a:True;want[2:]=[False,False]
        if case in ('wrong_issuer','wrong_people','wrong_baseline','wrong_standard','wrong_ref','wrong_norm_time'):
            if case=='wrong_issuer':w['h245c']=lambda s,*a:s=='other'
            if case in ('wrong_people','wrong_baseline','wrong_standard'):
                slot={'wrong_people':5,'wrong_baseline':7,'wrong_standard':9}[case]
                w['h245c']=lambda s,p,role,c,b,*a,slot=slot:b.items[slot]=='other'
            if case=='wrong_ref':w['h245c']=lambda s,p,role,c,b,r,*a:r=='bad'
            if case=='wrong_norm_time':w['h245c']=lambda *a:a[-1]=='anchor'
            want[2:]=[False,False]
        if case=='empty_comparison':w['h26o4']=lambda *a:False;want[:2]=[False,False]
        if case=='no_execution_candidate':w['zplain']=lambda *a:False;w['zcritical']=lambda *a:False;want[:2]=[False,False]
        if case=='execution_only_outside_comparison':w['h26o4']=lambda *a:a[-1]=='bad';want[:2]=[False,False]
        if case=='criticism_only_later_anchor':w['zcritical']=lambda j,k,f,h,a,*rest:a=='possible';want[1]=False
        if case=='wrong_condition_function':w['zcriteria']=lambda x:x;want[1]=False
        if case=='misnamed_item':
            w['znamepick']=lambda p,*cs:cs[DOMAIN.index('two' if p=='one' else p)];want[:2]=[False,False]
        if case in ('misnamed_history','misnamed_anchor'):
            wrong='history' if case=='misnamed_history' else 'anchor'
            w['zrefpick']=lambda p,*cs:cs[SCENES.index('bad' if p==wrong else p)];want[1]=False
        if case=='no_current_offer':assert v['zplain'](type('S',(),{'items':('one',)})(),type('S',(),{'items':NAMES})(),'reference','anchor') is False
        assert run(d,w)==want,(case,run(d,w),want);rows[case]=want
    for n in ('h26o4','zplain','zcritical','h245c','h237z'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Permissions consume quotation without executing its criterion selector or body.
    grant=fixture(('r6df','r6di'),'q[k r6df['+TARGS+' '+z('evaluation')+']].q[k r6di['+CARGS+' '+z('evaluation')+']].','offers')
    w,_=model(grant);w['zplain']=unknown;w['zcritical']=unknown;w['zcriteria']=unknown;assert run(grant,w)==[True,True]
    return dict(cases=rows,same_native_list_constructors_targets_candidate_and_permission=True,quote_not_executed_by_permission=True,unknown_rejected=True,
        boundary='Only r6cx/r6c6 action adapters are replaced with exact list/selector/time/binding boundaries, avoiding large-domain tuple enumeration. The prior native bodies and all ten positions are pinned in prior reports. r547/r37c and target/list constructors execute natively.')

def quant_model(d,extra_slot=None):
    v,saved=model(d)
    for n in DOMAIN:v['z'+n]=lambda:'alpha'
    v['zone']=lambda:'alpha';v['ztwo']=lambda:'beta'
    v['znamepick']=lambda p,*cs:cs[DOMAIN.index('one' if p=='alpha' else 'two')]
    def eligible(*a,critical=False):
        inds=a[:10]
        if any(x!='alpha' for i,x in enumerate(inds) if i!=extra_slot):return False
        if extra_slot is not None and inds[extra_slot] not in ('alpha','beta'):return False
        if tuple(a[10].items) not in (('alpha',),('beta',)):return False
        if not critical:return a[11:]==('reference','anchor')
        return tuple(a[11].items) in (('alpha',),('beta',)) and codeid(a[12])[1] in (dict(kind='function_ref',symbol='zcriteria'),dict(kind='function_ref',symbol='zothercriteria')) and a[13:]==('reference','anchor','history')
    v['r6de']=lambda *a:eligible(*a);v['r6dh']=lambda *a:eligible(*a,critical=True)
    v['r6df']=lambda *a:a[-1]=='evaluation';v['r6di']=lambda *a:a[-1]=='evaluation'
    return v

@lru_cache(None)
def quantifier_checks():
    q='q[k r6dg['+LOCAL+' '+z('evaluation')+']].q[k r6dj['+LOCAL+' '+args(('history','evaluation'))+']].'
    full=fixture(('r6dg','r6dj'),q,'quantifiers');v=quant_model(full)
    try:run(full,v,('alpha','beta'))
    except ValueError as e:assert 'Cannot finitely quantify the unbounded sequence domain' in str(e),str(e)
    else:raise AssertionError('Unbounded lists accepted as a finite domain')
    # Also test the code binder directly so sequence rejection cannot mask it.
    codes=fixture((),'q[f criterion '+CRITERIA+'[e[v criterion][v criterion]]].','quantifiers');v=quant_model(codes)
    try:run(codes,v,('alpha','beta'))
    except ValueError as e:assert 'Cannot finitely quantify' in str(e),str(e)
    else:raise AssertionError('All closed descriptions treated as a finite domain')
    d=fixture(('r6dg','r6dj'),q,'quantifiers',True);v=quant_model(d);assert run(d,v,('alpha','beta'))==[True,True];rows={}
    for slot,label in ((1,'activity'),(3,'audience'),(5,'legal_people'),(7,'baseline'),(8,'formulation'),(9,'standard')):
        w=quant_model(d,slot);w['r6df']=lambda *a,slot=slot:a[slot]!='beta';w['r6di']=lambda *a,slot=slot:a[slot]!='beta'
        assert run(d,w,('alpha','beta'))==[False,False],label;rows['second_'+label+'_denied']=[False,False]
    for case in ('second_thoughts_denied','second_criticisms_denied','second_criterion_code_denied','no_thought_candidates','no_critical_candidates','irrelevant_denial'):
        w=quant_model(d);want=[True,True]
        if case=='second_thoughts_denied':w['r6df']=lambda *a:tuple(a[10].items)!=('beta',);want[0]=False
        if case=='second_criticisms_denied':w['r6di']=lambda *a:tuple(a[11].items)!=('beta',);want[1]=False
        if case=='second_criterion_code_denied':w['r6di']=lambda *a:codeid(a[12])[1]!=dict(kind='function_ref',symbol='zothercriteria');want[1]=False
        if case=='no_thought_candidates':w['r6de']=lambda *a:False;want[0]=False
        if case=='no_critical_candidates':w['r6dh']=lambda *a:False;want[1]=False
        if case=='irrelevant_denial':w['r6df']=lambda *a:a[1]=='alpha';w['r6di']=lambda *a:a[1]=='alpha'
        assert run(d,w,('alpha','beta'))==want,case;rows[case]=want
    w=quant_model(d);w['r6dh']=unknown;rejects(d,w,('alpha','beta'))
    return dict(unbounded_sequences_and_codes_rejected=True,diagnostic_cases=rows,
        boundary='Only sequence/code binders become three list samples and two closed selector codes. All six individual candidate binders execute on two distinguishable individuals; candidate/permission bodies are separate exact boundaries. This is wiring evidence, not a finite proof of the complete domain.')

@lru_cache(None)
def population_checks():
    q='q[t[k r6dk['+args(('ruler','community','group','reference','history','anchor'))+']]['+z('evaluation')+']].'
    d=fixture(('r6dk',),q,'population');v,_=model(d)
    v.update(r2uj=lambda *a:a==('ruler','community','reference'),
        r5ni=lambda r,p,c,ref:(r,c,ref)==('ruler','community','reference') and p in ('person','other'),
        h246c=lambda g,p,ref:(g,ref)==('group','reference') and p in ('person','other'),
        h247d=lambda p,r:'scholar' if p=='person' else 'otherscholar')
    expected=lambda r,c,p,s,ref,a,t:(r,c,ref,a,t)==('ruler','community','reference','anchor','evaluation') and (p,s) in (('person','scholar'),('other','otherscholar'))
    v['r6dd']=expected;v['r6dg']=expected;v['r6dj']=lambda r,c,p,s,ref,a,h,t:h=='history' and expected(r,c,p,s,ref,a,t)
    assert run(d,v)==[True];rows={}
    for case in ('omit_second_subject','extra_non_subject','empty_group','nonhuman_member','different_ruler','different_community','wrong_scholarly_role','second_subject_general_denied','second_subject_thoughts_denied','second_subject_criticism_denied'):
        w=dict(v)
        if case=='omit_second_subject':w['h246c']=lambda g,p,r:(g,p,r)==('group','person','reference')
        if case=='extra_non_subject':w['h246c']=lambda g,p,r:(g,r)==('group','reference') and p in ('person','other','ruler')
        if case=='empty_group':w['h246c']=lambda *a:False
        if case=='nonhuman_member':w['aa']=lambda p:p!='other'
        if case=='different_ruler':w['r5ni']=lambda r,*a:r=='other'
        if case=='different_community':w['r2uj']=lambda r,c,ref:c=='other'
        if case=='wrong_scholarly_role':w['h247d']=lambda *a:'scholar'
        if case.startswith('second_subject_'):
            n={'second_subject_general_denied':'r6dd','second_subject_thoughts_denied':'r6dg','second_subject_criticism_denied':'r6dj'}[case]
            old=w[n];w[n]=lambda *a,old=old:a[2]!='other' and old(*a)
        assert run(d,w)==[False],case;rows[case]=False
    for n in ('r5ni','h246c','r6dj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,native_exact_nonempty_human_subject_group=True,all_three_permissions_for_every_subject=True,
        boundary='r2uj/r5ni retain institutional evidence; r6dd/r6dg/r6dj are exact person/role/frame/time boundaries tested internally elsewhere.')

@lru_cache(None)
def policy_quote_checks():
    ns=('ruler','community','group','reference','history','anchor');code='k r6dl['+' '.join('r['+z(n)+']' for n in ns)+']'
    d=fixture(('r6dl',),'q[e['+code+']['+code+']].','policy');v,_=model(d);assert run(d,v)==[True]
    decoded=fixture(('r6dl',),'q[t[s['+code+']]['+z('evaluation')+']].','policy');v,_=model(decoded)
    v['r6dk']=lambda *a:Content(SCENES,tuple(a==ns and t=='evaluation' for t in SCENES));assert run(decoded,v)==[True]
    for n in ns:
        w=dict(v);w['z'+n]=lambda n=n:'bad' if n in SCENES else 'other';assert run(decoded,w)==[False],n
    w=dict(v);w['r6dk']=unknown;rejects(decoded,w)
    return dict(policy_quote_not_executed=True,all_six_fixed_arguments_checked=True,boundary='r6dk only; subject/policy body checked separately')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016');f='seinen Unterthanen zu erlauben';a=u['text'].index(f,390);end=u['text'].index('der Welt öffentlich vorzulegen',a)+len('der Welt öffentlich vorzulegen')
    return dict(status='all_subjects_and_all_public_legislative_candidates_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],
      alignment=dict(segments=[dict(unit=u['id'],range=[a,end],text=u['text'][a:end],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),interpretation=LIMITS,
      unresolved=['国家元首の思考態度と啓蒙への照応、拡張、危険と洞察','実例、尊敬する君主の先行者不在、Aber/sogar、全文提示と通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'] and len(old.document['statements'])==118
    for source in (old,*dependencies()):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    expected={n:(0 if n in ('r6da','r6db','r6dc','r6dd') else 1 if n in ('r6df','r6di') else 2) for n in MEANINGS}
    assert ranks==expected,ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('general',general_checks),('offers',offer_checks),('quantifiers',quantifier_checks),('population',population_checks),('policy_quote',policy_quote_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_legislative_public_permissions.py','scripts/check_legislative_public_permissions.py','tests/test_legislative_public_permissions.py',
      'scripts/compose_legislative_thoughts.py','scripts/compose_clerical_duty_scope.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py',
      'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='all_subjects_public_legislative_permissions_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
