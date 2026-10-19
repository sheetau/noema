"""Separate a conditional tool profile from an actual remaining-life outcome."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure

PARENT = 'examples/v016/kant-instrumental-misuse.noema'
PARENT_BASIS = 'data/instrumental-misuse-basis-v1.json'
FULL = 'examples/v016/kant-conditioned-persistence.noema'
CORE = 'examples/v016/conditioned-persistence-core.noema'
BASIS = 'data/conditioned-persistence-basis-v1.json'
ANNOTATIONS = 'data/conditioned-persistence-identifiers-v1.json'
MEANINGS = {
    'r2eu': '比較候補ごとの継続点が空でないことを確認し、継続点の全てで条件内容が成り立つ候補では、同じ点の全てで結果内容も成り立つ。条件を満たす候補を少なくとも一つ要求する。既存rjmとrjoの合成であり、現実の条件や結果、無期限性、条件を途中で失った候補のそれ以前の結果までは含めない。',
    'r2ev': '同じ対象・本人・能力・活動・状況について、吟味のない使用r2ep、自然的能力の誤用hn2、その活動の生起を結ぶ。結果の成立や原因性は含めない。',
    'r2ew': '同じ対象を同じ本人が使う活動と能力があり、r2evを満たすという状況の内容。異なる状況では活動や使用能力が変わってもよい。',
    'r2ex': 'r2evの使用活動そのものが同じ本人の未成熟bfへの結果生成に関わり、その状況でbfも成り立つという内容。別の使用行為や別人の結果を借りず、生涯全体の結果h26は要求しない。',
    'r2ey': '同じ対象・本人について、選んだ継続範囲でr2ewの使用が続く候補には、同じ範囲でr2exの因果的結果が続くという条件付きの比較。r2euに候補と継続点の選定を明示的に渡す。現実にその使用をしているとは断定しない。',
    'r2ez': '基準状況で規定または定型表現h27に属する同じ対象と本人に、r2eyの条件付きの作用を結ぶ未採用の原文候補。著者帰属、全ての規定と定型表現への一般化、無期限性は含めない。',
}
LIMITS = [
    '第三文の道具と持続を、実際の残余生涯の結果とは区別して記述する比較候補である。原文に条件節を読み込むことを確定せず、既存の著者主張54文は改訂しない。',
    '候補と継続点の選定根拠・網羅性・現実との到達可能性は解釈の前提である。結果が成立する点だけを選んで作用を立証したとはしない。順序・凸性・連続時間・終点の不存在はこの構成には含めない。',
    '継続範囲全体で使用するという条件であり、使用を途中でやめた候補の停止前の状態を保証するまでの演算ではない。使用をやめれば必ず成熟するとも、使用がなくても永久に未成熟だとも述べない。',
    '少なくとも一つの使用継続候補を要求する強さは明示した選択であり、前件が不可能でも成立する条件文の全用法を代用しない。未知の候補や原因は偽として補完しない。',
    '因果関係g3は保持され、その判断を共起だけから推定しない。各継続点で生起する使用活動が必要な強い候補であり、一度の使用の遅延効果や通常性・例外を持つ傾向一般は未完である。',
    'h27に残る規定の制定・拘束性、一項の定型表現という制約、基礎的な能力や因果の意味説明は未完。分類の式記述全域を有限個の例で代用しない。',
    '原文のimmerwährendenの強さと第三文全体の読みは未確定であり、新しい対応文字数や意味確認済み分量は加えない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    size = len(doc['declarations']); statements = doc['statements']; doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + '''
d r2eu[condition e result e anchor d candidates h[d d] c continuations h[d d d] c] c[
 w[f branch d[y[c[v candidates][v anchor v branch]][g point d[c[v continuations][v anchor v branch v point]]]]]
 [k rjm[k rjo[v result v anchor v continuations] k rjo[v condition v anchor v continuations] v anchor v candidates]]
].
d r2ev[object a person a faculty a act a point d] c[
 w[k r2ep[v person v object v act v point p hx2 p fa p fb p hz2]][w[t[k hn2[v person v faculty v act]][v point]][k dg[v act v point]]]
].
d r2ew[object a person a] e[b point[g faculty a[g act a[k r2ev[v object v person v faculty v act v point]]]]].
d r2ex[object a person a] e[b point[g faculty a[g act a[w[k r2ev[v object v person v faculty v act v point]][w[k g3[v act v person r[p bf] v point]][t[k bf[v person]][v point]]]]]]].
d r2ey[object a person a anchor d candidates h[d d] c continuations h[d d d] c] c[
 k r2eu[k r2ew[v object v person] k r2ex[v object v person] v anchor v candidates v continuations]
].
d r2ez[object a person a anchor d candidates h[d d] c continuations h[d d d] c] c[
 w[t[k h27[v object]][v anchor]][k r2ey[v object v person v anchor v candidates v continuations]]
].
''')
    doc['statements'] = statements; doc = parse(format_graph(doc, 'compact'))
    assert len(statements) == 54 and statements == old.document['statements']
    core = deepcopy(doc); core.update(declarations=closure(doc, ['r2ez']), statements=[])
    added = doc['declarations'][size:]; assert len(added) == 6
    basis = dict(status='conditional_continuation_profile_not_adopted_as_author_claim', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')} for d in added}, limitations=LIMITS)
    body = format_graph(doc, 'compact') + '\n'
    annotations = json.loads((ROOT / 'data/instrumental-misuse-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    encode = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', BASIS: encode(basis), ANNOTATIONS: encode(annotations)}


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)
    print('Six definitions; all 54 author statements preserved', flush=True)
