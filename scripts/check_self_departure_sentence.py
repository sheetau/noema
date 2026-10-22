"""Check shared prospective courses and the complete fifth sentence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_self_departure_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,PROVIDERS,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/self-departure-sentence-v1.md';READING='data/self-departure-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v200.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/deliberate-retention-v1.json','reports/gradual-self-departure-v1.json','reports/noninterference-interval-v1.json','reports/manifest-example-sentence-v1.json')
SOURCE='data/eighth-paragraph-source-reading-v2.json'
SENTENCES=('data/prince-sentence-reading-v1.json','data/public-offers-sentence-reading-v1.json','data/spreading-spirit-sentence-reading-v1.json','data/manifest-example-sentence-reading-v1.json')
DOMAIN=('person','other','casea','caseb');SCENES=('reference','first','middle','last','outside')
def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for row in d['declarations']:
        if row['name'] in boundaries:
            row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r zhistory[d] c.r zbefore[d d] c.r zotherhistory[d] c.r zotherbefore[d d] c.'
    for role,(n,t) in PROVIDERS.items():
        forms={'history':('p zhistory','p zotherhistory'),'before':('p zbefore','p zotherbefore'),'first':(z('first'),z('middle'))}[role]
        extra+='r z'+role+'pick[a a a d '+t+' '+t+'] '+t+'.'
        extra+='d '+n+'[group a person a candidate a reference d] '+t+'[k z'+role+'pick[v group v person v candidate v reference r['+forms[0]+'] r['+forms[1]+']]].'
    p=parse('p:'+extra);ns={r['name'] for r in p['declarations']}
    d['declarations']=p['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v,domain=DOMAIN,scenes=SCENES):return evaluate(d,v,domain,scenes,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')
def model(d):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p in ('person','other'),h246c=lambda g,p,r:g=='casea' and p in ('person','other') and r=='reference',
        zhistory=lambda t:t in ('first','middle','last'),zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b),
        zotherhistory=lambda t:t in ('middle','last','outside'),zotherbefore=lambda a,b:SCENES.index(a)>SCENES.index(b),
        h26rv=lambda g,p,c,r:g=='casea' and p in ('person','other') and c in ('casea','caseb') and r=='reference',
        h26ru=lambda:'casea',h26pp=lambda:'reference',h26rh=lambda p,r,t:p in ('person','other') and r=='reference' and t=='first')
    for role in PROVIDERS:v['z'+role+'pick']=lambda g,p,c,r,a,b:a if c=='casea' else b
    return v
FRAME=args(('casea','person','reference'))+' p zhistory p zbefore '+z('first')

@lru_cache(None)
def horizon_checks():
    d=fixture(('r6ba','r6bb','r6bc'),''.join('q[k '+n+'['+(('p zhistory p zbefore '+z('first')) if n=='r6ba' else FRAME)+']].' for n in ('r6ba','r6bb','r6bc')),('r6a5','r6a6'))
    v=model(d);v.update(r6a5=lambda *a:False,r6a6=lambda *a:True);assert run(d,v)==[True,True,True]
    count=0
    for actor,activity,target,point in product(DOMAIN,DOMAIN,('person','other'),('first','middle','last')):
        row=(actor,activity,target,'reference',point)
        w=dict(v);w['r6a5']=lambda *a,row=row:a==row;assert run(d,w)==[True,True,False]
        w=dict(v);w['r6a6']=lambda *a,row=row:a!=row;assert run(d,w)==[True,False,True];count+=1
    cases={}
    for case in ('outside_time','outside_person','no_future','missing_start','earlier_point','cycle'):
        w=dict(v)
        if case=='outside_time':w['r6a5']=lambda *a:a[-1]=='outside'
        if case=='outside_person':w['r6a5']=lambda *a:a[2]=='caseb'
        if case=='no_future':w['zhistory']=lambda t:t=='first'
        if case=='missing_start':w['zhistory']=lambda t:t in ('middle','last')
        if case=='earlier_point':w['zhistory']=lambda t:t!='outside'
        if case=='cycle':w['zbefore']=lambda a,b:v['zbefore'](a,b) or (a,b)==('last','first')
        got=run(d,w);assert got[0]==(case in ('outside_time','outside_person')),(case,got);assert got[1:]==[True,True];cases[case]=got
    for n in ('r6a5','r6a6','zhistory','zbefore','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(all_interference_and_gap_positions=count,cases=cases,unknown_rejected=True,
        boundary='Only r6a5/r6a6 are prior exact five-argument boundaries. Ordered history, all quantifiers, member scope and the absence relation execute natively.')

@lru_cache(None)
def conditional_checks():
    d=fixture(('r6be',),'q[k r6be['+FRAME+']].',('r6bb','r6bc','r6bd'));rows=[]
    for complete,raw,absent,departed in product((False,True),repeat=4):
        v=model(d);v.update(r6bb=lambda *a:complete,r6bc=lambda *a:absent,r6bd=lambda *a:departed,h26rh=lambda *a:raw)
        got=run(d,v)[0];assert got==(complete and (not raw or not absent or departed))
        rows.append(dict(complete=complete,initially_raw=raw,noninterference=absent,departure=departed,value=got))
    v=model(d);v.update(r6bb=lambda *a:True,r6bc=lambda *a:True,r6bd=lambda *a:True)
    # A missing description must never make a conditional true via a false antecedent.
    for n in ('r6bb','r6bc','r6bd','h26rh'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    seen={n:[] for n in ('r6bb','r6bc','r6bd')}
    for n in seen:
        v[n]=lambda g,p,r,h,b,f,n=n:seen[n].append((g,p,r,tuple(h(t) for t in SCENES),tuple(b(a,c) for a,c in product(SCENES,repeat=2)),f)) is None
    assert run(d,v)==[True];assert seen['r6bb']==seen['r6bc']==seen['r6bd'] and len(seen['r6bb'])==1
    return dict(truth_table=rows,quality_outside_implication=True,all_six_arguments_shared=True,unknown_rejected=True,
        boundary='r6bb/r6bc/r6bd bodies have separate native evidence; this check executes ordering, raw-state restriction and the one-way conditional without world-content attribution.')

@lru_cache(None)
def provider_checks():
    d=fixture(('r6bf',),'q[k r6bf['+args(('casea','person','caseb','reference'))+']].',('r6be',));v=model(d);seen=[]
    def accept(g,p,r,h,b,f):
        seen.append((g,p,r,tuple(h(t) for t in SCENES),tuple(b(a,c) for a,c in product(SCENES,repeat=2)),f))
        return (g,p,r,f)==('casea','person','reference','middle') and all(h(t)==v['zotherhistory'](t) for t in SCENES) and all(b(a,c)==v['zotherbefore'](a,c) for a,c in product(SCENES,repeat=2))
    v['r6be']=accept;assert run(d,v)==[True];assert len(seen)==1
    count=0
    for role in PROVIDERS:
        base=v['z'+role+'pick']
        for i in range(4):
            w=dict(v)
            w['z'+role+'pick']=lambda *a,i=i,base=base:base(*a) if a[i]!=('casea','person','caseb','reference')[i] else a[-2]
            assert run(d,w)==[False],(role,i);count+=1
        w=dict(v);w['z'+role+'pick']=unknown;rejects(d,w)
    return dict(each_provider_context_argument_mutations=count,all_three_codes_decoded=True,same_function_truth_tables_and_first=True,unknown_rejected=True)

@lru_cache(None)
def outcome_checks():
    # Execute the existing gradual departure body underneath the new eventuality.
    from scripts import check_gradual_self_departure as prior
    d=prior.fixture('');decl=next(r for r in catalog().document['declarations'] if r['name']=='r6bd')
    d['declarations'].append(deepcopy(decl))
    q='q[k r6bd['+prior.args(('person','person','reference'))+' p zhistory p zbefore '+prior.z('first')+']].'
    d=parse(format_graph(d,'compact')+q);v=prior.model(d);assert prior.run(d,v)==[True];rows={}
    for case in ('no_result','other_person','no_own_initiative','single_jump','later_completion'):
        w=dict(v)
        if case=='no_result':w['g3']=lambda *a:False
        if case=='other_person':w['la']=lambda p,proc,a,b:p=='other'
        if case=='no_own_initiative':w['h26rn']=lambda *a:False
        if case=='single_jump':w=prior.model(d,(0,0,0,0,3))
        if case=='later_completion':w=prior.model(d,(0,1,1,2,3))
        got=prior.run(d,w);assert got==[case=='later_completion'],(case,got);rows[case]=got[0]
    return dict(cases=rows,native_gradual_body_and_eventual_quantifiers=True,attainment_not_fixed_to_an_arbitrary_deadline=True,
        boundary='The full r6a4/rcp/self-work/result/degree body executes natively with the prior qualitative numerical test fixture; this does not prove actual human development.')

@lru_cache(None)
def population_checks():
    q=''.join('q[t[k r6bh[]]['+z(t)+']].' for t in ('first','outside'))
    d=fixture(('r6bh',),q,('r6bf',));v=model(d);v['r6bf']=lambda *a:True;assert run(d,v)==[True,True];rows={}
    for person,candidate in product(('person','other'),('casea','caseb')):
        w=dict(v);w['r6bf']=lambda g,p,c,r:p!=person or c!=candidate
        assert run(d,w)==[False,False]
    for case in ('empty_group','nonhuman_member','one_person_no_candidates','only_second_succeeds','outside_person','wrong_reference'):
        w=dict(v)
        if case=='empty_group':w['h246c']=lambda *a:False
        if case=='nonhuman_member':w['aa']=lambda p:p=='person'
        if case=='one_person_no_candidates':w['h26rv']=lambda g,p,c,r:p=='person' and v['h26rv'](g,p,c,r)
        if case=='only_second_succeeds':w['r6bf']=lambda g,p,c,r:c=='caseb'
        if case=='outside_person':w['r6bf']=lambda g,p,c,r:p!='caseb'
        if case=='wrong_reference':w['h26pp']=lambda:'outside'
        got=run(d,w);assert got==[case=='outside_person']*2,(case,got);rows[case]=got
    for n in ('h26rv','r6bf','h246c'):
        w=dict(v);w[n]=unknown;rejects(d,w)
    return dict(cases=rows,every_person_and_every_candidate=True,empty_inputs_rejected=True,outer_point_does_not_move_context=True,unknown_rejected=True)

@lru_cache(None)
def discourse_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,('r6bi',)),statements=[]);d=parse(format_graph(d,'compact')+'q[k r6bi[]].')
    nodes=('h26ra','h26r3','h26r4');domain=(*nodes,'author','other');scenes=('context',)
    code=lambda n,ref=False:(1,json.dumps(dict(kind='function_ref',symbol=n) if ref else dict(kind='call',symbol=n,arguments=[]),sort_keys=True))
    norm=lambda xs:tuple((v.rank,json.dumps(json.loads(v.syntax),sort_keys=True)) if hasattr(v,'syntax') else v for v in xs)
    expected={'hzon':{('h26r3','author',code('r6bh'),'context')},
        'h26r2':{('h26r4','author',code('r6bh'),code('r6bc',True),code('r6bd',True),'context')},
        'ue':{('h26ra','h26r3','context'),('h26r3','h26r4','context')}}
    def values(rows):
        v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
        v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',h26rz=lambda:'context')
        v.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in rows.items()});return v
    assert run(d,values(expected),domain,scenes)==[True];count=0
    for n,rs in expected.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(expected);changed[n].remove(row);bad=list(row);bad[i]='other';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain,scenes)==[False];count+=1
    for i,n in enumerate(nodes):
        for other in nodes[i+1:]:
            v=values(expected);v[n]=lambda other=other:other
            for name in expected:v[name]=lambda *a:True
            assert run(d,v,domain,scenes)==[False]
    for n in expected:
        v=values(expected);v[n]=unknown
        try:run(d,v,domain,scenes)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown attribution accepted')
    assert all(values(expected)[n] is unknown for n in ('h26rv','h26rh','h26rk','h26rn'))
    return dict(argument_mutations=count,nur_same_bound_condition_and_result=True,quotation_not_executed=True,unknown_rejected=True)

FRAGMENTS=(
 ('Die Menschen ',['r6bg','r5ty'],'文脈内の人々一般を非空の範囲とし、各人・全関連候補を量化する。'),
 ('arbeiten sich ',['r6az','r6a2','r6bd'],'本人の精神的自己形成と同じ本人への結果生成を結び、後の達成を後件で量化する。'),
 ('von selbst ',['r6a2','h26rn'],'本人の関心・経験・検討からの働きかけ。助言や教育、努力を排除しない。'),
 ('nach und nach ',['r6ax','r6a3','r6a4'],'同じ形成面の厳密な中間段階を通る質的進行。停滞や後退を許す。'),
 ('aus der Rohigkeit heraus, ',['r6ap','r6ay','r6az'],'同じ未陶冶からその不成立への変化。未成熟一般や全人格の完成とはしない。'),
 ('wenn man nur nicht ',['r6bb','r6bc','r6be','r6bi'],'全経過の非介入を十分条件とする。全行為者を扱い、nurは条件の最小要求の提示。'),
 ('absichtlich künstelt, ',['r6as','r6a5'],'選択・統御された作為的操作を、実行と同じ活動・対象・点に結ぶ。'),
 ('um sie darin zu erhalten.',['r6aq','r6ar','r6at','r6a5','r6a6'],'同じ人々を同じ未陶冶に保つ目的。全保持目的設定を扱い、未来の保持成功は要求しない。'))
def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015');cursor=1210;clauses=[]
    for fragment,names,reading in FRAGMENTS:
        assert u['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==1354 and sum(not c.isspace() for c in u['text'][1210:cursor])==121
    return dict(status='self_departure_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1210,cursor],text=u['text'][1210:cursor]),selection=selection_binding(catalog(),[116]),
        clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_self_departure_sentence',
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=121,semantic_equivalence_automatically_proved=False,
        primary_evidence=[dict(path=SOURCE,observation='固定原文の第五文と原刊492頁の同文を、先行四文の文脈と共に再読。')],
        holistic_review=[
            '144文字・121非空白文字を八断片と全文で再読。対象範囲、本人の作業、自己からの働きかけ、質的漸進、同じ未陶冶からの離脱、条件・否定・限定、意図的操作とその同じ人・同じ状態の保持目的を接続した。',
            '非介入と結果は同じ本人・候補経過を共有し、全関連候補を成功や非介入で選別しない。各人の開始点は異なり得て、達成点は後件の内側に置く。全員同時の既成事実や任意の短い締切は補わない。',
            '条件は全将来経過で操作がないという持続的な読み。途中から妨害される経過に対し、妨害前の短期間内の完了は要求しない。この採用解釈を、原文がただ一つの時間粒度を指定したという主張と分けた。',
            '対象・候補・目的設定の非空性と完全性、順序の妥当性を、条件が偽であることによる空虚な成立から分けた。既に状態を離れた人に再離脱を課さず、対象となる人の失敗は他人の成功で補わない。',
            'nurは十分条件を最小要求として提示する関係に結び、必要条件や他の原因の全面排除にしない。著者帰属は閉じた全文へ行い、そのために現実の成長を実行・実証しない。',
            '先行四文の具体的な自由の例から人々一般への記述の広がりを保ち、本文順序を結ぶ。第五文単独で段落全体を意味確認済みと数えず、原刊照合v2と先行判断を保存する。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS)})
@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:116]==old.document['statements'] and len(c.document['statements'])==117
    assert all(c.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==17
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for p,i in zip(SENTENCES,range(112,116)):assert read(p)['selection']==selection_binding(c,[i])
    for p in (*PRIORS,SOURCE):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/manifest-example-sentence-identifiers-v1.json')['entries']
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={};t=format_graph(core,'compact')
    for name in ('r6bc','r6bd','r6bh'):
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert ranks=={'r6bc':1,'r6bd':1,'r6bh':1},ranks
    return dict(preserved_statements=116,added_statements=1,preserved_whole_unit_reviews=17,preserved_prior_sentence_characters=1033,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_reviewed_sentence_characters=121,minimum_quote_ranks=ranks,
        roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('horizon',horizon_checks),('conditional',conditional_checks),('providers',provider_checks),('outcome',outcome_checks),('population',population_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,*PRIORS,*SENTENCES,
        'scripts/compose_self_departure_sentence.py','scripts/check_self_departure_sentence.py','tests/test_self_departure_sentence.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_gradual_self_departure.py'}
    return dict(status='self_departure_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[116],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
