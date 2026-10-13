"""Quadratic tagged-sum error, prefix invariant and explicit mesh choice."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,lam,quant
from scripts.compose_wave_amplitudes import params
from scripts.compose_geometric_volumes import generic_composed as volume_generic,CUT

PARENT='examples/v014/einstein-geometric-volumes.noema'
CELL='h[b] '+CUT
PARTITION='j['+CELL+']'
ZERO,ONE,TWO='n p a b','n p b b','n p c b'


def rational_definitions():
    mul=lambda a,b:k('ad',a,b)
    add=lambda a,b:k('ab',a,b)
    sub=lambda a,b:add(a,k('ac',b))
    le=lambda a,b:op('u',k('aa',b,a))
    pi,R,D,B,delta,L,H,t,total=map(v,'pi radius factor bound delta lower upper tag total'.split())
    K=k('seeg',pi,D,B)
    primitive=lambda x:k('seef',pi,R,D,x)
    text=definition('seeg',params('pi factor bound','b'),mul(TWO,mul(pi,mul(mul(D,D),B))),'b')
    text+=definition('seeh',params('pi radius factor lower upper tag','b'),
        sub(mul(sub(H,L),k('seec',pi,R,D,t)),sub(primitive(H),primitive(L))),'b')
    error=sub(total,sub(primitive(H),primitive(L)))
    budget=mul(K,mul(delta,sub(H,L)))
    text+=definition('seei',params('pi radius factor lower upper bound delta total','b'),both(
        le('n p a b',pi),k('aa',ZERO,B),k('aa',ZERO,delta),le(k('ac',B),L),le(L,H),le(H,B),
        le(k('ac',budget),error),le(error,budget)))
    text+=definition('seej',params('pi radius factor bound delta lower upper tag','b'),both(
        le(ZERO,pi),k('aa',ZERO,B),k('aa',ZERO,delta),le(k('ac',B),L),k('aa',L,H),le(H,B),
        le(L,t),le(t,H),k('aa',sub(H,L),delta)))
    text+=definition('seek','partition j[h[b] b] '+params('pi radius factor','b'),
        k('md',v('partition'),lam('x','b',k('seec',pi,R,D,v('x')))),'b')
    text+=definition('seel','partition j[h[b] b] '+params('pi radius factor lower upper bound delta','b'),both(
        le(ZERO,pi),k('aa',ZERO,B),k('aa',ZERO,delta),le(k('ac',B),L),le(H,B),
        k('mb',v('partition'),L,H),k('mc',v('partition'),delta)))
    return text


RATIONAL_MEANINGS={
    'seeg':'非負のpi、正のboundに対するK=2*pi*factor²*bound。断面多項式の区間内での変化とタグ付き和の誤差を抑える係数。',
    'seeh':'一区間のタグ付き矩形の和から、断面多項式の原始関数候補の端点差を引いた誤差。',
    'seei':'下端から現在の端までの和と原始関数の端点差との誤差が、±K*delta*(現在の端−下端)の間にあるという接頭列の不変条件。',
    'seej':'非負pi、正のbound・delta、範囲内で増加する一区間と区間内のタグ、delta未満の区間幅を要求する。',
    'seek':'既存mdに断面多項式を渡したタグ付き和。順序・区間幅・タグの妥当性はseelで別途指定する。',
    'seel':'範囲[−bound,bound]内の正方向の区間に、既存mb・mcによる接続した分割と細かさを要求する。piは非負、bound・deltaは正。',
}


def generic_composed():
    text,basis=volume_generic();basis=deepcopy(basis)
    doc=parse(text+rational_definitions())
    basis.update(version='partition-bounds-basis-v1',document='examples/v014/partition-bounds.noema')
    basis['definitions'].update(RATIONAL_MEANINGS)
    basis['unresolved']+=['有理数の断面多項式に対する誤差と有限列の帰納条件。全実切断の体の法則や積分の存在・一意性を自動的に証明したとはしない。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def definitions():
    zero,one,two=[k('bb',n) for n in (ZERO,ONE,TWO)]
    mul=lambda a,b:k('shv',a,b)
    pi,R,D,B,delta,L,H,total=map(v,'pi radius factor bound delta lower upper total'.split())
    x=v('x')
    primitive=mul(pi,k('bf',mul(mul(R,R),x),mul(k('bb','n p b d'),mul(mul(D,D),mul(x,mul(x,x))))))
    text=definition('seds',params('pi radius factor x',CUT),primitive,CUT)
    text+=definition('sedt',params('pi factor bound',CUT),mul(two,mul(pi,mul(mul(D,D),B))),CUT)
    K=k('sedt',pi,D,B)
    globals=both(*[k('ba',v(n)) for n in 'pi radius factor lower upper bound delta'.split()],k('bc',zero,pi),
        k('bg',zero,B),k('bg',zero,delta),k('bc',k('be',B),L),k('bg',L,H),k('bc',H,B))
    profile=lam('x',CUT,k('sedl',pi,R,mul(D,x)))
    value=k('sedd',v('partition'),profile)
    expected=k('bf',k('seds',pi,R,D,H),k('seds',pi,R,D,L))
    budget=mul(K,mul(delta,k('bf',H,L)))
    text+=definition('sedu','partition '+PARTITION+' '+params('pi radius factor lower upper bound delta',CUT),both(
        globals,k('sedb',v('partition'),L,H),k('sedc',v('partition'),delta),k('svw',k('bf',value,expected),budget)))
    qualifies=both(k('sedb',v('partition'),L,H),k('sedc',v('partition'),delta))
    text+=definition('sedv',params('pi radius factor lower upper bound delta',CUT),both(globals,
        quant('f','partition',PARTITION,op('y',qualifies,k('svw',k('bf',value,expected),budget)))))
    epsilon=v('epsilon')
    text+=definition('sedw',params('pi factor lower upper bound epsilon',CUT),
        mul(epsilon,k('sjd',mul(two,mul(k('bd',K,one),k('bf',H,L))))),CUT)
    chosen=k('sedw',pi,D,L,H,B,epsilon)
    chosen_args=[pi,R,D,L,H,B,chosen]
    text+=definition('sedx',params('pi radius factor lower upper bound epsilon',CUT),both(
        k('ba',epsilon),k('bg',zero,epsilon),k('sedv',*chosen_args),
        k('bg',mul(K,mul(chosen,k('bf',H,L))),epsilon)))
    return text


MEANINGS={
    'seds':'断面多項式の原始関数候補pi*(radius²*x−factor²*x³/3)を実切断で構成する。',
    'sedt':'実切断のK=2*pi*factor²*bound。入力の有効性と符号条件は利用側で要求する。',
    'sedu':'指定した実切断の区間・係数・細かさについて、妥当な一つのタグ付き分割の和と原始関数の端点差の誤差がK*delta*区間長以下である。',
    'sedv':'有効な区間・非負係数・正のboundとdeltaのもとで、全ての妥当で十分細かい有限分割についてseduの誤差評価を要求する。分割の有限標本で代用しない。分割の存在をこの全称条件だけから導かない。',
    'sedw':'正のepsilonと区間長に対して、delta=epsilon/[2*(K+1)*区間長]という細かさを構成する。K=0でも正の分母となるよう1を加える。',
    'sedx':'正のepsilonについて、sedwで構成した細かさをsedvの全分割条件へ渡し、全区間の誤差上限がepsilon未満になることを要求する。実切断全域での一般証明や分割の存在とは区別する。',
}


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-geometric-volumes-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    basis.update(version='einstein-partition-bounds-basis-v1',document='examples/v014/einstein-partition-bounds.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '有理数の任意の有限分割の和の誤差は、空の接頭列と一段の延長を多項式として検査し、有限列のfoldの意味に基づく帰納規則で接続する。これは実切断の演算法則・アルキメデス性・全実分割の存在を機械証明したものではない。',
        '積分値の候補の端点差だけでなく、細かさに比例して消える誤差を記述した。空間測度、円板面積の同値性、物理的エネルギー、同じ光の集合、全文の意味一致は未完。既存173件の著者主張を保持する。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    extracted=extract_document(doc,roots=['sedu','sedx'],statement_indices=[])
    projected=extract_basis(doc,basis,extracted,version='partition-bounds-core-basis-v1',document_path='examples/v014/partition-bounds-core.noema')
    return format_graph(extracted.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'partition-bounds'),(source_composed,'einstein-partition-bounds'),(core_composed,'partition-bounds-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored partition bounds differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
