"""Compare force/acceleration evaluation conventions in selected alternatives."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_force_mass_units import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_field_equations import ROLES

PARENT='examples/v014/einstein-force-mass-units.noema'
SOURCE='examples/v014/einstein-convention-comparison.noema'
LIBRARY='examples/v014/convention-comparison.noema'
CORE='examples/v014/convention-comparison-core.noema'
SCOPE='h[a] c';VALUE='h[a] '+CUT;VECTOR='h[a] '+VALUE;COEFFICIENT='h[a] '+CUT
CANDIDATES='h[e d d] c'
SINGLE=[('cases',SCOPE),('force',VALUE),('acceleration',VALUE),('coefficient',CUT)]
COMPARE=[('cases',SCOPE),('axes',SCOPE)]+[(prefix+n,sort) for prefix in ('base','other') for n,sort in (('force',VECTOR),('acceleration',VECTOR),('coefficient',COEFFICIENT))]
HYPOTHETICAL=COMPARE[:5]+[('otherforce','h[d] '+VECTOR),('otheracceleration','h[d] '+VECTOR),('othercoefficient','h[d] '+COEFFICIENT),('candidates',CANDIDATES)]
ROOTS=['seqe','seqf','seqg','seqh','seqi','seqj']
READING='data/convention-comparison-reading-v1.json'


def definitions():
    case=v('case');a=app(v('acceleration'),case);force=app(v('force'),case)
    text=definition('seqe',params(SINGLE),both(k('ba',v('coefficient')),
        quant('g','case','a',both(app(v('cases'),case),k('ba',a),op('u',k('sca',a,k('bb','n p a b'))))),
        quant('f','case','a',op('y',app(v('cases'),case),both(k('ba',force),k('ba',a),k('sca',k('shv',v('coefficient'),a),force))))))
    pair=[('cases',SCOPE)]+[(prefix+n,VALUE) for prefix in ('base','other') for n in ('force','acceleration')]
    differences=[op('u',k('sca',app(v('base'+n),case),app(v('other'+n),case))) for n in ('force','acceleration')]
    text+=definition('seqf',params(pair),quant('g','case','a',both(app(v('cases'),case),op('x',*differences))))
    axis=v('axis');fits=[]
    for prefix in ('base','other'):
        fits.append(k('seqe',v('cases'),app(v(prefix+'force'),axis),app(v(prefix+'acceleration'),axis),app(v(prefix+'coefficient'),axis)))
    changed=k('seqf',v('cases'),*(app(v(prefix+n),axis) for prefix in ('base','other') for n in ('force','acceleration')))
    text+=definition('seqg',params(COMPARE),both(
        quant('f','axis','a',op('y',app(v('axes'),axis),both(*fits))),
        quant('g','axis','a',both(app(v('axes'),axis),changed,
            op('u',k('sca',app(v('basecoefficient'),axis),app(v('othercoefficient'),axis)))))))
    scene=v('scene');values=args(HYPOTHETICAL[:5])+[app(v('other'+n),scene) for n in ('force','acceleration','coefficient')]
    content='b scene['+k('seqg',*values)+']'
    text+=definition('seqh',params(HYPOTHETICAL+[('context','d')]),k('s5k',content,v('context'),v('candidates')))
    text+=definition('seqi',params(HYPOTHETICAL),'b context['+k('seqh',*args(HYPOTHETICAL),v('context'))+']','e')
    return text


MEANINGS={
    'seqe':'指定した全評価事例で係数×加速度＝力となり、非零の加速度を持つ事例が少なくとも一つある。全て零の入力だけでは係数の決定可能性を認めない。係数は固定された対象・速度・方向などの比較条件の範囲内で一定として指定する。',
    'seqf':'同じ比較領域の少なくとも一つの事例で、力か加速度の評価値が異なる。定義の綴りや参照名の違いだけから数値的な差を補わない。',
    'seqg':'同じ事例領域・方向集合で両規約の係数がseqeを満たし、少なくとも一方向で評価値と係数が異なる。全方向で差があることは要求せず、空の方向集合は認めない。',
    'seqh':'比較内容と現在の文脈に選定した非空の仮定状況全てでseqgが成り立つ。既存s5kを使い、現実の成立、未選定の全ての別定義、単位換算の有無を自動推論しない。',
    'seqi':'固定した事例・方向・元の数値評価と、状況ごとの別評価・係数・候補選定から、seqhの仮定的比較内容を作る。',
    'seqj':'u0259前半について、前段の縦横係数を元の値として別の力・加速度規約を採る仮定状況の比較を述べる部分読解。具体的な別定義と候補の選び方は入力であり、理論比較への注意をまだ含めない。',
}
LIMITS=[
    'ここで比較する関数は、同じ対象・速度条件・方向・物理事例を共通の固定単位で評価する規約として指定する。領域の完全性、条件の固定と実際の力・加速度定義への適合はなお解釈入力に依存する。',
    '別定義を採る仮定状況を選ぶ関係を明示した。近さ・通常性・反実条件一般の理論や、作者が考えた全ての別定義の同定は未完。都合の良い状況だけを選んで原文との意味一致を認定しない。',
    '力と加速度を比例して変えれば係数は同じになることがある。原文を「どのような別定義でも必ず全ての質量数値が変わる」という無制限の命題に強めない。',
    '評価値に差のない同義的な別表現と、未選定の仮定状況を今回の比較から区別する。単位の変更は前段の換算で処理し、物理的定義の変更と同一視しない。',
    'u0259冒頭のNatürlichの自明性の含み、後半の理論比較と非常に慎重に進めるべきという注意・程度・推論は未記述。区間全体の意味一致は認定しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    symbols={'zrbcases':(SCOPE,'比較条件を固定した同じ物理事例の完全な評価領域。既に観測した事例だけの一覧とはしない。'),
        'zrbforce':(VECTOR,'元の力の評価規約。方向ごとに同じ事例を共通の固定単位で評価する関数。'),
        'zrbacceleration':(VECTOR,'元の加速度の評価規約。方向と事例を元の力と共有し、比較中は単位を固定する。'),
        'zrbalternateforce':('h[d] '+VECTOR,'仮定状況ごとに別の力の定義を採る場合の評価規約。'),
        'zrbalternateacceleration':('h[d] '+VECTOR,'同じ仮定状況の別の加速度の評価規約。'),
        'zrbalternatemass':('h[d] '+COEFFICIENT,'仮定状況・方向ごとに得られる質量係数の候補値。'),
        'zrbcandidates':(CANDIDATES,'比較内容と現在の文脈から、別の定義を採る場合として関連する仮定状況を選ぶ関係。現在が選ばれるとは限らず、選択理由は未展開。'),
        'zrbnode':('a','u0259前半の別の定義なら別の数値を得ると述べる箇所。'),
        'zrbscope':('a','同じ対象と条件を保ち、力と加速度の定義を変える仮定的な比較の範囲。')}
    text=definitions()+''.join('r '+name+'[] '+sort+'.' for name,(sort,_) in symbols.items() if name!='zrbcandidates')
    text+='r zrbcandidates[e d d] c.'
    axes='i[axis a]['+op('x',op('e',v('axis'),k(ROLES[0])),op('x',op('e',v('axis'),k(ROLES[1])),op('e',v('axis'),k(ROLES[2]))))+']'
    coefficient='i[axis a]['+k('szi',op('e',v('axis'),k(ROLES[0])),k('zralongitudinal'),k('zratransverse'))+']'
    text+=definition('seqj','',k('seqi',k('zrbcases'),axes,k('zrbforce'),k('zrbacceleration'),coefficient,
        k('zrbalternateforce'),k('zrbalternateacceleration'),k('zrbalternatemass'),'p zrbcandidates'),'e')
    doc=parse(format_graph(doc,'compact')+text)
    addition=parse(format_graph(doc,'compact')+'s[k uh[k zrbnode[] k rd[] r[k seqj[]] k zrbscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+addition
    basis=json.loads((ROOT/'data/einstein-force-mass-units-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-convention-comparison-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in symbols.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],
            arguments=['content','context','candidate'] if name=='zrbcandidates' else [],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-convention-comparison-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,ROOTS[:5],[]),(CORE,[],[len(old['statements'])])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
