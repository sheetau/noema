"""Connect a controlled-vs-uncontrolled postural transition to failed experience."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_caused_deterrence import ROOT,closure

PARENT='examples/v016/kant-caused-deterrence.noema'
PARENT_BASIS='data/caused-deterrence-basis-v1.json'
FULL='examples/v016/kant-falling-depiction.noema'
CORE='examples/v016/falling-depiction-core.noema'
LIBRARY='examples/v016/postural-descent.noema'
BASIS='data/falling-depiction-basis-v1.json'
ANNOTATIONS='data/falling-depiction-identifiers-v1.json'
PRIMITIVES={
 'hzui':(['person','point'],'この身体主体が、足による支持の上に身体を保つ姿勢・均衡を維持している。歩いていることや歩行技能の保有は別条件であり、静止した立位でもよい。'),
 'hzuj':(['person','point'],'足底以外の身体部分が地面または下方の支持面に接し、そこで身体の荷重の一部を受ける。立位の足底接地や、手で物に軽く触れただけの状態とは区別する。接触だけから傷害を導かない。'),
 'hzuk':(['person','process','earlier','later'],'この同じ身体主体の位置が、この同じ過程の前後で、重力に沿う下向きへ移る。別人の下降、単なる時間的な先行、別過程での位置差では成立しない。具体的な距離・加速度は指定しない。'),
 'hzul':(['person','process','earlier','later'],'この同じ身体主体が、この同じ過程で、前後の姿勢と支持の移行を意図に沿って制御して遂行する。意図を持っただけ、偶然に無事だったこと、他者に支えられたことからは認定しない。'),
}
MEANINGS={
 'rqvu':'同じ身体主体・過程・先後の状況について、生起・状態移行・影響を受ける本人・前の足支持姿勢・後の姿勢喪失と地面側接触・下降・制御した移行の不成立を結ぶ。転倒の一つの身体的な読みの一般構成であり、どの一条件からも全体を補わない。',
 'hzum':'同じ人の同じ経験がzalの活動を試みるものであり、その経験の結果状況にrqvuの姿勢喪失と下降がある。評価時点を過程の前側に置き、別の経験の結果を流用しない。',
 'hzun':'二個体の引数列を本人・経験の順で受け、同じ二対象について既存fgの不成功経験を返す。空・不足・余分な引数を拒否する。',
 'hzuo':'同じ二個体の引数列を本人・経験の順で受け、同じ二対象についてhzumの身体的描写を返す。',
 'hzup':'学習の理由節fvで、本人・経験を保持した不成功経験hzunを身体的描写hzuoで非字義的に提示するという帰属。両内容の真理や、知的な失敗が実際の身体転倒であることを要求しない。',
}
LIMITS=[
 '歩行を試みる最中の、足支持姿勢を失って地面側へ至る転倒という読解を採る。空中にある途中、寝台からの落下、制御した受け身、Fallenの全語義をこの構成だけで尽くさない。',
 '身体の支持・地面側接触・下降・制御を四つの関係へ分ける。人体力学や運動制御の実証理論を完成条件にすり替えず、入力関係の意味規約として明示する。',
 '同じ経験の後状態に少なくとも一つ描写に合う結果を要求する。結果候補の欠落を転倒と扱わず、全ての結果が同じ姿勢であることや、傷害・永続的不能は要求しない。',
 'zalは既存の外部支持のない脚による身体移動であり、歩行と走行の境界は未精密化。今回追加したのはその試みの転倒で、身体的な歩行能力の取得と見込み全体はまだ接続していない。',
 '学習の対象側では既存fg・fp・frが経験・少数回・能力取得・見込みを記述する。今回のrbtは理由節内の本人と経験の対応であり、全ての知的な失敗を転倒だと一般化しない。',
 '既存38文と九単位の判断を保ち、比喩帰属を一文加える。原文対応範囲と全体確認済み分量は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def additions():
    text='''
d rqvu[person a process a start d end d before h[d d] c occurs h[a d] c changes h[a d d] c affected h[a a d d] c standing h[a d] c grounded h[a d] c downward h[a a d d] c controlled h[a a d d] c] c[
 w[c[v before][v start v end]][w[c[v occurs][v process v start]][w[c[v changes][v process v start v end]][w[c[v affected][v person v process v start v end]][
 w[c[v standing][v person v start]][w[u[c[v standing][v person v end]]][w[c[v grounded][v person v end]][w[c[v downward][v person v process v start v end]][u[c[v controlled][v person v process v start v end]]]]]]]]]]
].
r hzui[a d] c.r hzuj[a d] c.r hzuk[a a d d] c.r hzul[a a d d] c.
d hzum[person a experience a] e[b start[w[k f5[v person v experience r[p zal] v start]][g end d[w[k f6[v experience v end]][
 k rqvu[v person v experience v start v end p dd p dg p ag p la p hzui p hzuj p hzuk p hzul]
]]]]].
'''
    for name,body in [('hzun','k fg[v person v experience v scene]'),('hzuo','t[k hzum[v person v experience]][v scene]')]:
        text+='d '+name+'[bindings j[a]] e[b scene[w[e[d[v bindings]][n p c b]][g person a[g experience a[w[a[v bindings][n p a b][v person]][w[a[v bindings][n p b b][v experience]]['+body+']]]]]]].'
    return text+'d hzup[] c[k rbt[k fv[] k wa[] r[p hzun] r[p hzuo] k wh[]]].'


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzup[]].');doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hzup']);core['statements']=doc['statements'][-1:]
    library=deepcopy(doc);library['declarations']=closure(doc,['rqvu']);library['statements']=[]
    added=doc['declarations'][size:];by_name={d['name']:d for d in added}
    basis=dict(status='postural_descent_as_nonliteral_depiction_of_failed_experience',document=FULL,library=LIBRARY,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning) for n,(args,meaning) in PRIMITIVES.items()},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/caused-deterrence-identifiers-v1.json').read_text(encoding='utf-8'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Postural descent connected as a nonliteral experience depiction',flush=True)


if __name__=='__main__':main()
