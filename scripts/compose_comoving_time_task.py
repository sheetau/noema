"""Connect auxiliary coordinates and the first synchronized-time subtask."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_homogeneity_claim import ROOT,read
from scripts.compose_comoving_labels import TAU
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import interval
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-homogeneity-claim.noema';PARENT_BASIS='data/homogeneity-claim-basis-v1.json'
FULL='examples/v014/einstein-comoving-time-task.noema';CORE='examples/v014/comoving-time-task-core.noema'
BASIS='data/comoving-time-task-basis-v1.json';ANNOTATIONS='data/comoving-time-task-identifiers-v1.json';INDEX=274
MEANINGS={
 'eizm':'同じ点の代表位置について、kの自系時間区間全体での静止eit2とKの区間全体で同じ正のX速度を持つeivwを要求する。物質点に限らず配置点を扱い、時計の内部運動を停止させない。',
 'eizn':'指定点・K時点・出来事・K地点・k時点を明示して結ぶ。Kのym三値を同じ代表履歴と実測地点eixuに一致させ、同じ出来事を両系のsbと各系固有のeisnkへ接続する。両時刻値はそれぞれの区間に属し、tとτの数値一致は課さない。',
 'eizo':'同じ点とK時点についてeiznを満たす一つの出来事・K地点・k時点が存在する。値の断片を別の出来事から集めない。',
 'eizp':'全配置点と全比較時点の範囲を明示し、同じ並進設定eivz、全点の完全な静止・並進履歴、全点全時点の測定・出来事接続、Kの全区間実数時刻の被覆を要求した上でsilの補助三座標不変性を保持する。端点だけの不変性ではない。',
 'eizq':'同じ移動後設定でeizpが成立するという内容。x′はx-vtであり、ξへの同一視や一般的な力学的導出は含まない。',
 'eizr':'著者がsinを補助量の定義として置き、その同じ設定の全静止点に対する不変性eizqを主張し明白と提示する。定義導入から結果への本文順序を保つ。',
 'eizs':'補助座標導入と時間不変性eizrを述べるメッセージ。',
 'eizt':'u0048第一文を同じ著者・論説へ帰属し、直前の一様性による必要性の検討に続ける。',
 'eizu':'現在の全出来事の四座標対応eiy3を保ち、全対応座標対について候補関数が同じ速度で作ったx′とy,z,tから有効なk時刻成分τを返す条件。旧測定規則やξを関数の第一引数にしない。',
 'eizv':'eizuを満たす四引数関数を答えとする質問。具体式・存在・唯一性・発見済みを先取りしない。',
 'eizw':'同じ方程式探索の中で、まずτをx′,y,z,tの関数として求める質問eizvを選ぶ。主要な検討段階の最初と、この下位課題で最初に求める量を混同しない。',
 'eizx':'まずτの関数を求める課題eizwを述べるメッセージ。',
 'eizy':'u0048第二文を同じ著者・論説へ帰属し、補助座標の不変性に続ける。',
 'eizz':'eizuの候補関数と、同じ全配備時計の自系静止・校正・共通参照・全対全試行同期eiyfを結ぶ。全比較出来事とその全K座標に対し、そのk地点にある配備時計すべてでeiygの局所表示が候補値を与え、全有効読取値が候補値に等しい場合に限り同じ表示に対応する。時計一台・一部の指示だけへ縮めない。',
 'eiz2':'同じτ探索のためeizzの時計指示との一致条件を方程式で表す必要を提示し、同じkの局所表示規則eiyoを第一節の同期規則への参照へ結ぶ。目的と必要性を式の導出済みや達成済みに替えない。',
 'eiz3':'同期時計の指示全体を方程式で表す必要eiz2を述べるメッセージ。',
 'eiz4':'u0048第三文を同じ著者・論説へ帰属し、τを先に求める下位課題に続ける。',
}
LIMITS=[
 'u0048三文の全437文字・314本文文字を扱う。補助量の導入、全静止点の時間不変な三値、明白さ、まず求める量と四引数、目的、方程式で表す必要、指示全体との一致、第一節の同期規則を保持する。',
 'x′=x-vtは既存sinで定義する補助量である。vは同じ正のX方向速度zb7、tはKの既存の時刻である。運動系の物差しで測るξ、棒の固有長、両系共通の時刻へ置き換えない。',
 '静止点は同じ座標配置の全点eisk7として読む。位置履歴を考察する全範囲zdiのうちx4がk静止とする点と過不足なく結び、物質点に限定しない。各点の自系代表履歴eit2と同じK並進eivwを要求する。時計の全物質点を静止させるeipwは使わない。',
 'K側全比較時点ysをeislaへ一致させ、正の幅と全時点での利用可能性をsilで保つ。K区間内の全実数時刻についてeiwiで時点を確保する。各点各時点のymを同じ代表位置、同じ出来事、同じ測定地点へ結ぶ。全点にK時計の新設を課さず、異なる系の時刻値を等置しない。',
 '不変性は同じ点の全時点間でx′,y,zが変わらないこと。異なる点の値の一致、ξ=x′、静止と等速並進の一般的な同値性の導出証明を追加しない。明白さは著者による提示である。',
 'τの候補条件は先行する全比較出来事zc4と現在のeiy3/eiyz/eiy2/eiyyへ接続する。未測定の任意の実数四組の実現を追加しない。x′への代入後の同じ出来事のτとの一致を全対応対に要求する。',
 'Inbegriffおよびnichts anderesは、この同じ比較範囲の全出来事におけるkの配備時計の指示全体との過不足ない値対応として読む。全配備時計は初期から同じ集団で、共通参照と全対全試行の第一節同期を満たす。時計のない地点への新しい時刻拡張や、比較範囲外の出来事の時計値を勝手に追加しない。',
 'まずτを求めることと、そのため指示条件を方程式で表す必要は課題の提示である。まだ候補式の探索を実行した、式が一意に存在する、光往復の式を導出したとは記述しない。有限検査、通読判断、一般の物理的真理や同義性の証明は別に扱う。',
]

def proposed(function,first):
    time=k('zc6',first,k('zc7'))
    return 'c['+function+']['+' '.join([k('sin',k('zb7'),k('zc6',first,k('yn')),time),k('zc6',first,k('yo')),k('zc6',first,k('yp')),time])+']'

def definitions():
    p=v('point');c=v('context');moment=v('moment');event=v('event');place=v('place');other=v('othermoment')
    frame=k('ra');moving=k('zbm');lu=k('ta');tu=k('rb')
    track=lambda f,a:k('eismh',p,f,lu,tu,k(a),c)
    text=define('eizm',[('point','a'),('context','d')],both(k('eit2',p,moving,c,lu,tu,*interval(moving,c),*(track(moving,a) for a in ('yn','yo','yp'))),k('eivw',p,c)))
    time=k('yl',moment,frame,tu,c);tau=k('yl',other,moving,tu,c)
    coords=[k('ym',p,moment,frame,lu,k(a),c) for a in ('yn','yo','yp')]
    movingcoords=['c['+track(moving,a)+']['+tau+']' for a in ('yn','yo','yp')]
    fields=[(n,'a') for n in ('point','moment','event','place','othermoment')]+[('context','d')]
    body=[k('zce',p,moment,frame,lu,c),k('zcf',moment,frame,tu,c),k('ba',time),k('lg',*interval(frame,c),time),k('zbd',event),k('sb',p,event,frame,c,lu,tu,time,*coords),k('eisnk',event,moment,frame,c),k('cb',event,place,frame),k('zcf',other,moving,tu,c),k('ba',tau),k('lg',*interval(moving,c),tau),k('eisnk',event,other,moving,c),k('sb',p,event,moving,c,lu,tu,tau,*movingcoords)]
    for a,coord in zip(('yn','yo','yp'),coords):body.extend([k('sca',coord,'c['+track(frame,a)+']['+time+']'),k('eixu',place,frame,k(a),coord,c)])
    text+=define('eizn',fields,both(*body))
    text+=define('eizo',[('point','a'),('moment','a'),('context','d')],q('g','event','a',q('g','place','a',q('g','othermoment','a',k('eizn',*[v(n) for n,_ in fields])))))
    selected=both(k('zdi',p,c),k('x4',p,moving,c))
    allpoints=q('f','point','a',both(op('z',selected,k('eisk7',moving,p,c)),op('y',selected,both(k('eizm',p,c),q('f','moment','a',op('y',k('ys',moment,c),k('eizo',p,moment,c)))))))
    moments=q('f','moment','a',op('z',k('ys',moment,c),k('eisla',frame,moving,moment,c)))
    coverage=q('f','time',R,op('y',k('lg',*interval(frame,c),v('time')),k('eiwi',v('time'),c)))
    text+=define('eizp',[('context','d')],both(k('eivz',c),allpoints,moments,coverage,k('sil',c)))
    text+=content('eizq',k('eizp',k('zb6')))
    text+=content('eizr',both(k('zdm',k('zdj'),k('rd'),'r[p sin]',k('eisms'),v('point')),k('uh',k('zdk'),k('rd'),quote('eizq'),k('eisms'),v('point')),k('zdg',k('zdk'),k('rd'),quote('eizq'),k('eisms'),v('point')),k('ue',k('zdj'),k('zdk'),v('point'))))
    text+='d eizs[] f[j s[k eizr[]]].\n'
    def author(name,node,message,prior):return define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    text+=author('eizt','zdj','eizs','zdf')
    val=proposed(v('function'),v('first'))
    pairs=q('f','first','a',q('f','second','a',op('y',both(k('eiyz',v('first')),k('eiy2',v('second')),k('eiyy',v('first'),v('second'))),both(k('ba',val),k('sca',val,k('zc6',v('second'),k('zc7')))))))
    text+=define('eizu',[('function',TAU)],both('t[k eiy3[]][k zb6[]]',k('ba',k('zb7')),k('sca',k('zb7'),k('zbi',frame,moving,lu,tu,k('zb6'))),pairs))
    text+='d eizv[] g['+TAU+'][j v[i[function '+TAU+']['+k('eizu',v('function'))+']]].\n'
    text+=content('eizw',k('zdn',k('zdl'),k('rd'),k('zdb'),quote('eizv'),k('eisms'),v('point')))
    text+='d eizx[] f[j s[k eizw[]]].\n';text+=author('eizy','zdl','eizx','zdk')
    at=both(k('zc4',event),k('eiyx',event,v('first'),frame,k('zb6')),k('zcz',event,moving,k('zb6')),k('zbz',moving,v('clock'),k('zb6')),k('cb',v('clock'),place,moving),k('cb',event,place,moving))
    display=lambda value:k('eiyg',event,v('clock'),place,moving,value,k('zb6'))
    exact=both(display(val),q('f','reading',R,op('y',k('ba',v('reading')),op('z',display(v('reading')),k('sca',v('reading'),val)))))
    allreadings=op('y',at,exact)
    for name in reversed(('event','clock','place','first')):allreadings=q('f',name,'a',allreadings)
    text+=define('eizz',[('function',TAU)],both(k('eizu',v('function')),k('eiyf',moving,k('zb6')),allreadings))
    text+=content('eiz2',both(k('zdo',k('zdp'),k('rd'),'r[p eizz]',k('zdl'),k('eisms'),v('point')),k('eislp',k('zdp'),k('rd'),k('eisdy'),'r[p eiyo]',k('eirf'),v('point'))))
    text+='d eiz3[] f[j s[k eiz2[]]].\n';text+=author('eiz4','zdp','eiz3','zdl')
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eizt','eizy','eiz4')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='auxiliary_invariance_and_synchronized_time_task',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+3))).document
    ann=json.loads(read('data/homogeneity-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
