"""Bind planting and retaliatory personification to the existing case roles."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-prejudice-reason.noema'
PARENT_BASIS = 'data/prejudice-reason-basis-v1.json'
FULL = 'examples/v016/kant-prejudice-depictions.noema'
CORE = 'examples/v016/prejudice-depictions-core.noema'
BASIS = 'data/prejudice-depictions-basis-v1.json'
ANNOTATIONS = 'data/prejudice-depictions-identifiers-v1.json'
PRIMITIVES = {
    'h225t': ('[a d] c', ['plant', 'point'], 'この個体が、根を介して培地に定着して生育する植物体である。植え付け済み、成長の成功、特定の種であることは含めない。'),
    'h225u': ('[a d] c', ['medium', 'point'], 'この対象が植物の根を受け入れる土壌または生育用の培地である。特定の植物が実際に定着したことは含めない。'),
    'h225v': ('[a a d] c', ['plant', 'medium', 'point'], '同じ植物体の根の領域がこの培地の内部に収められ、培地と接する状態にある。近くに置いただけ、他の植物の根の接触、実際の生育とは区別する。'),
    'h225w': ('[a a d] c', ['plant', 'medium', 'point'], '同じ植物体がこの培地で根づいて生育している状態。目標として引用する場合は、現実の定着・成長の成功を要求しない。'),
    'h225x': ('[a] i[a]', ['case'], '同じ事例の受け手h225fを、植え付けの描写の培地として指す閉じた個体記述。元の参照との一致はr2paで検査する。'),
    'h225y': ('[] a', [], '固定原文kant-1784:u0011第三文の[721,744)、偏見を植えるという描写の箇所。'),
    'h225z': ('[a a] a', ['case', 'target'], '同じ事例・対象者の反作用を擬人化して述べる描写上の応答行為。現実の応答行為の存在や意図は参照だけから導かない。'),
    'h226a': ('[a a] i[a]', ['case', 'target'], '同じ事例の同じ反作用の対象者を指す閉じた個体記述。描写の意図内容を閉じるために用い、元の対象者との一致はr2pjで検査する。'),
    'h226b': ('[a a d] c', ['actor', 'prior_act', 'point'], 'この主体が、この先行行為を自分に対する害・不当な扱いとして受け止めている。先行行為の客観的な不当性、実際の被害、行為者への正当な請求権は保証しない。'),
    'h226c': ('[a a d] c', ['response', 'prior_act', 'point'], 'この応答が、指定した先行行為に対して扱いを返す応報的な対応として位置づけられる。単なる時系列の後続、将来の予防だけを目的とする措置、別の先行行為への対応とは区別する。応答主体・害・意図・因果は別に検査する。'),
    'h226d': ('[] a', [], '固定原文kant-1784:u0011第三文の[751,790)、偏見がついには本人たちに復讐するという擬人化の箇所。'),
}
MEANINGS = {
    'r2oy': '同じ培地について、植物体・培地の分類と、その植物の根の領域が培地内部で接する状態を結ぶ性質の族。生育の成功や植物の分類を意見の現実の性質として断言しない。',
    'r2oz': '同じ植物体が同じ培地で根づき生育するという目標内容。植え付けの目的として引用し、目標の実際の達成とは分ける。',
    'r2pb': '同じ行為が評価点に生起するという既存dgの内容。因果的寄与へ渡す要因記述に使う。',
    'r2pa': '同じ人が同じ生起行為へ参加し、同じ植物・培地の生育r2ozを目的に持ち、その行為の生起が同じ植物のr2oyの成立に因果的に寄与する。植物名と培地名の一致、結果状態の成立を要求し、成長の成功は要求しない。',
    'r2pc': '同じ事例から既存r2obへ全参照を供給する植え付けの対象側。後見人の意図や植物の実在を偏見採用の生成へ追加しない。',
    'r2pd': '同じ事例の生み手・行為・意見・受け手・植え付け点を、それぞれ植える人・配置行為・植物・培地・配置点へ対応づけてr2paへ渡す。別の事例の植物や人を選び直さない。',
    'r2pe': '一位置の列[事例]と評価点に、同じ事例の対象側r2pcを結ぶ内容の族。',
    'r2pf': 'r2peと同じ一位置・評価点に、同じ事例の植物側r2pdを結ぶ描写の族。',
    'r2pg': '一位置の列[事例]と評価点に、同じ固定事例範囲h225bを結ぶ。対象と描写の成否を範囲条件にしない。',
    'r2ph': '同じ評価主張r2otにおいて、同じ範囲r2pgの植え付けr2peを植物側r2pfで非字義的に提示する帰属。既存h224nへ閉じた段階3の族を渡す。',
    'r2pj': '同じ主体が同じ生起行為へ参加し、先行行為を自分への不当な扱いとして受け止め、その先行行為への応報として同じ対象者の不利益を意図し、同じ行為がその不利益に実際に寄与する。単なる害・意図だけ・別対象への応答では足りず、正当な処罰であることは要求しない。',
    'r2pk': '同じ事例・対象者の既存r2oiを保持し、同じ意見を応答主体、植え付け行為を応答が向けられる先行行為、同じ帰結点を応答点としてr2pjを加えた擬人化側。本人または先任者の選言と終点を省略しない。',
    'r2pl': '三位置[事例,意見,本人]と評価点を対象側r2onと共有し、同じ意見参照に固定したr2pkを描写側へ結ぶ。',
    'r2pm': '同じ理由節の主張r2ok・範囲r2om・対象r2onを、擬人化側r2plで非字義的に提示する帰属。偏見を世界の意図ある人物として認定しない。',
    'r2pn': '既存の第三文の統合r2oxに、同じ事例に結ぶ植物の植え付けr2phと報復の擬人化r2pmの提示を追加する。第三文全体の通読による意味判断は別途行う。',
}
LIMITS = [
    'pflanzenは、根のある植物を生育させるため培地へ置く描写として読む。種子の播種、農業の収量、実際に生育したこと、対象側の偏見を作る人の生育意図まで補わない。意図と成長は描写側で引用された条件である。',
    '対象側と植物側は同じ事例の生み手・行為・意見・受け手・植え付け点を共有する。受け手の人を現実の土壌、意見を現実の植物と分類することはない。',
    'sich rächenの対象側は、先行する偏見採用から生み手側への有害な反作用という既存の読みを保持する。擬人化側だけに、不当な扱いとしての受け止め、応報、同じ対象への加害意図と行為を加える。',
    '既存rfmは対象者本人の行為への処罰を扱うため、先任者が生み手である枝を含む今回はそのまま流用しない。一般の生起・参加・目的・不利益・因果を再利用し、応答が参照する先行行為と被害者を独立に結ぶ。',
    '報復の描写でも、同じ事例のr2oiを保持し、植え付けの生み手と被害者本人または先任者の選言、全経過の終点を省略しない。報復の正当性や、先行行為が客観的に不当だったことは足さない。',
    '二つの提示には既存h224nを使い、閉じた段階3の主張・範囲・対象・描写を渡す。帰属時に植物や報復行為を実行評価しない。未確認の文番号59をr2pnへ統合し、既存13区間・先頭二文382非空白文字の判断は保持する。',
    '今回の構成検査と、原文第三文全体の意味一致の判断を分ける。第三文の通読・句ごとの確認は次の統合判断に残し、検査成功から確認済み分量を増やさない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def unary(name, body):
    return ('d ' + name + '[roles j[a]] e[b reference[g case a['
            'w[e[v roles][l[a][v case]]][' + body + ']]]].')


def definitions():
    return '''
d r2oy[medium a] h[a] e[i[plant a][b point[
 w[k h225t[v plant v point]][w[k h225u[v medium v point]][k h225v[v plant v medium v point]]]
]]].
d r2oz[plant a medium a] e[b point[k h225w[v plant v medium v point]]].
d r2pb[act a] e[b point[k dg[v act v point]]].
d r2pa[actor a act a plant a medium a plantname i[a] mediumname i[a] point d] c[
 w[e[s[v plantname]][v plant]][w[e[s[v mediumname]][v medium]][w[k aa[v actor]][
 w[k dg[v act v point]][w[k df[v actor v act v point]][
 w[k hzu[v actor v act o a[r[p r2oz]][v plantname v mediumname] v point]][
 k rqqu[v act r[p r2pb] v plant o a[r[p r2oy]][v mediumname] v point]
 ]]]]]]
].
d r2pc[case a] c[k r2ob[k h225d[v case] k h225e[v case] k h225f[v case]
 k h225g[v case] k h225h[v case] k h225i[v case]]].
d r2pd[case a] c[k r2pa[k h225d[v case] k h225e[v case] k h225g[v case]
 k h225f[v case] k h225h[v case] k h225x[v case] k h225i[v case]]].
''' + unary('r2pe', 'k r2pc[v case]') + unary('r2pf', 'k r2pd[v case]') + unary(
        'r2pg', 'k h225b[v reference v case]') + '''
d r2ph[] c[k h224n[k h225y[] k wa[] r d[k r2ot[]]
 r d[p r2pg] r d[p r2pe] r d[p r2pf] k hzp3[]]].
d r2pj[actor a act a prior a target a targetname i[a] point d] c[
 w[e[s[v targetname]][v target]][w[k dg[v act v point]][w[k df[v actor v act v point]][
 w[k h226b[v actor v prior v point]][w[k h226c[v act v prior v point]][
 w[k hzu[v actor v act o a[r[p r2od]][v targetname] v point]][
 k rqqu[v act r[p r2pb] v target r[p r2od] v point]
 ]]]]]]
].
d r2pk[case a target a] c[
 w[k r2oi[v case v target]][k r2pj[k h225g[v case] k h225z[v case v target]
 k h225e[v case] v target k h226a[v case v target] k h225k[v case v target]]]
].
d r2pl[roles j[a]] e[b reference[g case a[g opinion a[g target a[
 w[e[v roles][l[a][v case v opinion v target]]][
 w[e[v opinion][k h225g[v case]]][k r2pk[v case v target]]]
]]]]].
d r2pm[] c[k h224n[k h226d[] k wa[] r d[k r2ok[]]
 r d[p r2om] r d[p r2on] r d[p r2pl] k hzp3[]]].
d r2pn[] c[w[k r2ox[]][w[k r2ph[]][k r2pm[]]]].
'''


def build():
    old = parent()
    doc = deepcopy(old.document)
    statements, doc['statements'] = doc['statements'], []
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') +
                ''.join('r ' + n + spec[0] + '.' for n, spec in PRIMITIVES.items()) + definitions())
    added = doc['declarations'][len(old.document['declarations']):]
    assert statements[-1] == dict(kind='assert', body=dict(kind='call', symbol='r2ox', arguments=[]))
    statement = dict(kind='assert', body=dict(kind='call', symbol='r2pn', arguments=[]))
    doc['statements'] = statements[:-1] + [statement]
    core = deepcopy(doc)
    core.update(declarations=closure(doc, ['r2pn']), statements=[statement])
    declarations = {d['name']: d for d in added}
    basis = dict(status='prejudice_planting_and_retaliation_depictions_integrated',
                 document=FULL, parent=PARENT, inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=declarations[n]['parameters'], result=declarations[n]['result'],
                                     arguments=spec[1], meaning_ja=spec[2]) for n, spec in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/prejudice-reason-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
