"""Classify revolutionary attempts within the same causal possibility case."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-political-withdrawal.noema'
PARENT_BASIS = 'data/political-withdrawal-basis-v1.json'
FULL = 'examples/v016/kant-revolution-routes.noema'
CORE = 'examples/v016/revolution-routes-core.noema'
BASIS = 'data/revolution-routes-basis-v1.json'
ANNOTATIONS = 'data/revolution-routes-identifiers-v1.json'
PRIMITIVES = {
    'h226q': ('[a a d] c', ['order', 'community', 'point'],
              'この対象は、同じ共同体における公的な決定権と決定の執行を組織する基本的な政治秩序の構成である。現在実施される秩序と提案された構成の双方を分類でき、実際に統治していることは別に要求する。任意の私的な好みや、一職員の人事だけとは区別する。'),
    'h226r': ('[a a a d] c', ['old', 'proposed', 'community', 'point'],
              '同じ共同体について二つの政治秩序を比較すると、公的な決定権の配分・権能・拘束的な規則の根幹に違いがある。単なる名称変更、通常の役職交代、局所的な運用修正ではない。提案が実施されたこと、改善・正当性・住民の啓蒙は含意しない。'),
    'h226s': ('[a a a d] c', ['act', 'old', 'community', 'point'],
              '同じ集団的な行為に、指定した政治秩序の既存の統治権力を覆そうとする対抗の実行がある。通常の権力継承としての交代や、提案だけに留まる活動とは分ける。対抗の成功、特定の手段、流血や全住民の参加は要求しない。秩序変更の具体的な目標と参加者は別に結ぶ。'),
    'h226t': ('[a a d] c', ['order', 'community', 'point'],
              '同じ共同体の公的な決定と執行が、この政治秩序によって実際に組織されている。案として存在することや、ある個人だけがこの秩序を望むこととは別である。正当性・恒久性・個々の人の服属をこの関係だけから補わない。'),
}
MEANINGS = {
    'r2qf': '三位置[旧秩序,提案秩序,共同体]に、旧秩序の実施が終わり提案秩序が実施されるという内容を結ぶ。革命的な行為の目標として引用し、達成済みとはしない。',
    'r2qg': '同じ共同体で実施される旧政治秩序と、根幹の異なる別の提案秩序を要求する。同じ集団的行為r2mlに既存統治権力への対抗h226sがあり、その行為の集団としての目標hztlが同じr2qfである。実施成功は要求せず、失敗する試みも含む。任意の政権交代や一人の私的な希望だけでは足りない。',
    'r2qh': '同じ対象・基準について、同じ活動と候補時点で、候補への所属・活動種類・生起・指定結果への因果・結果の成立を結ぶ経路が少なくとも一つある。rqcの活動種類を候補時点で評価する一般化で、別候補での分類や別活動の結果を混ぜない。',
    'r2qi': '同じ対象・活動種類・基準・候補関係を共有し、第一結果へのr2qhの経路があり、第二結果への経路がないという二判断を結ぶ。第二結果の否定を第一結果に成功した活動だけへ狭めず、他種類の活動による第二結果や現実の成功は否定しない。',
    'r2qj': '同じ共同体・対象・基準・候補について、活動と候補時点から同じ旧秩序・提案秩序・参加者を供給し、r2qgの革命的な試みを種類としてr2qhの結果経路に結ぶ。供給を結果の真偽によって選び直さない。',
    'r2qk': 'r2qjと同じ参照供給の革命的行為について、r2qiの可能な第一結果と不可能な第二結果を結ぶ。結果記述と文脈の充足は呼出側に残し、この関数だけで第五文全体の帰属を済ませない。',
}
LIMITS = [
    'Revolutionは、政治秩序の根幹を変えるための集団的な対抗の実行という読み。試みの失敗を許し、流血、特定の歴史的革命、正しい制度の実現、全住民の参加は補わない。産業上の技術変革や天体の公転の用法は採らない。',
    '目標は集団に帰属する同じ行為の計画・遂行として既存hztlへ結ぶ。各参加者全員の私的な目的の一致は要求しない。集団の行為r2mlの帰属と、集団の目標の帰属は別条件である。',
    '既存rqc/rqeの活動種類は一引数である。現実の一時点の分類を仮定の経過へ流用しないよう、候補時点も取るr2qh/r2qiへ一般化する。種類が時点に依存しない場合は旧式と一致する。生起・因果・結果評価の要件は弱めない。',
    '政治的離脱r2qeを閉じた結果として実際のr2qjへ接続して検査する。ただし公衆の全対象範囲・共通の候補供給・真の思考様式の改革・閉じた著者帰属は未充足。第五文の意味確認済み分量は増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    suppliers = ('community a reference d old h[a d] a proposed h[a d] a '
                 'participants h[a d] j[a]')
    kind = '''i[act a point d][k r2qg[v act v community c[v old][v act v point]
 c[v proposed][v act v point] c[v participants][v act v point] v point]]'''
    return '''
d r2qf[roles j[a]] e[b point[g old a[g proposed a[g community a[
 w[e[v roles][l[a][v old v proposed v community]]][
 w[u[k h226t[v old v community v point]]][k h226t[v proposed v community v point]]]
]]]]].
d r2qg[act a community a old a proposed a participants j[a] point d] c[
 w[u[e[v old][v proposed]]][
 w[k h226q[v old v community v point]][w[k h226q[v proposed v community v point]][
 w[k h226t[v old v community v point]][w[k h226r[v old v proposed v community v point]][
 w[k r2ml[v community v act v participants v point]][
 w[k h226s[v act v old v community v point]][
 k hztl[v community v act r[p r2qf] l[a][v old v proposed v community] v point]
 ]]]]]]]
].
d r2qh[target a kind h[a d] c result i[h[a] e] reference d candidate h[a d d] c] c[
 g act a[g point d[
 w[c[v candidate][v act v reference v point]][w[c[v kind][v act v point]][
 w[k dg[v act v point]][w[k g3[v act v target v result v point]][
 t[c[s[v result]][v target]][v point]
 ]]]]
 ]]
].
d r2qi[target a kind h[a d] c possible i[h[a] e] impossible i[h[a] e]
 reference d candidate h[a d d] c] c[
 w[k r2qh[v target v kind v possible v reference v candidate]][
 u[k r2qh[v target v kind v impossible v reference v candidate]]]
].
d r2qj[target a ''' + suppliers + ''' result i[h[a] e] candidate h[a d d] c] c[
 k r2qh[v target ''' + kind + ''' v result v reference v candidate]
].
d r2qk[target a ''' + suppliers + ''' possible i[h[a] e] impossible i[h[a] e]
 candidate h[a d d] c] c[
 k r2qi[v target ''' + kind + ''' v possible v impossible v reference v candidate]
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
    core.update(declarations=closure(doc, ['r2qj', 'r2qk']), statements=[])
    declarations = {d['name']: d for d in added}
    basis = dict(status='revolution_attempt_and_candidate_result_routes_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/political-withdrawal-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
