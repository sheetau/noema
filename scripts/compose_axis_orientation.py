"""Separate positive axis orientation from unoriented parallelism."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params
from scripts.compose_density_frame_binding import FULL as PARENT,INDEX,FIELDS,BINDINGS as PREVIOUS_BINDINGS
from scripts.compose_density_boost import CUT,FRAMES

FULL='examples/v014/einstein-axis-orientation.noema'
CORE='examples/v014/axis-orientation-manuscript.noema'
LIBRARY='examples/v014/oriented-directions.noema'
REVIEW='data/density-formula-review-v8.json'
BINDINGS={**PREVIOUS_BINDINGS,'frames':'sexh'}
NAMES='x y z u v w'.split()
SELECT='h[a a a a d] c'
COMPONENT='h[a a] '+CUT
PAIR=[('first','a'),('second','a'),('chart','a'),('unit','a'),('context','d'),
    ('xrole','a'),('yrole','a'),('zrole','a'),('selected',SELECT),('component',COMPONENT)]


def definitions():
    xs=[v(n) for n in NAMES];a=xs[:3];b=xs[3:]
    dot=lambda left,right:k('ab',k('ab',k('ad',left[0],right[0]),k('ad',left[1],right[1])),k('ad',left[2],right[2]))
    text=definition('sexa',params([(n,'b') for n in NAMES]),both(
        k('aa','n p a b',dot(a,a)),k('aa','n p a b',dot(b,b)),
        *(op('e',k('ad',a[i],b[j]),k('ad',a[j],b[i])) for i,j in ((0,1),(0,2),(1,2))),
        k('aa','n p a b',dot(a,b))))
    products=[k('shv',x,y) for x,y in zip(a,b)]
    text+=definition('sexb',params([(n,CUT) for n in NAMES]),k('bd',k('bd',*products[:2]),products[2]),CUT)
    valid=[k('ba',x) for x in xs]
    cross=[k('sca',k('shv',a[i],b[j]),k('shv',a[j],b[i])) for i,j in ((0,1),(0,2),(1,2))]
    text+=definition('sexc',params([(n,CUT) for n in NAMES]),both(*valid,
        k('sbg',k('sexb',*a,*a)),k('sbg',k('sexb',*b,*b)),*cross))
    text+=definition('sexd',params([(n,CUT) for n in NAMES]),both(k('sexc',*xs),k('sbg',k('sexb',*xs))))
    roles=[v(n+'role') for n in ('x','y','z')]
    selected=lambda record,axis:app(v('selected'),v(record),v(axis),v('chart'),v('unit'),v('context'))
    coords=lambda record:[app(v('component'),v(record),role) for role in roles]
    text+=definition('sexe',params(PAIR),both(
        *(op('u',op('e',roles[i],roles[j])) for i,j in ((0,1),(0,2),(1,2))),
        q('g','left','a',selected('left','first')),q('g','right','a',selected('right','second')),
        q('f','left','a',q('f','right','a',op('y',both(selected('left','first'),selected('right','second')),
            k('sexd',*coords('left'),*coords('right')))))))
    return text


def source_definitions():
    axis=lambda frame:k('zbo',v(frame),v('role'),v('context'))
    text='r zsa[a a a a d] c.r zsb[a a] '+CUT+'.\n'
    text+=definition('sexf','first a second a role a chart a unit a context d',both(
        k('zbw',v('first'),axis('first'),v('role'),v('context')),
        k('zbw',v('second'),axis('second'),v('role'),v('context')),
        k('sexe',axis('first'),axis('second'),v('chart'),v('unit'),v('context'),
            k('yn'),k('yo'),k('yp'),'p zsa','p zsb')))
    text+=definition('sexg','first a second a context d',both(k('va',k('ra')),k('ti',k('ta')),
        *(k('sexf',v('first'),v('second'),k(role),k('ra'),k('ta'),v('context')) for role in ('yn','yo','yp'))))
    text+=definition('sexh','','i[first a second a value '+CUT+' context d]['+both(
        app(k('sewz'),v('first'),v('second'),v('value'),v('context')),
        k('sexg',v('first'),v('second'),v('context')))+']',FRAMES)
    return text


MEANINGS={
    'sexa':'有理数の零でない二方向が平行で、内積が正である。同じ正の向きを持ち、長さの一致は要求しない。',
    'sexb':'実切断で与えた三成分の内積。共通の直交座標と成分単位を用いることは呼び出し側で指定する。',
    'sexc':'有効な六実成分からなる零でない二方向について、外積の三成分が零である。逆向きも許す平行条件。',
    'sexd':'sexcに加えて内積が正である。同じ正方向であり、単に鋭角をなす二方向や零方向は含めない。',
    'sexe':'同じ座標・単位・文脈で各対象に方向記録が少なくとも一つあり、両側の全記録対がsexdを満たす。三成分の役割は相異なる。不一致な記録を一つだけ選んで隠さない。',
    'sexf':'二系で同じ軸役割へ実際に割り当てられた軸を選び、共通の観測系・単位・文脈の正方向記録を比較する。候補軸の取得だけで割当て済みとはしない。',
    'sexg':'三つ全ての対応軸の正方向を静止系raの共通座標と長さ単位taで比較する。原点の位置、時計原点や慣性運動の条件は別に必要。',
    'sexh':'二系と速度の参照および元の物理的配置sewzを保持し、同じ文脈で対応三軸の正方向一致sexgを要求する。',
}
LIMITS=[
    '密度式M0390の標準配置を、対応三軸の正方向が一致する読解へ精密化した。逆向きを許す旧関係との無条件の意味同値は主張しない。',
    '方向記録zsaは同じ観測系の同一の直交座標・長さ単位で、軸の正の座標増分を表す非零変位を与える。軸上のどの二点を使ったか、その測定・校正・状況内の時刻の取り方は構成説明が残る。',
    '向きは正の倍率に対して不変であり、単位ベクトルを強制しない。記録の個体同一性や長さの一致も要求しない。',
    '原始記号zsaとzsbは記録の帰属と成分を与える意味規約であり、物理的な測定・軸や空間の基礎説明を済ませたとはしない。有限の記録を全領域の説明としない。',
    '元の物理配置zqfは保持する。共通原点・時計原点・慣性系・電気的帰属・全実数の演算法則・適用範囲と全文の意味確認は未完である。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions());doc['statements']=deepcopy(old['statements'])
    expression=doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert expression==dict(kind='call',symbol='seoz',arguments=[dict(kind='call',symbol=PREVIOUS_BINDINGS[n],arguments=[]) for n,_ in FIELDS])
    expression['arguments']=[dict(kind='call',symbol=BINDINGS[n],arguments=[]) for n,_ in FIELDS]
    basis=json.loads((ROOT/'data/einstein-density-frame-binding-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-axis-orientation-basis-v1',document=FULL)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    decls={d['name']:d for d in doc['declarations']}
    for name,arguments,meaning in (
        ('zsa',['record','axis','chart','length_unit','context'],'指定された軸の正の座標方向に沿う変位の方向記録が、この共通の直交観測座標・単位・状況に属する。記録の全候補を与え、候補が無い場合は空とする。数値だけからこの帰属を認定しない。'),
        ('zsb',['record','component_role'],'方向記録の指定空間成分の候補実数値。記録の帰属・共通の座標・単位・状況はzsaで、有効性と三成分の役割は合成条件で確認する。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=arguments,meaning_ja=meaning))
    basis['interpretation_revision']=dict(parent=PARENT,statement_index=INDEX,changed_arguments=['frames'],
        previous_bindings=PREVIOUS_BINDINGS,fixed_bindings=BINDINGS,equivalence_to_parent_proven=False,new_primitives=2,configuration_relation_retained='zqf')
    audit_basis(doc,basis)
    review=json.loads((ROOT/'data/density-formula-review-v7.json').read_text(encoding='utf-8'))
    review.update(version='density-formula-review-v8',supersedes='data/density-formula-review-v7.json',source_document=FULL,document=CORE,fixed_bindings=BINDINGS)
    for row in review['checks']:
        if row['id']=='source_context_bindings':
            row['evidence']='The quotation keeps its author, scope and coordinate units. Its frame relation sexh retains sewz, binding ra, zbm and zb7 and the original physical configuration predicate zqf, and adds positive orientation of all three assigned axes.'
            row['limit']='Direction records are bound to one chart, unit and context; their calibration, origins, clocks and complete source-case coverage remain open.'
    review['checks'].insert(-1,dict(id='positive_axis_orientation',status='connected_in_revised_reading',
        evidence='sexh preserves sewz and compares all direction records of the three assigned axes in one chart, unit and context. Nonzero collinearity and a positive dot product distinguish positive orientation from antiparallel axes.',
        limit='Direction-record calibration and physical construction, origin and clock alignment, and full source-case coverage remain open.'))
    review['integrated_symbols']+=list(MEANINGS);review['evidence_reports'].append('reports/axis-orientation-v1.json');review['semantic_completion']=False
    files={FULL:format_graph(doc,'compact')+'\n','data/einstein-axis-orientation-basis-v1.json':basis,REVIEW:review}
    for path,roots,indices in ((CORE,[],[INDEX]),(LIBRARY,['sexa','sexe'],[])):
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
    print('Positive orientation definitions and source revision composed',flush=True)


if __name__=='__main__':main()
