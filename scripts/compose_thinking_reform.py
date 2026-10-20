"""Compose a change in assessed independent judging across a fixed scope."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-revolution-routes.noema'
PARENT_BASIS = 'data/revolution-routes-basis-v1.json'
FULL = 'examples/v016/kant-thinking-reform.noema'
CORE = 'examples/v016/thinking-reform-core.noema'
BASIS = 'data/thinking-reform-basis-v1.json'
ANNOTATIONS = 'data/thinking-reform-identifiers-v1.json'
PRIMITIVES = {
    'h226u': ('[a d a] c', ['person', 'scope', 'topic'],
              '同じ本人の判断の仕方を評価する、指定文脈で固定した判断対象の全範囲。文脈上の生活上・公共的な判断領域を選び、変化の前後や成功の有無で対象を入れ替えない。一つの都合のよい結論だけへ限定しない。範囲の適切さは解釈入力であり、非空性の検査だけから適切さを導かない。'),
    'h226v': ('[a a d d d] c', ['person', 'topic', 'scope', 'anchor', 'candidate'],
              '同じ人と固定した判断対象について、基準時点の判断の仕方を評価する比較場面。判断の成否によらず対象場面を定める。scopeは前後で共通の領域、anchorは変化する本人側状態の評価点。'),
    'h226w': ('[a a d d d] c', ['person', 'topic', 'scope', 'anchor', 'candidate'],
              '比較場面で、同じ本人の基準時点の判断を組み立てる方針・理解・習慣を保持する。後の訓練を先の状態へ持ち込まず、判断の成功そのものを保持条件にはしない。領域scopeは前後で同じまま、anchorごとの方針の相違を許す。'),
    'h226x': ('[a a d d d d] c', ['person', 'topic', 'scope', 'anchor', 'preferred', 'other'],
              '固定領域・本人・判断対象・基準時点について、背景条件から先の比較場面を通常とする厳密な優先関係。自己判断の成否を優先の根拠にせず、例外の除外によって任意の成功を通常にしない。順序と通常場面の非空性は別に検査する。'),
    'h226y': ('[a a d d d a] c', ['person', 'topic', 'scope', 'anchor', 'candidate', 'judgment'],
              '同じ本人の判断の仕方を同じ話題・比較場面で評価するための対応する取り組み。未遂も含めて対応する全活動を指定し、うまく遂行した判断だけを選ばない。実際の生起・自己判断・理由の支持は別条件。'),
}
MEANINGS = {
    'r2ql': '同じ人・話題・領域・評価点・比較場面に対応する全判断が、既存r2gyの実際の生起、自分の理解力の使用、同じ話題と理由の支持、他者による指導の不在を満たす。対応活動の非空性は評価条件r2qoに置く。',
    'r2qo': '同じ人・話題・固定領域・評価点の全比較に本人側の基盤保持、対応活動の非空性、判断への外的機会があり、通常性が整い通常場面が非空である。既存r2guを使い、応答が成功することは要求しない。',
    'r2qm': '人である同じ本人について固定領域の判断対象が非空であり、その全対象のr2qoの評価条件が満たされる。前状態の応答不足を、対象や比較の欠落から作らない。',
    'r2qn': 'r2qmの全評価条件と、固定領域の全判断対象について通常場面の全対応活動のr2qlを要求する。単発の正しい意見や独立判断、知識量の増加だけでは足りない。例外場面や領域外の全生涯における無誤謬性は要求しない。',
    'r2qp': '同じ履歴の前後点を同じ実在の過程agで結び、同じ本人への作用laがある。両時点で同じ固定領域の評価r2qmが有効で、前にr2qnがなく後にある。真の思考様式の改革を、評価済みの自己判断の傾向への実際の変化として読む。本人の特定の自己訓練・流血・永続性・全知を条件に加えない。',
    'r2qq': '固定した領域・起点・履歴・順序の下で、評価点までに同じ人のr2qpを満たす過程があるという結果の内容族。革命の結果記述として引用でき、引用だけで変化や因果を断定しない。',
}
LIMITS = [
    'wahre Reform der Denkungsartは、この文脈で自分の理解力と理由によって判断する仕方への実際の変化と読む。後続の新旧の偏見の入れ替えとの対比を根拠とするが、思考様式一般や道徳的人格の全条件の唯一の定義ではない。',
    '1786年のAA VIII146の自己思考と知識量の区別を照合に用いる。1784年本文へ別著の全命題・普遍化試験・宗教論を追加しない。既存r2gyの理由ある自己判断を、固定領域の通常比較へ分配する採用解釈である。',
    '全比較の対象・基盤・機会・対応活動・通常性は総解釈で供給する。有限モデルや非空性だけで現実の全領域を調査したとはしない。未知は偽へ変えず、前後とも有効な評価を要求する。',
    '改革の過程自体と、革命がその結果を生むという因果は別である。r2qpに自己作業や革命を埋めず、結果への外的原因はr2qkのg3へ接続する。',
    '公衆の対象範囲と共通の候補供給、実際の著者帰属、様相・対比、後半の新旧の偏見と誘導は未統合。既存61文と意味判断を保持し、第五文の意味確認済み分量は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    cases = 'i[scene d][k h226v[v person v topic v scope v anchor v scene]]'
    held = '''i[scene d][w[k h226w[v person v topic v scope v anchor v scene]][
 g judgment a[k h226y[v person v topic v scope v anchor v scene v judgment]]]]'''
    opportunity = 'i[scene d][k hzzzv[v person v topic v scene]]'
    preferred = 'i[first d last d][k h226x[v person v topic v scope v anchor v first v last]]'
    response = 'i[scene d][k r2ql[v person v topic v scope v anchor v scene]]'
    args = ' '.join((cases, held, opportunity, preferred))
    return '''
d r2ql[person a topic a scope d anchor d scene d] c[
 f judgment a[y[k h226y[v person v topic v scope v anchor v scene v judgment]][
 k r2gy[v person v judgment v topic v scene]]]].
d r2qo[person a topic a scope d anchor d] c[k r2gu[''' + args + ''']].
d r2qm[person a scope d anchor d] c[
 w[k aa[v person]][w[g topic a[k h226u[v person v scope v topic]]][
 f topic a[y[k h226u[v person v scope v topic]][k r2qo[v person v topic v scope v anchor]]]]]].
d r2qn[person a scope d anchor d] c[
 w[k r2qm[v person v scope v anchor]][f topic a[y[k h226u[v person v scope v topic]][
 k r2gv[''' + args + ' ' + response + ''']]]]].
d r2qp[person a process a scope d first d last d history h[d] c before h[d d] c] c[
 w[k tg[v history v before v process v first v last p ag]][
 w[k la[v person v process v first v last]][
 w[k r2qm[v person v scope v first]][w[k r2qm[v person v scope v last]][
 w[u[k r2qn[v person v scope v first]]][k r2qn[v person v scope v last]]
 ]]]]].
d r2qq[scope d first d history h[d] c before h[d d] c] h[a] e[
 i[person a][b last[g process a[
 k r2qp[v person v process v scope v first v last v history v before]]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2qq']), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='thinking_reform_result_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/revolution-routes-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
