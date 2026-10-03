"""Compose the affine time form, its zero-origin convention and unfixed scale."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_transverse_time import CUT, TAU

PHI='h['+CUT+'] '+CUT
FAMILY='h[d] '+PHI
DOMAIN='h['+CUT+'] c'
SAME='h['+CUT+' '+CUT+'] c'


def rational_definitions():
    return '''
d slx[light b speed b space b ycoef b zcoef b timecoef b offset b] c[w[k skb[v light v speed v space v timecoef]][w[e[v ycoef][n p a b]][w[e[v zcoef][n p a b]][e[v offset][n p a b]]]]].
d sly[light b speed b inverse b] c[w[u[k aa[v speed n p a b]]][w[k aa[v speed v light]][k sja[n p b b k ab[k ad[v light v light] k ac[k ad[v speed v speed]]] v inverse]]]].
d slz[light b speed b scale b inverse b x b time b] b[k ad[v scale k ab[v time k ac[k ad[k ad[v speed v inverse] v x]]]]].
'''


def uncertainty_definitions():
    args='agent a stage d domain '+DOMAIN+' alternatives h[a d d] c family '+FAMILY+' same '+SAME
    value=lambda stage:'c[c[v family][v '+stage+']][v speed]'
    text='d sma['+args+' first d second d speed '+CUT+'] c['+both(
        'c[v alternatives][v agent v stage v first]','c[v alternatives][v agent v stage v second]',
        'c[v domain][v speed]',
        'u[c[v same]['+value('first')+' '+value('second')+']]')+'].\n'
    # The input domain is a speed range, not a range for coefficient values.
    text+='d smb['+args+'] c[g first d[g second d[g speed '+CUT+'[k sma[v agent v stage v domain v alternatives v family v same v first v second v speed]]]]].\n'
    return text


MEANINGS={
    'slx':'有理数のアフィン係数について、縦方向の偏微分方程式、二つの横係数の零、原点定数の零を分けて要求する。',
    'sly':'0≤v<Vのもとで、V²-v²の正の逆数を結ぶ有理数の条件。',
    'slz':'a*(t-v*x′/(V²-v²))の有理数の式。inverseはslyで結ぶ。aを1や特定の速度関数へ固定しない。',
    'sma':'同じ主体・段階に残された二つの候補状況で、同じ対象速度における関数の値が一致しない。候補関数の有効性は呼出側が規定する。',
    'smb':'対象速度のどこかで値が異なる二つの候補関数が、その段階に残るという未決定性。認識や知識の一般的な定義ではない。',
}


def generic_composed():
    doc=parse((ROOT/'examples/v014/transverse-time.noema').read_text(encoding='utf-8')+rational_definitions()+uncertainty_definitions())
    basis=deepcopy(json.loads((ROOT/'data/transverse-time-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='affine-time-form-basis-v1',document='examples/v014/affine-time-form.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['候補が複数あるという未決定性と、唯一の解を主体が知らないことを区別する。速度以外の変数への依存と単位変更は同じ関数族の外で扱う。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-transverse-time.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()+uncertainty_definitions()
    zero='k bb[n p a b]'
    coefficient_names=('space','ycoef','zcoef','timecoef','offset')
    coordinates=('x','y','z','time')
    coeffargs=' '.join(n+' '+CUT for n in coefficient_names)
    coordargs=' '.join(n+' '+CUT for n in coordinates)
    cv=' '.join('v '+n for n in coefficient_names)
    xv=' '.join('v '+n for n in coordinates)
    valid=lambda names:both(*('k ba[v '+n+']' for n in names))
    def forall(names,body):
        for name in reversed(names):body='f '+name+' '+CUT+'['+body+']'
        return body
    def exists(names,body):
        for name in reversed(names):body='g '+name+' '+CUT+'['+body+']'
        return body
    expression='v offset'
    for coefficient,coordinate in zip(coefficient_names,coordinates):
        expression='k bd['+expression+' k shv[v '+coefficient+' v '+coordinate+']]'
    text+='d smc['+coeffargs+' '+coordargs+'] '+CUT+'['+expression+'].\n'
    evaluated='c[v function]['+xv+']'
    text+='d smd[function '+TAU+' '+coeffargs+'] c['+both(valid(coefficient_names),forall(coordinates,
        'y['+valid(coordinates)+']['+both('k ba['+evaluated+']','k sca['+evaluated+' k smc['+cv+' '+xv+']]')+']'))+'].\n'
    text+='d sme[function '+TAU+' '+coeffargs+' '+coordargs+'] c['+both(valid((*coefficient_names,*coordinates)),
        'k sjw[v function '+xv+' v space v timecoef]',
        'k sjs[p ba i[coordinate '+CUT+'][c[v function][v x v coordinate v z v time]] v y v ycoef]',
        'k sjs[p ba i[coordinate '+CUT+'][c[v function][v x v y v coordinate v time]] v z v zcoef]')+'].\n'
    text+='d smf[function '+TAU+' light '+CUT+' speed '+CUT+' time '+CUT+' '+coeffargs+'] c['+both(
        'k smd[v function '+cv+']','k sme[v function '+cv+' '+zero+' '+zero+' '+zero+' v time]',
        'k sjy[v light v speed v space v timecoef]','k slk[v function '+zero+' '+zero+' '+zero+' v time]')+'].\n'
    atzero='c[v function]['+' '.join([zero]*4)+']'
    text+='d smg[function '+TAU+'] c['+both('k ba['+atzero+']','k sca['+atzero+' '+zero+']')+'].\n'
    delta='k bf[k shv[v light v light] k shv[v speed v speed]]'
    text+='d smh[light '+CUT+' speed '+CUT+' scale '+CUT+' x '+CUT+' time '+CUT+'] '+CUT+'[k shv[v scale k bf[v time k shv[k sje[v speed '+delta+'] v x]]]].\n'
    text+='d smi[function '+TAU+' light '+CUT+' speed '+CUT+' scale '+CUT+'] c['+both(
        valid(('light','speed','scale')),'k bc['+zero+' v speed]','k bg[v speed v light]',forall(coordinates,
        'y['+valid(coordinates)+']['+both('k ba['+evaluated+']','k sca['+evaluated+' k smh[v light v speed v scale v x v time]]')+']'))+'].\n'
    text+='d smj[function '+TAU+' coefficient '+PHI+' light '+CUT+' speed '+CUT+'] c[k smi[v function v light v speed c[v coefficient][v speed]]].\n'
    ctx='v context';event='v event';rest='k zdz['+event+' k ra[] '+ctx+']';moving='k zdz['+event+' k zbm[] '+ctx+']'
    clauses=['k zbv[k zbm[] k zbn[k zbm[] '+ctx+'] '+ctx+']',
        'k cb['+event+' k zbn[k zbm[] '+ctx+'] k zbm[]]',
        'k shd['+event+' '+rest+' k ra[] '+ctx+']','k shd['+event+' '+moving+' k zbm[] '+ctx+']']
    clauses+=['k sca[k sin[k zb7[] k zc6['+rest+' k yn[]] k zc6['+rest+' k zc7[]]] '+zero+']']
    for role in ('yo','yp','zc7'):clauses+=['k sca[k zc6['+rest+' k '+role+'[]] '+zero+']']
    for role in ('yn','yo','yp','zc7'):clauses+=['k sca[k zc6['+moving+' k '+role+'[]] '+zero+']']
    text+='d smk[event a context d] c['+both(*clauses)+'].\n'
    text+='d sml[context d] c['+both('k sio[k zd4[]]','k smg[k zd4[]]','g event a[k smk[v event v context]]')+'].\n'
    text+='r zeq[] '+PHI+'.r zer[] '+FAMILY+'.r zes[] d.r zet[a d d] c.\n'
    text+='r zeu[] a.r zev[] a.r zew[] a.r zex[a a a d] c.\n'
    text+='d smr[function '+TAU+' light '+CUT+' speed '+CUT+' time '+CUT+' coefficient '+PHI+' '+coeffargs+'] c['+both(
        'k smf[v function v light v speed v time '+cv+']','k ba[c[v coefficient][v speed]]',
        'k sca[v timecoef c[v coefficient][v speed]]')+'].\n'
    time='k sjh[k qe[k zdq[]] k zb6[]]'
    text+='d smm[] e[b context['+both('k sio[k zd4[]]',
        'k skn[k zd4[] k tc[] k zb7[] '+time+']','k slm[k zd4[] '+time+']',
        exists(coefficient_names,'k smr[k zd4[] k tc[] k zb7[] '+time+' k zeq[] '+cv+']'),'k sml[k zb6[]]')+']].\n'
    text+='d smn[] e[b context[k smj[k zd4[] k zeq[] k tc[] k zb7[]]]].\n'
    text+='d smo[] e[b context[k sml[k zb6[]]]].\n'
    # Candidate functions must be defined on the same admissible speed domain.
    text+='d sms[coefficient '+PHI+' family '+FAMILY+' stage d speed '+CUT+'] c['+both(
        'k ba[v speed]','k ba[c[v coefficient][v speed]]','k ba[c[c[v family][v stage]][v speed]]',
        'k sca[c[v coefficient][v speed] c[c[v family][v stage]][v speed]]')+'].\n'
    text+='d smq[coefficient '+PHI+' family '+FAMILY+' stage d domain '+DOMAIN+'] c['+forall(('speed',),
        'y[c[v domain][v speed]][k sms[v coefficient v family v stage v speed]]')+'].\n'
    domain='i[speed '+CUT+']['+both('k ba[v speed]','k bc['+zero+' v speed]','k bg[v speed k tc[]]')+']'
    validfamily='f alternative d[y[k zet[k zee[] k zes[] v alternative]]['+forall(('speed',),
        'y[c['+domain+'][v speed]][k ba[c[c[k zer[]][v alternative]][v speed]]]')+']]'
    text+='d smp[] e[b context['+both('k zet[k zee[] k zes[] k zes[]]',validfamily,
        'k smq[k zeq[] k zer[] k zes[] '+domain+']',
        'k smb[k zee[] k zes[] '+domain+' p zet k zer[] p sca]')+']].\n'
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[w[k ug[k zev[] k rd[] r[k smo[]] k rh[] k ri[]]][k zex[k zev[] k rd[] k rh[] k ri[]]]].
s[k zc[k zeu[] k rd[] r[k smm[]] r[k smn[]] k rh[] k ri[]]].
s[k uh[k zew[] k rd[] r[k smp[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-transverse-time-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-affine-time-form-basis-v1',document='examples/v014/einstein-affine-time-form.noema')
    basis['definitions'].update(MEANINGS|{
        'smc':'四つの座標のアフィン式。空間三係数、時間係数、原点定数を別の引数に保持する。',
        'smd':'同じ五つの係数が全ての有効な四座標で同じτを与える。入力ごとに係数を選び直さない。',
        'sme':'同じτの指定点で四偏微分がアフィン式の対応係数に一致する。縦・横・時間の引数を固定して差商の極限へ結ぶ。',
        'smf':'一つのアフィン表示とその偏微分係数、縦方向の方程式、横二方向の零条件を同じτと時刻へ結ぶ。原点定数をまだ消さない。',
        'smg':'τ(0,0,0,0)=0という座標式上の原点選択。横方向の偏微分の零だけからは導かない。',
        'smh':'実切断の式a*(t-v*x′/(V²-v²))。分母の正性と入力の妥当性はsmiで要求する。',
        'smi':'0≤v<Vの同じV,v,aについて、τが全有効入力でsmhに一致する。aの特定値や符号はこの式だけで補わない。',
        'smj':'同じ速度関数φを同じvで評価した値をaとしてsmiへ渡す。位置や時刻をφの隠れた引数にしない。',
        'smk':'運動系原点の同じ出来事が両系の座標記録に結ばれ、x′,y,z,tとξ,η,ζ,τが共通零点になるという明示的な原点規約。',
        'sml':'実際の座標対応に合うτ、零での関数値、同じ出来事での両系の零点を結ぶ。',
        'smm':'先行する縦・横の偏微分条件、同じτのアフィン性と係数の微分値、時刻原点の選択を含む明示的な導出前提。',
        'smn':'未定の速度関数φ(v)を係数aとする時間座標の式という内容。',
        'smo':'両系の同じ原点出来事で時刻を零に合わせるという選択内容。',
        'smq':'同じ許容速度域で、現在の関数が指定段階の関数族と値として一致し、有効である。関数個体の同一性は要求しない。',
        'smr':'アフィン表示の時間係数が、同じ速度vでの未定関数φの値であると明示して前提に結ぶ。式の結論だけで別の係数を後付けしない。',
        'sms':'指定速度で、現在の係数関数と指定段階の候補関数の値がともに有効で一致する。',
        'smp':'現在の候補を含み、同じ速度域で値が異なる候補も残るという段階依存の未決定性。全候補の係数値の有効性も要求する。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zeq',[],'現在考察する速度から係数への関数φ。値を1や後段の係数へ固定しない。'),
        ('zer',[],'同じ座標系・単位規約における、候補状況ごとの速度係数関数族。'),
        ('zes',[],'この箇所の、係数の決定がまだ終わっていない考察段階。'),
        ('zet',['agent','stage','alternative'],'主体がその段階で排除していない係数関数の候補状況。候補の選び方を明示する関係。'),
        ('zeu',[],'偏微分条件と線形性から時間座標の式を提示する推論箇所。'),
        ('zev',[],'記述を短くするための時刻原点の仮定を述べる箇所。'),
        ('zew',[],'速度係数がこの段階ではまだ未知だと提示する箇所。'),
        ('zex',['node','author','scope','context'],'著者がその仮定を記述の簡潔さのために採ると位置付ける。仮定の必然性や結論の証明ではない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=generic_composed()[1]['unresolved'][-1:]+[
        'u0062〜u0064の部分記述。先行する測定座標上のアフィン性を、τの全有効四座標のアフィン表示へ拡張する読みを明示する。原文との同義性や実測からの導出は未証明。',
        '両系の同じ原点出来事を零とする規約を採った。原文の「運動系の原点でτ=0のときt=0」との含意の過不足、原刊表記の照合は未完。',
        '一般の実切断についてアフィン関数の偏微分係数、偏微分値の一意性と逆数の体の法則を機械的に証明したものではない。有理数の係数補題を別に検査する。',
        '未知を残存候補の複数性へ接続する部分モデル。唯一の解があるが認識していない場合や、後続の証明で候補が消える過程は未接続。',
        '係数がこの段階で自由ということは、その全候補が後続の物理条件を満たすという主張ではない。φ=1や最終的な速度係数を補わない。',
        '固有文字の可読性、全文の意味一致の確認、一般的な記述の短さは別の未完課題として残る。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/affine-time-form-basis-v1.json'),(source_composed,'data/einstein-affine-time-form-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored affine time form differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Affine time form, coincident clock zeros and unfixed scale composed')


if __name__=='__main__':main()
