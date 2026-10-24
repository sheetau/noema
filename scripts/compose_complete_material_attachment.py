"""Exclude arbitrary coarse material domains from unchanging charge attachment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_attached_material_charge import ROOT,R,read,define,FIXED,MATERIAL,SPATIAL,SMALL,ALL,PHYSICAL,LABELS,BALL,PULLBACK,args
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-attached-material-charge.noema';PARENT_BASIS='data/attached-material-charge-basis-v1.json'
FULL='examples/v014/einstein-complete-material-attachment.noema';CORE='examples/v014/complete-material-attachment-core.noema'
BASIS='data/complete-material-attachment-basis-v1.json';ANNOTATIONS='data/complete-material-attachment-identifiers-v1.json'
ADMISSIBLE=[(n,t) for n,t in PHYSICAL if n!='amount']
MEANINGS={
 'ekxz':'同じ物体・分布・量種・系・出来事・座標時刻・物質部分・単位・文脈について、有効な実数の保有量をeisvyへ結べるという物理的な部分量の存在。単に選んだ部分族に所属することを適格性の定義にしない。実測記録の有無や未知入力を物理量の不存在へ置き換えない。',
 'ekx2':'ekxvの完全な物体履歴と不変な部分量に加え、全時刻の同じ出来事で、選んだ部分族とekxzの物理的に量が存在する全物質部分を双方向に一致させる。その同じ出来事で全物質部分のekxtと全空間逆像のekxuも要求し、粗い部分族や別出来事での完全性によって内部交換を見落とさない。',
 'ekx3':'同じ物体・区間・系・尺度・全成員・座標族の完全な不変付着ekx2と小さい剛体ekxxを共有する。前版ekxyの宣言された部分族だけの条件に、物理的部分量の全範囲との一致を加えた利用側の条件。',
}
LIMITS=[
 '前版ekxv/ekxyは宣言された部分族の全てを確認するが、その族を空部分と全体だけへ粗くすれば内部交換を隠せる。数学的な旧定義・旧検査記録を保持し、今後の本文接続には完全性を加えたekx2/ekx3を使う。前版だけで物理的な全部分への不変性が成立するとしない。',
 '部分族の完全性を、新しい任意の適格性述語へ移さない。既存eisvyで有効な実数の物理的保有量が存在することをekxzで構成し、部分族への所属と双方向に一致させる。eisvyは観測済み記録の一覧ではなく、その物理的帰属関係全体として解釈する。未知の物理入力を偽へ補わない。',
 '物理的に有限な量を持たない部分まで全ての任意部分集合へ有限値を強制しない。どの部分が物理的に適格か、同じ物質の追跡と校正の充足は解釈の入力である。有限の二物質点診断を連続体の全域の証明にはしない。',
 '完全性、固定部分量への帰属、空間領域への移送は各時刻の一つの同じ出来事にまとめる。前版の存在量化と独立に完全性だけを別出来事で確認する条件にはしない。',
 '408主張と旧判断を保持する。複数担体成分と場の全分布、評価系の対応、イオン/電子、理論の基礎、著者提示と原文単位全体の統合は残る。',
]

def definitions():
    amount=q('g','amount',R,both(k('ba',v('amount')),k('eisvy',*args(PHYSICAL))))
    text=define('ekxz',ADMISSIBLE,both(k('ba',v('time')),amount))
    appropriate=k('ekxz',*args(ADMISSIBLE,kind=k('zor'),quantityunit=v('chargeunit')))
    everypart=q('f','part',LABELS,both(op('z',app(v('parts'),v('part')),appropriate),op('y',app(v('parts'),v('part')),k('ekxt',*args(MATERIAL)))))
    preimage=k('ekxs',*args(PULLBACK))
    everyspace=q('f','space',BALL,op('y',app(v('parts'),preimage),k('ekxu',*args(SPATIAL))))
    sameevent=q('g','event','a',both(everypart,everyspace))
    alltimes=q('f','time',R,op('y',k('lg',v('lower'),v('upper'),v('time')),sameevent))
    text+=define('ekx2',FIXED,both(k('ekxv',*args(FIXED)),alltimes))
    text+=define('ekx3',ALL,both(k('ekx2',*args(FIXED)),k('ekxx',*args(SMALL))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='physically_complete_material_attachment_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/attached-material-charge-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
