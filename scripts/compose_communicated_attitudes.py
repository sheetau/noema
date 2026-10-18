"""Connect a received message route to acquisition of a described attitude."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-prospective-liberty.noema'
PARENT_BASIS='data/prospective-liberty-basis-v1.json'
FULL='examples/v016/kant-communicated-attitudes.noema'
CORE='examples/v016/communicated-attitudes-core.noema'
LIBRARY='examples/v016/described-state-acquisition.noema'
BASIS='data/communicated-attitudes-basis-v1.json'
MEANINGS={
 'rqte':'同じ対象・過程・前後で、記述された性質を不成立から成立へ変える。状態を評価する関数を同じ記述から取り出し、同じ記述を結果生成の関係へ渡す。生起する同じ過程の同じ活動部分が、対象者にその性質を生じさせる。別の性質の原因や単なる同時生起を代用しない。',
 'hzni':'指定した性質の記述に該当する自分の状態を、その人が好ましく受け入れているという内容を作る関数。既存idを使い、対象の性質が実際に成立することや能力・義務・真理は要求しない。',
 'hznj':'異なる二人の同じ提示行為・話題・発話記述・終点について、提示・受領・理解と、受け手がhzniの態度を取得する変化を結ぶ。その提示行為が同じ変化過程の部分であり、同じ態度を生じさせる。対象の性質から態度の記述を内部で構成し、原因の目標と状態評価を一致させる。',
 'hznk':'既存h6iの理解を伴う有限伝達経路の最後の段階を、列の集計で取り出す。その段階の送信者・行為をhznjへ渡し、最終受け手の同じ話題・発話・終点の取得を要求する。経路外の行為や最初の発信者の別活動を原因へ差し替えない。',
 'hznl':'同じ宛先・参照文脈の想定読者を固定し、hznkの伝達と態度取得を満たす人の範囲をrqswで内部構成する。人の範囲の適格性をrqszで確認し、広がりの基準は引数として指定する。各人の経路・過程・前後は異なってよいが、発信者・話題・発話・態度の対象記述・基準文脈は共用する。',
}
LIMITS=[
 '態度はidの好ましい受容として明示的に読む。理解・信念・義務・能力・実行と同一ではなく、Geistやあらゆる態度の必要十分条件とはしない。',
 '態度の対象記述は入力として保持する。理性的な自己価値の評価と各人の自己思考の使命は、この一般構成へまだ具体的に接続していない。原語の文字列を意味の代わりに保存しない。',
 '受領を含む伝達行為が態度を生じさせるという既存g3の因果規約を使う。単なる受領・理解と取得の同時発生では足りないが、説得の心理機構や内容だけの十分原因を証明するものではない。',
 '取得の前に態度は偽、後に真である。以前から持つ態度の強化や維持、後の永続、全中継者の賛同、発信者の誠実さを追加条件にしない。',
 '伝達経路はh6iの同じ発話記述を保つ。内容を変える伝播、言い換えの同義性、周囲という社会的範囲は別の記述を要する。中継者が想定読者の範囲外でもよい。',
 '最後の受領と取得完了を同じ粗い終点で記録する。遅れて取得する過程の内部時刻や、発話後の詳細な心理過程はこの読みでは分解しない。',
 '集団の取得者は同じ基準時までに到達した人であり、同時に変わる必要はない。原文に人数基準を補わず、公開性・将来の様相・公衆の自己啓蒙全体は未完。',
 '既存32文・意味規約・七つの意味確認を保持し、新しい著者主張・原文の対応範囲・完成単位は加算しない。',
]


def definitions():
    return '''
d rqte[history h[d] c before h[d d] c target a process a part a start d end d
 description i[h[a] e] changes h[a d d] c affected h[a a d d] c occurs h[a d] c
 partof h[a a d] c produces h[a a i[h[a] e] d] c] c[
 w[k th[v history v before v process v start v end v changes c[s[v description]][v target]]][
 w[c[v affected][v target v process v start v end]][w[c[v occurs][v process v end]][
 w[c[v occurs][v part v end]][w[c[v partof][v part v process v end]][
 c[v produces][v part v target v description v end]]]]]]
].
d hzni[property i[h[a] e]] h[a] e[i[person a][b point[k id[v person v property v point]]]].
d hznj[actor a target a act a subject a message i[h[a] f] property i[h[a] e]
 process a start d end d anchor d] c[
 w[k aa[v actor]][w[k aa[v target]][w[u[e[v actor][v target]]][
 w[k ia[v target v anchor v anchor]][w[x[e[v end][v anchor]][k ic[v end v anchor v anchor]]][
 w[k rdc[v actor v target v act v subject v message v end p dg p f3 p f2 p h6e]][
 w[k h6g[v target v subject v message v end]][
 k rqte[i[point d][k ia[v target v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
 v target v process v act v start v end o a[r[p hzni]][o r[v property]] p ag p la p dg p h6a p g3]
 ]]]]]]]
].
d hznk[first a rest j[a] origin a target a subject a message i[h[a] f] property i[h[a] e]
 process a start d end d anchor d sender h[a] a recipient h[a] a activity h[a] a point h[a] d] c[
 w[k h6i[v first v rest v origin v target v subject v message v end v anchor v sender v recipient v activity v point]][
 c[i[last a][k hznj[c[v sender][v last] v target c[v activity][v last] v subject v message v property
 v process v start v end v anchor]]][q[v rest][v first][i[previous a step a][v step]]]]
].
d hznl[audience a reference d origin a subject a message i[h[a] f] property i[h[a] e] anchor d
 firsts h[a] a tails h[a] j[a] processes h[a] a starts h[a] d ends h[a] d
 sender h[a] a recipient h[a] a activity h[a] a point h[a] d extent h[h[a] c h[a] c] c] c[
 w[k rqsz[v audience v reference p h6t p aa]][k rqsw[i[person a][k h6t[v audience v person v reference]]
 i[target a][k hznk[c[v firsts][v target] c[v tails][v target] v origin v target v subject v message v property
 c[v processes][v target] c[v starts][v target] c[v ends][v target] v anchor v sender v recipient v activity v point]] v extent]]
].
'''


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hznl','rqsx','rqsy','bb'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqte'])
    basis=dict(status='received_message_and_acquired_attitude_partial_reading',document=FULL,
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
    print('Message routes connected to acquisition of the same described attitude')


if __name__=='__main__':main()
