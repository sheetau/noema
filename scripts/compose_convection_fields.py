"""Bind convective source terms and charge density to the same field partials."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_field_equations import CUT,FIELD,POINT,REGION,JET,ROLES,TAU
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-area-time-flux.noema'
SCALAR='light rate positive negative density drift'
DENSITY='density charge conversion xx yy zz'
FIELDS=[('electric',FIELD),('magnetic',FIELD),('region',REGION),('point',POINT)]
JETS=[('electricjet',JET),('magneticjet',JET)]
BALANCE=[('light',CUT),('density',CUT),('velocity',POINT)]+JETS
POINT_FIELDS=FIELDS+BALANCE
REGIONAL=FIELDS[:3]+[('light',CUT),('densityfield',TAU),('velocityfield',FIELD)]
ASSIGN='h[a a '+TAU+' '+TAU+' '+FIELD+' '+REGION+' d] c'
INPUTS=[('matter','a'),('frame','a'),('event','a'),('context','d')]+FIELDS+[
    ('light',CUT),('densityfield',TAU),('chargefield',TAU),('velocityfield',FIELD)]+JETS+[('pi',CUT),('assigned',ASSIGN)]
ROOTS=['sema','semb','semc','semd','seme','semf','semg','semh','semi','semj','semk','seml','semm','semn','semo']


def scalar_definition(real=False):
    add=lambda a,b:k('bd' if real else 'ab',a,b)
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    neg=lambda a:k('be' if real else 'ac',a)
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    zero=k('bb','n p a b') if real else 'n p a b'
    conditions=[k('ba',v(n)) for n in SCALAR.split()] if real else []
    conditions+=[k('bg' if real else 'aa',zero,v('light')),
        eq(add(v('rate'),mul(v('density'),v('drift'))),mul(v('light'),add(v('positive'),neg(v('negative')))))]
    return definition('semc' if real else 'sema',params([(n,CUT if real else 'b') for n in SCALAR.split()]),both(*conditions))


def rational_definitions():
    return scalar_definition()+definition('semb',params([(n,'b') for n in DENSITY.split()]),both(
        k('aa','n p a b',v('conversion')),op('e',v('density'),k('ad',v('conversion'),v('charge'))),
        op('e',v('density'),k('ab',k('ab',v('xx'),v('yy')),v('zz')))))


def at(field):
    return app(field,*(app(v('point'),k(role)) for role in ROLES))


def point_values():
    return dict(density=at(v('densityfield')),velocity='i[axis a]['+at(app(v('velocityfield'),v('axis')))+']')


def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b')
    entry=lambda jet,component,axis:app(v(jet),k(component),k(axis))
    text=scalar_definition(True)
    text+=definition('semd',params([('electricjet',JET),('density',CUT)]),both(k('ba',v('density')),
        *(k('ba',entry('electricjet',role,role)) for role in ROLES[:3]),k('sca',v('density'),k('s6q',v('electricjet')))))
    for symbol,printed in (('seme',False),('semf',True)):
        equations=[k('ba',v('density'))]+[k('ba',app(v('velocity'),k(role))) for role in ROLES[:3]]
        for i,component in enumerate(ROLES[:3]):
            following,last=ROLES[(i+1)%3],ROLES[(i+2)%3]
            equations.append(k('semc',v('light'),entry('electricjet',component,ROLES[3]),
                entry('magneticjet',last,following),entry('magneticjet',following,last),v('density'),app(v('velocity'),k(component))))
            equations.append(k('s5v',one if printed else v('light'),entry('magneticjet',component,ROLES[3]),
                entry('electricjet',following,last),entry('electricjet',last,following)))
        text+=definition(symbol,params(BALANCE),both(*equations))
    partials=[k('s5u',*args(FIELDS+JETS))]
    partials += [k('s5t',app(v('electric'),k(role)),v('region'),v('point'),k(role),entry('electricjet',role,role)) for role in ROLES[:3]]
    text+=definition('semg',params(FIELDS+JETS),both(*partials))
    for symbol,balance in (('semh','seme'),('semi','semf')):
        text+=definition(symbol,params(POINT_FIELDS),both(k('semg',*args(FIELDS+JETS)),
            k('semd',v('electricjet'),v('density')),k(balance,*args(BALANCE))))
    inside=both(k('shn',k('shx'),v('point'),'p ba'),at(v('region')))
    for symbol,condition in (('semj','semh'),('semk','semi')):
        equation=k(condition,*args(POINT_FIELDS,**point_values()))
        jets=quant('g','electricjet',JET,quant('g','magneticjet',JET,equation))
        text+=definition(symbol,params(REGIONAL),both(k('ba',v('light')),k('bg',zero,v('light')),
            quant('g','point',POINT,inside),quant('f','point',POINT,op('y',inside,jets))))
    text+=definition('seml',params([('pi',CUT),('density',CUT),('charge',CUT)]),both(k('sedi',v('pi')),
        k('ba',v('density')),k('ba',v('charge')),k('sca',v('density'),k('shv',k('bj','n p e b',v('pi')),v('charge')))))
    binding=both(k('va',v('frame')),k('znn',v('frame'),v('electric'),v('magnetic'),v('region'),v('context')),
        k('zpb',v('matter'),v('frame'),v('event'),v('point'),v('context')),
        app(v('assigned'),*map(v,('matter','frame','densityfield','chargefield','velocityfield','region','context'))),inside)
    text+=definition('semm',params(INPUTS),binding)
    for symbol,condition in (('semn','semh'),('semo','semi')):
        text+=definition(symbol,params(INPUTS),both(k('semm',*args(INPUTS)),
            k(condition,*args(POINT_FIELDS,**point_values())),
            k('seml',v('pi'),at(v('densityfield')),at(v('chargefield')))))
    return text


RATIONAL_MEANINGS={
    'sema':'正のVについて、時間変化率と密度・流速の積の和が、Vと二空間微分値の差の積に等しいという有理数の関係。電荷密度と流速の符号を制限しない。',
    'semb':'正の換算係数Cについて、規格化した密度がC倍の電荷密度で、同時に三つの対角微分の和に等しい。有理数の比較用で、Cを実際の4πとする証明ではない。',
}
MEANINGS={
    'semc':'semaの関係を有効な実切断で記述する。流れの項を時間微分と同じ辺に加え、分母を払って正のVを保持する。',
    'semd':'同じ電気側の微分表の三空間対角値の和が規格化した密度である。三値と密度が有効な実切断であることを要求する。',
    'seme':'電気側の三式に同じ密度と対応する流速成分の積を加え、磁気側の三式には従来のV倍の回転を用いる。原刊916頁の変換前M0383の六式。',
    'semf':'原刊916頁の変換後M0389に印刷された六式。電気側はsemeと同形だが、磁気側の時間微分の係数1/Vがない形を別に保持する。変換則からの導出結果と同一視しない。',
    'semg':'同じ二場・領域・四座標に、六つの回転の式で必要な18偏微分と電気側の三つの空間対角偏微分を結ぶ。使わない磁気側の三対角微分や零発散を追加条件にしない。',
    'semh':'同じ場と点に結ばれた21偏微分、電気側の発散による密度semd、流れを伴う六式semeを同時に要求する。',
    'semi':'semhと同じ21偏微分と発散の密度を、印刷形semfの六式へ結ぶ。式を黙って修正せず別の条件にする。',
    'semj':'指定領域に有効な四座標が存在し、その全てで同じ二場・密度場・流速場・正のVについてsemhを満たす微分表が存在する。有限点の検査をこの全域条件の証明にしない。',
    'semk':'semjの全域条件を、変換後に印刷された六式semiについて記述する。',
    'seml':'既存の積分によるπの指定を使い、規格化した密度ρが実際の電荷密度の4π倍であることを表す。符号付きの密度と零密度を許す。',
    'semm':'同じ物質・基準系・出来事・文脈・地点に二つの場と領域、規格化した密度場・電荷密度場・流速場を結ぶ。電荷を含む物質への割当は引数で明示し、数値一致から帰属を推定しない。',
    'semn':'semmの割当と地点で密度場・流速場を評価し、同じ21偏微分のsemhと、電荷密度の4π倍というsemlを接続する。',
    'semo':'semnと同じ帰属・地点・密度の換算を、原刊の変換後の印刷形semiに接続する。基準系間の変換関係は別に記述する。',
}
LIMITS=[
    'ρは電荷密度そのものではなく4π倍の量である。電流項ρuはその規格化に対応する。単位系と電気量の測定の実現、物質への帰属、イオン・電子・剛体・不変に結びつくことの一般的な意味は未完。',
    '一つの密度と一つの速度を共有する対流の形を記述する。複数の電荷種の流れを、合計密度と単一の速度の積へ無条件に置換しない。',
    'M0389の磁気側三式には原刊でも係数1/Vがない。転記訂正とはせずsemfで保持する。今回の比較は係数の相違であり、全場の変換からの導出や誤植の歴史的確定ではない。',
    '既存の相対的な差商極限で偏微分を構成する。実関数全域の微分存在、連鎖律、境界条件、開領域と物理的意味の完全な証明は未完。磁気側の発散条件は原文の六式へ勝手に加えない。',
    '全域条件は明示するが、有限検査では有理数を埋め込んだ実切断とアフィン関数の微分オラクルを用いる。全実数上の解析や実際の電磁場の測定を検証したものではない。',
]


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions())
    labels={'aa':'有理数の厳密順序。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis=dict(version='convection-fields-basis-v1',document='examples/v014/convection-fields.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']]) for d in doc['declarations'] if d['kind']=='primitive'],
        definitions=RATIONAL_MEANINGS.copy(),unresolved=LIMITS.copy())
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-area-time-flux-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+rational_definitions()+definitions());doc['statements']=statements
    basis.update(version='einstein-convection-fields-basis-v1',document='examples/v014/einstein-convection-fields.noema')
    basis['definitions'].update(RATIONAL_MEANINGS|MEANINGS);basis['unresolved']+=LIMITS+[
        'u0229・u0231の式、u0232の密度と速度の説明、u0234の変換後の印刷形へ部分接続する。新しい原始概念・局所参照・著者の主張を追加しない。',
        'u0233の基準系Kからkへの帰属を保った変換、M0390の速度と密度の変換、u0237の相対性原理との適合、u0238の電荷不変の議論と全文の意味一致は未完。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=ROOTS,statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='convection-fields-core-basis-v1',document_path='examples/v014/convection-fields-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'convection-fields'),(source_composed,'einstein-convection-fields'),(core_composed,'convection-fields-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored convection fields differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
