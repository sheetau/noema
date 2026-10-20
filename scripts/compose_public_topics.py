"""Make every subject explicit in the fixed scope of public permission."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-revolution-presentation.noema'
PARENT_BASIS = 'data/revolution-presentation-basis-v1.json'
FULL = 'examples/v016/kant-public-topics.noema'
CORE = 'examples/v016/public-topics-core.noema'
BASIS = 'data/public-topics-basis-v1.json'
ANNOTATIONS = 'data/public-topics-identifiers-v1.json'
PRIMITIVES = {
    'h227z': ('[a a d] c', ['activity', 'subject', 'reference'],
              '同じ基準文脈で、この活動記述がこの事柄を主題として扱う。活動の実行、発話の正しさ、許可、本人の能力とは区別する。一活動が複数の主題を持つことを許し、別活動の主題を流用しない。h6uの経路・発話記述まで必要としない一般的な主題関係。'),
    'h232a': ('[a d a] c', ['public', 'reference', 'subject'],
              '同じ公衆と基準文脈で、理性の公的使用が扱う事柄の全範囲に属する。in allen Stükkenの読みでは、公的に論じうる事柄を、許可の有無、好ましさ、実際の発言、成功、候補ごとの政策から選別しない。特定の教義や職務に限定せず、対象範囲の正しい供給は解釈側の責任とする。'),
}
MEANINGS = {
    'r2sj': '同じ公衆の固定した非空の読者範囲と非空の全主題範囲を確認する。各読者は人で、各主題に少なくとも一つの公的使用の役割・活動記述があり、その人の全公的活動は少なくとも一つの範囲内主題へ結ばれる。公的使用は既存zzoで判定し、実行・許可・能力を範囲の選別に使わない。',
    'r2sk': 'r2sjの主題範囲の完全性と、同じ公衆・基準・出所・評価点の既存hznaを結ぶ。各主題の一活動だけを許せばよいとはせず、固定範囲の全公的活動への積極的許可と反対要求の不在を要求する。',
    'r2sl': '同じ公衆・基準のr2sjを、第四段落第一文の自由維持r2lmへ結ぶ。公衆・活動・主題の範囲は基準で固定し、起点と後続期間の許可を同じ候補内で評価する。第五段落の全事柄という限定を、既存の自由維持の対象範囲へ明示的に接続する内容族。',
}
LIMITS = [
    '第五段落第一文のvon seiner Vernunft in allen Stükken öffentlichen Gebrauch zu machenを構成するための対象範囲と許可の接続である。学識者として読者世界へ向ける公的使用は、同段落後の定義に沿った既存zzoを再利用する。職業資格や実際の受領人数を条件にしない。',
    '全主題に活動記述があるという条件は、理性を使う活動をその主題について記述できることの範囲確認である。全読者があらゆる問題を解く能力、発言の正しさ、活動の実行、読者全員への現実の到達を要求しない。',
    '人物・主題・役割・活動の分類は同じ基準時点に固定する。禁止された主題や未実行の活動を候補の範囲から外して許可を空虚に成立させない。主題範囲自体の外部からの正しい供給は有限モデル検査では証明しない。',
    '公衆の全読者への許可という既存の読みを保ち、許可の出所は既存h222fの同じ文脈参照を使う。特定の統治者、全ての規範源の一致、不実行への積極的許可、社会的・身体的妨害の全面不在を補わない。',
    '新しい範囲条件があるためr2skからhzna、r2slからr2lmは保たれるが、その逆は無条件には成り立たない。既存の定義や確認済みの第四段落を変更せず、後続文の明示された限定として追加する。',
    'dieserの先行する啓蒙への照応、nichts erfordert alsの要件の限定、unschädlichsteの比較、aber/und zwar/nämlichの提示と第一文全体の帰属・通読は残る。新しい著者主張や確認済み文字数は追加しない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def definitions():
    return '''
d r2sj[public a reference d] c[
 w[g person a[k h6t[v public v person v reference]]][
 w[g subject a[k h232a[v public v reference v subject]]][
 f person a[y[k h6t[v public v person v reference]][
 w[k aa[v person]][
 w[f subject a[y[k h232a[v public v reference v subject]][
 g role a[g act a[w[k zzo[v person v act v role v reference]][k h227z[v act v subject v reference]]]]
 ]]][
 f role a[f act a[y[k zzo[v person v act v role v reference]][
 g subject a[w[k h232a[v public v reference v subject]][k h227z[v act v subject v reference]]]
 ]]]
 ]]]]
 ]]
].
d r2sk[public a reference d source a point d] c[
 w[k r2sj[v public v reference]][k hzna[v public v reference v source v point]]
].
d r2sl[public a reference d] e[b candidate[
 w[k r2sj[v public v reference]][t[k r2lm[v public v reference]][v candidate]]
]].
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
    basis = dict(status='all_public_subjects_permission_scope_partial', document=FULL, parent=PARENT,
                 inherited_meaning_basis=PARENT_BASIS, definitions=MEANINGS,
                 primitives={n: dict(parameters=decls[n]['parameters'], result=decls[n]['result'],
                                     arguments=s[1], meaning_ja=s[2]) for n, s in PRIMITIVES.items()},
                 new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added},
                 limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/revolution-presentation-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encoded = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n',
            BASIS: encoded(basis), ANNOTATIONS: encoded(annotations)}
