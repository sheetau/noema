"""Compose motional driving, its intrinsic-energy denial, and the two-case comparison."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_magnet_case import ROOT,read,BASE,RESULT as FIRST_RESULT,FIELDS as FIRST_FIELDS,EXAMPLE,NEIGHBOR,ELIGIBILITY,COVER,motion,history,CURRENT_POINT
from scripts.compose_observable_contrast import FIELDS as COMPARISON,current_args
from scripts.compose_relative_history_match import FIELDS as RELATIVE
from scripts.compose_magnetic_action import CONVENTION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import FIELD,POINT,ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-moving-magnet-case.noema'
PARENT_BASIS='data/moving-magnet-case-basis-v1.json'
FULL='examples/v014/einstein-moving-conductor-case.noema'
CORE='examples/v014/moving-conductor-case-core.noema'
BASIS='data/moving-conductor-case-basis-v1.json'
ANNOTATIONS='data/moving-conductor-case-identifiers-v1.json'
INDEX=210
ONE='n p b b'
VECTOR=[('velocity',POINT),('magnetic',POINT),('conversion',R),('driving',POINT)]
LAW='i[h['+' '.join(t for _,t in VECTOR)+'] c]'
RESULT=[('forceunit','a'),('driveunit','a'),('conversion',R),('drive',FIELD),('point',POINT),('driving',POINT)]+[(n,t) for n,t in FIRST_RESULT if n in ('sections','cumulative','current','section','orientation','time')]
FIELDS=BASE+RESULT
CALIBRATION=CONVENTION+[('driveunit','a')]
UNIT=[('driveunit','a'),('forceunit','a'),('chargeunit','a'),('context','d')]
DRIVE=[(n,t) for n,t in FIELDS if n in ('process','left','right','frame','context','lengthunit','timeunit','chargeunit','electricunit','magneticunit','sourcecondition','electricfield','magneticfield','region','lower','upper','rightmembers','rightx','righty','rightz','forceunit','driveunit','conversion','drive')]+[('law',LAW)]
RESPONSE=[(n,t) for n,t in FIELDS if n in ('process','right','frame','context','lengthunit','timeunit','driveunit','drive','region','chargeunit','lower','upper','sections','cumulative','current')]
ENERGY=[(n,t) for n,t in FIELDS if n in ('process','right','frame','context','driveunit','drive','region')]+[('time',R),('energyunit','a'),('value',R)]
ENERGY_HISTORY=[(n,t) for n,t in ENERGY if n not in ('time','energyunit','value')]+[('lower',R),('upper',R)]
ZERO_FIELD=[(n,t) for n,t in BASE if n in ('electricfield','region','lower','upper')]
ZERO_POINT=ZERO_FIELD+[(n,R) for n in ('x','y','z','time')]
DRIVE_POINT=[('drive',FIELD),('region',next(t for n,t in BASE if n=='region')),('point',POINT),('driving',POINT)]
CLAUSE='i[h['+' '.join(t for _,t in FIELDS)+'] c]'
PAIRED=COMPARISON+[(case+n,t) for case,rs in (('first',FIRST_RESULT),('second',RESULT)) for n,t in rs if n not in ('sections','cumulative','current')]
PRIMITIVES={
 'eisar':(UNIT,'driveunitはforceunitで表す力をchargeunitで表す電荷で割った局所的な駆動の単位である。数値qの電荷への力の数値は、この単位の駆動三成分へqを掛けて対応する。同じ系の右手直交単位基底で、符号付き電荷に対する力を区別する。閉回路を一周する仕事/電荷の積分値や、機械力そのものの単位へ置き換えない。具体的な電圧単位名は原文へ追加しない。'),
 'eisas':(DRIVE,'同じprocessでleftの指定源条件に帰属する磁気側場とrightの運動により、right内の局所的な駆動driveが生じるという物理的帰属。全物質点の指定履歴と同じ系・状況・座標単位・全区間を用い、各局所位置の駆動は、その導体部分と共に動く正の単位試験電荷への磁気的作用を電荷で規格化した係数として読む。単位試験電荷は力を定義する試験規約であり、実際に測定装置や粒子を追加したという存在主張ではない。局所の速度は同じ導体部分の座標時刻微分、磁気成分は同じ位置・時刻のmagneticfieldから採り、閉じたlawの型に従う。局所力の物理的な同定・基底と単位の規約は既存eirt/eiruの磁気的作用の読みを引き継ぐ。導体の全体並進だけ、一点の評価だけ、任意の名前を起電力として代用しない。電気側場とは別の速度依存の駆動であり、電荷輸送の相対的な速度を導体全体の運動へ置き換えない。電流生成、非零の駆動、蓄積エネルギーの有無は合成で別に要求する。'),
 'eisat':(ENERGY,'指定過程・導体・系・状況・範囲の局所駆動driveに、それ自体に対応する独立の蓄積エネルギーを、指定時刻・energyunit・valueで帰属する関係。エネルギーは仕事と交換収支で扱う量で、単位は力と変位の積の基準に整合する。駆動が作用する間に供給源から移転する仕事、導体や磁石の運動エネルギー、既存磁場の蓄積エネルギー、電流による発熱をこの駆動自体の状態量へ付け替えない。否定はこの関係への合成条件で述べるため、この記号自身は有無を先取りしない。零値の慣用的な帰属を許すが、値の妥当性や非零性は合成で扱う。'),
 'eisau':(RESPONSE,'同じprocess・導体・系・状況で、指定された導体内の局所駆動driveが電荷の輸送を駆動し、同じ全有向断面の累積輸送量と電流履歴を物理的応答として生む帰属。各部分の駆動と輸送は同じ導体・座標単位・電荷単位・区間・範囲に属し、別の物体や別時刻の電流との単なる共存、相関、順序からは認定しない。駆動の局所的な物理意味はeisasにより導体の運動と源の磁場へ別に結ぶ。零交差や他の作用の併存を許し、全介入解での必要十分性や微視的機構の証明、実際の測定済みを要求しない。駆動自体の蓄積エネルギーの否定から、この生成に仕事や他のエネルギー交換が不要とは導かない。'),
 'eisav':([], '固定原文einstein-1905:u0003[771,1203)の、磁石静止・導体運動の場合と第一の場合の電流を比較する一文の箇所。'),
 'eisaw':([('node','a'),('author','a'),('whole','i[e]'),('first',CLAUSE),('second',CLAUSE),('scope','a'),('context','d')],'著者がこの箇所の閉じたwholeの説明の内部で、同じ引数束を受けるfirstとsecondの二条件を順序付きに対照して提示する談話関係。二条件はwholeで束縛される同じ事例・対象・履歴の成分であり、別々の証人へ交換しない。引用した条件をここで実行せず、両者の真理や論理的矛盾を要求しない。否定と肯定の対置、ある属性の否定にもかかわらず別の作用があるという対置を記述でき、物理的な因果をこの提示関係で代用しない。'),
}
MEANINGS={
 'eidz':'同じ速度と磁気成分に対するeicnを正の単位電荷の数値1へ適用し、局所的な力/電荷の係数を得る数値条件。符号付きの実電荷をこの係数へ掛けることと単位を区別し、閉回路電圧だけに限定しない。',
 'eid2':'磁気作用の同じ基底・長さ時間・電荷・磁気場・力単位と正の換算係数をeiruへ結び、局所駆動の単位をeisarの力/電荷に結ぶ。',
 'eid3':'同じdriveを領域内の有効な四座標で評価し、非零な空間成分を持つ駆動の証人。電気側場の非零とは区別する。',
 'eid4':'有効な座標・時刻が区間と領域内にあるなら、その点の電気側三成分が有効かつ全て零であるという条件。区間外や領域外に零を強制しない。',
 'eid5':'全実空間座標と全実時刻についてeid4を要求する、指定区間・領域に電気側場がないという内容。有限点の零や、発生の記録がないことでは代用しない。',
 'eid6':'同じ駆動に有効な時刻・値で独立の蓄積エネルギーeisatが帰属されるなら、その値は零である。非零の帰属を排除し、零値の帰属と帰属そのものがない場合の両方を許す。',
 'eid7':'全区間内時刻・全エネルギー単位・全実値にeid6を要求する。駆動自体の非零エネルギーを否定し、仕事の移転・磁場や物体のエネルギーは否定しない。',
 'eiea':'同じ許容事例と磁石・導体・結合設定に、磁石の静止と導体の運動を同じ系・区間で結ぶ前件。相対運動一致や第一の場合の存在をこの前件へ入れない。',
 'eieq':'同じ事例の電気側場・周囲領域・区間にeid5を適用する、電場不存在の成分。',
 'eier':'同じ源の磁気側場と導体の全物質点履歴に、校正した単位・係数・閉じた局所則eidzを用いる駆動eisasを結ぶ。領域内かつ導体内部・区間内の非零駆動の証人も要求する。',
 'eies':'同じ事例・導体・局所駆動について、eid7のそれ自体の非零蓄積エネルギーの不存在を要求する成分。',
 'eiet':'同じ局所駆動から同じ全電流履歴への生成帰属eisauと、既存eidrの非零電流の証人を結ぶ。相対運動の比較はこの生成の必要条件にしない。',
 'eieb':'磁石周囲の範囲と全導体部分の位置を保ち、電場不存在eieq、導体内の駆動eier、それ自体のエネルギーの否定eies、電流生成eietを同じ束縛で結ぶ。',
 'eiec':'eieaの磁石静止・導体運動の条件なら、単位と局所駆動、電流の全履歴および非零証人が存在してeiebを満たすという条件。',
 'eied':'同じ二物体・例について、許容する全候補の設定にeiecを課す内容。特定の実験実施を要求しない。',
 'eiee':'同じ例の妥当な比較eidaと、第一の場合の前件eidm・説明eids、第二の場合の前件eiea・説明eiebを、各場合の系・場・履歴・証人を交換せず結ぶ。相対履歴や電流一致を前件に混入しない。',
 'eief':'eieeの二場合がeia2の同じ相対配置履歴を持つなら、eibiの全有向断面・全経過時間の電流履歴が一致するという条件。各場合の局所的な力や駆動の値まで同一とは要求しない。',
 'eieg':'同じ二物体と例について、許容する全候補の二場合にeiefを要求する内容。大きさだけの一致、一時点、断面の合計や時間を任意に伸縮した曲線で同じ経過を代用しない。',
 'eieh':'前文と同じ磁石・導体・例についての第二の場合の閉じた条件内容。',
 'eiei':'同じ二物体・例の、第一の場合の電気的作用と第二の場合の局所駆動による電流の閉じた比較内容。',
 'eiej':'第二の場合の条件内容eiehと、同じ相対運動という留保の下での電流比較eieiを同じ評価点に結ぶ。留保を電場不存在や駆動の存在自体へ移動しない。',
 'eiek':'先行文と同じ通常の理解に、eiejの閉じた説明内容を非事実的に帰属する。',
 'eiel':'eiekの見解帰属を主張の力で提示するメッセージ。',
 'eiem':'著者・論説へのeielの発話帰属、第一の場合とのaberの対照、同じ事例内の電場不存在/駆動のdagegenとエネルギー否定/電流生成のaberの対照、本文順序を結ぶ。引用内容をこの帰属の評価時に実行しない。',
}
LIMITS=[
 '起電力は本文u0174の動く単位電荷への作用という用法を参照し、導体部分と共に動く試験電荷への局所的な磁気作用の係数として読む。閉回路の周回積分値だけに狭めず、起電力という名称を機械力そのものへ置き換えない。',
 '局所則には既存eicnの同じ系での古典的な磁気作用と単位規約を再利用する。u0174の一次近似の言い表しscj2を厳密な相対論的変換の定理へ昇格させない。',
 '否定する電場はこの例で磁石に帰属する電気側の場で、指定周囲領域と全比較区間に範囲を保つ。他の源、表面電荷の応答、外部電場を含む全場がどこでも零だとは追加しない。',
 'an sichの否定は局所的な駆動自体の独立の非零蓄積エネルギーに限る。零と帰属なしの両方を許し、エネルギーの移転や電流を生む仕事の不要性は導かない。',
 '相対運動の一致という挿入留保は二場合の電流比較に作用する。第二の場合の場・駆動・エネルギー・生成の条件は比較相手がなくても述べる。',
 '二場合は既存の同じ物質点・マクロな剛い参照配置・単位・正方向・定数時刻差による比較を引き継ぐ。一文全体の通読判断と第一文を含む全段落の判断は別にする。',
]

def case_name(case,n):
    if n=='chargeunit':return 'quantityunit'
    if n in {n for n,_ in BASE if n not in ('frame','context','electricunit','magneticunit','sourcecondition','electricfield','magneticfield','region','lower','upper','leftx','lefty','leftz','rightx','righty','rightz')}|{'sections'}:return n
    return case+n
def case_args(case,fields):return [v(case_name(case,n)) for n,_ in fields]
def apply_fields(symbol,fields):return k(symbol,*args(fields))
def universal(symbol,fields):
    body=k(symbol,*[v('point' if n=='reference' else n) for n,_ in fields])
    for n,t in reversed(fields):
        if n not in ('left','right','process','reference'):body=q('f',n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eidz',VECTOR,k('eicn',k('bb',ONE),v('velocity'),v('magnetic'),v('conversion'),v('driving')))
    text+=define('eid2',CALIBRATION,both(k('eiru',*args(CONVENTION)),k('eisar',*args(UNIT)),k('ba',v('conversion')),k('bg',k('bb',ZERO),v('conversion'))))
    coords=[app(v('point'),k(n)) for n in ROLES]
    nonzero=[op('u',k('sca',app(v('driving'),k(n)),k('bb',ZERO))) for n in ROLES[:3]]
    text+=define('eid3',DRIVE_POINT,both(app(v('region'),*coords),k('scb2',AXES,v('drive'),v('point'),v('driving')),op('x',nonzero[0],op('x',*nonzero[1:]))))
    p=[v(n) for n in ('x','y','z','time')]
    inside=both(*(k('zzba',x) for x in p),k('lg',v('lower'),v('upper'),v('time')),app(v('region'),*p))
    values=[app(app(v('electricfield'),k(n)),*p) for n in ROLES[:3]]
    text+=define('eid4',ZERO_POINT,op('y',inside,both(*(both(k('ba',x),k('sca',x,k('bb',ZERO))) for x in values))))
    zero=apply_fields('eid4',ZERO_POINT)
    for n in reversed(('x','y','z','time')):zero=q('f',n,R,zero)
    text+=define('eid5',ZERO_FIELD,zero)
    text+=define('eid6',ENERGY,op('y',both(k('zzba',v('time')),k('zzba',v('value')),apply_fields('eisat',ENERGY)),k('sca',v('value'),k('bb',ZERO))))
    noenergy=q('f','time',R,q('f','energyunit','a',q('f','value',R,op('y',k('lg',v('lower'),v('upper'),v('time')),apply_fields('eid6',ENERGY)))))
    text+=define('eid7',ENERGY_HISTORY,noenergy)
    text+=define('eiea',BASE,both(apply_fields('eisap',ELIGIBILITY),apply_fields('eic2',EXAMPLE),k('eiah',*motion('left')),k('eiag',*motion('right'))))
    text+=define('eieq',FIELDS,apply_fields('eid5',ZERO_FIELD))
    text+=define('eier',FIELDS,both(apply_fields('eid2',CALIBRATION),k('eisas',*args(DRIVE[:-1]),'r[p eidz]'),apply_fields('eid3',DRIVE_POINT),k('lg',v('lower'),v('upper'),coords[3]),k('eiro',*[v(n) for n in ('right','frame','context','lengthunit','timeunit')],*coords)))
    text+=define('eies',FIELDS,apply_fields('eid7',ENERGY_HISTORY))
    text+=define('eiet',FIELDS,both(apply_fields('eisau',RESPONSE),k('eidr',*history(),v('section'),v('orientation'),v('time'))))
    text+=define('eieb',FIELDS,both(apply_fields('eisal',NEIGHBOR),k('eidn',*motion('right'),v('region')),*(apply_fields(n,FIELDS) for n in ('eieq','eier','eies','eiet'))))
    result=apply_fields('eieb',FIELDS)
    for n,t in reversed(RESULT):result=q('g',n,t,result)
    text+=define('eiec',BASE,op('y',apply_fields('eiea',BASE),result))
    text+='d eied[left a right a process a] e[b point['+universal('eiec',BASE)+']].\n'
    text+=define('eiee',PAIRED,both(apply_fields('eida',COMPARISON),k('eidm',*case_args('first',BASE)),k('eiea',*case_args('second',BASE)),k('eids',*case_args('first',FIRST_FIELDS)),k('eieb',*case_args('second',FIELDS))))
    text+=define('eief',PAIRED,op('y',both(apply_fields('eiee',PAIRED),apply_fields('eia2',RELATIVE)),k('eibi',*current_args())))
    text+='d eieg[left a right a process a] e[b point['+universal('eief',PAIRED)+']].\n'
    for symbol,target in (('eieh','eied'),('eiei','eieg')):text+='d '+symbol+'[] e[k '+target+'[k eisaa[] k eisab[] k eisac[]]].\n'
    text+='d eiej[] e[b point['+both('t[k eieh[]][v point]','t[k eiei[]][v point]')+']].\n'
    text+='d eiek[] e[b point['+both(k('eisah',k('eisak'),k('eirf'),v('point')),k('eisai',k('eisak'),'r[k eiej[]]',v('point')))+']].\n'
    text+='d eiel[] f[j s[k eiek[]]].\n'
    text+=define('eiem',[],both(k('eir3',k('eisav'),k('rd'),k('eirf'),'r[k eiel[]]',k('ri')),k('zbc',k('eisav'),k('rd'),'r[k eidv[]]','r[k eieh[]]',k('eisac'),k('ri')),
        *(k('eisaw',k('eisav'),k('rd'),'r[k eiej[]]','r[p '+a+']','r[p '+b+']',k('eisac'),k('ri')) for a,b in (('eieq','eier'),('eies','eiet'))),
        k('ue',k('eisaq'),k('eisav'),k('ri')),op('u',op('e',k('eisaq'),k('eisav')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiem',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='moving_conductor_case_and_conditional_current_comparison',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-magnet-case-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Moving-conductor explanation and comparison appended')
