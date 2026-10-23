"""Connect clock capabilities, current origin placement and a genuine rate question."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_reciprocal_shape_results import ROOT,read
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_rod_methods import interval
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-reciprocal-shape-results.noema';PARENT_BASIS='data/reciprocal-shape-results-basis-v1.json'
FULL='examples/v014/einstein-origin-clock-question.noema';CORE='examples/v014/origin-clock-question-core.noema'
BASIS='data/origin-clock-question-basis-v1.json';ANNOTATIONS='data/origin-clock-question-identifiers-v1.json';INDICES=(337,338)
CLOCK=[('clock','a'),('frame','a'),('context','d')]
LOCAL=[(n,'a') for n in ('clock','event','display','record','place','frame')]+[('context','d')]
PAIRED=[(n,'a') for n in ('clock','event','display','record','place','observed')]+[('context','d')]
MEANINGS={
 'ejij':'同じ指定系・状況の時計について、型・時間単位・校正と、全区間の代表位置の静止履歴eit2を結ぶ。状況を持たない静止関係ccやx4へ代替状況の静止を集約せず、針や内部機構の運動も止めない。',
 'ejik':'同じ時計の同所の対象出来事と表示出来事を、指定系・状況の現在の四座標と場所へ結ぶ局所表示の全候補。自系区間の時刻を持ち、当該出来事での時計所在zabと局所対応eisgmを要求する。表示値が正しいものだけを候補に選ばない。',
 'ejil':'同じ候補の四座標を時計の代表位置の実際の軌跡sbへ結び、対象・表示の双方で座標時刻と等しい指示を要求する。他の有効な読みがある場合も全て同じ値でなければならず、尺度・原点のずれや誤った別表示を許さない。',
 'ejim':'指定した自系の区間内時刻に、同じ時計の局所候補ejikと校正された表示ejilを満たす一組の出来事・表示・四記録・場所が存在する。同じ四つの証人を両条件で共有する。',
 'ejin':'同じ系に校正され代表位置が静止する時計ejijについて、全ての局所候補がejilを満たし、区間内の全実数時刻にejimが存在する。一回の正しい表示や測定済み標本だけから全期間の時刻表示能力を認定しない。',
 'ejio':'同じ時計について、基準状況から許容される代替設定zidの下でKに静止して同じ系の時刻tを示せる場合と、kに静止してその時刻τを示せる場合がそれぞれ存在する。二場合を現実の同一状況の同時成立にしない。',
 'ejja':'指定時刻に同じ時計の代表位置三成分が零であり、同じkの測定原点の三座標も零で、時計がその原点に置かれるという局所条件。場所個体と零の数値を単に同一視しない。',
 'ejip':'同じ時計が実際の考察設定でkに静止してτを正確に示すejinを満たす。kの全対象時刻にejjaの原点配置を保ち、全ての局所表示候補の場所も同じ原点である。',
 'ejiq':'同じ時計の同じ対象出来事・同所表示・kの現在記録の校正を、同じ出来事のKの現在記録と代表位置の実際の軌跡へ結ぶ。Kの対象区間の時刻を使い、別の出来事のtや遠隔受信時刻を代用しない。',
 'ejjb':'指定K時刻に、ejiqを満たす同じ時計の一組の出来事・表示・k記録・場所・K記録が存在する。五つの証人を同じ出来事への対応として結ぶ。',
 'ejir':'同じ時計のKにおける正の時間幅・校正尺度・完全な代表位置の軌跡を保持し、その全対象時刻にejjbの両系の照合が存在する。Kにも静止することや具体的な進み率は要求しない。',
 'ejis':'正の候補進み率、厳密に前後する観測時刻二値、時計の指示二値について、指示差が候補率と観測時間差の積である。有効性・時間順序と非零の時間幅を保つ。',
 'ejit':'同じ時計・状況のk記録とK記録が、ある一つの出来事・同所表示・場所を共有してejiqに対応する。数値の一致だけで無関係な二記録を組にしない。',
 'ejiu':'同じ原点時計と全K時刻の照合について、異なるK時刻の記録組が存在し、その全ての時間順の組で実際のτ指示差がejisの候補率に従う。一定の正の進み率という今回の読みで、特定の平方根や答えの存在を先に指定しない。',
 'ejiv':'Kから見た同じ原点時計zieの進み方を、ejiuを満たす正の一定率を答えの候補とする実数値の問い。問いを作るだけで答えの存在・一意性・発見済みを断言しない。',
 'ejiw':'両系でその系の時刻を表示できる同じ時計zieを、現在はkの原点に置きτを示すようにするという能力ejioと配置・校正ejipの思考設定。',
 'ejix':'同じ第四節で時計の設定ejiwを考察の前提に追加するug/zaoの提示と、既出t/τの規則への記号参照。実際の製作・設置済みという報告ではない。',
 'ejiy':'u0118第一文の追加の時計設定ejixを述べるメッセージ。',
 'ejiz':'第一文を同じ著者・論説へ帰属し、前の二方向の形状結果の箇所zibに続ける。',
 'eji2':'同じ時計の進み率の問いejivを著者が同じ第四節で提示するzih。Kからの比較は問いの内部に固定し、別の時計やk自身から見た率に替えない。',
 'eji3':'u0118第二文の進み方を問う提示eji2を述べるメッセージ。',
 'eji4':'第二文の問いを同じ著者・論説へ帰属し、同じ時計の設定zifの後に続ける。',
}
LIMITS=[
 'u0118の全二文を原刊903頁末と904頁冒頭に照合する。M0207=t、M0208=τ、M0209=k、M0210=τを既存の同じ時刻規則と移動系へ結ぶ。改頁で第一文を分断しない。',
 'eine der Uhrenは各系に静止したときにその系の時刻を示せる時計の一つと読む。同じ選択対象zieに二つの代替設定での能力を与え、現在の配置をkの原点に固定する。両系へ同時に静止する物体を作らず、時計の製造や実際の運搬過程も補わない。',
 '静止は時計の校正された代表位置の完全な区間履歴で表す。内部の針・機構を停止させる全物質点の静止ではない。代替設定の許容は既存zidの物理的入力であり、論理的無矛盾や一つの有限成功例から能力を推定しない。',
 'so gerichtetはτを同じ尺度と原点で指示するよう校正されていることと読む。単なる一定の比、任意の表示原点、未知の倍率のままの時計ではない。局所的一致と同じ現在の四座標・代表軌跡を保持し、誤った別の読みも全読み条件で排除する。',
 '旧zacは動く時計と静止系の局所時刻を比較する記録であるため、代替設定の一般的な局所表示の候補には使わない。現在の同所表示eisgm、所在zab、場所付き四記録eiywと全区間での存在を合成する。旧shd/x4や過去の記録・証拠は変更しない。',
 '問いは今回の一様運動と校正された理想時計について、Kの観測時間差当たりの正の一定な指示差を問うと読む。瞬間的に変動する進み率一般の定義とはしない。候補条件に全時間順の記録組と正の時間幅を要求するが、問いの提示から候補の存在・一意性を導かない。',
 '進み率の候補へ√(1−(v/V)²)、β、その逆数を先に代入しない。u0119以降の二式・比例式・単位時間の遅れと近似はこの二文の内容には加えない。',
 'Wir denken uns fernerを同じ節への思考設定の追加、Wie schnellを同じ設定に続く問いとして保持する。検査・通読判断・実際の時計の実現可能性や物理法則の証明を区別する。新しい原始記号は追加しない。',
]

def tracks(clock,frame,ctx):return [k('eismh',clock,frame,k('ta'),k('rb'),k(a),ctx) for a in ('yn','yo','yp')]
def trajectory(clock,frame,ctx):return [clock,frame,ctx,k('ta'),k('rb'),*interval(frame,ctx),*tracks(clock,frame,ctx)]

def definitions():
    cl=v('clock');frame=v('frame');ctx=v('context');event=v('event');display=v('display');record=v('record');place=v('place');time=v('time');zero=k('bb','n p a b')
    stamp=lambda rec:k('zc6',rec,k('zc7'))
    xyz=lambda rec:[k('zc6',rec,k(a)) for a in ('yn','yo','yp')]
    text=define('ejij',CLOCK,both(k('ca',cl),k('va',frame),k('ci',k('rb')),k('eisdf',cl,ctx),k('eit2',*trajectory(cl,frame,ctx))))
    selection=both(k('eiyw',event,record,place,frame,ctx),k('zab',cl,event,place,frame,ctx),k('zbd',display),k('cb',display,place,frame),k('eisgm',event,display,cl,frame,ctx),k('lg',*interval(frame,ctx),stamp(record)))
    text+=define('ejik',LOCAL,selection)
    coordinates=xyz(record);moment=stamp(record);actual=[app(f,moment) for f in tracks(cl,frame,ctx)]
    reads=lambda e,r:k('ce',cl,e,frame,k('rb'),r)
    unique=q('f','reading',R,op('y',both(k('ba',v('reading')),op('x',reads(event,v('reading')),reads(display,v('reading')))),k('sca',v('reading'),moment)))
    text+=define('ejil',LOCAL,both(k('ba',moment),*(k('ba',x) for x in coordinates),k('sb',cl,event,frame,ctx,k('ta'),k('rb'),moment,*actual),*(k('sca',x,y) for x,y in zip(coordinates,actual)),reads(event,moment),reads(display,moment),unique))
    fields=('event','display','record','place');local=args(LOCAL)
    witness=bind(fields,'a','g',both(k('ejik',*local),k('ejil',*local),k('sca',stamp(record),time)))
    text+=define('ejim',[('clock','a'),('frame','a'),('time',R),('context','d')],both(k('lg',*interval(frame,ctx),time),witness))
    allrecords=bind(fields,'a','f',op('y',k('ejik',*local),k('ejil',*local)))
    alltimes=q('f','time',R,op('y',k('lg',*interval(frame,ctx),time),k('ejim',cl,frame,time,ctx)))
    text+=define('ejin',CLOCK,both(k('ejij',cl,frame,ctx),allrecords,alltimes))
    alternatives=[q('g','trial','d',both(k('zid',cl,k(f),ctx,v('trial')),k('ejin',cl,k(f),v('trial')))) for f in ('ra','zbm')]
    text+=define('ejio',[('clock','a'),('context','d')],both(k('ca',cl),op('u',op('e',k('ra'),k('zbm'))),*alternatives))
    moving=k('zbm');lab=k('ra');origin=k('zbn',moving,ctx)
    text+=define('ejja',[('clock','a'),('context','d'),('time',R)],both(k('lg',*interval(moving,ctx),time),k('zbv',moving,origin,ctx),k('cb',cl,origin,moving),*(k('eixu',origin,moving,k(a),zero,ctx) for a in ('yn','yo','yp')),*(k('sca',app(f,time),zero) for f in tracks(cl,moving,ctx))))
    movinglocal=[cl,event,display,record,place,moving,ctx]
    atorigin=bind(fields,'a','f',op('y',k('ejik',*movinglocal),op('e',place,origin)))
    text+=define('ejip',[('clock','a'),('context','d')],both(k('ejin',cl,moving,ctx),q('f','time',R,op('y',k('lg',*interval(moving,ctx),time),k('ejja',cl,ctx,time))),atorigin))
    observed=v('observed');labtime=stamp(observed);labcoords=xyz(observed);labactual=[app(f,labtime) for f in tracks(cl,lab,ctx)]
    text+=define('ejiq',PAIRED,both(k('ejik',*movinglocal),k('ejil',*movinglocal),k('eiyx',event,observed,lab,ctx),k('lg',*interval(lab,ctx),labtime),k('sb',cl,event,lab,ctx,k('ta'),k('rb'),labtime,*labactual),*(k('sca',x,y) for x,y in zip(labcoords,labactual))))
    labwitness=bind((*fields,'observed'),'a','g',both(k('ejiq',*args(PAIRED)),k('sca',labtime,time)))
    text+=define('ejjb',[('clock','a'),('time',R),('context','d')],both(k('lg',*interval(lab,ctx),time),labwitness))
    text+=define('ejir',[('clock','a'),('context','d')],both(k('bg',*interval(lab,ctx)),k('eisdd',lab,k('ta'),k('rb'),ctx),k('se',*trajectory(cl,lab,ctx)),q('f','time',R,op('y',k('lg',*interval(lab,ctx),time),k('ejjb',cl,time,ctx)))))
    rate=v('rate');first=v('first');last=v('last');firstreading=v('firstreading');lastreading=v('lastreading')
    text+=define('ejis',[(n,R) for n in ('rate','first','last','firstreading','lastreading')],both(*(k('ba',v(n)) for n in ('rate','first','last','firstreading','lastreading')),k('sbg',rate),k('bg',first,last),k('sca',k('bf',lastreading,firstreading),k('shv',rate,k('bf',last,first)))))
    text+=define('ejit',[('clock','a'),('record','a'),('observed','a'),('context','d')],bind(('event','display','place'),'a','g',k('ejiq',*args(PAIRED))))
    rs=('firstown','firstlab','lastown','lastlab');fo,fl,lo,ll=map(v,rs)
    pair=both(k('ejit',cl,fo,fl,ctx),k('ejit',cl,lo,ll,ctx),k('bg',stamp(fl),stamp(ll)))
    law=k('ejis',rate,stamp(fl),stamp(ll),stamp(fo),stamp(lo))
    text+=define('ejiu',[('clock','a'),('rate',R),('context','d')],both(k('sbg',rate),k('ejip',cl,ctx),k('ejir',cl,ctx),bind(rs,'a','g',pair),bind(rs,'a','f',op('y',pair,law))))
    text+='d ejiv[] g['+R+'][j v[i[rate '+R+']['+k('ejiu',k('zie'),rate,k('zb6'))+']]].\n'
    text+=content('ejiw',both(k('ejio',k('zie'),k('zb6')),k('ejip',k('zie'),k('zb6'))))
    notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,rule in (('eism5','eiwt'),('eisnl','eiym'))]
    text+=content('ejix',both(k('ug',k('zif'),k('rd'),quote('ejiw'),k('eisn5'),v('point')),k('zao',k('zib'),k('zif'),k('eisn5'),v('point')),*notation))
    text+='d ejiy[] f[j s[k ejix[]]].\n'
    text+=content('eji2',k('zih',k('zig'),k('rd'),quote('ejiv'),k('eisn5'),v('point')))
    text+='d eji3[] f[j s[k eji2[]]].\n'
    for name,message,node,previous in (('ejiz','ejiy','zif','zib'),('eji4','eji3','zig','zif')):
        text+=define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejiz','eji4')];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='origin_clock_capabilities_current_readings_and_rate_question',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/reciprocal-shape-results-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
