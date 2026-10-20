"""Only-slow attainment: possible achievement and no admissible faster route."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-prejudice-depictions.noema'
PARENT_BASIS = 'data/prejudice-depictions-basis-v1.json'
FULL = 'examples/v016/kant-public-slow-attainment.noema'
CORE = 'examples/v016/public-slow-attainment-core.noema'
BASIS = 'data/public-slow-attainment-basis-v1.json'
ANNOTATIONS = 'data/public-slow-attainment-identifiers-v1.json'
PRIMITIVES = {
    'h226e': ('[a d] j[a]', ['group', 'reference'],
              '同じ集団・基準文脈の状態取得について進行速度を比較する質的尺度を、遅い方から並べた有限列。最小値は進行なし、最大値は比較上の高速側の端である。正確な時間・数値確率・等間隔を含意しない。尺度の妥当性は合成定義で検査する。'),
    'h226f': ('[a d a] c', ['group', 'reference', 'rate'],
              '同じ集団・基準で、進行速度を遅いと扱う正の低速度帯。候補や到達結果に合わせて閾値を変更せず、速度以外の単なる難しさや長い待機を判定する帯ではない。非空性・両端の除外・低い方への閉性は別に検査する。'),
    'h226g': ('[a a i[h[a] e] j[a] d d d d] a',
              ['group', 'process', 'property', 'population', 'first', 'last', 'reference', 'candidate'],
              '同じ候補経過の同じ過程・前後点において、固定した全構成員列の指定状態への取得進行を、その過程の同じ経過時間に対して比較した平均の進行速度の質的評価値。基準文脈と対象状態を固定する。対象量を無視した長さ、開始前の無関係な待ち時間、別過程や別状態の速度は流用しない。個々の瞬間の一様速度は含意しない。測定・判断としての対応を与える基本関係であり、順序や例の通過から値を算出したとはしない。過程の成立、到達、全成員列、尺度所属、低速度の判定は別に検査する。'),
    'h226h': ('[] a', [], '固定原文kant-1784:u0011第四文[846,906)、Daherからgelangenまでの文章箇所。'),
}
MEANINGS = {
    'r2po': '有限の重複なしの速度尺度を、相異なる両端を持つ厳密全順序として検査する。既存rqssの順序を逆にして、正の低速度帯が非空で両端を含まず、より低い正の速度へ閉じることを要求する。最低値の無進行は遅い到達に数えない。',
    'r2pp': '先頭文hzngの到達の存在証人を、同じ公衆・参照・候補・過程・前後点へ展開した関係。h222g/h222hの同じ期間と起点、同じh6tの全読者とr2lcの広がりを使い、hzmyの能力変化と因果を保つ。先頭文と別の到達目標や成功者列を選び直さない。',
    'r2pq': '同じ到達の公衆・過程・前後点・参照・候補、同じh4lの目標状態、同じh222iの全読者列から得た進行速度が、同じ尺度に属し、同じ低速度帯に入ることを要求する。未到達や別過程の遅さで成功させない。到達自体は呼出側のr2ppで保持する。',
    'r2pr': '先頭文と同じ候補範囲h222kの少なくとも一候補に、同じ公衆のr2ppを満たす過程・前後点がある。到達可能性の肯定であり、全候補の成功や現実の到達ではない。',
    'r2ps': '同じ速度尺度と低速度帯の妥当性、r2prの到達可能性を要求する。同じ非空の候補範囲の全候補の時間枠を検査し、全ての到達過程・前後点についてr2ppならr2pqとする。一つの遅い経路があっても別の速い到達経路があれば成立しない。到達しない候補の存在は許す。',
    'r2pt': '先頭三文と同じ非空の公衆範囲h222eの全対象に、同じ分類r2la・構成員照合r2nd・可能だが遅い到達r2psを要求する内容。自由の現実の成立や全員同時の変化を追加しない。',
    'r2pu': '第四文の箇所・著者wa・段落文脈hzp3に、閉じた段階3の内容r2ptを帰属する。可能な経過を現実として実行評価しない。',
    'r2pv': 'Daherの根拠として採用する第三文の作用の反転h224m、有害さの評価h225s、反作用の理由節h225oの三箇所。根拠を第四文自身や無関係な先行箇所へ置き換えない。',
    'r2pw': '第四文の内容帰属r2puと、第三文の三箇所からの帰結提示ud、根拠箇所との区別と本文順ueを統合する。論理的な十分性や哲学的主張の真理を保証しない。',
}
LIMITS = [
    '第四文のkannを文脈上の到達可能性、nur langsamを全ての可能な到達経路に対する低速度の制約と読む。到達できる場合にだけ遅いという空虚な含意でも、一つの遅い経路の存在だけでもない。',
    '公衆・候補・期間・起点・到達目標・全読者と広がり基準を先頭文から継承する。Aufklärungを同じ文脈の自立的理解力使用への能力変化として読み、単なる知識の増加や全国民の一斉到達へ置き換えない。',
    'langsamは同じ取得過程の全体についての低い進行速度と読む。原文に日数・数値尺度・毎瞬間の一様性を補わない。進行量を無視した経過の長さや無関係な待機を速度として使わない。質的な評価値と低速度帯の文脈的適切さは基本関係の解釈責任であり、有限検査で測定したものではない。',
    'Daherの根拠を第三文の三つの内容箇所とする。理由の帰属は論理的な必然や正しさの証明から分ける。',
    '先頭60文と既存13区間・先頭三文719非空白文字の判断を保存する。第四文全体は原文通読と句ごとの判断を別記する。第五文と段落全体はこの構成に含めない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2po[scale j[a] slow h[a] c fallback a] c[
 w[k rt[v scale]][
 w[k rqsq[i[value a][k hg[v scale v value]]
 i[first a second a][k r2dj[v scale v first v second]]
 k r2dp[v scale v fallback] k r2dq[v scale v fallback]]][
 k rqss[i[value a][k hg[v scale v value]]
 i[first a second a][k r2dj[v scale v second v first]] v slow
 k r2dq[v scale v fallback] k r2dp[v scale v fallback]]
 ]]
].
d r2pp[public a reference d candidate d process a first d last d] c[
 w[k hzne[k h222g[v public v reference] k h222h[v public v reference v candidate] v candidate]][
 w[k h7q[k h222g[v public v reference] v candidate v first]][
 w[k h7q[k h222g[v public v reference] v candidate v last]][
 w[k ic[v first v last v candidate]][
 w[k ic[k h222h[v public v reference v candidate] v last v candidate]][
 k hzmy[v public v process v first v last v candidate
 i[group a person a point d][k h6t[v group v person v reference]]
 i[members h[a] c changed h[a] c][k r2lc[v public v reference v members v changed]]]
 ]]]]]
].
d r2pq[public a reference d candidate d process a first d last d] c[
 c[i[value a][w[k hg[k h226e[v public v reference] v value]][k h226f[v public v reference v value]]]][
 k h226g[v public v process r[p h4l] k h222i[v public v reference]
 v first v last v reference v candidate]]
].
d r2pr[public a reference d] c[
 g candidate d[w[k h222k[v public v reference v candidate]][
 g process a[g first d[g last d[k r2pp[v public v reference v candidate v process v first v last]]]]
 ]]
].
d r2ps[public a reference d] c[
 w[k r2po[k h226e[v public v reference] i[value a][k h226f[v public v reference v value]] v public]][
 w[k r2pr[v public v reference]][
 f candidate d[y[k h222k[v public v reference v candidate]][
 w[k hzne[k h222g[v public v reference] k h222h[v public v reference v candidate] v candidate]][
 f process a[f first d[f last d[
 y[k r2pp[v public v reference v candidate v process v first v last]][
 k r2pq[v public v reference v candidate v process v first v last]]
 ]]]
 ]]]
 ]]
].
d r2pt[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][
 w[k r2la[v public v reference]][w[k r2nd[v public v reference]][k r2ps[v public v reference]]]
 ]]]
]].
d r2pu[] c[k hznreport[k h226h[] k wa[] r d[k r2pt[]] k h226h[] k hzp3[]]].
d r2pv[node a] c[k hg[l[a][k h224m[] k h225s[] k h225o[]] v node]].
d r2pw[] c[
 w[k r2pu[]][w[k ud[k wa[] p r2pv k h226h[] k hzp3[]]][
 f node a[y[k r2pv[v node]][
 w[u[e[v node][k h226h[]]]][k ue[v node k h226h[] k hzp3[]]]
 ]]
 ]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2pw', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2pw']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='public_only_slow_attainment_integrated', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prejudice-depictions-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
