"""Describe opportunities for every selected faculty without asserting growth."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_assessed_barriers import ROOT,SOURCE as PARENT,STATE,mask,fixed,params,av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_restricted_utterance import primitive
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/faculty-opportunities.noema'
SOURCE='examples/v016/kant-faculty-opportunities.noema'
CORE='examples/v016/faculty-opportunities-core.noema'
BASIS='data/faculty-opportunities-basis-v1.json'
GROWTH=[('person','a'),('activities','h[a] c'),('start','d'),('end','d'),('earlier','h[d d] c'),
    ('assessed','h[a a d] c'),('capable','h[a a d] c')]
OPPORTUNITY=[('person','a'),('faculties','h[a] c'),('goals','h[a] e'),('start','d'),('available','h[a a d] c'),
    ('prospects','h[a a d d] c'),('evaluated','h[a a d d] c')]


def definitions():
    old=app(v('capable'),v('person'),v('activity'),v('start'))
    new=app(v('capable'),v('person'),v('activity'),v('end'))
    scoped=app(v('activities'),v('activity'))
    valid=both(app(v('assessed'),v('person'),v('activity'),v('start')),
        app(v('assessed'),v('person'),v('activity'),v('end')),op('y',old,new))
    text=definition('rwy',params(GROWTH),both(app(v('earlier'),v('start'),v('end')),
        quant('f','activity','a',op('y',scoped,valid)),quant('g','activity','a',both(scoped,op('u',old),new))))
    nonempty=quant('g','faculty','a',app(v('faculties'),v('faculty')))
    achievement=k('xd',v('person'),app(v('goals'),v('faculty')),v('start'),*[v(n) for n in ('available','prospects','evaluated')])
    text+=definition('rwz',params(OPPORTUNITY),both(nonempty,quant('f','faculty','a',op('y',app(v('faculties'),v('faculty')),achievement))))
    all_goals='b result['+quant('f','faculty','a',op('y',app(v('faculties'),v('faculty')),op('t',app(v('goals'),v('faculty')),v('result'))))+']'
    text+=definition('rw2',params(OPPORTUNITY),both(nonempty,k('xd',v('person'),all_goals,v('start'),*[v(n) for n in ('available','prospects','evaluated')])))
    return text


def additions():
    text=''.join(primitive('iae'+n,t) for n,t in [('faculties','h[a a d] c'),('tasks','h[a a a d] c'),('earlier','h[d d] c')])
    text+='r iaereport[a a i d[e] a d] c.'
    for name,base in [('assessed','xf'),('capable','xd')]:
        text+=definition('iae'+name,'person a activity a point d',k(base,v('person'),k('iacgoal',v('person'),v('activity')),
            v('point'),'p iacavailable','p iacprospects','p iacevaluated'))
    # tasks takes person, faculty, activity, anchor; freeze it before evaluating outcomes.
    scope='i[activity a][k iaetasks[v person v faculty v activity v anchor]]'
    text+=definition('iaedevelopment','person a faculty a anchor d start d','b end['+k('rwy',v('person'),scope,v('start'),v('end'),
        'p iaeearlier','p iaeassessed','p iaecapable')+']','e')
    faculties='i[faculty a][k iaefaculties[v person v faculty v anchor]]'
    goals='i[faculty a][k iaedevelopment[v person v faculty v anchor v start]]'
    args=[v('person'),faculties,goals,v('start'),'p iacavailable','p iacprospects','p iacevaluated']
    for name,base in [('individual','rwz'),('together','rw2')]:
        text+=definition('iae'+name,'person a anchor d start d',k(base,*args))
    task_scope=quant('f','faculty','a',op('y',k('iaefaculties',v('person'),v('faculty'),v('anchor')),
        quant('f','activity','a',op('y',k('iaetasks',v('person'),v('faculty'),v('activity'),v('anchor')),
            k('iacmentalactivities',v('person'),v('activity'))))))
    text+=definition('iaeopportunities','anchor d start d',both(quant('g','person','a',k('iacpeople',v('person'))),
        quant('f','person','a',op('y',k('iacpeople',v('person')),both(task_scope,k('iaeindividual',v('person'),v('anchor'),v('start')))))))
    off_goal='i[state '+STATE+'][k iaeopportunities[v anchor k iachigher[k iadview[v state]]]]'
    text+=definition('iaeroom','anchor d',both(k('iadaligned',v('anchor')),
        k('iaeopportunities',v('anchor'),k('iaclower',v('anchor'))),
        k('rw',k('iadvariables'),'p iadequations',mask(k('iadfactor')),fixed(False),off_goal)))
    text+=definition('iaecontrast','','b anchor['+both(op('t',k('iadcontrast'),v('anchor')),k('iaeroom',v('anchor')))+']','e')
    text+=definition('iaeattribution','',k('iaereport',k('iacnode'),k('wa'),'r d[k iaecontrast[]]',k('iacscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['declarations']=closure(parent,['xd']);lib['statements']=[]
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iaeattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='partial_all_faculties_development_opportunity',parent=PARENT,document=SOURCE,
        definitions={
            'rwy':'同じ本人・活動範囲の前後を比較する。前後とも各活動の能力評価が成立し、時間順序があり、以前の能力を失わず、新たに達成できる活動がある。',
            'rwz':'選択した能力範囲が非空で、各能力の目標に達するxdの方法がある。能力ごとに別の方法でよい。',
            'rw2':'非空の同じ能力範囲の全目標を、一つの方法の同じ評価結果で達成できる。rwzより強い比較用構成で、本文には要求しない。',
            'iaedevelopment':'基準視点で固定した同じ本人・能力の活動範囲について、指定の開始状況からrwyが成立する目標内容を作る。',
            'iaeopportunities':'前段の人々が非空で、各人の全選択能力に発展目標への方法があり、活動が前段の精神的活動範囲に含まれる。',
            'iaeroom':'同じ制度対応iadalignedを保持し、現在の低い側と、要因を外した非空の全解でiaeopportunitiesが成立する。',
            'iaecontrast':'前段の見かけの利益と現実の障壁に、低い側の発展機会を同じ基準視点で連言する。'},
        inputs={
            'faculties':'その人に属し、議論で対象となる精神的能力の全範囲。開始後の成功に合わせて選別せず、基準視点で固定する。',
            'tasks':'本人のその能力が発展する範囲に属する活動。基準視点で固定し、他の能力の活動へ成功を移さない。',
            'earlier':'開始状況から結果状況への時間的な先行。制度間の比較順序や、単なる識別子の違いとは区別する。'},
        limitations=[
            '発展を、同じ能力に属する達成可能活動の真包含拡大とする候補。質、深さ、熟練、能力の強度の全側面は扱わない。',
            '民衆の精神を各人の能力機会へ分配する強い読みであり、集団的精神の独自の意味を確定しない。能力・活動範囲の適合やその所有の基礎説明は残る。',
            '各能力に別々の発展方法があればよく、全能力の発展結果を一つの方法で実現することは本文の条件にしない。rw2も各行為が同時に起こることを意味しない。現在すでに発展したことや、実際に方法を選び実行したことも主張しない。',
            '低い側を前段の包含順序の相手として保持する。一度合いの数値差や最小差を原文へ補わない。',
            '要因を外した全解で発展機会があるという明示的なモデル内の強い条件。確率的な傾向、自由の程度の語義、制度と因果モデルの妥当性は未完。',
            '前段のdochと今回のhingegenの談話上の対比、後続の自然と成長の比喩、段落全体の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
