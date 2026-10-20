"""Compose motivated oppression and withdrawal from the same prior orders."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-public-slow-attainment.noema'
PARENT_BASIS = 'data/public-slow-attainment-basis-v1.json'
FULL = 'examples/v016/kant-political-withdrawal.noema'
CORE = 'examples/v016/political-withdrawal-core.noema'
BASIS = 'data/political-withdrawal-basis-v1.json'
ANNOTATIONS = 'data/political-withdrawal-identifiers-v1.json'
PRIMITIVES = {
    'h226i': ('[a a d] c', ['holder', 'order', 'point'],
              '同じ統治・指配の仕組みにおいて、この主体が他の当事者に従わせる決定を事実上統制している。肩書、助言するだけの立場、制度の正当性とは分ける。対象者がこの仕組みに服していることは別関係である。'),
    'h226j': ('[a a d] c', ['holder', 'order', 'point'],
              '同じ仕組みの決定で、この主体自身の裁量が決定的とされ、その個人の意思から独立した拘束的な基準や対抗的な統制によって抑えられない。この個人への裁量の集中を表し、一般的な監督役や単なる役職上位とは区別する。具体的な憲法や制度の法的正当性は主張しない。'),
    'h226k': ('[a a d] c', ['act', 'target', 'point'],
              '同じ行為が、優越的な圧力によって、この対象者の行動・生活上の選択や資源利用をその利益に反して制約し、負担を課す。単なる心理的な気分の重さ、助言、任意に選んだ負担とは区別する。行為の生起・担い手・実際の不利益への因果は別に結ぶ。'),
    'h226l': ('[a d] c', ['person', 'point'],
              'この本人が、文脈上の取得・取引において金銭・財などの物質的な純利益を得る。単なる気分の改善や他者だけの利益とは区別する。欲求や目的の内容として引用した場合、現実の利益の取得を要求しない。'),
    'h226m': ('[a i[h[j[a]] e] j[a] d] c', ['person', 'goal', 'roles', 'point'],
              '同じ本人の、指定した内容関数と順序付き引数で表された目標への欲求を、文脈上の妥当な限度を越えて強く優先し追求するものとして評価する。単なる利益や支配の希望を過度な執着と同一視せず、具体的な行為の目的・生起や目標の実現は別に要求する。数値閾値や臨床診断は含めない。'),
    'h226n': ('[a a d] c', ['order', 'target', 'point'],
              'この対象者が、指定した支配・服属の仕組みの下に実際に置かれ、その指配に従う関係にある。仕組みの性質・担い手の動機・法的正当性とは別の継続的な関係で、一行為の終了や担い手の交代だけから不成立としない。'),
    'h226o': ('[a a a d d] c', ['process', 'order', 'target', 'first', 'last'],
              '同じ過程で同じ対象者が指定した仕組みへの服属を拒み、その結び付きの終結に関与する。単なる自然消滅や、本人が関与しない別人による変更とは区別する。前後の服属状態、時間順、本人の参加と作用は別に検査する。'),
    'h226p': ('[a a d] c', ['act', 'order', 'point'],
              'この行為が、この同じ指配の仕組みを行使する行為として位置づけられる。単なる同時生起や別の仕組みでの私的行為を混ぜない。行為の生起、参加者、服属者、効果や正当性は別条件である。'),
}
MEANINGS = {
    'r2px': '同じ人が同じ生起行為に参加し、同じ引用目標と順序付き引数をそれ自体求め、その欲求が過度なものと評価され、同じ行為の計画・遂行でその目標を目指す。欲求・過度さ・行為目的を別人や別の目標から集めない。目標の実際の達成や唯一の動機であることは要求しない。',
    'r2py': '一位置の引数列[本人]に、その同じ本人の物質的利益取得h226lという目標内容を結ぶ。利益欲の内容として閉じて引用でき、実際の利益を要求するとは限らない。',
    'r2pz': '二位置の引数列[本人,指配の仕組み]に、その同じ本人が同じ仕組みを統制するh226iという目標内容を結ぶ。別の仕組みへの支配欲を流用しない。',
    'r2qa': '同じ仕組みについて、担い手が人であり、その人に事実上の決定統制h226iと、個人の裁量に抑制を欠くh226jがある。persönlicher Despotismを個人の恣意的支配と読む構成。統制だけ、肩書だけでは成立しない。',
    'r2qb': '同じ行為が同じ対象者を圧迫するh226kを満たし、同じ行為の生起r2pbが本人の不利益r2odへ因果的に寄与する。既存rqquの固定した二内容をdgとurへ展開し、同じhzieと合わせる。実際の要因・結果・因果を保ち、不要な記述評価を残さず閉じた結果を段階0で引用できる。単なる気分の重さや因果のない損失では代用しない。',
    'r2qc': '人である同じ対象者が同じ仕組みに服し、その仕組みの行使である同じ圧迫行為r2qbについて、同じ担い手の過度な利益欲または同じ仕組みへの支配欲がr2pxで結ばれる。両動機の併存を許し、いずれか一方のみとは限定しない。',
    'r2qd': '指定した仕組みと対象者の継続的な服属関係h226nを、状況ごとの内容として取り出す。前後の同じ結び付きの検査に使う。',
    'r2qe': '同じ対象者・過程・履歴・前後点に、先行する個人的専制r2qaと動機を持つ圧迫r2qcを結び、その両方の仕組みへの服属を既存rcfで終わらせる。専制側と圧迫側の仕組みや担い手は同じでも異なってもよい。本人の参加・作用・終結関与と、前に服属し後に服属しないことを各関係で要求する。別の結び付きの喪失、役職交代、動機の消失だけでは足りない。',
}
LIMITS = [
    '第五文全体の依存関係のうち、Abfall von persönlichem Despotism und gewinnsüchtiger oder herrschsüchtiger Bedrükkungの結果構成を扱う。革命という活動種類、可能性と否定側の改革結果、著者帰属、後半の予測と描写はまだ接続していない。',
    '個人的専制を、事実上の決定統制と個人裁量への抑制の欠如として読む。特定の国家形態・君主・歴史的事件を補わない。Bedrükkungは対人・社会的な圧迫の読みで、心理的な抑うつ感に置き換えない。',
    'gewinnsüchtig/herrschsüchtigは、物質的利益または同じ仕組みへの支配を過度に求める動機が、同じ圧迫行為の目的にあることと読む。利得の取得や支配拡大の成功は条件にしない。単に別の時に欲求を持っていたという共存でもない。',
    'Abfallは、当事者が指定の服属から離反し、その関係を実際に断つ過程と読む。外部者だけが仕組みを改める読みや、当事者が服したまま支配者が交代する読みとは分ける。永久的自由や他の全ての支配の不在は補わない。',
    'この構成は個々の当事者に対する結果条件である。公衆の全対象範囲、集団への広がり、同じ革命がその結果を生む候補の結合は次に充足する。有限検査から原文全体の意味判断を認定しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2px[actor a act a goal i[h[j[a]] e] roles j[a] point d] c[
 w[k aa[v actor]][w[k dg[v act v point]][w[k df[v actor v act v point]][
 w[k hzxq[v actor v goal v roles v point]][
 w[k h226m[v actor v goal v roles v point]][k hztl[v actor v act v goal v roles v point]]
 ]]]]
].
d r2py[roles j[a]] e[b point[g person a[
 w[e[v roles][l[a][v person]]][k h226l[v person v point]]
]]].
d r2pz[roles j[a]] e[b point[g person a[g order a[
 w[e[v roles][l[a][v person v order]]][k h226i[v person v order v point]]
]]]].
d r2qa[order a holder a] e[b point[
 w[k aa[v holder]][w[k h226i[v holder v order v point]][k h226j[v holder v order v point]]]
]].
d r2qb[act a target a point d] c[
 w[k h226k[v act v target v point]][w[k dg[v act v point]][
 w[k ur[v target v point]][k hzie[v act r[p r2pb] v target r[p r2od] v point]]
 ]]
].
d r2qc[actor a target a act a order a point d] c[
 w[k aa[v target]][w[k h226n[v order v target v point]][
 w[k h226p[v act v order v point]][w[k r2qb[v act v target v point]][
 x[k r2px[v actor v act r[p r2py] l[a][v actor] v point]][
 k r2px[v actor v act r[p r2pz] l[a][v actor v order] v point]]
 ]]]]
].
d r2qd[order a target a] e[b point[k h226n[v order v target v point]]].
d r2qe[target a ruler a despotic a oppressor a oppressive a pressure a process a
 first d last d history h[d] c before h[d d] c] c[
 w[t[k r2qa[v despotic v ruler]][v first]][
 w[k r2qc[v oppressor v target v pressure v oppressive v first]][
 w[k rcf[v history v before v process v despotic v target v first v last
 p r2qd p ag p la p df p h226o]][
 k rcf[v history v before v process v oppressive v target v first v last
 p r2qd p ag p la p df p h226o]
 ]]]
].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2qe']), statements=[])
    declarations = {d['name']: d for d in added}
    basis = dict(status='political_withdrawal_result_composed_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-slow-attainment-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
