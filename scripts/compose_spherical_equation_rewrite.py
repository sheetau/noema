"""Connect the sphere-equation rewrite and its same-calculation assessment."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rest_spherical_wave import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q
from scripts.compose_calculation_discourse import STEP,STEPS

PARENT='examples/v014/einstein-rest-spherical-wave.noema';PARENT_BASIS='data/rest-spherical-wave-basis-v1.json'
FULL='examples/v014/einstein-spherical-equation-rewrite.noema';CORE='examples/v014/spherical-equation-rewrite-core.noema'
BASIS='data/spherical-equation-rewrite-basis-v1.json';ANNOTATIONS='data/spherical-equation-rewrite-identifiers-v1.json';INDEX=306
MEANINGS={
 'ejae':'同じ波zfuが同じ放出zfvからKで到来する一つの対象出来事を、現在のK記録firstとk記録secondへ同じ設定で結ぶ。両記録を別の出来事から取らない。',
 'ejaf':'任意の現在K到来記録に同じ出来事の現在k記録が存在し、同じ到来出来事に結び付く全K/k記録対ejaeについて、k側の同じ四成分がξ²+η²+ζ²=V²τ²を満たす内容。到来をkでの正時刻や全波面の成立へ先取りしない。',
 'ejag':'現在のK球面波ei77、任意の到来点のK式ejaa、同じ四変換式ei7cと全対象出来事の現在両系記録ei3aを、球面式の書換え前提として合わせる。全て同じ物理設定zb6と同じV,v,φに属する。',
 'ejah':'同じ著者が同じ評価文脈で利用できる方法が存在し、その方法の同じ非空有限手順列が前提ejagから結果ejafへ許容された変形でつながり、各手順の非負負担の合計が文脈上の低負担基準に入る。別方法の容易さや内容の真理で代用しない。',
 'ejai':'同じ著者・第三節・箇所zgeに、先行K球面式ejaaを前提ejagによってk球面式ejafへ書き換える提示zd3と、その同じ計算が簡単だという評価ejahを結ぶ。',
 'ejaj':'球面式の座標変換と計算の評価ejaiを断定の伝達形式にする。',
 'ejak':'u0089–u0090の計算提示と表示式を同じ著者・論説へ帰属し、先行K球面式の箇所zgdからの順序を保持する。',
}
LIMITS=[
 'u0089の全文とu0090の表示式・句点を原刊901頁へ照合する。Diese Gleichungは直前の同じ波のK球面式ejaa、unsere Transformationsgleichungenは既出の現在の四式ei7cを指す。',
 'wir ... transformieren und erhaltenは著者による論述上の計算提示と読む。読者が実際に計算したことや計算機の実行履歴を加えず、同じ著者・論説・第三節・箇所へ帰属する。',
 '同じ到来出来事の現在K/k記録をejaeで結び、k記録の存在を要求した上で全ての対応するk記録へ式を適用する。任意の到来点を一つの成功点へ固定せず、別の出来事の座標や欠けたk記録による空の全称で済ませない。',
 '四式はei7cの全現在座標範囲を保ち、同じφ(v)=a(v)β(v)、V,vと原点の規約を使う。u0085で述べた一般の加法定数は、この共通零原点の波の設定へ新たに足さない。',
 'ξ²+η²+ζ²=V²τ²は同じk記録の三位置と時刻の二乗式sqkである。二乗式だけから未来側、φの正値やφ=1、kでの全到来波面、二原理の両立性の証明完了を導かない。これらの後続記述はu0091以降へ残す。',
 'einfacher Rechnungは、同じ計算の有限手順列について文脈上の負担合計が低いという明示的な読みを採る。既存s2w/s2x/s2yとzlw/zlx/zla/zlb/zlcを合成し、原文にない手順数・数値閾値・実行時間を固定しない。',
 '低負担の計算は、四式とK波面を含む同じ前提ejagから同じk式ejafまでつながる方法として存在量化する。許容変形の根拠と負担の尺度は既存の意味規約に従い、評価内容の提示から一般的な証明認定を行わない。',
 '保存済みの有理多項式証拠では変換後の球面残差がφ²倍になる。現在の記録・全称範囲・引用・計算評価の有限対照はその接続を検査するものであり、一般実切断上の物理的導出や原文との意味同値の自動証明ではない。',
]


def definitions():
    event,first,second,ctx=map(v,('event','first','second','context'))
    rest=k('ra');moving=k('zbm');wave=k('zfu');emission=k('zfv')
    selected=lambda context:both(k('zc4',event),k('eiyx',event,first,rest,context),k('ei74',wave,emission,event,rest,context))
    text=define('ejae',[('event','a'),('first','a'),('second','a'),('context','d')],both(selected(ctx),k('eiyx',event,second,moving,ctx)))
    setting=k('zb6')
    exists=q('f','event','a',q('f','first','a',op('y',selected(setting),q('g','second','a',k('eiyx',event,second,moving,setting)))))
    equation=q('f','event','a',q('f','first','a',q('f','second','a',op('y',k('ejae',event,first,second,setting),k('sqk',second,k('tc'))))))
    text+=content('ejaf',both(exists,equation))
    text+=content('ejag',both(*(op('t',k(n),v('point')) for n in ('ei77','ejaa','ei7c')),k('ei3a',setting)))
    method=v('method');point=v('point');steps=k('zlx',method,point)
    easy=k('s2y',steps,quote('ejag'),quote('ejaf'),'i[before i[e] after i[e]]['+k('zla',v('before'),v('after'),point)+']','i[step '+STEP+']['+k('zlb',v('step'),point)+']','i[burden b]['+k('zlc',v('burden'),point)+']')
    text+=content('ejah',q('g','method','a',both(k('zlw',k('rd'),method,point),easy)))
    text+=content('ejai',both(k('zd3',k('zge'),k('rd'),quote('ejag'),quote('ejaa'),quote('ejaf'),k('eisms'),point),k('uh',k('zge'),k('rd'),quote('ejah'),k('eisms'),point)))
    text+='d ejaj[] f[j s[k ejai[]]].\n'
    text+=define('ejak',[],both(k('eir3',k('zge'),k('rd'),k('eirf'),quote('ejaj'),k('ri')),k('ue',k('zgd'),k('zge'),k('ri')),op('u',op('e',k('zgd'),k('zge')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejak',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_sphere_equation_rewrite_and_easy_calculation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/rest-spherical-wave-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
