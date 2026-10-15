"""Calibrate recorded endpoint order against the owning coordinate axis."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params
from scripts.compose_direction_measurements import FULL as PARENT,INDEX,FIELDS,BINDINGS as PREVIOUS_BINDINGS
from scripts.compose_density_boost import CUT,FRAMES

FULL='examples/v014/einstein-positive-axis-calibration.noema'
CORE='examples/v014/positive-axis-calibration-manuscript.noema'
LIBRARY='examples/v014/positive-coordinate-rays.noema'
REVIEW='data/density-formula-review-v10.json'
BINDINGS={**PREVIOUS_BINDINGS,'frames':'sext'}
COORDS='tailx taily tailz headx heady headz'.split()
RAY=[(n,'a') for n in ('role','xrole','yrole','zrole')]+[(n,CUT) for n in COORDS]


def definitions():
    text=definition('sexo','tail b head b',k('aa',v('tail'),v('head')))
    text+=definition('sexp','tail '+CUT+' head '+CUT,both(k('ba',v('tail')),k('ba',v('head')),k('bg',v('tail'),v('head'))))
    zero=k('bb','n p a b');roles=[v(n+'role') for n in ('x','y','z')];branches=[]
    for axis in ('x','y','z'):
        branches.append(both(op('e',v('role'),v(axis+'role')),k('sexp',v('tail'+axis),v('head'+axis)),
            *(k('sca',v(end+other),zero) for other in ('x','y','z') if other!=axis for end in ('tail','head'))))
    text+=definition('sexq',params(RAY),both(
        *(op('u',op('e',roles[i],roles[j])) for i,j in ((0,1),(0,2),(1,2))),
        *(k('ba',v(n)) for n in COORDS),op('x',branches[0],op('x',branches[1],branches[2]))))
    return text


def source_definitions():
    tail,head,moment=[k('zsc',v('record'),'n p '+digit+' b') for digit in ('a','b','c')]
    axis=k('zbo',v('frame'),v('role'),v('context'))
    coordinate=lambda point,role:k('ym',point,moment,v('frame'),v('unit'),k(role),v('context'))
    text=definition('sexr','record a frame a role a unit a context d',both(k('va',v('frame')),k('ti',v('unit')),
        k('zbw',v('frame'),axis,v('role'),v('context')),k('zsd',v('record'),tail,head,moment,v('context')),
        *(k('zcc',point,axis,v('context')) for point in (tail,head)),
        *(k('zce',point,moment,v('frame'),v('unit'),v('context')) for point in (tail,head)),
        k('sexq',v('role'),k('yn'),k('yo'),k('yp'),
            *(coordinate(point,role) for point in (tail,head) for role in ('yn','yo','yp')))))
    clauses=[]
    for role in ('yn','yo','yp'):
        axis=k('zbo',v('frame'),k(role),v('context'))
        selected=k('zsa',v('record'),axis,k('ra'),k('ta'),v('context'))
        clauses.append(q('f','record','a',op('y',selected,k('sexr',v('record'),v('frame'),k(role),k('ta'),v('context')))))
    text+=definition('sexs','frame a context d',both(*clauses))
    text+=definition('sext','','i[first a second a value '+CUT+' context d]['+both(
        app(k('sexn'),v('first'),v('second'),v('value'),v('context')),
        k('sexs',v('first'),v('context')),k('sexs',v('second'),v('context')))+']',FRAMES)
    return text


MEANINGS={
    'sexo':'有理数の始値より終値が大きい。値自体が正であることと、増加することを区別する。',
    'sexp':'有効な実切断の始値より終値が大きい。増分が零の場合や逆向きは含めない。',
    'sexq':'異なる三役割のうち指定された一軸の座標が始点から終点へ増加し、両点の他二成分は零である。単なる平行移動した線上の二点ではなく、この座標軸上の正向きの順序を表す。',
    'sexr':'同じ記録の二点・観測時点を引き継ぎ、実際に割り当てられた所有系の軸で、位置座標の利用可能性とsexqの正方向の順序を要求する。所有系の座標を共通観測系の座標から推測しない。',
    'sexs':'元の共通観測系の記録範囲zsaを保ち、同じ系の三軸の全選択記録に、その所有系での正方向の条件sexrを課す。',
    'sext':'二系と速度、物理的配置、共通観測系での正方向の一致と二点の座標差sexnを保持し、同じ二点の順序を各所有系の正の座標増分へ結ぶ。',
}
LIMITS=[
    '選択された二点の順序を、所有系の対応軸の座標増加と他二成分の零へ結んだ。zsaの正方向という意味規約を単に再宣言するだけではないが、その帰属と記録範囲の完全性は保持する。',
    '共通の観測系と各軸の所有系の座標は別々に利用可能性を要求する。数値の一致を前提にせず、長さ・進み率・時計指示の一致を追加しない。',
    '元の観測時点の参照を両方の座標に引き継ぐ。このことから、両系の時計が同じ指示を示すことや、同時性が両系で一致することを主張しない。',
    '二点が座標軸上で正の順序にあることは検査するが、物質軸の全点の直線性、計器の物理的校正、測定の構成説明は残る。有限の記録を全空間・全時刻の検証とはしない。',
    '他二成分を零とするため、旧版が許した平行なずれた線の記録を除外し得る。旧版との無条件の意味同値は主張しない。共通原点・時計原点・慣性系・電気的帰属・適用範囲と全文の意味確認は未完である。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions());doc['statements']=deepcopy(old['statements'])
    expression=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert expression==dict(kind='call',symbol='seoz',arguments=[dict(kind='call',symbol=PREVIOUS_BINDINGS[n],arguments=[]) for n,_ in FIELDS])
    expression['arguments']=[dict(kind='call',symbol=BINDINGS[n],arguments=[]) for n,_ in FIELDS]
    basis=json.loads((ROOT/'data/einstein-direction-measurements-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-positive-axis-calibration-basis-v1',document=FULL)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    basis['interpretation_revision']=dict(parent=PARENT,statement_index=INDEX,changed_arguments=['frames'],previous_bindings=PREVIOUS_BINDINGS,
        fixed_bindings=BINDINGS,equivalence_to_parent_proven=False,new_primitives=0,configuration_relation_retained='zqf')
    audit_basis(doc,basis)
    review=json.loads((ROOT/'data/density-formula-review-v9.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v10',supersedes='data/density-formula-review-v9.json',source_document=FULL,document=CORE,fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id']=='source_context_bindings':
            row['evidence']='The frame relation sext retains the ordered source pair, signed speed, configuration, direction alignment and recorded displacements, and calibrates the same endpoint order against the owning frame coordinates.'
            row['limit']='Positive coordinate order is explicit; physical metrology, whole-axis straightness, origin/clock alignment and full source-case coverage remain open.'
    review['checks'].insert(-1,dict(id='own_axis_positive_order',status='connected_in_revised_reading',
        evidence='Every selected record keeps its linked endpoints and observation reference. In the owning frame, coordinates must be available, the assigned axial coordinate strictly increases, and both transverse coordinates of each endpoint vanish.',
        limit='This does not prove physical coordinate calibration, whole-axis geometry or equal simultaneity/clock readings across frames. It does not compare endpoint distances across frames.'))
    review['integrated_symbols']+=list(MEANINGS);review['evidence_reports'].append('reports/positive-axis-calibration-v1.json');review['semantic_completion']=False
    files={FULL:format_graph(doc,'compact')+'\n','data/einstein-positive-axis-calibration-basis-v1.json':basis,REVIEW:review}
    for path,roots,indices in ((CORE,[],[INDEX]),(LIBRARY,['sexo','sexq'],[])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Positive endpoint order calibrated in each owning frame',flush=True)


if __name__=='__main__':main()
