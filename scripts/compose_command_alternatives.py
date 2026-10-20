"""Compose drill, payment and belief as alternatives to the same prohibited activity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-heard-prohibition.noema'
PARENT_BASIS = 'data/heard-prohibition-basis-v1.json'
FULL = 'examples/v016/kant-command-alternatives.noema'
CORE = 'examples/v016/command-alternatives-core.noema'
BASIS = 'data/command-alternatives-basis-v1.json'
ANNOTATIONS = 'data/command-alternatives-identifiers-v1.json'
PRIMITIVES = {
    'h232x': ('[a a d] c', ['practice', 'pattern', 'point'],
              'この活動は、指定された遂行の型を身につけ保つために反復して練習する性質を持つ。単にその型と似た動作、偶然の反復、説明を聞くだけとは区別する。現在の生起・参加者・熟達の達成は別に結ぶ。'),
    'h232y': ('[a d] c', ['pattern', 'reference'],
              '同じ基準で、この遂行の型は、号令への応答、隊形の動作、武器の扱いなど、軍務のための身体的教練に当たる。一般的な体操・算術の練習・実戦の成功そのものとは区別する。全種目の同時実施、特定の国の教範や兵器を指定しない。'),
    'h232z': ('[d a a] c', ['reference', 'payer', 'transfer'],
              '同じ基準と本人に対し、この支払指示で履行対象として指定する取引の活動記述に当たる。別件の贈与・自分への移動・要求と無関係な少額移転を代用しない。取引の同定は要求された対象・受取先・額等の文脈に従うが、その成立や正当な義務までは含意しない。特定の金額や税制を本文へ補わず、実行の成否で候補を選別しない。'),
    'h233a': ('[d a] c', ['reference', 'teaching'],
              'この基準の呼びかけで信仰の対象としている宗教的な教えの全範囲に属する。真だと解釈者が認めた教えや実際に受け入れられた教えだけを選ばず、無関係な日常の推測を対象にしない。特定の教派や原文にない個々の教義は供給しない。'),
    'h233b': ('[a d] i[e]', ['teaching', 'reference'],
              '同じ基準でこの教えが述べる内容の閉じた記述。表題や語形だけではなく、何が信じられるかの内容を保持する。記述の参照からその教えの真理や信仰の成立を導かない。'),
    'h233c': ('[a i[e] d] c', ['person', 'content', 'point'],
              'この本人がこの状況で、記述された同じ内容を真として受け入れる信念を持つ。単に文を知ること、引用、賛成したふり、好ましいという感情、仮定としての採用とは区別する。内容の真理、証拠による正当化、他者との同意、疑いの全不在を要求せず、内容の脱引用はしない。宗教的な対象範囲は呼び出し側で指定する。'),
}
MEANINGS = {
    'r2tg': '基準で軍事教練に分類する同じ遂行の型について、同じ本人が参加する練習の活動が評価点で生起する内容族。dg・dfと練習h232x・型h232yを結び、別人の実施や一般的な反復だけでは成立しない。熟達や実戦の実行は要求しない。',
    'r2th': '基準で同じ本人への指示の対象とされた取引について、その本人から別の受取人への同じ価値媒体の移転と媒体の受容を既存rfa/ti/tjで結ぶ内容族。無関係な取引を納付の代わりに使わず、移転の成功を求めるが、要求の正当性や特定の額を補わない。',
    'r2ti': '基準で固定した非空の宗教的教えの全てについて、同じ本人が評価点でその教えの同じ内容h233bを真として受け入れる。各教えの真理や現在の発話、教えごとの別人へのすり替えは要求しない。',
    'r2tj': '同じ本人・基準・評価点について、既存r2taの言語的検討の不実行と、引数で渡す肯定的内容の成立を合わせ、それを命令型の発話へ包む。禁止だけでも肯定側だけでもなく、否定の作用域を肯定側へ広げない。発話の成立・規範・実際の履行は別である。',
    'r2tk': 'r2tjの肯定側を同じ基準の軍事教練r2tgへ固定し、言語的検討をせず教練を行うよう求める発話の族を作る。',
    'r2tl': 'r2tjの肯定側を同じ基準の支払いr2thへ固定し、言語的検討をせず指定の支払いを行うよう求める発話の族を作る。',
    'r2tm': 'r2tjの肯定側を同じ基準の信仰r2tiへ固定し、言語的検討をせず指定された宗教的内容を信じるよう求める発話の族を作る。命令が信念を実際に生じさせるという因果は加えない。',
}
LIMITS = [
    '第五段落[274,426)の三つの命令に共通する否定内容と、exercirt/bezahlt/glaubtの肯定内容を構成する。将校・財務担当官・聖職者という発信者の役割、sagtの省略、sondernによる代替の提示、前文の方面への対応、著者帰属と三文全体の通読は残る。',
    'exercirtはこの軍事的な文脈で、本人が軍事教練を行うという読みとする。他人を訓練すること、身体的な動作の能力があるだけ、全ての軍務や実際の戦闘、訓練の成功まで同一視しない。練習と軍事的な遂行の型は意味規約で分類し、その全ての身体・軍事概念を定義展開したという主張ではない。',
    'bezahltはこの指示で指定する取引への支払いと読む。既存の価値移転と受容を再利用し、無関係な贈与や自分への移動では成立させない。金額・税目・期限・全債務の清算は原文から補わないが、文脈上の対象取引の同定を空白のまま成功としない。',
    'glaubtは文脈で指される宗教的教えを真として受け入れるという信仰の読みを採る。宗教的信頼の全側面や全てのglaubenの語義をこの構成へ還元しない。教えの範囲は同じ基準に固定し、内容が実際に真かどうかによって信念を判定しない。',
    '命令の内容を評価する検査と、その命令を引用して提示する検査を分ける。前者は指定行動・信念と検討の不実行を評価するが、後者から実行や信念、教義の真理、法的・道徳的な義務を導かない。',
    '三つの命令内容を追加した部分構成であり、現在の65主張と14区間・第五段落先頭二文232文字の判断を保持する。新しい著者主張や意味確認済み文字数は追加しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2tg[reference d] h[a] e[i[person a][b point[
 g practice a[g pattern a[
 w[k dg[v practice v point]][w[k df[v person v practice v point]][
 w[k h232x[v practice v pattern v point]][k h232y[v pattern v reference]]
 ]]]
 ]
]]].
d r2th[reference d] h[a] e[i[person a][b point[
 g transfer a[g receiver a[g medium a[
 w[k h232z[v reference v person v transfer]][
 k rfa[v person v receiver v transfer v medium v point p ti p tj]]
 ]]]
]]].
d r2ti[reference d] h[a] e[i[person a][b point[
 w[g teaching a[k h233a[v reference v teaching]]][
 f teaching a[y[k h233a[v reference v teaching]][
 k h233c[v person k h233b[v teaching v reference] v point]
 ]]]
]]].
d r2tj[reference d alternative h[a] e] h[a] f[i[person a][j m[b point[
 w[t[c[k r2ta[v reference]][v person]][v point]][t[c[v alternative][v person]][v point]]
]]]].
d r2tk[reference d] h[a] f[k r2tj[v reference k r2tg[v reference]]].
d r2tl[reference d] h[a] f[k r2tj[v reference k r2th[v reference]]].
d r2tm[reference d] h[a] f[k r2tj[v reference k r2ti[v reference]]].
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
    basis = dict(status='three_command_contents_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/heard-prohibition-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
