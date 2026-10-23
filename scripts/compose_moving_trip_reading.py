"""Present the moving-clock trial, its two results and the local time gloss."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_trip_geometry import ROOT,read
from scripts.compose_carried_clock_synchrony import record_args
from scripts.compose_rod_methods import coords
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-moving-trip-geometry.noema';PARENT_BASIS='data/moving-trip-geometry-basis-v1.json'
FULL='examples/v014/einstein-moving-trip-reading.noema';CORE='examples/v014/moving-trip-reading-core.noema'
BASIS='data/moving-trip-reading-basis-v1.json';ANNOTATIONS='data/moving-trip-reading-identifiers-v1.json';INDICES=(261,262,263)
PRIMITIVES={
 'eismi':([('node','a'),('author','a'),('division','a'),('criterion','i[h['+R+' '+R+' '+R+'] c]'),('document','a'),('context','d')], 'authorがnodeで同じdocumentの先行divisionに提示されたcriterionを、現在の三指示値による同期判定の適用基準として参照する。閉じた三実数の関係型と参照先を固定し、節番号の類似や現在の判定成功だけで参照を代用しない。参照・適用は条件の成立を含意しない。'),
 'eismj':([('node','a'),('author','a'),('setting','i[e]'),('principle','i[e]'),('result','i[e]'),('scope','a'),('document','a'),('context','d')], 'authorがnodeで、scopeの同じsettingの下でprincipleを考慮してresultを得ると、現在の論証の結果として提示する。想定・原理・結果の向きと同じ論説を保持する。未来の予告、単なる可能性、無前提の実測報告へ替えない。著者の結果提示への帰属であり、処理系による原理の実証・導出の検証・必要性の法則や原理だけの十分性は含意しない。'),
 'eismk':([], '原刊896頁下部の著者注1)、固定原文u0280の注本文箇所。時間という語の現在の使用を説明する。'),
 'eisml':([], 'u0036の第二文冒頭Zur Zeitの直後、最初の出発時刻t_Aの前にある原刊896頁の著者注1)の付着箇所。注本文や全段落とは別の局所的な本文位置。'),
 'eismm':([], '注u0280の冒頭で引用されるZeitという呼称。現在の棒端時計と光試行における適用規則を合成側で指定する。'),
}
MEANINGS={
 'eito':'同じ棒と両時計の全区間の条件、三照合記録、共動観測者と判定適用、同じ光の出発・反射・帰着を結ぶ試行設定。光は同じ端点の三出来事に同じ座標で属し、二伝播区間は真空である。ここではVによる全直線軌道や二つの経過時間式を仮定に含めない。',
 'eitn':'eitoを既出の運動設定ydで想定する内容。光往復の出来事と観測者の条件は想定の内側であり、実験実施を報告しない。',
 'eitp':'同じ試行設定とeitkの全直線軌道・交点、単位校正、静止系測定eip6とsdbの二つの経過時間式を結ぶ結果内容。sdiで既出の同じ三記録の表示値と長さzavを結び、方法bへの設定継承を保持する。',
 'eitq':'同じ棒のどちらかの時計の照合記録について、その現在位置の局所静止時計と動く時計のeiq2を要求し、valueが局所時刻zahと自分の表示zagの両方に等しいという時刻呼称の適用規則。任意の別時計や別場所の表示を同じ時間と呼ばない。',
 'eitr':'この議論のZeitをeitqの同じ局所時刻かつ動く時計の表示として解釈する説明。第一節以来の静止系時間規約とeingへの対応をeiskuで保持し、時計の物理的静止や固有時への変更を追加しない。',
 'eits':'前の時計設定zalへ試行eitnをさらに加えて想定するug/zaoと、第一節の判定biへの明示参照を結ぶ提示。',
 'eitt':'同じ試行eitnの下で現行の光速度原理eiotを考慮し、二式とその物理的対応eitpを得るという著者の現在の結果提示。',
 'eitu':'追加の試行想定と第一節への参照eitsを述べるメッセージ。',
 'eitv':'二式を一緒に得るという結果提示eittを述べるメッセージ。式間のundはsdbの二条件の連言に保持する。',
 'eitw':'同じ時間の二つの局所的な読みeitrを説明する注のメッセージ。zugleichを別時刻の順序や二種類の時間の併存にはしない。',
 'eitx':'u0036の追加想定と試行を同じ著者・論説へ帰属し、直前の時計設定からの本文順序を保持する。',
 'eity':'u0036末尾から二式u0037〜u0039までの現在の結果提示を同じ著者・論説へ帰属し、試行の導入からの順序を保持する。',
 'eitz':'注u0280の説明を同じ著者・論説へ帰属し、Zur Zeitの局所的な付着箇所と注1)で結び、試行の時間の読みへの補足として保持する。原文インベントリ末尾の配置を本文順序にしない。',
}
LIMITS=[
 '原刊896/897頁のu0036〜u0039と、896頁下部の注u0280を共有文脈で読む。計476本文文字とM0054〜M0061。u0040冒頭のr_ABの説明は量の解釈に参照し、観測者別の判断を含むu0040全体の確認とはしない。',
 'Wir denken uns fernerとgehe/werde/gelangeは既存の棒と時計へ加える思考上の設定。時計ごとのそばの共動観測者は巨視的代表位置で読み、内部運動の凍結や数値の近接閾値を補わない。第一節の基準を適用することは判定が成功することではない。',
 '設定eitoは光・三出来事と端点での同所的な対応を保つ。一定光速による全直線軌道eitkと式sdbは原理を考慮して得る結果eitpの内側へ置き、結論の式を初めから設定として仮定しない。真空は同じ光速度原理の適用範囲として継承する。',
 'Aを正の進行方向の後端、Bを前端と読むのは往路V−vと復路V+vに即した今回の配置。時刻t_A、t_B、t_A′は同じ三記録のzag/zahであり、素数記号を微分・別系の時刻・出発時刻の反復へ替えない。',
 'r_ABは同じ運動棒を静止系で同時刻に測るeip6の値zav。初期静止長ya、移動側の長さ、往復光路全長とは同一視しない。yxは同じ運動状態を方法bの設定へ継承する既存の物理的対応。量の数値には同じ校正済み単位比を保つ。',
 '正のr_ABと0≤v<Vの下で商の式を(V−v)Δt=r_AB、(V+v)Δt=r_ABとして記述する。本文の運動はeipkの正のybを保持し、零速度は汎用数値定義の比較例に限る。除算の符号、二式の連言、任意の座標原点と出発時刻を保持する。',
 'Unter Berücksichtigung ... finden wirはこの想定における現在の結果提示である。旧zcの必然性や将来の予告へ替えず、現行eiotを参照する。有限代数検査は全物理法則の真理や論証全域の自動証明ではない。',
 '注のhierは現在の棒端時計と光試行での時間の使用。eitqは同じ場所・出来事の局所静止系時刻と動く時計の指示の両方に同じ値を結ぶ。三回の記録だけに適用範囲を縮めず、当該二時計の任意の適格記録を扱う。針位置は校正された表示値として読み、同じ周期の表示だけで出来事を同一視しない。',
 '既存eiq2/eiq4、完全な世界線、測定方法、光速度原理の意味規約と証拠を継承する。引用された想定・結果・規則を談話の検査で実行せず、全実数の時間・候補値域を有限標本へ変更しない。u0040以降と二作品全体は残る。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c=v('context');event=lambda rec:k('zad',k(rec));time=lambda rec:k('zah',k(rec))
    clauses=[k('eitm',c),k('eipk',c),k('eiq4',k('zaj'),k('xn'),c),k('eiq4',k('zak'),k('xo'),c),k('eisb5',k('zax'),k('ra'),c),k('sde',k('zax'),*(event(rec) for rec in ('zas','zat','zau')),k('ra'),'p cf','p cg','p ch')]
    for first,last in (('zas','zat'),('zat','zau')):clauses.append(k('eisca',k('zax'),event(first),event(last),k('ra'),c))
    for rec,end in (('zas','xn'),('zat','xo'),('zau','xn')):
        xyz=[app(app(f,k(end)),time(rec)) for f in coords(k('xi'),k('ra'),c)]
        clauses.append(k('sb',k('zax'),event(rec),k('ra'),c,k('ta'),k('rb'),time(rec),*xyz))
    text+=define('eito',[('context','d')],both(*clauses));text+=content('eitn',k('eito',k('yd')))
    text+=content('eitp',both(k('eito',k('yd')),k('eitk',k('yd')),k('eiscc',k('ra'),k('ta'),k('rb'),k('tb'),k('yd')),k('sdi',k('yd'),'p eip6','p sdb')))
    rec=v('record');val=v('value')
    comparisons=[both(k('zac',rec,k(clock),c),k('eiq2',k(clock),k(end),*record_args(rec),c)) for clock,end in (('zaj','xn'),('zak','xo'))]
    text+=define('eitq',[('record','a'),('value',R),('context','d')],both(k('ba',val),k('sca',val,k('zag',rec)),k('sca',val,k('zah',rec)),op('x',*comparisons)))
    text+=content('eitr',both(k('eislo',k('eismm'),'r[p eitq]',k('eirf'),v('point')),k('eisku',k('eisjd'),'r[p eing]',k('ra'),k('rb'),k('eirf'),v('point'))))
    text+=content('eits',both(k('ug',k('za2'),k('rd'),quote('eitn'),k('xy'),v('point')),k('zao',k('zal'),k('za2'),k('xy'),v('point')),k('eismi',k('za2'),k('rd'),k('eisdy'),'r[p bi]',k('eirf'),v('point'))))
    text+=content('eitt',k('eismj',k('za3'),k('rd'),quote('eitn'),quote('eiot'),quote('eitp'),k('xy'),k('eirf'),v('point')))
    for msg,body in (('eitu','eits'),('eitv','eitt'),('eitw','eitr')):text+='d '+msg+'[] f[j s['+k(body)+']].\n'
    for stmt,node,prior,msg in (('eitx','za2','zal','eitu'),('eity','za3','za2','eitv')):
        text+=define(stmt,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(msg),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    text+=define('eitz',[],both(k('eir3',k('eismk'),k('rd'),k('eirf'),quote('eitw'),k('ri')),k('eisfo',k('eisml'),k('eismk'),k('eirf'),'n p b b',k('ri')),op('u',op('e',k('eisml'),k('eismk'))),k('eisa5',k('eismk'),k('rd'),quote('eitn'),quote('eitr'),k('ri'))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==261;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eitx','eity','eitz')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='moving_trial_results_and_time_note_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/moving-trip-geometry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eismm',role='designation',forms=[dict(text='Zeit',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
