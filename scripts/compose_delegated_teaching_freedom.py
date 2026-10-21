"""Bind actual non-freedom and a negative demand to the same quoted discretion."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_confessional_teaching import MESSAGE
from scripts.compose_representative_teaching import TASK_FIELDS,TASK_ARGS

PARENT='data/clerical-resignation-condition-basis-v1.json'
DEPENDENCY='data/congregational-private-use-basis-v1.json'
LIBRARY='examples/v016/delegated-teaching-freedom.noema'
BASIS='data/delegated-teaching-freedom-basis-v1.json'
NAMES=('church','person','role','subject')
FIELDS=' '.join(n+' a' for n in NAMES)+' message '+MESSAGE+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v message v reference'
TARGET='i b[h[j[a] d] e]'
PRIMITIVES={
    'h253f':('[a a d] a',['principal','role','reference'],
        '同じ委託元・職務・固定基準について、他者の委任を受けてその職務に当たる者の、委任された業務と権限に関する責任を評価する規範の出所。委託元が実際に出した命令・法令、その者の全発言の正当性、本人の内心の確信や良心的許容そのものとは区別する。個別の自由への要求・禁止や、その現実の履行はこの参照だけから導かず、別に接続する。'),
}
MEANINGS={
    'r44g':'同じ閉じた発話記述と、教会・本人・職務・主題の正確な四個体列・固定基準を受け、r4dの自由な教示内容決定の権限という内容を作る。列の順序と長さを確認し、発話は内容関数への別引数として保持する。個体の列に発話コードを押し込まない。',
    'r44h':'同じ発話記述を引用持上げo rし、段階1の閉じた外側関数へ引用適用o aして、四個体列と固定基準を受けるr44gの閉じた内容関数記述を構成する。発話や自由内容を実行せず、同値な別発話記述にも置き換えない。',
    'r44i':'同じ教会・本人・職務・主題・発話・固定基準のr4eを使い、教示内容の自由な決定権限が現にない内容を保持する。否定は権限h247pと他者の指定に拘束されない決定基準h247qの連言に掛ける。思考能力や全ての実務上の判断を否定しない。',
    'r44j':'同じ委託元と職務についてh253fが参照する職務責任の評価規範が、同じ本人に同じ職務で、r44hの内容関数へ同じ教会・本人・職務・主題列と基準を渡す自由内容を負極性で要求する。h237zの既存関係を使い、許可の単なる不在とも、自由の現実の不存在とも区別する。',
    'r44k':'同じ六引数・評価点について、自由の現実の否定r44iと、同じ自由内容への負の要求r44jを連言する。規範から履行を導かず、現実の不自由だけから規範を補わない。',
    'r44l':'同じ聖職者事例・活動・発話について、先行r44fの私的使用・委託の遂行・会衆の性格に、同じ教会・本人・職務・主題・発話・基準のr44kを接続する。規範の対象は教示の決定権限であり、教示の実行そのものの禁止ではない。',
}
LIMITS=[
    'u0012[4408,4734)のin Ansehung dessen ... als Priester, nicht frei, und darf es auch nicht seinに向けた依存群。自由の範囲は同じ職務上の教示に関する内容と扱いの自己決定とする。前方のfreie Gewalt nach eigenem Gutdünkenに対応するr4d/r4eを再利用し、後続の学識者としての公的自由は否定しない。',
    'nicht freiは同じ教示に関する自由な決定権限の現実の否定、darf ... nichtは同じ状態を認めない職務責任の規範的要求という明示読み。物理的不能、監禁、思考の禁止、発話の実行自体の全面禁止とはしない。',
    '自由な決定権限の不成立には、権限はあるが他者の指定する基準に拘束される場合も含める。局所的な判断や工夫が許されるだけでは、この自由は成立しない。未知の権限や規範を否定の証拠として扱わない。',
    '規範源は同じ委託職務の責任を評価する枠組みとして参照する。原文にない現代の法令・処罰・具体的な命令者を補わず、委託元が命令したから正しいという結論も加えない。評価源の参照だけでは当該負の要求は導かれない。',
    '今回の自由内容は、同じ主題・閉じた発話についての教示決定の権限である。全文では同じ職務上の全該当使用へ一般化する必要があり、一つの発話の否定だけで職務全体を記述済みとはしない。将来の統合で量化対象を許可済み・適合済みの発話だけへ絞らない。',
    '発話を含む内容関数の記述は既存の引用持上げと引用適用で構成する。任意の実行時個体を閉じた引用へ取り込まず、個体は正確な四個体列、固定基準は別引数として渡す。規範要求時には内側の自由や発話を評価しない。',
    '全文の一般化・also・二つのweil・in Ansehung dessen・auchと規模への譲歩の提示・著者帰属は次の統合事項。今回の依存群で本文・確認文字数は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def definitions():
    target='t[k r4d['+ARGS+']][v point]'
    text='d r44g[message '+MESSAGE+' bindings j[a] reference d] e[b point['+bind(NAMES,target)+']].\n'
    template='r b[i[message '+MESSAGE+'][i[bindings j[a] reference d][k r44g[v message v bindings v reference]]]]'
    text+='d r44h[message '+MESSAGE+'] '+TARGET+'[o a['+template+'][o r[v message]]].\n'
    text+='d r44i['+FIELDS+'] e[k r4e['+ARGS+']].\n'
    text+=('d r44j['+FIELDS+'] e[b point[k h237z[k h253f[v church v role v reference] v person v role k r44h[v message] l[a]['+
        ' '.join('v '+n for n in NAMES)+'] v reference '+FALSE+' v point]]].\n')
    text+='d r44k['+FIELDS+'] e[b point['+both('t[k r44i['+ARGS+']][v point]','t[k r44j['+ARGS+']][v point]')+']].\n'
    case='v church v person v role v subject v message v reference'
    text+='d r44l['+TASK_FIELDS+'] e[b point['+both('t[k r44f['+TASK_ARGS+']][v point]','t[k r44k['+case+']][v point]')+']].\n'
    return text


def build():
    old=parent();dep=dependency();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r4d','r4e','h237z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(dep.document,['r44f']):
        n=d['name'];e=dep.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(dep.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='same_teaching_freedom_actual_negation_and_normative_rejection',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set(old.source_sha256)|set(dep.source_sha256))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
