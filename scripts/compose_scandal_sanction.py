"""Scandal assessment, intentional sanction and separate normative availability."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/protected-remarks-basis-v1.json'
LIBRARY='examples/v016/scandal-sanction.noema'
BASIS='data/scandal-sanction-basis-v1.json'
NAMES=('authority','measure','person','criticism','community','standard')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
BOUND='l[a]['+' '.join('v '+n for n in NAMES)+']'
PRIMITIVES={
    'h244u':('[a a d d] c',['activity','community','reference','point'],
        'この振舞いは同じ共同体の他者へ公然と示され、他者が接し得る行為の例となる。内心だけの態度や秘密の行為と分ける。全員の現実の観察・模倣、全読者世界への刊行、既に反抗が広がったことは含めない。'),
    'h244v':('[a a d] c',['standard','community','reference'],
        'この評価基準は同じ共同体の実践に関して厳格に拘束する義務規則として扱われる。好みや任意の助言だけとは区別する。特定の法令、罰則、規則の道徳的正当性や個別の要求の存在は別である。'),
    'h244w':('[a a d d] c',['activity','standard','reference','point'],
        '同じ振舞いには、固定した義務規則を行為の拘束として重んじず軽視する姿勢が外に表れる。単に規則について異論を述べること、失敗・不能・不注意、知識の不足とは区別する。模倣の発生や処罰の許可は含めない。'),
    'h244x':('[a a d] c',['measure','person','point'],
        '同じ措置によってこの人に、その人にとっての不利益・負担が与えられる。処置の名称や非難の表明だけで不利益を成立させず、利益しかない処置とは分ける。特定の刑種・量・期間を固定しない。'),
    'h244y':('[a a a d] c',['authority','measure','person','point'],
        '同じ施行者は同じ措置を通じてこの人に不利益を与えることを意図している。偶然の副作用や単なる予測と区別する。実際の不利益・措置の実行は別に確認し、正当性・許可・義務を含意しない。'),
    'h244z':('[a a a a a a i[h[a a a d] e] d d] c',
        ['authority','measure','person','offense','community','standard','assessment','reference','point'],
        '同じ施行者は同じ人の対象行為を、同じ共同体・規則・基準を閉じた内容関数へ渡した内容で評価し、その評価を根拠とする応答として同じ措置を加える。既存rfmの応答関係に評価の束縛引数を明示する。内容の真理や規範的正当性は含めず、別の行為への報復や評価と無関係な害を区別する。'),
    'h245a':('[a a a d] c',['authority','role','community','reference'],
        'この施行者は、この共同体で制度上の処罰措置を扱う立場を持つ。私人の復讐だけとは区別する。個別の措置への許可や実行、制度の正当性は別に扱う。'),
    'h245b':('[a a d d] c',['measure','community','evaluation','outcome'],
        '同じ共同体と措置について、評価状況から見た事情の下で実行の候補となる結果状況。成功した候補だけを事後選別しない。規範的な許可・義務、現実の結果、実行成功をこの関係だけからは導かない。'),
    'h245c':('[a a a i b[h[j[a] d] e] j[a] d c d] c',
        ['source','authority','role','description','bindings','reference','polarity','point'],
        '規範の出所が、この施行者にこの立場で、閉じた段階1の内容関数へ同じ順序の個体列・固定基準を渡した内容を指定極性で積極的に許可する。h7lの記述段階と基準引数を一般化した関係。内容を許可時に実行せず、実現可能性・実際の実行・義務・道徳的正当性を含意しない。'),
}
MEANINGS={
    'r34j':'同じ活動が共同体の他者へ公然と行為の例として示され、同じ基準で厳格な義務規則として扱う規則を軽視する姿勢を表すという評価内容。Skandalの明示した読みであり、模倣・反抗の現実の発生や処罰の許可を内包しない。',
    'r34k':'同じ施行者が措置を実行し、本人に不利益が与えられ、その不利益を意図し、本人の同じ批判を同じ共同体・規則・基準のr34jで評価したことへの応答として措置を加える内容。rfmと同じ四条件を、評価の明示引数付きで合成する。評価の真理は実行しない。',
    'r34l':'施行者・措置・本人・批判・共同体・規則の正確な六個体列と固定基準から、同じr34kを構成する閉じたアダプター。段階1で引用でき、引数の不足・追加・順序の取り違えを許さない。',
    'r34m':'同じ施行者が同じ共同体の処罰を扱う立場を持ち、同じ評価状況からの少なくとも一つの候補で同じr34kの措置が成立する内容。実行可能性であり、現在の実行、全候補での成立、許可や義務を含まない。',
    'r34n':'同じ規範の出所が、同じ施行者・立場へ、同じ措置・本人・批判・共同体・規則・基準のr34lを積極的に許可し、同じ出所から反対極性の要求がないという内容。規範的な利用可能性であり、実行可能性r34mや実行r34kと区別する。',
    'r34o':'同じ出所・本人・批判・共同体・規則・基準について、制度上の処罰を扱う施行者・立場・措置でr34nを満たす組があるという内容。規範的に処罰し得るという採用読解の内容を準備する。全措置の許可や処罰の義務・実施は主張しない。',
}
LIMITS=[
    'u0012[2513,2770)のals ein Skandal ... bestraft werdenへの依存群。賦課批判と誘発可能性の既存群との全文接続、sogar、括弧の補足説明、著者帰属はまだ行わず、新規意味判断を加算しない。',
    'data/scandal-reading-v1.jsonに1797年AA6/474の同一著者の語義説明を補助資料として固定する。1784年の唯一の定義とせず、別著作の交際回避の義務を移入しない。資料自体がSkandalと法律上の不処罰を併記するため、評価と許可を分ける。',
    'bestraft werden kannは規範的に処罰対象となり得るという読みをr34oで採用する方針。実行可能性r34mも別に保持するが、この二内容を自動的に同一視・連言しない。規範の出所は全文接続時に明示し、処罰権限を誰にでも広げない。',
    '処罰は意図した不利益が実際に与えられる評価への応答として合成する。失敗した試みや単なる内心の非難を処罰の実行に数えない。原文にない特定の刑種・量・裁判手続は補わない。',
    'alsの評価内容を処罰の根拠として同じ対象行為に束縛し、措置があることから評価が真だとはしない。原文の一般的反抗の誘発可能性は、別のr34iおよび談話上の補足説明で接続する必要がある。',
    'r34nの反対要求の不在は同じ規範の出所についての整合性条件。あらゆる規範体系での合法性、倫理的な正当性、他の要求の不在まで証明するものではない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    text='d r34j[activity a community a standard a reference d] e[b point['+both(
        'k h244u[v activity v community v reference v point]',
        'k h244v[v standard v community v reference]',
        'k h244w[v activity v standard v reference v point]')+']].\n'
    text+='d r34k['+FIELDS+'] e[b point['+both('k cg[v authority v measure v point]',
        'k h244x[v measure v person v point]','k h244y[v authority v measure v person v point]',
        'k h244z[v authority v measure v person v criticism v community v standard r[p r34j] v reference v point]')+']].\n'
    text+='d r34l[bindings j[a] reference d] e[b point['+bind(NAMES,'t[k r34k['+ARGS+']][v point]')+']].\n'
    text+='d r34m[role a '+FIELDS+'] e[b point['+both('k h245a[v authority v role v community v reference]',
        'k rfj[v measure v point i[act a evaluation d outcome d][k h245b[v act v community v evaluation v outcome]] '
        'i[outcome d][t[k r34k['+ARGS+']][v outcome]]]')+']].\n'
    norm='v source v authority v role r b[p r34l] '+BOUND+' v reference '
    text+='d r34n[source a role a '+FIELDS+'] e[b point['+both(
        'k h245c['+norm+TRUE+' v point]', 'u[k h237z['+norm+FALSE+' v point]]')+']].\n'
    text+='d r34o[source a person a criticism a community a standard a reference d] e[b point['
    text+='g authority a[g role a[g measure a['+both('k h245a[v authority v role v community v reference]',
        't[k r34n[v source v role '+ARGS+']][v point]')+']]]]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['cg','rfj','h237z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='scandal_assessment_and_distinct_execution_possibility_permission',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
