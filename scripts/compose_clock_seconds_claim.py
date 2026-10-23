"""Connect exact seconds lost and the qualified second-order approximation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_origin_clock_time import ROOT,read
from scripts.compose_solid_sphere_geometry import bind,args
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-origin-clock-time.noema';PARENT_BASIS='data/origin-clock-time-basis-v1.json'
FULL='examples/v014/einstein-clock-seconds-claim.noema';CORE='examples/v014/clock-seconds-claim-core.noema'
BASIS='data/clock-seconds-claim-basis-v1.json';ANNOTATIONS='data/clock-seconds-claim-identifiers-v1.json';INDICES=(341,342)
PAIR=[(n,'a') for n in ('clock','firstown','firstlab','lastown','lastlab')]+[('context','d')]
INTERVAL=PAIR[:-1]+[(n,R) for n in ('scale','duration','elapsed','lost')]+PAIR[-1:]
MEANINGS={
 'ejjq':'同じ時計・状況の二つの局所記録対ejitを選び、Kの時刻が厳密に先後することを要求する。先後それぞれのk記録とK記録を同じ出来事に結び、零時間幅や逆順を除く。',
 'ejjr':'正の観測経過秒数と指示経過秒数、その差である遅れ秒数について、同じ正の率f=√(1−(v/V)²)で指示経過=T*f、遅れ=T−指示経過=T*(1−f)を結ぶ。一秒当たりの値1−fと全経過の遅れを混同しない。',
 'ejjs':'同じ時計の時間順の二記録対、同じ正の秒換算尺度svp、観測時間差とτ指示差を結ぶ。両差に同じ尺度を掛け、得た経過・指示経過・遅れをejjrの厳密な秒の関係に渡す。',
 'ejjt':'同じ原点時計の全現在範囲ejjdと全時間の率ejiuを保ち、一つの正の秒換算尺度を全ての時間順の記録対に共通に使ってejjsを要求する。一秒ちょうどの測定例の存在は要求しない。',
 'ejju':'同じ時計zieの全ての時間順の記録対がejjtを満たす共通の秒換算尺度が存在するという、厳密な一秒当たりの遅れの内容。',
 'ejjv':'同じ時計の厳密な遅れejjuに、同じv/Vでの二次近似と残差の区別svq、速度比の零近傍で誤差が四次のオーダーというswcを合わせる。oderは留保付きの近似表示への言い換えとして保持する。',
 'ejjw':'前の同じ時計の比例式・差の式ejjmと、時間単位から秒への共通の正の換算が使えることを合わせた、単位秒の遅れを導く前提。',
 'ejjx':'woraus folgtを同じ著者によるejjwからejjuへの帰結提示として保持する。Kの経過に対する同じ時計の指示の遅れであり、絶対時刻の一回の大小比較ではない。',
 'ejjy':'著者が同じ遅れについて、二次近似を四次以上の留保と共にejjvとして提示する。近似を厳密値へ等置しない。',
 'ejjz':'厳密な単位秒の遅れへの帰結ejjxを述べるメッセージ。',
 'ejj2':'同じ遅れの留保付き二次近似ejjyを述べるメッセージ。',
 'ejj3':'厳密な遅れの提示を同じ著者・論説に帰属し、比例式の位置zijに続ける。',
 'ejj4':'同じ遅れの近似表示を同じ著者・論説に帰属し、同文の厳密表示zimからzinへ続ける。',
}
LIMITS=[
 'u0125のworaus folgtからzurückbleibt.までを原刊904頁へ照合する。M0217は1−√(1−(v/V)²)、M0218は(v/V)²/2。時計・Kからの観測・一秒当たり・秒という単位・近似の留保・遅れるという関係を保持する。',
 '指示の遅れはKの正の経過時間に対する同じ時計の指示差の不足である。負でもよい座標時刻そのものの大小を遅れへ替えない。二つの記録は同じ時計の現在の同じ出来事対応を通じてK/kへ結ぶ。',
 '秒zikは原文で指定された共通の時間基準単位として用い、既存zil/svpの原点移動を含まない正の線形換算で接続する。座標単位rbを無条件に秒と同一視せず、観測差と指示差、全記録対で同じ尺度を使う。歴史的な秒の実現装置をこの文に追加しない。',
 'pro Sekundeは正の経過を一秒に規格化した比率として読む。一秒ちょうどの区間が測定済みであるという存在主張を加えず、全経過の遅れT*(1−f)と一秒当たりの数値1−fを区別する。',
 'oderは厳密表示から留保付き近似表示への言い換え。速度比u=v/Vの零近傍で1−√(1−u²)−u²/2がO(u⁴)という読みを明示する。二次項が全速度域で厳密値に等しいこと、全速度で誤差が実用上小さいこと、解析的級数の任意次数の展開全体は主張しない。',
 '四次以上の留保は既存svy/swcの集積点・共通の正の定数と近傍幅・全近傍点での両側誤差条件として保持する。有限な速度の標本へ縮めない。原文にない残差の係数1/8や1/2の具体的な上下限は今回の著者の主張へ追加しない。',
 '同じ原点時計の全現在範囲、校正、代表軌跡、実際の記録、正の時間幅、全時間順の率を継承する。旧zac/zdz/svcの草案の範囲へ戻らず、同じK時刻とτ表示へ接続する。',
 '局所検査・通読判断・一般の物理的真理の証明を区別する。新しい原始記号は追加しない。AからBへの運搬と到着時比較はu0126以降に残る。',
]

def definitions():
    cl=v('clock');ctx=v('context');fo=v('firstown');fl=v('firstlab');lo=v('lastown');ll=v('lastlab');scale=v('scale');T=v('duration');E=v('elapsed');L=v('lost')
    stamp=lambda rec:k('zc6',rec,k('zc7'));mul=lambda a,b:k('shv',a,b);sub=lambda a,b:k('bf',a,b);eq=lambda a,b:k('sca',a,b)
    text=define('ejjq',PAIR,both(k('ejit',cl,fo,fl,ctx),k('ejit',cl,lo,ll,ctx),k('bg',stamp(fl),stamp(ll))))
    text+=define('ejjr',[(n,R) for n in ('duration','elapsed','lost')],both(k('sbg',T),k('sbg',E),k('ba',L),k('stx',k('tc'),k('zb7'),k('svm')),eq(E,mul(T,k('svm'))),eq(L,sub(T,E)),eq(L,mul(T,k('svt')))))
    duration=mul(scale,sub(stamp(ll),stamp(fl)));elapsed=mul(scale,sub(stamp(lo),stamp(fo)));lost=sub(duration,elapsed)
    text+=define('ejjs',INTERVAL,both(k('svp',scale,ctx),k('ejjq',*args(PAIR)),eq(T,duration),eq(E,elapsed),k('ejjr',T,E,L)))
    every=bind(('firstown','firstlab','lastown','lastlab'),'a','f',op('y',k('ejjq',*args(PAIR)),k('ejjs',cl,fo,fl,lo,ll,scale,duration,elapsed,lost,ctx)))
    text+=define('ejjt',[('clock','a'),('scale',R),('context','d')],both(k('svp',scale,ctx),k('ejjd',cl,ctx),k('ejiu',cl,k('svm'),ctx),every))
    text+=content('ejju',q('g','scale',R,k('ejjt',k('zie'),scale,k('zb6'))))
    point=v('point');ev=lambda n:op('t',k(n),point)
    text+=content('ejjv',both(ev('ejju'),k('svq',*(k(n) for n in ('tc','zb7','svm','svt','svu','svv'))),k('swc')))
    text+=content('ejjw',both(ev('ejjm'),q('g','scale',R,k('svp',scale,k('zb6')))))
    text+=content('ejjx',k('zc',k('zim'),k('rd'),quote('ejjw'),quote('ejju'),k('eisn5'),point))
    text+=content('ejjy',k('uh',k('zin'),k('rd'),quote('ejjv'),k('eisn5'),point))
    for n,body in (('ejjz','ejjx'),('ejj2','ejjy')):text+='d '+n+'[] f[j s[k '+body+'[]]].\n'
    for name,message,node,previous in (('ejj3','ejjz','zim','zij'),('ejj4','ejj2','zin','zim')):
        text+=define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejj3','ejj4')];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_clock_seconds_loss_and_qualified_approximation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/origin-clock-time-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
