"""Compose linked calculation steps and description-sensitive assessments."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q

TRUE=op('e','n p a b','n p a b')
FALSE=op('u',TRUE)
SELECT='h[i[e] i[e]] i[e]'
STEP='h['+SELECT+'] i[e]'
STEPS='j['+STEP+']'
RULE='h[i[e] i[e]] c'
COST='h['+STEP+'] b'
LEFT='i[left i[e] right i[e]][v left]'
RIGHT='i[left i[e] right i[e]][v right]'


def step(before,after):
    return 'i[select '+SELECT+']['+app(v('select'),before,after)+']'


def generic_definitions():
    before=app(v('step'),LEFT);after=app(v('step'),RIGHT)
    initial='i[target i[e]]['+op('e',v('target'),v('premise'))+']'
    update='i[state h[i[e]] c step '+STEP+'][i[target i[e]]['+both(
        app(v('state'),before),app(v('allowed'),before,after),op('e',v('target'),after))+']]'
    folded='q[v steps]['+initial+']['+update+']'
    params='steps '+STEPS+' premise i[e] conclusion i[e] allowed '+RULE
    text=definition('s2w',params,both(op('u',op('e','d[v steps]','n p a b')),app(folded,v('conclusion'))))
    cost=app(v('cost'),v('step'))
    text+=definition('s2x','steps '+STEPS+' cost '+COST,'q[v steps][n p a b][i[total b step '+STEP+']['+k('ab',v('total'),cost)+']]','b')
    nonnegative='q[v steps]['+TRUE+'][i[valid c step '+STEP+']['+both(v('valid'),op('u',k('aa',cost,'n p a b')))+']]'
    text+=definition('s2y',params+' cost '+COST+' low h[b] c',both(k('s2w',v('steps'),v('premise'),v('conclusion'),v('allowed')),
        nonnegative,app(v('low'),k('s2x',v('steps'),v('cost')))))
    text+=definition('s2z','subject i[e] context d measure h[i[e] d] b standard h[b d] c',
        app(v('standard'),app(v('measure'),v('subject'),v('context')),v('context')))
    return text


MEANINGS={
    's2w':'非空の有限手順列が、指定した前提の記述から結論の記述まで順につながり、各前後対が同じ許容変形関係を満たす。記述の内容を真として評価しない。許容関係の健全性は別の条件。',
    's2x':'同じ有限手順列の各出現に付いた有理数の負担評価を順に足す。空列は0、重複した出現も加算する。実際の実行時間や固定の計算量ではない。',
    's2y':'s2wでつながる同じ手順列について、各出現の負担が非負であり、その合計が指定した低負担基準に入る。成功する高負担の手順と、低負担の別の手順を混ぜない。',
    's2z':'同じ内容の記述と評価文脈から得る尺度値が、その文脈の基準に入る。内容自体の真理、別の同値記述への置換、尺度と基準の普遍性を含意しない。',
}


def generic_composed():
    doc=parse('n:\nr aa[b b] c.r ab[b b] b.\n'+generic_definitions())
    basis={'version':'calculation-assessments-basis-v1','document':'examples/v014/calculation-assessments.noema',
        'primitives':[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],arguments=['left','right'],
            meaning_ja='有理数の厳密な順序。' if d['name']=='aa' else '有理数の加算。') for d in doc['declarations'] if d['kind']=='primitive'],
        'definitions':MEANINGS.copy(),'unresolved':[
            '許容変形の根拠、負担評価と低負担の基準は引数で明示する。低負担をあらゆる意味での容易さや単純さと同一視しない。',
            '評価尺度の一般的な構成と、注目に値するという語義の全体は未完。記述内容を評価せずに評価対象として保持できることを検査する。']}
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/'examples/v014/einstein-angle-composition.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+generic_definitions()
    relation='h['+CUT+' '+CUT+' '+CUT+'] c';domain='h['+CUT+' '+CUT+'] c'
    left,right,result=map(v,('left','right','result'))
    text+=definition('s3a','relation '+relation+' domain '+domain,
        q('f','left',CUT,q('f','right',CUT,q('f','result',CUT,op('y',app(v('domain'),left,right),
            op('z',app(v('relation'),left,right,result),app(v('relation'),right,left,result)))))))
    text+='r zkx[] a.r zky[] a.r zkz[] '+STEPS+'.\n'
    text+='r zla[i[e] i[e] d] c.r zlb['+STEP+' d] b.r zlc[b d] c.r zld[i[e] d] b.r zle[b d] c.\n'
    cosine=app(k('zkt'),TRUE);sine=app(k('zkt'),FALSE);zero=k('bb','n p a b')
    rel='i[left '+CUT+' right '+CUT+' result '+CUT+']['+k('s2t',k('tc'),left,right,cosine,sine,result)+']'
    dom='i[left '+CUT+' right '+CUT+']['+both(k('ba',left),k('ba',right),op('u',k('bg',left,zero)),op('u',k('bg',right,zero)))+']'
    text+=definition('s3b','','b context['+both(k('ba',k('tc')),k('bg',zero,k('tc')),k('s2j',k('zkt')),k('s3a',rel,dom))+']','e')
    text+=definition('s3c','','b context['+both('t[k syy[]][v context]',k('szt',k('zkq'),k('zke')),
        k('szs',k('zkp'),k('zke')),k('s2u',k('zkc'),k('zkd'),k('zkq'),cosine,sine))+']','e')
    text+=definition('s3d','','b context['+k('s2y',k('zkz'),'r[k s3c[]]','r[k s2v[]]',
        'i[before i[e] after i[e]][k zla[v before v after v context]]',
        'i[step '+STEP+'][k zlb[v step v context]]','i[burden b][k zlc[v burden v context]]')+']','e')
    text+=definition('s3e','','b context['+k('s2z','r[k s3b[]]',v('context'),'p zld','p zle')+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zkx[] k rd[] r[k s3c[]] r[k s2v[]] k zkf[] k ri[]]].
s[k uh[k zkx[] k rd[] r[k s3d[]] k zkf[] k ri[]]].
s[k uh[k zky[] k rd[] r[k s3b[]] k zkf[] k ri[]]].
s[k uh[k zky[] k rd[] r[k s3e[]] k zkf[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/angle-composition-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='calculation-discourse-basis-v1',document='examples/v014/einstein-calculation-discourse.noema')
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zkx',[],'簡単な計算から速度合成式が得られると述べる本文箇所。'),
        ('zky',[],'二つの速度が合成式へ対称に入ることを注目すべきものと述べる箇所。'),
        ('zkz',[],'本文の計算として解釈する有限手順列。原文にない手順数や具体的な途中式は指定しない。各要素は前後の記述を選択関数へ渡す対であり、対自体も既存の関数構文だけで構成できる。'),
        ('zla',['before','after','context'],'同じ文脈の計算方法で、前の記述から後の記述への変形を採用できるとする関係。外部検査器による証明済みと同一視しない。'),
        ('zlb',['step','context'],'記述された同じ変形手順の、文脈ごとの負担評価。実際の時間や機械演算回数への固定はしない。'),
        ('zlc',['burden','context'],'計算の負担を小さいと評価する文脈基準。原文にない数値閾値は固定しない。'),
        ('zld',['subject','context'],'記述された事柄へ注意を向ける価値の文脈的な評価値。内容の真理値や驚きの度合いとは区別する。'),
        ('zle',['degree','context'],'注意を向ける価値が、その文脈で注目に値する基準に入るという条件。著者の評価を全読者共通の尺度にはしない。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        's3a':'指定された二入力の範囲で、同じ結果を持つ関係が入力の交換によって保たれる。実切断全体へ量化する一般的な対称性条件であり、選んだ一組だけの一致ではない。',
        's3b':'正の光速度と単位円の角の下で、合成式s2tの二つの非負入力を交換しても関係が同じとなるという内容。二乗式だけでなく符号付きの商を対象にする。',
        's3c':'先行する運動と変換の内容、同じ点の二つの速さ、角と成分の対応を合わせた導出元の明示的な読み。追加した対応条件を著者の逐語的な前提とは扱わない。',
        's3d':'同じ前提s3cと結論s2vをつなぐ計算手順の負担が小さいという部分解釈。導出の正当性を帰属だけから認定しない。',
        's3e':'対称性s3bの記述に、注意を向ける価値の尺度と文脈基準を適用した評価。対称性の真理や読み手の実際の注目とは区別する。'})
    basis['unresolved']+=generic_composed()[1]['unresolved']+[
        'u0139後半とu0141第一文の部分解釈。einfache Rechnungを低負担の有限変形、bemerkenswertを注意を向ける価値として読むが、唯一の語義とはしない。',
        '原文は計算の手順列や負担値を示していない。zkzを具体的な機械証明や著者が実行した履歴として扱わず、zlaの健全性は別途確認する。',
        '対称性は合成式の二つの非負入力の交換であり、二つの基準系の観測値・意味役割・出来事の同一視ではない。',
        '成分と角の対応、分母の符号、歴史的な規約、一般の実切断の演算法則、後続の平行運動と全文の意味一致は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,basisname in ((generic_composed,'calculation-assessments'),(composed,'calculation-discourse')):
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+basisname+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored calculation discourse differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Finite calculation chains, burden and symmetry appraisal composed')


if __name__=='__main__':main()
