"""Bind the axial light trial to comoving positions and moving-clock readings."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT, OP, SAME, VALID

SYNC='h[a a a a d] c'


def definitions():
    return '''
d siq[first b middle b last b] c[e[k ad[n p b c k ab[v first v last]]][v middle]].
'''+('d sir[first '+CUT+' middle '+CUT+' last '+CUT+' valid '+VALID+' same '+SAME+' add '+OP+'] c['+both(
        'c[v valid][v first]','c[v valid][v middle]','c[v valid][v last]',
        'c[v same][c[v add][v first v last] c[v add][v middle v middle]]')+'].\n')


MEANINGS={
    'siq':'有理数の三つの読みについて、出発と帰着の平均が反射の読みと等しい。順序や物理的な往復の存在は別条件。',
    'sir':'有効な三つの値について、出発と帰着の和が反射の値の二倍と等しい。実数の加法と値一致へ接続して中点条件として使う。',
}


def generic_composed():
    basis=deepcopy(json.loads((ROOT/'data/comoving-labels-basis-v1.json').read_text(encoding='utf-8')))
    doc=parse((ROOT/'examples/v014/comoving-labels.noema').read_text(encoding='utf-8'))
    doc['declarations']=[d for d in doc['declarations'] if d['kind']=='primitive']
    doc=parse(format_graph(doc,'compact')+definitions())
    basis.update(version='axial-clock-trip-basis-v1',document='examples/v014/axial-clock-trip.noema',definitions=MEANINGS.copy(),
        unresolved=['中点の数値条件だけでは、光往復・時刻の順序・時計の同期を含意しない。演算を引数で渡す場合の実数法則は呼出側の責任である。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-comoving-labels.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'''
r zdq[] a.r zdr[] a.r zds[] a.r zdt[] h[b] c.r zdu[] a.r zdv[] a.
r zdw[a a a a a d] c.
d sis[first h[b] c middle h[b] c last h[b] c] c[k sir[v first v middle v last p ba p sca p bd]].
d sit[first h[b] c middle h[b] c last h[b] c] c[
 w[k ba[v first]][w[k ba[v middle]][w[k ba[v last]][k sca[k bj[n p b c k bd[v first v last]] v middle]]]]].
'''
    trial='v trial';frame='k zbm[]';unit='k rb[]';ctx='v context'
    origin='k qc['+trial+']';mirror='k qd['+trial+']';ray='k qh['+trial+']'
    events=['k '+s+'['+trial+']' for s in ('qe','qf','qg')]
    readings=['k '+s+'['+trial+']' for s in ('qi','qj','qk')]
    axis='k zbo['+frame+' k yn[] '+ctx+']'
    clauses=[
        'k qb[v firstclock v secondclock '+frame+' '+unit+' '+ctx+' '+trial+']',
        'u[e[v firstclock][v secondclock]]','u[e['+origin+']['+mirror+']]',
        'e['+origin+'][k zbn['+frame+' '+ctx+']]','k zbv['+frame+' '+origin+' '+ctx+']',
        'k zbw['+frame+' '+axis+' k yn[] '+ctx+']',
        'k zbz['+frame+' v firstclock '+ctx+']','k zbz['+frame+' v secondclock '+ctx+']',
        'k zcu['+origin+' '+frame+' '+ctx+']','k zcu['+mirror+' '+frame+' '+ctx+']',
        'k da[v firstclock v secondclock '+origin+' '+mirror+' '+' '.join(events)+' '+ray+' '+frame+' '+unit+' '+' '.join(readings)+']',
        'k sde['+ray+' '+' '.join(events)+' '+frame+' p cf p cg p ch]',
        'c[v synchrony][v firstclock v secondclock '+frame+' '+unit+' '+ctx+']',
    ]
    for first,last in zip(events,events[1:]):clauses+=['k zdw['+ray+' '+first+' '+last+' '+axis+' '+frame+' '+ctx+']']
    for event,value,place in zip(events,readings,(origin,mirror,origin)):
        clauses+=['c[v valid]['+value+']',
            'k sgp['+event+' '+place+' '+frame+' '+unit+' '+ctx+' v synchrony v valid v same]',
            'c[v same]['+value+' k zbe['+event+' '+frame+' '+unit+' '+ctx+']]']
    for first,last in zip(readings,readings[1:]):clauses+=['c[v before]['+first+' '+last+']']
    text+='d siu[trial a firstclock a secondclock a context d synchrony '+SYNC+' valid '+VALID+' same '+SAME+' before '+SAME+'] c['+both(*clauses)+'].\n'
    text+='d siv[event a label '+CUT+' context d synchrony '+SYNC+' valid '+VALID+' same '+SAME+' subtract '+OP+' multiply '+OP+'] c['+both(
        'c[v valid][v label]',
        'g tuple a['+both('k shc[v event v tuple k ra[] v context v synchrony v valid v same]',
            'c[v same][k sig[k zb7[] k zc6[v tuple k yn[]] k zc6[v tuple k zc7[]] v subtract v multiply] v label]',
            'c[v same][k zc6[v tuple k yo[]] k bb[n p a b]]',
            'c[v same][k zc6[v tuple k yp[]] k bb[n p a b]]')+']')+'].\n'
    text+='d siw[trial a label '+CUT+' context d synchrony '+SYNC+' valid '+VALID+' same '+SAME+' subtract '+OP+' multiply '+OP+'] c['+both(*[
        'k siv['+event+' '+label+' v context v synchrony v valid v same v subtract v multiply]'
        for event,label in zip(events,('k bb[n p a b]','v label','k bb[n p a b]'))])+'].\n'
    text+='d six[context d] c['+both(
        'u[e[k ra[]][k zbm[]]]','k va[k ra[]]','k va[k zbm[]]','k ci[k rb[]]','k ti[k ta[]]',
        'k tj[k ta[] k rb[] k tb[]]','k ba[k zb7[]]','k bg[k bb[n p a b] k zb7[]]',
        'k ba[k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'k sca[k zb7[] k zbi[k ra[] k zbm[] k ta[] k rb[] v context]]',
        'k ba[k zdt[]]','u[k sca[k zdt[] k bb[n p a b]]]',
        'k siu[k zdq[] k zdr[] k zds[] v context p qo p ba p sca p bg]',
        'k siw[k zdq[] k zdt[] v context p qo p ba p sca p bf p shv]')+'].\n'
    text+='''
d siy[] e[b context[k six[k zb6[]]]].
d siz[] e[b context[k sit[k qi[k zdq[]] k qj[k zdq[]] k qk[k zdq[]]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ug[k zdu[] k rd[] r[k siy[]] k rh[] k ri[]]].
s[k zc[k zdv[] k rd[] r[k siy[]] r[k siz[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-comoving-labels-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-axial-clock-trip-basis-v1',document='examples/v014/einstein-axial-clock-trip.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zdq',[],'§3でτの条件を作るために仮定する、原点から軸方向へ出発して反射し帰着する光往復の試行。以前の棒の試行とは別の指示対象。'),
        ('zdr',[],'この試行で運動系の原点に置かれた時計。出発と帰着を同じ時計で読む。'),
        ('zds',[],'この試行で反射地点に置かれた運動系の時計。'),
        ('zdt',[],'反射地点を指定する補助量x′の値。実数・非零・静止系の座標からの構成を別に要求する。ξとの同一性や正の向きは補わない。'),
        ('zdu',[],'§3の原点からの光往復を仮定する箇所。'),
        ('zdv',[],'その往復の三つのτの読みに中点条件が必要だと述べる箇所。'),
        ('zdw',['ray','from_event','to_event','axis','frame','context'],'指定系・文脈で、同じ光の二出来事間の伝播経路全体が指定された軸の支持線上にある。端点だけの軸上配置とは区別する。伝播・反射・軸の割当は別に要求する。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        'sis':'実切断の和と値一致を使う、分母を払った中点条件。',
        'sit':'有効な実切断について、1/2(τ₀+τ₂)=τ₁という式をそのまま構成する。時刻の順序をこの式から推測しない。',
        'siu':'同じ運動系・文脈・時間単位で、原点の同じ時計から出発し同じ場所へ戻る一つの光往復。別の反射時計、三つの異なる出来事、両伝播、反射、軸上の全経路、配備・同期・局所時刻と三つの時計の読み、厳密な時刻順序を結ぶ。',
        'siv':'同じ出来事の静止系の座標を使い、x-vtが指定された補助量でy=z=0であることを要求する。運動系の時刻τやξを代入しない。',
        'siw':'一つの試行の出発・反射・帰着に、それぞれ補助量0・x′・0を同じ静止系・文脈・速度で結ぶ。',
        'six':'共通の単位と正の相対速度、非零の補助距離、運動系の同期時計を使う軸上の光往復を、静止系から作った補助座標に接続する。',
        'siy':'§3の同じ運動設定で、この光往復を置くという内容。',
        'siz':'その試行の時計の三つの読みが中点式を満たすという内容。静止系時刻tの中点式ではない。'})
    basis['unresolved']+=[
        'u0049・u0050の部分記述。同期時計を使うという先行条件と、共通の軸支持線を使うという配置を明示的に継承して解釈した。X軸の原刊表記と配置の一般的整合性は未確認。',
        '原文の非退化な往復を、異なる原点・反射地点、非零の補助量、厳密な時刻順序で表した。正方向やτの具体形は補っていない。',
        '元の同期定義から選択された試行の中点条件を取り出す論理の有限モデル検査と有理数の同値検査は別の証拠であり、全実数上の物理的導出の証明ではない。',
        '後続の光速度一定による静止系時刻tの引数展開、τの具体形の導出、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/axial-clock-trip-basis-v1.json'),(source_composed,'data/einstein-axial-clock-trip-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored axial clock trial differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Axial light trial and moving-clock midpoint composed')


if __name__=='__main__':main()
