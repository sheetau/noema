"""Check public disturbances, non-unanimous concord and every warranted threat."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_peace_concord import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/civic-peace-concord-v1.md';READING='data/civic-peace-concord-reading-v1.json'
INDEX='data/semantic-review-index-v199.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/shared-liberty-policy-v1.json','reports/spreading-spirit-sentence-v1.json')
DOMAIN=('p','q','left','right','community','episode');SCENES=('reference','assessment','safe','quietloss','unityloss')
FRAME=('left','right','community','left','episode','reference')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,policy=False):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r zconditionrow[d] c.r zharmrow[d] c.r zscope[d] c.r zassessed[d] c.r zwarranted[d] c.'
    extra+='d zcondition[] e[b point[k zconditionrow[v point]]].d zharm[] e[b point[k zharmrow[v point]]].'
    if policy:
        for r in d['declarations']:
            if r['name']=='r56i':r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
        extra+='r zpolicy[a a a a a d d] c.d r56h[government a office a community a group a topic a reference d] e[b point[k zpolicy[v government v office v community v group v topic v reference v point]]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown turned into known absence')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p in ('p','q'),h237c=lambda p,c,r:p in ('p','q') and (c,r)==('community','reference'),
        h246c=lambda g,p,r:r=='reference' and (g,p) in (('left','p'),('right','q')),
        dg=lambda ep,t:(ep,t)==('episode','quietloss'),h26qq=lambda ep,r:(ep,r)==('episode','reference'),
        h26qp=lambda ep,c,r,t:(ep,c,r,t)==('episode','community','reference','quietloss'),
        h26qr=lambda first,second,c,r,t:(first,second,c,r,t)==('left','right','community','reference','unityloss'),
        h26qs=lambda first,second,c,r,t:{first,second}=={'left','right'} and (c,r,t)==('community','reference','unityloss'),
        zconditionrow=lambda t:t in SCENES[2:],zharmrow=lambda t:t in ('quietloss','unityloss'),
        zscope=lambda t:t in SCENES[2:],zassessed=lambda t:True,zwarranted=lambda t:t=='safe',
        r56i=lambda *a:a==FRAME,zpolicy=lambda *a:a[:6]==FRAME and a[6] in SCENES[2:],
        h26qt=lambda *a:a[:7]==(*FRAME,'assessment') and a[7] in SCENES[2:],
        h26qu=lambda *a:a[:7]==(*FRAME,'assessment'),
        h26qv=lambda *a:a==(*FRAME,'assessment','safe'))
    return v

@lru_cache(None)
def peace_checks():
    q=''.join('q[t[k r572['+args(('community','reference'))+']]['+z(t)+']].' for t in ('safe','quietloss'))
    d=fixture(('r572',),q);v=model(d);assert run(d,v)==[True,False];rows={}
    for case in ('no_occurrence','not_adversarial','no_public_impact','other_community','other_reference','other_episode','empty_community'):
        w=dict(v)
        if case=='no_occurrence':w['dg']=lambda *a:False
        if case=='not_adversarial':w['h26qq']=lambda *a:False
        if case=='no_public_impact':w['h26qp']=lambda *a:False
        if case=='other_community':w['h26qp']=lambda ep,c,r,t:c=='left'
        if case=='other_reference':w['h26qp']=lambda ep,c,r,t:r=='assessment'
        if case=='other_episode':w['h26qp']=lambda ep,c,r,t:ep=='left'
        if case=='empty_community':w['h237c']=lambda *a:False
        got=run(d,w);assert got==([False,False] if case=='empty_community' else [True,True]),(case,got);rows[case]=got
    for n in ('dg','h26qq','h26qp','h237c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_occurring_adversarial_public_episode=True,unknown_rejected=True,no_lexical_quietness_truth_primitive=True)

@lru_cache(None)
def concord_checks():
    q=''.join('q[t[k r575['+args(('community','reference'))+']]['+z(t)+']].' for t in ('safe','unityloss'))
    d=fixture(('r575',),q);v=model(d);assert run(d,v)==[True,False];rows={}
    for case in ('reverse_hostility','mere_disagreement','local_grievance','empty_first_group','outsider_group','overlapping_groups','no_violence','empty_community'):
        w=dict(v)
        if case=='reverse_hostility':w['h26qr']=lambda first,second,c,r,t:(first,second,c,r,t)==('right','left','community','reference','unityloss')
        if case=='mere_disagreement':w['h26qr']=lambda *a:False
        if case=='local_grievance':w['h26qs']=lambda *a:False
        if case=='empty_first_group':w['h246c']=lambda g,p,r:(g,p,r)==('right','q','reference')
        if case=='outsider_group':w['h237c']=lambda p,c,r:(p,c,r)==('p','community','reference')
        if case=='overlapping_groups':w['h246c']=lambda g,p,r:r=='reference' and (g,p) in (('left','p'),('right','p'),('right','q'))
        if case=='no_violence':w['dg']=lambda *a:False;w['h26qq']=lambda *a:False
        if case=='empty_community':w['h237c']=lambda *a:False
        got=run(d,w);expected=[False,False] if case=='empty_community' else [True,False] if case in ('reverse_hostility','no_violence') else [True,True]
        assert got==expected,(case,got);rows[case]=got
    for n in ('h26qr','h26qs','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,nonempty_disjoint_internal_groups_checked=True,unilateral_or_reversed_hostility=True,
        peaceful_disagreement_not_split=True,nonviolent_split_can_break_concord=True,unknown_rejected=True)

@lru_cache(None)
def harm_checks():
    q=''.join('q[t[k '+n+'['+args(('community','reference'))+']]['+z('safe')+']].' for n in ('r572','r575','r576'))
    d=fixture(('r572','r575','r576'),q);rows={}
    for quiet_lost,unity_lost in product((False,True),repeat=2):
        v=model(d);v['dg']=lambda ep,t:ep=='episode'
        v['h26qp']=lambda ep,c,r,t:quiet_lost and (ep,c,r)==('episode','community','reference')
        v['h26qr']=lambda first,second,c,r,t:unity_lost and (first,second,c,r)==('left','right','community','reference')
        v['h26qs']=lambda first,second,c,r,t:{first,second}=={'left','right'} and (c,r)==('community','reference')
        got=run(d,v);assert got==[not quiet_lost,not unity_lost,quiet_lost or unity_lost],got;rows[str((quiet_lost,unity_lost))]=got
    return dict(matrix=rows,either_public_good_can_be_harmed=True,no_requirement_that_both_fail=True,native_contents=True)

@lru_cache(None)
def threat_checks():
    q='q[k r577[k zcondition[] k zharm[] p zscope p zassessed p zwarranted]].'
    d=fixture(('r577',),q);count=0
    for condition,harm,warranted in product(tuple(product((False,True),repeat=3)),repeat=3):
        v=model(d)
        def table(row):return lambda t:row[SCENES.index(t)-2] if t in SCENES[2:] else False
        v.update(zconditionrow=table(condition),zharmrow=table(harm),zwarranted=table(warranted))
        expected=any(condition) and not any(c and h and w for c,h,w in zip(condition,harm,warranted))
        got=run(d,v);assert got==[expected],(condition,harm,warranted,got);count+=1
    rows={}
    for case in ('unassessed_free_case','unassessed_nonfree_case','empty_scope','unwarranted_possible_harm','one_warranted_threat'):
        v=model(d)
        if case.startswith('unassessed_'):v['zassessed']=lambda t:t!='quietloss'
        if case=='unassessed_nonfree_case':v['zconditionrow']=lambda t:t=='safe'
        if case=='empty_scope':v['zscope']=lambda *a:False
        if case=='one_warranted_threat':v['zwarranted']=lambda t:t in ('safe','quietloss')
        got=run(d,v);assert got==[case in ('unassessed_nonfree_case','unwarranted_possible_harm')],(case,got);rows[case]=got[0]
    for n in ('zconditionrow','zharmrow','zscope','zassessed','zwarranted'):
        v=model(d);v[n]=unknown;rejects(d,v)
    return dict(three_outcome_combinations=count,cases=rows,no_vacuity_from_impossible_condition=True,
        assessment_separate_from_warrant=True,unknown_rejected=True,native_nonempty_universal_and_existential_conditions=True)

@lru_cache(None)
def liberty_binding_checks():
    q='q[k r6aa['+args((*FRAME,'assessment'))+']].'
    d=fixture(('r6aa',),q,True);v=model(d);assert run(d,v)==[True];rows={}
    for case in ('peace_threat','concord_threat','unassessed','no_liberty_case','no_scope','wrong_government','wrong_community','wrong_reference','wrong_assessment','empty_population','nonfree_unevaluated'):
        w=dict(v)
        if case=='peace_threat':w['h26qv']=lambda *a:a==(*FRAME,'assessment','quietloss')
        if case=='concord_threat':w['h26qv']=lambda *a:a==(*FRAME,'assessment','unityloss')
        if case=='unassessed':w['h26qu']=lambda *a:a[-1]!='quietloss'
        if case=='no_liberty_case':w['zpolicy']=lambda *a:False
        if case=='no_scope':w['h26qt']=lambda *a:False
        if case=='wrong_government':w['zpolicy']=lambda *a:a[0]=='right'
        if case=='wrong_community':w['zpolicy']=lambda *a:a[2]=='left'
        if case=='wrong_reference':w['h26qt']=lambda *a:a[5]=='assessment'
        if case=='wrong_assessment':w['h26qt']=lambda *a:a[6]=='reference'
        if case=='empty_population':w['h237c']=lambda *a:False
        if case=='nonfree_unevaluated':w['zpolicy']=lambda *a:a[:6]==FRAME and a[-1]=='safe';w['h26qu']=lambda *a:a[-1]=='safe'
        got=run(d,w);assert got==[case=='nonfree_unevaluated'],(case,got);rows[case]=got[0]
    for n in ('r56i','zpolicy','h26qt','h26qu','h26qv'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_liberty_frame_community_reference_assessment=True,native_both_civic_harms=True,
        boundary='r56i eligibility and r56h policy content have separate deep evidence; their exact setting arguments are checked. The two public-state contents and assessed no-threat construction execute natively.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='civic_peace_concord_and_no_warranted_threat_partial',source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1050,1209],text=u['text'][1050:1209]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['前文の同じ政府へのdieserの照応','先行自由例の同じ内容とBeispiel・leuchtet vorの接続','Denn/doch・本文設定・全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'];assert len(old.document['statements'])==115
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r572','r575','r577','r6aa'):
        for rank,label in enumerate(('','b','c','d','e')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert len(ranks)==4
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=115,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('peace',peace_checks),('concord',concord_checks),('harm',harm_checks),('threat',threat_checks),('liberty_binding',liberty_binding_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_civic_peace_concord.py','scripts/check_civic_peace_concord.py','tests/test_civic_peace_concord.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='civic_peace_concord_and_assessed_no_warranted_threat_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
