"""Connect expression symmetry, its appraisal and the directed axial case."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_velocity_composition_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import call as k,v,op,both

PARENT='examples/v014/einstein-velocity-composition-claim.noema';PARENT_BASIS='data/velocity-composition-claim-basis-v1.json'
FULL='examples/v014/einstein-velocity-axial-claim.noema';CORE='examples/v014/velocity-axial-claim-core.noema'
BASIS='data/velocity-axial-claim-basis-v1.json';ANNOTATIONS='data/velocity-axial-claim-identifiers-v1.json';INDICES=(136,137,138)
MEANINGS={
 'ejpl':'現在の同じU/w/αの取得ejpaを共有し、その同じ光速と単位円成分を持つ印刷式s2tについて、非負二入力の交換に対する関係の不変性s3bを述べる内容。系と点の観測上の役割を交換する主張ではない。',
 'ejpm':'現在の式の対称性ejplの記述へ、同じ評価文脈で注意を向ける価値zldと注目すべき基準zleを適用する。対称性の真理、意外さ、読者の実際の注意と区別する。',
 'ejpn':'直前の合成式zkwを受け、同じ著者・第五節が対称性ejplをzkyで述べる。二箇所の区別と本文順序を保持する。',
 'ejpo':'同じ著者・第五節・対称性の箇所zkyで、その同じ対称性への注目価値の評価ejpmを述べる。',
 'ejpp':'現在の同じ運動と三量ejpaを保ち、kの点速度の横成分が零、非負速さwが正で縦成分と等しいs3iを加える。系速度vの既存の正方向にwも沿うという条件。XとΞは現在の対応した縦軸であり、別の軸を追加しない。',
 'ejpq':'同じ現在の三量ejpaの下で、光速V、系速度v、点の速さw、Kの速さUをs3gへ渡し、U=(v+w)/(1+vw/V²)を述べる。符号付き商の式自体の領域と、現在の正方向の場合を区別する。',
 'ejpr':'同じ状況で、正方向の条件ejppが成り立つなら同じ三量の一次元合成式ejpqが成り立つという条件内容。前提が偽のときの含意を実際の導出例とみなさない。',
 'ejps':'同じ著者・第五節がzlfで、wも対応する縦軸の正方向に進むという前提ejppから、表示式ejpqを得ると提示する。コロンと続く式を同じ帰結へ結ぶ。',
 'ejpt':'同方向条件から表示式を得る提示ejpsを述べるメッセージ。',
 'ejpu':'同方向の場合の帰結提示を同じ著者・論説へ帰属し、対称性への評価zkyから条件と式zlfへの本文順序を保持する。',
}
LIMITS=[
 'u0141の二文全体とu0142/M0263を原刊906頁に照合する。第一文は式の対称性とその注目価値、第二文はwもX（Ξ）軸方向なら得られるという条件付き提示である。',
 '対称性は同じVと角の下で、印刷式s2tの非負二入力を交換しても同じ結果との関係が保たれるという読み。実数域全体への量化を残し、選んだ一組の一致や系と点の意味役割の交換へ縮めない。',
 'bemerkenswertは、その同じ対称性の内容へ注意を向ける文脈上の価値が基準を満たすことと読む。尺度値・閾値を原文へ補わず、真理・意外さ・全読者の反応と同一視しない。',
 'Richtung der X-Achse（Ξ-Achse）は既存の規約に従い正方向への非零運動と読む。横成分が零だけでは逆向きと停止も含むため不十分。auchは既存の正の系速度と点の速度が同じ向きであることへ結ぶ。歴史的な符号規約の唯一の解釈とはしない。',
 '同じ点、K/k、対応する縦軸、現在履歴、座標微分、非負ノルム、角をejpa経由で保つ。式だけの零入力は許すが、零速度に方向を与えない。点の光速未満という後続文の条件をここへ先取りしない。',
 'M0263は二つの分数とVの二乗を含む符号付き一次元商のまま保持する。式の定義域はV>0と非零分母。現在の正方向条件は物理的な適用状況であり、式単独の符号付き入力を削らない。',
 '帰結提示の記述は全実数・全物理モデルでの導出の機械証明ではない。旧多項式証拠、有限の引数対照、全実数量化の有限列挙拒否、原刊の通読判断を区別する。',
 '旧文136–138だけを置換し、旧定義・証拠と既判断を保存する。u0143以降と、u0147のs5mに残る旧s3c/s3mへの接続は別途行う。',
]

def definitions():
    point=v('point');author=k('rd');scope=k('eisoq');setting=k('ejpa',k('zb6'))
    ev=lambda n:'t['+k(n)+']['+point+']'
    text=content('ejpl',both(setting,ev('s3b')))
    text+=content('ejpm',k('s2z',quote('ejpl'),point,'p zld','p zle'))
    text+=define('ejpn',[],both(k('uh',k('zky'),author,quote('ejpl'),scope,k('ri')),k('ue',k('zkw'),k('zky'),k('ri')),op('u',op('e',k('zkw'),k('zky')))))
    text+=define('ejpo',[],k('uh',k('zky'),author,quote('ejpm'),scope,k('ri')))
    text+=content('ejpp',both(setting,k('s3i',k('zkc'),k('zkd'),k('zkq'))))
    text+=content('ejpq',both(setting,k('s3g',k('tc'),k('zb7'),k('zkq'),k('zkp'))))
    text+=content('ejpr',op('y',ev('ejpp'),ev('ejpq')))
    text+=content('ejps',k('zc',k('zlf'),author,quote('ejpp'),quote('ejpq'),scope,point))
    text+='d ejpt[] f[j s[k ejps[]]].\n'
    text+=define('ejpu',[],both(k('eir3',k('zlf'),author,k('eirf'),quote('ejpt'),k('ri')),k('ue',k('zky'),k('zlf'),k('ri')),op('u',op('e',k('zky'),k('zlf')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejpn','ejpo','ejpu')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='symmetry_appraisal_and_directed_axial_consequence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/velocity-composition-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
