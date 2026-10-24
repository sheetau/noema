"""Compose material-free space-time regions and calibrated electromagnetic fields."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_electrodynamic_part_heading import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_field_equations import POINT,REGION,FIELD,ROLES
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-electrodynamic-part-heading.noema'
PARENT_BASIS='data/electrodynamic-part-heading-basis-v1.json'
FULL='examples/v014/einstein-vacuum-field-domain.noema'
CORE='examples/v014/vacuum-field-domain-core.noema'
BASIS='data/vacuum-field-domain-basis-v1.json'
ANNOTATIONS='data/vacuum-field-domain-identifiers-v1.json'
CHART=[('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')]
VACUUM=CHART+[('region',REGION)]
FIELDS=VACUUM+[('chargeunit','a'),('electricunit','a'),('magneticunit','a'),('forceunit','a'),('electricconversion',R),('magneticconversion',R),('electricfield',FIELD),('magneticfield',FIELD)]
MEANINGS={
 'ejsj':'相異なる三空間軸と時刻の四役割で取り出した値が全て有効な実数であり、同じ四値が指定四座標領域に属する。有効性・役割の違いを保ち、空間と時刻を交換しない。',
 'ejsk':'指定系・文脈・長さ時間単位の有効な四座標について、その位置と時刻を物質領域として占有する物体が全個体域に存在しない。既存eiroを否定量化し、正味電荷零や物質の記録不足を真空へ代用しない。',
 'ejsl':'同じ系の長さ・時間単位が適格かつ別であり、eisddの校正されたCartesian基底と時刻規約を共有する座標記述条件。別系・別単位の占有判定を混ぜない。',
 'ejsm':'ejslの同じ座標規約で、有効な四座標を持つ指定領域が非空であり、その全有効点についてejskの物質占有の不存在が成立する。境界や外部の物体は、その座標が領域に入らない限り排除しない。',
 'ejsn':'同じ系・文脈・領域への電気側と磁気側の場割当znnを、それぞれの場単位eirnと、同じ電荷・力単位に対するeirm/eiruの物理的同定規約へ接続する。換算係数は正の有効実数とし、磁気側では同じ長さ時間の速度単位を保つ。任意の数値関数や別の場の単位を物理的な場の代用にしない。',
 'ejso':'同じ全引数の場割当と単位規約ejsnに、同じ領域の物質占有の不存在ejsmを合わせる。場があることと物質があることを区別し、電場・磁場が零である条件を真空へ追加しない。',
 'ejsp':'同じ真空領域・物理的な二場・単位規約ejsoと、指定した同じ正のlight値に対する六つの回転方程式s5yを結ぶ。領域・二場・定数を別の証人へ交換せず、発散条件や変換の正しさを六式から補わない。',
}
LIMITS=[
 'u0152の第六節見出しと続く方程式の仮定に向けた依存定義であり、本文357主張を変更しない。見出しの全主題、方程式の固有名、引用と変換、起電力の性質の案内への接続は別途必要で、今回だけでは全単位の意味判断を増やさない。',
 '真空は指定領域内に物質が占有する位置・時刻がないという古典的な読みを採る。eiroの全個体域に対する不存在を使い、帯電物体だけでなく中性物質や物質的媒体も除く。外部源が作る場、光や電磁場自身は物質占有へ自動分類しない。未知の占有を偽と補わない。',
 '領域は同じ座標と単位で指定する。内部に含めた物質表面は除外対象となり、外部や除外した境界の放出源・物体は許す。非空性は要求するが、この条件だけで四次元の開集合、微分可能性、全点への実測済みを認定しない。',
 '場の意味は既存znn/eirnの割当・単位とeirm/eiruの電気側・磁気側の物理的同定規約を共有する。試験電荷による力の同定を、真空内に実際の試験粒子を追加した存在主張にはしない。特定の電荷の力を述べる際は既存eibs/eicoの同じ出来事・記録・速度との結合を用いる。',
 'light引数の正値はs5yが要求する。光速度であるという本文上の指示と尺度は適用時に既出V=tc及び単位規約へ接続する必要がある。正の数だけから光速度の物理的同定や普遍法則を認定しない。場と力の換算係数を1や1/Vへ先に固定しない。',
 '六つの回転式を、発散条件を含む完全な場の方程式と取り違えない。物質占有の不存在という条件を追加しただけでは、Noemaの推論として発散零やLorentz変換後の式は得られない。必要な追加法則・連鎖律・物理的適用条件は後続で明示する。',
 '全四座標領域への量化は正本に保持する。局所検査は二つの明示した座標関数を用いた代入診断と、実際の点ごとの本体を分ける。全実数・全関数域の有限列挙拒否を維持し、有限の非占有例を全空間の真空の証明へしない。',
]


def definitions():
    point=v('point');coords=[app(point,k(n)) for n in ROLES]
    roles=[op('u',op('e',k(a),k(b))) for i,a in enumerate(ROLES) for b in ROLES[i+1:]]
    valid=both(*roles,*(k('ba',x) for x in coords))
    text=define('ejsj',[('point',POINT),('region',REGION)],both(valid,app(v('region'),*coords)))
    occupied=k('eiro',v('body'),v('frame'),v('context'),v('lengthunit'),v('timeunit'),*coords)
    text+=define('ejsk',CHART+[('point',POINT)],both(valid,op('u',q('g','body','a',occupied))))
    text+=define('ejsl',CHART,both(k('va',v('frame')),k('ti',v('lengthunit')),k('ci',v('timeunit')),op('u',op('e',v('lengthunit'),v('timeunit'))),k('eisdd',*[v(n) for n,_ in CHART])))
    inside=k('ejsj',point,v('region'))
    text+=define('ejsm',VACUUM,both(k('ejsl',*[v(n) for n,_ in CHART]),q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,k('ejsk',*[v(n) for n,_ in CHART],point)))))
    units=[k('eirn',v('frame'),v(field),v(unit),v('context')) for field,unit in (('electricfield','electricunit'),('magneticfield','magneticunit'))]
    positive=[both(k('ba',v(n)),k('bg',k('bb','n p a b'),v(n))) for n in ('electricconversion','magneticconversion')]
    electric=k('eirm',*[v(n) for n in ('chargeunit','electricunit','forceunit','electricconversion','context')])
    magnetic=k('eiru',*[v(n) for n in ('frame','chargeunit','lengthunit','timeunit','magneticunit','forceunit','magneticconversion','context')])
    text+=define('ejsn',FIELDS,both(k('ejsl',*[v(n) for n,_ in CHART]),k('znn',v('frame'),v('electricfield'),v('magneticfield'),v('region'),v('context')),*units,*positive,electric,magnetic))
    text+=define('ejso',FIELDS,both(k('ejsn',*[v(n) for n,_ in FIELDS]),k('ejsm',*[v(n) for n,_ in VACUUM])))
    text+=define('ejsp',FIELDS+[('light',R)],both(k('ejso',*[v(n) for n,_ in FIELDS]),k('s5y',v('electricfield'),v('magneticfield'),v('region'),v('light'))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==357
    doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='material_free_region_and_calibrated_electromagnetic_field_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electrodynamic-part-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
