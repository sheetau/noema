"""Compose an agitating appeal and its actual motivational effect."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_enlightenment_incapacity import FIELDS as PRIOR_FIELDS

PARENT = 'examples/v016/kant-enlightenment-incapacity.noema'
PARENT_BASIS = 'data/enlightenment-incapacity-basis-v1.json'
FULL = 'examples/v016/kant-public-incitation.noema'
CORE = 'examples/v016/public-incitation-core.noema'
BASIS = 'data/public-incitation-basis-v1.json'
ANNOTATIONS = 'data/public-incitation-identifiers-v1.json'
FIELDS = [(n, t) for n, t in PRIOR_FIELDS if n != 'incites'] + [('pressurename', 'i[a]')]
PRIMITIVES = {
    'h223s': ('[a a d] c', ['person', 'action', 'point'],
              '本人が、認知上捉えている指定行為への能動的な参加に向けて、進んで取り組む意向と準備を持つ。行為は予定として指示でき、実際の実行や成功を要求しない。その行為自体を内在的に好ましいと評価すること、熟慮して決めたこと、他の動機の不在は含意しない。別の行為への意欲や単なる知識と区別する。'),
    'h223t': ('[a a d] c', ['act', 'recipient', 'point'],
              'この提示行為の表現・遂行の様式が、この受け手の怒り・憤りなどの反抗的な感情に訴えるものである。理由を冷静に示すだけの様式とは区別する。受け手に実際に感情や意欲が生じたこと、行動、因果的な成功、虚偽の内容は含意しない。発話に限らず理解できる身振りや表示も含み得る。'),
    'h223u': ('[a a d] c', ['person', 'action', 'point'],
              '本人が、認知上捉えている同じ行為へ向けて、怒り・興奮などの反抗的な感情の高まりを持つ。平静な行動意欲、無関係な対象への怒り、単なる身体運動とは区別する。行為の実行、熟慮、合理的な正当性や、感情の発生原因はこの関係だけから導かない。'),
}
MEANINGS = {
    'r2mw': '同じ指定行為の生起と、本人のその行為への能動的参加を内容とする関数。働きかけの目標を記述するために使い、引用しただけで将来の行為が実際に生起したとはしない。',
    'r2mx': '本人に同じ指定行為への参加r2mwを求める発話。促しの内容を保ち、命令権限や実行済みの事実へ置換しない。',
    'r2my': '同じ本人・行為・時点に、取り組む意向と準備h223s、および反抗的な感情の高まりh223uが共にある内容。平静な意欲だけ、別の行為への感情だけでは足りない。',
    'r2mz': '同じ生起する提示行為が同じ受け手へ、同じ指定行為への参加を求める発話r2mxを示し、受け手がそれを受領・理解している。提示の様式h223t、同じ行為へのr2myの実際の成立、その同じ提示行為による結果生成g3を結ぶ。求めた行為自体の実行は要求しない。',
    'r2na': '公衆の非空の構成員列を受け手に固定し、非空で重複のない人の発信者列の全員が同じ提示行為へ参加して提示側の当事者となり、全受け手にr2mzが成立する関数を作る。引用する目標行為の閉じた参照が、引数の圧力行為と同一であることも検査する。後見役・不能・複数性はr2mqで別に要求する。',
    'r2nb': 'r2mvに、後の公衆側参加者を受け手とするr2naを渡し、扇動関係を充足する。閉じた圧力行為名と元の行為の同一性を含意の外でも要求する。別行為の名によって前件を偽にして通すことはできない。後の強制行為の生起と保持因果は従来どおり後件で評価する。',
}
LIMITS = [
    'aufgewiegeltを、同じ行為に向けた呼びかけが、反抗的な感情に訴える様式を通じて、その行為への意欲と感情の高まりを実際に生じさせたという読みで構成する。単なる説明、受信、偶然の昂まり、冷静な助言と区別する。虚偽、暴力、合法性、全員一致は補わない。',
    '発信者は提示側の共同当事者であり、全員がそれぞれ別々に十分な原因であるとは要求しない。公衆全員ではなく、後に同じ強制を担う非空の参加者群を受け手へ固定する。集団としての作用への帰属h223oは後の強制側で要求する。',
    '圧力行為は予定として閉じた参照で指示する。その同じ行為への参加の促しを引用し、受け手の理解と意欲は評価するが、求めた行為の実行や成功は扇動の条件に含めない。これにより条件の後件を前件へ先取りしない。',
    '提示時点は働きかけと結果を評価する局面であり、その内部の細かい前後を指定しない。扇動局面から強制開始への厳密な前後は既存r2mrで要求する。先行の後見人から公衆への作用と扇動の相互順序は固定しない。',
    '被作用者affectedの集団述定としての十分さ、事例の閉じた参照供給、頚木の照応、Besonders/selbst、偏見の害と報復、閉じた著者帰属と第三文全体の通読は残る。既存59文、十三の全単位判断、先頭二文382非空白文字を保持し、第三文の確認済み文字数は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    fields = ' '.join(n + ' ' + t for n, t in FIELDS)
    args = ' '.join('k r2na[v participants v pressurename]' if n == 'incites' else 'v ' + n
                    for n, _ in PRIOR_FIELDS)
    return '''
d r2mw[action a] h[a] e[i[person a][b point[w[k dg[v action v point]][k df[v person v action v point]]]]].
d r2mx[action a] h[a] f[i[person a][j m[c[k r2mw[v action]][v person]]]].
d r2my[action a] h[a] e[i[person a][b point[w[k h223s[v person v action v point]][k h223u[v person v action v point]]]]].
d r2mz[act a recipient a action i[a] point d] c[
 w[k aa[v recipient]][w[k dg[v act v point]][
 w[k f2[v act v recipient v recipient o a[r[p r2mx]][v action] v point]][
 w[k h6e[v act v recipient v recipient o a[r[p r2mx]][v action] v point]][
 w[k h6g[v recipient v recipient o a[r[p r2mx]][v action] v point]][
 w[k h223t[v act v recipient v point]][
 w[t[c[k r2my[s[v action]]][v recipient]][v point]][
 k g3[v act v recipient o a[r[p r2my]][v action] v point]
 ]]]]]]]
].
d r2na[recipients j[a] action i[a]] h[a a j[a] a d] c[
 i[act a public a agitators j[a] pressure a point d][
 w[e[s[v action]][v pressure]][w[k r2mo[v public v recipients]][
 w[k hi[v agitators p aa]][w[g person a[k hg[v agitators v person]]][
 w[f person a[y[k hg[v agitators v person]][w[k df[v person v act v point]][k f3[v person v act v point]]]]][
 f person a[y[k hg[v recipients v person]][k r2mz[v act v person v action v point]]]
 ]]]]]
 ]
].
d r2nb[''' + fields + '''] c[
 w[e[s[v pressurename]][v pressure]][k r2mv[''' + args + ''']]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + text + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2nb']), statements=[])
    declarations = {d['name']: d for d in added}
    basis = dict(status='incitation_condition_composed_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result='truth',
                                     arguments=spec[1], meaning_ja=spec[2])
                             for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/enlightenment-incapacity-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
