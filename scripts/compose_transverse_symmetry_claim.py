"""Attribute measured meaning, spatial symmetry and the reciprocal-speed rewrite."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_comparison_scope import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-transverse-comparison-scope.noema';PARENT_BASIS='data/transverse-comparison-scope-basis-v1.json'
FULL='examples/v014/einstein-transverse-symmetry-claim.noema';CORE='examples/v014/transverse-symmetry-claim-core.noema'
BASIS='data/transverse-symmetry-claim-basis-v1.json';ANNOTATIONS='data/transverse-symmetry-claim-identifiers-v1.json';INDICES=(318,319,320,321,322)
PRIMITIVES={
 'eisn2':([('node','a'),('author','a'),('conclusion','i[e]'),('scope','a'),('reference','d')],'authorがnodeで、同じ背景と尺度の下で空間的な配置の向きの変更を特別扱いしないという物理的対称性を理由として、conclusionの内容をscopeで提示する。どの対象・配置・変更・量の範囲で何が不変なのかはconclusionの合成内容へ明示する。理由の種類を示す論述上の帰属であり、その対称性の実験的検証、全物理法則の定理、結論の自動証明や明白さ自体を含意しない。'),
 'eisn3':([], 'u0101末のHieraus folgtからu0102の二つの分数の等値を提示する箇所。直前の測定長不変と後続のoderによるφの等値への書換えを区別するための識別子。'),
}
MEANINGS={
 'ejdk':'直前の同じ横棒の幾何・運動ejclと両端の全対象時刻の現在式ejcm/ejcnを合わせる、長さを得るための前提内容。',
 'ejdl':'現在設定zb6の同じ棒の正の測定長zha(zb6)を、全履歴・同時刻の現在両端記録と同じl/φ(v)の一致ejc2へ結ぶ。',
 'ejdm':'著者が同じ両端式ejdkから測定長ejdlを結論し、その同じ測定内容によって同じφの物理的意味が与えられると提示する。alsoとdamitを、結論と解釈の二つの関係で保つ。',
 'ejdn':'全物質点・固有形状・尺度を保った全方向の理想化した設定群について、同速なら現在測定長が一致するejdeの内容。正負二例だけへ縮めない。',
 'ejdo':'著者がejdnを同じ節の主張として採用し、空間的対称性を理由にして明らかだと提示する。範囲付き主張、理由、明白さを区別し、処理系の物理証明としない。',
 'ejdp':'同じ棒・尺度・固有形状の現在設定zb6と別の逆向き設定zg2における二つの正の測定長を、vと−vの全端点式と測定ejdhへ結ぶ。',
 'ejdq':'方向・向きに依存しないejdnと、その同じ範囲で実際に比較する正負速度の二測定ejdpを合わせる著者の前提。',
 'ejdr':'同じ正負速度の二測定ejdpを保持し、その二つの現在測定長の値が等しいという内容。測定候補の名前だけの等値にしない。',
 'ejds':'著者が一般の対称性と二設定ejdqから、vを−vへ交換しても同じ測定長が変わらないejdrを結論する提示。',
 'ejdt':'同じ二設定の現在測定と正の長さ・非零φを保持するejdpの下で、二分数の等値ejdiと同じφの正負値の等値sskが同値であるという内容。oderを二者択一や片方向の含意へ縮めない。',
 'ejdu':'著者が同じ二測定長の不変ejdrから、二分数の等値ejdiが従うとHieraus folgtの箇所で提示する。',
 'ejdv':'著者が同じ二測定ejdpの下で、二分数の等値ejdiを同じφの正負値の一致sskへ書き換え、同値の内容ejdtを採用する。相反積からのφ=1はまだ加えない。',
 'ejdw':'測定長によるφの意味ejdmを述べるメッセージ。',
 'ejdx':'u0101第一文の結論と物理的解釈を同じ著者・論説へ帰属し、両端座標の提示からの進行を保つ。',
 'ejdy':'対称性を理由とする明白さejdoを述べるメッセージ。',
 'ejdz':'u0101第二文の一般の方向・向きへの不変性を同じ著者・論説へ帰属し、長さによる解釈に続ける。',
 'ejd2':'正負速度の交換でも長さが変わらないejdsを述べるメッセージ。',
 'ejd3':'u0101第三文の正負交換への帰結を同じ著者・論説へ帰属する。',
 'ejd4':'二つの分数の等値への帰結ejduを述べるメッセージ。',
 'ejd5':'u0101末のHieraus folgtとu0102の分数等値を同じ著者・論説へ帰属する。',
 'ejd6':'oderによる同じφの二値の一致への書換えejdvを述べるメッセージ。',
 'ejd7':'u0103のoderとu0104のφの等値・句点を同じ著者・論説へ帰属し、二分数の等値に続ける。',
}
LIMITS=[
 '原刊902頁のu0101–u0104を、Kで測る長さからφの物理的意味へ進む説明、方向一般の対称性と明白さ、正負速度の長さ不変、二つの商の等値、oderによる同値書換えとして読む。M0186の平坦化文字列を積と読まない。',
 '測定長は現在の同時刻両端記録と校正計量から得る正の距離。原文のl/φ(v)との等値は、符号付き商を正の距離へ等置する向きの読みとして明示する。端点式だけが与えるl/|φ(v)|からφの正値を無断で導出したとはしない。',
 '同じ特定の棒は同じ全物質点・固有形状・固有長を保つ。比較する両系と尺度を固定し、配置の位置と向きは変えられる。各系の時刻・区間端や、別設定の時計原点を等置しない。',
 '方向と向きへの独立性は、0<|v⃗|<Vの各速度三成分に適格設定が存在する理想化した比較群で、同速なら長さが等しいという全称として読む。速度零・光速以上は先行する動く系の設定の範囲外。有限実験の網羅や加速による全設定の実現を主張しない。候補選択に長さの等値を含めない。',
 'Aus Symmetriegründenは同じ背景・尺度で空間の向きを特別扱いしないという理由の帰属eisn2、einleuchtendは同じ内容の明白さzdgで保持する。nur von der Geschwindigkeitはこの対称性比較における速度の大きさだけへの依存で、他の独立な物理条件を変える場合まで無条件に同じ長さとしない。',
 '正負交換では同じK/kと同じ棒を保ち、別設定で速度だけを(v,0,0)から(−v,0,0)へ変える。同じφを正負の引数で評価し、K/kの交換や別関数への交換としない。',
 'alsoとHieraus folgtは著者の帰結提示。damitは同じ測定内容による物理的解釈。oderは非零φと同じ正のlを保つ二つの等値の同値書換えであり、単なる選択肢ではない。著者の主張の真理と処理系の検査を分ける。',
 'φ(v)=φ(−v)だけから各値1を導かず、前の相反積との合成と最終四式・βの定義はu0105–u0108へ残す。有限対照・全実数域の拒否・原刊通読を別の証拠として保持する。',
]
GROUPS=(('ejdm','ejdw','ejdx','zhk','zhj'),('ejdo','ejdy','ejdz','zhl','zhk'),('ejds','ejd2','ejd3','zhm','zhl'),('ejdu','ejd4','ejd5','eisn3','zhm'),('ejdv','ejd6','ejd7','zhn','eisn3'))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    point=v('point');author=k('rd');scope=k('eisms');forward=k('zb6');backward=k('zg2')
    ev=lambda n:op('t',k(n),point)
    text+=content('ejdk',both(*(ev(n) for n in ('ejcl','ejcm','ejcn'))))
    text+=content('ejdl',k('ejc2',forward,k('zha',forward)))
    text+=content('ejdm',both(k('zc',k('zhk'),author,quote('ejdk'),quote('ejdl'),scope,point),k('zhf',k('zhk'),author,quote('spc'),quote('ejdl'),scope,point)))
    text+=content('ejdn',k('ejde'))
    text+=content('ejdo',both(k('uh',k('zhl'),author,quote('ejdn'),scope,point),k('eisn2',k('zhl'),author,quote('ejdn'),scope,point),k('zdg',k('zhl'),author,quote('ejdn'),scope,point)))
    text+=content('ejdp',k('ejdh',k('zha',forward),k('zha',backward)))
    text+=content('ejdq',both(ev('ejdn'),ev('ejdp')))
    text+=content('ejdr',both(ev('ejdp'),k('sca',k('zha',forward),k('zha',backward))))
    text+=content('ejds',k('zc',k('zhm'),author,quote('ejdq'),quote('ejdr'),scope,point))
    text+=content('ejdt',op('y',ev('ejdp'),op('z',ev('ejdi'),ev('ssk'))))
    text+=content('ejdu',k('zc',k('eisn3'),author,quote('ejdr'),quote('ejdi'),scope,point))
    text+=content('ejdv',both(k('zd3',k('zhn'),author,quote('ejdp'),quote('ejdi'),quote('ssk'),scope,point),k('uh',k('zhn'),author,quote('ejdt'),scope,point)))
    for value,message,claim,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+value+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='measured_phi_meaning_spatial_symmetry_and_signed_rewrite',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/transverse-comparison-scope-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
