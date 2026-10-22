"""Check realized examples and as-of qualitative precedence, not first arrival."""
from copy import deepcopy
from functools import lru_cache
from html import unescape
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_example import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,NAMES,DATES,CONTENT,SCHEMA,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/royal-example-v1.md';READING='data/royal-example-reading-v1.json'
INDEX='data/semantic-review-index-v202.json';SOURCE='data/ninth-paragraph-source-reading-v2.json'
LEXICAL='artifacts/ninth-paragraph-source-v3/adelung-vorgehen.html'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/enlightened-thinking-v1.json','reports/legislative-public-permissions-v1.json','reports/manifest-example-v1.json')
DOMAIN=('ruler','community','group','manner','topic','example','author','public','reader','other','foreign')
SCENES=('reference','history','past','anchor','assessment','future');TIME=('past','anchor','assessment','future')
ALL=(*DOMAIN,*SCENES)
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def codeid(c):return c.rank,json.loads(c.syntax)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
FARGS=args(NAMES);FVALUES=tuple(NAMES)
PATTERN=(4,dict(kind='function_ref',symbol='r6d4'))
REGARD=(1,dict(kind='function_ref',symbol='r6eb'))
ACTUAL=(4,dict(kind='call',symbol='zactual',arguments=[]))
CONCRETE=(4,dict(kind='apply',function=dict(kind='function_ref',symbol='r6d4'),arguments=[dict(kind='call',symbol='z'+n,arguments=[]) for n in NAMES]))
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
    extra+='r ztruth[d] c.d zactual[] e[b p[k ztruth[v p]]].'
    extra+='r zhist[d] c.r zbefore[d d] c.r zscope[a d] c.r zassessed[a d] c.r zbetter[a d a d] c.'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']};d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d['declarations']=closure(d,(*roots,*ns));return parse(format_graph(d,'compact')+query)
def content(fields,expected):return Content(SCENES,tuple(tuple(fields)==tuple(expected) and t=='anchor' for t in SCENES))
def before(a,b):return a in TIME and b in TIME and TIME.index(a)<TIME.index(b)
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in ALL})
    v.update(znamepick=lambda p,*cs:cs[DOMAIN.index(p)],zrefpick=lambda p,*cs:cs[SCENES.index(p)],ztruth=lambda t:t=='anchor',
      r6d2=lambda *a:content(a,FVALUES),r6dk=lambda *a:content(a,FVALUES[:6]),r6d4=lambda *a:content(a,FVALUES),
      h26t4=lambda e,c,t,r:(e,t,r)==('example','anchor','reference') and codeid(c)==ACTUAL,
      h26t5=lambda e,c,p,r,t:(e,p,r,t)==('example','public','reference','assessment') and codeid(c)==CONCRETE,
      h26t6=lambda e,p,r,t:(e,p,r,t)==('example','public','reference','assessment'),
      aa=lambda p:p in ('ruler','other','author','reader'),
      r5ty=lambda g,r:(g,r)==('public','reference'),
      h246c=lambda g,p,r:(g,r)==('public','reference') and p in ('author','reader'),
      h26nu=lambda p,k,c,t:p in ('author','reader') and(k,t)==('ruler','assessment') and codeid(c)==REGARD,
      h257z=lambda r,h,t:(r,h)==('reference','history') and t in TIME,
      ic=lambda a,b,h:h=='history' and before(a,b),
      r2uj=lambda p,c,t:(p,c) in (('ruler','community'),('other','foreign')) and t in TIME,
      h26t7=lambda p,t,c,r,a:p in ('ruler','other') and t in TIME and codeid(c)==PATTERN and(r,a)==('reference','assessment'),
      h26ua=lambda *a:False,
      zhist=lambda t:t in TIME,zbefore=before,zscope=lambda p,t:p in ('ruler','other') and t in TIME,
      zassessed=lambda p,t:True,zbetter=lambda *a:False)
    return v
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def realized_checks():
    q='q[t[k r6d4['+FARGS+']]['+z('anchor')+']].'
    d=fixture(('r6d4',),q,('r6d2','r6dk'));v=model(d);assert run(d,v)==[True];rows={}
    for name in ('r6d2','r6dk'):
        w=dict(v);w[name]=lambda *a:Content(SCENES,(False,)*len(SCENES));assert run(d,w)==[False];rows[name+'_absent']=False
        w=dict(v);w[name]=unknown;rejects(d,w)
    for n in NAMES:
        w=dict(v);w['z'+n]=lambda n=n:'past' if n in DATES else 'other';assert run(d,w)==[False],n
    # Constructing the concrete quote does not execute its contents.
    code='k r6d5['+' '.join('r['+z(k)+']' for k in NAMES)+']'
    qd=fixture(('r6d5',),'q[e['+code+']['+code+']].',('r6d4',));w=model(qd);w['r6d4']=unknown;assert run(qd,w)==[True]
    ed=fixture(('r6d6',),'q[k r6d6['+z('example')+' r e[k zactual[]] '+args(('anchor','reference'))+']].');v=model(ed);assert run(ed,v)==[True]
    for case in ('imagined','false_content','other_content','other_instance','other_reference'):
        w=dict(v)
        if case=='imagined':w['h26t4']=lambda *a:False
        if case=='false_content':w['ztruth']=lambda *a:False
        if case=='other_content':w['h26t4']=lambda e,c,*a:codeid(c)==CONCRETE
        if case=='other_instance':w['h26t4']=lambda e,c,t,r:t=='past'
        if case=='other_reference':w['h26t4']=lambda e,c,t,r:r=='history'
        assert run(ed,w)==[False],case;rows[case]=False
    for n in ('h26t4','ztruth'):
        w=dict(v);w[n]=unknown;rejects(ed,w)
    return dict(cases=rows,all_eight_values_bound=True,quotation_does_not_execute=True,
      boundary='r6d2 and r6dk only for the native conjunction; r6d6 executes its quoted truth natively. Full policy/insight bodies have pinned prior reports.')

@lru_cache(None)
def precedence_checks():
    q='q[k r6d7[p zhist p zbefore p zscope p zassessed p zbetter '+args(('ruler','anchor','assessment'))+']].'
    d=fixture(('r6d7',),q);v=model(d);assert run(d,v)==[True];rows={}
    for case in ('equal_predecessor','past_superior','present_superior','future_superior','nonmonarch_superior','missing_past_assessment','missing_future_assessment','self_above_itself','empty_scope','target_not_monarch','point_after_cutoff','cyclic_history','missing_cutoff'):
        w=dict(v);want=True
        if case=='equal_predecessor':w['zbetter']=lambda *a:False
        if case in ('past_superior','present_superior','future_superior'):
            at={'past_superior':'past','present_superior':'assessment','future_superior':'future'}[case]
            w['zbetter']=lambda p,t,k,kt,at=at:(p,t,k,kt)==('other',at,'ruler','anchor');want=case=='future_superior'
        if case=='nonmonarch_superior':w['zbetter']=lambda p,*a:p=='reader'
        if case=='missing_past_assessment':w['zassessed']=lambda p,t:(p,t)!=('other','past');want=False
        if case=='missing_future_assessment':w['zassessed']=lambda p,t:t!='future'
        if case=='self_above_itself':w['zbetter']=lambda p,t,k,kt:(p,t)==(k,kt);want=False
        if case=='empty_scope':w['zscope']=lambda *a:False;want=False
        if case=='target_not_monarch':w['zscope']=lambda p,t:p=='other';want=False
        if case=='point_after_cutoff':w['zanchor']=lambda:'future';want=False
        if case=='cyclic_history':w['zbefore']=lambda a,b:before(a,b) or(a,b)==('future','past');want=False
        if case=='missing_cutoff':w['zhist']=lambda t:t in TIME and t!='assessment';want=False
        assert run(d,w)==[want],case;rows[case]=want
    for n in ('zhist','zbefore','zscope','zassessed','zbetter'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    # Move the cutoff to include the formerly irrelevant future superior.
    w=dict(v);w['zassessment']=lambda:'future';w['zbetter']=lambda p,t,k,kt:(p,t,k,kt)==('other','future','ruler','anchor')
    assert run(d,w)==[False]
    return dict(cases=rows,future_superior_rejected_when_cutoff_reaches_it=True,first_arrival_not_required=True,
      native='r6d7 and ta execute, including all scoped candidate times, comparison evaluation and ordered-history validation',unknown_rejected=True)

@lru_cache(None)
def connection_checks():
    q='q[k r6ed['+args(('example','author','public'))+' '+FARGS+' '+z('assessment')+']].'
    d=fixture(('r6ed',),q,('r6d4','r2uj','r5ty'));v=model(d)
    v['h26t4']=lambda e,c,t,r:(e,t,r)==('example','anchor','reference') and codeid(c)==CONCRETE
    assert run(d,v)==[True];rows={}
    for case in ('other_example','no_shared_access','not_outstanding','different_example_content','not_realized','author_outside_public','one_member_does_not_respect','different_honored_king','wrong_regard_aspect','invalid_public','foreign_monarch_superior','future_monarch_superior','missing_monarch_assessment','wrong_pattern','not_historically_monarch'):
        w=dict(v);want=False
        if case=='other_example':w['h26t6']=lambda e,*a:e=='other'
        if case=='no_shared_access':w['h26t6']=lambda *a:False
        if case=='not_outstanding':w['h26t5']=lambda *a:False
        if case=='different_example_content':w['h26t5']=lambda e,c,*a:codeid(c)==ACTUAL
        if case=='not_realized':w['r6d4']=lambda *a:Content(SCENES,(False,)*len(SCENES))
        if case=='author_outside_public':w['h246c']=lambda g,p,r:(g,p,r)==('public','reader','reference')
        if case=='one_member_does_not_respect':w['h26nu']=lambda p,*a:p=='author'
        if case=='different_honored_king':w['h26nu']=lambda p,k,*a:k=='other'
        if case=='wrong_regard_aspect':w['h26nu']=lambda p,k,c,t:codeid(c)==PATTERN
        if case=='invalid_public':w['r5ty']=lambda *a:False
        if case=='foreign_monarch_superior':w['h26ua']=lambda p,t,k,kt,c,r:(p,t,k,kt)==('other','past','ruler','anchor') and codeid(c)==PATTERN and r=='reference'
        if case=='future_monarch_superior':w['h26ua']=lambda p,t,*a:(p,t)==('other','future');want=True
        if case=='missing_monarch_assessment':w['h26t7']=lambda p,t,*a:(p,t)!=('other','past')
        if case=='wrong_pattern':w['h26t7']=lambda p,t,c,*a:codeid(c)==CONCRETE
        if case=='not_historically_monarch':
            w['r2uj']=lambda p,c,t:(p,c,t)==('ruler','community','anchor')
            w['h26ua']=lambda p,t,*a:(p,t)==('other','past');want=True
        assert run(d,w)==[want],case;rows[case]=want
    for n in NAMES:
        w=dict(v)
        if n not in DATES:w['znamepick']=lambda p,*cs,n=n:cs[DOMAIN.index('other' if p==n else p)]
        else:w['zrefpick']=lambda p,*cs,n=n:cs[SCENES.index('past' if p==n else p)]
        assert run(d,w)==[False],n
    for n in ('h26t4','h26t5','h26t6','h26t7','h26ua','h26nu','h246c','r2uj'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,all_eight_names_checked=True,
      native='r6ed/r6d5/r6d6/r6ea/r6d7/r6ec and ta execute; same concrete content, generic eight-role pattern and person-aspect quotes are inspected',
      boundaries='r6d4 only for the deep realized policy/cognition; r2uj only for historical monarch classification; r5ty only for the previously checked nonempty human-group condition')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0016');segments=[]
    for phrase in ('davon wir ein glänzendes Beispiel haben','wodurch noch kein Monarch demjenigen vorging','welchen wir verehren'):
        a=u['text'].index(phrase,390);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='realized_royal_example_and_no_qualitative_superior_yet_partial',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),interpretation=LIMITS,
      lexical_evidence=dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_5_1_1605',path=LEXICAL,entry='Vorgehen',locations=['1(1): figurative superiority','1(3): going before as an example'],
        adopted_reading='Qualitative superiority in the exemplified practice, bounded by the present; not first historical achievement.',certainty='Explicit contextual reading; the dictionary does not prove uniqueness.'),
      unresolved=['一般化の範囲、前段の君主との談話上の同定','原文箇所を固定した照応、Aber/noch/selbst/sogar、全文帰属・通読'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,SOURCE,LEXICAL,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();dep=dependency();assert not c.document['statements'] and len(old.document['statements'])==118
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
        for rank,label in enumerate(('','b','c','d','e','f','g')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks['r6d4']==4 and ranks['r6d6']==5 and ranks['r6d7']==0,ranks
    assert c.entries['h26nu']['arguments']==['holder','person','aspect','point']
    lex=unescape((ROOT/LEXICAL).read_text(encoding='utf-8'));assert 'Vorgehen' in lex and 'übertreffen' in lex and 'Nachahmung' in lex
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('realized',realized_checks),('precedence',precedence_checks),('connection',connection_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,SOURCE,LEXICAL,INVENTORY,*PRIORS,
      'scripts/compose_royal_example.py','scripts/check_royal_example.py','tests/test_royal_example.py',
      'scripts/compose_legislative_safety_insight.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='realized_example_regard_and_no_superior_yet_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
