"""Represent heard prohibitions without converting quoted commands into norms."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_public_first_sentence import replace_calls

PARENT = 'examples/v016/kant-enlightenment-requirement.noema'
PARENT_BASIS = 'data/enlightenment-requirement-basis-v1.json'
FULL = 'examples/v016/kant-heard-prohibition.noema'
CORE = 'examples/v016/heard-prohibition-core.noema'
BASIS = 'data/heard-prohibition-basis-v1.json'
ANNOTATIONS = 'data/heard-prohibition-identifiers-v1.json'
CONTEXT_MAPPING = {'r2su': 'r2sx', 'r2sv': 'r2sy', 'r2sw': 'r2sz', 'hzp3': 'h232o'}
PRIMITIVES = {
    'h232o': ('[] d', [], '固定原文kant-1784:u0012の第五段落の提示文脈。前段落専用のhzp3と区別する。先行箇所をこの文脈で振り返ることはできるが、報告された発声・聴覚経験の場面や実際の現在時刻とは同一視しない。'),
    'h232p': ('[a d] c', ['activity', 'reference'],
              '同じ基準で、この活動記述が、事柄について理拠を述べ検討し、問いや異論を論ずる言語的な活動に当たる。単なる音声、従順な復唱、結果のない冗談や全ての内心の思考を一律にこの範囲へ含めない。公的・職務内のいずれも分類でき、実行・正しさ・成功・社会的許可は別条件。本人自身の理性使用caと組み合わせてräsonnirenの採用読解を構成する。'),
    'h232q': ('[a a d] c', ['observer', 'event', 'point'],
              'この本人が同じ場面で、この出来事からの音を聴覚を通じて知覚する。別の出来事の音、書面を読んだだけ、伝聞や想像だけとは区別する。発話内容の理解、賛同、本人が宛先であることはこの関係だけでは要求しない。'),
    'h232r': ('[a d] c', ['event', 'point'],
              'この発声は、声を上げて相手へ届くよう呼びかける様式を持つ。音量の数値や怒り・暴力・喉の極限の叫びを必須にせず、単なる黙読・表示と区別する。発声の生起、発信者、受信・理解は別に結ぶ。'),
    'h232s': ('[a d a] c', ['observer', 'reference', 'quarter'],
              '同じ観察者と基準文脈で、周囲の呼び声を見渡す対象となる社会的な方面の全範囲に属する。ここでの四方は幾何的な全方位や世界の全員ではなく、後続の軍務・財務・宗教などに例示される諸方面として読む。都合のよい発声が見つかった方面だけを事後に残さない。'),
    'h232t': ('[a a d] c', ['quarter', 'speaker', 'reference'],
              '同じ基準で、この話者がその社会的な方面からの声として位置づく。単なる近接や宛先の所属ではなく、声の出所をその方面へ結ぶ。複数方面に属する話者を許す。権限・正当性・実際の発声・全構成員の賛同は含意しない。'),
    'h232u': ('[a d a] c', ['call', 'reference', 'recipient'],
              '同じ呼びかけと基準文脈で、二人称の集団的な宛先として指す全対象者の範囲に属する。実際に受領・理解・服従した人だけに狭めず、呼び声を聞く観察者と宛先を同一視しない。複数性と人の条件は呼び出し側で検査する。'),
    'h232v': ('[] d', [], '第五段落第二文で著者がNun höre ichと現在の経験として提示する場面。叙述上の現在の場面参照であり、現在の実行日時や特定の日付・場所を捏造しない。場面内の生起と知覚は合成定義で別に要求する。'),
    'h232w': ('[] a', [], '固定原文kant-1784:u0012第二文[215,273)の文章箇所。'),
}
MEANINGS = {
    'r2sx': '第一文の自由の二段説明r2suを、その内容・箇所・著者を保って第五段落の提示文脈h232oへ接続する。旧定義と旧判断は変更しない。',
    'r2sy': '第一文の啓蒙への照応r2svを第五段落の提示文脈h232oへ接続する。先行箇所h232lと同じ目標r2lnは保ち、前段落そのものの提示文脈を上書きしない。',
    'r2sz': '第一文の内容r2ss・二つの部分内容・説明・照応・対比・順序を第五段落の提示文脈で帰属し直す。命題内容は旧r2swと同じで、提示文脈と二つの説明用定義だけを置き換える。',
    'r2ta': '基準で固定した同じ人の自らの理性使用caかつ言語的な検討h232pに当たる活動記述が非空で、その全てが評価点で実行されないという内容族。範囲を実行の有無で切り詰めない。公的役割・読者世界の分類までは要求せず、職務内の検討も対象にできる。',
    'r2tb': '閉じた基準名を保持し、同じ宛先にr2taの活動を行わないよう求める命令型の発話を作る。命令を発していないという否定、活動がないという平叙、現実に不実行が成立したこと、正当な規範の成立とは異なる。',
    'r2tc': '同じ人の発信者による同じ生起する呼び声について、固定した複数の宛先全員にr2tbの禁止を示す。観察者が同じ呼び声を聴覚で捉え、各宛先に関する同じ発話記述を受領・理解する。観察者が命令の宛先であることや、宛先側の受領・服従は要求しない。',
    'r2td': '基準名の指示が評価点と一致し、同じ観察者・基準で固定した複数の社会的方面の全てについて、そこに位置づく話者の呼び声r2tcが存在する。別の方面の声で埋めず、全員が呼ぶことや同時刻・同じ発声の共有は要求しない。',
    'r2te': '著者waを観察者に固定し、叙述上の現在h232vを基準名とするr2tdの内容。原文の私が聞くという視点を保持する。帰属された叙述内での知覚であり、特定の史実の日付・発言記録まで主張しない。',
    'r2tf': '第二文の呼び声の内容r2teを、同じ著者と第五段落の文脈へ帰属する。第一文の自由の要件r2ssとの対比と本文順序を結ぶ。著者自身が禁止を命じたことや実際に禁止が正当な規範として成立することは導かない。',
}
LIMITS = [
    '前回の第一文では前段落専用hzp3を提示文脈へ渡していた。この版は第五段落h232oを別に置き、第一文の提示だけを再構成して読み直す。旧定義・証拠は保存し、文脈を変えた主張63に旧選択ハッシュをそのまま引き継がない。',
    'räsonnirt nichtを、本人の理性によって理拠を述べ検討・異論を論ずる活動をしないよう求める命令として読む。単なる雑談や、結果の出ない議論という後代の軽蔑的な語義へ限定しない。公的使用だけに先に限定せず、後続の職務内の例にも同じ禁止内容を使える。',
    '否定は命令内容の活動実行にかかる。話者が命令しないこと、宛先が既に活動していないこと、禁止の正当性、権限、制裁、実際の服従は加えない。命令を引用する経路では活動実行の入力は未知のままでよい。',
    'höreは聴覚による知覚と発話内容の取得・理解を結ぶ読みとする。観察者は著者であるが、命令の宛先であるとは限らない。rufenは声を上げる呼びかけの様式とし、怒りや叫びの数値的な強度は補わない。',
    'von allen Seitenは文脈上の複数の社会的方面からの声を広く示す表現と読む。幾何的な無限の方向や世界中の全員、各方面の全構成員を量化しない。方面の範囲は成否から選別せず、各方面に一つ以上の同じ内容の呼び声を要求する。',
    '二人称複数の命令は、各呼び声が集団的な宛先に向ける禁止として読む。固定した複数の宛先それぞれに同じ否定内容を適用し、一人だけの服従や受領で範囲を縮めない。文中の私と宛先のあなた方を混同しない。',
    'Nunは著者が叙述上の現在の場面へ注意を移す読みとし、aberは先の自由の要件の提示と周囲の禁止の声との対比とする。第一文の主張を撤回せず、歴史的な全世界での自由不在や二内容の論理的矛盾までは加えない。',
    '第二文の通読は固定転写と原刊484頁に基づくアシスタントの意味判断であり、自動的同義性証明ではない。続く将校・徴税官・聖職者と一人の君主の命令の具体例、段落全体、二作品全文は未完。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def corrected():
    result = []
    for old, new in list(CONTEXT_MAPPING.items())[:3]:
        row = replace_calls(deepcopy(parent().entries[old]['declaration']), CONTEXT_MAPPING)
        row['name'] = new
        result.append(row)
    return result


def definitions():
    return '''
d r2ta[reference d] h[a] e[i[person a][b point[
 w[g act a[w[k ca[v person v act v reference]][k h232p[v act v reference]]]][
 f act a[y[w[k ca[v person v act v reference]][k h232p[v act v reference]]][u[k cg[v person v act v point]]]]]
]]].
d r2tb[reference d] h[a] f[i[person a][j m[c[k r2ta[v reference]][v person]]]].
d r2tc[speaker a call a observer a reference i[d] point d] c[
 w[k aa[v speaker]][w[k aa[v observer]][
 w[k dg[v call v point]][w[k f3[v speaker v call v point]][
 w[k h232r[v call v point]][w[k h232q[v observer v call v point]][
 w[g first a[g second a[w[u[e[v first][v second]]][
 w[k h232u[v call s[v reference] v first]][k h232u[v call s[v reference] v second]]]]]][
 f recipient a[y[k h232u[v call s[v reference] v recipient]][
 w[k aa[v recipient]][
 w[k f2[v call v recipient v recipient o a[r[p r2tb]][v reference] v point]][
 w[k h6e[v call v observer v recipient o a[r[p r2tb]][v reference] v point]][
 k h6g[v observer v recipient o a[r[p r2tb]][v reference] v point]
 ]]]
 ]]
 ]]]]]]]
].
d r2td[observer a reference i[d] point d] c[
 w[e[s[v reference]][v point]][
 w[g first a[g second a[w[u[e[v first][v second]]][
 w[k h232s[v observer s[v reference] v first]][k h232s[v observer s[v reference] v second]]]]]][
 f quarter a[y[k h232s[v observer s[v reference] v quarter]][
 g speaker a[g call a[w[k h232t[v quarter v speaker s[v reference]]][
 k r2tc[v speaker v call v observer v reference v point]
 ]]]
 ]]
 ]]
].
d r2te[] e[b point[k r2td[k wa[] r[k h232v[]] v point]]].
d r2tf[] c[
 w[k hzon[k h232w[] k wa[] r b[k r2te[]] k h232o[]]][
 w[k h222q[k h232w[] k wa[] k h232h[] r b[k r2ss[]] k h232w[] r b[k r2te[]] r[p h4l] k h232o[]]][
 k ue[k h232h[] k h232w[] k h232o[]]
 ]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    primitives = ''.join('r ' + n + s[0] + '.' for n, s in PRIMITIVES.items())
    doc = parse(format_graph(doc, 'compact') + primitives)
    doc['declarations'].extend(corrected())
    doc = parse(format_graph(doc, 'compact') + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[63]['body']['symbol'] == 'r2sw'
    statements[63]['body']['symbol'] = 'r2sz'
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2tf', arguments=[]))
    doc['statements'] = statements + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2sz', 'r2tf']), statements=[statements[63], statement])
    decls = {d['name']: d for d in added}
    basis = dict(status='heard_prohibition_under_explicit_reading', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/enlightenment-requirement-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
