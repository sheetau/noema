"""Connect signed potential drops, oriented field integrals and kinetic energy."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-experimental-comparison.noema'
SOURCE='examples/v014/einstein-potential-speed.noema'
LIBRARY='examples/v014/potential-speed.noema'
CORE='examples/v014/potential-speed-core.noema'
READING='data/potential-speed-reading-v1.json'
SCALAR='h['+CUT+'] '+CUT
DOMAIN='h['+CUT+'] c'
NUMERIC='light speed beta mass charge drop'
BOUNDS=[(n,CUT) for n in ('lower','upper')]+[('profile',SCALAR),('drop',CUT)]
POTENTIAL=[('domain',DOMAIN),('potential',SCALAR),('profile',SCALAR)]


def definitions():
    text=''
    for real,name in ((False,'seuq'),(True,'seur')):
        fields=[(n,CUT if real else 'b') for n in NUMERIC.split()]
        light,speed,beta,mass,charge,drop=args(fields)
        zero=k('bb',ZERO) if real else ZERO
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        product=k('shv' if real else 'ad',charge,drop)
        text+=definition(name,params(fields),both(*([k('ba',charge),k('ba',drop)] if real else []),
            op('u',eq(charge,zero)),k('serc' if real else 'serb',light,speed,beta,mass,product)))
    lower,upper,profile,drop=args(BOUNDS);one=k('bb','n p b b')
    text+=definition('seus',params(BOUNDS),k('sero',lower,upper,one,drop,profile))
    charge,work=v('charge'),v('work')
    text+=definition('seut',params(BOUNDS+[('charge',CUT),('work',CUT)]),both(
        k('seus',*args(BOUNDS)),k('sero',lower,upper,charge,work,profile),k('sca',work,k('shv',charge,drop))))
    fields=[(n,CUT) for n in ('initial','final','drop')]
    text+=definition('seuu',params(fields),both(*[k('ba',x) for x in args(fields)],k('sca',v('drop'),k('bf',v('initial'),v('final')))))
    domain,potential,profile=args(POTENTIAL);x,y=v('x'),v('y')
    # Values on the whole declared domain, not a few sampled endpoints.
    text+=definition('seuv',params(POTENTIAL),both(
        quant('f','x',CUT,op('y',app(domain,x),both(k('ba',x),k('ba',app(potential,x)),k('ba',app(profile,x))))),
        quant('f','x',CUT,quant('f','y',CUT,op('y',both(app(domain,x),app(domain,y)),
            k('seus',x,y,profile,k('bf',app(potential,x),app(potential,y))))))))
    text+=definition('seuw',params(POTENTIAL+[(n,CUT) for n in ('lower','upper','drop')]),both(
        app(domain,lower),app(domain,upper),k('seuv',*args(POTENTIAL)),
        k('seuu',app(potential,lower),app(potential,upper),drop)))
    return text


MEANINGS={
    'seuq':'非零の符号付き電荷と電位降下の積が、同じ正の質量・光速度、非負で光速未満の速度の運動エネルギーになる有理数の関係。電荷の絶対値へ置き換えない。',
    'seur':'seuqの実切断版。原文のmu/epsilonを、epsilon非零とepsilon*drop=mu*V^2*(beta-1)で表す。',
    'seus':'向き付きの一次元の場の積分を電位降下dropとする。既存seroの電荷を1として使い、経路の上下端を明示する。',
    'seut':'同じ上下端・場の積分から、単位電荷当たりのdropと電荷chargeの仕事workを結び、work=charge*dropも要求する。積分の線形性を機械的に証明したとはしない。',
    'seuu':'電位の初期値から最終値を引いた符号付きの降下。両端値が同じだけ変化しても差は変わらない。',
    'seuv':'指定領域の全ての二点について、電位値の差が同じ場の向き付き積分となる一次元の静的な電位関数。各点で値が有効な実切断であることも要求する。',
    'seuw':'seuvの領域内の二点に、同じ電位関数から得る降下を結ぶ。領域外の端点を認めない。',
    'seux':'本文の同じ静電場・交換過程・系K・開始と終了・電位単位・文脈にPを帰属させ、原点から既存終点までのXの積分へ結ぶ。',
    'seuy':'本文の同じV・v・mu・epsilon・Pをseurへ結ぶ数値式の内容。',
    'seuz':'M0438のP、場の積分、速度の式をseuxとseuyの同時成立として述べる内容。',
    'seva':'同じ仕事・エネルギー収支・初期零・無放射、非零電荷、運動エネルギー式と場の積分の線形性を明示した導出候補の前提。著者がこの全前提を逐語的に列挙したとはしない。',
}
LIMITS=[
    '原文の積分には上下端が印刷されていない。前段の初期静止・原点からの軸上運動に接続する読みを採り、その両端を明示する。任意の初期速度への無条件の公式ではない。',
    '電位差は初期電位から最終電位を引いた降下として符号を定める。電子の電荷の符号を固定せず、電荷が負なら加速に対応する降下も負になる。',
    '全領域での電位関数seuvは一般定義であり、本文の局所積分からその存在まで導かない。空領域では全称条件が空虚に成立するが、seuwは二つの端点の所属を要求する。',
    '電荷、電位、場、長さ、エネルギーの数値は積と積分が整合する共通の単位規約を前提とする。単位の実現・校正、三次元の経路独立性、時間変動する場への拡張は未完。',
    '全実切断の積分の線形性と基本定理の機械的証明、静電場と電荷の物理的な基礎説明、原文全体の意味一致は未完。原文のM0427にある中間積分の質量欠落を、この新しい式で訂正したとは扱わない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={
        'zrndrop':(CUT,'u0269・M0438の符号付き電位降下P。'),
        'zrnunit':('a','同じPの単位。既存の電荷とエネルギーの単位に積が整合する規約を前提とする。'),
        'zrnassigned':('h[a a a a a a '+CUT+' d] c','交換過程・場・基準系・開始・終了・電位単位・降下値・文脈への電位降下の帰属。'),
        'zrnclaimnode':('a','M0438の式の提示箇所。'),
        'zrnreasonnode':('a','u0269の運動エネルギーの導出から式へ進む理由の接続。'),
        'zrnscope':('a','u0269の初期静止・静電場からの加速と非零電荷の式の適用範囲。'),
    }
    text=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    binding=app(k('zrnassigned'),*[k(n) for n in ('zrgepisode','zrgfield','ra','zrgstart','zraevent','zrnunit','zrndrop')],v('context'))
    bounds=[k('bb',ZERO),k('zrgposition'),k('zrgprofile'),k('zrndrop')]
    numeric=[k(n) for n in ('tc','zb7')]+[k('soy',k('tc'),k('zb7'))]+[k(n) for n in ('zramu','zrgcharge','zrndrop')]
    content=lambda n:'t['+k(n)+']['+v('context')+']'
    formulas={
        'seux':both(binding,k('seus',*bounds)),
        'seuy':k('seur',*numeric),
        'seuz':both(content('seux'),content('seuy')),
        'seva':both(binding,content('serq'),content('sert'),
            op('u',k('sca',k('zrgcharge'),k('bb',ZERO))),
            k('serc',*numeric[:4],k('zrfenergy')),
            k('seut',*bounds,k('zrgcharge'),k('zrgwithdrawn'))),
    }
    for n,formula in formulas.items():text+=definition(n,'','b context['+formula+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    statements='s[k uh[k zrnclaimnode[] k rd[] r[k seuz[]] k zrnscope[] k ri[]]].s[k zc[k zrnreasonnode[] k rd[] r[k seva[]] r[k seuz[]] k zrnscope[] k ri[]]].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+statements)['statements']
    basis=json.loads((ROOT/'data/einstein-experimental-comparison-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-potential-speed-basis-v1',document=SOURCE);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for n,(_,meaning) in values.items():
        d=lookup[n];basis['primitives'].append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-potential-speed-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:7],[]),(CORE,['seuq','seuu','seuw'],list(range(len(old['statements']),len(doc['statements']))))):
        selection=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selection.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selection,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
