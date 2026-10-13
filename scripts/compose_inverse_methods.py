"""Keep solving a forward formula and applying its reversed rule distinct."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_field_equations import CUT, FIELD
from scripts.compose_calculation_discourse import STEPS, RULE, generic_definitions

PARENT='examples/v014/einstein-field-parity.noema'


def method_definition():
    return definition('sbs2','first '+STEPS+' second '+STEPS+' premise i[e] solved i[e] reversed i[e] allowed '+RULE,
        both(op('u',op('e',v('solved'),v('reversed'))),
            k('s2w',v('first'),v('premise'),v('solved'),v('allowed')),
            k('s2w',v('second'),v('premise'),v('reversed'),v('allowed'))))


MEANINGS={
    'sbi2':'有効で非零の第一係数と、有効な第二係数を指定する。逆数を使う条件であり、正の係数だけに限定しない。',
    'sbj2':'第一の方法として、共通係数の逆数と逆速度の電気成分変換を使い、入力の二場から元の電気成分を解いた関数を構成する。',
    'sbk2':'sbj2と同じ第一の方法による磁気成分の関数。',
    'sbl2':'第二の方法として、同じ係数関数の逆速度での値と逆速度の電気成分変換を使う。第一の係数の逆数へ先に置き換えない。',
    'sbm2':'sbl2と同じ第二の方法による磁気成分の関数。',
    'sbn2':'逆係数を用いる条件のもとで、第一係数の逆数を掛けた値と第二係数を掛けた値が、指定した同じ有効入力値で一致する。',
    'sbo2':'sbn2の一致を全ての有効な実数入力へ要求する。零の一例だけの一致とは区別する。同じ逆速度の線形変換の前後に掛かる係数写像の比較である。',
    'sbp2':'新系の二場から、第一の方法で旧系の二場を復元するという式の内容。元の領域で全六成分の一致を要求する。',
    'sbq2':'第二の方法で旧系の二場を復元するという式の内容。sbp2と同じ入力・出力・領域を使い、係数だけを逆速度で評価する。',
    'sbr2':'正の光速・許容速度と同じ係数関数のもとで、二方法の係数写像が任意の入力で一致するという内容。',
    'sbs2':'同じ前提の記述から、異なる二つの結論記述へつながる二つの非空の計算手順を要求する。記述の相違と、結果の意味的な一致を分ける。',
    'sbt2':'先行する共通係数付きの式からsbp2・sbq2へ至る二つの計算手順の記述。許容変形を同じ文脈で評価し、引用内容を真として実行しない。',
    'sbu2':'二方法の手順がつながり、先行する変換式と二方法の係数写像の一致を採用したという、逆係数の積1への前提。',
}


def generic_composed():
    from scripts.compose_calculation_discourse import MEANINGS as previous
    doc=parse('n:r aa[b b] c.r ab[b b] b.'+generic_definitions()+method_definition())
    basis=dict(version='inverse-methods-basis-v1',document='examples/v014/inverse-methods.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['left','right'],meaning_ja='有理数の順序。' if d['name']=='aa' else '有理数の加算。') for d in doc['declarations'] if d['kind']=='primitive'],
        definitions=previous|{'sbs2':MEANINGS['sbs2']},unresolved=['手順の接続は指定した許容変形関係についての条件であり、数学的な健全性や実行済みを保証しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact');zero=k('bb','n p a b');one=k('bb','n p b b')
    text+=definition('sbi2','first '+CUT+' second '+CUT,both(k('ba',v('first')),op('u',k('sca',v('first'),zero)),k('ba',v('second'))))
    V,s=v('light'),v('speed');opposite=k('bf',zero,s)
    args='light '+CUT+' speed '+CUT+' factor '+CUT+' electric '+FIELD+' magnetic '+FIELD
    for name,operation in (('sbj2','s6k'),('sbk2','s6l')):
        text+=definition(name,args,k('sal2',k('sjt',v('factor')),k(operation,V,opposite,v('electric'),v('magnetic'))),FIELD)
    args='light '+CUT+' speed '+CUT+' factor h['+CUT+'] '+CUT+' electric '+FIELD+' magnetic '+FIELD
    for name,operation in (('sbl2','s6k'),('sbm2','s6l')):
        text+=definition(name,args,k('sal2',app(v('factor'),opposite),k(operation,V,opposite,v('electric'),v('magnetic'))),FIELD)
    text+=definition('sbn2','first '+CUT+' second '+CUT+' input '+CUT,both(k('sbi2',v('first'),v('second')),k('ba',v('input')),
        k('sca',k('shv',k('sjt',v('first')),v('input')),k('shv',v('second'),v('input')))))
    text+=definition('sbo2','first '+CUT+' second '+CUT,both(k('sbi2',v('first'),v('second')),
        q('f','input',CUT,op('y',k('ba',v('input')),k('sbn2',v('first'),v('second'),v('input'))))))
    V,s=k('tc'),k('zb7');a=app(k('znz'),s);b=app(k('znz'),k('bf',zero,s));oldE,oldH=k('znl'),k('znm');newE,newH=k('znr'),k('zns')
    binding=both(k('znn',k('ra'),oldE,oldH,k('znk'),v('context')),k('znn',k('zbm'),newE,newH,k('znt'),v('context')),
        k('saj2',k('s6m',V,s,k('znk')),k('znt')))
    for name,e,h,factor in (('sbp2','sbj2','sbk2',a),('sbq2','sbl2','sbm2',k('znz'))):
        text+=definition(name,'','b context['+both(k('s45',V,s),k('sbi2',a,b),binding,
            k('sai2',one,oldE,oldH,k(e,V,s,factor,newE,newH),k(h,V,s,factor,newE,newH),k('znk')))+']','e')
    text+=definition('sbr2','','b context['+both(k('s45',V,s),k('sbo2',a,b))+']','e')
    text+=method_definition()+'r zoc[] '+STEPS+'.r zod[] '+STEPS+'.r zoe[] a.'
    text+=definition('sbt2','','b context['+k('sbs2',k('zoc'),k('zod'),'r[k sak2[]]','r[k sbp2[]]','r[k sbq2[]]',
        'i[before i[e] after i[e]][k zla[v before v after v context]]')+']','e')
    text+=definition('sbu2','','b context['+both(op('t',k('sbt2'),v('context')),op('t',k('sak2'),v('context')),op('t',k('sbr2'),v('context')))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k zc[k zoe[] k rd[] r[k sbu2[]] r[k saq2[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-parity-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-inverse-methods-basis-v1',document='examples/v014/einstein-inverse-methods.noema')
    for name,meaning in (('zoc','第一の方法の手順列。先行する式を解いた記述へ至る有限の前後対を与える。実行ログや固定手順数を意味しない。'),('zod','第二の方法の手順列。先行する式を逆速度で適用した記述へ至る有限の前後対を与える。'),('zoe','u0165で二方法を比較し、M0311を帰結として提示する箇所。')):
        d=next(d for d in doc['declarations'] if d['name']==name);basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0165の二方法と比較からの帰結を部分記述した。実際に手順を実行したという主張へ変えず、非空の手順の接続と式の内容・一致を分ける。',
        '二方法の共通する逆速度変換を保持し、残る係数写像の全入力での一致をsbo2とする。特定の零の場だけの一致から係数積1を結論しない。',
        '第二の方法は同じ変換の規則を速度-vへ適用するという著者の操作として記述する。単独の一速度で成立した等式から一般規則を機械的に導出したとはしない。許容手順関係zlaの健全性と一般の実関数での同値変形の証明は未完。',
        '条件の下で二式が同じでなければならないという要求を比較前提に明示した。修辞的・方法論的な必要性の語義全体、力・単位・真空と全文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'inverse-methods'),(composed,'einstein-inverse-methods')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored inverse methods differ: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Two inverse constructions and their comparison composed')


if __name__=='__main__':main()
