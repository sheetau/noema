"""Compose an armed-operation capability without asserting present fighting."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_assigned_formation import SOURCE as PARENT,QUALIFICATION

LIBRARY='examples/v016/armed-readiness.noema'
EXAMPLE='examples/v016/armed-readiness-example.noema'
SOURCE='examples/v016/kant-armed-readiness.noema'
CORE='examples/v016/armed-readiness-core.noema'
BASIS='data/armed-readiness-basis-v1.json'
ABILITY='examples/v013/contextual-ability.noema'
TOOL=[('restricted','h[a a d] c'),('toolmethods','h[a a a a d] c'),
      ('tooloutcomes','h[a a a a d d] c'),('toolselected','h[a a a a d d] c')]
ACT=[('occurs','h[a d] c'),('commanded','h[a a d] c')]+[(n,'h[a d] a') for n in ('opponentof','actorof','targetof','toolof')]+[
    ('members','h[a a d] c'),('opposes','h[a a a d] c'),('instrument','h[a d] c'),
    ('used','h[a a a d] c'),('against','h[a a a d] c'),('onbehalf','h[a a d] c')]
UNIT=[('unitmethods','h[a a a d] c'),('unitoutcomes','h[a a a d d] c'),('unitselected','h[a a a d d] c')]
RELATIONS=ACT+TOOL+UNIT
BASE=[('group','a'),('community','a'),('point','d')]


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    bound=[]
    for name in ('toolmethods','tooloutcomes','toolselected'):
        fields='operator a method a start d'+(' end d' if name!='toolmethods' else '')
        args=[v('operator'),v('tool'),v('target'),v('method'),v('start')]+([v('end')] if name!='toolmethods' else [])
        bound.append('i['+fields+']['+app(v(name),*args)+']')
    text=definition('rwc','operator a tool a target a anchor d '+params(TOOL),
        k('xd',v('operator'),'b result['+app(v('restricted'),v('tool'),v('target'),v('result'))+']',v('anchor'),*bound))
    selected={n:app(v(n+'of'),v('event'),v('point')) for n in ('opponent','actor','target','tool')}
    actor,target,tool,opponent=(selected[n] for n in ('actor','target','tool','opponent'))
    body=both(app(v('occurs'),v('event'),v('point')),app(v('commanded'),v('event'),v('group'),v('point')),
        op('u',op('e',v('group'),opponent)),op('u',op('e',actor,target)),
        app(v('members'),v('group'),actor,v('point')),app(v('members'),opponent,target,v('point')),
        app(v('opposes'),v('group'),opponent,v('community'),v('point')),
        app(v('instrument'),tool,v('point')),app(v('used'),v('event'),actor,tool,v('point')),
        app(v('against'),v('event'),actor,target,v('point')),app(v('onbehalf'),v('event'),v('community'),v('point')),
        k('rwc',actor,tool,target,v('point'),*av(TOOL)))
    text+=definition('rwd',params([('event','a')]+BASE+ACT+TOOL),body)
    text+=definition('rwe',params(BASE+ACT+TOOL),quant('g','event','a',k('rwd',v('event'),*av(BASE+ACT+TOOL))))
    bound=[]
    for name in ('unitmethods','unitoutcomes','unitselected'):
        fields='unit a method a start d'+(' end d' if name!='unitmethods' else '')
        args=[v('unit'),v('community'),v('method'),v('start')]+([v('end')] if name!='unitmethods' else [])
        bound.append('i['+fields+']['+app(v(name),*args)+']')
    goal='b point['+k('rwe',*av(BASE+ACT+TOOL))+']'
    text+=definition('rwf',params([('group','a'),('community','a'),('anchor','d')]+RELATIONS),
        k('xd',v('group'),goal,v('anchor'),*bound))
    return text


def additions():
    text=''
    for name,sort in RELATIONS:text+='r hzz'+name+'['+sort[2:sort.rfind(']')]+'] '+sort[sort.rfind(']')+1:].strip()+'.'
    text+=definition('hzzmission','group a community a','b anchor[k rwf[v group v community v anchor '+
        ' '.join('p hzz'+n for n,t in RELATIONS)+']]','e')
    scope='c[k hzxmembersof[v actor v group v anchor]][v group v person v anchor]'
    text+=definition('hzzagreement','actor a group a anchor d',
        'f person a[z[k hzzmembers[v group v person v anchor]]['+scope+']]')
    text+=definition('hzzqualified','remaining '+QUALIFICATION+' actor a group a community a anchor d',both(
        k('hzzagreement',*map(v,('actor','group','anchor'))),
        't[k hzzmission[v group v community]][v anchor]',app(v('remaining'),*map(v,('actor','group','community','anchor')))))
    text+=definition('hzzonly','remaining '+QUALIFICATION+' anchor d',
        k('hzyonly','r[p hzzmission]','i[actor a group a community a point d]['+k('hzzqualified',*map(v,('remaining','actor','group','community','point')))+']',v('anchor')))
    text+='r hzzannotation[a a i c[h['+QUALIFICATION+' d] c] a d] c.'
    text+=definition('hzzattribution','',k('hzzannotation','k hztnode[]','k wa[]','r c[p hzzonly]','k hztscope[]','k wh[]'))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    library=deepcopy(parent);library['statements']=[];library['declarations']=closure(parent,['xd'])
    library=parse(format_graph(library,'compact')+definitions())
    text=format_graph(library,'compact')+'r jqgroup[] a.r jqcommunity[] a.r jqanchor[] d.r jqevent[] a.'
    for name,sort in RELATIONS:text+='r jq'+name+'['+sort[2:sort.rfind(']')]+'] '+sort[sort.rfind(']')+1:].strip()+'.'
    refs={n:'p jq'+n for n,t in RELATIONS};refs.update(group='k jqgroup[]',community='k jqcommunity[]',point='k jqanchor[]',anchor='k jqanchor[]',event='k jqevent[]')
    fields=[('group','a'),('community','a'),('anchor','d')]+RELATIONS
    ready=k('rwf',*[refs[n] for n,t in fields])
    questions=[ready,k('rwe',*[refs[n] for n,t in BASE+ACT+TOOL]),'e[r['+ready+']][r['+ready+']]']
    example=parse(text+''.join('q['+q+'].' for q in questions))
    doc=deepcopy(parent);statements=doc['statements'];doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k hzzattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in [(LIBRARY,library),(EXAMPLE,example),(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='explicit_armed_readiness_candidate_not_complete_military_identity',definitions={
        'rwc':'同じ操作者・道具・対象について、道具の物理的作用により対象の身体的行為能力が制約される結果を実現する方法がある。既存xdで利用可能性、非空の評価結果、想定結果への包含、全評価結果の達成を要求する。',
        'rwd':'同じ出来事が同じ集団の指揮下で起き、構成員が別の対立集団の構成員へ道具を向けて使用し、その道具による身体的制約が可能である。出来事の対象共同体への帰属も照合する。現在の負傷や制約の成立は要求しない。',
        'rwe':'指定集団・共同体・状況についてrwdを満たす出来事が存在する。',
        'rwf':'同じ集団・対象共同体の方法でrweを達成できる。平時の基準状況でrweが成立していることは要求しない。',
        'hzzmission':'rwfを集団・対象共同体から得る内容にし、任務記述として使う。',
        'hzzagreement':'基準状況で、任務の構成員と前段の保護条件の構成員が同じ集団について一致する。将来まで人員が固定されることは要求しない。',
        'hzzqualified':'同じ候補者・集団・共同体・基準文脈について構成員一致、実際の準備能力、残余条件を要求する。任務が割り当てられていることだけで能力を補わない。',
        'hzzonly':'前段hzyonlyのmissionにhzzmissionの記述を渡し、残余条件にはhzzqualifiedを使う。',
        'hzzattribution':'この候補の記述を帰属し、戦闘の発生や正当性は断言しない。'},
        parameters={
            'restricted':'道具の物理的作用により、指定した対象の身体的行為能力が制約されている関係。単なる命令や制度上の禁止ではない。物理・身体・因果の詳細な基礎付けは入力として残る。',
            'toolmethods/tooloutcomes/toolselected':'操作者・道具・対象・方法・基準状況を共有する利用可能性、想定結果、評価結果。道具が原因と関係なく対象が動けない状況を成功としないというrestrictedの意味規約を伴う。',
            'actorof/targetof/toolof/opponentof':'出来事と状況に対応する一つの使用行為の担当者・対象者・道具・相手集団。複数人・複数道具の使用は行為を分けて記述する。',
            'instrument':'身体の一部そのものではなく、外的な物理的手段として使う道具。ここだけで武器と分類しない。',
            'opposes':'同じ対象共同体に関して両集団の目的・要求が対立する関係。どちらが正当か、防衛か侵攻かは追加しない。',
            'occurs/commanded/used/against/onbehalf':'実際の出来事、集団の指揮への帰属、本人による同じ道具の使用、同じ対象者に向けた使用、共同体のための活動という帰属を別々に結ぶ。帰属だけで共同体への実際の利益や合法性を要求しない。',
            'unitmethods/unitoutcomes/unitselected':'同じ集団・対象共同体の方法と評価結果。各人が別々に成功できるという分配的能力とは区別する。'},
        unresolved=[
            '軍事的任務を武力行使の準備能力で捉える明示的な候補であり、Heerの必要十分条件や唯一の歴史的語義ではない。武装警察等との制度上の境界は残る。',
            '道具・身体的制約・対立・指揮帰属などの入力関係の基礎付け、武器体系や戦闘一般の説明は未完。',
            'rwdは有効な身体的制約を行える者が道具を向けて使用するという操作的条件。単なる武器保有とは異なるが、威嚇・遠隔行為・多主体行動の全てを網羅してはいない。',
            '準備能力は既存xdの明示した評価結果に相対的な条件である。時間上の即応性や全緊急事態への対応は要求しない。未知の利用可能性や評価結果を成功として補わない。',
            '原文の軍隊・公的平穏の全体、任務割当・保護・発言能力を合わせた統合解釈と原文単位全体の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
