"""Compose actual progress into, and retention within, a near-target region."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_limits import v, call as k, app, op, both, quant, definition

PARENT = 'examples/v016/kant-acquired-affection.noema'
PARENT_BASIS = 'data/acquired-affection-basis-v1.json'
FULL = 'examples/v016/kant-graded-change.noema'
CORE = 'examples/v016/graded-change-core.noema'
BASIS = 'data/graded-change-basis-v1.json'
ANNOTATIONS = 'data/graded-change-identifiers-v1.json'
SCALE = [('scale', 'h[a] c'), ('less', 'h[a a] c'), ('near', 'h[a] c'), ('low', 'a'), ('high', 'a'), ('assessed', 'h[d a] c')]
CHANGE = [('history', 'h[d] c'), ('before', 'h[d d] c'), ('person', 'a'), ('process', 'a'),
          ('earlier', 'd'), ('later', 'd'), ('changes', 'h[a d d] c'), ('affected', 'h[a a d d] c')] + SCALE
MEANINGS = {
    'r2cl': '同じ評価関係の同じ状況で、指定値が尺度内にあり、評価された値であり、その状況で評価された全値と同一である。評価欠落、多値、尺度外の値を確定した程度として扱わない。',
    'r2cm': '同じ尺度の厳密な全順序rqsqと最高値の手前の近接域rqssを検査し、指定状況の一意な評価値r2clがその近接域にある。最高値への到達、確率の大きさ、過去の変化とは分ける。',
    'r2cn': '同じ順序付き履歴の実際の過程tgで本人が変化を受け、同じ尺度・評価関係の一意な前後値が厳密に増加し、後端が近接域に入る。前端が既に近接域にある場合も許す。単に後端が近いことや前後の並置だけでは成立しない。',
    'r2co': 'r2cnの同じ変化の後端から、同じ履歴に属する後続または同時の基準まで、近接域にある状態を保持する。域内での増減は許し、前後区間の全過程での単調増加や最高値への到達、未来の永続は要求しない。',
    'r2cp': '本人の現在の未成熟bfに、r2coの程度変化と結果状態の保持を結ぶ部分ひな形。評価関係へ本人・bfの記述・比較基準・現在の評価文脈・各履歴点・程度を同じ順で渡す。本性として何を比較するか、尺度と評価の根拠は明示的な引数として残す。',
}
LIMITS = [
    'カント第三段落のbeinaheとgewordenenの作用範囲を検討するための構成。現在の近さ、近接域への新規の進入、近接域内を含む程度の進行を区別する。原文の唯一の読解や段落全体の確認とはしない。',
    '近接域は上端に近いが上端そのものを含まない既存rqssの厳密な読みを採る。割合・確率・距離・等間隔や固定した数値閾値は与えず、近さの基準は入力として明示する。',
    '実際の過程とその本人への作用は既存ag・laで結ぶ。尺度値の増加だけから因果や変化過程を捏造しない。途中の単調性や連続性は要件にしない。',
    '比較基準・尺度・評価関係は全履歴点で固定する。値の一意性は検査するが、現実の評価根拠の妥当性、比較対象の選定、近接域の適切さは別途必要である。',
    'r2cpの比較基準は未充足の明示的な引数。本性の内容を値や未解釈な原文専用記号へ置換した完成訳ではない。後天的な定着を生来の起源と区別するための比較特性の構成は残る。',
    '51本文文と十二単位の既存判断を保つ。第一文の個々人の困難・自己の働きかけ・also、人称と量化、著者への帰属は接続せず、意味確認済み分量を増やさない。',
]


def parameters(fields):
    return ' '.join(n + ' ' + t for n, t in fields)


def refs(fields):
    return [v(n) for n, _ in fields]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    use = lambda name, *names: app(v(name), *(v(n) for n in names))
    unique = both(use('scale', 'degree'), use('assessed', 'point', 'degree'),
        quant('f', 'other', 'a', op('y', use('assessed', 'point', 'other'), op('e', v('degree'), v('other')))))
    text = definition('r2cl', 'assessed h[d a] c scale h[a] c point d degree a', unique)
    valid = both(k('rqsq', *(v(n) for n in ('scale', 'less', 'low', 'high'))),
                 k('rqss', *(v(n) for n in ('scale', 'less', 'near', 'low', 'high'))))
    near_at = lambda point: k('r2cm', *refs(SCALE), v(point))
    value_at = lambda point, degree: k('r2cl', v('assessed'), v('scale'), v(point), v(degree))
    text += definition('r2cm', parameters(SCALE) + ' point d', both(valid,
        quant('g', 'degree', 'a', both(value_at('point', 'degree'), use('near', 'degree')))))
    growth = quant('g', 'initial', 'a', quant('g', 'final', 'a', both(
        value_at('earlier', 'initial'), value_at('later', 'final'), use('less', 'initial', 'final'), use('near', 'final'))))
    text += definition('r2cn', parameters(CHANGE), both(valid,
        k('tg', *(v(n) for n in ('history', 'before', 'process', 'earlier', 'later', 'changes'))),
        use('affected', 'person', 'process', 'earlier', 'later'), growth))
    le = lambda a, b: op('x', op('e', v(a), v(b)), use('before', a, b))
    interval = both(use('history', 'point'), le('later', 'point'), le('point', 'anchor'))
    text += definition('r2co', parameters(CHANGE) + ' anchor d', both(k('r2cn', *refs(CHANGE)),
        use('history', 'anchor'), le('later', 'anchor'),
        quant('f', 'point', 'd', op('y', interval, near_at('point')))))
    source_fields = [('person', 'a'), ('reference', 'a')] + SCALE[:-1] + [('measured', 'h[a i[h[a] e] a d d a] c')]
    bindings = dict(history='i[point d][k ia[v person v anchor v point]]',
        before='i[first d last d][k ic[v first v last v anchor]]',
        person=v('person'), process=v('process'), earlier=v('earlier'), later=v('later'), changes='p ag', affected='p la',
        **{n:v(n) for n, _ in SCALE[:-1]},
        assessed='i[point d degree a][c[v measured][v person r[p bf] v reference v anchor v point v degree]]')
    result = k('r2co', *(bindings[n] for n, _ in CHANGE), v('anchor'))
    for name, sort in (('later', 'd'), ('earlier', 'd'), ('process', 'a')):
        result = quant('g', name, sort, result)
    content = 'b anchor[' + both(op('t', k('bf', v('person')), v('anchor')), result) + ']'
    text += 'd r2cp[' + parameters(source_fields) + '] e[' + content + '].'
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + definitions())
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    added = doc['declarations'][size:]; assert len(added) == 5 and all(d['kind'] == 'definition' for d in added)
    basis = dict(status='graded_actual_change_and_retention_with_explicit_reference_schema', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/acquired-affection-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)
    print('Five definitions composed; no new primitives or authored assertions', flush=True)
