"""Connect source-resolved electromagnetic contributions to a carrier in a host."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_magnetic_action import ROOT,read,FIELDS as MAGNETIC,COMBINED
from scripts.compose_electric_action import FIELDS as ELECTRIC
from scripts.compose_magnet_source import SOURCE
from scripts.compose_conductor_reading import PROFILES
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both,ZERO

PARENT='examples/v014/einstein-magnet-source.noema'
PARENT_BASIS='data/magnet-source-basis-v1.json'
FULL='examples/v014/einstein-source-action.noema'
CORE='examples/v014/source-action-core.noema'
BASIS='data/source-action-basis-v1.json'
ANNOTATIONS='data/source-action-identifiers-v1.json'
FIELDS=[({'totalrecord':'sourcerecord','totalforce':'sourceforce'}.get(n,n),t) for n,t in COMBINED]+[(n,'a') for n in ('sourcebody','hostbody','sourcecondition')]
CLASSIFIED=FIELDS+[('standard','a'),('threshold',R),('minimumspan',R)]+[('trial'+n,t) for n,t in PROFILES]
ATTRIBUTION=[(n,'a') for n in ('record','sourcebody','carrier','frame','event','sourcecondition')]+[('context','d')]
MEANINGS={
 'eicw':'異なる二物体について、sourcebodyに由来する二成分場eirwと、hostbodyの物質領域内にある同じ点状担体への電気的寄与eibs・磁気的寄与eicoを結ぶ。担体は両物体全体と区別し、同じ出来事・系・文脈・単位の四座標をsbとeiroへ共有する。二力とその三成分和を、同じ源条件の寄与としてeiryで帰属した各記録へ接続する。源による合成寄与は零でもよく、全発生源を合わせた電磁力eirvや機械的合力を代用しない。',
 'eicx':'eicwの同じ源による合成寄与について、三空間成分の少なくとも一つが非零であるという局所的な作用の証人。電気的・磁気的寄与が互いに相殺して零になる場合はeicwを満たしてもこの条件は満たさない。',
 'eicy':'eicwへ、同じ源物体と源条件のeicrによる磁石の読み、同じ所在物体と元状況のeiciによる導体の読みを接続する。能力評価の電荷単位は担体の電荷単位、時間単位は同じ座標時刻単位へ結ぶ。可能な能力試行の履歴は局所作用の記録とは別であり、その輸送率閾値や最小持続時間を当該作用の強さ・持続へ追加しない。',
 'eicz':'eicyの磁石から導体内担体への局所的な源寄与が、eicxの非零条件も満たす証人。逆向きの作用・物体全体の力・電流生成・例示の発話をこれだけで記述したとはしない。源の場と担体の応答の接続に用いる。',
}
PRIMITIVE_MEANING='この記録が、同じ担体・系・出来事・文脈に対する、指定sourcebodyを発生源とする電磁的な力の寄与に帰属する。sourceconditionは場の源の分解と同じ初期/境界条件・他の源からの分離規約を指す。電気的寄与か磁気的寄与か又はその和かは、別の力の種類と合成式により指定する。力の数値が偶然一致するだけで源への帰属を推定しない。他の源の力や全力の記録をこの寄与と混同せず、零の寄与も許す。物理的な源別の記録帰属を基本規約として採り、別の物体に同時に等大反対向きの力があることや実験実施を内包しない。'
LIMITS=[
 'eirwの源の場を全場と同一視しないため、全電磁力eicp/eirvは呼ばず、eibsとeicoの寄与を直接再利用する。旧意味・旧主張は変更しない。',
 '同じ担体の同じ出来事が物質領域にあるという局所条件であり、担体が剛体の構成点であること、常に内部にあること、電流の唯一の担い手であることは要求しない。',
 'eicyの導体の能力試行は元状況での性質を定める。実際の電流生成や非零電流、局所力と導電の閾値の比較を追加しない。',
 '磁石・導体間の一方向の局所寄与の記録を接続する。電磁相互作用の全体、場の交換、全担体と全時間の応答、逆方向の作用、原文の例示の呼びかけは別に接続する。',
 '全実数の履歴・微分や磁石の外部点の存在、導体の能力を有限の一例から証明しない。原文207主張と著者表示判断を保持する。',
]

def source_args():return [v('sourcebody' if n=='body' else n) for n,_ in SOURCE]

def capacity_args():
    return [v(n) for n in ('standard','hostbody','context','timeunit','chargeunit','threshold','minimumspan')]+[v('trial'+n) for n,_ in PROFILES]

def definitions():
    text='r eiry['+' '.join(t for _,t in ATTRIBUTION)+'] c.\n'
    electric={'forcerecord':'electricrecord','fieldunit':'electricunit','force':'electricforce','conversion':'electricconversion'}
    coords=[app(v('point'),k(n)) for n in ROLES]
    attributions=[k('eiry',v(record),*[v(n) for n in ('sourcebody','carrier','frame','event','sourcecondition','context')]) for record in ('electricrecord','forcerecord','sourcerecord')]
    text+=define('eicw',FIELDS,both(*(op('u',op('e',v(a),v(b))) for a,b in (('sourcebody','hostbody'),('sourcebody','carrier'),('hostbody','carrier'))),
        k('zm',v('sourcebody')),k('zm',v('hostbody')),k('eirw',*source_args()),
        k('eibs',*[v(electric.get(n,n)) for n,_ in ELECTRIC]),k('eico',*args(MAGNETIC)),
        k('sb',*[v(n) for n in ('carrier','event','frame','context','lengthunit','timeunit')],coords[3],*coords[:3]),
        k('eiro',*[v(n) for n in ('hostbody','frame','context','lengthunit','timeunit')],*coords),*attributions,
        k('zpc',v('sourcerecord'),v('carrier'),k('zpn'),v('frame'),v('event'),v('forceunit'),v('sourceforce'),v('context')),
        k('shn',AXES,v('sourceforce'),'p ba'),k('sho',AXES,k('s7s',AXES,v('electricforce'),v('force')),v('sourceforce'),'p sca')))
    nonzero=[op('u',k('sca',app(v('sourceforce'),k(n)),k('bb',ZERO))) for n in ROLES[:3]]
    text+=define('eicx',FIELDS,both(k('eicw',*args(FIELDS)),op('x',nonzero[0],op('x',nonzero[1],nonzero[2]))))
    text+=define('eicy',CLASSIFIED,both(k('eicw',*args(FIELDS)),k('eicr',*source_args()),k('eici',*capacity_args())))
    text+=define('eicz',CLASSIFIED,both(k('eicy',*args(CLASSIFIED)),k('eicx',*args(FIELDS))))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eiry'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):];primitive=added[0]
    basis=dict(status='source_resolved_force_in_material_host',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eiry':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=[n for n,_ in ATTRIBUTION],meaning_ja=PRIMITIVE_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/magnet-source-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Source-resolved forces connected to a carrier in a material host')
