"""Link conscientious office ability, prospective departure and conditional duties."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_contained_conflict import BELIEF,CONTAINS,CLASHES,CANDIDATES
from scripts.compose_described_norms import DESCRIPTION,RULE,TRUE

PARENT='examples/v014/kant-contained-conflict.noema'
PERFORMS='h[a a d] c'
AVAILABLE='h[a a a d] c'
OUTCOMES='h[a a a d d] c'
CASES='h[a a a a d d] c'
GOAL=[('person','a'),('role','a'),('performs',PERFORMS),('conscientious',PERFORMS)]
ABILITY=[('person','a'),('role','a'),('context','d')]+GOAL[2:]+[
    ('available',AVAILABLE),('outcomes',OUTCOMES),('selected',OUTCOMES)]
TRIGGER=BELIEF[:4]+[('context','d')]+BELIEF[4:]
CONDITIONAL=[('source','a'),('person','a'),('role','a'),('document','a'),('standard','a'),
    ('activity','a'),('target',DESCRIPTION),('anchor','d')]+ABILITY[3:]+BELIEF[4:]+[('cases',CASES),('required',RULE)]
HISTORIES='h[a d d] c'
ORDER='h[d d d] c'
HOLDING='h[a a d] c'
CHANGES='h[a d d] c'
AFFECTED='h[a a d d] c'
AGENT='h[a a d] c'
TERMINATES='h[a a a d d] c'
TRANSITION=[('person','a'),('role','a'),('activity','a'),('earlier','d'),('later','d'),
    ('history','h[d] c'),('before','h[d d] c'),('holding',HOLDING),('changes',CHANGES),
    ('affected',AFFECTED),('agent',AGENT),('terminates',TERMINATES)]
SETTINGS=[('role','a'),('histories',HISTORIES),('order',ORDER)]+TRANSITION[7:]
SOURCE_TARGET=[('role','a'),('terminates',TERMINATES)]
ROOTS=['rg3','rg4','rg5','rg6','rg7','rha','rhb','rhc','rhd']


def ability_args():
    goal=k('rg3',*args(GOAL))
    available='i[who a plan a start d]['+app(v('available'),v('who'),v('role'),v('plan'),v('start'))+']'
    def outcomes(name):
        return 'i[who a plan a start d end d]['+app(v(name),v('who'),v('role'),v('plan'),v('start'),v('end'))+']'
    return [v('person'),goal,v('context'),available,outcomes('outcomes'),outcomes('selected')]


def definitions():
    text=definition('rg3',params(GOAL),'b point['+both(
        app(v('performs'),v('person'),v('role'),v('point')),
        app(v('conscientious'),v('person'),v('role'),v('point')))+']','e')
    callargs=ability_args()
    text+=definition('rg4',params(ABILITY),k('xd',*callargs))
    text+=definition('rg5',params(ABILITY),k('xg',*callargs))
    text+=definition('rg6',params(ABILITY),k('xe',callargs[0],*callargs[2:]))
    fixed='i[doc a claim a ignored d]['+app(v('contains'),v('doc'),v('claim'),v('anchor'))+']'
    text+=definition('rg7',params(TRIGGER),k('rgw',*args(BELIEF,anchor=v('context'),contains=fixed)))
    premise='i[who a][b point['+k('rg7',*args(TRIGGER,person=v('who'),context=v('point')))+']]'
    duty=app(v('required'),v('source'),v('who'),v('role'),v('activity'),v('target'),TRUE,v('point'))
    consequence='i[who a][b point['+both(k('rg5',*args(ABILITY,person=v('who'),context=v('point'))),duty)+']]'
    cases='i[point d]['+app(v('cases'),*map(v,('person','role','document','standard','anchor','point')))+']'
    conditional=k('rc',v('person'),premise,consequence,cases)
    text+=definition('rha',params(CONDITIONAL),conditional)
    text+=definition('rhb',params(CONDITIONAL),both(k('rha',*args(CONDITIONAL)),k('re',v('person'),premise,cases)))
    state='i[office a who a][b point['+app(v('holding'),v('who'),v('office'),v('point'))+']]'
    text+=definition('rhc',params(TRANSITION),k('rcf',v('history'),v('before'),v('activity'),v('role'),v('person'),
        v('earlier'),v('later'),state,*map(v,('changes','affected','agent','terminates'))))
    history='i[point d]['+app(v('histories'),v('person'),v('context'),v('point'))+']'
    before='i[first d second d]['+app(v('order'),v('first'),v('second'),v('context'))+']'
    future=quant('g','later','d',k('rhc',*args(TRANSITION,earlier=v('context'),history=history,before=before)))
    text+=definition('rhd',params(SETTINGS),'i[person a activity a][b context['+future+']]','h[a a] e')
    return text


MEANINGS={
    'rg3':'同じ人が同じ役職の職務を行い、その遂行が良心に適うという評価を同じ状況で満たす内容。遂行と評価の関係は別の引数で与える。',
    'rg4':'同じ本人・役職・開始状況に利用可能な方法のうち、非空で整合する評価結果の全てでrg3を満たすものがある。職務遂行だけの能力や実際の遂行と区別する。',
    'rg5':'利用可能な全方法について評価範囲が非空で想定結果に含まれ、その評価においてrg3を達成する方法がない。未評価の方法がある場合に、単なるrg4の否定を不能としない。',
    'rg6':'同じ本人・役職・開始状況の全利用可能方法について、評価結果が非空で想定結果に含まれる。良心の評価の正当性や方法範囲の現実的な網羅性を保証するものではない。',
    'rg7':'対象に含まれる部分を元の基準文脈で固定し、指定した評価文脈で本人が、その対象に基準と対立する部分があると判断するというrgwの条件。仮定状況ごとに別の規定群の部分へ差し替えない。',
    'rha':'選んだ仮定状況が非空で、その全てにおいて、同じ本人・対象・基準へのrg7の判断があるなら、同じ本人・役職についてrg5が成立し、同じ行為・閉じた目標記述への肯定的な要求がある。現実の判断・不能・要求・実行は含意しない。',
    'rhb':'rhaに加え、選んだ仮定状況の少なくとも一つで判断の前件が成立する。前件が全て偽である条件文と、適用候補がある条件文を区別する。',
    'rhc':'同じ本人が行う同じ変化過程により、同じ役職の保持が順序付き履歴の前で成立し、後で成立しなくなる。本人への作用と役職保持の終結関係を要求し、偶然の不在や他人による除去だけと区別する。',
    'rhd':'同じ本人・行為から内容への関数を作る。その内容は評価文脈から先の同じ履歴にrhcの終点があること。現在の要求と、今後の自己による役職保持の終結を別に記述するための、閉じて引用できる目標の構成。',
}
LIMITS=[
    '良心に適うという評価と職務遂行、利用可能な方法と結果・選択範囲は引数で明示する。良心の実質的な理論や規範的正当性、能力一般の唯一の定義を主張しない。',
    'rhaは判断から不能や義務を論理的に導く公理ではなく、明示した仮定範囲でその条件が成立するかを述べる。前件が偽の状況では後件を要求しない。反事実一般や例外・優先順位は未定義。',
    '役職の終結rhcは、自分の行為による同じ保持状態の終結を表す。発話による辞意表明、受理、法的な効力、自由意思や辞職理由の一般理論は別に必要である。',
    '目標rhdは評価文脈より後の終点を要求する。所要期間や期限を補わない。規範の評価は目標内容を実行せず、後の辞職が実現するとも予測しない。',
    '規範の対象記述は引用の構造を保持する。役職と関係を閉じた式で渡す引用を記述生成補助で作り、人・行為の引数を保つ。任意の別名・同値式への規範移送は行わない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-contained-conflict-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    source_target=k('rhd',v('role'),'p ia','p ic','p cf','p ag','p la','p df',v('terminates'))
    text=definitions()+definition('hzby',params(SOURCE_TARGET),source_target,'h[a a] e')
    for symbol,target in (('hzbz','rha'),('hzb2','rhb')):
        text+=definition(symbol,params(CONDITIONAL[:-1]),k(target,*args(CONDITIONAL,required='p h7a')))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-conscientious-office-basis-v1',document='examples/v014/kant-conscientious-office.noema')
    basis['definitions'].update(MEANINGS|{
        'hzby':'役職と終結関係を受け取り、既存の本人別履歴ia・順序ic・委任cf・変化ag・本人への作用la・本人の行為dfを使って、今後の役職保持の自己終結を述べる人・行為の内容関数を作る。',
        'hzbz':'rhaの条件文を、既存の同じ出所・本人・立場・行為・記述への要求h7aに接続する。辞職の目標には同じ役職で閉じたhzbyの引用を渡す。出所や実際の要求・辞職を自動的に補わない。',
        'hzb2':'hzbzの条件に加え、対立する部分があるという本人の判断を満たす仮定状況の存在を要求する。現実にその判断があることではない。',
    })
    basis['unresolved']+=LIMITS+[
        'u0012の職務遂行不能と辞職要求を、判断を前件とする同じ仮定範囲へ部分接続する。sein Amtの役職を目標引用の役職と一致させるのは閉じた記述の構成時であり、任意の入力記述を辞職へ自動変換しない。',
        '内的宗教と良心の実質、発見という認識行為、条件選択の正当性、dennによる説明、要求の出所、原文全体の意味一致は未完。新しい原始概念・局所参照・著者主張を追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=roots,statement_indices=[])
    projected_basis=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',projected_basis


def generic_composed():return projected(ROOTS,'conscientious-office')
def core_composed():return projected(ROOTS+['hzby','hzbz','hzb2'],'conscientious-office-core')
BUILDERS=((generic_composed,'conscientious-office'),(source_composed,'kant-conscientious-office'),(core_composed,'conscientious-office-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored conscientious office differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
