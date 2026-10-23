"""Bind transfer clocks to current local displays and complete phase histories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_seconds_claim import ROOT,read
from scripts.compose_clock_transfer import COMMON,CONSTANTS
from scripts.compose_origin_clock_question import tracks
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-clock-seconds-claim.noema';PARENT_BASIS='data/clock-seconds-claim-basis-v1.json'
FULL='examples/v014/einstein-clock-transfer-records.noema';CORE='examples/v014/clock-transfer-records-core.noema'
BASIS='data/clock-transfer-records-basis-v1.json';ANNOTATIONS='data/clock-transfer-records-identifiers-v1.json'
LOCAL=[(n,'a') for n in ('clock','event','display','record','place')]+[('context','d')]
READING=LOCAL[:-1]+[('reading',R)]+LOCAL[-1:]
RATE=[('clock','a')]+[(n,R) for n in ('lower','upper','initialreading','rate')]+[('context','d')]
REST=[(n,'a') for n in ('clock','place','record')]+[(n,R) for n in ('lower','upper')]+[('context','d')]
MEANINGS={
 'ejj5':'同じ時計のKでの現在の局所表示候補ejikを、同じ出来事・状況の実際の代表軌跡sbと三座標へ結ぶ。指示値の正誤では候補を選ばず、対象出来事・表示出来事・記録・場所を保持する。',
 'ejj6':'同じ現在の局所表示候補について、指定した有効な実数指示が対象出来事と表示出来事の双方で読まれ、他の全ての有効な指示も同じ値である。K座標時刻と同じ値であることは要求しない。',
 'ejj7':'指定した時計・対象出来事・K記録・場所・指示値・状況について、一つの表示出来事がejj6を満たす。到着時に二時計を比較する際も同じ対象出来事と場所を渡す。',
 'ejka':'指定したK時刻に、同じ時計・状況のejj5を満たす出来事・表示・現在記録・場所が一組存在する。四つの証人と記録時刻を共有する。',
 'ejkb':'正の幅のK閉区間の完全な代表軌跡と校正を持つ同じ時計について、全現在候補の指示がinitialreading+rate*(t−lower)となり、全実時刻に同じ値を指示するejkcの一組が存在する。正の一定率と任意の共通表示原点を許し、端点だけで中途のリセットを見逃さない。',
 'ejkc':'指定したK時刻に指定した指示値を持つejj6の出来事・表示・現在記録・場所が一組存在する。時刻の証人と指示の証人を独立に選ばない。',
 'ejkd':'同じ時計のKでの出発・到着記録について、正の所要時間と速さ、端点距離、全閉区間の代表軌跡、全時刻での現在表示候補の存在、全候補の三次元線形補間swpを結ぶ。端点が合うだけの迂回や非等速移動を許さない。',
 'ejke':'同じ時計がKの正の閉区間全体で代表位置を一定に保つeit2を満たし、その位置が現在記録と同じ一意な場所placeである。針や内部機構の停止を要求せず、初期静止と移送中のBへの残留へ同じ規則を適用する。',
 'ejkf':'二時計・A/B・出発/初期B表示/到着・三つのK記録を現在表示へ結ぶ移送設定。初期区間末端で出発し、両時計は全初期区間で静止して同じK時刻に同じ指示を持つ。B時計は全移送区間Bに残り、移送時計は全区間AからBへ直線等速移動する。到着時の二指示は同じ出来事とBに属する。移送時計の進み率の答えはこの設定に含めない。',
 'ejkg':'同じ移送設定ejkfに、移動時計がf=√(1−(v/V)²)、B時計が1という全区間の指示法則ejkbを加える。両端も含む現在表示と初期指示を使い、発進・停止の追加指示変化がないという明示した区間法則の解釈を表す。原点時計の慣性運動だけからこれを証明したとはしない。',
 'ejkh':'同じ移送についてejkgを保ち、正の所要時間に対する移動時計とB時計の実際の出発・到着指示差を、それぞれ率fと1のejisへ接続する。全期間の法則と端点の代数的比較を区別する。',
}
LIMITS=[
 'u0126全体へ接続する意味依存群。原刊904頁の二文を照合し、初期同期、同じ時計の直線移送、初めからBにある時計、到着時の同所比較を現在表示と完全な代表軌跡へ更新する。本文への帰属と一単位全体の判断は後続であり、意味確認済み件数を増やさない。',
 '初期同期はKの同じ時刻に両時計が全初期区間で同じ指示を示す読み。Kの時間尺度を共有する正しい率1の時計を用い、両方に共通の指示原点は任意とする。初期区間を出発で閉じ、移送区間は出発から到着までとする。区間を選ぶ規約であり、原文にない待機時間の数値を指定しない。',
 '現在の局所候補ejik、同所表示eisgm、場所付き現在四記録eiyw、同じ時計の代表軌跡sb/se、正の尺度・校正を引き継ぐ。旧swl/swm/swqのshd/x4の範囲へ戻らず、指示差の成否から候補を選ばない。全時刻の存在と全候補の正しい指示を分ける。',
 '全時間の初期同期は同時刻の同じ指示として表す。初期の光往復試行の実施済みや新たな測定操作を要求しない。到着時の非同期は後続で同所の異なる指示として記述し、移送前後を一つの無限定な静止状況にしない。',
 'AとBを異なる地点、正の速さv<Vと正の所要時間の直線移送として読む。方向は三次元の端点差で定まり、正のX軸に限定しない。後のA=Bの帰還や折れ線へこの単一区間の条件をそのまま流用しない。',
 '移送中の平方根の率とB時計の率1は追加の理想化を明示する区間法則である。発進・停止で指示の追加変化がないことを含むが、加速度応答の物理的導出や一般の加速時計仮説の証明ではない。原文の条件付き主張へ解釈として接続し、著者の明記した追加前提として捏造しない。',
 '所要時間と到着指示差の共通秒換算、二次近似と四次以上の留保、Hierausの前段参照、eigentümlicheの評価、非同期と遅れの対比、著者の条件付き提示は後続で統合する。原始記号は追加しない。',
]

def stamp(rec):return k('zc6',rec,k('zc7'))
def sub(a,b):return k('bf',a,b)
def mul(a,b):return k('shv',a,b)
def eq(a,b):return k('sca',a,b)
def path(cl,lo,hi,ctx):return [cl,k('ra'),ctx,k('ta'),k('rb'),lo,hi,*tracks(cl,k('ra'),ctx)]

def definitions():
    cl=v('clock');ctx=v('context');event=v('event');display=v('display');record=v('record');place=v('place');reading=v('reading');t=stamp(record);lo=v('lower');hi=v('upper');time=v('time');one=k('bb','n p b b')
    actual=[app(f,t) for f in tracks(cl,k('ra'),ctx)]
    text=define('ejj5',LOCAL,both(k('ejik',cl,event,display,record,place,k('ra'),ctx),k('sb',cl,event,k('ra'),ctx,k('ta'),k('rb'),t,*actual),*(eq(k('zc6',record,k(axis)),x) for axis,x in zip(('yn','yo','yp'),actual))))
    reads=lambda ev,val:k('ce',cl,ev,k('ra'),k('rb'),val)
    unique=q('f','otherreading',R,op('y',both(k('ba',v('otherreading')),op('x',reads(event,v('otherreading')),reads(display,v('otherreading')))),eq(v('otherreading'),reading)))
    text+=define('ejj6',READING,both(k('ejj5',*args(LOCAL)),k('ba',reading),reads(event,reading),reads(display,reading),unique))
    text+=define('ejj7',[f for f in READING if f[0]!='display'],q('g','display','a',k('ejj6',*args(READING))))
    witnesses=('event','display','record','place')
    text+=define('ejka',[('clock','a'),('time',R),('context','d')],both(k('ba',time),bind(witnesses,'a','g',both(k('ejj5',*args(LOCAL)),eq(t,time)))))
    text+=define('ejkc',[('clock','a'),('time',R),('reading',R),('context','d')],both(k('ba',time),k('ba',reading),bind(witnesses,'a','g',both(k('ejj6',*args(READING)),eq(t,time)))))
    value=lambda at:k('bd',v('initialreading'),mul(v('rate'),sub(at,lo)))
    every=bind(witnesses,'a','f',op('y',both(k('ejj5',*args(LOCAL)),k('lg',lo,hi,t)),k('ejj6',cl,event,display,record,place,value(t),ctx)))
    alltimes=q('f','time',R,op('y',k('lg',lo,hi,time),k('ejkc',cl,time,value(time),ctx)))
    text+=define('ejkb',RATE,both(k('ca',cl),k('ci',k('rb')),k('eisdf',cl,ctx),k('eisdd',k('ra'),k('ta'),k('rb'),ctx),k('bg',lo,hi),k('lg',*interval(k('ra'),ctx),lo),k('lg',*interval(k('ra'),ctx),hi),k('ba',v('initialreading')),k('sbg',v('rate')),k('se',*path(cl,lo,hi,ctx)),every,alltimes))
    first=v('firstrecord');last=v('lastrecord');start=stamp(first);end=stamp(last)
    everypath=bind(witnesses,'a','f',op('y',both(k('ejj5',*args(LOCAL)),k('lg',start,end,t)),k('swp',record,first,last)))
    pathcoverage=q('f','time',R,op('y',k('lg',start,end,time),k('ejka',cl,time,ctx)))
    text+=define('ejkd',[('clock','a'),('firstrecord','a'),('lastrecord','a'),('context','d')],both(k('ca',cl),k('eisdf',cl,ctx),k('eisdd',k('ra'),k('ta'),k('rb'),ctx),k('lg',*interval(k('ra'),ctx),start),k('lg',*interval(k('ra'),ctx),end),k('swo',first,last,k('zb7')),k('se',*path(cl,start,end,ctx)),everypath,pathcoverage))
    text+=define('ejke',REST,both(k('ca',cl),k('eisdf',cl,ctx),k('lg',*interval(k('ra'),ctx),lo),k('lg',*interval(k('ra'),ctx),hi),k('eit2',*path(cl,lo,hi,ctx)),k('eiyv',record,place,k('ra'),ctx),*(eq(app(f,lo),k('zc6',record,k(axis))) for f,axis in zip(tracks(cl,k('ra'),ctx),('yn','yo','yp')))))
    moving=v('movingclock');ref=v('reference');initial=v('initial');motion=v('motion');initiallo,initialhi=interval(k('ra'),initial)
    fields=[(a,b) for a,b in (('movingclock','reference'),('placea','placeb'),('departure','initialreference'),('departure','arrival'),('initialreference','arrival'),('initial','motion'))]
    clauses=[*(op('u',op('e',v(a),v(b))) for a,b in fields),eq(start,stamp(v('initialrecord'))),k('bg',start,end),eq(initialhi,start),eq(v('movingstart'),v('referencestart'))]
    for clock,ev,rec,pl,val,context in (('movingclock','departure','firstrecord','placea','movingstart','initial'),('reference','initialreference','initialrecord','placeb','referencestart','initial'),('movingclock','departure','firstrecord','placea','movingstart','motion'),('movingclock','arrival','lastrecord','placeb','movingend','motion'),('reference','arrival','lastrecord','placeb','referenceend','motion')):
        clauses.append(k('ejj7',*(v(n) for n in (clock,ev,rec,pl,val,context))))
    for clock,pl,rec,endpoint in (('movingclock','placea','firstrecord','movingstart'),('reference','placeb','initialrecord','referencestart')):
        clauses.extend((k('ejke',v(clock),v(pl),v(rec),initiallo,initialhi,initial),k('ejkb',v(clock),initiallo,initialhi,sub(v(endpoint),sub(initialhi,initiallo)),one,initial)))
    clauses.extend((k('ejke',ref,v('placeb'),v('initialrecord'),start,end,motion),k('ejkd',moving,first,last,motion)))
    text+=define('ejkf',COMMON,both(*clauses))
    text+=define('ejkg',COMMON,both(k('ejkf',*args(COMMON)),k('stx',k('tc'),k('zb7'),k('svm')),k('ejkb',moving,start,end,v('movingstart'),k('svm'),motion),k('ejkb',ref,start,end,v('referencestart'),one,motion)))
    text+=define('ejkh',COMMON,both(k('ejkg',*args(COMMON)),k('ejis',k('svm'),start,end,v('movingstart'),v('movingend')),k('ejis',one,start,end,v('referencestart'),v('referenceend'))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==343;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_clock_transfer_phase_records_and_interval_laws_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/clock-seconds-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
