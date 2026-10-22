"""Check delayed benefit, nonfactive gratitude and actual praising separately."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_grateful_regard import ROOT,LIBRARY,BASIS,GOAL,ASPECT,CONTENT,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/grateful-regard-v1.md';READING='data/grateful-regard-reading-v1.json';REPORT='reports/grateful-regard-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';INDEX='data/semantic-review-index-v196.json'
PRIORS=('reports/merit-praise-v1.json','reports/qualified-prince-frame-v1.json')
SOURCES=('data/eighth-paragraph-source-reading-v1.json','artifacts/merit-praise-v1/dwb-dankbar.html',
    'artifacts/grateful-regard-v1/kant-aa06-454.html','artifacts/grateful-regard-v1/kant-aa06-455.html')
DOMAIN=('holder','actor','activity','beneficiary','response','hearer','other')
SCENES=('reference','candidate','past','result','now','future')
def z(n):return 'k z'+n+'[]'
G='r[p zstate]'
ARGS=' '.join(z(n) for n in ('actor','activity','beneficiary'))+' '+G+' '+' '.join(z(n) for n in ('reference','candidate','now'))
NAMES=('actor','activity','beneficiary','reference','candidate','now')
def codes(beneficiary='beneficiary'):
    names=('actor','activity',beneficiary)
    values=' '.join('r['+z(n)+']' for n in names)+' r['+G+'] '+' '.join('r['+z(n)+']' for n in ('reference','candidate','now'))
    return {'belief':'k r5yi['+values+']','aspect':'k r5yk['+values.removeprefix('r['+z('actor')+'] ')+']','message':'k r5x4['+G+']'}
def saves(beneficiary='beneficiary'):return ''.join('q[k zsave'+n+'['+c+']].' for n,c in codes(beneficiary).items())

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def identity(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zholds[a d] c.d zstate[person a] e[b point[k zholds[v person v point]]].'
    extra+='r zsavebelief['+CONTENT+'] c.r zsaveaspect['+ASPECT+'] c.r zsavemessage[i[h[a] f]] c.'
    prefix=parse('p:'+extra);replacements={x['name']:x for x in prefix['declarations'] if x['name'] in ('h223g','h223h')}
    additions=[x for x in prefix['declarations'] if x['name'] not in replacements]
    d['declarations']=additions+[replacements.get(x['name'],x) for x in d['declarations']]
    d.update(declarations=closure(d,(*roots,*(x['name'] for x in additions))),statements=[])
    return parse(format_graph(d,'compact')+query)

def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def base(d):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda item,*codes:codes[DOMAIN.index(item)],zrefpick=lambda point,*codes:codes[SCENES.index(point)],
        aa=lambda p:p in ('holder','actor','beneficiary','hearer','other'))
    for n in ('belief','aspect','message'):v['zsave'+n]=lambda c,n=n:saved.update({n:identity(c)}) is None
    return v,saved
def actual_model(d):
    v,saved=base(d);order=('past','result','now','future')
    v.update(h257z=lambda r,c,p:(r,c)==('reference','candidate') and p in order,
        ic=lambda a,b,c:c=='candidate' and a in order and b in order and order.index(a)<order.index(b),
        dg=lambda a,p:(a,p)==('activity','past'),df=lambda p,a,s:(p,a,s)==('actor','activity','past'),
        g3=lambda a,b,g,p:(a,b,identity(g),p)==('activity','beneficiary',(0,dict(kind='function_ref',symbol='zstate')),'result'),
        zholds=lambda b,p:(b,p)==('beneficiary','result'))
    return v,saved

@lru_cache(None)
def benefit_checks():
    query='q[k r5yf['+ARGS+']].q[t[s['+codes()['belief']+']]['+z('future')+']].'
    d=fixture(('r5yf','r5yi'),query);rows={}
    for variant in ('baseline','no_cause','no_result','no_action','wrong_actor','wrong_beneficiary','future_effect','empty_history','cyclic_order'):
        v,_=actual_model(d)
        if variant=='no_cause':v['g3']=lambda *a:False
        if variant=='no_result':v['zholds']=lambda *a:False
        if variant=='no_action':v['dg']=lambda *a:False
        if variant=='wrong_actor':v['df']=lambda p,a,s:(p,a,s)==('other','activity','past')
        if variant=='wrong_beneficiary':v['g3']=lambda a,b,g,p:(a,b,p)==('activity','other','result')
        if variant=='future_effect':v['g3']=lambda a,b,g,p:(a,b,p)==('activity','beneficiary','future');v['zholds']=lambda b,p:(b,p)==('beneficiary','future')
        if variant=='empty_history':v['h257z']=lambda *a:False
        if variant=='cyclic_order':v['ic']=lambda a,b,c:a!=b and a in ('past','result','now','future') and b in ('past','result','now','future')
        got=run(d,v);assert got==[variant=='baseline']*2,(variant,got);rows[variant]=got
    for n in ('g3','dg','df','zholds','h257z','ic'):
        v,_=actual_model(d);v[n]=unknown;rejects(d,v)
    return dict(cases=rows,action_precedes_effect=True,result_need_not_persist_to_now=True,
        quoted_content_keeps_its_fixed_evaluation_point=True,time_order_not_substituted_for_cause=True,unknown_rejected=True)

def attitude_model(d,valued=True,accepted=True,regard=True,based=True,beneficiary='beneficiary'):
    v,saved=base(d);goal=(0,dict(kind='function_ref',symbol='zstate'))
    v.update(id=lambda h,g,p:valued and (h,identity(g),p)==('holder',goal,'now'),
        h26nt=lambda h,b,g,p:valued and (h,b,identity(g),p)==('holder',beneficiary,goal,'now'),
        h26nf=lambda h,c,p:accepted and (h,identity(c),p)==('holder',saved['belief'],'now'),
        h26nu=lambda h,a,c,p:regard and (h,a,identity(c),p)==('holder','actor',saved['aspect'],'now'),
        h26nv=lambda h,a,c,g,p:based and (h,a,identity(c),identity(g),p)==('holder','actor',saved['aspect'],saved['belief'],'now'))
    return v,saved

@lru_cache(None)
def attitude_checks():
    q=saves()+'q[k r5yn['+z('holder')+' '+ARGS+']].';roots=('r5yi','r5yk','r5x4','r5yn')
    d=fixture(roots,q);rows=[]
    for bits in product((False,True),repeat=4):
        v,_=attitude_model(d,*bits);got=run(d,v);assert got==[True]*3+[all(bits)];rows.append(dict(inputs=bits,result=got[-1]))
        for n in ('dg','df','g3','zholds','h257z','ic'):assert v[n] is unknown
    self_args=ARGS.replace(z('beneficiary'),z('holder'))
    own=fixture(roots,saves('holder')+'q[k r5yn['+z('holder')+' '+self_args+']].')
    v,_=attitude_model(own,beneficiary='holder');v['h26nt']=lambda *a:False;assert run(own,v)==[True]*4
    v['id']=lambda *a:False;assert run(own,v)==[True]*3+[False]
    # Every attitude argument, including both descriptions, is independent.
    for name,size in (('h26nf',3),('h26nu',4),('h26nv',5)):
        for pos in range(size):
            v,_=attitude_model(d);old=v[name]
            def wrong(*a):
                if hasattr(a[pos],'syntax'):return False
                b=list(a);b[pos]='future' if pos==size-1 else 'other';return old(*b)
            v[name]=wrong;assert run(d,v)==[True]*3+[False],(name,pos)
    for name in NAMES:
        v,_=attitude_model(d)
        if name in SCENES:v['zrefpick']=lambda p,*codes:codes[SCENES.index('future' if p==name else p)]
        else:v['znamepick']=lambda p,*codes:codes[DOMAIN.index('other' if p==name else p)]
        assert run(d,v)==[True]*3+[False],name
    for n in ('h26nt','h26nf','h26nu','h26nv','znamepick','zrefpick'):
        v,_=attitude_model(d);v[n]=unknown;rejects(d,v)
    return dict(sixteen_components=rows,self_and_other_beneficiaries_distinct=True,
        twelve_attitude_arguments_and_six_names_checked=True,unrelated_affection_not_enough=True,
        actual_benefit_and_response_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def response_checks():
    args=' '.join(z(n) for n in ('activity','beneficiary'))+' '+G+' '+z('reference')+' '+z('candidate')
    audience='i[recipient a][e[v recipient]['+z('hearer')+']]'
    q=saves()+'q[k r5yn['+z('holder')+' '+ARGS+']].q[t[c[k r5yp['+args+' '+audience+' '+G+']]['+z('holder')+' '+z('response')+' '+z('actor')+']]['+z('now')+']].'
    d=fixture(('r5yi','r5yk','r5x4','r5yn','r5yp'),q);rows=[]
    for grateful,performed in product((False,True),repeat=2):
        v,saved=attitude_model(d,regard=grateful);goal=(0,dict(kind='function_ref',symbol='zstate'))
        v.update(dg=lambda a,p:performed and (a,p)==('response','now'),f3=lambda h,a,p:(h,a,p)==('holder','response','now'),
            f2=lambda a,r,t,m,p:(a,r,t,identity(m),p)==('response','hearer','actor',saved['message'],'now'),
            h26nr=lambda h,a,t,g,p:(h,a,t,identity(g),p)==('holder','response','actor',goal,'now'),
            h26ns=lambda h,a,t,g,r,p:(h,a,t,identity(g),r,p)==('holder','response','actor',goal,'reference','now'))
        got=run(d,v);assert got==[True]*3+[grateful,grateful and performed];rows.append(dict(grateful=grateful,performed=performed,result=got[-2:]))
        assert v['g3'] is unknown and v['df'] is unknown and v['zholds'] is unknown
    return dict(cases=rows,benefaction_distinct_from_praise_action=True,no_praise_implied_by_attitude=True,
        no_actual_merit_implied_by_belief_or_expression=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');start=u['text'].index('dankbaren');end=u['text'].index(' als derjenige')
    return dict(status='credited_benefit_and_grounded_appreciative_attitude_dependency',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=u['text'][start:end]),
        interpretation=LIMITS,evidence=[dict(path=SOURCES[1],url='https://www.dwds.de/wb/dwb/dankbar',observation='人格的態度と表出の用法を補助に使う。'),
            dict(path=SOURCES[2],url='https://korpora.org/kant/aa06/454.html',retrieved='2026-10-23',observation='31–33行の恩恵に基づく相手への敬意を補助とし、後年の定義全体を1784年へ移さない。'),
            dict(path=SOURCES[3],url='https://korpora.org/kant/aa06/455.html',retrieved='2026-10-23',observation='心情と行為の区別、26–28行の先祖への感謝。義務論全体と善意だけへの感謝は今回の条件に追加しない。')],
        unresolved=['具体的な解放の功績と恩恵内容・称揚根拠の同じ出来事への束縛','世界と後代の全人物範囲・時代順序・集団の態度分布と規範評価への引用','良心事項・政府側の最初の解放・全設定・著者帰属・一文全体と後続'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,*SOURCES)})

@lru_cache(None)
def structure_checks():
    c=catalog()
    for p in parents():
        for n,e in c.entries.items():
            if n in p.entries:assert e['declaration']==p.entries[n]['declaration'] and e['meaning_ja']==p.entries[n]['meaning_ja']
    assert not c.document['statements'] and len(parents()[1].document['statements'])==112
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    source=(ROOT/LIBRARY).read_text(encoding='utf-8')
    try:parse(source.replace('r b[p r5yj]','r[p r5yj]'))
    except (ValueError,TypeError):pass
    else:raise AssertionError('Actual state dequotation rank lost')
    for notation in ('compact','full'):
        s=format_graph(c.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==c.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_statements=0,main_statements_preserved=112,
        new_verified_characters=0,compact_full_v2_roundtrips=True,rank_one_aspect_required=True,parent_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('benefit',benefit_checks),('attitude',attitude_checks),('response',response_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{READING,DOC,INVENTORY,INDEX,*SOURCES,*PRIORS,
        'scripts/compose_grateful_regard.py','scripts/check_grateful_regard.py','tests/test_grateful_regard.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='delayed_benefit_and_nonfactive_grateful_regard_checked',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
