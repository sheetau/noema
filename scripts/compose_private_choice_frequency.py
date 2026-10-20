"""Measure fixed private choices excluded by positive or negative demands."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_aligned_influence import RECORDS, FIELDS, RULE
from scripts.compose_qualitative_influence import both

PARENT_BASIS = 'data/public-enlightenment-route-basis-v1.json'
LIBRARY = 'examples/v016/private-choice-frequency.noema'
BASIS = 'data/private-choice-frequency-basis-v1.json'
IDENTITY = 'source a person a role a reference d'
MEASURE = (IDENTITY + ' ' + RECORDS + ' required ' + RULE +
           ' choices j[d] scope h[d] c choiceweight h[d] b')
MARGS = 'v source v person v role v reference ' + FIELDS + ' v required v choices v scope v choiceweight'
FREQUENCY = (MEASURE + ' frame a degrees h[d] b degreecriterion h[b] c '
             'points j[d] timeweight h[d] b frequency b frequencycriterion h[b] c anchor d')
MEANINGS = {
    'r2yo': '指定の本人・職務に向けた固定表の要求のうち、評価時点で適用中の要求が少なくとも一つあり、同じ本人・活動へ記述を適用した選択候補の真偽が要求極性と違う。肯定の行為要求も否定の禁止も同じ不適合として数える。実際の違反や合法性は主張しない。',
    'r2yp': '本人が人で、固定要求表が非空であり、全行が同じ出所・本人・職務の私的理性使用zzpに基準文脈で結ばれる。禁止や不実行の結果を見て活動を範囲外へ出さず、別人・別役割・別出所の要求を混ぜない。',
    'r2yq': 'r2ypの固定表について、選択範囲を過不足なく重複なしで並べた非空の候補列と正の重みをrd6で確認し、適用中の要求に適合しなくなる選択肢の正確な割合を求める。少なくとも一つの適合選択を残すことも要求する。要求の矛盾で何も選べない場合を単に最大の程度として認定しない。',
    'r2yr': '同じr2yqの正確な割合が正であり、指定された強い制限の程度基準を満たす。程度基準を原文にない普遍的な数値へ固定しない。',
    'r2ys': '同じ本人・職務・要求表・私的活動分類・選択肢と重みを全時点で固定し、整合した期間の全点を列挙する。各点のr2yqが評価済みで、r2yrの強い制限が成立する点の正確な重み付き頻度が正で、別に指定した頻度基準を満たす。要求の適用だけは各点で変わり得る。',
}
LIMITS = [
    'sehr engeの準備として、固定された本人の私的使用の選択肢が要求によってどれだけ排除されるかを測る。活動別の明示的禁止率h74とは別の尺度であり、肯定の要求が非実行の選択を除く場合も扱う。',
    '選択候補は同じ本人・職務・活動記述・関連背景を保持し、要求の遵守以外の理由で不可能な選択や別人の違反を混ぜない。要求に適合する結果だけへ範囲を絞らない。固定表は対象方針の全要求として供給する。',
    '選択肢を表す状況の有限列と正の有理数重みによる操作的な尺度を採る。選択の分割では重みを保存し、機会頻度の重みとは分ける。連続時間全体・無限の全選択肢の測度を有限の実行例で証明したとはしない。',
    '要求表自体は非空だが各時点で全要求が不適用なら程度0と評価できる。要求内容の真偽と規範の適用の真偽を区別する。何も適合する選択がない表・候補の組合せは不適合とし、その時点を頻度の失敗例へ黙って埋めない。',
    '段階1の要求内容を実評価するので、その全記述域を有限に実行できなければ拒否する。r2ud等の評価拒否を有限標本で迂回しない。これらの定義を外側の許可へ引用する際は段階2が必要であり、旧h7lの段階0方針記述へ暗黙変換しない。',
    'しばしばという頻度は、強い制限の方針内容に含める準備である。頻繁な制限を許可することから実際にその頻度で制限したとは導かない。原文への出所・本人・職務・全候補・期間・基準の固定、許可、啓蒙への留保との接続は次の作業である。',
    '著者主張・意味確認済み文字数・新しい基本関係は追加しない。旧尺度と過去の記録は保持する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    vals = ' '.join('c[v ' + n + '][v record]' for n in
                    ('sources', 'people', 'roles', 'activities', 'codes', 'polarities'))
    mismatch = ('u[z[t[c[s[c[v codes][v record]]][v person c[v activities][v record]]][v choice]]'
                '[c[v polarities][v record]]]')
    text = 'd r2yo[person a role a ' + RECORDS + ' required ' + RULE + ' point d choice d] c[g record a[' + both(
        'c[v records][v record]', 'e[c[v people][v record]][v person]',
        'e[c[v roles][v record]][v role]', 'c[v required][' + vals + ' v point]', mismatch) + ']].\n'
    text += 'd r2yp[' + IDENTITY + ' ' + RECORDS + '] c[' + both(
        'k aa[v person]', 'g record a[c[v records][v record]]',
        'f record a[y[c[v records][v record]][' + both(
            'e[c[v sources][v record]][v source]', 'e[c[v people][v record]][v person]',
            'e[c[v roles][v record]][v role]',
            'k zzp[v person c[v activities][v record] v role v reference]') + ']]') + '].\n'
    excluded = 'k r2yo[v person v role ' + FIELDS + ' v required v point v choice]'
    text += 'd r2yq[' + MEASURE + ' ratio b point d] c[' + both(
        'k r2yp[v source v person v role v reference ' + FIELDS + ']',
        'k rd6[v choices v scope i[choice d][e[v choice][v choice]] i[choice d][' +
        excluded + '] v choiceweight v ratio]',
        'g choice d[' + both('c[v scope][v choice]', 'u[' + excluded + ']') + ']') + '].\n'
    text += 'd r2yr[' + MEASURE + ' ratio b criterion h[b] c point d] c[' + both(
        'k r2yq[' + MARGS + ' v ratio v point]', 'k hc[n p a b v ratio]',
        'c[v criterion][v ratio]') + '].\n'
    text += 'd r2ys[' + FREQUENCY + '] c[' + both(
        'k tb[i[point d][k h7q[v frame v anchor v point]] '
        'i[point d][k h7r[v frame v anchor v point]] i[first d last d][k ic[v first v last v anchor]]]',
        'k rd7[v points i[point d][k h7r[v frame v anchor v point]] '
        'i[point d][k r2yq[' + MARGS + ' c[v degrees][v point] v point]] '
        'i[point d][k r2yr[' + MARGS + ' c[v degrees][v point] v degreecriterion v point]] '
        'v timeweight v frequency v frequencycriterion]',
        'k hc[n p a b v frequency]') + '].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['aa', 'zzp', 'rd6', 'rd7', 'tb', 'h7q', 'h7r', 'ic']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives, meanings = {}, {}
    for n, entry in imported.items():
        d = entry['declaration']
        if entry['kind'] == 'primitive':
            primitives[n] = dict(parameters=d['parameters'], result=d['result'],
                                 arguments=entry['arguments'], meaning_ja=entry['meaning_ja'])
        else:
            meanings[n] = entry['meaning_ja']
    basis = dict(status='private_choice_degree_and_frequency_dependency', document=LIBRARY,
                 primitives=primitives, definitions=meanings | MEANINGS,
                 imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
