"""Separate charge-transport capacity from its actual manifestation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_current_distribution import ROOT,read,HISTORY,MOTION,EXTRA as DISTRIBUTION,SCOPE,FAMILY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-current-distribution.noema'
PARENT_BASIS='data/current-distribution-basis-v1.json'
FULL='examples/v014/einstein-charge-transport-capacity.noema'
CORE='examples/v014/charge-transport-capacity-core.noema'
BASIS='data/charge-transport-capacity-basis-v1.json'
ANNOTATIONS='data/charge-transport-capacity-identifiers-v1.json'
WITNESS=HISTORY+[('threshold',R),('section','a'),('orientation','a'),('time',R)]
RESPONSE=HISTORY+[('threshold',R)]
TRIAL=[('body','a'),('source','d'),('operation','a'),('alternative','d'),('timeunit','a'),('quantityunit','a'),('threshold',R)]+[
    (n,t) for n,t in HISTORY if n not in ('body','context','timeunit','quantityunit')]
PROFILES=[(n,'h[d a d] '+t) for n,t in HISTORY if n not in ('body','context','timeunit','quantityunit')]
CAPACITY=[('body','a'),('source','d'),('timeunit','a'),('quantityunit','a'),('threshold',R)]+PROFILES
EXTRA=[('threshold',R)]+[('trial'+n,t) for n,t in PROFILES]
MEANINGS={
 'eibk':'有効な実数閾値が非負で、有効な符号付き率の絶対値がその閾値を厳密に超える。正負のどちらの向きも受け入れるが、零や閾値ちょうどを成功としない。閾値の適切さはこの数値関係だけでは決めない。',
 'eibl':'完全な物体付き断面電流履歴eibfの下で、指定断面・向きが全範囲に属し、指定時刻が区間内にあり、その電流がeibkを満たすという一つの応答証人。物体の移動、未知の履歴、範囲外の値を電荷通過の証人にしない。',
 'eibm':'同じ物体・系・文脈・単位・区間・全断面履歴と閾値について、eiblを満たす断面・向き・実時刻が存在する。全区間で閾値を超える持続や、全断面での成功は要求しない。現に評価する履歴の応答であり、それだけで物体の導電性という種類を認定しない。',
 'eibn':'元の状況にある同じ物体への許容試行eirkと、既存zrdpossibleの物理的に可能な結果状況を結び、その結果の同じ物体でeibmの通過応答を要求する。元の状況で電流が流れていることも、試行を実行済みであることも要求しない。',
 'eibo':'同じ物体・元の状況・電荷と時間単位・閾値について、eibnを満たす操作と可能な結果が存在するという条件付き電荷通過能力。各結果の系・区間・全断面・累積量・電流は、元の状況と同じ操作と結果で索引した関数族から共有して選ぶ。空の候補や実現不可能な成功から能力を認定しない。全結果成功の保証とは異なる。',
 'eibp':'二場合の相対運動・全断面電流一致eibjへ、同じ右側物体が各場合の元状況でeiboの通過能力を持つことを結ぶ候補条件。二場合に同じ閾値・単位と試行規約を使うが、成功する試行は別でよい。磁石・導体の種類や電磁法則の主張をこの条件だけから導かない。',
}
PRIMITIVE_MEANING='その元状況にある同じ物体について、operationが評価対象の構成・物質的同一性を保つ許容試行であるという一般的な物理条件。温度・相・配置・作用の強さなど、評価する性質に関係する許容範囲を事前に定め、破壊・別物質への変質・別物体への置換を成功例へ混入しない。試行の成功は意味せず、物理的な可能な結果は別のzrdpossibleで指定する。電荷通過への適用では、同じ物体内の電荷移動を調べる作用と配置を対象とし、未知の条件を許容と補わない。これは導体という種類の名前でも、非零電流という結果でもない。'
LIMITS=[
 '導体の意味に必要な、現に流れていなくても持つ電荷通過能力を構成する。許容試行と閾値を明示し、微小な漏れや物体の変質だけで導体という種類を認定しない。原文に適切な試行・閾値の選定、電気的作用への接続、自由な担体の物理的根拠は未完であり、eiboを導体全般との同義とまだ判断しない。',
 '閾値は電荷単位/時間単位の率である。零閾値も使えるが、零閾値の存在条件だけでは漏れと通常の導電を区別できない。原文に数値閾値やOhm則を勝手に補わない。',
 'eirkの許容試行とzrdpossibleの物理的可能性は別の入力。既存の電荷追加能力seqvで使う一般的な可能結果関係を再利用し、電荷追加操作や点状理想化を要求しない。能力は実際の実行や全結果での保証を含まない。',
 'eibmは一時刻の閾値超過の存在であり、全区間の持続や全方向の等方性を意味しない。全実数時刻の存在を有限サンプルへ置き換えず、有限検査ではこの存在条件を境界として区別する。',
 '既存207主張と判断を保持する。磁石・導体の語義の最終判断、実際の尺度・全断面範囲、電気量の作用と校正、電場・起電力・エネルギー、著者への帰属と全文接続は残る。',
]

def definitions():
    zero=k('bb',ZERO);rate=v('rate');threshold=v('threshold')
    text='r eirk[a a d] c.\n'
    text+=define('eibk',[('rate',R),('threshold',R)],both(k('ba',rate),k('ba',threshold),k('bc',zero,threshold),
        op('x',k('bg',threshold,rate),k('bg',rate,k('bf',zero,threshold)))))
    current=app(app(v('current'),v('section'),v('orientation')),v('time'))
    text+=define('eibl',WITNESS,both(k('eibf',*args(HISTORY)),app(v('sections'),v('section'),v('orientation')),
        k('lg',v('lower'),v('upper'),v('time')),k('eibk',current,threshold)))
    text+=define('eibm',RESPONSE,q('g','section','a',q('g','orientation','a',q('g','time',R,k('eibl',*args(WITNESS))))))
    result=[v('alternative') if n=='context' else v(n) for n,_ in RESPONSE]
    text+=define('eibn',TRIAL,both(k('zm',v('body')),k('eirk',v('body'),v('operation'),v('source')),
        app(k('zrdpossible'),v('operation'),v('body'),v('source'),v('alternative')),k('eibm',*result)))
    selected=[app(v(n),v('source'),v('operation'),v('alternative')) if n in {n for n,_ in PROFILES} else v(n) for n,_ in TRIAL]
    text+=define('eibo',CAPACITY,q('g','operation','a',q('g','alternative','d',k('eibn',*selected))))
    capabilities=[]
    for case in ('first','second'):
        capabilities.append(k('eibo',v('right'),v(case+'context'),v('timeunit'),v('quantityunit'),threshold,*[v('trial'+n) for n,_ in PROFILES]))
    text+=define('eibp',MOTION+DISTRIBUTION+EXTRA,both(k('eibj',*args(MOTION+DISTRIBUTION)),*capabilities))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eirk'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];p=added[0]
    basis=dict(status='conditional_charge_transport_capacity_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eirk':dict(parameters=p['parameters'],result=p['result'],arguments=['body','operation','source'],meaning_ja=PRIMITIVE_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/current-distribution-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Conditional charge transport capacity composed')
