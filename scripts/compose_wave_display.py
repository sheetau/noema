"""Expand seven displayed equations, amplitude vectors and wavefront normals."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_distant_wave_source import ROOT,read,SETTING,WITNESSES,SPACE,REGION,FIELD,POINT,PROFILE,AMPLITUDES
from scripts.compose_field_equations import TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-distant-wave-source.noema';PARENT_BASIS='data/distant-wave-source-basis-v1.json'
FULL='examples/v014/einstein-wave-display.noema';CORE='examples/v014/wave-display-core.noema'
BASIS='data/wave-display-basis-v1.json';ANNOTATIONS='data/wave-display-identifiers-v1.json';INDICES=[364,365]
PHASE=[(n,R) for n in ('light','rate','ax','ay','az')]
COORDS=[(n,R) for n in ('x','y','z','time')]
DISPLAY=[('sine',PROFILE)]+PHASE+[(n,R) for n in AMPLITUDES]+[('electricrepresentative',FIELD),('magneticrepresentative',FIELD),('phase',TAU)]
VECTORS=[(n,R) for n in AMPLITUDES]+[('electricvector',POINT),('magneticvector',POINT),('electricamplitude',R),('magneticamplitude',R)]
NORMAL=PHASE+[('phase',TAU)]+[(n,R) for n in ('x','y','z','otherx','othery','otherz','time')]
PRIMITIVES={
 'eissb':([('node','a'),('anchor','a'),('author','a'),('prior','i[e]'),('expanded','i[e]'),('scope','a'),('context','d')],'authorが同じscopeのanchorで導入したpriorを、nodeでexpandedとして明示又は説明する。同じ仮定設定の対象・系・単位・量の割当と適用範囲を保持し、数式の表示又はそこで用いる量の説明をその内部に位置付ける。別の設定で偶然成立する内容や、独立した現実の実験報告へ切り離さない。説明による新しい真理・導出の健全性・引用の自動実行はこの関係だけから認定しない。'),
 'eissc':([], '固定原文einstein-1905:u0181で、直前の六成分の係数を二つの振幅ベクトルとして、三方向値を波面法線の方向余弦として説明する箇所。語の内容は同じ係数と位相の合成へ接続する。'),
}
MEANINGS={
 'ekbe':'指定した三成分を同じ三空間軸へ割り当てるベクトル表現。非空間役割の拡張値は零であり、時空点としての時刻成分を持つとは解釈しない。',
 'ekbf':'Φ=ω(t−(ax+by+cz)/V)という同じ位相を四座標の関数として作る。空間の三項全体をVで割り、ωを括弧全体へ掛ける既存sds2を使う。',
 'ekbg':'同じ有効な四座標で、指定phaseの値と位相式を等置し、その同じphase値の正弦を六つの各係数へ掛けた値と、電気側・磁気側の各三成分をそれぞれ等置する七式。各成分の位置と同じ位相を保持する。',
 'ekbh':'指定領域内の全有効四座標についてekbgの七式を要求する。これだけで領域の非空性や物理的な実在を断言せず、設定側の条件を共有する。',
 'ekbi':'先行の同じ遠方源と近似設定ekazを保持し、その正弦・位相・六振幅から構成した二つの近似表現場と位相関数について、同じ全領域で七式ekbhを述べる。実際の二場を無条件に厳密な正弦波へ置換しない。',
 'ekbj':'六つの同じ係数を二つの三成分ベクトルへ結び、それぞれの非負の大きさを三成分の二乗和の平方根に対応させる。各成分の符号と相対方向を失わず、振幅を一成分だけで代用しない。',
 'ekbk':'正のVとω及び単位三方向の下で、同時刻の二位置が同じ指定phase値を持つことと、その位置差が方向ベクトルに直交することを同値として述べる。Cartesian基底の単位方向の三成分を法線の方向余弦として読む局所条件。',
 'ekbl':'同じekbiの設定・近似場・位相・六係数について、二振幅ベクトルとその大きさekbjを述べ、同じ時間と領域にある全位置対に法線条件ekbkを要求する。異なる波・時刻・近似場の断片を混ぜない。',
 'ekbm':'K・V・第七節を固定し、先行と同じ31役割の証人を共有する七表示式を含む仮定内容。',
 'ekbn':'ekbmと同じ設定を、二振幅ベクトルと波面法線の方向余弦まで明示する内容。局所的な近似と物理場の規約を保持する。',
 'ekbo':'u0180の七表示式を先行u0179の同じ仮定内容の明示として著者へ帰属する。表示の等号を実際の二場の近似誤差零という追加主張へ変えない。',
 'ekbp':'七表示式の提示ekboを述べるメッセージ。',
 'ekbq':'七表示式を同じ著者・論説に接続し、源の仮定に続く別の表示箇所とする。',
 'ekbr':'Hierbeiの説明を直前の七表示式と同じ係数・位相の解釈として著者へ帰属する。新しい波を導入しない。',
 'ekbs':'振幅と法線の説明ekbrを述べるメッセージ。',
 'ekbt':'u0181の説明を同じ著者・論説に接続し、七表示式に続く別の箇所として保持する。',
}
LIMITS=[
 'u0180のM0320は六成分と位相の七等式を一つの表示として読む。X,Y,ZとL,M,Nはu0179で十分な近似として使う表現場の成分であり、実際の物理場との誤差は先行のseat/eisrwに残す。表示の等号から誤差が零とはしない。',
 'Φは同じ四座標の共通位相、ωはその時間に対する正の角周波数パラメータである。V=tc、K=raと同じ尺度を保ち、ωを通常の一秒あたり周期数νと数値同一視しない。関数値としての位相をその綴りの個体へ置き換えない。',
 '六係数は三つずつ同じ校正されたCartesian空間基底のベクトル成分であり、正規化した同じ正弦に掛かる振幅係数として読む。符号・偏光方向を保ち、各ベクトルの大きさは非負の二乗和平方根で定まる。測定済みの記録や新しい物理定数を追加しない。',
 '波面は同時刻の等位相面と読む。同じ位相の二位置差がn=(a,b,c)と直交し、nの長さが1であることを法線と方向余弦の構成に使う。別時刻の等位相点を同一の空間波面へ混ぜない。正のω,Vと位相の符号が伝播側の向きを固定し、波面に垂直な向きを無条件に逆転させない。',
 '法線は近似表現の平面波面について述べる。誤差を持つ実際の場の全波面が厳密な平面であること、全空間・全時間に同じ近似が成り立つこと、横波の振幅関係や場の全方程式を追加しない。',
 'Hierbeiは直前の同じ係数と位相を説明する役割とする。七式と振幅・法線の説明は先行仮定の内部の明示であり、別の現実の放射実験が成立したという追加の存在主張にしない。',
 '有限検査では同じ四座標の七式、六係数と二ベクトル、同時刻の位置差と位相差を正確な切断算術で対照する。診断用の波形を正弦と称さず、実数全域の正弦・領域・全設定量化を有限標本へ交換しない。',
 'u0178の第七節主題、u0182の移動系観測者による問いと変換の適用、以降の変換後の表示・物理的周波数の説明は別途必要である。',
]

def representatives():
    base=[v(n) for n in ('sine','light','rate','ax','ay','az')]
    return dict(electricrepresentative=k('sdx2',*base,*[v(n) for n in AMPLITUDES[:3]]),magneticrepresentative=k('sdx2',*base,*[v(n) for n in AMPLITUDES[3:]]),phase=k('ekbf',*args(PHASE)))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');axes=('yn','yo','yp')
    component=zero
    for axis,n in reversed(list(zip(axes,('x','y','z')))):component=k('szi',op('e',v('axis'),k(axis)),v(n),component)
    text+=define('ekbe',[(n,R) for n in ('x','y','z')],'i[axis a]['+component+']',POINT)
    coords=args(COORDS);phase=k('sds2',*args(PHASE),v('time'),v('x'),v('y'),v('z'))
    text+=define('ekbf',PHASE,'i['+' '.join(n+' '+t for n,t in COORDS)+']['+phase+']',TAU)
    phi=app(v('phase'),*coords);rhs=app(v('sine'),phi)
    values=[app(app(v(field),k(axis)),*coords) for field in ('electricrepresentative','magneticrepresentative') for axis in axes]
    equations=[k('sca',phi,phase)]+[k('sca',left,k('shv',v(amp),rhs)) for left,amp in zip(values,AMPLITUDES)]
    text+=define('ekbg',DISPLAY+COORDS,both(*(k('ba',x) for x in coords+[phi]+values),*equations))
    inside=both(*(k('ba',x) for x in coords),app(v('region'),*coords));allpoints=op('y',inside,k('ekbg',*args(DISPLAY),*coords))
    for n,t in reversed(COORDS):allpoints=q('f',n,t,allpoints)
    text+=define('ekbh',DISPLAY+[('region',REGION)],allpoints)
    reps=representatives();get=lambda n:reps.get(n,v(n));region=k('ekau',v('space'),v('lower'),v('upper'))
    text+=define('ekbi',SETTING,both(k('ekaz',*args(SETTING)),k('ekbh',*[get(n) for n,t in DISPLAY],region)))
    vectorvalues=[app(v(vec),k(axis)) for vec in ('electricvector','magneticvector') for axis in axes]
    text+=define('ekbj',VECTORS,both(*(k('ba',v(n)) for n in AMPLITUDES),*(k('sca',value,v(n)) for value,n in zip(vectorvalues,AMPLITUDES)),k('seal',*[v(n) for n in AMPLITUDES[:3]],v('electricamplitude')),k('seal',*[v(n) for n in AMPLITUDES[3:]],v('magneticamplitude'))))
    first=[v(n) for n in ('x','y','z')];second=[v(n) for n in ('otherx','othery','otherz')]
    delta=[k('bf',b,a) for a,b in zip(first,second)]
    dot=k('seah',v('ax'),v('ay'),v('az'),*delta)
    equalphase=k('sca',app(v('phase'),*first,v('time')),app(v('phase'),*second,v('time')))
    text+=define('ekbk',NORMAL,both(*(k('ba',v(n)) for n,t in NORMAL if n!='phase'),k('bg',zero,v('light')),k('bg',zero,v('rate')),k('sca',k('seag',v('ax'),v('ay'),v('az')),one),op('z',equalphase,k('sca',dot,zero))))
    vectorargs=[v(n) for n in AMPLITUDES]+[k('ekbe',*[v(n) for n in ns]) for ns in (AMPLITUDES[:3],AMPLITUDES[3:])]+[k('sky',k('seag',*[v(n) for n in ns])) for ns in (AMPLITUDES[:3],AMPLITUDES[3:])]
    pair=both(*(k('ba',x) for x in first+second+[v('time')]),app(region,*first,v('time')),app(region,*second,v('time')))
    normal=op('y',pair,k('ekbk',*[get(n) for n,t in NORMAL]))
    for n,t in reversed(NORMAL[len(PHASE)+1:]):normal=q('f',n,t,normal)
    text+=define('ekbl',SETTING,both(k('ekbi',*args(SETTING)),k('ekbj',*vectorargs),normal))
    override={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')}
    for root,rule in (('ekbm','ekbi'),('ekbn','ekbl')):text+=content(root,bind(WITNESSES,k(rule,*[override.get(n,v(n)) for n,t in SETTING])))
    for shown,message,statement,node,anchor,prior,expanded in (('ekbo','ekbp','ekbq','eisrz','eisry','ekba','ekbm'),('ekbr','ekbs','ekbt','eissc','eisrz','ekbm','ekbn')):
        text+=content(shown,k('eissb',k(node),k(anchor),k('rd'),quote(prior),quote(expanded),k('eisrx'),v('point')))
        text+='d '+message+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(statement,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(anchor),k(node),k('ri')),op('u',op('e',k(anchor),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0]
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekbq','ekbt')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='seven_wave_equations_amplitude_vectors_and_normal_direction',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/distant-wave-source-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
