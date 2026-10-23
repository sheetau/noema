"""Carry endpoint clocks through every local rest-time comparison in the interval."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rod_methods import ROOT,read,coords,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-kinematic-replacement.noema';PARENT_BASIS='data/kinematic-replacement-basis-v1.json'
FULL='examples/v014/einstein-carried-clock-synchrony.noema';CORE='examples/v014/carried-clock-synchrony-core.noema'
BASIS='data/carried-clock-synchrony-basis-v1.json';ANNOTATIONS='data/carried-clock-synchrony-identifiers-v1.json';INDICES=(260,)
LOCAL=[(n,'a') for n in ('clock','endpoint','event','place','localclock')]+[('own',R),('local',R),('context','d')]
PRIMITIVES={
 'eismc':([('node','a'),('author','a'),('designation','a'),('qualification','i[h[a d] c]'),('subjects','j[a]'),('frame','a'),('scope','a'),('document','a'),('context','d')], 'authorがnodeで、scopeの想定に属するsubjectsを、frameに関してqualificationを満たすものとしてdesignationで呼ぶ。対象の列・条件記述・基準系と呼称の対応を保持する適用であり、想定を現実の事実へ変えない。列外の対象への適用や他系における同じ条件の成立は要求しない。'),
 'eismd':([], 'u0035末尾のsynchron im ruhenden Systemという引用呼称。時計の静止自体ではなく、指定系における同期の資格を合成で与える。'),
 'eisme':([('node','a'),('author','a'),('target','i[e]'),('gloss','i[e]'),('document','a'),('context','d')], 'authorがnodeでtargetの言い方の内容・適用条件を、同じdocumentのglossによってすなわちという説明として明確化する。説明の向き・同じ対象と想定を保ち、無関係な代案や時間的順序へ替えない。引用した内容の現実の成立や、全文脈での論理的同値の証明は含意しない。'),
 'eismf':([], 'u0035で同じ棒の第一端を指すために導入するAという識別呼称。端点との対応は命名関係で結ぶ。'),
 'eismg':([], 'u0035で同じ棒の第二端を指すために導入するBという識別呼称。端点との対応は命名関係で結ぶ。'),
}
MEANINGS={
 'eiqz':'同じ時計・棒端・設定についてcaとzaaの取り付け、xfの棒端所属を保ち、時計の位置を代表する基準点とその端点に同じ全時間区間・三座標のseを要求する。時計の針や内部部品全体の静止ではなく、取り付け位置が棒端に伴うことを表す。',
 'eiq2':'旧scvの同じ時計・端点・出来事・現在位置・局所時計と二表示値を、eingによる第一節の局所時刻へ接続する。両表示出来事の同所的対応、同じ時刻の端点と時計のsbを保持する。動く時計へ静止系のccを課さない。',
 'eiq3':'同じ時計・端点・設定の指定区間内時刻に、その時刻の局所時刻値を持つ照合記録が少なくとも一つ存在し、eiq2を満たす。任意の別時点の記録で時間区間の欠けを埋めない。',
 'eiq4':'eiqzの全区間の取り付け位置と、非空かつ完全な照合記録範囲zaiを保つ。全記録にeiq2を要求し、さらに区間内の全実時刻にeiq3の証人を要求する。少数記録や一回の表示一致で同期を完成扱いしない。',
 'eiq5':'同じ棒のある端点に対してeiq4を満たす時計の条件。現在位置の静止系時刻を全区間で表示するという資格であり、動く系の二時計に光往復中点条件を適用した結果ではない。',
 'eiq6':'同じydの運動する剛体棒eipkと、指定軸両端xn/xoに付けた異なるzaj/zakにそれぞれeiq4を要求する追加の思考設定の内容。各時計の現在位置に静止する局所時計は時刻ごとに変わり得る。',
 'eiq7':'著者がeiq5の条件を静止系において同期した時計の規約としてzanで示し、同じ想定の二時計を同じ引用呼称eismdで呼ぶ。想定外の時計や動く系への呼称の適用を追加しない。',
 'eita':'著者がeiq6を同じ棒の先行設定へ追加して想定する。A/Bの二呼称、第一節の静止系時間規約とeingへの対応、d. h.の説明、eiq6を理由としてeiq7の呼称を適用するalsoを保持する。物理的想定を本文文脈で実行しない。',
 'eitb':'棒端時計の追加想定・局所時刻による説明・同期呼称の適用eitaを述べるメッセージ。実験の実施報告や時計の自然な進み方の法則ではない。',
 'eitc':'u0035全体を同じ著者・論説へ帰属し、通常の運動学の仮定zvから現在の追加設定zalへの順序を保持する。',
}
LIMITS=[
 '原刊896頁のu0035全321文字・257本文文字とM0052のA・M0053のBを対象とする。A/Bは呼称個体eismf/eismgから既出の端点xn/xoへ結び、端点本体を呼称の文字列と同一視しない。',
 '時計の取り付けzaaは同じ棒端に伴う固定した物理的接続という入力であり、同じ座標が偶然一致するだけでは代用しない。ここではその位置を代表する時計の基準点と端点を全区間の同じseへ接続する。時計の歯車・針・内部運動を停止させる条件は課さない。',
 '動く時計は局所比較の出来事ごとにzabで現在位置を持つ。静止系の時刻はその同じ場所に静止する別の局所時計のeingで与え、共通参照rc・単位rb・同期qoを保持する。動く時計自身とrcへ直接qoを適用して静止を要求しない。',
 '両時計の表示は同じ局所出来事に対応し、数値はscaで一致する。端点と時計の出来事を同じ座標時刻・三位置へsbで結び、別周期の同じ表示や遠隔で信号を受けた時刻では代用しない。',
 'zacの全照合記録とzaiの完全性規約を保った上で、同じ運動区間内の全実時刻に対応記録の存在を明示する。現在位置や局所時計は記録ごとに変えてよく、一個の固定場所に動く時計を据えた条件にはしない。',
 '補正機構や時計の自然な固有時進行をこの文は説明していない。表示が静止系時刻に合うという思考上の設定を記述し、補正なしの実機が自然にそう動くという法則を追加しない。',
 'Wir denken uns fernerは同じ棒の設定へ更に条件を加える著者の想定である。d. h.は同期の呼び方を局所時刻との一致で説明する提示、alsoはその条件を理由とした同じ二時計への呼称適用として保持する。物理的な導出完了や実測済みではない。',
 '引用されたZeit des ruhenden Systemsは既に命名した時間規約eisjdで、その時刻付与規則eing・系ra・単位rbをeiskuで保持する。synchron im ruhenden Systemを時計が静止することや動く系での同期と混同しない。',
 '有限検査は局所表示・全時刻への記録の結合・代表点の世界線・引用の役割を調べる。全実数時刻の列挙や物理的実在、意味同値の自動証明とはしない。u0036の共動観測者と光往復は別の後続単位である。',
]


def record_args(record):return [k(n,record) for n in ('zad','zae','zaf','zag','zah')]
def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    clock=v('clock');end=v('endpoint');ctx=v('context');frame=k('ra')
    xyz=[app(f,end) for f in coords(k('xi'),frame,ctx)]
    text+=define('eiqz',[('clock','a'),('endpoint','a'),('context','d')],both(k('ca',clock),k('zaa',clock,end,k('xi'),ctx),k('xf',end,k('xi'),frame,ctx),*(k('se',obj,frame,ctx,k('ta'),k('rb'),*interval(frame,ctx),*xyz) for obj in (clock,end))))
    display=q('g','display','a',both(k('zbd',v('display')),k('cb',v('display'),v('place'),frame),k('eisgm',v('event'),v('display'),clock,frame,ctx),k('ce',clock,v('display'),frame,k('rb'),v('own'))))
    localxyz=[app(f,v('local')) for f in xyz]
    text+=define('eiq2',LOCAL,both(k('scv',*(v(n) for n,_ in LOCAL),'p qo','p sca','p ba'),k('lg',*interval(frame,ctx),v('local')),k('eing',v('event'),v('localclock'),v('place'),v('local'),ctx),display,*(k('sb',obj,v('event'),frame,ctx,k('ta'),k('rb'),v('local'),*localxyz) for obj in (clock,end))))
    rec=v('record');selected=k('zac',rec,clock,ctx);check=k('eiq2',clock,end,*record_args(rec),ctx)
    text+=define('eiq3',[('clock','a'),('endpoint','a'),('time',R),('context','d')],both(k('lg',*interval(frame,ctx),v('time')),q('g','record','a',both(selected,k('sca',k('zah',rec),v('time')),check))))
    text+=define('eiq4',[('clock','a'),('endpoint','a'),('context','d')],both(k('eiqz',clock,end,ctx),k('zai',clock,frame,ctx),q('g','record','a',selected),q('f','record','a',op('y',selected,check)),q('f','time',R,op('y',k('lg',*interval(frame,ctx),v('time')),k('eiq3',clock,end,v('time'),ctx)))))
    text+=define('eiq5',[('clock','a'),('context','d')],q('g','endpoint','a',k('eiq4',clock,end,ctx)))
    clauses=[k('eipk',k('yd')),op('u',op('e',k('xn'),k('xo'))),op('u',op('e',k('zaj'),k('zak')))]
    for ck,endpoint,selector in (('zaj','xn','eislv'),('zak','xo','eislw')):clauses.extend([op('e',k(endpoint),k(selector,k('xi'),frame,k('yd'))),k('eiq4',k(ck),k(endpoint),k('yd'))])
    text+=content('eiq6',both(*clauses))
    text+=content('eiq7',both(k('zan',k('zam'),k('rd'),'r[p eiq5]',frame,k('xy'),v('point')),k('eismc',k('zam'),k('rd'),k('eismd'),'r[p eiq5]','l[a][k zaj[] k zak[]]',frame,k('xy'),k('eirf'),v('point'))))
    clauses=[k('ug',k('zal'),k('rd'),quote('eiq6'),k('xy'),v('point')),k('zao',k('y2'),k('zal'),k('xy'),v('point')),'t[k eiq7[]][v point]',k('eisku',k('eisjd'),'r[p eing]',frame,k('rb'),k('eirf'),v('point')),k('eisme',k('zal'),k('rd'),quote('eiq7'),quote('eiq6'),k('eirf'),v('point')),k('eisdk',k('eirf'),quote('eiq6'),quote('eiq7'),v('point'))]
    for designation,endpoint in (('eismf','xn'),('eismg','xo')):clauses.append(k('eisd4',k('zal'),k('rd'),k(designation),k(endpoint),k('eirf'),v('point')))
    text+=content('eita',both(*clauses));text+='d eitb[] f[j s[k eita[]]].\n'
    text+=define('eitc',[],both(k('eir3',k('zal'),k('rd'),k('eirf'),quote('eitb'),k('ri')),k('ue',k('zv'),k('zal'),k('ri')),op('u',op('e',k('zv'),k('zal')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eitc',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='carried_endpoint_clocks_and_complete_local_rest_time_correspondence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/kinematic-replacement-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for n,form in (('eismd','synchron im ruhenden System'),('eismf','A'),('eismg','B')):ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
