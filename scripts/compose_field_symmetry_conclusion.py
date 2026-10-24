"""Connect the symmetry footnote, even coefficient and final six equations."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-inverse-field-claim.noema';PARENT_BASIS='data/inverse-field-claim-basis-v1.json'
FULL='examples/v014/einstein-field-symmetry-conclusion.noema';CORE='examples/v014/field-symmetry-conclusion-core.noema'
BASIS='data/field-symmetry-conclusion-basis-v1.json';ANNOTATIONS='data/field-symmetry-conclusion-identifiers-v1.json'
INDICES=[157,158,159,160,161]
PRIMITIVES={
 'eisp6':([], 'u0168のM0312、同じ第六節の係数の正負速度での偶性を述べる表示箇所。'),
 'eisp7':([], 'u0170のM0313、同じ係数の値1を述べる表示箇所。'),
 'eisqa':([], 'u0172のM0314、共通係数を1とした最終六式の表示箇所。'),
}
MEANINGS={
 'ejvf':'現在の物理的な両場と共通係数付き六式ejuh、逆変換からの積1の内容ejuzを背景にし、同じ旧系の同じ領域内の同じ点でX=Y=Z=L=M=0,N≠0となるsbe2を仮定する比較範囲。非自明な速度反転のv≠0を明示し、応答や偶性を範囲の選定条件にしない。',
 'ejvg':'同じ点の同じN,Vと係数関数で、vを-vへ変えたときの二つのY′が反対符号で同じ絶対値となるsbf2の応答内容。新系の同じ数値座標を固定する読みではなく、同じ旧系の出来事で比較する。',
 'ejvh':'非空の全ての例示的な比較状況ejvfでejvgの応答が必要だという脚注の内容。現実にその場を実測した事実や係数の正値を要求しない。',
 'ejvi':'現在の同じ物理的な両場の設定で、第六節の係数のvと-vでの値が等しいsar2という偶性の内容。v=0の恒等的な場合を排除しない。',
 'ejvj':'同じ現在の設定で、直前の積1のejuzと対称性を理由にした偶性ejviを採る、著者の値1への前提。正値は追加しない。',
 'ejvk':'同じ現在の設定で、同じ第六節の係数が1であるsat2を結論とする内容。ejvjから論理的に自動導出されるという保証ではない。',
 'ejvl':'直前の共通係数付き六式ejuhと係数の値1のejvkを同じ文脈で採用する、最終六式への前提。',
 'ejvm':'現在の物理的な両場と同じ過程・領域を保持し、同じ逆座標写像と混合に係数1を用いるsau2の全六成分・全点での最終六式。',
 'ejvn':'著者が脚注の対称性比較ejvhを理由として偶性ejviを提示し、対称性を理由とする帰属と続く数式表示を保つ。一般の物理的対称性や例からの一般化を処理系が証明したとはしない。',
 'ejvo':'著者が積1と偶性ejvjから値1のejvkをalsoとして結論し、続く数式表示へ結ぶ。負の枝を前提から無断で除かない。',
 'ejvp':'著者が共通係数付き六式と値1のejvlから、われわれの式の最終形ejvmを提示し、その六式の表示へ結ぶ。',
 'ejvq':'脚注の例示的条件の下での応答の必要性ejvhを同じ著者が主張し、空間的対称性を理由として明白だと位置付ける。条件、必要性、理由、明白さを区別する。',
 'ejvr':'同じ論説の偶性の理由箇所zn4に付された著者脚注1)をzoaへ結び、その内容ejvhを理由の一つの具体例として位置付ける。本文の論点から脚注への説明関係を保ち、物理的な時間順序や例の実測を追加しない。',
 'ejvs':'対称性を理由にする偶性とその表示ejvnを述べるメッセージ。',
 'ejvt':'偶性の提示を同じ著者・論説へ帰属させ、直前の積1の表示に続ける。旧文157を置き換える。',
 'ejvu':'積1と偶性を理由にする係数の値1とその表示ejvoを述べるメッセージ。',
 'ejvv':'係数の値1の提示を同じ著者・論説へ帰属させ、偶性の表示に続ける。旧文158を置き換える。',
 'ejvw':'共通係数を除いた最終六式とその表示ejvpを述べるメッセージ。',
 'ejvx':'最終六式を同じ著者・論説へ帰属させ、係数の値1の表示に続ける。旧文159を置き換える。',
 'ejvy':'脚注の仮定例・応答の必要性・対称性による明白さejvqを述べるメッセージ。',
 'ejvz':'脚注全体の内容を同じ著者・論説へ帰属させる。旧文160を置き換える。',
 'ejwa':'脚注の参照・例示・説明ejvrを同じ論説の提示状況で述べる。旧文161の部分的な推論提示を、この本文と脚注の明示的な接続へ置き換える。',
}
LIMITS=[
 '原刊909頁のu0167–u0172を、さらに対称性から偶性が従い、したがって係数は1となり、われわれの式は最終六式となる、という連続した一文群として読む。著者脚注u0282と番号1)の参照も同じ意味依存群へ接続する。',
 '脚注は同じ旧系の同じ領域の一点で五成分が零、Nが非零という仮定例。場全体を定数場に限定せず、同じNとV・尺度・旧系の出来事を保持して速度の符号だけを変える。Y′は対応する新系の出来事で評価され、別の速度でも同じ数値の新座標だとはしない。',
 'numerischer Wertを符号から独立な大きさと読む。速度もY′も大きさを保って符号を反転する。非自明な反転例はv≠0であり、v=0では偶性は同じ引数の恒等である。零のY′同士を厳密な符号反転の証拠にはしない。',
 '脚注の必要性は、直前の六式・積1を背景にする非空の仮定状況全てで応答を要求する読み。候補選択へ応答の成功や偶性を混ぜない。対称性と明白さは著者の理由と評価として別に帰属させ、物理的な実験や定理の証明としない。',
 '積1と偶性だけでは係数-1も残る。本文が値1を結論する提示を記述し、正値・連続性・向きの規約を原文の前提へ無断で補わない。負の枝の反例を保持する。最終六式は著者が採った値1に従って構成する。',
 '原刊909頁のφは直前908頁のψと同じ第六節の係数znz。第三節の座標係数とは区別する。固定原文・MathML・原刊画像を変更しない。脚注の在庫のpage_at_end=921は集めた注の配置であり、原刊の実際の掲載頁は909。',
 '既存の数値・場・内容・必要性・著者帰属・理由・例示・脚注参照の関係を合成し、新しい基本関係を追加しない。有限対照、保存した記号的検証、原文の通読判断を区別し、全実数・全関数域の有限列挙拒否を保持する。',
 '旧文157–161だけを置き換え、他353主張、旧版、既存判断と証拠を保存する。脚注は本文の時間順序へ挿入せず、付された位置と例示の方向で結ぶ。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);p=v('point');a=k('rd');scope=k('zno');paper=k('eirf');ctx=k('ri')
    text+=content('ejvf',both(evaluate('ejuh'),evaluate('ejuz'),evaluate('sbe2')))
    text+=content('ejvg',evaluate('sbf2'))
    text+=content('ejvh',k('ejrj',k('ejvf'),k('ejvg'),p))
    for n,left,right in [('ejvi','ejub','sar2'),('ejvj','ejuz','ejvi'),('ejvk','ejub','sat2'),('ejvl','ejuh','ejvk'),('ejvm','ejub','sau2')]:text+=content(n,both(evaluate(left),evaluate(right)))
    for name,node,premise,result,display in [('ejvn','zn4','ejvh','ejvi','eisp6'),('ejvo','zn5','ejvj','ejvk','eisp7'),('ejvp','zn6','ejvl','ejvm','eisqa')]:
        terms=[k('zc',k(node),a,quote(premise),quote(result),scope,p),k('eisox',k(display),quote(result),p),k('uf',a,k(node),k(display),p),k('ue',k(node),k(display),p),op('u',op('e',k(node),k(display)))]
        if name=='ejvn':terms.append(k('eisn2',k(node),a,quote(result),scope,p))
        text+=content(name,both(*terms))
    text+=content('ejvq',both(k('uh',k('zoa'),a,quote('ejvh'),scope,p),k('eisn2',k('zoa'),a,quote('ejvh'),scope,p),k('zdg',k('zoa'),a,quote('ejvh'),scope,p)))
    text+=content('ejvr',both(k('eisfo',k('zn4'),k('zoa'),paper,'n p b b',p),k('eir5',k('zoa'),a,k('zn4'),quote('ejvh'),p),k('uf',a,k('zn4'),k('zoa'),p),op('u',op('e',k('zn4'),k('zoa')))))
    for value,message,claim,node,prior in [('ejvn','ejvs','ejvt','zn4','eisp5'),('ejvo','ejvu','ejvv','zn5','eisp6'),('ejvp','ejvw','ejvx','zn6','eisp7'),('ejvq','ejvy','ejvz','zoa',None)]:
        text+='d '+message+'[] f[j s[k '+value+'[]]].\n';terms=[k('eir3',k(node),a,paper,quote(message),ctx)]
        if prior:terms += [k('ue',k(prior),k(node),ctx),op('u',op('e',k(prior),k(node)))]
        text+=define(claim,[],both(*terms) if len(terms)>1 else terms[0])
    text+=define('ejwa',[],op('t',k('ejvr'),ctx));return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejvt','ejvv','ejvx','ejvz','ejwa')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='symmetry_footnote_even_coefficient_claimed_unit_and_final_equations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/inverse-field-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
