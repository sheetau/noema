"""Review the current opening's deficit scope without redefining its language.

The reading decision is recorded explicitly below. Truth tables check the
implemented distinctions, not whether a natural-language reading is unique.
"""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_courageous_undertaking import FULL,BASIS

STATUS='data/opening-reading-status-v1.json'
REPORT=ROOT/'reports/opening-scope-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','method','other')
SCENES=('now','outcome')
HISTORICAL_REPORTS=('reports/described-transition-v1.json','reports/contextual-ability-v1.json',
    'reports/factive-cause-v1.json','reports/conditional-imputation-v1.json')


def unknown(*args):raise ValueError('Unknown scope interpretation')


@lru_cache(None)
def fixture():
    full=parse((ROOT/FULL).read_text(encoding='utf-8'));doc=deepcopy(full)
    doc['declarations']=closure(doc,['bd','rqqy','rqqz','rqrh','rqri']);doc['statements']=[]
    # Diagnostic alternatives are not added to the authored manuscript.
    return parse(format_graph(doc,'compact')+'''
r zperson[] a.r zscene[] d.
d zany[person a] e[b scene[x[t[k rqqy[v person]][v scene]][t[k rqqz[v person]][v scene]]]].
d znotboth[person a] e[b scene[u[w[k hzin[v person r[p bb] v scene]][k hzio[v person r[p bb] v scene]]]]].
d zindividual[person a scene d] c[w[k hzie[v person r[p rqqy] v person r[p bf] v scene]][k hzie[v person r[p rqqz] v person r[p bf] v scene]]].
q[t[k rqrh[k zperson[]]][k zscene[]]].
q[t[k zany[k zperson[]]][k zscene[]]].
q[t[k znotboth[k zperson[]]][k zscene[]]].
q[k bd[k zperson[] k zscene[]]].
q[k zindividual[k zperson[] k zscene[]]].
''')


def is_ref(code,name):return code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


def model(doc,lacks=(True,True),causes=(True,False,False),understanding=(False,False)):
    resolve,courage=lacks;joint,first,second=causes;intellect,intellect_cause=understanding
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    # An actual human, with no available successful method, instantiates bc.
    # Its Noema definition is evaluated, not replaced by a Python truth flag.
    values.update(zperson=lambda:'person',zscene=lambda:'now',aa=lambda p:p=='person',
        ab=lambda *a:False,ac=lambda *a:False,ad=lambda *a:False,
        ae=lambda *a:False,af=lambda *a:False,ap=lambda *a:False)
    def sufficient(deficit):
        def check(p,g,s):
            if not is_ref(g,'bb'):raise ValueError('Unknown assessment goal')
            return not(deficit and p=='person')
        return check
    values.update(hzin=sufficient(resolve),hzio=sufficient(courage),hzip=sufficient(intellect))
    def causal(p,g,q,result,s):
        if (p,q)!=('person','person') or not is_ref(result,'bf'):return False
        return any(is_ref(g,name) and truth for name,truth in zip(('rqrh','rqqy','rqqz','rqri'),(joint,first,second,intellect_cause)))
    values['hzie']=causal
    return values


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=2000000,memoize_definitions=False,memoize_expressions=False)]


def scope_checks():
    doc=fixture();rows=[]
    for lacks in product((False,True),repeat=2):
        actual=evaluate(doc,model(doc,lacks=lacks))
        assert actual==[all(lacks),any(lacks),any(lacks),all(lacks),False],(lacks,actual)
        rows.append(dict(lacks_resolve=lacks[0],lacks_courage=lacks[1],joint_deficit=actual[0],
            either_deficit=actual[1],negated_joint_adequacy=actual[2],source_condition=actual[3]))
    return dict(cases=rows,one_missing_capacity_does_not_satisfy_both_missing=True,
        negating_joint_adequacy_is_a_different_reading=True)


def causal_checks():
    doc=fixture();count=0;counterexamples={}
    for lacks in product((False,True),repeat=2):
        for causes in product((False,True),repeat=3):
            actual=evaluate(doc,model(doc,lacks=lacks,causes=causes))
            assert actual==[all(lacks),any(lacks),any(lacks),all(lacks) and causes[0],causes[1] and causes[2]],(lacks,causes,actual)
            count+=1
            if all(lacks) and causes in ((True,False,False),(False,True,True)):
                counterexamples['joint_only' if causes[0] else 'individual_only']=dict(source_condition=actual[3],both_individual_causes=actual[4])
    excluded=[]
    for understanding in product((False,True),repeat=2):
        actual=evaluate(doc,model(doc,understanding=understanding))
        assert actual[3]==(not all(understanding))
        excluded.append(dict(lacks_understanding=understanding[0],causal=understanding[1],source_condition=actual[3]))
    return dict(deficit_and_joint_individual_cause_combinations=count,non_distributivity_counterexamples=counterexamples,
        negated_cause_not_negated_deficit=excluded,actual_immaturity_definition_evaluated=True,uncached_and_unlowered=True)


def unknown_checks():
    doc=deepcopy(fixture());doc['statements']=doc['statements'][3:4]
    for name in ('hzin','hzio','hzip','hzie'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown scope' in str(error)
        else:raise AssertionError(name)
    # Looking up a jointly described factor must not silently ask about its
    # components, even if each component has a known causal interpretation.
    values=model(doc);original=values['hzie']
    def missing_joint(p,g,q,result,s):
        if is_ref(g,'rqrh'):raise ValueError('Unknown joint causal factor')
        return original(p,g,q,result,s)
    values['hzie']=missing_joint
    try:evaluate(doc,values)
    except ValueError as error:assert 'Unknown joint causal factor' in str(error)
    else:raise AssertionError('Individual causes substituted for unknown joint cause')
    return dict(unknowns_refused=5,unknown_not_false=True,components_do_not_fill_unknown_joint_record=True)


def ability_recheck():
    full=parse((ROOT/FULL).read_text(encoding='utf-8'));doc=deepcopy(full)
    doc['declarations']=closure(doc,['xb','xc','xd','xe','xf','xg']);doc['statements']=[]
    suffix='r za[] a.r zb[] d.r zd[a a d] c.r ze[a a d d] c.r zf[a a d d] c.r zg[d] c.'
    arguments='k za[] b scene[k zg[v scene]] k zb[] p zd p ze'
    for name in ('xb','xc','xd','xe','xf','xg'):
        params='k za[] k zb[] p zd p ze p zf' if name=='xe' else arguments+(' p zf' if name in ('xd','xf','xg') else '')
        suffix+='q[k '+name+'['+params+']].'
    doc=parse(format_graph(doc,'compact')+suffix)
    subsets=[{s for i,s in enumerate(('now','outcome')) if mask&(1<<i)} for mask in range(4)]
    count=0
    for enabled,outcomes,selected,success in product((False,True),subsets,subsets,subsets):
        valid=bool(selected) and selected<=outcomes;witness=enabled and valid and selected<=success
        assessable=not enabled or valid
        expected=[enabled and bool(outcomes&success),enabled and bool(outcomes) and outcomes<=success,
            witness,assessable,assessable or witness,assessable and not witness]
        values=dict(za=lambda:'person',zb=lambda:'now',
            zd=lambda p,m,s:enabled and (p,m,s)==('person','method','now'),
            ze=lambda p,m,s,t:(p,m,s)==('person','method','now') and t in outcomes,
            zf=lambda p,m,s,t:(p,m,s)==('person','method','now') and t in selected,
            zg=lambda s:s in success)
        assert evaluate(doc,values)==expected,(enabled,outcomes,selected,success)
        count+=1
    return dict(models=count,current_manuscript_definitions=True,current_constructed_runtime=True,
        matches_independent_set_conditions=True,historical_finite_runtime_not_used=True,
        source_assessment_scope_not_semantically_certified=True)


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def build_status():
    cat=catalog();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0008')
    prior=json.loads((ROOT/'reports/courageous-undertaking-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    roots=['rqqy','rqqz','rqrh','rqri','bd','xb','xc','xf'];selected=[d['name'] for d in closure(cat.document,roots)]
    references=[dict(title='Kant, AA VIII 35, lines 3–6',url='https://korpora.org/Kant/aa08/035.html',
        supports='Mangelに続く理解力と、対比される決意・勇気の属格の並列、同じ不定詞句への接続を再読した。'),
        dict(title='IDS, Phrasen',url='https://grammis.ids-mannheim.de/progr@mm/90102',
        supports='同種の句を並列できるという一般的な構造を確認する資料。このカント文の不足や因果の読みを一意に決める根拠ではない。')]
    paths=set(cat.source_sha256)|set(prior['source_sha256'])|{INVENTORY,'reports/courageous-undertaking-v1.json',
        'artifacts/publication-header-v1/page-481.jpg','data/targeted-adequacy-review-v1.json','data/conditional-imputation-review-v1.json',
        'scripts/audit_opening_scope.py','tests/test_opening_scope.py','docs/opening-scope-v1.md'}
    historical_audit={}
    for path in HISTORICAL_REPORTS:
        historical=json.loads((ROOT/path).read_text(encoding='utf-8'))
        changed=[]
        for name,expected in historical['source_sha256'].items():
            actual=digest((ROOT/name).read_bytes())
            if actual!=expected:changed.append(dict(path=name,recorded_sha256=expected,current_sha256=actual))
        historical_audit[path]=dict(status='historical_inputs_differ' if changed else 'pinned_inputs_still_match',
            changed_inputs=changed,rerun_of_original_report=False)
        paths.add(path);paths.update(historical['source_sha256'])
    return dict(status='explicit_subclause_reading_and_current_opening_worklist',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[251,330],text=unit['text'][251:330]),references=references,
        judgment=dict(reviewer='assistant_review',decision='coordination_scope_accepted_under_stated_reading',
            reading='同じ目標に向けた決意と勇気の双方が十分でない状態を、合わせて原因として指す読みを採る。双方の十分さの連言を否定する読みや、片方の不足だけでよい読みは採らない。二つを合わせた状態の因果寄与から、各不足が単独でも原因であるとは推論しない。',
            rationale='原文はMangelを対比の両側で共有し、後半では属格の決意と勇気をundで並列する。今回はその両方の不足として読む。因果を述べる箇所は一つであり、各不足の独立した必要性・十分性や原因の唯一性を補わない。これは明示した読解判断であり、一般文法や真理値表から導いた唯一の解釈ではない。',
            closed_item='決意と勇気の不足の連言という採用読解と、共同の因果要因への接続範囲。',
            not_closed=['決意・勇気の十分さを判定する文脈基準','原文全体との意味一致','因果から帰責への条件の読みの最終確認'],
            whole_unit_semantically_verified=False),
        binding=dict(statement=selection_binding(cat,[1]),definition_entries={n:digest(json.dumps(cat.entries[n],ensure_ascii=False,sort_keys=True).encode('utf-8')) for n in selected}),
        historical_evidence_audit=historical_audit,
        already_implemented=[
            dict(item='離脱の本人・過程・前後状態',symbols=['be','la','hzid','bp','up'],evidence='reports/described-transition-v1.json'),
            dict(item='能力と全結果での成功保証の分離',symbols=['xd','xc','ap'],evidence='reports/contextual-ability-v1.json'),
            dict(item='実際の原因と説明への採用の分離',symbols=['hzie','rqqu','rqqv','ea'],evidence='reports/factive-cause-v1.json'),
            dict(item='原因条件と自己への帰責、条件の向きの分離',symbols=['bd','rqrj','rqrk','rqrl'],evidence='reports/conditional-imputation-v1.json'),
            dict(item='命令の引用と実際の取り組み・達成の分離',symbols=['hzs4','hzs5','hzs6','hzsb'],evidence='reports/courageous-undertaking-v1.json')],
        remaining_semantic_reviews=[
            dict(item='能力と不足の文脈基準',symbols=['bc','xd','ap','hzin','hzio','hzip'],next_action='能力評価の機会範囲と十分さの解釈を、原文が省略した文脈条件と訳で追加した条件に分けて確定する。'),
            dict(item='自己に責任がある状態とwennの提示',symbols=['rqrj','rqrk','rqrl'],next_action='一方向の条件という読みで原文の分類の役割を保てるか確認する。心理機構や帰責の正しさの実証を、著者の主張の記述へ追加要求しない。'),
            dict(item='ラテン語の判断能力と取り組みの読み',symbols=['bk','yb','hzs6'],next_action='sapereの分別を判断能力とする範囲と、audeに試みを要求する候補の適否を確認する。ドイツ語の同義語へ戻さない。'),
            dict(item='標語と段落全体の提示',symbols=['hzs7','hzsa','hzsb'],next_action='標語が指す二つの呼びかけ、alsoの根拠範囲、六箇所の全体を再読する。順序検査の成功だけで認定しない。')],
        review_scope='現行版への作業項目の整理。既存実装の列挙は各語義の新しい全体レビューではなく、今回採用した判断も一つの作用範囲に限る。過去の検査報告は入力差分を明示した履歴として参照し、今回の検査は現行本文と現行の構成言語評価器で実行する。現在の入力ハッシュで古い実行環境を再現したとは扱わない。',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def structural_checks():
    status=build_status();cat=catalog()
    assert status['source']['text']=='nicht am Mangel des Verstandes, sondern der Entschließung und des Muthes liegt,'
    for row in status['already_implemented']+status['remaining_semantic_reviews']:
        assert set(row['symbols'])<=set(cat.entries)
        if 'evidence' in row:assert row['evidence'] in status['source_sha256']
    index=json.loads((ROOT/'data/semantic-review-index-v24.json').read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document']==FULL
    assert status['binding']['statement']==selection_binding(cat,[1])
    assert (ROOT/STATUS).read_text(encoding='utf-8')==encoded(status)
    doc=fixture()
    for notation in ('compact','full'):
        text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(current_manuscript_bound=True,author_text_unchanged=True,current_review_index_unchanged=True,
        diagnostic_definitions_not_added_to_manuscript=True,fixture_roundtrips=True,
        one_subclause_judgment_not_whole_paragraph_review=True)


def encoded(value):return json.dumps(value,ensure_ascii=False,indent=2)+'\n'


def write_exact(path,body):
    if path.exists():assert path.read_text(encoding='utf-8')==body,path
    else:
        with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)


def build_report():
    status=build_status();results={}
    for name,fn in [('scope',scope_checks),('causality',causal_checks),('unknowns',unknown_checks),('current_ability',ability_recheck),('structure',structural_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    source=status['source'];alignment=dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],
        definitions=['rqrh','bd'],status='partial_review_of_coordination_scope',full_semantic_equivalence=False)
    from scripts.audit_written_progress_extended import collect_alignment
    units={r['id']:r for r in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units']}
    rows=collect_alignment(dict(alignment=alignment),units,set(catalog().entries),'reports/opening-scope-v1.json')
    assert len(rows)==1 and rows[0]['status']=='partial'
    pins=dict(status['source_sha256']);pins[STATUS]=digest((ROOT/STATUS).read_bytes())
    pins['data/semantic-review-index-v24.json']=digest((ROOT/'data/semantic-review-index-v24.json').read_bytes())
    return dict(status='coordination_reading_reviewed_without_manuscript_change',document=FULL,**results,alignment=alignment,
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256=pins)


def main():
    cli=argparse.ArgumentParser();mode=cli.add_mutually_exclusive_group();mode.add_argument('--status-only',action='store_true');mode.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    write_exact(ROOT/STATUS,encoded(build_status()))
    if args.status_only:print('Current opening reading worklist recorded',flush=True);return
    result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:write_exact(REPORT,encoded(result))
    print('Coordination scope and causal non-distribution checked; whole paragraph remains unreviewed',flush=True)


if __name__=='__main__':main()
