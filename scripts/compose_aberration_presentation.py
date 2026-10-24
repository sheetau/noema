"""Name the literal line angle and attribute the printed aberration equation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_aberration_line import ROOT,read,SETTING,VARIABLES,GEOMETRY,components
from scripts.compose_wave_display import PHASE,COORDS,NORMAL
from scripts.compose_wave_transform_application import transformed
from scripts.compose_field_equations import POINT,TAU,REGION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-aberration-line.noema';PARENT_BASIS='data/aberration-line-basis-v1.json'
FULL='examples/v014/einstein-aberration-presentation.noema';CORE='examples/v014/aberration-presentation-core.noema'
BASIS='data/aberration-presentation-basis-v1.json';ANNOTATIONS='data/aberration-presentation-identifiers-v1.json';INDICES=[375,376]
FORWARD=[(n,R) for n in ('light','ax','ay','az')]+COORDS+[('elapsed',R)]
RAY=PHASE+[('phase',TAU)]+COORDS+[('elapsed',R)]
OPTICS=PHASE+[('phase',TAU),('region',REGION)]
RAY_VARS=COORDS+[('elapsed',R)];NORMAL_VARS=NORMAL[len(PHASE)+1:]
NAME_WITNESSES=[(n,t) for n,t in SETTING if n not in ('wave','newangle','frame','light','scope','context')]
assert len(NAME_WITNESSES)==59
PRIMITIVES={
 'eissv':([], 'u0193のφ′という角の命名、波面法線と光線方向の説明、a′の式の書換えを述べる箇所。'),
 'eissw':([], 'u0194=M0340のcosφ′の光行差の式を表示する箇所。'),
 'eissx':([], 'u0193で結線との同じ実数角を指すφ′という表記個体。その役割はekgzの閉じた対象・値・状況の規則へ結び、文字の形を角の意味の代わりにしない。'),
 'eissy':([], 'u0186=M0327の四つのパラメータ式のうち、a′=(a−v/V)/(1−av/V)を与える第二式への参照。a′は同じ変換後波面法線の縦方向余弦であり、今回の結線との角を最初からa′に等置しない。'),
}
MEANINGS={
 'ekgt':'指定した有限の始点から、elapsedの間に同じV*nだけ進んだ終点の四座標。空間はp+V*n*elapsed、時刻はt+elapsed。波の位相率rateを伝播速度へ代入しない。',
 'ekgu':'正のV・位相率と単位方向、有限始点、正のelapsedについて、同じphaseが始点とekgtの終点で等しいという前方位相伝播の一点条件。光線方向はこの局所的な幾何光学的方向と読み、光子の軌跡や実測したエネルギー流を追加しない。',
 'ekgv':'同じphase・regionについて、有効な始点と正elapsedの全割当のうち両端点がその同じregionに入るものにekguを要求する。成功した一本だけで方向を定めず、領域外での実際の場の一致を要求しない。',
 'ekgw':'同じphase・region内の同時刻の全位置対について既存ekbkの等位相面と単位法線の直交条件を要求する。新系の波面法線を旧系の別の位相の法線へ取り違えない。',
 'ekgx':'正のVと位相率・単位方向について、同じ局所phase/regionの波面法線ekgwと前方位相伝播ekgvを同時に述べる。同じnが括弧内の光線方向にもなるという合成内容。',
 'ekgy':'先行ekgnの同じ65役割を保ち、同じ速度の逆Lorentz写像で引き戻した新phase、同じ新領域eken、同じsdn2による位相率、同じekgdの方向にekgxを結ぶ。角の基準線を速度方向へ替えない。',
 'ekgz':'対象objectを同じwave、候補valueを同じnewangleとし、K・V・節・状況を保って残る59役割にekgyの証人を取るφ′の表記役割。名前の規則へ印刷された帰結ekgoを含めず、条件と角で別の証人を選ばない。',
 'ekha':'同じ変換後法線ekgdの縦成分a′が、同じ旧角の余弦anglecosを使うsdo2の商に一致するという先行a′式の内容。結線との角newanglecosと別の量として保つ。',
 'ekhb':'同じ61役割への全称条件ekgyの下でekhaを述べる、先行a′式の参照内容。ekhcの印刷帰結と仮定・対象の割当をそろえる。',
 'ekhc':'同じ61役割への全称条件ekgyの下でekgoのcosφ′の印刷式を述べる。前段の同時刻結線の明示読解を継承し、この内容の真理を著者への帰属時に要求しない。',
 'ekhd':'同じ61役割についてekgnなら同じ新phase・region・位相率・法線がekgxを満たすと述べる、括弧内の光線方向との同定の内容。物理的な支持範囲と近似条件を先行設定から保つ。',
 'ekhe':'φ′の表記eissxを同じ波・角度・状況のekgzへ結ぶ定義的な命名規約。Nennt manはこの角をそう呼ぶという記号導入であり、命名者の人数や実測行為を補わない。',
 'ekhf':'同じ命名ekheと括弧内の同定ekhdへの著者の主張・挿入を保ち、先行a′項目eissyのekhbを同じ設定のekhcとして明示するという提示、コロンと表示への説明・順序を接続する。',
 'ekhg':'u0193全文の命名・同定・書換え提示ekhfを述べるメッセージ。',
 'ekhh':'u0193全文を同じ著者・論説へ帰属し、直前の無限大の記述に続ける。',
 'ekhi':'u0194の表示箇所を、同じ設定と命名を継承する条件内容ekhcへ結ぶ。別の系や無条件の数値式へ切り離さない。',
 'ekhj':'u0194の表示対応ekhiを述べるメッセージ。',
 'ekhk':'u0194の表示を同じ著者・論説へ帰属し、u0193のコロンに続く箇所として保持する。',
 'ekhl':'同じ65設定役割から、新系の位相率・波面法線・引戻し位相・局所領域を構成してekgxへ渡す共通条件。旧角と新角の値をこの光学的条件だけで同定せず、全称内容と同じ設定の結合で共有する。',
}
LIMITS=[
 'u0193–u0194と原刊912頁を固定し、M0338はφ′、M0339はa′、M0340はcosφ′=(cosφ−v/V)/(1−(v/V)cosφ)として保持する。原刊にない速度方向への訂正をしない。',
 '結線は同じ移動系の同時刻の源から観測者への向きとする前段の読解を継承する。源は同じK静止モデルからLorentz変換し、同じ新時刻にそろえる。結線の極限方向は(a/γ,b,c)の正規化であり、変換後の波面法線や+x軸とは別に構成する。',
 'Wellennormaleは同時刻の等位相面の単位法線、Strahlrichtungは同じ局所波の位相をV*nで前方へ運ぶ幾何光学的な方向として読む。光子の個体軌跡、実測済みのエネルギー流、領域外の実際の場の厳密な平面性を追加しない。同じ引戻し位相と新領域の全対象点を保持する。',
 'Nennt manは同じ波の結線との実数角をφ′と呼ぶ定義的な記号導入として読む。eisloの既存規約に、候補角と同じ物理設定の役割を合成する。cosφ′の値を角そのものと同一視せず、59証人を条件と角の両方へ共有する。',
 'a′の式は先行M0327の第二式であり、同じ変換後法線の縦成分を指す。原文はこれをcosφ′の表示へ明示すると述べる。その帰属はeissbで保持し、数式の同値性を自動認定しない。採用した結線読解ではV5,v3,n=(0,1,0)で実際の角の余弦4/5と表示式−3/5が一致しないことを前段の証拠に残す。',
 '括弧内の同一方向の説明を同じ命名への挿入として保持し、so ... die Form anとコロンを同じ先行式からの明示・後続表示への説明と読む。歴史的な誤植の一意な確定、本文にない実験・証明成功、独立の法則の追加はしない。',
 '新しい一般基本関係は加えず、局所位相・直交・全称条件・存在量化・命名・挿入・書換え提示・著者帰属を既存規約から合成する。原語の表記だけで意味を代用しない。',
 '全実数・全関数域を有限標本へ縮めない。局所の正確な有理数切断、全位置の結合診断、引用と提示の対照検査は、物理法則の真理や意味同義性の自動証明ではない。',
]

def allq(fields,body,marker='f'):
    for n,t in reversed(fields):body=q(marker,n,t,body)
    return body

def optics_args():
    V=v('light');speed=v('speed');normal=components(k('ekgd',*args(GEOMETRY)))
    phase=transformed(speed)[-1];region=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    return [V,k('sdn2',V,speed,v('rate'),v('ax')),*normal,phase,region]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    zero=k('bb','n p a b');V=v('light');time=v('time');elapsed=v('elapsed');n=[v(x) for x in ('ax','ay','az')];xyz=[v(x) for x in ('x','y','z')]
    moved=[k('bd',x,k('shv',k('shv',V,a),elapsed)) for x,a in zip(xyz,n)];future=k('bd',time,elapsed);space=k('ekbe',*moved)
    text+=define('ekgt',FORWARD,'i[axis a]['+k('szi',op('e',v('axis'),k('zc7')),future,app(space,v('axis')))+']',POINT)
    end=k('ekgt',*args(FORWARD));endpoint=[app(end,k(a)) for a in ('yn','yo','yp','zc7')]
    text+=define('ekgu',RAY,both(k('sdl2',V,zero,v('rate'),*n),*(k('ba',v(x)) for x,t in RAY_VARS),k('bg',zero,elapsed),k('sca',app(v('phase'),*args(COORDS)),app(v('phase'),*endpoint))))
    inside=both(*(k('ba',v(x)) for x,t in RAY_VARS),k('bg',zero,elapsed),app(v('region'),*args(COORDS)),app(v('region'),*endpoint))
    text+=define('ekgv',OPTICS,allq(RAY_VARS,op('y',inside,k('ekgu',*args(RAY)))))
    first=xyz;second=[v(x) for x in ('otherx','othery','otherz')]
    pair=both(*(k('ba',v(x)) for x,t in NORMAL_VARS),app(v('region'),*first,time),app(v('region'),*second,time))
    text+=define('ekgw',OPTICS,allq(NORMAL_VARS,op('y',pair,k('ekbk',*args(NORMAL)))))
    text+=define('ekgx',OPTICS,both(k('sdl2',V,zero,v('rate'),*n),k('ekgv',*args(OPTICS)),k('ekgw',*args(OPTICS))))
    text+=define('ekhl',SETTING,k('ekgx',*optics_args()))
    text+=define('ekgy',SETTING,both(k('ekgn',*args(SETTING)),k('ekhl',*args(SETTING))))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('context'),'wave':v('object'),'newangle':v('value')}
    text+=define('ekgz',[('object','a'),('value',R),('context','d')],allq(NAME_WITNESSES,k('ekgy',*[fixed.get(n,v(n)) for n,t in SETTING]),'g'))
    text+=define('ekha',SETTING,k('sca',app(k('ekgd',*args(GEOMETRY)),k('yn')),k('sdo2',V,v('speed'),v('anglecos'))))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in SETTING]
    for name,premise,conclusion in [('ekhb',k('ekgy',*actual),k('ekha',*actual)),('ekhc',k('ekgy',*actual),k('ekgo',*actual))]:
        text+=content(name,allq(VARIABLES,op('y',premise,conclusion)))
    text+=content('ekhd',allq(VARIABLES,op('y',k('ekgn',*actual),k('ekhl',*actual))))
    p=v('point');node=k('eissv');display=k('eissw');prior=k('eissy');author=k('rd');scope=k('eisrx')
    text+=content('ekhe',k('eislo',k('eissx'),'r[p ekgz]',k('eirf'),p))
    text+=content('ekhf',both(evaluate('ekhe'),k('uh',node,author,quote('ekhd'),scope,p),k('eisa5',node,author,quote('ekhe'),quote('ekhd'),p),k('eisox',prior,quote('ekhb'),p),k('eissb',node,prior,author,quote('ekhb'),quote('ekhc'),scope,p),k('ue',k('eissj'),node,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ekhi',k('eisox',display,quote('ekhc'),p))
    for shown,msg,stmt,item,previous in [('ekhf','ekhg','ekhh','eissv','eisst'),('ekhi','ekhj','ekhk','eissw','eissv')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(item),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==375
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekhh','ekhk')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='literal_line_angle_naming_ray_direction_and_aberration_display',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/aberration-line-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eissx',role='designation',forms=[dict(text='φ′',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
