"""Compare matched intervention outcomes without crossing unrelated branches."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import STATE, MODEL, ARGS, both, side, every, compare
from scripts.compose_aligned_influence import (
    LINK, LARGS, TARGET, TARGS, WORLD, ASSESSMENT, ORDER, CODE)
from scripts.compose_demand_candidates import fields, choices

PARENT_BASIS = 'data/demand-candidates-basis-v1.json'
LIBRARY = 'examples/v016/paired-restriction-influence.noema'
BASIS = 'data/paired-restriction-influence-basis-v1.json'
MATCH = 'h[' + STATE + ' ' + STATE + '] c'
PAIRED = MODEL + ' matches ' + MATCH
PROFILE = PAIRED + ' assessed h[' + STATE + '] c atleast ' + MATCH
PARGS = ARGS + ' v matches v assessed v atleast'
MEANINGS = {
    'r2wi': '同じ要因の有無の両側に解があり、各あり側解に少なくとも一つの対応するなし側解が、各なし側解にも少なくとも一つの対応するあり側解がある。matchesはあり側・なし側の順で使う。一部の結果だけを比較から落とす対応を拒否する。解でない割当て同士へのmatchesの値は使わない。',
    'r2wj': '対応r2wiが両側を覆い、全解が評価済みで、同じ比較は全解上で反射的・推移的であり、対応する有無の組ごとに比較可能である。対応しない異なる背景の解まで比較可能とする条件は加えない。',
    'r2wk': '同じモデルのあり側解となし側解のうち、matchesで対応する組に厳密な悪化がある。別の背景や選択枝の高低を総当たりで借りない。対応の完備性・評価の有効性はr2wjで別に確認する。',
    'r2wl': '同じ対応する有無の組に厳密な改善がある。背景の一致を結果の良否から事後選別せず、同じmatchesを悪化と改善の双方に使う。',
    'r2wm': '対応と評価がr2wjで整い、対応組の悪化r2wkがある。対応する背景の少なくとも一つで進行を妨げうるというモデル内の潜在性であり、全背景での悪化や通常の頻度は意味しない。',
    'r2wn': '同じr2wjの下で、対応する組に悪化がない。未対応の解・評価不足を無害とせず、同順位だけの組も許す。',
    'r2wo': '同じ有効な対応で悪化がなく、少なくとも一つの対応組に改善がある。改善だけを拾って別の対応組の悪化を隠さない。',
    'r2wp': '同じ公衆・基準・閉じた啓蒙内容族r2ln・割当てから状況への対応を保ち、r2wjによる評価へ結ぶ。対応する世界どうしでだけ比較可能性を要求し、目標を別の公衆や経済成果へ置き換えない。',
    'r2wq': '同じ要求表についてr2vmの自由選択の排除とr2vpの全要求の適用／解除を保ち、同じ啓蒙への対応比較r2wpへ接続する。対応は要求の存在と履行を同一化しない。',
    'r2wr': '同じ要求・目標・対応のr2wqを満たし、対応組で悪化する可能性を求める。',
    'r2ws': '同じr2wqを満たし、対応組での悪化がないことを求める。対応不足を非阻害に含めない。',
    'r2wt': '同じr2wsの非悪化に加え、同じ対応組の少なくとも一つに改善を求める。',
    'r2wu': '先行四事例のr2waと同じ宛先別要求表を、r2wqの対応比較の有効性へ渡す。自由選択h234n・公衆・基準・要求内容を一貫して保持する。',
    'r2wv': '同じ先行事例・要求表・対応をr2wrへ渡し、対応組の悪化を分類する。別の候補の背景や内容を借りない。',
    'r2ww': '同じ先行事例・要求表・対応をr2wsへ渡し、対応組での非悪化を分類する。',
    'r2wx': '同じ先行事例・要求表・対応をr2wtへ渡し、非悪化と改善を分類する。統治者の議論の許可と全服従内容は既存r2waと要求内容に保持する。',
}
LIMITS = [
    '旧r2vd〜r2viの全解交差比較は別の頑健な比較として保存する。新しい定義では、制限と無関係な背景・非決定的な選択枝の差を、その制限の効果へ数えないため、比較する組を明示する。',
    'matchesは同じ外生条件、同じ介入前の状態、対応させる非決定的な選択の下で、要因だけを変更した結果の対応として入力する。結果の高低を見て都合のよい組を選ぶ関係ではない。構造式だけから対応を推測せず、対応の現実への適合もこの検査から証明しない。',
    '両側の全解を少なくとも一つの組で覆うことは構成で検査する。一対一対応は一般には要求せず、一対多も許す。複数の可能な対応が意味上適切なら全てを与え、悪化する対応を省かないことはmatchesの意味規約である。',
    '阻害は評価済みの対応組で悪化が起こりうること、非阻害は同じ全対応組に悪化がないこと、促進は非阻害に加え改善する組があることという潜在性の読みを採る準備。平均効果、典型的頻度、全背景での厳密改善を原文へ補わない。',
    '啓蒙への尺度・期間・公衆・対応背景を原文の共通文脈へ固定する作業と、四事例以外の全要求表は残る。問いの帰属、照応、aber/sondern、wohl/garと後続回答は未統合。新しい著者主張・原始関係・意味確認文字数は追加しない。',
    '全記述域を量化するr2udの有限評価拒否は保持する。具体的な四事例の検査は先行内容の検査と新しい比較への引数接続を分け、その境界を報告する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def pair():
    return 'c[v matches][v on v off]'


def paired_some(body):
    return side('rv', True, 'i[on ' + STATE + '][' +
                side('rv', False, 'i[off ' + STATE + '][' + both(pair(), body) + ']') + ']')


def goal_callbacks():
    assessed = ('i[state ' + STATE +
                '][c[v evaluated][v public v reference r b[p r2ln] c[v worlds][v state]]]')
    order = ('i[first ' + STATE + ' second ' + STATE +
             '][c[v atleast][v public v reference r b[p r2ln] c[v worlds][v first] c[v worlds][v second]]]')
    return assessed, order


def definitions():
    on_covered = side('rw', True, 'i[on ' + STATE + '][' +
                      side('rv', False, 'i[off ' + STATE + '][' + pair() + ']') + ']')
    off_covered = side('rw', False, 'i[off ' + STATE + '][' +
                       side('rv', True, 'i[on ' + STATE + '][' + pair() + ']') + ']')
    text = 'd r2wi[' + PAIRED + '] c[' + both('k ree[' + ARGS + ']', on_covered, off_covered) + '].\n'
    transitive = every('first', every('middle', every('last',
        'y[' + both(compare('first', 'middle'), compare('middle', 'last')) +
        '][' + compare('first', 'last') + ']')))
    comparable = side('rw', True, 'i[on ' + STATE + '][' +
        side('rw', False, 'i[off ' + STATE + '][y[' + pair() + '][x[' +
             compare('on', 'off') + '][' + compare('off', 'on') + ']]]') + ']')
    text += 'd r2wj[' + PROFILE + '] c[' + both('k r2wi[' + ARGS + ' v matches]',
        every('state', both('c[v assessed][v state]', compare('state', 'state'))),
        transitive, comparable) + '].\n'
    for name, low, high in [('r2wk', 'on', 'off'), ('r2wl', 'off', 'on')]:
        text += 'd ' + name + '[' + PAIRED + ' atleast ' + MATCH + '] c[' + both(
            'k rz[v variables v factor]',
            paired_some(both(compare(high, low), 'u[' + compare(low, high) + ']'))) + '].\n'
    raw = ARGS + ' v matches v atleast'
    text += 'd r2wm[' + PROFILE + '] c[' + both('k r2wj[' + PARGS + ']', 'k r2wk[' + raw + ']') + '].\n'
    text += 'd r2wn[' + PROFILE + '] c[' + both('k r2wj[' + PARGS + ']', 'u[k r2wk[' + raw + ']]') + '].\n'
    text += 'd r2wo[' + PROFILE + '] c[' + both('k r2wn[' + PARGS + ']', 'k r2wl[' + raw + ']') + '].\n'
    assessed, order = goal_callbacks()
    text += 'd r2wp[' + MODEL + ' worlds ' + WORLD + ' matches ' + MATCH + ' ' + TARGET + '] c[' + (
        'k r2wj[' + ARGS + ' v matches ' + assessed + ' ' + order + ']') + '].\n'
    whole = LINK + ' choices h[a d] c matches ' + MATCH + ' ' + TARGET
    wholeargs = LARGS + ' v choices v matches ' + TARGS
    text += 'd r2wq[' + whole + '] c[' + both(
        'k r2vm[v records v sources v people v roles v activities v codes v polarities v choices]',
        'k r2vp[' + LARGS + ']',
        'k r2wp[' + ARGS + ' v worlds v matches ' + TARGS + ']') + '].\n'
    raw = ARGS + ' v matches ' + order
    text += 'd r2wr[' + whole + '] c[' + both('k r2wq[' + wholeargs + ']', 'k r2wk[' + raw + ']') + '].\n'
    text += 'd r2ws[' + whole + '] c[' + both('k r2wq[' + wholeargs + ']', 'u[k r2wk[' + raw + ']]') + '].\n'
    text += 'd r2wt[' + whole + '] c[' + both('k r2ws[' + wholeargs + ']', 'k r2wl[' + raw + ']') + '].\n'
    params = ('case a code ' + CODE + ' ' + MODEL + ' worlds ' + WORLD + ' matches ' + MATCH +
              ' public a evaluated ' + ASSESSMENT + ' atleast ' + ORDER)
    args = (fields() + ' p h234s v variables v equations v factor v worlds ' + choices() +
            ' v matches v public k h232v[] v evaluated v atleast')
    for name, target in [('r2wu', 'r2wq'), ('r2wv', 'r2wr'), ('r2ww', 'r2ws'), ('r2wx', 'r2wt')]:
        text += 'd ' + name + '[' + params + '] c[' + both(
            'k r2wa[v case v code]', 'k ' + target + '[' + args + ']') + '].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    roots = ['ree', 'r2vc', 'r2wa', 'r2vm', 'r2vp', 'r2ln', 'r2uw', 'h234r', 'h234q', 'h234s', 'h234n']
    doc.update(declarations=closure(doc, roots), statements=[])
    imports = [d['name'] for d in doc['declarations']]
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = {}, {}
    for n in imports:
        e = old.entries[n]
        if e['kind'] == 'primitive':
            d = e['declaration']
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=e['arguments'], meaning_ja=e['meaning_ja'])
        else:
            meanings[n] = e['meaning_ja']
    pins = set(old.source_sha256) | {PARENT_BASIS, old.document_path}
    basis = dict(status='partial_matched_intervention_comparison', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_meaning_basis=PARENT_BASIS, imported_symbols=imports,
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(pins)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
