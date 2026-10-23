"""Present the velocity-composition heading and the constant planar-motion setting."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_point_motion_records import ROOT,read
from scripts.compose_solid_sphere_geometry import args,bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-point-motion-records.noema';PARENT_BASIS='data/point-motion-records-basis-v1.json'
FULL='examples/v014/einstein-velocity-opening-claim.noema';CORE='examples/v014/velocity-opening-claim-core.noema'
BASIS='data/velocity-opening-claim-basis-v1.json';ANNOTATIONS='data/velocity-opening-claim-identifiers-v1.json';INDICES=(350,351)
RELATIVE=[('firstframe','a'),('secondframe','a'),('context','d')]+[('relative'+a,R) for a in ('x','y','z')]
COMPOSE=[('object','a'),('firstframe','a'),('secondframe','a'),('context','d')]+[(prefix+a,R) for prefix in ('relative','own','result') for a in ('x','y','z')]
RULE='h['+' '.join(t for _,t in COMPOSE)+'] c'
PRIMITIVES={
 'eisoo':([('inquiry','a'),('relation','i['+RULE+']'),('context','d')],'inquiryが、同じ対象と二つの記述基準・適用状況を保持するrelationの下で、第一の三成分量と第二の三成分量から第三の三成分量へ合成する規則とその適用条件を扱う主題である。三量の物理的な意味、同じ対象と二基準、尺度は引用する関係へ接続する。単なる九数値の一覧や成分ごとの通常の加算を意味せず、見出しだけから規則の存在・全域性・一意性・可換性や特定の公式を認定しない。対象・第一基準・第二基準・適用状況・第一量三成分・第二量三成分・第三量三成分という型順を保つ。'),
 'eisop':([('inquiry','a'),('context','d')],'inquiryを、対象とする規則又は命題を、明示する前提と条件から理由を追って導く定理の論述として位置付ける。一般的な説明や単なる定義の仕事と区別するが、この主題の提示だけで証明の完了・妥当性・処理系での機械的証明を主張しない。'),
 'eisoq':([], 'この論説の第五節という文書区分。固定原文u0129から第二部u0151直前のu0150までを含み、第一部の直接の下位区分である。見出しの箇所と表示番号・主題は別に結ぶ。'),
 'eisor':([], '固定原文einstein-1905:u0129の第五節見出しの箇所。第五節という区分そのものと区別する。'),
 'eisos':([], '固定原文einstein-1905:u0131–u0132のwξという識別表記。点zkbのkにおける同じ全期間の縦速度成分をejm7の規則へ結び、系の速度vや位置ξと区別する。'),
 'eisot':([], '固定原文einstein-1905:u0131–u0132のwηという識別表記。点zkbのkにおける同じ全期間の横速度成分をejnaの規則へ結び、縦成分や位置ηと区別する。'),
}
MEANINGS={
 'ejm2':'同じ二系の全固定配置・全比較時点による等速並進eiojと、同じ尺度の三相対速度成分eislcを、指定された三つの有効な実数へ結ぶ。成分ごとの正負や非零を限定せず、原点一つの速度だけで全系の運動を済ませない。',
 'ejm3':'同じ対象・出来事・系・状況について、ejmsを満たす現在記録と場所が存在する。出来事の同一性を保持した、対象期間に属する現在の世界線の範囲である。',
 'ejm4':'同じ二系の相対速度ejm2、同じ点の第二系での三定速度と第一系での三定速度ejmvを結ぶ。両系で対象とする現在の出来事の全範囲は一致し、別々の点や別の期間を合成しない。座標時刻の数値や両系の同時性を一致させる条件ではない。',
 'ejm5':'ejm4の三つの物理的な速度ベクトルを結ぶ合成規則と条件を対象とし、それを前提から導く定理の論述として位置付ける複合主題。通常のベクトル加算や後続の特定公式を見出しの主張へ先取りしない。',
 'ejm6':'第五節を第一部に直接属する深さ2・表示番号5の区分として案内し、速度合成定理ejm5を主題へ結ぶ見出し。直前の地球時計の帰結からの順序を保持する。',
 'ejm7':'指定対象が同じ点zkbであり、kの全期間の平面運動ejmwにおける有効な縦速度成分zkcとvalueが一致する規則。表記wξが意味する同じ定数の参照先として用い、系の速度又は一時点だけの位置値へ替えない。',
 'ejna':'指定対象が同じ点zkbであり、kの全期間の平面運動ejmwにおける有効な横速度成分zkdとvalueが一致する規則。表記wηが意味する同じ定数の参照先として用いる。',
 'ejnb':'著者が同じ第五節で点の平面運動ejmyを仮定として置き、wξ/wηという二表記を同じ対象の全期間に共有する定速度の規則ejm7/ejnaとして説明する内容。設定・三式・wobei以下を一つの発話に保持する。',
 'ejnc':'u0130–u0132の設定と三式、二成分の定数性ejnbを述べるメッセージ。',
 'ejnd':'その同じ設定の発話を同じ著者・論説へ帰属し、第五節見出しの後に置く。後続の運動を求める問いや変換の答えはまだ追加しない。',
}
LIMITS=[
 '原刊905頁の見出しu0129と設定の一文u0130–u0132を全体として扱う。四単位の本文文字は40/102/0/27、七数式要素はX/K/v/k、ξ=wξτ・η=wητ・ζ=0、wξ/wηである。三式の末尾のコンマからwobeiの説明へ続く同じ文として読む。',
 'Additionstheoremは、同じ対象・二系・適用状況における系の相対速度、第二系での点の速度、第一系での点の速度を結ぶ合成規則を、その条件から導く定理の主題とする読み。引用関係の適用条件には二系と全出来事範囲を保持し、二つの裸の数値三組だけから常に唯一の結果が得られるという主張はしない。',
 '見出しは第一部に直接属する深さ2・番号5の節を案内する。次の第二部見出し直前のu0150までが第五節であり、後続の導出や本文全体の意味確認済みをこの見出しから認定しない。',
 'bewegeは同じK/kの既出設定で点の運動を考える仮定として読む。Kの正X方向の系の等速並進は全配置を持つeivzへ、点の二定数と全期間の実際の位置・現在記録はejmwへ接続する。三式の原点を通る条件を保持し、下端時刻を零に固定しない。',
 '点は一つの三座標の世界線として位置を追う運動学的理想化であり、質量・電荷・内部形状を追加しない。点の速度には正負・零を許し、光速未満の制限を先回りして加えない。Kとkの時刻数値・同時刻面は等置しない。',
 'wξ/wηが定数を意味することは、それぞれ同じ点の全期間の縦/横の成分を固定する規則へ表記を結ぶことで保持する。未説明の記号名や別の成分へ置き換えず、表記の引用から実測の実行又は現実での運動の成立を導かない。',
 '新規基本関係は適用条件を保持した三成分量の合成を扱う主題と定理という論述種類の二つであり、残る四記号は区分・箇所・表記の参照。物理的な合成条件と全期間の運動は既存定義から構成し、原文一文の真偽を基本記号へ隠さない。',
 '有限検査は全域の範囲一致・同じ対象の引数・成分と表記・見出しの構造・仮定の提示を調べる。全実数の履歴を有限標本へ替えず、原文全体の判断は別記録にする。u0133以降の運動を求める課題、§3の変換式の代入、結果の三式は後続。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    first=v('firstframe');second=v('secondframe');ctx=v('context');obj=v('object');axes=('yn','yo','yp')
    velocities=[v('relative'+a) for a in ('x','y','z')]
    text+=define('ejm2',RELATIVE,both(k('eioj',first,second,k('ta'),k('rb'),ctx),*(k('ba',x) for x in velocities),*(k('sca',k('eislc',first,second,k('ta'),k('rb'),k(axis),ctx),x) for axis,x in zip(axes,velocities))))
    ev=v('event');fr=v('frame')
    text+=define('ejm3',[('object','a'),('event','a'),('frame','a'),('context','d')],bind(('record','place'),'a','g',k('ejms',obj,ev,v('record'),v('place'),fr,ctx)))
    same=q('f','event','a',op('z',k('ejm3',obj,ev,first,ctx),k('ejm3',obj,ev,second,ctx)))
    text+=define('ejm4',COMPOSE,both(k('ejm2',*args(RELATIVE)),k('ejmv',obj,second,*(v('own'+a) for a in ('x','y','z')),ctx),k('ejmv',obj,first,*(v('result'+a) for a in ('x','y','z')),ctx),same))
    text+=define('ejm5',[('inquiry','a'),('context','d')],both(k('eisoo',v('inquiry'),'r[p ejm4]',ctx),k('eisop',v('inquiry'),ctx)))
    text+=define('ejm6',[],both(k('eihq',k('eisor'),k('eisoq'),k('eisdx'),k('eirf'),'n p c b','n p f b','r[p ejm5]',k('ri')),k('ue',k('zjy'),k('eisor'),k('ri')),op('u',op('e',k('zjy'),k('eisor')))))
    for name,quantity in (('ejm7','zkc'),('ejna','zkd')):
        text+=define(name,[('object','a'),('value',R),('context','d')],both(op('e',obj,k('zkb')),k('ejmw',obj,k('zbm'),k('zkc'),k('zkd'),ctx),k('ba',v('value')),k('sca',v('value'),k(quantity))))
    point=v('point');notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),point) for sign,rule in (('eisos','ejm7'),('eisot','ejna'))]
    text+=content('ejnb',both(k('ug',k('zkg'),k('rd'),quote('ejmy'),k('eisoq'),point),*notation))
    text+='d ejnc[] f[j s[k ejnb[]]].\n'
    text+=define('ejnd',[],both(k('eir3',k('zkg'),k('rd'),k('eirf'),quote('ejnc'),k('ri')),k('ue',k('eisor'),k('zkg'),k('ri')),op('u',op('e',k('eisor'),k('zkg')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==350;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejm6','ejnd')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='velocity_composition_heading_and_current_planar_motion_assumption',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/point-motion-records-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for symbol,form in (('eisos','wξ'),('eisot','wη')):ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
