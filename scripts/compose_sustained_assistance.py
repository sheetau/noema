"""Compose purpose-directed assistance across explicit past work occasions."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from noema.linking import relocate
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_parameterized_goals import AIMS,DESCRIPTION

PARENT='examples/v014/einstein-intellectual-credit.noema'
TEMPORAL='examples/v014/persistence.noema'
SOURCE='examples/v014/einstein-sustained-assistance.noema'
LIBRARY='examples/v014/sustained-assistance.noema'
CORE='examples/v014/sustained-assistance-core.noema'
READING='data/sustained-assistance-reading-v1.json'
RELATIONS=[('occurs','h[a d] c'),('performs','h[a a d] c'),('aims',AIMS),
    ('goalfor','h[a a '+DESCRIPTION+' d] c'),('working','h[a a d] c')]
EPISODE=[('helper','a'),('recipient','a'),('work','a'),('act','a'),('point','d'),('goal',DESCRIPTION)]+RELATIONS
AT=[(n,t) for n,t in EPISODE if n!='act']
TEMP=[('recipient','a'),('work','a'),('context','d'),('history','h[d] c'),
    ('scope','h[d] c'),('before','h[d d] c'),('working','h[a a d] c')]
OCCASIONS=[('scope','h[d] c'),('occasions','h[d] c')]
PERIOD=[('helper','a'),('recipient','a'),('work','a'),('goal',DESCRIPTION),('context','d')]+TEMP[3:6]+[('occasions','h[d] c')]+RELATIONS


def reused_temporal():
    doc=parse((ROOT/TEMPORAL).read_text(encoding='utf-8'))
    return [relocate(d,{'ta':'sewm','tb':'sewn'}) for d in doc['declarations'] if d['name'] in ('ta','tb')]


def definitions():
    point=v('point');bindings='l[a][v recipient v work]'
    episode=both(app(v('working'),v('recipient'),v('work'),point),
        app(v('goalfor'),v('recipient'),v('work'),v('goal'),point),
        app(v('occurs'),v('act'),point),app(v('performs'),v('helper'),v('act'),point),
        app(v('aims'),v('helper'),v('act'),v('goal'),bindings,point))
    text=definition('sewo',params(EPISODE),episode)
    text+=definition('sewp',params(AT),quant('g','act','a',k('sewo',*args(EPISODE))))
    temporal=both(k('sewn',v('history'),v('scope'),v('before')),app(v('history'),v('context')),
        quant('f','point','d',op('y',app(v('scope'),point),both(
            app(v('before'),point,v('context')),app(v('working'),v('recipient'),v('work'),point)))))
    text+=definition('sewq',params(TEMP),temporal)
    selected=app(v('occasions'),point)
    text+=definition('sewr',params(OCCASIONS),both(quant('g','point','d',selected),
        quant('f','point','d',op('y',selected,app(v('scope'),point)))))
    valid=both(k('sewq',*args(TEMP)),k('sewr',*args(OCCASIONS)))
    support=k('sewp',*args(AT))
    text+=definition('sews',params(PERIOD),both(valid,quant('g','point','d',both(selected,support))))
    text+=definition('sewt',params(PERIOD),both(valid,quant('f','point','d',op('y',selected,support))))
    text+=definition('sewu',params(PERIOD),both(valid,quant('g','point','d',both(selected,op('u',support)))))
    return text


MEANINGS={
    'sewm':'既存taを移した、非空の履歴上の厳密な全順序。',
    'sewn':'既存tbを移した、同じ履歴の非空で間の抜けない区間。',
    'sewo':'同じ受け手の同じ仕事の進行中に、助け手が起きた同じ行為を行い、その受け手と仕事のための同じ目標記述へ志向する。目的の達成や唯一の動機は要求しない。',
    'sewp':'その状況でsewoを満たす行為が少なくとも一つある。物理的な同席や無目的な利益だけで代用しない。',
    'sewq':'基準状況を含む同じ履歴の中で、同じ受け手が仕事を進めていた非空の連続区間を選び、全区間を基準より厳密に過去へ置く。',
    'sewr':'支援機会の範囲が非空で、全て同じ仕事の評価区間内にある。成功した時点だけを後から選ぶための条件ではない。',
    'sews':'妥当な過去の仕事区間・支援機会のうち、少なくとも一機会で目的に向けた支援行為がある。',
    'sewt':'同じ妥当な区間の全ての明示された支援機会に、その仕事のための支援行為があるという強い継続条件。無関係な中間時刻にも行為を要求しない。',
    'sewu':'同じ妥当な範囲に、目的に向けた支援行為のない機会が少なくとも一つある。範囲不備を支援不履行と混同しない。',
    'sewv':'受け手・仕事の順序付き二個体列を、その受け手の仕事が前進する内容へ結ぶ目標記述の候補。長さと位置を保つ。',
    'seww':'本文の同じ著者・Besso・研究と、明示した過去区間・機会へ結んだ少なくとも一度の支援。',
    'sewx':'本文の同じ人々・仕事・過去区間で、明示された全支援機会に目的に向けた行為があるという継続的支援の候補。忠実さ一般の必要十分条件ではない。',
}
LIMITS=[
    'zur Seite standを同じ仕事への目的に向けた行為として、treuを明示した支援機会への応答の継続として具体化する強い候補である。準備だけの支援、精神的な支え、例外を許す信頼性、困難な場面での態度を含む語義全体を確定しない。',
    '支援機会は結果と独立に指定する。失敗した機会を除外すれば継続が真になりうるため、範囲の正当性・完全性は原文と別途確認する。空の機会を忠実な支援と判定しない。',
    '目標への志向は既存の引数付き目的の規約を使う。目標の達成・実現可能性、成果を生む因果的十分性、無私の唯一動機、実際の同席を要求しない。目的形成と実際の援助の機構の説明は残る。',
    '仕事の全評価区間を基準より過去とする候補である。基準は論文の発話状況であり、絶対日時・作業区間の端点・支援機会を原文から自動的に補わない。',
    '友人・同僚・結びとしての言明は今回の対応範囲に含めない。先行する着想の寄与と支援行為は同じ人物・仕事を共有するが、全て同じ行為だとは同一化しない。',
    '作業の進行、目的の受益対象、目的志向、前進の判定は原始関係の解釈に残る。歴史的事実、忠実さの語用と全文の意味一致は未確認である。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc['declarations']+=reused_temporal()
    values={
        'zrrnode':('a','u0276前半の支援に関する主張箇所。'),
        'zrrscope':('h[d] c','結果とは独立に明示する、同じ研究の作業区間。'),
        'zrrhistory':('h[d] c','作業と論文の基準状況を含む同じ履歴。'),
        'zrrbefore':('h[d d] c','同じ履歴の時間的先行。'),
        'zrroccasions':('h[d] c','同じ研究で支援を評価する機会の範囲。成功した行為から逆算しない。'),
        'zrrworking':('h[a a d] c','本人が同じ仕事を進めている状況。'),
        'zrrgoalfor':('h[a a '+DESCRIPTION+' d] c','同じ本人と仕事のための目標記述。'),
        'zrraims':(AIMS,'行為者が同じ行為で同じ目標記述と順序付き引数へ志向する。目標の真理を意味しない。'),
        'zrradvances':('h[a a d] c','同じ本人の同じ研究が前進するという目標の候補。前進の評価規約は別途必要。'),
    }
    extra=definitions()+''.join('r '+n+'[] '+sort+'.' for n,(sort,_) in values.items())
    goal=both(op('e','d[v bindings]','n p c b'),
        'a[v bindings][n p a b][v recipient]','a[v bindings][n p b b][v work]',
        app(k('zrradvances'),v('recipient'),v('work'),v('point')))
    goal=quant('g','recipient','a',quant('g','work','a',goal))
    extra+=definition('sewv','','i[bindings j[a]][b point['+goal+']]','h[j[a]] e')
    replacements=dict(helper=k('zrqperson'),recipient=k('rd'),work=k('zrqwork'),goal='r[k sewv[]]',
        context=v('context'),occurs=k('zrqoccurs'),performs=k('zrqperforms'))
    replacements.update({n:k('zrr'+n) for n,_ in PERIOD if n not in replacements})
    for target,root in (('seww','sews'),('sewx','sewt')):
        extra+=definition(target,'','b context['+k(root,*args(PERIOD,**replacements))+']','e')
    doc=parse(format_graph(doc,'compact')+extra)
    statement='s[k uh[k zrrnode[] k rd[] r[k sewx[]] k zrqscope[] k ri[]]].'
    doc['statements']=old['statements']+parse(format_graph(doc,'compact')+statement)['statements']
    basis=json.loads((ROOT/'data/einstein-intellectual-credit-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-sustained-assistance-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    lookup={d['name']:d for d in doc['declarations']}
    for n,(_,meaning) in values.items():
        d=lookup[n];basis['primitives'].append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-sustained-assistance-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,list(MEANINGS)[:9],[]),(CORE,['seww','sewu'],[len(old['statements'])])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(p,len(body),flush=True)


if __name__=='__main__':main()
