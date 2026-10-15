"""Connect each selected direction record to one same-time endpoint pair."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params
from scripts.compose_axis_orientation import FULL as PARENT,INDEX,FIELDS,BINDINGS as PREVIOUS_BINDINGS
from scripts.compose_density_boost import CUT,FRAMES

FULL='examples/v014/einstein-direction-measurements.noema'
CORE='examples/v014/direction-measurements-manuscript.noema'
LIBRARY='examples/v014/recorded-displacements.noema'
REVIEW='data/density-formula-review-v9.json'
BINDINGS={**PREVIOUS_BINDINGS,'frames':'sexn'}
LINK='h[a a a a d] c'
PLACED='h[a a d] c'
AVAILABLE='h[a a a a d] c'
COORDINATE='h[a a a a a d] '+CUT
COMPONENT='h[a a] '+CUT
RECORD=[(n,'a') for n in ('record','axis','chart','unit')]+[('context','d')]+[
    (n,'a') for n in ('xrole','yrole','zrole','tail','head','moment')]+[
    ('linked',LINK),('placed',PLACED),('available',AVAILABLE),('coordinate',COORDINATE),('component',COMPONENT)]


def definitions():
    text=definition('sexi','tail b head b delta b',op('e',v('delta'),k('ab',v('head'),k('ac',v('tail')))))
    text+=definition('sexj',params([(n,CUT) for n in ('tail','head','delta')]),both(
        *(k('ba',v(n)) for n in ('tail','head','delta')),k('sca',v('delta'),k('bf',v('head'),v('tail')))))
    roles=[v(n+'role') for n in ('x','y','z')]
    coordinate=lambda point,role:app(v('coordinate'),v(point),v('moment'),v('chart'),v('unit'),role,v('context'))
    component=lambda role:app(v('component'),v('record'),role)
    text+=definition('sexk',params(RECORD),both(
        app(v('linked'),v('record'),v('tail'),v('head'),v('moment'),v('context')),
        op('u',op('e',v('tail'),v('head'))),
        *(op('u',op('e',roles[i],roles[j])) for i,j in ((0,1),(0,2),(1,2))),
        *(app(v('placed'),v(point),v('axis'),v('context')) for point in ('tail','head')),
        *(app(v('available'),v(point),v('moment'),v('chart'),v('unit'),v('context')) for point in ('tail','head')),
        *(k('sexj',coordinate('tail',role),coordinate('head',role),component(role)) for role in roles),
        k('sbg',k('sexb',*[component(role) for role in roles]*2))))
    return text


def source_definitions():
    text='r zsc[a b] a.r zsd[a a a a d] c.\n'
    fields=[k('zsc',v('record'),'n p '+digit+' b') for digit in ('a','b','c')]
    text+=definition('sexl','record a axis a chart a unit a context d',k('sexk',
        *map(v,('record','axis','chart','unit','context')),k('yn'),k('yo'),k('yp'),
        *fields,'p zsd','p zcc','p zce','p ym','p zsb'))
    clauses=[]
    for role in ('yn','yo','yp'):
        axis=k('zbo',v('frame'),k(role),v('context'))
        selected=k('zsa',v('record'),axis,k('ra'),k('ta'),v('context'))
        clauses.append(q('f','record','a',op('y',selected,k('sexl',v('record'),axis,k('ra'),k('ta'),v('context')))))
    text+=definition('sexm','frame a context d',both(*clauses))
    text+=definition('sexn','','i[first a second a value '+CUT+' context d]['+both(
        app(k('sexh'),v('first'),v('second'),v('value'),v('context')),
        k('sexm',v('first'),v('context')),k('sexm',v('second'),v('context')))+']',FRAMES)
    return text


MEANINGS={
    'sexi':'有理数の順序付き二値の差が記録された増分に等しい。終値から始値を引き、絶対値へ変えない。',
    'sexj':'実切断の始値・終値・増分が有効であり、増分が終値から始値を引いた値に等しい。',
    'sexk':'同じ方向記録に結ばれた異なる二点と一時点について、両点が対象の配置点で、同じ観測座標・単位・文脈で三座標が利用できることを要求する。各方向成分がその二点の座標差に一致し、増分全体は非零である。',
    'sexl':'方向記録の候補二点と時点を取り出し、実際の記録への結合zsd、配置点zcc、位置の利用可能性zce、座標ymおよび方向成分zsbをsexkで接続する。',
    'sexm':'同じ系の三つの軸について、元の帰属zsaで選ばれた全方向記録がsexlを満たす。座標差に合わない記録を選択範囲から外さない。',
    'sexn':'元の二系・速度・物理配置および三軸の正方向sexhを保持し、両系の全選択方向記録を同時点の二点の座標差へ接続する。',
}
LIMITS=[
    '方向の数値を独立に与えるだけでなく、同じ記録に結ばれた配置点の座標差に一致させる改訂である。旧記録との無条件の意味同値は主張しない。',
    '候補項目zscだけでは二点・時点を取得済みとしない。zsdが同じ方向記録にその順序で実際に結び付いていることを要求する。未知の項目や座標を既知値へ補完しない。',
    '両端の位置座標は一つの時点・観測系・単位・文脈を共有する。別々の時点の位置差を軸の方向として流用しない。',
    '正方向への順序は既存のzsaの規約を保持する。軸自身の座標増分による正方向の校正、軸に沿う全点の直線性、計測や物質の基礎説明は未構成である。',
    '同じ対象の位置座標が存在し一意というzceの規約と、記録の完全性は残る。有限の記録から全空間・全時刻の配置を証明しない。',
    '共通原点・時計原点・慣性系・電気的帰属・全実数の演算法則・原文の適用範囲と全文の意味確認は未完である。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions());doc['statements']=deepcopy(old['statements'])
    expression=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert expression==dict(kind='call',symbol='seoz',arguments=[dict(kind='call',symbol=PREVIOUS_BINDINGS[n],arguments=[]) for n,_ in FIELDS])
    expression['arguments']=[dict(kind='call',symbol=BINDINGS[n],arguments=[]) for n,_ in FIELDS]
    basis=json.loads((ROOT/'data/einstein-axis-orientation-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-direction-measurements-basis-v1',document=FULL)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    decls={d['name']:d for d in doc['declarations']}
    for name,arguments,meaning in (
        ('zsc',['record','field_index'],'方向記録の候補項目。添字0は始点、1は終点、2は一つの共通観測時点。取得だけでは記録に結ばれた有効な項目とは認めず、zsdを別に要求する。'),
        ('zsd',['record','tail','head','moment','context'],'同じ方向記録に、この順序付き二点と一つの共通観測時点が実際に記録されている。両点の配置・位置座標の利用可能性・方向成分との一致は別の合成条件で検査する。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=arguments,meaning_ja=meaning))
    basis['interpretation_revision']=dict(parent=PARENT,statement_index=INDEX,changed_arguments=['frames'],previous_bindings=PREVIOUS_BINDINGS,
        fixed_bindings=BINDINGS,equivalence_to_parent_proven=False,new_primitives=2,configuration_relation_retained='zqf')
    audit_basis(doc,basis)
    review=json.loads((ROOT/'data/density-formula-review-v8.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v9',supersedes='data/density-formula-review-v8.json',source_document=FULL,document=CORE,fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id']=='source_context_bindings':
            row['evidence']='The frame relation sexn retains the ordered pair, signed velocity, original physical configuration and positive axis orientation, and binds all selected direction records to same-time endpoint coordinate differences.'
            row['limit']='The positive-axis calibration, physical measurement construction, origin and clock alignment, and full source-case coverage remain open.'
    review['checks'].insert(-1,dict(id='recorded_endpoint_displacement',status='connected_in_revised_reading',
        evidence='The original zsa record set is retained. Every selected record must have linked distinct endpoints on the same axis and available coordinates at one common moment/chart/unit/context; all three reported components equal head minus tail.',
        limit='Point placement, coordinate availability and record provenance have explicit primitive contracts. Their physical construction, positive-direction calibration and complete source-case coverage remain open.'))
    review['integrated_symbols']+=list(MEANINGS);review['evidence_reports'].append('reports/direction-measurements-v1.json');review['semantic_completion']=False
    files={FULL:format_graph(doc,'compact')+'\n','data/einstein-direction-measurements-basis-v1.json':basis,REVIEW:review}
    for path,roots,indices in ((CORE,[],[INDEX]),(LIBRARY,['sexi','sexk'],[])):
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
    print('Direction records connected to same-time endpoint coordinates',flush=True)


if __name__=='__main__':main()
