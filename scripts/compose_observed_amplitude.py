"""Compose frame-bound amplitude candidates, names and an attributed square ratio."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_doppler_specialization import ROOT,read,EXTENDED
from scripts.compose_wave_transform_application import transformed
from scripts.compose_aberration_presentation import allq
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-aberration-specialization.noema';PARENT_BASIS='data/aberration-specialization-basis-v1.json'
FULL='examples/v014/einstein-observed-amplitude.noema';CORE='examples/v014/observed-amplitude-core.noema'
BASIS='data/observed-amplitude-basis-v1.json';ANNOTATIONS='data/observed-amplitude-identifiers-v1.json';INDICES=[379,380]
AMP_NAMES=('ex','ey','ez','hx','hy','hz')
MAGNITUDE=[('magneticside','c')]+[(n,R) for n in AMP_NAMES]+[('amplitude',R)]
QUESTION=EXTENDED+[('magneticside','c')]
SETTING=QUESTION+[('amplitude',R),('newamplitude',R)]
VARIABLES=[(n,t) for n,t in SETTING if n not in ('frame','light','scope','context')]
NAME_WITNESSES=[(n,t) for n,t in QUESTION if n not in ('wave','frame','light','scope','context')]
code=lambda result:'i[h['+' '.join(t for n,t in QUESTION)+'] '+result+']'
TRUE=op('e','n p a b','n p a b')
PRIMITIVES={
 'eiss4':([('node','a'),('author','a'),('anchor','a'),('prior','i[e]'),('condition',code('c')),('question',code('g['+R+']')),('remaining','c'),('scope','a'),('context','d')],'authorがscopeのanchorから引き継ぐpriorの仮定について、nodeの段階でconditionの下にquestionの答えを求めることを論述上の課題として提示する。conditionとquestionは同じ型・順序の引数列を受ける閉じた規則で、固定した一割当を候補の外側で共有する。remainingが真なら、先行の同じ検討を踏まえてこの段階でなお取り扱うべき課題として位置付ける。数値を答えとする質問族への一般提示関係であり、具体的な物理対象・系・候補条件は規則で構成する。答えの存在・唯一性・既知性・発見済み、調査や測定の実施済み、著者以外の共同主体、仮定の現実成立、引用の自動評価を要求しない。'),
 'eiss5':([], 'u0197の残る振幅の探索課題、AとA′の命名、二系での測定の役割と結果の導入を述べる箇所。'),
 'eiss6':([], 'u0198=M0345の二乗振幅比の表示箇所。原刊912頁では分母に根号がなく、保存電子在庫との差は別の照合記録で保持する。'),
 'eiss7':([], 'u0197で静止系の同じ波の選んだ電気側又は磁気側の振幅を指すAという表記個体。'),
 'eista':([], 'u0197で移動系の同じ波の同じ側の振幅を指すA′という表記個体。'),
}
MEANINGS={
 'ekhz':'magneticsideが偽なら同じ電気三係数、真なら同じ磁気三係数についてsealで非負の振幅を定める。二乗値だけで負の振幅を認めず、両側の値が等しいことを前提にしない。',
 'ekia':'同じ六係数と同じspeed,Vの成分変換を使い、同じ側を旧振幅amplitudeと新振幅newamplitudeの両方へ渡す。単に二乗比を満たす二値を選ぶ構成ではない。',
 'ekib':'先行の同じ60設定eketに、選んだ側の旧新の非負振幅ekiaを結ぶ。波・源・過程・観測者・二系・単位・位相・近似・用途上の十分性を共有する。測定とは各系で校正された同じ電気力又は磁気力の単位で、この局所波形の振幅を評価する理想化した読みで、厳密な実測記録を追加しない。横波のseaj又は印刷された二乗比を新前件に含めない。',
 'ekic':'同じ61設定を固定し、移動系の同じ変換後三係数と同じ側の非負の大きさを候補valueへ結ぶ。候補ごとに波・場・単位・系・側を選び直さない。',
 'ekid':'同じ61設定の下でekicを満たす実数値を答えとする質問。質問を作ることは候補の全探索や答えの存在・一意性・既知性の主張ではない。',
 'ekie':'質問族の同じ61設定の許容条件。先行eketの物理的・数学的・近似の設定を保ち、側の選択と質問本体に同じ引数列を使う。',
 'ekif':'同じwave=objectとvalueについて、K・V・節・状況を固定し、同じ旧係数の選んだ側の非負振幅として解釈できる56設定証人を取るAの表記規則。物理的な設定と候補値で証人を分けない。',
 'ekig':'同じwave=objectとvalueについて、同じ56証人から移動系の変換後の同じ側の振幅候補ekicへ結ぶA′の表記規則。独立した波の係数又は新しい単位を選ばない。',
 'ekih':'Aを旧系のekif、A′を新系のekigへそれぞれ結ぶ命名規約。二つの名の役割を分け、実際の比の主張では同じ63設定を使って側と対象を共有する。',
 'ekii':'A²*(1−(v/V)*cosφ)²/(1−(v/V)²)を同じ実数量で構成する。原刊の平方根のない分母を保持し、二乗振幅と振幅そのものを同じ値にしない。',
 'ekij':'同じ新振幅の二乗が同じ旧振幅・V・speed・旧角余弦のekiiに等しいという表示帰結。物理的適用条件や真理の証明をこの等式自体へ混ぜない。',
 'ekik':'同じ59役割を全称量化し、同じ校正と近似と振幅条件ekibなら同じ二乗比ekijと述べる表示内容。magneticsideを前件と帰結で共有し、片側だけの式にしない。',
 'ekim':'同じ59全称役割とekibの下で、同じ六係数が既存sdz2の成分変換へ結ばれるという先行の式の内容。表示の二乗比を導出済みと先取りしない。',
 'ekin':'先行の同じ波の問いeissfと仮定ekbnを受け、同じ条件ekieと質問ekidの族を、この段階でなお求める課題として著者へ帰属する。現在の読者の時刻や実際の実験の依頼にしない。',
 'ekio':'残る課題ekinと二つの命名ekihを保ち、先行成分表示ekcoを同じ設定のekimとして明示し、そこから二乗比ekikを得るという著者の帰結提示とコロンを接続する。',
 'ekip':'u0197の探索・命名・測定の読み・帰結提示ekioを述べるメッセージ。',
 'ekiq':'u0197全文を同じ著者・論説へ帰属し、光行差の特殊形に続ける。',
 'ekir':'u0198の表示箇所を、同じ59全称と選んだ同じ側の条件付き二乗比ekikへ結ぶ。',
 'ekis':'u0198の表示対応ekirを述べるメッセージ。',
 'ekit':'u0198の表示を同じ著者・論説へ帰属し、u0197のコロンの後に置く。',
}
LIMITS=[
 'u0197–u0198を原刊912頁へ照合する。M0343=A、M0344=A′、M0345はA′²=A²(1−(v/V)cosφ)²/(1−(v/V)²)。電子在庫の外側分母の根号との差はdata/wave-amplitudes-facsimile-v1.jsonの既存判断に従い明記し、元の在庫を変更しない。',
 '振幅は先行の同じ局所的な正弦波形の三成分係数の非負の大きさと読む。gemessenは同じ各系で校正された電気力又は磁気力の単位によって評価するという理想化した量の意味であり、測定装置を使い終えた特定の観測記録の存在は補わない。電気側と磁気側の単位は先行ejsnの別役割を保持する。',
 '既存eketの校正された物理場、同じ源・波・過程・観測者、成分変換、全局所領域の近似と用途上の十分性を引き継ぐ。近似場の係数が実際の場の厳密な振幅記録と等しいとは主張しない。許容する全設定への条件付きの著者主張であり、測定誤差の一般推定理論を導入したことにはしない。',
 'oderは同じ一つの側を旧新で共有する選択として構成する。電気振幅と磁気振幅の等値は定義へ含めず、それぞれ同じ側について二乗比を述べる。既存seajの横波条件からの代数的な支持は再使用できるが、原文に書かれない横波条件を無説明に前件へ加えない。真空の微分方程式からその条件を導く証明は、著者の式を記述することとは別である。',
 'nun nochは同じ波の性質について先行の周期数・方向の検討を踏まえ、この段階でなお振幅を求める課題と読む。Wirは同じ論述主体の著者へ帰属する。答えを既に発見したという前提や共同著者を補わない。Nennt manの命名とso erhält manの帰結提示、コロンを別に保持する。',
 '著者に帰属させる二乗比は、引用だけでは真理評価しない。正弦の係数だけなら非横波の反例があり得ることも記録する。全実数・全関数の域を有限標本へ縮めず、局所検査と原文の意味判断を区別する。',
]

def selected(side,amps,value):return k('ekhz',side,*amps,value)

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    side=v('magneticside');amp=v('amplitude');newamp=v('newamplitude');old=[v(n) for n in AMP_NAMES];V=v('light');speed=v('speed');new=transformed(speed)[0]
    text+=define('ekhz',MAGNITUDE,both(op('y',op('u',side),k('seal',*old[:3],amp)),op('y',side,k('seal',*old[3:],amp))))
    text+=define('ekia',SETTING,both(selected(side,old,amp),selected(side,new,newamp)))
    text+=define('ekib',SETTING,both(k('eket',*args(EXTENDED)),k('ekia',*args(SETTING))))
    text+=define('ekic',QUESTION+[('value',R)],both(k('eket',*args(EXTENDED)),selected(side,new,v('value'))))
    text+=define('ekid',QUESTION,'j v[i[value '+R+']['+k('ekic',*args(QUESTION),v('value'))+']]', 'g['+R+']')
    text+=define('ekie',QUESTION,k('eket',*args(EXTENDED)))
    fixed={'wave':v('object'),'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('context')}
    oldrule=both(k('ekie',*[fixed.get(n,v(n)) for n,t in QUESTION]),selected(side,old,v('value')))
    newrule=k('ekic',*[fixed.get(n,v(n)) for n,t in QUESTION],v('value'))
    for name,body in [('ekif',oldrule),('ekig',newrule)]:text+=define(name,[('object','a'),('value',R),('context','d')],allq(NAME_WITNESSES,body,'g'))
    p=v('point');a=k('rd');scope=k('eisrx');node=k('eiss5');display=k('eiss6')
    text+=content('ekih',both(*(k('eislo',k(symbol),'r[p '+rule+']',k('eirf'),p) for symbol,rule in [('eiss7','ekif'),('eista','ekig')])))
    mul=lambda x,y:k('shv',x,y);sq=lambda x:mul(x,x);one=k('bb','n p b b');ratio=mul(speed,k('sjd',V))
    rhs=mul(sq(amp),mul(sq(k('bf',one,mul(ratio,v('anglecos')))),k('sjd',k('bf',one,sq(ratio)))))
    text+=define('ekii',[(n,R) for n in ('light','speed','anglecos','amplitude')],rhs,R)
    text+=define('ekij',SETTING,k('sca',sq(newamp),k('ekii',V,speed,v('anglecos'),amp)))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':scope,'context':p};actual=[fixed.get(n,v(n)) for n,t in SETTING]
    prior=k('sdz2',k('tc'),speed,*old,*transformed(speed)[0]).replace(v('light'),k('tc'))
    for name,result in [('ekik',k('ekij',*actual)),('ekim',prior)]:text+=content(name,allq(VARIABLES,op('y',k('ekib',*actual),result)))
    text+=content('ekin',k('eiss4',node,a,k('eissf'),quote('ekbn'),'r[p ekie]','r[p ekid]',TRUE,scope,p))
    text+=content('ekio',both(evaluate('ekin'),evaluate('ekih'),k('eissb',node,k('eissj'),a,quote('ekco'),quote('ekim'),scope,p),k('zc',node,a,quote('ekim'),quote('ekik'),scope,p),k('uf',a,node,display,p),k('ue',node,display,p)))
    text+=content('ekir',k('eisox',display,quote('ekik'),p))
    for shown,msg,stmt,item,previous in [('ekio','ekip','ekiq','eiss5','eiss2'),('ekir','ekis','ekit','eiss6','eiss5')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(item),a,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==379
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekiq','ekit')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_wave_calibrated_amplitude_inquiry_names_and_square_ratio',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/aberration-specialization-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for n,text in [('eiss7','A'),('eista','A′')]:ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=text,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
