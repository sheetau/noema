"""Connect independent choices and command-guided compliance to the current text."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts import compose_choice_permissions as choice
from scripts import compose_scoped_obedience as obedience

PARENT = 'examples/v016/kant-role-commands.noema'
PARENT_BASIS = 'data/role-commands-basis-v1.json'
FULL = 'examples/v016/kant-free-choice-obedience.noema'
CORE = 'examples/v016/free-choice-obedience-core.noema'
BASIS = 'data/free-choice-obedience-basis-v1.json'
ANNOTATIONS = 'data/free-choice-obedience-identifiers-v1.json'
PRIMITIVES = {
    'h233p': ('[a d a] c', ['source', 'reference', 'recipient'],
              '同じ発信者が同じ基準場面で「あなた方」と呼びかける全宛先の範囲。受領・許可・実行・服従した人だけに狭めず、発信者を替えればその発信者の呼びかける範囲を照合する。人と複数性は発話への接続時に別に検査する。'),
    'h233q': ('[a a d] c', ['person', 'topic', 'reference'],
              'この本人が同じ基準場面で自ら論じたいと望む話題の全範囲。実際に論じた、許可された、安全な、正しい話題だけを選ばず、望む話題がない場合も許す。将来の選択や別人の希望を混ぜない。'),
    'h233r': ('[a a d] c', ['person', 'extent', 'reference'],
              'この本人が同じ基準場面で自ら望む議論の量・程度の全範囲。長さ・回数・詳しさ等、文脈で同定する程度指定を指し、許可された量や実際の遂行量とは区別する。数値単位や有限の上限を原文へ補わず、本人の希望が空の場合も許す。'),
    'h233s': ('[a a d] a', ['person', 'activity', 'reference'],
              '同じ本人の同じ活動候補について、基準で固定した議論の話題指定。複合的な話題も一つの指定として扱える。活動の主題であることはh227zへ別に接続し、実行済みの活動や許可済みの話題へ付け替えない。'),
    'h233t': ('[a a d] a', ['person', 'activity', 'reference'],
              '同じ本人の同じ活動候補について、基準で固定した議論の量・程度の指定。実際に達成した量の測定値ではなく、その量だけ論じるという候補の内容上の指定であり、許可結果に合わせて小さな量へ付け替えない。'),
    'h233u': ('[a a d] a', ['person', 'activity', 'reference'],
              '同じ本人が同じ議論の候補を行う際の立場の参照。許可と反対要求を同じ立場へ照合するために固定する。本文のこの発言だけから公的使用の学識者に限定せず、実行・役職保持・命令の正当性を参照だけで導かない。'),
    'h233v': ('[a a d a] c', ['source', 'person', 'reference', 'role'],
              '同じ出所に対するこの本人の服従について、基準場面で扱う政治的・市民的な職務や立場の全範囲。私的な好みや無関係な他者の命令を含めず、不都合な要求がある立場を事後に除かない。正当な命令かどうかの判定とは分ける。'),
    'h233w': ('[a a d a] c', ['source', 'person', 'reference', 'item'],
              '同じ出所・本人・基準場面について、服従の対象要求を記述する記録項目の範囲。要求の全体を尽くすこと、記録の真実性や履行は合成定義で別に検査し、記録を消して要求を消したことにはしない。'),
    'h233x': ('[a] a', ['item'], '同じ要求記録の対象となる本人の立場。実際にその立場の要求であることは別に照合する。'),
    'h233y': ('[a] a', ['item'], '同じ要求記録の対象行為。別の行為の実行で履行を代用せず、要求の照合と内容評価へ同じ参照を渡す。'),
    'h233z': ('[a] i[h[a a] e]', ['item'],
              '同じ要求記録の閉じた行為内容の記述。第一引数は本人、第二引数は対象行為であり、原語の文や題名だけで代用しない。要求への照合と履行評価で同じ記述を使う。'),
    'h234a': ('[a] c', ['item'], '同じ要求記録の極性。真は指定内容を満たす要求、偽はその不成立を求める要求。要求の存在や履行の真偽とは別である。'),
    'h234b': ('[a a a a i[h[a a] e] c d d] c',
              ['source', 'person', 'role', 'activity', 'content', 'polarity', 'reference', 'point'],
              'この本人が評価点で、同じ出所・立場・行為・記述・極性の基準時の要求を、自分の当該遂行を導く指示として受け入れ、それに従って遂行を調整する。偶然同じ結果になっただけ、別要求を理由にした行動とは区別する。要求への道徳的賛同、無批判な信念、唯一の動機、要求の正当性や実際の履行成功はこの関係だけからは導かない。'),
}
IMPORTED = {n: m for n, m in choice.basis()['definitions'].items()}
IMPORTED.update({n: m for n, m in obedience.basis()['definitions'].items() if n in ('rtw', 'rtx', 'rty', 'rtz')})
MEANINGS = IMPORTED | {
    'r2tz': '同じ本人が自分の理性を用いる言語的検討の活動候補ca/h232pであり、その活動が指定された同じ話題h233sを扱うh227z。実行・許可・能力は候補の選別に使わない。',
    'r2ua': '同じ本人・活動・基準の許可対象を既存zzqの実行内容へ固定した閉じた記述。活動を実際に行ったことは要求しない。',
    'r2ub': '指定した一人について、希望する話題h233qと程度h233rの全組合せを既存rtuで扱う。同じ活動候補・役割・実行記述に同じ出所の積極的許可があり、反対要求がない。許可の評価点と希望の基準を分ける。',
    'r2uc': '同じ出所・本人・基準の全選択要求について、同じ立場・行為・内容・極性を本人が遂行の指示として受け入れ調整するh234b。要求の存在・全体の網羅・実際の履行は別条件である。',
    'r2ud': '固定した要求の全体の網羅rtx、記録の妥当性と評価点での履行rtw、同じ要求に従って遂行を調整するr2ucを合わせる。偶然の一致や抜けた要求を許さず、評価点で要求が消えたことを基準時の要求の消滅としない。',
    'r2ue': '同じ出所・基準で固定した全宛先についてr2ubの話題と量の自由選択への許可を要求する内容。宛先の範囲は実際に許可・実行した人から選ばない。空や単数の呼びかけを本文へ採用しない条件は発話側で結ぶ。',
    'r2uf': '同じ出所・基準で固定した全宛先についてr2udの要求に従う履行を求める内容。各宛先の範囲を許可の側と共用するが、実際の許可の成立をこの履行の条件に加えない。',
    'r2ug': '基準を固定し、出所を引数に、その出所の全宛先へのr2ueの許可方針を述べる発話の族を作る。命令形räsonnirtを許容的な働きとして読むための、許可内容の明示であり、議論の実行を強制しない。',
    'r2uh': '基準を固定し、出所を引数に、その出所の全宛先へr2ufの服従を求める命令の族を作る。許可を述べる発話とは別の型を保ち、引用から履行や正当性を導かない。',
}
LIMITS = [
    '第五段落[427,536)の括弧文のうち、引用内の話題・量の自由選択と服従の内容を構成する依存群である。唯一のHerrの役割と世界の量化範囲、発話者との同一性、複数宛先の発話、aberの対照、括弧の挿入、著者帰属と一文全体の通読は次の統合に残す。新しい意味確認済み文字数は追加しない。',
    'räsonnirtは共通する理拠に基づく言語的な検討として既存ca/h232pへ結ぶ。この発言の命令形は、各宛先に望む量と話題で論じることを許す働きと読む。全員に現実の議論を義務づける命令とは読まない。発言の許可内容を述べる構成であり、発言だけで法的に有効な許可が発生する一般理論を加えない。',
    '本人が選ぶ話題と程度の全組合せに候補を要求し、同じ範囲の全候補を許す。希望が空なら議論を強制せず、望まない活動や望む以上の量への許可はここからは導かない。願いが後に変わった全時点を無条件に量化せず、基準場面の同じ希望を保って許可を評価する。',
    '活動候補・話題・程度は内容上の指定であり、実行能力や実際の遂行ではない。程度の連続量・単位の一般理論は主張せず、原文に数値的な上限を付けない。有限検査の二話題・二程度は意味の全領域ではない。',
    'gehorchtは同じ統治上の出所に対し、政治的・市民的な立場での対象要求を欠かさず履行し、その要求を自分の遂行の指示として扱う読みを採る。従来rtyだけの内容一致にh234bを加え、偶然の一致を区別する。要求への道徳的賛同・内心の無批判・唯一の動機・制裁は補わない。',
    '要求の網羅性rtxは全ての型に合う閉じた内容記述を量化する。有限評価器による全域評価は拒否し、有限の記述を代入した診断を全域の証明としない。内容引用は可能であり、網羅性を省いて型制約を回避しない。',
    '許可を述べる発話と服従の指令を分け、前者の真理条件に後者の実際の履行を加えない。本文のaberによる対照は未接続であり、単なる二内容の用意だけで一文全体を完成とはしない。',
    '服従の内容は記述の脱引用を含むため、閉じた発話族の引用には段階1を使う。既存f2の段階0引数へ強引に渡さず、後続の発話接続でも段階を保持する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def requirements():
    return ('v source v person v reference '
            'i[role a][k h233v[v source v person v reference v role]] '
            'i[item a][k h233w[v source v person v reference v item]] '
            'p h233x p h233y p h233z p h234a p h7a')


def definitions():
    args = requirements()
    return choice.definitions() + obedience.definitions() + '''
d r2tz[person a activity a reference d] c[
 w[k ca[v person v activity v reference]][w[k h232p[v activity v reference]][
 k h227z[v activity k h233s[v person v activity v reference] v reference]]]
].
d r2ua[person a activity a reference d] i[h[a a] e][r[p zzq]].
d r2ub[source a person a reference d] e[
 k rtu[i[recipient a][e[v recipient][v person]]
 p h233q p h233r p r2tz p h233s p h233t v reference
 v source p h233u p r2ua p h7a p h7b]
].
d r2uc[source a person a reference d point d] c[
 f item a[y[k h233w[v source v person v reference v item]][
 k h234b[v source v person k h233x[v item] k h233y[v item]
 k h233z[v item] k h234a[v item] v reference v point]
 ]]
].
d r2ud[source a person a reference d] e[b point[
 w[k rtx[''' + args + ''']][w[k rtw[''' + args + ''' v point]][
 k r2uc[v source v person v reference v point]]]
]].
d r2ue[source a reference d] e[b point[
 f person a[y[k h233p[v source v reference v person]][t[k r2ub[v source v person v reference]][v point]]]
]].
d r2uf[source a reference d] e[b point[
 f person a[y[k h233p[v source v reference v person]][t[k r2ud[v source v person v reference]][v point]]]
]].
d r2ug[reference d] h[a] f[i[source a][j s[k r2ue[v source v reference]]]].
d r2uh[reference d] h[a] f[i[source a][j m[k r2uf[v source v reference]]]].
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
    basis = dict(status='free_choice_and_command_guided_obedience_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 reused_libraries=[choice.LIBRARY, obedience.LIBRARY], limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/role-commands-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
