"""Express the nonzero magnetic probe and its signed response separately."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, POINT, ROLES
from scripts.compose_field_transform import rational_definitions

PARENT='examples/v014/einstein-field-scale-inverse.noema'


def rational():
    text=definition('saw2','factor b beta b ratio b magnetic b',k('ad',v('factor'),k('s6b',v('beta'),v('ratio'),'n p a b',v('magnetic'))),'b')
    zero='n p a b';a,b=v('first'),v('second')
    signs=op('x',both(k('aa',a,zero),k('aa',zero,b)),both(k('aa',b,zero),k('aa',zero,a)))
    return text+definition('saz2','first b second b',both(signs,op('e',k('ad',a,a),k('ad',b,b))))


MEANINGS={
    'saw2':'他の五成分が零の場合のY′=-factor*β*ratio*Nを有理数で構成する。',
    'saz2':'二つの有理数が厳密に反対の符号を持ち、絶対値が等しいことを、符号条件と平方の等値で表す。零同士は符号反転の証拠としない。',
    'sba2':'有効な実数二つが厳密に反対の符号を持ち、絶対値が等しい条件。大きさの不変と符号の反転を両方要求する。',
    'sbb2':'実数の共通係数・β・速度比・磁気成分からY′=-factor*β*ratio*Nを構成する。',
    'sbc2':'V>0、|v|<V、v≠0、有効で非零のNを要求する非自明な比較条件。',
    'sbd2':'同じNとVを保持し、同じ係数関数をvと-vに適用した二つのY′にsba2を要求する。βもそれぞれの速度から計算する。',
    'sbe2':'静止系へ割り当てた同じ場・領域内の同じ有効な点でX=Y=Z=L=M=0かつN≠0とする比較用の条件。零でない許容速度を指定する。',
    'sbf2':'sbe2の点における同じNを使い、速度を反転したときにY′の大きさが変わらず符号が反転するという応答条件。',
    'sbg2':'比較用の条件と先行する逆係数の積1を採用した場合に応答条件が成立するという著者の例示的な主張。物理的な対称性自体を定義済みとは扱わない。',
    'sbh2':'比較用の条件、逆係数の積1、符号・大きさの応答条件を同じ文脈で採用する、係数の偶性への前提。',
}


def generic_composed():
    doc=parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'+rational_definitions()+rational())
    from scripts.compose_field_transform import MEANINGS as previous
    labels={'aa':'有理数の厳密順序。','ab':'有理数の加算。','ac':'有理数の加法逆元。','ad':'有理数の乗算。'}
    basis=dict(version='field-parity-basis-v1',document='examples/v014/field-parity.noema',
        primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['value'] if d['name']=='ac' else ['left','right'],meaning_ja=labels[d['name']]) for d in doc['declarations'] if d['kind']=='primitive'],
        definitions={name:(previous|MEANINGS)[name] for name in ('s6b','s6c','saw2','saz2')},
        unresolved=['実際の物理系がこの応答の対称性を持つことを、算術定義だけから認定しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational();zero=k('bb','n p a b');a,b=v('first'),v('second')
    signs=op('x',both(k('bg',a,zero),k('bg',zero,b)),both(k('bg',b,zero),k('bg',zero,a)))
    text+=definition('sba2','first '+CUT+' second '+CUT,both(k('ba',a),k('ba',b),signs,k('sca',k('shu',a),k('shu',b))))
    text+=definition('sbb2','factor '+CUT+' beta '+CUT+' ratio '+CUT+' magnetic '+CUT,k('shv',v('factor'),k('s6d',v('beta'),v('ratio'),zero,v('magnetic'))),CUT)
    V,s,N=v('light'),v('speed'),v('magnetic');opposite=k('bf',zero,s)
    args='light '+CUT+' speed '+CUT+' magnetic '+CUT
    text+=definition('sbc2',args,both(k('s45',V,s),op('u',k('sca',s,zero)),k('ba',N),op('u',k('sca',N,zero))))
    response=lambda speed:k('sbb2',app(v('factor'),speed),k('soy',V,speed),k('shv',speed,k('sjd',V)),N)
    text+=definition('sbd2',args+' factor h['+CUT+'] '+CUT,both(k('sbc2',V,s,N),k('ba',app(v('factor'),s)),k('ba',app(v('factor'),opposite)),k('sba2',response(s),response(opposite))))
    text+='r zn7[] '+POINT+'.r zoa[] a.r zob[] a.'
    point=k('zn7');coords=[app(point,k(role)) for role in ROLES]
    component=lambda field,role:app(app(k(field),k(role)),*coords)
    N=component('znm','yp');V,s=k('tc'),k('zb7')
    zeros=[component('znl',role) for role in ROLES[:3]]+[component('znm',role) for role in ROLES[:2]]
    probe=both(k('znn',k('ra'),k('znl'),k('znm'),k('znk'),v('context')),k('shn',k('shx'),point,'p ba'),app(k('znk'),*coords),
        *(both(k('ba',value),k('sca',value,zero)) for value in zeros),k('sbc2',V,s,N))
    text+=definition('sbe2','','b context['+probe+']','e')
    text+=definition('sbf2','','b context['+k('sbd2',V,s,N,k('znz'))+']','e')
    accepted=both(op('t',k('sbe2'),v('context')),op('t',k('saq2'),v('context')))
    text+=definition('sbg2','','b context['+op('y',accepted,op('t',k('sbf2'),v('context')))+']','e')
    text+=definition('sbh2','','b context['+both(accepted,op('t',k('sbf2'),v('context')))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'s[k uh[k zoa[] k rd[] r[k sbg2[]] k zno[] k ri[]]].s[k zc[k zob[] k rd[] r[k sbh2[]] r[k sar2[]] k zno[] k ri[]]].')
    basis=deepcopy(json.loads((ROOT/'data/einstein-field-scale-inverse-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-parity-basis-v1',document='examples/v014/einstein-field-parity.noema')
    for name,meaning in (('zn7','脚注で比較する旧系の場の評価点への参照。同じ出来事の成分を保って速度の符号だけを変える。'),('zoa','脚注u0282の例示的な符号・大きさの応答を述べる箇所。'),('zob','その応答条件を根拠として係数の偶性へ接続する推論箇所。')):
        d=next(d for d in doc['declarations'] if d['name']==name);basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        '原刊909頁の著者脚注u0282を非零速度の非自明な比較として部分記述する。v=0では符号を変える実験は同じ条件になるため、この比較条件から除外するが、係数の偶性そのものはv=0で恒等的に成立する。',
        'sbg2の応答は物理的対称性から著者が要求するものとして保持し、一般の物理的対称性の定義・測定・向きの規約を完成したとは扱わない。先行する係数積1の主張を前提として明示する。',
        '同じNの値・同じ地点で比較し、他の五成分の零条件を別の点から借用しない。場が全領域で一定だとは要求しない。',
        '数式から符号反転と偶性の関係を検査できても、係数の正の枝を選ぶ根拠、二通りの逆変換を比較する論述、力・単位・真空と原文全体の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-parity'),(composed,'einstein-field-parity')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored field parity differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Nonzero field probe and signed response composed')


if __name__=='__main__':main()
