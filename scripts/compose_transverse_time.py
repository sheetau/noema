"""Use equal transverse travel times to express the y and z time derivatives."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT
from scripts.compose_comoving_labels import TAU


def rational_definitions():
    return '''
d sla[light b speed b transverse b] c[w[u[k aa[v speed n p a b]]][w[k aa[v speed v light]][w[k aa[n p a b v transverse]][e[k ab[k ad[v speed v speed] k ad[v transverse v transverse]]][k ad[v light v light]]]]]].
d slb[length b transverse b first b middle b last b] c[w[k aa[n p a b v length]][w[k aa[n p a b v transverse]][w[k aa[v first v middle]][w[k aa[v middle v last]][w[e[k ad[v transverse k ab[v middle k ac[v first]]]][v length]][e[k ad[v transverse k ab[v last k ac[v middle]]]][v length]]]]]]].
d slc[transverse b axispartial b timepartial b inverse b] c[w[k sja[n p b b v transverse v inverse]][e[k ad[v inverse v timepartial]][k ab[v axispartial k ad[v inverse v timepartial]]]]].
d sld[a b b b c b d b offset b x b y b z b time b] b[k ab[k ab[k ab[k ab[k ad[v a v x] k ad[v b v y]] k ad[v c v z]] k ad[v d v time]] v offset]].
'''


MEANINGS={
    'sla':'同じ単位の有理数について、0≤v<V、w>0、v²+w²=V²という横方向成分の条件。光の全速さVをwに置換しない。',
    'slb':'同じ正の横距離と同じ正の成分速度wで、往路・復路の経過時間を結ぶ有理数の式。',
    'slc':'正の横速度の逆数を使い、同じ時間微分項が両辺にある微分係数の式。軸方向微分が0であることと同値になる代数的条件。',
    'sld':'四変数のアフィン関数の有理数の検査用候補。実際のτをこの形へ確定しない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/arbitrary-origins.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/arbitrary-origins-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='transverse-time-basis-v1',document='examples/v014/transverse-time.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['平方和の代数を実際の光路の幾何学の証明とは扱わない。横方向の成分と光の全速さ、静止系と運動系の時計を区別する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def transverse_protocol(parent):
    declaration=deepcopy(next(d for d in parent['declarations'] if d['name']=='skp'))
    declaration['name']='slo';declaration['parameters'].append({'name':'axis','sort':'individual'})
    def replace(node):
        if isinstance(node,list):return [replace(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='yn' and not node['arguments']:return {'kind':'variable','name':'axis'}
        return {k:replace(v) for k,v in node.items()}
    allowed={'kind':'or','arguments':[{'kind':'equal','arguments':[{'kind':'variable','name':'axis'},
        {'kind':'call','symbol':symbol,'arguments':[]}]} for symbol in ('yo','yp')]}
    declaration['body']={'kind':'and','arguments':[allowed,replace(declaration['body'])]}
    return declaration


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-arbitrary-origins.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    doc['declarations'].append(transverse_protocol(doc))
    text=format_graph(doc,'compact')+rational_definitions()
    for name,args in (('skw','v y v x v z v time'),('skx','v z v y v x v time')):
        text+='d '+name+'[function '+TAU+'] '+TAU+'[i[x '+CUT+' y '+CUT+' z '+CUT+' time '+CUT+'][c[v function]['+args+']]].\n'
    text+='''
d sky[nonnegative h[b] c] h[b] c[i[q b][x[k aa[v q n p a b]][c[v nonnegative][k ad[v q v q]]]]].
d sle[light h[b] c speed h[b] c] h[b] c[k sky[k bf[k shv[v light v light] k shv[v speed v speed]]]].
'''
    zero='k bb[n p a b]'
    guards=['k ba[v light]','k ba[v speed]','k ba[v transverse]','k bc['+zero+' v speed]',
        'k bg[v speed v light]','k bg['+zero+' v transverse]']
    text+='d skz[light '+CUT+' speed '+CUT+' transverse '+CUT+'] c['+both(*guards,
        'k sca[k bd[k shv[v speed v speed] k shv[v transverse v transverse]] k shv[v light v light]]',
        'k sca[v transverse k sle[v light v speed]]')+'].\n'
    pointargs='function '+TAU+' a '+CUT+' b '+CUT+' c '+CUT+' time '+CUT+' transverse '+CUT
    duration='k sje[v step v transverse]';middle='k bd[v time '+duration+']';last='k bd['+middle+' '+duration+']'
    readings=['c[v function]['+' '.join(args)+']' for args in (
        ('v a','v b','v c','v time'),('k bd[v a v step]','v b','v c',middle),('v a','v b','v c',last))]
    text+='d slf['+pointargs+' step '+CUT+'] c['+both(*('k ba[v '+n+']' for n in ('a','b','c','time','transverse','step')),
        'k bg['+zero+' v transverse]','k bg['+zero+' v step]',*('k ba['+v+']' for v in (duration,middle,last,*readings)),
        'k sit['+' '.join(readings)+']')+'].\n'
    text+='d slg['+pointargs+' radius '+CUT+'] c['+both('k ba[v radius]','k bg['+zero+' v radius]',
        'f step '+CUT+'[y['+both('k ba[v step]','k bg['+zero+' v step]','k bg[v step v radius]')+'][k slf[v function v a v b v c v time v transverse v step]]]')+'].\n'
    text+='d slh['+pointargs+'] c[g radius '+CUT+'[g axispartial '+CUT+'[g timepartial '+CUT+'['+both(
        'k slg[v function v a v b v c v time v transverse v radius]',
        'k sjv[v function v a v b v c v time v axispartial v timepartial]',
        'k sjw[v function v a v b v c v time v axispartial v timepartial]')+']]]].\n'
    text+='d sli[function '+TAU+' a '+CUT+' b '+CUT+' c '+CUT+' time '+CUT+'] c['+both(
        *('k ba[v '+n+']' for n in ('a','b','c','time')),
        'k sjs[p ba i[coordinate '+CUT+'][c[v function][v coordinate v b v c v time]] v a '+zero+']')+'].\n'
    coordinates='function '+TAU+' x '+CUT+' y '+CUT+' z '+CUT+' time '+CUT
    permuted=['k skw[v function] v y v x v z v time','k skx[v function] v z v y v x v time']
    text+='d slj['+coordinates+' transverse '+CUT+'] c['+both(*('k slh['+args+' v transverse]' for args in permuted))+'].\n'
    text+='d slk['+coordinates+'] c['+both(*('k sli['+args+']' for args in permuted))+'].\n'
    for name,called,extra in (('sll','slj',' transverse '+CUT),('slm','slk','')):
        callargs='v function v x v y v z v time'+(' v transverse' if extra else '')
        body='f x '+CUT+'[f y '+CUT+'[f z '+CUT+'[y['+both(*('k ba[v '+n+']' for n in ('x','y','z')))+'][k '+called+'['+callargs+']]]]]'
        text+='d '+name+'[function '+TAU+' time '+CUT+extra+'] c['+both('k ba[v time]',body)+'].\n'
    text+='''
r zej[a a d] c.r zek[a d] h[b] c.r zel[a d] h[b] c.r zem[d] c.
r zen[] a.r zeo[] a.r zep[a a a a d] c.
'''
    trial='v trial';ctx='v context';events=['k '+n+'[v trial]' for n in ('qe','qf','qg')]
    times=['k sjh['+e+' '+ctx+']' for e in events]
    tuples=['k zdz['+e+' k ra[] '+ctx+']' for e in events]
    coord=lambda i,role:'k zc6['+tuples[i]+' '+role+']'
    auxiliary=lambda i:'k sin[k zb7[] '+coord(i,'k yn[]')+' '+times[i]+']'
    length='k zek[v trial v context]';w='k zel[v trial v context]'
    clauses=['k slo[v trial k qc[v trial] v context v axis]','k skq[v trial v context]',
        'k ba['+length+']','k bg['+zero+' '+length+']','k skz[k tc[] k zb7[] '+w+']']
    for i in (1,2):clauses+=['k sca['+auxiliary(i)+' '+auxiliary(0)+']']
    for role in ('yo','yp'):
        for i in (1,2):clauses+=['y[u[e[v axis][k '+role+'[]]]][k sca['+coord(i,'k '+role+'[]')+' '+coord(0,'k '+role+'[]')+']]']
    clauses+=['k sca[k bf['+coord(1,'v axis')+' '+coord(0,'v axis')+'] '+length+']',
        'k sca['+coord(2,'v axis')+' '+coord(0,'v axis')+']']
    for first,last in zip(times,times[1:]):clauses+=['k bg['+first+' '+last+']',
        'k sca[k shv['+w+' k bf['+last+' '+first+']] '+length+']']
    text+='d slp[trial a axis a context d] c['+both(*clauses)+'].\n'
    clauses=['k sfm[v context]','k sbc[k tc[] v context]','k sio[k zd4[]]','k zem[v context]',
        'u[e[k yo[]][k yp[]]]','u[e[k yn[]][k yo[]]]','u[e[k yn[]][k yp[]]]',
        'k skz[k tc[] k zb7[] k sle[k tc[] k zb7[]]]']
    for role in ('yo','yp'):clauses+=['g trial a[k zej[v trial k '+role+'[] v context]]']
    clauses+=['f trial a[f axis a[y[k zej[v trial v axis v context]][w[x[e[v axis][k yo[]]][e[v axis][k yp[]]]][k slp[v trial v axis v context]]]]]']
    text+='d sls[context d] c['+both(*clauses)+'].\n'
    time='k sjh[k qe[k zdq[]] v context]'
    text+='d slt[context d] c['+both('k sls[v context]','k sll[k zd4[] '+time+' k sle[k tc[] k zb7[]]]')+'].\n'
    text+='''
d slu[] e[b context[k slt[k zb6[]]]].
d slv[] e[b context[k slm[k zd4[] k sjh[k qe[k zdq[]] k zb6[]]]]].
d slw[] e[b context[k sls[k zb6[]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k uh[k zen[] k rd[] r[k slw[]] k rh[] k ri[]]][k zei[k zen[] k rd[] k rh[] k ri[]]]].
s[w[k zc[k zeo[] k rd[] r[k slu[]] r[k slv[]] k rh[] k ri[]]][k zep[k zeo[] k rd[] k zea[] k rh[] k ri[]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-arbitrary-origins-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-transverse-time-basis-v1',document='examples/v014/einstein-transverse-time.noema')
    basis['definitions'].update(MEANINGS|{
        'skw':'四引数関数の最初と二番目の空間引数を交換し、y方向を既存の一番目の変数についての解析へ接続する。',
        'skx':'四引数関数の最初と三番目の空間引数を交換し、z方向を同じ解析へ接続する。',
        'sky':'非負の実切断の非負平方根。既存real-productsのcjと同じ構成を再利用する。',
        'sle':'実切断で√(V²-v²)を構成する。定義域はskzで確認する。',
        'skz':'正の横成分速度wについて、0≤v<V、v²+w²=V²と非負平方根との一致を要求する。Vは静止系での全速さ、wは横方向成分である。',
        'slf':'指定軸の正の変位hを同じ成分速度wで往復し、t・t+h/w・t+2h/wで読む中点式。帰着位置は元の位置へ戻る。',
        'slg':'同じ中点式を指定正半径より小さい全ての正の軸変位について要求する。',
        'slh':'その位置の軸変数と時刻に関する全微分可能性・偏微分値と、近傍全体の中点式を要求する。',
        'sli':'同じ位置で他の三引数を固定した軸方向の偏微分が0であるという、差商の極限による条件。',
        'slj':'同じ元のτ候補・四座標・横成分速度について、yとzの両方向の局所前提を要求する。',
        'slk':'同じτ候補の同じ評価点で、yとzの両偏微分が0である。',
        'sll':'同じ時刻と関数について、全空間座標でy,z両方向の局所前提を要求する。',
        'slm':'同じ時刻と関数について、全空間座標でy,z両偏微分が0である。',
        'slo':'既存skpの往復プロトコルを、指定したyまたはz軸に平行な経路へ一般化する。X軸方向をこの条件で受理しない。',
        'slp':'同じ横方向試行の座標と時計を結び、x-vtと非選択の横座標を固定し、正の横距離を同じwで往復する両時間式を要求する。',
        'sls':'指定された完全な横方向試行範囲のy,z両方に試行があり、全て同じ静止系の光速度と並進速度のもとでslpを満たすという条件。',
        'slt':'横方向試行の条件と、全空間での中点近傍・微分可能性の前提を結ぶ。',
        'slu':'同様の微分の議論を横方向へ適用するための、明示した十分条件という内容。',
        'slv':'全空間座標で∂τ/∂y=0かつ∂τ/∂z=0という内容。',
        'slw':'静止系での横成分速度と、それを用いた両方向の試行の条件という内容。'})
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zej',['trial','axis_role','context'],'指定した横軸方向と設定で考察する光往復の全試行範囲。既観測の標本に限定せず理想的な試行を含む。'),
        ('zek',['trial','context'],'同じ横方向試行の正の片道距離の候補。座標差と両伝播時間への接続はslpで要求する。'),
        ('zel',['trial','context'],'同じ試行の横方向の成分速度の候補。全速さVと区別し、平方和・平方根・伝播時間に接続する。'),
        ('zem',['context'],'zejのy,z方向の試行範囲が議論の対象を尽くすという明示的前提。有限検査による認定ではない。'),
        ('zen',[],'静止系での横成分速度を考慮すべきこととして提示する箇所。'),
        ('zeo',[],'同様の議論からy,zの偏微分条件を得ると述べる箇所。'),
        ('zep',['node','author','earlier_argument','scope','context'],'著者がこの箇所を、指定した先行論法に類似した議論として位置付ける。機械的な同値性や導出済みを意味しない。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0059〜u0061の部分記述。抽出資料のH・Zという軸表記をy,zの横方向に接続する。原刊画像の字形照合は未完。',
        '√(V²-v²)は静止系での光の全速さではなく、運動する横軸に沿う成分として記述する。平方和を実際の光路の幾何へ接続する一般定理は未証明。',
        '近傍全体の中点式と二変数の全微分可能性は、同様の極限推論を扱う十分条件の補足である。実際の全光路からの導出、連鎖律の一般的な機械的証明は未完。',
        '非負平方根の実切断全域の法則、τの具体形の導出、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/transverse-time-basis-v1.json'),(source_composed,'data/einstein-transverse-time-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored transverse time differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Transverse light times and vanishing y/z time derivatives composed')


if __name__=='__main__':main()
