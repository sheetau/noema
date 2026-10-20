"""Close contextual scope and case references before attributing the conditional."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_public_incitation import FIELDS

PARENT = 'examples/v016/kant-public-incitation.noema'
PARENT_BASIS = 'data/public-incitation-basis-v1.json'
FULL = 'examples/v016/kant-reversal-attribution.noema'
CORE = 'examples/v016/reversal-attribution-core.noema'
BASIS = 'data/reversal-attribution-basis-v1.json'
ANNOTATIONS = 'data/reversal-attribution-identifiers-v1.json'
PROVIDERS = {
    'guardians': ('h223x', 'a', '先行作用を担う後見人群'),
    'former': ('h223y', 'j[a]', '先行作用の実際の参加後見人の全列'),
    'agitators': ('h223z', 'j[a]', '扇動条件で評価する後見人たちの全列'),
    'earlieract': ('h224a', 'a', '公衆への先行作用の行為'),
    'earlier': ('h224b', 'd', '先行作用とその結果を評価する時点'),
    'incitingact': ('h224c', 'a', '扇動条件で評価する提示行為'),
    'incited': ('h224d', 'd', '扇動とその動機的結果を評価する局面'),
    'pressure': ('h224e', 'a', '後の強制として問題にする行為の参照。生起自体は含意しない'),
    'participants': ('h224f', 'j[a]', '公衆側の行為参加と扇動の受け手を評価する全対象者列'),
    'history': ('h224g', 'i[h[d] c]', '期間評価の履歴範囲の閉じた記述'),
    'before': ('h224h', 'i[h[d d] c]', '同じ履歴の先行関係の閉じた記述'),
    'first': ('h224i', 'i[d]', '後の強制の開始として問題にする時点の閉じた記述'),
    'last': ('h224j', 'i[d]', '保持期間の終点として問題にする時点の閉じた記述'),
    'anchor': ('h224k', 'd', '保持期間全体とその因果を評価する時点'),
    'pressurename': ('h224l', 'i[a]', '同じ予定圧力行為の閉じた参照。元の行為との一致はr2nbで検査する'),
}
PRIMITIVES = {
    'h223v': ('[a i[h[a] e] d] j[a]', ['group', 'state', 'context'],
              'この文脈で、記述された性質を同じ集団へ分配的に述定する際の、関連する構成員の全対象範囲。集団の全成員と必ず同じではないが、結果が成立した者だけを選んだり、都合の悪い構成員を後から外したりしない。実際の性質の成立・因果・集団所属はこの参照だけから導かず、呼出側で検査する。'),
    'h223w': ('[a d a] c', ['public', 'reference', 'case'],
              '先頭二文と同じ公衆・参照文脈について、先行する後見人からの作用を背景に第三文前半を述べる対象の事例範囲。事例は実際または仮定の経過を識別し、後の扇動や強制の成否を見て選び直さない。行為・人物・期間の各参照は同じ事例から供給する。各事例の関係の真理は合成内容で別に評価する。'),
    'h224m': ('[] a', [], '固定原文kant-1784:u0011第三文の前半[449,699)の文章箇所。公衆と後見人の逆向きの作用と扇動条件を含む。内容はr2nfで構成する。Besonders/selbstと頚木の比喩の提示はこの帰属だけでは尽くさない。'),
}
for field, (name, result, meaning) in PROVIDERS.items():
    PRIMITIVES[name] = ('[a] ' + result, ['case'],
                        '同じ固定事例の' + meaning + 'を指す局所参照。参照先の意味と各関係の成立は合成定義で検査し、原文内容の代替述語にはしない。')
MEANINGS = {
    'r2nc': '同じ集団・性質・文脈において、指定された人々の列と、文脈で先に固定された全対象範囲h223vが同じ成員を持つ。両列は非空で重複のない人の集団内部分集合とし、列順の違いは許す。一部の成功者だけへの縮小や、範囲外の追加を拒否する。',
    'r2nd': '同じ公衆のmpの完全な構成員列が、先頭二文で使うh6tの同じ参照文脈の成員範囲と一致する。非空・重複なし・全員が人であることも要求する。公共的な言説の宛先としての分類はr2laで別に検査する。',
    'r2ne': '同じ公衆・固定事例から、先行作用・扇動・強制・保持の全参照を供給し、r2nbへ渡す。先行する被作用者は同じ公衆・未成熟bf・先行時点の全対象範囲h223vに固定する。後見人群、扇動者、参加者、各行為、履歴と時点を、条件の結果に合わせて存在量化で選び直さない。',
    'r2nf': '参照文脈の非空の公衆範囲h222eの全対象について、公衆の分類と構成員の一致を要求し、その非空の全事例h223wにr2neが成立する内容。先頭二文と同じ公衆範囲を引き継ぎ、一事例が成功しただけでは全事例の主張を満たさない。',
    'r2ng': '第三文前半の同じ箇所h224m・著者wa・段落提示文脈hzp3に、閉じた段階3の内容記述r2nfをhznreportで帰属する。帰属時に世界の先行作用・扇動・強制を実行評価しない。前半の関係内容についての帰属であり、未接続の比喩・際立てや後半まで確認済みとはしない。',
}
LIMITS = [
    '集団への分配的な述定の全対象範囲を、同じ公衆・性質・先行時点の文脈で先に固定する。全人口の一律の未成熟や割合の数値を追加せず、非空の成功者を任意に選ぶことも許さない。範囲が原文の文脈に適切かは、構文や有限解釈だけでは証明できない。',
    '一般的な条件付き記述として、同じ公衆に関係する非空の全事例を量化する。事例は先行する後見人の作用を背景として固定し、扇動や後の強制の成否から選別しない。先行の関係は各事例の内容で評価し、後の強制は扇動条件の後件に保つ。',
    '人物・行為・時点・履歴の参照供給は内容の意味述語ではない。r2nb以下の既存構成が関係内容を評価する。閉じた行為・時点・履歴の記述は束縛変数を捕捉せず、圧力行為名は元の参照との一致を検査する。',
    '帰属として本文に一文を追加するが、内容を著者に帰属したことから哲学的主張の真理を認定しない。先頭二文と同じ公衆範囲h222eと分類r2laを使い、mpとh6tの成員を照合する。',
    '前半の頚木の照応とBesonders/selbstの提示、後半の偏見の植え付け・害・生み手または先任者に関係する報復、第三文全体の統合と通読は残る。既存59文、十三の全単位判断、先頭二文382非空白文字を保持し、第三文の確認済み文字数は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    affected = 'k h223v[v public r[p bf] k h224b[v case]]'
    args = ' '.join('v public' if n == 'public' else affected if n == 'affected'
                    else 'k ' + PROVIDERS[n][0] + '[v case]' for n, _ in FIELDS)
    return '''
d r2nc[group a affected j[a] state i[h[a] e] context d] c[
 w[k r2mo[v group v affected]][w[k r2mo[v group k h223v[v group v state v context]]][
 f person a[w[
 y[k hg[v affected v person]][k hg[k h223v[v group v state v context] v person]]
 ][y[k hg[k h223v[v group v state v context] v person]][k hg[v affected v person]]]]
 ]]
].
d r2nd[public a reference d] c[
 w[k r2mo[v public k mp[v public]]][
 f person a[w[
 y[k hg[k mp[v public] v person]][k h6t[v public v person v reference]]
 ][y[k h6t[v public v person v reference]][k hg[k mp[v public] v person]]]]
 ]
].
d r2ne[public a reference d case a] c[
 w[k h223w[v public v reference v case]][
 w[k r2nc[v public ''' + affected + ''' r[p bf] k h224b[v case]]][
 k r2nb[''' + args + ''']]]
].
d r2nf[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][
 w[k r2la[v public v reference]][w[k r2nd[v public v reference]][
 w[g case a[k h223w[v public v reference v case]]][
 f case a[y[k h223w[v public v reference v case]][k r2ne[v public v reference v case]]]
 ]]]
 ]]
 ]
]].
d r2ng[] c[
 k hznreport[k h224m[] k wa[] r d[k r2nf[]] k h224m[] k hzp3[]]
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
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2ng', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2ng']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='conditional_case_scope_and_closed_attribution_partial',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS,
                 definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2])
                             for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-incitation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
