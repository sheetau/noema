"""Check exact source scope, universal liberties, and nonfactive support."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_freedom_ethos import ROOT,PARENT,LIBRARY,BASIS,CONTENT,NAMES,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/freedom-ethos-v1.md';READING='data/freedom-ethos-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/public-offers-sentence-v1.json','reports/religious-freedom-policy-v1.json','reports/all-offered-freedoms-v1.json')
DOMAIN=('a','b');SCENES=('reference','now','later')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),policy=False):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            assert row['result']=='truth'
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a i[a] i[a]] i[a].r zrefpick[d i[d] i[d] i[d]] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item r['+z('a')+'] r['+z('b')+']]].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zsave['+CONTENT+'] c.'
    if 'r55c' in boundaries:
        fields='person a office a church a creed a subject a scholar a reference d anchor d'
        forwarded='v person v office v church v creed v subject v scholar v reference v anchor'
        extra+='r zclerical[a a a a a a d d h[a d] c] c.'
        extra+='d r55c['+fields+' comparisons i[h[a d] c]] c[k zclerical['+forwarded+' s[v comparisons]]].'
    if policy:
        extra+='r zreligious[a a a a d d] c.d r5v7[ruler a group a community a topic a reference d] e[b point[k zreligious[v ruler v group v community v topic v reference v point]]].'
    prefix=parse('p:'+extra);ns={r['name'] for r in prefix['declarations']}
    d['declarations']=prefix['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zsave=lambda c:saved.update(content=codeid(c)) is None,aa=lambda p:True)
    return v,saved

@lru_cache(None)
def scope_checks():
    d=fixture(('r55w',),'q[k r55w['+args(('a','b','a','b','reference','now'))+']].',('r5xh',));out={}
    for case in ('all','missing_person','foreign_person','nonhuman','different_ruler','different_office','different_community','different_point'):
        v,_=model(d)
        v['r5xh']=lambda *a:a==('a','b','a','now')
        v['h246c']=lambda g,p,r:(g,r)==('b','reference') and p=='a'
        v['h26hi']=lambda p,o,c,t:(p,o,c,t)==('a','b','a','now')
        if case=='missing_person':v['h246c']=lambda *a:False
        if case=='foreign_person':v['h246c']=lambda *a:True
        if case=='nonhuman':v['aa']=lambda p:p!='a'
        if case=='different_ruler':v['r5xh']=lambda *a:False
        for name,index,value in [('different_office',1,'a'),('different_community',2,'b'),('different_point',3,'later')]:
            if case==name:
                expected=['a','b','a','now'];expected[index]=value
                v['h26hi']=lambda *a:tuple(a)==tuple(expected)
        got=run(d,v);assert got==[case=='all'],(case,got);out[case]=got[0]
    for n in ('r5xh','h246c','h26hi','aa'):
        v,_=model(d);v.update(r5xh=lambda *a:True,h246c=lambda *a:True,h26hi=lambda *a:True);v[n]=unknown;rejects(d,v)
    return dict(cases=out,all_people_exact_group=True,boundary='Only r5xh is an independently checked classification boundary; membership equality executes natively.')

@lru_cache(None)
def clerical_checks():
    d=fixture(('r55x',),'q[k r55x['+args(('b','a','reference','now'))+']].',('r54y','r55c'));out={}
    def base():
        v,_=model(d);v['h26hi']=lambda p,o,c,t:(o,c,t)==('b','a','now')
        v['r54y']=lambda *a:a[-2:]==('reference','now')
        v['zclerical']=lambda *a:True
        return v
    v=base();seen=[]
    def actual(*a):
        assert a[6:8]==('reference','now');seen.append(a[:6]);return True
    v['zclerical']=actual;assert run(d,v)==[True];assert len(set(seen))==64
    out['native_six_variable_combinations']=64
    for i in range(6):
        v=base();v['zclerical']=lambda *a:a[i]!='b';assert run(d,v)==[False]
    for case in ('outside_jurisdiction','not_clerical','wrong_name','wrong_reference_name','unknown_freedom'):
        v=base();v['zclerical']=lambda *a:False
        if case=='outside_jurisdiction':v['h26hi']=lambda *a:False
        if case=='not_clerical':v['r54y']=lambda *a:False
        if case=='wrong_name':v['zclerical']=lambda *a:True;v['znamepick']=lambda p,a,b:b if p=='a' else a
        if case=='wrong_reference_name':v['zclerical']=lambda *a:True;v['zrefpick']=lambda p,*cs:cs[2]
        if case=='unknown_freedom':v['zclerical']=unknown;rejects(d,v);continue
        got=run(d,v);assert got==[case in ('outside_jurisdiction','not_clerical')],(case,got);out[case]=got[0]
    # Inspect the constructed comparison function without replacing its constructor.
    v=base();count=[0]
    def inspect(*a):
        count[0]+=1
        return a[-1]('a','now') is True
    v['zclerical']=inspect
    v['h26o6']=lambda ch,cr,su,item,ref,t:(ch,cr,su,item,ref,t)==('a','a','a','a','reference','now')
    assert run(d,v)==[False] # Later church/creed/subject tuples cannot borrow the first comparison.
    assert count[0]>1
    return dict(cases=out,each_variable_counterexample_rejected=True,comparison_constructor_executed=True,
        boundary='r54y and r55c are separately checked deep boundaries; six native quantifiers, jurisdiction, four names and real r546 closure remain active.')

@lru_cache(None)
def other_checks():
    d=fixture(('r55y',),'q[k r55y['+args(('b','a','reference','now'))+']].',('r55j','r55h','r55i'));out={}
    for case in ('all','second_denied','second_restricted','second_clerical','second_foreign','second_nonhuman','wrong_scholar','wrong_point'):
        v,_=model(d);v['h26hi']=lambda p,o,c,t:(o,c,t)==('b','a','now')
        v['h247d']=lambda p,r:'b' if p=='a' else 'a'
        v['r55j']=lambda *a:False;v['r55h']=lambda *a:True
        v['r55i']=lambda p,s,r,t:s==v['h247d'](p,r) and (r,t)==('reference','now')
        if case.startswith('second_'):
            v['r55i']=lambda p,*a:p=='a'
            if case=='second_restricted':v['r55h']=lambda p,*a:p=='a'
            if case=='second_clerical':v['r55j']=lambda p,*a:p=='b'
            if case=='second_foreign':v['h26hi']=lambda p,*a:p=='a'
            if case=='second_nonhuman':v['aa']=lambda p:p=='a'
        if case=='wrong_scholar':v['r55i']=lambda p,s,r,t:s!=v['h247d'](p,r)
        if case=='wrong_point':v['r55i']=lambda p,s,r,t:t=='later'
        got=run(d,v);assert got==[case not in ('second_denied','wrong_scholar','wrong_point')],(case,got);out[case]=got[0]
    for n in ('r55j','r55h','r55i'):
        v,_=model(d);v.update(h26hi=lambda *a:True,h247d=lambda *a:'a',r55j=lambda *a:False,r55h=lambda *a:True,r55i=lambda *a:True);v[n]=unknown;rejects(d,v)
    return dict(cases=out,boundary='Native all-person scope with r55j, r55h and r55i as separately checked boundaries; no prince-merit condition.')

@lru_cache(None)
def policy_checks():
    vals=('a','b','a','b','a','reference')
    q='q[t[k r55z['+args(vals)+']]['+z('now')+']].q[t[k r55z['+args(vals)+']]['+z('later')+']].'
    d=fixture(('r55z',),q,('r55w','r55x','r55y'),True);out={}
    def base():
        v,_=model(d);v['r55w']=lambda *a:a==('a','b','a','b','reference','now')
        v['r55x']=v['r55y']=lambda *a:a==('b','a','reference','now')
        v['zreligious']=lambda *a:a==('a','b','a','a','reference','now')
        return v
    assert run(d,base())==[True,False]
    for n in ('r55w','r55x','r55y','zreligious'):
        v=base();v[n]=lambda *a:False;assert run(d,v)==[False,False];out[n]=False
        v=base();v[n]=unknown;rejects(d,v)
    return dict(all_four_required=out,same_point_for_all=True,boundary='The conjunction and exact argument wiring execute; deep liberty and membership evaluations are separate.')

@lru_cache(None)
def attitude_checks():
    vals=('a','b','a','b','a','reference')
    codes=' '.join('r['+z(n)+']' for n in vals)
    q='q[k zsave[k r552['+codes+']]].q[k r554['+z('b')+' '+args(vals)+' '+z('now')+']].q[t[c[k r555['+args(vals)+']]['+z('b')+']]['+z('later')+']].'
    d=fixture(('r552','r554','r555'),q);out={}
    for case in ('support','nonhuman','wrong_content','wrong_holder','wrong_point','unknown'):
        v,saved=model(d)
        v['h26pg']=lambda p,c,t:p=='b' and codeid(c)==saved['content'] and t=='now'
        if case=='nonhuman':v['aa']=lambda *a:False
        if case=='wrong_content':v['h26pg']=lambda p,c,t:codeid(c)!=saved['content']
        if case=='wrong_holder':v['h26pg']=lambda p,c,t:p=='a'
        if case=='wrong_point':v['h26pg']=lambda p,c,t:t=='reference'
        if case=='unknown':v['h26pg']=unknown;rejects(d,v);continue
        got=run(d,v);assert got==[True,case=='support',False],(case,got);out[case]=got[1:]
    # Every bound individual and the interpretation point participates in the exact quote.
    for i in range(6):
        changed=list(vals);changed[i]=('b' if vals[i]=='a' else 'a') if i<5 else 'later'
        altered=' '.join('r['+z(n)+']' for n in changed)
        alt=fixture(('r552','r554'),'q[k zsave[k r552['+altered+']]].q[k r554['+z('b')+' '+args(vals)+' '+z('now')+']].')
        v,saved=model(alt);v['h26pg']=lambda p,c,t:codeid(c)==saved['content'];assert run(alt,v)==[True,False]
    v,saved=model(d);v['h26pg']=lambda *a:True;v['znamepick']=lambda p,a,b:b if p=='a' else a
    assert run(d,v)==[True,False,False]
    v,saved=model(d);v['h26pg']=lambda *a:True;v['zrefpick']=lambda p,*cs:cs[2]
    assert run(d,v)==[True,False,False]
    return dict(cases=out,all_six_reference_mutations_rejected=True,wrong_names_rejected=True,
        quoted_policy_primitives_remain_unknown=True,attitude_is_not_factual_freedom_or_belief=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='antecedent_liberties_as_favorable_attitude_partial',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,1049],text=u['text'][890:1049]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['先行例への支持と自由一般の態度の接続','元と外の統治圏、同じ態度の共有・取得・影響経路','外的障害、格闘の必要、政府の自己誤解','auch/selbst、照応、全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    assert not c.document['statements'];assert len(old.document['statements'])==114
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r55z','r554','r555'):
        for rank,label in enumerate(('','b','c','d','e','f')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks['r55z']==2
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=114,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('scope',scope_checks),('clerical',clerical_checks),('other',other_checks),('policy',policy_checks),('attitude',attitude_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_freedom_ethos.py','scripts/check_freedom_ethos.py','tests/test_freedom_ethos.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_clerical_duty_scope.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='antecedent_liberty_content_and_nonfactive_support_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
