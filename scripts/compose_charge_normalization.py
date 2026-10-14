"""Connect divergence normalization to physical density and material charge."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_boost import FLOW
from scripts.compose_material_charge import CELL,JAC,CUT,INPUTS as MATERIAL
from scripts.compose_field_equations import JET

PARENT='examples/v014/einstein-material-charge.noema'
NORMAL='conversion normalized newnormalized'
SCALE=FLOW+' '+NORMAL
TOTAL=CELL+' '+NORMAL
PI=CELL+' pi normalized newnormalized'
INPUTS=MATERIAL+[('pi',CUT),('normalized',CUT),('newnormalized',CUT)]
JETS=[('electricjet',JET),('newelectricjet',JET)]
JET_ASSIGN='h[a a a '+JET+' d] c'
BOUND=INPUTS+JETS+[('jetassigned',JET_ASSIGN)]
ROOTS=['senj','senk','senl','senm','senn','seno','senp','senq']


def definitions(real=False):
    scale,total=('senl','senm') if real else ('senj','senk')
    sort=CUT if real else 'b';zero=k('bb','n p a b') if real else 'n p a b'
    mul=lambda a,b:k('shv' if real else 'ad',a,b)
    eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
    lt=lambda a,b:k('bg' if real else 'aa',a,b)
    valid=lambda names:[k('ba',v(n)) for n in names.split()] if real else []
    normalized={n:v(n) for n in FLOW.split()}
    normalized.update(density=v('normalized'),newdensity=v('newnormalized'))
    text=definition(scale,params([(n,sort) for n in SCALE.split()]),both(*valid(SCALE),lt(zero,v('conversion')),
        eq(v('normalized'),mul(v('conversion'),v('density'))),eq(v('newnormalized'),mul(v('conversion'),v('newdensity'))),
        k('semt' if real else 'semp',*(normalized[n] for n in FLOW.split()))))
    text+=definition(total,params([(n,sort) for n in TOTAL.split()]),both(*valid(TOTAL),k(scale,*map(v,SCALE.split())),
        k('seng' if real else 'send',*map(v,JAC.split())),lt(zero,v('volume')),lt(zero,v('newvolume')),
        eq(v('newvolume'),mul(v('stretch'),v('volume'))),
        eq(v('charge'),mul(v('density'),v('volume'))),eq(v('newcharge'),mul(v('newdensity'),v('newvolume')))))
    return text


MEANINGS={
    'senj':'同じ正の換算係数Cで両側の規格化密度をC倍の電荷密度に結び、規格化密度と三速度に先行版sempの変換を課す。電荷密度自体の変換や総電荷の等値は前提に追加しない。',
    'senk':'senjの同じ換算と密度変換に、同時刻切片の体積変換send、正の体積、各側の総電荷＝電荷密度×体積を結ぶ。規格化密度×体積を物理的な電荷の値と混同しない。',
    'senl':'senjの共通の正の換算係数と密度変換を、有効な実切断で記述する。有理数の比較係数を4πそのものと認定しない。',
    'senm':'senkの換算・同時刻体積・総電荷を有効な実切断で記述する。電荷密度に対するsenhは前提に含めず、規格化密度側の変換から導く対象として分ける。',
    'senn':'同じπの指定と両側のsemlの4π換算を、C=4πのsenmへ結ぶ。積分で定めたπの値を使う構成であり、πを近似有理数に置き換えない。',
    'seno':'sennを同じ物質領域・二系・二切片の密度・体積・総電荷の割当へ結ぶ。規格化密度と電荷密度を別の引数に保ち、割当関係は電荷密度と物理的な総電荷を受け取る。',
    'senp':'sennに、同じ二つの規格化密度がそれぞれの電気側の微分表の発散semdに等しいことを加える。微分表の入力を、電荷密度へ無断で読み替えない。',
    'senq':'senoとsenpを同じ値で結び、二つの微分表も同じ物質領域・基準系・切片・文脈へ割り当てる。任意の数表が実際の場の微分であるという根拠を数値一致だけから補わない。',
}
LIMITS=[
    '規格化密度と電荷密度を別の数値として保持する。総電荷の式で使うのは電荷密度であり、規格化密度に体積を掛けた値はC倍の総電荷である。',
    '有理数版のCは正の一般係数である。二系で別の換算を無断で使うと、規格化した総量が一致しても物理的な総量の一致は導けない。密度零の観測値だけから換算係数が一意に同定できるとも主張しない。',
    'senn以降は既存seml・sediの同じπを使う。有限解釈で使うπ判定オラクルは接続検査用であり、πの実値や全実数の積分を有限の有理値で証明したものではない。',
    'jetassignedは同じ物質領域の二つの同時刻切片へ電気側の微分表を割り当てる関係入力である。全場の偏微分の存在、同じ切片全域での密度の一様性、異なる時刻面での同じ物体の追跡は別途必要である。',
    '前版の一様並進・正の同時刻体積という条件を引き継ぐ。任意の加速・変形、非一様密度の体積積分、動く境界の流束、一般の保存則は未完。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-material-charge-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()+definitions(True)
    converted={n:v(n) for n in TOTAL.split()};converted['conversion']=k('bj','n p e b',v('pi'))
    text+=definition('senn',params([(n,CUT) for n in PI.split()]),both(
        k('seml',v('pi'),v('normalized'),v('density')),k('seml',v('pi'),v('newnormalized'),v('newdensity')),
        k('senm',*(converted[n] for n in TOTAL.split()))))
    binding=[app(v('frames'),v('oldframe'),v('newframe'),v('speed'),v('context')),
        app(v('paired'),*map(v,('matter','oldframe','newframe','oldslice','newslice','context')))]
    for prefix,density,volume,charge in (('old','density','volume','charge'),('new','newdensity','newvolume','newcharge')):
        binding.append(app(v('assigned'),v('matter'),v(prefix+'frame'),v(prefix+'slice'),v(density),v(volume),v(charge),v('context')))
    text+=definition('seno',params(INPUTS),both(*binding,k('senn',*map(v,PI.split()))))
    text+=definition('senp',params([(n,CUT) for n in PI.split()]+JETS),both(k('senn',*map(v,PI.split())),
        k('semd',v('electricjet'),v('normalized')),k('semd',v('newelectricjet'),v('newnormalized'))))
    text+=definition('senq',params(BOUND),both(k('seno',*args(INPUTS)),k('senp',*map(v,PI.split()),*args(JETS)),
        app(v('jetassigned'),v('matter'),v('oldframe'),v('oldslice'),v('electricjet'),v('context')),
        app(v('jetassigned'),v('matter'),v('newframe'),v('newslice'),v('newelectricjet'),v('context'))))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='einstein-charge-normalization-basis-v1',document='examples/v014/einstein-charge-normalization.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS+[
        '前版に残した4πの換算を同じ物質領域の総量へ接続する。既存の場の微分表の発散と、電荷密度・体積・電荷の割当を別々の値へ分離しない。',
        'u0238への同じ部分的な解釈注記を精密化する。原文の任意運動の主張や物理的な単位の実現を完成させたものではなく、新しい本文主張・原始概念・原文範囲は追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS[:2],'charge-normalization')
def core_composed():return projected(ROOTS+['senh','seni'],'charge-normalization-core')
BUILDERS=((generic_composed,'charge-normalization'),(source_composed,'einstein-charge-normalization'),(core_composed,'charge-normalization-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored charge normalization differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
