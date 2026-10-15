"""Separate signed transverse acceleration, equal strength and response ratios."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,both,op,ZERO
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-material-energy-extension.noema'
SOURCE='examples/v014/einstein-deflection-ratio.noema'
LIBRARY='examples/v014/deflection-ratio.noema'
CORE='examples/v014/deflection-ratio-core.noema'
READING='data/deflection-ratio-reading-v1.json'
LAW='light speed beta mass charge electric magnetic acceleration'
COMPARE='light speed beta mass charge electric magnetic electricacc magneticacc totalacc'
RESPONSE='light speed beta mass charge magnitude gain electricresponse magneticresponse'
RATIO='light speed electricresponse magneticresponse'


def definitions():
    text=''
    for real,names in ((False,('setj','setl','setn','setp','setr')),(True,('setk','setm','seto','setq','sets'))):
        typ=CUT if real else 'b';zero=k('bb',ZERO) if real else ZERO
        fields=lambda words:[(n,typ) for n in words.split()]
        valid=lambda words:[k('ba',v(n)) for n in words.split()] if real else []
        mul=lambda a,b:k('shv' if real else 'ad',a,b)
        sub=lambda a,b:k('bf',a,b) if real else k('ab',a,k('ac',b))
        lt=lambda a,b:k('bg' if real else 'aa',a,b)
        eq=lambda a,b:k('sca',a,b) if real else op('e',a,b)
        sq=lambda a:mul(a,a)
        V,s,b,m,q,Y,N,a=map(v,LAW.split())
        normal=both(k('srd' if real else 'sra',V,s,b),lt(zero,m),op('u',lt(s,zero)))
        text+=definition(names[0],params(fields(LAW)),both(*valid(LAW),normal,
            eq(mul(mul(m,b),mul(V,a)),mul(q,sub(mul(V,Y),mul(s,N))))))
        common=[V,s,b,m,q]
        text+=definition(names[1],params(fields(COMPARE)),both(
            k(names[0],*common,Y,zero,v('electricacc')),
            k(names[0],*common,zero,N,v('magneticacc')),
            k(names[0],*common,Y,N,v('totalacc'))))
        balance='light speed electric magnetic'
        text+=definition(names[2],params(fields(balance)),both(*valid(balance),lt(zero,V),op('u',lt(s,zero)),lt(s,V),
            op('u',lt(Y,zero)),op('u',lt(N,zero)),eq(mul(V,Y),mul(s,N))))
        Q,G,Ae,Am=map(v,('magnitude','gain','electricresponse','magneticresponse'))
        text+=definition(names[3],params(fields(RESPONSE)),both(*valid(RESPONSE),normal,lt(zero,Q),eq(sq(Q),sq(q)),
            lt(zero,G),lt(zero,Ae),op('u',lt(Am,zero)),
            eq(mul(mul(m,b),Ae),mul(G,Q)),eq(mul(mul(m,b),mul(V,Am)),mul(mul(G,Q),s))))
        text+=definition(names[4],params(fields(RATIO)),both(*valid(RATIO),lt(zero,V),op('u',lt(s,zero)),lt(s,V),
            lt(zero,Ae),op('u',lt(Am,zero)),eq(mul(V,Am),mul(s,Ae))))
    text+=definition('sett',params([(n,CUT) for n in ('light','electricresponse','magneticresponse')]),
        k('shv',v('light'),k('shv',v('magneticresponse'),k('sjd',v('electricresponse')))),CUT)
    return text


MEANINGS={
    'setj':'第二の運動方程式(A)の横方向成分をmu*beta*V*a=charge*(V*Y-v*N)として表す有理数の式。正のmu・V、正規化beta、0<=v<Vを保持し、電荷と場の成分の符号は固定しない。共動系の力に対するmu*beta^2という係数とは区別する。',
    'setk':'setjの実切断版。分母を払った式だけで零質量や光速境界を許容しない。',
    'setl':'同じ瞬間の速度・質量・電荷で、電場だけ、磁場だけ、両場を加えた場合の三つの符号付き加速度をsetjへ結ぶ。',
    'setm':'setlの実切断版。二つの効果が同じ強さでも、符号付き加速度が同一であるとはしない。',
    'setn':'非負の場の成分Y,Nについて、V*Y=v*Nという釣合条件。YやNやvによる除算を使わず、零速度と零の場も含む。',
    'seto':'setnの実切断版。これだけで実際の場や加速度の帰属は補わない。',
    'setp':'同じ正の応答係数gainと電荷の大きさを用い、電場・磁場の単位成分当たりの応答をそれぞれAe,Amへ結ぶ有理数のモデル。mu*beta*Ae=gain*|charge|、mu*beta*V*Am=gain*|charge|*v。',
    'setq':'setpの実切断版。二つの応答に共通の校正・幾何学的要因をgainで明示する解釈候補。原文がこの応答の定義を明記したとはしない。',
    'setr':'正のAeと非負のAmについてAm/Ae=v/Vという有理数の比。非零の分母を保持し、光速以上の速さを許容しない。',
    'sets':'setrの実切断版。Ae=0で両辺を払った等式だけを成立させることはできない。',
    'sett':'正のAeを前提にV*Am/Aeを作る速度の候補。定義域と元の速度との一致はsetsで保持する。',
    'setu':'同じ本文のV・v・mu・電荷・Y・Nに対する三つの横方向応答を、第二の運動方程式で比較する前提内容。物理的な試験配置と加速度測定の構成は未展開。',
    'setv':'u0266前半の、非負のY,NがY=N*v/Vを満たすなら二つの横方向加速度の大きさが等しいという条件文。加速度が同方向という主張ではない。',
    'setw':'M0436のAm/Ae=v/Vを、同じ本文のV・vと二つの応答値、非零の電気側の分母で述べる。装置や測定可能性をこの式だけで保証しない。',
    'setx':'同じ本文の値に、共通gainと電荷の大きさを用いるsetqを適用した応答モデルの候補。著者がこのモデルを明記したという帰属は加えない。',
    'sety':'応答モデルsetxと比の式setwを同じ値で合わせる内容構成子。異なる校正条件の二つの応答を混ぜない。',
}
LIMITS=[
    '瞬間的な横方向の運動方程式を用いる。力を共動系で測る質量係数mu*beta^2を、静止系の場に対するmu*betaへ置換する一般規則は追加しない。',
    'Ablenkbarkeitは共通の正の応答係数を持つ二つの応答として読む候補である。実際の曲率、通過時間、装置、単位、測定法の完全な定義は未展開。',
    '速度零でAm=0となる数値式は許すが、静止した粒子からこの測定法で速度を決定できると認定しない。分母Aeと電荷の大きさ、gainは正を要求する。',
    'u0266後半の任意速度についての実験的な決定可能性、u0265の列挙の予告、u0268の直接測定との照合と原文全体の意味一致は未完。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    meanings={'electric':'本文の電気側の横成分Y。','magnetic':'本文の磁気側の成分N。',
        'electricacc':'同じ瞬間の電場単独の符号付き横加速度。','magneticacc':'同じ瞬間の磁場単独の符号付き横加速度。',
        'totalacc':'同じ両場を加えた場合の符号付き横加速度。','magnitude':'同じ電荷の大きさ。零ではない応答モデルで用いる。',
        'gain':'二つの応答が共有する正の校正・幾何学的要因。','electricresponse':'原文のAeという電気側の応答値。','magneticresponse':'原文のAmという磁気側の応答値。'}
    values={'zrl'+n:(CUT,m) for n,m in meanings.items()}
    values.update(zrlbalancenode=('a','u0266の同じ強さの偏向の条件を述べる箇所。'),zrlreasonnode=('a','第二式からの帰結を述べる箇所。'),
        zrlrationode=('a','u0267の比の式を述べる箇所。'),zrlscope=('a','同じ電子の速度と場の規約で二つの応答を比較する範囲。'))
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    fixed=[k('tc'),k('zb7'),k('soy',k('tc'),k('zb7')),k('zramu'),k('zrgcharge')]
    extra+=definition('setu','','b context['+k('setm',*fixed,*[k('zrl'+n) for n in ('electric','magnetic','electricacc','magneticacc','totalacc')])+']','e')
    sq=lambda x:k('shv',x,x)
    extra+=definition('setv','','b context['+op('y',k('seto',k('tc'),k('zb7'),k('zrlelectric'),k('zrlmagnetic')),
        k('sca',sq(k('zrlelectricacc')),sq(k('zrlmagneticacc'))))+']','e')
    extra+=definition('setw','','b context['+k('sets',k('tc'),k('zb7'),k('zrlelectricresponse'),k('zrlmagneticresponse'))+']','e')
    extra+=definition('setx','','b context['+k('setq',*fixed,*[k('zrl'+n) for n in ('magnitude','gain','electricresponse','magneticresponse')])+']','e')
    extra+=definition('sety','','b context['+both('t['+k('setx')+']['+v('context')+']','t['+k('setw')+']['+v('context')+']')+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    claims=''.join('s['+k('uh',k(node),k('rd'),'r['+k(content)+']',k('zrlscope'),k('ri'))+'].' for node,content in [('zrlbalancenode','setv'),('zrlrationode','setw')])
    claims+='s['+k('zc',k('zrlreasonnode'),k('rd'),'r['+k('setu')+']','r['+k('setv')+']',k('zrlscope'),k('ri'))+'].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+claims)['statements']
    basis=json.loads((ROOT/'data/einstein-material-energy-extension-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-deflection-ratio-basis-v1',document=SOURCE);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-deflection-ratio-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:11],[]),(CORE,['sety','sett','setl','setn','setp','setr'],list(range(len(old['statements']),len(doc['statements']))))):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
