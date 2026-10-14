"""Order same-goal achievements without inventing unique credit or causal action."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/kant-deserved-responses.noema'
GOAL='i[h[a] e]'
ACHIEVES='h[a a a '+GOAL+' d] c'
CONFIG=[('history','h[d] c'),('before','h[d d] c'),('people','h[a] c'),('target','a'),('goal',GOAL),('achieves',ACHIEVES),('assessed','h[a d] c')]
FIRST=CONFIG+[('anchor','d'),('person','a'),('activity','a'),('point','d')]
CHANGE=[('history','h[d] c'),('before','h[d d] c'),('person','a'),('activity','a'),('target','a'),('earlier','d'),('later','d'),('goal',GOAL)]
RELATIONS=[('changes','h[a d d] c'),('affected','h[a a d d] c'),('occurs','h[a d] c'),('agent','h[a a d] c'),('produces','h[a a '+GOAL+' d] c')]
FACTORY=CHANGE[:2]+[('goal',GOAL)]+RELATIONS
ROOTS=['rob','roc','rod','roe','rof','rog']


def definitions():
    le=lambda first,last:op('x',op('e',v(first),v(last)),app(v('before'),v(first),v(last)))
    match=lambda person,act,point:app(v('achieves'),v(person),v(act),v('target'),v('goal'),v(point))
    checked=quant('f','other','a',quant('f','when','d',op('y',both(app(v('people'),v('other')),app(v('history'),v('when')),le('when','point')),app(v('assessed'),v('other'),v('when')))))
    earlier=quant('g','other','a',quant('g','event','a',quant('g','when','d',both(app(v('people'),v('other')),app(v('history'),v('when')),app(v('before'),v('when'),v('point')),match('other','event','when')))))
    first=both(k('ta',v('history'),v('before')),app(v('history'),v('anchor')),app(v('history'),v('point')),le('point','anchor'),app(v('people'),v('person')),match('person','activity','point'),checked,op('u',earlier))
    text=definition('rob',params(FIRST),first)
    unique=quant('f','other','a',quant('f','event','a',op('y',both(app(v('people'),v('other')),match('other','event','point')),op('e',v('other'),v('person')))))
    text+=definition('roc',params(FIRST),both(k('rob',*args(FIRST)),unique))
    for name,target in (('rod','rob'),('roe','roc')):
        content=quant('g','activity','a',quant('g','point','d',k(target,*args(FIRST))))
        text+=definition(name,params(CONFIG),'i[person a][b anchor['+content+']]','h[a] e')
    state=app('s[v goal]',v('target'))
    transition=k('th',v('history'),v('before'),v('activity'),v('earlier'),v('later'),v('changes'),state)
    achieved=both(transition,app(v('affected'),v('target'),v('activity'),v('earlier'),v('later')),app(v('occurs'),v('activity'),v('later')),
        app(v('agent'),v('person'),v('activity'),v('later')),app(v('produces'),v('activity'),v('target'),v('goal'),v('later')))
    text+=definition('rof',params(CHANGE+RELATIONS),achieved)
    event=both(op('e',v('requested'),v('goal')),quant('g','earlier','d',k('rof',*args(CHANGE+RELATIONS))))
    text+=definition('rog',params(FACTORY),'i[person a activity a target a requested '+GOAL+' later d]['+event+']',ACHIEVES)
    return text

MEANINGS={
    'rob':'同じ厳密な全順序履歴・比較対象者・受益対象・目標記述で、基準時までに指定本人の指定行為が達成し、それ以前に範囲内の誰の達成もない。候補時点までの比較対象者の評価を要求し、同時の他者の達成は許す。',
    'roc':'robに加え、同じ時点に同じ目標を達成した比較対象者が指定本人だけである。同じ本人による複数行為は排除せず、功績や原因の独占とも区別する。',
    'rod':'基準時までにrobを満たす行為と時点を持つ本人という内容関数。現在も結果が続くことや、後続の達成者がいないことは要求しない。',
    'roe':'基準時までにrocを満たす行為と時点を持つ本人という内容関数。同時の達成者が複数ならrodと区別される。',
    'rof':'同じ行為が受益対象を履歴上の目標不成立から成立へ移し、生起・本人の関与・同じ対象と目標記述への結果生成がある。行為者と受益対象を別に保持し、時間順序だけを因果の証拠にしない。',
    'rog':'固定した履歴・順序・目標について、同じ目標記述を要求し、rofを満たす開始点がある達成関係。未知の目標への脱引用を含むため、引用へ渡す接続では閉じた目標に静的特殊化する。',
    'hzgd':'rofの変化・対象・生起・関与・結果生成をag・la・dg・df・g3へ接続する。本人だけが原因であること、意図や道徳的な功績の正当性は含めない。',
    'hzge':'rogを同じ五つの既存関係へ接続する。比較可能な達成関係を作り、単に結果が真であることや指図しなかったことを達成行為に数えない。',
}
LIMITS=[
    '最初という比較は明示した履歴・人々・受益対象・目標記述に限る。全人類の全歴史を網羅した証明ではない。比較対象を変えると最初の判定も変わり得る。',
    'assessedは候補時点までの各対象者について該当達成の評価範囲がそろっているという条件。評価漏れを不達成に補わない。現実の記録の完全性を形式だけで保証しない。',
    '同時の達成者を許すrobと、唯一の最初の達成者rocを分ける。原文zuerstだけから唯一性を補わず、どちらも因果や功績の独占を意味しない。',
    '履歴の順序は非空の厳密な全順序を要求する。比較不能な時点や循環を先着順に直さない。無限・密な履歴で最初の達成点がない場合、存在条件を成立させない。',
    '目標は同じ対象で不成立から成立へ変わることを要求する。瞬間的な行為、持続する結果、十分原因・必要原因、他者の援助の不在は含まない。',
    '政府側からの自由への作例は、指定した集団の同じ人々・主題・活動について、同じ規範源が実行と不実行を許す政策を目標にする。人類全体の自立・未成熟の全語義・国家や政府の制度・宗教と良心の内容は未完。',
    'u0015のder zuerstへの部分注記。全文の解放内容、少なくとも政府側という限定、集団の範囲、感謝・世界・後世と全文の意味一致は残る。時間的な先行だけで称賛に値すると結論しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    fixed=dict(changes='p ag',affected='p la',occurs='p dg',agent='p df',produces='p g3')
    text=definitions()+definition('hzgd',params(CHANGE),k('rof',*args(CHANGE+RELATIONS,**fixed)))
    text+=definition('hzge',params(FACTORY[:3]),k('rog',*args(FACTORY,**fixed)),ACHIEVES)
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-deserved-responses-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-first-achievers-basis-v1',document='examples/v014/kant-first-achievers.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'first-achievers')
def core_composed():return projected(ROOTS+['hzgd','hzge','hzfo','ro6'],'first-achievers-core')
BUILDERS=((generic_composed,'first-achievers'),(source_composed,'kant-first-achievers'),(core_composed,'first-achievers-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored first achiever differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
