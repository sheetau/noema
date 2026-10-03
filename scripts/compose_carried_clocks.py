"""Compare a carried clock with local rest-frame time at each current position."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def definitions():
    return '''
d sct[event a clock a place a frame a unit a value h[b] c context d clocks h[a] c units h[a] c located h[a a a a d] c reads h[a a a a h[b] c] c] c[
 w[c[v clocks][v clock]][w[c[v units][v unit]][w[c[v located][v clock v event v place v frame v context]][c[v reads][v clock v event v frame v unit v value]]]]
].
d scu[own h[b] c local h[b] c ownreading h[h[b] c] c localreading h[h[b] c] c same h[h[b] c h[b] c] c] c[
 w[c[v ownreading][v own]][w[c[v localreading][v local]][c[v same][v own v local]]]
].
'''


MEANINGS={
    'sct':'指定出来事における時計の場所と読みを、同じ基準系・時間単位・文脈へ結ぶ。時計がその基準系に静止している条件は含まない。',
    'scu':'同じ比較における二つの読みの記録が成立し、指定の値の同一性で両指示が一致する。値だけの一致や片方だけの記録では成立しない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/geometric-replacement.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/geometric-replacement-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='carried-clocks-basis-v1',document='examples/v014/carried-clocks.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '時計の出来事ごとの位置と読みは別の物理的意味規約に必要。静止対象の常設場所の関係を流用しない。',
        '指示の一致は局所比較の条件であり、離れた二時計へ光往復の中点条件を適用した結果とは分ける。',
        '動く時計の指示を静止系の時刻へ合わせる機構、時計の自然な進み方、補正の操作は記述していない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-geometric-replacement.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    doc=parse(format_graph(old,'compact')+definitions()+'''
r zaa[a a a d] c.r zab[a a a a d] c.r zac[a a d] c.
r zad[a] a.r zae[a] a.r zaf[a] a.r zag[a] h[b] c.r zah[a] h[b] c.
r zai[a a d] c.r zaj[] a.r zak[] a.r zal[] a.r zam[] a.
r zan[a a i[h[a d] c] a a d] c.r zao[a a a d] c.
d scv[clock a endpoint a event a place a localclock a own h[b] c local h[b] c context d synchrony h[a a a a d] c same h[h[b] c h[b] c] c valid h[h[b] c] c] c[
 w[u[e[v clock][v localclock]]][w[u[e[v clock][k rc[]]]][
 w[c[v valid][v own]][w[c[v valid][v local]][w[k xm[v clock k ra[] v context]][
 w[k zaa[v clock v endpoint k xi[] v context]][w[k xf[v endpoint k xi[] k ra[] v context]][
 w[k xg[v endpoint v event v place k ra[] v context]][
 k scu[v own v local
 i[value h[b] c][k sct[v event v clock v place k ra[] k rb[] v value v context p ca p ci p zab p ce]]
 i[value h[b] c][k qt[v event v localclock v place v value v context v synchrony]] v same]
 ]]]]]]]]
].
d scw[clock a endpoint a context d synchrony h[a a a a d] c same h[h[b] c h[b] c] c valid h[h[b] c] c] c[
 w[k zai[v clock k ra[] v context]][w[g record a[k zac[v record v clock v context]]][
 f record a[y[k zac[v record v clock v context]][
 k scv[v clock v endpoint k zad[v record] k zae[v record] k zaf[v record] k zag[v record] k zah[v record] v context v synchrony v same v valid]
 ]]]]
].
d scx[clock a context d] c[
 g endpoint a[k scw[v clock v endpoint v context p qo p sca p ba]]
].
d scz[context d synchrony h[a a a a d] c same h[h[b] c h[b] c] c valid h[h[b] c] c] c[
 w[k xa[k xi[]]][w[k xm[k xi[] k ra[] v context]][w[u[e[k xn[]][k xo[]]]][w[u[e[k zaj[]][k zak[]]]][
 w[k scw[k zaj[] k xn[] v context v synchrony v same v valid]][k scw[k zak[] k xo[] v context v synchrony v same v valid]]
 ]]]]
].
d scy[] e[b context[k scz[k yd[] p qo p sca p ba]]].
''')
    doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k zal[] k rd[] r[k scy[]] k xy[] k ri[]]][k zao[k y2[] k zal[] k xy[] k ri[]]]].
s[k zan[k zam[] k rd[] r[p scx] k ra[] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-geometric-replacement-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-carried-clocks-basis-v1',document='examples/v014/einstein-carried-clocks.noema')
    basis['definitions'].update(MEANINGS)
    meanings=[
        ('zaa',['clock','endpoint','rod','context'],'時計が同じ棒の指定端点へ取り付けられ、その設定で端点と共に動く。取り付けの機構は未説明。'),
        ('zab',['clock','event','place','frame','context'],'その出来事で時計が現在その場所にある。時計の全期間の設置場所とは区別する。'),
        ('zac',['record','clock','context'],'その時計の指示と静止系の局所時刻を照合する出来事の記録。'),
        ('zad',['record'],'照合記録の出来事。'),('zae',['record'],'その出来事における時計と棒端点の現在位置。'),
        ('zaf',['record'],'その現在位置に静止する静止系の局所時計。別の出来事では別の時計を使える。'),
        ('zag',['record'],'動く時計の当該出来事の読み。'),('zah',['record'],'同じ出来事の静止系の局所時刻。'),
        ('zai',['clock','frame','context'],'zacの記録がこの時計について必要な全出来事を尽くすという前提。有限の観測例だけから認定しない。'),
        ('zaj',[],'棒の一方の端点に取り付けた時計。'),('zak',[],'棒の他方の端点に取り付けた別の時計。'),
        ('zal',[],'両端へ時計を付ける思考上の設定を追加する本文箇所。'),('zam',[],'時計を静止系において同期していると呼ぶ本文箇所。'),
        ('zan',['node','author','qualification','frame','scope','context'],'著者がこの条件を満たす時計を、指定基準系において同期した時計と呼ぶ規約を提示する。時計自体の静止や、動く系での光往復中点条件を含意しない。'),
        ('zao',['prior_node','added_node','scope','context'],'同じ思考上の設定に、先行箇所へ追加して後の条件を置く。別々の無関係な想定として扱わない。'),
    ]
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'scv':'端点と動く時計の同じ出来事・現在位置を結び、時計の指示と、その場所の参照時計へ同期した静止時計の指示を比較する。動く時計へ静止条件を課さない。',
        'scw':'非空かつ完全と指定した同じ時計の全照合記録が、同じ端点への取り付けとscvを満たす。記録間で局所時計や現在位置が変わることを許す。',
        'scx':'全記録で静止系の局所時刻を表示する時計の条件を、実数・値の一致・静止時計の同期の既存定義へ接続する。',
        'scz':'同じ動く棒の異なる二端点に異なる時計を取り付け、両時計の全記録で局所時刻との一致を要求する。',
        'scy':'sczを先行する棒の運動設定ydと実数条件へ接続した追加の想定内容。'})
    basis['unresolved'] += generic_composed()[1]['unresolved'][-3:] + [
        'u0035の部分草案。時計の取り付け、読み、全出来事を尽くす範囲の根拠、命名・追加想定の一般的な意味は未完。',
        '静止系の時刻を表示するという思考上の設定であり、補正していない移動時計が自然にその指示を保つという物理法則は主張しない。',
        'u0036以降の共動観測者、光往復の出来事と到達時間、動く系での同期判定との相違は未接続。',
        '連続する全時刻の物理モデル、原刊照合、全文の意味確認は残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/carried-clocks-basis-v1.json'),(source_composed,'data/einstein-carried-clocks-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored carried-clock draft differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Carried-clock readings and local rest-frame time comparisons composed')


if __name__=='__main__':main()
