"""Bind transverse endpoint measurements to symmetry and the positive scale."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_affine_time_form import CUT, PHI


def definitions():
    return '''
d srt[light b speed b beta b scale b proper b x b y b z b time b tau b] c[w[u[e[v scale][n p a b]]][k srb[v light v speed v beta v scale v x v y v z v time n p a b v proper n p a b v tau]]].
d sru[proper b plus b minus b forward b reverse b] c[w[k aa[n p a b v proper]][w[k aa[n p a b v forward]][w[k aa[n p a b v reverse]][w[e[k ad[v plus v forward]][v proper]][w[e[k ad[v minus v reverse]][v proper]][e[v forward][v reverse]]]]]]].
d srv[plus b minus b] c[w[e[k ad[v plus v minus]][n p b b]][w[e[v plus][v minus]][k aa[n p a b v plus]]]].
'''


MEANINGS={
    'srt':'有理数の四座標式で運動系の端点をξ=ζ=0、η=properへ置く。φの非零を明示し、proper=0も許す。',
    'sru':'同じ正の固有長と正負速度での正の測定長を、それぞれの係数との積で結び、測定長が等しいとする。',
    'srv':'係数二値の積1、二値の一致、正の枝を合わせる。正の枝を無断で補わない。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/reverse-transform.noema').read_text(encoding='utf-8')+definitions())
    basis=deepcopy(json.loads((ROOT/'data/reverse-transform-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='transverse-rod-scale-basis-v1',document='examples/v014/transverse-rod-scale.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['長さを正の符号付き横差として読む規約を明示する。絶対距離だけなら負のφも残り得る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-reverse-transform.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions();zero='k bb[n p a b]';one='k bb[n p b b]'
    mul=lambda a,b:'k shv['+a+' '+b+']';sub=lambda a,b:'k bf['+a+' '+b+']'
    coord=lambda record,role:'k zc6['+record+' k '+role+'[]]'
    phi='k spc[]';v='k zb7[]';minus=sub(zero,v);scale=lambda speed:'c['+phi+']['+speed+']'
    text+='d srw[rest a moving a speed '+CUT+' proper '+CUT+'] c['+both('k sre[v rest v moving k tc[] v speed '+phi+']',
        'k ba[v proper]','k bc['+zero+' v proper]','u[k sca['+scale('v speed')+' '+zero+']]',
        'k sca['+coord('v moving','yn')+' '+zero+']','k sca['+coord('v moving','yp')+' '+zero+']','k sca['+coord('v moving','yo')+' v proper]')+'].\n'
    text+='d srx[proper '+CUT+' factor '+CUT+'] '+CUT+'[k sje['+mul('v proper','v factor')+' '+mul('v factor','v factor')+']].\n'
    text+='d sry[rest a speed '+CUT+' proper '+CUT+' factor '+CUT+'] c['+both('k sha[v rest p ba]','k ba[v speed]','k ba[v proper]','k ba[v factor]',
        'u[k sca[v factor '+zero+']]','k ba[k srx[v proper v factor]]',
        'k sca['+coord('v rest','yn')+' '+mul('v speed',coord('v rest','zc7'))+']',
        'k sca['+coord('v rest','yo')+' k srx[v proper v factor]]','k sca['+coord('v rest','yp')+' '+zero+']')+'].\n'
    args='lowrest a highrest a lowmoving a highmoving a speed '+CUT+' proper '+CUT
    text+='d srz['+args+'] c['+both('k sbg[v proper]','k srw[v lowrest v lowmoving v speed '+zero+']',
        'k srw[v highrest v highmoving v speed v proper]',
        'k sca['+coord('v lowrest','zc7')+' '+coord('v highrest','zc7')+']')+'].\n'
    text+='r zgu[] a.r zgv[] a.r zgw[] a.r zgx[d] a.r zgy[d] a.r zgz[] '+CUT+'.r zg2[] d.\n'
    text+='r zha[d] '+CUT+'.r zhb[d] '+CUT+'.r zhc[d] c.r zhd[d] a.\n'
    text+='r zhf[a a i['+PHI+'] i[e] a d] c.r zhg[a a i['+PHI+'] a d] c.\n'
    text+='r zhh[] a.r zhi[] a.r zhj[] a.r zhk[] a.r zhl[] a.r zhm[] a.r zhn[] a.r zho[] a.r zhp[] a.r zhq[] a.\n'
    record=lambda event,frame:'k zdz['+event+' k '+frame+'[] v setting]'
    le='v lowevent';he='v highevent';lr=record(le,'ra');hr=record(he,'ra');lm=record(le,'zbm');hm=record(he,'zbm')
    physical_args='rod a low a high a lowevent a highevent a setting d speed '+CUT+' proper '+CUT
    bindings=[]
    for frame in ('ra','zbm'):
        for endpoint,event in (('low',le),('high',he)):
            bindings.append('g place a['+both('k xg[v '+endpoint+' '+event+' v place k '+frame+'[] v setting]',
                'k cb['+event+' v place k '+frame+'[]]')+']')
    text+='d ssa['+physical_args+'] c['+both('k xa[v rod]','u[e[v low][v high]]','u[e[v lowevent][v highevent]]',
        'k x4[v rod k zbm[] v setting]','k zbq[v rod v setting]',
        'k yu[v rod k zbm[] k zbo[k zbm[] k yo[] v setting] v setting]',
        'k zbw[k zbm[] k zbo[k zbm[] k yo[] v setting] k yo[] v setting]',
        'k zbs[k zbo[k ra[] k yn[] v setting] k zbo[k zbm[] k yo[] v setting] v setting]',
        'k zgj[k zbm[] k ra[] k zbo[k ra[] k yn[] v setting] v speed k ta[] k rb[] v setting]',
        *('k xf[v '+endpoint+' v rod k '+frame+'[] v setting]' for endpoint in ('low','high') for frame in ('ra','zbm')),
        *bindings,'k zc4[v lowevent]','k zc4[v highevent]',
        *('k shd['+event+' '+record(event,frame)+' k '+frame+'[] v setting]' for event in (le,he) for frame in ('ra','zbm')),
        'k srz['+lr+' '+hr+' '+lm+' '+hm+' v speed v proper]')+'].\n'
    text+='d ssb['+physical_args+' length '+CUT+'] c['+both('k ssa[v rod v low v high v lowevent v highevent v setting v speed v proper]',
        'k sbg[v length]','k sry['+lr+' v speed '+zero+' '+scale('v speed')+']',
        'k sry['+hr+' v speed v proper '+scale('v speed')+']',
        'k sca[v length '+sub(coord(hr,'yo'),coord(lr,'yo'))+']',
        'k sca[v length k srx[v proper '+scale('v speed')+']]',
        'k za[v rod k ra[] k ta[] v length v setting]',
        'g firstplace a[g lastplace a['+both('k xg[v low v lowevent v firstplace k ra[] v setting]',
            'k xg[v high v highevent v lastplace k ra[] v setting]',
            'k th[v firstplace v lastplace k ra[] k ta[] v length]')+']]')+'].\n'
    text+='d ssc[settings h[d] c speed h[d] '+CUT+' length h[d] '+CUT+'] c['+both('g setting d[c[v settings][v setting]]',
        'f first d[f second d[y[w[c[v settings][v first]][c[v settings][v second]]]['+both(
            'k ba[c[v speed][v first]]','k ba[c[v speed][v second]]',
            'k sbg[c[v length][v first]]','k sbg[c[v length][v second]]',
            'y[k sca['+mul('c[v speed][v first]','c[v speed][v first]')+' '+mul('c[v speed][v second]','c[v speed][v second]')+']][k sca[c[v length][v first] c[v length][v second]]]')+']]]')+'].\n'
    # Eligibility keeps the same physical rod and transverse geometry in each setting.
    text+='d ssd[setting d] c['+both('k zhc[v setting]','k xa[k zgu[]]','k x4[k zgu[] k zbm[] v setting]',
        'k zbq[k zgu[] v setting]','k sbg[k zgz[]]','k sbg[k zha[v setting]]',
        'k za[k zgu[] k zbm[] k ta[] k zgz[] v setting]','k za[k zgu[] k ra[] k ta[] k zha[v setting] v setting]',
        'k zbs[k zhd[v setting] k zbo[k zbm[] k yo[] v setting] v setting]',
        'k zgj[k zbm[] k ra[] k zhd[v setting] k zhb[v setting] k ta[] k rb[] v setting]')+'].\n'
    setup=lambda ctx,speed,length: 'k '+('ssa' if length is None else 'ssb')+'[k zgu[] k zgv[] k zgw[] k zgx['+ctx+'] k zgy['+ctx+'] '+ctx+' '+speed+' k zgz[]'+(' '+length if length else '')+']'
    forward='k zb6[]';reverse='k zg2[]'
    text+='d sse[] e[b context['+setup(forward,v,None)+']].\n'
    lo='k zdz[k zgx['+forward+'] k ra[] '+forward+']';hi='k zdz[k zgy['+forward+'] k ra[] '+forward+']'
    text+='d ssf[] e[b context['+both('k sry['+lo+' '+v+' '+zero+' '+scale(v)+']','k sry['+hi+' '+v+' k zgz[] '+scale(v)+']',
        'k sca['+coord(lo,'zc7')+' '+coord(hi,'zc7')+']')+']].\n'
    text+='d ssg[] e[b context['+setup(forward,v,'k zha['+forward+']')+']].\n'
    text+='d ssh[] e[b context['+both('t[k ssg[]][v context]',setup(reverse,minus,'k zha['+reverse+']'),
        'u[e['+forward+']['+reverse+']]')+']].\n'
    text+='d ssi[] e[b context['+both('k ssd['+forward+']','k ssd['+reverse+']',
        'k sca[k zhb['+forward+'] '+v+']','k sca[k zhb['+reverse+'] '+minus+']',
        'k ssc[p ssd p zhb p zha]')+']].\n'
    text+='d ssj[] e[b context[k sca[k zha['+forward+'] k zha['+reverse+']]]].\n'
    text+='d ssk[] e[b context['+both('k ba['+scale(v)+']','k ba['+scale(minus)+']','k sca['+scale(v)+' '+scale(minus)+']')+']].\n'
    text+='d ssl[] e[b context['+both('k ba['+scale(v)+']','k ba['+scale(minus)+']','k sca['+scale(v)+' '+one+']','k sca['+scale(minus)+' '+one+']')+']].\n'
    text+='d ssm[] e[b context['+both('t[k sro[]][v context]','t[k ssk[]][v context]','k bg['+zero+' '+scale(v)+']')+']].\n'
    text+='d ssn[first a second a] c[k sre[v first v second k tc[] '+v+' i[speed '+CUT+']['+one+']]].\n'
    text+='d sso[] e[b context[k spi[p ssn]]].\n'
    text+='d ssp[] e[b context['+both('t[k spk[]][v context]','t[k ssl[]][v context]','t[k spq[]][v context]')+']].\n'
    text+='d ssq[] e[b context[w[t[k ssh[]][v context]][t[k ssi[]][v context]]]].\n'
    text+='d ssr[] e[b context[w[t[k ssh[]][v context]][t[k ssj[]][v context]]]].\n'
    text+='d sss[] e[b context['+both('t[k ssh[]][v context]','t[k sro[]][v context]','t[k ssk[]][v context]')+']].\n'
    text+='d sst[] e[b context[y[t[k ssh[]][v context]][z[t[k ssj[]][v context]][t[k ssk[]][v context]]]]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zhg[k zhh[] k rd[] r[k spc[]] k rh[] k ri[]]].
s[k ug[k zhi[] k rd[] r[k sse[]] k rh[] k ri[]]].
s[k zc[k zhj[] k rd[] r[k sse[]] r[k ssf[]] k rh[] k ri[]]].
s[k zhf[k zhk[] k rd[] r[k spc[]] r[k ssg[]] k rh[] k ri[]]].
s[w[k uh[k zhl[] k rd[] r[k ssi[]] k rh[] k ri[]]][k zdg[k zhl[] k rd[] r[k ssi[]] k rh[] k ri[]]]].
s[k zc[k zhm[] k rd[] r[k ssq[]] r[k ssj[]] k rh[] k ri[]]].
s[k zd3[k zhn[] k rd[] r[k ssh[]] r[k ssj[]] r[k ssk[]] k rh[] k ri[]]].
s[k zfl[k zhq[] k rd[] r[k sss[]] r[k ssm[]] k rh[] k ri[]]].
s[k zc[k zho[] k rd[] r[k ssm[]] r[k ssl[]] k rh[] k ri[]]].
s[k zd3[k zhp[] k rd[] r[k ssp[]] r[k spk[]] r[k sso[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-reverse-transform-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-transverse-rod-scale-basis-v1',document='examples/v014/einstein-transverse-rod-scale.noema')
    basis['definitions'].update(MEANINGS|{
        'srw':'同じ端点出来事の両系の記録に四式を適用し、運動系ではξ=ζ=0、η=properとする。φの非零とproperの非負を要求する。',
        'srx':'非零の係数についてl/φを(l*φ)/φ²として表す。正の分母の既存除算を使い、負のφを勝手に正へ変えない。',
        'sry':'静止系の端点座標x=v*t、y=l/φ、z=0を記述する。l=0の端点も同じ定義で扱う。',
        'srz':'同じ正の固有長に対する両端の二組の変換と、静止系での同時測定を合わせる。',
        'ssa':'同じ横向きの剛な棒と異なる両端・出来事・両系の実測記録を結ぶ。移動系のη軸上の配置と静止系での同時刻、符号付き並進の軸・速度・単位を保持する。',
        'ssb':'ssaの測定に端点式を結び、正の静止系長さを両端の符号付きy差・l/φ・二地点の距離・棒の長さの呼称に接続する。この向きの規約を明示し、絶対距離だけと区別する。',
        'ssc':'非空の設定範囲で、速度の大きさが同じなら正の測定長も同じである。向きの違いは設定の違いとして保持し、速度の符号や軸を同じものへ置換しない。',
        'ssd':'同じ棒、固有長、単位、剛体理想化、横方向の運動と正の測定長を持つ対称性の比較設定。実際の許容設定範囲はzhcで指定する。',
        'sse':'正速度側で同時測定する横棒と端点の設定内容。',
        'ssf':'正速度側の同時刻の二端点が静止系の二つの座標式を満たす内容。',
        'ssg':'正速度側での静止系測定長をl/φ(v)に接続する内容。',
        'ssh':'同じ棒・同じ固有長を、別設定の正負速度で同じ測定条件により比較する内容。',
        'ssi':'二つの対象設定が対称性の範囲に属し、速度値がvと−vであり、範囲内の同じ速さでは長さが等しいという内容。物理的な対称性は本文が採用する条件。',
        'ssj':'正負速度の二つの測定長が等しいという内容。',
        'ssk':'同じφ関数のvと−vでの値が等しいという内容。積1とは別に要求する。',
        'ssl':'対象速度vと−vでφが1になる内容。有限標本から全速度域を検査済みとはしない。',
        'ssm':'既出の相反条件と反転対称性、正の枝を合わせたφ決定の十分条件。',
        'ssn':'係数を1とした四座標式。未知関数spcの既存定義を変更しない。',
        'sso':'対象範囲の全記録対で係数1の四式と実際の対応が過不足なく一致する内容。',
        'ssp':'既出の四式・φ=1・βの定義を合わせた最終表示への書換え前提。',
        'ssq':'二つの測定と対称性の条件から測定長の一致へ進む前提内容。',
        'ssr':'正の二測定長とその一致からφの二値の一致へ進む前提内容。',
        'sss':'正の測定長と固有長を保持し、係数の正の枝を明示するための追加解釈の前提。',
        'sst':'二つの測定条件が成立するなら、測定長の一致とφの二値の一致が同値である。本文の「または」による書換えを片方向の含意へ縮めない。'})
    decls={d['name']:d for d in doc['declarations']}
    entries=[('zgu',[],'移動系のη軸に沿う今回の横棒。前段の縦棒とは区別する。'),('zgv',[],'η=0側の同じ棒の端点。'),('zgw',[],'η=l側の同じ棒の端点。'),
        ('zgx',['setting'],'各測定設定におけるη=0側の端点の出来事。'),('zgy',['setting'],'各測定設定におけるη=l側の端点の別出来事。'),('zgz',[],'同じ横棒の正の固有長l。'),('zg2',[],'同じ棒を逆速度で比較する別の測定設定。'),
        ('zha',['setting'],'同じ横棒の静止系での測定長の候補値。ssbまたはssdで測定・物体に結ぶ。'),('zhb',['setting'],'対称性の比較設定における符号付き速度値。'),('zhc',['setting'],'同じ横棒の運動方向と向きの対称性を比較する許容設定。履歴・幾何からの一般的構成は未完。'),('zhd',['setting'],'対称性の比較設定での運動方向を指定する軸。'),
        ('zhf',['node','author','function_description','physical_content','scope','context'],'著者が関数の物理的な解釈を、指定した測定内容によって与える。関数値の計算済み事実や全速度での証明とは分ける。'),
        ('zhg',['node','author','function_description','scope','context'],'著者が指定した関数の物理的な意味を問いとして提示する。値を問う計算問題とは区別する。'),
        ('zhh',[],'φの物理的な意味を問う箇所。'),('zhi',[],'η軸上の横棒を取り上げる箇所。'),('zhj',[],'両端の静止系座標を述べる箇所。'),('zhk',[],'測定長からφの意味を示す箇所。'),('zhl',[],'方向と向きによらない対称性を明らかとする箇所。'),('zhm',[],'正負速度の長さの一致を述べる箇所。'),('zhn',[],'長さの一致をφの一致へ書き換える箇所。'),('zho',[],'相反条件と対称性からφ=1を得る箇所。'),('zhp',[],'φ=1を四式へ代入する箇所。'),('zhq',[],'正の長さと符号付き横差の規約に基づく正の枝の追加解釈。')]
    for name,args,meaning in entries:
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0097〜u0108の部分記述。棒全体が軸の指定区間を占める物質点の集合、測定の一般理論、許容運動方向の全範囲、原刊照合と意味一致は未完。',
        '座標1はη=l側、座標2はη=0側として接続した。本文の提示順序だけで端点を交換しない。',
        'l/φを正の測定長として扱う向きの規約を明示した。絶対距離l/|φ|と対称性・相反条件だけではφ=−1を除けない。正の枝は追加解釈として区別する。',
        '対称性は同じ棒と速さの許容設定で採用する物理条件であり、端点の代数から導出しない。',
        'φ=1は任意に選んだ対象速度の条件付き代数として検査する。測定設定の全速度域での実現と、一般の実切断の体の機械的証明は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'transverse-rod-scale'),(source_composed,'einstein-transverse-rod-scale')):
        text,basis=compose()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored transverse rod scale differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Transverse rod endpoints, measured lengths and scale normalization composed')


if __name__=='__main__':main()
