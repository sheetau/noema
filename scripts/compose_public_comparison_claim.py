"""Bind the public comparison to explicit populations and a source assertion."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-prospective-comparison.noema'
PARENT_BASIS = 'data/prospective-comparison-basis-v1.json'
FULL = 'examples/v016/kant-public-comparison-claim.noema'
CORE = 'examples/v016/public-comparison-claim-core.noema'
BASIS = 'data/public-comparison-claim-basis-v1.json'
ANNOTATIONS = 'data/public-comparison-claim-identifiers-v1.json'
PRIMITIVES = {
    'h222e': ('[a d] c', ['audience', 'reference'],
              '同じ参照文脈で一般的な比較を述べる対象の宛先集団の範囲。話題上の範囲を与える入力で、公衆の分類、成功者や許可対象だけの選別ではない。結果・候補を見て範囲を縮めず、公衆としての条件と全対象への主張を利用側で検査する。'),
    'h222f': ('[a d] a', ['audience', 'reference'],
              '同じ宛先集団と参照文脈について、許可政策の出所として談話が仮定する主体。原文のmanを特定の歴史上の統治者へ同定せず、候補を替えても同じ出所を用いる。主体が実際に許可したことは含意しない。'),
    'h222g': ('[a d] a', ['audience', 'reference'],
              '同じ宛先集団と参照文脈で比較する変化の期間枠。個人側と公衆側、自由の条件と結果で共用する。具体的な日数や、結果に応じて伸縮する期間を意味しない。'),
    'h222h': ('[a d d] d', ['audience', 'reference', 'candidate'],
              '同じ比較の候補経過内で、将来を区切る起点を指定する。現実の参照文脈とは別の点を許し、公衆の変化・個人の変化・許可維持へ同じ点を渡す。経過内にあることは利用側が検査する。'),
    'h222i': ('[a d] j[a]', ['audience', 'reference'],
              '同じ参照文脈の宛先の想定読者を列挙する有限列候補。成功者・受領者・許可された人の標本ではない。完全性・人の分類・非空性・重複は利用側で検査する。実行時の観測標本から全読者を推定しない。'),
    'h222j': ('[a d] b', ['audience', 'reference'],
              '同じ集団と参照文脈で、その集団の能力変化と呼ぶ広がりの最低比率を定める文脈上の基準。0と1の間で、成功比率がこれを厳密に超える読みとする。原文に固定数値を補わず、変化した人数から逆算して基準を選ばない。'),
    'h222k': ('[a d d] c', ['audience', 'reference', 'candidate'],
              '同じ集団と参照文脈で比較に採る候補経過の範囲。個人の成功、公衆の成功、自由の成立を見て先に絞らない。自由による条件付き制限は内容の式の内部で別に行う。'),
    'h222l': ('[a d] j[a]', ['audience', 'reference'],
              '比較に使う質的な可能性尺度の値を低い順に並べた有限列候補。両端・所属・順序・重複を利用側で検査する。候補数から数値確率を作る列ではなく、同じ比較の全内容で共用する。'),
    'h222m': ('[a d a] c', ['audience', 'reference', 'degree'],
              '指定した比較尺度で必然の端点に近いと採る範囲。利用側のrqssが非空・端点除外・上方への閉性を検査する。基準は文脈の明示入力であり、順序だけから近さを発見したものではない。'),
    'h222n': ('[a d] a', ['audience', 'reference'],
              '同じ候補と尺度での、その公衆の将来の自己啓蒙への無条件の程度評価。比較個人や自由条件を替えて別の目標にしない。値の意味はrqstの両端と比較条件へ接続する。'),
    'h222o': ('[a a d] a', ['audience', 'person', 'reference'],
              '同じ公衆の比較枠で評価する、指定個人の将来の自己形成による自立の程度。先行段落の対象者へ束縛し、別人の程度を流用しない。公衆と同じ候補・期間・尺度における評価である。'),
    'h222p': ('[a d] a', ['audience', 'reference'],
              '同じ公衆の同じ目標について、自由の維持を条件にした程度評価。無条件の値h222nとは区別し、条件付きで必然に近いが端点ではないことを式で検査する。'),
}
MEANINGS = {
    'r2la': '同じ参照文脈の宛先に異なる二人以上の想定読者がいて全員が人である。読者世界ceの想定読者に全員が含まれ、学識者の立場cdで理性を用いる同じ活動記述が、その宛先と読者世界双方へ向けられている。公的議論の宛先としての公衆という採用解釈。実際の提示・受領・理解・許可は要求せず、宛先を読者世界全体と同一視しない。',
    'r2lb': '明示した有限列が指定の構成員範囲を過不足・重複なく尽くすことをrcmで検査し、全員の適格性と正確な比率をpdで検査する。構成員でかつ変化した人の比率が、0より大きく1より小さい指定閾値を厳密に超える。外部の成功者や成功者だけの列を数えない。',
    'r2lc': '同じ集団と参照文脈からh222iの全読者列とh222jの広がり基準を取り出し、aaの適格性を伴うr2lbへ渡す。候補内で変わるのは変化した人の述語であり、母集団と基準は固定する。',
    'r2ld': '同じ集団・同じ個人・同じ参照文脈から全十五引数を供給し、既存r2kwの比較と条件付きのほぼ必然へ接続する。期間・起点・出所・広がり・候補・尺度を公衆ごとに固定し、比較個人によって変える入力は個人とその程度だけである。尺度の列はrtで重複を拒み、先頭・末尾を両端へ使う。',
    'r2le': '話題上の宛先範囲h222eと、第三段落冒頭hzzq・whに固定した個人の範囲hzznをともに非空とする。全ての宛先についてr2laを要求し、前段落の全対象者が人であり、その各人とのr2ldが成立するという文脈的な一般化。成功しそうな公衆や比較しやすい一人だけへ縮めない。',
    'r2lf': 'r2leを同じ参照状況で評価する閉じた内容。候補内の許可や変化の真理は内容の中に置き、現実の成立を外側へ出さない。',
    'r2lg': '閉じたr2lfを、既存の第四段落第一文の箇所hzp4・著者wa・提示文脈hzp3へ階数1の主張帰属hzonで結ぶ。第三段落末h5tからの本文順序ueも記述する。aber・ja・nurの提示作用や原文全体の完成判断はこの帰属に含めない。',
}
LIMITS = [
    'ein Publikumは、ある時代の読者世界の中で、公的議論の宛先となる有限の人々の集団として読む。人数の多い任意の集まり、職務命令だけの宛先とは区別する。全世界の読者との同一性、現実の出版や取得、全員の参加は要求しない。',
    '一般化は、明示した話題上の公衆範囲と第三段落の個人範囲の全てにわたる文脈的な全称として採用する。一般化の例外を確率分布で表す別の読みや、一人の典型人物との比較とは区別する。元の範囲に不適格な対象があれば、それを黙って除いて成功させない。',
    '公衆の自己啓蒙は、内部の異なる人の活動が、自立的な理解力の使用をできるようにする変化が、固定した比率基準を超えて広がることとして読む。全員同時、過半数、固定の人数を原文へ補わない。既に自立した内部の協力者自身の再変化も要求しない。',
    '比率の基準は未知のまま真偽を決める抜け道ではなく、人数上限や通常性尺度と同じ明示的な解釈入力。実行には値が必要であり、意味上は結果から独立に固定する。有限性と人数比を採る明示した読みで、無限の公衆や全ての集合的性質の一般理論ではない。',
    '自由は公的な理性使用の規範的な許可を選択期間で維持する読みを引き継ぐ。公衆を分類したことからその自由を推定しない。身体的機会・他の妨害・権利の保障を同じ許可に自動合流させない。',
    '新しい十二基本宣言は対象範囲・列・閾値・候補・尺度等の文脈入力であり、一文の意味を丸ごと返す演算子ではない。主張内容は既存の分類・能力変化・自己形成・因果・様相・許可から合成する。',
    '第一文の中核内容を本文へ追加するが、aber、ja、nurの作用範囲と提示の接続、一文全体の通読判断は残る。意味確認済み全単位と確認済み文字分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    text = ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items())
    text += '''
d r2la[audience a reference d] c[
 w[f person a[y[k h6t[v audience v person v reference]][k aa[v person]]]][
 w[g first a[g second a[w[u[e[v first][v second]]][w[k h6t[v audience v first v reference]][k h6t[v audience v second v reference]]]]]][
 g world a[w[k ce[v world v reference]][w[
 f person a[y[k h6t[v audience v person v reference]][k h6t[v world v person v reference]]]
 ][g speaker a[g activity a[g role a[w[k aa[v speaker]][w[k ca[v speaker v activity v reference]][
 w[k cb[v speaker v activity v role v reference]][w[k cd[v role v reference]][
 w[k cc[v activity v audience v reference]][k cc[v activity v world v reference]]
 ]]]]]]]]]]]]
].
d r2lb[population j[a] threshold b members h[a] c changed h[a] c eligible h[a] c] c[
 w[k rcm[v population v members]][w[k hc[n p a b v threshold]][w[k hc[v threshold n p b b]][
 k pd[v population v eligible i[person a][w[c[v members][v person]][c[v changed][v person]]]
 i[ratio b][k hc[v threshold v ratio]]]
 ]]]
].
d r2lc[audience a reference d members h[a] c changed h[a] c] c[
 k r2lb[k h222i[v audience v reference] k h222j[v audience v reference] v members v changed p aa]
].
d r2ld[audience a person a reference d] c[
 w[k rt[k h222l[v audience v reference]]][
 k r2kw[v reference v audience v person k h222f[v audience v reference] k h222g[v audience v reference]
 i[branch d][k h222h[v audience v reference v branch]]
 i[members h[a] c changed h[a] c][k r2lc[v audience v reference v members v changed]]
 i[branch d][k h222k[v audience v reference v branch]]
 i[value a][k hg[k h222l[v audience v reference] v value]]
 i[first a second a][k r2dj[k h222l[v audience v reference] v first v second]]
 i[value a][k h222m[v audience v reference v value]]
 k r2dp[k h222l[v audience v reference] v audience] k r2dq[k h222l[v audience v reference] v audience]
 k h222n[v audience v reference] k h222o[v audience v person v reference] k h222p[v audience v reference]]
 ]
].
d r2le[reference d] c[
 w[g audience a[k h222e[v audience v reference]]][
 w[g person a[k hzzn[k hzzq[] v person k wh[]]]][
 f audience a[y[k h222e[v audience v reference]][w[k r2la[v audience v reference]][
 f person a[y[k hzzn[k hzzq[] v person k wh[]]][w[k aa[v person]][k r2ld[v audience v person v reference]]]]
 ]]]
 ]]
].
d r2lf[] e[b reference[k r2le[v reference]]].
d r2lg[] c[w[k hzon[k hzp4[] k wa[] r b[k r2lf[]] k hzp3[]]][k ue[k h5t[] k hzp4[] k hzp3[]]]].
'''
    return text


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2lg', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2lg']), statements=[statement])
    declarations = {d['name']: d for d in added}
    primitives = {n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                          arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()}
    basis = dict(status='contextual_public_comparison_core_claim_source_sentence_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS, primitives=primitives,
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prospective-comparison-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
