"""Keep conductor capacity, comparison preparation and current conclusions distinct."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_conductor_reading import ROOT,read,PROFILES
from scripts.compose_current_distribution import MOTION,EXTRA as DISTRIBUTION,PAIR
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-conductor-reading.noema'
PARENT_BASIS='data/conductor-reading-basis-v1.json'
FULL='examples/v014/einstein-conductor-cases.noema'
CORE='examples/v014/conductor-cases-core.noema'
BASIS='data/conductor-cases-basis-v1.json'
ANNOTATIONS='data/conductor-cases-identifiers-v1.json'
CAPABILITIES=[('standard','a'),('right','a'),('firstcontext','d'),('secondcontext','d'),('timeunit','a'),('quantityunit','a'),('threshold',R),('minimumspan',R)]+[('trial'+n,t) for n,t in PROFILES]
PREMISE=MOTION+[('scope','a'),('standard','a'),('quantityunit','a'),('threshold',R),('minimumspan',R)]+[('trial'+n,t) for n,t in PROFILES]
FIELDS=PREMISE+[(n,t) for n,t in DISTRIBUTION if n!='quantityunit']
PREPARATION=[('scope','a'),('left','a'),('right','a'),('firstcontext','d'),('secondcontext','d')]
MEANINGS={
 'eicj':'同じ右側物体が、二場合の各元状況でeiciの基準付き電荷輸送能力を持つ。同じ評価基準・電荷と時間単位・閾値・最小時間・試行規約を共有するが、成功する試行と可能結果は別でよい。能力の試行履歴を本文の実際の二電流へ代入しない。',
 'eick':'eia3の同じ相対配置履歴と逆の運動・静止役割、eicjの同じ導体の二状況での能力、eirsの比較準備条件を結ぶ。まだ電流の一致を要求しない。左側が磁石であること、電場・起電力・エネルギーの説明と著者の主張は別に接続する。',
 'eicl':'eickの比較条件が成立するなら、同じ右側物体・二場合・単位・時刻対応・全断面範囲にeibiの電流履歴一致が成立する、という条件内容。前件へ電流一致を入れず、前件が真で電流が異なる場合は偽になる。条件内容の構成であり、言語処理系による物理法則の導出ではない。',
 'eicm':'eickの比較条件とeibiの電流一致を共に満たす具体的な二場合の内容。eiclが前件不成立で真になる場合を、実際に条件を満たした比較例として扱わないために区別する。両場合が現実に実行済みであることまでは述べない。',
}
PRIMITIVE_MEANING='指定した比較範囲において、同じ二物体を置いた第一・第二の状況が、運動の役割を取り替えて比べるための準備条件を保つという物理的な対応。対象に関係する材料・内部状態、形と尺度、回路の接続・負荷、温度、外部から設定する条件などを範囲の規約に従って固定し、結果を見て好都合な比較だけを選ばない。相対運動の一致は別にeia3で要求する。誘起される電場・起電力・電流・それらに結び付くエネルギーを等しいと要求する関係ではなく、それらは比較の結果又は説明対象である。単なる座標一致から準備条件の一致を推定しない。原文へ適用する範囲の選択を明示すべき基礎的な比較条件で、磁石・導体の種類や電流一致そのものを表す原始記号ではない。'
LIMITS=[
 '導体という同じ対象の二場合への接続と、比較の前提・結論の区別を構成する。原文の磁石・電磁相互作用、通常の理解への帰属、例示・呼びかけ、場・起電力・エネルギーの各内容と全文判断は残る。',
 '能力を評価する可能な試行と、原文で比較する電流履歴は別の関数族・文脈である。原文の電流は零・符号変化・短時間の値も扱い、能力評価の閾値や最小持続時間を実際の電流の一致条件へ追加しない。',
 '同じ種類であることから磁化や導電率等の物理的状態が等しいとは導かない。eirsの準備条件は物理的入力として別に指定する一方、誘起場や電流の一致を前件へ混入しない。',
 'eiclの条件内容とeicmの前件を満たす場合を分ける。有限検査で真だったことから、原文の物理法則が証明されたとはしない。',
 'eia3の既存の剛な参照配置・全物質点・単位・時刻原点の定数差という解釈を引き継ぐ。比較範囲・尺度と磁石側の性質を原文へ明示して適用する必要がある。既存207主張と著者表示判断を保持する。',
]

def conclusion():return k('eibi',*[v('right') if n=='body' else v(n) for n,_ in PAIR])

def definitions():
    text='r eirs[a a a d d] c.\n'
    cases=[k('eici',v('standard'),v('right'),v(case+'context'),v('timeunit'),v('quantityunit'),v('threshold'),v('minimumspan'),*[v('trial'+n) for n,_ in PROFILES]) for case in ('first','second')]
    text+=define('eicj',CAPABILITIES,both(*cases))
    text+=define('eick',PREMISE,both(k('eia3',*args(MOTION)),k('eicj',*args(CAPABILITIES)),k('eirs',*args(PREPARATION))))
    text+=define('eicl',FIELDS,op('y',k('eick',*args(PREMISE)),conclusion()))
    text+=define('eicm',FIELDS,both(k('eick',*args(PREMISE)),conclusion()))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eirs'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];primitive=added[0]
    basis=dict(status='conductor_cases_premise_conclusion_connection',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eirs':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=[n for n,_ in PREPARATION],meaning_ja=PRIMITIVE_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/conductor-reading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Conductor identity and conditional current agreement connected')
