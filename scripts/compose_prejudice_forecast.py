"""Bind the future comparison to the same publics and revolutionary cases."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-prejudice-guidance.noema'
PARENT_BASIS = 'data/prejudice-guidance-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-forecast.noema'
CORE = 'examples/v016/prejudice-forecast-core.noema'
BASIS = 'data/prejudice-forecast-basis-v1.json'
ANNOTATIONS = 'data/prejudice-forecast-identifiers-v1.json'
PRIMITIVES = {
    'h227l': ('[a d] j[a]', ['public', 'reference'],
              '同じ公衆と基準文脈において第五文後半で古い偏見として対照に置く意見群の全参照列。候補ごとに古い意見を選び替えず、各項の実際の採用・働き、複数性はr2rk以下で検査する。特定の歴史的教説名は補わない。'),
    'h227m': ('[a d d] j[a]', ['public', 'reference', 'candidate'],
              '同じ公衆と基準について、候補経過で新しい偏見として言及する意見群の全参照列。成功する項目だけを抽出しない。参照を与えることと、意見が実際に採用され働くことは区別し、新しさ・複数性・新旧の内容差はr2rk以下で要求する。候補ごとに具体的内容が異なってよい。'),
    'h227n': ('[] a', [], '固定原文kant-1784:u0011第五文後半[1102,1216)、sondernからdienenまでの文章箇所。新旧の偏見の将来の働きの帰属に用い、sondernの対比とLeitbandの描写はこの参照だけでは尽くさない。'),
    'h227o': ('[] a', [], '固定原文kant-1784:u0011第五文後半の大衆を指すdes gedankenlosen großen Haufens[1176,1208)の文章箇所。語調を内容の真偽と区別して帰属するための参照。'),
}
MEANINGS = {
    'r2rl': '同じ公衆・基準・候補の先頭文から引き継いだ期間枠と起点を用いる。起点より後のある点で、固定した旧意見群h227lと同じ候補の新意見群h227mが、同じ大衆についてr2rkの比較を満たす。前後点の時間枠はr2qs、履歴と順序は同じh7q/icで結ぶ。',
    'r2rm': '同じ公衆・基準で全候補の時間枠が有効であり、前半と同じr2qxの革命候補が少なくとも一つある。全活動・候補について、それがr2qxに該当すれば同じ候補のr2rlを要求する。離脱に成功した革命だけへの制限や、一つの当たった予測での代用はしない。',
    'r2rn': '先頭四文と前半と同じ非空の公衆範囲h222eを量化し、各公衆の分類r2la・全構成員照合r2ndとr2rmの予測を要求する閉じた内容。候補内での未来を、現実の過去の事実へ移さない。',
    'r2ro': '同じ著者wa・段落文脈hzp3・後半の箇所h227nへ、段階3の閉じた予測r2rnをhznreportで帰属する。予測の真理を帰属時に実行しない。',
    'r2rp': '後半の大衆を指す同じ箇所h227oで、著者が先頭文からの公衆範囲と第二文からの大衆参照族h223iに対し、低く扱う呼称を使うことを既存h223lで帰属する。人数と未吟味の作用は内容側に保ち、語調から能力や社会的身分を推論しない。',
    'r2rq': '後半の予測帰属r2ro、大衆の語調r2rp、前半の箇所h227hから後半への本文順序ueと箇所の区別を統合する。sondernの意味上の対比やLeitbandの物理的描写までは順序だけで代用しない。',
}
LIMITS = [
    'werdenは、前半で論じた革命のある候補において、議論の起点より後に新しい偏見が同じ大衆へ働くという予測と読む。全対象候補でのカテゴリー的な予測の読みで、数値確率や将来の全時点での永続を加えない。著者への帰属と予測の現実の正しさは別である。',
    '時間枠・起点・公衆・革命分類は前半と共用する。新旧比較は起点と後続点を結ぶが、革命の完了後に初めて新しい意見が生まれるという厳密な開始順序や、革命が偏見を直接作るという因果は原文へ補わない。',
    '旧意見群は基準文脈で固定し、新意見群は候補ごとの言及対象とする。各項の働き・内容差・新しさ・集団への広がりはr2rkで実際に要求し、参照供給を原文内容の代替にしない。',
    '同じ公衆に複数の革命的活動がある場合も全て検査する。後半は候補内の大衆の状態についての予測であり、活動ごとに別の新意見群を選んで都合のよい結果へ付け替えない。',
    'h223lの呼称の扱いを第二文と同じ大衆参照へ再利用する。侮蔑の程度の数値、身分・貧困、全員の思考不能や無意識は補わない。',
    '未来予測と語調を本文に追加するが、Leitbandの身体的描写、vielleicht wohlの留保・譲歩、aber/sondernの対比、第五文と段落全体の通読は残る。旧62文と意味判断を保持し、第五文の確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2rl[public a reference d candidate d] c[
 g later d[
 w[k r2qs[v public v reference v candidate k h222h[v public v reference v candidate] v later]][
 k r2rk[v public v reference k h227l[v public v reference] k h227m[v public v reference v candidate]
 k h222h[v public v reference v candidate] v later
 i[point d][k h7q[k h222g[v public v reference] v candidate v point]]
 i[first d last d][k ic[v first v last v candidate]]]
 ]]
].
d r2rm[public a reference d] c[
 w[f candidate d[y[k h222k[v public v reference v candidate]][
 k hzne[k h222g[v public v reference] k h222h[v public v reference v candidate] v candidate]
 ]]][
 w[g act a[g candidate d[k r2qx[v public v reference v act v candidate]]]][
 f act a[f candidate d[y[k r2qx[v public v reference v act v candidate]][
 k r2rl[v public v reference v candidate]
 ]]]
 ]]
].
d r2rn[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][
 w[k r2la[v public v reference]][w[k r2nd[v public v reference]][k r2rm[v public v reference]]]
 ]]]
]].
d r2ro[] c[k hznreport[k h227n[] k wa[] r d[k r2rn[]] k h227n[] k hzp3[]]].
d r2rp[] c[k h223l[k h227o[] k wa[] r b[p h222e] r b[p h223i] k hzp3[]]].
d r2rq[] c[
 w[k r2ro[]][w[k r2rp[]][w[u[e[k h227h[]][k h227n[]]]][
 k ue[k h227h[] k h227n[] k hzp3[]]
 ]]]
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
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2rq', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2rq']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='prejudice_forecast_and_mass_tone_attributed_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prejudice-guidance-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
