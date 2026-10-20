"""Bind 'here everywhere' to nontrivial demands in the four preceding cases."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-single-ruler.noema'
PARENT_BASIS = 'data/single-ruler-basis-v1.json'
FULL = 'examples/v016/kant-everywhere-restriction.noema'
CORE = 'examples/v016/everywhere-restriction-core.noema'
BASIS = 'data/everywhere-restriction-basis-v1.json'
ANNOTATIONS = 'data/everywhere-restriction-identifiers-v1.json'
PRIMITIVES = {
    'h234l': ('[a d] a', ['case_node', 'reference'],
              '同じ基準で、この先行箇所の事例を具体化する発話者の参照。発話・役割・内容がその事例に一致することは合成定義で別に検査する。制限が見つかるかどうかによって人物を取り替えない。'),
    'h234m': ('[a d] a', ['case_node', 'reference'],
              '同じ基準で、この先行箇所の事例に当たる発話行為の参照。h234lの話者と同じ行為・宛先・内容を合成定義で照合する。別の命令や制約を述べる発話を代用しない。'),
    'h234n': ('[a a d d d] c', ['case_node', 'person', 'reference', 'baseline', 'alternative'],
              '同じ事例・本人・基準・現状を比較するとき、その本人の行動や態度の選び方として、当該要求による適否を条件にしなければ選択肢となる状況。本人以外の行動、発話者・発話・宛先、要求の範囲と内容、判断に必要な背景を保持し、本人の選択だけを変える。要求を満たす候補だけに事後選別せず、他人の不履行や背景の消失、論理的に不可能な事態だけで選択の制約を作らない。現実に選んだことや、要求による選択の物理的な強制・法的正当性は意味しない。'),
    'h234o': ('[] a', [], '第五段落u0012の[537,581)で、ここでは至るところ自由の制限があると述べる文章箇所。'),
    'h234p': ('[a a j[a] d] c', ['node', 'author', 'antecedent_nodes', 'context'],
              '同じ著者・箇所・文脈のこの談話上の指示が、指定した先行箇所の列に示された事例を対象範囲として指す。地理的な全世界や同じ語を含む任意の箇所へ広げず、都合のよい一事例だけを抜き出さない。各事例の内容の真理や、その全てへの同じ述定は別に構成する。'),
}
MEANINGS = {
    'r2us': '直前の将校・財務担当官・聖職者・統治者の四つの文章箇所を、原文順に固定した列。Hierの指示とüberallの量化で同じ列を使う。',
    'r2ut': 'この事例の箇所が、固定した四箇所r2usのいずれかに属する。世界の全ての場所・人・自由を対象にしない。',
    'r2uu': '指定された同じ話者・呼び声・社会的方面について、著者の周囲の方面h232sと源泉h232t、役割、同じ禁止と肯定命令r2tqを結ぶ。先行三文の存在証人を明示した形で再利用する。',
    'r2uv': '事例の箇所に応じて、同じ話者と発話を将校の教練、財務担当官の支払い、聖職者の信仰、世界の統治者の許可と服従へそれぞれ接続する。対応を入れ替えず、後の制約とは無関係な別命令を持ち込まない。',
    'r2uw': '同じ事例・話者・発話・基準の固定された宛先範囲。前三者は同じ呼び声のh232u、統治者は同じ発話者のh233pを用いる。単に制約を受ける別の人を選ばない。',
    'r2ux': '同じ事例と本人について、評価状況で当該指示の内容を満たす条件。前三者は本人に適用したr2tk/r2tl/r2tmの内容、統治者は同じ出所に対する本人のr2udの履行を評価する。統治者の議論への許可r2ueを禁止へ反転しない。',
    'r2uy': '同じ事例の宛先の少なくとも一人に、本人以外の背景を保った自由選択候補h234nがあり、その候補では同じ当該指示の内容r2uxを満たさない。要求はその選択を適合するものとして残さないという非自明な制限を表す。現実の違反、物理的な不能、全選択肢の消滅は要求しない。',
    'r2uz': '叙述上の現在と評価点を一致させ、異なる固定四事例の全てについて同じ話者・発話の対応r2uvと非自明な選択の制限r2uyを要求する。一事例の制限だけで全体を満たさず、各事例で全宛先の自由が全面的に失われたとは言わない。',
    'r2va': 'この全事例の制限r2uzを著者へ帰属し、Hierの指示範囲r2usと、直前の括弧文からの本文順序を同じ第五段落の提示文脈に結ぶ。発話の存在から規範の正当性を導く規則にはしない。',
}
LIMITS = [
    'Hier ist überall Einschränkung der Freiheit.を、直前の四つの事例ではどれにも、本人の選択に任せない要求が含まれるという読みで構成する。四事例を地理的な全世界や全自由の全面的な消滅へ広げない。',
    '制限は、その要求がなければ本人の選択肢となる候補の少なくとも一つが、当該要求を満たさないという意味である。要求への適合と、能力、実際の実行、物理的な強制、法的・道徳的な正当性を区別する。単なる発話の存在や、もともと不可能な選択だけを制限の証拠にはしない。',
    '前三者では同じ本人への議論の不実行と教練・支払い・信仰を求める内容、統治者では同じ出所の要求に従う履行の内容を扱う。統治者の議論への容認を否定したり、全てを公的な理性使用の禁止へ揃えたりしない。',
    '候補状況では同じ基準の要求・宛先・他者・関連する背景を保持し、その本人の選択だけを変える。制約される人と、指示の内容を評価する人・出所を取り替えない。自由選択候補の適切な供給は意味規約の一部であり、任意の別世界を入力して制限と認定しない。',
    '各事例について少なくとも一人に選択の制限があることを要求する。überallを全四事例への量化と読み、全宛先の全行動を一律に制限するという強い主張は補わない。現実の誰かの違反や全員の服従も主張しない。',
    '新しい主張は、同じ要求の内容が選択を制限するという著者の評価を追加する。先行する発話の提示だけから正当な義務や政策の効力を自動的に導く推論規則ではない。',
    '統治者の履行条件r2udは全記述域の網羅性を含む。先行版の有限評価拒否と診断の限界を保持し、この文の局所検査でも境界を明記する。',
    '続く[582,638)の阻害を問う文と[639,687)の非阻害・促進を問う文は未統合である。この一文の判断を両問や第五段落全体の完成へ拡張しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2us[] j[a][l[a][k h233m[] k h233n[] k h233o[] k h234i[]]].
d r2ut[case a] c[k hg[k r2us[] v case]].
d r2uu[speaker a call a quarter a reference i[d] role h[a d] c positive i[h[d] h[a] e] command i[h[d] h[a] f] point d] c[
 w[k h232s[k wa[] s[v reference] v quarter]][
 w[k h232t[v quarter v speaker s[v reference]]][
 w[c[v role][v speaker v point]][k r2tq[v speaker v call k wa[] v reference v positive v command v point]]
 ]]
].
d r2uv[case a speaker a call a reference i[d] point d] c[
 x[w[e[v case][k h233m[]]][k r2uu[v speaker v call k h233i[] v reference p r2to r[p r2tg] r[p r2tk] v point]]][
 x[w[e[v case][k h233n[]]][k r2uu[v speaker v call k h233j[] v reference p r2tp r[p r2th] r[p r2tl] v point]]][
 x[w[e[v case][k h233o[]]][k r2uu[v speaker v call k h233k[] v reference p sp r[p r2ti] r[p r2tm] v point]]][
 w[e[v case][k h234i[]]][w[k r2uk[v speaker s[v reference] v point]][k r2ul[v speaker v call v reference v point]]]
 ]]]
].
d r2uw[case a speaker a call a reference d person a] c[
 w[k r2ut[v case]][
 x[w[e[v case][k h234i[]]][k h233p[v speaker v reference v person]]][
 w[u[e[v case][k h234i[]]]][k h232u[v call v reference v person]]]
 ]
].
d r2ux[case a source a person a reference d point d] c[
 x[w[e[v case][k h233m[]]][t[o[c[k r2tk[v reference]][v person]]][v point]]][
 x[w[e[v case][k h233n[]]][t[o[c[k r2tl[v reference]][v person]]][v point]]][
 x[w[e[v case][k h233o[]]][t[o[c[k r2tm[v reference]][v person]]][v point]]][
 w[e[v case][k h234i[]]][t[k r2ud[v source v person v reference]][v point]]
 ]]]
].
d r2uy[case a source a call a reference d point d] c[
 g person a[w[k r2uw[v case v source v call v reference v person]][
 g alternative d[w[k h234n[v case v person v reference v point v alternative]][
 u[k r2ux[v case v source v person v reference v alternative]]]]
 ]]
].
d r2uz[] e[b point[
 w[e[k h232v[]][v point]][w[k hh[k r2us[]]][
 f case a[y[k r2ut[v case]][
 w[k r2uv[v case k h234l[v case k h232v[]] k h234m[v case k h232v[]] r[k h232v[]] v point]][
 k r2uy[v case k h234l[v case k h232v[]] k h234m[v case k h232v[]] k h232v[] v point]]
 ]]
 ]]
]].
d r2va[] c[
 w[k hzon[k h234o[] k wa[] r b[k r2uz[]] k h232o[]]][
 w[k h234p[k h234o[] k wa[] k r2us[] k h232o[]]][k ue[k h234i[] k h234o[] k h232o[]]]
 ]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + s[0] + '.' for n, s in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2va', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2va']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='everywhere_restriction_under_explicit_reading', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/single-ruler-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
