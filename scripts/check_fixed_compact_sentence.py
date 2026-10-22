"""Verify the eighth sentence's bindings, scope, quotation and source reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_fixed_compact_sentence import ROOT,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,LIMITS,NAMES,NODES,NODE_INFO,parent,dependencies,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_persistent_compact_progress import base as period_base,SCENES,DOMAIN,EXTRA

INDEX='data/semantic-review-index-v186.json'
REPORT='reports/fixed-compact-sentence-v1.json'
READING='data/fixed-compact-sentence-reading-v1.json'
DOC='docs/fixed-compact-sentence-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/provisional-order-sentence-v1.json','reports/fixed-religious-compact-v1.json','reports/persistent-compact-progress-v1.json','reports/compact-causal-denial-v1.json','reports/posterity-harm-v1.json')

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def content(points):return Content(SCENES,tuple(p in points for p in SCENES))
def base(d,bindings=('alpha',)*6):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(zbindings=lambda:SequenceValue(bindings,'"individual"'),h26b7=lambda:'reference',h26ax=lambda:'alpha',h26fh=lambda:'beta')
    return v

@lru_cache(None)
def generic_checks():
    d=fixture(('r5ki',),'q[t[k r5ki[]][k zcandidate[]]].',('r5js',));rows={}
    first=('alpha',)*6;second=('beta','beta','alpha','beta','alpha','beta')
    for variant in ('baseline','missing_second_ban','missing_consequence','wrong_source','wrong_role','wrong_reference','positive_sign','empty_scope'):
        v=base(d)
        v['r5js']=lambda *a:a[:-2] in (first,second) and a[-2:]==('reference','candidate') and variant!='empty_scope'
        def norm(source,group,role,target,b,r,sign,p):
            s=normalized(b)
            return (source,role,normalized(target),r,sign,p)==('alpha','beta',('r5jt',1),'reference',variant=='positive_sign','candidate') and s in(first,second) and group==s[0] and not(variant=='missing_second_ban' and s==second)
        v['h237z']=norm
        v['h253x']=lambda cause,cb,result,rb,r,p:normalized((cause,result,r,p))==(('r5jx',2),('r5jo',2),'reference','candidate') and normalized(cb)==normalized(rb) and variant!='missing_consequence'
        if variant=='wrong_source':v['h26ax']=lambda:'beta'
        if variant=='wrong_role':v['h26fh']=lambda:'alpha'
        if variant=='wrong_reference':
            v['h26b7']=lambda:'assessment'
            # Keep cases present at the changed context, so this checks bindings
            # rather than vacuous truth caused by an empty scope.
            v['r5js']=lambda *a:a[:-2] in(first,second) and a[-2:]==('assessment','candidate')
        actual=run(d,v);assert actual==[variant in ('baseline','empty_scope')],(variant,actual);rows[variant]=actual[0]
    return dict(all_candidates_fixed_source_role_reference_and_first_consequence=rows,
        no_harm_or_actual_formation_required=True,boundary='r5js; native scope preserved in compact-causal-denial')

@lru_cache(None)
def adapter_checks():
    rows={}
    for root,target in (('r5kd','r5js'),('r5ke','r5ju'),('r5kf','r5jr'),('r5kg','r5jo')):
        d=fixture((root,),'q[t[k '+root+'[k zbindings[] k zreference[]]][k zcandidate[]]].',(target,));positions=[]
        for i in range(6):
            six=tuple('beta' if j==i else 'alpha' for j in range(6));v=base(d,six)
            if root=='r5kd':v[target]=lambda *a:a==(*six,'reference','candidate')
            elif root=='r5ke':v[target]=lambda *a:a==('alpha',six[0],'beta',*six[1:],'reference','candidate')
            elif root=='r5kf':v[target]=lambda *a:a==(*six[1:],'reference','candidate')
            else:v[target]=lambda b,r:content({'candidate'} if normalized(b)==six[1:] and r=='reference' else set())
            assert run(d,v)==[True],(root,i)
            v['zbindings']=lambda:SequenceValue(('alpha',)*6,'"individual"')
            assert run(d,v)==[i==0 and root in ('r5kf','r5kg')],(root,i);positions.append(i)
        for length in (5,7):
            v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v)==[False]
        rows[root]=positions
    return dict(exact_six_adapters=rows,group_dropped_only_from_five_object_consequences=True,
        boundaries=['r5js','r5ju','r5jr','r5jo; each native dependency preserved'])

@lru_cache(None)
def lifetime_checks():
    d=fixture(('r5kd','r5kh'),'q[t[k r5kd[k zbindings[] k zreference[]]][k zcandidate[]]].q[t[k r5kh[k zbindings[] k zreference[]]][k zcandidate[]]].',('r5js',));rows={}
    for variant in ('one_lifetime','split_lifetimes','no_lifetime','outside_scope'):
        v=period_base(d);v['zbindings']=lambda:SequenceValue(('alpha',)*6,'"individual"')
        v['r5js']=lambda *a:a==(*('alpha',)*6,'reference','candidate') and variant!='outside_scope'
        if variant=='split_lifetimes':
            v['aa']=lambda p:p in DOMAIN
            v['ib']=lambda p,c,t:c=='candidate' and ((p=='alpha' and t in ('before','start','middle')) or(p=='beta' and t in ('end','after')))
        if variant=='no_lifetime':v['ib']=lambda *a:False
        actual=run(d,v);expected=[variant!='outside_scope',variant=='one_lifetime']
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(native_lifetime_subset=rows,not_union_of_several_lifetimes=True,
        native=['r5kh','r5ji','r5jd','r5h2','ta','tb'],boundary='r5js only')

@lru_cache(None)
def depiction_checks():
    d=fixture(('r5kc',),'q[t[k r5kc[k zbindings[] k zreference[]]][k zcandidate[]]].');rows={}
    for variant in ('baseline','always_exists','never_exists','appears_only','no_cause','other_agreement','other_period','other_result','other_reference','other_candidate','wrong_order','outside_history'):
        v=base(d);history=('start','end')
        v['h257z']=lambda r,c,p:(r,c)==('reference','candidate') and p in history and not(variant=='outside_history' and p=='end')
        v['ic']=lambda f,t,c:(f,t,c)==('end','start','candidate') if variant=='wrong_order' else(f,t,c)==('start','end','candidate')
        exists={'start'}
        if variant=='always_exists':exists={'start','end'}
        if variant=='never_exists':exists=set()
        if variant=='appears_only':exists={'end'}
        v['h26fb']=lambda obj,c,p:obj==('beta' if variant=='other_period' else 'alpha') and c=='candidate' and p in exists
        wanted=['alpha',('r5kb',0),('alpha',)*6,'reference','candidate']
        changes={'other_agreement':(0,'beta'),'other_result':(1,('r5kg',0)),'other_reference':(3,'assessment'),'other_candidate':(4,'end')}
        if variant in changes:i,value=changes[variant];wanted[i]=value
        v['h26as']=lambda *a:normalized(a)==tuple(wanted) and variant!='no_cause'
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_literal_disappearance_and_same_cause=rows,boundaries=[])

@lru_cache(None)
def discourse_checks():
    d=fixture(('r5kj',),'q[k r5kj[]].');q=lambda n:(n,2);whole=('r5ki',3);a='author';ctx='outer';ref='reference'
    expected={
      'h236i':{('h26fi',a,whole,ctx)},
      'h222q':{('h26fj',a,'h26ei',('r5hv',1),'h26fi',('r5ki',1),('r5kk',0),ctx)},
      'h26fg':{('h26fk',a,whole,q('r5kd'),q('r5kh'),q('r5ke'),ref,ctx)},
      'h26fc':{('h26fl',a,whole,q('r5kd'),q('r5kf'),q('r5kc'),ref,ctx)},
      'h26fa':{('h26fp',a,whole,q('r5j7'),q('r5j6'),ref,ctx)},
      'h26fe':{('h26fo',a,whole,q('r5j7'),q('r5j4'),q('r5j6'),ref,ctx)},
      'h26fd':{('h26fq',a,whole,q('r5j7'),q('r5j4'),q('r5j6'),ref,ctx)},
      'h26ff':{('h26fr',a,whole,q('r5kd'),q('r5ke'),ref,ctx)},
      'ue':{(x,y,ctx) for x,y in (('h26ei','h26fi'),('h26fj','h26fk'),('h26fk','h26fs'),('h26fs','h26fl'),('h26fl','h26fm'),('h26fm','h26fn'),('h26fo','h26fp'),('h26fp','h26fq'),('h26fn','h26fr'))}}
    rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','wrong_reference','different_whole','wrong_lifetime','literal_world','unqualified_harm','different_cause','merged_nodes'):
        v=base(d);v.update({n:lambda n=n:n for n in NODES});v['wa']=lambda:'other' if variant=='wrong_author' else a
        v['h255n']=lambda:'candidate' if variant=='wrong_context' else ctx
        if variant=='wrong_reference':v['h26b7']=lambda:'assessment'
        wanted=deepcopy(expected)
        changes={'different_whole':('h26fg',2,('r5hv',3)),'wrong_lifetime':('h26fg',4,q('r5kd')),
          'literal_world':('h26fc',4,q('r5kc')),'unqualified_harm':('h26fa',4,q('r5j3')),'different_cause':('h26fe',4,q('r5kf'))}
        if variant in changes:
            key,pos,value=changes[variant];row=list(next(iter(wanted[key])));row[pos]=value;wanted[key]={tuple(row)}
        v.update({n:lambda *args,n=n,values=values:n!=variant and normalized(args) in values for n,values in wanted.items()})
        if variant=='merged_nodes':
            v['h26fi']=lambda:'h26ei'
            for n in expected:v[n]=lambda *a:True
        actual=run(d,v,(*NODES,a,'other'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('h26fb','h26as','h26e4','h26e5','h237z','h253x'):assert v[n] is unknown
    return dict(same_whole_author_reference_and_qualified_presentation=rows,native_package='r5ka',
        quoted_disappearance_harm_and_norms_not_executed=True)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');cursor=2310;clauses=[]
    for fragment,names,reading in (
      ('Aber ',['h222q','r5kk','r5kj'],'前文の暫定的な可能性と、公的問い直しを禁じる制度固定化の禁止を対照する。'),
      ('auf eine beharrliche, ',['r5jf','r5jg','r5jh'],'同じ配置を全期間にわたり持続させること。有界・終点なしを共通に扱う。'),
      ('von Niemanden öffentlich zu bezweifelnde Religionsverfassung, ',['r5h3','r5h4','r5h5','r5jg'],'同じ宗教制度に対する全人の公的問い直しを禁止する。現実の疑念や批判の不在ではない。'),
      ('auch nur binnen der Lebensdauer eines Menschen, ',['r5ji','r5kh','h26fg'],'同じ一人の生涯内という限定部分にまで及ぶ禁止。全禁止範囲を限定部分へ縮めない。'),
      ('sich zu einigen, ',['r5ja','r5jh','r5js','r5jt','r5ju'],'同じ全当事者の同じ内容への共同合意形成を禁止の対象にする。宣誓や全住民の同意を追加しない。'),
      ('und dadurch ',['r5jr','r5jw','r5kf'],'同じ合意方針の実施から同じ期間の不毛化への因果的帰結。単なる併存ではない。'),
      ('einen Zeitraum in dem Fortgange der Menschheit zur Verbesserung ',['r5jj','r5jk','r5jl','r5jm'],'同じ期間の全人類について、認識獲得・理由ある訂正・理由ある自己判断の改善を全前後点で比較する。'),
      ('gleichsam zu vernichten, ',['r5kb','r5kc','h26fc'],'同じ期間を消失させる姿への見立て。字義的な消失を世界の真理条件へ連言しない。'),
      ('und fruchtlos, ',['r5jo','r5kg'],'同じ全期間に改善がないという結果。未知・絶滅・別期間の停滞を代用しない。'),
      ('dadurch aber wohl gar ',['r5j5','r5j6','r5ka','h26fe','h26fd'],'不毛化から害への第二の因果的帰結を、推量を保った対照・増幅として提示する。'),
      ('der Nachkommenschaft nachtheilig, ',['r5jy','r5jz','r5j2','r5j3','r5j7'],'合意の時代より後の全人を含む集団の知的継承・発展の機会の不利益。全員の個別被害にしない。'),
      ('zu machen, ',['r5j4','r5j5','r5j6'],'同じ不毛化を原因側、同じ後代の害を結果側に保つ。第一の原因関係との推移律は追加しない。'),
      ('ist schlechterdings unerlaubt.',['r5jv','r5ke','r5ki','h26ff'],'全候補の合意形成への例外なしの負極性要求。害の成功を禁止の条件にしない。')):
        assert unit['text'][cursor:cursor+len(fragment)]==fragment,(cursor,fragment)
        clauses.append(dict(range=[cursor,cursor+len(fragment)],text=fragment,definitions=names,reading=reading));cursor+=len(fragment)
    assert cursor==2677
    pages=[p for p in read('data/law-enactment-reading-v1.json')['primary_pages'] if 'page-489' in p['path']]
    assert len(pages)==1 and all(digest((ROOT/p['path']).read_bytes())==p['sha256'] for p in pages)
    return dict(status='fixed_compact_sentence_reviewed_under_explicit_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[2310,2677],text=unit['text'][2310:2677]),
        selection=selection_binding(catalog(),[103]),clauses=clauses,interpretation=LIMITS,unresolved=[],
        decision='equivalent_under_stated_reading_for_fixed_compact_sentence',whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=sum(not c.isspace() for c in unit['text'][2310:2677]),semantic_equivalence_automatically_proved=False,
        original_pages=pages,primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='28–32',observation='固定化の合意への禁止、期間を消す見立て、不毛化から後世への害という推量された帰結を原刊と照合。')],
        holistic_review=[
          '原刊489頁を表示して第八文全体を再読した。前文末の維持意向と冒頭Aber、第八文末と次のEin Menschの境界を保ち、連続する全語句を対応表へ記録した。',
          '固定化は同じ制度配置と全人への公的問い直しの禁止を同じ全期間で保つ。実際の疑念のなさ・心理的同意へ替えず、有限の一人生涯の限定部分も無期限を含む全候補の中へ位置付けた。',
          '相互形成の全当事者・同じ合意内容・制度・公衆・期間を追跡した。禁止は形成へかかり、実際の原因や被害を生じた場合だけの禁止にはしていない。規範出所は人間の進展、立場は一般の制度固定化の合意側に固定した。',
          '人類の改善は既存の三種類の進展の明示読解を保持した。終了点を含む全前後比較と完全な人類範囲により、単なる終点差・未知・空の人類を不毛さへ置き換えていない。',
          '同じ合意方針から不毛化への第一の帰結と、不毛化から後代の害への第二の帰結を分けた。消去の描写の主体・対象・原因性を同じ対象へ結び、字義的な期間消失を世界条件に加えない。',
          '後代の全成員と比較基準を固定した集団的な知的機会の不利益という読みを採る。全員の個別被害・任意の一人の被害に置き換えず、集団利益の評価と反事実的基準が入力である限界を記録した。',
          '第二の帰結にだけwohlの推量を置き、内側aberとgarの対照・増幅も同じ範囲と焦点へ接続した。中心命題ではこれを無条件に連言せず、第一の帰結と禁止を弱める留保にもしていない。',
          '前文との制度配置をめぐる対照、限定してもなおという取り立て、見立て、推量、増幅、全面性を同じ著者・全体・固定基準・文脈へ帰属した。引用内容の現実の評価は実行しない。',
          '全語句と合成定義を通読して、明示した読解の下で第八文の対応を確認した。有限模型の成功から原文同値を自動認定せず、独立査読・唯一の解釈・二作品完成とは区別する。'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,*(x['path'] for x in pages),*PRIORS)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog();assert new.document['statements'][:103]==old.document['statements'] and len(new.document['statements'])==104
    assert all(new.entries[n]==e for n,e in old.entries.items())
    for lib in dependencies():
        for n,e in lib.entries.items():assert new.entries[n]['declaration']==e['declaration'] and new.entries[n]['meaning_ja']==e['meaning_ja']
    reviews=load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:assert row['selection']==selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for p,indices in (('data/covenant-question-reading-v1.json',[96,97]),('data/covenant-nullity-reading-v1.json',[98]),('data/cohort-covenant-denial-reading-v1.json',[99]),('data/posterity-rights-reading-v1.json',[100]),('data/legislative-touchstone-reading-v1.json',[101]),('data/provisional-order-sentence-reading-v1.json',[102])):
        assert read(p)['selection']==selection_binding(new,indices)
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record()
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    record=reading_record();assert record['newly_reviewed_sentence_characters']==320
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013')
    for name,(span,meaning) in NODE_INFO.items():assert unit['text'][span[0]:span[1]] and name in new.entries
    actual={d['name'] for d in closure(new.document,['r5ki'])}
    assert not actual&{'h26fb','r5kb','r5kc','h26e4','h26e5','r5j3','r5j5','r5j6'}
    return dict(preserved_statements=103,added_statements=1,preserved_whole_unit_reviews=len(reviews),preserved_opening_sentence_characters=1981,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,new_reviewed_sentence_characters=320,
        literal_disappearance_and_unqualified_harm_absent_from_world_conditions=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('generic',generic_checks),('adapters',adapter_checks),('lifetime',lifetime_checks),('depiction',depiction_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{INDEX,READING,DOC,INVENTORY,*PRIORS,*(p['path'] for p in read(READING)['original_pages']),
        'data/covenant-question-reading-v1.json','data/covenant-nullity-reading-v1.json','data/cohort-covenant-denial-reading-v1.json','data/posterity-rights-reading-v1.json','data/legislative-touchstone-reading-v1.json','data/provisional-order-sentence-reading-v1.json',
        'scripts/compose_fixed_compact_sentence.py','scripts/check_fixed_compact_sentence.py','tests/test_fixed_compact_sentence.py',
        'scripts/check_covenant_nullity.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_persistent_compact_progress.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_compact_causal_denial.py'}
    return dict(status='fixed_compact_sentence_under_explicit_reading',document=FULL,**results,
        alignment=dict(**read(READING)['source'],statements=[103],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
