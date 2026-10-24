"""Define moving-frame fields by signed test responses and apply one law."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_field_equations import FIELD,REGION,POINT,ROLES
from scripts.compose_material_relative_frame import define
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-field-transformation-application.noema'
PARENT_BASIS='data/field-transformation-application-basis-v1.json'
FULL='examples/v014/einstein-moving-field-definition.noema'
CORE='examples/v014/moving-field-definition-core.noema'
BASIS='data/moving-field-definition-basis-v1.json'
ANNOTATIONS='data/moving-field-definition-identifiers-v1.json';INDEX=154
RESPONSE='h['+POINT+' '+R+'] '+POINT
PHYSICAL=[('kind','a'),('frame','a'),('lengthunit','a'),('timeunit','a'),('amountunit','a'),('forceunit','a'),('region',REGION),('context','d'),('response',RESPONSE)]
CALIBRATION=[('kind','a'),('amountunit','a'),('fieldunit','a'),('forceunit','a'),('conversion',R),('context','d')]
FIELD_ARGS=PHYSICAL+[('fieldunit','a'),('conversion',R),('field',FIELD)]
UNITS=('chargeunit','poleunit','electricunit','magneticunit','forceunit')
FACTORS=('electricconversion','magneticconversion');RESPONSES=('electricresponse','magneticresponse')
WITNESSES=[(n,'a') for n in UNITS]+[(n,R) for n in FACTORS]+[(n,RESPONSE) for n in RESPONSES]
PRIMITIVES={
 'eisps':([], '磁気的な極性と局所作用の強さを表す加法的な符号付き磁極強度の量種。正極を選ぶ規約と反対極の負符号を持つ。試験磁極への局所的な力を比較して尺度を与える理想化であり、慣性質量、電荷、磁石全体への合力とは別である。孤立した磁荷の実在を要求せず、磁石の一方の極を理想化して扱うことを許す。'),
 'eispt':(PHYSICAL, '指定frameの同じ長さ・時間尺度とcontextで、regionの地点時刻に、kindの符号付き量をamountunitで表す試験系を瞬間的に静止させた際の局所的な機械力の理想応答がresponseである。応答の引数は同じ四座標と符号付き量、結果はforceunitと同じ三軸による力の三成分。試験量と大きさを零へ近づけて元の配置への影響を除く一次応答を、任意の符号付き量で規格化して表示する規約であり、大きな有限試験体の厳密な線形応答ではない。力は運動量変化への寄与又はそれを釣り合わせる機械的作用として同定し、支持力・重力や他の種類の寄与との合力を代入しない。磁極の場合は一方の極の局所寄与で、全磁石への合力ではない。物理的な帰属と極限規約を基本入力とし、任意の数値関数だけから認定しない。実測、試験体又は孤立磁荷の実在を含意しない。'),
 'eispu':(CALIBRATION, '同じcontextにおいてkindの符号付き量のamountunitと場のfieldunitの積を、機械力のforceunitへ直す正の係数がconversionであるという校正規約。量種の極性と単位の正の尺度を固定し、電気量と磁極強度、場と機械力を区別する。場の数値や力との比例関係自体は別に合成し、名前の一致や特定のSI換算係数では代用しない。'),
 'eispv':([], 'u0161の(X′,Y′,Z′)という移動系の電気側三成分の順序付き表記。現在の場znrへ規則で結ぶ。'),
 'eispw':([], 'u0161の(L′,M′,N′)という移動系の磁気側三成分の順序付き表記。現在の場znsへ規則で結ぶ。'),
 'eispx':([], 'u0162のM0300にある移動系の六方程式の表示箇所。原理による条件付き要求を具体化する。'),
 'eispy':([], 'u0161のd. h.以下で、移動系の二場の定義と表示式によって先の要求を言い換えて説明する箇所。'),
}
MEANINGS={
 'ejtq':'同じ四座標で場を評価した三成分へ、同じ有効な符号付き試験量と正の換算係数を掛け、同じ地点時刻・試験量に対する応答関数の三力成分へ結ぶ。三軸の相違と全成分の実数有効性をeibrで保持する。',
 'ejtr':'非空の指定領域の全有効四座標と全有効な符号付き試験量にejtqを要求する。有限標本、零試験量だけ、正極だけ、場の大きさだけの一致へ縮めない。',
 'ejts':'同じ系・座標単位・領域・量種の物理的な試験応答eispt、単位積の校正eispu、場の単位eirn、座標規約ejslを、同じ場と応答の全点・全試験量の比例ejtrへ結ぶ。',
 'ejtt':'現在の移動系k=zbm、ta/rb、領域znt、二場znr/znsについて、電荷zorと磁極強度eispsを区別した二つのejtsを構成し、同じ電磁過程eisppの記述へ結ぶ。同じ力単位を共有し、試験量・場単位・係数・応答は種類ごとに保持する。',
 'ejtu':'現在の移動系の二場について、同じ五単位・二係数・二理想応答を持つejttの証人が存在する。有限の実測記録や領域内の試験体の存在は要求しない。',
 'ejtv':'同じ移動系の物理的な二場ejtu、同じ領域の真空ejsm、同じ二場・領域・Vの六方程式s5yを接続する。',
 'ejtw':'移動系の物理的に定義された二場が真空の六式を満たすejtvの内容。前文の計算上の混合関数との同一性は含めない。',
 'ejtx':'指定した場が同じ物理的な規約ejtuの下で、領域znt全体において現在の電気側znrと三成分で一致するという表記解釈規則。',
 'ejty':'指定した場が同じ物理的な規約ejtuの下で、領域znt全体において現在の磁気側znsと三成分で一致するという表記解釈規則。',
 'ejtz':'移動系の二つのプライム付き三成分表記をejtx/ejtyの閉じた規則へ結ぶ説明内容。',
 'ejt2':'指定した一つの理論について、適格な等速並進系対が非空であり、全適格対でeiomが成立する。第一原理eionの理論証人を外へ明示した同じ本体である。',
 'ejt3':'同じ理論の法則znuと候補履歴znv、同じK/kの全範囲による適格性、両記述znw/znxを結び、法則適合をそれぞれ現在の仮定ejs6と移動系の内容ejtwの真偽へ結ぶ適用条件。二つの数値場を等置しない。',
 'ejt4':'第一原理の同じ一つの理論をejt2とejt3の両方へ共有する適用前提内容。原理の一般範囲を成功した一履歴だけへ縮めない。',
 'ejt5':'同じ文脈で静止系の仮定内容ejs6が成立するなら移動系の内容ejtwが成立する条件文。前件が偽のとき後件を真と断言しない。',
 'ejt6':'著者が相対性原理を適用してejt5を要求すると述べる提示。d. h.の説明、二場の表記規則、同じ条件下に読む六式の表示を同じ文の順序で結ぶ。',
 'ejt7':'u0161–u0162の原理による要求、場の定義、六式の説明ejt6を述べるメッセージ。',
 'ejua':'同じ著者・論説への帰属と、前文のβ補足の後という順序を保持する。旧文154だけを置き換える。',
}
LIMITS=[
 'u0161–u0162を原刊908頁で一文として読む。相対性原理が要求する条件文、d. h.の言い換え、同じ移動系の場の物理的定義、六式を保持する。',
 '電気的質量は符号付き電荷、磁気的質量は符号付き磁極強度を担う試験系と読む。磁極は歴史的な局所的理想化で、孤立磁荷の発見や慣性質量、磁石全体の合力を主張しない。',
 '場は同じ系に静止した試験系への局所的な機械力の一次応答により同定する。試験系を小さくして元の場への影響を除く規約を明示し、実際の試験体によって真空を占有したとはしない。極限手順を実験した証明ではなく、基本量の物理的同定規約である。',
 '同じ地点時刻、量種・単位、正負の試験量と三成分を合成する。二つの新しい一般関係は物理的な理想応答の帰属と単位積の校正であり、文全体を一基本記号へ隠さない。',
 '第一原理の現在の定式化eionと同じ本体で、一つの理論の全適格系対・全法則・全候補記述と個別適用を共有する。適用条件は明示した読みであり、原文が条件を別々に列挙したとはしない。',
 '移動系の新しい二場znr/znsと領域zntを維持し、前文のs6k/s6lとの等値、共通係数、同じ六式だけから成分が比例するという後続主張は先取りしない。',
 '表示六式は原理の条件付き要求の具体化として読む。著者の導出提示と内容の真偽・推論の自動証明を区別し、全実数・全関数域の有限列挙拒否を保つ。',
 '旧文154以外の357主張と旧意味規約・証拠を保持する。旧znr/znsの意味規約に残る未完という履歴説明は上書きせず、現在の物理的定義はejtu以下で接続する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    p=v('point');amount=v('amount');coords=[app(p,k(n)) for n in ROLES]
    sample='i[axis a]['+app(app(v('field'),v('axis')),*coords)+']'
    numeric=[('field',FIELD),('response',RESPONSE),('conversion',R),('point',POINT),('amount',R)]
    text+=define('ejtq',numeric,both(*(k('ba',x) for x in coords),k('eibr',amount,sample,v('conversion'),app(v('response'),p,amount))))
    inside=k('ejsj',p,v('region'))
    text+=define('ejtr',numeric[:3]+[('region',REGION)],both(q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,q('f','amount',R,op('y',k('ba',amount),k('ejtq',*[v(n) for n,_ in numeric])))))))
    text+=define('ejts',FIELD_ARGS,both(k('ejsl',*[v(n) for n in ('frame','lengthunit','timeunit','context')]),k('eispt',*[v(n) for n,_ in PHYSICAL]),k('eispu',*[v(n) for n,_ in CALIBRATION]),k('eirn',v('frame'),v('field'),v('fieldunit'),v('context')),k('ejtr',v('field'),v('response'),v('conversion'),v('region'))))
    ctx=v('context');pair=[]
    for kind,amountunit,fieldunit,conversion,response,field in (('zor','chargeunit','electricunit','electricconversion','electricresponse','znr'),('eisps','poleunit','magneticunit','magneticconversion','magneticresponse','zns')):
        fixed={'kind':k(kind),'frame':k('zbm'),'lengthunit':k('ta'),'timeunit':k('rb'),'amountunit':v(amountunit),'forceunit':v('forceunit'),'region':k('znt'),'context':ctx,'response':v(response),'fieldunit':v(fieldunit),'conversion':v(conversion),'field':k(field)}
        pair.append(k('ejts',*[fixed[n] for n,_ in FIELD_ARGS]))
    text+=define('ejtt',WITNESSES+[('context','d')],both(op('u',op('e',k('zor'),k('eisps'))),k('znn',k('zbm'),k('znr'),k('zns'),k('znt'),ctx),k('eispn',k('eispp'),k('zbm'),k('znr'),k('zns'),k('znt'),ctx),*pair))
    body=k('ejtt',*[v(n) for n,_ in WITNESSES],ctx)
    for n,t in reversed(WITNESSES):body=q('g',n,t,body)
    text+=define('ejtu',[('context','d')],body)
    text+=define('ejtv',[('context','d')],both(k('ejtu',ctx),k('ejsm',k('zbm'),k('ta'),k('rb'),ctx,k('znt')),k('s5y',k('znr'),k('zns'),k('znt'),k('tc'))))
    text+=content('ejtw',k('ejtv',p))
    for name,field in (('ejtx','znr'),('ejty','zns')):text+=define(name,[('field',FIELD),('context','d')],both(k('ejtu',ctx),k('ejs3',v('field'),k(field),k('znt'))))
    text+=content('ejtz',both(*(k('eispi',k(sign),'r[p '+rule+']',k('eirf'),p) for sign,rule in (('eispv','ejtx'),('eispw','ejty')))))
    eligible=k('eiok',v('first'),v('second'),ctx)
    text+=define('ejt2',[('theory','a'),('context','d')],both(bind(('first','second'),'a','g',eligible),bind(('first','second'),'a','f',op('y',eligible,k('eiom',v('first'),v('second'),v('theory'),ctx)))))
    text+=define('ejt3',[('theory','a'),('context','d')],both(k('eiok',k('ra'),k('zbm'),ctx),k('eisle',v('theory'),k('znu'),ctx),k('eislf',v('theory'),k('znv'),ctx),k('vh',k('znv'),k('ra'),k('znw'),ctx),k('vh',k('znv'),k('zbm'),k('znx'),ctx),op('z',k('vi',k('znu'),k('znw'),ctx),op('t',k('ejs6'),ctx)),op('z',k('vi',k('znu'),k('znx'),ctx),op('t',k('ejtw'),ctx))))
    text+=content('ejt4',q('g','theory','a',both(k('ejt2',v('theory'),p),k('ejt3',v('theory'),p))))
    text+=content('ejt5',op('y',evaluate('ejs6'),evaluate('ejtw')))
    nodes=('zny','eispy','eispx');author=k('rd');node=k('zny');scope=k('zno')
    text+=content('ejt6',both(k('zc',node,author,quote('ejt4'),quote('ejt5'),scope,p),k('eisch',k('eisk3'),quote('eion'),scope,p),k('eisch',k('eispf'),quote('ejtw'),scope,p),evaluate('ejtz'),k('eisox',k('eispx'),quote('ejtw'),p),*(k('uf',author,k(a),k(b),p) for a,b in zip(nodes,nodes[1:])),*(k('ue',k(a),k(b),p) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ejt7[] f[j s[k ejt6[]]].\n'
    text+=define('ejua',[],both(k('eir3',node,author,k('eirf'),quote('ejt7'),k('ri')),k('ue',k('eispr'),node,k('ri')),op('u',op('e',k('eispr'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejua',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='moving_fields_defined_by_signed_probe_forces_and_relativity_application',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/field-transformation-application-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for symbol,form in (('eispv','(X′,Y′,Z′)'),('eispw','(L′,M′,N′)')):ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
