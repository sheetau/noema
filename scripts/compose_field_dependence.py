"""Express the magnetic counterpart and witnesses against frame-independent presence."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q
from scripts.compose_force_wordings import CUT, POINT, ROLES, ZERO, ONE, vector, at
from scripts.compose_rest_force import AXES

PARENT='examples/v014/einstein-force-wordings.noema'


def definitions():
    extra=k('sci2',v('light'),v('velocity'),v('electric'))
    text=definition('scq2','light '+CUT+' velocity '+POINT+' electric '+POINT,
        'i[axis a]['+k('bf',ZERO,app(extra,v('axis')))+']',POINT)
    args='light '+CUT+' velocity '+POINT+' electric '+POINT+' magnetic '+POINT
    text+=definition('scr2',args,k('s7s',AXES,v('magnetic'),k('scq2',v('light'),v('velocity'),v('electric'))),POINT)
    E=[app(v('electric'),k(role)) for role in ROLES[:3]];H=[app(v('magnetic'),k(role)) for role in ROLES[:3]]
    beta=k('soy',ONE,v('ratio'))
    text+=definition('scs2','ratio '+CUT+' electric '+POINT+' magnetic '+POINT,
        vector((H[0],k('s6e',beta,v('ratio'),H[1],E[2]),k('s6d',beta,v('ratio'),H[2],E[1]))),POINT)
    exact=k('scs2',v('ratio'),v('electric'),v('magnetic'))
    approximation=k('scr2',ONE,vector((v('ratio'),ZERO,ZERO)),v('electric'),v('magnetic'))
    domain='i[ratio '+CUT+']['+k('s45',ONE,v('ratio'))+']'
    conditions=[k('svy',domain,'i[ratio '+CUT+']['+app(exact,k(role))+']',
        'i[ratio '+CUT+']['+app(approximation,k(role))+']',
        'i[ratio '+CUT+']['+k('shv',v('ratio'),v('ratio'))+']',ZERO) for role in ROLES[:3]]
    text+=definition('sct2','electric '+POINT+' magnetic '+POINT,both(k('sch2',v('electric'),v('magnetic')),*conditions))
    zero='i[axis a]['+ZERO+']'
    text+=definition('scu2','value '+POINT,both(k('shn',AXES,v('value'),'p ba'),op('u',k('sho',AXES,v('value'),zero,'p sca'))))
    text+=definition('scv2','first '+POINT+' second '+POINT,both(k('sch2',v('first'),v('second')),
        op('u',op('z',k('scu2',v('first')),k('scu2',v('second'))))))
    pole=vector((ZERO,ZERO,ONE))
    text+=definition('scw2','ratio '+CUT,both(k('s45',ONE,v('ratio')),op('u',k('sca',v('ratio'),ZERO)),
        k('scv2',zero,k('scl2',v('ratio'),zero,pole)),k('scv2',zero,k('scs2',v('ratio'),pole,zero))))
    return text


MEANINGS={
    'scq2':'電気側ベクトルと速度から、既存の外積の追加項sci2の符号を反転して磁気側の追加項を構成する。−(u×E)/Vであり、加法逆元を省かない。正の光速度と成分の有効性はsck2で要求する。',
    'scr2':'磁気側ベクトルへscq2を加えた一次の候補式。これ単独を厳密な力の法則とはしない。',
    'scs2':'標準配置のx方向の符号付き速度比について、既存の正規化変換の磁気側三成分を、同じ旧系地点の電気・磁気ベクトルから構成する。',
    'sct2':'固定した電気・磁気ベクトルについて、速度比を零へ近づけたとき、磁気側の厳密な混合式scs2と一次式scr2の各成分の差が速度比の二乗のオーダーとなる条件。',
    'scu2':'有効な空間三成分のうち少なくとも一つが非零である。対象や場の存在一般ではなく、その成分群が零ベクトルではないという数値上の条件。',
    'scv2':'二つの有効な三成分ベクトルについて、一方が零ベクトルで他方が非零である。非零のまま値や方向が変わる場合とは区別する。',
    'scw2':'有効で非零の速度比について、電気側零・磁気側単位横成分の配置で電気側が非零になり、逆に磁気側零・電気側単位横成分の配置で磁気側が非零になる二つの別々の証人。両配置を一つの場だとはしない。',
    'scx2':'既存の変換則に、scw2の二配置で零・非零を変える許容速度比が存在するという部分的な読み。全ての場や全ての系で存在・不在が変わるとは述べない。存在一般についての著者の主張全体と同値とはしない。',
    'scy2':'同じ旧系の場と対象の出来事・地点に、磁気側の一次の追加項と二次誤差条件を部分接続する。磁気的な単位極の実在や測定を補わない。',
}


def composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'r zps[] a.r zpt[] a.'
    text+=definition('scx2','','b context['+q('g','ratio',CUT,k('scw2',v('ratio')))+']','e')
    ctx=v('context');point=k('zpj');coords=[app(point,k(role)) for role in ROLES]
    binding=both(k('va',k('ra')),k('znn',k('ra'),k('znl'),k('znm'),k('znk'),ctx),
        k('zpb',k('zol'),k('ra'),k('zpo'),point,ctx),k('shn',k('shx'),point,'p ba'),app(k('znk'),*coords))
    text+=definition('scy2','','b context['+both(binding,k('sct2',at(k('znl'),point),at(k('znm'),point)))+']','e')
    doc=parse(text);doc['statements']=statements;text=format_graph(doc,'compact')
    for node,content in (('zps','scy2'),('zpt','scx2')):text+='s[k uh[k '+node+'[] k rd[] r[k '+content+'[]] k zno[] k ri[]]].'
    doc=parse(text)
    basis=deepcopy(json.loads((ROOT/'data/einstein-force-wordings-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-field-dependence-basis-v1',document='examples/v014/einstein-field-dependence.noema')
    for name,meaning in (('zps','u0176冒頭で磁気側にも対応する説明が成り立つと述べる箇所。'),
        ('zpt','u0176末尾で電気・磁気の力の基準系への依存を述べる箇所。現在は零・非零が変わる変換則の証人による部分解釈。')):
        d=next(d for d in doc['declarations'] if d['name']==name)
        basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0176の磁気側への対応と、基準系に依存しない存在を持たないという末尾を部分記述した。後者は変換則で成分群の零・非零が変わる証人による限定的な解釈であり、存在一般の主張を数値変化へ還元し終えたものではない。',
        '電動力を理論の中で補助概念としてのみ用いるという役割、その導入を依存性から説明する関係、明白さの位置付けは未記述。追加項そのものは既存の関数から構成し、独立した未定義の力の原語を導入しない。',
        '二つの証人は異なる入力配置である。特定の現実の場が常に零と非零を切り替えるとはしない。全実切断での漸近証明、物理的な力・単位・場の説明、一般方向と全文の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def generic_composed():
    text,basis=composed();doc=parse(text);byname={d['name']:d for d in doc['declarations']};needed={'scq2','scr2','scs2','sct2','scu2','scv2','scw2'}
    def references(node):
        if isinstance(node,list):return set().union(*(references(n) for n in node)) if node else set()
        if not isinstance(node,dict):return set()
        found={node['symbol']} if node.get('symbol') in byname else set()
        return found|set().union(*(references(n) for n in node.values()))
    todo=list(needed)
    while todo:
        for name in references(byname[todo.pop()])-needed:needed.add(name);todo.append(name)
    doc['declarations']=[d for d in doc['declarations'] if d['name'] in needed];doc['statements']=[]
    basis=dict(version='field-dependence-basis-v1',document='examples/v014/field-dependence.noema',
        primitives=[p for p in basis['primitives'] if p['symbol'] in needed],definitions={n:m for n,m in basis['definitions'].items() if n in needed},
        unresolved=['磁気側の一次の追加項と、成分群の零・非零の違い。理論上の補助的役割や存在一般の意味をこれだけで定義しない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'field-dependence'),(composed,'einstein-field-dependence')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored field dependence differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Magnetic counterpart and frame-dependent zero/nonzero witnesses composed')


if __name__=='__main__':main()
