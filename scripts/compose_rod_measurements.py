"""Keep comoving-ruler and simultaneous-endpoint measurements as distinct methods."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sbe[object a observer a ruler a frame a unit a length h[b] c context d objects h[a] c observers h[a] c rulers h[a] c stationary h[a a d] c aligned h[a a a d] c reads h[a a a a a h[b] c d] c] c[
 w[c[v objects][v object]][w[c[v observers][v observer]][w[c[v rulers][v ruler]][
 w[c[v stationary][v object v frame v context]][w[c[v stationary][v observer v frame v context]][w[c[v stationary][v ruler v frame v context]][
 w[c[v aligned][v ruler v object v frame v context]][c[v reads][v observer v ruler v object v frame v unit v length v context]]
 ]]]]]]
].
d sbf[object a first a last a firstevent a lastevent a firstplace a lastplace a frame a context d endpoints h[a a a d] c located h[a a a a d] c] c[
 w[u[e[v first][v last]]][w[c[v endpoints][v first v object v frame v context]][w[c[v endpoints][v last v object v frame v context]][
 w[c[v located][v first v firstevent v firstplace v frame v context]][c[v located][v last v lastevent v lastplace v frame v context]]
 ]]]
].
d sbg[length h[b] c] c[w[k ba[v length]][k bg[k bb[n p a b] v length]]].
'''


MEANINGS={
    'sbe':'同じ対象・観測者・物差しが指定基準系で静止し、物差しをその対象へ合わせ、同じ観測者・物差し・対象・基準系・単位・文脈の長さの読みを得る直接測定の条件。',
    'sbf':'同じ対象の異なる二端点を、それぞれの出来事・場所・共通基準系・文脈に結び付ける。両端点の位置を別の出来事や物体から混ぜない。同時性は別に要求する。',
    'sbg':'長さの候補値が実数の下側切断として有効であり、正である。'}


def generic_composed():
    text=(ROOT/'examples/v014/emitted-light.noema').read_text(encoding='utf-8')+definitions()
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/emitted-light-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='rod-measurements-basis-v1',document='examples/v014/rod-measurements.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '対象の形状、端点、物差し、物差しを当てる操作、尺度の読みの構成説明は引数となる関係の意味規約に必要。',
        'sbfの位置関係は出来事を明示する。動く端点の位置を、静止対象の全期間にわたる設置場所と同一視しない。',
        '二方法の値の一致や収縮の式はこれらの測定条件から補わない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-emitted-light.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r xa[a] c.r xb[a] c.r xc[a] c.r xd[a a a d] c.r xe[a a a a a h[b] c d] c.
r xf[a a a d] c.r xg[a a a a d] c.r xh[a a a a a a h[b] c d] c.
r xi[] a.r xj[] a.r xk[] a.r xl[] a.r xm[a a d] c.
r xn[] a.r xo[] a.r xp[] a.r xq[] a.r xr[] a.r xs[] a.r xt[] a.r xu[] a.
r xv[] h[b] c.r xw[] a.r xx[] a.r xy[] a.r xz[a a i[h[h[b] c d] c] a d] c.
r x2[] h[b] c.r x3[] h[b] c.r x4[a a d] c.
d sbh[value h[b] c context d validlength h[h[b] c] c] c[
 w[c[v validlength][v value]][w[k ti[k ta[]]][w[k sat[k ra[] k xl[] v context]][w[k xm[k xi[] k ra[] v context]][
 k sbe[k xi[] k xk[] k xj[] k xl[] k ta[] v value v context p xa p xb p xc p x4 p xd p xe]
 ]]]]
].
d sbi[value h[b] c context d] c[k sbh[v value v context p sbg]].
d sbj[value h[b] c context d synchrony h[a a a a d] c validlength h[h[b] c] c equalvalue h[h[b] c h[b] c] c] c[
 w[c[v validlength][v value]][w[k xa[k xi[]]][w[k xb[k xk[]]][w[k xc[k xj[]]][
 w[k xm[k xi[] k ra[] v context]][w[k x4[k xj[] k ra[] v context]][w[k ti[k ta[]]][
 w[k sbf[k xi[] k xn[] k xo[] k xp[] k xq[] k xt[] k xu[] k ra[] v context p xf p xg]][
 w[k qt[k xp[] k xr[] k xt[] k x2[] v context v synchrony]][
 w[k qt[k xq[] k xs[] k xu[] k x3[] v context v synchrony]][
 w[c[v equalvalue][k x2[] k x3[]]][w[c[v equalvalue][k x2[] k xv[]]][
 w[k th[k xt[] k xu[] k ra[] k ta[] v value]][
 k xh[k xk[] k xj[] k xt[] k xu[] k ra[] k ta[] v value v context]
 ]]]]]]]]]]]]]
].
d sbk[value h[b] c context d] c[
 w[k ba[k x2[]]][w[k ba[k x3[]]][w[k ba[k xv[]]][
 k sbj[v value v context p qo p sbg i[first h[b] c last h[b] c][k sag[v first v last p bc]]]
 ]]]
].
'''
    doc=parse(text)
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k xz[k xw[] k rd[] r[p sbi] k xy[] k ri[]]].
s[k xz[k xx[] k rd[] r[p sbk] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-emitted-light-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-rod-measurements-basis-v1',document='examples/v014/einstein-rod-measurements.noema')
    basis['definitions'].update(MEANINGS)
    meanings=[
        ('xa',['rod'],'測定対象として選んだ棒。細長い形状・剛性からの構成説明は未完。'),
        ('xb',['observer'],'測定の観測者。'),('xc',['ruler'],'長さの比較に使う物差し。'),
        ('xd',['ruler','rod','frame','context'],'指定基準系・文脈で、その物差しをその棒に当てて長さを比較する配置。'),
        ('xe',['observer','ruler','rod','frame','length_unit','length','context'],'同じ観測者がその物差しを用いてその棒の長さを直接読み取る関係。単なる場所の距離の値とは分ける。'),
        ('xf',['endpoint','rod','frame','context'],'その対象がその棒の端点であるという指定。'),
        ('xg',['endpoint','event','place','frame','context'],'動き得る端点が、指定出来事において指定基準系のその場所にある。'),
        ('xh',['observer','ruler','first_place','last_place','frame','length_unit','length','context'],'その観測者が同じ物差しを用い、指定基準系で二地点間の距離を測る関係。棒へ直接物差しを当てる測定とは区別する。'),
        ('xi',[],'二方法で測る同じ棒。'),('xj',[],'二方法で使う同じ物差し。基準系に対する静止条件は方法ごとに異なる。'),
        ('xk',[],'二方法で扱う観測者。'),('xl',[],'棒・物差し・観測者が共に静止する移動側の基準系。'),
        ('xm',['object','frame','context'],'対象が指定基準系に対してこの測定文脈で動いているという明示的な関係。静止の記述がないだけで補わない。'),
        ('xn',[],'棒の一方の端点。'),('xo',[],'棒の他方の端点。'),('xp',[],'一方の端点の位置を定める出来事。'),
        ('xq',[],'他方の端点の位置を定める出来事。'),('xr',[],'一方の出来事の場所にある静止系の時計。'),
        ('xs',[],'他方の出来事の場所にある静止系の時計。'),('xt',[],'一方の出来事がある静止系の場所。'),
        ('xu',[],'他方の出来事がある静止系の場所。'),('xv',[],'両端を評価する指定時刻。数値は補わない。'),
        ('xw',[],'棒と共に動く物差しによる方法の本文箇所。'),('xx',[],'静止系の同時刻の二地点の距離による方法の本文箇所。'),
        ('xy',[],'二つの測定操作を考察する思考上の設定。現実の測定の実行済み事実とはしない。'),
        ('xz',['node','author','method','scope','context'],'著者がこの考察範囲で、記述された長さ候補の条件を測定方法として提示する。値の存在や一意性、二方法の値の一致を主張しない。'),
        ('x2',[],'一方の局所時計の出来事時点の読み。'),('x3',[],'他方の局所時計の出来事時点の読み。'),
        ('x4',['object','frame','context'],'対象が指定した測定設定でその基準系に静止している。二方法の別々の設定を文脈で区別し、同じ物差しが同時に相対運動する両基準系で静止すると主張しない。')]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sbh':'同じ棒・観測者・物差しが移動側基準系で静止する直接測定を構成する。静止側との等速並進の設定と、棒が静止側では動いていることを保持する。',
        'sbi':'sbhの長さ条件を実数の正値性sbgへ接続した方法aの候補判定。',
        'sbj':'同じ棒の二端点を同じ指定時刻における静止系の二地点へ結び、その距離を同じ物差しで測る方法。両端はqtによって同じ参照時計へ同期した局所時計で時刻評価する。物差しは静止系で静止し、観測者の静止は追加しない。',
        'sbk':'sbjの時計読みと指定時刻を有効な実数とし、同期qo・正の実数長sbg・切断の一致sagへ接続した方法bの候補判定。'})
    basis['unresolved']+=generic_composed()[1]['unresolved'][-3:]+[
        'u0030・u0031の二方法の部分草案。u0029の棒の初期長・剛性・軸・運動の付与・問いはまだ接続していない。',
        'u0032以降の長さの命名、静止時の長さとの同値、二原理からの相違の導出、旧運動学への帰属は未記述。',
        'sbiとsbkは候補値の条件であり、全対象に一意の測定値を生成する関数ではない。',
        '有限検査は同期・実数の正値性・実切断の一致への結合を別の判定関数で検査する。全物理モデルの有限近似による証明ではない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/rod-measurements-basis-v1.json'),(source_composed,'data/einstein-rod-measurements-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored rod measurement differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Comoving ruler and simultaneous-endpoint length methods composed')


if __name__=='__main__':main()
