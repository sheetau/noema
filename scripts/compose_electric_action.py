"""Bind signed charge, local electric field and electric force records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_charge_transport_capacity import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import POINT,FIELD,REGION,ROLES
from scripts.compose_rest_force import AXES
from scripts.compose_limits import R,v,call as k,app,op,both,ZERO

PARENT='examples/v014/einstein-charge-transport-capacity.noema'
PARENT_BASIS='data/charge-transport-capacity-basis-v1.json'
FULL='examples/v014/einstein-electric-action.noema'
CORE='examples/v014/electric-action-core.noema'
BASIS='data/electric-action-basis-v1.json'
ANNOTATIONS='data/electric-action-identifiers-v1.json'
SCALAR=[('charge',R),('electric',R),('conversion',R),('force',R)]
VECTOR=[('charge',R),('electric',POINT),('conversion',R),('force',POINT)]
FIELDS=[(n,'a') for n in ('chargerecord','forcerecord','carrier','frame','event')]+[('context','d')]+[
    (n,'a') for n in ('chargeunit','fieldunit','forceunit')]+[('chargescale','b'),('forcescale','b'),('charge',R),
    ('point',POINT),('electricfield',FIELD),('magneticfield',FIELD),('region',REGION),('electric',POINT),('force',POINT),('conversion',R)]
MEANINGS={
 'eibq':'有効な符号付き電荷・電場成分・力成分について、正の単位換算係数を含むforce=conversion×charge×electricを要求する。一成分の数値関係であり、物理的な作用への帰属は含まない。零電荷を割らずに扱い、正負の電荷による向きの反転を保存する。',
 'eibr':'互いに異なる既存の三空間軸yn/yo/ypに対してeibqを要求する電気的力のベクトル関係。同じ電荷と換算係数を三成分へ共有し、大きさだけの等値や一成分だけの一致で代用しない。',
 'eibs':'同じ点状担体・系・出来事・文脈に、単位と尺度付きの電気量の記録sbw2、四座標zpb、領域内の場割当znnとscb2による評価、電気的な力として特定した記録eirlと力ベクトルzpcを結ぶ。eirmの単位整合を保ち、eibrの三成分関係を要求する。他の力を含む合力、別の出来事の電荷、別系の電場を代入しない。電荷への電気的作用の構成であり、磁気力や担体の運動をこれだけで説明しない。',
}
PRIMITIVES={
 'eirl':(['record','carrier','frame','event','context'],'この記録が、その担体に当該系・出来事・文脈で働く電気的な力の寄与を記述するという作用の帰属。重力・支持力・磁気的寄与を含む合力の記録とは区別する。力は方向を持つ機械的作用の量であり、同じ状態の運動量変化への寄与またはそれを釣り合わせる機械的作用と比較して同定する基礎的な物理量として採る。電荷との数値比例や力の非零だけからこの帰属を推測しない。仮定上の記録も許し、実測済みの標識ではない。'),
 'eirm':(['chargeunit','fieldunit','forceunit','conversion','context'],'同じ文脈で電場を単位正電荷あたりの電気的な力として読む規約に従い、指定した電荷単位と電場単位の積を力単位へ直す正の係数がconversionである。数値関数や同じ名前だけでは単位規約は成立しない。電荷は電気的作用の強さと二つの極性を記述する加法的な符号付き物理量として採り、全体の符号選択と単位尺度を規約へ固定する。電場は同じ系・地点・時刻の電気的作用を、十分小さい静止試験電荷への力/電荷の極限で同定する物理量として解釈する。個別の有限試験が系を乱さないことや実験の実施を自動認定しない。'),
 'eirn':(['frame','field','unit','context'],'指定系・文脈の同じ成分場の数値が、この場の量単位で表示されているという帰属。場の物理的種類と領域は別の場割当で指定し、単位が同じ別の場や、同じ数値の異なる単位を同一視しない。'),
}
LIMITS=[
 '電荷・力の基礎量は明示した物理的同定規約として採り、名称だけや有限検査の任意の真偽で説明済みにはしない。eibsはその入力を数値・対象・場所・時刻へ接続する。実際の校正手順、場への試験電荷の影響の極限、力と運動量の一般的な力学をこの三定義だけで機械的に証明してはいない。',
 '任意の符号付き電荷を扱い、値1や静止担体に限定しない。電気的寄与だけを述べ、全電磁力がqEであるとはしない。磁気力、散乱・抵抗、担体が物体を通過する機構は別に必要。',
 '電荷と力の正の有理尺度は既存zof/sbw2の規約を使い、電場との積の単位換算はeirmへ明示する。原文へ現代SIの定数や特定の数値係数を補わない。',
 '既存の電気量zor、場znn、力zpcの規約と旧主張を変更せず、この構成で作用の特定と単位規約を追加する。旧草案の意味完成を遡って認定しない。原文207主張と著者表示判断を保持し、新たな全文意味判断は加えない。',
]

def definitions():
    text='r eirl[a a a a d] c.\n'+'r eirm[a a a '+R+' d] c.\n'+'r eirn[a '+FIELD+' a d] c.\n'
    text+=define('eibq',SCALAR,both(*(k('ba',v(n)) for n,_ in SCALAR),k('bg',k('bb',ZERO),v('conversion')),
        k('sca',v('force'),k('shv',v('conversion'),k('shv',v('charge'),v('electric'))))))
    axes=ROLES[:3]
    text+=define('eibr',VECTOR,both(*(op('u',op('e',k(a),k(b))) for a,b in ((axes[0],axes[1]),(axes[1],axes[2]),(axes[0],axes[2]))),
        *(k('eibq',v('charge'),app(v('electric'),k(a)),v('conversion'),app(v('force'),k(a))) for a in axes)))
    coords=[app(v('point'),k(n)) for n in ROLES]
    text+=define('eibs',FIELDS,both(app(k('zrdpointlike'),v('carrier'),v('context')),
        k('sbw2',*[v(n) for n in ('chargerecord','carrier')],k('zor'),*[v(n) for n in ('frame','event','chargeunit','chargescale','charge','context')],'p zof','p zog'),
        k('znn',v('frame'),v('electricfield'),v('magneticfield'),v('region'),v('context')),
        k('eirn',v('frame'),v('electricfield'),v('fieldunit'),v('context')),
        k('zpb',v('carrier'),v('frame'),v('event'),v('point'),v('context')),app(v('region'),*coords),
        k('scb2',AXES,v('electricfield'),v('point'),v('electric')),
        k('eirl',*[v(n) for n in ('forcerecord','carrier','frame','event','context')]),
        k('zof',v('forceunit'),k('zpn'),v('forcescale'),v('context')),k('aa',ZERO,v('forcescale')),
        k('zpc',v('forcerecord'),v('carrier'),k('zpn'),v('frame'),v('event'),v('forceunit'),v('force'),v('context')),
        k('eirm',v('chargeunit'),v('fieldunit'),v('forceunit'),v('conversion'),v('context')),
        k('eibr',*args(VECTOR))))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=PRIMITIVES[d['name']][0],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='signed_charge_electric_action_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/charge-transport-capacity-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Electric action on signed charge composed')
