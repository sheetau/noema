"""Bind opening reading decisions to the current claims, not their truth."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.audit_opening_scope import ROOT,FULL,BASIS,INVENTORY,catalog,encoded,write_exact
from scripts.compose_subject_bound_departure import closure

STATUS='data/opening-reading-status-v2.json'
FIXTURE='examples/v016/opening-conditional-review.noema'
REPORT='reports/opening-claims-v1.json'
PRIOR='data/opening-reading-status-v1.json'
DOMAIN=('person','other','method')
SCENES=('now','elsewhere')


def unknown(*args):raise ValueError('Unknown opening claim interpretation')


def code_is(code,kind,symbol,arguments=None):
    expected=dict(kind=kind,symbol=symbol)
    if arguments is not None:expected['arguments']=arguments
    return code.rank==0 and json.loads(code.syntax)==expected


@lru_cache(None)
def fixture():
    full=parse((ROOT/FULL).read_text(encoding='utf-8'));doc=deepcopy(full)
    doc['declarations']=closure(full,['rqrk','rqrl','rqrj','bd']);doc['statements']=[]
    return parse(format_graph(doc,'compact')+'''
r zperson[] a.r zscene[] d.
q[k bd[k zperson[] k zscene[]]].
q[k rqrj[k zperson[] k zscene[]]].
q[t[k rqrk[]][k zscene[]]].
q[t[k rqrl[]][k zscene[]]].
''')


def model(doc,causes=(),imputed=(),humans=('person','other'),variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(zperson=lambda:'person',zscene=lambda:'now',aa=lambda p:p in humans,
        ab=lambda *a:False,ac=lambda *a:False,ad=lambda *a:False,
        ae=lambda *a:False,af=lambda *a:False,ap=lambda *a:False,
        hzin=lambda *a:False,hzio=lambda *a:False,hzip=lambda *a:True)
    values['hzie']=lambda p,f,q,r,s:p==q and p in causes and s=='now' and code_is(f,'function_ref','rqrh') and code_is(r,'function_ref','bf')
    values['hziq']=lambda p,g,s:p in imputed and s==('elsewhere' if variant=='other_scene' else 'now') and code_is(g,'function_ref','bb' if variant=='other_state' else 'bf')
    return values


def evaluate(doc,values,domain=DOMAIN,scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def conditional_checks():
    doc=fixture();rows=[]
    for a,b,c,d in product((False,True),repeat=4):
        causes={p for p,on in zip(('person','other'),(a,b)) if on}
        imputed={p for p,on in zip(('person','other'),(c,d)) if on}
        actual=evaluate(doc,model(doc,causes,imputed))
        assert actual==[a,c,causes<=imputed,causes==imputed],(causes,imputed,actual)
        rows.append(dict(causal_people=sorted(causes),imputed_people=sorted(imputed),values=actual))
    assert evaluate(doc,model(doc))==[False,False,True,True]
    assert evaluate(doc,model(doc,imputed=('person',)))==[False,True,True,False]
    return dict(cases=rows,count=len(rows),no_existence_claim=True,converse_not_asserted_or_denied=True,
        other_person_counterexample_detected=True,current_native_definitions=True,uncached_and_unlowered=True)


def imputation_checks():
    doc=fixture();cases={}
    for name,options,expected in [
        ('same_person_state_scene',{},[True,True,True,True]),
        ('other_state',{'variant':'other_state'},[True,False,False,False]),
        ('other_scene',{'variant':'other_scene'},[True,False,False,False]),
        ('other_person',{'imputed':('other',)},[True,False,False,False]),
        ('no_immaturity',{'humans':()},[False,False,True,True]),
    ]:
        params=dict(causes=('person',),imputed=('person',));params.update(options)
        actual=evaluate(doc,model(doc,**params));assert actual==expected,(name,actual);cases[name]=actual
    direct=deepcopy(doc);direct['statements']=direct['statements'][1:2]
    values=model(direct,causes=('person',));values['hziq']=unknown
    try:evaluate(direct,values)
    except ValueError as error:assert 'Unknown opening claim' in str(error)
    else:raise AssertionError('Causality filled an unknown imputation')
    return dict(cases=cases,unknown_imputation_refused=True,imputation_does_not_create_the_state=True)


def presentation_checks():
    full=parse((ROOT/FULL).read_text(encoding='utf-8'));doc=deepcopy(full)
    doc['declarations']=closure(full,['hzsb','wa','wh','wb','wc','wd','we','wf','wg'])
    doc['statements']=[full['statements'][1]]
    nodes=('first','second','third','latin','german','conclusion')
    domain=('author',*nodes);rows={}
    for variant in ('baseline','equivalence_instead','missing_condition','other_author','other_context',
                    'missing_conclusion_link','one_premise_only','reverse_explanation'):
        values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        values.update({n:(lambda value=value:value) for n,value in zip(('wa','wb','wc','wd','we','wf','wg'),domain)})
        values['wh']=lambda:'now'
        def context(author,scene):
            return (author,scene)==('first' if variant=='other_author' else 'author','elsewhere' if variant=='other_context' else 'now')
        def defines(n,a,code,s):
            return context(a,s) and code_is(code,'function_ref',{'first':'bi','second':'bf'}.get(n))
        def quotes(n,a,code,s):
            return context(a,s) and code_is(code,'call',{'latin':'hzs6','german':'bn'}.get(n),[dict(kind='call',symbol='ao',arguments=[])])
        def claims(n,a,code,s):
            if n=='third' and variant=='missing_condition':return False
            return context(a,s) and code_is(code,'call',{'third':'rqrl' if variant=='equivalence_instead' else 'rqrk','conclusion':'hzsa'}.get(n),[])
        def conclusion(a,p,n,s):
            premises=list(nodes[:1] if variant=='one_premise_only' else nodes[:-1])
            return variant!='missing_conclusion_link' and context(a,s) and n=='conclusion' and [x for x in domain if p(x)]==premises
        values.update(ua=defines,ub=quotes,uc=claims,ud=conclusion,
            ue=lambda a,b,s:s=='now' and a in nodes and b in nodes and nodes.index(a)<nodes.index(b),
            uf=lambda a,x,y,s:context(a,s) and (x,y)==(('german','latin') if variant=='reverse_explanation' else ('latin','german')))
        actual=evaluate(doc,values,domain,('now',));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(cases=rows,quoted_causal_imputation_ability_and_directive_values_all_unknown=True,
        reports_claim_without_certifying_its_truth=True,selected_five_node_support_checked=True)


def build_status():
    prior=json.loads((ROOT/PRIOR).read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    cat=catalog();assert prior['binding']['statement']==selection_binding(cat,[1])
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0008')
    decisions=[dict(id='conditional_direction',range=[182,381],definitions=['bd','rqrj','rqrk','rqrl'],
        reading='原因条件bdが成立する人は、本人に責任がある未成熟rqrjに分類される、という十分条件の主張を採る。逆向き、該当者の実在、原因から帰責への論理的還元は加えない。',
        rationale='原文はwennで原因条件を述べ、その場合の自己に責任があるという分類を提示する。必要条件を表すnur wennや同値を明示する句はない。この箇所ではその十分条件を採用する。定義的な同値を含意するという別の読解を一般文法だけで排除した判断ではない。',
        closed='一方向の条件と分類の提示という読み、および原因と帰責の区別。',
        remaining='条件中の能力・不足の文脈基準は別の未確定項目であり、第三文全体の意味一致は未確認。'),
        dict(id='conclusion_presentation',range=[449,488],definitions=['hzs7','hzsa','hzsb','vb','vc'],
        reading='二つの呼びかけを並べた全体を啓蒙の標語とし、先行五箇所を談話上の根拠側のまとまりとして結論を提示する読みを採る。ドイツ語による説明はラテン語と同義であるという等式にはしない。',
        rationale='ist also der Wahlspruchは直前の二つの呼びかけを受け、帰結として位置付ける。原文は形式的な前提集合を列挙していないため、先行五箇所は談話のまとまりとしての明示的な採用読解である。各箇所が独立に必要、十分、真であるとは述べない。',
        closed='標語の二つの引用先、説明の向き、談話上の根拠範囲の採用判断。',
        remaining='呼びかけと啓蒙そのものの語義、段落全体の意味一致は未確認。')]
    for row in decisions:
        start,end=row['range'];row.update(source=unit['text'][start:end],reviewer='assistant_review',
            decision='scope_accepted_under_stated_reading',whole_unit_semantically_verified=False)
    remaining=deepcopy(prior['remaining_semantic_reviews'])
    remaining=[r for r in remaining if r['item']!='自己に責任がある状態とwennの提示']
    remaining[-1]['next_action']='今回採用した標語の引用先・説明の向き・根拠範囲を保ち、能力とラテン語の語義を確定した後で、六箇所を合わせた意味・照応・追加条件と脱落を再読する。'
    remaining[0]['next_action']='現在の機会を含むxdと、機会を補ったrqva等を比較した記録を踏まえ、能力評価の範囲を原文に即して選ぶ。本人の保持は候補場面の始点であり、方法の途中の学習を排除した定義ではない。十分さの文脈基準も残る。'
    paths=set(prior['source_sha256'])|set(cat.source_sha256)|{PRIOR,FIXTURE,
        'reports/opening-scope-v1.json','reports/standing-ability-v1.json','data/semantic-review-index-v24.json',
        'scripts/audit_opening_claims.py','tests/test_opening_claims.py','docs/opening-claims-v1.md'}
    return dict(status='conditional_and_discourse_scope_decisions_not_whole_unit_review',document=FULL,meaning_basis=BASIS,
        supersedes_worklist=PRIOR,source_unit=unit['id'],unit_sha256=unit['text_sha256'],
        reference=dict(title='Kant, AA VIII 35, lines 1–8',url='https://korpora.org/Kant/aa08/035.html',
            role='原文の条件接続と標語の位置付けを再読。唯一の論理解釈を自動決定する資料ではない。'),
        decisions=decisions,inherited_coordination_judgment=prior['judgment'],
        binding=selection_binding(cat,[1]),remaining_semantic_reviews=remaining,
        review_limit='人による読解に相当するassistant_reviewの判断。有限モデルはNoemaの区別を検査し、自然言語との意味一致や著者の主張の真実性を証明しない。全文レビューの登録簿は変更しない。',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def structure():
    status=build_status();cat=catalog()
    assert len(status['remaining_semantic_reviews'])==3
    assert all(not row['whole_unit_semantically_verified'] for row in status['decisions'])
    assert json.loads((ROOT/STATUS).read_text(encoding='utf-8'))==status
    assert parse((ROOT/FIXTURE).read_text(encoding='utf-8'))==fixture()
    for d in fixture()['declarations']:
        if d['name'] not in ('zperson','zscene'):assert d==cat.entries[d['name']]['declaration']
    for notation in ('compact','full'):
        text=format_graph(fixture(),notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==fixture()
    index=json.loads((ROOT/'data/semantic-review-index-v24.json').read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document']==FULL and len(index['works']['kant-1784']['reviews'])==8
    return dict(current_statement_and_meanings_bound=True,new_language_definitions=0,new_whole_units=0,
        source_and_review_index_unchanged=True,fixture_roundtrips=True)


def build_report():
    status=build_status();results={}
    for name,fn in [('condition',conditional_checks),('imputation',imputation_checks),('presentation',presentation_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    pins=dict(status['source_sha256']);pins[STATUS]=digest((ROOT/STATUS).read_bytes())
    segments=[dict(unit=status['source_unit'],unit_sha256=status['unit_sha256'],range=r['range'],source=r['source'],
        definitions=r['definitions'],status='partial_reading_scope_judgment',full_semantic_equivalence=False) for r in status['decisions']]
    from scripts.audit_written_progress_extended import collect_alignment
    units={r['id']:r for r in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units']}
    assert len(collect_alignment(dict(alignment=dict(segments=segments)),units,set(catalog().entries),REPORT))==2
    return dict(status='source_readings_chosen_and_current_claims_checked',document=FULL,**results,
        alignment=dict(segments=segments),new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256=pins)


def main():
    cli=argparse.ArgumentParser();group=cli.add_mutually_exclusive_group();group.add_argument('--status-only',action='store_true');group.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    write_exact(ROOT/FIXTURE,format_graph(fixture(),'compact')+'\n')
    write_exact(ROOT/STATUS,encoded(build_status()))
    if args.status_only:print('Opening claim reading decisions recorded',flush=True);return
    result=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==result
    else:write_exact(ROOT/REPORT,encoded(result))
    print('Conditional and discourse readings checked; complete paragraph remains pending',flush=True)


if __name__=='__main__':main()
