"""Connect homogeneous four-coordinate increments to the author's affine claim."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_event_coordinate_task import ROOT,read
from scripts.compose_homogeneous_coordinates import VECTOR,MATRIX,MAP
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-event-coordinate-task.noema';PARENT_BASIS='data/event-coordinate-task-basis-v1.json'
FULL='examples/v014/einstein-homogeneity-claim.noema';CORE='examples/v014/homogeneity-claim-core.noema'
BASIS='data/homogeneity-claim-basis-v1.json';ANNOTATIONS='data/homogeneity-claim-identifiers-v1.json';INDEX=273
PRIMITIVES={
 'eisnm':([('node','a'),('task','a'),('document','a'),('context','d')],'同じdocumentでtaskに答えるための主要な検討段階の全範囲にnodeが属する。課題を定式化する以前の準備、同じ段階内の理由・挿入説明とは区別する。成功した段階や都合のよい後続箇所だけを選ばず、本文がその課題に対して展開する主要段階を尽くす。順序、最初の段階、各段階の妥当性や課題の解決は別に合成する。'),
}
MEANINGS={
 'eizc':'前段の全有効な静止系四座標eiyzのいずれかと、同じ四役割shxの値が一致する有効なベクトルの全範囲。旧shzの旧測定条件への依存を更新し、有限標本や隠れた第五成分を意味させない。',
 'eizd':'同じ出来事の現在の四座標対応eiyyと変換の出力が、全K側・k側の有効座標対で過不足なく一致する。sgwの値として一意な対応を保ち、全K側入力で出力が有効である。',
 'eize':'同じ両系・単位・移動後設定の四役割へ正規化した変換siaがeizdを満たし、その全有効入力対と、移動後も範囲内にある全有効四変位についてshsの増分の出発点独立性を満たす内容。この運動学の空間・時間の一様性を、同じ計器規約の座標比較に特権的な場所・時刻がないという操作的な読みで表す。',
 'eizf':'同じ変換siaが現行の出来事対応に一致し、一つの同じ行列と定数ベクトルによるshtのアフィン形で全対象入力を表す。行列や原点定数を入力ごとに選び直さない。',
 'eizg':'全入力に共通する行列と定数ベクトルが存在してeizfを満たすというアフィン性の内容。原点定数を零にせず、係数を発見した事実や原点保存を含意しない。',
 'eizh':'著者が同じ第三節の思考設定で、空間・時間に特権的な出発点を与えないeizeの規約を採用するという性質帰属。一般の物理法則すべてを実験で検証したという報告へ替えない。',
 'eizi':'同じ方程式探索課題の主要検討段階に現在のzdfが含まれ、他の全主要段階に本文順序で先行することを要求する。Zunächstを論説全体の最初や物理的な最早時刻にしない。',
 'eizj':'一様性eizeの採用、その同じ内容を理由にアフィン形eizgが従わなければならないという著者の主張、明白さの提示、先行する方程式探索課題への必要条件、まずという検討順序を合わせる。帰属を処理系による導出証明へ替えない。',
 'eizk':'一様性を理由とした線形性の必要性と明白さeizjを述べるメッセージ。',
 'eizl':'u0047の一文全体を同じ著者・論説へ帰属し、u0046の方程式系探索課題からの本文順序を保持する。',
}
LIMITS=[
 'u0047全129文字・112本文文字を対象とする。Zunächst、ist klar、müssen、wegen、welche wir Raum und Zeit beilegenを省かず、前段の同じ四座標と方程式探索課題へ結ぶ。',
 '一様性は、この運動学で同じ系・計器・尺度の四座標を比較するとき、同じ空間変位・時間変位の比較規則が出発点の場所・時刻に依存しないという読みを採る。前段の実測地点と局所時計へ接続した全座標範囲を使い、単なる任意の記号関数の性質や、全物理法則の一様性一般と同義だとはしない。',
 'shsは空でない全入力範囲の全出発点対と、両移動後の点も範囲内となる全有効四変位を扱う。空間三方向・時間方向・混合変位を含む。零変位や一地点の成功だけで済ませず、全実数の量化を有限試験点へ替えない。',
 'linearは、この段階で原点一致が指定されていないため、各出力量が同じ一つの行列と成分別定数で表されるアフィン形として読む。原点保存・零定数を補わず、任意の非線形な同値表記まで式の見かけが一次であることを要求しない。',
 '三位置成分と一時刻成分の数値を、固定した長さ・時間単位で扱う。行列の混合係数はその単位に従う数値で、時間と長さそのものを同じ量として加える規約ではない。入力・出力の四役割以外をsieで零へ正規化し、隠れた情報を使わせない。',
 '一様性から一般の実数域で行列表示を導く証明は主張しない。原文に明記されない連続性などを仮定へ足して証明済みにせず、著者がその理由で必要だと述べることと、処理系が含意を証明したことを分ける。',
 '同じ現行座標対応に適合する変換のアフィン形を、先行方程式探索課題の必要条件として帰属する。係数の数値、具体的なLorentz変換、解の発見済みは加えない。明白さは著者の提示であり、検査器の自明性認定ではない。',
 'Zunächstはこの課題を検討する主要段階の最初である。課題以前の計器設定や現在段階内の一様性の説明を別の先行主要段階として混ぜない。有限検査・原文通読・同義性の自動証明は区別する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    vector=v('vector');transform=v('transform');axes=k('shx')
    text+=define('eizc',[('vector',VECTOR)],both(k('shn',axes,vector,'p ba'),q('g','tuple','a',both(k('eiyz',v('tuple')),k('sho',axes,vector,k('shy',v('tuple')),'p sca')))))
    valid=q('f','first','a',op('y',k('eiyz',v('first')),k('shn',axes,'c['+transform+']['+k('shy',v('first'))+']','p ba')))
    exact=q('f','first','a',q('f','second','a',op('y',both(k('eiyz',v('first')),k('eiy2',v('second'))),op('z',k('eiyy',v('first'),v('second')),k('sho',axes,'c['+transform+']['+k('shy',v('first'))+']',k('shy',v('second')),'p sca')))))
    text+=define('eizd',[('transform',MAP)],both(k('sgw','p eiyz','p eiy2','p eiyy','p shh'),valid,exact))
    text+=content('eize',both(k('eizd',k('sia')),k('shs',axes,'p eizc',k('sia'),'p ba','p sca','p bd','p bf')))
    text+=define('eizf',[('matrix',MATRIX),('offset',VECTOR)],both(k('eizd',k('sia')),k('sht',axes,'p eizc',k('sia'),v('matrix'),v('offset'),'p ba','p sca','p bd','p shv')))
    text+=content('eizg',q('g','matrix',MATRIX,q('g','offset',VECTOR,k('eizf',v('matrix'),v('offset')))))
    text+=content('eizh',k('ug',k('zde'),k('rd'),quote('eize'),k('eisms'),v('point')))
    member=lambda node:k('eisnm',node,k('zdb'),k('eirf'),v('point'))
    text+=content('eizi',both(member(k('zdf')),q('f','step','a',op('y',both(member(v('step')),op('u',op('e',v('step'),k('zdf')))),k('ue',k('zdf'),v('step'),v('point'))))))
    text+=content('eizj',both('t[k eizh[]][v point]',k('zc',k('zdf'),k('rd'),quote('eize'),quote('eizg'),k('eisms'),v('point')),k('zdg',k('zdf'),k('rd'),quote('eizg'),k('eisms'),v('point')),k('zdh',k('zdf'),k('zdb'),quote('eizg'),k('eisms'),v('point')),'t[k eizi[]][v point]'))
    text+='d eizk[] f[j s[k eizj[]]].\n'
    text+=define('eizl',[],both(k('eir3',k('zdf'),k('rd'),k('eirf'),quote('eizk'),k('ri')),k('ue',k('zdb'),k('zdf'),k('ri')),op('u',op('e',k('zdb'),k('zdf')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eizl',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='homogeneous_spacetime_comparison_and_attributed_affine_necessity',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/event-coordinate-task-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
