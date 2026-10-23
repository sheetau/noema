"""Complete the assumed curve extension and the equatorial/polar rate comparison."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_curved_clock_records import ROOT,read,CURVE,COMPARE,all_cases,PHI
from scripts.compose_clock_transfer_records import stamp,sub,mul,eq,path
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-curved-clock-records.noema';PARENT_BASIS='data/curved-clock-records-basis-v1.json'
FULL='examples/v014/einstein-curve-earth-claim.noema';CORE='examples/v014/curve-earth-claim-core.noema'
BASIS='data/curve-earth-claim-basis-v1.json';ANNOTATIONS='data/curve-earth-claim-identifiers-v1.json';INDICES=(347,348,349)
PROFILE=[('clock','a'),('readings',PHI),('context','d')]
MEAN=[('readings',PHI),('lower',R),('upper',R),('rate',R)]
SLOW=[('firstreading',PHI),('secondreading',PHI),('lower',R),('upper',R),('scope','a'),('context','d')]
PAIR=[(n,'a') for n in ('first','second','firstplace','secondplace')]
OBSERVED=PAIR+[('firstreading',PHI),('secondreading',PHI),('context','d')]
WINDOW=OBSERVED[:-1]+[('lower',R),('upper',R)]+OBSERVED[-1:]
DURATION_RULE='h['+' '.join(s for _,s in CURVE)+' '+R+'] c'
PRIMITIVES={
 'eisol':([('subject','e'),('reference','d'),('candidate','d')],'同じ内容と基準状況について、先行の議論と比較の前提を保って物理的帰結を評価する許容候補状況。候補は内容の真偽を調べる前に定め、後件が成立するものだけを選ばない。全論理的可能世界や規範的な許可とは区別する一般的な推論範囲の入力。候補の非空性と基準状況の包含、全候補での成立は利用側で要求する。'),
 'eisom':([], '固定原文einstein-1905:u0128のM0239/M0241で、同じ閉曲線を帰還する所要時間を秒で表すtの識別表記。ejltの同じ経路の規則へ結び、絶対座標時刻や文字盤の指示値と区別する。'),
 'eison':([('designation','a'),('rule','i['+DURATION_RULE+']'),('text','a'),('context','d')],'指定された表記を、同じ文章・提示文脈の型付き量の規則へ結ぶ識別関係。既存eisloと同じ記号解釈の関係を、経路の全引数と秒数を共有する規則の型で用いる。語形の一致だけから物理量の同一性や規則の真理を認定しない。'),
}
MEANINGS={
 'ejlz':'同じK閉区間全体の時計の現在表示を、実時刻から指示を得る一つの関数へ結ぶ。完全な代表軌跡・校正、全現在候補の同じ指示、全実時刻での表示存在を要求する。一定率や平方根の答え、他の時計との同期は含めない。',
 'ejma':'同じ指示関数の前後二時刻について、正の平均歩度と正のK時間差の積が実際の指示差に等しい。両指示と両時刻の有効性を保ち、文字盤の原点を率に含めず、零時間の割算を使わない。',
 'ejmb':'共通の正の比較時間区間で、二つの現在指示関数から求めた正の平均歩度が存在し、第一が第二より小さく、同じ差・参照率・比較範囲が非常に小さいという程度基準を満たす。',
 'ejmc':'同じ地球の赤道と一方の極に固定された異なる二時計が、復元弾性の回転振動系を調速に用い、同じ構造・性状を持ち、その他の完全な比較条件が一致する。歩度の答えや初期同期を前件へ追加しない。',
 'ejmd':'同じ地球時計の設定ejmcに、二時計の全期間の現在指示関数ejlzを結ぶ観測設定。離れた二時計を同じ出来事や場所へ同定せず、同じK尺度と時間区間で比較する。',
 'ejme':'ejmdが成立し、二時刻が同じK期間内で厳密に前後するなら、その同じ二時計の指示関数についてejmbのごく小さい歩度差が成立するという条件付き関係。',
 'ejmf':'任意の同じ二時計・場所・現在指示関数と、同じ比較期間内の任意の正の時間幅についてejmeを述べる内容。langsamer laufenを比較期間にわたる歩度の遅さとして読む。',
 'ejmg':'一様回転の地球という明示した背景の下、基準設定自身を含む非空の許容候補全てで同じ地球時計の比較内容ejmfが成立するという推論上の必要性。mußを義務や処理系の物理的証明としない。',
 'ejmh':'同じ閉曲線の設定を満たす全ケースで、ejluの全期間指示法則を採る補足のモデル内容。原文の前件を狭めず、厳密率と近似残差を用いるための発話外注記へ接続する。',
 'ejmi':'著者が現在の前段の折れ線結果の箇所zjbを証明済みとして扱い、その結果から曲線へ拡張する内容ejlxを同じ推論範囲zjdで仮定として採用する提示。',
 'ejmj':'同じ前段結果と拡張仮定ejlyから閉曲線の帰還結果ejlwが得られるという著者の帰結提示。仮定の後に置き、所要時間tを同じ経路引数の秒数規則ejltへ結ぶ。',
 'ejmk':'同じ閉曲線の帰還結果ejlwから、赤道と極の二時計についてejmgの必要性付き比較を著者が帰結として述べる提示。同所の帰還比較と離れた時計の歩度比較を区別する。',
 'ejml':'閉曲線の全期間法則ejmhを用いて同じ帰還結果ejlwを読む補足注記。著者の発話外に置き、著者が追加前提を全て明記したことや、その現実成立を補わない。',
 'ejmm':'u0128第一文の拡張仮定と前段の証明済みという位置付けejmiを述べるメッセージ。',
 'ejmn':'その仮定提示を同じ著者・論説へ帰属し、前段の折れ線での帰還zjcに続ける。',
 'ejmo':'同じ第一文の閉曲線の帰結と所要時間の説明ejmjを述べるメッセージ。',
 'ejmp':'閉曲線の帰結を同じ著者・論説へ帰属し、仮定の後に置く。補足の全期間法則ejmlはメッセージ外に併記する。',
 'ejmq':'u0128第二文の地球時計の必要性付き比較と先行帰結への接続ejmkを述べるメッセージ。',
 'ejmr':'第二文を同じ著者・論説へ帰属し、閉曲線の帰還結果の後に続ける。',
}
LIMITS=[
 'u0128の全二文552非空白本文文字と五数式要素を原刊904–905頁で照合する。曲線への仮定、前段の証明済みという位置付け、同じ推論範囲の帰結、初期同期・一定の速さ・閉曲線帰還・所要時間t・残る時計との差、地球時計の構造・その他同条件・赤道/極・程度・必要性を保持する。',
 '曲線は既存ejlpのC1位置と連続速度、端点での片側微分、共通の正の光速未満の速さで読む。前段の現在表示と全期間の初期同期/残留、同じ到着、秒換算と固定所要時間での近似留保を継承する。全実数・全関数の量化を有限標本へ替えない。',
 '前段の厳密率を近似残差の構成基準とする読みで、全期間の理想指示法則はejmh/ejmlの発話外注記に置く。著者が採る曲線への拡張仮定と、この読解上の補足を区別し、原文の前件ejlqを狭めない。',
 'Unruhuhrは、時計の機械的構成として、慣性体と復元弾性を持つ軸周りの往復回転系を歩度調整に用いる時計と読む。既存zjg/zjh/zjiを部分・振動作用・調速機能の意味入力として合成し、振り子時計や単なる任意の時計へ替えない。脱進機の設計や全力学の導出は本文の主張に追加しない。',
 '同じ構造・性状cdと、その他の選択条件全ての一致syjを別々に要求する。比較条件の範囲は非空で完全なものとして与え、両者で成立しない条件も一致に含む。運動と地理的位置そのものはその他同条件の対象外であり、必要な環境条件の数値を補わない。',
 '地球を同じ軸周りに一様回転する物体として比較する背景を明示する。赤道は表面の軸方向座標零・軸距離正、極は表面の軸距離零・軸方向座標非零として両極を含む。離れた時計は同じ現在表示の出来事を共有せず、比較のために初期同期や対面帰還を要求しない。',
 'langsamer laufenは同じK尺度・期間内の任意の正の時間幅について、実際の指示差から得る正の平均歩度が小さいという読み。別々の文字盤原点を許し、瞬間の指示値の大小を歩度差にしない。小ささは既存zjvの文脈基準に残し、原文にない数値閾値を設定しない。',
 'mußは同じ物理的前提と一様回転背景を保つ非空の許容候補全てで同じ比較内容が成立するという推論上の必要性と読む。基準設定自身も範囲へ含める。候補は結果の真偽から選ばず、全論理的可能性や規範的義務、実世界での正しさの認定とはしない。',
 '帰結として述べることと物理的に十分な導出を区別する。発話内の引用内容を有限評価で実行せず、原刊の主張・仮定を記述する。一般的な候補状況の関係と型付き記号解釈、tの識別表記だけを追加し、新しい時計の物理法則を原始記号へ隠さない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    cl=v('clock');ctx=v('context');f=v('readings');lo,hi=interval(k('ra'),ctx);t=v('time');rec=v('record')
    local=[cl,v('event'),v('display'),rec,v('place'),ctx]
    each=bind(('event','display','record','place'),'a','f',op('y',both(k('ejj5',*local),k('lg',lo,hi,stamp(rec))),k('ejj6',*local[:-1],app(f,stamp(rec)),ctx)))
    coverage=q('f','time',R,op('y',k('lg',lo,hi,t),k('ejkc',cl,t,app(f,t),ctx)))
    text+=define('ejlz',PROFILE,both(k('ca',cl),k('ci',k('rb')),k('eisdf',cl,ctx),k('eisdd',k('ra'),k('ta'),k('rb'),ctx),k('bg',lo,hi),k('se',*path(cl,lo,hi,ctx)),each,coverage))
    lower=v('lower');upper=v('upper');rate=v('rate')
    text+=define('ejma',MEAN,both(k('ba',lower),k('ba',upper),k('bg',lower,upper),k('ba',app(f,lower)),k('ba',app(f,upper)),k('sbg',rate),eq(sub(app(f,upper),app(f,lower)),mul(rate,sub(upper,lower)))))
    r1=v('firstrate');r2=v('secondrate');f1=v('firstreading');f2=v('secondreading')
    text+=define('ejmb',SLOW,q('g','firstrate',R,q('g','secondrate',R,both(k('ejma',f1,lower,upper,r1),k('ejma',f2,lower,upper,r2),k('bg',r1,r2),k('zjv',sub(r2,r1),r2,v('scope'),ctx)))))
    first=v('first');second=v('second');pa=v('firstplace');pb=v('secondplace')
    text+=define('ejmc',PAIR+[('context','d')],both(op('u',op('e',first,second)),k('syi',first,ctx),k('syi',second,ctx),k('cd',first,second),k('syj',first,second,k('zjw'),ctx),k('zjm',first,pa,k('zjr'),ctx),k('zjm',second,pb,k('zjr'),ctx),k('syk',pa,k('zjr'),k('zjs'),k('ta'),ctx),k('syl',pb,k('zjr'),k('zjs'),k('ta'),ctx)))
    text+=define('ejmd',OBSERVED,both(k('ejmc',*args(PAIR),ctx),k('ejlz',first,f1,ctx),k('ejlz',second,f2,ctx)))
    inside=both(k('lg',lo,hi,lower),k('lg',lo,hi,upper),k('bg',lower,upper))
    text+=define('ejme',WINDOW,op('y',both(k('ejmd',*args(OBSERVED)),inside),k('ejmb',f1,f2,lower,upper,k('zjw'),ctx)))
    body=k('ejme',*args(WINDOW[:-1]),v('point'))
    for n,s in reversed(WINDOW[:-1]):body=q('f',n,s,body)
    text+=content('ejmf',body)
    selected=both(k('eisol',v('subject'),v('reference'),v('candidate')),k('zjn',k('zjr'),k('zjs'),k('ra'),v('candidate')))
    candidates='i[subject e reference d candidate d]['+selected+']'
    text+=content('ejmg',both(k('eisol',k('ejmf'),k('zjt'),k('zjt')),k('zjn',k('zjr'),k('zjs'),k('ra'),k('zjt')),k('s5k',k('ejmf'),k('zjt'),candidates)))
    text+=content('ejmh',all_cases(op('y',both(k('ejlq',*args(COMPARE)),k('ejlr',*args(CURVE))),k('ejlu',*args(COMPARE)))))
    point=v('point');scope=k('zjd');author=k('rd')
    text+=content('ejmi',both(k('ui',author,k('zjb'),point),k('ug',k('zje'),author,quote('ejlx'),scope,point)))
    text+=content('ejmj',both(k('uh',k('zjf'),author,quote('ejlw'),scope,point),k('zc',k('zjf'),author,quote('ejly'),quote('ejlw'),scope,point),k('ue',k('zje'),k('zjf'),point),k('eison',k('eisom'),'r[p ejlt]',k('eirf'),point)))
    text+=content('ejmk',both(k('zc',k('zjy'),author,quote('ejlw'),quote('ejmg'),scope,point),k('uh',k('zjy'),author,quote('ejmg'),scope,point)))
    text+=define('ejml',[],k('zfl',k('zjf'),author,quote('ejmh'),quote('ejlw'),scope,k('ri')))
    for name,body in (('ejmm','ejmi'),('ejmo','ejmj'),('ejmq','ejmk')):text+='d '+name+'[] f[j s[k '+body+'[]]].\n'
    for name,message,node,previous in (('ejmn','ejmm','zje','zjc'),('ejmp','ejmo','zjf','zje'),('ejmr','ejmq','zjy','zjf')):
        rows=[k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if name=='ejmp':rows.insert(0,k('ejml'))
        text+=define(name,[],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==347;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejmn','ejmp','ejmr')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='assumed_curve_extension_and_current_earth_clock_rate_comparison',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/curved-clock-records-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')));ann['entries'].append(dict(symbol='eisom',role='designation',forms=[dict(text='t',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
