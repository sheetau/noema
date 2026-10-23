"""Connect signed full-frame translation and two transformations to current records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_phi_determination_intent import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-phi-determination-intent.noema';PARENT_BASIS='data/phi-determination-intent-basis-v1.json'
FULL='examples/v014/einstein-third-frame-geometry.noema';CORE='examples/v014/third-frame-geometry-core.noema'
BASIS='data/third-frame-geometry-basis-v1.json';ANNOTATIONS='data/third-frame-geometry-identifiers-v1.json'
MEANINGS={
 'eja2':'同じ第一系の長さta・時間rbで見た第二系の全固定配置・全比較時点にeiojの等速並進を要求し、共通速度の縦成分を指定した符号付き速度、横二成分を零にする。第二系原点を実際の固定配置に含め、全比較時点の第一系での横二座標を零とし、第一系の縦軸上を動く条件を保つ。軸三組と対応の幾何学sfcを要求し、平行だが横へずれた原点軌道では満たさない。',
 'eja3':'指定した同じ対象出来事で、現在のK/kの共通原点・零時刻ei46に、第三系K′の実際の原点で起こることと現在の四座標記録eiyxの全成分零を結ぶ。出来事を光の放出に限定しない。',
 'eja4':'同じ一つの全対象出来事について、相異なるK・k・K′の三つの現在の測定記録eiyxを結ぶ。旧shdの記録や別出来事の記録を混ぜない。',
 'eja5':'非空の全対象出来事にK・k・K′の現在の記録が存在し、各系内の候補記録は四座標値として一意である。同じ値の別記録を許すsgvを隣接二組で要求し、中間系を共通にする。',
 'eja6':'同じ全対象出来事の全対応三記録にsrfを要求する。K→kへv、同じ中間記録のk→K′へ−vを使い、二回とも同じ正規化後の関数spcの四式を適用する。範囲の非空性と記録存在はeja5と併せて要求する。',
 'eja7':'同じ全対象出来事の全対応三記録に、最後の四成分が最初の対応成分の共通倍率spc(v)*spc(−v)倍であるsrgを要求する。時刻を含む全四成分を保持し、共通倍率が1だとはしない。',
 'ejba':'三系の記録存在・値の一意性eja5と、同じ中間記録を使う二回の四式eja6、四成分全ての共通倍率による最終値eja7を合わせる。印刷された四つの連鎖等式の中間式と最終式を両方保持する。',
 'ejbb':'第三系K′がkに対しその縦軸上を−vで全体として並進し、既存の基準出来事zgkで三原点・三時刻零が一致する設定内容。K′はKともkとも別の系であり、K′とKの同じ単位率や恒等変換は加えない。',
 'ejbc':'現在の四変換式ei7cと第三系の設定ejbb、現在の三記録の存在・値の一意性、同じ四式の二回適用を結論へ渡す前提内容。共通倍率の結果や著者による推論の提示はこの前提とは別である。',
}
LIMITS=[
 'u0093–u0094の第三系設定と二回変換の意味依存群。まだ導入の目的、座標の命名、著者の提示、全文の意味判断を追加しない。完成単位数を増やさない。',
 '全固定配置・全比較時点は既存eisk7/eisla/eislbの意味規約を使う。三軸はsfcで対応させ、以前と同じ四式を適用するための向き・軸の読みを保持する。原点の縦軸上条件を全時点の横座標零へ結び、並進の方向だけでは代用しない。',
 'K′の座標x′は以前の補助変数x′=x−vtとは別の役割である。M0152/M0154の印字Ξはkの縦軸として読む。具体的な呼称の宣言は後続の本文接続へ残す。',
 'M0161のβ(−v)はsrdの正の枝とv²<V²に従う。同じ関数φの正負二引数を使い、φ(v)=φ(−v)、φ=1、共通倍率1、K′とKの恒等変換は仮定しない。',
 '実切断の演算の有限対照と、全対象の存在・値の一意性の有限モデル検査を区別する。有限モデルから全物理世界・全実数での真理や原文との意味同値を証明しない。旧証拠と旧定義を保持する。',
]


def definitions():
    ctx=v('context');zero=k('bb','n p a b');first=v('first');second=v('second')
    fields=[('first','a'),('second','a'),('speed',R),('context','d')]
    origin=k('zbn',second,ctx)
    components=[k('sca',k('eislc',first,second,k('ta'),k('rb'),k(axis),ctx),value) for axis,value in (('yn',v('speed')),('yo',zero),('yp',zero))]
    onaxis=q('f','moment','a',op('y',k('eisla',first,second,v('moment'),ctx),both(*(k('sca',k('ym',origin,v('moment'),first,k('ta'),k(axis),ctx),zero) for axis in ('yo','yp')))))
    text=define('eja2',fields,both(k('eioj',first,second,k('ta'),k('rb'),ctx),k('sfc',first,second,ctx),k('ba',v('speed')),*components,k('eisk7',second,origin,ctx),onaxis))
    event=v('event');third=k('zdz',event,k('zgi'),ctx)
    text+=define('eja3',[('event','a'),('context','d')],both(k('zc4',event),k('ei46',event,k('zdz',event,k('ra'),ctx),k('zdz',event,k('zbm'),ctx),ctx),k('zbv',k('zgi'),k('zbn',k('zgi'),ctx),ctx),k('cb',event,k('zbn',k('zgi'),ctx),k('zgi')),k('eiyx',event,third,k('zgi'),ctx),*(k('sca',k('zc6',third,k(role)),zero) for role in ('yn','yo','yp','zc7'))))
    triples=[('event','a'),('first','a'),('middle','a'),('last','a'),('context','d')]
    text+=define('eja4',triples,both(k('zc4',event),*(op('u',op('e',k(a),k(b))) for a,b in (('ra','zbm'),('ra','zgi'),('zbm','zgi'))),*(k('eiyx',event,v(record),k(frame),ctx) for record,frame in (('first','ra'),('middle','zbm'),('last','zgi')))))
    side=lambda frame:'i[event a tuple a]['+k('eiyx',event,v('tuple'),k(frame),ctx)+']'
    text+=define('eja5',[('context','d')],both(*(k('sgv','p zc4',side(a),side(b),'p shh') for a,b in (('ra','zbm'),('zbm','zgi')))))
    for name,body in (('eja6',k('srf',v('first'),v('middle'),v('last'))),('eja7',k('srg',v('first'),v('last'),k('srh')))):
        predicate=op('y',k('eja4',*[v(n) for n,_ in triples]),body)
        for n,_ in reversed(triples[:-1]):predicate=q('f',n,'a',predicate)
        text+=define(name,[('context','d')],predicate)
    text+=define('ejba',[('context','d')],both(*(k(n,ctx) for n in ('eja5','eja6','eja7'))))
    setting=k('zb6')
    text+=content('ejbb',both(*(op('u',op('e',k(a),k(b))) for a,b in (('ra','zgi'),('zbm','zgi'))),k('eja2',k('zbm'),k('zgi'),k('bf',zero,k('zb7')),setting),k('eja3',k('zgk'),setting)))
    text+=content('ejbc',both(*(op('t',k(n),v('point')) for n in ('ei7c','ejbb')),k('eja5',setting),k('eja6',setting)))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==310;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='third_frame_current_record_dependencies_only',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/phi-determination-intent-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
