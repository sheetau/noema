"""Join fixed private policies to matched, bounded enlightenment losses."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import STATE, MODEL, ARGS, FALSE, both, side, every
from scripts.compose_aligned_influence import WORLD, RECORDS, FIELDS, RULE
from scripts.compose_paired_influence import MATCH
from scripts.compose_private_choice_frequency import BASIS as CHOICE_BASIS, MEASURE, MARGS

PARENT_BASIS = 'data/public-enlightenment-route-basis-v1.json'
LIBRARY = 'examples/v016/qualified-private-influence.noema'
BASIS = 'data/qualified-private-influence-basis-v1.json'
PROFILE = MODEL + ' worlds ' + WORLD + ' matches ' + MATCH + ' public a reference d tolerance b'
PARGS = ARGS + ' v worlds v matches v public v reference v tolerance'
BOUND = (MEASURE + ' frame a degrees h[d d] b degreecriterion h[b] c points h[d] j[d] '
         'timeweight h[d d] b frequencies h[d] b frequencycriterion h[b] c ' +
         MODEL + ' worlds ' + WORLD + ' matches ' + MATCH + ' public a tolerance b')
MEANINGS = {
    'r2yt': '同じ公衆・基準について両候補のr2wzを確認し、許容低下を非負とする。なし側の各時間条件付き過程の広がりに対して、あり側にその広がりとの差が許容値以内となる一過程がある。同じr2xcの尺度を使い、異なる過程の人数を合算しない。許容0ではr2xdと同じ比較となる。',
    'r2yu': '同じ要因の両側の全解がr2wiで対応組へ覆われ、全解に同じr2lnの尺度の定義域r2xfがあり、全対応組でr2ytの許容低下以内にある。対応しない解同士を比較せず、未対応や未評価を無害としない。許容差のある比較へ推移性は要求しない。',
    'r2yv': '同じ方針内容がhzeによって全介入解の要因の真偽へ対応し、なし側の全解で指定した解除内容も成立する。方針の不成立だけで完全な解除を代用しない。解除内容が同じ要求表を指すことは原文用のr2yyで固定する。',
    'r2yw': '指定状況で方針が成立し、その同じ方針と解除がr2yvで介入へ対応し、同じ啓蒙への低下がr2yuで全対応組について許容範囲内であるという内容。実際に啓蒙へ到達することや規範的な許可はこの内容だけから導かない。',
    'r2yx': '固定した非空の要求表について、同じ期間枠の整合した対象期間の全点でr2vlの全要求不適用が成立するという解除内容。一部の要求の解除、一時点の解除、強い程度や頻度の閾値を下回っただけの状態では代用しない。',
    'r2yy': '同じ本人・役割・要求表・私的活動基準・選択肢をr2ysの強い制限の頻度とr2yxの全解除へ同時に束縛する。各候補の期間点・程度評価・機会重み・頻度だけを同じ候補から取り出す。その方針と解除をr2ywへ渡し、方針の期間枠を同じ公衆・基準の啓蒙比較期間h222gへ一致させる。',
}
LIMITS = [
    '進行の読みは先行r2ln/r2xcの、同じ期間内の一つの集団的変化過程で自立的能力変化がどれだけ広がるかを継承する。単なる活動数や他の成果に置き換えず、異なる過程を合算しない。',
    '許容低下は同じ比率尺度で非負とし、境界と等しい低下を含める。具体的な許容値や小ささの基準は原文へ補わず、適切な基準の固定は原文へ接続する段階の課題である。0へ自動固定してsonderlichの留保を消さない。',
    '許容差付きの比較は一般には推移的でない。r2wjの前順序をこの関係へ要求せず、既存r2wiの全対応とr2xfの評価の有効性を使って、各対応組を直接調べる。',
    '対応は同じ外生条件・介入前の状態・非決定的な選択枝を保つものとして、結果の良否から選ばない。両側の全解が対応することは検査するが、現実のモデルや対応の正しさを形式検査だけで証明しない。',
    '方針が強い制限の頻度を満たさないことと、全要求の解除を区別する。r2yyは同じ要求表と期間を使い、解除側の一部の要求や一部の時点の残存を拒否する。',
    '進行を特に妨げないという留保を含む方針内容の準備であり、許可の成立や著者の帰属はまだ追加しない。原文側の参照供給、頻度・程度・低下の基準、談話と一文全体の通読は残る。',
    '本文・過去の判断・全記述域の有限評価拒否は変更しない。基本関係・著者主張・意味確認済み文字数は追加しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def choices():
    return load_catalog(ROOT, CHOICE_BASIS)


def definitions():
    off_ratio = 'k r2xc[v public v reference v off v offprocess v offstart v offend]'
    on_ratio = 'k r2xc[v public v reference v on v onprocess v onstart v onend]'
    bound = ('f offprocess a[f offstart d[f offend d[y['
             'k r2xa[v public v reference v off v offstart v offend]][g onprocess a[g onstart d[g onend d[' +
             both('k r2xa[v public v reference v on v onstart v onend]',
                  'u[k hc[k ha[' + on_ratio + ' v tolerance] ' + off_ratio + ']]') + ']]]]]]]')
    text = 'd r2yt[public a reference d on d off d tolerance b] c[' + both(
        'u[k hc[v tolerance n p a b]]', 'k r2wz[v public v reference v on]',
        'k r2wz[v public v reference v off]', bound) + '].\n'
    matched = side('rw', True, 'i[on ' + STATE + '][' +
                   side('rw', False, 'i[off ' + STATE + '][y[c[v matches][v on v off]]['
                        'k r2yt[v public v reference c[v worlds][v on] c[v worlds][v off] v tolerance]]]') + ']')
    text += 'd r2yu[' + PROFILE + '] c[' + both(
        'u[k hc[v tolerance n p a b]]', 'k r2wi[' + ARGS + ' v matches]',
        every('state', 'k r2xf[v public v reference r b[p r2ln] c[v worlds][v state]]'), matched) + '].\n'
    text += 'd r2yv[policy e released e ' + MODEL + ' worlds ' + WORLD + '] c[' + both(
        'k hze[v policy ' + ARGS + ' v worlds]',
        side('rw', False, 'i[state ' + STATE + '][t[v released][c[v worlds][v state]]]')) + '].\n'
    text += 'd r2yw[policy e released e ' + PROFILE + '] e[b point[' + both(
        't[v policy][v point]', 'k r2yv[v policy v released ' + ARGS + ' v worlds]',
        'k r2yu[' + PARGS + ']') + ']].\n'
    text += 'd r2yx[' + RECORDS + ' required ' + RULE + ' frame a] e[b branch[' + both(
        'k tb[i[point d][k h7q[v frame v branch v point]] i[point d][k h7r[v frame v branch v point]] '
        'i[first d last d][k ic[v first v last v branch]]]',
        'k tc[i[point d][k h7r[v frame v branch v point]] '
        'b point[k r2vl[' + FIELDS + ' v required ' + FALSE + ' v point]]]') + ']].\n'
    policy = ('b branch[k r2ys[' + MARGS + ' v frame i[point d][c[v degrees][v branch v point]] '
              'v degreecriterion c[v points][v branch] i[point d][c[v timeweight][v branch v point]] '
              'c[v frequencies][v branch] v frequencycriterion v branch]]')
    released = 'k r2yx[' + FIELDS + ' v required v frame]'
    text += 'd r2yy[' + BOUND + '] e[b evaluation[' + both(
        'e[v frame][k h222g[v public v reference]]',
        't[k r2yw[' + policy + ' ' + released + ' ' + PARGS + ']][v evaluation]') + ']].\n'
    return text


def build():
    old, prior = parent(), choices()
    doc = deepcopy(old.document)
    selected = closure(old.document, ['r2wz', 'r2xa', 'r2xc', 'r2wi', 'r2vc', 'r2xf', 'r2ln', 'hze', 'r2vl', 'tc'])
    wanted = {d['name'] for d in selected} | {d['name'] for d in prior.document['declarations']}
    doc.update(declarations=[deepcopy(d) for d in old.document['declarations'] if d['name'] in wanted], statements=[])
    doc['declarations'] += [deepcopy(d) for d in prior.document['declarations'] if d['name'] not in old.entries]
    imported = {d['name']: (old.entries.get(d['name']) or prior.entries[d['name']]) for d in doc['declarations']}
    assert not set(MEANINGS) & (set(old.entries) | set(prior.entries))
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = {}, {}
    for n, entry in imported.items():
        d = entry['declaration']
        if entry['kind'] == 'primitive':
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=entry['arguments'], meaning_ja=entry['meaning_ja'])
        else:
            meanings[n] = entry['meaning_ja']
    pins = set(old.source_sha256) | set(prior.source_sha256)
    pins |= set(json.loads((ROOT / CHOICE_BASIS).read_text(encoding='utf-8'))['import_source_sha256'])
    basis = dict(status='qualified_private_policy_and_matched_extent_bound', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(pins)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
