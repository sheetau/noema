"""Compositional time windows, event stages and explicit temporal anchors."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed

LIBRARY='examples/v016/shared-time-v1.noema'
BASIS='data/shared-time-basis-v1.json'
PERSISTENCE='examples/v014/persistence.noema'
TRANSITIONS='examples/v014/transitions.noema'
OLD_NAMES={'ta':'chronology','tb':'timewindow','tc':'holdsall','tg':'processextent','th':'becomes'}
S='situation'; I='individual'; T='truth'
WINDOW=function_sort([S],T)
ORDER=function_sort([S,S],T)
EVENTS=function_sort([I],T)
TRACE=function_sort([I,S],T)


def q(kind,name,sort,body): return dict(kind=kind,variable=name,sort=sort,body=body)
def lam(name,sort,body): return dict(kind='lambda',parameters=[dict(name=name,sort=sort)],body=body)
def allof(*values):
    result=values[-1]
    for value in reversed(values[:-1]): result=op('and',value,result)
    return result
def le(a,b): return op('or',op('equal',v(a),v(b)),app('order',v(a),v(b)))
def trace(event='event'): return lam('point',S,app('trace',v(event),v('point')))
def valid(window): return call('timewindow',v('history'),window,v('order'))
def definition(name,parameters,body):
    return dict(kind='definition',name=name,parameters=[dict(name=n,sort=t) for n,t in parameters],result=T,body=body)


@lru_cache(maxsize=1)
def composed():
    declarations=[]
    for path,names in ((PERSISTENCE,('ta','tb','tc')),(TRANSITIONS,('tg','th'))):
        source=parse((ROOT/path).read_text(encoding='utf-8'))
        declarations.extend(renamed(d,OLD_NAMES) for d in source['declarations'] if d['name'] in names)
    base=[('history',WINDOW),('order',ORDER)]
    params=base+[('window',WINDOW),('anchor',S)]
    for name,body in (
        ('windowbefore',q('forall','point',S,op('implies',app('window',v('point')),app('order',v('point'),v('anchor'))))),
        ('windowafter',q('forall','point',S,op('implies',app('window',v('point')),app('order',v('anchor'),v('point'))))),
        ('windowat',app('window',v('anchor')))):
        declarations.append(definition(name,params,allof(valid(v('window')),app('history',v('anchor')),body)))
    params=base+[('left',WINDOW),('right',WINDOW)]
    for name,body in (
        ('windowoverlap',q('exists','point',S,op('and',app('left',v('point')),app('right',v('point'))))),
        ('windowwithin',q('forall','point',S,op('implies',app('left',v('point')),app('right',v('point')))))):
        declarations.append(definition(name,params,allof(valid(v('left')),valid(v('right')),body)))
    params=base+[('event',I),('trace',TRACE),('anchor',S),('culmination',TRACE)]
    endpoint=q('exists','finish',S,allof(app('trace',v('event'),v('finish')),
        app('culmination',v('event'),v('finish')),le('finish','anchor'),
        q('forall','point',S,op('implies',app('trace',v('event'),v('point')),le('point','finish')))))
    completed=q('exists','finish',S,allof(app('history',v('finish')),
        app('culmination',v('event'),v('finish')),le('finish','anchor')))
    underway=allof(app('trace',v('event'),v('anchor')),
        q('exists','earlier',S,op('and',app('trace',v('event'),v('earlier')),app('order',v('earlier'),v('anchor')))),
        op('not',completed))
    for name,body in (('eventunderway',underway),('eventcompleteby',endpoint)):
        declarations.append(definition(name,params,allof(valid(trace()),app('history',v('anchor')),body)))
    params=base+[('window',WINDOW),('events',EVENTS),('trace',TRACE)]
    def matches(e):
        return op('and',app('events',v(e)),call('windowoverlap',v('history'),v('order'),trace(e),v('window')))
    once=q('exists','event',I,op('and',matches('event'),q('forall','other',I,
        op('implies',matches('other'),op('equal',v('event'),v('other'))))))
    checked=q('forall','event',I,op('implies',app('events',v('event')),valid(trace())))
    declarations.append(definition('eventonce',params,op('and',checked,once)))
    params=base+[('periods',EVENTS),('windows',TRACE),('events',EVENTS),('trace',TRACE)]
    window=lam('point',S,app('windows',v('period'),v('point')))
    every=op('and',q('exists','period',I,app('periods',v('period'))),
        q('forall','period',I,op('implies',app('periods',v('period')),q('exists','event',I,
            op('and',app('events',v('event')),call('windowwithin',v('history'),v('order'),trace(),window))))))
    declarations.append(definition('eventevery',params,every))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[]))


MEANINGS={
 'chronology':'履歴が空でなく、その履歴内で先行関係が厳密な全順序をなす。',
 'timewindow':'空でない順序付き履歴内の、空でない凸な部分範囲。途中の履歴点を除かない。',
 'holdsall':'空でない範囲の全状況で指定した内容が成立する。範囲の時間的整合性は別途timewindowで確認する。',
 'processextent':'同じ順序付き履歴の厳密に前後する二状況を、指定した実際の変化過程が結ぶ。',
 'becomes':'processextentを満たす同じ過程の前で内容が偽、後で真である。因果機構は含意しない。',
 'windowbefore':'整合した範囲の全点が同じ履歴内の基準時より厳密に前である。',
 'windowafter':'整合した範囲の全点が同じ履歴内の基準時より厳密に後である。',
 'windowat':'同じ履歴内の基準時が整合した範囲に含まれる。',
 'windowoverlap':'二つの整合した範囲に共通する状況が少なくとも一つある。',
 'windowwithin':'第1の整合した範囲の全点が第2の整合した範囲に含まれる。',
 'eventunderway':'同じ出来事の整合した進行範囲が基準時を含み、より前の進行点があり、基準時までに指定の完了条件が成立していない。将来の完了を要求しない。',
 'eventcompleteby':'同じ出来事の整合した進行範囲に完了点があり、それより後の進行点がなく、完了点は基準時以前である。',
 'eventonce':'全該当出来事の進行範囲が整合し、そのうち指定範囲と重なる出来事がちょうど一つ存在する。',
 'eventevery':'対象期間が空でなく、各期間に全体が含まれる整合した該当出来事が少なくとも一つある。期間も整合した時間範囲である。'}
ROLES={
 'chronology':['history','order'],'timewindow':['history','window','order'],'holdsall':['window','content'],
 'processextent':['history','order','event','earlier','later','process'],
 'becomes':['history','order','event','earlier','later','process','content']}
ROLES.update({name:['history','order','window','anchor'] for name in ('windowbefore','windowafter','windowat')})
ROLES.update({name:['history','order','left','right'] for name in ('windowoverlap','windowwithin')})
ROLES.update({name:['history','order','event','trace','anchor','culmination'] for name in ('eventunderway','eventcompleteby')})
ROLES.update(eventonce=['history','order','window','events','trace'],
             eventevery=['history','order','periods','windows','events','trace'])
INTERPRETATION={
 'history':'同じ時間的履歴に属する状況の全範囲。観測された点だけへ無断で縮めない。',
 'order':'その履歴での厳密な先行。異なる履歴の可能性や評価上の順位と混同しない。',
 'window':'評価する時間範囲。境界を含むかと粒度を指定する。',
 'left':'第1時間範囲。','right':'第2時間範囲。',
 'anchor':'判定の基準時。発話時・報告内の現在を呼出側で区別する。',
 'content':'各状況で評価する同じ内容。','event':'対象となる同一の出来事。',
 'earlier':'過程の前状況。','later':'過程の後状況。',
 'process':'出来事と実際の前後状況の対応。観察者や別人の過程を混ぜない。',
 'trace':'出来事と、その出来事が実際に進行する状況の対応。未知を不在に置き換えない。',
 'culmination':'同じ出来事が指定の目的・課題の完了条件に達した状況。停止や観測の欠落だけでは成立しない。',
 'events':'話題の活動・主体・対象等に該当する出来事。主体等の対応をここで明示する。',
 'periods':'反復を評価する期間の全範囲。','windows':'各期間と、その期間に含まれる状況の対応。'}


def basis():
    declarations=composed()['declarations']
    return dict(status='shared_explicit_temporal_readings',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=n,sort=p['sort'],interpretation=INTERPRETATION[n])
            for n,p in zip(ROLES.get(d['name'],[p['name'] for p in d['parameters']]),d['parameters'])],result=d['result'])
            for d in declarations},
        source_renamings={PERSISTENCE:{k:v for k,v in OLD_NAMES.items() if k in ('ta','tb','tc')},
                          TRANSITIONS:{k:v for k,v in OLD_NAMES.items() if k in ('tg','th')}},
        limitations=['有限モデルは連続時間の証明ではない。','進行・完了・一度・毎回の明示した読みを提供し、全用法の自動判定はしない。',
                    '履歴、出来事の境界、完了条件、主体・対象、期間の選定を解釈入力として保持する。',
                    'Native共通定義の円文字への語彙登録と第三者読解は未完。'])


def prepare():
    for path,value in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=value: raise ValueError('Published content differs: '+path)
        if not target.exists(): target.write_text(value,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
