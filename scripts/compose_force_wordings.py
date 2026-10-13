"""Keep the cross-product approximation distinct from a comoving-frame force."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT, POINT, FIELD, ROLES
from scripts.compose_rest_force import AXES

PARENT='examples/v014/einstein-rest-force.noema'
ZERO=k('bb','n p a b');ONE=k('bb','n p b b')


def vector(components):
    result=ZERO
    for role,component in reversed(tuple(zip(ROLES[:3],components))):
        result=k('szi',op('e',v('axis'),k(role)),component,result)
    return 'i[axis a]['+result+']'


def at(field,point):
    return 'i[axis a]['+app(app(field,v('axis')),*(app(point,k(role)) for role in ROLES))+']'


def definitions():
    first=[app(v('first'),k(role)) for role in ROLES[:3]];second=[app(v('second'),k(role)) for role in ROLES[:3]]
    cross=[k('bf',k('shv',first[j],second[l]),k('shv',first[l],second[j])) for j,l in ((1,2),(2,0),(0,1))]
    text=definition('scg2','first '+POINT+' second '+POINT,vector(cross),POINT)
    text+=definition('sch2','first '+POINT+' second '+POINT,both(k('shn',AXES,v('first'),'p ba'),k('shn',AXES,v('second'),'p ba')))
    crossvalue=k('scg2',v('velocity'),v('magnetic'))
    text+=definition('sci2','light '+CUT+' velocity '+POINT+' magnetic '+POINT,
        'i[axis a]['+k('shv',k('sjd',v('light')),app(crossvalue,v('axis')))+']',POINT)
    args='light '+CUT+' velocity '+POINT+' electric '+POINT+' magnetic '+POINT
    text+=definition('scj2',args,k('s7s',AXES,v('electric'),k('sci2',v('light'),v('velocity'),v('magnetic'))),POINT)
    text+=definition('sck2',args,both(k('ba',v('light')),k('bg',ZERO,v('light')),k('sch2',v('velocity'),v('magnetic')),k('shn',AXES,v('electric'),'p ba')))
    E=[app(v('electric'),k(role)) for role in ROLES[:3]];H=[app(v('magnetic'),k(role)) for role in ROLES[:3]]
    beta=k('soy',ONE,v('ratio'))
    response=(E[0],k('s6d',beta,v('ratio'),E[1],H[2]),k('s6e',beta,v('ratio'),E[2],H[1]))
    text+=definition('scl2','ratio '+CUT+' electric '+POINT+' magnetic '+POINT,vector(response),POINT)
    domain='i[ratio '+CUT+']['+k('s45',ONE,v('ratio'))+']'
    approximate=k('scj2',ONE,vector((v('ratio'),ZERO,ZERO)),v('electric'),v('magnetic'))
    exact=k('scl2',v('ratio'),v('electric'),v('magnetic'))
    conditions=[k('svy',domain,'i[ratio '+CUT+']['+app(exact,k(role))+']',
        'i[ratio '+CUT+']['+app(approximate,k(role))+']',
        'i[ratio '+CUT+']['+k('shv',v('ratio'),v('ratio'))+']',ZERO) for role in ROLES[:3]]
    text+=definition('scm2','electric '+POINT+' magnetic '+POINT,both(k('sch2',v('electric'),v('magnetic')),*conditions))
    return text


MEANINGS={
    'scg2':'順序付けた三軸yn,yo,ypに対する二つのベクトルの外積。成分は(y z−z y, z x−x z, x y−y x)の順とし、他の役割は零とする。右手系の成分規約で使う。',
    'sch2':'三つの空間軸が異なり、二ベクトルの全三成分が有効な実数である。零ベクトルや平行なベクトルを排除しない。',
    'sci2':'速度ベクトルと磁気側のベクトルの外積を正の光速度で割った追加項。外積の順序を保持する。定義域はsck2で要求する。',
    'scj2':'電気側ベクトルへsci2の追加項を加えた一次の候補式。単独で厳密な力の式だとは宣言しない。',
    'sck2':'光速度が有効で正であり、速度・電気側・磁気側の三成分が有効であるという演算条件。小速度の誤差条件は別に要求する。',
    'scl2':'標準配置のx方向の符号付き速度比について、同じ旧系地点の電気・磁気側の値を既存の正規化した三変換式で混合する。比の絶対値が1未満で使う。',
    'scm2':'固定した電気・磁気ベクトルについて、x方向の速度比を零へ近づけたとき、scl2と一次の外積式scj2の各成分の差が速度比の二乗のオーダーとなる条件。固定ベクトルごとの定数・近傍幅を許す。全場・全方向について一様な定数があるとはしない。',
    'scn2':'本文の同じ点状の単位電気量が静止系に対して動いているという、二つの言い表しで用いる前提。単位の値を力評価の出来事へ接続する。',
    'sco2':'旧来の言い表しの、標準配置・固定地点の場の値での部分記述。前提が成立するとき、単位と場・対象位置を結び、一次の外積式と正規化変換の二次誤差条件を要求する。任意方向の厳密な力の法則までは述べない。',
    'scp2':'同じ点状の単位電気量が動き、移動系へ当該瞬間静止するなら、その系で測る力を、同じ出来事へ変換した座標で評価する変換後の電気側ベクトルへ結ぶ。旧系で測る力の三成分とは同一視しない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r zpp[] a.r zpq[] a.r zpr[] a.'
    ctx=v('context');body=k('zol');event=k('zpo');oldpoint=k('zpj');newpoint=k('zpk')
    text+=definition('scn2','','b context['+both(k('zok',body,ctx),k('xm',body,k('ra'),ctx),
        k('sbw2',k('zpp'),body,k('zor'),k('ra'),event,k('zou'),'n p b b',ONE,ctx,'p zof','p zog'))+']','e')
    coords=[app(oldpoint,k(role)) for role in ROLES]
    oldbinding=both(k('va',k('ra')),k('znn',k('ra'),k('znl'),k('znm'),k('znk'),ctx),
        k('zpb',body,k('ra'),event,oldpoint,ctx),k('shn',k('shx'),oldpoint,'p ba'),app(k('znk'),*coords))
    text+=definition('sco2','','b context['+op('y',op('t',k('scn2'),ctx),
        both(oldbinding,k('scm2',at(k('znl'),oldpoint),at(k('znm'),oldpoint))))+']','e')
    mapped=k('s46',k('tc'),k('zb7'),oldpoint)
    premise=both(op('t',k('scn2'),ctx),k('zpa',body,k('zbm'),event,ctx))
    consequent=both(oldbinding,k('s45',k('tc'),k('zb7')),
        k('shn',k('shx'),newpoint,'p ba'),k('sho',k('shx'),mapped,newpoint,'p sca'),
        op('t',k('scf2'),ctx),k('scb2',AXES,k('s6k',k('tc'),k('zb7'),k('znl'),k('znm')),newpoint,k('zpm')))
    text+=definition('scp2','','b context['+op('y',premise,consequent)+']','e')
    doc=parse(text);doc['statements']=statements
    text=format_graph(doc,'compact')
    for node,content in (('zpq','sco2'),('zpr','scp2')):text+='s[k uh[k '+node+'[] k rd[] r[k '+content+'[]] k zno[] k ri[]]].'
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/einstein-rest-force-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-force-wordings-basis-v1',document='examples/v014/einstein-force-wordings.noema')
    for name,meaning in (('zpp','二つの言い表しで用いる同じ点状電気量の、力評価時の単位値1の記録。'),
        ('zpq','u0174の旧来の言い表しを提示する箇所。'),('zpr','u0175の新しい言い表しを提示する箇所。')):
        d=next(d for d in doc['declarations'] if d['name']==name)
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0174の外積式を三方向に定義し、近似の留保を標準配置のx方向の変換で部分記述した。任意方向の運動への座標回転、全方向・全場に一様な誤差条件、全実切断での漸近評価の証明は未完。',
        'u0175は先行する二つの系・同じ対象・出来事・力の記録へ部分接続した。瞬間静止する系と変換速度の物理的な同定、場と力・電気量・単位の一般的な基礎説明は未完。',
        'u0173末尾の最初の三式を二つの言い表しへ結ぶ談話、旧来・新しいという言語上の対比、電動力という補助概念の地位と後続段落、全文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed=set(('scg2','sch2','sci2','scj2','sck2','scl2','scm2'))
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='force-wordings-basis-v1',document='examples/v014/force-wordings.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['右手系の三成分規約での外積と、固定した場の値に対するx方向の一次近似。物理的な意味の基礎説明と全実切断の漸近証明は含まない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'force-wordings'),(composed,'einstein-force-wordings')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored force wording differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Cross-product approximation and transformed comoving force composed')


if __name__=='__main__':main()
