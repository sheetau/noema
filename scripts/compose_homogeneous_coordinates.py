"""Separate homogeneous increments, affine form and attribution of an inference."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both

CUT='h[b] c'
VECTOR='h[a] '+CUT
MATRIX='h[a a] '+CUT
MAP='h['+VECTOR+'] '+VECTOR
OP='h['+CUT+' '+CUT+'] '+CUT
VALID='h['+CUT+'] c'
SAME='h['+CUT+' '+CUT+'] c'
TRUE='e[n p a b][n p a b]'
ZERO='n p a b'


def definitions():
    text='''
d shm[axes j[a]] c[
 w[u[e[d[v axes]][n p a b]]][f item a[c[
 q[v axes][i[seen c][TRUE]][i[continuation h[c] c current a][i[seen c][
 w[u[w[v seen][e[v current][v item]]]][c[v continuation][x[v seen][e[v current][v item]]]]
 ]]]][u[TRUE]]]]
].
'''.replace('TRUE',TRUE)
    text+='d shn[axes j[a] vector '+VECTOR+' valid '+VALID+'] c['+both('k shm[v axes]',
        'q[v axes]['+TRUE+'][i[ok c axis a][w[v ok][c[v valid][c[v vector][v axis]]]]]')+'].\n'
    text+='d sho[axes j[a] first '+VECTOR+' second '+VECTOR+' same '+SAME+'] c['+both('k shm[v axes]',
        'q[v axes]['+TRUE+'][i[ok c axis a][w[v ok][c[v same][c[v first][v axis] c[v second][v axis]]]]]')+'].\n'
    text+='d shp[first '+VECTOR+' second '+VECTOR+' add '+OP+'] '+VECTOR+'[i[axis a][c[v add][c[v first][v axis] c[v second][v axis]]]].\n'
    text+='d shq[axes j[a] matrix '+MATRIX+' offset '+VECTOR+' vector '+VECTOR+' add '+OP+' multiply '+OP+'] '+VECTOR+'[i[row a]['+\
        'q[v axes][c[v offset][v row]][i[value '+CUT+' column a][c[v add][v value c[v multiply][c[v matrix][v row v column] c[v vector][v column]]]]]]].\n'
    args='axes j[a] first '+VECTOR+' second '+VECTOR+' shift '+VECTOR+' transform '+MAP+' valid '+VALID+' same '+SAME+' add '+OP+' subtract '+OP
    shifted=lambda name:'k shp[v '+name+' v shift v add]'
    out=lambda v:'c[v transform]['+v+']'
    inc=lambda name:'k shp['+out(shifted(name))+' '+out('v '+name)+' v subtract]'
    requirements=['k shn[v axes '+v+' v valid]' for v in ('v first','v second','v shift',shifted('first'),shifted('second'),out('v first'),out('v second'),out(shifted('first')),out(shifted('second')),inc('first'),inc('second'))]
    text+='d shr['+args+'] c['+both(*requirements,'k sho[v axes '+inc('first')+' '+inc('second')+' v same]')+'].\n'
    globalargs='axes j[a] domain h['+VECTOR+'] c transform '+MAP+' valid '+VALID+' same '+SAME+' add '+OP+' subtract '+OP
    antecedent=both('c[v domain][v first]','c[v domain][v second]','k shn[v axes v shift v valid]',
        'c[v domain]['+shifted('first')+']','c[v domain]['+shifted('second')+']')
    text+='d shs['+globalargs+'] c['+both('k shm[v axes]','g first '+VECTOR+'[c[v domain][v first]]',
        'f first '+VECTOR+'[f second '+VECTOR+'[f shift '+VECTOR+'[y['+antecedent+'][k shr[v axes v first v second v shift v transform v valid v same v add v subtract]]]]]')+'].\n'
    affineargs='axes j[a] domain h['+VECTOR+'] c transform '+MAP+' matrix '+MATRIX+' offset '+VECTOR+' valid '+VALID+' same '+SAME+' add '+OP+' multiply '+OP
    matrixvalid='q[v axes]['+TRUE+'][i[ok c row a][w[v ok][q[v axes]['+TRUE+'][i[good c column a][w[v good][c[v valid][c[v matrix][v row v column]]]]]]]]'
    body=both('k shn[v axes v vector v valid]','k shn[v axes c[v transform][v vector] v valid]',
        'k sho[v axes c[v transform][v vector] k shq[v axes v matrix v offset v vector v add v multiply] v same]')
    text+='d sht['+affineargs+'] c['+both('k shn[v axes v offset v valid]',matrixvalid,
        'g vector '+VECTOR+'[c[v domain][v vector]]','f vector '+VECTOR+'[y[c[v domain][v vector]]['+body+']]')+'].\n'
    # A rational row is a separate algebraic lemma carrier, not a real-cut approximation.
    terms=['k ad[v '+coefficient+' v '+value+']' for coefficient,value in zip(('a','b','c','d'),('x','y','z','t'))]
    summed='v offset'
    for term in terms:summed='k ab['+summed+' '+term+']'
    text+='d shw[a b b b c b d b offset b x b y b z b t b] b['+summed+'].\n'
    return text


MEANINGS={
    'shm':'成分の列が空でなく、同じ役割を重複して含まない。',
    'shn':'成分列がshmを満たし、ベクトルの全成分が有効な値である。',
    'sho':'同じ成分列の全成分の値が一致する。関数の個体同一性は要求しない。',
    'shp':'指定した二項演算を二ベクトルの各成分へ適用する。加算にも差にも使える。',
    'shq':'各出力成分について、同じ行列の係数と全入力成分の積を足し、その成分固有の定数項を加える。',
    'shr':'二つの出発点と同じ変位を取り、変換前後の点と変位が有効で、変換後の増分が両出発点で一致することを要求する。',
    'shs':'非空の対象範囲の全出発点対と、移動後も範囲内にとどまる全有効な変位についてshrを要求する。一様性の操作的な部分モデル。',
    'sht':'同じ一つの行列と定数ベクトルが全対象入力の変換を与えるというアフィン形の条件。入力ごとに係数を選び直さない。',
    'shw':'四つの有理数入力に対する一行のアフィン式。全実切断の演算や物理的な変換の導出とは別の代数的検査に使う。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.\n'+definitions())
    inherited=json.loads((ROOT/'data/einstein-coordinate-correspondence-basis-v1.json').read_text(encoding='utf-8'))
    basis={'version':'homogeneous-coordinates-basis-v1','document':'examples/v014/homogeneous-coordinates.noema',
        'primitives':[deepcopy(p) for p in inherited['primitives'] if p['symbol'] in ('aa','ab','ac','ad')],
        'definitions':MEANINGS.copy(),'unresolved':[
            '同じ増分の出発点独立性から、実数全域での行列表示を導く一般定理はここでは証明しない。連続性などの条件と対象範囲の形の検討は残る。',
            '定数項を許すアフィン形と、原点を保つ線形写像を区別する。定数項を自動的に零にはしない。',
            '成分ごとの数値演算であり、時間と長さを加算する物理操作ではない。混合成分の係数は単位を固定した数値として解釈する。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-coordinate-correspondence.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()
    zero='k bb['+ZERO+']'
    nonnegative=lambda v:'k bc['+zero+' v '+v+']'
    text+='d shu[value '+CUT+'] '+CUT+'[i[q b][x[w['+nonnegative('value')+'][c[v value][v q]]][w[u['+nonnegative('value')+']][c[k be[v value]][v q]]]]].\n'
    equal_sign='z['+nonnegative('first')+']['+nonnegative('second')+']'
    magnitude='k sah[k shu[v first] k shu[v second]]'
    text+='d shv[first '+CUT+' second '+CUT+'] '+CUT+'[i[q b][x[w['+equal_sign+'][c['+magnitude+'][v q]]][w[u['+equal_sign+']][c[k be['+magnitude+']][v q]]]]].\n'
    text+='r zdd[a a a a d] '+MAP+'.r zde[] a.r zdf[] a.r zdg[a a i[e] a d] c.r zdh[a a i[e] a d] c.\n'
    text+='d shx[] j[a][l[a][k yn[] k yo[] k yp[] k zc7[]]].\n'
    text+='d shy[tuple a] '+VECTOR+'[i[role a][k zc6[v tuple v role]]].\n'
    text+='d shz[vector '+VECTOR+'] c['+both('k shn[k shx[] v vector p ba]',
        'g tuple a[w[k shf[v tuple]][k sho[k shx[] v vector k shy[v tuple] p sca]]]')+'].\n'
    member='q[k shx[]][u['+TRUE+']][i[found c axis a][x[v found][e[v axis][v role]]]]'
    text+='d sie[vector '+VECTOR+'] '+VECTOR+'[i[role a][i[q b][x[w['+member+'][c[c[v vector][v role]][v q]]][w[u['+member+']][k aa[v q '+ZERO+']]]]]].\n'
    text+='d sia[] '+MAP+'[i[vector '+VECTOR+'][k sie[c[k zdd[k ra[] k zbm[] k ta[] k rb[] k zb6[]]][k sie[v vector]]]]].\n'
    text+='d sib[transform '+MAP+'] c['+both('k sgw[p shf p shg p she p shh]',
        'f first a[y[k shf[v first]][k shn[k shx[] c[v transform][k shy[v first]] p ba]]]',
        'f first a[f second a[y[w[k shf[v first]][k shg[v second]]][z[k she[v first v second]][k sho[k shx[] c[v transform][k shy[v first]] k shy[v second] p sca]]]]]')+'].\n'
    text+='d sic[] e[b context['+both('k sib[k sia[]]',
        'k shs[k shx[] p shz k sia[] p ba p sca p bd p bf]')+']].\n'
    text+='d sid[] e[b context['+both('k sib[k sia[]]',
        'g matrix '+MATRIX+'[g offset '+VECTOR+'[k sht[k shx[] p shz k sia[] v matrix v offset p ba p sca p bd p shv]]]')+']].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k ug[k zde[] k rd[] r[k sic[]] k rh[] k ri[]]].
s[w[k zc[k zdf[] k rd[] r[k sic[]] r[k sid[]] k rh[] k ri[]]][w[k zdg[k zdf[] k rd[] r[k sid[]] k rh[] k ri[]]][k zdh[k zdf[] k zdb[] r[k sid[]] k rh[] k ri[]]]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-coordinate-correspondence-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-homogeneous-coordinates-basis-v1',document='examples/v014/einstein-homogeneous-coordinates.noema')
    basis['definitions'].update(MEANINGS);decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zdd',['from_frame','to_frame','length_unit','time_unit','context'],'指定した系・単位・設定での四座標変換の候補。観測された同じ出来事の対応との一致はsibで別に要求する。'),
        ('zde',[],'空間と時間へ一様性を帰属させる本文箇所。'),('zdf',[],'その一様性から線形性が従うと述べる本文箇所。'),
        ('zdg',['node','author','content','scope','context'],'著者がこの内容を明らかであると提示するという帰属。検査器による自明性や証明の認定ではない。'),
        ('zdh',['node','task_node','required_content','scope','context'],'先行する課題への解に、記述された条件が必要だと述べる箇所の対応。解の発見や存在は含意しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'shu':'有効な実切断の絶対値。零以上ならそのまま、負なら既存の符号反転beを使う。',
        'shv':'二つの有効な実切断の積。絶対値の非負積sahを作り、符号が違うときに反転する。',
        'shx':'三位置成分と時刻の四役割の列。',
        'shy':'座標記録から四成分を読む関数。',
        'shz':'測定済みの静止系座標と四成分の値が一致する有効なベクトルの範囲。',
        'sie':'四役割以外の成分を零へ固定する関数表現。選択外の値を隠れた入力に使わせないための表現規約であり、物理的に余分な座標を追加するものではない。',
        'sia':'前段の同じ二系・単位・運動設定に変換候補を固定し、入力と出力をsieで四役割へ制限する。',
        'sib':'同じ出来事の測定済み座標の対応と変換候補の出力が、対象範囲の全座標対で過不足なく一致する。',
        'sic':'前段の座標対応に合う変換について、対象範囲内の同じ変位の増分が出発点に依存しないという一様性の部分モデル。',
        'sid':'同じ座標対応に合う変換が、全対象入力に共通する一つの行列と成分別の原点定数で表せるというアフィン形の内容。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0047の部分解釈。一様性を変換の増分の出発点独立性へ接続するが、物理法則の一様性一般と同義であることは示していない。',
        '原文のlinearを、原点定数を残せるアフィン形として読む。式の代数的な書き方すべてが一次式でなければならないとは主張しない。',
        'sicからsidへの一般的な含意は証明せず、著者の必然性と明白さの提示を帰属として保存する。連続性、対象範囲の完全性と原点規約は今後の検討事項。',
        'signed productの実数体としての一般法則の機械的証明は未完。有限整数切断で全実数演算を代用しない。',
        '具体的な係数、速度への依存、変換の導出、原刊照合、全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/homogeneous-coordinates-basis-v1.json'),(source_composed,'data/einstein-homogeneous-coordinates-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored homogeneous coordinates differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Homogeneous increments, affine form and attributed inference composed')


if __name__=='__main__':main()
