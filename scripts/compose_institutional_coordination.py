"""Compose shared institutional targets and role requirements, before attribution."""
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_grounded_step import ROOT
from scripts.compose_qualitative_influence import both

LIBRARY = 'examples/v016/institutional-coordination.noema'
BASIS = 'data/institutional-coordination-basis-v1.json'
PARENT_BASIS = 'data/use-definitions-basis-v1.json'
OUTCOME = 'h[a a a a i[e] d] c'
TARGET = 'i[h[j[a]] e]'
REQUIRED = 'h[a a a ' + TARGET + ' j[a] c d] c'
GROUP = 'people h[a] c community a reference d human h[a] c member h[a a d] c'
GARGS = 'v people v community v reference v human v member'
RESULT = ('people h[a] c community a government a work a arrangement a goal i[e] '
          'reference d human h[a] c member h[a a d] c directs ' + OUTCOME + ' prevents ' + OUTCOME)
RARGS = ('v people v community v government v work v arrangement v goal v reference '
         'v human v member v directs v prevents')
COORDINATED = (RESULT + ' mechanism a governing h[a a d] c coordinated h[a h[a] c a d] c '
               'artificial h[a a d] c supplies h[a a a d] c')
CARGS = RARGS + ' v mechanism v governing v coordinated v artificial v supplies'
MEANINGS = {
    'r2zn': '指定した対象範囲は空でなく、その全員が同じ基準において人であり同じ共同体の成員である。一部の成員を選ぶ条件であり、共同体の全成員を選ぶ条件や真部分集合の条件は加えない。範囲は後の成否から選び直さない。',
    'r2zo': '同じ政府・本人・仕事・協調配置・閉じた目的内容・評価点について、配置を通じた目的への方向付け、または配置を通じた目的破壊の抑止が成立する。包含的な選言で両方の成立を許す。目的の真理は実行しない。方向付けと抑止の関係は引数として明示し、単なる命令や破壊が偶然起きなかったことでは代用しない。',
    'r2zp': 'r2znの固定した非空の成員範囲の各人について、同じ仕事・政府・協調配置・目的内容でr2zoが成立する。人によって選言の成立側が違ってよい。基準での所属と成果を評価する点を分け、成果の良い人だけに範囲を縮めない。',
    'r2zq': '同じ共同体を管轄する政府、同じ成員範囲・仕事についての人為的な協調配置、その配置を同じ仕事に供給する機構、各人についてその配置を通じるr2zpの方向付けまたは抑止を結ぶ。配置の単なる併存で効果を代用せず、各効果の関係にも同じ配置を渡す。全員の内心の信念や目的への同意は要求しない。',
    'r2zr': 'r2zqを評価点に関する内容として構成する。所属・政府の管轄は同じ基準へ固定する。後の目的の引用に渡せる内容であり、この関数を作るだけでは機構の作動、方向付け、抑止、目標達成を断言しない。',
    'r2zs': 'r2znの同じ人々それぞれについて、同じ機構・仕事で割り当てられた役割と、その役割で指定内容を満たす要求を結ぶ。規範の出所、本人、役割、閉じた内容関数、本人・役割・仕事の順序付き三引数、正極性、基準を保持する。要求内容は評価せず、実際の遂行や要求の正当性は含意しない。',
}
LIMITS = [
    'u0012[1294,1660)へ向けた意味依存群であり、当該文の完成訳・帰属・意味確認ではない。本文78主張と既存の意味判断は変更しない。',
    '機構の必要性、仕事が公共の利益に関わる条件、目標の公共性、目的としての引用、passivの具体的内容、oder wenigstensの最低限としての提示、Nunの論述接続は次の本文統合で残る。',
    '成員ごとに方向付けまたは抑止を許す分配的な候補を構成した。全員一括の選言へ強めず、方向付けから抑止を論理的に導かない。この選択の原文適合は文全体の通読で判断する。',
    '供給する入力関係には明示した意味が必要である。空でない人の部分集合、同じ機構による協調、政府・仕事・目的の束縛は合成したが、入力関係自体の意味を有限モデルから証明したとはしない。',
    'r2zsの要求関係は既存h7kと同じ型・引数順序で受ける。機構と規範の出所は別引数とし、政府の個人的な意図、指揮権の正当性、実際の服従を補わない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = 'd r2zn[' + GROUP + '] c[' + both(
        'g person a[c[v people][v person]]',
        'f person a[y[c[v people][v person]][' + both(
            'c[v human][v person]', 'c[v member][v person v community v reference]') + ']]') + '].\n'
    text += ('d r2zo[government a person a work a arrangement a goal i[e] point d '
             'directs ' + OUTCOME + ' prevents ' + OUTCOME + '] c[x['
             'c[v directs][v government v person v work v arrangement v goal v point]][c[v prevents]['
             'v government v person v work v arrangement v goal v point]]].\n')
    text += 'd r2zp[' + RESULT + ' point d] c[' + both(
        'k r2zn[' + GARGS + ']',
        'f person a[y[c[v people][v person]][k r2zo[v government v person v work v arrangement '
        'v goal v point v directs v prevents]]]') + '].\n'
    text += 'd r2zq[' + COORDINATED + ' point d] c[' + both(
        'k r2zp[' + RARGS + ' v point]',
        'c[v governing][v government v community v reference]',
        'c[v coordinated][v arrangement v people v work v point]',
        'c[v artificial][v arrangement v work v point]',
        'c[v supplies][v mechanism v arrangement v work v point]') + '].\n'
    text += 'd r2zr[' + COORDINATED + '] e[b point[k r2zq[' + CARGS + ' v point]]].\n'
    text += ('d r2zs[' + GROUP + ' mechanism a work a source a roles h[a] a '
             'assigned h[a a a a d] c target ' + TARGET + ' required ' + REQUIRED + '] c[' + both(
        'k r2zn[' + GARGS + ']',
        'f person a[y[c[v people][v person]][' + both(
            'c[v assigned][v person c[v roles][v person] v mechanism v work v reference]',
            'c[v required][v source v person c[v roles][v person] v target '
            'l[a][v person c[v roles][v person] v work] e[v person][v person] v reference]') + ']]') + '].\n')
    return text


def build():
    assert not set(MEANINGS) & set(parent().entries)
    doc = parse('p:' + definitions())
    basis = dict(status='institutional_coordination_dependency_group_not_sentence_review',
                 document=LIBRARY, primitives={}, definitions=MEANINGS,
                 limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n',
            BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
