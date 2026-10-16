"""Bind collective extent to the exact targets of one internal change process."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_graded_modality import definitions as modal_definitions,MEANINGS as MODAL_MEANINGS,LIMITS as MODAL_LIMITS

PARENT='examples/v016/kant-cross-reference.noema'
PARENT_BASIS='data/cross-reference-basis-v1.json'
FULL='examples/v016/kant-collective-change.noema'
CORE='examples/v016/collective-change-core.noema'
LIBRARY='examples/v016/collective-change.noema'
BASIS='data/collective-change-basis-v1.json'
MEANINGS={
 'rqsw':'非空の構成員範囲と変化条件から、両方を満たす人の範囲を式の内部で作る。その範囲も非空でなければならず、元の構成員範囲と同じ変化範囲を指定の広がり基準へ渡す。成功者だけを外部から選んだ別の集合や、集団外の成功者を代入しない。',
 'rqsx':'構成員の全員が指定範囲に含まれるという広がり基準。非空性は呼出側rqswで要求する。原文に全員という条件を自動的に加える既定値ではない。',
 'rqsy':'構成員のうち異なる二人が指定範囲に含まれるという広がり基準。人数を一般的な集団変化の定義へ固定せず、複数人を要求する明示的な選択肢として与える。',
 'hzmw':'同じ集団・変化過程・開始点・終了点・評価基準を固定し、既存h6bを満たす内部の当事者と活動部分がある構成員を、変化した人の範囲としてrqswへ渡す。広がり基準は引数であり、一人・複数人・全員を混同しない。公開性・態度の伝播・公衆全体の啓蒙をこの条件だけで認定しない。',
}
LIMITS=[
 '一人を対象とする既存の変化を、同じ過程の変化範囲へ接続する。変化は能力を失った人や新たに加入した人の単なる比率差ではなく、同じ対象者の前後条件による。',
 '構成員は既存mpが与える固定範囲である。参加・離脱、公衆としての公開性、公開の議論の成立は別に記述する。',
 '変化ごとに内部の当事者と活動部分は違ってよいが、集団・過程・前後・基準時は共用する。別の過程や別時点の成功を合算しない。',
 '本人が能力を獲得する過程に他者が関わることと、結果側の能力使用が他者の指導を必要とすることは異なる。既存h6bの区別を保持する。',
 '広がりの基準は原文への適合を別に判断する。二人・全員・過半数をカントの公衆の自己啓蒙の固定した意味としない。',
 '前段の程度比較の六定義も互換な拡張へ含めるが、自由の内容・比較背景・著者帰属への接続は未完。既存32文と意味確認登録簿は変更しない。',
]


def definitions():
    return '''
d rqsw[members h[a] c transition h[a] c extent h[h[a] c h[a] c] c] c[
 w[g person a[c[v members][v person]]][w[
 g person a[w[c[v members][v person]][c[v transition][v person]]]
 ][c[v extent][v members i[person a][w[c[v members][v person]][c[v transition][v person]]]]]]
].
d rqsx[members h[a] c reached h[a] c] c[
 f person a[y[c[v members][v person]][c[v reached][v person]]]
].
d rqsy[members h[a] c reached h[a] c] c[
 g first a[g second a[w[u[e[v first][v second]]][w[c[v members][v first]][w[
 c[v members][v second]
 ][w[c[v reached][v first]][c[v reached][v second]]]]]]]
].
'''


def source_definition():
    return '''
d hzmw[group a process a start d end d anchor d extent h[h[a] c h[a] c] c] c[
 k rqsw[i[person a][k hg[k mp[v group] v person]]
 i[target a][g actor a[g part a[k h6b[v group v actor v target v process v part v start v end v anchor]]]]
 v extent]
].
'''


def build():
    parent=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(parent.document)
    assert not (set(MEANINGS)|set(MODAL_MEANINGS))&set(parent.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+modal_definitions()+definitions()+source_definition())
    doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzmw','rqsx','rqsy'])
    library=parse('p:'+definitions())
    basis=dict(status='collective_change_extension_candidate_not_complete_public_enlightenment',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions={**MODAL_MEANINGS,**MEANINGS},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=[*MODAL_LIMITS,*LIMITS])
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Collective extent connected to one shared internal change process')


if __name__=='__main__':main()
