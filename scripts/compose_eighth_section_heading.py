"""Connect the eighth heading to energy representations and mirror pressure."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,op,both
from scripts.compose_material_relative_frame import define
from scripts.compose_mean_light_energy import TOTAL
from scripts.compose_doppler_infinity import quantified
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-optical-problem-method.noema';PARENT_BASIS='data/optical-problem-method-basis-v1.json'
FULL='examples/v014/einstein-eighth-section-heading.noema';CORE='examples/v014/eighth-section-heading-core.noema'
BASIS='data/eighth-section-heading-basis-v1.json';ANNOTATIONS='data/eighth-section-heading-identifiers-v1.json';INDEX=407
PAIR=[('first',R),('second',R),('firstframe','a'),('secondframe','a'),('context','d')]
FIXED={'frame':v('firstframe'),'light':k('tc'),'scope':k('eisrx'),'context':v('context'),'energy':v('first'),'newenergy':v('second')}
VARIABLES=[(n,t) for n,t in TOTAL if n not in FIXED]
PRIMITIVES={
 'eisvv':([('inquiry','a'),('correspondence','i[h['+R+' '+R+' a a d] c]'),('context','d')],'同じinquiryが、閉じたcorrespondenceにより同じ対象と量へ結ばれる二つの実数値表現について、第一の表示系から第二の表示系へ移す規則とその適用条件を主題とする。対応規則の引数は第一値・第二値・第一表示系・第二表示系・状況の順。対象同一性、何の量か、単位と尺度、表示系の適格性は引用する対応規則で構成する。二数値の単なる列挙・別対象の値の比較・呼称だけの改名と区別する。研究主題の指定であり、特定の公式の真理、変換の発見・証明済み、全域性・可逆性、実際の一例の存在を要求しない。eismrと同種の変換主題を実数値そのものへ型付けし、個体記録への符号化又は実測記録の存在を補わない。'),
 'eisvw':([], '固定原文einstein-1905:u0202の第八節見出しの箇所。既存の第八節区分eistk、直前の第七節末尾eistg、次の密度説明eistlとは別である。'),
}
MEANINGS={
 'ekw7':'同じ光の部分のK及びkにおける二つの平均総エネルギーの対応。第一・第二値を同じ70設定のenergy/newenergyへ渡し、K=ra、k=zbmとその区別を保ち、残る64証人を共有したekmiの平均と空間積分へ結ぶ。V=tcと先行波の考察範囲を保持する。総量比や体積比の結論を対応の前提にしない。',
 'ekxa':'同じ光の同じ部分の平均総エネルギーの二系対応ekw7を、その値表現の変換規則を扱う主題へ結ぶ。エネルギー密度・振幅・仕事への改名ではなく、既存の物理的エネルギーと空間積分を使う。',
 'ekxb':'同じ研究が、完全鏡と光の相互作用・同じ面部分への法線力の平均圧力を保持する設定ekugと、検討する圧力法則ekufを対象に理論的説明・成立条件・導出を扱う。設定と式を別々に引用し、圧力の原式を真として仮定しない。',
 'ekxc':'同じ研究と状況が、光線のエネルギー変換ekxaと完全鏡に及ぼされる放射圧の理論ekxbをともに扱う第八節の複合主題。Theorieは第二項へ明示的に掛かり、第一項を圧力又は両者の同一性へ置き換えない。',
 'ekxd':'第二部に直接属する深さ2・表示番号8の既存区分eistkを、二つの主題ekxcへ結ぶ見出し。第七節末尾eistgから見出しeisvw、次の密度説明eistlへの順序と箇所の相違を保持する。物理法則を述べる本文メッセージとは区別する。',
}
LIMITS=[
 'u0202全体を原刊913頁で照合する。§8、Transformation der Energie der Lichtstrahlen、句点、Theorie des auf vollkommene Spiegel ausgeübten Strahlungsdruckesを保持する。二項の主題を同じ節へ結び、Theorieを第二項の理論的研究として読む。',
 'エネルギー変換は本文が扱う同じ光の部分のKからkへの平均総量の表現変換と読む。源・波・二場・同じ部分と領域・単位・二系の同時断面・位相平均及び空間積分をekmiから再利用する。密度や振幅だけを総エネルギーとしない。引用する代表モデルは前後本文の明示した読みであり、全ての光が球形又は平面波だという見出しの主張を追加しない。',
 '二つの値はnativeな実数値で、実測記録の存在や任意の関数の個体への単射符号化を要求しない。旧新の値・系・同時刻の断面を同一視せず、一つの同じ物理設定の証人を共有する。旧側の零エネルギーを比の都合で排除せず、E′/Eの式を対応の前提にしない。',
 '完全鏡は先行の物質的平面・同伴系での境界条件・入射反射の相互作用と損失の理想化を保持する。放射圧は同じ光の過程が鏡の面部分へ及ぼす力の法線成分を面積と時間で平均した量で、鏡から光への逆の力や支持力を含む合力ではない。ekugはこの設定を、ekufは検討する表示法則を指定する。',
 '理論は規則性・成立条件・他原理との関係・説明・導出を研究するという既存eisthの主題関係として読む。引用された物理設定の現実成立、圧力公式の真理、導出の成功、理論の完成又は実験実施を見出しから要求しない。先行の角の読みと印刷式の不一致を変更しない。',
 '第二部の直接の下位区分で、範囲はu0202–u0226、次の同階層見出しu0227で閉じる。番号8と階層深さ2を区別する。旧主張の配列は変更せず、本文の順序関係で接続する。',
 '有限対照は64証人の各位置と旧新値・二系の結合、二主題の同じ研究と文脈、引用と提示、番号・階層・前後順序を検査する。下位の平均・積分・反射・力は固定した既存証拠を再利用し、全実数・全関数域を有限標本へ置換しない。全単位の意味判断は別の記録で行う。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    correspondence=quantified('g',VARIABLES,k('ekmi',*[FIXED.get(n,v(n)) for n,t in TOTAL]))
    text+=define('ekw7',PAIR,both(op('e',v('firstframe'),k('ra')),op('e',v('secondframe'),k('zbm')),op('u',op('e',v('firstframe'),v('secondframe'))),correspondence))
    topic=[('inquiry','a'),('context','d')];iq=v('inquiry');ctx=v('context')
    text+=define('ekxa',topic,k('eisvv',iq,'r[p ekw7]',ctx))
    text+=define('ekxb',topic,k('eisth',iq,quote('ekug'),quote('ekuf'),ctx))
    text+=define('ekxc',topic,both(k('ekxa',iq,ctx),k('ekxb',iq,ctx)))
    node=k('eisvw');previous=k('eistg');following=k('eistl');p=k('ri')
    text+=define('ekxd',[],both(k('eihq',node,k('eistk'),k('eispb'),k('eirf'),'n p c b','n p i b','r[p ekxc]',p),k('ue',previous,node,p),k('ue',node,following,p),op('u',op('e',previous,node)),op('u',op('e',node,following))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekxd',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='eighth_section_energy_transformation_and_pressure_theory_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/optical-problem-method-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
