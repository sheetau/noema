"""Check the course, same whole-view act, conditional scope and sentence links."""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_whole_view_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PC,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,parent,dependency,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/whole-view-sentence-v1.md';READING='data/whole-view-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v204.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json'
PRIORS=('reports/counterexpected-affairs-v1.json','reports/qualified-speech-sentence-v1.json','data/qualified-speech-sentence-reading-v1.json')
DOMAIN=tuple('abcdef');SCENES=('reference','oldreference','now','alt','other','context')
PATTERN='r b[k r6g3[]]';NORMAL='r b[k znormal[]]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def atom(n):return dict(kind='call',symbol=n,arguments=[])
def desc(rank,body):return rank,json.dumps(body,sort_keys=True)
def code(n,rank=5):return desc(rank,atom(n))
def norm(xs):return tuple(desc(x.rank,json.loads(x.syntax)) if hasattr(x,'syntax') else x for x in xs)
def applied(n):return desc(3,dict(kind='apply',function=dict(kind='function_ref',symbol=n),arguments=[atom('h26x3'),atom('h26x5')]))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=(),capture=False):
    d=deepcopy(catalog().document);d['statements']=[]
    for r in d['declarations']:
        if r['name'] in boundaries:r.update(kind='primitive',parameters=[p['sort'] for p in r['parameters']]);r.pop('body')
    extra='r zcourse[] a.r zperson[] a.r zactivity[] a.r zaspect[] a.r zreference[] d.r zpoint[] d.r zouter[] d.'
    extra+='r ztruth[d] c.d znormal[] e[b point[k ztruth[v point]]].r zcapture['+' '.join([PC]*4)+'] c.'
    prefix=parse('p:'+extra)['declarations'];ns={r['name'] for r in prefix}
    d['declarations']=prefix+d['declarations'];d['declarations']=closure(d,(*roots,*ns))
    if capture:query='q[k zcapture['+PATTERN+' k r6gq['+PATTERN+'] '+NORMAL+' k r6gq['+NORMAL+']]].'+query
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,memo=True):return evaluate(d,v,domain,SCENES,memo)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};codes=[]
    def capture(*xs):codes[:]=xs;return True
    v.update(zcourse=lambda:'b',zperson=lambda:'a',zactivity=lambda:'c',zaspect=lambda:'a',zreference=lambda:'reference',zpoint=lambda:'now',zouter=lambda:'other',
      h26x3=lambda:'b',h26x4=lambda:'a',h26x5=lambda:'reference',h26x6=lambda:'context',wa=lambda:'a',
      h26wo=lambda:'a',h26wp=lambda:'oldreference',h26wr=lambda:'a',h26ws=lambda:'b',h26km=lambda:'oldreference',h26kn=lambda _: 'now',
      ha=lambda a,b:a+b,hb=lambda a,b:a*b,hc=lambda a,b:a<b,hd=lambda x:F(int(x)),aa=lambda p:p in DOMAIN,
      zcapture=capture,ztruth=lambda t:t=='now')
    v.update(h26xu=lambda c,a,r:(c,r)==('b','reference') and a in DOMAIN,h26xw=lambda c,r:seq(DOMAIN if (c,r)==('b','reference') else ()),
      h26xv=lambda c,a,b,r:(c,r)==('b','reference') and (a,b) in (('a','b'),('b','c')),
      h26xx=lambda a,p,r:a in DOMAIN and(p,r)==('f','reference'),dg=lambda a,t:(a,t)==('c','now'),
      h26xy=lambda p,a,c,r,t:(p,a,c,r,t)==('a','c','b','reference','now'),
      h26xz=lambda a,x,r,t:(a,r,t)==('c','reference','now') and x in DOMAIN,
      h26x2=lambda act,a,b,r,t:(act,r,t)==('c','reference','now') and(a,b) in (('a','b'),('b','c')),
      h26xm=lambda c,p,r,a,t:(c,p,r,t)==('b','a','reference','now') and a in DOMAIN)
    return v,codes

@lru_cache(None)
def course_checks():
    d=fixture(('r6gw',),'q[k r6gw[k zcourse[] k zreference[]]].');v,_=model(d);assert run(d,v)==[True];cases={}
    for name in ('empty','singleton','omitted','duplicate','outside_edge','no_edge','reflexive_only','nonhuman','one_nonhuman_aspect','wrong_course','wrong_reference'):
        w=dict(v)
        if name=='empty':w.update(h26xw=lambda *a:seq(()),h26xu=lambda *a:False)
        if name=='singleton':w.update(h26xw=lambda *a:seq(('a',)),h26xu=lambda c,a,r:a=='a',h26xv=lambda *a:False)
        if name=='omitted':w['h26xw']=lambda *a:seq(DOMAIN[:-1])
        if name=='duplicate':w['h26xw']=lambda *a:seq((*DOMAIN,'a'))
        if name=='outside_edge':w.update(h26xw=lambda *a:seq(DOMAIN[:-1]),h26xu=lambda c,a,r:a!='f',h26xv=lambda c,a,b,r:(a,b)==('a','f'))
        if name=='no_edge':w['h26xv']=lambda *a:False
        if name=='reflexive_only':w['h26xv']=lambda c,a,b,r:a==b
        if name=='nonhuman':w['aa']=lambda *a:False
        if name=='one_nonhuman_aspect':w['h26xx']=lambda a,p,r:a!='f' and(p,r)==('f','reference')
        if name=='wrong_course':w['zcourse']=lambda:'c'
        if name=='wrong_reference':w['zreference']=lambda:'other'
        assert run(d,w)==[False],name;cases[name]=False
    for n in ('h26xu','h26xv','h26xw','h26xx','aa'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,native_exact_census_and_human_involvement=True,at_least_one_distinct_relevant_pair=True,all_edges_internal=True,unknown_rejected=True)

@lru_cache(None)
def whole_act_checks():
    q='q[k r6gx[k zperson[] k zactivity[] k zcourse[] k zreference[] k zpoint[]]].'
    d=fixture(('r6gx',),q);v,_=model(d);assert run(d,v)==[True];cases={}
    for name in ('missing_aspect','missing_relation','wrong_activity','wrong_person','wrong_course','wrong_reference','wrong_point','not_actual','scope_omission','scope_addition'):
        w=dict(v)
        if name=='missing_aspect':w['h26xz']=lambda a,x,r,t:x!='f' and(a,r,t)==('c','reference','now')
        if name=='missing_relation':w['h26x2']=lambda act,a,b,r,t:(a,b)==('a','b')
        if name.startswith('wrong_'):
            n={'activity':'zactivity','person':'zperson','course':'zcourse','reference':'zreference','point':'zpoint'}[name[6:]];w[n]=lambda:'other' if n in ('zreference','zpoint') else 'd'
        if name=='not_actual':w['dg']=lambda *a:False
        if name=='scope_omission':w['h26xm']=lambda c,p,r,a,t:a!='f'
        if name=='scope_addition':w.update(h26xu=lambda c,a,r:a!='f',h26xw=lambda *a:seq(DOMAIN[:-1]))
        assert run(d,w)==[False],name;cases[name]=False
    for n in ('dg','h26xy','h26xz','h26x2','h26xm'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    q='q[t[k r6gy[k zcourse[] k zperson[] k zreference[]]][k zpoint[]]].';d=fixture(('r6gy',),q);v,_=model(d)
    assert run(d,v)==[True]
    v.update(dg=lambda a,t:a in ('c','d') and t=='now',h26xy=lambda p,a,c,r,t:a in ('c','d') and(p,c,r,t)==('a','b','reference','now'),
      h26xz=lambda a,x,r,t:(r,t)==('reference','now') and ((a=='c' and x in 'abc') or(a=='d' and x in 'def')),
      h26x2=lambda act,a,b,r,t:act in ('c','d') and(r,t)==('reference','now'))
    assert run(d,v)==[False]
    return dict(cases=cases,one_same_native_consideration_act_required=True,two_partial_acts_cannot_be_merged=True,scope_exact_in_both_directions=True,unknown_rejected=True)

@lru_cache(None)
def generic_checks():
    q='q[t[k r6gz[k zcourse[] k zreference[]]][k zpoint[]]].'
    d=fixture(('r6gz',),q,('r6gw','r6gy','r6gv'));base,_=model(d);rows=[]
    for attending in product((False,True),repeat=2):
        for outcomes in product((False,True),repeat=2):
            v=dict(base);v['aa']=lambda p:p in 'ab';v['r6gw']=lambda c,r:(c,r)==('b','reference')
            v['r6gy']=lambda c,p,r:content(lambda t:p in 'ab' and attending['ab'.index(p)] and(c,r,t)==('b','reference','now'))
            v['r6gv']=lambda c,p,r,t:p in 'ab' and outcomes['ab'.index(p)] and(c,r,t)==('b','reference','now')
            want=all(not a or b for a,b in zip(attending,outcomes));assert run(d,v)==[want],(attending,outcomes)
            rows.append(dict(considering=attending,judgments=outcomes,value=want))
    v=dict(base);v.update(aa=lambda p:p=='a',r6gw=lambda *a:True,r6gy=lambda c,p,r:content(lambda t:p=='b'),r6gv=lambda *a:False)
    assert run(d,v)==[True]
    v['r6gw']=lambda *a:False;assert run(d,v)==[False]
    for n in ('r6gw','r6gy','r6gv'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(two_person_condition_matrix=rows,no_actual_considerer_required=True,nonhuman_not_quantified_as_observer=True,invalid_course_not_vacuously_true=True,
      boundary='r6gw/r6gy/r6gv for conditional truth table; native course, consideration and contextual consequence checked separately.')

def pattern_model(d):
    v,codes=model(d)
    v['r6f4']=lambda topic,c,r:content(lambda t:(topic,r)==('a','oldreference') and c in DOMAIN and t in ('now','other'))
    v['r6gc']=lambda standard,role,r:content(lambda t:(standard,role,r)==('a','b','oldreference') and t in ('now','other'))
    return v,codes
@lru_cache(None)
def pattern_checks():
    q=''.join('q[t[k '+n+'[]][k '+p+'[]]].' for p in ('zpoint','zouter') for n in ('r6gk','r6g3'))
    d=fixture(('r6gk','r6g3'),q,('r6f4','r6gc'));v,_=pattern_model(d);rows=[]
    for left,right,other_left,other_right in product((False,True),repeat=4):
        w=dict(v)
        w['r6f4']=lambda topic,c,r:content(lambda t:(topic,r)==('a','oldreference') and c in DOMAIN and ((t=='now' and left) or(t=='other' and other_left)))
        w['r6gc']=lambda s,role,r:content(lambda t:(s,role,r)==('a','b','oldreference') and ((t=='now' and right) or(t=='other' and other_right)))
        actual=left and right;alternative=other_left and other_right
        assert run(d,w)==[actual,actual,actual,alternative];rows.append(dict(actual=actual,alternative=alternative))
    for n,value in (('h26wo','b'),('h26wp','reference'),('h26wr','b'),('h26ws','a')):
        w=dict(v);w[n]=lambda value=value:value;assert run(d,w)==[False]*4,n
    w=dict(v);w['r6f4']=lambda *a:content(lambda t:a[1]=='a');assert run(d,w)==[False]*4
    for n in ('r6f4','r6gc'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(truth_assignments=len(rows),old_and_lifted_pattern_equal_at_anchor=True,alternative_truth_can_vary_independently=True,
      topic_reference_standard_role_and_all_communities_preserved=True,boundary='r6f4/r6gc; original full bodies and meanings pinned by the unchanged first-sentence report.')

def contextual_model(d):
    v,codes=pattern_model(d)
    def exact(x):return norm((x,))[0]
    v.update(h26xn=lambda c,a,r:codes[2 if a=='f' else 0],
      h26xo=lambda c,r,o,q,t,s:(c,r,o,t)==('b','reference','a','now') and exact(q)==exact(codes[0]) and s in ('alt','other'),
      h26xq=lambda c,o,r,t:seq(DOMAIN),h26xr=lambda c,o,r,t:F(1,3),
      h26xs=lambda o,f,r,t:(o,f,r,t)==('a','b','reference','now'),h26xt=lambda *a:False)
    def ranking(c,r,o,a,b,t):
        if (c,r,o,t)!=('b','reference','a','now'):return False
        order={exact(codes[0]):0,exact(codes[1]):1,exact(codes[2]):1,exact(codes[3]):0};return order[exact(a)]>=order[exact(b)]
    v['h26xp']=ranking;return v,codes
@lru_cache(None)
def local_integration_checks():
    q='q[k r6g4[k zcourse[] k zperson[] k zaspect[] k zreference[] k zpoint[]]].q[k r6gv[k zcourse[] k zperson[] k zreference[] k zpoint[]]].'
    d=fixture(('r6g4','r6gv','r6gq'),q,('r6f4','r6gc'),capture=True);v,codes=contextual_model(d);assert run(d,v)==[True,True,True];cases={}
    for name in ('wrong_content','unselected_aspect','empty_candidates','expected_pattern','ordinary_explanation','false_actual','all_paradoxical','nonparadox_exception_false'):
        w,cs=contextual_model(d);want=[True,True]
        if name=='wrong_content':w['h26xn']=lambda *a:cs[2];want=[False,False]
        if name=='unselected_aspect':w.update(h26xu=lambda c,a,r:a!='a',h26xw=lambda *a:seq(DOMAIN[1:]),h26xv=lambda c,a,b,r:(a,b)==('b','c'));want[0]=False
        if name=='empty_candidates':w['h26xo']=lambda *a:False;want[0]=False
        if name=='expected_pattern':w['h26xo']=lambda *a:a[-1]=='now';want[0]=False
        if name=='ordinary_explanation':w['h26xt']=lambda *a:True;want[0]=False
        if name=='false_actual':w['r6gc']=lambda *a:content(lambda t:False);want=[False,False]
        if name=='all_paradoxical':w['h26xn']=lambda *a:cs[0];want[1]=False
        if name=='nonparadox_exception_false':w['ztruth']=lambda *a:False;want[1]=False
        assert run(d,w)==[True,*want],(name,run(d,w));cases[name]=want
    for n in ('zcourse','zperson','zaspect','zreference','zpoint'):
        w,_=contextual_model(d);w[n]=lambda n=n:'other' if n in ('zreference','zpoint') else 'f';assert not run(d,w)[1],n
    for n in ('h26xn','h26xo','h26xs','h26xt','h26xp','h26xq','h26xr'):
        w,_=contextual_model(d);w[n]=unknown;rejects(d,w)
    return dict(cases=cases,real_closed_pattern_code_used=True,native_r6gu_and_r6gv_with_lifted_pattern=True,
      same_course_observer_aspect_reference_and_point=True,unknown_rejected=True,boundaries='Only the inherited r6f4/r6gc patterns; course, actual content, expectation, familiarity, comparison and census execute natively.')

@lru_cache(None)
def projections_checks():
    q='q[t[c[k r6g5[k zcourse[] k zreference[]]][k zperson[]]][k zpoint[]]].q[t[c[k r6g6[k zcourse[] k zreference[]]][k zperson[]]][k zpoint[]]].'
    d=fixture(('r6g5','r6g6'),q,('r6gy','r6gv'));v,_=model(d)
    v['r6gy']=lambda c,p,r:content(lambda t:(c,p,r,t)==('b','a','reference','now'))
    v['r6gv']=lambda c,p,r,t:(c,p,r,t)==('b','a','reference','now');assert run(d,v)==[True,True]
    for n in ('zcourse','zperson','zreference','zpoint'):
        w=dict(v);w[n]=lambda n=n:'other' if n in ('zreference','zpoint') else 'f';assert run(d,w)==[False,False]
    q=''.join('q[t[k '+n+'[]][k '+point+'[]]].' for point in ('zpoint','zouter') for n in ('r6g7','r6ha','r6hb'))
    d=fixture(('r6g7','r6ha','r6hb'),q,('r6g4','r6gz'));base,_=model(d)
    for a,b in product((False,True),repeat=2):
        v=dict(base);v['r6g4']=lambda c,o,x,r,t:a and(c,o,x,r,t)==('b','a','a','reference','now')
        v['r6gz']=lambda c,r:content(lambda t:b and(c,r,t)==('b','reference','now'));assert run(d,v)==[a,b,a and b]*2
    for n in ('h26x3','h26x4','h26x5','wa','h26kn'):
        w=dict(v);w[n]=lambda *a,n=n:'other' if n in ('h26x5','h26kn') else 'f';assert not run(d,w)[2],n
    for n in ('r6g4','r6gz'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(same_person_profiles=True,fixed_actual_anchor_for_both_sentence_parts=True,both_parts_required=True,
      boundaries='r6gy/r6gv for profiles; r6g4/r6gz for whole-content wiring. Native bodies checked in the other groups.')

@lru_cache(None)
def discourse_checks():
    nodes=(*NODE_INFO,'h26w4');domain=(*nodes,'author','course','wrong')
    d=fixture(('r6hc',),'q[k r6hc[]].');v,_=model(d);v.update({n:lambda n=n:n for n in nodes})
    v.update(wa=lambda:'author',h26x3=lambda:'course');whole=code('r6hb')
    pairs=(('h26w4','h26yd'),('h26ye','h26yf'),('h26yf','h26yg'),('h26yg','h26yh'),('h26yh','h26yi'),('h26yj','h26yk'),('h26yk','h26yl'),('h26yi','h26ym'),('h26ym','h26yn'))
    rows={'h26ub':{('h26yd','author',whole,'context')},
      'h26x7':{('h26ye','author',whole,code('r6gk'),'h26w4',code('r6g3',1),'context')},
      'h26ya':{('h26yh','author',whole,code('r6g7'),code('r6ha'),'context')},
      'h26yb':{('h26yi','author',whole,applied('r6g5'),applied('r6g6'),'context')},
      'h26yc':{(n,'author',whole,'h26yg','course','reference','context') for n in ('h26yk','h26ym')},
      'ue':{(a,b,'context') for a,b in pairs}}
    def values(expected):
        w=dict(v);w.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in expected.items()});return w
    assert run(d,values(rows),domain)==[True];mutations=0
    for n,rs in rows.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(rows);changed[n].remove(row);bad=list(row);bad[i]='__mismatch__';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain)==[False],(n,i);mutations+=1
    for n in rows:
        w=values(rows);w[n]=unknown
        try:run(d,w,domain)
        except ValueError as e:assert 'Unknown' in str(e),str(e)
        else:raise AssertionError(n)
    return dict(argument_mutations=mutations,whole_authorship_and_previous_evidence_linked=True,conditional_profiles_closed_without_execution=True,
      local_general_analogy=True,both_anaphors_same_course=True,source_order_bound=True,unknown_rejected=True)

FRAGMENTS=(
 ('So zeigt sich hier ',['h26x7','r6g2','r6g3'],'前文の政治的対比を受け、この場合に見て取れる結果として提示する。本文現在で一致する同じパターンを通常予測の候補状況へも評価できる形にする。'),
 ('ein befremdlicher nicht erwarteter ',['r6g4','r6gu','r6gp','r6gt'],'当の同じ局所側面が実際に成立し、通常の標準予測に一貫した肯定的見通しとして含まれず、馴染みの説明枠にも無理なく収まらない。'),
 ('Gang menschlicher Dinge; ',['r6gw','h26xu','h26xv','h26xx'],'人の行為・制度的立場・帰結に関わる複数の全関連側面とその間の関連を持つ同じ推移。'),
 ('so wie auch sonst, ',['h26ya','r6ha'],'当の例以外にも認める一般的なあり方と類比して提示する。後続の全体考察という条件を保持する。'),
 ('wenn man ',['r6gz','h26yb'],'一般の各人について、同じ人が後続の条件を満たす場合という条件付け。実際の考察者の存在を要求しない。'),
 ('ihn ',['h26yc','h26x3'],'先行のGangと同じ推移を考察対象にする。'),
 ('im Großen betrachtet, ',['r6gx','r6gy'],'同じ一つの実際の考察行為で、固定した全関連側面とその間の全関連を考慮し、評価対象を全体と一致させる。'),
 ('darin ',['h26yc','r6gv'],'同じ推移の内側の全関連側面を範囲とする。'),
 ('fast alles paradox ist.',['r6gv','r6gs','r6gr'],'全関連側面の具体的内容が成立し、少数の正の例外を除いて、その否定より見込まれにくいという反期待性を持つ。'))
def reading_record():
    u=unit();cursor=304;clauses=[]
    for fragment,ns,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in ns),ns
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=ns,reading=reading));cursor+=len(fragment)
    assert cursor==466 and sum(not c.isspace() for c in u['text'][304:cursor])==137
    return dict(status='whole_view_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[304,cursor],text=u['text'][304:cursor]),selection=selection_binding(catalog(),[120]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_whole_view_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=137,semantic_equivalence_automatically_proved=False,
      holistic_review=[r for _,_,r in FRAGMENTS]+['原文第二文を9断片と合わせて通読し、前文との接続、局所と一般の違い、一般の人への条件、同じ推移への二照応、不可解さ・非期待・反期待・ほとんど全ての区別を確認した。第一文と後続二文を含む段落全体の判断は別に行う。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:-1]==old.document['statements'] and len(c.document['statements'])==121
    for source in (old,dependency()):
        for n,e in source.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==19
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    first=read('data/qualified-speech-sentence-reading-v1.json');assert first['selection']==selection_binding(c,[119])
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/qualified-speech-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f','g','h')):
            try:parse(t+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    expected={n:0 if n in ('r6gw','r6gx','r6gy','r6g5') else 1 if n in ('r6g2','r6g3') else 2 for n in MEANINGS}
    assert ranks==expected,ranks
    return dict(preserved_statements=120,added_statements=1,preserved_whole_unit_reviews=19,preserved_first_sentence_review=True,
      new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('course',course_checks),('whole_act',whole_act_checks),('generic',generic_checks),('pattern',pattern_checks),('local_integration',local_integration_checks),('projections',projections_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,*PRIORS,
      'scripts/compose_whole_view_sentence.py','scripts/check_whole_view_sentence.py','tests/test_whole_view_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_prince_sentence.py','scripts/compose_qualified_speech_sentence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='whole_view_sentence_checked_under_explicit_reading',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[120],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
