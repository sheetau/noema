"""Use a context-bound audience predicate instead of an enumerated population."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-collective-change.noema'
PARENT_BASIS='data/collective-change-basis-v1.json'
FULL='examples/v016/kant-audience-change.noema'
CORE='examples/v016/audience-change-core.noema'
LIBRARY='examples/v016/scoped-population.noema'
BASIS='data/audience-change-basis-v1.json'
MEANINGS={
 'rqsz':'同じ対象・基準文脈で指定された範囲に含まれる全個体が、指定の適格条件を満たすこと。範囲は述語で与え、有限列を要求しない。この検査だけでは非空性や範囲の社会的な妥当性を主張しない。',
 'hzmx':'同じ集団・基準文脈の範囲を述語で与え、全員が人であることを確かめ、異なる内部の当事者と対象者の能力変化をrdaへ結ぶ。履歴・前後評価・結果の自立性・作用・活動部分・因果はh6bと同じ構成に保つ。mpの列を必要とせず、範囲の時点を過程の途中で取り替えない。',
 'hzmy':'同じ集団・過程・開始点・終了点・基準文脈についてhzmxを満たす対象者を、同じ基準文脈の範囲内で取り出し、rqswの広がり基準へ渡す。内部の当事者と活動部分は各対象者で異なってよい。',
 'hzmz':'hzmyの範囲関係として既存h6tを用いる。指定された宛先が想定する読者の範囲と、その内部で能力が変わった人の範囲を結ぶ。実際の受領者や取得許可のある人だけへ縮めず、公衆一般の分類をこの接続だけで認定しない。',
}
LIMITS=[
 '有限の構成員列に依存する旧h6b・hzmwを保持し、別定義として述語の範囲へ一般化する。旧列が適格な人を重複なく表し、同じ基準時の範囲と一致する場合の整合性を検査する。',
 '同じ基準時の範囲を比較中は固定する。基準時が異なる場合に宛先範囲が変わることは記述できるが、加入・離脱そのものの過程を説明したものではない。',
 'h6tは想定読者への展開であり、受領・理解・賛同・許可の記録から公衆を自動生成する関係ではない。範囲が公衆を適切に表す社会的根拠は引き続き必要。',
 'ceは読者世界全体としての公衆を分類する既存の関係である。一つの宛先を無条件にceへ分類したり、原文のein Publikumを全読者世界そのものへ強めたりしない。',
 '一人以上・複数人・全員の条件は広がりの明示的な選択肢であり、いずれも公衆の自己啓蒙の固定した人数基準とはしない。',
 '式は述語を量化するが、実行したモデルは有限領域である。無限の読者範囲を列挙・実行検証したとは主張しない。',
 '既存32文・全宣言・意味規約・確認済み七単位の結び付きを保存する。公衆の公開性、態度の伝播、自由、比較背景、著者帰属への接続は未完。',
]


def definitions():
    return '''
d rqsz[group a anchor d scope h[a a d] c eligible h[a] c] c[
 f person a[y[c[v scope][v group v person v anchor]][c[v eligible][v person]]]
].
d hzmx[group a actor a target a process a part a start d end d anchor d scope h[a a d] c] c[
 w[k rqsz[v group v anchor v scope p aa]][w[k ia[v target v anchor v anchor]][w[
 x[e[v end][v anchor]][k ic[v end v anchor v anchor]]
 ][k rda[i[point d][k ia[v target v anchor v point]]
 i[first d last d][k ic[v first v last v anchor]]
 i[person a][c[v scope][v group v person v anchor]]
 v actor v target v process v part v start v end
 i[person a point d][t[k fo[v person]][v point]] p bf p h4l r[p h4l]
 p ag p la p dg p df p h6a p g3]]]]
].
d hzmy[group a process a start d end d anchor d scope h[a a d] c extent h[h[a] c h[a] c] c] c[
 k rqsw[i[person a][c[v scope][v group v person v anchor]]
 i[target a][g actor a[g part a[k hzmx[v group v actor v target v process v part v start v end v anchor v scope]]]]
 v extent]
].
d hzmz[audience a process a start d end d anchor d extent h[h[a] c h[a] c] c] c[
 k hzmy[v audience v process v start v end v anchor p h6t v extent]
].
'''


def build():
    parent=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(parent.document)
    assert not set(MEANINGS)&set(parent.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzmz','rqsx','rqsy'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqsz'])
    basis=dict(status='predicate_audience_change_extension_not_complete_public_enlightenment',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Capacity changes bound to the intended audience without an enumerated population')


if __name__=='__main__':main()
