"""Bind individual effects to the public, with one event per causal outcome."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-thinking-reform.noema'
PARENT_BASIS = 'data/thinking-reform-basis-v1.json'
FULL = 'examples/v016/kant-public-revolution.noema'
CORE = 'examples/v016/public-revolution-core.noema'
BASIS = 'data/public-revolution-basis-v1.json'
ANNOTATIONS = 'data/public-revolution-identifiers-v1.json'
PRIMITIVES = {
    'h226z': ('[a i[h[a] e] d] b', ['public', 'result', 'reference'],
              '同じ公衆と基準文脈について、指定結果がその公衆へ広がったと呼ぶ最低比率。結果の種類ごとに基準を分け、候補・革命・実際の成功者数から選び直さない。0と1の間で厳密に超える読みを利用側で検査する。能力取得用のh222jの値を自動流用せず、固定の過半数や全員という数値を原文へ追加しない。'),
    'h227a': ('[a d] a', ['public', 'reference'],
              'この公衆について政治的変化を述べる文脈上の共同体。公的議論の宛先と政治的共同体を区別して指す。国名・特定国家・現実の革命は指定せず、政治秩序と集団行為の関係は合成内容で要求する。'),
    'h227b': ('[a] i[a]', ['public'],
              '同じ公衆の閉じた参照記述。引用された個人結果に公衆を固定するために使い、元の公衆との一致は呼出側で検査する。'),
    'h227c': ('[d] i[d]', ['reference'],
              '同じ基準文脈の閉じた参照記述。結果内容へ固定した範囲と期間を渡すために使い、元の基準との一致は呼出側で検査する。'),
    'h227d': ('[a d a d] c', ['public', 'reference', 'act', 'candidate'],
              '同じ公衆・基準で、候補経過における政治的変化の原因として検討する全活動。結果の成否や革命への該当によって先に選別しない。先頭文と同じ候補範囲h222kの内側で用い、活動の種類と生起は別に要求する。'),
    'h227e': ('[a d a d] a', ['public', 'reference', 'act', 'candidate'],
              '同じ比較活動と候補について、変更を目指す旧政治秩序の参照。現に実施されていること・革命への該当は別に検査する。'),
    'h227f': ('[a d a d] a', ['public', 'reference', 'act', 'candidate'],
              '同じ比較活動と候補について、変更目標となる提案政治秩序の参照。旧秩序との相違と変更目標の実在を別に検査し、提案の実施成功は参照から導かない。'),
    'h227g': ('[a d a d] j[a]', ['public', 'reference', 'act', 'candidate'],
              '同じ比較活動と候補における政治的な集団行為の全参加者列。公衆の全読者列とは区別する。人・共同体所属・実際の参加・集団への帰属をr2qgで検査する。'),
    'h227h': ('[] a', [], '固定原文kant-1784:u0011第五文前半[907,1101)、Durchからzu Stande kommenまでの文章箇所。中核の二結果の帰属に用い、様相語・対比の提示と後半はまだ尽くさない。'),
}
MEANINGS = {
    'r2qr': '同じ公衆・基準の全読者列と結果別の広がり基準をr2lbへ渡す。変化した人は、同じ活動が同じ候補で同じ記述結果をその人へ生み、実際にその結果が成立する人に限る。別活動・別候補の個人効果を合算しない。',
    'r2qs': '先頭文と同じ公衆・基準・候補の有効な時間枠について、指定した前後点が枠に属し、前が後に先行し、後が将来の起点より後にある。個々の人の完了点の同一性は要求しない。',
    'r2qt': '同じ公衆の政治的共同体に現に実施される個人的専制と圧迫から、同じ人がr2qeで離脱する結果内容。担い手・秩序・圧迫行為・過程・前後点を存在量化するが、全ての関係は同じ証人に束縛し、r2qsの共通枠を使う。特定の君主名や全員同じ圧迫行為を補わない。',
    'r2qu': '同じ公衆・基準の時間枠内で、同じ人にr2qpの思考様式の改革過程がある結果内容。判断領域の基準は同じreferenceに固定し、人ごとに異なる過程と前後点を許す。',
    'r2qv': '基準と公衆を引数として固定した、r2qtの個人結果の族。閉じた適用で引用するための関数。',
    'r2qw': '基準と公衆を引数として固定した、r2quの個人結果の族。閉じた適用で引用するための関数。',
    'r2qx': '先頭文と同じ候補範囲と、同じ公衆・基準・活動の供給を使う。同じ政治的共同体、旧秩序、提案、参加者でr2qgの革命を判定し、その生起を要求する。結果の成功はこの活動分類に含めない。',
    'r2qy': '全候補の時間枠と閉じた参照の一致を確認する。同じ革命・候補による政治的離脱の広がりr2qrが可能であり、思考様式の改革の広がりr2qrはどの革命・候補でも生じないという二結果の対比。個人の改革が一例でもあれば偽とする読みや、各人ごとの別革命の成功を集める読みとは区別する。',
    'r2qz': '先頭四文と同じ非空の公衆範囲h222eを量化し、各対象の公衆分類r2la・全構成員照合r2ndとr2qyを要求する閉じた内容。全人口の同時変化や、成功しやすい公衆だけへの限定を補わない。',
    'r2ra': '第五文前半の同じ箇所・著者wa・段落文脈hzp3へ、r2qzの段階3の閉じた内容を帰属する。第四文からの本文順序を保持し、帰属時に哲学的主張を現実の真理として実行しない。',
}
LIMITS = [
    '第五文を先行する公衆の自己啓蒙の議論として読む。集団の結果は、同じ革命に因果的に由来する個人の結果が、同じ全読者中で結果別の文脈基準を超えて広がることとする。全員・過半数・固定比率は補わない。',
    'niemalsの否定範囲を、公衆の思考様式が改革されたと呼ぶ広がりを革命が生むことへ置く。革命をきっかけに一人が考え直す例まで絶対に不可能とする強い別読解は採らない。採用した範囲と閾値の適切さは明示的な解釈要件で、有限検査だけでは原文の唯一性を証明しない。',
    '離脱の対象となる専制秩序は同じ政治的共同体に実施されるものとし、圧迫・動機・終結関与を同じ人と過程へ結ぶ。革命が全員の全ての従属を消す、提案秩序が成功する、元の思考様式が永久に消えるとはしない。',
    '第一結果の可能性と第二結果の経路の不在を先に本文へ帰属する。vielleicht wohlの提示、aber/sondernの対比、後半の新旧の偏見・誘導・予測は未接続であり、前半を含め第五文の意味確認済み分量は増やさない。',
    '全読者と候補範囲・期間枠は先頭文から継承する。政治的共同体は公衆の参照と区別する。各人の結果は異なる完了点を許すが、集計される因果は同じ革命と候補に固定する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    history = 'i[point d][k h7q[k h222g[v public v reference] v candidate v point]]'
    before = 'i[earlier d later d][k ic[v earlier v later v candidate]]'
    desc = lambda name: 'o a[r[p ' + name + ']][k h227c[v reference] k h227b[v public]]'
    return '''
d r2qr[public a reference d act a candidate d result i[h[a] e]] c[
 k r2lb[k h222i[v public v reference] k h226z[v public v result v reference]
 i[person a][k h6t[v public v person v reference]]
 i[person a][w[k g3[v act v person v result v candidate]][t[c[s[v result]][v person]][v candidate]]]
 p aa]
].
d r2qs[public a reference d candidate d first d last d] c[
 w[k hzne[k h222g[v public v reference] k h222h[v public v reference v candidate] v candidate]][
 w[k h7q[k h222g[v public v reference] v candidate v first]][
 w[k h7q[k h222g[v public v reference] v candidate v last]][
 w[k ic[v first v last v candidate]][
 k ic[k h222h[v public v reference v candidate] v last v candidate]
 ]]]]
].
d r2qt[reference d public a person a] e[b candidate[
 g ruler a[g despotic a[g oppressor a[g oppressive a[g pressure a[g process a[g first d[g last d[
 w[k r2qs[v public v reference v candidate v first v last]][
 w[k h226t[v despotic k h227a[v public v reference] v first]][
 k r2qe[v person v ruler v despotic v oppressor v oppressive v pressure v process
 v first v last ''' + history + ' ' + before + ''']
 ]]
 ]]]]]]]]
]].
d r2qu[reference d public a person a] e[b candidate[
 g process a[g first d[g last d[
 w[k r2qs[v public v reference v candidate v first v last]][
 k r2qp[v person v process v reference v first v last ''' + history + ' ' + before + ''']
 ]
 ]]]
]].
d r2qv[reference d public a] h[a] e[i[person a][k r2qt[v reference v public v person]]].
d r2qw[reference d public a] h[a] e[i[person a][k r2qu[v reference v public v person]]].
d r2qx[public a reference d act a candidate d] c[
 w[k h222k[v public v reference v candidate]][
 w[k h227d[v public v reference v act v candidate]][
 w[k dg[v act v candidate]][
 k r2qg[v act k h227a[v public v reference]
 k h227e[v public v reference v act v candidate] k h227f[v public v reference v act v candidate]
 k h227g[v public v reference v act v candidate] v candidate]
 ]]]
].
d r2qy[public a reference d] c[
 w[e[s[k h227b[v public]]][v public]][w[e[s[k h227c[v reference]]][v reference]][
 w[f candidate d[y[k h222k[v public v reference v candidate]][
 k hzne[k h222g[v public v reference] k h222h[v public v reference v candidate] v candidate]
 ]]][
 w[g act a[g candidate d[w[k r2qx[v public v reference v act v candidate]][
 k r2qr[v public v reference v act v candidate ''' + desc('r2qv') + ''']
 ]]]][
 u[g act a[g candidate d[w[k r2qx[v public v reference v act v candidate]][
 k r2qr[v public v reference v act v candidate ''' + desc('r2qw') + ''']
 ]]]]
 ]]]]
].
d r2qz[] e[b reference[
 w[g public a[k h222e[v public v reference]]][
 f public a[y[k h222e[v public v reference]][
 w[k r2la[v public v reference]][w[k r2nd[v public v reference]][k r2qy[v public v reference]]]
 ]]]
]].
d r2ra[] c[
 w[k hznreport[k h227h[] k wa[] r d[k r2qz[]] k h227h[] k hzp3[]]][
 k ue[k h226h[] k h227h[] k hzp3[]]]
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
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2ra', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2ra']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='public_revolution_outcome_core_attributed_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/thinking-reform-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
