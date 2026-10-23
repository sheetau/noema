"""Present the magnet/conductor example as an invitation, not a realized experiment."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_source_action import ROOT,read,FIELDS as ACTION
from scripts.compose_magnet_source import SOURCE
from scripts.compose_conductor_reading import PROFILES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-source-action.noema'
PARENT_BASIS='data/source-action-basis-v1.json'
FULL='examples/v014/einstein-interaction-example.noema'
CORE='examples/v014/interaction-example-core.noema'
BASIS='data/interaction-example-basis-v1.json'
ANNOTATIONS='data/interaction-example-identifiers-v1.json'
INDEX=207
SCHEMA='i[h['+' '.join(t for _,t in ACTION)+'] c]'
FIELDS=[('left','a'),('right','a'),('process','a')]+[(n,t) for n,t in SOURCE if n!='body']+[
    ('standard','a'),('chargeunit','a'),('threshold',R),('minimumspan',R)]+[('trial'+n,t) for n,t in PROFILES]
AUXILIARY=[(n,t) for n,t in FIELDS if n not in ('left','right','process','context')]
COUPLING=[('process','a'),('right','a')]+SOURCE+[('local_action',SCHEMA)]
PRIMITIVES={
 'eirz':(COUPLING,'指定processは、同じ二物体を電磁的に結合して扱う物理的な設定・経過である。bodyに帰属する指定の源条件・系・単位・領域・二成分場をその片側の場として使い、両物体の電荷・内部電流・磁化や運動の状態と、相手に由来する場への応答を結び付けて扱う。各方向の場と応答は同じ結合設定の構成部分であり、無関係な二記録の併置ではない。点状担体への局所力を記述する際の規約は、渡された閉じたlocal_actionの内容型に従う。全物体を一点で代表したり、任意の瞬間に両方向の非零機械力を要求したりせず、零や相殺、拘束下の静止、場を介する応答を許す。相互の結合を採るモデル上の物理的帰属を基本規約とし、一方向の一力記録だけから認定しない。力の同時等大反対向き、全担体の微視的機構、一般的な場の方程式の証明、現実の実験実施は含意しない。'),
 'eir2':([('person','a'),('target','i[e]'),('context','d')],'指定主体が、閉じたtargetで記述する設定や事柄を思考の対象として取り上げ、関係や帰結を検討する。実際の実験・物理的実現、targetの真理への同意、信念の獲得とは区別する。targetを説明のない語名として扱わず、内容型を保持した記述として受け取る。'),
 'eir3':([('node','a'),('author','a'),('document','a'),('message','i[f]'),('context','d')],'著者が同じ文書・提示文脈のこの箇所で、閉じたmessageの記述が指定する発話の力と内容を読者へ提示する。指示・主張・問いを交換しない。帰属された発話の内容をその場で実行せず、読者の遵守、内容の真理、著者による実験実施を含意しない。'),
 'eir4':([('person','a'),('document','a'),('context','d')],'この文書の同じ提示文脈で、呼びかけを受ける読者としての人の範囲に指定主体が属する。文書を読む立場への一般的な宛先であり、世界の全人間、特定一名、実際に読了した人だけへ置き換えない。'),
 'eir5':([('node','a'),('author','a'),('prior','a'),('target','i[e]'),('context','d')],'著者がこの箇所で指定targetの内容を、同じ提示文脈の先行箇所の論点を考える一つの具体例として取り上げる。先行箇所と例示対象を固定するが、唯一の例、全事例の網羅、例の現実化、例からの論理的証明は含意しない。'),
 'eir6':([], '固定原文einstein-1905:u0003[210,307)のMan denkeからLeiter.までの例示への呼びかけの箇所。'),
 'eir7':([], '同じ導入段落[0,209)の、通常の電気力学の適用上の非対称性と現象の対照を論点として提示する先行箇所。その文全体の内容の完成認定や真理をこの参照から導かない。'),
 'eisaa':([], 'この例示で思考の対象として導入され、後続の二場合にも引き継ぐ磁石側の談話上の対象。磁石の性質はeicrで仮定内容の内側に要求し、この参照だけで物理的種類や実在を断定しない。'),
 'eisab':([], 'この例示で思考の対象として導入され、後続の二場合にも引き継ぐ導体側の談話上の対象。導体の性質はeiciで仮定内容の内側に要求し、この参照だけで物理的種類や実在を断定しない。'),
 'eisac':([], 'この同じ例示で考える二物体の結合設定・経過の談話上の対象。既に実行済みの実験や唯一の実在の出来事への参照とはしない。'),
}
MEANINGS={
 'eic2':'異なる左側・右側物体について、同じ文脈の磁石の読みeicr、右側の導体能力eici、および同じ源の場・単位・源条件を使う両物体の結合設定eirzを結ぶ。eirzへ既存eicwの閉じた局所作用型を明示する。一方向の非零力だけを相互作用とせず、逆方向の非零力も追加条件にしない。',
 'eic3':'同じ左側物体・右側物体・結合設定を保ち、eic2を満たす系、単位、源条件、場、領域、導体の基準と試行規約が存在するという内容。特定の数値・材質・装置を原文へ固定しない。評価する設定を内容の引数pointとして、提示文脈と分ける。',
 'eic4':'例示で導入する同じ二つの談話対象と結合設定にeic3を適用する閉じた内容。固定名で磁石・導体の語義を代用せず、種類と相互作用の条件を内容の内側に保持する。',
 'eic5':'同じ文書・提示文脈の読者としての各人が、指定した閉じたtargetを思考の対象として検討するという内容。読者範囲は提示文脈で固定し、思考行為を評価する点とは別にする。targetの物理的成立や同意を要求しない。',
 'eic6':'同じ論説の読者に、eic4の例を考えることを促す指示の力を持つメッセージ。主張ではなく指示として構成し、義務の正当性や読者の実行済みを含めない。',
 'eic7':'著者rdが論説eirfの当該箇所でeic6を提示し、同じeic4を先行箇所の論点の具体例として取り上げることを結ぶ。本文順序も保持する。メッセージと例示対象は引用して渡し、その物理内容や読者の思考をここで実行しない。',
}
LIMITS=[
 '相互作用は、明示した源と局所作用の規約を使って両物体の状態と応答を結ぶ物理モデル上の関係として読む。eirzはこの一般的な結合の基礎規約であり、原文一文全体の真偽を返す専用記号ではない。物体の種類・指示の力・考察対象・例示・著者と文書への帰属は別々に合成する。',
 '一つの磁石と一つの導体は思考対象の談話上の参照であり、現実に観測済みの特定装置を導入しない。磁石は活動中の外部磁気源、導体は通常の条件で有意な電荷輸送が可能という既存の明示した読みを引き継ぐ。',
 'z. B.は先行の論点を考える具体例の提示である。非対称性の物理的証明、著者の全主張への同意、唯一の例、例の網羅を追加しない。先行第一文の内容全体は別の未完課題として保つ。',
 '今回追加するのは固定範囲[210,307)の一文の提示であり、u0003全段落の完成ではない。後続の同じ二場合への参照、観測可能な現象の依存、通常の理解への対置、場・起電力・エネルギーは残る。',
]

def source_args():return [v('left' if n=='body' else n) for n,_ in SOURCE]
def capacity_args():return [v(n) for n in ('standard','right','context','timeunit','chargeunit','threshold','minimumspan')]+[v('trial'+n) for n,_ in PROFILES]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fields)+'] '+('a' if not fields else 'c')+'.\n' for n,(fields,_) in PRIMITIVES.items())
    text+=define('eic2',FIELDS,both(op('u',op('e',v('left'),v('right'))),k('eicr',*source_args()),k('eici',*capacity_args()),
        k('eirz',v('process'),v('right'),*source_args(),'r[p eicw]')))
    selected=[v('point' if n=='context' else n) for n,_ in FIELDS]
    content=k('eic2',*selected)
    for n,t in reversed(AUXILIARY):content=q('g',n,t,content)
    text+='d eic3[left a right a process a] e[b point['+content+']].\n'
    text+='d eic4[] e[k eic3[k eisaa[] k eisab[] k eisac[]]].\n'
    consideration=q('f','person','a',op('y',k('eir4',v('person'),v('document'),v('presentation')),k('eir2',v('person'),v('target'),v('point'))))
    text+='d eic5[document a presentation d target i[e]] e[b point['+consideration+']].\n'
    text+='d eic6[] f[j m[k eic5[k eirf[] k ri[] r[k eic4[]]]]].\n'
    text+=define('eic7',[],both(k('eir3',k('eir6'),k('rd'),k('eirf'),'r[k eic6[]]',k('ri')),
        k('eir5',k('eir6'),k('rd'),k('eir7'),'r[k eic4[]]',k('ri')),k('ue',k('eir7'),k('eir6'),k('ri')),op('u',op('e',k('eir6'),k('eir7')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eic7',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='interaction_example_invitation_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/source-action-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Interaction example invitation appended at statement 207')
