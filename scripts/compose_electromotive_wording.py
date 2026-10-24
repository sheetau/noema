"""Describe the old wording as a physical response and a directional first jet."""
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
from scripts.compose_force_wordings import vector,at
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-force-motion-binding.noema';PARENT_BASIS='data/force-motion-binding-basis-v1.json'
FULL='examples/v014/einstein-electromotive-wording.noema';CORE='examples/v014/electromotive-wording-core.noema'
BASIS='data/electromotive-wording-basis-v1.json';ANNOTATIONS='data/electromotive-wording-identifiers-v1.json';INDEX=167
DYNAMIC='h['+POINT+' '+R+' '+POINT+'] '+POINT
PHYSICAL=[(n,'a') for n in ('kind','frame','lengthunit','timeunit','amountunit','forceunit')]+[('electric',FIELD),('magnetic',FIELD),('region',REGION),('context','d'),('response',DYNAMIC)]
APPROX=[('light',R),('velocity',POINT),('magnetic',POINT),('base',POINT),('point',POINT),('response',DYNAMIC)]
CURRENT=[('velocity',POINT),('response',DYNAMIC)]+[(n,'a') for n in ('magneticunit','totalrecord','extrarecord')]+[('context','d')]
PRIMITIVES={
 'eisqp':(PHYSICAL, '同じframeの校正された右手直交三軸・lengthunit/timeunit、同じcontextとregionのelectric/magneticという外部の両場で、kindの符号付き試験量をamountunitで指定し、その地点で指定した座標時刻速度を持たせるときの局所的な機械力の理想応答がresponseである。引数は四座標・符号付き量・三速度、結果は同じ軸とforceunitで表す三成分。試験量と大きさを零へ近づけて配置への影響を除いた応答を単位量へ規格化する既存の静止試験規約を、速度も入力とする関数へ拡張する。異なる速度は同じ背景の下での仮想的な比較であり、同じ出来事に相反する速度が同時に実現したとはしない。力は運動量変化への寄与又はそれを釣り合わせる機械的作用で同定する。この両場による寄与を扱い、重力・支持力等を加えた合力ではない。物理的な帰属を数値から推定せず、実測・有限試験体の実在・特定の力の法則は含意しない。零速度での電気側との一致、寄与の分解、速度依存、外積や近似次数は別に合成する。'),
 'eisqq':([('expression','a'),('rule','i[h['+POINT+' d] c]'),('wording','a'),('document','a'),('context','d')], '同じdocumentのwordingでexpressionを引用して取り上げる語として用い、その指すベクトル量の役割を同じ状況での閉じたruleに従って解釈する。規則は三成分の値と状況を引数に取り、対象・系・単位・物理的な役割は規則内へ結ぶ。ここでの引用は用語を取り上げる働きであり、他人の発言の再現、皮肉、命題の否定を自動で加えない。綴りだけの意味代用、引用内容の実行、規則の成立やその物理法則の自動証明ではない。'),
 'eisqr':([('established','a'),('new','a'),('scope','a'),('context','d')], '同じscopeの二つの記述の仕方について、establishedをその議論で既に用いられてきた言い方、newを今回の議論で新しく提示する言い方として対置する。発話の時間順だけや一方の真偽・優劣とは区別し、前者の禁止・完全廃棄、後者が歴史上初めてであること、二つが無条件に厳密同値であることは含意しない。'),
 'eisqs':([], 'u0174第一項で引用符を付けて取り上げるelektromotorische Kraftという用語の表現。物理的な追加寄与の役割は閉じた規則ejygへ接続し、原語の綴りだけで意味を代用しない。'),
}
MEANINGS={
 'ejxy':'指定三ベクトルを同じ実数倍し、空間以外の役割を0とする。成分の順序と符号を保つ。',
 'ejxz':'同じ三空間軸で第一ベクトルから第二ベクトルを引く。力の寄与の差に用いるときは物理的な対象・系・単位を別に一致させる。',
 'ejx2':'三空間成分の二乗和。非負の速度の大きさの二乗を、平方根を導入せず表す。',
 'ejx3':'正の有効な光速度と有効な三速度を要求し、速度の二乗和を光速度の二乗より小さくする。向きは限定せず、零速度も許す。点状電気量が動く条件はejxmで別に要求する。',
 'ejx4':'同じ地点・量1・指定速度での物理応答から、指定された電気側の基準寄与を引く追加ベクトル。応答と基準寄与の帰属は呼出側で保持する。',
 'ejx5':'固定した速度ベクトルをparameter倍したときの速さ／光速度の二乗。parameter²*(u·u)/V²を構成する。向きの符号を消した外積の代用ではなく、誤差次数の比較量である。',
 'ejx6':'同じ光速度・固定した非零速度方向・固定地点・固定磁場・電気基準寄与と応答について、速度をparameter倍して0へ近づける。全三成分で追加応答と(u×H)/Vの差が、その速さ／光速度の二乗のオーダーとなる。固定した場・方向ごとの定数と近傍幅を許し、全場一様性、解析性、有限速度での厳密等値を要求しない。',
 'ejx7':'現在の同じK・zol・zpo・zpj・zou・Dynと両場について速度依存の機械力応答を帰属させる。静止の電気力ejwuと応答の零速度値を一致させ、同じ磁場単位を電気量単位との積が換算1でDynとなる規約へ結ぶ。実際の速度での全寄与と電気基準を引いた追加寄与の別々の力記録を同じ対象・出来事・系・単位へ結び、追加値が0の場合も許す。',
 'ejya':'現在の三速度・物理応答を、同じ地点の磁場と現在の電気基準力zplに対するejx6の一次近似へ接続する。電気寄与と追加寄与を足すと同じ実際の応答となり、数値だけの外積を物理力と認定しない。',
 'ejyb':'先行する場変換の適用域で、現在の点状単位電気量が同じKの場内を任意方向に動く前提。ejxmの物理的履歴・量・位置を保持し、速さは光速度未満と明示する。',
 'ejyc':'指定した同じ三速度について、物理応答・磁場単位・全寄与記録・追加寄与記録が存在し、ejx7の同じ物理的帰属とejyaの一次近似を満たす。全成分へ同じ証人を共有する。',
 'ejyd':'任意の有効な方向の速度についてejybならejycとなる、第一項の力と近似の内容。x方向だけの条件ではない。先行理論の適用域で著者が提示する主張であり、処理系がその法則を証明したとはしない。',
 'ejye':'同じ物理的な応答と電気基準によりejx7の追加寄与となる三成分値。近似式そのものや電位差ではなく、同じ対象に働く機械的な寄与の残差として指示する。',
 'ejyg':'現在の電気量の同じ運動前提と物理的な分解に属する追加値であるという用語解釈の閉じた規則。近似の正しさを用語の意味に組み込まない。',
 'ejyh':'著者が第一項の任意方向の条件付き力の主張ejydを述べ、引用して取り上げた用語をejygへ結び、第一項を旧来、後続第二項を新しい言い方として対置する。',
 'ejyi':'第一項全体の力・留保・引用用語・旧来の位置付けejyhを述べるメッセージ。',
 'ejyj':'第一項を同じ著者・論説へ帰属し、既存の二表現の導入eisqnに続ける。文167を更新し、後続第二項の実内容の完成を先取りしない。',
}
LIMITS=[
 'u0174を原刊909末尾–910頁で全体として読む。点状の単位電気量・同じ電磁場・運動という条件、電気力に加わる寄与、引用された用語、二次以上の留保、速度×磁気側の場／光速度、旧来の言い方という位置付けを保持する。M0318=v/V、A0024は頁区切りである。',
 '二つの言い表しは先行する最終場変換の解釈であり、同じ理論の正のV・光速未満の速さで扱う。第一項の運動方向をx軸へ制限せず、右手直交三軸で直接外積を構成する。数式を記述するために任意方向の変換の導出を先に証明する必要はない。第二項の任意方向の共動系への変換は別に完成させる。',
 'ここでKraftを同じ系・位置・単位の理想試験電気量への局所的な機械的作用と読む。追加寄与は同じ動的応答から零速度の電気基準を引く分解として明示する。電位差・電源の起電力、重力や支持力を含む合力、独立の新しい実体又は非零の追加力を要求しない。',
 '異なる速度の応答は同じ背景の下での仮想比較であり、実際の電気量の履歴はejxmの同じ出来事での速度へ結ぶ。全期間の等速、加速度0、同じ出来事への複数の実速度、実験実施、有限の試験体による元の場の不変を追加しない。',
 '二次以上を捨てるを、固定した場・方向についての速度比の一次部分を保持し差をO((v/V)^2)とする読みで表す。parameterを0へ動かして同じ三速度を比例縮小し、外積の符号と誤差の速さ二乗を区別する。任意の速度で一次式が厳密成立する、誤差が非零、全場一様な定数、解析的な冪級数の収束は要求しない。',
 '電気基準の単位はejwu、磁気側数値の単位はeirnとeispuの積の換算1で同じDynへ接続する。現代SIの係数や異なる量単位の数値の一致を補わない。原文の正規化された単位の読みを保持する。',
 'Alte/Neueは同じ二表現の論述上の位置付けであり、前者の誤り・禁止や後者の歴史的初出を含意しない。引用符は用語を取り上げる働きと読み、皮肉や他者発言の再現を補わない。第一項の指示を第三の表現や後続u0176の内容へ替えない。',
 '文167以外の359主張、旧定義・意味規約・証拠を保持する。新規基本関係は速度入力付きの物理的試験応答、引用用語のベクトル役割の解釈、旧来／新しいの対置の三つ、残る一記号は用語の参照。有限検査・型検査・著者の主張の記述を、全実数の真理又は意味同値の自動証明と混同しない。',
]

def bind(fields,body):
    for n,t in reversed(fields):body=q('g',n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');u=v('velocity');V=v('light');param=v('parameter');ctx=v('context');response=v('response')
    text+=define('ejxy',[('velocity',POINT),('parameter',R)],vector([k('shv',app(u,k(a)),param) for a in ROLES[:3]]),POINT)
    text+=define('ejxz',[('first',POINT),('second',POINT)],vector([k('bf',app(v('first'),k(a)),app(v('second'),k(a))) for a in ROLES[:3]]),POINT)
    comps=[app(u,k(a)) for a in ROLES[:3]]
    text+=define('ejx2',[('velocity',POINT)],k('sexb',*comps,*comps),R)
    text+=define('ejx3',[('light',R),('velocity',POINT)],both(k('ba',V),k('bg',zero,V),k('shn',AXES,u,'p ba'),k('bg',k('ejx2',u),k('shv',V,V))))
    extra=[('response',DYNAMIC),('point',POINT),('base',POINT),('velocity',POINT)]
    text+=define('ejx4',extra,k('ejxz',app(response,v('point'),one,u),v('base')),POINT)
    ratio_squared=k('shv',k('ejx2',u),k('sjd',k('shv',V,V)))
    text+=define('ejx5',[('light',R),('velocity',POINT),('parameter',R)],k('shv',k('shv',param,param),ratio_squared),R)
    scaled=k('ejxy',u,param);domain='i[parameter '+R+']['+both(k('ba',param),k('ejx3',V,scaled))+']'
    exact=k('ejx4',response,v('point'),v('base'),scaled);linear=k('sci2',V,scaled,v('magnetic'))
    remainder=[k('svy',domain,'i[parameter '+R+']['+app(exact,k(a))+']','i[parameter '+R+']['+app(linear,k(a))+']','i[parameter '+R+']['+k('ejx5',V,u,param)+']',zero) for a in ROLES[:3]]
    text+=define('ejx6',APPROX,both(k('ejx3',V,u),k('ejxj',u),k('sch2',v('magnetic'),v('base')),k('shn',k('shx'),v('point'),'p ba'),*remainder))
    physical=dict(kind=k('zor'),frame=k('ra'),lengthunit=k('ta'),timeunit=k('rb'),amountunit=k('zou'),forceunit=k('zot'),electric=k('znl'),magnetic=k('znm'),region=k('znk'),context=ctx,response=response)
    actual=app(response,k('zpj'),one,u);additional=k('ejx4',response,k('zpj'),k('zpl'),u)
    values=[k('zpc',v(record),k('zol'),k('zpn'),k('ra'),k('zpo'),k('zot'),val,ctx) for record,val in (('totalrecord',actual),('extrarecord',additional))]
    text+=define('ejx7',CURRENT,both(k('eisqp',*[physical[n] for n,_ in PHYSICAL]),k('ejwu',ctx),
        k('eirn',k('ra'),k('znm'),v('magneticunit'),ctx),k('eispu',k('zor'),k('zou'),v('magneticunit'),k('zot'),one,ctx),
        k('sho',AXES,app(response,k('zpj'),one,vector((zero,zero,zero))),k('zpl'),'p sca'),k('shn',AXES,actual,'p ba'),*values,
        *(op('u',op('e',a,b)) for a,b in ((v('totalrecord'),v('extrarecord')),(v('totalrecord'),k('zpe')),(v('extrarecord'),k('zpe'))))))
    text+=define('ejya',[('velocity',POINT),('response',DYNAMIC),('context','d')],k('ejx6',k('tc'),u,at(k('znm'),k('zpj')),k('zpl'),k('zpj'),response))
    text+=define('ejyb',[('velocity',POINT),('context','d')],both(k('ejxm',u,ctx),k('ejx3',k('tc'),u)))
    text+=define('ejyc',[('velocity',POINT),('context','d')],bind(CURRENT[1:-1],both(k('ejx7',*[v(n) for n,_ in CURRENT]),k('ejya',u,response,ctx))))
    p=v('point');text+=content('ejyd',q('f','velocity',POINT,op('y',k('ejyb',u,p),k('ejyc',u,p))))
    text+=define('ejye',CURRENT+[('value',POINT)],both(k('ejx7',*[v(n) for n,_ in CURRENT]),k('shn',AXES,v('value'),'p ba'),k('sho',AXES,v('value'),additional,'p sca')))
    text+=define('ejyg',[('value',POINT),('context','d')],bind(CURRENT[:-1],both(k('ejyb',u,ctx),k('ejye',*[v(n) for n,_ in CURRENT],v('value')))))
    text+=content('ejyh',both(k('uh',k('zpq'),k('rd'),quote('ejyd'),k('zno'),p),k('eisqq',k('eisqs'),'r[p ejyg]',k('zpq'),k('eirf'),p),k('eisqr',k('zpq'),k('zpr'),k('zno'),p)))
    text+='d ejyi[] f[j s[k ejyh[]]].\n'
    text+=define('ejyj',[],both(k('eir3',k('zpq'),k('rd'),k('eirf'),quote('ejyi'),k('ri')),k('ue',k('eisqn'),k('zpq'),k('ri')),op('u',op('e',k('eisqn'),k('zpq')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not (set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejyj',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='old_wording_physical_additional_force_and_any_direction_first_order',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/force-motion-binding-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisqs',role='designation',forms=[dict(text='„elektromotorische Kraft“',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
