"""Check every retention configuration and every interference point."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_noninterference_interval import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/noninterference-interval-v1.md';READING='data/noninterference-interval-reading-v1.json'
INDEX='data/semantic-review-index-v200.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/deliberate-retention-v1.json','reports/gradual-self-departure-v1.json')
SOURCE='data/eighth-paragraph-source-reading-v2.json'
DOMAIN=('a','b','c');SCENES=('reference','first','middle','last','outside')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(query,boundaries):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r zha[d] c.r zhb[d] c.r zba[d d] c.r zbb[d d] c.'
    extra+='r zhistory[d] c.r zbefore[d d] c.'
    for n,role,t,left,right in (
        ('h26rq','history','i[h[d] c]','p zha','p zhb'),('h26rr','before','i[h[d d] c]','p zba','p zbb'),
        ('h26rs','first','i[d]',z('first'),z('middle')),('h26rt','last','i[d]',z('last'),z('outside'))):
        extra+='r z'+role+'pick[a d '+t+' '+t+'] '+t+'.d '+n+'[configuration a reference d] '+t+'[k z'+role+'pick[v configuration v reference r['+left+'] r['+right+']]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown configuration accepted as noninterference')
def symbol(code):return json.loads(code.syntax).get('symbol')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zhistorypick=lambda config,ref,a,b:a if config=='a' else b,
        zbeforepick=lambda config,ref,a,b:a if config=='a' else b,
        zfirstpick=lambda config,ref,a,b:a,
        zlastpick=lambda config,ref,a,b:a if config=='a' else b,
        zhistory=lambda t:t!='reference',zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b),
        aa=lambda p:p in ('a','b'),h246c=lambda g,p,r:g=='a' and r=='reference' and p in ('a','b'),
        h26rp=lambda actor,act,target,config,ref,point:(actor,act,target,ref,point)==('a','c','b','reference','first') and config in ('a','b'))
    return v

@lru_cache(None)
def configuration_checks():
    q=''.join('q[k '+n+'['+args(('a','c','b','reference','first'))+']].' for n in ('r6a5','r6a6'))
    d=fixture(q,('r6at',));v=model(d);seen=[]
    def actual(*a):
        codes=tuple(symbol(c) for c in a[3:7]);seen.append((a[:3],codes,a[7:]))
        return a[:3]==('a','c','b') and codes==('zhb','zbb','zfirst','zoutside') and a[7:]==('reference','first')
    v['r6at']=actual;assert run(d,v)==[True,True]
    assert {row[1] for row in seen}=={('zha','zba','zfirst','zlast'),('zhb','zbb','zfirst','zoutside')}
    rows={}
    for case in ('only_nonadopted_setting','empty_settings','wrong_first_name','wrong_history','wrong_order','wrong_end','wrong_actor','wrong_target','wrong_activity','wrong_reference','wrong_point'):
        w=dict(v)
        if case=='only_nonadopted_setting':w['h26rp']=lambda a,b,c,config,r,t:config=='a'
        if case=='empty_settings':w['h26rp']=lambda *a:False
        if case=='wrong_first_name':w['zfirstpick']=lambda config,ref,a,b:b if config=='b' else a
        if case=='wrong_history':w['zhistorypick']=lambda config,ref,a,b:a
        if case=='wrong_order':w['zbeforepick']=lambda config,ref,a,b:a
        if case=='wrong_end':w['zlastpick']=lambda config,ref,a,b:a
        if case in ('wrong_actor','wrong_target','wrong_activity','wrong_reference','wrong_point'):
            i={'wrong_actor':0,'wrong_activity':1,'wrong_target':2,'wrong_reference':7,'wrong_point':8}[case]
            w['r6at']=lambda *a,i=i:actual(*(a[:i]+('outside' if i>=7 else 'a' if a[i]=='b' else 'b',)+a[i+1:]))
        got=run(d,w);expected=[False,case not in ('empty_settings','wrong_first_name')]
        assert got==expected,(case,got);rows[case]=got
    for n in ('h26rp','zhistorypick','zbeforepick','zfirstpick','zlastpick','r6at'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    assert all(v[n] is unknown for n in ('zha','zhb','zba','zbb'))
    return dict(cases=rows,second_configuration_can_supply_actual_goal=True,all_four_codes_and_five_context_arguments_checked=True,
        future_history_and_order_not_executed=True,unknown_rejected=True,
        boundary='r6at has prior native evidence; this check executes scope quantification and all native code providers. Exhaustiveness of the semantic input scope is explicit, not inferred from the finite test domain.')

@lru_cache(None)
def interval_checks():
    q='q[k r6a7['+args(('a','reference'))+' p zhistory p zbefore '+args(('first','last'))+']].'
    d=fixture(q,('r6a5','r6a6'));v=model(d);v['r6a5']=lambda *a:False;v['r6a6']=lambda *a:True
    assert run(d,v)==[True];count=0
    for actor in DOMAIN:
        for act in DOMAIN:
            for target in ('a','b'):
                for point in ('first','middle','last'):
                    row=(actor,act,target,'reference',point)
                    w=dict(v);w['r6a5']=lambda *a,row=row:a==row;assert run(d,w)==[False],row
                    w=dict(v);w['r6a6']=lambda *a,row=row:a!=row;assert run(d,w)==[False],row;count+=1
    rows={}
    for case in ('outside_interval','outside_target','empty_population','nonhuman_population','missing_endpoint','reversed_time'):
        w=dict(v)
        if case=='outside_interval':w['r6a5']=lambda *a:a[-1]=='outside'
        if case=='outside_target':w['r6a5']=lambda *a:a[2]=='c'
        if case=='empty_population':w['h246c']=lambda *a:False
        if case=='nonhuman_population':w['h246c']=lambda g,p,r:p=='c'
        if case=='missing_endpoint':w['zhistory']=lambda t:t not in ('reference','last')
        if case=='reversed_time':w['zfirst']=lambda:'last';w['zlast']=lambda:'first'
        got=run(d,w);assert got==[case in ('outside_interval','outside_target')],(case,got);rows[case]=got[0]
    for n in ('r6a5','r6a6','zhistory','zbefore','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(each_interference_and_configuration_gap_location=count,cases=rows,
        both_endpoints_and_all_middle_points=True,all_actors_activities_and_members=True,unknown_rejected=True,
        boundary='r6a5/r6a6 are exact five-argument boundaries checked separately; all interval validity, member scope and four quantifiers execute natively.')
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='all_retention_settings_interval_noninterference_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1210,1354],text=u['text'][1210:1354]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ候補履歴・期間の自己からの漸進的離脱への条件接続','Die Menschenとnur・本文設定・全文帰属・通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,SOURCE)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for old in parents():
        for n,e in c.entries.items():
            if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r6a5':1,'r6a6':1,'r6a7':1},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,
        roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('configurations',configuration_checks),('interval',interval_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,SOURCE,
        'scripts/compose_noninterference_interval.py','scripts/check_noninterference_interval.py','tests/test_noninterference_interval.py',
        'scripts/compose_gradual_self_departure.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='noninterference_all_settings_and_interval_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
