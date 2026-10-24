"""Present the third frame, same-form substitution and scoped group necessity."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_parallel_alternative_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-parallel-alternative-claim.noema';PARENT_BASIS='data/parallel-alternative-claim-basis-v1.json'
FULL='examples/v014/einstein-parallel-group-claim.noema';CORE='examples/v014/parallel-group-claim-core.noema'
BASIS='data/parallel-group-claim-basis-v1.json';ANNOTATIONS='data/parallel-group-claim-identifiers-v1.json';INDICES=(145,146,147,149)
PRIMITIVES={'eispa':([], '第五節の二変換合成で導入する第三座標系を指す小文字k′という呼称個体。対象zloへの命名を別に結ぶ。第三節の大文字K′を指すeisnrとは別の使用である。')}
MEANINGS={
 'ejrj':'前提内容premiseが成立する評価状況を候補の全範囲として、同じ結論内容conclusionをs5kの非空全称で評価する必要性。候補選定は前提だけを用い、結論の真偽によって成功例を選ばない。現在の単独の真理、全ての解釈モデルにおける論理的必然性、義務を同一視しない。',
 'ejrk':'同じ正の有効な実光速度tcと、相異なる三位置・時刻の四役割を固定する数学的な評価前提。変換の族はs46の係数1・共通原点の定義を共有し、群であることや合成則の真理をこの候補条件に含めない。',
 'ejrl':'同じ数学的前提ejrkを満たす非空の全評価状況で、同じ平行変換の族が群をなすs5fが成立するというejrjの必要性内容。数学的解釈は固定し、状況間で光速度・演算・四役割・変換の定義を交換しない。',
 'ejrm':'同じ論説へ第三系zloを導入し、現在の全並進・軸上原点・校正と三零点ejq4を仮定に採用し、k′の呼称を付す。§3の既出K/kの設定eiwvを参照し、既存命名zcgのK/kと同じ二系を保つ。',
 'ejrn':'同じ第三系設定と二回適用ejq7から、同じ四式へ合成速度を代入したejq6を得るという著者の提示。§3の最終四式ejehとKのx/y/z/tの現在の量規則を参照する。式を独立した無条件の主張へ分断しない。',
 'ejro':'直前の現在三系の合成結果ejq6と、その同形式の合成を任意の許容速度・四入力へ適用するs5gを合わせた群の主張の根拠内容。現在の出来事の範囲を数学的な全入力域と同一視しない。',
 'ejrp':'同じ著者・第五節がzluで、その合成結果と全域の合成則ejroから、同じ変換の族の群s5fが分かると提示する。閉性だけを群と呼ばず、結合則・単位元・両側逆・全写像の同一性を保つ。',
 'ejrq':'同じ著者がzm3で数学的必要性ejrlを述べ、それを同じ群の内容s5fへの挿入的補足eisa5にする。wie dies sein mußのdiesを別の公式や第三系の実在に替えず、主節から切り離さない。',
 'ejrr':'第三系の導入・仮定・命名と先行二系参照ejrmを述べるメッセージ。',
 'ejrs':'同形式の四変換と速度置換の帰結ejrnを述べるメッセージ。',
 'ejrt':'合成から群が分かるという提示ejrpを述べるメッセージ。',
 'ejru':'群の主張への挿入的な必要性ejrqを述べるメッセージ。',
 'ejrv':'同じ著者・論説へ第三系の導入を帰属し、過去の別導出zm2からzlrへの本文順序と区別を保持する。',
 'ejrw':'同じ著者・論説へ速度置換の帰結を帰属し、第三系導入zlrから結果zlsへの順序を保持する。906頁の文・式と907頁の動詞trittを同じ帰結として扱う。',
 'ejrx':'同じ著者・論説へ群の提示を帰属し、直前の合成結果zlsからzluへの本文順序と区別を保持する。',
 'ejry':'同じ著者・論説へ、群の主節に挿入された必要性の補足を帰属する。独立した後続の論点や、読者による承認済みの内容へ替えない。',
}
LIMITS=[
 'u0147第一文の過去の別導出は現行ejriで保持する。第二文の第三系導入・条件と同形式の四式、u0148/M0285、u0149冒頭trittと群・挿入句を一つの関連群として原刊906/907頁へ照合する。',
 'k′は第三系zloであり、§3の逆変換第三系zgiとは別である。w=zltはk′のkに対する系速度、前の点のw=zkqとの対応は別導出の補助設定ejrcだけで明示する。§3と同じ四式は校正と共通原点・零時刻の規約を引き継ぎ、任意の原点ずれを速度置換だけから消さない。',
 '原刊のM0285は(v+w)/(1+vw/V²)。時間式も含む同じs4lの速度引数とβへ、この同じ値を渡す。Kのx/y/z/tとk′の対応記録を結び、物理的に実現する全出来事の範囲を全実数四入力の実在と同一視しない。',
 'solche Paralleltransformationenは、同じ光速度・同じ軸・係数1・共通原点の符号付き光速未満の変換族として読む。s5e/fは全実速度・全有効四入力の合成、単位元、両側逆と忠実な対応を構成する。負の速度と零を残し、正速度だけの集合や一般の全方向変換群へ変更しない。',
 'wie dies sein mußは数学的設定に相対的な必要性として読む。ejrkの正の光速度と異なる四役割の前提だけで候補範囲を選び、その非空の全域で同じs5fを要求する。群の成否で候補を選ぶ旧zlzの未説明な選定は使わない。命令・義務・心理的な当然さの全てを同一化する読みではない。',
 '必要性は固定した数学的解釈内の全評価状況への量化であり、演算を変えた全解釈モデルへの量化ではない。数学的な内容が状況に依存しなければ各状況の真偽は同じになるが、非空の前提範囲と全称の条件を省かない。前提を満たす状況がないことから必要性を成立させない。',
 'man sieht darausは著者による根拠からの群の帰結提示。閉性だけから群を導く一般の推論を認定せず、引用された命題・必要性の真理を発話帰属から実行しない。有限対照、保存された有理多項式証拠、全域量化の有限列挙拒否と通読の意味判断を区別する。',
 '過去の別導出の補助設定は物理的な系速度の光速未満条件を持つが、前の点速度の式を狭めない。同じejprに至る手順の著者帰属と、許容規則や一般的導出の健全性を区別した前回の読みを保つ。',
]

def definitions():
    text='r eispa[] a.\n';point=v('point');author=k('rd');paper=k('eirf');scope=k('eisoq');ev=lambda n:op('t',k(n),point)
    candidates='i[subject e reference d scene d]['+op('t',v('premise'),v('scene'))+']'
    text+=define('ejrj',[('premise','e'),('conclusion','e'),('context','d')],k('s5k',v('conclusion'),v('context'),candidates))
    roles=('yn','yo','yp','zc7');zero=k('bb','n p a b')
    text+=content('ejrk',both(k('ba',k('tc')),k('bg',zero,k('tc')),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(roles) for b in roles[i+1:])))
    text+=content('ejrl',k('ejrj',k('ejrk'),k('s5f'),point))
    naming=[k('eisd4',k('zcg'),author,k(sign),k(target),paper,point) for sign,target in (('eisnb','ra'),('eisna','zbm'))]
    text+=content('ejrm',both(k('eisd3',k('zlr'),k('zlo'),paper,point),k('ug',k('zlr'),author,quote('ejq4'),scope,point),k('eisd4',k('zlr'),author,k('eispa'),k('zlo'),paper,point),k('eisov',k('zlr'),author,k('eisms'),quote('eiwv'),paper,point),*naming))
    notation=[k('eislo',k(sign),'r[p '+rule+']',paper,point) for sign,rule in (('eisne','eixv'),('eisnf','eixw'),('eisng','eixx'),('eism5','eiwt'))]
    text+=content('ejrn',both(k('zc',k('zls'),author,quote('ejq7'),quote('ejq6'),scope,point),k('eisov',k('zls'),author,k('eisms'),quote('ejeh'),paper,point),*notation))
    text+=content('ejro',both(ev('ejq6'),ev('s5g')))
    text+=content('ejrp',k('zc',k('zlu'),author,quote('ejro'),quote('s5f'),scope,point))
    text+=content('ejrq',both(k('uh',k('zm3'),author,quote('ejrl'),scope,point),k('eisa5',k('zm3'),author,quote('s5f'),quote('ejrl'),point)))
    for message,body in (('ejrr','ejrm'),('ejrs','ejrn'),('ejrt','ejrp'),('ejru','ejrq')):text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
    for claim,node,message,previous in (('ejrv','zlr','ejrr','zm2'),('ejrw','zls','ejrs','zlr'),('ejrx','zlu','ejrt','zls'),('ejry','zm3','ejru',None)):
        rows=[k('eir3',k(node),author,paper,quote(message),k('ri'))]
        if previous:rows += [k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        text+=define(claim,[],both(*rows) if len(rows)>1 else rows[0])
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejrv','ejrw','ejrx','ejry')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='third_frame_same_form_composition_and_group_necessity',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)+[148]).document
    ann=json.loads(read('data/parallel-alternative-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eispa',role='designation',forms=[dict(text='k′',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
