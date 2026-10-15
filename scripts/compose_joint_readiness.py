"""Separate finite group size, common-plan compliance and a shared outcome goal."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import TRUE,DESCRIPTION,RULE

LIBRARY='examples/v016/joint-readiness.noema'
EXAMPLE='examples/v016/joint-readiness-example.noema'
BASIS='data/joint-readiness-basis-v1.json'
COUNTS='examples/v014/scoped-counts.noema'
OBEDIENCE='examples/v016/scoped-obedience.noema'
MODEL='examples/v016/anchored-ability.noema'
BASE=[('planner','a'),('group','a'),('members','j[a]'),('anchor','d'),('membersof','h[a a d] c'),
      ('goals','h[a a a a d] e'),('available','h[a a a d] c'),('outcomes','h[a a a d d] c'),('selected','h[a a a d d] c')]
PLAN=BASE+[('plan','a')]
TARGET=BASE+[('goal','e')]

def av(fields):return [v(n) for n,_ in fields]

def definitions():
    text=definition('rup','members j[a] scope h[a] c criterion h[b] c',both(k('rcm',v('members'),v('scope')),app(v('criterion'),'d[v members]')))
    scope='i[person a]['+app(v('membersof'),v('group'),v('person'),v('anchor'))+']'
    available=app(v('available'),v('planner'),v('group'),v('plan'),v('anchor'))
    selected=app(v('selected'),v('planner'),v('group'),v('plan'),v('anchor'),v('point'))
    outcome=app(v('outcomes'),v('planner'),v('group'),v('plan'),v('anchor'),v('point'))
    membergoal=app(v('goals'),v('planner'),v('group'),v('person'),v('plan'),v('anchor'))
    allmembers='q[v members]['+TRUE+'][i[valid c person a]['+both(v('valid'),op('t',membergoal,v('point')))+']]'
    consistent=both(quant('g','point','d',selected),quant('f','point','d',op('y',selected,outcome)))
    text+=definition('ruq',params(PLAN),both(k('rcm',v('members'),scope),available,consistent,
        quant('f','point','d',op('y',selected,allmembers))))
    text+=definition('rur',params(PLAN+[('goal','e')]),both(k('ruq',*av(PLAN)),
        quant('f','point','d',op('y',selected,op('t',v('goal'),v('point'))))))
    text+=definition('rus',params(TARGET),quant('g','plan','a',k('rur',*av(PLAN),v('goal'))))
    text+=definition('rut',params(BASE),both(quant('g','plan','a',available),quant('f','plan','a',op('y',available,k('ruq',*av(PLAN))))))
    text+=definition('ruu',params(TARGET+[('criterion','h[b] c')]),both(k('rup',v('members'),scope,v('criterion')),k('rut',*av(BASE)),k('rus',*av(TARGET))))
    return text

def build():
    parent=parse((ROOT/MODEL).read_text(encoding='utf-8'));old=parse((ROOT/COUNTS).read_text(encoding='utf-8'))
    lookup={d['name']:d for d in old['declarations']};keep=set();pending={'rcm'}
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    doc=dict(parent,declarations=[d for d in old['declarations'] if d['name'] in keep],statements=[])
    library=parse(format_graph(doc,'compact')+definitions())
    example=deepcopy(library);example['declarations']+=parse((ROOT/OBEDIENCE).read_text(encoding='utf-8'))['declarations']
    text=format_graph(example,'compact')
    for name,t in BASE:
        if name=='goals':continue
        if t.startswith('h['):text+='r js'+name+'['+t[2:t.rfind(']')]+'] '+t[t.rfind(']')+1:].strip()+'.'
        else:text+='r js'+name+'[] '+t+'.'
    for name,args,result in [('jsplan','','a'),('jscriterion','b','c'),('jstarget','d','c'),
        ('jsscope','a a a a d','c'),('jsitems','a a a a d','c'),('jsroles','a a a a d','a'),('jsactions','a a a a d','a'),
        ('jssigns','a a a a d','c'),('jsrequired','a a a a '+DESCRIPTION+' c d','c'),('jsexecution','a a d','c')]:
        text+='r '+name+'['+args+'] '+result+'.'
    text+=definition('jsaction','person a activity a','b point[k jsexecution[v person v activity v point]]','e')
    text+=definition('jsdescriptions','group a person a item a plan a anchor d','r[p jsaction]',DESCRIPTION)
    scope='i[role a][k jsscope[v group v person v role v plan v anchor]]'
    selectors=['i[item a][k js'+name+'[v group v person v item v plan v anchor]]' for name in ('items','roles','actions','descriptions','signs')]
    text+=definition('jsgoals','planner a group a person a plan a anchor d',k('rty',v('planner'),v('person'),v('anchor'),scope,*selectors,'p jsrequired'),'e')
    text+=definition('jsgoal','','b point[k jstarget[v point]]','e')
    refs={n:('p js'+n if t.startswith('h[') else 'k js'+n+'[]') for n,t in BASE};refs.update(plan='k jsplan[]',goal='k jsgoal[]',criterion='p jscriterion')
    scope='i[person a][k jsmembersof[k jsgroup[] v person k jsanchor[]]]'
    text+='q[k rup[k jsmembers[] '+scope+' p jscriterion]].'
    for name,fields in [('ruq',PLAN),('rus',TARGET),('rut',BASE),('ruu',TARGET+[('criterion','h[b] c')])]:text+='q['+k(name,*[refs[n] for n,_ in fields])+'].'
    quoted='r b['+k('ruu',*[refs[n] for n,_ in TARGET+[('criterion','h[b] c')]])+']'
    text+='q[e['+quoted+']['+quoted+']].'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}

def basis():
    return dict(status='finite_group_common_plan_readiness_not_complete_military_concept',
        definitions={
            'rup':'指定範囲を過不足なく列挙した非空・重複なしの構成員列について、その人数が指定した数量基準を満たす。既存rcmを再利用する。',
            'ruq':'同じ計画者・集団・基準文脈で利用可能な一つの計画について、非空で想定結果に含まれる評価対象の全結果で、同じ構成員全員の指定目標が成立する。',
            'rur':'ruqと同じ計画・同じ評価結果の全てで、共通の目標内容も成立する。別計画の成功や別結果の目標を継ぎ合わせない。',
            'rus':'rurを満たす共同計画が少なくとも一つ利用できる。各人が別々の計画で成功できるという分配的能力とは区別する。',
            'rut':'利用可能な計画が少なくとも一つあり、その全てでruqが成立する。成功する一計画だけを選んだことを全計画での適合とみなさない。',
            'ruu':'同じ集団の人数基準rup、利用可能な全計画での構成員の適合rut、共通目的を保証する一計画の存在rusをともに要求する。',
            'jsgoals':'作例の各人・計画・基準文脈の要求記録と役割範囲をrtyへ渡す。要求の出所を同じ計画者に固定し、記録の網羅性と履行を同じ評価結果で調べる。'},
        parameters={
            'membersof':'集団・人・基準文脈に関する構成員の範囲。列の長さはこの範囲を完全列挙している場合だけ人数として使う。',
            'criterion':'人数を受け取る文脈上の評価基準。原文が具体的な人数や普遍的な閾値を指定したとはしない。',
            'available/outcomes/selected':'同じ計画者・集団・計画・基準文脈に対する利用可能性、想定結果、評価対象。計画の有効な指揮権や現実の因果機構の説明は別に必要。',
            'goals':'同じ計画者・集団・人・計画・基準文脈に結び付いた構成員の目標内容。作例では要求への適合を使うが、一般関数の型だけでそれを強制しない。',
            'goal':'同じ結果で実現する共通目的。公的平穏の語義や社会的な保証の全条件を入力名で代用した完成表現とは扱わない。'},
        limitations=[
            '集団的な実行可能性と、各人の個別の可能性を分ける基盤であり、軍隊・軍事的統制・国家・公的平穏の概念を完成させたものではない。',
            'rutは指定した全利用可能計画と評価範囲での適合という強い操作的条件。訓練、規律の維持、服従の意図、例外を許す信頼性や頻度は別途必要。',
            '要求の網羅性は全行為記述への量化として残す。有限評価器は全域を拒否し、少数記述に限定した診断を全域の証明とはしない。',
            '目標の共同成立は指定した想定結果での条件であり、同時成立だけから実際の因果的な保証や、計画者の正当な統制権を導かない。',
            '構成員の同定、役割範囲、計画一覧と評価範囲、数量基準そのものの妥当性は別の説明が必要。空の構成員・空の評価範囲・計画の不存在は成功と扱わない。',
            '本文の啓蒙、影への恐れ、軍隊、公的平穏、限定された発話可能性への接続は残り、新たな原文対応範囲は追加しない。'])

def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))

if __name__=='__main__':main()
