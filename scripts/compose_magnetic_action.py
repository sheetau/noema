"""Bind magnetic force to the same charge, field and coordinate-time velocity."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_electric_action import ROOT,read,FIELDS as ELECTRIC
from scripts.compose_material_velocity import DOMAIN,CURVE
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import POINT,FIELD,ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both,ZERO

PARENT='examples/v014/einstein-conductor-cases.noema'
PARENT_BASIS='data/conductor-cases-basis-v1.json'
FULL='examples/v014/einstein-magnetic-action.noema'
CORE='examples/v014/magnetic-action-core.noema'
BASIS='data/magnetic-action-basis-v1.json'
ANNOTATIONS='data/magnetic-action-identifiers-v1.json'
VECTOR=[('charge',R),('velocity',POINT),('magnetic',POINT),('conversion',R),('force',POINT)]
FIELDS=[({'fieldunit':'magneticunit','electric':'magnetic'}.get(n,n),t) for n,t in ELECTRIC]+[
    ('lengthunit','a'),('timeunit','a'),('domain',DOMAIN),('curve',CURVE),('velocity',POINT)]
COMBINED=FIELDS+[('electricrecord','a'),('electricunit','a'),('electric',POINT),('electricforce',POINT),('electricconversion',R),('totalrecord','a'),('totalforce',POINT)]
ATTR=[('record','a'),('carrier','a'),('frame','a'),('event','a'),('context','d')]
CONVENTION=[(n,'a') for n in ('frame','chargeunit','lengthunit','timeunit','magneticunit','forceunit')]+[('conversion',R),('context','d')]
MEANINGS={
 'eicn':'有効な三速度成分と三磁場成分の順序付き外積scg2へ、同じ符号付き電荷と正の単位規約係数を掛けた値を三力成分へ結ぶ。既存eibrを再利用し、零電荷・零速度・磁場と平行な速度も割算なしで扱う。磁場が非零でも力が零になり得る。',
 'eico':'同じ点状担体・系・出来事・文脈で、電荷記録sbw2、四座標zpb、領域内の磁場評価scb2、磁気的な力の寄与eirtと力記録zpcを結ぶ。seocによる同じ軌跡の座標時刻微分を速度に使い、sepwで全履歴の座標と長さ・時間単位を接続する。eiruの基底・単位規約を保ってeicnを要求し、別系の速度・別出来事の力・合力で代用しない。',
 'eicp':'同じ電荷・担体・系・出来事・四座標・場・力単位について、eibsの電気的寄与とeicoの磁気的寄与を結び、その三成分の和をeirvで帰属した全電磁力の記録へ接続する。力の寄与ごとに場単位と換算係数を明示する。重力や支持力を含む全機械的な合力とは区別する。',
}
PRIMITIVES={
 'eirt':(ATTR,'この記録が、指定担体・系・出来事・文脈に働く磁気的な力の寄与を表す。電気的寄与や重力・支持力を含む合力の記録とは区別する。力は同じ系での運動量変化又はそれを釣り合わせる機械的作用により同定する基礎量として採る。磁場があることや外積の数値が合うことだけから、この寄与への帰属を推定しない。'),
 'eiru':(CONVENTION,'指定系の右手直交単位軸と同じ文脈で、長さ単位/時間単位で表示する速度、電荷単位、磁気側場の単位の積を力単位へ接続する正の係数conversionを定める規約。磁気側場は、電気的寄与を区別した移動電荷への速度依存の横向きの力を定める軸性の物理量として読む。原文の磁気側成分を、説明なしに現代SIの物質中のHや特定の透磁率へ置き換えない。係数は採用する場・単位の正規化を含み、1や1/cを原文へ無条件に補わない。実験の実施や一般的な微視的機構の証明を意味しない。'),
 'eirv':(ATTR,'この記録が、同じ担体・系・出来事・文脈への電気的寄与と磁気的寄与を合わせた全電磁力を表すという帰属。重力・支持力・接触力などを含む全機械的な合力とは別である。成分の和の条件は合成定義で要求し、記録名だけで等式を成立させない。'),
}
LIMITS=[
 '古典的な電荷・場・力を同じ評価系で読む構成であり、本文の全主張を真と証明するものではない。採用した基礎量と単位規約を明示する。',
 '速度は既存seocの両側の座標時刻微分である。区間の端点の片側微分、二地点の平均速度、固有時による微分を同じ速度として代用しない。物体全体の運動と一本の担体軌跡も区別する。',
 '磁気側場の表示単位は既存eirnで場そのものへ結ぶ。eiruの係数と右手基底の規約だけから、任意の材料中のHとBの構成則を認定しない。原文に数値係数や現代SIを追加しない。',
 '旧scj2の一階近似の力に関する言い表しを一般の全電磁力へ昇格させない。本構成は同じ系での力の二寄与を直接接続し、旧意味規約と207主張を変更しない。',
 '磁石という物体と場の発生源の帰属、導体との相互作用、磁石周囲の領域、起電力・エネルギー、著者への帰属と導入全体の判断は残る。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fields)+'] c.\n' for n,(fields,_) in PRIMITIVES.items())
    text+=define('eicn',VECTOR,both(k('sch2',v('velocity'),v('magnetic')),
        k('eibr',v('charge'),k('scg2',v('velocity'),v('magnetic')),v('conversion'),v('force'))))
    coords=[app(v('point'),k(n)) for n in ROLES]
    track=[v(n) for n in ('carrier','frame','context','domain','curve')]
    text+=define('eico',FIELDS,both(app(k('zrdpointlike'),v('carrier'),v('context')),
        k('sbw2',v('chargerecord'),v('carrier'),k('zor'),*[v(n) for n in ('frame','event','chargeunit','chargescale','charge','context')],'p zof','p zog'),
        op('u',op('e',v('lengthunit'),v('timeunit'))),
        k('seoc',*track,v('event'),v('point'),*(app(v('velocity'),k(n)) for n in ROLES[:3])),
        k('sepw',*track,v('lengthunit'),v('timeunit')),
        k('znn',v('frame'),v('electricfield'),v('magneticfield'),v('region'),v('context')),
        k('eirn',v('frame'),v('magneticfield'),v('magneticunit'),v('context')),app(v('region'),*coords),
        k('scb2',AXES,v('magneticfield'),v('point'),v('magnetic')),
        k('eirt',*[v(n) for n in ('forcerecord','carrier','frame','event','context')]),
        k('zof',v('forceunit'),k('zpn'),v('forcescale'),v('context')),k('aa',ZERO,v('forcescale')),
        k('zpc',v('forcerecord'),v('carrier'),k('zpn'),v('frame'),v('event'),v('forceunit'),v('force'),v('context')),
        k('eiru',*args(CONVENTION)),k('eicn',*args(VECTOR))))
    mapping={'forcerecord':'electricrecord','fieldunit':'electricunit','force':'electricforce','conversion':'electricconversion'}
    sumforce=k('s7s',AXES,v('electricforce'),v('force'))
    text+=define('eicp',COMBINED,both(k('eico',*args(FIELDS)),k('eibs',*[v(mapping.get(n,n)) for n,_ in ELECTRIC]),
        k('eirv',*[v(n) for n in ('totalrecord','carrier','frame','event','context')]),
        k('zpc',v('totalrecord'),v('carrier'),k('zpn'),v('frame'),v('event'),v('forceunit'),v('totalforce'),v('context')),
        k('shn',AXES,v('totalforce'),'p ba'),k('sho',AXES,sumforce,v('totalforce'),'p sca')))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='magnetic_and_electromagnetic_force_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/conductor-cases-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Magnetic and combined electromagnetic action composed')
