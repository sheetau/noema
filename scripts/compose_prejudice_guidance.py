"""Compose unexamined guidance and new plural opinions retaining that function."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-public-revolution.noema'
PARENT_BASIS = 'data/public-revolution-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-guidance.noema'
CORE = 'examples/v016/prejudice-guidance-core.noema'
BASIS = 'data/prejudice-guidance-basis-v1.json'
ANNOTATIONS = 'data/prejudice-guidance-identifiers-v1.json'
PRIMITIVES = {
    'h227i': ('[a a a d] c', ['review', 'opinion', 'decision', 'point'],
              'この吟味判断は、指定した同じ意見を同じ後続判断の根拠・判断基準として使ってよいかを検討する判断である。意見そのものへの別の検討、無関係な活動や別意見の適用についての吟味とは分ける。誰が実際に吟味したかはfaで別に結ぶ。'),
    'h227j': ('[a a] c', ['old', 'new'],
              '指定された二つの意見・教説には、何をどのように肯定するかという実質的な内容の違いがある。名前・媒体・言い回しの違いだけでは成立しない。相互矛盾、どちらかの真理、新奇さや社会的な採用時期までは含意しない。'),
    'h227k': ('[a d] b', ['group', 'reference'],
              '同じ集団・基準文脈について、ある意見群の採用やそれによる判断の方向付けが集団に広がっていると呼ぶ最低比率。前後・新旧・結果に応じて変えず、0と1の間を厳密に超える読みを合成定義で検査する。固定の過半数や全員は原文へ追加しない。'),
}
MEANINGS = {
    'r2rb': '既存r2nzの偏見採用の存在証人を明示する。同じ人の同じ判断が同じ意見の内容と話題を肯定し、確定した原則として採用するが、その本人による十分な根拠の吟味は済んでいない。判断を存在量化すればr2nzと同じ条件になる。',
    'r2rc': '同じ人の実際の後続判断に、同じ意見を偏見として採用した別の判断r2rbを理由として使うfcがある。その人による同じ意見の同じ後続判断への適用の吟味h227iはない。偏見を持つだけ、別人の理由、単なる後続・共存では成立しない。',
    'r2rd': '同じ意見について、本人にr2rcの後続判断があるという性質の族。Leitbandの対象側を、吟味されない原則を実際の判断の根拠として使う働きと読む。特定の操作者・外からの命令・生涯の無思考・判断能力の欠如は補わない。',
    'r2re': '同じ人が同じ意見の内容と話題を肯定し、確定した原則として採用している内容の族。根拠の吟味があったかを条件にせず、新しさの比較で、以前から十分に吟味して採用していた意見も既存の採用として数える。',
    'r2rf': '同じ集団の全構成員列mp、同じ基準のh227k、aaの人の分類を既存r2lbへ渡す。条件に該当する人の比率が基準を超える。成功者だけの列や範囲外の成功を数えない。',
    'r2rg': '指定した意見列の少なくとも一つが、同じ人に同じ時点でr2rdの方向付けとして働く内容族。異なる意見が異なる人を方向付けてもよく、全員が全意見を採用するとはしない。',
    'r2rh': '指定した意見列の少なくとも一つが、同じ人に同じ時点でr2reの確定した原則として採用される内容族。集団で新しく広がったかを、同じ列の以前の採用範囲と比較するために使う。',
    'r2ri': '意見列は重複がなく二項以上あり、その各項が同じ集団内の少なくとも一人に同じ時点でr2rdとして実際に働く。使われない名前を足して複数形を満たすことを許さない。広がりの条件は別に要求する。',
    'r2rj': '同じ有効な履歴・集団・基準で、先の複数の偏見による方向付けが広がり、内容の異なる後の複数の意見群は先には採用が広がっておらず、後には同じr2rdの働きが広がる。新旧の全項は実際の働き手を持つ。古い偏見の完全消滅、同じ人々の一斉交代、同一の効果量を要求しない。',
    'r2rk': '第二文と同じ公衆・基準から大衆h223iを指し、同じ人数条件r2m7と、同じ集団のr2rjを結ぶ。公衆の全読者と大衆を同一視せず、相対する別集団の新旧の採用を混ぜない。',
}
LIMITS = [
    'gedankenlosは、この意見を判断の根拠として用いる際に本人が吟味していないという読み。知能・不能・意識不在・あらゆる局面での思考の欠如とはしない。Dudenの第一語義を補助にし、気が散っているという別語義は採らない。',
    'Leitbandの対象側を、偏見として採用された原則が本人の後の判断の根拠として実際に使われる働きと読む。fcの理由使用は、fdの正当な支持・内容の真理や、特定人物の操作意図を含意しない。身体的な紐・歩行誘導の描写と対応はまだ別途必要。',
    '新しい意見は単なる改名と区別し、同じ集団で以前には広く採用されていなかったものと読む。新しい発明や全員にとって初耳であることは要求しない。古い意見が後にも残ることを許す。',
    '新旧の共通性は方向付けの働きであり、人数・強度・意見の内容が同一という主張にはしない。複数の偏見を集合的に読むので、各意見が全員へ作用することは要求しない。',
    '同じ有限集団の全構成員と前後で固定した広がり基準を使う。現実の閾値の適切さは解釈入力であり、数値例の検査から唯一の原文解釈を導かない。未知の吟味や採用を偽へ変換しない。',
    '新旧の意見群と時点の文脈供給、革命候補内の予測への量化、Leitbandの描写、呼称の語調、前半の様相・対比、第五文全体の通読は残る。既存62文と意味判断は保持し、確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2rb[person a opinion a judgment a point d] c[
 w[k aa[v person]][w[k fa[v person v judgment v point]][
 w[k fb[v judgment k h224z[v opinion] v point]][
 w[k hznn[v judgment k h224z[v opinion] k h224y[v opinion] e[v person][v person] v point]][
 w[k h224w[v judgment v point]][u[k h224x[v person k h224z[v opinion] k h224y[v opinion] v point]]]
 ]]]]
].
d r2rc[person a opinion a decision a point d] c[
 w[k dg[v decision v point]][w[k fa[v person v decision v point]][
 w[g judgment a[w[u[e[v judgment][v decision]]][
 w[k r2rb[v person v opinion v judgment v point]][k fc[v decision v judgment v point]]]]][
 u[g review a[w[k fa[v person v review v point]][k h227i[v review v opinion v decision v point]]]]
 ]]]
].
d r2rd[opinion a] h[a] e[i[person a][b point[g decision a[k r2rc[v person v opinion v decision v point]]]]].
d r2re[opinion a] h[a] e[i[person a][b point[
 w[k aa[v person]][g judgment a[
 w[k fa[v person v judgment v point]][w[k fb[v judgment k h224z[v opinion] v point]][
 w[k hznn[v judgment k h224z[v opinion] k h224y[v opinion] e[v person][v person] v point]][
 k h224w[v judgment v point]]
 ]]
 ]]
]]].
d r2rf[group a reference d selected h[a] c] c[
 k r2lb[k mp[v group] k h227k[v group v reference]
 i[person a][k hg[k mp[v group] v person]] v selected p aa]
].
d r2rg[opinions j[a]] h[a] e[i[person a][b point[
 g opinion a[w[k hg[v opinions v opinion]][t[c[k r2rd[v opinion]][v person]][v point]]]
]]].
d r2rh[opinions j[a]] h[a] e[i[person a][b point[
 g opinion a[w[k hg[v opinions v opinion]][t[c[k r2re[v opinion]][v person]][v point]]]
]]].
d r2ri[group a opinions j[a] point d] c[
 w[k rt[v opinions]][w[k hc[n p b b d[v opinions]]][
 f opinion a[y[k hg[v opinions v opinion]][
 g person a[w[k hg[k mp[v group] v person]][t[c[k r2rd[v opinion]][v person]][v point]]]
 ]]]]
].
d r2rj[group a old j[a] new j[a] earlier d later d reference d history h[d] c before h[d d] c] c[
 w[k ta[v history v before]][w[c[v history][v earlier]][w[c[v history][v later]][
 w[c[v before][v earlier v later]][
 w[k r2ri[v group v old v earlier]][w[k r2ri[v group v new v later]][
 w[f former a[y[k hg[v old v former]][f fresh a[y[k hg[v new v fresh]][
 w[u[e[v former][v fresh]]][k h227j[v former v fresh]]
 ]]]]][
 w[k r2rf[v group v reference i[person a][t[c[k r2rg[v old]][v person]][v earlier]]]][
 w[u[k r2rf[v group v reference i[person a][t[c[k r2rh[v new]][v person]][v earlier]]]]][
 k r2rf[v group v reference i[person a][t[c[k r2rg[v new]][v person]][v later]]]
 ]]]]]]]]]
].
d r2rk[public a reference d old j[a] new j[a] earlier d later d history h[d] c before h[d d] c] c[
 w[k r2m7[v public v reference]][
 k r2rj[k h223i[v public v reference] v old v new v earlier v later v reference v history v before]]
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
    doc['statements'] = statements
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2rk']), statements=[])
    decls = {d['name']: d for d in added}
    basis = dict(status='new_prejudices_same_unexamined_guidance_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/public-revolution-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
