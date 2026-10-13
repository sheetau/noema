"""Represent available alternative derivations and scoped necessity."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_calculation_discourse import STEPS, STEP, LEFT, RIGHT, TRUE, FALSE, generic_definitions as calculation_definitions

AVAILABLE='h[a a d] c'
PROGRAM='h[a d] '+STEPS
RULES='h[i[e] i[e] d] c'
CANDIDATES='h[e d d] c'


def definitions():
    current=v('step');before=app(current,LEFT);after=app(current,RIGHT)
    contains=op('x',v('found'),both(op('e',before,v('before')),op('e',after,v('after'))))
    text=definition('s5h','steps '+STEPS+' before i[e] after i[e]',
        'q[v steps]['+FALSE+'][i[found c step '+STEP+']['+contains+']]')
    who,method,stage,premise,conclusion=map(v,('who','method','stage','premise','conclusion'))
    steps=app(v('program'),method,stage)
    allowed='i[before i[e] after i[e]]['+app(v('rules'),v('before'),v('after'),stage)+']'
    args='who a method a stage d premise i[e] conclusion i[e] available '+AVAILABLE+' program '+PROGRAM+' rules '+RULES
    text+=definition('s5i',args,both(app(v('available'),who,method,stage),k('s2w',steps,premise,conclusion,allowed)))
    args='who a previous a stage d oldpremise i[e] premise i[e] conclusion i[e] before i[e] after i[e] available '+AVAILABLE+' program '+PROGRAM+' rules '+RULES
    previous=app(v('program'),v('previous'),stage)
    alternative=q('g','method','a',both(op('u',op('e',method,v('previous'))),
        k('s5i',who,method,stage,premise,conclusion,v('available'),v('program'),v('rules')),
        k('s5h',steps,v('before'),v('after'))))
    text+=definition('s5j',args,both(k('s2w',previous,v('oldpremise'),conclusion,allowed),alternative))
    subject,context,scene=map(v,('subject','context','scene'));selected=app(v('candidates'),subject,context,scene)
    text+=definition('s5k','subject e context d candidates '+CANDIDATES,
        both(q('g','scene','d',selected),q('f','scene','d',op('y',selected,op('t',subject,scene)))))
    text+=definition('s5l','subject e context d candidates '+CANDIDATES,
        both(k('s5k',subject,context,v('candidates')),op('t',subject,context)))
    return text


MEANINGS={
    's5h':'非空とは限らない有限手順列に、指定した前後の記述を持つ一手が出現する。等しい真偽の別記述を代用せず、出現の順序も反転しない。',
    's5i':'同じ主体・方法・段階について方法が利用可能であり、その段階の同じ方法の手順が指定前提から指定結論まで許容規則でつながる。実際の実行、内容の真理、規則の健全性は要求しない。',
    's5j':'以前の方法がその前提から同じ結論につながり、それとは異なる利用可能な方法が別に指定した前提から同じ結論へつながって必要な一手を含む。二つの方法・手順・前提を混ぜない。前提の相互含意や著者の実行履歴は主張しない。',
    's5k':'内容と文脈について指定された候補状況が非空で、その全候補で同じ内容が成立する。現在状況の真理や、あらゆる理論での論理的必然性とは区別する。',
    's5l':'s5kに加えて同じ内容が現在状況でも成立する。候補の全称条件だけで現実の成立を補うこととの違いを明示する比較用の関係。',
}


def generic_composed():
    source=parse('n:r aa[b b] c.r ab[b b] b.'+calculation_definitions())
    source['declarations']=[d for d in source['declarations'] if d['name']=='s2w']
    doc=parse(format_graph(source,'compact')+definitions())
    from scripts.compose_calculation_discourse import MEANINGS as CHAIN_MEANINGS
    basis=dict(version='derivation-modalities-basis-v1',document='examples/v014/derivation-modalities.noema',
        primitives=[],definitions={'s2w':CHAIN_MEANINGS['s2w']}|MEANINGS,
        unresolved=['利用可能性、手順の割当、許容規則、候補の選定は引数で指定する。一般的な能力、証明の健全性、反実条件文全般の語義を完成したものではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/'examples/v014/einstein-transform-group.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()
    text+='r zlv[] a.r zlw[a a d] c.r zlx[a d] '+STEPS+'.r zly[] d.r zlz[e d d] c.r zm2[] a.r zm3[] a.r zm4[d d] c.\n'
    text+=definition('s5m','','b context['+both(k('zm4',k('zly'),v('context')),k('s5j',k('rd'),k('zlv'),k('zly'),
        'r[k s3c[]]','r[k s4s[]]','r[k s3m[]]','r[k s4s[]]','r[k s4r[]]','p zlw','p zlx','p zla'))+']','e')
    text+=definition('s5n','','b context['+k('s5k',k('s5f'),v('context'),'p zlz')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zm2[] k rd[] r[k s5m[]] k zlq[] k ri[]]].
s[k uh[k zm3[] k rd[] r[k s5n[]] k zlq[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/transform-group-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-derivation-modalities-basis-v1',document='examples/v014/einstein-derivation-modalities.noema')
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zlv',[],'速度合成式を前段の運動と計算から得る既出の方法への参照。計算箇所の識別子と実行済みの行為を同一視しない。'),
        ('zlw',['actor','method','stage'],'指定主体がその段階で指定方法を利用できるという関係。実行済み、成功済み、心理的な容易さを含意しない。'),
        ('zlx',['method','stage'],'指定方法をその段階で用いるときの有限手順列。前後の記述対で与える。実際の実行ログや原文に列挙された途中式とは限らない。'),
        ('zly',[],'二つの変換による方法も選べたと振り返る導出段階。現在の発話状況と区別し、原文にない日時は補わない。'),
        ('zlz',['subject','context','candidate'],'数学的な内容を、この議論の条件に沿って評価するときに採用する候補状況。義務への違反の可否や世界全体の可能性とは同一視しない。候補を選ぶ根拠の構成は未完。'),
        ('zm2',[],'同方向の場合の式を二つの変換からも得られたと振り返るu0147の箇所。'),
        ('zm3',[],'群をなすことについて、そうでなければならないと挿入して述べるu0149の箇所。'),
        ('zm4',['earlier','later'],'第一の状況が第二の状況より時間的に前であるという厳密な先後関係。同時や関係の未指定を以前と扱わず、具体的な日時は補わない。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        's5m':'現在状況より前の導出段階で、既出の運動・計算に基づく方法とは異なり、二変換から一変換を得るs4s→s4rの一手を含む利用可能な手順が、同方向の条件付き合成式s3mへ至り得たという部分読解。以前の方法も同じs3mを結論とする。',
        's5n':'同じ群の記述s5fが、この議論で採用する非空の全候補において成立するという必要性の部分読解。主張自体を命令や義務へ置き換えない。'})
    basis['unresolved'] += [
        'u0147第一文とu0149の挿入句の部分記述。hätten…könnenは先の段階で利用可能だった別の導出として読む。実際に採用しなかったという含意や反実条件文一般の意味は確定しない。',
        '同方向の式は既存の条件付き内容s3mで指す。前段の方法の途中式と、第三系の変換から同じ物理的な速さの式へ至る手順はzlx・zlaで指定する規約であり、本文の逐語的な手順や機械的に証明済みの経路とは扱わない。',
        'wie dies sein mußを、この議論の条件に沿った候補に関する必要性として読む。論理的必然性、方法上の要請、修辞的な当然さの全てを同一化せず、唯一の歴史的語義とは主張しない。',
        '新しい基本関係は方法の利用・手順割当・候補選定を表す引数の具体化である。それらを認知・行為・証拠から構成する説明、原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'derivation-modalities'),(composed,'einstein-derivation-modalities')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored derivation modalities differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Alternative derivations and nonempty scoped necessity composed')


if __name__=='__main__':main()
