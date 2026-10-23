"""Connect arbitrary finite current-clock paths and return to the same place."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_transfer_claim import ROOT,read
from scripts.compose_clock_transfer_records import LOCAL,stamp,sub,mul,eq,path
from scripts.compose_polygon_clock import PATH as OLD_PATH
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-clock-transfer-claim.noema';PARENT_BASIS='data/clock-transfer-claim-basis-v1.json'
FULL='examples/v014/einstein-polygon-clock-claim.noema';CORE='examples/v014/polygon-clock-claim-core.noema'
BASIS='data/polygon-clock-claim-basis-v1.json';ANNOTATIONS='data/polygon-clock-claim-identifiers-v1.json';INDICES=(345,346)
PATH=OLD_PATH[:5]+[('places','h[a] a')]+OLD_PATH[5:]
COMPARE=PATH+[('reference','a'),('initialevent','a'),('initialrecord','a'),('referencestart',R),('referenceend',R),('initial','d')]
LEG=[('clock','a'),('first','a'),('last','a'),('record','h[a] a'),('reading','h[a] '+R),('places','h[a] a'),('speed',R),('setting','d')]
NUMBERS=[(n,R) for n in ('scale','duration','gap','approximation','error')]
MEANINGS={
 'ejkx':'指定した共通速さの、同じ時計の全閉区間の三次元直線等速経路。ejkdの現在表示・完全な代表軌跡・全候補と全実時刻を保ち、速さを引数に一般化する。端点だけで中途の経路を済ませない。',
 'ejky':'一つの正の時間幅の区間について、同じ時計の出発と到着の現在表示を同じ出来事・記録・指示・場所の関数へ結び、ejkxの全直線経路を要求する。',
 'ejkz':'非空の任意有限区間列が同じ出来事で順に接続し、全出現で同じ時計・速さと共有された記録/指示/場所の関数を使ってejkyを満たす。幾何学的な同じ場所の再訪や自己交差を禁止しない。',
 'ejk2':'折れ線全体の比較設定。両時計は全初期区間で同じK時刻に同じ指示を持って静止し、参照時計は全移送期間終着場所に残る。初期表示と到着表示は現在の局所記録へ結ぶ。出発と初期参照出来事、出発と終着の場所は一致してよい。',
 'ejk3':'同じ任意有限折れ線の完全な経路ejkzと初期同期・参照時計・到着比較ejk2を結ぶ原文の設定。移動時計の平方根の率や到着遅れを前件へ加えない。',
 'ejk4':'同じ折れ線の全区間について、共通速さの平方根の率による全時刻の指示法則ejkbと端点差sxiを採る追加解釈。折れ点の同じ出来事・単一指示を共有し、区間間での指示リセットを許さない。',
 'ejk5':'同じ経路・比較設定にejk4と参照時計の全区間の率1、実際の参照指示差、同じ端点に関する望遠和ejk6を加えた補足の指示法則。加速応答を慣性運動から証明したとはしない。',
 'ejk6':'同じ順序付き列の全出現について、K時間差の和sxjが出発から到着の差、指示差の和sxkが同じ時計の全指示差に等しい。正の全所要時間を保つ。和の一致だけで経路や区間法則を認定しない。',
 'ejk7':'同じ折れ線の正の全K所要時間と実際の到着指示差を共通の正尺度で秒へ換算し、共通速さの二次近似と残差へ結ぶ。初期座標時刻、一区間だけの時間、前の特定時計の固定記録を代用しない。',
 'ejla':'同じ到着出来事・場所に属する現在の二指示が非一致で、移動時計が小さく、差が全所要時間と共通速さの遅れ率の積である。共通秒換算、二次近似と固定全所要時間の四次以上の留保を合わせた、前段と同じ結果。',
 'ejlb':'同じ折れ線の出発と到着が正の時間を隔てた異なる出来事で、同じ場所と三座標位置へ帰還する。場所の一致を出来事や時刻の同一性へ替えない。',
 'ejlc':'任意の有限列とその区間・記録・指示・場所の関数、同じ二時計・共通速さ・初期と移送の設定について、ejk3なら同じ到着結果ejlaを述べる内容。全列・全関数・全実数量化を保持する。',
 'ejld':'同じ任意範囲で、ejk3と帰還ejlbなら同じejlaが成立する内容。A=Bの場合を明示するが、帰還という条件を折れ線全体の一般主張へ追加しない。',
 'ejle':'任意の同じ設定ejk3で、区間と折れ点に追加指示変化を生じないejk5を採用する補足の解釈内容。原文の前件へこの物理的理想化を混入しない。',
 'ejlf':'補足の全区間指示法則ejleを用いて一般の折れ線結果ejlcを読むzflの解釈注記。著者の発話メッセージ外へ置く。',
 'ejlg':'前段の現在の移送結果ejkmから任意折れ線での同じ結果ejlcへ拡張する著者の提示と、直ちに認められるという明白さzdgを同じ内容へ帰属する。',
 'ejlh':'同じ一般の折れ線結果ejlcに続いて、出発地点と終着地点が一致する場合ejldも同じく成立すると著者が明示する。一般結果からの適用であり、場所の一致を同じ出来事への帰還にしない。',
 'ejli':'u0127前半の一般折れ線への拡張と明白さejlgを述べるメッセージ。',
 'ejlj':'前半を同じ著者・論説へ帰属し、直線移送の帰結zi7に続ける。補足解釈ejlfは発話外へ併記する。',
 'ejlk':'u0127後半の帰還でも同じ結果が成立するejlhを述べるメッセージ。',
 'ejll':'後半を同じ著者・論説へ帰属し、前半の一般折れ線の後に続ける。',
}
REUSED_SOURCE='examples/v014/einstein-polygon-clock.noema'
REUSED_BASIS='data/polygon-clock-basis-v1.json'
MEANINGS={**{n:json.loads(read(REUSED_BASIS))['definitions'][n] for n in ('sxd','sxj','sxk')},**MEANINGS}
LIMITS=[
 'u0127全155非空白本文文字とM0233–M0236のA/B/A/Bを原刊904頁へ照合する。Man sieht sofort、dies Resultat、auch dann noch、任意のpolygonale Linie、und zwar auch dann、AとBの一致を保持する。',
 '折れ線は任意の非空有限列で表す。各実際の移動区間は正の所要時間と共通の正の速さv<Vを持つ。隣接する同じ頂点を重複記載した零区間は経路を変えない表記上の冗長として除き、待機時間を暗黙に追加しない。速さを区間ごとに変える場合は今回の前段と同じ結果ではなく加重和が必要である。',
 '同じ幾何学的な辺や場所への再訪、自己交差は排除しない。出来事には各到達時刻を含め、前区間の終わりと次区間の始まりでは同じ出来事と一つの記録・指示・場所関数を共有する。幾何学的位置だけが等しい別出来事を折れ点の接続にしない。',
 '全区間の現在表示、完全な代表軌跡、全実時刻の存在と全候補の経路条件を保持する。全有限列・関数・実数の量化を有限標本へ替えず、検査用の小さい領域を実際の主張範囲にしない。',
 'A=Bは同じ場所へ正の全時間の後で戻る場合であり、出発と帰着は異なる出来事である。両時計が初め同じ場所・同じ出来事で比較されることを許し、u0126の異なる地点や初期出来事の条件を流用しない。初期同期・参照時計の残留・到着直後の同所比較は前段と同じ読みで保持する。',
 '同じ結果は、全所要時間に対する到着時の遅れと、共通秒換算による二次近似・固定全所要時間の四次以上の留保を含む。全所要時間は全区間の時間差の和と同じ端点の差へ結ぶ。距離固定で時間も速度依存の族の無条件のO(v⁴)や具体的残差係数は追加しない。',
 '方向転換・発進・停止に追加の指示変化がないという全区間法則はejle/ejlfの発話外の補足解釈へ置く。著者が述べる原文の前件ejk3をその法則で狭めず、著者の一般主張を記述することと加速時計の物理的導出を区別する。',
 'Man sieht sofortは、前段の同じ結果の拡張が直ちに認められるという著者の明白さの提示と読む。全読者の認知の事実、反応時間、処理系の証明済み認定にしない。und zwar以下は一般範囲を帰還に限定するのではなく、その場合も含まれると明示する。',
 '新しい原始記号は追加しない。u0128の連続曲線への適用を仮定する発話と地球上の時計への適用は後続である。',
]

def rec(event):return app(v('record'),event)
def reading(event):return app(v('reading'),event)
def place(event):return app(v('places'),event)
def elapsed(first,last):return sub(stamp(rec(last)),stamp(rec(first)))
def all_cases(body):
    for n,s in reversed(COMPARE):body=q('f',n,s,body)
    return body

def definitions():
    cl=v('clock');ctx=v('context');fr=v('firstrecord');lr=v('lastrecord');speed=v('speed');t=v('time');record=v('record');lo=stamp(fr);hi=stamp(lr)
    every=bind(('event','display','record','place'),'a','f',op('y',both(k('ejj5',*args(LOCAL)),k('lg',lo,hi,stamp(record))),k('swp',record,fr,lr)))
    text=define('ejkx',[('clock','a'),('firstrecord','a'),('lastrecord','a'),('speed',R),('context','d')],both(k('ca',cl),k('eisdf',cl,ctx),k('eisdd',k('ra'),k('ta'),k('rb'),ctx),k('lg',*interval(k('ra'),ctx),lo),k('lg',*interval(k('ra'),ctx),hi),k('swo',fr,lr,speed),k('se',*path(cl,lo,hi,ctx)),every,q('f','time',R,op('y',k('lg',lo,hi,t),k('ejka',cl,t,ctx)))))
    first=v('first');last=v('last');setting=v('setting');segments=v('segments');start=v('start');end=v('end');a=app(start,v('segment'));b=app(end,v('segment'));one=k('bb','n p b b')
    current=lambda clock,event,val,here:k('ejj7',clock,event,rec(event),place(event),val,here)
    text+=define('ejky',LEG,both(op('u',op('e',first,last)),current(cl,first,reading(first),setting),current(cl,last,reading(last),setting),k('ejkx',cl,rec(first),rec(last),speed,setting)))
    leg=[cl,a,b,v('record'),v('reading'),v('places'),speed,setting]
    text+=define('ejkz',PATH,both(k('aa','n p a b','d[v segments]'),k('sxc',segments,start,end,first,last),k('sxb',segments,lam('segment','a',k('ejky',*leg)))))
    reference=v('reference');initial=v('initial');ir=v('initialrecord');ie=v('initialevent');rs=v('referencestart');re=v('referenceend');begin=stamp(rec(first));finish=stamp(rec(last));T=elapsed(first,last);initiallo,initialhi=interval(k('ra'),initial)
    conditions=[op('u',op('e',cl,reference)),op('u',op('e',initial,setting)),op('u',op('e',first,last)),k('sbg',T),eq(begin,stamp(ir)),eq(initialhi,begin),eq(reading(first),rs)]
    conditions.extend((current(cl,first,reading(first),initial),current(cl,first,reading(first),setting),current(cl,last,reading(last),setting),current(reference,last,re,setting)))
    for here in (initial,setting):conditions.append(k('ejj7',reference,ie,ir,place(last),rs,here))
    for clock,where,record,value in ((cl,place(first),rec(first),reading(first)),(reference,place(last),ir,rs)):
        conditions.extend((k('ejke',clock,where,record,initiallo,initialhi,initial),k('ejkb',clock,initiallo,initialhi,sub(value,sub(initialhi,initiallo)),one,initial)))
    conditions.append(k('ejke',reference,place(last),ir,begin,finish,setting))
    text+=define('ejk2',COMPARE,both(*conditions))
    text+=define('ejk3',COMPARE,both(k('ejkz',*args(PATH)),k('ejk2',*args(COMPARE))))
    rate=k('stw',k('tc'),speed)
    law=k('ejkb',cl,stamp(rec(a)),stamp(rec(b)),reading(a),rate,setting)
    text+=define('ejk4',PATH,both(k('sxi',*args(OLD_PATH)),k('sxb',segments,lam('segment','a',law))))
    text+=define('ejk6',PATH,both(k('sbg',T),eq(k('sxj',*args(OLD_PATH)),T),eq(k('sxk',*args(OLD_PATH)),sub(reading(last),reading(first)))))
    text+=define('ejk5',COMPARE,both(k('ejk3',*args(COMPARE)),k('ejk4',*args(PATH)),k('ejkb',reference,begin,finish,rs,one,setting),eq(sub(re,rs),T),k('ejk6',*args(PATH))))
    scale=v('scale');seconds=mul(scale,T);gap=mul(scale,sub(re,reading(last)));approx=mul(seconds,k('swa',k('sje',speed,k('tc'))));error=sub(gap,approx)
    text+=define('ejk7',COMPARE+NUMBERS,both(k('sbg',T),k('svp',scale,setting),*(k('ba',v(n)) for n,_ in NUMBERS),eq(v('duration'),seconds),eq(v('gap'),gap),eq(v('approximation'),approx),eq(v('error'),error)))
    oldcompare=args(OLD_PATH)+[reference,ie,ir,rs,re,initial]
    result=both(current(cl,last,reading(last),setting),current(reference,last,re,setting),op('u',eq(reading(last),re)),k('sxn',*oldcompare),q('g','scale',R,both(k('ejk7',*args(COMPARE),scale,seconds,gap,approx,error),k('swy',seconds))))
    text+=define('ejla',COMPARE,result)
    text+=define('ejlb',PATH,both(k('sxo',*args(OLD_PATH)),op('e',place(first),place(last))))
    settingrule=k('ejk3',*args(COMPARE));result=k('ejla',*args(COMPARE))
    text+=content('ejlc',all_cases(op('y',settingrule,result)))
    text+=content('ejld',all_cases(op('y',both(settingrule,k('ejlb',*args(PATH))),result)))
    text+=content('ejle',all_cases(op('y',settingrule,k('ejk5',*args(COMPARE)))))
    text+=define('ejlf',[],k('zfl',k('zjb'),k('rd'),quote('ejle'),quote('ejlc'),k('eisn5'),k('ri')))
    point=v('point')
    text+=content('ejlg',both(k('zc',k('zjb'),k('rd'),quote('ejkm'),quote('ejlc'),k('eisn5'),point),k('uh',k('zjb'),k('rd'),quote('ejlc'),k('eisn5'),point),k('zdg',k('zjb'),k('rd'),quote('ejlc'),k('eisn5'),point)))
    text+=content('ejlh',both(k('zc',k('zjc'),k('rd'),quote('ejlc'),quote('ejld'),k('eisn5'),point),k('uh',k('zjc'),k('rd'),quote('ejld'),k('eisn5'),point)))
    for name,body in (('ejli','ejlg'),('ejlk','ejlh')):text+='d '+name+'[] f[j s[k '+body+'[]]].\n'
    for name,message,node,previous in (('ejlj','ejli','zjb','zi7'),('ejll','ejlk','zjc','zjb')):
        rows=[k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if name=='ejlj':rows.insert(0,k('ejlf'))
        text+=define(name,[],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    reused='\n'.join(line for line in read(REUSED_SOURCE).splitlines() if line.startswith(('d sxd[','d sxj[','d sxk[')))+'\n'
    doc=parse(format_graph(doc,'compact')+reused+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejlj','ejll')];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='arbitrary_current_polygon_clock_paths_and_return_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/clock-transfer-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
