"""Compose an acquired internal contribution and its withdrawal comparison."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_graded_change import SCALE, parameters
from scripts.compose_limits import v, call as k, app, op, both, quant, definition

PARENT = 'examples/v016/kant-graded-change.noema'
PARENT_BASIS = 'data/graded-change-basis-v1.json'
FULL = 'examples/v016/kant-internalized-state.noema'
CORE = 'examples/v016/internalized-state-core.noema'
BASIS = 'data/internalized-state-basis-v1.json'
ANNOTATIONS = 'data/internalized-state-identifiers-v1.json'
PRIMITIVES = {
    'hzyz': (['pattern', 'person', 'point'], 'この組織化された過程の構成が、この時点でこの本人の内的な構成として存在する。所有物や外部の指導者とは分ける。構成の活動、形成の原因、性質への寄与、生得的か後天的かは別条件である。'),
    'hzzb': (['pattern', 'point'], 'この組織化された構成による過程が、この局面で作動している。構成が存在するだけ、実行された回数、特定の結果への寄与とは区別する。身体的・心理的な機構の細部をこの関係だけで還元したとはしない。'),
    'hzzc': (['experience', 'pattern', 'earlier', 'point'], 'この前時点の同じ経験が、この後時点の同じ構成の形成に実際に寄与している。時系列や反復回数だけからは導かず、現在の作動や結果への寄与は含まない。先天的な要因の併存や他の形成原因は排除しない。'),
    'hzzd': (['pattern', 'person', 'description', 'anchor', 'point', 'candidate'], '固定した評価文脈で、本人の指定履歴点の内的構成と関連する背景を保ち、記述した性質への外からの維持作用の更新を比較する候補局面。履歴点自体の状態や比較後の性質の成立を保存条件にしない。比較する経過期間と背景は文脈入力とし、成立した結果で候補を選ばない。学習し直した別の構成や別人への変更も含めない。'),
    'hzze': (['person', 'description', 'candidate'], 'この比較局面で、記述した性質をこの本人について維持する外部からの働きかけが更新されている。単なる外物の存在、通常の生命維持条件、過去の指導の履歴とは分ける。未知の更新を不存在として入力してはいけない。'),
}
MEANINGS = {
    'r2cq': '本人が参加する実際の活動があり、その同じ活動で別の人から指導される。後天的な形成の経験対象として使う。未成熟という状態そのものを経験した活動の代用にせず、成功や反復回数を要求しない。',
    'r2cr': '指定された構成が作動しているという一変数の内容。因果関係で使う閉じた性質記述を与える。本人への所属や結果はこの内容に含めず、呼出側で同じ構成に結ぶ。',
    'r2cs': '本人の内的構成があり、同じ順序付き履歴の過去に、本人が他者の指導下で活動した経験があり、その同じ経験が現在の同じ構成の形成へ寄与する。活動の実際の成立もr2cqで確認する。経験の存在だけ、生来の要因だけ、別の構成の形成だけでは成立しない。',
    'r2ct': '同じ本人の内的構成が現在作動し、本人の未成熟bfが成立し、その構成の作動がその未成熟へ実際に因果的に寄与する。同時に存在するだけでは成立しない。唯一・必要・十分な原因や未来の持続とは主張しない。',
    'r2cu': '同じ本人・構成・未成熟の記述・評価文脈・履歴点の比較候補から、現在の外的な維持作用の更新がない局面を選ぶ。その非空範囲でr2ctの内的な因果的寄与を評価し、与えた程度の両端をrqsrで整合させる。すべて不成立なら最小、すべて成立なら最大、中間なら両端以外。中間値を件数から計算しない。',
    'r2cv': '経験による内的構成の形成r2csと現在の内的寄与r2ctを、同じ本人・構成についてr2cpの程度増加と近接状態の保持へ接続する。測定関係をr2cuで制約し、比較する性質を外的な更新なしの内的寄与に定める。本性に近いという句の明示的な解釈候補であり、原文の全語義を確定する定義ではない。',
}
LIMITS = [
    '本性との比較を、経験に由来する構成が内側から状態へ寄与し、外的な維持の更新がなくてもその寄与が広く成立するという読みへ具体化する。自然一般、生来の性質、単なる慣れ、全習慣の同義定義ではない。',
    'Kantの後年のAnthropologie AA VII149は習慣を内的な強制として述べるが、1784年の句へ今回の反事実的な比較基準が一意に導かれるわけではない。無反省・強制性・自動性の全条件はこの比較軸だけでは表していない。',
    '指導下での経験を形成の一因として採ること、候補の期間と背景、外的更新の範囲、中間値と近接域の校正は明示的な解釈上の選択である。原文にない神経機構や数値閾値を補わない。',
    'r2cuは比較候補の選定と両端の整合を検査するが、中間値の大小が妥当かを自動証明しない。r2cvでは同じ尺度・測定関係を固定し、欠落や多値を以前の低い程度とみなさない。',
    '因果的寄与は唯一原因ではない。比較局面の外的更新の不在と過去の外的な影響の不在を混同しない。後天的な形成への寄与は生来の要因の併存を排除しない。',
    '既存51本文文と十二単位の意味判断を保持する。句全体、個々人の離脱の困難、also、人称と量化、著者帰属は未確認であり、原文の新しい意味確認済み文字数は計上しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = 'r hzyz[a a d] c.r hzzb[a d] c.r hzzc[a a d d] c.r hzzd[a a i[h[a] e] d d d] c.r hzze[a i[h[a] e] d] c.'
    def content(name, fields, point, body):
        return 'd ' + name + '[' + fields + '] e[b ' + point + '[' + body + ']].'
    def holds(name, *args, point='point'):
        return op('t', k(name, *(v(n) for n in args)), v(point))
    practice = quant('g', 'act', 'a', both(k('dg', v('act'), v('point')), k('df', v('person'), v('act'), v('point')),
        quant('g', 'guide', 'a', both(op('u', op('e', v('guide'), v('person'))), k('ad', v('guide'), v('person'), v('act'), v('point'))))))
    text += content('r2cq', 'person a', 'point', practice)
    text += content('r2cr', 'pattern a', 'point', k('hzzb', v('pattern'), v('point')))
    history = 'i[past d][k ia[v person v point v past]]'
    before = 'i[first d last d][k ic[v first v last v point]]'
    past = quant('g', 'earlier', 'd', both(k('ia', v('person'), v('point'), v('earlier')),
        k('ic', v('earlier'), v('point'), v('point')), holds('r2cq', 'person', point='earlier'),
        quant('g', 'event', 'a', both(k('h3e', v('person'), v('event'), 'r[p r2cq]', v('earlier')),
                                   k('hzzc', v('event'), v('pattern'), v('earlier'), v('point'))))))
    text += content('r2cs', 'person a pattern a', 'point', both(k('hzyz', v('pattern'), v('person'), v('point')),
        k('ta', history, before), k('ia', v('person'), v('point'), v('point')), past))
    text += content('r2ct', 'pattern a person a', 'point', both(k('hzyz', v('pattern'), v('person'), v('point')),
        holds('r2cr', 'pattern'), holds('bf', 'person'), k('hzie', v('pattern'), 'r[p r2cr]', v('person'), 'r[p bf]', v('point'))))
    cases = 'i[candidate d][' + both(k('hzzd', v('pattern'), v('person'), 'r[p bf]', v('anchor'), v('point'), v('candidate')),
        op('u', k('hzze', v('person'), 'r[p bf]', v('candidate')))) + ']'
    response = 'i[candidate d][' + holds('r2ct', 'pattern', 'person', point='candidate') + ']'
    text += definition('r2cu', 'pattern a person a anchor d point d scale h[a] c degree a low a high a',
        k('rqsr', cases, response, v('scale'), v('degree'), v('low'), v('high')))
    fields = [('person', 'a'), ('pattern', 'a')] + SCALE[:-1] + [('measured', 'h[a i[h[a] e] a d d a] c')]
    # The original measurement input is retained, but every value must agree
    # with the explicitly composed withdrawal comparison at the same point.
    raw = 'i[at d value a][c[v measured][v actor v description v reference v anchor v at v value]]'
    assessed = 'i[actor a description i[h[a] e] reference a anchor d point d degree a][' + both(
        k('r2cl', raw, v('scale'), v('point'), v('degree')),
        k('r2cu', v('reference'), v('actor'), v('anchor'), v('point'), v('scale'), v('degree'), v('low'), v('high'))) + ']'
    args = 'v person v pattern ' + ' '.join('v ' + n for n, _ in SCALE[:-1]) + ' ' + assessed
    return text + content('r2cv', parameters(fields), 'now', both(holds('r2cs', 'person', 'pattern', point='now'),
        holds('r2ct', 'pattern', 'person', point='now'), op('t', 'k r2cp[' + args + ']', v('now'))))


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(MEANINGS) | set(PRIMITIVES)) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]; by_name = {d['name']: d for d in added}
    assert len(added) == 11
    basis = dict(status='acquired_internal_contribution_with_withdrawal_comparison_candidate', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
        primitives={n: dict(parameters=by_name[n]['parameters'], result=by_name[n]['result'], arguments=args, meaning_ja=meaning)
                    for n, (args, meaning) in PRIMITIVES.items()}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/graded-change-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Six definitions and five general inputs composed; no new authored assertions', flush=True)
