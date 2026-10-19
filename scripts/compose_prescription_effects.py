"""Derive rule-attributed normative targets from applicable prescriptions."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.semantic_reviews import digest
from noema.meaning_catalog import load_catalog
from scripts.compose_grounded_step import ROOT, closure

SOURCE = 'examples/v016/kant-polymorphic-forms.noema'
SOURCE_BASIS = 'data/polymorphic-forms-basis-v1.json'
LIBRARY = 'examples/v016/prescription-effects.noema'
BASIS = 'data/prescription-effects-basis-v1.json'
MEANINGS = {
    'r2fn': '一個体から内容への目標記述を、長さ一の個体列から内容への記述へ包む。列の唯一の対象へ同じ目標を適用する構文を保持する。空列・過剰な列は成立せず、生成時は目標を実行しない。元の目標記述が異なれば、真偽が同じでも包みを同一化しない。',
    'r2fo': '規定の目標を渡す列の長さがちょうど一であるという規約。内容の成立や本人の役割を意味しない。',
    'r2fp': '明示した一つの規定採用の証拠からの要求寄与。規定そのものを規範の出所とし、採用者は別に保持する。同じ立場の本人についてrbbの適用が成立し、要求対象が同じ目標をr2fnで包んだ記述・本人一人の列・同じ肯否である。目標の実現、正当性、積極的許可や他の規定からの要求は含めない。',
    'r2fq': '同じ規定を出所とするr2fpの寄与が、いずれかの採用者・条件記述・目標記述について存在する。規定の存在だけでは本人への要求にならず、立場と条件を同じ本人・文脈で検査する。全ての記述への存在量化を、既知の少数の規定で代用しない。',
}
LIMITS = [
    'rbaの既存の意味規約は条件付きの要求としての採用を含む。その規約を共通の規範対象へ接続する定義であり、単なる署名・承認・記録から要求を導く一般法則ではない。',
    '規範の出所には規定を渡し、その採用者を同じ引数へ潰さない。要求がこの規定に帰属するという構成であり、既存h7kの全ての解釈をこの関数へ自動で置き換えない。',
    'r2fpが偽でも他の証拠や規定からの要求がないとは言えない。一つの証拠の寄与と、r2fqの全記述に及ぶ存在条件を区別する。',
    '適用条件の評価は必要だが、要求を述べるだけでは目標を実行しない。不履行rdwだけが同じ目標の真偽を評価する。型付きのNoema記述だけを用い、原語の文言を埋め込まない。',
    '制度の成立、制定権限、普遍的な道徳的拘束、例外・優先順位・期限・制裁・実行能力は新たに定義していない。相反する要求の存在から両目標の事実を導かない。',
    '既存の一人に対する条件付き規定を接続する。定型関数一般の型拡張と、規範の対象型一般の拡張は別であり、後者を完了したとはしない。',
    'Satzungenの読みの基礎を補うが、原稿・登録簿・既存の意味判断を変更せず、第三文の意味確認や新しい原文対応範囲を主張しない。',
]


@lru_cache(None)
def catalog(): return load_catalog(ROOT, SOURCE_BASIS)


def definitions():
    return '''
d r2fn[goal i[h[a] e]] i[h[j[a]] e][o a[
 r[i[target h[a] e][i[bindings j[a]][b point[g person a[w[
 e[d[v bindings]][n p b b]][w[a[v bindings][n p a b][v person]][t[c[v target][v person]][v point]]]]]]]]
 ][v goal]].
d r2fo[bindings j[a]] c[k rdr[v bindings n p b b]].
d r2fp[rule a issuer a ruledrole a condition i[h[a] e] goal i[h[a] e] positive c holding h[a a d] c
 source a person a role a description i[h[j[a]] e] bindings j[a] polarity c context d] c[
 w[e[v source][v rule]][w[e[v role][v ruledrole]][w[e[v description][k r2fn[v goal]]][w[
 e[v bindings][l[a][v person]]][w[e[v polarity][v positive]][
 k rbb[v rule v issuer v person v ruledrole v condition v goal v positive v context v holding]]]]]]
].
d r2fq[source a person a role a description i[h[j[a]] e] bindings j[a] polarity c context d holding h[a a d] c] c[
 g issuer a[g condition i[h[a] e][g goal i[h[a] e][
 k r2fp[v source v issuer v role v condition v goal v polarity v holding
 v source v person v role v description v bindings v polarity v context]
 ]]]
].
'''


def build():
    old = catalog(); assert not set(MEANINGS) & set(old.entries)
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rbb', 'rbc', 'rbd', 'rdr', 'rds', 'rdt', 'rdv', 'rdw', 'riv']), statements=[])
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = [], {}
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'definition': meanings[n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
        else:
            e = old.entries[n]
            primitives.append(dict(symbol=n, parameters=d['parameters'], result=d['result'], arguments=e['arguments'], meaning_ja=e['meaning_ja']))
    basis = dict(status='applicable_prescriptions_connected_to_normative_targets', document=LIBRARY,
        primitives=primitives, definitions=meanings, limitations=LIMITS,
        origin_sha256={SOURCE: digest((ROOT / SOURCE).read_bytes()), SOURCE_BASIS: digest((ROOT / SOURCE_BASIS).read_bytes())})
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Four definitions; no new primitives; manuscript and registry preserved', flush=True)
