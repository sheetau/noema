"""Compose both magnetic counterparts using the same pole, motion and units."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_velocity import DOMAIN as TIMES,CURVE
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,ROLES
from scripts.compose_force_wordings import vector,at
from scripts.compose_rest_force import AXES
from scripts.compose_moving_field_definition import FIELD_ARGS,RESPONSE
from scripts.compose_electromotive_wording import DYNAMIC,PHYSICAL,APPROX as ELECTRIC_APPROX,bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-comoving-wording.noema';PARENT_BASIS='data/comoving-wording-basis-v1.json'
FULL='examples/v014/einstein-magnetomotive-wording.noema';CORE='examples/v014/magnetomotive-wording-core.noema'
BASIS='data/magnetomotive-wording-basis-v1.json';ANNOTATIONS='data/magnetomotive-wording-identifiers-v1.json';INDEX=169
LOCAL=[(n,'a') for n in ('carrier','event','poleunit','amountrecord')]+[('point',POINT),('velocity',POINT),('context','d')]
HISTORY=LOCAL+[('domain',TIMES),('curve',CURVE)]
OLD_WITNESSES=[('dynamic',DYNAMIC),('static',RESPONSE)]+[(n,'a') for n in ('electricunit','magneticunit','baserecord','totalrecord','extrarecord')]
OLD=LOCAL+OLD_WITNESSES
NEW_WITNESSES=[('speed',R)]+[(n,'a') for n in ('frame','newamountrecord','fieldunit','forcerecord')]+[('static',RESPONSE)]
NEW=LOCAL+NEW_WITNESSES
APPROX=[('electric' if n=='magnetic' else n,t) for n,t in ELECTRIC_APPROX]
PRIMITIVES={
 'eisqu':([('node','a'),('author','a'),('source','i[e]'),('counterpart','i[e]'),('scope','a'),('context','d')], 'authorがnodeで、同じscopeのsourceに対応するcounterpartも成り立つと、内容間の類推として提示する。対応先の対象・量・符号・条件はcounterpartの合成内容で明示する。同じ語への言及や任意の類似性だけで真偽を推論せず、両内容の無条件な同義性、対象の数値的同一性又は処理系による証明とは区別する。'),
 'eisqv':([], 'u0176冒頭で引用して取り上げるmagnetomotorischen Kräfteという用語の表現。磁極強度に対する機械力応答から静止の磁気基準を引いた追加寄与の役割ejzdへ結ぶ。引用語の綴りだけで物理的意味を代用しない。'),
}
MEANINGS={
 'ejy3':'指定された点状の磁極担体・出来事・Kの四座標を、磁極強度eispsの同じ単位値1の結果記録、座標単位、同じ履歴の三つの瞬間微分へ結ぶ。任意方向の非零・光速未満の速度を要求し、担体を固定電気量zolへ替えない。仮定上の試験極として読む。',
 'ejy4':'同じ磁極担体の運動ejy3の時間領域と履歴があり、同じKの二場と領域内の同じ地点へ接続する。磁極が実在したとの無条件の存在主張をせず、後続の条件文の前件に用いる。',
 'ejy5':'同じ固定地点・磁気基準・動的応答と任意方向について、追加応答と−(u×E)/Vの差を全三成分で速度比二乗のオーダーへ結ぶ。負符号を保ち、速度を比例縮小する族で読む。有限速度での厳密等値や全場一様な誤差を加えない。',
 'ejy6':'同じ磁極強度単位・K・対象・出来事・地点について、静止時の磁気側試験応答と動的機械力応答を帰属する。量1での静止応答、動的応答の零速度値、同じ地点の磁気側の場を一致させ、全寄与と基準との差の別記録を同じ力単位へ結ぶ。電気側の場の単位も磁極量との積が換算1となるよう保持する。近似はこの物理的な役割へ含めない。',
 'ejy7':'同じ磁極の運動条件に対し、ejy6の共通の応答・単位・記録の証人があり、その追加力が同じ地点の電気側の場によるejy5の一次式を満たす。静止磁気力と追加磁動力を別対象や別地点へ分けない。',
 'ejzi':'同じ磁極の局所引数と動的応答について、同じ地点の電気側の場を一次項、磁気側の場を静止基準としてejy5へ渡す。近似と物理的帰属ejy6は別に検査し、存在証人の動的応答を共有する。',
 'ejza':'同じ磁極へ瞬間的に相対静止する系の全体並進と全域座標対応ejysを要求し、同じ担体・出来事の瞬間静止ejwrと単位値1を変換後の位置へ結ぶ。両場と領域を同じ逆座標で変換し、磁気側の場をその新地点の静止試験力と同じ記録へ同定する。旧Kの力をコピーしない。',
 'ejzb':'同じ磁極の運動に対し、速さ・共動系・新系の量記録・場単位・力記録・静止応答の共通証人があり、ejzaを満たす。各成分へ別の系や別の磁極を割り当てない。',
 'ejzc':'任意の仮定上の点状単位磁極と出来事・単位・記録・地点・速度について、ejy4の運動前件なら、旧来の追加項ejy7と共動系で測る力ejzbの両方が成り立つという磁気側の対応内容。二系の力の同一成分を主張しない。',
 'ejzd':'同じ仮定上の磁極の運動とejy6の物理的な分解に属する追加力の値であるという閉じた用語規則。量や系を省かず、一次近似の真理を用語の意味に含めない。',
 'ejze':'先行する電気側の二つの言い表しejydとejywを、類推の参照元となる一つの内容へまとめる。引用された内容を処理系が実行・証明するものではない。',
 'ejzf':'著者が磁気側にもejzcが成り立つと述べ、先行する二つの電気側の言い表しejzeへの類推を明示し、引用用語を同じ磁極の追加寄与の規則ejzdへ結ぶ。',
 'ejzg':'磁動力への対応内容・類推・引用語ejzfを述べるメッセージ。',
 'ejzh':'同じ著者・論説への帰属を保持し、直前の第二項の後に磁動力への類推を接続する。文169を更新し、u0176後半の補助概念・導入理由・系依存性を未処理のまま完成扱いしない。',
}
LIMITS=[
 'u0176冒頭の一文を、直前の二つの電気側の言い表しの磁気側への対応として読む。静止基準H、追加寄与−(u×E)/Vと二次以上の留保、共動系の変換後H′による同系の力の二側面を保持する。',
 '磁極強度は既存eispsの符号付き試験量として扱い、量1の仮定上の点状担体の運動を条件文の前件に置く。孤立した磁荷の実在、現代の磁気単極子理論、磁石全体への合力を追加しない。量の種類は電荷zorと区別する。',
 '共動系は先行第二項と同じ、任意方向の光速未満の三速度に合わせた純粋boostの代表である。担体の当該瞬間の静止を要求するが、加速度0や全期間の静止は要求しない。速度は同じ担体の物理的履歴の三微分へ接続する。',
 '旧来の追加力と新系で測る全寄与を同一の三成分としない。基準・全寄与・追加寄与は旧Kで同じ対象・出来事・単位の別記録に結び、新系では同じ量種・量単位・力単位を用いる。単位積の換算1を明示する。',
 '静止・動的な試験応答は既存の物理的な帰属規約eispt/eisqpであり、数値関数だけから認定しない。全実数・全関数の量化を保持し、有限対照と存在結合診断を一般的な物理法則又は意味同義性の自動証明にしない。',
 '新基本関係は二つの閉じた内容間の類推を著者へ帰属する一般関係一つ、参照は引用用語一つである。磁極の量・運動・力・単位・両変換・近似は既存の関係と計算から合成する。',
 'u0176後半のMan sieht、理論内で補助概念の役割だけを持つという主張、電気・磁気の力の座標系の運動状態からの非独立性、その同じ事情による導入理由を今後完成させる。今回だけでu0176全体の意味判断を増やさない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');ctx=v('context');point=v('point');u=v('velocity');carrier=v('carrier');event=v('event');unit=v('poleunit')
    text+=define('ejy3',HISTORY,both(k('ejxj',u),k('ejx3',k('tc'),u),app(k('zrdpointlike'),carrier,ctx),k('ejsl',k('ra'),k('ta'),k('rb'),ctx),k('eisqd',carrier,k('ra'),event,k('ta'),k('rb'),point,ctx),k('sbw2',v('amountrecord'),carrier,k('eisps'),k('ra'),event,unit,'n p b b',one,ctx,'p zof','p zog'),k('seoc',carrier,k('ra'),ctx,v('domain'),v('curve'),event,point,*(app(u,k(a)) for a in ROLES[:3]))))
    text+=define('ejy4',LOCAL,both(bind(HISTORY[-2:],k('ejy3',*[v(n) for n,_ in HISTORY])),k('ejsy',ctx),k('ejsj',point,k('znk'))))
    V=v('light');param=v('parameter');scaled=k('ejxy',u,param)
    domain='i[parameter '+R+']['+both(k('ba',param),k('ejx3',V,scaled))+']'
    exact=k('ejx4',v('response'),point,v('base'),scaled);linear=k('scq2',V,scaled,v('electric'))
    remainder=[k('svy',domain,'i[parameter '+R+']['+app(exact,k(a))+']','i[parameter '+R+']['+app(linear,k(a))+']','i[parameter '+R+']['+k('ejx5',V,u,param)+']',zero) for a in ROLES[:3]]
    text+=define('ejy5',APPROX,both(k('ejx3',V,u),k('ejxj',u),k('sch2',v('electric'),v('base')),k('shn',k('shx'),point,'p ba'),*remainder))
    def static(frame,region,field,fieldunit,response):
        values=dict(kind=k('eisps'),frame=frame,lengthunit=k('ta'),timeunit=k('rb'),amountunit=unit,forceunit=k('zot'),region=region,context=ctx,response=response,fieldunit=fieldunit,conversion=one,field=field)
        return k('ejts',*[values[n] for n,_ in FIELD_ARGS])
    def force_record(record,frame,value):return k('zpc',record,carrier,k('zpn'),frame,event,k('zot'),value,ctx)
    base=at(k('znm'),point);actual=app(v('dynamic'),point,one,u);extra=k('ejx4',v('dynamic'),point,base,u)
    values=dict(kind=k('eisps'),frame=k('ra'),lengthunit=k('ta'),timeunit=k('rb'),amountunit=unit,forceunit=k('zot'),electric=k('znl'),magnetic=k('znm'),region=k('znk'),context=ctx,response=v('dynamic'))
    records=[force_record(v(record),k('ra'),value) for record,value in [('baserecord',base),('totalrecord',actual),('extrarecord',extra)]]
    text+=define('ejy6',OLD,both(k('eisqp',*[values[n] for n,_ in PHYSICAL]),static(k('ra'),k('znk'),k('znm'),v('magneticunit'),v('static')),k('eirn',k('ra'),k('znl'),v('electricunit'),ctx),k('eispu',k('eisps'),unit,v('electricunit'),k('zot'),one,ctx),k('sho',AXES,app(v('static'),point,one),base,'p sca'),k('sho',AXES,app(v('dynamic'),point,one,vector((zero,zero,zero))),base,'p sca'),k('shn',AXES,actual,'p ba'),*records,*(op('u',op('e',v(a),v(b))) for a,b in [('baserecord','totalrecord'),('baserecord','extrarecord'),('totalrecord','extrarecord')])))
    text+=define('ejzi',LOCAL+[('dynamic',DYNAMIC)],k('ejy5',k('tc'),u,at(k('znl'),point),base,point,v('dynamic')))
    text+=define('ejy7',LOCAL,bind(OLD_WITNESSES,both(k('ejy6',*[v(n) for n,_ in OLD]),k('ejzi',*[v(n) for n,_ in LOCAL],v('dynamic')))))
    speed=v('speed');frame=v('frame');newpoint=k('ejym',k('tc'),speed,u,point);E=k('ejyp',k('tc'),speed,u,k('znl'),k('znm'));H=k('ejyq',k('tc'),speed,u,k('znl'),k('znm'));region=k('ejyr',k('tc'),speed,u,k('znk'));force=at(H,newpoint)
    text+=define('ejza',NEW,both(k('ejys',u,speed,frame,ctx),k('ejwr',carrier,frame,event,newpoint,ctx),k('eisqd',carrier,frame,event,k('ta'),k('rb'),newpoint,ctx),k('sbw2',v('newamountrecord'),carrier,k('eisps'),frame,event,unit,'n p b b',one,ctx,'p zof','p zog'),k('eispn',k('eispp'),k('ra'),k('znl'),k('znm'),k('znk'),ctx),k('eispn',k('eispp'),frame,E,H,region,ctx),static(frame,region,H,v('fieldunit'),v('static')),k('sho',AXES,app(v('static'),newpoint,one),force,'p sca'),force_record(v('forcerecord'),frame,force)))
    text+=define('ejzb',LOCAL,bind(NEW_WITNESSES,k('ejza',*[v(n) for n,_ in NEW])))
    arguments=[v(n) if n!='context' else v('point') for n,_ in LOCAL]
    # Rename the quantified location to avoid content()'s situation binder.
    arguments[4]=v('location')
    claim=op('y',k('ejy4',*arguments),both(k('ejy7',*arguments),k('ejzb',*arguments)))
    for n,t in reversed(LOCAL[:-1]):claim=q('f','location' if n=='point' else n,t,claim)
    text+=content('ejzc',claim)
    role=both(k('ejy4',*[v(n) for n,_ in LOCAL]),k('ejy6',*[v(n) for n,_ in OLD]),k('shn',AXES,v('value'),'p ba'),k('sho',AXES,v('value'),extra,'p sca'))
    text+=define('ejzd',[('value',POINT),('context','d')],bind(LOCAL[:-1]+OLD_WITNESSES,role))
    text+=content('ejze',both(op('t',k('ejyd'),v('point')),op('t',k('ejyw'),v('point'))))
    text+=content('ejzf',both(k('uh',k('zps'),k('rd'),quote('ejzc'),k('zno'),v('point')),k('eisqu',k('zps'),k('rd'),quote('ejze'),quote('ejzc'),k('zno'),v('point')),k('eisqq',k('eisqv'),'r[p ejzd]',k('zps'),k('eirf'),v('point'))))
    text+='d ejzg[] f[j s[k ejzf[]]].\n'
    text+=define('ejzh',[],both(k('eir3',k('zps'),k('rd'),k('eirf'),quote('ejzg'),k('ri')),k('ue',k('zpr'),k('zps'),k('ri')),op('u',op('e',k('zpr'),k('zps')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejzh',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='magnetic_counterparts_of_both_force_wordings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/comoving-wording-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisqv',role='designation',forms=[dict(text='„magnetomotorischen Kräfte“',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
