"""Compose unexamined settled judgment, instilling and later adverse effects."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-reversal-focus.noema'
PARENT_BASIS = 'data/reversal-focus-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-effects.noema'
CORE = 'examples/v016/prejudice-effects-core.noema'
BASIS = 'data/prejudice-effects-basis-v1.json'
ANNOTATIONS = 'data/prejudice-effects-identifiers-v1.json'
PRIMITIVES = {
    'h224w': ('[a d] c', ['judgment', 'point'],
              '同じ判断において、肯定する内容を単に仮の見込みとして保留するのでなく、さらに判断する際の確定した原則として受け入れている。内容の真理、理由の十分性、社会的な普及、本人の悪意は含意しない。'),
    'h224x': ('[a a i[h[a] e] d] c', ['person', 'topic', 'claim', 'point'],
              'この本人は、この話題に適用された同じ内容記述を確定した原則として受け入れるに足る根拠について、その時点までに実際に吟味して確認を済ませている。単に他者からそう教わったこと、本人の確信、吟味したとの自己申告、別の内容の検討だけでは成立しない。吟味の全くの不在と不十分な吟味の両方を、この関係の不成立に含める。'),
    'h224y': ('[a] i[h[a] e]', ['opinion'],
              '同じ意見・教説の対象について肯定される内容の閉じた性質記述。適用先の話題はh224zで別に指す。参照だけから誰かの採用、内容の真理、偏見の分類を導かない。'),
    'h224z': ('[a] a', ['opinion'],
              '同じ意見・教説に関してh224yの内容記述を適用する話題の参照。人や集団の任意の別話題へ付け替えず、参照だけで内容の真理や採用を保証しない。'),
    'h225a': ('[a a a d d] c', ['role', 'prior', 'later', 'earlier', 'after'],
              '同じ社会的実践の指定役割について、先の局面の担い手から後の局面の担い手へ務めが引き継がれる継続関係がある。中間の担い手を経る場合も含む。血縁、同一職種、単に先に活動しただけでは足りない。両者の実際の役割保持、人物の区別、時点の有効性と前後関係は別に検査する。'),
}
MEANINGS = {
    'r2nz': '同じ意見について本人が同じ話題・内容を肯定する実際の判断を行い、その判断で内容を確定した原則として採用するが、その本人による十分な根拠の吟味・確認は済んでいない、という内容の族。偏見の明示した読みであり、内容が必ず偽であること、差別的な内容であること、悪意や本人の不能を追加しない。',
    'r2oa': '与えられた内容の関数を話題へ適用して断言する発話の族。閉じた適用で同じ意見のh224yを渡す。発話を構成すること自体は話者・受け手の信念や内容の真理を主張しない。',
    'r2ob': '同じ人の同じ生起行為が、同じ受け手へ同じ意見を提示し、その受領・理解と、受け手におけるr2nzの実際の成立、その行為による同じ状態の結果生成を伴う。意見の閉じた名前と元の参照の一致も要求する。提示しただけ、既に持っていた偏見との単なる共存、理解なき接触では足りない。',
    'r2oc': '指定した意見のr2nzが、指定した先行点に同じ本人へ成立していたという内容の族。後の評価点に移っても要因の時点を先行点に固定する。後にその偏見を放棄した場合も、過去の状態が要因であることは表せる。',
    'r2od': '同じ人にその状況が不利益をもたらすという既存urの内容。何を不利益とみなすかはurの意味規約と文脈に依存し、恐怖や加害意図で代用しない。',
    'r2oe': '同じ履歴で、r2obによる植え付けの点が不利益の点より前にあり、その同じ受け手の先行する偏見採用r2ocが同じ対象者の後の不利益r2odに因果的に寄与する。rqquで要因・結果の実際の成立も要求する。対象者が生み手本人か先任者を持つ者かはまだ引数に残し、単なる後続・共存から因果を導かない。',
    'r2of': '異なる二人が同じ役割を同じ履歴の前後点で実際に担い、同じ役割の務めの継続関係h225aで結ばれる。間に別の担い手がいてもよく、血縁だけや別役割の保持を先任関係へ数えない。',
    'r2og': 'r2oeで実際に同じ偏見採用を生じさせた人が、後にその害を受ける本人であるか、その同じ被害者のr2ofの先任者であるという選言を結ぶ。生み手を無関係な別の人から選び直さず、受け手・意見・生成行為・要因・不利益・前後点を共有する。両方の枝の成立は要求しない。',
}
LIMITS = [
    'Vorurtheileは、十分な根拠を吟味・確認しないまま確定した原則として採用された判断という読み。単に暫定的な判断、必ず偽である判断、現代の差別的先入観だけに限定した分類とはしない。',
    'Jäsche編Logikの予備判断と偏見の区別を補助に用いる。1800年の編集された講義用論理学と1784年の本文を同一の発言とはせず、採用した意味の範囲を明示する。',
    'pflanzenの対象側を、提示・受領・理解により同じ受け手に当該状態を生じさせることとして構成する。提示の媒体、悪意、全ての後見人の意図、内容の真理は補わない。植物を植える描写との非字義的な対応は別途必要である。',
    'sich rächenの対象側には、意図的な処罰とは異なる、先行する状態から後の不利益への因果的な反作用という読みを採る。r2ogで生み手本人または生み手の役割を継いだ者へ結ぶが、最後に返ることの談話上の位置づけと全対象範囲は別に必要である。',
    'Urheberは、この文脈で同じ受け手の当該の偏見採用を生じさせた者という因果的な生み手の読み。人類史上でその内容を初めて発明した者とはしない。Vorgängerは同じ社会的実践の役割の先任者であり、直接一代前という制限、血縁、正式な任命儀礼を加えない。',
    'r2oeは同じ先行点の偏見採用を要因とし、後の点でまだ偏見を保持していることを余分に要求しない。時間順序は厳密に検査するが、唯一原因・十分原因や反作用の最終性は加えない。',
    '既存60文・13区間の判断・先頭二文382非空白文字を保持する。後半の全対象範囲と参照供給、zuletzt、so/weil、denen selbst、描写と文全体の閉じた帰属・通読が残る。今回の定義だけで後半の確認済み文字数を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2nz[opinion a] h[a] e[i[person a][b point[
 w[k aa[v person]][g judgment a[
 w[k fa[v person v judgment v point]][w[k fb[v judgment k h224z[v opinion] v point]][
 w[k hznn[v judgment k h224z[v opinion] k h224y[v opinion] e[v person][v person] v point]][
 w[k h224w[v judgment v point]][u[k h224x[v person k h224z[v opinion] k h224y[v opinion] v point]]]
 ]]]
 ]]
]]].
d r2oa[claim h[a] e] h[a] f[i[topic a][j s[c[v claim][v topic]]]].
d r2ob[planter a act a recipient a opinion a name i[a] point d] c[
 w[e[s[v name]][v opinion]][w[k aa[v planter]][w[k aa[v recipient]][
 w[k dg[v act v point]][w[k df[v planter v act v point]][w[k f3[v planter v act v point]][
 w[k f2[v act v recipient k h224z[v opinion] o a[r[p r2oa]][k h224y[v opinion]] v point]][
 w[k h6e[v act v recipient k h224z[v opinion] o a[r[p r2oa]][k h224y[v opinion]] v point]][
 w[k h6g[v recipient k h224z[v opinion] o a[r[p r2oa]][k h224y[v opinion]] v point]][
 w[t[c[k r2nz[v opinion]][v recipient]][v point]][
 k g3[v act v recipient o a[r[p r2nz]][v name] v point]
 ]]]]]]]]]]
].
d r2oc[opinion a earlier d] h[a] e[i[person a][b anchor[
 t[c[k r2nz[v opinion]][v person]][v earlier]
]]].
d r2od[person a] e[b point[k ur[v person v point]]].
d r2oe[planter a act a recipient a opinion a name i[a] earlier d earliername i[d]
 later d target a history h[d] c before h[d d] c] c[
 w[e[s[v earliername]][v earlier]][w[k ta[v history v before]][
 w[c[v history][v earlier]][w[c[v history][v later]][w[c[v before][v earlier v later]][
 w[k r2ob[v planter v act v recipient v opinion v name v earlier]][
 k rqqu[v recipient o a[r[p r2oc]][v name v earliername]
 v target r[p r2od] v later]
 ]]]]]]
].
d r2of[prior a successor a role a earlier d later d history h[d] c before h[d d] c] c[
 w[k aa[v prior]][w[k aa[v successor]][w[u[e[v prior][v successor]]][
 w[k ta[v history v before]][w[c[v history][v earlier]][w[c[v history][v later]][
 w[c[v before][v earlier v later]][w[k hzwn[v prior v role v earlier]][
 w[k hzwn[v successor v role v later]][k h225a[v role v prior v successor v earlier v later]]
 ]]]]]]]]
].
d r2og[planter a act a recipient a opinion a name i[a] earlier d earliername i[d]
 later d target a role a history h[d] c before h[d d] c] c[
 w[k r2oe[v planter v act v recipient v opinion v name v earlier v earliername
 v later v target v history v before]][
 x[e[v planter][v target]][k r2of[v planter v target v role v earlier v later v history v before]]
 ]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2og']), statements=[])
    declarations = {d['name']: d for d in added}
    basis = dict(status='prejudice_instilling_and_later_adverse_effect_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/reversal-focus-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
