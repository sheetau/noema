"""Check expectation scopes, strict comparison and exact almost-all census."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_counterexpected_affairs import ROOT,LIBRARY,BASIS,PC,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/counterexpected-affairs-v1.md';READING='data/counterexpected-affairs-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json';INDEX='data/semantic-review-index-v204.json'
PRIORS=('reports/qualified-speech-sentence-v1.json','reports/reasoned-concession-v1.json')
DOMAIN=tuple('abcdef');SCENES=('reference','now','alt','other')
Q='r b[k zodd[]]';NORMAL='r b[k znormal[]]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def code(x):return x.rank,json.dumps(json.loads(x.syntax),sort_keys=True)
def normalized(xs):return tuple(code(x) if hasattr(x,'syntax') else x for x in xs)
def sequence(xs):return SequenceValue(tuple(xs),'"individual"')
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=False):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    extra='r zobserver[] a.r zcourse[] a.r zaspect[] a.r zreference[] d.r zpoint[] d.r zpopulation[] j[a].r ztolerance[] b.'
    extra+='r ztruth[d] c.r znormaltruth[d] c.d zodd[] e[b point[k ztruth[v point]]].d znormal[] e[b point[k znormaltruth[v point]]].'
    extra+='r zscope[a] c.r zproperty[a] c.r zpossible[a '+PC+' d d] c.r zranking[a '+PC+' '+PC+' d] c.'
    extra+='r zcapture['+' '.join([PC]*4)+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+d['declarations'];d['declarations']=closure(d,(*roots,*ns))
    if capture:query='q[k zcapture['+Q+' k r6gq['+Q+'] '+NORMAL+' k r6gq['+NORMAL+']]].'+query
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown input accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*values):codes[:]=values;return True
    v.update(zobserver=lambda:'a',zcourse=lambda:'b',zaspect=lambda:'a',zreference=lambda:'reference',zpoint=lambda:'now',
      zpopulation=lambda:sequence(DOMAIN),ztolerance=lambda:F(1,3),zscope=lambda p:p in DOMAIN,zproperty=lambda p:p!='f',
      ztruth=lambda t:t in ('now','other'),znormaltruth=lambda t:t=='now',zcapture=capture,
      ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda t:F(int(t)),aa=lambda p:p in DOMAIN)
    return v,codes

@lru_cache(None)
def expectation_checks():
    q=''.join('q[k '+n+'['+Q+' k zobserver[] k zpoint[] p zpossible]].' for n in ('r6go','r6gp'))
    d=fixture(('r6go','r6gp'),q);base,_=model(d);rows=[]
    for selected_bits in product((False,True),repeat=2):
        selected={t for t,b in zip(('alt','other'),selected_bits) if b}
        for truth_bits in product((False,True),repeat=3):
            truth={t for t,b in zip(('now','alt','other'),truth_bits) if b};v=dict(base)
            v['ztruth']=lambda t,truth=truth:t in truth
            v['zpossible']=lambda o,q,t,s,selected=selected:(o,t)==('a','now') and s in selected
            expected=bool(selected) and selected<=truth;not_expected=bool(selected) and not expected
            assert run(d,v)==[expected,not_expected],(selected,truth)
            rows.append(dict(candidates=sorted(selected),true_at=sorted(truth),expected=expected,not_expected=not_expected))
    v=dict(base);v['zpossible']=unknown;rejected(d,v)
    v=dict(base);v['zpossible']=lambda *a:True;v['ztruth']=unknown;rejected(d,v)
    return dict(matrix=rows,nonempty_scope_required_on_both_sides=True,actual_truth_independent=True,
      absence_from_uniform_normal_forecast_not_opposite_prediction=True,unknown_rejected=True)

@lru_cache(None)
def comparison_checks():
    q='q[k r6gr['+Q+' k zobserver[] k zpoint[] p zranking]].'
    d=fixture(('r6gr','r6gq'),q,capture=True);rows=[]
    for bits in product((False,True),repeat=4):
        v,codes=model(d)
        def ranking(o,a,b,t):
            if (o,t)!=('a','now'):return False
            ids=[code(x) for x in codes[:2]];return bits[ids.index(code(a))*2+ids.index(code(b))]
        v['zranking']=ranking;expected=bits[0] and bits[3] and bits[2] and not bits[1]
        assert run(d,v)==[True,expected],bits;rows.append(dict(bits=list(bits),counterexpected=expected))
    v,codes=model(d);v['zranking']=lambda o,a,b,t:code(a)==code(b) or(code(a),code(b))==(code(codes[1]),code(codes[0]))
    v['ztruth']=lambda *a:False;assert run(d,v)==[True,False]
    v['ztruth']=lambda t:True;v['zranking']=unknown;rejected(d,v)
    quoted=fixture(('r6gq',),'q[e[k r6gq['+Q+']][k r6gq['+Q+']]].');v,_=model(quoted);v['ztruth']=unknown;assert run(quoted,v)==[True]
    return dict(native_rqts_weak_comparison_matrix=rows,actual_claim_required=True,tie_and_incomparability_rejected=True,
      negative_description_constructed_without_execution=True,unknown_rejected=True)

@lru_cache(None)
def almost_all_checks():
    d=fixture(('r6gs',),'q[k r6gs[k zpopulation[] p zscope p zproperty k ztolerance[]]].');base,_=model(d);rows=[]
    for bits in product((False,True),repeat=6):
        positive={p for p,b in zip(DOMAIN,bits) if b};v=dict(base);v['zproperty']=lambda p,positive=positive:p in positive
        expected=0<6-len(positive)<2;assert run(d,v)==[expected],bits;rows.append(dict(positives=len(positive),value=expected))
    cases={}
    for name,seq,scope,tolerance in (
      ('empty',(),(),F(1,3)),('omitted_exception',DOMAIN[:-1],DOMAIN,F(1,3)),('duplicate',(*DOMAIN,'a'),DOMAIN,F(1,3)),
      ('outside_scope',DOMAIN,DOMAIN[:-1],F(1,3)),('zero_tolerance',DOMAIN,DOMAIN,F(0)),('half_tolerance',DOMAIN,DOMAIN,F(1,2)),
      ('boundary',DOMAIN,DOMAIN,F(1,6)),('negative_tolerance',DOMAIN,DOMAIN,F(-1,3))):
        v=dict(base);v.update(zpopulation=lambda seq=seq:sequence(seq),zscope=lambda p,scope=scope:p in scope,ztolerance=lambda tolerance=tolerance:tolerance)
        assert run(d,v)==[False],name;cases[name]=False
    for n in ('zproperty','zscope','ztolerance'):
        v=dict(base);v[n]=unknown;rejected(d,v)
    v=dict(base);v['hd']=lambda t:F(1);assert run(d,v)==[False]
    return dict(six_item_truth_assignments=len(rows),positive_counts_accept_only_five_of_six=True,cases=cases,
      native_exact_census_and_indicator_checked=True,all_true_is_not_almost_all_under_reading=True,unknown_rejected=True)

@lru_cache(None)
def unfamiliar_checks():
    q='q[k r6gt['+Q+' k zobserver[] k zreference[] k zpoint[]]].';d=fixture(('r6gt',),q);rows=[]
    for known in product((False,True),repeat=2):
        familiar={p for p,b in zip(('a','b'),known) if b}
        for fits in product((False,True),repeat=2):
            adequate={p for p,b in zip(('a','b'),fits) if b};v,_=model(d)
            v['h26xs']=lambda o,f,r,t,familiar=familiar:(o,r,t)==('a','reference','now') and f in familiar
            v['h26xt']=lambda f,q,r,t,adequate=adequate:f in adequate and (r,t)==('reference','now')
            expected=bool(familiar) and not familiar&adequate;assert run(d,v)==[expected],(known,fits)
            rows.append(dict(familiar=sorted(familiar),adequate=sorted(adequate),value=expected))
    for n in ('h26xs','h26xt'):
        v,_=model(d);v.update(h26xs=lambda o,f,r,t:f=='a',h26xt=lambda *a:False);v[n]=unknown;rejected(d,v)
    return dict(matrix=rows,nonempty_familiar_frameworks_required=True,unfamiliar_framework_does_not_cancel_judgment=True,
      claim_truth_and_expectation_not_evaluated_here=True,unknown_rejected=True)

def contextual_model(d):
    v,codes=model(d)
    def content(c,a,r):return codes[2 if a=='f' else 0]
    def possible(c,r,o,q,t,s):return (c,r,o,t)==('b','reference','a','now') and code(q)==code(codes[0]) and s in ('alt','other')
    def ranking(c,r,o,a,b,t):
        if (c,r,o,t)!=('b','reference','a','now'):return False
        order={code(codes[0]):0,code(codes[1]):1,code(codes[2]):1,code(codes[3]):0}
        return order[code(a)]>=order[code(b)]
    v.update(h26xm=lambda c,o,r,a,t:(c,o,r,t)==('b','a','reference','now') and a in DOMAIN,h26xn=content,h26xo=possible,h26xp=ranking,
      h26xq=lambda c,o,r,t:sequence(DOMAIN),h26xr=lambda c,o,r,t:F(1,3),
      h26xs=lambda o,f,r,t:(o,f,r,t)==('a','b','reference','now'),h26xt=lambda *a:False)
    return v,codes

@lru_cache(None)
def context_checks():
    local='q[k r6gu[k zcourse[] k zobserver[] k zreference[] k zaspect[] k zpoint[]]].'
    almost='q[k r6gv[k zcourse[] k zobserver[] k zreference[] k zpoint[]]].'
    d=fixture(('r6gu','r6gv','r6gq'),local+almost,capture=True);v,codes=contextual_model(d);assert run(d,v)==[True,True,True];rows={}
    for variant in ('expected','familiar_explanation','no_framework','false_aspect','empty_candidates','nonhuman','empty_catalogue','omitted_exception','all_counterexpected'):
        w,cs=contextual_model(d);want=[True,True]
        if variant=='expected':w['h26xo']=lambda *a:a[-1]=='now';want[0]=False
        if variant=='familiar_explanation':w['h26xt']=lambda *a:True;want[0]=False
        if variant=='no_framework':w['h26xs']=lambda *a:False;want[0]=False
        if variant=='false_aspect':w['znormaltruth']=lambda *a:False;want[1]=False
        if variant=='empty_candidates':w['h26xo']=lambda *a:False;want[0]=False
        if variant=='nonhuman':w['aa']=lambda *a:False;want=[False,False]
        if variant=='empty_catalogue':w['h26xq']=lambda *a:sequence(());want[1]=False
        if variant=='omitted_exception':w['h26xq']=lambda *a:sequence(DOMAIN[:-1]);want[1]=False
        if variant=='all_counterexpected':w['h26xn']=lambda *a:cs[0];want[1]=False
        got=run(d,w);assert got==[True,*want],(variant,got);rows[variant]=want
    for n in ('zcourse','zobserver','zreference','zpoint'):
        w,_=contextual_model(d);w[n]=lambda n=n:'other' if n in ('zreference','zpoint') else 'c';assert run(d,w)==[True,False,False],n
    w,_=contextual_model(d);w['zaspect']=lambda:'f';assert run(d,w)==[True,False,True]
    for n in PRIMITIVES:
        w,_=contextual_model(d);w[n]=unknown;rejected(d,w)
    return dict(cases=rows,native_expectation_comparison_census_and_unfamiliarity_integrated=True,
      all_selected_contents_true_including_exceptions=True,same_course_observer_reference_aspect_and_point=True,unknown_rejected=True)

@lru_cache(None)
def provider_checks():
    q='q[k r6gu[k zcourse[] k zobserver[] k zreference[] k zaspect[] k zpoint[]]].q[k r6gv[k zcourse[] k zobserver[] k zreference[] k zpoint[]]].'
    d=fixture(('r6gu','r6gv','r6gq'),q,('r6gp','r6gs','r6gr'),capture=True);v,codes=contextual_model(d);calls=[]
    def expected(q,o,t,candidates):
        assert (code(q),o,t)==(code(codes[0]),'a','now');candidates('f',codes[2],'other','alt');return True
    def ranked(q,o,t,ranking):
        assert o=='a' and t=='now' and code(q) in (code(codes[0]),code(codes[2]))
        ranking('f',codes[2],codes[0],'other');return True
    def almost(population,scope,property,tolerance):
        assert population.items==DOMAIN and tolerance==F(1,3)
        for p in DOMAIN:assert scope(p) and property(p)
        return True
    v.update(r6gp=expected,r6gr=ranked,r6gs=almost)
    def record(name):
        def f(*a):calls.append((name,normalized(a)));return True
        return f
    v['h26xo']=record('h26xo');v['h26xp']=record('h26xp');assert evaluate(d,v,DOMAIN,SCENES,False)==[True,True,True]
    assert calls[0]==('h26xo',('b','reference','f',code(codes[2]),'other','alt')),calls
    assert calls[1:]==[('h26xp',('b','reference','f',code(codes[2]),code(codes[0]),'other'))]*6,calls
    return dict(alternative_observer_content_and_points_forwarded=True,scope_property_sequence_and_tolerance_bound=True,
      boundaries='r6gp/r6gs/r6gr only for adapter recording; all three native bodies run in context_checks.')

def reading_record():
    u=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017');segments=[]
    for phrase in ('befremdlicher nicht erwarteter','fast alles paradox'):
        a=u['text'].index(phrase);segments.append(dict(unit=u['id'],range=[a,a+len(phrase)],text=phrase,definitions=list(MEANINGS),status='explicit_interpretive_annotation'))
    return dict(status='nonexpectation_counterexpectation_and_almost_all_dependency',source_unit=u['id'],unit_sha256=u['text_sha256'],alignment=dict(segments=segments),
      interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,SOURCE,INVENTORY,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();assert not c.document['statements']
    for n,e in parent().entries.items():
        if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
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
    assert ranks=={n:0 if n in ('r6gq','r6gs','r6gt') else 2 for n in MEANINGS},ranks
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_bodies_and_meanings_unchanged=True,
      minimum_quote_ranks=ranks,roundtrips=True,new_verified_characters=0)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('expectation',expectation_checks),('comparison',comparison_checks),('almost_all',almost_all_checks),('unfamiliarity',unfamiliar_checks),('context',context_checks),('providers',provider_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,SOURCE,INVENTORY,INDEX,*PRIORS,
      'scripts/compose_counterexpected_affairs.py','scripts/check_counterexpected_affairs.py','tests/test_counterexpected_affairs.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='nonexpectation_counterexpectation_and_almost_all_checked_partial',document=LIBRARY,**results,alignment=read(READING)['alignment'],
      whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
