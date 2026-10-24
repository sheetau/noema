"""Introduce the incident quantities and attribute both k-frame displays literally."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
# Load the reusable layers before the recent composer, avoiding a historical
# import chain used solely to obtain the newest setting's field names.
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_wave_transform_application import transformed
from scripts.compose_aberration_line import SETTING as LINE_SETTING,NEW_ANGLE,GEOMETRY
from scripts.compose_perfect_mirror_setting import SETTING as MIRROR
from scripts.compose_wave_cycle_frequency import HARMONIC
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-reflected-light-inquiry.noema';PARENT_BASIS='data/reflected-light-inquiry-basis-v1.json'
FULL='examples/v014/einstein-mirror-wave-quantities.noema';CORE='examples/v014/mirror-wave-quantities-core.noema'
BASIS='data/mirror-wave-quantities-basis-v1.json';ANNOTATIONS='data/mirror-wave-quantities-identifiers-v1.json';INDICES=[396,397,398,399]
REF_ANGLE=[(n,R) for n in ('refanglecos','refanglesin','refratio','refprincipal','refangle')]
SETTING=MIRROR+NEW_ANGLE+REF_ANGLE+[('magneticside','c')]+[(n,R) for n in ('amplitude','newamplitude','refamplitude','refperiod','reffrequency')]
FIXED={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')}
VARIABLES=[(n,t) for n,t in SETTING if n not in FIXED]
NAMES=[('eksa','eisul','amplitude','A'),('eksb','eisum','newamplitude','A′'),('eksc','eisun','refamplitude','A″'),('eksd','eisuo','angle','φ'),('ekse','eisup','newangle','φ′'),('eksf','eisuq','refangle','φ″'),('eksg','eisur','frequency','ν'),('eksh','eisus','newfrequency','ν′'),('eksi','eisut','reffrequency','ν″')]
PRIMITIVES={
 'eisuh':'u0216の、入射光をKのA・cosφ・νで指定し、kでの対応量をコロンで導入する二文の箇所。',
 'eisui':'u0217=M0372の、同じ入射光のkでの振幅・角余弦・周期数の三式を表示する箇所。',
 'eisuj':'u0218の、同じ反射過程をkで記述すると得られる量をコロンで導入する箇所。',
 'eisuk':'u0219=M0374の、kでの反射光の振幅保存・角余弦反転・周期数保存の三式の表示箇所。',
}
for rule,symbol,field,label in NAMES:
    PRIMITIVES[symbol]=f'現在の鏡の設定における{field}を指す{label}の表記個体。同じ波・面・系・側・角の基準線と周期の役割は{rule}で構成する。既存の同じ綴りの記録や前節の判断を書き換えず、この局所の量の使用を識別する。'
MEANINGS={
 'ekrz':'同じ82設定で完全鏡のekrfと前節の同時刻結線による新角ekgnを保持する。三段階の同じ側の振幅を各三係数の非負の大きさへ、反射後の角を同じ結線と鏡映した法線へ、反射周期数を同じ正規化位相対と周期へ結ぶ。印刷された三式を前件へ加えない。',
 'ekr2':'同じ正の平方根分母sqrt(1−(v/V)²)を持つ、value*(1−(v/V)*cosφ)/sqrt(1−(v/V)²)の数値式。既存ekdrを実数式として再使用し、valueの量種類を同一視しない。',
 'ekr3':'同じ入射波のA′、cosφ′、ν′が、それぞれ原刊M0372の三つの右辺に等しいという表示内容。cosφ′は継承した結線に対する角の余弦であり、先に座標縦成分と同一視しない。',
 'ekr4':'同じ反射後のA″=A′、cosφ″=−cosφ′、ν″=ν′というM0374の三式。法線の鏡映から結線に対する角余弦の反転が自動的に従うとはしない。',
 'eksj':'Kで同じ入射光を指定するA・φ・νの三つの命名規約を結ぶ。cosφは同じ実数角の余弦であり、角そのものと同一視しない。',
 'eksk':'kから見た同じ入射光のA′・φ′・ν′を同じ設定の量へ結ぶ命名規約。φ′は先行の結線との角の読みを継承する。',
 'eksl':'kで反射後の同じ波のA″・φ″・ν″を同じ設定の量へ結ぶ命名規約。φ″にも同じ比較基準線を用いる読みを明示し、式を命名規則へ混ぜない。',
 'eksm':'K・V・先行の波範囲と状況を固定した78証人による同じ鏡設定と量の指定ekrz。入射を三量で記すことは偏光・接線方向・位相・場の全情報が三数で一意に決まるとの主張ではない。',
 'eksn':'同じ78役割の全割当についてekrzならM0372の三式ekr3という著者の表示内容。継承した角の読みと表示式が一致しない場合も前件を狭めて隠さない。',
 'ekso':'同じ78役割の全割当についてekrzならM0374の三式ekr4という著者の表示内容。全設定を同じに保ち、角の反転式を仮定にしてから繰り返さない。',
 'eksp':'Das einfallende Licht sei ... definiertを同じ鏡設定の内部の量の指定と仮定採用へ、Kの括弧内指定をその量の役割へ結ぶ。続くVon k ... sindを同じkの三式への著者の提示、コロンを同じ表示への説明と順序へ接続する。',
 'eksq':'同じ入射光のkでの三量を命名し、u0217の表示を同じ条件付きの三式eksnへ結ぶ。',
 'eksr':'同じ反射過程をkで扱うeksmからeksoを得るという著者の帰結提示、同じ前文の量の設定への照応、コロンと表示順序を保持する。有限の反射計算をこの帰結の無条件の真理証明にしない。',
 'ekss':'同じ反射光のkでの三量を命名し、u0219の表示を同じ条件付きの三式eksoへ結ぶ。',
}
for rule,symbol,field,label in NAMES:
    MEANINGS[rule]=f'同じobject=waveとvalue={field}及び状況について、K・V・先行の波範囲を固定した同じ76証人にekrzを要求する{label}の表記規則。候補の量と設定で別の波を選ばず、印刷等式を語義へ入れない。'
for shown,msg,stmt,node,previous in [('eksp','ekst','eksu','eisuh','eisug'),('eksq','eksv','eksw','eisui','eisuh'),('eksr','eksx','eksy','eisuj','eisui'),('ekss','eksz','eks2','eisuk','eisuj')]:
    MEANINGS[msg]=f'同じ提示内容{shown}を述べるメッセージ。'
    MEANINGS[stmt]=f'同じ箇所{node}の{msg}を著者と論説へ帰属し、先行箇所{previous}からの順序と箇所の区別を保つ。'
LIMITS=[
 '原刊914頁u0216–u0219、本文184非空白文字とM0369–M0374を対象とする。M0369はA,cosφ,ν、M0370はK、M0371/M0373はk、M0372/M0374は各三式であり、全ての行・プライム・符号・根号範囲を保持する。',
 '同じ完全導体面・同じ前節の源と波・局所近似・二系・校正・相互作用を引き継ぐ。三量による指定はこの反射の議論に使う振幅・角余弦・周期数の指定と読む。偏光、接線方向、位相、六係数を三数で一意に復元できるという主張は補わない。',
 'A,A′,A″は同じ電気側又は磁気側を一度選んだ三係数の非負の大きさ、ν,ν′,ν″は同じ時間単位と正規化位相の周期数とする。負の振幅、場の一成分、二乗振幅、位相率を代用しない。原文の普通のAの式に二乗を補わない。',
 'φは先行の源―観測者方向と速度との角を、φ′はu0193で明示的に導入された移動系の波面法線と同時刻結線との角という既存読解を継承する。φ″は反射後の法線とその同じ比較結線との角として読む。式に合わせて結線を+x軸へ暗黙に変更しない。',
 'この角の読みでは、M0372の角の式とM0374の角余弦反転は一般には成立しない。著者が提示する式をそのまま記述し、前件にその式を入れたり、対象を正面入射だけへ縮めたりして一致を作らない。旧法線(111,48,80)/145、V=5,v=3の対照ではk法線(15,24,40)/49、結線(111,60,100)/161で、cosφ′=145/161と表示右辺15/49は異なる。鏡映後の同じ結線との余弦3775/7889も−145/161ではない。',
 '本文の式が記述できることと、採用した字義的な角の読解の下で真であることを区別する。過去の角の判断も原刊の式も書き換えず、訂正された理論として完成扱いしない。歴史的意図や誤植の一意な確定は行わない。',
 '新しい表記個体はこの箇所の同じ量の使用を識別する。前節の同じ綴りの表記個体と判断を保存し、その数値的・物理的役割を現在の設定へ接続する。定義・仮定採用・著者の主張と帰結提示・式表示を既存関係で合成し、新しい一般基本関係は加えない。',
 '82設定のうちK・V・波範囲・状況以外の78役割を全称又は存在量化し、名前の76証人も同じ設定を共有する。側は真偽値として保持する。全関数・実数の域を有限対照へ縮めず、引用した内容の真理を帰属時に実行しない。',
 'u0220以降のKへの再変換、原刊M0376、光圧の仕事による導出と近似、二作品全体は未完。',
]

def name_witnesses(field):return [(n,t) for n,t in SETTING if n not in {'wave','frame','light','scope','context',field}]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);zero=k('bb','n p a b')
    amps,shifted,_,_=transformed(v('speed'));refamps=[amps[0],k('be',amps[1]),k('be',amps[2]),k('be',amps[3]),amps[4],amps[5]]
    refnormal=[k('be',shifted[1]),shifted[2],shifted[3]];line=[app(k('ekgc',*args(GEOMETRY)),k(a)) for a in ('yn','yo','yp')]
    magnitudes=[k('ekhz',v('magneticside'),*coefs,v(name)) for coefs,name in [([v(n) for n in ('ex','ey','ez','hx','hy','hz')],'amplitude'),(amps,'newamplitude'),(refamps,'refamplitude')]]
    angle=k('ekgf',*refnormal,*line,*[v(n) for n in ('refanglecos','refanglesin','refratio','refprincipal','pi','refangle')])
    text+=define('ekrz',SETTING,both(k('ekrf',*args(MIRROR)),k('ekgn',*args(LINE_SETTING)),*magnitudes,angle,k('ekc7',*args(HARMONIC),shifted[0],zero,v('refperiod'),v('reffrequency'))))
    text+=define('ekr2',[(n,R) for n in ('light','speed','value','anglecos')],k('ekdr',v('light'),v('speed'),v('value'),v('anglecos')),R)
    text+=define('ekr3',SETTING,both(k('sca',v('newamplitude'),k('ekr2',v('light'),v('speed'),v('amplitude'),v('anglecos'))),k('sca',v('newanglecos'),k('sdo2',v('light'),v('speed'),v('anglecos'))),k('sca',v('newfrequency'),k('ekr2',v('light'),v('speed'),v('frequency'),v('anglecos')))))
    text+=define('ekr4',SETTING,both(k('sca',v('refamplitude'),v('newamplitude')),k('sca',v('refanglecos'),k('be',v('newanglecos'))),k('sca',v('reffrequency'),v('newfrequency'))))
    for rule,symbol,field,label in NAMES:
        fixed=dict(FIXED,context=v('context'),wave=v('object'));fixed[field]=v('value')
        text+=define(rule,[('object','a'),('value',R),('context','d')],quantified('g',name_witnesses(field),k('ekrz',*[fixed.get(n,v(n)) for n,t in SETTING])))
    groups=[('eksj',(0,3,6)),('eksk',(1,4,7)),('eksl',(2,5,8))]
    for name,indices in groups:text+=content(name,both(*(k('eislo',k(NAMES[i][1]),'r[p '+NAMES[i][0]+']',k('eirf'),v('point')) for i in indices)))
    actual=[FIXED.get(n,v(n)) for n,t in SETTING]
    text+=content('eksm',quantified('g',VARIABLES,k('ekrz',*actual)))
    for name,result in [('eksn','ekr3'),('ekso','ekr4')]:text+=content(name,quantified('f',VARIABLES,op('y',k('ekrz',*actual),k(result,*actual))))
    p=v('point');author=k('rd');scope=k('eistk');node=k('eisuh');display=k('eisui')
    text+=content('eksp',both(evaluate('eksj'),k('eislz',node,author,quote('eksm'),scope,p),k('ug',node,author,quote('eksm'),scope,p),k('eissb',node,k('eisue'),author,quote('ekrg'),quote('eksm'),scope,p),k('uh',node,author,quote('eksn'),scope,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('eksq',both(evaluate('eksk'),k('eisox',display,quote('eksn'),p)))
    node=k('eisuj');display=k('eisuk')
    text+=content('eksr',both(k('zc',node,author,quote('eksm'),quote('ekso'),scope,p),k('eisra',node,author,k('eirf'),k('eisuh'),quote('eksm'),quote('ekso'),scope,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ekss',both(evaluate('eksl'),k('eisox',display,quote('ekso'),p)))
    for shown,msg,stmt,node,previous in [('eksp','ekst','eksu','eisuh','eisug'),('eksq','eksv','eksw','eisui','eisuh'),('eksr','eksx','eksy','eisuj','eisui'),('ekss','eksz','eks2','eisuk','eisuj')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(node),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==396
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eksu','eksw','eksy','eks2')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_incident_and_reflected_k_quantities_with_literal_angle_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/reflected-light-inquiry-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=symbol,role='designation',forms=[dict(text=label,language='de',role='printed_identifying_form')]) for rule,symbol,field,label in NAMES]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
