"""Present accompanying equations without making attribution a physics proof."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_referents import BINDINGS,INPUTS,ASSIGN,ELECTRIC,FRAMES
from scripts.compose_density_formula import PARTIALS
from scripts.compose_field_equations import JET,CUT
from scripts.compose_kant_discourse import discourse_basis

PARENT='examples/v014/einstein-density-referents.noema'
RELATIONS=[('assigned',ASSIGN),('electricassigned',ELECTRIC),('frames',FRAMES)]
FIXED=[('light',CUT)]+RELATIONS
CASES=[p for p in BINDINGS if p[0] not in {'context',*(n for n,_ in FIXED)}]
DISCOURSE=[('node','a'),('author','a'),('earlier','a'),('scope','a'),('context','d'),('content','i[e]')]
QUOTE='r[k senx[k tc[] k zqd[] k zqe[] k zqf[]]]'
SOURCE_ASSERTION='s[k seny[k zqb[] k rd[] k zqa[] k zqc[] k ri[] '+QUOTE+']].'
MEANINGS={
    'senw':'senuの同じ参照関係の下で、五つの等式と必要な三偏微分を満たす新電場の微分表が存在する。任意の微分表を正しいとせず、未使用の対角外や時間微分値を特定しない。',
    'senx':'与えた光速度と三つの帰属・配置関係を固定し、その文脈でsenuに当てはまる各対象と量についてsenwを要求する内容。帰属関係そのものを任意の関係として全称量化しない。著者による提示は別に記述する。',
    'seny':'著者が指定範囲内で引用した内容を提示し、別の先行箇所をこの箇所で説明するという帰属を、同じ著者・文脈と本文順序へ結ぶ。内容の評価、論理的な証明、前提の真理は含意しない。',
}
LIMITS=[
    'M0390を、その考察範囲で割り当てられた新旧の量に関する条件として読む部分解釈である。uhの範囲外の無条件の法則、全ての仮の帰属関係に成り立つ命題へ広げない。',
    'zqd・zqe・zqfは式へ用いる帰属と標準配置の関係であり、意味規約を公開するが、現実の測定や物理概念への完全な還元は未完。全称量化する対象と固定した解釈を区別する。光速度は本文の共有値tcを参照し、同じ物体の量に対して任意の光速度を要求しない。',
    '前置されたM0389の文章箇所へ談話上の説明関係を結ぶが、その箇所の全内容・仮定・導出を完成したとはしない。式を補うwobeiをこの関係として読む解釈上の限界を残す。',
    '新電場の微分表の存在と、全ての実数・場を含む内容の真偽は有限解釈器では評価しない。引用して提示する際に内容を実行しないことと、内容の意味が説明不要であることは別である。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-density-referents-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    body=quant('g','newelectricjet',JET,k('senv',*args(INPUTS)))
    text=definition('senw',params(BINDINGS),body)
    body=op('y',k('senu',*args(BINDINGS)),k('senw',*args(BINDINGS)))
    for name,sort in reversed(CASES):body=quant('f',name,sort,body)
    text+=definition('senx',params(FIXED),'b context['+body+']','e')
    text+='r ue[a a d] c.r uf[a a a d] c.'
    text+=definition('seny',params(DISCOURSE),both(op('u',op('e',v('earlier'),v('node'))),
        k('uh',v('node'),v('author'),v('content'),v('scope'),v('context')),
        k('uf',v('author'),v('earlier'),v('node'),v('context')),k('ue',v('earlier'),v('node'),v('context'))))
    text+='r zqa[] a.r zqb[] a.r zqc[] a.'
    for symbol,(_,sort) in zip(('zqd','zqe','zqf'),RELATIONS):
        # Reuse the checked function type as a first-class local relation.
        text+='r '+symbol+'[] '+sort+'.'
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+SOURCE_ASSERTION)
    basis.update(version='einstein-equation-presentation-basis-v1',document='examples/v014/einstein-equation-presentation.noema')
    basis['primitives'] += [deepcopy(p) for p in discourse_basis()['primitives'] if p['symbol'] in ('ue','uf')]
    declarations={d['name']:d for d in doc['declarations']}
    for name,meaning in (
        ('zqa','先行するM0389の場の方程式の文章箇所。位置への参照であり、その全内容の記述はこれだけでは完了しない。'),
        ('zqb','wobeiに続けてM0390の速度と密度の関係を示す文章箇所。'),
        ('zqc','§9の新旧の系を用いる電磁気の考察範囲。前提全体の真理や導出の成立は局所参照だけから認定しない。'),
        ('zqd','同じ物質・系・出来事・文脈へ規格化密度と三速度成分を割り当てる関係。値の一致だけから帰属を推定しない。'),
        ('zqe','同じ系・領域・文脈に電気側の三成分場を割り当てる関係。磁場をこの関係へ混ぜない。'),
        ('zqf','順序付きの二つの基準系を、符号付きの相対速度と文脈へ結ぶ標準配置の関係。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',basis


def generic_composed():return projected(['seny'],'accompanying-relations')
def core_composed():return projected(['senw','senx','seny'],'equation-presentation-core')
BUILDERS=((generic_composed,'accompanying-relations'),(source_composed,'einstein-equation-presentation'),(core_composed,'equation-presentation-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored presentation differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
