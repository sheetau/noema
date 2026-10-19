"""Keep a depicted insistent stance separate from normative world content."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure

PARENT='examples/v016/kant-quiet-depiction.noema'
PARENT_BASIS='data/quiet-depiction-basis-v1.json'
FULL='examples/v016/kant-insistent-framing.noema'
CORE='examples/v016/insistent-framing-core.noema'
LIBRARY='examples/v016/depicted-insistence.noema'
BASIS='data/insistent-framing-basis-v1.json'
ANNOTATIONS='data/insistent-framing-identifiers-v1.json'
PRIMITIVES={
 'hzye':(['node','presenter','claim','viewpoint','focus','context'],
    '提示者がこの箇所・文脈の同じ主張記述の中で、指定した視点の担い手に帰属させる強い姿勢として、焦点の内容を緩めず維持するものとして示す。単なる真偽の報告や確実さの評価とは異なる提示上の働き。焦点の一個体・二状況は同じ主張内の対象者・先行時点・基準時点に対応する。担い手は描かれた視点であって、現実の発話者、実際の内心、著者の賛同や命令行為とは限らない。焦点内容の真理、義務や禁止の追加、制裁、聞き手の同意、量化範囲の拡大を含意しない。'),
}
MEANINGS={
 'r2ab':'同じ箇所・提示者・主張・文脈に、主張の帰属、異なる対象と描写の対応、描写側の焦点へ指定視点の強い姿勢を帰属させる提示を結ぶ。強調の対象は同じ描写記述であり、他の主張・描写・担い手の強調を借りない。内容は全て引用のままで評価しない。',
 'r2ac':'同じ複文hztr(db)について、rqzwからrqzxへの既存の身体側の不許容の描写を保持し、その同じ焦点を後見人群dbの緩めない姿勢として強く提示する。ja keinen Schritt ... wagen durftenをこの文脈で読む追加の提示であり、前の条件文のjaの認めやすさやschonの確言とは同一視しない。',
}
LIMITS=[
 'jaの働きを、後見人側の一歩も許容しない姿勢を強く描く提示として読む。原刊の文字列から音声の強勢を確定したとはしない。',
 '焦点は既存rqzxの身体側の不許容全体。同じ人物・先行時点・基準時点を対応させ、四つの目標指定形や不許容の論理条件は変更しない。',
 '著者がこの規範を支持して命令したこと、後見人が実際に発話したこと、制裁を加えること、全候補に明示的な禁止が制定されたことは補わない。',
 '強い姿勢は意味上の提示関係として明示する。語用論全体、すべてのjaの語義、表現の強さの数値尺度や実際の読者への効果の一般理論ではない。',
 '本文へ一文追加するが、各部分の接続から複文全体の意味一致を自動的に認定しない。家畜・局面上の落ち着き・歩行の語義範囲と節の結合、段落末尾と二作品全文の確認は残る。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='''
r hzye[a a i[e] a i[h[a d d] c] d] c.
d r2ab[node a presenter a claim i[e] viewpoint a target i[h[a d d] c] depiction i[h[a d d] c] context d
 claims h[a a i[e] d] c aligns h[a a i[e] i[h[a d d] c] i[h[a d d] c] d] c insists h[a a i[e] a i[h[a d d] c] d] c] c[
 w[u[e[v target][v depiction]]][w[c[v claims][v node v presenter v claim v context]][
  w[c[v aligns][v node v presenter v claim v target v depiction v context]][
   c[v insists][v node v presenter v claim v viewpoint v depiction v context]]]]
].
d r2ac[] c[k r2ab[k hzsq[] k wa[] r[k hztr[k db[]]] k db[] r[p rqzw] r[p rqzx] k wh[] p uc p hzyb p hzye]].
s[k r2ac[]].
'''
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (9,35,36,46,47,48,49)]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['r2ab']),statements=[])
    added=doc['declarations'][size:]
    basis=dict(status='insistent_viewpoint_framing_without_changing_normative_content',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],
            meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/quiet-depiction-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for path,text in build().items():write_exact(ROOT/path,text)
    print('Insistent framing appended; normative contents and old 49 statements unchanged',flush=True)


if __name__=='__main__':main()
