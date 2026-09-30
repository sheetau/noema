"""Compose local event readings and comparisons with one common reference clock."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
d sae[event a clock a place a frame a unit a value h[b] c clocks h[a] c located h[a a a] c stationary h[a a] c units h[a] c reads h[a a a a h[b] c] c] c[
 w[c[v clocks][v clock]][w[c[v stationary][v clock v frame]][w[c[v units][v unit]][w[
  c[v located][v clock v place v frame]
 ][w[c[v located][v event v place v frame]][c[v reads][v clock v event v frame v unit v value]]]]]]
].
d saf[event a clock a place a reference a frame a unit a value h[b] c context d clocks h[a] c located h[a a a] c stationary h[a a] c units h[a] c reads h[a a a a h[b] c] c synchrony h[a a a a d] c] c[
 w[k sae[v event v clock v place v frame v unit v value v clocks v located v stationary v units v reads]][w[
  c[v clocks][v reference]
 ][w[c[v stationary][v reference v frame]][c[v synchrony][v clock v reference v frame v unit v context]]]]
].
d sag[first h[b] c second h[b] c included h[h[b] c h[b] c] c] c[
 w[c[v included][v first v second]][c[v included][v second v first]]
].
'''


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'event-time-basis-v1','document':'examples/v014/event-time.noema','primitives':[],
        'definitions':{
            'sae':'同じ基準系・時間単位について、静止時計と出来事が同じ場所にあり、その時計の当該出来事の時点の読みが与えられた値である。別の受信出来事の読みを混ぜない。',
            'saf':'saeの局所的な読みを、同じ基準系で静止する参照時計との同期へ結ぶ。同期の対象・単位・評価文脈を保持する。',
            'sag':'二つの数値表現について、包含関係が両方向で成立する。一方向の大小比較や関数の同一性で、値の一致を代用しない。'},
        'unresolved':[
            '時計・場所・静止・読み・同期の関係は引数で与える。読みの値が実数の条件を満たすことは呼出側で要求する。',
            '関係として候補の読みを検査し、値を任意に生成する全域関数とはしない。読みの存在・一意性、精度や時計の指示機構は別に要する。',
            '同じ場所と同じ時点の読みを結ぶ条件であり、光の伝播時間を補正して遠隔測定を行う方法はまだ含まない。',
            'sagは包含引数の意味規約に依存する。原文接続では実数の下側切断の包含bcを使い、実数条件を別に確認する。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-synchrony-network.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'''
r rj[] a.r uj[a a i[h[a a a h[b] c d] c] a d] c.
d qt[event a clock a place a value h[b] c context d synchrony h[a a a a d] c] c[
 k saf[v event v clock v place k rc[] k ra[] k rb[] v value v context p ca p cb p cc p ci p ce v synchrony]
].
d qu[event a clock a place a value h[b] c context d] c[
 w[k ba[v value]][k qt[v event v clock v place v value v context p qo]]
].
d qw[first a firstclock a firstplace a second a secondclock a secondplace a firstvalue h[b] c secondvalue h[b] c context d] c[
 w[k qu[v first v firstclock v firstplace v firstvalue v context]][w[
  k qu[v second v secondclock v secondplace v secondvalue v context]
 ][k sag[v firstvalue v secondvalue p bc]]]
].
'''
    doc=parse(text)
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'\ns[k uj[k rj[] k rd[] r[p qu] k rh[] k ri[]]].\n')
    basis=deepcopy(json.loads((ROOT/'data/einstein-synchrony-network-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-event-time-basis-v1',document='examples/v014/einstein-event-time.noema')
    basis['definitions'].update(generic_composed()[1]['definitions'])
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('rj',[],'同期した局所時計による出来事の時刻の定義を提示する本文箇所。'),
        ('uj',['node','author','assignment_rule','scope','context'],'著者が指定した範囲で、記述された出来事・時計・場所・読み・文脈の関係を、時刻の付与規則として定義に採用する。規則への帰属であり、全出来事の読みの存在や真理を検査器が認定することではない。')):
        d=decls[name]
        basis['primitives'].append({'symbol':name,'parameters':d['parameters'],'result':d['result'],'arguments':args,'meaning_ja':meaning})
    basis['definitions'].update({
        'qt':'局所的な出来事の読みと同期を、同じ参照時計rc・静止基準系ra・単位rbへ結ぶ接続。同期関係を引数に取るので、接続部分と実数条件の検査を分離できる。',
        'qu':'読みが実数の下側切断であり、qtの同期関係が既存の光往復全試行の定義qoである場合の時刻付与関係。新しい読みを生成せず、提示された値の条件を検査する。',
        'qw':'同じ基準系・単位・文脈・参照時計で評価した二出来事の読みが、切断として同じ値になるという同時性の部分的な条件。異なる場所の別々の局所時計を許す。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0018の時刻の付与規則と、同時性を等しい付与値で扱う条件を追加した。冒頭の定義を得たという談話、思考上の物理的経験の役割、全時刻決定の存在と一意性は未完。',
        '局所時計による出来事の時刻と、遠隔地で光を受け取る出来事の時刻を分ける。原文u0012の観測者による代替方式や位置依存の全説明は未記述。',
        '有限検査で同期を明示した関係として与える場合と、実数全域のqo・baを含む定義を評価する場合を区別する。全物理モデルを検証したとはしない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/event-time-basis-v1.json'),(source_composed,'data/einstein-event-time-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored event time differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Local event time and common-reference comparison composed')


if __name__=='__main__':main()
