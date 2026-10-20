"""Bind the three attributed commands to appointed roles and the heard calls."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-command-alternatives.noema'
PARENT_BASIS = 'data/command-alternatives-basis-v1.json'
FULL = 'examples/v016/kant-role-commands.noema'
CORE = 'examples/v016/role-commands-core.noema'
BASIS = 'data/role-commands-basis-v1.json'
ANNOTATIONS = 'data/role-commands-identifiers-v1.json'
PRIMITIVES = {
    'h233d': ('[a d] c', ['institution', 'point'],
              'この状況で、この制度的集団は政治的共同体の軍務を担う軍事組織である。単に武器を持つ集団、武装した警察、競技団体とは区別する。現に戦闘中であることやその政治的正当性を要求しない。'),
    'h233e': ('[a a d] c', ['role', 'institution', 'point'],
              '同じ軍事組織・状況の階級制度で、この役職は、兵卒・下士官とは区別される将校の任官階級に位置付く。単に他人へ号令できることや教練を指導した実績では足りない。特定の現代国家の階級表、現在の指揮行為、貴族身分、能力や任官の正当性は付けない。保持者と有効な任用は別に結ぶ。'),
    'h233f': ('[a d] c', ['institution', 'point'],
              'この状況で、この制度は領邦・国家の収入を管理する公的な財務行政の機関である。私人の家計、商店の売上管理、単なる金融会社とは区別する。特定の税制や収入源、行政の正当性は指定しない。'),
    'h233g': ('[a a d] c', ['role', 'institution', 'point'],
              '同じ財務行政機関のこの役職には、領邦・国家の収入の管理を担当する参事・官吏としての行政上の責務がある。個々の納付を窓口で受け取る人、私的な会計係、名誉称号だけとは区別する。唯一の長官・大臣であること、特定の階級や現在の徴収行為は指定しない。'),
    'h233h': ('[a a a i[h[a] e] i[h[a] e] d] c',
              ['utterance', 'speaker', 'recipient', 'negative_condition', 'positive_condition', 'point'],
              '同じ発話で同じ話者が、この宛先への否定的指示で退ける行為に代えて何をするかとして、指定された肯定的内容を提示する。二つの記述は同じ宛先へ適用する内容族であり、単なる話題の併置や時間的な前後とは区別する。否定・肯定それぞれの命令内容、発話の成立、内容の実行は別に結び、この関係から両内容の論理的矛盾や命令の正当性を導かない。'),
    'h233i': ('[] a', [], 'u0012の呼び声が由来する社会的な方面のうち軍務の方面。個々の話者や発話そのものとは別の参照。'),
    'h233j': ('[] a', [], 'u0012の呼び声が由来する社会的な方面のうち公的財務の方面。個々の話者や発話そのものとは別の参照。'),
    'h233k': ('[] a', [], 'u0012の呼び声が由来する社会的な方面のうち宗教の方面。個々の話者や発話そのものとは別の参照。'),
    'h233l': ('[a a a i b[e] i b[e] d] c',
              ['example_node', 'author', 'general_node', 'general_content', 'example_content', 'context'],
              '同じ著者・提示文脈で、指定された箇所の一般的な叙述を、この箇所の具体的な内容によって例示する。どの一般叙述をどの内容で具体化するかを保持する。二内容の真理、単なる隣接、普遍命題の論理的証明や一般叙述の全事例の列挙とは区別する。'),
    'h233m': ('[] a', [], 'u0012の原文[274,327)で将校の命令を述べる第三文の文章箇所。'),
    'h233n': ('[] a', [], 'u0012の原文[328,377)で財務担当官の命令を述べる第四文の文章箇所。'),
    'h233o': ('[] a', [], 'u0012の原文[378,426)で聖職者の命令を述べる第五文の文章箇所。'),
}
MEANINGS = {
    'r2tn': '同じ人・役職・機関・状況について、人であること、役職保持hzwn、有効な制度的任用hzxf、機関の領域と同機関の役職分類を結ぶ。別の役職の保持や別の機関の任用を混ぜず、現在の職務実行を要求しない。',
    'r2to': 'r2tnの機関領域を軍事組織h233d、役職分類を将校の任官階級h233eに固定した、任用された将校の読み。',
    'r2tp': 'r2tnの機関領域を公的財務行政h233f、役職分類を収入管理の担当参事・官吏h233gに固定したFinanzrathの読み。単なる徴税窓口の人へ狭めない。',
    'r2tq': 'r2tcの同じ発信者・呼び声・観察者・基準・評価点に、固定された複数宛先のそれぞれへの肯定内容を含む命令とその取得・理解を接続する。同じ話者が同じ宛先へ禁止に代わる肯定内容を提示するh233hを要求する。命令族と肯定内容族は閉じた記述を引数とし、実行や信念を脱引用しない。',
    'r2tr': '叙述上の現在と評価点を一致させ、指定した同じ社会的方面に位置付く話者が指定役割を持ち、その人の同じ呼び声r2tqがある。前文と同じ方面範囲h232s・源泉分類h232t・観察者・基準を使う。全役職者の全称命題や唯一の話者という読みは採らない。',
    'r2ts': '著者の叙述上の現在に、軍務の方面の将校がr2tkの禁止と教練の命令を述べる具体例。肯定内容r2tgと命令r2tkの同じ基準への引用適用を対応させる。',
    'r2tt': '同じ著者・現在に、公的財務の方面の財務担当官がr2tlの禁止と支払いの命令を述べる具体例。原文で省略されたsagtも同じr2tr/r2tqで構成する。',
    'r2tu': '同じ著者・現在に、宗教の方面の聖職者spがr2tmの禁止と信仰の命令を述べる具体例。既存spの任用と公的な宗教奉仕の責務を保持する。',
    'r2tv': '指定文の具体例を同じ著者・第五段落の提示文脈へ帰属し、先行する諸方面の呼び声r2teを具体化する例示関係と本文の順序を結ぶ。世界での役職者の存在や命令実行を無帰属で断定しない。',
    'r2tw': '将校の第三文にr2tvを適用する。前の第二文からの本文順序を保つ。',
    'r2tx': '財務担当官の第四文にr2tvを適用する。第三文からの本文順序を保つ。',
    'r2ty': '聖職者の第五文にr2tvを適用する。第四文からの本文順序を保つ。',
}
LIMITS = [
    '三つの定冠詞付き単数役職名は、著者が周囲の社会的方面を代表させる人物例として提示する読みを採る。世界に唯一の将校・財務担当官・聖職者、各職全員の発言、特定の実名人物を補わない。語りの場面の中の存在例であり、発言の史料的実在の証明ではない。',
    '役職保持と制度的任用は既存hzwn/hzxfを使い、軍事組織・将校の階級、公的財務機関・参事の責務は明示した語彙的関係で分類する。これらの軍制・行政概念を物理的関係だけに還元したという主張ではない。Geistlicheは既存spと同じ読みであり、特定教派の資格を追加しない。',
    'Finanzrathは領邦・国家の収入管理を担当する官吏・参事と読む。同時代に近いAdelungのKämmerer第三義の説明を参照し、単なる徴税人、現代の財務大臣、私的な会計係へ置き換えない。',
    'sagtは後二文にも省略して反復される。前文の聴覚的な呼び声の例として、同じ役職者の発話を同じ著者が聴き、複数宛先それぞれへの命令を理解する。著者自身が命令の宛先であること、各宛先の受領や理解は付けない。',
    'nicht ... sondern ...は、同じ人が言語的検討を行わず、代わりに教練・支払い・信仰をするよう求める指示と読む。共通禁止と肯定内容の連言に加え、話者が代替として提示する関係h233hを明示する。実際の不実行・実行や義務の正当性を命令の提示から導かない。',
    '教練・支払い・信仰はcommand-alternatives版の解釈を保持する。教練は同じ本人の軍事的な練習、支払いは指定取引の受容された価値媒体の移転、信仰は固定した宗教的教えの同じ内容への非事実的な信念である。',
    '三つの方面・役割・内容は対応づけるが、三人を必ず別人とする不等式、方面の排他的所属、三方面だけで全社会を尽くす制限は補わない。各具体例は前文の方面に属し、その一般叙述を例示する。',
    '三文の意味判断は原刊484頁、固定転写、明示した採用解釈に対する通読である。テストによる自動同義性証明ではなく、続く一人の君主の発言、第五段落全体と二作品全体は未完である。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2tn[person a point d domain h[a d] c classification h[a a d] c] c[
 w[k aa[v person]][g role a[g institution a[
 w[k hzwn[v person v role v point]][w[k hzxf[v person v role v institution v point]][
 w[c[v domain][v institution v point]][c[v classification][v role v institution v point]]
 ]]]]]
].
d r2to[person a point d] c[k r2tn[v person v point p h233d p h233e]].
d r2tp[person a point d] c[k r2tn[v person v point p h233f p h233g]].
d r2tq[speaker a call a observer a reference i[d] positive i[h[d] h[a] e] command i[h[d] h[a] f] point d] c[
 w[k r2tc[v speaker v call v observer v reference v point]][
 f recipient a[y[k h232u[v call s[v reference] v recipient]][
 w[k f2[v call v recipient v recipient o a[v command][v reference] v point]][
 w[k h6e[v call v observer v recipient o a[v command][v reference] v point]][
 w[k h6g[v observer v recipient o a[v command][v reference] v point]][
 k h233h[v call v speaker v recipient o a[r[p r2ta]][v reference] o a[v positive][v reference] v point]
 ]]]
 ]]]
].
d r2tr[observer a quarter a reference i[d] role h[a d] c positive i[h[d] h[a] e] command i[h[d] h[a] f] point d] c[
 w[e[s[v reference]][v point]][w[k h232s[v observer s[v reference] v quarter]][
 g speaker a[g call a[
 w[k h232t[v quarter v speaker s[v reference]]][
 w[c[v role][v speaker v point]][k r2tq[v speaker v call v observer v reference v positive v command v point]]
 ]]]
 ]]
].
d r2ts[] e[b point[k r2tr[k wa[] k h233i[] r[k h232v[]] p r2to r[p r2tg] r[p r2tk] v point]]].
d r2tt[] e[b point[k r2tr[k wa[] k h233j[] r[k h232v[]] p r2tp r[p r2th] r[p r2tl] v point]]].
d r2tu[] e[b point[k r2tr[k wa[] k h233k[] r[k h232v[]] p sp r[p r2ti] r[p r2tm] v point]]].
d r2tv[node a content i b[e] previous a] c[
 w[k hzon[v node k wa[] v content k h232o[]]][
 w[k h233l[v node k wa[] k h232w[] r b[k r2te[]] v content k h232o[]]][
 k ue[v previous v node k h232o[]]
 ]]
].
d r2tw[] c[k r2tv[k h233m[] r b[k r2ts[]] k h232w[]]].
d r2tx[] c[k r2tv[k h233n[] r b[k r2tt[]] k h233m[]]].
d r2ty[] c[k r2tv[k h233o[] r b[k r2tu[]] k h233n[]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + s[0] + '.' for n, s in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    new_statements = [dict(kind='assert', body=dict(kind='call', symbol=n, arguments=[]))
                      for n in ('r2tw', 'r2tx', 'r2ty')]
    doc['statements'] = statements + new_statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2tw', 'r2tx', 'r2ty']), statements=new_statements)
    decls = {d['name']: d for d in added}
    basis = dict(status='role_commands_under_explicit_reading', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/command-alternatives-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
