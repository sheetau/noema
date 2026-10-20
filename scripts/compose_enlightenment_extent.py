"""Compare the extent of the same collective change within a fixed period."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import MODEL, TRUE, both
from scripts.compose_aligned_influence import LINK, LARGS, WORLD, FAMILY, CODE
from scripts.compose_paired_influence import BASIS as PAIRED_BASIS, MATCH

PARENT_BASIS = 'data/demand-candidates-basis-v1.json'
LIBRARY = 'examples/v016/enlightenment-extent.noema'
BASIS = 'data/enlightenment-extent-basis-v1.json'
MEANINGS = {
    'r2wy': '同じ公衆と参照状況でr2laの公衆分類を確認し、h222iの全読者列・h222jの広がり基準をr2lbへ渡して、完全性・非空性・重複なし・人の分類・0と1の間の基準を確認する。この検査では変化述語を恒真にし、現実の全員の変化は主張しない。',
    'r2wz': 'r2wyと、同じh222gの期間・候補ごとのh222hの起点によるrqtbの有効な将来経過を求める。変化や目標達成そのものを要求せず、無効な母集団・期間を進行ゼロと同一視しない。',
    'r2xa': '同じ期間の候補経過内にある開始・終了点で、開始より終了が後にあり、終了が同じ起点より厳密に後にある。既存rqtdと同じ時間条件。過程の存在や変化した人はこの時間条件だけから導かない。',
    'r2xb': '同じ参照状況の公衆に属し、同じ過程・開始点・終了点・候補経過で既存hzmxを満たす内部の当事者と活動部分がある人。自立的な能力変化、作用と因果を単なる人数へ置き換えず、hzmyの変化対象をそのまま取り出す。',
    'r2xc': '同じ全読者列について、r2xbを満たす人の比率をpbで計算する。異なる過程の変化した人を合併せず、同じ人の複数の当事者や活動を重複加算しない。値だけでは母集団や期間の有効性を保証せず、利用側でr2wzを要求する。',
    'r2xd': '同じ公衆・参照状況で両候補がr2wzを満たし、右候補の各時間条件付き過程の変化比率以上になる過程が左候補にある。期間内に一つの過程として達する最大の広がりを比較する。数値の最大値を未定義関数として返さず、過程の証拠間の量化で構成する。ゼロ同士は同順位であり、達成閾値より下の違いも区別する。',
    'r2xe': '同じ有効な母集団と期間で、r2xaの時間条件を満たす一つの過程の変化比率が、既存h222jの閾値を厳密に超える。r2lnの集団変化を、尺度と同じ変化対象・比率から再構成した検査用条件。閾値と等しいだけの場合は達成としない。',
    'r2xf': '評価要求の目標記述が閉じたr2lnと一致し、同じ公衆・参照状況・候補にr2wzの尺度の定義域があることを確認する。目標への到達を評価済みの条件にしない。未知の変化入力を偽やゼロに補う規則ではない。',
    'r2xg': '同じr2lnの目標記述を確認してr2xdの比較へ渡す。公衆・期間・起点・広がり基準を比較の途中で交換しない。',
    'r2xh': '同じ全要求表・介入モデル・対応組・公衆・参照状況を、r2wqへ渡し、評価と比較にはr2xf/r2xgの啓蒙進行尺度を使用する。尺度を無関係な入力へ差し替えない。',
    'r2xi': '同じr2xhの入力と尺度で、r2wrによる対応組の悪化を分類する。',
    'r2xj': '同じ入力と尺度で、r2wsによる対応組の非悪化を分類する。',
    'r2xk': '同じ入力と尺度で、r2wtによる非悪化かつ改善を分類する。',
    'r2xl': '先行四事例と同じ宛先別要求表をr2wuへ渡し、r2xf/r2xgの尺度で同じ公衆・基準の比較を有効化する。',
    'r2xm': '同じ四事例の接続と尺度で、r2wvによる対応組の悪化を分類する。',
    'r2xn': '同じ四事例の接続と尺度で、r2wwによる対応組の非悪化を分類する。',
    'r2xo': '同じ四事例の接続と尺度で、r2wxによる非悪化かつ改善を分類する。',
}
LIMITS = [
    '先行r2lnの採用読解である、固定された有限の全読者における自立的能力変化の広がりを、その同じ期間の進行尺度へ拡張する。外部の成功者、経済成果、実際の議論回数を啓蒙へ置き換えない。',
    '尺度は同じ期間内に一つの集団変化過程として達する広がりである。期間内の達成速度、個人の自立の質的な深さ、異なる過程の結果の総和は別の尺度であり、この読解に黙って混ぜない。期間や閾値の具体的な日数・数値は原文へ追加しない。',
    '同じ母集団なので比率の比較は人数順序と一致するが、数える対象はhzmxの全条件を満たす変化である。単なる成功者名簿や指導への服従で変化したことにはしない。',
    '有効な期間には起点とそれより後の点がある。変化を起こさない過程候補では比率がゼロとなるので、変化のない二候補も比較できる。公衆分類や期間が不適合な場合は評価対象にせず、無害判定へ流さない。',
    'r2lnとの閾値対応は、同じr2wyとrqtbが成り立ち、既存の有理数計算が規約どおりである下で確認する。尺度の構成だけから現実のモデル・対応matchesの妥当性や原文全体の同義性を証明しない。',
    '基本関係・著者主張・意味確認済み文字数は追加しない。共通の公衆・背景を二問の提示文脈へ固定すること、四事例以外の要求表、問いの帰属・照応・aber/sondern・wohl/gar・後続回答への接続が残る。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def paired():
    return load_catalog(ROOT, PAIRED_BASIS)


def members():
    return 'i[person a][k h6t[v public v person v reference]]'


def timeline(branch):
    return ('i[point d][k h7q[k h222g[v public v reference] v ' + branch + ' v point]] '
            'i[before d after d][k ic[v before v after v ' + branch + ']] '
            'k h222h[v public v reference v ' + branch + ']')


def placement(branch, before, after):
    return 'k r2xa[v public v reference v ' + branch + ' v ' + before + ' v ' + after + ']'


def ratio(branch, process, before, after):
    return ('k r2xc[v public v reference v ' + branch + ' v ' + process +
            ' v ' + before + ' v ' + after + ']')


def definitions():
    text = 'd r2wy[public a reference d] c[' + both('k r2la[v public v reference]',
        'k r2lb[k h222i[v public v reference] k h222j[v public v reference] ' +
        members() + ' i[person a][' + TRUE + '] p aa]') + '].\n'
    text += 'd r2wz[public a reference d branch d] c[' + both(
        'k r2wy[v public v reference]', 'k rqtb[' + timeline('branch') + ']') + '].\n'
    text += 'd r2xa[public a reference d branch d before d after d] c[' + both(
        'k h7q[k h222g[v public v reference] v branch v before]',
        'k h7q[k h222g[v public v reference] v branch v after]',
        'k ic[v before v after v branch]',
        'k ic[k h222h[v public v reference v branch] v after v branch]') + '].\n'
    params = 'public a reference d branch d process a before d after d'
    text += 'd r2xb[' + params + ' person a] c[' + both('k h6t[v public v person v reference]',
        'g actor a[g part a[k hzmx[v public v actor v person v process v part v before v after v branch '
        'i[group a member a point d][k h6t[v group v member v reference]]]]]') + '].\n'
    text += 'd r2xc[' + params + '] b[k pb[k h222i[v public v reference] '
    text += 'i[person a][k r2xb[v public v reference v branch v process v before v after v person]]]].\n'
    right = ratio('right', 'rprocess', 'rstart', 'rend')
    left = ratio('left', 'lprocess', 'lstart', 'lend')
    dominates = ('f rprocess a[f rstart d[f rend d[y[' + placement('right', 'rstart', 'rend') +
                 '][g lprocess a[g lstart d[g lend d[' + both(
                     placement('left', 'lstart', 'lend'), 'u[k hc[' + left + ' ' + right + ']]') + ']]]]]]]')
    text += 'd r2xd[public a reference d left d right d] c[' + both(
        'k r2wz[v public v reference v left]', 'k r2wz[v public v reference v right]', dominates) + '].\n'
    threshold = 'g process a[g before d[g after d[' + both(
        placement('branch', 'before', 'after'),
        'k hc[k h222j[v public v reference] ' + ratio('branch', 'process', 'before', 'after') + ']') + ']]]'
    text += 'd r2xe[public a reference d branch d] c[' + both(
        'k r2wz[v public v reference v branch]', threshold) + '].\n'
    identity = 'e[v goal][r b[p r2ln]]'
    text += 'd r2xf[public a reference d goal ' + FAMILY + ' branch d] c[' + both(
        identity, 'k r2wz[v public v reference v branch]') + '].\n'
    text += 'd r2xg[public a reference d goal ' + FAMILY + ' left d right d] c[' + both(
        identity, 'k r2xd[v public v reference v left v right]') + '].\n'
    params = LINK + ' choices h[a d] c matches ' + MATCH + ' public a reference d'
    args = LARGS + ' v choices v matches v public v reference p r2xf p r2xg'
    for name, target in zip(('r2xh', 'r2xi', 'r2xj', 'r2xk'), ('r2wq', 'r2wr', 'r2ws', 'r2wt')):
        text += 'd ' + name + '[' + params + '] c[k ' + target + '[' + args + ']].\n'
    params = 'case a code ' + CODE + ' ' + MODEL + ' worlds ' + WORLD + ' matches ' + MATCH + ' public a'
    args = 'v case v code v variables v equations v factor v worlds v matches v public p r2xf p r2xg'
    for name, target in zip(('r2xl', 'r2xm', 'r2xn', 'r2xo'), ('r2wu', 'r2wv', 'r2ww', 'r2wx')):
        text += 'd ' + name + '[' + params + '] c[k ' + target + '[' + args + ']].\n'
    return text


def build():
    old, prior = parent(), paired()
    doc = deepcopy(prior.document)
    names = {d['name'] for d in doc['declarations']}
    extra = closure(old.document, ['r2la', 'r2lb', 'rqtb', 'hzmx', 'pb', 'r2ln'])
    # Prepend only missing earlier dependencies, in original declaration order.
    missing = [deepcopy(d) for d in extra if d['name'] not in names]
    imported = {d['name']: old.entries[d['name']] for d in missing}
    for d in doc['declarations']:
        n = d['name']
        imported[n] = prior.entries[n]
        if n in old.entries:
            assert old.entries[n]['declaration'] == d
            assert old.entries[n]['meaning_ja'] == prior.entries[n]['meaning_ja']
    # Original dependencies may already be in prior; merge by the old document
    # order, then retain the newly allocated paired definitions after them.
    retained = names | set(imported)
    doc['declarations'] = [deepcopy(d) for d in old.document['declarations'] if d['name'] in retained]
    doc['declarations'] += [deepcopy(d) for d in prior.document['declarations'] if d['name'] not in old.entries]
    assert not set(MEANINGS) & set(imported)
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = {}, {}
    for d in doc['declarations']:
        n = d['name']
        if n not in imported:
            continue
        e = imported[n]
        if e['kind'] == 'primitive':
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=e['arguments'], meaning_ja=e['meaning_ja'])
        else:
            meanings[n] = e['meaning_ja']
    pins = set(old.source_sha256) | set(prior.source_sha256)
    basis = dict(status='partial_same_enlightenment_extent_scale', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(pins)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
