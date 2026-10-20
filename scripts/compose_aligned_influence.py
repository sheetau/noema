"""Bind intervention variables to complete demands and the same enlightenment goal."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import (
    BASIS as PROFILE_BASIS, LIBRARY as PROFILE_LIBRARY, MEANINGS as PROFILE_MEANINGS,
    STATE, MODEL, ARGS, TRUE, FALSE, both, side)

PARENT_BASIS = 'data/everywhere-restriction-basis-v1.json'
LIBRARY = 'examples/v016/aligned-restriction-influence.noema'
BASIS = 'data/aligned-restriction-influence-basis-v1.json'
CODE = 'i b[h[a a] e]'
RULE = 'h[a a a a ' + CODE + ' c d] c'
RECORDS = ('records h[a] c sources h[a] a people h[a] a roles h[a] a activities h[a] a '
           'codes h[a] ' + CODE + ' polarities h[a] c')
FIELDS = 'v records v sources v people v roles v activities v codes v polarities'
FAMILY = 'i b[h[a d] e]'
ASSESSMENT = 'h[a d ' + FAMILY + ' d] c'
ORDER = 'h[a d ' + FAMILY + ' d d] c'
WORLD = 'h[' + STATE + '] d'
LINK = RECORDS + ' required ' + RULE + ' ' + MODEL + ' worlds ' + WORLD
LARGS = FIELDS + ' v required ' + ARGS + ' v worlds'
TARGET = 'public a reference d evaluated ' + ASSESSMENT + ' atleast ' + ORDER
TARGS = 'v public v reference v evaluated v atleast'
MEANINGS = {
    'r2vl': '非空の固定された要求記録の全てについて、同じ出所・本人・役割・活動・段階1の内容記述・極性への要求の有無が、指定した有効フラグと一致する。偽の場合は全要求の不存在を求め、一部の不存在で代用しない。対象内容の実行や要求の法的正当性は判定しない。',
    'r2vm': '固定された要求記録の少なくとも一つについて、その同じ本人と活動に内容記述を適用した真偽が、その要求の極性と一致しない自由選択候補がある。要求の有無・実行済みの違反とは別に、その内容が少なくとも一つの選択を適合するものとして残さないことを述べる。',
    'r2vn': '同じ全要求記録が有効となっているという内容。命令に従った状態の内容ではない。出所・宛先・役割・活動・記述・極性を介入側ごとに選び直さない。',
    'r2vo': '同じ非空の全要求記録が無効となっているという内容。他の要求一般の不存在や、対象者のあらゆる自由を意味しない。r2vnが偽であるだけの部分的解除とは区別する。',
    'r2vp': '同じモデルの両介入の全解で、要求群r2vnの成立と要因の真偽がhzeで一致し、さらに要因なし側の全解で全要求の不存在r2voが成立する。部分的解除、反転した要因、別の要求群の切替えを排除する。制限の法的許可・実際の履行・現状での適用は追加しない。',
    'r2vq': '同じ公衆・基準・閉じた啓蒙内容族r2lnを、結果評価と質的比較の両方へ明示してr2vdに渡す。両側で同じ割当てから状況への対応を使う。能力人数・経済的成果・他の公衆の改善へ目標を取り替えず、啓蒙の現実の成立を質問の準備から導かない。',
    'r2vr': '要求内容に実際に排除される自由選択肢r2vmがあり、同じ要求群と介入要因の対応r2vpが成立し、同じ啓蒙目標への比較r2vqが有効である。要求の存在と履行の真偽を取り違えたモデルを、制限の影響として扱わない。',
    'r2vs': '同じ制限と啓蒙へ接続したr2vrの下で、要因あり側がなし側より厳密に低い結果の組がある。現実の因果の実証や一般的な傾向の判断は含めない。',
    'r2vt': '同じr2vrの下で、厳密に低い結果の組がない。モデル無効・制限内容なし・評価不足から非悪化を導かない。同程度だけの影響も含む。',
    'r2vu': '同じr2vtの非悪化に加え、同じ啓蒙への厳密な改善の組がある。別の出所・対象者・目標・基準・状況対応から改善を借りない。',
}
LIMITS = [
    '原文二問へ向けた接続構成であり、本文の新しい著者主張、原始関係、意味確認済み文字数は追加しない。先行比較ライブラリと採用本文の必要な定義を変更せず取り込む。',
    '要求記録の範囲は、効果を見て事後選別しない同じ政策・指示群の全範囲として供給する。他の独立した要求はこの範囲外に残せるが、要因の切替え以外の背景はモデルの両側で固定する。記録の完備性と現実のモデル適合は、この一般形だけから証明しない。',
    '自由選択候補は要求の適否を選別条件にせず、同じ本人・活動の選択を変える候補である。出所・宛先・要求内容・他者と関連背景を保持する。単に不可能な状況、他人の違反、要求の内容そのものの変更で選択制約を作らない。',
    '内容の真偽を評価するr2vmと、要求の存在を調べるr2vlを分ける。内容記述の有限評価ができない場合はそれを拒否し、有限標本への置換で網羅したことにはしない。',
    '内容記述は段階1とする。既存のr2udのように内部で記述を評価する履行条件を、段階0へ無理に引用しない。required引数も同じ段階1の記述を受ける型であり、段階0のh7aへの暗黙の型変換や規範の同一化は行わない。',
    'r2vqは目標族r2lnへの参照を固定するが、質的比較の尺度や公衆・基準・期間の意味を自動的に定めるものではない。比較入力は同じr2lnの進行を評価することが必要で、数値や成果人数を無断で補わない。',
    '全解の交差比較という先行版の頑健なモデル内の読みを保持する。現実の一般的な阻害・促進と同一とするには、同じ背景、適切な解の対応、通常性または潜在性の採用読解の確認が残る。',
    '次に、原文の制限候補へ全要求記録を結び、四事例以外を排除しない候補範囲を作る。二問の照応、問いの帰属、aber/sondern、wohl/gar、回答への接続はまだ未統合である。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def profile():
    return load_catalog(ROOT, PROFILE_BASIS)


def definitions():
    values = ' '.join('c[v ' + n + '][v record]' for n in
                      ('sources', 'people', 'roles', 'activities', 'codes', 'polarities'))
    present = 'c[v required][' + values + ' v point]'
    text = 'd r2vl[' + RECORDS + ' required ' + RULE + ' flag c point d] c[' + both(
        'g record a[c[v records][v record]]',
        'f record a[y[c[v records][v record]][z[' + present + '][v flag]]]') + '].\n'
    fulfills = 't[c[s[c[v codes][v record]]][c[v people][v record] c[v activities][v record]]][v candidate]'
    text += ('d r2vm[' + RECORDS + ' choices h[a d] c] c[g record a[' +
             both('c[v records][v record]', 'g candidate d[' + both(
                 'c[v choices][v record v candidate]',
                 'u[z[' + fulfills + '][c[v polarities][v record]]]') + ']') + ']].\n')
    for name, flag in [('r2vn', TRUE), ('r2vo', FALSE)]:
        text += 'd ' + name + '[' + RECORDS + ' required ' + RULE + '] e[b point[k r2vl[' + FIELDS + ' v required ' + flag + ' v point]]].\n'
    inactive = side('rw', False, 'i[state ' + STATE + '][t[k r2vo[' + FIELDS +
                    ' v required]][c[v worlds][v state]]]')
    text += 'd r2vp[' + LINK + '] c[' + both(
        'k hze[k r2vn[' + FIELDS + ' v required] ' + ARGS + ' v worlds]', inactive) + '].\n'
    assessment = 'i[state ' + STATE + '][c[v evaluated][v public v reference r b[p r2ln] c[v worlds][v state]]]'
    order = ('i[first ' + STATE + ' second ' + STATE +
             '][c[v atleast][v public v reference r b[p r2ln] c[v worlds][v first] c[v worlds][v second]]]')
    text += 'd r2vq[' + MODEL + ' worlds ' + WORLD + ' ' + TARGET + '] c[k r2vd[' + ARGS + ' ' + assessment + ' ' + order + ']].\n'
    whole = LINK + ' choices h[a d] c ' + TARGET
    wholeargs = LARGS + ' v choices ' + TARGS
    text += 'd r2vr[' + whole + '] c[' + both('k r2vm[' + FIELDS + ' v choices]',
        'k r2vp[' + LARGS + ']', 'k r2vq[' + ARGS + ' v worlds ' + TARGS + ']') + '].\n'
    # Keep source, target and world mapping identical in all three classifications.
    text += 'd r2vs[' + whole + '] c[' + both('k r2vr[' + wholeargs + ']', 'k r2ve[' + ARGS + ' ' + order + ']') + '].\n'
    text += 'd r2vt[' + whole + '] c[' + both('k r2vr[' + wholeargs + ']', 'u[k r2ve[' + ARGS + ' ' + order + ']]') + '].\n'
    text += 'd r2vu[' + whole + '] c[' + both('k r2vt[' + wholeargs + ']', 'k r2vf[' + ARGS + ' ' + order + ']') + '].\n'
    return text


def build():
    old, earlier = parent(), profile()
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['hze', 'r2ln']), statements=[])
    selected = {d['name'] for d in doc['declarations']}
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    for d in earlier.document['declarations']:
        n = d['name']
        if n in selected:
            assert imported[n]['declaration'] == d
            assert imported[n]['meaning_ja'] == earlier.entries[n]['meaning_ja']
        else:
            doc['declarations'].append(deepcopy(d))
            imported[n] = earlier.entries[n]
            selected.add(n)
    assert not set(MEANINGS) & selected
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = {}, {}
    for n, entry in imported.items():
        if entry['kind'] == 'primitive':
            d = entry['declaration']
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=entry['arguments'], meaning_ja=entry['meaning_ja'])
        else:
            meanings[n] = entry['meaning_ja']
    sources = {PARENT_BASIS, old.document_path, PROFILE_BASIS, PROFILE_LIBRARY}
    sources.update(e['meaning_basis'] for e in imported.values())
    basis = dict(status='partial_demand_intervention_and_same_enlightenment_alignment',
                 document=LIBRARY, primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(sources)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
