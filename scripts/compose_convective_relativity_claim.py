"""Join a concrete conditional foundation to the same common-law system."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,v,call as k,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_convective_foundation_reading import GLOBAL,typed

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-convective-velocity-interpretation.noema';PARENT_BASIS='data/convective-velocity-interpretation-basis-v1.json'
FULL='examples/v014/einstein-convective-relativity-claim.noema';CORE='examples/v014/convective-relativity-claim-core.noema'
BASIS='data/convective-relativity-claim-basis-v1.json';ANNOTATIONS='data/convective-relativity-claim-identifiers-v1.json';INDEX=411
PRIMITIVES={
 'eiswp':([('law','a'),('condition',typed(GLOBAL)),('consequence',typed(GLOBAL)),('reference','d')],'法則個体lawの物理的内容を、同じ型・順序の設定引数を共有する閉じたconditionとconsequenceによる条件付き規則として指定する対応。同じ物体・場・単位・領域・履歴・物理的contextを両規則へ渡し、適用条件を満たす全設定で帰結を要求する。そのlawについてviが候補記述への適合を、eisbiが各系での一般法則としての成立を述べる際にも、この同じ内容を用いる。文字列の一致、一例の真偽一致、別の意味の同名法則では代用しない。対応自体は法則の真理、各系での成立、候補履歴の適合、系間保存、理論による採用を認定しない。それらは別の合成条件で要求する。'),
 'eiswq':([], '固定原文einstein-1905:u0237のDaからentsprichtまでの一文。第五節による新三速度の同定を理由として、運動学的原理の下でLorentz理論の電気力学の基礎が相対性原理に適合すると示されたという箇所。'),
}
MEANINGS={
 'ek2n':'同じ理論の研究対象ekyvを保ち、同じ一つの研究証人について元のekyo条件とekyqを基礎として採用するeiswaとeisdiを結ぶ。同じlawをその理論の電気力学の法則eisbeに属させ、表示系を引数化したek2lと同じekyqの条件付き内容へeiswpで固定する。Kへの制限が元の条件と一致する前段の構成を共有する。',
 'ek2o':'同じlawが、完全な共通法則体系theoryの電気力学の法則であり、その体系全体がeiffを満たす。同じ個体lawを使うため、この基礎にも全適格系のeisbiと、全候補履歴・全対応記述でのviの保存が及ぶ。理論名だけを同じにせず、eiffの完全性と非空性を保つ。',
 'ek2p':'指定した同じlawを含むek2oの共通法則体系が存在する。Lorentz理論全体をその体系だと固定せず、基礎法則の同じ内容が共通体系へ入ることを要求する。単なる二内容の別々の成立可能性ではない。',
 'ek2q':'同じ評価点で絶対静止に対応する現象特性を否定するeifiを保ち、同じLorentz理論の具体的な条件付き基礎ek2nが共通法則体系へ入るek2pを要求する適合内容。相対性原理eifjの二部分を保ち、その存在する共通体系に指定した基礎法則を接続する。Lorentz理論の未記述の全法則が適合すると拡張しない。',
 'ek2r':'著者の運動学的原理を、既出の相対性原理eifjと真空光速度原理eifyの同じ内容の連言として読む。第一節の時刻規約と第二節の定式化への既存接続を引き継ぎ、二採用行為eif3そのものには替えない。',
 'ek2s':'第五節で既に述べた同じ点の変換された三運動式ejnpと角度付き速度合成則ejpcを併せ、現在の速度同定の根拠として参照する内容。前者の成分と後者の速さを混同せず、原刊の符号付き分母を保持する。',
 'ek2t':'直前の同じ変換結果ekz7と、新しい三速度がkで測った同じ電荷成員の速度であるek2jを結ぶ、damitの議論内容。物理的同定を変換の前提へ逆流させない。',
 'ek2u':'同じ点で運動学的原理ek2rを基礎に置くなら具体的な基礎の適合ek2qを要求する条件付きの結論内容。原理の現実成立や無条件の適合へ強めない。',
 'ek2v':'著者が同じ第五節eisoqの成分・合成則ek2sを参照し、それから新系の実際の速度の同定ek2jが従うと提示する。同じ同定を仮定範囲の主張uhとして述べ、挿入された根拠と主たる理由節を結ぶ。',
 'ek2w':'著者が自らの二原理ek2rを基礎として採用し、相対性原理の呼称を同じ全内容eifjへ固定する。Lorentzの基礎を先行eiswkのekyxへ照応させ、同じ変換と速度同定ek2tから条件付き適合ek2uが示されたとzc/uh/uiで提示する。',
 'ek2x':'同じu0237の第五節参照と速度の同定ek2v、原理の採用・基礎の照応・適合への結論・証明済み提示ek2wを連言する一文全体。',
 'ek2y':'同じ一文全体ek2xを断定の伝達形式にする。引用された法則や著者の推論の真理を処理系が実行しない。',
 'ek2z':'同じ著者rd・論説eirfへ一文のメッセージek2yを帰属し、直前の五等式zqbからの順序と箇所の区別を保つ。',
}
LIMITS=[
 'u0237全文と二数式要素を原刊917頁へ照合する。nichts anderes ist alsは既出の同じ構成ベクトルが実際の電荷成員の新系での三速度であるという同定であり、慣性質量の速度や速さの大きさだけには替えない。',
 'entsprichtは、この節で具体化された条件付き基礎法則の同じ内容が、原理の要求する完全な共通法則体系の一法則として入るという明示した読みを採る。全適格系での法則成立と全候補履歴の全対応記述の適合保存をeiff/eife/eifd/sarへ結ぶ。独立に一つずつ成立し得るだけ、成功する一対だけ、観測済み履歴だけには弱めない。',
 '共通体系の証人はLorentz理論eisv5へ固定しない。元の理論からその具体的な電気力学の基礎を取るのであり、未記述のLorentz理論全体又は全光学法則の相対性適合へ拡張しない。eifiの絶対静止に関する部分も同じ採用原理の下で保持する。',
 '唯一の新しい一般関係eiswpは法則参照と具体的な条件付き内容との対応である。適合や相対性、第五節、Einstein、Lorentz、証明済みという結論をこの関係に含めない。規則の型は既存GLOBALを使い、物理的解釈と法則の帰結は独立した引用を共有設定へ適用する。',
 '運動学的原理は既出のeifj/eifyの同じ内容と読む。第二節のeion/eiotは先行のeislhによる定式化の対応を保持し、異なる範囲の二表現を構文的又は論理的に同一だとはしない。unsererは同じ著者が自らの議論へ採用する声として保持し、読者全員の同意や採用人数を補わない。',
 '第五節の参照は成分変換ejnpとAdditionstheoremの式ejpcを指す明示した読み。既出の平面・定速の一設定から全新流速への一般化が数学的に証明されたとは認定せず、著者が同定はこの定理から従うと述べる役割をzcで保持する。新流速の内容自体はek2jの全設定・全成員・全対象記録であり、参照元の一例へ縮めない。',
 'Da ... so ...とdamit gezeigtは、直前の変換と速度同定を根拠にした著者の帰結と証明済みの位置付けとして読む。ug/uhと条件付き内容ek2uでunter Zugrundelegungを保ち、現在の物理的真理又は処理系が検証した定理へ昇格させない。',
 '原刊M0389の磁気側1/V欠落は旧semfへ保存する。同じ基礎法則は原系形ekyqであり、この著者結論に合わせて印刷結果を修正したり、足りない物理前提を本文へ追加したりしない。新三速度の定義域・両系の記録対応・同じ座標時刻による実微分は前段の規約を引き継ぐ。',
 '有限対照は引用内容の同一性、全称範囲と証人の共有、法則不成立・候補不適合・欠落記録・原理の条件性・提示役割を診断する。全物理履歴・全実数・連続体・原文同義性の自動証明ではない。後続u0238の任意運動での総電荷不変は含めない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    law,theory,ctx=map(v,('law','theory','context'));inquiry=v('inquiry')
    adopted=q('g','inquiry','a',both(k('eiswa',theory,inquiry,'r[p ekyo]','r[p ekyq]',ctx),k('eisdi',theory,inquiry,ctx)))
    text+=define('ek2n',[('law','a'),('theory','a'),('context','d')],both(k('ekyv',theory,ctx),adopted,k('eisbe',law,k('eisbf'),theory,ctx),k('eiswp',law,'r[p ek2l]','r[p ekyq]',ctx)))
    text+=define('ek2o',[('law','a'),('theory','a'),('context','d')],both(k('eisbe',law,k('eisbf'),theory,ctx),k('eiff',theory,ctx)))
    text+=define('ek2p',[('law','a'),('context','d')],q('g','theory','a',k('ek2o',law,theory,ctx)))
    p=v('point');ev=lambda n:op('t',k(n),p)
    text+=content('ek2q',both(ev('eifi'),q('g','law','a',both(k('ek2n',law,k('eisv5'),p),k('ek2p',law,p)))))
    for name,targets in [('ek2r',('eifj','eify')),('ek2s',('ejnp','ejpc')),('ek2t',('ekz7','ek2j'))]:text+=content(name,both(*(ev(n) for n in targets)))
    text+=content('ek2u',op('y',ev('ek2r'),ev('ek2q')))
    node=k('eiswq');author=k('rd');scope=k('eisv6');paper=k('eirf')
    text+=content('ek2v',both(k('eisov',node,author,k('eisoq'),quote('ek2s'),paper,p),k('zc',node,author,quote('ek2s'),quote('ek2j'),scope,p),k('uh',node,author,quote('ek2j'),scope,p)))
    text+=content('ek2w',both(k('ug',node,author,quote('ek2r'),scope,p),k('eisch',k('eiscg'),quote('eifj'),scope,p),k('eiswm',node,author,k('eiswk'),quote('ekyx'),paper,p),k('zc',node,author,quote('ek2t'),quote('ek2u'),scope,p),k('uh',node,author,quote('ek2u'),scope,p),k('ui',author,node,p)))
    text+=content('ek2x',both(ev('ek2v'),ev('ek2w')))
    text+='d ek2y[] f[j s[k ek2x[]]].\n'
    text+=define('ek2z',[],both(k('eir3',node,author,paper,quote('ek2y'),k('ri')),k('ue',k('zqb'),node,k('ri')),op('u',op('e',k('zqb'),node))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ek2z',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='convective_foundation_conforms_to_the_same_relativity_principle',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/convective-velocity-interpretation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
