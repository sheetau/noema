"""Compare freedom forms through their content, without asserting their realization."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-public-topics.noema'
PARENT_BASIS = 'data/public-topics-basis-v1.json'
FULL = 'examples/v016/kant-freedom-comparison.noema'
CORE = 'examples/v016/freedom-comparison-core.noema'
BASIS = 'data/freedom-comparison-basis-v1.json'
ANNOTATIONS = 'data/freedom-comparison-identifiers-v1.json'
FAMILY = 'i b[h[a d] e]'
PRIMITIVES = {
    'h232b': ('[a d] c', ['form', 'reference'],
              '同じ基準文脈で、自由と呼びうる種類の全比較範囲に属する。実現済みの自由、法的な自由、許可された自由、無害と先に判定した自由だけには限定しない。ここでの呼びうるは名称の適用範囲を広く採る読みであり、全可能世界での命名行為を量化しない。範囲は評価結果から選別せず、外部から適切に供給する。'),
    'h232c': (f'[a d] {FAMILY}', ['form', 'reference'],
              '同じ基準文脈で、この種類の自由が何を可能・許容とする状態なのかを指定する閉じた内容族の記述。族を同じ公衆・基準へ適用すると、その自由が与えられる候補の内容を得る。種類名だけを返さず、内容の実行、実際の自由、害の生起を含意しない。別名が同じ内容族を指すことを許す。'),
    'h232d': (f'[{FAMILY} {FAMILY} a d] c',
              ['first_content_family', 'second_content_family', 'public', 'reference'],
              '二つの閉じた内容族を同じ公衆・基準に適用して指定した状態について、第一の害を及ぼす性質が第二以下だという文脈的評価。同じ評価対象・害の観点・背景条件で比較し、低い方をより無害とする。害の対象は公衆の読者だけに限定せず、文脈で固定する。現実の害の件数、数値的期待損失、唯一の最小、害が絶対にないこと、比較内容の実現を要求しない。自由以外の内容にも適用できる比較関係で、全比較可能性・反射性・推移性は呼び出し側で別に検査する。'),
}
MEANINGS = {
    'r2sm': '固定基準の全自由種類h232bと各種類の閉じた内容h232cを用い、同じ公衆・基準での害の比較h232dについて、その種類が最小である。既存rce/rcdが非空性・範囲所属・反射性・推移性・全比較可能性と全対象以下を要求する。同順位を許す。',
    'r2sn': '公的使用の自由の内容族r2slそのものをh232cが指す種類が、同じ範囲の害の比較で最小である。単に別の自由が最小であることや、同じ対象名を使うことでは足りない。内容族は閉じた記述の同一性で接続し、r2slの許可・活動・時間内容を現実に実行しない。',
    'r2so': '先行する啓蒙と同じ非空の公衆範囲h222eの全公衆について、r2snを参照状況で述べる内容。自由の現実の付与や、公衆が現実に啓蒙したことを要求しない。第一文の要件限定と帰属へ後で接続する比較内容である。',
}
LIMITS = [
    'unschädlichsteを、文脈上の害を及ぼす性質が比較範囲の中で最小という相対的な最上級として読む。無害という語の評価的な向きは保持するが、絶対的な害ゼロ、厳密な唯一性、数値の確率や損失量は補わない。',
    'unter allem, was nur Freiheit heißen magは自由と呼びうる種類を広く採る比較範囲と読む。現在認められた自由や政治的な自由だけへの縮小、危険な種類の除外はしない。全ての種類をこの有限モデルが列挙できたという証明ではない。',
    '害の比較は自由を与える状態の性質に関する評価であり、現に害が起きたことや現在の制度の害の総量ではない。具体的な被害者、害の種類、評価背景は原文が特定しないため文脈入力に残す。読者だけへの身体的危害という狭い尺度に固定しない。',
    '内容を比較する二つの引数に同じ公衆・基準を渡す。比較の公衆範囲は先行するh222eを使い、最小となる内容族は全事柄の公的使用と自由維持を構成したr2slへ同一性で結ぶ。別の自由についての有利な評価を流用しない。',
    '内容族の同一性はこの本文で採る正規の閉じた記述を使う。意味が等価そうな別の定義を、構造の一致なしに同じと認める一般的な同義性判定はしない。同じ正規内容を指す種類名の重複は許す。',
    'rceの再利用により同じ範囲で全比較可能な前順序を要求する。尺度が未定で比較不能の組がある場合を同順位として埋めない。実際にこうした評価が正しいことは著者の評価の内容であり、有限検査で実証するものではない。',
    '第五段落第一文[71,214)の比較と公的使用の内容の同一性を構成した部分記述である。und zwarとnämlichの論述上の提示、dieserの照応、nichts erfordert alsの要件限定、aberの対比、第一文全体の帰属と通読は未完。新しい著者主張と確認済み文字数は追加しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2sm[public a reference d form a] c[
 k rce[v form i[item a][k h232b[v item v reference]]
 i[first a second a][k h232d[
 k h232c[v first v reference] k h232c[v second v reference] v public v reference]]]
].
d r2sn[public a reference d] c[
 g form a[w[e[k h232c[v form v reference]][r b[p r2sl]]][k r2sm[v public v reference v form]]]
].
d r2so[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][k r2sn[v public v reference]]]]
]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + s[0] + '.' for n, s in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, list(MEANINGS)), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='freedom_content_minimum_harm_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-topics-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
