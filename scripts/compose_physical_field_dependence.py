"""Bind the frame-dependent electric/magnetic distinction to physical fields."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,FIELD,REGION,ROLES
from scripts.compose_field_transform import MAP
from scripts.compose_force_wordings import at
from scripts.compose_moving_field_definition import FIELD_ARGS,RESPONSE
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-magnetomotive-wording.noema';PARENT_BASIS='data/magnetomotive-wording-basis-v1.json'
FULL='examples/v014/einstein-physical-field-dependence.noema';CORE='examples/v014/physical-field-dependence-core.noema'
BASIS='data/physical-field-dependence-basis-v1.json';ANNOTATIONS='data/physical-field-dependence-identifiers-v1.json';INDEX=170
UNITS=[(n,'a') for n in ('chargeunit','poleunit','electricunit','magneticunit','forceunit')]
RESPONSES=[(n,RESPONSE) for n in ('firstelectric','firstmagnetic','secondelectric','secondmagnetic')]
CONFIG=[(n,'a') for n in ('process','first','second')]+[('point',POINT),('velocity',POINT),('speed',R),('electric',FIELD),('magnetic',FIELD),('region',REGION)]
PAIR=[('theory','a')]+CONFIG+[('context','d')]+UNITS+RESPONSES
REALIZATION=[('process','a'),('frame','a'),('electric',FIELD),('magnetic',FIELD),('region',REGION),('context','d')]+UNITS+[('electricresponse',RESPONSE),('magneticresponse',RESPONSE)]
COMPARE=[('kind','a'),('point',POINT),('velocity',POINT),('speed',R),('electric',FIELD),('magnetic',FIELD)]
PRIMITIVES={
 'eisqw':([], 'この論説で二原理から展開してきた同じ理論の参照。u0176のentwickelten Theorieに対応し、既存の構成課題eigjと本文の提示eisqyへ結ぶ。他人の理論、原著者が述べていない任意の現代理論や将来予定だけの見解へ替えない。参照名だけで理論の真理・無矛盾性を認定しない。'),
 'eisqx':([('theory','a'),('process','a'),('context','d')], '同じcontextでprocessがtheoryの法則・物理量と単位規約により許される電磁的な過程の配置である。実際に観測・実現された過程だけでなく、同じ理論の仮定上の配置を含む。単なる数値関数、成功した変換例という理由だけから許容を認定しない。理論の全適用範囲についての許容関係であり、量種や法則を配置ごとに交換しない。各系の場・試験応答・対応座標は別の合成内容で指定する。'),
 'eisqy':([('theory','a'),('document','a'),('project','i[e]'),('scope','a'),('context','d')], '同じdocumentのscopeのこの論述段階で、projectで指定した理論構成を既に展開した体系としてtheoryを参照・提示する。同じ構成課題・法則・概念規約を保持し、序文の将来の計画だけへの言及や別の理論への交換とは区別する。著者の論述段階の帰属であり、全導出の正しさ・実験的実証・処理系による証明が完了したという保証ではない。'),
}
MEANINGS={
 'ejzj':'同じ過程・系・領域の二場を、場割当znnと過程への帰属eispn、電荷と磁極強度それぞれの静止試験応答ejtsへ結ぶ。同じ五単位で換算1となる二つの場の物理的な意味を保持し、任意の数値関数を物理的な場へ格上げしない。',
 'ejzk':'任意方向の非零・光速未満の三速度と非負の速さを、二系全体の等速並進、同じ長さ時間の校正、純粋boostによる同一出来事の全域座標対応へ結ぶ。軸回転だけや単位変更だけの比較を運動状態の変化として使わない。',
 'ejzl':'同じ理論が許す一つの過程について、ejzkの二系を、同じ地点時刻の対応と両場の混合・逆座標評価・領域逆像へ結ぶ。両系のejzjは同じ五単位を共有し、各系の電気・磁気の四応答をそれぞれ保持する。別過程や別地点の零と非零を比較しない。',
 'ejzm':'電荷種又は磁極強度種について、同じ旧地点とそのboost像で、対応する電気側又は磁気側の有効な三成分の一方だけが零である。両側とも非零のまま成分や向きだけが変わる例、未知値、異なる量種への切替ではこの条件を満たさない。',
 'ejzn':'指定した同じ理論と量種について、物理的な対応ejzlと局所的な作用の有無の相違ejzmを満たす過程・二系・地点・速度・二場・領域・単位・応答の証人がある。全ての場又は全ての系で変化するという全称主張にはしない。',
 'ejzo':'電気側と磁気側のそれぞれについて、同じ理論にejznの証人がある。二つの証人は別の許容過程でもよい。単位試験量への電気/磁気の局所作用の有無を運動状態に独立な区分とはできないという読みを保つ。電磁過程自体の不存在や全ての系での零/非零反転を主張しない。',
 'ejzp':'同じ論説の理論構成eigjをこの段階で展開した同じ理論eisqwとして参照し、その理論についてejzoの電気・磁気双方の非独立性を述べる内容。過去の単なる数値証人scx2を物理的な結論の代用にしない。',
 'ejzq':'同じ著者が末尾の系依存性ejzpを述べたことを保持する。後半全体の補助概念という役割・導入理由・Man siehtの提示は別に接続する。',
 'ejzr':'物理的な場の系依存性ejzqを述べるメッセージ。',
 'ejzs':'末尾の系依存性を同じ著者・論説へ帰属し、冒頭の磁動力への類推の後に置く。文170を更新する。原文の後半全体やu0176全体を、この部分だけで完成扱いしない。',
}
LIMITS=[
 'u0176末尾の電気・磁気の力は、直前で同定した系ごとの単位試験量への局所作用として読む。存在が運動状態から独立でないという句を、その二種類への局所的な有無の区分が理論全体で系に独立なものではない、と明示して解釈する。単なる成分値の変化に縮めず、対応する有効三成分の零/非零の相違と物理的な試験応答を結ぶ。',
 '同じ一つの過程の同じ出来事を二系で比較し、別の現象・別の地点・別の単位を持ち寄って零/非零を作らない。純粋boostの代表を使い、同じ向きの対応軸、全系の等速並進、全域座標対応を保持する。',
 '二つの量種にそれぞれ反例があることは、その区分を理論全体で運動状態に独立にはできないという内容である。全ての場が全ての速度で変わること、同じ一配置で電気側と磁気側の両方が同時に出現又は消滅すること、電磁過程全体が存在しなくなることを要求しない。',
 '物理的な許容配置はeisqxにより同じ理論の範囲へ結ぶ。現実の観測済み配置・有限の実験・磁気単極子の実在を追加せず、理論が許す仮定上の配置を扱う。場の物理的帰属、試験応答、単位・座標規約を数値計算から推定しない。',
 '展開した理論は、同じ論説の序文で述べた構成課題eigjに対応する現在の体系としてeisqyへ結ぶ。著者の論述段階と理論の物理的真理の証明を区別する。',
 'この構成は系依存性の節を物理的な解釈へ接続する。補助概念の役割だけを持つというnur、同じ概念の導入とその理由、Man siehtの提示、およびu0176全体の通読判断はまだ残る。旧scx2・sdf2・sdg2と証拠を上書きしない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    one=k('bb','n p b b');ctx=v('context');point=v('point');u=v('velocity');speed=v('speed');first=v('first');second=v('second');E=v('electric');H=v('magnetic');region=v('region');process=v('process')
    pair=[]
    for kind,amountunit,fieldunit,response,field in [('zor','chargeunit','electricunit','electricresponse','electric'),('eisps','poleunit','magneticunit','magneticresponse','magnetic')]:
        values=dict(kind=k(kind),frame=v('frame'),lengthunit=k('ta'),timeunit=k('rb'),amountunit=v(amountunit),forceunit=v('forceunit'),region=region,context=ctx,response=v(response),fieldunit=v(fieldunit),conversion=one,field=v(field))
        pair.append(k('ejts',*[values[n] for n,_ in FIELD_ARGS]))
    text+=define('ejzj',REALIZATION,both(op('u',op('e',k('zor'),k('eisps'))),k('znn',v('frame'),E,H,region,ctx),k('eispn',process,v('frame'),E,H,region,ctx),*pair))
    geometry=[('first','a'),('second','a'),('velocity',POINT),('speed',R),('context','d')]
    mapping='i[location '+POINT+']['+k('ejym',k('tc'),speed,u,v('location'))+']'
    text+=define('ejzk',geometry,both(k('ejyk',k('tc'),speed,u),k('ejxj',u),k('ejm2',first,second,ctx,*(app(u,k(a)) for a in ROLES[:3])),*(k('ejsl',f,k('ta'),k('rb'),ctx) for f in (first,second)),k('eisqt',first,second,k('ta'),k('rb'),mapping,ctx)))
    newpoint=k('ejym',k('tc'),speed,u,point);newE=k('ejyp',k('tc'),speed,u,E,H);newH=k('ejyq',k('tc'),speed,u,E,H);newregion=k('ejyr',k('tc'),speed,u,region)
    realization=lambda f,e,h,r,er,mr:k('ejzj',process,f,e,h,r,ctx,*[v(n) for n,_ in UNITS],v(er),v(mr))
    text+=define('ejzl',PAIR,both(k('eisqx',v('theory'),process,ctx),k('ejzk',*[v(n) for n,_ in geometry]),k('ejsj',point,region),k('ejsj',newpoint,newregion),realization(first,E,H,region,'firstelectric','firstmagnetic'),realization(second,newE,newH,newregion,'secondelectric','secondmagnetic')))
    text+=define('ejzm',COMPARE,op('x',both(op('e',v('kind'),k('zor')),k('scv2',at(E,point),at(newE,newpoint))),both(op('e',v('kind'),k('eisps')),k('scv2',at(H,point),at(newH,newpoint)))))
    witnesses=CONFIG+UNITS+RESPONSES
    text+=define('ejzn',[('theory','a'),('kind','a'),('context','d')],bind(witnesses,both(k('ejzl',*[v(n) for n,_ in PAIR]),k('ejzm',*[v(n) for n,_ in COMPARE]))))
    text+=define('ejzo',[('theory','a'),('context','d')],both(k('ejzn',v('theory'),k('zor'),ctx),k('ejzn',v('theory'),k('eisps'),ctx)))
    p=v('point');text+=content('ejzp',both(k('eisqy',k('eisqw'),k('eirf'),quote('eigj'),k('zno'),p),k('ejzo',k('eisqw'),p)))
    text+=content('ejzq',k('uh',k('zpt'),k('rd'),quote('ejzp'),k('zno'),p))
    text+='d ejzr[] f[j s[k ejzq[]]].\n'
    text+=define('ejzs',[],both(k('eir3',k('zpt'),k('rd'),k('eirf'),quote('ejzr'),k('ri')),k('ue',k('zps'),k('zpt'),k('ri')),op('u',op('e',k('zps'),k('zpt')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejzs',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='physical_frame_dependence_of_electric_and_magnetic_action',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/magnetomotive-wording-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
