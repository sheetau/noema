"""Align bodily permission with the same person and prior point in a claim."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure

PARENT='examples/v016/kant-quantified-step-goals.noema'
PARENT_BASIS='data/quantified-step-goals-basis-v1.json'
FULL='examples/v016/kant-step-depiction.noema'
CORE='examples/v016/step-depiction-core.noema'
LIBRARY='examples/v016/timed-nonliteral-depiction.noema'
BASIS='data/step-depiction-basis-v1.json'
ANNOTATIONS='data/step-depiction-identifiers-v1.json'
PRIMITIVES={
 'hzyb':(['node','author','claim','target','depiction','context'],
    '著者がこの箇所・提示文脈の同じ主張記述の内で、対象側の関係を描写側の関係によって非字義的に提示する。両記述の一個体・二状況の位置は、同じ対象者・先行時点・基準時点を指す対応を持ち、主張内の同じ対象者と時点の束縛に結ぶ。両側で別々に選んだ時点を同じと扱わない。引用された内容の実際の成立、真偽の一致、因果的な同一性は要求しない。'),
}
MEANINGS={
 'rqzv':'同じ主張内の一個体・二状況を対応させるhzybの非字義的な提示について、対象と描写の記述が異なることを要求する。人物や状況を別の型へ符号化せず、記述内容を実行評価しない。',
 'rqzw':'同じ本人への慎重な阻止hztoと、知的自立を敢えて試みることへの許容欠如hztcが、同じ先行時点にある。先行時点は指定基準時点より前である。後見人群dbと立場hztdを固定し、hztqの第二の先行段階から取り出す対象側の関係である。',
 'rqzx':'同じ本人について、基準時点の装置qsを保持し、同じ先行時点で装置外への一歩を敢えて試みることへの許容が四つの指定形全てでない。足・過程の指定位置には個体領域全体を量化し、実行・成功・その時点の足の所属で範囲を縮めない。移動の成立条件は引用した目標側に残す。',
 'rqzy':'既存の複文hztr(db)に含まれるrqzwの局面を、rqzxの身体側の不許容で非字義的に描写するという追加の提示。対象者・先行時点・基準時点を同じ束縛へ対応させる。既存の家畜・閉じ込め・条件付き危険の描写を保持し、実際の身体的不許容を主張しない。',
}
LIMITS=[
 '対象はrqzuの四つの指定形で表す一歩の目標である。足と過程の指定位置を全個体領域へ開き、実際に起きた移動だけへ縮めない。個体領域には参照可能な未実現の過程も解釈でき、生起dgを量化から導かない。',
 '身体目標は既存rqzdの通常の接地更新の読みを継承する。全ての歩容や、任意の同義記述・任意の粒度での目標の同一性を保証するものではない。',
 '対象者と先行時点・基準時点の対応を、主張に結び付いた提示関係として明示する。対象側の真理から描写側の真理を導いたり、実際の人を動物として分類したりしない。',
 'qsは基準時点で選んだ同じ装置を先行時点の許容対象へ使う。先行時点に同名の別装置を選び直さない。装置の構成と閉じ込め成立は既存zbfの描写で保持する。',
 '原文に対する明示的な部分解釈として本文へ追加する。ruhigenとja、歩行と家畜の語義範囲、複文全体と第二段落全体の確認は残る。新しい全文単位や一文全体の意味確認は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document)
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
r hzyb[a a i[e] i[h[a d d] c] i[h[a d d] c] d] c.
d rqzv[node a author a claim i[e] target i[h[a d d] c] depiction i[h[a d d] c] context d] c[
 w[u[e[v target][v depiction]]][k hzyb[v node v author v claim v target v depiction v context]]
].
d rqzw[person a prior d anchor d] c[
 w[k dd[v prior v anchor]][w[t[k hzto[k db[] v person]][v prior]][t[k hztc[k db[] v person k hztd[] r[p bb]]][v prior]]]
].
d rqzx[person a prior d anchor d] c[
 w[k dd[v prior v anchor]][k rqzu[k db[] v person k hztd[] k qs[v person v anchor]
  i[item a][e[n p a b][n p a b]] i[item a][e[n p a b][n p a b]] v prior]]
].
d rqzy[] c[k rqzv[k hzsq[] k wa[] r[k hztr[k db[]]] r[p rqzw] r[p rqzx] k wh[]]].
s[k rqzy[]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46,47)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqzv']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='bodily_permission_depiction_aligned_to_prior_stage',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
            meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/walking-warning-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Bodily permission depiction added at the same prior stage',flush=True)


if __name__=='__main__':main()
