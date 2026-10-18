"""Bind the origin's own departure before a future completed dissemination."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-transmitted-profiles.noema'
PARENT_BASIS='data/transmitted-profiles-basis-v1.json'
FULL='examples/v016/kant-emancipated-transmission.noema'
CORE='examples/v016/emancipated-transmission-core.noema'
LIBRARY='examples/v016/prior-completion.noema'
BASIS='data/emancipated-transmission-basis-v1.json'
MEANINGS={
 'rqtg':'同じ厳密に順序付けられた履歴に、先行完了点・後続開始点・基準点が属し、先行完了が後続開始より厳密に前で、後続開始が基準点以前である。順序だけから因果や出来事の存在を推定しない。',
 'hzod':'同じ発信者が、同じ自己活動の過程と前後点で、既存h4pの自立への変化を完了している。その完了が最初の発信より前であることを、同じ発信者・基準点の履歴と順序で要求する。',
 'hzoe':'受領・理解・取得・持続のhzobと、最初の発信者のhzodを結ぶ。最初の発信点は同じ伝達経路のfirstとpointから取り出す。中継者の離脱や最後の受領時刻への比較に差し替えない。',
 'hzof':'指定期間枠に基準の開始点より後があることを確認し、同じ枠内で開始点より後に取得を完了した受け手の範囲を作る。各人にhzoeを要求し、発信者の同じ離脱過程・前後・性向記述を共用する。想定読者は参照文脈で固定する。',
}
LIMITS=[
 '自ら依存を脱することを、本人の精神的な働きかけで、他者の指導なしに理解力を使える状態へ移るh4pとして読む候補である。原文の全ての離脱がこの自己形成過程だけによるとは確定しない。',
 '本人の関与と同じ活動による結果生成を要求するが、他者の助力や他の原因を排除しない。依存を脱した事実だけから、以後の全判断が自立的であるとは補わない。',
 'nachdemの順序を完了と最初の発信の厳密な前後として読む。二つを同じ粗い時点へ丸めた場合は、この粒度では順序を確認できない。全活動の非重複や、離脱が伝達の原因であることは追加しない。',
 'hzofは指定した経過内での将来完了という内容を作る。開始点以前に発信が始まり、以後に受け手の取得が完了する場合も許す。候補の内容が成立したことを現実の予言や必然性へ昇格させない。',
 '発信者の履歴と期間枠は別に確認し、同じ離脱の前後と、各人の最初の発信・取得の前後を両方へ接続する。期間枠の完全性や実世界の未来を有限検査で証明しない。',
 '周囲という社会的範囲を単なる想定読者と同一化しない。頚木の比喩、発信者の恒常的な自己思考と任用、適切な性向基準、将来の様相と著者帰属への全文接続は未完。',
 '既存32文と全意味規約・七単位の確認を保存する。本文の新しい無条件主張や意味確認済み単位は増やさず、原文範囲には部分構成として記録する。',
]


def definitions():
    return '''
d rqtg[history h[d] c before h[d d] c attained d begun d anchor d] c[
 w[k ta[v history v before]][w[c[v history][v attained]][w[c[v history][v begun]][
 w[c[v history][v anchor]][w[c[v before][v attained v begun]][x[e[v begun][v anchor]][c[v before][v begun v anchor]]]]]]]
].
d hzod[origin a process a start d attained d firstsent d anchor d] c[
 w[k h4p[v origin v process v start v attained v anchor]][
 k rqtg[i[point d][k ia[v origin v anchor v point]] i[first d last d][k ic[v first v last v anchor]]
 v attained v firstsent v anchor]]
].
d hzoe[first a rest j[a] origin a target a subject a message i[h[a] f] state i[h[a] e]
 process a start d end d anchor d sender h[a] a recipient h[a] a activity h[a] a point h[a] d
 departure a prior d attained d] c[
 w[k hzod[v origin v departure v prior v attained c[v point][v first] v anchor]][
 k hzob[v first v rest v origin v target v subject v message v state v process v start v end v anchor
 v sender v recipient v activity v point]]
].
d hzof[audience a reference d origin a subject a message i[h[a] f] state i[h[a] e]
 frame a initial d anchor d departure a prior d attained d
 firsts h[a] a tails h[a] j[a] processes h[a] a starts h[a] d ends h[a] d
 sender h[a] a recipient h[a] a activity h[a] a point h[a] d extent h[h[a] c h[a] c] c] c[
 w[k hzne[v frame v initial v anchor]][w[k h7q[v frame v anchor v prior]][w[k h7q[v frame v anchor v attained]][
 w[k rqsz[v audience v reference p h6t p aa]][
 k rqsw[i[person a][k h6t[v audience v person v reference]]
 i[target a][w[k h7q[v frame v anchor c[v point][c[v firsts][v target]]]][
 w[k h7q[v frame v anchor c[v starts][v target]]][w[k h7q[v frame v anchor c[v ends][v target]]][
 w[k ic[v initial c[v ends][v target] v anchor]][
 k hzoe[c[v firsts][v target] c[v tails][v target] v origin v target v subject v message v state
 c[v processes][v target] c[v starts][v target] c[v ends][v target] v anchor
 v sender v recipient v activity v point v departure v prior v attained]]]]]]
 v extent]]]]]
].
'''


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,['hzof','hzny','rqsx','rqsy'])
    library=deepcopy(core);library['declarations']=closure(doc,['rqtg'])
    basis=dict(status='origin_self_departure_before_transmission_and_future_recipient_acquisition',document=FULL,
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
    print('Origin departure bound before the first transmission and future acquisition',flush=True)


if __name__=='__main__':main()
