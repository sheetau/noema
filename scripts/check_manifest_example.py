"""Check realized configurations, manifest evidence and closed target content."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_manifest_example import ROOT,LIBRARY,BASIS,CONTENT,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/manifest-example-v1.md';READING='data/manifest-example-reading-v1.json'
INDEX='data/semantic-review-index-v199.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/civic-peace-concord-v1.json','reports/shared-liberty-policy-v1.json')
SOURCE=('sourcegov','sourceoffice','sourcecommunity','sourcegroup','sourcetopic')
TARGET=('government','office','community','group','topic')
DOMAIN=('example',*SOURCE,*TARGET,'other');SCENES=('reference','instance','assessment','otherpoint')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
def literal(n,ns):return 'r c[c[p '+n+']['+args(ns)+']]'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in ('r56i','r6aa'):
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r znamepick[a '+' '.join('i[a]' for n in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for n in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r zpolicy[a a a a a d d] c.r zpeace[a d d] c.r zconcord[a d d] c.'
    extra+='d r56h[government a office a community a group a topic a reference d] e[b point[k zpolicy[v government v office v community v group v topic v reference v point]]].'
    for n,p in (('r572','zpeace'),('r575','zconcord')):
        extra+='d '+n+'[community a reference d] e[b point[k '+p+'[v community v reference v point]]].'
    extra+='r zsavesource['+CONTENT+'] c.r zsavetarget['+CONTENT+'] c.r zsaveactual['+CONTENT+'] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    pre='q[k zsavesource['+literal('r6ag',(*SOURCE,'reference'))+']].q[k zsavetarget['+literal('r6ad',(*TARGET,'reference'))+']].'
    return parse(format_graph(d,'compact')+pre+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)[2:]
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted as manifest evidence')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};saved={}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
        zsavesource=lambda c:saved.update(source=codeid(c)) is None,zsavetarget=lambda c:saved.update(target=codeid(c)) is None,
        zsaveactual=lambda c:saved.update(actual=codeid(c)) is None,
        zpolicy=lambda *a:a==(*SOURCE,'reference','instance'),
        zpeace=lambda *a:a==('sourcecommunity','reference','instance'),zconcord=lambda *a:a==('sourcecommunity','reference','instance'),
        r56i=lambda *a:a==(*TARGET,'reference'),
        h26qw=lambda e,c,t,r:(e,t,r)==('example','instance','reference') and codeid(c)==saved['source'],
        h26qx=lambda *a:a==('example','government','reference','assessment'),
        h26qy=lambda e,c,r,t:(e,r,t)==('example','reference','assessment') and codeid(c)==saved['target'],
        h26qz=lambda e,g,c,r,t:(e,g,r,t)==('example','government','reference','assessment') and codeid(c)==saved['target'])
    return v,saved

@lru_cache(None)
def instance_checks():
    query='q[k r6ab['+args(('example',*SOURCE,'reference','instance'))+']].'
    d=fixture(('r6ab','r6ad'),query);v,_=model(d);assert run(d,v)==[True];rows={}
    for case in ('imaginary','different_example','different_content','different_instance','different_reference','no_liberty','no_peace','no_concord','wrong_community','wrong_policy_government','wrong_policy_office','wrong_policy_group','wrong_policy_topic','other_policy_point','other_peace_point'):
        w=dict(v)
        if case in ('imaginary','different_content'):w['h26qw']=lambda *a:False
        if case=='different_example':w['h26qw']=lambda e,c,t,r:e=='other'
        if case=='different_instance':w['h26qw']=lambda e,c,t,r:t=='assessment'
        if case=='different_reference':w['h26qw']=lambda e,c,t,r:r=='otherpoint'
        if case=='no_liberty':w['zpolicy']=lambda *a:False
        if case=='no_peace':w['zpeace']=lambda *a:False
        if case=='no_concord':w['zconcord']=lambda *a:False
        if case=='wrong_community':w['zpeace']=lambda c,r,t:(c,r,t)==('community','reference','instance')
        if case.startswith('wrong_policy_'):
            index={'government':0,'office':1,'group':3,'topic':4}[case.removeprefix('wrong_policy_')]
            changed=list((*SOURCE,'reference','instance'));changed[index]='other';w['zpolicy']=lambda *a,b=tuple(changed):a==b
        if case=='other_policy_point':w['zpolicy']=lambda *a:a==(*SOURCE,'reference','assessment')
        if case=='other_peace_point':w['zpeace']=lambda *a:a==('sourcecommunity','reference','assessment')
        got=run(d,w);assert got==[False],(case,got);rows[case]=False
    for n in ('h26qw','zpolicy','zpeace','zconcord'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    for liberty,peace,concord in product((False,True),repeat=3):
        w=dict(v);w.update(zpolicy=lambda *a:liberty,zpeace=lambda *a:peace,zconcord=lambda *a:concord)
        assert run(d,w)==[liberty and peace and concord]
    return dict(cases=rows,eight_actual_state_combinations=True,same_example_configuration_and_point=True,
        unknown_rejected=True,boundary='Native r6ag and r6ab connect content identity, names, point and conjunction. r56h/r572/r575 have explicit native-content wrappers and independent prior deep evidence.')

@lru_cache(None)
def manifestation_checks():
    query='q[k r6ac['+z('example')+' '+z('government')+' '+literal('r6ad',(*TARGET,'reference'))+' '+args(('reference','assessment'))+']].'
    d=fixture(('r6ac','r6ad','r6ag'),query);v,_=model(d);assert run(d,v)==[True]
    for available,support,plain in product((False,True),repeat=3):
        w=dict(v);w.update(h26qx=lambda *a:available,h26qy=lambda *a:support,h26qz=lambda *a:plain)
        assert run(d,w)==[available and support and plain]
    mutations=0
    for n,arity in (('h26qx',4),('h26qy',4),('h26qz',5)):
        for i in range(arity):
            original=v[n]
            def bad(*a,i=i,original=original):
                b=list(a)
                if hasattr(b[i],'syntax'):return False
                b[i]='other';return original(*b)
            w=dict(v);w[n]=bad;assert run(d,w)==[False];mutations+=1
        w=dict(v);w[n]=unknown;rejects(d,w)
    assert all(v.get(n,unknown) is unknown for n in ('aa','gg','h247u','h245q','r6aa'))
    return dict(independent_three_relation_combinations=8,argument_mutations=mutations,
        no_actual_individual_recognition_or_government_assent=True,no_execution_of_supported_content=True,unknown_rejected=True)

@lru_cache(None)
def content_checks():
    query='q[k zsaveactual[k r6ae['+' '.join('r['+z(n)+']' for n in (*TARGET,'reference'))+']]].'
    d=fixture(('r6ae','r6ag'),query);v,saved=model(d);assert run(d,v)==[True];assert saved['actual']==saved['target'];assert saved['actual']!=saved['source']
    for i in range(6):
        changed=list((*TARGET,'reference'));changed[i]='otherpoint' if i==5 else 'other'
        q='q[k zsaveactual[k r6ae['+' '.join('r['+z(n)+']' for n in changed)+']]].'
        dd=fixture(('r6ae','r6ag'),q);vv,ss=model(dd);assert run(dd,vv)==[True];assert ss['actual']!=ss['target']
    q='q[t[k r6ad['+args((*TARGET,'reference'))+']]['+z('assessment')+']].'
    d=fixture(('r6ad','r6ag'),q);v,_=model(d);calls=[]
    v['r6aa']=lambda *a:calls.append(a) is None and a==(*TARGET,'reference','assessment')
    assert run(d,v)==[True];assert set(calls)=={(*TARGET,'reference',t) for t in SCENES}
    for i in range(7):
        changed=list((*TARGET,'reference','assessment'));changed[i]='other' if i<5 else 'otherpoint'
        v['r6aa']=lambda *a,b=tuple(changed):a==b
        assert run(d,v)==[False]
    v['r6aa']=unknown;rejects(d,v)
    return dict(six_closed_arguments_checked=True,source_and_supported_contents_different=True,
        all_seven_safety_arguments_and_evaluation_point_checked=True,minimum_supported_quote_rank=2,
        boundary='r6aa is an explicit truth boundary only for the r6ad native content wrapper. Literal expected descriptions independently check quote construction without evaluating r6aa.')

@lru_cache(None)
def binding_checks():
    query='q[k r6af['+args(('example',*SOURCE,*TARGET,'reference','instance','assessment'))+']].'
    d=fixture(('r6af',),query);v,_=model(d);assert run(d,v)==[True];rows={}
    for case in ('unqualified_target','wrong_target_government','wrong_source_content','wrong_target_content','wrong_assessment','wrong_instance'):
        w=dict(v)
        if case=='unqualified_target':w['r56i']=lambda *a:False
        if case=='wrong_target_government':w['h26qx']=lambda e,g,r,t:g=='sourcegov'
        if case=='wrong_source_content':w['h26qw']=lambda *a:False
        if case=='wrong_target_content':w['h26qy']=lambda *a:False
        if case=='wrong_assessment':w['h26qz']=lambda e,g,c,r,t:t=='instance'
        if case=='wrong_instance':w['h26qw']=lambda e,c,t,r:t=='assessment'
        got=run(d,w);assert got==[False],(case,got);rows[case]=False
    for item in (*SOURCE,*TARGET):
        w=dict(v);w['znamepick']=lambda p,*cs,item=item:cs[DOMAIN.index('other' if p==item else p)]
        # Permissive evidence relations make the independent name guards observable.
        for n in ('h26qw','h26qx','h26qy','h26qz'):w[n]=lambda *a:True
        assert run(d,w)==[False],item
    w=dict(v);w['zrefpick']=lambda p,*cs:cs[3]
    for n in ('h26qw','h26qx','h26qy','h26qz'):w[n]=lambda *a:True
    assert run(d,w)==[False]
    for n in ('r56i','h26qw','h26qx','h26qy','h26qz','znamepick','zrefpick'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    def source_only(*a):
        if a[:5]!=SOURCE:raise AssertionError('Target policy executed')
        return a[-2:]==('reference','instance')
    w=dict(v);w['zpolicy']=source_only;assert w['r6aa'] is unknown;assert run(d,w)==[True]
    return dict(cases=rows,eleven_wrong_names_rejected_with_permissive_evidence=True,
        distinct_governments_and_communities_preserved=True,target_liberty_and_safety_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='manifest_realized_example_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1050,1209],text=u['text'][1050:1209]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ先行君主の実例・同じ自己誤解する政府への本文束縛','Denn/doch・全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements']
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r6ab','r6ac','r6ad','r6af'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert len(ranks)==4
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,
        roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('instance',instance_checks),('manifestation',manifestation_checks),('content',content_checks),('binding',binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_manifest_example.py','scripts/check_manifest_example.py','tests/test_manifest_example.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='manifest_realized_example_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
