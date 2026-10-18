"""Describe, acquire and retain the same nonnumerical response disposition."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-qualitative-thinkers.noema'
PARENT_BASIS='data/qualitative-thinkers-basis-v1.json'
FULL='examples/v016/kant-qualitative-receipt.noema'
CORE='examples/v016/qualitative-receipt-core.noema'
LIBRARY='examples/v016/described-preferred-responses.noema'
BASIS='data/qualitative-receipt-basis-v1.json'
MEANINGS={
 'hzq6':'同じ本人・評価時点に候補範囲と通常性の比較を固定し、その本人の応答内容を候補場面で評価してrqt4へ渡す性質関数。評価時点の実際の応答や数値評点を要求せず、例外を許す条件はrqt4と共通にする。',
 'hzq7':'応答・候補範囲・通常性比較の閉じた記述からhzq6の閉じた性質記述を構成する。同じ記述を状態の評価、取得の原因、持続の検査へ渡せる。構成時に応答や通常性を実行しない。',
 'hzr2':'理由ある自己評価と全ての人の自己思考への課題を認める判断hznvを、hzq7の応答へ接続する。同じ場面・同じ人で両方が成立することを求める。基準・話題・規範源・立場・候補・通常性比較を全て同じ閉じた性質記述に保持する。',
}
LIMITS=[
 '前段の独立判断の性向と、今回受け手が取得する自己評価・規範承認への性向は異なる内容である。通常候補で応答する構成だけを共用する。',
 '原文のGeistを説明する数値なしの読解候補であり、心理機構・適切な候補と通常性・反事実的な妥当性は別に説明を要する。旧hznyの加重プロフィールと同値とはしない。',
 '既存hzoa・hzob・rqte・rafへ同じ状態記述を渡す。提示・受領・理解・新たな取得・因果・持続を省略せず、受領したというだけで性向を取得したとはしない。',
 '実行した伝達例の有限検査は、全ての中継列や原文の集団全体の伝播の真理を証明しない。既存の存在量化と条件付きの枠を保持する。',
 '既存34文と確認済み七単位を保持する。原文の全解釈値は未確定であり、新しい本文主張・対応文字・意味確認済み単位は増やさない。',
]


def definitions():
    return '''
d hzq6[response h[a] e cases h[a d d] c preferred h[a d d d] c] h[a] e[
 i[person a][b anchor[k rqt4[i[scene d][c[v cases][v person v anchor v scene]]
 i[first d last d][c[v preferred][v person v anchor v first v last]]
 i[scene d][t[c[v response][v person]][v scene]]]]]
].
d hzq7[response i[h[a] e] cases i[h[a d d] c] preferred i[h[a d d d] c]] i[h[a] e][
 o a[r[p hzq6]][v response v cases v preferred]
].
d hzr2[criterion i[a] subject i[a] source i[a] role i[a] cases i[h[a d d] c] preferred i[h[a d d d] c]] i[h[a] e][
 k hzq7[k hznv[v criterion v subject v source v role] v cases v preferred]
].
'''


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzr2','hzob','rqt6','hzpy','rqsx'])
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['hzq7'])
    basis=dict(status='qualitative_response_description_shared_by_acquisition_and_retention',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Qualitative state description connected to acquisition and retention',flush=True)


if __name__=='__main__':main()
