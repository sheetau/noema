"""Check whole conditional scope, fixed endpoints, discourse and source reading."""
from copy import deepcopy
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
from scripts.compose_collective_return_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,NODE_INFO,ORDER,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_scoped_counts import arithmetic

DOC='docs/collective-return-sentence-v1.md';READING='data/collective-return-sentence-reading-v1.json'
INDEX='data/semantic-review-index-v206.json';INVENTORY='artifacts/written-units-v1/kant-1784.json';SOURCE='data/tenth-paragraph-source-reading-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('government-causal-extension','germ-figurative-connection','civic-feedback','civic-choice-mediation','self-directed-choice','civic-human-agency','dignity-conforming-treatment','government-benefit-appraisal','nurtured-germ','germ-regime-connection','thinking-impulse-development','civic-spirit-sentence','attached-note'))
SENTENCES=('data/qualified-speech-sentence-reading-v1.json','data/whole-view-sentence-reading-v1.json','data/civic-spirit-sentence-reading-v1.json')
DOMAIN=('a','b');SCENES=('reference','caseone','casetwo','middle','late','other','context','note')
CONSTANTS=dict(community='b',lowerorder='a',higherorder='b',person='a',start='caseone',end='middle',late='late',point='other')
TRIPLE=('community','lowerorder','higherorder');SIX=(*TRIPLE,'start','end','late');ARGS=' '.join('k z'+n+'[]' for n in TRIPLE)
LOWER=('r6kb','r6jd','r6l7')
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def unit():return next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0017')
def args(names):return ' '.join('k z'+n+'[]' for n in names)
def content(f):return Content(SCENES,tuple(f(t) for t in SCENES))
def seq(xs):return SequenceValue(tuple(xs),'"individual"')
def desc(rank,body):return rank,json.dumps(body,sort_keys=True)
def code(n):return desc(5,dict(kind='call',symbol=n,arguments=[]))
def profile(n):return desc(4,dict(kind='function_ref',symbol=n))
def norm(xs):return tuple(desc(x.rank,json.loads(x.syntax)) if hasattr(x,'syntax') else x for x in xs)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=LOWER):
    d=deepcopy(catalog().document);d['statements']=[]
    for row in d['declarations']:
        if row['name'] in boundaries:row.update(kind='primitive',parameters=[p['sort'] for p in row['parameters']]);row.pop('body')
    d['declarations']=closure(d,roots)
    extra=''.join('r z'+n+'[] '+('a' if v in DOMAIN else 'd')+'.' for n,v in CONSTANTS.items())
    return parse(format_graph(d,'compact')+extra+query)
def model(d,selected=3,premise=3,result=3):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'};v.update(arithmetic());v.update({'z'+n:lambda x=x:x for n,x in CONSTANTS.items()})
    fixed=lambda c,l,h,r:(c,l,h,r)==('b','a','b','reference')
    cases=('caseone','casetwo')
    v.update(h26zj=lambda:'reference',h27aw=lambda:'context',wa=lambda:'a',h27c6=lambda c,r:'a',
      h26zi=fixed,r6kb=fixed,h27cl=lambda c,l,h,r,p:fixed(c,l,h,r) and p in DOMAIN,
      h27d2=lambda c,l,h,r,s:fixed(c,l,h,r) and s in cases and bool(selected&(1<<cases.index(s))),
      r6jd=lambda c,l,h,p:content(lambda s:(c,l,h)==('b','a','b') and p in DOMAIN and s in cases and bool(premise&(1<<cases.index(s)))),
      r6l7=lambda c,l,h,r,s,e,g,t:fixed(c,l,h,r) and(g,e,t)==('a','middle','late') and s in cases and bool(result&(1<<cases.index(s))),
      h27ck=lambda *a:seq(DOMAIN),aa=lambda p:p in DOMAIN,h237c=lambda p,c,r:p in DOMAIN and(c,r)==('b','reference'),r6jz=lambda c,r:(c,r)==('b','reference'))
    return v
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown accepted')

@lru_cache(None)
def conditional_checks():
    d=fixture(('r6mf','r6mg'),'q[t[k r6mf['+ARGS+']][k zpoint[]]].q[t[k r6mg[]][k zpoint[]]].');rows=0
    for selected,premise,result in product(range(4),repeat=3):
        v=model(d,selected,premise,result);expected=bool(selected and not(selected&premise&~result))
        assert run(d,v)==[expected]*2,(selected,premise,result);rows+=1
    # The universal condition does not assert that its antecedent is realized.
    assert run(d,model(d,premise=0,result=0))==[True,True]
    cases={}
    for label in ('empty_comparison','one_failing_comparison','wrong_reference','wrong_government','missing_endpoints'):
        v=model(d)
        if label=='empty_comparison':v['h26zi']=lambda *a:False
        if label=='one_failing_comparison':v['h26zi']=lambda c,l,h,r:(l,h,r)==('a','b','reference')
        if label=='wrong_reference':v['h26zj']=lambda:'other'
        if label=='wrong_government':v['h27c6']=lambda *a:'b'
        if label=='missing_endpoints':v['r6l7']=lambda *a:False
        got=run(d,v);assert got[-1] is False,(label,got);cases[label]=got
    # One of the same contributors lacking the antecedent prevents the whole
    # antecedent, even if another contributor has developed.
    d=fixture(('r6mb',),'q[k r6mb['+ARGS+' k zstart[]]].')
    for developed in range(4):
        v=model(d);v['r6jd']=lambda c,l,h,p:content(lambda t:t=='caseone' and bool(developed&(1<<DOMAIN.index(p))))
        assert run(d,v)==[developed==3]
    for n in ('h27d2','h27cl','r6jd','r6l7'):
        d=fixture(('r6mg',),'q[t[k r6mg[]][k zpoint[]]].');v=model(d);v[n]=unknown;rejects(d,v)
    return dict(all_64_two_case_conditionals=rows,contrasts=cases,false_antecedent_does_not_require_result=True,
      all_contributors_share_same_case_point=True,nonempty_all_comparisons_and_cases=True,unknown_rejected=True,
      boundary='r6kb/r6jd/r6l7 are pinned dependency boundaries in the truth matrix. The new conditional, population quantifier and both existential endpoints run natively.')

@lru_cache(None)
def native_scope_checks():
    d=fixture(('r6mf',),'q[t[k r6mf['+ARGS+']][k zpoint[]]].',('r6jz','r6jd','r6l7'))
    v=model(d);assert run(d,v)==[True];cases={}
    for label in ('empty_contributors','omitted_contributor','duplicate_contributor','nonhuman_contributor','outside_community','invalid_prior_population'):
        v=model(d)
        if label=='empty_contributors':v['h27ck']=lambda *a:seq(());v['h27cl']=lambda *a:False
        if label=='omitted_contributor':v['h27ck']=lambda *a:seq(('a',))
        if label=='duplicate_contributor':v['h27ck']=lambda *a:seq(('a','b','b'))
        if label=='nonhuman_contributor':v['aa']=lambda p:p=='a'
        if label=='outside_community':v['h237c']=lambda p,c,r:p=='a'
        if label=='invalid_prior_population':v['r6jz']=lambda *a:False
        assert run(d,v)==[False],label;cases[label]=False
    # A proper nonempty subset of the same population is permitted.
    v=model(d);v['h27ck']=lambda *a:seq(('a',));v['h27cl']=lambda c,l,h,r,p:p=='a';assert run(d,v)==[True]
    return dict(native_prior_r6kb_and_rcm_membership=True,contrasts=cases,causal_population_can_be_proper_subset=True,
      boundary='Only r6jz (already checked mental population/features), r6jd and r6l7 are bounded; the original cause-population body executes in the new conditional.')

@lru_cache(None)
def endpoint_checks():
    names=('r6mc','r6mh','r6mi','r6mj','r6mk','r6ml','r6mp','r6mq','r6mr')
    q='q[k r6mc['+args(SIX)+']].'+''.join('q[t[k '+n+'['+args(SIX)+']][k zpoint[]]].' for n in names[1:])
    lower=('r6l6','r6ke','r6kr','r6kz','r6ld','r6ly')
    d=fixture(names,q,lower);rows=0
    def values(flags):
        v=model(d)
        exact=(*('b','a','b'),'reference','caseone','middle','a','late')
        v['r6l6']=lambda *a:a==exact and flags[0]
        v['r6ld']=lambda *a:a==('b','reference','late') and flags[1]
        v['r6ly']=lambda *a:a==('a','b','reference','late') and flags[2]
        v['r6ke']=lambda *a:a==exact[:6] and flags[3]
        v['r6kr']=lambda *a:a==('b','reference','caseone','middle') and flags[4]
        v['r6kz']=lambda *a:a==exact[:6] and flags[5]
        return v
    for flags in product((False,True),repeat=6):
        a,b,c,e,f,g=flags;expected=[a and b and c,e,a,a and b and c,f,g,c,b,b and c]
        assert run(d,values(flags))==expected;rows+=1
    for n in (*SIX,'h26zj','h27c6'):
        v=values((True,)*6);key=n if n in ('h26zj','h27c6') else 'z'+n
        v[key]=lambda *a,n=n:'other' if n in ('start','end','late','h26zj') else 'b' if n in ('lowerorder','h27c6') else 'a'
        assert run(d,v)[0] is False,n
    # The two referent families preserve population and actual two-disposition
    # contents while quotation in the discourse does not execute those contents.
    d=fixture(('r6mn','r6mo'),'q[t[k r6mn['+ARGS+' k zperson[]]][k zpoint[]]].q[t[k r6mo[k zcommunity[] k zperson[]]][k zpoint[]]].',('r6ja',))
    from noema.constructed_semantics import FunctionValue
    v=model(d);v['r6ja']=lambda c,r:FunctionValue(('individual',),'content',lambda p:content(lambda t:(c,r,p)==('b','reference','a')))
    assert run(d,v)==[True,True];v['zperson']=lambda:'b';assert run(d,v)==[False,True]
    return dict(all_64_endpoint_component_assignments=rows,native_r6l7_conjoins_cause_human_and_appraisal=True,
      all_six_slots_reference_and_government_checked=True,actual_human_clause_outside_appraisal=True,
      referent_families_bound=True,boundary='The new wrappers and inherited r6l7 execute natively; their large semantic dependencies are pinned and separately checked, without treating boundary values as a whole social model.')

@lru_cache(None)
def discourse_checks():
    nodes=tuple(dict.fromkeys((*NODE_INFO,'h26zq','h27av','h27at','hzlv','hzlu','hzik','hzlw')));domain=(*nodes,'author','wrong')
    d=fixture(('r6ms',),'q[k r6ms[]].',('r6jw',));v=model(d);v.update({n:lambda n=n:n for n in nodes});v.update(wa=lambda:'author',r6jw=lambda:True,hzjl=lambda:'note')
    whole=code('r6mg')
    rows={
      'h26ub':{('h27ed','author',whole,'context')},
      'h27d4':{('h27ef','author',whole,'h26zq',code('r6ih'),'context')},
      'h27d3':{('h27ei','author',whole,profile('r6mh'),profile('r6mk'),profile('r6ml'),'context'),('h27ep','author',whole,profile('r6mp'),profile('r6mq'),profile('r6mr'),'context')},
      'h27d5':{('h27el','author',whole,'h27eg',profile('r6ml'),'h27ek',profile('r6mi'),'context')},
      'h27d6':{('h27em','author',whole,profile('r6ml'),profile('r6mi'),'context')},
      'h27d7':{('h27eh','author',whole,'h27at',profile('r6mn'),'context')},
      'h27ea':{('h27ej','author',whole,'h27eg',profile('r6mo'),'context')},
      'h27eb':{('h27eo','author',whole,profile('r6mp'),'context')},
      'h27ec':{('h27ed','author',whole,'hzlv','hzlu','hzik','context')},
      'ue':{(a,b,'context') for a,b in ORDER},
      'dg':{('hzlw','note')},'hzlx':{('hzlu','hzik','note'),('hzlv','hzik','note')},
      'hzly':{('hzlw','hzlu','hzlv','hzik','note')},'hzij':{('hzlw','hzlu','author','note')},
    }
    def values(expected):
        w=dict(v);w.update({n:lambda *a,allowed=rs:norm(a) in allowed for n,rs in expected.items()});return w
    assert run(d,values(rows),domain)==[True];mutations=0
    for n,rs in rows.items():
        for row in rs:
            for i in range(len(row)):
                changed=deepcopy(rows);changed[n].remove(row);bad=list(row);bad[i]='__mismatch__';changed[n].add(tuple(bad))
                assert run(d,values(changed),domain)==[False],(n,i);mutations+=1
    for a,b in ORDER:
        changed=deepcopy(rows);changed['ue'].add((b,a,'context'));assert run(d,values(changed),domain)==[False]
        w=values(rows);w[b]=lambda a=a:a;assert run(d,w,domain)==[False]
    w=values(rows);w['r6jw']=lambda:False;assert run(d,w,domain)==[False]
    for n in (*rows,'r6jw'):
        w=values(rows);w[n]=unknown
        try:run(d,w,domain)
        except ValueError as e:assert 'Unknown' in str(e),str(e)
        else:raise AssertionError(n)
    return dict(argument_mutations=mutations,same_whole_author_context_and_scoped_profiles=True,
      preserved_metaphor_required=True,native_existing_note_attachment=True,quoted_condition_and_profiles_not_executed=True,
      distinct_forward_order_without_reverse=True,unknown_rejected=True,
      boundary='Only r6jw is bounded; its original metaphor/apposition tests are pinned. Existing hzlz/rqsm and every new discourse condition execute natively.')

CLAUSES=(
 ([716,736],['r6mf','r6mg','h27d4','r6jq'],'Wennは同じ非空の全事例での条件で、dennは先行説明の継続。自然は形成力を持つ描写側の働き手であり、実在の意志や感情を断言しない。'),
 ([736,762],['r6ju','r6i5','r6jm','ryu'],'同じ低い制度への覆いの照応を保つ。硬さは固定した負荷条件での小さい変形の耐性で、現実に試験済みとはしない。'),
 ([762,772],['r6jg','r6jq','r6jv'],'形成初期の植物体としての同じ芽を、本人の二性向の組へ比喩的に対応させる。人・植物・性質を物理的に同一視しない。'),
 ([772,807],['r6jl','r6jm','ryl'],'同じ自然が同じ芽を世話し、固定した全比較範囲で優しさが最大であるという描写。最上級の同率を許し、成長成功による範囲縮小をしない。'),
 ([807,853],['r6je','r6jc','r6iw'],'nämlichの同格で芽を思考への好意的傾向と内的な促しの組として説明する。外的職務としての使命にはしない。'),
 ([853,871],['r6jd','r6i7','r6jo','r6mb'],'同じ低い制度下で各人の二性向が潜在から顕在へ発達し、原因側の全員について共通起点までに完了する。前件の現実の実在は断言しない。'),
 ([871,931],['r6mh','r6ke','r6mb','h27d7'],'soは同じ前件の後件。dieserは同じ芽・二性向を受け、同じ民衆の経験的な心的傾向への漸次の反作用を述べる。一定の既存差だけでは足りない。'),
 ([931,1000],['r6mk','r6ml','r6kz','h27d3','h27ea'],'同じ民衆の心的変化を介して、本人の理由による実行・意図的に控える能力の固定集団得点が徐々に増える。集団得点の増加を全員の単調増加へ強めない。'),
 ([1000,1057],['r6mi','r6l6','h27d5','h27d6'],'同じ原因が後の同じ政府原則の採用変化にも及ぶ。endlichは後の評価点、auchは作用先の追加、sogarは予想しにくい先への強調。完全な後件消失や必須の旧新置換を要求しない。'),
 ([1057,1094],['r6mp','r6ly','r6lu','h27eb'],'同じ政府が、その扱いを政府自身にも有益と肯定する非事実的判断。固定目標の達成見込みを比較し、実際の利益・採用・履行を導かない。selbstの同一受益対象を強調する。'),
 ([1094,1108],['r6lk','r6mo'],'同じ民衆の全人間成員へ総称を分配し、能力を得た者だけへ尊厳の対象を狭めない。'),
 ([1108,1139],['r6mq','r6mr','r6ld'],'同じ政治的終点に全成員が自分の理由による行為能力を持つ追加内容。政府の信念の内側だけに置かず、職務上の受動的遂行とは両立する。以前の理性・尊厳の不存在は加えない。'),
 ([1139,1172],['r6lg','r6li','r6lk','r6ll','r6lm'],'同じ本人に肯定的かつ価値上代替できない地位があり、同じ政府の全公的処遇で価値を独立の拘束理由として守る。政府利益への還元や発言許可だけへの縮小はしない。'),
 ([1172,1174],['hzlz','rqsm','h27ec'],'同じ文書の末尾標識と既存著者注u0020を結ぶ構造的参照。注の七文と全単位判断を保ち、直前文だけの理由や内容の重複にしない。'),
)
def reading_record():
    u=unit();cursor=716;clauses=[]
    for (start,end),names,reading in CLAUSES:
        assert start==cursor and all(n in catalog().entries for n in names),(start,names)
        clauses.append(dict(range=[start,end],text=u['text'][start:end],definitions=names,reading=reading));cursor=end
    assert cursor==1174 and sum(not c.isspace() for c in u['text'][716:1174])==383
    return dict(status='collective_return_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
      source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[716,1174],text=u['text'][716:1174]),selection=selection_binding(catalog(),[122]),
      clauses=clauses,interpretation=LIMITS,unresolved=[],decision='equivalent_under_stated_reading_for_collective_return_sentence',
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,newly_reviewed_sentence_characters=383,semantic_equivalence_automatically_proved=False,
      holistic_review=[r for _,_,r in CLAUSES]+['第四文の14範囲と全体を通読し、固定された全比較・全事例・同じ非空の原因側を共有する条件として確認した。前件の比喩と対象側、因果モデルと現実の実証、能力と実行、利益判断と実際の利益、一般方針と採用・履行を区別した。前件から後の二終点への量化、心的反作用・媒介・政府原則の共通原因、同じ政治的終点の二関係節、談話の継続・追加・強調、芽・民衆・政府・本人の指示を確認した。局所検査だけをこの通読判断に代用していない。第十段落全体の四文の接続判断は別記録で行う。'],
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,CORE,BASIS,ANNOTATIONS,DOC,INVENTORY,SOURCE,*PRIORS,*SENTENCES)})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert c.document['statements'][:-1]==old.document['statements'] and len(c.document['statements'])==123
    for prior in (old,*dependencies()):
        for n,e in prior.entries.items():
            if n in c.entries:assert c.entries[n]['declaration']==e['declaration'] and c.entries[n]['meaning_ja']==e['meaning_ja'],n
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784'];assert len(reviews)==19
    for row in reviews:assert row['selection']==selection_binding(c,[s['index'] for s in row['selection']['statements']])
    for path,index in zip(SENTENCES,(119,120,121)):assert read(path)['selection']==selection_binding(c,[index])
    for p in (*PRIORS,SOURCE,*SENTENCES):validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256']);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert read(ANNOTATIONS)['entries']==read('data/civic-spirit-sentence-identifiers-v1.json')['entries'];assert read(READING)==reading_record()
    for p,b in build().items():assert(ROOT/p).read_text(encoding='utf-8')==b,p
    core=parse((ROOT/CORE).read_text(encoding='utf-8'));text=format_graph(core,'compact')
    for notation in ('compact','full'):
        t=format_graph(core,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==core
    ranks={}
    for n in MEANINGS:
        for rank,label in enumerate(('','b','c','d','e','f','g')):
            try:parse(text+'q[e[r '+label+'[p '+n+']][r '+label+'[p '+n+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[n]=rank;break
    assert ranks=={n:3 if n=='r6ms' else 0 if n in ('r6me','r6mo','r6mk','r6mq') else 1 for n in MEANINGS},ranks
    return dict(preserved_statements=122,added_statements=1,preserved_whole_unit_reviews=19,preserved_three_sentence_reviews=True,
      new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),minimum_quote_ranks=ranks,roundtrip_scope='new core compact/full/v2; inherited manuscript and meanings unchanged')

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('conditional',conditional_checks),('native_scope',native_scope_checks),('endpoints',endpoint_checks),('discourse',discourse_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,SOURCE,*PRIORS,*SENTENCES,
      'scripts/compose_collective_return_sentence.py','scripts/check_collective_return_sentence.py','tests/test_collective_return_sentence.py',
      'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py'}
    return dict(status='collective_return_sentence_checked_under_explicit_reading',document=FULL,**results,
      alignment=dict(**read(READING)['source'],statements=[122],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
      whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
      source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
