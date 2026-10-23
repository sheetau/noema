"""Connect the expanded tau arguments to the same measured light roundtrip."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_axial_time_condition import ROOT,read
from scripts.compose_comoving_labels import TAU
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-axial-time-condition.noema';PARENT_BASIS='data/axial-time-condition-basis-v1.json'
FULL='examples/v014/einstein-light-time-expansion.noema';CORE='examples/v014/light-time-expansion-core.noema'
BASIS='data/light-time-expansion-basis-v1.json';ANNOTATIONS='data/light-time-expansion-identifiers-v1.json';INDEX=279
MEANINGS={
 'ei2k':'同じ出来事のK四座標から作る補助値eiz5に加え、同じ組のy,zが零であることを要求する。後続表示式の軸上座標規約であり、先行u0049の一般設定を改変しない。',
 'ei2l':'同じ試行の出発・反射・帰着に対して、zdzのK座標候補を現在のeiyxへ結ぶei2kを使い、補助値0,x′,0とy=z=0を明示する。正のx′と既出v>0、v<Vを要求する。出発のK時刻tを零にしない。',
 'ei2m':'同じ静止系の光速度原理の全適用範囲に属する指定区間・光・両端出来事・幾何学的光路長・単位をeifw/eiorへ結び、全軸経路と、両端の現在の局所表示・一意な時刻・系内時点を保持する。区間のwo/wpと同じ出来事のK座標時刻sjhを等値にし、指定経路長をwqへ結ぶ。',
 'ei2n':'同じ二端点・光・三出来事にeitiの完全な直線往復履歴と出会いを適用し、Kの実際の出発位置、端点間隔x′、共通光速V、既出速度vと同じ三時刻を渡す。往路・復路をそれぞれei2mの実際の区間へ結び、正の光路長を向きを保った端点差へ接続する。',
 'ei2o':'同じ四引数τ候補について、現在の全時計指示との過不足ない一致eizzと、同じ試行の0,x′,0・零横成分・三つの実際のK時刻における関数値がk時計の三読取りに一致するsjkを合わせる。旧sioや別の関数へ戻さない。',
 'ei2p':'先行する同じ軸方向往復ei2bを保持し、表示式の原点・正方向規約、現在のK配備時計、静止系の全真空光速度原理eios、全往復履歴と両光路、同じτ候補の全指示対応を結ぶ。この書換えを読むための同じ思考設定であり、具体的なτ解の発見を意味しない。',
 'ei2q':'τの引数を明示して静止系光速度一定を適用する、同じ前提ei2pの内容。',
 'ei2r':'同じτ候補zd4、補助値x′、光速V、速度v、実際の出発時刻tを既存sjgへ渡す展開済み中点式の内容。M0100の左辺とM0101の等号・右辺を一つの等値条件にする。',
 'ei2s':'同じ前提ei2qの下で、直前の中点式ei2dを展開式ei2rへ同値な形として書き換えるという著者の提示。oderと、引数の付加・静止系光速度原理の適用を一つの条件付き書換えへ結び、導出の自動証明とはしない。',
 'ei2t':'τの引数展開と光速度原理の適用による書換えei2sを述べるメッセージ。',
 'ei2u':'u0051–u0053にまたがる同じ文と表示式を、同じ著者・論説に帰属し、直前の中点式の必要性からの本文順序を保持する。',
}
LIMITS=[
 'u0051全142文字・116本文文字と、数式だけのu0052 M0100・u0053 M0101を一つの文と表示式として扱う。oder、τの四引数を付すこと、静止系の光速度原理の適用、左辺の半和と右辺を保持する。',
 '表示式に現れる0,x′,0およびy=z=0を、この縦方向の試行で採る座標規約として明示する。k原点の補助座標x-vtが零となるよう原点を選ぶ読みであり、両原点が全時刻で一致すること、出発時刻t=0、t=τ、x′=ξは追加しない。先行u0049では未指定だった零を遡及して強制しない。',
 '正の縦方向へ進む非退化な往復としてx′>0、既出v>0、v<Vを保つ。二分母V-vとV+vは正となり、二つの商を正の経過時間と解釈する。負の補助座標を許す先行の抽象往復に、この向きの経過時間式を無条件に適用しない。',
 '各K四座標は同じ出来事の現在のeiyxから得る。zdzの取得だけで座標の有効性を認めず、同じ組のx,tからx-vtを作る。候補τは現在の全対応と全k時計指示へ結ぶeizzを満たすという前提の下で用い、具体形や解の発見済みは補わない。',
 'eitiで両端点の同じ等速履歴、往路・復路の完全な光の履歴、同じ三出来事での出会いと真空・反射を保持する。Kの出発位置は同じ座標組のxであり、数値零へ置き換えない。端点差だけから光の全経路を推定しない。',
 '全真空伝播区間と全部分区間に同じVを与える既存eiosを静止系で適用する。両選択区間をその範囲eiscdへ含め、光・放出元・出来事・校正・幾何学的弧長をeifw/eiorへ結ぶ。Kの局所時計をkの動く時計へ交換せず、現在の表示対応eiyg/eiyi/eiyjも保持する。',
 '三関数値はτ(0,0,0,t)、τ(x′,0,0,t+x′/(V-v))、τ(0,0,0,t+x′/(V-v)+x′/(V+v))である。中点式の左辺は第一と第三の半和、右辺は第二であり、反射・帰着や二分母を交換しない。同じ関数の同じ時点に値を結ぶ。',
 '書換えの帰属zd3は著者が同じ前提の下で同値な形として提示する関係である。全実数上の逆数の一般法則や現実の光速度原理の実証を、この通読判断が証明したとはしない。旧数値核・有理代数の証拠は保存する。u0054以降の無限小・微分や具体的τ変換式はまだ記述しない。',
]

def definitions():
    e=v('event');t=v('tuple');label=v('label');ctx=v('context');rest=k('ra');lu=k('ta');tu=k('rb');zero=k('bb','n p a b')
    text=define('ei2k',[('event','a'),('tuple','a'),('label',R),('context','d')],both(k('eiz5',e,t,label,ctx),*(k('sca',k('zc6',t,k(a)),zero) for a in ('yo','yp'))))
    trial=k('zdq');events=[k(n,trial) for n in ('qe','qf','qg')];ray=k('qh',trial)
    locations=(zero,k('zdt'),zero)
    text+=define('ei2l',[('context','d')],both(k('sbg',k('zdt')),k('sbg',k('zb7')),k('ba',k('tc')),k('bg',k('zb7'),k('tc')),*(k('ei2k',event,k('zdz',event,rest,ctx),value,ctx) for event,value in zip(events,locations))))
    seg=v('segment');first=v('first');last=v('last');r=v('ray');axis=k('zbo',rest,k('yn'),ctx);at=lambda n:k(n,seg)
    parts=[k('eiscd',seg,rest,lu,tu,ctx),k('eifw',seg,rest,k('rc'),k('tc'),ctx),k('eior',seg,ctx),op('e',at('wf'),r),op('e',at('wi'),first),op('e',at('wj'),last),k('zbw',rest,axis,k('yn'),ctx),k('zdw',r,first,last,axis,rest,ctx),k('sca',at('wq'),v('path'))]
    for event,cl,place,val in ((first,'wk','wm','wo'),(last,'wl','wn','wp')):
        parts.extend([k('eiyg',event,at(cl),at(place),rest,at(val),ctx),k('eiyi',event,at(place),rest,ctx),k('eiyj',event,rest,ctx),k('sca',at(val),k('zbe',event,rest,tu,ctx)),k('sca',at(val),k('sjh',event,ctx))])
    text+=define('ei2m',[(n,'a') for n in ('segment','ray','first','last')]+[('path',R),('context','d')],both(*parts))
    times=[k('sjh',event,ctx) for event in events];xs=[k('sji',event,ctx) for event in events]
    geometry=k('eiti',k('qc',trial),k('qd',trial),ray,*events,rest,ctx,lu,tu,xs[0],k('zdt'),k('tc'),k('zb7'),*times)
    text+=define('ei2n',[('context','d')],both(geometry,k('ei2m',k('zdx'),ray,events[0],events[1],k('bf',xs[1],xs[0]),ctx),k('ei2m',k('zdy'),ray,events[1],events[2],k('bf',xs[1],xs[2]),ctx)))
    text+=define('ei2o',[('function',TAU)],both(k('eizz',v('function')),k('sjk',v('function'),k('zb6'))))
    text+=define('ei2p',[],both(k('ei2b'),k('ei2l',k('zb6')),k('eios',k('tc'),k('zb6')),k('eiyf',rest,k('zb6')),k('ei2n',k('zb6')),k('ei2o',k('zd4'))))
    text+=content('ei2q',k('ei2p'))
    text+=content('ei2r',k('sjg',k('zd4'),k('zdt'),k('tc'),k('zb7'),k('sjh',events[0],k('zb6'))))
    text+=content('ei2s',k('zd3',k('zd2'),k('rd'),quote('ei2q'),quote('ei2d'),quote('ei2r'),k('eisms'),v('point')))
    text+='d ei2t[] f[j s[k ei2s[]]].\n'
    text+=define('ei2u',[],both(k('eir3',k('zd2'),k('rd'),k('eirf'),quote('ei2t'),k('ri')),k('ue',k('zdv'),k('zd2'),k('ri')),op('u',op('e',k('zdv'),k('zd2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ei2u',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_trial_tau_argument_expansion_under_light_principle',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/axial-time-condition-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
