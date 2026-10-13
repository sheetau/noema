"""Reuse tagged integration for pi, disk sections and light-region volumes."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, lam
from scripts.compose_wave_amplitudes import params
from scripts.compose_light_complex import CUT, ENERGY

PARENT = 'examples/v014/einstein-light-complex.noema'
INTEGRALS = 'examples/v014/integrals.noema'
ALIASES = dict(zip(('na','nb','nc','nd','ne','nf','ni'), ('seda','sedb','sedc','sedd','sede','sedf','sedg')))
ALIASES.update(cd='shv',la='sjo',lb='sjp',lg='sxs')
ZERO, ONE, FOUR, EIGHT = 'n p a b','n p b b','n p e b','n p i b'


def rename(node):
    if isinstance(node,list):
        return [rename(item) for item in node]
    if not isinstance(node,dict):
        return node
    result = {key:rename(value) for key,value in node.items()}
    if 'symbol' in result:
        result['symbol'] = ALIASES.get(result['symbol'],result['symbol'])
    if result.get('kind') == 'definition':
        result['name'] = ALIASES.get(result['name'],result['name'])
    return result


def integral_declarations():
    old = parse((ROOT/INTEGRALS).read_text(encoding='utf-8'))
    return [rename(d) for d in old['declarations'] if d['name'] in ('na','nb','nc','nd','ne','nf','ni')]


def rational_definitions():
    mul=lambda a,b:k('ad',a,b)
    sub=lambda a,b:k('ab',a,k('ac',b))
    sq=lambda a:mul(a,a)
    x,value,R,pi,D,volume=map(v,('x','value','radius','pi','factor','volume'))
    text=definition('seea','x b value b',both(op('u',k('aa',x,ZERO)),op('u',k('aa',ONE,x)),
        k('aa',ZERO,value),op('e',mul(k('ab',ONE,sq(x)),value),ONE)))
    text+=definition('seeb',params('pi radius x','b'),mul(pi,sub(sq(R),sq(x))),'b')
    text+=definition('seec',params('pi radius factor x','b'),mul(pi,sub(sq(R),sq(mul(D,x)))),'b')
    ball=mul('n p e d',mul(pi,mul(R,sq(R))))
    text+=definition('seed',params('radius pi volume','b'),both(*[k('aa',ZERO,q) for q in (R,pi,volume)],op('e',volume,ball)))
    text+=definition('seee',params('radius pi factor volume','b'),both(*[k('aa',ZERO,q) for q in (R,pi,D,volume)],op('e',mul(D,volume),ball)))
    text+=definition('seef',params('pi radius factor x','b'),mul(pi,sub(mul(sq(R),x),mul('n p b d',mul(sq(D),mul(x,sq(x)))))),'b')
    return text


RATIONAL_MEANINGS={
    'seea':'0≤x≤1における正の有理数値yが(1+x²)y=1を満たす。πの積分の被積分関数の有理数でのグラフ。',
    'seeb':'係数piと半径radiusから作る、pi*(radius²−x²)という断面積の多項式。係数をπとする条件は別途必要。',
    'seec':'同じ多項式の位置引数をfactor倍にしたもの。断面の中心の平行移動は面積に影響しないという幾何学的解釈とは区別する。',
    'seed':'正の三数についてvolume=(4/3)*pi*radius³を要求する。有理数piは比較用の係数で、円周率そのものと認定しない。',
    'seee':'正の四数についてfactor*volume=(4/3)*pi*radius³を要求する。',
    'seef':'断面多項式の原始関数候補pi*(radius²*x−factor²*x³/3)。微分・積分の一般法則はこの式だけから認定しない。',
}


def generic_composed():
    old=parse((ROOT/INTEGRALS).read_text(encoding='utf-8'))
    oldbasis=json.loads((ROOT/'data/integrals-basis-v1.json').read_text(encoding='utf-8'))
    selected=extract_document(old,roots=['ma','mb','mc','md','mg'],statement_indices=[])
    basis=extract_basis(old,oldbasis,selected,version='geometric-volumes-basis-v1',document_path='examples/v014/geometric-volumes.noema')
    doc=parse(format_graph(selected.document,'compact')+rational_definitions())
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['unresolved']+=['πの有限上下界や断面多項式の検査用。円周率そのものを有限小数・有理数で置換しない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    z,o,four,eight=[k('bb',n) for n in (ZERO,ONE,FOUR,EIGHT)]
    mul=lambda a,b:k('shv',a,b)
    sq=lambda a:mul(a,a)
    x,pi,R,area,volume=map(v,('x','pi','radius','area','volume'))
    text=definition('sedh',params('x',CUT),k('sjd',k('bd',o,sq(x))),CUT)
    text+=definition('sedi',params('pi',CUT),both(k('ba',pi),k('bg',z,pi),
        k('sede',z,o,'p sedh',mul(k('bb','n p b e'),pi))))
    height=lam('x',CUT,k('sky',k('bf',sq(R),sq(x))))
    text+=definition('sedj',params('radius pi area',CUT),both(k('sedi',pi),k('ba',R),k('bc',z,R),
        k('ba',area),k('bc',z,area),k('sedf',z,R,height,mul(k('bb','n p b e'),area))))
    text+=definition('sedk',params('radius pi area',CUT),both(k('sedi',pi),k('ba',R),k('bc',z,R),
        k('ba',area),k('bc',z,area),k('sca',area,mul(pi,sq(R)))))
    text+=definition('sedl',params('pi radius x',CUT),mul(pi,k('bf',sq(R),sq(x))),CUT)
    text+=definition('sedm',params('radius pi volume',CUT),both(k('sedi',pi),k('ba',R),k('bg',z,R),
        k('ba',volume),k('bg',z,volume),k('sede',k('be',R),R,lam('x',CUT,k('sedl',pi,R,x)),volume)))
    ball=mul(k('bb','n p e d'),mul(pi,mul(R,sq(R))))
    text+=definition('sedn',params('radius pi volume',CUT),both(k('sedi',pi),k('ba',R),k('bg',z,R),
        k('ba',volume),k('bg',z,volume),k('sca',volume,ball)))
    V,s,a,b,c=map(v,('light','speed','ax','ay','az'))
    D=k('sdn2',V,s,o,a)
    width=mul(R,k('sjd',D))
    ellipse=lam('x',CUT,k('sedl',pi,R,mul(D,x)))
    text+=definition('sedo',params('light speed ax ay az radius pi volume',CUT),both(
        *[k('ba',v(n)) for n in ('light','speed','ax','ay','az','radius','volume')],k('s45',V,s),
        k('sca',k('seag',a,b,c),o),k('sedi',pi),k('bg',z,R),k('bg',z,volume),
        k('sede',k('be',width),width,ellipse,volume)))
    oldvolume,newvolume=map(v,('volume','newvolume'))
    text+=definition('sedp',params('light speed ax ay az radius pi volume newvolume',CUT),both(
        k('sedm',R,pi,oldvolume),k('sedo',V,s,a,b,c,R,pi,newvolume)))
    text+=definition('sedq',params(ENERGY.replace('conversion','pi'),CUT),both(k('sedi',pi),
        k('seci',V,s,a,v('power'),v('newpower'),oldvolume,newvolume,mul(eight,pi),v('energy'),v('newenergy'))))
    power,density=map(v,('power','density'))
    text+=definition('sedr',params('pi power density',CUT),both(k('sedi',pi),
        k('ba',power),k('bc',z,power),k('ba',density),k('bc',z,density),k('sca',mul(mul(eight,pi),density),power)))
    return text


MEANINGS={
    'sedh':'実切断xに対して1/(1+x²)を構成する。有効な実入力では分母が正。',
    'sedi':'有効で正の切断piを、0から1までのsedhの積分がpi/4となる関係で指定する。小数近似や任意の正数をπと認定しない。',
    'sedj':'sediのpiと非負半径について、第一象限の円弧高さsqrt(radius²−x²)の向き付き積分の4倍を円板面積として指定する。零半径では面積零を許す。円周長によるπの定義との一致は別途証明が必要。',
    'sedk':'sediのpiと非負半径について、面積=pi*radius²という式。sedjとの同値性を前提に含めない。',
    'sedl':'pi*(radius²−x²)という球の円板断面の面積式を構成する。幾何学的解釈では|x|≤radiusを要求する。',
    'sedm':'正の半径の球の体積を、−radiusからradiusまでのsedlの積分として指定する。断面積積分による体積の定義であり、一般の三次元測度との一致は未証明。',
    'sedn':'sediのpiと正の半径・体積についてvolume=(4/3)*pi*radius³を要求する。sedmとの同値性は別途検証する。',
    'sedo':'許容速度と単位方向に対するD=β(1−av/V)を用い、−R/DからR/Dまでpi*(R²−D²x²)を積分した値を変換後の断面体積とする。横方向の断面中心の移動は面積に影響しないというユークリッド幾何での解釈。',
    'sedp':'同じ半径・sediで指定したpiについて、元の球と変換後の断面の二つの体積積分が成立する。体積比sechの結論を条件に含めない。',
    'sedq':'sediによりpiを指定し、前版seciの共通換算係数を8*piへ固定する。物理的なエネルギー密度の法則や測定が存在することまで証明しない。',
    'sedr':'sediのpiと非負二乗振幅・密度について8*pi*density=powerを要求する。零振幅・零密度は許し、比の分母となるエネルギーの正値条件とは区別する。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-light-complex-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc['declarations']+=integral_declarations()
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-geometric-volumes-basis-v1',document='examples/v014/einstein-geometric-volumes.noema')
    oldbasis=json.loads((ROOT/'data/integrals-basis-v1.json').read_text(encoding='utf-8'))
    for old in ('na','nb','nc','nd','ne','nf','ni'):
        basis['definitions'][ALIASES[old]]='既存'+old+'の名前を置換して再利用。'+oldbasis['definitions'][old]
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '先行版で未指定だった換算係数8πのπを、全分割に量化した積分で指定する。積分の存在・一意性と円周長比との一致の一般的な機械証明は未完であり、有限上下界で代用しない。',
        '球と楕円体の体積を断面積の積分で記述する。断面の面積公式、積分による円板面積とpi*R²の同値性、座標系に依存しない一般の三次元測度および積分変数の変換則の機械的証明は未完。',
        'エネルギー密度の物理法則、同じ光の集合、境界をエネルギーが横切らないこと、測定・観測者・単位の帰属、本文全体の意味一致は引き続き未完。既存173件の著者主張を保持する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['sedj','sedk','sedn','sedp','sedq','sedr'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='geometric-volumes-core-basis-v1',document_path='examples/v014/geometric-volumes-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'geometric-volumes'),(source_composed,'einstein-geometric-volumes'),(core_composed,'geometric-volumes-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored geometric volumes differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
