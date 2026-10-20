"""Join the sole enabling requirement, same enlightenment and specified freedom."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-freedom-comparison.noema'
PARENT_BASIS = 'data/freedom-comparison-basis-v1.json'
FULL = 'examples/v016/kant-enlightenment-requirement.noema'
CORE = 'examples/v016/enlightenment-requirement-core.noema'
BASIS = 'data/enlightenment-requirement-basis-v1.json'
ANNOTATIONS = 'data/enlightenment-requirement-identifiers-v1.json'
FAMILY = 'i b[h[a d] e]'
PRIMITIVES = {
    'h232e': (f'[a {FAMILY} a d] c', ['requirement', 'goal_family', 'subject', 'reference'],
              '同じ対象・基準で、閉じた内容族が指定する目標へ向けて進めるために供給を求める要件として、この条件項目が挙げられる。既に固定した背景条件や目標達成の内部過程の全てを追加供給要件へ数えない。特定の法的命令者を補わず、世界全体の論理的必要条件、実際の供給、達成の確実性や即時性とは区別する。要件を持たない個体では偽とし、全要件の項目をこの関係の範囲に含める。'),
    'h232f': (f'[a d] {FAMILY}', ['requirement', 'reference'],
              'この条件項目が同じ基準で求める状態の、閉じた内容族の記述。対象と基準を族へ渡して内容を特定する。項目名や供給者名だけを返さず、条件の現実の充足を含意しない。同じ内容の別名の項目を許す。'),
    'h232g': (f'[a a {FAMILY} a d] c', ['mention', 'author', 'referent_family', 'scope', 'context'],
              '同じ著者・文章範囲・提示文脈におけるこの表現箇所が、指定した二引数の閉じた内容族を指すという解釈。対象・基準へ適用して得る状態や過程の種類の参照であり、現実の個体や出来事の生起をそれだけで断言しない。一引数の性質を指す既存ibbdenotesと同じ参照の規約を、対象と基準を保持する族へ適用する。'),
    'h232h': ('[] a', [], '固定原文kant-1784:u0012第一文全体[0,214)の箇所。'),
    'h232i': ('[] a', [], '同第一文[52,60)、要件として挙げるFreiheitの箇所。'),
    'h232j': ('[] a', [], '同第一文[71,130)、最も無害な種類と限定する名詞句の箇所。'),
    'h232k': ('[] a', [], '同第一文[145,214)、理性の全事柄での公的使用によって自由を特定する箇所。'),
    'h232l': ('[] a', [], '固定原文kant-1784:u0011第四文[886,896)、先行するAufklärungの箇所。'),
    'h232m': ('[] a', [], '固定原文kant-1784:u0012第一文[3,20)、dieser Aufklärungの照応箇所。'),
    'h232n': ('[] a', [], '同第一文[0,61)、自由以外は要求されないと述べる主節の箇所。'),
}
MEANINGS = {
    'r2sp': '同じ目標・対象・基準で、指定の焦点内容を求める要件項目が少なくとも一つあり、全ての要件項目の内容がその焦点内容と一致する。全個体を量化し、自由の種類だけに量化範囲を狭めない。要件が空の場合や、別の内容の追加要件を排除する。同じ内容の重複項目は許し、条件と目標は実行しない。',
    'r2sq': '同じ公衆・基準での啓蒙r2lnを目標とする供給要件について、r2spの唯一の内容を全事柄の公的使用の自由r2slへ固定する。比較の最小性r2snが指す自由と同じ記述を使う。自由を他の条件と取り替えず、現実の自由・成功・無条件の十分性を追加しない。',
    'r2sr': '前段落と同じ非空の公衆範囲h222eの全てについて、同じ基準でr2sqの要件限定を述べる内容。読者の独立した理性使用への能力変化という先行目標r2lnを保持する。',
    'r2ss': '同じ参照状況で要件限定r2srと害の最小比較r2soを合わせる第一文の内容。要件に挙げる自由と比較される自由はどちらもr2slである。両内容の公衆範囲を別々に選び直さない。',
    'r2st': '二箇所が異なり、同じ著者・範囲・文脈で同じ二引数内容族を指し、本文順序が正向きのみで、後者が前者の指示を説明する。既存rytと同じ構成を二引数の参照族へ適用し、説明関係ibbclarifiesと順序ueを再利用する。',
    'r2su': '自由を挙げる箇所、最も無害な種類とする箇所、公的使用と説明する箇所を、同じr2slを指す二段の説明として接続する。und zwarの限定とnämlichの特定化を、別の自由への交替や単なる本文順序と区別する。害の最小性そのものはr2soで構成する。',
    'r2sv': '先行する第四段落のAufklärungと当文dieser Aufklärungが、同じ著者・現文の照応範囲・文脈で同じ目標族r2lnを指すことと、正向きのみの本文順序を要求する。啓蒙の現実の達成や、前後の句を別の意味へ解釈することを認めない。',
    'r2sw': '第一文全体のr2ss、主節の要件限定r2sr、自由の最小性r2soを対応する箇所と著者へ帰属する。自由の説明r2suと啓蒙の照応r2svを接続し、前段落の遅い到達r2ptと要件の限定を自立的使用h4lという共通観点で対比する。前段落末尾から当文への順序を保ち、世界内容を実行しない。',
}
LIMITS = [
    'Zu dieser Aufklärungは、前段落で述べた同じ公衆の啓蒙へ向けた要件の話題設定と読む。目標はr2lnの同じ期間・起点・内部の作用・自立的使用能力の広がりを持ち、単なる知識増加や個別の出来事名へ替えない。',
    'nichts erfordert als Freiheitを、固定した背景の下で啓蒙を進めるために供給を求める要件の内容がこの自由だけだと読む。自由の要件を肯定し、自由とは別の供給要件を否定する。目標達成に内在する人の思考活動や既存の背景まで不要とする主張ではない。',
    'この要件の読みは、自由なしには全ての世界で啓蒙が論理的に不可能という必然命題でも、自由があれば例外なく即座に成功するという十分条件でもない。前段落のほぼ避けがたいという留保や遅い到達の記述を消さない。既存h222sの足りる条件の提示だけで、当文の要件の存在と他要件の排除を代用しない。',
    '自由の種類の比較と全事柄での公的使用は直前二版の構成を保持する。害ゼロ・唯一の最小・実際の自由付与・現実の発話や成功・全住民同時の変化は要求しない。全比較範囲と同じ評価背景の外部からの適切な供給は解釈上の責任として残る。',
    'aberは、先行段落のゆっくりとしか到達できないという困難の叙述と、供給要件は自由だけという提示の対比として読む。先行する遅さや革命の限界の否定、二内容の論理的矛盾、全ての通常予想の反転を加えない。',
    'und zwarとnämlichは同じ自由を順に限定・説明する提示として読む。最小性を帰属する内容、同じ自由内容への参照、後句が前句を説明する関係、本文順序を別々に保持する。接続語ごとに真偽未展開の専用演算子を置かない。',
    '第一文214文字・183非空白文字の意味判断は、固定転写・原刊484頁・既存の意味規約を通読したアシスタントの判断である。有限モデル検査は結合と区別の検査であり、同義性の自動証明や独立査読ではない。第五段落の後続文と二作品全体は未完。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return f'''
d r2sp[subject a goal {FAMILY} focus {FAMILY} reference d
 required h[a {FAMILY} a d] c content h[a d] {FAMILY}] c[
 w[g item a[w[c[v required][v item v goal v subject v reference]][e[c[v content][v item v reference]][v focus]]]][
 f item a[y[c[v required][v item v goal v subject v reference]][e[c[v content][v item v reference]][v focus]]]]
].
d r2sq[public a reference d] c[
 k r2sp[v public r b[p r2ln] r b[p r2sl] v reference p h232e p h232f]
].
d r2sr[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][k r2sq[v public v reference]]]]
]].
d r2ss[] e[b reference[w[t[k r2sr[]][v reference]][t[k r2so[]][v reference]]]].
d r2st[first a second a author a referent {FAMILY} scope a context d] c[
 w[u[e[v first][v second]]][
 w[k h232g[v first v author v referent v scope v context]][
 w[k h232g[v second v author v referent v scope v context]][
 w[k ue[v first v second v context]][
 w[u[k ue[v second v first v context]]][k ibbclarifies[v first v second v author v scope v context]]
 ]]]]
].
d r2su[] c[
 w[k r2st[k h232i[] k h232j[] k wa[] r b[p r2sl] k h232h[] k hzp3[]]][
 k r2st[k h232j[] k h232k[] k wa[] r b[p r2sl] k h232h[] k hzp3[]]]
].
d r2sv[] c[
 w[u[e[k h232l[]][k h232m[]]]][
 w[k h232g[k h232l[] k wa[] r b[p r2ln] k h232h[] k hzp3[]]][
 w[k h232g[k h232m[] k wa[] r b[p r2ln] k h232h[] k hzp3[]]][
 w[k ue[k h232l[] k h232m[] k hzp3[]]][u[k ue[k h232m[] k h232l[] k hzp3[]]]]
 ]]]
].
d r2sw[] c[
 w[k hzon[k h232h[] k wa[] r b[k r2ss[]] k hzp3[]]][
 w[k hzon[k h232n[] k wa[] r b[k r2sr[]] k hzp3[]]][
 w[k hzon[k h232j[] k wa[] r b[k r2so[]] k hzp3[]]][
 w[k r2su[]][w[k r2sv[]][
 w[k h222q[k h232h[] k wa[] k h226h[] r b[k r2pt[]] k h232n[] r b[k r2sr[]] r[p h4l] k hzp3[]]][
 k ue[k h227w[] k h232h[] k hzp3[]]
 ]]]]]]
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
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2sw', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2sw']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='enlightenment_requirement_sentence_under_explicit_reading', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/freedom-comparison-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
