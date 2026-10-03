"""Expand the clock midpoint using rest-frame light travel and four-argument tau."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_moving_light_trip import ROOT, both
from scripts.compose_homogeneous_coordinates import CUT, OP, SAME, VALID
from scripts.compose_comoving_labels import TAU

MIDPOINT='h['+' '.join([CUT]*3)+'] c'


def definitions():
    return '''
d sja[numerator b denominator b result b] c[w[k aa[n p a b v denominator]][e[k ad[v denominator v result]][v numerator]]].
d sjb[label b light b speed b outward b returning b] c[
 w[u[k aa[v speed n p a b]]][w[k aa[v speed v light]][w[
 k sja[v label k ab[v light k ac[v speed]] v outward]
 ][k sja[v label k ab[v light v speed] v returning]]]]].
d sjc[space b time b offset b label b moment b] b[k ab[k ab[k ad[v space v label] k ad[v time v moment]] v offset]].
'''


MEANINGS={
    'sja':'分母が正で、分母と結果の積が分子に等しいという有理数の商の関係。分子の符号を制限しない。',
    'sjb':'0≤v<Vのもとで、二つの商x′/(V-v)とx′/(V+v)を有理数の乗算で指定する。正の経過時間と解釈するときはx′>0を別に要求する。',
    'sjc':'補助位置と静止系時刻に対するアフィン関数a*x′+b*t+c。有理数の検査用候補であり、τの一般形を仮定・導出したものではない。',
}


def generic_composed():
    basis=deepcopy(json.loads((ROOT/'data/axial-clock-trip-basis-v1.json').read_text(encoding='utf-8')))
    doc=parse((ROOT/'examples/v014/axial-clock-trip.noema').read_text(encoding='utf-8'))
    doc=parse(format_graph(doc,'compact')+definitions())
    basis.update(version='light-time-arguments-basis-v1',document='examples/v014/light-time-arguments.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['有理数の商の一意性と代数的な時刻条件を検査する。全実数上の除算・物理的光伝播・τの具体形の導出の証明ではない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-axial-clock-trip.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'''
d sjd[positive h[b] c] h[b] c[i[q b][x[k aa[v q n p a b]][
 g upper b[w[k aa[n p a b v upper]][w[u[c[v positive][v upper]]][k aa[k ad[v q v upper] n p b b]]]]]]].
d sje[numerator h[b] c denominator h[b] c] h[b] c[k shv[v numerator k sjd[v denominator]]].
'''
    zero='k bb[n p a b]'
    outward='c[v divide][v label c[v subtract][v light v speed]]'
    returning='c[v divide][v label c[v add][v light v speed]]'
    middle='c[v add][v time '+outward+']'
    last='c[v add]['+middle+' '+returning+']'
    readings=['c[v function]['+' '.join(args)+']' for args in (
        (zero,zero,zero,'v time'),('v label',zero,zero,middle),(zero,zero,zero,last))]
    args='function '+TAU+' label '+CUT+' light '+CUT+' speed '+CUT+' time '+CUT+' valid '+VALID+' before '+SAME+' add '+OP+' subtract '+OP+' divide '+OP+' midpoint '+MIDPOINT
    text+='d sjf['+args+'] c['+both(
        *('c[v valid][v '+n+']' for n in ('label','light','speed','time')),
        'u[c[v before][v speed '+zero+']]','c[v before][v speed v light]',
        *('c[v valid]['+term+']' for term in (outward,returning,middle,last,*readings)),
        'c[v midpoint]['+' '.join(readings)+']')+'].\n'
    text+='d sjg[function '+TAU+' label '+CUT+' light '+CUT+' speed '+CUT+' time '+CUT+'] c[k sjf[v function v label v light v speed v time p ba p bg p bd p bf p sje p sit]].\n'
    text+='''
r zdx[] a.r zdy[] a.r zdz[a a d] a.r zd2[] a.
r zd3[a a i[e] i[e] i[e] a d] c.
'''
    text+='r zd4[] '+TAU+'.\n'
    text+='''
d sjh[event a context d] h[b] c[k zc6[k zdz[v event k ra[] v context] k zc7[]]].
d sji[event a context d] h[b] c[k zc6[k zdz[v event k ra[] v context] k yn[]]].
'''
    trial='k zdq[]';ray='k qh['+trial+']';frame='k ra[]';ctx='v context'
    events=['k '+n+'['+trial+']' for n in ('qe','qf','qg')]
    times=['k sjh['+event+' '+ctx+']' for event in events]
    xs=['k sji['+event+' '+ctx+']' for event in events]
    clauses=['k sbc[k tc[] '+ctx+']','k bg['+zero+' k zdt[]]',
        'k ba[k tc[]]','k bg[k zb7[] k tc[]]']
    for event,label in zip(events,(zero,'k zdt[]',zero)):
        tup='k zdz['+event+' '+frame+' '+ctx+']'
        clauses+=['k shd['+event+' '+tup+' '+frame+' '+ctx+']',
            'k sca[k sin[k zb7[] k sji['+event+' '+ctx+'] k sjh['+event+' '+ctx+']] '+label+']']
        for role in ('yo','yp'):clauses+=['k sca[k zc6['+tup+' k '+role+'[]] '+zero+']']
    axis='k zbo['+frame+' k yn[] '+ctx+']'
    clauses+=['k zbw['+frame+' '+axis+' k yn[] '+ctx+']']
    for segment,first,last,path in (
        ('k zdx[]',events[0],events[1],'k bf['+xs[1]+' '+xs[0]+']'),
        ('k zdy[]',events[1],events[2],'k bf['+xs[1]+' '+xs[2]+']')):
        clauses+=['k wa['+segment+' '+frame+' k rb[] k ta[] '+ctx+']',
            'e[k wf['+segment+']]['+ray+']','e[k wi['+segment+']]['+first+']','e[k wj['+segment+']]['+last+']',
            'k zdw['+ray+' '+first+' '+last+' '+axis+' '+frame+' '+ctx+']',
            'k sba['+segment+' k tc[] '+ctx+' p qo p sax]',
            'k sca[k wo['+segment+'] k sjh['+first+' '+ctx+']]',
            'k sca[k wp['+segment+'] k sjh['+last+' '+ctx+']]',
            'k sca[k wq['+segment+'] '+path+']']
    text+='d sjj[context d] c['+both(*clauses)+'].\n'
    clauses=[]
    for label,time,reading in zip((zero,'k zdt[]',zero),times,('qi','qj','qk')):
        value='c[v function]['+' '.join((label,zero,zero,time))+']'
        clauses+=['k ba['+value+']','k sca['+value+' k '+reading+'['+trial+']]']
    text+='d sjk[function '+TAU+' context d] c['+both(*clauses)+'].\n'
    text+='d sjl[context d] c['+both('k six[v context]','k sjj[v context]','k sio[k zd4[]]','k sjk[k zd4[] v context]')+'].\n'
    text+='''
d sjm[] e[b context[k sjl[k zb6[]]]].
d sjn[] e[b context[k sjg[k zd4[] k zdt[] k tc[] k zb7[] k sjh[k qe[k zdq[]] k zb6[]]]]].
'''
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zd3[k zd2[] k rd[] r[k sjm[]] r[k siz[]] r[k sjn[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-axial-clock-trip-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-light-time-arguments-basis-v1',document='examples/v014/einstein-light-time-arguments.noema')
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zdx',[],'§3の同じ光の原点から反射点までの片道区間。'),
        ('zdy',[],'§3の同じ光の反射点から原点までの片道区間。'),
        ('zdz',['event','frame','context'],'同じ出来事・系・文脈に対する四座標記録の候補。取得だけでは有効性・存在・一意性を含意せず、shdで測定と接続する。'),
        ('zd2',[],'τの引数を明示し、静止系での光速度一定を適用して中点式を書き換える箇所。'),
        ('zd3',['node','author','premise','before','after','scope','context'],'著者が指定の前提のもと、前の内容を後の内容へ同値な形として書き換えて提示する。帰属関係であり、前提・内容の真理や同値性の検証済みを意味しない。'),
        ('zd4',[],'τを求める下位課題で扱う四引数の候補関数。sioで既存の座標対応との一致を条件にし、具体形・係数・解の発見は補わない。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        'sjd':'正の実切断の逆数。既存real-productsのcfと同じ構成を記号衝突なく再利用する。正の有効な入力だけで逆数と解釈する。',
        'sje':'正の分母の逆数と分子の符号付き積。呼出側で分母の正値性と入力・結果の有効性を検査する。',
        'sjf':'四引数関数の値を、出発(0,0,0,t)、反射(x′,0,0,t+x′/(V-v))、帰着(0,0,0,t+x′/(V-v)+x′/(V+v))で求めて中点条件に渡す。演算と妥当性を引数で与える。',
        'sjg':'sjfを実切断の演算・正分母の除算・半和の中点式に接続する。0≤v<Vを要求し、分子の正値性は物理的試行の接続条件で課す。',
        'sjh':'同じ出来事の静止系の四座標記録からt成分を得る。記録の有効性はsjjで確認する。',
        'sji':'同じ出来事の静止系の四座標記録からx成分を得る。',
        'sjj':'光速度一定の同じ対象範囲へ往復の両区間を含め、同じ光・始終出来事・静止系の軸・局所時刻・光路長を接続する。三出来事の補助量0・x′・0、y=z=0を保持し、直線光路長を符号を保った端点差へ結ぶ。ここはx′>0の向きを扱う。',
        'sjk':'候補τの、同じ三出来事に対応する補助位置と静止系時刻での値を、運動系の三つの時計の読みに結ぶ。',
        'sjl':'先行する運動系の光往復、静止系の光速度一定の適用、座標対応に合う候補関数と時計の読みとの照合を、同じ設定で要求する。',
        'sjm':'引数の展開と光速度一定を適用するための同じ設定の内容。',
        'sjn':'選択したτ候補について、二つの片道時間を引数へ挿入した中点式という内容。原文の分割された左右を一つの等式として記述する。'})
    basis['unresolved']+=[
        'u0051〜u0053の部分記述。M0100は左辺、M0101は等号と右辺であり、sjnで一つの式に接続する。原刊照合と全文の意味確認は未完。',
        '静止系の光路と数値の接続は、真空・同じ光・直線軸上・同じ同期時刻を先行するsbaへ結ぶ。有限標本から全光線の法則を認定しない。',
        '正方向の非退化な光往復ではx′>0と0≤v<Vを使う。前段の負のx′を許す抽象試行へ同じ向きの因果的時間式を無条件に適用しない。',
        '正の実切断の逆数・商の一般法則、現実の全光路の幾何、τの具体形の導出と存在・唯一性の証明は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,filename in ((generic_composed,'data/light-time-arguments-basis-v1.json'),(source_composed,'data/einstein-light-time-arguments-basis-v1.json')):
        text,basis=compose()
        for name,body in ((basis['document'],text),(filename,json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored light-time arguments differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Light travel times and complete tau arguments composed')


if __name__=='__main__':main()
