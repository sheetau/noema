"""Compose material axis triads, geometric alignment and matching instruments."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both


def definitions():
    text='''
d set[x b y b z b u b v b w b] b[k ab[k ab[k ad[v x v u] k ad[v y v v]] k ad[v z v w]]].
d seu[x b y b z b] c[k aa[n p a b k set[v x v y v z v x v y v z]]].
d sev[x b y b z b u b v b w b] c[
 w[k seu[v x v y v z]][w[k seu[v u v v v w]][e[k set[v x v y v z v u v v v w]][n p a b]]]
].
d sew[x b y b z b u b v b w b] c[
 w[k seu[v x v y v z]][w[k seu[v u v v v w]][w[e[k ad[v x v v]][k ad[v y v u]]][
 w[e[k ad[v x v w]][k ad[v z v u]]][e[k ad[v y v w]][k ad[v z v v]]]]]]
].
'''
    args='frame a origin a x a y a z a xrole a yrole a zrole a context d origins h[a a d] c assigned h[a a a d] c material h[a] c rigid h[a d] c starts h[a a d] c perpendicular h[a a d] c'
    clauses=['c[v origins][v frame v origin v context]']
    for a,b in (('x','y'),('x','z'),('y','z')):
        clauses+=['u[e[v '+a+'][v '+b+']]','u[e[v '+a+'role][v '+b+'role]]',
            'c[v perpendicular][v '+a+' v '+b+' v context]']
    for a in ('x','y','z'):
        clauses+=['c[v assigned][v frame v '+a+' v '+a+'role v context]',
            'c[v material][v '+a+']','c[v rigid][v '+a+' v context]',
            'c[v starts][v '+a+' v origin v context]']
    text+='d sex['+args+'] c['+both(*clauses)+'].\n'
    text+='''
d sey[x a y a z a otherx a othery a otherz a context d coincident h[a a d] c parallel h[a a d] c] c[
 w[c[v coincident][v x v otherx v context]][w[c[v parallel][v y v othery v context]][c[v parallel][v z v otherz v context]]]
].
d sez[frame a ruler a context d rulers h[a] c clocks h[a] c rigid h[a d] c givenruler h[a a d] c givenclock h[a a d] c] c[
 w[c[v rulers][v ruler]][w[c[v rigid][v ruler v context]][w[c[v givenruler][v frame v ruler v context]][
 w[g clock a[c[v givenclock][v frame v clock v context]]][f clock a[y[c[v givenclock][v frame v clock v context]][c[v clocks][v clock]]]]]]]
].
'''
    args='first a second a firstrod a secondrod a context d rulers h[a] c clocks h[a] c rigid h[a d] c givenruler h[a a d] c givenclock h[a a d] c sameruler h[a a d] c sameclock h[a a d] c'
    tail='v context v rulers v clocks v rigid v givenruler v givenclock'
    selected=lambda n:'x[c[v givenclock][v first v '+n+' v context]][c[v givenclock][v second v '+n+' v context]]'
    text+='d sfa['+args+'] c['+both('u[e[v first][v second]]','u[e[v firstrod][v secondrod]]',
        'k sez[v first v firstrod '+tail+']','k sez[v second v secondrod '+tail+']',
        'c[v sameruler][v firstrod v secondrod v context]',
        'f a a[f b a[y[w['+selected('a')+']['+selected('b')+']][c[v sameclock][v a v b v context]]]]')+'].\n'
    return text


MEANINGS={
    'set':'有理数の三成分の内積。位置や単位自体をこの式だけで決めない。',
    'seu':'有理数の方向ベクトルが零ではない。成分の二乗和が正であることによる検査。',
    'sev':'零でない二方向ベクトルの内積が零であるという直交条件。',
    'sew':'零でない二方向ベクトルの外積の三成分が零であるという平行条件。逆向きも許し、線の位置の一致とは区別する。',
    'sex':'異なる三つの軸が異なる三役割に割り当てられ、同じ原点から出る剛な物質線で、互いに直交する。基準系の全ての性質をこれだけで定義したとはしない。',
    'sey':'対応する第一軸は幾何学的に同じ線を占め、第二軸・第三軸はそれぞれ平行。対応する物体や二原点の同一性は要求しない。',
    'sez':'一つの系に剛な物差しと非空の時計の範囲が与えられ、選ばれた全ての時計が時計型を満たす。時計がちょうど一個とは要求しない。',
    'sfa':'異なる二系に異なる物差しが与えられ、物差しの仕様が一致する。両系に与えられた全時計の全組合せで仕様が一致する。同じ個体や同じ指示値を要求しない。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.\n'+definitions())
    previous=json.loads((ROOT/'data/einstein-relative-simultaneity-basis-v1.json').read_text(encoding='utf-8'))
    basis={'version':'coordinate-frames-basis-v1','document':'examples/v014/coordinate-frames.noema',
        'primitives':[deepcopy(p) for p in previous['primitives'] if p['symbol'] in ('aa','ab','ac','ad')],
        'definitions':MEANINGS.copy(),'unresolved':[
            '物質線・剛性・原点から出ること・軸の割当て・計器の仕様一致は引数の意味規約。物体や空間の一般的な基礎説明は残る。',
            '有理数の方向の検査は幾何学の補助例。任意の実方向や物質線の全点・全時刻を検証したとはしない。',
            '同じ仕様の計器であっても、異なる運動状態での時計指示の一致や物差しの測定値の一致は別の主張である。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-relative-simultaneity.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zbm[] a.r zbn[a d] a.r zbo[a a d] a.
r zbp[a] c.r zbq[a d] c.r zbr[a a d] c.r zbs[a a d] c.r zbt[a a d] c.r zbu[a a d] c.
r zbv[a a d] c.r zbw[a a a d] c.r zbx[a a d] c.r zby[a d] a.r zbz[a a d] c.
r zb2[a a d] c.r zb3[a a d] c.r zb4[] d.r zb5[] a.
d sfb[frame a context d] c[
 w[k va[v frame]][k sex[v frame k zbn[v frame v context]
 k zbo[v frame k yn[] v context] k zbo[v frame k yo[] v context] k zbo[v frame k yp[] v context]
 k yn[] k yo[] k yp[] v context p zbv p zbw p zbp p zbq p zbr p zbs]]
].
d sfc[first a second a context d] c[
 w[u[e[v first][v second]]][w[k sfb[v first v context]][w[k sfb[v second v context]][
 k sey[k zbo[v first k yn[] v context] k zbo[v first k yo[] v context] k zbo[v first k yp[] v context]
 k zbo[v second k yn[] v context] k zbo[v second k yo[] v context] k zbo[v second k yp[] v context]
 v context p zbu p zbt]]]]
].
d sfd[first a second a context d] c[
 k sfa[v first v second k zby[v first v context] k zby[v second v context]
 v context p xc p ca p zbq p zbx p zbz p zb2 p zb3]
].
d sfe[] e[b context[
 w[k sfc[k ra[] k zbm[] k zb4[]]][w[k sfd[k ra[] k zbm[] k zb4[]]][
 w[k x4[k ra[] k ra[] k zb4[]]][k x4[k zbm[] k ra[] k zb4[]]]]]
]].
'''
    doc=parse(text);doc['statements']=statements
    # The old comparison condition used fixed relative orientation as if it
    # guaranteed aligned axes. Refine only this definition in the new edition;
    # keep the frozen predecessor unchanged, and place dependencies before it.
    previous_names={d['name'] for d in old['declarations']}
    additions=[d for d in doc['declarations'] if d['name'] not in previous_names]
    inherited=[d for d in doc['declarations'] if d['name'] in previous_names]
    index=next(i for i,d in enumerate(inherited) if d['name']=='sel')
    comparison=inherited[index]
    comparison['body']={'kind':'and','arguments':[comparison['body'],
        {'kind':'call','symbol':'sfc','arguments':[{'kind':'variable','name':comparison['parameters'][i]['name']} for i in (2,3,4)]}]}
    doc['declarations']=inherited[:index]+additions+inherited[index:]
    doc=parse(format_graph(doc,'compact')+'s[k ug[k zb5[] k rd[] r[k sfe[]] k rh[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-relative-simultaneity-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-coordinate-frames-basis-v1',document='examples/v014/einstein-coordinate-frames.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    entries=[
        ('zbm',[],'§3で後から等速並進を与える側の座標系。初期設定zb4では静止している。'),
        ('zbn',['frame','context'],'指定系の原点の候補。実際に原点として割り当てられていることをzbvで要求する。'),
        ('zbo',['frame','role','context'],'指定系のx・y・zの役割に対応する物質軸の候補。割当てzbwを別に要求する。'),
        ('zbp',['line'],'空間に置かれた物質線。単なる数値方向や記号とは分ける。物質の基礎説明は未完。'),
        ('zbq',['object','context'],'指定設定で形状を固定した剛な物体として扱う。物質軸と物差しへ共通に適用する理想化であり、加速中や全ての系で長さが等しいとの法則は含まない。'),
        ('zbr',['line','origin','context'],'指定物質線が同じ原点から出る。任意の離れた一点を原点として流用しない。'),
        ('zbs',['first_line','second_line','context'],'二つの物質軸の方向が直交する。局所的なユークリッド方向の内積が零という意味規約。実方向と物理的測定からの接続は未完。'),
        ('zbt',['first_line','second_line','context'],'二物質軸が幾何学的に平行。逆向きもこの関係単体では除かない。位置の一致は要求しない。'),
        ('zbu',['first_line','second_line','context'],'二物質軸の幾何学的な支持直線が重なる。物体の同一性ではなく、単なる平行より強い条件。'),
        ('zbv',['frame','origin','context'],'その系にその点が原点として割り当てられている。'),
        ('zbw',['frame','line','role','context'],'その系にその物質線がその軸の役割として割り当てられている。'),
        ('zbx',['frame','ruler','context'],'その系にその物差しが備えられている。'),
        ('zby',['frame','context'],'その系へ備えた物差しの候補。zbxと物差し型を別に確認する。'),
        ('zbz',['frame','clock','context'],'その系に備えられた時計の範囲を指定する。解釈は一部の標本でなく、この設定での全時計を与える。'),
        ('zb2',['first_ruler','second_ruler','context'],'二つの物差しが初期設定において同じ構成・目盛りの仕様を持つ。二つが同じ物体であることや、全運動状態で同じ測定値を持つことではない。'),
        ('zb3',['first_clock','second_clock','context'],'二つの時計が初期設定において同じ構成・刻みの仕様を持つ。両者が同期済みであることや、運動後の指示一致を含まない。'),
        ('zb4',[],'二つの座標系を静止空間内へ置き、計器を備えた初期設定。後で一方を動かす設定と区別する。'),
        ('zb5',[],'§3冒頭の二座標系と同一仕様の計器を想定する本文箇所。')]
    for name,args,meaning in entries:
        d=decls[name]
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sel':'既存の回転しない等速相対運動sat、有効で非零の相対速度に加え、sfcによる直交三軸と対応軸の配置を要求する。前版で配置の保証が不足していた比較範囲を、この文書で明示的に精密化した。',
        'sfb':'系に実際に割り当てられた原点と三つの物質軸を、役割ごとに取り出して直交三軸sexへ接続する。',
        'sfc':'二系の三軸構成と、x支持直線の一致・y同士とz同士の平行を同時に要求する。原点の一致は追加しない。',
        'sfd':'同じ初期文脈で両系の物差しと全時計を取り出し、型・剛性・仕様の一致へ接続する。',
        'sfe':'両系が初期に静止系raに対して静止し、sfcの配置とsfdの計器を備えるという想定内容。後続の運動はまだ断定しない。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0043の部分草案。ちょうど三つの選択した役割を要求するが、補助的な別の線や物体の存在は排除しない。無限に延びる線と物理的な有限の軸の関係は未説明。',
        '「genau gleich」を構成・目盛りの仕様が一致するという初期設定の意味で部分解釈した。製作・較正の手順、測定誤差、完全一致という理想化の根拠は残る。',
        '既存satは軸の相対回転がない条件で、直交三軸や平行配置を単独では保証しない。この文書ではselにsfcを加えた。方向の正負や軸の向き付け、物理的な配置の全域的な実現はなお未説明。',
        'u0044の原点・軸・計器への運動の共有と対称性に基づく仮定、u0045の両系での空間と時刻の測定、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/coordinate-frames-basis-v1.json'),(source_composed,'data/einstein-coordinate-frames-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored coordinate frame differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Material triads, geometric alignment and identical instrument specifications composed')


if __name__=='__main__':main()
