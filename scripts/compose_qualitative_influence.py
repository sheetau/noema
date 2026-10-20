"""Compose assessed qualitative intervention profiles and open answer sets."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT_BASIS = 'data/everywhere-restriction-basis-v1.json'
LIBRARY = 'examples/v016/qualitative-influence.noema'
BASIS = 'data/qualitative-influence-basis-v1.json'
STATE = 'h[a] c'
MODEL = 'variables j[a] equations h[a h[a] c] c factor a'
ORDER = 'atleast h[h[a] c h[a] c] c'
PROFILE = MODEL + ' assessed h[h[a] c] c ' + ORDER
ARGS = 'v variables v equations v factor'
PARGS = ARGS + ' v assessed v atleast'
TRUE = 'e[n p a b][n p a b]'
FALSE = 'u[' + TRUE + ']'
MEANINGS = {
    'r2vb': '同じ変数列・方程式・要因について、指定割当てが要因だけを真または偽へ固定した介入方程式のいずれかの解である。要因以外の方程式と背景を変えず、列外変数の真や重複変数は既存ruで拒否する。',
    'r2vc': '同じモデルの真・偽の介入解の和集合の全てについて条件を調べる。既存rsで有限変数の全割当てを列挙し、解でない割当てを量化の対象から除く。解の存在はこの全称だけでは要求しない。',
    'r2vd': '同じ要因の有無の双方に解があり、全介入解の結果が同じ尺度で評価され、結果の少なくとも同程度という比較が反射的・推移的で、両側の各解の組が比較可能である。相互比較なら同程度を許し、同じ程度の異なる割当てを同一視しない。解なし・評価なし・比較不能を非悪化へ補わない。',
    'r2ve': '同じモデルで、要因ありの解が要因なしの解より厳密に低い組がある。低いことを、後者が前者以上で逆は成立しないこととして構成する。実際の観測・全組の悪化・結果の全面的な不成立は要求しない。評価の妥当性はr2vdが別に検査する。',
    'r2vf': '同じモデルで、要因ありの解が要因なしの解より厳密に高い組がある。結果を二値の達成・未達成や人数尺度へ限定せず、反対向きの悪化の有無もこの条件だけでは決めない。',
    'r2vg': '評価と比較がr2vdで整い、同じモデルに厳密な悪化の組r2veがある。改善する組の併存を許す、評価済みの潜在的な不利益の分類。原文hinderlichの語義全体とはまだ同一視しない。',
    'r2vh': '評価と比較がr2vdで整い、同じモデルのどの有無の組にも厳密な悪化がない。同程度だけの場合を含み、改善があることは要求しない。無効なモデルで悪化を見つけられないことからは成立しない。',
    'r2vi': '同じr2vdの下で悪化する組がなく、改善する組が少なくとも一つある。全ての組で厳密な改善を要求する旧試作より弱く、同程度の組を許す。一部で改善しても別の組で悪化する場合は通らない。',
    'r2vj': '範囲・評価済み条件・悪化条件を同じ候補へ適用し、それらを満たす個体を答え候補とする開いた質問を構成する。答え候補の存在・唯一性や現実の発話を主張しない。',
    'r2vk': '同じ候補範囲と評価条件で、悪化がなく改善がある個体を答え候補とする質問。非悪化だけで改善を補わず、別の個体の改善を借りない。留保・強調・談話上の対照はこの質問構成とは別に必要である。',
}
LIMITS = [
    '第五段落の二問に必要な影響の比較を準備する一般ライブラリ。新たな原始関係・著者主張・原文意味判断は追加しない。原文の二問を記述済みとは数えない。',
    '有限変数の二値構造モデルを用いるが、結果の比較尺度は数値や二値に限定しない。同じ方程式・背景で要因だけを固定するというモデル内部の対照であり、現実の社会的因果を同定した証拠ではない。',
    '全解の交差比較は、非決定的な解同士を結ぶ追加の対応規則がないときの頑健な比較である。無関係な外生条件の違いを同じモデルに混ぜない。対を限定する必要があるモデルには、対応条件を明示する拡張が必要。',
    '評価済みは比較入力の充足条件であり、著者が答えを知っているという心理状態ではない。入力が未知なら評価器は例外を返す。解がない・評価が欠ける・比較不能という既知の不適合は全てr2vdで拒否し、害がないという判断に置き換えない。',
    '原文へ接続する前に、候補の制限とモデル要因の有無の対応、既存r2lnと同じ啓蒙への進行尺度、対象・期間・背景の固定、通常性または潜在性のどちらを採るかを確定する。数値尺度や全解での非悪化を原文が指定したものとはしない。',
    'Welcheの候補範囲を直前の四個人だけへ縮めない。二問の同じ制限・啓蒙への照応、aberとsondernの対照、wohlの留保、garの焦点、後続の回答への接続は未完である。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def both(*items):
    if len(items) == 1:
        return items[0]
    return 'w[' + items[0] + '][' + both(*items[1:]) + ']'


def side(operator, sign, body):
    return ('k ' + operator + '[v variables v equations i[item a][e[v item][v factor]] '
            'i[item a][' + (TRUE if sign else FALSE) + '] ' + body + ']')


def every(name, body):
    return 'k r2vc[' + ARGS + ' i[' + name + ' ' + STATE + '][' + body + ']]'


def compare(first, second):
    return 'c[v atleast][v ' + first + ' v ' + second + ']'


def definitions():
    off = side('ru', False, 'v state')
    on = side('ru', True, 'v state')
    text = 'd r2vb[state ' + STATE + ' ' + MODEL + '] c[x[' + off + '][' + on + ']].\n'
    text += ('d r2vc[' + MODEL + ' test h[' + STATE + '] c] c['
             'q[k rs[v variables]][' + TRUE + '][i[acc c state ' + STATE + '][' +
             both('v acc', 'y[k r2vb[v state ' + ARGS + ']][c[v test][v state]]') + ']]].\n')
    transitive = every('first', every('middle', every('last',
        'y[' + both(compare('first', 'middle'), compare('middle', 'last')) +
        '][' + compare('first', 'last') + ']')))
    comparable = side('rw', True, 'i[on ' + STATE + '][' +
        side('rw', False, 'i[off ' + STATE + '][x[' + compare('on', 'off') +
             '][' + compare('off', 'on') + ']]') + ']')
    valid = both('k ree[' + ARGS + ']',
        every('state', both('c[v assessed][v state]', compare('state', 'state'))),
        transitive, comparable)
    text += 'd r2vd[' + PROFILE + '] c[' + valid + '].\n'
    for name, low, high in [('r2ve', 'on', 'off'), ('r2vf', 'off', 'on')]:
        strict = both(compare(high, low), 'u[' + compare(low, high) + ']')
        body = side('rv', True, 'i[on ' + STATE + '][' +
            side('rv', False, 'i[off ' + STATE + '][' + strict + ']') + ']')
        text += 'd ' + name + '[' + MODEL + ' ' + ORDER + '] c[' + both('k rz[v variables v factor]', body) + '].\n'
    raw = ARGS + ' v atleast'
    text += 'd r2vg[' + PROFILE + '] c[' + both('k r2vd[' + PARGS + ']', 'k r2ve[' + raw + ']') + '].\n'
    text += 'd r2vh[' + PROFILE + '] c[' + both('k r2vd[' + PARGS + ']', 'u[k r2ve[' + raw + ']]') + '].\n'
    text += 'd r2vi[' + PROFILE + '] c[' + both('k r2vh[' + PARGS + ']', 'k r2vf[' + raw + ']') + '].\n'
    fields = 'scope h[a] c assessed h[a] c decreases h[a] c'
    candidate = both('c[v scope][v item]', 'c[v assessed][v item]')
    text += 'd r2vj[' + fields + '] g[a][j v[i[item a][' + both(candidate, 'c[v decreases][v item]') + ']]].\n'
    text += 'd r2vk[' + fields + ' increases h[a] c] g[a][j v[i[item a][' + both(
        candidate, 'u[c[v decreases][v item]]', 'c[v increases][v item]') + ']]].\n'
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rs', 'ru', 'rv', 'rw', 'ree']), statements=[])
    imports = [d['name'] for d in doc['declarations']]
    assert not set(MEANINGS) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    primitives = {}
    meanings = {}
    for n in imports:
        e = old.entries[n]
        if e['kind'] == 'primitive':
            primitives[n] = dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'],
                                 arguments=e['arguments'], meaning_ja=e['meaning_ja'])
        else:
            meanings[n] = e['meaning_ja']
    basis = dict(status='partial_qualitative_intervention_comparison_for_restriction_questions',
                 document=LIBRARY, primitives=primitives, definitions=meanings | MEANINGS,
                 imported_meaning_basis=PARENT_BASIS, imported_symbols=imports,
                 import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in
                                       (PARENT_BASIS, old.document_path)},
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
