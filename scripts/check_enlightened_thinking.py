"""Check support, same-person cognitive attribution, and the policy connection."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_enlightened_thinking import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,CONTENT,NAMES,TIMES,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/enlightened-thinking-v1.md';READING='data/enlightened-thinking-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/legislative-safety-insight-v1.json','reports/religious-emphasis-sentence-v1.json')
DOMAIN=('ruler','community','group','manner','topic','activity','judgment','reason','other','second')
SCENES=('reference','history','anchor','now')
ALL=(*DOMAIN,*SCENES)
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def codeid(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
FARGS=args((*NAMES,*TIMES))
TARGET=(3,dict(kind='call',symbol='zsafe',arguments=[]))
ENLIGHTENMENT=(0,dict(kind='function_ref',symbol='bi'))
def applied(symbol,rank):return (rank,dict(kind='apply',function=dict(kind='function_ref',symbol=symbol),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in (*NAMES,*TIMES)]))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in ALL)
    extra+='r znamepick[a '+' '.join('i[a]' for _ in DOMAIN)+'] i[a].r zrefpick[d '+' '.join('i[d]' for _ in SCENES)+'] i[d].'
    extra+='d h223g[item a] i[a][k znamepick[v item '+' '.join('r['+z(n)+']' for n in DOMAIN)+']].'
    extra+='d h223h[point d] i[d][k zrefpick[v point '+' '.join('r['+z(n)+']' for n in SCENES)+']].'
    extra+='r ztruth[d] c.d zsafe[] e[b p[k ztruth[v p]]].d zalias[] e[k zsafe[]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns))
    return parse(format_graph(d,'compact')+query)
def cognition(v,target):
    v.update(h26nf=lambda p,c,t:(p,t)==('ruler','now') and codeid(c)==target,
      h26tw=lambda p,c,r,t:(p,r,t)==('ruler','reference','now') and codeid(c)==target,
      h26ai=lambda p,j,r,t:(p,j,r,t)==('ruler','judgment','reference','now'),
      h26tv=lambda j,c,r,s,t:(j,r,s,t)==('judgment','reference',True,'now') and codeid(c)==target,
      fc=lambda j,g,t:(j,g,t)==('judgment','reason','now'),fd=lambda g,j,t:(g,j,t)==('reason','judgment','now'),
      h26aj=lambda g,j,r,t:(g,j,r,t)==('reason','judgment','reference','now'))
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in ALL})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],
      ztruth=lambda t:t=='now',aa=lambda p:p=='ruler',
      dg=lambda a,t:(a,t)==('activity','now'),df=lambda p,a,t:(p,a,t)==('ruler','activity','now'),
      h26tx=lambda p,a,c,r,t:(p,a,r,t)==('ruler','activity','reference','now') and codeid(c)==ENLIGHTENMENT,
      h4m=lambda m,p,t:(m,p,t)==('manner','ruler','now'),
      h26ty=lambda m,p,r,t:(m,p,r,t)==('manner','ruler','reference','now'),
      h26tz=lambda m,j,r,t:(m,j,r,t)==('manner','judgment','reference','now'),
      h26t2=lambda m,p,s,r,t:(m,p,s,r,t)==('manner','ruler','topic','reference','now'),
      h26j7=lambda s,r:(s,r)==('topic','reference'),
      r2uj=lambda p,c,r:(p,c,r)==('ruler','community','reference'),
      r6bo=lambda p,c,g,r:(p,c,g,r)==('ruler','community','group','reference'),
      r6dp=lambda p,c,r,a:Content(SCENES,tuple(codeid(p)==applied('r6dk',2) and(c,r,a,t)==('community','reference','anchor','now') for t in SCENES)),
      h26t3=lambda m,a,n,c,t:(m,a,n,t)==('activity','ruler','topic','now') and codeid(c)==ENLIGHTENMENT)
    cognition(v,TARGET);return v
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def support_checks():
    q='q[k r6dv['+z('ruler')+' r[p bi] '+args(('reference','now'))+']].'
    q+='q[k r6dw['+args(('ruler','community','reference','now'))+']].'
    d=fixture(('r6dv','r6dw'),q,('r2uj',));v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('private_approval_only','not_actual','other_actor','different_activity','different_process','different_reference','different_point','not_head','other_community'):
        w=dict(v);want=[False,False]
        if case=='private_approval_only':w['h26tx']=lambda *a:False
        if case=='not_actual':w['dg']=lambda *a:False
        if case=='other_actor':w['df']=lambda p,a,t:p=='other'
        if case=='different_activity':w['h26tx']=lambda p,a,*rest:a=='other'
        if case=='different_process':w['h26tx']=lambda p,a,c,*rest:codeid(c)==(0,dict(kind='function_ref',symbol='bp'))
        if case=='different_reference':w['h26tx']=lambda p,a,c,r,t:r=='history'
        if case=='different_point':w['h26tx']=lambda p,a,c,r,t:t=='anchor'
        if case=='not_head':w['r2uj']=lambda *a:False;want=[True,False]
        if case=='other_community':w['r2uj']=lambda p,c,r:c=='other';want=[True,False]
        assert run(d,w)==want,case;rows[case]=want
    for n in ('aa','dg','df','h26tx','r2uj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # be is unknown throughout: supporting the process kind does not execute it.
    assert v.get('be',unknown) is unknown
    return dict(cases=rows,process_achievement_not_executed=True,unknown_rejected=True,boundary='r2uj only; activity, actor and quoted process binding execute natively')

@lru_cache(None)
def manner_checks():
    base=z('ruler')+' '+z('manner')+' r d[k zsafe[]] '+args(('reference','now','now'))
    d=fixture(('r6dz','r6dt'),'q[k r6dz['+base+']].q[k r6dt['+z('ruler')+' r d[k zsafe[]] '+args(('reference','now','now'))+']].')
    v=model(d);assert run(d,v)==[True,True];rows={}
    for case in ('not_mental_component','reversed_component_owner','other_owner','single_opinion_only','unrelated_manner','other_judgment','not_held','other_content','wrong_polarity','not_accepted','not_grasped','no_used_reason','not_supported','insufficient_ground','other_reason','false_content','truth_elsewhere','grounded_other_judgment'):
        w=dict(v);want=[False,False]
        if case=='not_mental_component':w['h4m']=lambda *a:False;want=[False,True]
        if case=='reversed_component_owner':w['h4m']=lambda m,p,t:(m,p,t)==('ruler','manner','now');want=[False,True]
        if case=='other_owner':w['h26ty']=lambda m,p,r,t:p=='other';want=[False,True]
        if case=='single_opinion_only':w['h26ty']=lambda *a:False;want=[False,True]
        if case=='unrelated_manner':w['h26tz']=lambda m,j,r,t:m=='other';want=[False,True]
        if case=='other_judgment':w['h26tz']=lambda m,j,r,t:j=='other';want=[False,True]
        if case=='not_held':w['h26ai']=lambda *a:False
        if case=='other_content':w['h26tv']=lambda j,c,*a:codeid(c)==(3,dict(kind='call',symbol='zalias',arguments=[]))
        if case=='wrong_polarity':w['h26tv']=lambda j,c,r,s,t:s is False
        if case=='not_accepted':w['h26nf']=lambda *a:False
        if case=='not_grasped':w['h26tw']=lambda *a:False
        if case=='no_used_reason':w['fc']=lambda *a:False
        if case=='not_supported':w['fd']=lambda *a:False
        if case=='insufficient_ground':w['h26aj']=lambda *a:False
        if case=='other_reason':w['h26aj']=lambda g,*a:g=='other'
        if case=='false_content':w['ztruth']=lambda t:False
        if case=='truth_elsewhere':w['ztruth']=lambda t:t=='anchor'
        if case=='grounded_other_judgment':
            # Both judgments have the same holder/content. Only the unrelated one has grounds.
            w.update(h26ai=lambda p,j,r,t:(p,r,t)==('ruler','reference','now') and j in ('judgment','second'),
              h26tv=lambda j,c,r,s,t:j in ('judgment','second') and codeid(c)==TARGET and(r,s,t)==('reference',True,'now'),
              fc=lambda j,g,t:(j,g,t)==('second','reason','now'),fd=lambda g,j,t:(g,j,t)==('reason','second','now'),
              h26aj=lambda g,j,r,t:(g,j,r,t)==('reason','second','reference','now'))
            want=[False,True]
        assert run(d,w)==want,(case,run(d,w));rows[case]=want
    for n in ('h4m','h26ty','h26tz','h26nf','h26tw','h26ai','h26tv','fc','fd','h26aj','ztruth'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,same_judgment_ground_and_manner=True,native='r6dx/r6dy/r6dz and existing r6ds/r6dt; no cognitive definition adapters',unknown_rejected=True)

@lru_cache(None)
def connection_checks():
    q='q[t[k r6d2['+FARGS+' '+args(('manner','topic'))+']]['+z('now')+']].'
    d=fixture(('r6d2',),q,('r2uj','r6bo','r6dp'));v=model(d);cognition(v,applied('r6dq',3));assert run(d,v)==[True];rows={}
    for case in ('different_subject_group','not_head','no_practical_support','different_manner','different_owner','not_religion','no_religious_application','wrong_safety_content','unsafe','wrong_policy','wrong_community','wrong_reference','wrong_anchor','wrong_assessment','no_ground'):
        w=dict(v)
        if case=='different_subject_group':w['r6bo']=lambda p,c,g,r:g=='other'
        if case=='not_head':w['r2uj']=lambda *a:False
        if case=='no_practical_support':w['h26tx']=lambda *a:False
        if case=='different_manner':w['h26t2']=lambda m,*a:m=='other'
        if case=='different_owner':w['h26t2']=lambda m,p,*a:p=='other'
        if case=='not_religion':w['h26j7']=lambda *a:False
        if case=='no_religious_application':w['h26t2']=lambda *a:False
        if case=='wrong_safety_content':w['h26nf']=lambda p,c,t:codeid(c)==TARGET
        if case in ('unsafe','wrong_policy','wrong_community','wrong_reference','wrong_anchor','wrong_assessment'):
            def safe(p,c,r,a,case=case):
                accepted={'unsafe':False,'wrong_policy':codeid(p)==TARGET,'wrong_community':c=='other','wrong_reference':r=='history','wrong_anchor':a=='reference','wrong_assessment':True}[case]
                return Content(SCENES,tuple(accepted and t==('anchor' if case=='wrong_assessment' else 'now') for t in SCENES))
            w['r6dp']=safe
        if case=='no_ground':w['h26aj']=lambda *a:False
        assert run(d,w)==[False],case;rows[case]=False
    for n in (*NAMES,*TIMES):
        w=dict(v)
        if n in NAMES:w['znamepick']=lambda p,*cs,n=n:cs[DOMAIN.index('other' if p==n else p)]
        else:w['zrefpick']=lambda p,*cs,n=n:cs[SCENES.index('history' if p==n and n!='history' else 'anchor' if p==n else p)]
        assert run(d,w)==[False],n
    for n in ('h26t2','h26j7','r6bo','r6dp'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,all_six_names_checked=True,
      native='r6d2/r6dw/r6dv/r6dz/r6dx/r6dy and r6dr/r6dq/r6dl execute; safety receives the actual same policy quote',
      boundaries='r2uj and r6bo retain previously checked office/subject semantics; r6dp is an exact policy/community/reference/anchor/assessment adapter. Its native causal and scope bodies are checked by the pinned prior report. No unbounded policy enumeration is attempted.')

@lru_cache(None)
def anaphora_checks():
    ns=('activity','ruler','topic','now');d=fixture(('r6d3',),'q[k r6d3['+args(ns)+']].');v=model(d);assert run(d,v)==[True]
    for n in ns:
        w=dict(v);w['z'+n]=lambda n=n:'anchor' if n=='now' else 'other';assert run(d,w)==[False],n
    w=dict(v);w['h26t3']=lambda m,a,n,c,t:codeid(c)==(0,dict(kind='function_ref',symbol='bp'));assert run(d,w)==[False]
    w=dict(v);w['h26t3']=unknown;rejects(d,w)
    c=catalog();assert c.entries['bi']['declaration']['body']==c.entries['r6ca']['declaration']['body']
    return dict(antecedent_process_not_immaturity=True,first_sentence_expansion_identical=True,all_roles_bound=True,process_not_executed=True,unknown_rejected=True)

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016');segments=[]
    for phrase in ('die Denkungsart eines Staatsoberhaupts','der die erstere begünstigt','geht noch weiter, und sieht ein'):
        a=u['text'].index(phrase,390);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='enlightenment_support_and_personal_thinking_manner_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),interpretation=LIMITS,
      unresolved=['一般化の範囲、具体例と尊敬する君主の先行者不在','Aber/noch/selbst/sogar、原文箇所を固定した照応と全文帰属・通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();dep=dependency();assert not c.document['statements'] and len(old.document['statements'])==118
    assert c.entries['h4m']['arguments']==['part','person','point']
    for source in (old,dep):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    ranks={};t=format_graph(c.document,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:(4 if n in ('r6dz','r6d2') else 0) for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('support',support_checks),('manner',manner_checks),('connection',connection_checks),('anaphora',anaphora_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,INVENTORY,*PRIORS,
      'scripts/compose_enlightened_thinking.py','scripts/check_enlightened_thinking.py','tests/test_enlightened_thinking.py',
      'scripts/compose_legislative_safety_insight.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='practical_support_and_same_person_thinking_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
