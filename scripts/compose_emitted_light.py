"""Compose one-way light paths using the existing synchronized local event times."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sax[path h[b] c start h[b] c end h[b] c speed h[b] c] c[
 w[k ba[v path]][w[k ba[v start]][w[k ba[v end]][w[k ba[v speed]][
 w[k bg[k bb[n p a b] v path]][w[k bg[v start v end]][w[k bg[k bb[n p a b] v speed]][
 k sag[k sah[v speed k bf[v end v start]] v path p bc]
 ]]]]]]]
].
d say[path b start b end b speed b lengthscale b timescale b speedscale b] c[
 w[k aa[n p a b v lengthscale]][w[k aa[n p a b v timescale]][w[k aa[n p a b v speedscale]][
 w[k aa[n p a b v path]][w[k aa[v start v end]][w[k aa[n p a b v speed]][
 e[k ad[k ad[v speedscale v speed] k ad[v timescale k ab[v end k ac[v start]]]]][k ad[v lengthscale v path]]
 ]]]]]]
].
d saz[ray a emitter a emission a frame a context d bodies h[a] c emitted h[a a a a d] c resting h[a a a d] c moving h[a a a d] c] c[
 w[c[v bodies][v emitter]][w[c[v emitted][v ray v emitter v emission v frame v context]][
 w[x[c[v resting][v emitter v frame v emission v context]][c[v moving][v emitter v frame v emission v context]]][
 u[w[c[v resting][v emitter v frame v emission v context]][c[v moving][v emitter v frame v emission v context]]]
 ]]]
].
'''


MEANINGS={
    'sax':'正の光路長・経過時間・速度について、速度×経過時間＝光路長を実切断の両方向の包含で課す。往復の距離を2倍する式と区別する。',
    'say':'有理数の光路長・始終時刻・速度を、正の各単位尺度で換算した片道の速度条件。',
    'saz':'同じ光・放出元の物体・放出出来事・基準系・文脈を結び、放出時の静止か運動かが排他的に指定されている。未分類や矛盾した分類を静止と補完しない。'}


def generic_composed():
    base=(ROOT/'examples/v014/roundtrip-speed.noema').read_text(encoding='utf-8')
    doc=parse(base+definitions())
    basis=deepcopy(json.loads((ROOT/'data/roundtrip-speed-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='emitted-light-basis-v1',document='examples/v014/emitted-light.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'saxとsayは区間の速度条件。瞬間的な速さを述べるには必要な全ての部分区間を対象とする範囲指定が別に必要。',
        'sazの静止・運動は、同じ放出出来事における同じ基準系との関係として評価する。光の速さと光源の速さを足す規約は含まない。',
        '静止光源と運動光源の両方が実際に観測されたという存在主張は追加しない。選択範囲とその完全性は呼出側の条件である。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    previous=parse((ROOT/'examples/v014/einstein-law-invariance.noema').read_text(encoding='utf-8'))
    statements,previous['statements']=previous['statements'],[]
    text=format_graph(previous,'compact')+definitions()+'''
r wa[a a a a d] c.r wb[a] c.r wc[a a a a d] c.r wd[a a a d] c.r we[a a a d] c.
r wf[a] a.r wg[a] a.r wh[a] a.r wi[a] a.r wj[a] a.r wk[a] a.r wl[a] a.r wm[a] a.r wn[a] a.
r wo[a] h[b] c.r wp[a] h[b] c.r wq[a] h[b] c.
r wr[a a a a a a h[b] c d] c.r ws[a a a d] c.r wt[] a.r wu[] a.r wv[] a.
d sba[segment a value h[b] c context d synchrony h[a a a a d] c rate h[h[b] c h[b] c h[b] c h[b] c] c] c[
 w[k cf[k wf[v segment]]][w[k saz[k wf[v segment] k wg[v segment] k wh[v segment] k ra[] v context p wb p wc p wd p we]][
 w[x[e[k wh[v segment]][k wi[v segment]]][k cg[k wf[v segment] k wh[v segment] k wi[v segment] k ra[]]]][
 w[k cg[k wf[v segment] k wi[v segment] k wj[v segment] k ra[]]][
 w[k tk[k wf[v segment] k wi[v segment] k wj[v segment] k ra[]]][
 w[k ti[k ta[]]][w[k tj[k ta[] k rb[] k tb[]]][
 w[k wr[v segment k wf[v segment] k wi[v segment] k wj[v segment] k ra[] k ta[] k wq[v segment] v context]][
 w[k qt[k wi[v segment] k wk[v segment] k wm[v segment] k wo[v segment] v context v synchrony]][
 w[k qt[k wj[v segment] k wl[v segment] k wn[v segment] k wp[v segment] v context v synchrony]][
 c[v rate][k wq[v segment] k wo[v segment] k wp[v segment] v value]
 ]]]]]]]]]]
].
d sbb[value h[b] c context d synchrony h[a a a a d] c rate h[h[b] c h[b] c h[b] c h[b] c] c] c[
 w[k ws[k ra[] k rb[] k ta[] v context]][
 k sak[v value i[segment a][k wa[v segment k ra[] k rb[] k ta[] v context]]
 i[segment a speed h[b] c][k sba[v segment v speed v context v synchrony v rate]]]
 ]
].
d sbc[value h[b] c context d] c[k sbb[v value v context p qo p sax]].
d sbd[] e[b context[k sbc[k tc[] v context]]].
'''
    doc=parse(text)
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k vl[k wt[] k rd[] r[k sbd[]] k rh[] k ri[]]].
s[w[k ug[k wu[] k rd[] r[k saw[]] k wv[] k ri[]]][k ug[k wu[] k rd[] r[k sbd[]] k wv[] k ri[]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-law-invariance-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-emitted-light-basis-v1',document='examples/v014/einstein-emitted-light.noema')
    basis['definitions'].update(MEANINGS)
    meanings=[
        ('wa',['segment','frame','time_unit','length_unit','context'],'光速度の法則で対象とする伝播区間。放出元の静止・運動によって除外しない。必要な全ての部分区間を範囲へ含める。'),
        ('wb',['emitter'],'放出元となる物体。時計や座標系そのものとの同一視はしない。'),
        ('wc',['ray','emitter','emission','frame','context'],'指定基準系・文脈において、同じ光が指定物体から指定出来事で放出される。'),
        ('wd',['emitter','frame','emission','context'],'同じ放出出来事で、その物体が指定基準系に対して静止する。'),
        ('we',['emitter','frame','emission','context'],'同じ放出出来事で、その物体が指定基準系に対して運動する。物体の速度値や等速性は補わない。'),
        ('wf',['segment'],'区間を伝播する光。'),('wg',['segment'],'その光の放出元の物体。'),
        ('wh',['segment'],'その光の放出出来事。'),('wi',['segment'],'対象区間の始点出来事。放出自体または同じ光がそこから伝播した先の出来事。'),
        ('wj',['segment'],'対象区間の終点出来事。'),('wk',['segment'],'始点の局所時計。'),('wl',['segment'],'終点の局所時計。'),
        ('wm',['segment'],'始点の場所。'),('wn',['segment'],'終点の場所。'),('wo',['segment'],'始点の局所時計の読み。'),
        ('wp',['segment'],'終点の局所時計の読み。'),('wq',['segment'],'対象区間の光路長の読み。端点間の距離だけとは区別する。'),
        ('wr',['segment','ray','start','end','frame','length_unit','path_length','context'],'同じ伝播区間・光・両端出来事の光路長が、指定基準系・長さ単位・文脈で指定値になる。経路長の幾何学的な構成は未完。'),
        ('ws',['frame','time_unit','length_unit','context'],'waの範囲が法則に必要な光線と部分区間を尽くすという前提。観測済みの一区間や一方の光源分類だけへ範囲を縮めない。'),
        ('wt',[],'光速度不変の第二原理を定義として提示する本文箇所。'),
        ('wu',[],'二つの原理を後続議論の根拠として採用する導入箇所。'),
        ('wv',[],'二つの原理に依拠する後続議論の範囲。先行の同期に関する仮定の範囲とは別に保持する。')]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sba':'同じ光・放出元・区間を結び、光路長と始終の局所時計の読みを片道の速度判定へ渡す。両時計はqtで同じ参照時計・基準系・時間単位に接続し、放出元が動いていることと時計が動いていることを区別する。',
        'sbb':'完全と指定した非空の全区間で、同じ速度値をsbaへ渡す。光源分類ごとに別の速度を選ばない。',
        'sbc':'sbbの同期条件を既存qo、速度条件を実切断のsaxとした第二原理の成立条件。',
        'sbd':'前節の共通速度値tcを使う第二原理の状況ごとの内容。定義提示と、後続推論の仮定採用へ記述として渡す。'})
    basis['unresolved']+=generic_composed()[1]['unresolved'][-3:]+[
        'u0024・u0026〜u0028の部分草案。光の伝播・放出・物体・光路長・運動の基礎説明、全区間の完全性、原刊画像との照合と全文の意味確認は未完。',
        '真空中という適用範囲を、前節のVの定義から引き継ぐ解釈。媒質中の全光線まで同じ速さだと主張するものではない。',
        '有限検査では同期と実数の速度条件への結合を別の判定関数で確認する。実切断全域の物理モデルを有限近似して証明したことにはしない。',
        '光路長の全部分区間での条件を要求するが、微分による瞬間速度との同値性を今回機械的に証明したわけではない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/emitted-light-basis-v1.json'),(source_composed,'data/einstein-emitted-light-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored emitted-light document differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Emitted light, synchronized endpoint times and two-principle premises composed')


if __name__=='__main__':main()
