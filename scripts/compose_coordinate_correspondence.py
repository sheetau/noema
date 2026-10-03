"""Describe same-event coordinate correspondence and a still-open equation task."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both

SIDE='h[a a c] h[b] c'
SYSTEM='j['+SIDE+']'
TRUE='e[n p a b][n p a b]'


def definitions():
    text='''
d sgt[first a second a roles h[a] c component h[a a] h[b] c same h[h[b] c h[b] c] c] c[
 w[g role a[c[v roles][v role]]][f role a[y[c[v roles][v role]][c[v same][c[v component][v first v role] c[v component][v second v role]]]]]
].
d sgu[events h[a] c source h[a a] c target h[a a] c first a second a] c[
 g event a[w[c[v events][v event]][w[c[v source][v event v first]][c[v target][v event v second]]]]
].
d shl[place a candidates h[a] c] c[
 w[c[v candidates][v place]][f other a[y[c[v candidates][v other]][e[v other][v place]]]]
].
d sgv[events h[a] c source h[a a] c target h[a a] c same h[a a] c] c[
 w[g event a[c[v events][v event]]][f event a[y[c[v events][v event]][
 w[g first a[c[v source][v event v first]]][w[g second a[c[v target][v event v second]]][
 f first a[f second a[w[
 y[w[c[v source][v event v first]][c[v source][v event v second]]][c[v same][v first v second]]][
 y[w[c[v target][v event v first]][c[v target][v event v second]]][c[v same][v first v second]]]]]]]
 ]]]
].
d sgw[left h[a] c right h[a] c relation h[a a] c same h[a a] c] c[
 w[g first a[c[v left][v first]]][f first a[y[c[v left][v first]][
 w[g second a[w[c[v right][v second]][c[v relation][v first v second]]]][
 f other a[f second a[f third a[y[w[c[v left][v other]][w[c[v same][v first v other]][w[c[v right][v second]][w[c[v right][v third]][w[c[v relation][v first v second]][c[v relation][v other v third]]]]]]][c[v same][v second v third]]]]]]
 ]]]
].
'''
    lhs='c[v equation][v first v second '+TRUE+']'
    rhs='c[v equation][v first v second u['+TRUE+']]'
    text+='d sgx[equations '+SYSTEM+' first a second a valid h[h[b] c] c same h[h[b] c h[b] c] c] c['+both(
        'u[e[d[v equations]][n p a b]]',
        'q[v equations]['+TRUE+'][i[accepted c equation '+SIDE+']['+both(
            'v accepted','c[v valid]['+lhs+']','c[v valid]['+rhs+']','c[v same]['+lhs+' '+rhs+']')+']]')+'].\n'
    args='left h[a] c right h[a] c relation h[a a] c tuplesame h[a a] c valid h[h[b] c] c same h[h[b] c h[b] c] c'
    text+='d sgy[equations '+SYSTEM+' '+args+'] c['+both(
        'k sgw[v left v right v relation v tuplesame]',
        'f first a[f second a[y[w[c[v left][v first]][c[v right][v second]]][z[k sgx[v equations v first v second v valid v same]][c[v relation][v first v second]]]]]')+'].\n'
    text+='d sgz['+args+'] g['+SYSTEM+'][j v[i[equations '+SYSTEM+'][k sgy[v equations v left v right v relation v tuplesame v valid v same]]]].\n'
    return text


MEANINGS={
    'sgt':'非空の成分範囲で全ての成分値が一致する。記録の識別子の一致と、数値の一致を分ける。',
    'sgu':'同じ一つの対象が第一表現と第二表現を持つという対応。二つの別対象から表現を取り出して組み合わせない。',
    'shl':'指定した場所が候補条件を満たし、同じ候補条件を満たす場所が全てその場所と同一である。出来事の同一性とは分ける。',
    'sgv':'対象範囲は非空で、全対象に両側の表現が存在し、それぞれの側の全候補が値として一致する。同じ表現を持つ別対象の存在は禁じない。',
    'sgw':'第一表現の範囲が非空で、全第一表現に第二表現の対応が存在する。同じ値の第一表現から対応する第二表現は全て同じ値になる。両側の記録の識別子の唯一性や逆向きの一意性は要求しない。',
    'sgx':'非空の有限な方程式列を、同じ二表現へ適用する。各式の左右の値が有効で同じ値であることを全式に要求する。各項は二表現と左右の選択を受け取る関数で表す。',
    'sgy':'対応がsgwを満たし、対象範囲の全表現対で、方程式列を満たすことと実際の対応が同値になる。対応する例だけでなく、余分な解も検査する。',
    'sgz':'sgyを満たす有限の方程式列を答えとする質問。答えの存在、発見、唯一性、導出済みを主張しない。',
}


def generic_composed():
    doc=parse('n:\n'+definitions())
    basis={'version':'coordinate-correspondence-basis-v1','document':'examples/v014/coordinate-correspondence.noema',
        'primitives':[],'definitions':MEANINGS.copy(),'unresolved':[
            '対象・表現の範囲、値の妥当性と同値性は引数で与える。範囲の完全性や物理的な実現は有限例からは証明できない。',
            '方程式の項を関数として与える意味論であり、特定の代数的構文への制限や方程式を発見するアルゴリズムは追加しない。',
            'sgyの過不足のない対応は指定範囲に相対的である。有限標本との一致を全空間での変換則の証明と扱わない。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    old=parse((ROOT/'examples/v014/einstein-frame-measurements.noema').read_text(encoding='utf-8'))
    statements,old['statements']=old['statements'],[]
    text=format_graph(old,'compact')+definitions()+'''
r zc4[a] c.r zc5[a] c.r zc6[a a] h[b] c.r zc7[] a.
r zda[] a.r zdb[] a.
'''
    text+='r zdc[a a i[g['+SYSTEM+']] a d] c.\n'
    roles=('yn','yo','yp','zc7')
    role_scope='x[e[v role][k yn[]]][x[e[v role][k yo[]]][x[e[v role][k yp[]]][e[v role][k zc7[]]]]]'
    text+='d sha[tuple a valid h[h[b] c] c] c['+both('k zc5[v tuple]',
        *('u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(roles) for b in roles[i+1:]),
        *('c[v valid][k zc6[v tuple k '+r+'[]]]' for r in roles))+'].\n'
    text+='d shb[first a second a same h[h[b] c h[b] c] c] c[k sgt[v first v second i[role a]['+role_scope+'] p zc6 v same]].\n'
    conditions=['k zcu[v place v frame v context]','k cb[v event v place v frame]',
        'k sgp[v event v place v frame k rb[] v context v synchrony v valid v same]',
        'c[v same][k zc6[v tuple k zc7[]] k zbe[v event v frame k rb[] v context]]']
    for r in roles[:3]:
        conditions+=['k sgk[v place v frame k '+r+'[] k ta[] v context v valid v same]',
            'c[v same][k zc6[v tuple k '+r+'[]] k zcy[v place v frame k '+r+'[] k ta[] v context]]']
    location=['k zcu[v other v frame v context]']
    for r in roles[:3]:
        location+=['k sgk[v other v frame k '+r+'[] k ta[] v context v valid v same]',
            'c[v same][k zc6[v tuple k '+r+'[]] k zcy[v other v frame k '+r+'[] k ta[] v context]]']
    conditions+=['k shl[v place i[other a]['+both(*location)+']]']
    text+='d shc[event a tuple a frame a context d synchrony h[a a a a d] c valid h[h[b] c] c same h[h[b] c h[b] c] c] c['+both(
        'k zc4[v event]','k zcz[v event v frame v context]','k va[v frame]','k ti[k ta[]]','k ci[k rb[]]',
        'k sha[v tuple v valid]','g place a['+both(*conditions)+']')+'].\n'
    text+='''
d shd[event a tuple a frame a context d] c[k shc[v event v tuple v frame v context p qo p ba p sca]].
d she[first a second a] c[k sgu[p zc4 i[event a tuple a][k shd[v event v tuple k ra[] k zb6[]]] i[event a tuple a][k shd[v event v tuple k zbm[] k zb6[]]] v first v second]].
d shf[tuple a] c[g event a[w[k zc4[v event]][k shd[v event v tuple k ra[] k zb6[]]]]].
d shg[tuple a] c[g event a[w[k zc4[v event]][k shd[v event v tuple k zbm[] k zb6[]]]]].
d shh[first a second a] c[k shb[v first v second p sca]].
d shi[] e[b context[
 w[k sgv[p zc4 i[event a tuple a][k shd[v event v tuple k ra[] k zb6[]]] i[event a tuple a][k shd[v event v tuple k zbm[] k zb6[]]] p shh]][
 k sgw[p shf p shg p she p shh]]
]].
'''
    text+='d shj[equations '+SYSTEM+'] c[k sgy[v equations p shf p shg p she p shh p ba p sca]].\n'
    text+='d shk[] g['+SYSTEM+'][k sgz[p shf p shg p she p shh p ba p sca]].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k uh[k zda[] k rd[] r[k shi[]] k rh[] k ri[]]][k zao[k zc3[] k zda[] k rh[] k ri[]]]].
s[k zdc[k zdb[] k rd[] r[k shk[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-frame-measurements-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-coordinate-correspondence-basis-v1',document='examples/v014/einstein-coordinate-correspondence.noema')
    basis['definitions'].update(MEANINGS)
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zc4',['event'],'二系の座標を比較する同じ出来事の範囲。有限観測標本だけではなく、記述が対象とする全出来事を指定する。'),
        ('zc5',['tuple'],'三位置成分と一時刻成分を持つ座標値の組。値と各系・単位・出来事との結合はshcで要求する。'),
        ('zc6',['tuple','role'],'座標値の組から指定成分の実切断を取り出す。三位置成分は共通長さ単位ta、時刻成分は共通時間単位rbで扱う。役割以外の引数での値は使用しない。'),
        ('zc7',[],'四つの成分のうち時刻を表す役割。三位置成分の役割と異なる。'),
        ('zda',[],'同じ出来事の座標値の組が二つの系で対応すると述べる本文箇所。'),
        ('zdb',[],'座標を結ぶ方程式系を求めることを課題として提示する本文箇所。'),
        ('zdc',['node','author','question','scope','context'],'著者が記述された質問の答えを見いだすことを課題として提示する。解の存在・唯一性・発見済み・証明済みを含意しない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update({
        'sha':'座標値の組が型を持ち、四成分の役割が全て異なり、全成分が有効な値である。',
        'shb':'四成分全ての値を比較する。同じ場所・時刻の別出来事や別記録を、同じ個体へ潰さない。',
        'shc':'同じ出来事の同じ系での場所を選び、その場所の三座標と局所時計による時刻へ四成分を結ぶ。座標測定と時刻付与の存在・一意性に加え、その三座標を持つ範囲内の測定済み場所が同一であることも要求する。',
        'shd':'shcの時計同期をqo、有効な実切断をba、値一致をscaへ接続する。',
        'she':'静止系と運動系で同じ出来事に付与される座標値の組の対応。',
        'shf':'対象出来事に静止系の測定で実際に付与できる座標値の組の範囲。',
        'shg':'同じ対象出来事に運動系の測定で実際に付与できる座標値の組の範囲。',
        'shh':'shbを実切断の値の一致へ固定する。',
        'shi':'全対象出来事が両系で値として一意な四座標を持ち、全静止系座標に値として一意な運動系座標が対応するという内容。出来事の識別子の一意性は要求しない。',
        'shj':'対象範囲の座標対に対して、非空の方程式列の解が同じ出来事の対応と過不足なく一致するという解候補条件。',
        'shk':'shjと同じ候補条件を持つ方程式列を求める質問。後段の具体的な変換式を先に答えとして埋め込まない。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0046の部分記述。Ort und Zeitを三位置成分と時刻として接続し、測定済み地点間で場所が一意になる条件も要求した。その条件の幾何学的な根拠、全空間の座標表現の完全性は未完。',
        'shcは前段の時計配置点での測定条件を使う。時計のない地点への時刻の拡張や、任意の実数四組が実現するという全域性を追加しない。',
        '同じ座標を持つ別出来事を許す。逆変換の存在や第二系から第一系への一意性はこの段落の接続条件へ追加しない。',
        '方程式列は左右の実数値を返す関数の列として記述する。代数的構文、線形性、原点定数、具体的変換の導出は後続段落の課題である。',
        '原刊照合と全文の意味確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/coordinate-correspondence-basis-v1.json'),(source_composed,'data/einstein-coordinate-correspondence-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored correspondence differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Same-event correspondence and the equation-finding task composed')


if __name__=='__main__':main()
