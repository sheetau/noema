"""Connect the same point's current histories to substitution and a motion question."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_point_motion_records import ROOT,read
from scripts.compose_origin_clock_question import tracks
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-velocity-opening-claim.noema';PARENT_BASIS='data/velocity-opening-claim-basis-v1.json'
FULL='examples/v014/einstein-point-motion-transform.noema';CORE='examples/v014/point-motion-transform-core.noema'
BASIS='data/point-motion-transform-basis-v1.json';ANNOTATIONS='data/point-motion-transform-identifiers-v1.json'
PATH='h[a '+R+'] '+R
MEANINGS={
 'ejne':'同じ点・出来事・状況に対するKとkの現在記録を、それぞれの場所を共有するejmsへ結ぶ。両記録の時刻値や場所個体の一致を要求しない。',
 'ejnf':'同じ点のK/k二記録が一つの出来事を共有してejneを満たす。別の出来事から片側ずつ記録を取らない。',
 'ejng':'同じ現在状況zb6で両系の完全な履歴ejmuを保ち、対象とする出来事の全範囲を両方向で一致させる。全ejnf対を§3の現在の全座標範囲と同じ出来事対応eiyz/eiy2/eiyyへ結ぶ。数値方程式の成否で候補を選ばない。',
 'ejnh':'同じV,v,wξ,wη,x,y,z,tについて既存sytの三運動式を用い、正のβを1/√(1−(v/V)²)へ結ぶ。分母V²+v*wξは非零で正負を許す。原文の商はこの定義域で分母を払った同値な三等式として表す。',
 'ejni':'同じK/k二記録について係数1の四座標変換ssnと、k側のξ=wξτ・η=wητ・ζ=0を連言する。同じ二定数を用い、式へ代入する出来事・座標成分を共有する。',
 'ejnj':'同じ点に用いるV,vと二定数で、指定K記録の三位置と時刻がejnhの三式を満たす。kの時刻τを結果のtへ置き換えない。',
 'ejnk':'同じ点の両系の全現在履歴と§3への対応ejngについて、全ejnf対が代入前の二組の方程式ejniを満たす。選択した成功対だけの一致に限定しない。',
 'ejnl':'同じ点の両系の全現在履歴ejngについて、Kの全現在記録ejmzが変換後の三式ejnjを満たす。時刻のない位置一覧や別の点の軌道に替えない。',
 'ejnm':'同じ対象・系・状況の完全な現在履歴について、候補関数が各対象実時刻と三軸を受け、実際の代表位置の各有効な値と一致する。答えは三位置の時間依存として与え、等速性・零原点・特定の変換公式を候補の型から要求しない。',
 'ejnn':'直前の点の設定ejmxを共有し、その同じ点zkbのKでの全期間の運動をejnmで表す関数を求める質問。候補を作ることは答えの存在・一意性・発見済みの断言ではない。',
 'ejno':'同じ点の仮定ejmy、§3の現在の最終変換ejeh、同じ両系の全記録での代入条件ejnk、商の非零分母を合わせる前提内容。分母条件は結果をtの関数として読む定義域であり、点の光速上限を加えない。',
 'ejnp':'同じ点zkbと現在状況zb6についてKの全記録が変換後の三式を満たすejnlの内容。課題提示・代入の発話・著者帰属は別に接続する。',
}
LIMITS=[
 '原刊905頁のu0133–u0134を対象に、先行設定、Kでの運動を求める第一文、§3の変換を使う第二文、結果の三式の意味依存群を整える。課題と代入を述べる著者の発話・§3という参照の提示・二単位全体の意味判断は後続であり、今回の追加で確認済み件数は増やさない。',
 'Bewegungは同じ点の三位置をKの全対象時刻の関数として求めると読む。候補は軸と時刻を受ける関数であり、候補条件は全期間の実際の軌道に一致すること。全域の質問を有限の答え一覧に替えず、候補に結果の三式を先に埋め込まない。',
 '二系で同じ点の同じ出来事の全範囲を追う。各系の対象時刻区間はその系の時計規約に従い、tとτや両区間の端点の数値を同一にしない。全期間の記録の存在・全候補の一致はejmuへ接続し、式の成功を基準に出来事を選ばない。',
 '§3の最終変換は現在のejeh・eiyz/eiy2/eiyyと同じssnである。旧syxのzka/shd範囲に戻らず、既出のK/k・物差し・局所時計・現在の比較状況zb6を保持する。',
 '原文三式はx=(wξ+v)/(1+vwξ/V²)t、y=√(1−(v/V)²)/(1+vwξ/V²)wηt、z=0。正の根と同じβの逆数を明記し、sytの分母を払った三等式と同じ定義域で結ぶ。',
 '1+vwξ/V²≠0を、原文の商でtを独立変数として運動を記す際の明示した定義域と読む。原文に条件が印刷されているとはしない。負の分母・負の成分も許す。零分母でも元の変換と平面式が一致する記録はあり得るが、tの関数としてのこの商の結果に含めない。',
 '数値核の対照例、同じ証人の結合、全候補への適用と全実時刻の候補関数を別々に検査する。全実数・全関数の量化は有限評価を拒否する。実切断の一般的な体の法則や物理的真理を有限例で証明したとはしない。新しい基本記号は追加しない。',
]


def definitions():
    obj=v('object');event=v('event');lab=v('lab');own=v('own');ctx=v('context');K=k('ra');moving=k('zbm')
    fields=[('object','a'),('event','a'),('lab','a'),('own','a'),('context','d')]
    text=define('ejne',fields,bind(('labplace','ownplace'),'a','g',both(k('ejms',obj,event,lab,v('labplace'),K,ctx),k('ejms',obj,event,own,v('ownplace'),moving,ctx))))
    text+=define('ejnf',[f for f in fields if f[0]!='event'],q('g','event','a',k('ejne',obj,event,lab,own,ctx)))
    selected=k('ejnf',obj,lab,own,ctx)
    allpairs=lambda body:bind(('lab','own'),'a','f',op('y',selected,body))
    common=q('f','event','a',op('z',k('ejm3',obj,event,K,ctx),k('ejm3',obj,event,moving,ctx)))
    text+=define('ejng',[('object','a'),('context','d')],both(op('e',ctx,k('zb6')),k('ejmu',obj,K,ctx),k('ejmu',obj,moving,ctx),common,allpairs(both(k('eiyz',lab),k('eiy2',own),k('eiyy',lab,own)))))
    names=('light','speed','longitudinal','transverse','x','y','z','time');V,s,u,w,x,y,z,t=map(v,names);beta=k('soy',V,s)
    text+=define('ejnh',[(n,R) for n in names],both(k('syt',V,s,beta,u,w,x,y,z,t),k('sca',beta,k('sjd',k('stw',V,s)))))
    V=k('tc');s=k('zb7');u=k('zkc');w=k('zkd');zero=k('bb','n p a b')
    coords=lambda rec:[k('zc6',rec,k(a)) for a in ('yn','yo','yp','zc7')]
    text+=define('ejni',[('lab','a'),('own','a')],both(k('ssn',lab,own),k('syr',u,w,*coords(own))))
    text+=define('ejnj',[('lab','a')],k('ejnh',V,s,u,w,*coords(lab)))
    text+=define('ejnk',[('object','a'),('context','d')],both(k('ejng',obj,ctx),allpairs(k('ejni',lab,own))))
    text+=define('ejnl',[('object','a'),('context','d')],both(k('ejng',obj,ctx),q('f','lab','a',op('y',k('ejmz',obj,lab,K,ctx),k('ejnj',lab)))))
    fr=v('frame');time=v('time');candidate=v('candidate');actual=tracks(obj,fr,ctx)
    values=[app(candidate,k(a),time) for a in ('yn','yo','yp')]
    match=both(*(k('ba',a) for a in values),*(k('sca',a,app(f,time)) for a,f in zip(values,actual)))
    text+=define('ejnm',[('object','a'),('frame','a'),('context','d'),('candidate',PATH)],both(k('ejmu',obj,fr,ctx),q('f','time',R,op('y',k('lg',*interval(fr,ctx),time),match))))
    text+='d ejnn[] g['+PATH+'][j v[i[candidate '+PATH+']['+both(k('ejmx',k('zb6')),k('ejnm',k('zkb'),K,k('zb6'),candidate))+']]].\n'
    point=v('point');ev=lambda n:op('t',k(n),point)
    text+=content('ejno',both(ev('ejmy'),ev('ejeh'),k('ejnk',k('zkb'),k('zb6')),op('u',k('sca',k('sys',V,s,u),zero))))
    text+=content('ejnp',k('ejnl',k('zkb'),k('zb6')))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==352;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_point_histories_motion_question_and_transformed_equations_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/velocity-opening-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
