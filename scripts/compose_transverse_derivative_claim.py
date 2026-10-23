"""Connect all transverse trials and local calculus to the author's conclusion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_light_trial import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-transverse-light-trial.noema';PARENT_BASIS='data/transverse-light-trial-basis-v1.json'
FULL='examples/v014/einstein-transverse-derivative-claim.noema';CORE='examples/v014/transverse-derivative-claim-core.noema'
BASIS='data/transverse-derivative-claim-basis-v1.json';ANNOTATIONS='data/transverse-derivative-claim-identifiers-v1.json';INDEX=284
MEANINGS={
 'ei34':'指定横方向試行の同じ出発出来事から補助x-vt,y,zとK時刻を取り、その同じ地点・距離候補zek・成分候補zelを現在の完全試行ei32へ結ぶ。両光区間を存在量化し、候補値を座標差・両伝播時間・全光軌道から切り離さない。',
 'ei35':'指定設定の全測定履歴、同じτ候補の全対応と全k指示、全K時計と全光速度原理を保つ。完全な横方向試行範囲zej/zemの両軸が非空であり、全ての選択試行が同じ設定のei34を満たす。全速さVと横成分√(V²-v²)を区別し、常にを二標本だけへ縮めない。',
 'ei36':'横軸に沿う伝播をKから見た成分速度と現在の全横方向試行ei35を、基準設定zb6について述べる内容。',
 'ei37':'同じ全横方向試行ei35と同じ候補τ・同じ出発時刻・横成分速度について、全空間点の両横方向の正近傍中点条件と局所全微分可能性・偏微分をsllへ結ぶ内容。先行する十分な正則性の読みを引き継ぐ。',
 'ei4a':'著者が同じ第三節で横方向の伝播条件ei36を述べ、その条件に注意を向ける内容。wenn man beachtetを独立した無条件の証明や当然性へ変えない。',
 'ei4b':'横方向の伝播条件と注意喚起ei4aを述べるメッセージ。',
 'ei4c':'u0059の横方向の伝播と注意条件を同じ著者・論説へ帰属し、任意の出発点の全空間への帰結に続ける。',
 'ei4d':'同じ横方向の全試行と局所微分の前提ei37から、同じτの両横偏微分が全空間値で零であるslvが得られるという著者の提示。先行の縦方向の微分推論zeaに類似する論法であることをzepで保持する。',
 'ei4e':'横方向へ適用した類似推論と二つの零偏微分への帰結ei4dを述べるメッセージ。',
 'ei4f':'u0059の類似推論とu0060/u0061の二つの式を同じ著者・論説へ帰属し、同じ文の伝播条件に続ける。',
}
LIMITS=[
 'u0059全225文字・172本文文字とM0106–M0108、表示式だけのu0060 M0109とu0061 M0110を一つの文と二式として扱う。類似議論・二横軸・条件への注意・Kからの視点・常に・平方根の速度と両零偏微分を保持する。',
 '固定抽出のH・Zと原刊の対応字形を保存する。H・Zは運動系のη・ζ方向の軸表記として読み、既出のK/k軸の平行性を通じて補助座標のy,zへ接続する。Hを新しい第四軸とせず、固定原文をYへ書き換えない。',
 '静止系Kの全光速Vと、運動する横軸に沿う成分w=√(V²-v²)を区別する。同じ光はKで縦成分vを持ち、往復で横成分だけが反転する。現在の全軌道・同じ三出来事・局所時計・幾何学的経路長へ接続し、Kでの全速さがwであるとはしない。',
 'stetsは、理想的な試行を含む明示した全範囲zej/zemに対する全称条件として保持する。両横方向の非空性と全選択試行を要求し、結果が一致する二標本だけを抜き出さない。全範囲の物理的実現を有限評価が証明したとはしない。',
 '全τ対応と全k時計指示は同じ候補zd4・同じ設定で保つ。局所の正近傍・全微分可能性・二偏微分は同じτと同じ点・時刻へ結ぶ。全空間への適用は先行u0058の範囲を引き継ぎ、時刻は同じ出発時刻のパラメータとする。',
 '同様の議論は、前の正側極限と十分な局所正則性を横方向へ適用する読みとする。中点の時間項が両辺で同じとなることと、実際の偏微分が零であることを区別し、単なる数値係数の零や独立した二つのτ候補にしない。',
 'wenn man beachtetは伝播条件に注意して推論するという読み、analoge Überlegungは先行する縦方向推論への参照として保持する。著者・同じ第三節・論説と本文順序を結び、引用した帰結を実行して一般物理的導出の自動証明へ替えない。',
 '新規原始語はない。既存の軸引数交換、平方根、局所微分と全空間条件を再利用し、全実数の量化は有限評価を拒否する。u0062以降の線形性からの具体的τ解・未定係数・原点時刻の選択は先取りしない。',
]

def definitions():
    trial=v('trial');axis=v('axis');ctx=v('context');depart=k('qe',trial);tup=k('zdz',depart,k('ra'),ctx)
    t=k('sjh',depart,ctx);coord=lambda a:k('zc6',tup,k(a));x=k('sin',k('zb7'),coord('yn'),t)
    body=k('ei32',trial,axis,k('qc',trial),v('outward'),v('returning'),k('zek',trial,ctx),k('zel',trial,ctx),x,coord('yo'),coord('yp'),t,ctx)
    text=define('ei34',[('trial','a'),('axis','a'),('context','d')],q('g','outward','a',q('g','returning','a',body)))
    allowed=op('x',op('e',axis,k('yo')),op('e',axis,k('yp')))
    rows=[q('g','history','a',k('ei3d',ctx,v('history'))),k('ei3c',k('zd4'),ctx),k('eiyf',k('ra'),ctx),k('eios',k('tc'),ctx),k('zem',ctx),k('skz',k('tc'),k('zb7'),k('sle',k('tc'),k('zb7')))]
    rows += [op('u',op('e',k(a),k(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp'))]
    rows += [q('g','trial','a',k('zej',trial,k(role),ctx)) for role in ('yo','yp')]
    rows.append(q('f','trial','a',q('f','axis','a',op('y',k('zej',trial,axis,ctx),both(allowed,k('ei34',trial,axis,ctx))))))
    text+=define('ei35',[('context','d')],both(*rows))
    time=k('sjh',k('qe',k('zdq')),k('zb6'));w=k('sle',k('tc'),k('zb7'))
    text+=content('ei36',k('ei35',k('zb6')))
    text+=content('ei37',both(k('ei35',k('zb6')),k('sll',k('zd4'),time,w)))
    text+=content('ei4a',both(k('uh',k('zen'),k('rd'),quote('ei36'),k('eisms'),v('point')),k('zei',k('zen'),k('rd'),k('eisms'),v('point'))))
    text+='d ei4b[] f[j s[k ei4a[]]].\n'
    def author(name,node,message,previous):return define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    text+=author('ei4c','zen','ei4b','zeh')
    text+=content('ei4d',both(k('zc',k('zeo'),k('rd'),quote('ei37'),quote('slv'),k('eisms'),v('point')),k('zep',k('zeo'),k('rd'),k('zea'),k('eisms'),v('point'))))
    text+='d ei4e[] f[j s[k ei4d[]]].\n';text+=author('ei4f','zeo','ei4e','zen')
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ei4c','ei4f')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_transverse_trials_and_zero_partial_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/transverse-light-trial-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
