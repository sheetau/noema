"""Separate lack of an easy strategy from lack of any affordable success path."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_graded_change import parameters
from scripts.compose_relative_difficulty import ORDER, METHOD, TASK, refs
from scripts.compose_limits import v, call as k, app, op, both, quant, definition
from scripts.compose_courageous_undertaking import replace_symbols

PARENT = 'examples/v016/kant-individual-departure.noema'
PARENT_BASIS = 'data/individual-departure-basis-v1.json'
FULL = 'examples/v016/kant-assessed-difficulty.noema'
CORE = 'examples/v016/assessed-difficulty-core.noema'
BASIS = 'data/assessed-difficulty-basis-v1.json'
ANNOTATIONS = 'data/assessed-difficulty-identifiers-v1.json'
SETTING = [('actor', 'a'), ('start', 'd')] + ORDER + [('capacity', 'h[a d a] c'), ('limit', 'a')]
ASSESSMENT = [('actor', 'a'), ('start', 'd'), ('scale', 'h[a] c')] + METHOD[6:]
MAPPING = {'r2di': 'r2dw', 'r2dl': 'r2dx', 'r2dm': 'r2dy', 'r2do': 'r2dz'}
MEANINGS = {
    'r2dr': '同じ本人・開始に対する一意な投入上限、質的尺度の有界全順序、上限に沿った余力の少ない帯を検査する。方法の存在や達成の可能性は含まない。',
    'r2ds': '全ての利用可能な方法で採用結果が非空で想定結果内にあり、そのうち達成する各経路の必要量が尺度内で一意に評価されている。全結果では成功しない方法の成功経路も調べる。既知の失敗経路の必要量は不要だが、未知の成否や量を失敗へ補わない。',
    'r2dt': '同じ利用可能な方法の有効な結果評価に、指定の達成関係と本人の上限内の一意な必要量を満たす経路が少なくとも一つある。同じ方法の全採用結果での達成、成功の確保、現在の実行は要求しない。',
    'r2du': '尺度・上限・帯が有効でr2dsの経路評価が整い、全採用結果で余裕を確保して達成できる方法r2dfはない。到達する経路の存在も不在もここでは主張しない。評価された選択肢についての非容易性であり、未評価という認識状態ではない。',
    'r2dv': 'r2duと同じ尺度・上限・帯とr2dsの評価の下で、上限内で達成する採用経路r2dtが一つもない。成功を確保できないだけの方法や、未評価とは区別する。指定した方法・結果・開始基盤の範囲に相対的であり、全世界・全未来の絶対的不可能性ではない。',
    'r2dw': '本人の現在の未成熟と、同じ本人の自己作業によるh4pへの方法についてr2duを結ぶ。努力の実施者・受益者・評価種類を保持し、余裕のある達成方法の不在を述べる。誰にでも達成する方法があるという旧r2diの存在条件を加えない。',
    'r2dx': '同じ本人・開始基準の力の尺度列、順序、両端、帯をr2dwへ渡す。性向の尺度とは分け、空・重複した尺度や欠落した評価を有効な困難さへ置き換えない。',
    'r2dy': '非空で人だけからなる同じ対象範囲の各人に、既存r2dkの性向と新しいr2dxの非容易性を結ぶ。各人の到達可能性や到達不能を全称文へ追加しない。',
    'r2dz': '第一文の新しい内容r2dyを同じ著者・箇所・文脈へ引用して帰属し、同じ六箇所からの帰結提示と順序を保持する。旧内容の引用を混ぜず、世界内容の真偽や論理的含意は評価しない。',
}
LIMITS = [
    '第一文のschwerを、現在の本人にとって余裕を持って達成を確保できる方法がないという、文脈相対的な非容易性として読む。全員が達成可能という含意を取り除くが、一般に難しいという語の全用法をこの定義へ還元しない。',
    'AA VII146-147では容易・困難を可能性との関連から論じ、余力と煩わしさを区別する。この後年の記述とAA VIII036の文脈は今回の読みの参考であり、1784年の文を一意に決定する証明ではない。',
    '成功を確保できる方法の不在と、成功する採用経路の不在を分ける。一つは成功し一つは失敗する方法では、非容易性が成立しても、経路の不在は成立しない。結果採用の妥当性は既存の文脈規約に依存する。',
    '方法が存在しないと既知である場合は、同じ基盤では容易な方法も達成経路もない。ただし、未入力の方法一覧を既知の空集合として与えてはならない。利用可能性・成否・必要量が未知なら評価を保留する。',
    '量を評価する対象を、全結果で達成する方法だけから、個々の成功経路まで広げる。混合結果を持つ方法の未測定の成功経路を、到達不能の証拠にしない。失敗経路の未測定はそれだけで否定判断を妨げない。',
    'r2dvは評価範囲内で資源面の達成経路がないという診断であり、現実に成功しなかったこと、物理的な不可能性、将来の訓練後も不可能なこととは別である。本文はr2duを使い、この診断結果を追加主張しない。',
    '旧定義と履歴は保持する。現在の第52文だけを新しい引用内容へ置換し、先行51文と十二単位の意味判断は変えない。原文の対応範囲も意味確認済み分量も増やさない。',
    '本性に近い性向の読解、尺度と近接域の校正、形容節の情報構造は引き続き明示した読みとして検討する。今回の修正だけで第一文や段落の意味一致を認定しない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    use = lambda name, *names: app(v(name), *(v(n) for n in names))
    ceiling = 'i[point d value a][c[v capacity][v actor v point v value]]'
    setting = both(k('rqsq', *(v(n) for n in ('scale', 'less', 'low', 'high'))),
        k('r2cl', ceiling, v('scale'), v('start'), v('limit')),
        k('r2db', *(v(n) for n in ('scale', 'less', 'low', 'limit', 'band'))))
    text = definition('r2dr', parameters(SETTING), setting)
    selected = use('selected', 'actor', 'plan', 'start', 'end')
    success = use('success', 'actor', 'plan', 'start', 'end')
    need = 'i[point d value a][c[v required][v actor v plan v start v point v value]]'
    unique = quant('g', 'amount', 'a', k('r2cl', need, v('scale'), v('end'), v('amount')))
    valid = k('xa', v('actor'), v('plan'), v('start'), v('outcomes'), v('selected'))
    body = quant('f', 'plan', 'a', op('y', use('available', 'actor', 'plan', 'start'), both(valid,
        quant('f', 'end', 'd', op('y', both(selected, success), unique)))))
    text += definition('r2ds', parameters(ASSESSMENT), body)
    path = k('r2dc', *(v(n) for n in ('actor', 'plan', 'start', 'end', 'limit', 'scale', 'less', 'required')))
    text += definition('r2dt', parameters(METHOD), both(use('available', 'actor', 'plan', 'start'), valid,
        quant('g', 'end', 'd', both(selected, success, path))))
    for name, predicate, extra in [('r2du', 'r2df', [v('band')]), ('r2dv', 'r2dt', [])]:
        text += definition(name, parameters(TASK), quant('g', 'limit', 'a', both(
            k('r2dr', *refs(SETTING)), k('r2ds', *refs(ASSESSMENT)),
            op('u', quant('g', 'plan', 'a', k(predicate, *refs(METHOD), *extra))))))
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    # Preserve historical definitions; only the new chain uses the weaker,
    # explicitly assessed statement instead of presumed feasibility.
    mapping = dict(MAPPING, r2dh='r2du')
    for name in ('r2di', 'r2dl', 'r2dm', 'r2do'):
        row = replace_symbols(deepcopy(old.entries[name]['declaration']), mapping)
        row['name'] = MAPPING[name]; doc['declarations'].append(row)
    assert statements[-1]['body']['content']['symbol'] == 'r2do' and len(statements) == 52
    doc['statements'] = deepcopy(statements[:-1]) + [replace_symbols(statements[-1], MAPPING)]
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS) + ['wh']), statements=[doc['statements'][-1]])
    added = doc['declarations'][size:]; assert len(added) == 9
    basis = dict(status='assessed_non_ease_without_feasibility_presupposition', document=FULL, parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {key: d[key] for key in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/individual-departure-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Nine definitions, no new primitives; the first-sentence claim revised', flush=True)
