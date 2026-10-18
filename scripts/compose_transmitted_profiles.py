"""Compose assessed response profiles, receipt, acquisition and retention."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-reasoned-self-appraisal.noema'
PARENT_BASIS='data/reasoned-self-appraisal-basis-v1.json'
FULL='examples/v016/kant-transmitted-profiles.noema'
CORE='examples/v016/transmitted-profiles-core.noema'
LIBRARY='examples/v016/described-response-profile.noema'
BASIS='data/transmitted-profiles-basis-v1.json'
MEANINGS={
 'hznw':'応答の関数と、同じ本人・評価時点に結んだ場面の列挙・範囲・評価済み条件・正の重み・閾値を既存rqbへ渡し、評価した応答傾向という性質を作る。応答は選んだ場面で調べ、現実の評価時点での応答を要求しない。',
 'hznx':'応答と五つの評価条件の閉じた記述からhznwの適用記述を構成する。その同じ記述を状態評価と因果の目標へ渡せる。評価時点だけでなく評価基準の同一性も保持する。',
 'hzny':'理由ある自己評価と、全ての人の自己思考への課題を認める判断hznvを、hznxの応答へ具体的に接続する。各場面で同じ本人の両条件を要求し、二つの別々の場面の成功を一つの成功に合算しない。',
 'hznz':'異なる二人の提示・受領・理解と、同じ提示行為による受け手の記述された状態の取得を接続する。状態は引数の記述から直接評価し、好ましい自己受容hzniへ置き換えない。',
 'hzoa':'理解を伴う有限伝達経路の最後の送信者と活動を取り出し、最終受け手のhznzへ結ぶ。話題・発話・終点を共用し、経路外の行為を取得の原因にしない。',
 'hzob':'hzoaによる取得に加え、同じ人・履歴・記述された状態が、取得完了から基準時まで続くことを既存rafで要求する。原因の記述と持続する状態を別々に供給しない。',
 'hzoc':'同じ想定読者の範囲を固定し、hzobによる取得と持続を満たす人の正確な範囲を内部で作る。広がりの基準は指定する。各人の経路・取得時点は異なってよい。',
}
LIMITS=[
 '性向の操作的な読解候補として、明示した場面での理由ある自己評価と規範承認への応答傾向を用いる。一度の現実の判断だけを性向全体とせず、実際の判断がなくても仮定場面の応答から記述できる。',
 '場面と重みと閾値は結果を見る前に選ぶ解釈条件である。状態の変化に対応する仮定場面は評価時点ごとに変わり得るが、成功例だけを事後選択してよいという規約ではない。有限の全列挙を現実の全可能性の網羅としない。',
 'hznwは評価範囲に対する応答傾向を与える。持続は別条件hzobで明示する。Geistの心理機構・適切な評価場面と基準・社会的な妨害への頑健性の完全な理論ではない。',
 '規範承認を評価しても、その規範の真理や思考の実行を要求しない。提示された発話内容と、取得した性向の記述も区別する。言い換えや同義性の解決は含まない。',
 '伝達を受けた人が初めて状態を取得する読みであり、既存の性向の強化は含まない。全中継者の賛同は不要で、最終受け手の同じ変化を最後の活動へ結ぶ。',
 '持続は同じ履歴の取得完了から基準時までの全点に限る。無期限の未来、生涯、実時間の連続性を有限検査から証明しない。',
 '周囲という範囲、自由の条件、将来の様相と著者帰属への全文接続は残る。既存32文と七単位の確認を保存し、新たな原文範囲や全文確認を加算しない。',
]


def definitions():
    return '''
d hznw[response h[a] e points h[a d] j[d] cases h[a d d] c assessed h[a d d] c
 weights h[a d d] b threshold h[a d] b] h[a] e[i[person a][b anchor[
 k rqb[v person v anchor v points v cases v assessed v weights v threshold
 i[target a base d scene d][t[c[v response][v target]][v scene]]]
]]].
d hznx[response i[h[a] e] points i[h[a d] j[d]] cases i[h[a d d] c] assessed i[h[a d d] c]
 weights i[h[a d d] b] threshold i[h[a d] b]] i[h[a] e][
 o a[r[p hznw]][v response v points v cases v assessed v weights v threshold]
].
d hzny[criterion i[a] subject i[a] source i[a] role i[a]
 points i[h[a d] j[d]] cases i[h[a d d] c] assessed i[h[a d d] c]
 weights i[h[a d d] b] threshold i[h[a d] b]] i[h[a] e][
 k hznx[k hznv[v criterion v subject v source v role] v points v cases v assessed v weights v threshold]
].
d hznz[actor a target a act a subject a message i[h[a] f] state i[h[a] e]
 process a start d end d anchor d] c[
 w[k aa[v actor]][w[k aa[v target]][w[u[e[v actor][v target]]][
 w[k ia[v target v anchor v anchor]][w[x[e[v end][v anchor]][k ic[v end v anchor v anchor]]][
 w[k rdc[v actor v target v act v subject v message v end p dg p f3 p f2 p h6e]][
 w[k h6g[v target v subject v message v end]][
 k rqte[i[point d][k ia[v target v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
 v target v process v act v start v end v state p ag p la p dg p h6a p g3]
 ]]]]]]]
].
d hzoa[first a rest j[a] origin a target a subject a message i[h[a] f] state i[h[a] e]
 process a start d end d anchor d sender h[a] a recipient h[a] a activity h[a] a point h[a] d] c[
 w[k h6i[v first v rest v origin v target v subject v message v end v anchor v sender v recipient v activity v point]][
 c[i[last a][k hznz[c[v sender][v last] v target c[v activity][v last] v subject v message v state
 v process v start v end v anchor]]][q[v rest][v first][i[previous a step a][v step]]]]
].
d hzob[first a rest j[a] origin a target a subject a message i[h[a] f] state i[h[a] e]
 process a start d end d anchor d sender h[a] a recipient h[a] a activity h[a] a point h[a] d] c[
 w[k hzoa[v first v rest v origin v target v subject v message v state v process v start v end v anchor
 v sender v recipient v activity v point]][
 k raf[i[scene d][k ia[v target v anchor v scene]] i[left d right d][k ic[v left v right v anchor]]
 v target s[v state] v process v start v end v anchor p ag p la]]
].
d hzoc[audience a reference d origin a subject a message i[h[a] f] state i[h[a] e] anchor d
 firsts h[a] a tails h[a] j[a] processes h[a] a starts h[a] d ends h[a] d
 sender h[a] a recipient h[a] a activity h[a] a point h[a] d extent h[h[a] c h[a] c] c] c[
 w[k rqsz[v audience v reference p h6t p aa]][k rqsw[i[person a][k h6t[v audience v person v reference]]
 i[target a][k hzob[c[v firsts][v target] c[v tails][v target] v origin v target v subject v message v state
 c[v processes][v target] c[v starts][v target] c[v ends][v target] v anchor v sender v recipient v activity v point]] v extent]]
].
'''


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzny','hzoc','rqsx','rqsy'])
    library=deepcopy(core);library['declarations']=closure(doc,['hznx'])
    basis=dict(status='assessed_response_disposition_with_causal_receipt_and_retention',document=FULL,
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
    print('Described response profiles connected to causal receipt and retention',flush=True)


if __name__=='__main__':main()
