"""Compose the appointed-guardian forecast and expectation background."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-dissemination-content.noema'
PARENT_BASIS = 'data/dissemination-content-basis-v1.json'
FULL = 'examples/v016/kant-guardian-forecast.noema'
CORE = 'examples/v016/guardian-forecast-core.noema'
BASIS = 'data/guardian-forecast-basis-v1.json'
ANNOTATIONS = 'data/guardian-forecast-identifiers-v1.json'
PRIMITIVES = {
    'h223i': ('[a d] a', ['audience', 'reference'],
              '同じ公衆についてのこの参照文脈で、任用された指導役が関わる多数の被指導者として言及される人口集団の参照候補。公的議論の読者集合そのものとは同定しない。大きさと人の分類は利用側で検査する。貧困・身分・全員の無思考・現在の被指導の実行をこの参照だけから導かない。'),
    'h223j': ('[a d] b', ['audience', 'reference'],
              '同じ公衆と参照文脈で、被指導者の人口集団を大勢と呼ぶ人数上の下限。結果や自己思考者の人数から逆算せず、背景となる人口規模に照らして固定する。利用側で二人以上の下限であることと、それを集団の人数が厳密に超えることを検査する。原文に具体的な人数を補うものではない。'),
    'h223k': ('[a a a a d] c', ['event', 'issuer', 'person', 'role', 'point'],
              'この制度上の任用行為によって、この出所がこの人へこの職務を委ねる。行為・出所・本人・職務・状況の一致を保持し、自己申告、単なる推薦や活動実績とは区別する。生起と任用時の委任、評価時点でなお職務を委ねられていることは利用側で別に結ぶ。特定の儀礼、法的正当性、本人の同意は要求しない。'),
}
MEANINGS = {
    'r2m5': '同じ人々の集団の構成員である少なくとも一人の他者について、担い手が総括的に指導・監督する立場dcを持つ活動内容。役割の公的な責務の記述として引用する。全構成員を一人の後見役が監督すること、現実の行為や成功を要求しない。',
    'r2m6': '同じ役割に、同じ対象集団の人々への指導・監督r2m5を担う公的責務が制度上委ねられている。既存hzxgの役割・活動記述・共同体・状況を用いる。任用履歴や現在の職務委任はhzhbで別に結び、職務分類だけで本人の任用を認定しない。',
    'r2m7': '指定公衆・参照文脈のh223iが指す集団について、全構成員列mpに重複がなく全員が人であり、列の人数が文脈下限h223jを厳密に超えることを要求する。下限は二人以上とし、少数者を大勢と呼ぶための負の値を受理しない。公衆の読者と集団を同一化しない。',
    'r2ma': 'r2m3の同じ条件付き伝播の枠に、r2m7の大衆の分類と大きさを加える。焦点とその外側の比較のどちらにも同じ公衆・参照・大衆・人数条件を共用する。',
    'r2mb': '公衆と参照文脈の閉じた呼称記述を用い、r2maの閉じた階数1の枠記述を構成する。内容を実行せず、元の対象と呼称の一致は内側のr2m4で検査する。',
    'r2mc': '同じ公衆・参照から、大衆の閉じた参照、任用行為h223k、役割分類r2m6をhzpxへ渡す。その同じ任用された後見役の焦点と否定を同じr2mbの枠へ適用し、hzpwで主張と期待背景の組を作る。比較候補の実在や期待の数値確率を補わない。',
    'r2mg': '量化した元の公衆と参照状況について、閉じた呼称の指し先がそれぞれ元の対象と一致することを要求する。引用の内側で置き換わった対象だけを再検査して、元とは別の公衆の成功で代用することを防ぐ。呼称の表記そのものの一致は要求しない。',
    'r2md': '非空の文脈上の公衆範囲h222eの全てがr2laの分類を満たし、それぞれのr2mcから取り出した主張内容が同じ参照状況で成立するという閉じた内容。公衆ごとの大衆と焦点を保持し、一つの任意の公衆の主張で代用しない。',
    'r2me': 'r2mdと同じ非空の公衆範囲と分類について、同じ各r2mcの期待背景を同じ参照状況で述べる閉じた内容。主張側が偽であることを背景の否定へ変換せず、主張の真理と背景の扱いを分ける。',
    'r2mf': '閉じた主張r2mdと背景r2meを、既存rtqの二つの帰属関係で同じ第二文の箇所・著者・提示文脈へ接続する。主張範囲hzpzと背景範囲hzq2を区別する。世界の伝播・任用や期待比較の真理を帰属時に実行しない。',
}
LIMITS = [
    '大衆は、その文脈で制度上の指導役が関わる大勢の人々という読み。公的議論の読者、公衆全体、特定の身分・貧困層、全員が思考不能な集団と同一視しない。語の侮蔑的な含みの強さを数値化したものではない。',
    '大きさを固定した文脈下限と人数で扱う明示的な読みである。人数はmpの全構成員列から取り、任用者・自己思考者・伝播成功者だけを数えない。規模の基準は原文が与える数値ではない。',
    '後見役を、同じ人々の集団への指導・監督を担う公的責務を持ち、その職務へ過去の行為で任用され、評価機会でも委任されている人として読む。法的な未成年後見制度、全対象者の一括監督、現在の実際の指導を要求しない。',
    '同じ対象集団への制度上の公的責務を既存hzxgへ結ぶ。大衆を法的に単一の法人や地理的に一箇所へ集まる群衆とする条件は加えない。制度の全機構や職務の正当性はこの分類から導かない。',
    'sogarは、同じ条件付き伝播が後見役を含む場合を、その外側を含む場合より見込みにくいと提示する背景として読む。焦点の主張と背景は別に帰属し、外側にも自己思考者が実在するという断言や著者の内心の測定値を加えない。',
    '本文上の二つの帰属は、同じ文脈の各公衆についての主張と背景をそれぞれ量化してから構成する。帰属の真理から、原著者の予測が実際に正しいことを認定しない。',
    '第二文の中核内容・任用・大衆・比較背景を閉じた著者帰属にする。頚木の比喩と予測内の同じ人物・自己離脱との接続を点検し、第二文全体を再読する作業は残る。今回だけで第二文の意味確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    text += '''
d r2m5[holder a governed a] e[b point[
 g person a[w[k hg[k mp[v governed] v person]][w[k aa[v person]][
 w[u[e[v holder][v person]]][k dc[v holder v person v point]]]]]
]].
d r2m6[role a governed a point d] c[k hzxg[v role r[p r2m5] v governed v point]].
d r2m7[audience a reference d] c[
 w[k hi[k mp[k h223i[v audience v reference]] p aa]][
 w[u[k hc[k h223j[v audience v reference] n p c b]]][
 k hc[k h223j[v audience v reference] d[k mp[k h223i[v audience v reference]]]]
 ]]
].
d r2ma[audience a reference d] h[i[h[a d] c]] e[
 i[subgroup i[h[a d] c]][b point[
 w[k r2m7[v audience v reference]][t[c[k r2m3[v audience v reference]][v subgroup]][v point]]
 ]]
].
d r2mb[audience a reference d] i b[h[i[h[a d] c]] e][
 o a[r b[p r2ma]][k h223g[v audience] k h223h[v reference]]
].
d r2mc[audience a reference d] h[h[i c[e] i c[e]] i c[e]] i c[e][
 k hzpw[k r2mb[v audience v reference]
 k hzpx[o a[r[p h223i]][k h223g[v audience] k h223h[v reference]] r[p h223k] r[p r2m6]]]
].
d r2mg[audience a reference d] c[
 w[e[s[k h223g[v audience]]][v audience]][e[s[k h223h[v reference]]][v reference]]
].
d r2md[] e[b reference[
 w[g audience a[k h222e[v audience v reference]]][
 f audience a[y[k h222e[v audience v reference]][
 w[k r2la[v audience v reference]][w[k r2mg[v audience v reference]][t[s[k rsu[k r2mc[v audience v reference]]]][v reference]]]
 ]]
 ]
]].
d r2me[] e[b reference[
 w[g audience a[k h222e[v audience v reference]]][
 f audience a[y[k h222e[v audience v reference]][
 w[k r2la[v audience v reference]][w[k r2mg[v audience v reference]][t[s[k rsv[k r2mc[v audience v reference]]]][v reference]]]
 ]]
 ]
]].
d r2mf[] c[
 k rtq[k hzp5[] k wa[] r d[k r2md[]] r d[k r2me[]]
 k hzpz[] k hzq2[] k hzp3[] p hznreport p hzrbgreport]
].
'''
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2mf', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2mf', 'hzp6']), statements=[statement, statements[32]])
    declarations = {d['name']: d for d in added}
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='closed_guardian_forecast_and_background_sentence_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/dissemination-content-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
