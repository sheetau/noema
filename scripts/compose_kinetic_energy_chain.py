"""Preserve the printed kinetic-energy chain separately from its weighted variant."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,both,op,lam,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-material-mass-extension.noema'
SOURCE='examples/v014/einstein-kinetic-energy-chain.noema'
LIBRARY='examples/v014/kinetic-energy-chain.noema'
CORE='examples/v014/kinetic-energy-chain-core.noema'
READING='data/kinetic-energy-chain-reading-v1.json'
NAMES='light speed beta mass energy'


def definitions():
    text=''
    for real,name in ((False,'serb'),(True,'serc')):
        typ=CUT if real else 'b';fields=[(n,typ) for n in NAMES.split()]
        light,speed,beta,mass,energy=args(fields)
        zero=k('bb',ZERO) if real else ZERO;one=k('bb','n p b b') if real else 'n p b b'
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        sub=lambda a,b:k('bf',a,b) if real else k('ab',a,k('ac',b))
        lt=lambda a,b:k('bg' if real else 'aa',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        text+=definition(name,params(fields),both(*([k('ba',x) for x in args(fields)] if real else []),
            k('srd' if real else 'sra',light,speed,beta),lt(zero,mass),op('u',lt(speed,zero)),
            eq(energy,mul(mass,mul(mul(light,light),sub(beta,one))))))
    light,speed,mass,energy=map(v,('light','speed','mass','energy'))
    beta=k('soy',light,speed);mul=lambda a,b:k('shv',a,b)
    text+=definition('serd',params([('light',CUT),('speed',CUT)]),mul(mul(mul(beta,beta),beta),speed),CUT)
    text+=definition('sere',params([('light',CUT),('mass',CUT),('speed',CUT)]),mul(mass,k('serd',light,speed)),CUT)
    zero=k('bb',ZERO);one=k('bb','n p b b')
    fields=[(n,CUT) for n in ('light','mass','speed','energy')]
    integral=k('sede',zero,speed,lam('velocity',CUT,k('sere',light,mass,v('velocity'))),energy)
    text+=definition('serf',params(fields),both(*[k('ba',x) for x in args(fields)],k('bg',zero,light),k('bg',zero,mass),
        op('u',k('bg',speed,zero)),k('bg',speed,light),op('x',
            both(k('sca',speed,zero),k('sca',energy,zero)),both(k('bg',zero,speed),integral))))
    for name,factor in (('serg',one),('serh',mass)):
        text+=definition(name,params(fields),both(k('serc',light,speed,beta,mass,energy),k('serf',light,factor,speed,energy)))
    return text


MEANINGS={
    'serb':'正のmass、非負で光速未満のspeedと正規化betaについてenergy=mass*light^2*(beta-1)を表す有理数の式。速度零でenergy零を許す。',
    'serc':'serbの実切断版。光速境界と負のbetaを除き、質量と光速度を正とする。',
    'serd':'正の光速度とその未満の速度でbeta^3*speedを表す被積分関数。betaは既存の正の正規化soyから得る。引数が適用領域内にある条件は呼出側で課す。',
    'sere':'serdに同じmassを掛けた被積分関数。原刊の中間積分にはこのmassが印刷されていない。',
    'serf':'0から非負で光速未満のspeedまで、同じ正のmassを係数とするsereの積分がenergyとなる。正区間は既存の全分割によるsedeを使い、零区間は値零で別に定義する。',
    'serg':'原刊M0427の中間積分と最右辺を、massを掛けない積分serf(light,1,speed,energy)とsercの同時成立として保持する。原文の式を黙って補正しない。',
    'serh':'中間積分にも同じmassを掛けた候補とsercの同時成立。原刊の逐語的な式や機械的に証明済みの積分恒等式とは区別する。',
    'seri':'本文のV・v・muとWについて、原刊の中間積分と最右辺をsergで述べる部分内容。左側の仕事積分と身体・場への量の帰属は残る。',
    'serj':'同じ本文パラメータについてmassを含めたserhの候補内容を作る。著者がこの形を印刷したという帰属は加えない。',
}
LIMITS=[
    '原刊920頁と電子テキストの中間積分はいずれもbeta^3*vの積分であり、muがない。原文保存のsergとmuを含めるserhを分離する。転記訂正や原刊が訂正されたという主張はしない。',
    'M0427の中間積分と最右辺だけへの部分対応である。最初のepsilon*Xの位置による仕事積分、u0261の原点・初速零・軸上の運動・静電力・放射しない仮定とエネルギー帰属は未接続。',
    '正のmassと非負の速度に限定した数値化を使う。単位尺度は原文の式に整合する共通の規約を前提とし、異なる単位の値をそのまま代入する一般化はしない。',
    '正規化式の微分を仮定した有理数の代数関係と、全実切断の微積分法則は別である。原始関数候補から積分値への一般的な基本定理の機械的証明は残る。',
    '有限個の分割や数値積分でsedeの全分割条件を代用しない。原文の等号列の整合性、物理的導出、区間全体の意味一致をこの段階で認定しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={'zrfenergy':(CUT,'当該式のWという運動エネルギー候補値。対象・場・単位への帰属は未接続。'),
        'zrfnode':('a','u0262の中間積分と最右辺を提示する箇所。'),'zrfscope':('a','原刊の正の質量、非負で光速未満の速度という式の適用範囲。')}
    text=definitions()+''.join('r '+name+'[] '+sort+'.' for name,(sort,_) in values.items())
    for name,target in (('seri','serg'),('serj','serh')):
        text+=definition(name,'','b context['+k(target,k('tc'),k('zramu'),k('zb7'),k('zrfenergy'))+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+'s[k uh[k zrfnode[] k rd[] r[k seri[]] k zrfscope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-material-mass-extension-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-kinetic-energy-chain-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-kinetic-energy-chain-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['serb','serc','serd','sere','serf','serg','serh'],[]),(CORE,['serj'],[len(old['statements'])])):
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
