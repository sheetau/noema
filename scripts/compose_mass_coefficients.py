"""Separate a force equation at one input from its directional coefficients."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,op,both,quant
from scripts.compose_situated_criticism import params

ROOT=Path(__file__).resolve().parents[1]
PARENT='examples/v014/einstein-reconciled-v1.noema'
SOURCE='examples/v014/einstein-mass-coefficients.noema'
LIBRARY='examples/v014/mass-coefficients.noema'
CORE='examples/v014/mass-coefficients-core.noema'
CUT='h[b] c'
FACTORS='light speed beta restmass longitudinal transverse'
COMPONENTS='ax ay az fx fy fz'
CONVENTION='matter forceframe accelerationframe event forceunit accelerationunit'
READING='data/mass-coefficients-reading-v1.json'


def definitions():
    text=''
    for real,names in ((False,('sepa','sepb','sepc','sepd')),(True,('sepe','sepf','sepg','seph'))):
        typ=CUT if real else 'b'
        fields=lambda words:params([(n,typ) for n in words.split()])
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        valid=lambda words:[k('ba',v(n)) for n in words.split()] if real else []
        normal=k('srd' if real else 'sra',*map(v,('light','speed','beta')))
        longitudinal=mul(v('restmass'),mul(mul(v('beta'),v('beta')),v('beta')))
        transverse=mul(v('restmass'),mul(v('beta'),v('beta')))
        text+=definition(names[0],fields('mass acceleration force'),both(*valid('mass acceleration force'),eq(mul(v('mass'),v('acceleration')),v('force'))))
        text+=definition(names[1],fields(FACTORS),both(*valid(FACTORS),normal,
            eq(v('longitudinal'),longitudinal),eq(v('transverse'),transverse)))
        text+=definition(names[2],fields('light speed beta restmass '+COMPONENTS),both(*valid('light speed beta restmass '+COMPONENTS),normal,
            eq(mul(longitudinal,v('ax')),v('fx')),eq(mul(transverse,v('ay')),v('fy')),eq(mul(transverse,v('az')),v('fz'))))
        text+=definition(names[3],fields('longitudinal transverse '+COMPONENTS),both(*valid('longitudinal transverse '+COMPONENTS),
            k(names[0],v('longitudinal'),v('ax'),v('fx')),k(names[0],v('transverse'),v('ay'),v('fy')),k(names[0],v('transverse'),v('az'),v('fz'))))
        relation=op('z',k(names[2],*map(v,('light speed beta restmass '+COMPONENTS).split())),
            k(names[3],*map(v,('longitudinal transverse '+COMPONENTS).split())))
        if real:relation=op('y',both(*valid(COMPONENTS)),relation)
        for variable in reversed(COMPONENTS.split()):relation=quant('f',variable,typ,relation)
        text+=definition('sepi' if real else 'sepj',fields(FACTORS),both(*valid(FACTORS),normal,relation))
    return text


MEANINGS={
    'sepa':'有理数の質量係数・加速度数値・力数値について係数×加速度＝力。零加速度・零力の一例では係数を一意に決めない。',
    'sepb':'V>0、|v|<V、正のbetaの正規化を保ち、縦係数をmu*beta^3、横係数をmu*beta^2とする有理数の式。muの符号は数学的条件として制限しない。',
    'sepc':'同じmu・betaで三成分の力を、それぞれmu*beta^3*ax、mu*beta^2*ay、mu*beta^2*azと結ぶ有理数の式。電磁場からこの式を導いたことは含めない。',
    'sepd':'一つの縦係数と、二つの横成分で共通の横係数について、三成分の係数×加速度＝力を要求する。',
    'sepe':'有効な実切断についてsepaの数値式を表す。切断の実装の同一性ではなく値の一致を使う。',
    'sepf':'sepbを実切断で表す。光速境界や負のbetaを分母を払った式だけで受け入れない。横係数はmu*betaでなくmu*beta^2である。',
    'sepg':'sepcを実切断で表し、三つの力数値と加速度数値を同じ正規化・muに結ぶ。',
    'seph':'sepdを実切断で表す。一例の等式から係数同定を補わない。',
    'sepi':'同じV・v・beta・muと二係数について、全ての有効な実切断の加速度・力の六数値でsepgとsephが同値となる係数恒等条件。実際に全ての加速度が観測されたとの主張ではない。',
    'sepj':'sepiの有理数版。有限の標本や一つの零入力の成立を、この全称条件と同一視しない。',
    'sepk':'同じ対象・出来事について、力の系への瞬間静止と、力・加速度の系と単位を選ぶ数値化規約を結ぶ。加速度は静止系K、力は共動系kという役割を保存する。',
    'sepl':'同じ数値化規約と、V・v・muおよび二係数に対する全実数の係数恒等条件を合わせた導出前提の記述。',
    'sepm':'同じ規約の下で二係数がmu*beta^3、mu*beta^2であるという結論の記述。規約を離れて質量一般を同じ値とするものではない。',
}
LIMITATIONS=[
    '力はその瞬間の共動系k、加速度は静止系Kという数値化規約を明示した。規約の採用関係は未展開であり、実際の力の測定や座標時刻の二階微分を今回構成したわけではない。',
    '係数恒等式として読む明示的な部分解釈である。加速度の全数値を実際に実現・観測することは要求しない。ばね秤、電荷と場、前段の運動方程式からの物理的導出は残る。',
    'muを数学的な入力係数として扱い、一般式では零や負の値も排除しない。低速での粒子の質量というmuの物理的な意味、単位の実現、縦横の幾何学的な基礎説明は未完。',
    '有理数の代数検査と実切断の式の構成を分ける。全実切断についての一般法則の機械的証明や、原文区間全体の意味一致を有限検査から認定しない。',
    '力や加速度の別の定義を採る場合の比較と慎重さを述べるu0259、周辺の仮定・論述は未記述のままである。',
]


def build():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));old=deepcopy(doc);doc['statements']=[]
    text=definitions()
    local={'zramatter':('a','係数の議論で追跡する同じ点状の荷電対象への参照。'),
        'zraevent':('a','力の系が対象と共動する当該瞬間の出来事への参照。'),
        'zraforceunit':('a','力数値に使う単位への参照。'),
        'zraaccelerationunit':('a','加速度数値に使う単位への参照。'),
        'zramu':(CUT,'mu：低速での粒子の質量として指定された数値。基礎的な測定説明は未完。'),
        'zralongitudinal':(CUT,'採用する数値化規約における縦方向の質量係数の候補値。'),
        'zratransverse':(CUT,'同じ規約における二つの横方向に共通する質量係数の候補値。'),
        'zramassnode':('a','u0255--u0258の数値式と二係数への導出を述べる箇所への参照。'),
        'zramassscope':('a','この力・加速度の数値化規約の下での係数導出の範囲。')}
    for name,(sort,_) in local.items():text+='r '+name+'[] '+sort+'.'
    text+='r zraconvention[a a a a a a d] c.'
    fixed=[k('zramatter'),k('zbm'),k('ra'),k('zraevent'),k('zraforceunit'),k('zraaccelerationunit'),v('context')]
    text+=definition('sepk','context d',both(k('va',k('ra')),k('va',k('zbm')),
        k('zpa',k('zramatter'),k('zbm'),k('zraevent'),v('context')),k('zraconvention',*fixed)))
    inputs=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zralongitudinal'),k('zratransverse')]
    for name,target in (('sepl','sepi'),('sepm','sepf')):
        text+=definition(name,'','b context['+both(k('sepk',v('context')),k(target,*inputs))+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+
        's[k zc[k zramassnode[] k rd[] r[k sepl[]] r[k sepm[]] k zramassscope[] k ri[]]].')['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    basis=deepcopy(json.loads((ROOT/'data/einstein-reconciled-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-mass-coefficients-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITATIONS
    lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in local.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    d=lookup['zraconvention']
    basis['primitives'].append(dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
        arguments=CONVENTION.split()+['context'],meaning_ja='指定対象・出来事で、力をforceframe・forceunit、加速度をaccelerationframe・accelerationunitの数値で扱う規約を選んだ関係。数値式の成立や実際の測定値をこの関係だけで補わない。'))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-mass-coefficients-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['sepa','sepb','sepc','sepd','sepj'],[]),(CORE,[],[len(old['statements'])])):
        selected=extract_document(doc,roots=roots,statement_indices=indices)
        stem=Path(path).stem
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n' for p,value in files.items()}


def main():
    for name,text in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==text,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
        print(name,len(text),flush=True)


if __name__=='__main__':main()
