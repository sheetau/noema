"""Connect comoving direct measurement and synchronized endpoint measurement."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rod_experiment import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-rod-experiment.noema';PARENT_BASIS='data/rod-experiment-basis-v1.json'
FULL='examples/v014/einstein-rod-methods.noema';CORE='examples/v014/rod-methods-core.noema'
BASIS='data/rod-methods-basis-v1.json';ANNOTATIONS='data/rod-methods-identifiers-v1.json';INDICES=(255,256)
RULE='i[h['+R+' d] c]'
PRIMITIVES={
 'eisl3':([('node','a'),('author','a'),('procedure','i[h['+R+' a d] c]'),('movingframe','a'),('restframe','a'),('moving',''+RULE),('comparison',RULE),('scope','a'),('document','a'),('context','d')], 'authorがnodeで、movingの操作を、restframeでcomparisonの状況が成立していた場合と同じprocedureの仕方で行うものとして比較する。movingframeとrestframeの対応、同じ対象・道具・観測者・単位・操作規則は引用した規則に固定する。比較するのは物差しを当てて直接読むという手順であり、二状況の実在、同じ数値結果、全物理法則の不変性を要求しない。'),
 'eisl4':([('observer','a'),('endpoint','a'),('event','a'),('clock','a'),('place','a'),('frame','a'),('timeunit','a'),('value',R),('context','d')], '同じobserverが、endpointのeventに関して、frameのplaceに設置されたclockの局所表示と既定の時刻規約を手段として、その端点が指定時刻valueに位置するplaceを確定する操作。単に数値が一致しているだけで観測・決定を推測せず、端点の出来事・場所・局所表示・同期・指定値への一致は別条件で要求する。信号を遠隔で受け取った時刻や、物差しによる二地点間距離の測定と分ける。'),
 'eisl5':([('node','a'),('author','a'),('subject','a'),('designation','a'),('methods','j['+RULE+']'),('scope','a'),('document','a'),('context','d')], 'authorがnodeで、subjectに対して列methodsの各操作で得る値候補を、同じdesignationの量として呼ぶことを認める。後の方法も先の方法に加えて同じ量の呼称を適用できるという分類上の許容であり、各規則は対象・単位・状況を保つ閉じた記述である。呼称の採用を義務にせず、値の実在・唯一性や方法間の数値的一致は含意しない。'),
 'eisl6':([], 'u0031第二文の引用符付きLänge des Stabesという量の呼称。指す棒と許容する測定規則の範囲は合成で指定する。'),
}
MEANINGS={
 'eipw':'指定した同じ物体・基準系・設定の全物質点履歴をeiahへ渡し、正の区間幅で静止を要求する。移動側と静止側の時刻を同一視しない。',
 'eipx':'同じ指定物体の静止系raでの全物質点履歴へeipfを適用し、既出のybによる正のX方向等速並進を要求する。棒・物差し・観測者の巨視的な位置を同じ区間で追う。',
 'eipy':'同じ棒・物差し・観測者が静止系で同じybの並進を行い、同じ移動側系xlでは全区間静止する条件。棒には既存eipkの剛性・軸配置を保持し、移動系の全固定配置にも同じ速度成分のeiojを要求する。',
 'eipz':'同じ棒・観測者・物差しについて、指定系での直接接触と尺度の読取りsbeを、三者の全履歴の静止、正の長さ、棒の剛性と軸長eipeへ結ぶ共通の直接測定規則。数値だけから読みを認定しない。',
 'eip2':'先行する方法aのsbiと、全履歴の同伴eipy、移動系での直接測定eipzを結ぶ。先の問いで参照した方法を同じ対象・道具・尺度の下で具体化する。',
 'eip3':'同じ共通の直接測定規則eipzを静止系raの想定へ適用する比較側の条件。実際に三者が静止系で止まったとは主張しない。',
 'eip4':'同じ棒の二端標識を長軸の両端、各出来事と場所へ結び、第一節のeingで静止時計・局所表示・共通参照rcの時刻を与える。両値を同じ指定時刻xvに一致させ、同じ端点の世界線・時刻・三座標もsbへ結ぶ。',
 'eip5':'既存eipkの運動する棒についてeip4の二端の時刻・場所を保持し、同じ観測者がそれぞれの局所時計を使ってその場所を確定する操作を結ぶ。観測者の静止は要求しない。',
 'eip6':'先行する方法bのsbkと、時計を用いた二端位置の確定eip5、今回は静止系で静止する同じ物差しの全履歴を結ぶ。既存th/xhの二地点間距離と、同じ指定時刻の軸長eipaが同じ値である。棒へ直接物差しを当てる方法aへ交換しない。',
 'eip7':'著者が同じ考察範囲で方法aのeip2を提示し、その直接測定手順を、三者が静止系で静止しているなら行うeip3と同じeipzとして比較する内容。比較から値の一致を導かない。',
 'eiqa':'方法aの提示と静止の場合への手順比較eip7を述べるメッセージ。実測結果の報告ではない。',
 'eiqb':'方法aを同じ著者・論説へ帰属し、先の問いのコロンに続く第一項とする。',
 'eiqc':'著者が方法bのeip6を提示し、用いる時刻規則eingを第一節へ参照する。同じ棒に対する方法aとbの両値候補をLänge des Stabesと呼び得るという追加の許容を結ぶ。',
 'eiqd':'方法bの時計・距離の測定と長さの呼称の許容eiqcを述べるメッセージ。二方法の同値や相対性原理からの結論ではない。',
 'eiqe':'方法bを同じ著者・論説へ帰属し、方法aの後の第二項として保持する。二文と改頁を一つの方法の説明として扱う。',
}
LIMITS=[
 'u0030の方法a全243文字・207本文文字、u0031の方法b全420文字・353本文文字、M0048のtを対象とする。原刊895頁から896頁への改頁で方法bを分断しない。',
 '三者の同伴と静止は測定操作の間の巨視的な配置・物質点履歴について読む。生体の内部運動や物差しの微視的熱運動を禁止せず、測定時の位置を定める理想化された代表配置を用いる。棒の全物質点・全時刻の剛性と並進は保持する。',
 '移動側xlと静止側raの同じ長さ単位ta・時間単位rbを使うが、両系の時刻や同時性を等置しない。各系の全履歴はその系の時間区間で読む。方法aの長さを初期値yaと同じにする結論はu0032まで加えない。',
 '方法aのebenso, wie wennは同じ物差しを当てて直接読む手順の比較。比較側の静止の現実化、同じ値、法則全体の不変性をこの句から追加しない。',
 '方法bは同じ二端標識・出来事・静止系の場所・局所時計表示を結び、両端の値を同じxvへ固定する。遠隔受信の時刻や移動する棒の時計で代用しない。観測者自身が静止している条件は加えない。',
 '同じ物差しxjは方法aではxlに、方法bではraに静止する。ye/yfの別設定で評価し、両系へ同時に静止するとは主張しない。二地点間の距離を測る操作xhと棒への直接接触xd/xeを分ける。',
 '長軸の端面中心を二端として追跡し、形状の帰属はeislq、世界線と座標はse/sb、時刻はeingへ結ぶ。幾何学的標識は必ず物質点であるとは要求しない。',
 'ebenfallsとbezeichnen kannは方法bの値も棒の長さという呼称に含め得ることとして保持する。呼称を強制せず、方法間の値の一致・相違、値の存在・一意性や測定実行済みを語句だけから補わない。',
 '原文の操作はu0029で導入した思考上の考察範囲xyに属する。有限検査は依存群の引数、局所時計、指定時刻、測定行為、型付き引用、比較・呼称の役割を検査し、全実数履歴や物理的真理を証明しない。',
]


def interval(frame,c):return [k(n,frame,k('rb'),c) for n in ('eisls','eislt')]
def coords(body,frame,c):return [k('eislu',body,frame,k('ta'),k('rb'),k(role),c) for role in ('yn','yo','yp')]
def history(body,frame,c):return [body,frame,c,k('ta'),k('rb'),*interval(frame,c),'i[point a]['+k('eirh',body,v('point'),c)+']',*coords(body,frame,c)]
def axis(frame,c):return history(k('xi'),frame,c)+[k(n,k('xi'),frame,c) for n in ('eislv','eislw')]
def endpoints():return (('xn','xp','xr','xt','x2'),('xo','xq','xs','xu','x3'))


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c=v('context');frame=v('frame');val=v('value')
    text+=define('eipw',[('body','a'),('frame','a'),('context','d')],both(k('bg',*interval(frame,c)),k('eiah',*history(v('body'),frame,c))))
    text+=define('eipx',[('body','a'),('context','d')],k('eipf',*history(v('body'),k('ra'),c),k('yb')))
    speed=lambda role:k('eislc',k('ra'),k('xl'),k('ta'),k('rb'),k(role),c)
    text+=define('eipy',[('context','d')],both(k('eipk',c),*(k('eipx',k(b),c) for b in ('xj','xk')),*(k('eipw',k(b),k('xl'),c) for b in ('xi','xj','xk')),k('eioj',k('ra'),k('xl'),k('ta'),k('rb'),c),k('sca',speed('yn'),k('yb')),*(k('sca',speed(a),k('bb','n p a b')) for a in ('yo','yp'))))
    text+=define('eipz',[('value',R),('frame','a'),('context','d')],both(k('sbg',val),k('ti',k('ta')),k('sbe',k('xi'),k('xk'),k('xj'),frame,k('ta'),val,c,'p xa','p xb','p xc','p x4','p xd','p xe'),*(k('eipw',k(b),frame,c) for b in ('xi','xj','xk')),k('eipe',*axis(frame,c),val)))
    text+=define('eip2',[('value',R),('context','d')],both(k('sbi',val,c),k('eipy',c),k('eipz',val,k('xl'),c)))
    text+=define('eip3',[('value',R),('context','d')],k('eipz',val,k('ra'),c))
    clauses=[k('sbf',k('xi'),*[k(n) for n in ('xn','xo','xp','xq','xt','xu')],k('ra'),c,'p xf','p xg'),k('ba',k('xv')),k('lg',*interval(k('ra'),c),k('xv'))]
    for (p,e,clock,place,time),selector in zip(endpoints(),('eislv','eislw')):
        clauses.extend([op('e',k(p),k(selector,k('xi'),k('ra'),c)),k('eing',k(e),k(clock),k(place),k(time),c),k('sca',k(time),k('xv')),k('sb',k(p),k(e),k('ra'),c,k('ta'),k('rb'),k('xv'),*(app(app(fn,k(p)),k('xv')) for fn in coords(k('xi'),k('ra'),c)))])
    text+=define('eip4',[('context','d')],both(*clauses))
    observations=[k('eisl4',k('xk'),k(p),k(e),k(clock),k(place),k('ra'),k('rb'),k('xv'),c) for p,e,clock,place,_ in endpoints()]
    text+=define('eip5',[('context','d')],both(k('eipk',c),k('eip4',c),*observations))
    text+=define('eip6',[('value',R),('context','d')],both(k('sbk',val,c),k('eip5',c),k('eipw',k('xj'),k('ra'),c),k('eipa',k('xn'),k('xo'),k('xv'),*coords(k('xi'),k('ra'),c),val)))
    text+=content('eip7',both(k('xz',k('xw'),k('rd'),'r[p eip2]',k('xy'),v('point')),k('eisl3',k('xw'),k('rd'),'r[p eipz]',k('xl'),k('ra'),'r[p eip2]','r[p eip3]',k('xy'),k('eirf'),v('point'))))
    text+='d eiqa[] f[j s[k eip7[]]].\n'
    text+=define('eiqb',[],both(k('eir3',k('xw'),k('rd'),k('eirf'),quote('eiqa'),k('ri')),k('eiskj',k('xw'),k('y3'),'n p b b',k('eirf'),k('ri')),k('ue',k('y3'),k('xw'),k('ri')),op('u',op('e',k('y3'),k('xw')))))
    text+=content('eiqc',both(k('xz',k('xx'),k('rd'),'r[p eip6]',k('xy'),v('point')),k('eislp',k('xx'),k('rd'),k('eisdy'),'r[p eing]',k('eirf'),v('point')),k('eisl5',k('xx'),k('rd'),k('xi'),k('eisl6'),'l['+RULE+'][r[p eip2] r[p eip6]]',k('xy'),k('eirf'),v('point'))))
    text+='d eiqd[] f[j s[k eiqc[]]].\n'
    text+=define('eiqe',[],both(k('eir3',k('xx'),k('rd'),k('eirf'),quote('eiqd'),k('ri')),k('eiskj',k('xx'),k('y3'),'n p c b',k('eirf'),k('ri')),k('ue',k('xw'),k('xx'),k('ri')),op('u',op('e',k('xw'),k('xx')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eiqb','eiqe')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='comoving_direct_and_synchronized_endpoint_measurement_methods',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/rod-experiment-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisl6',role='designation',forms=[dict(text='Länge des Stabes',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
