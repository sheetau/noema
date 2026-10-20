"""Bind four concrete directive contents to complete recipient-indexed demand rows."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_aligned_influence import (
    BASIS as ALIGN_BASIS, LIBRARY as ALIGN_LIBRARY, CODE, RULE, MODEL, WORLD,
    ASSESSMENT, ORDER, TRUE, both)

PARENT = 'examples/v016/kant-everywhere-restriction.noema'
PARENT_BASIS = 'data/everywhere-restriction-basis-v1.json'
FULL = 'examples/v016/kant-demand-candidates.noema'
CORE = 'examples/v016/demand-candidates-core.noema'
BASIS = 'data/demand-candidates-basis-v1.json'
ANNOTATIONS = 'data/demand-candidates-identifiers-v1.json'
CASES = ('h233m', 'h233n', 'h233o', 'h234i')
CONTENTS = ('r2vv', 'r2vw', 'r2vx', 'r2vy')
PRIMITIVES = {
    'h234q': ('[a] a', ['case_node'],
              '指定された発話事例で要求の対象になる行為の型の参照。前三者では議論を行わずに教練・支払い・信仰を行う複合的な行為型、統治者では同じ出所の指示に従って履行する行為型を指す。発話行為そのもの・実行済みの出来事・文章箇所とは区別する。内容は合成定義r2vv〜r2vyで固定し、この参照だけで履行や義務の正当性を主張しない。'),
    'h234r': ('[a a d] a', ['case_node', 'recipient', 'reference'],
              '同じ事例・宛先・基準で、この要求を受ける立場の参照。受け手の立場であり、命令者の職位へ取り替えない。後の公的／私的使用の分類をここで先取りせず、参照だけで実際の役職保持や要求の正当性を保証しない。'),
    'h234s': ('[a a a a ' + CODE + ' c d] c',
              ['source', 'recipient', 'role', 'activity_type', 'content', 'polarity', 'point'],
              '同じ出所が宛先にその立場で、その行為型について段階1の内容記述を本人・行為型へ適用した内容の指定極性を満たすよう要求している。h7aの要求対象を段階1へ拡張した関係で、内容・極性・出所を保持する。発話の提示h234gとは別であり、単に言ったことから要求の現実の効力、履行、法的・道徳的な正当性を自動推論しない。'),
}
MEANINGS = {
    'r2vv': '同じ将校事例の要求対象行為型h234qを第二引数として照合し、その同じ本人について既存r2uxの議論の不実行と教練の内容を評価する。別の行為型や受け手を代用しない。',
    'r2vw': '同じ財務担当官事例の要求対象行為型を照合し、同じ本人の議論の不実行と支払いという既存r2uxの内容を評価する。',
    'r2vx': '同じ聖職者事例の要求対象行為型を照合し、同じ本人の議論の不実行と信仰という既存r2uxの内容を評価する。信仰内容の真理や実際の信仰を引用だけから肯定しない。',
    'r2vy': '同じ統治者事例の服従の行為型を照合し、既存r2uxを通じて同じ出所のr2udの内容を同じ本人について評価する。議論の許可は否定せず、全記述域の網羅性・指示に従う調整を省かない。',
    'r2vz': '四つの固定した事例箇所をそれぞれ対応するr2vv/r2vw/r2vx/r2vyの段階1の閉じた記述へ結ぶ。別の事例の内容、同じ真理値だけを持つ別名の記述、段階0の引用を代用しない。',
    'r2wa': '同じ事例に対応する内容記述r2vzを確認し、先行文と同じh234lの話者・h234mの発話・h232vの基準でr2uvの役割と発話内容へ接続する。要求関係h234sの現実の成立は、この接続から導かない。',
    'r2wb': '先行文と同じ固定宛先を行キーとして、各人に一つの全命令内容を正極性で対応させる。全宛先に同じ話者・本人自身・受け手の立場・対象行為型・同じ内容記述を渡し、全要求の有無r2vlを調べる。人を物理的な記録文書と同一視せず、宛先による表の索引を使う。',
    'r2wc': '同じ宛先別要求表と、先行する本人の自由選択候補h234nをr2vmへ接続する。別人の候補、別の要求内容、別の基準による違反を借りず、世界での現実の違反は要求しない。',
    'r2wd': '同じ先行事例の接続r2waと、宛先別要求表・h234nの自由選択・同じ公衆と啓蒙r2lnへの介入比較r2vrを合わせる。表と世界対応・基準を、有効性の途中で取り替えない。',
    'r2we': '直前の四事例の箇所が異なり、その全てが指定した比較候補範囲に含まれる。候補がこの四事例だけで尽きるという逆向きの含意は置かず、第五の候補や別の制限の種類を排除しない。',
    'r2wf': 'r2wdと同じ事例・要求表・公衆・基準・モデルの接続を保ち、r2vsの評価済みの悪化する組を求める。別の候補の不利益をこの事例へ移さない。',
    'r2wg': '同じ全接続を保ち、r2vtの非悪化を求める。発話の存在だけ、部分的な解除、比較不足からは成立しない。',
    'r2wh': '同じ全接続を保ち、r2vuの非悪化かつ改善を求める。統治者の許可を禁止へ変えず、非悪化だけで促進を補わない。',
}
LIMITS = [
    '第五段落の二問への具体的な候補接続。先行70主張と全意味規約を保持し、新しい著者主張や意味確認済み文字数は追加しない。モデル内の分類を原文の全語義へ昇格しない。',
    '行キーは同じ固定宛先で、一人につき発話の全要求内容を一つの行へまとめる。前三者は議論の不実行と肯定命令を連言のまま保持し、統治者は同じ出所への服従を保持する。許可は要求ではないので服従の行へ混ぜず、既存の発話接続r2uv/r2ulに残す。',
    '行為型h234qと受け手の立場h234rは索引用の意味参照であり、原文に特定の役職保持や独立した実行出来事を追加しない。型の内容はr2uxによる既存命令へ固定し、単なる語句の名前だけを要求の内容にしない。',
    '段階1の要求h234sは、既存の段階0のh7aや発話の提示と自動同一化しない。比較モデルで要求が適用されることは別入力であり、発話があっただけで法的義務が生じる推論規則ではない。',
    '統治者のr2udは全記述域を量化する。有限評価拒否を保持し、内容の接続検査では既存の評価境界と引数を明記する。網羅性を消して有限検査を通すことはしない。',
    '四事例は比較候補に必ず含めるが、それ以外を禁止しない。追加候補の全要求表、啓蒙の質的尺度・対象・期間・背景、通常性か潜在性かの採用読解、二問の照応と帰属、aber/sondern、wohl/gar、回答への接続が残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def aligned():
    return load_catalog(ROOT, ALIGN_BASIS)


def fields():
    source = 'k h234l[v case k h232v[]]'
    call = 'k h234m[v case k h232v[]]'
    return ('i[person a][k r2uw[v case ' + source + ' ' + call + ' k h232v[] v person]] '
            'i[person a][' + source + '] i[person a][v person] '
            'i[person a][k h234r[v case v person k h232v[]]] '
            'i[person a][k h234q[v case]] i[person a][v code] i[person a][' + TRUE + ']')


def choices():
    return 'i[person a point d][k h234n[v case v person k h232v[] k h232v[] v point]]'


def definitions():
    text = ''
    for name, case in zip(CONTENTS, CASES):
        text += 'd ' + name + '[person a activity a] e[b point[' + both(
            'e[v activity][k h234q[k ' + case + '[]]]',
            'k r2ux[k ' + case + '[] k h234l[k ' + case +
            '[] k h232v[]] v person k h232v[] v point]') + ']].\n'
    branches = [both('e[v case][k ' + case + '[]]', 'e[v code][r b[p ' + name + ']]')
                for name, case in zip(CONTENTS, CASES)]
    joined = branches[-1]
    for branch in reversed(branches[:-1]):
        joined = 'x[' + branch + '][' + joined + ']'
    text += 'd r2vz[case a code ' + CODE + '] c[' + joined + '].\n'
    text += 'd r2wa[case a code ' + CODE + '] c[' + both('k r2vz[v case v code]',
        'k r2uv[v case k h234l[v case k h232v[]] k h234m[v case k h232v[]] r[k h232v[]] k h232v[]]') + '].\n'
    text += 'd r2wb[case a code ' + CODE + ' flag c point d] c[k r2vl[' + fields() + ' p h234s v flag v point]].\n'
    text += 'd r2wc[case a code ' + CODE + '] c[k r2vm[' + fields() + ' ' + choices() + ']].\n'
    params = ('case a code ' + CODE + ' ' + MODEL + ' worlds ' + WORLD +
              ' public a evaluated ' + ASSESSMENT + ' atleast ' + ORDER)
    args = (fields() + ' p h234s v variables v equations v factor v worlds ' + choices() +
            ' v public k h232v[] v evaluated v atleast')
    for name, target in [('r2wd', 'r2vr'), ('r2wf', 'r2vs'), ('r2wg', 'r2vt'), ('r2wh', 'r2vu')]:
        text += 'd ' + name + '[' + params + '] c[' + both('k r2wa[v case v code]', 'k ' + target + '[' + args + ']') + '].\n'
    text += 'd r2we[scope h[a] c] c[' + both('k hh[k r2us[]]',
        'f case a[y[k r2ut[v case]][c[v scope][v case]]]') + '].\n'
    return text


def build():
    old, prior = parent(), aligned()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    imported = {}
    for d in prior.document['declarations']:
        n = d['name']
        if n in old.entries:
            assert old.entries[n]['declaration'] == d
            assert old.entries[n]['meaning_ja'] == prior.entries[n]['meaning_ja']
        else:
            doc['declarations'].append(deepcopy(d))
            imported[n] = prior.entries[n]['meaning_ja']
    assert not (set(MEANINGS) | set(PRIMITIVES)) & (set(old.entries) | set(imported))
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + data[0] + '.' for n, data in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='partial_concrete_demand_candidates_and_open_scope',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=data[1], meaning_ja=data[2]) for n, data in PRIMITIVES.items()},
                 definitions=imported | MEANINGS,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 imported_comparison_basis=ALIGN_BASIS,
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in (ALIGN_BASIS, ALIGN_LIBRARY)},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/everywhere-restriction-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda data: json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
