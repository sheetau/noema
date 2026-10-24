"""Name the same two volumes and present their ratio by a simple calculation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_ellipsoid_surface import ROOT,read,SETTING,GEOMETRY,FIXED,VARIABLES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_calculation_discourse import STEP,STEPS
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-light-ellipsoid-surface.noema';PARENT_BASIS='data/light-ellipsoid-surface-basis-v1.json'
FULL='examples/v014/einstein-light-volume-ratio.noema';CORE='examples/v014/light-volume-ratio-core.noema'
BASIS='data/light-volume-ratio-basis-v1.json';ANNOTATIONS='data/light-volume-ratio-identifiers-v1.json';INDEX=391
PRINTED=[(n,R) for n in ('light','speed','anglecos')]
RATIO=PRINTED+[(n,R) for n in ('volume','newvolume')]
VOLUMES=GEOMETRY+[(n,R) for n in ('pi','volume','newvolume')]
NAME=[('object','a'),('value',R),('context','d')]
PRIMITIVES={
 'eistw':'u0208の同じ球と楕円体の体積をS/S′と名づけ、簡単な計算が示す比を導入する本文箇所。',
 'eistx':'u0209=M0362のS′/Sの体積比を表示する箇所。',
 'eisty':'同じ光の部分の旧系同時球内部の体積を示す、この箇所での量記号S。',
 'eistz':'同じ光の部分の新系同時楕円体内部の体積を示す、この箇所での量記号S′。',
}
MEANINGS={
 'ekox':'印刷された√(1−(v/V)²)/(1−(v/V)cosφ)を実数演算で構成する。正の平方根を分子に置き、余弦の符号と分母を保つ。',
 'ekoy':'有効なV,v,cosφ,S,S′、許容速度s45、−1≤cosφ≤1、正の二体積と分母の下で、S′/Sがekoxに一致する条件。比の向きを逆にしない。',
 'ekoz':'同じ68設定のV,v,角の余弦と二体積をekoyへ渡す。別の波・部分・角又は独立に選んだ二つの体積を結論に持ち込まない。',
 'ekpa':'対象objectと状況contextについて、K,V,波範囲を固定し、同じekn7設定の旧系volume=valueとなる残余証人を存在量化する量記号Sの取得規則。内部の体積であり表面積ではない。',
 'ekpb':'ekpaと同じ物理部分・校正体積の規則で、新系newvolume=valueを指定する量記号S′の取得規則。各系自身の零時刻を使う。',
 'ekpc':'同じ論説・状況でSとS′をそれぞれekpa/ekpbの型付き量取得規則へ結ぶ命名。命名の慣習自体を自然法則又は新たな物理仮説にしない。',
 'ekpd':'同じ63役割のekn7を前件に、その同じ球と楕円体の二つの積分sedp及びcosφ=aを述べる計算前提の内容。積分からの体積比を前件へ追加しない。',
 'ekpe':'同じ63役割のekn7を前件に、同じ体積・角のekozを帰結とする表示内容。全実数と物理設定を有限標本へ縮めない。',
 'ekpf':'同じ著者・状況で利用できる一つの有限計算列が、引用したekpdからekpeへ許容変形で接続し、その同じ列の非負負担の和が低いとするs2yの内容。固定手数・閾値・実行済み履歴を補わない。',
 'ekpg':'S/S′の命名ekpc、著者による体積比と計算容易性の主張、コロンから式への導入・表示・順序、直前の同じ楕円体面への照応を結ぶ。一つの計算の始点と終点を共有し、著者の主張を機械的証明と混同しない。',
 'ekph':'同じ二体積の命名・比・簡単な計算による提示を述べるメッセージ。',
 'ekpi':'u0208–u0209の一続きの文を同じ著者と論説へ帰属し、楕円体面と零時刻式の説明に続ける。',
}
LIMITS=[
 '原刊913頁のu0208–u0209を一文として読む。Nennt manは量記号の導入、so istはその記法による帰結、wie eine einfache Rechnung zeigtは同じ帰結への計算による根拠と容易性の著者評価である。',
 'S/S′は同じ部分zvaaの旧系t=0の球と新系τ=0の楕円体の閉内部の体積。面積や同じ出来事集合の二座標表示ではない。既存ekl4とsedpの積分、共通長さ単位の三乗、同じ物理部分の領域履歴を引き継ぐ。',
 'φは先行する光の進行方向と正の標準軸速度の角であり、ekn7→eklp→eklf→eket→ekdqの既存条件によりcosφ=aを共有する。新しい自由角を導入しない。純粋な比関数は零・符号付き亜光速も扱うが、著者の設定は既存ekevの0<v<Vを保つ。',
 '二つの量名の取得規則は存在証人を使うが、比の主張と計算の両端は一つの同じ68設定からの全称条件である。独立した二対象の値を組み合わせない。命名を外的仮説として比の真理の前件へ加えない。',
 '二体積の積分を計算前提、比を帰結として分離する。D*S′=Sとβ=1/√(1−(v/V)²)から印刷比へ移す。既存積分補題は有理多項式の原始関数と端点の証拠であり、全実数の積分論・変数変換定理又はπの存在を自動証明したとはしない。',
 '簡単な計算は同一の前提・帰結を結ぶ有限許容列への低負担評価として読む。著者の計算の各中間式、具体的な計算量閾値又は実施済み記録を原文へ追加しない。原文の主張、有限評価、有理補題、意味判断を区別する。',
 '有限の有理数対照はπの積分的意味の代用ではない。無限実数・関数域は有限評価を拒否する。次のE/E′命名と総エネルギー比、二作品全体は未完。',
]

def name_variables(which):
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'portion':v('object'),'context':v('context'),which:v('value')}
    return fixed,[(n,t) for n,t in SETTING if n not in fixed]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);zero=k('bb','n p a b');one=k('bb','n p b b');minus=k('be',one)
    mul=lambda a,b:k('shv',a,b);V=v('light');speed=v('speed');co=v('anglecos');ratio=mul(speed,k('sjd',V));den=k('bf',one,mul(ratio,co))
    text+=define('ekox',PRINTED,mul(k('sky',k('bf',one,mul(ratio,ratio))),k('sjd',den)),R)
    text+=define('ekoy',RATIO,both(*(k('ba',x) for x in args(RATIO)),k('s45',V,speed),k('bc',minus,co),k('bc',co,one),k('bg',zero,v('volume')),k('bg',zero,v('newvolume')),k('bg',zero,den),k('sca',mul(v('newvolume'),k('sjd',v('volume'))),k('ekox',*args(PRINTED)))))
    text+=define('ekoz',SETTING,k('ekoy',*args(RATIO)))
    for name,which in [('ekpa','volume'),('ekpb','newvolume')]:
        fixed,variables=name_variables(which);text+=define(name,NAME,quantified('g',variables,k('ekn7',*[fixed.get(n,v(n)) for n,t in SETTING])))
    p=v('point');author=k('rd');node=k('eistw');display=k('eistx');scope=k('eistk')
    text+=content('ekpc',both(*(k('eislo',k(sign),'r[p '+rule+']',k('eirf'),p) for sign,rule in [('eisty','ekpa'),('eistz','ekpb')])))
    setting=[FIXED.get(n,v(n)) for n,t in SETTING];volumes=[FIXED.get(n,v(n)) for n,t in VOLUMES]
    premise=both(k('sedp',*volumes),k('sca',v('anglecos'),v('ax')))
    for name,target in [('ekpd',premise),('ekpe',k('ekoz',*setting))]:text+=content(name,quantified('f',VARIABLES,op('y',k('ekn7',*setting),target)))
    easy=k('s2y',k('zlx',v('method'),p),quote('ekpd'),quote('ekpe'),'i[before i[e] after i[e]][k zla[v before v after v point]]','i[step '+STEP+'][k zlb[v step v point]]','i[burden b][k zlc[v burden v point]]')
    text+=content('ekpf',quantified('g',[('method','a')],both(k('zlw',author,v('method'),p),easy)))
    text+=content('ekpg',both('t[k ekpc[]][v point]',k('uh',node,author,quote('ekpe'),scope,p),k('uh',node,author,quote('ekpf'),scope,p),k('eisox',display,quote('ekpe'),p),k('uf',author,node,display,p),k('ue',node,display,p),k('eisra',node,author,k('eirf'),k('eistu'),quote('ekos'),quote('ekpd'),scope,p)))
    text+='d ekph[] f[j s[k ekpg[]]].\n'
    text+=define('ekpi',[],both(k('eir3',node,author,k('eirf'),quote('ekph'),k('ri')),k('ue',k('eistu'),node,k('ri')),op('u',op('e',k('eistu'),node)),op('u',op('e',node,display)),op('u',op('e',k('eisty'),k('eistz')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekpi',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_radiation_volumes_named_and_ratio_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/light-ellipsoid-surface-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for n,form in [('eisty','S'),('eistz','S′')]:ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
