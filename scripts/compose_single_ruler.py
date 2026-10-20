"""Attribute the parenthetical permission and obedience to exactly one ruler."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-free-choice-obedience.noema'
PARENT_BASIS = 'data/free-choice-obedience-basis-v1.json'
FULL = 'examples/v016/kant-single-ruler.noema'
CORE = 'examples/v016/single-ruler-core.noema'
BASIS = 'data/single-ruler-basis-v1.json'
ANNOTATIONS = 'data/single-ruler-identifiers-v1.json'
PRIMITIVES = {
    'h234c': ('[a d] c', ['community', 'reference'],
              '基準で語られる同時代の世界に属する政治的共同体の全範囲。自国・欧州・発言記録が見つかった国・好ましい政策を採る国だけに狭めない。過去と未来の全統治者、別の可能世界を混ぜず、地球に一つの政府しかないことを意味しない。'),
    'h234d': ('[a a d] c', ['role', 'community', 'point'],
              '同じ政治的共同体と状況の統治制度における役職の全範囲。この集合の中で保持者と上下関係を照合する。君主より上の役職や比較不能の役職を都合よく除かず、私的な会社だけの組織表とは区別する。'),
    'h234e': ('[a a a d] c', ['higher', 'lower', 'community', 'point'],
              '同じ政治的共同体の同じ統治制度・状況で、第一役職が第二役職より上位に位置付く関係。直接の上司だけでなく推移的な上位関係を与える。実際の発令・服従、制度の正当性は含めず、厳密な順序かどうかは合成定義で検査する。'),
    'h234f': ('[a a d] c', ['role', 'community', 'point'],
              'この政治的共同体の制度で、この役職にある単独の個人が、その人自身の公的権威において統治の最終的な決定と執行を統べる立場にある。委任された一部門の管理者、私的な所有者、単なる敬称とは区別する。ここでのHerrを君主的な統治者とする語彙的な読みであり、世襲・終身・貴族身分・神授・制度の正当性は一律に要求しない。保持者・任用・最高位・唯一の保持は別に検査する。'),
    'h234g': ('[a a a i b[h[a] f] d] c',
              ['utterance', 'recipient', 'subject', 'message_family', 'point'],
              'この発話行為が、この宛先へ、指定対象に適用した同じ発話族の内容と発話の働きを提示する。既存f2と同じ提示関係を、段階0の記述評価を内側に含みうる段階1の閉じた発話族記述へ拡張する。生起・話者は別に結ぶ。提示から受領・理解・賛同・内容の真理・実行・法的な効力を導かず、記述を脱引用しない。'),
    'h234h': ('[a a a a i b[h[a] f] i b[h[a] f] d] c',
              ['utterance', 'speaker', 'recipient', 'subject', 'first_message', 'second_message', 'point'],
              '同じ発話で同じ話者が同じ宛先へ、指定対象について、第一の発話に続けて第二の発話を対照的な留保として提示する。先行内容を撤回せず後続の制約も保持する働きであり、順序を保持する。単なる併置、第一の否定、二内容の論理的矛盾、第二の実行が第一の真理の必要条件であることとは区別する。各内容の提示は別に要求する。'),
    'h234i': ('[] a', [], '第五段落u0012の[427,536)で、ただ一人のHerrの発言を挿入する括弧文の文章箇所。'),
    'h234j': ('[] a', [], '第五段落u0012の[274,426)で将校・財務担当官・聖職者の三つの声を列挙する文章ブロック。'),
    'h234k': ('[a a a d] c', ['aside_node', 'author', 'anchor_node', 'context'],
              '同じ著者がこの文脈で、主たる叙述の指定箇所に関連する補足として、この箇所を括弧による挿入の位置に提示する。単に二文が隣接すること、引用符、発話者の私的な独白とは区別する。補足の真理、対照の内容、本文順序は別に結ぶ。'),
}
MEANINGS = {
    'r2ui': '同じ人・役職・共同体・評価点について、役職保持hzwnと、その共同体の制度による有効な任用hzxfを結ぶ。同じ役職を別の共同体で持つだけでは代用しない。',
    'r2uj': '指定された共同体の君主的な統治職h234fについて、同じ本人が既存hzfnの最高役職の唯一の保持者で、任用と職務の委託cfを持つ。役職の全範囲・厳密な順序・他の全役職より上であることを既存rm2/rexで検査する。世界で唯一の統治者とはしない。',
    'r2uk': '固定した同時代の世界に含まれる政治的共同体h234cの少なくとも一つで、この本人がr2ujの統治者である。同じ人物による複数共同体の統治を許し、発言の有無で比較範囲を縮めない。',
    'r2ul': '同じ人の同じ生起する発話について、固定された複数の人の宛先全員に、同じ基準の許可方針r2ugと服従の指令r2uhを段階1の記述で提示する。発話族の対象引数は話者自身であり、規範の出所を宛先や別人へすり替えない。同じ二内容の順序付きの対照的留保h234hを要求する。受領・理解・聴覚知覚・叫び方はsagtだけから補わない。',
    'r2um': '指定した範囲の中で指定述語を満たす者が存在し、その述語も満たす他の範囲内対象は全て同一である。他の範囲内対象の存在そのものを排除しない、存在と唯一性の合成。',
    'r2un': '基準名が指す叙述上の現在と評価点を一致させ、その世界の統治者r2ukのうちr2ulの発言をする者がr2umの意味でちょうど一人である。発話行為を一つだけにせず、同じ人が複数回述べることを許す。',
    'r2uo': 'この作品の叙述上の現在h232vを基準名に固定した、ただ一人の統治者が許可と服従を述べるr2unの内容。特定の実名人物への同定は加えない。',
    'r2up': '直前の三文に帰属した、将校・財務担当官・聖職者の命令内容r2ts/r2tt/r2tuを同じ評価点でまとめた内容。対照の先行側を新しい別の主張へ置き換えない。',
    'r2uq': '同じ基準で本人自身の理性を用いる言語的検討に当たる活動が、評価点で本人により実行される内容族。三者の禁止と統治者の容認を対照する共通観点として引用し、現実に実行されたことは要求しない。',
    'r2ur': '括弧文の内容r2uoを同じ著者・第五段落の文脈へ帰属し、先の三者の内容r2upとの対照、括弧での補足挿入、先行文からの本文順序を合わせる。著者が実際に命令したことや世界の政策・履行の真理を無帰属で断定しない。',
}
LIMITS = [
    'Herrは政治的共同体の君主的な統治者として読む。後のAA8:40–41でMonarch、Staatsoberhaupt、Fürstの話に同じ発言が現れる文脈を参照する。この箇所の中に原文にない固有名・世襲・終身・特定の国制を補わない。',
    'Nur ein einzigerは、この同じ発言をする統治者がちょうど一人であるという焦点の読みを採る。世界の全統治者が一人しかいないことではなく、他の統治者がこの発言をしないことを要求する。無発言者や別の発言をする統治者は存在でき、同じ一人の発言回数は制限しない。',
    'in der Weltの範囲は、叙述上の現在における世界の政治的共同体全体へ固定する。欧州や自国、著者が直接発言を聞いた範囲へ狭めない。全時代・全可能世界へは広げない。原文の唯一性の主張を著者へ帰属するのであり、その歴史的な真偽をこの構成だけで証明しない。',
    '君主的な役職の分類と政治的な共同体・役職の範囲は語彙的関係として明示する。最高役職の保持だけで国家や主権を定義済みとはせず、同じ共同体での有効な任用と単独者の公的な最終統治の立場を接続する。制度の道徳的正当性は追加しない。',
    'sagtは、同じ話者が同じ発話で複数宛先全員へ許可の方針と服従の命令を示すことと読む。直前のrufenの例と異なり、括弧内の発言について著者の聴覚知覚・叫ぶ様式までは追加しない。発話族の対象は同じ話者なので、内容内の規範の出所と発話者が一致する。',
    '引用内のräsonnirtは望む話題と量で議論することの容認、gehorchtは同じ出所の要求を漏れなく履行し、その指示に従って遂行することへの命令と読む。free-choice-obedience版の内容を保持し、発話の引用時には許可・要求の全域・実行・意向を評価しない。',
    'aberは、議論への容認を撤回せずに服従の制約を続けて提示する対照的な留保と読む。許可を実際の服従に依存する条件文へ変えず、議論と服従が論理的に矛盾するともしない。',
    '括弧は直前の三つの禁止の声に対する補足的な対照を挿入するものとして構成する。論じることの禁止と容認を共通観点で対照するが、三者の声を著者が撤回したという読みは加えない。',
    '括弧文の通読は原刊484頁、固定転写、明示した解釈に対するアシスタントの意味判断である。独立査読や同義性の自動証明ではない。第五段落の残りと二作品全体は未完である。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2ui[person a role a community a point d] c[
 w[k hzwn[v person v role v point]][k hzxf[v person v role v community v point]]
].
d r2uj[person a community a point d] c[
 g role a[w[k h234f[v role v community v point]][
 k hzfn[v person v role v community v point p h234d p r2ui p h234e]]]
].
d r2uk[person a reference d point d] c[
 g community a[w[k h234c[v community v reference]][k r2uj[v person v community v point]]]
].
d r2ul[speaker a call a reference i[d] point d] c[
 w[k aa[v speaker]][w[k dg[v call v point]][w[k f3[v speaker v call v point]][
 w[g first a[g second a[w[u[e[v first][v second]]][
 w[k h233p[v speaker s[v reference] v first]][k h233p[v speaker s[v reference] v second]]]]]][
 f recipient a[y[k h233p[v speaker s[v reference] v recipient]][
 w[k aa[v recipient]][
 w[k h234g[v call v recipient v speaker o a[r b[p r2ug]][v reference] v point]][
 w[k h234g[v call v recipient v speaker o a[r b[p r2uh]][v reference] v point]][
 k h234h[v call v speaker v recipient v speaker
 o a[r b[p r2ug]][v reference] o a[r b[p r2uh]][v reference] v point]
 ]]]
 ]]
 ]]]]
].
d r2um[scope h[a] c predicate h[a] c] c[
 g person a[w[c[v scope][v person]][w[c[v predicate][v person]][
 f other a[y[w[c[v scope][v other]][c[v predicate][v other]]][e[v other][v person]]]
 ]]]
].
d r2un[reference i[d] point d] c[
 w[e[s[v reference]][v point]][
 k r2um[i[person a][k r2uk[v person s[v reference] v point]]
 i[person a][g call a[k r2ul[v person v call v reference v point]]]]]
].
d r2uo[] e[b point[k r2un[r[k h232v[]] v point]]].
d r2up[] e[b point[w[t[k r2ts[]][v point]][w[t[k r2tt[]][v point]][t[k r2tu[]][v point]]]]].
d r2uq[reference d] h[a] e[i[person a][b point[
 g activity a[w[k ca[v person v activity v reference]][
 w[k h232p[v activity v reference]][k cg[v person v activity v point]]]]
]]].
d r2ur[] c[
 w[k hzon[k h234i[] k wa[] r b[k r2uo[]] k h232o[]]][
 w[k h222q[k h234i[] k wa[] k h234j[] r b[k r2up[]] k h234i[] r b[k r2uo[]]
 o a[r[p r2uq]][r[k h232v[]]] k h232o[]]][
 w[k h234k[k h234i[] k wa[] k h234j[] k h232o[]]][
 k ue[k h233o[] k h234i[] k h232o[]]
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
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2ur', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2ur']), statements=[statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='single_ruler_parenthesis_under_explicit_reading', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/free-choice-obedience-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
