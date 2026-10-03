"""Bind moving-endpoint light travel to carried-clock readings and a midpoint test."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_event_time import ROOT


def both(*args):
    return args[0] if len(args)==1 else 'w['+args[0]+']['+both(*args[1:])+']'


def definitions():
    domain=['k aa[n p a b v length]','u[k aa[v speed n p a b]]','k aa[v speed v light]',
        'k aa[v first v middle]','k aa[v middle v last]']
    out='k ab[v middle k ac[v first]]';back='k ab[v last k ac[v middle]]'
    text='d sda[length b light b speed b first b middle b last b] c['+both(*domain,
        f'e[k ad[k ab[v light k ac[v speed]] {out}]][v length]',
        f'e[k ad[k ab[v light v speed] {back}]][v length]')+'].\n'
    names='length light speed first middle last'.split()
    text+='d sdb['+' '.join(n+' h[b] c' for n in names)+'] c['+both(
        *('k ba[v '+n+']' for n in names),'k bg[k bb[n p a b] v length]',
        'k bc[k bb[n p a b] v speed]','k bg[v speed v light]','k bg[v first v middle]','k bg[v middle v last]',
        'k sag[k sah[k bf[v light v speed] k bf[v middle v first]] v length p bc]',
        'k sag[k sah[k bd[v light v speed] k bf[v last v middle]] v length p bc]')+'].\n'
    reflection=f'k ab[k ab[v origin v length] k ad[v speed {out}]]'
    text+='d sdc[origin b length b light b speed b first b middle b last b] c['+both(*domain,
        f'e[k ab[v origin k ad[v light {out}]]][{reflection}]',
        f'e[k ab[{reflection} k ac[k ad[v light {back}]]]][k ab[v origin k ad[v speed k ab[v last k ac[v first]]]]]')+'].\n'
    text+=f'd sdd[first b middle b last b] c[e[{out}][{back}]].\n'
    text+='''
d sde[ray a depart a reflection a arrive a frame a rays h[a] c travels h[a a a a] c reflects h[a a a] c] c[
 w[u[e[v depart][v reflection]]][w[u[e[v depart][v arrive]]][w[u[e[v reflection][v arrive]]][
 w[c[v rays][v ray]][w[c[v travels][v ray v depart v reflection v frame]][
 w[c[v travels][v ray v reflection v arrive v frame]][c[v reflects][v ray v reflection v frame]]]]]]]
].
'''
    return text


MEANINGS={
    'sda':'正の静止系の棒長r、0以上で光速度V未満の棒速度v、時間順に並ぶ三時刻について、(V-v)(tB-tA)=rと(V+v)(tA後-tB)=rを同時に要求する。',
    'sdb':'sdaの有効な実数の下側切断による記述。正の分母を要求し、除算を分母との積の等式として保持する。v=0は比較用の退化例として許す。',
    'sdc':'同じ有理数座標で、一定速度の二端点と往復光の反射・帰着位置が一致する条件。原点をゼロに固定せず、往路と復路の光速の大きさを同じVとする。',
    'sdd':'三つの有理数時刻について、往路時間と復路時間が等しいという中点条件。試行の設定自体は別に必要。',
    'sde':'同じ光が異なる三出来事を出発・反射・帰着の順に結び、指定基準系で反射する。時計の静止や出発点と帰着点の座標一致を要求しない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/carried-clocks.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/carried-clocks-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='moving-light-trip-basis-v1',document='examples/v014/moving-light-trip.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'sdcの直線軌道は選んだ運動学的モデル。反射・一定光速・剛体の物理的基礎を代数だけで証明しない。',
        '速度は同じ長さ単位と時間単位の商の数値を使う。分母がゼロまたは非正の入力はこの往復設定に含めない。',
        '有理数の代数検査と、実切断全域での演算の一般法則の証明を区別する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-carried-clocks.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zap[a a d] c.r zaq[a a a d] c.r zar[a a a a i[h[h[b] c h[b] c h[b] c] c] d] c.
r zas[] a.r zat[] a.r zau[] a.r zav[] h[b] c.r zaw[] a.r zax[] a.r zay[] a.r zaz[] a.
r za2[] a.r za3[] a.r za4[a a a a a a d] c.
'''
    events={name:'k zad[k '+name+'[]]' for name in ('zas','zat','zau')}
    clauses=[]
    for record,clock,endpoint in (('zas','zaj','xn'),('zat','zak','xo'),('zau','zaj','xn')):
        clauses.extend([f'k zac[k {record}[] k {clock}[] v context]',
            f'k scv[k {clock}[] k {endpoint}[] {events[record]} k zae[k {record}[]] k zaf[k {record}[]] k zag[k {record}[]] k zah[k {record}[]] v context v synchrony v same v valid]'])
    clauses.extend([
        f'k sde[k zax[] {events["zas"]} {events["zat"]} {events["zau"]} k ra[] p cf p cg p ch]',
        f'k tk[k zax[] {events["zas"]} {events["zat"]} k ra[]]',
        f'k tk[k zax[] {events["zat"]} {events["zau"]} k ra[]]',
        f'k za4[k zaw[] k zax[] {events["zas"]} {events["zat"]} {events["zau"]} k ra[] v context]'])
    args='context d synchrony h[a a a a d] c same h[h[b] c h[b] c] c valid h[h[b] c] c'
    text+='d sdf['+args+'] c['+both(*clauses)+'].\n'
    clauses=['u[e[k zay[]][k zaz[]]]','k sdf[v context v synchrony v same v valid]']
    for observer,clock in (('zay','zaj'),('zaz','zak')):
        clauses.extend([f'k xb[k {observer}[]]',f'k zap[k {observer}[] k {clock}[] v context]',
            f'k zaq[k {observer}[] k {clock}[] k ra[] v context]',
            f'k zar[k {observer}[] k zaj[] k zak[] k zaw[] r[p bi] v context]'])
    text+='d sdg['+args+'] c['+both(*clauses)+'].\n'
    text+='''
d sdh[] e[b context[k sdg[k yd[] p qo p sca p ba]]].
d sdi[context d measured h[h[b] c d] c relation h[h[b] c h[b] c h[b] c h[b] c h[b] c h[b] c] c] c[
 w[k ti[k ta[]]][w[k tj[k ta[] k rb[] k tb[]]][w[k yx[v context k yf[]]][
 w[c[v measured][k zav[] k yf[]]][c[v relation][k zav[] k tc[] k yb[] k zag[k zas[]] k zag[k zat[]] k zag[k zau[]]]]]]]
].
d sdj[] e[b context[k sdi[k yd[] p sbk p sdb]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k za2[] k rd[] r[k sdh[]] k xy[] k ri[]]][k zao[k zal[] k za2[] k xy[] k ri[]]]].
s[k zc[k za3[] k rd[] r[k sbd[]] r[k sdj[]] k xy[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-carried-clocks-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-moving-light-trip-basis-v1',document='examples/v014/einstein-moving-light-trip.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'].remove('u0036以降の共動観測者、光往復の出来事と到達時間、動く系での同期判定との相違は未接続。')
    meanings=[
        ('zap',['observer','clock','context'],'観測者が指定時計のそばにいる。具体的な距離範囲は未説明。'),
        ('zaq',['observer','clock','frame','context'],'観測者が時計と共に動く。観測者の全軌道と時計との相対位置からの構成説明は未完。'),
        ('zar',['observer','first_clock','second_clock','trial','criterion','context'],'観測者が同じ試行の二時計に指定した中点条件を適用する。適用したことは、条件が成立するとの判定や時計が同期していることを含意しない。'),
        ('zas',[],'A端の時計の出発時の照合記録。'),('zat',[],'B端の時計の反射時の照合記録。'),('zau',[],'A端の時計の帰着時の照合記録。'),
        ('zav',[],'静止系で測った動く棒の長さrAB。初期静止長yaや光路全長とは分ける。'),
        ('zaw',[],'二観測者が条件を適用する同じ光往復試行。'),('zax',[],'出発・反射・帰着を結ぶ同じ光。'),
        ('zay',[],'A端の時計と共に動く観測者。'),('zaz',[],'B端の時計と共に動く別の観測者。'),
        ('za2',[],'観測者と光往復を追加する想定の本文箇所。'),('za3',[],'光速度の原理から往復時間の式を得ると述べる本文箇所。'),
        ('za4',['trial','ray','depart','reflection','arrival','frame','context'],'条件を適用する試行が、同じ光・三出来事・基準系・文脈からなることを指定する。')]
    declarations={d['name']:d for d in doc['declarations']}
    for name,arguments,meaning in meanings:
        d=declarations[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=arguments,meaning_ja=meaning))
    basis['definitions'].update({
        'sdf':'動く両端の時計の出発・反射・帰着の指示を、現在位置の静止系時刻、同じ光と真空中の往復試行へ接続する。',
        'sdg':'同じ試行について各時計のそばで共に動く観測者を結び、両者が既存の中点条件biを二時計へ適用する。',
        'sdh':'sdgを前の棒の運動設定と実数・局所時計の同期条件へ接続した追加想定。',
        'sdi':'静止系で同じ棒を測った長さ、光速度V、棒速度v、同じ三記録の時計指示を往復時間の関係へ結ぶ。単位の商と測定設定の継承も保持する。',
        'sdj':'sdiを静止系での測定方法sbkと実切断の往復時間式sdbへ接続した内容。'})
    basis['unresolved']+=generic_composed()[1]['unresolved'][-3:]+[
        'u0036〜u0039とu0040の長さの指示の部分草案。原文の正の棒速度は先行の運動設定に属する。数式単体ではv=0の比較例も許す。',
        'sdcの代数的な交点モデルと、物理的な全軌道・全位置の解釈を結ぶ証明は未完。原理からの結果は著者への帰属として記述する。',
        '中点条件の適用を、条件が成立するとの判定に置き換えない。u0040後半の観測者ごとの判定の帰属と、u0041の一般的な相対的同時性への結論は未接続。',
        '観測者・共動・近接・反射・測定の基礎、原刊照合、全文の意味確認は残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/moving-light-trip-basis-v1.json'),(source_composed,'data/einstein-moving-light-trip-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored moving light trip differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Moving light-trip times, carried-clock protocol and observer criterion application composed')


if __name__=='__main__':main()
