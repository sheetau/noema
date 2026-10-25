"""Unevaluated reading alternatives, licensed completion and explicit revision."""
from functools import lru_cache
import json
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_time import allof
from scripts.shared_reference import truth,lam,definition

I='individual';S='situation';T='truth';U='message'
D=description_sort(U);DI=description_sort(I);DS=description_sort(S)
READINGS=sequence_sort(D)
TEMPLATE=description_sort(function_sort([I,I,S],U))
CHANGE=function_sort([I,I,D,I,T],T)
COVERAGE=function_sort([I,I,READINGS,T,I],T)
LICENSE=function_sort([I,I,I,I,TEMPLATE,DI,DI,DS],T)
LIBRARY='examples/v016/shared-readings-v1.noema'
BASIS='data/shared-readings-basis-v1.json'


def fold(sequence,initial,parameters,body):
    return dict(kind='fold',sequence=sequence,initial=initial,step=lam(parameters,body))
def every(sequence,variable,body):
    return fold(sequence,truth(True),[('accepted',T),(variable,D)],op('and',v('accepted'),body))
def num(n):return dict(kind='number',numerator=n,denominator=1)
def empty(sequence):return op('equal',dict(kind='length',sequence=sequence),num(0))
def apply_description(template,subject,related,anchor):
    return dict(kind='quoted_application',function=template,arguments=[subject,related,anchor])


@lru_cache(maxsize=1)
def raw():
    defs=[]
    def add(name,params,result,body):defs.append(definition(name,params,result,body))
    add('readingcontains',[('readings',READINGS),('reading',D)],T,
        fold(v('readings'),truth(False),[('found',T),('item',D)],op('or',v('found'),op('equal',v('item'),v('reading')))))
    add('readingsempty',[('readings',READINGS)],T,empty(v('readings')))
    different=fold(v('readings'),truth(False),[('foundother',T),('other',D)],
        op('or',v('foundother'),op('not',op('equal',v('item'),v('other')))))
    add('readingsambiguous',[('readings',READINGS)],T,
        fold(v('readings'),truth(False),[('found',T),('item',D)],op('or',v('found'),different)))
    add('readingssingle',[('readings',READINGS)],T,
        op('and',op('not',empty(v('readings'))),op('not',call('readingsambiguous',v('readings')))))
    for name,condition in (('readingsabsence',empty(v('readings'))),('readingsresolved',call('readingssingle',v('readings')))):
        add(name,[('readings',READINGS),('complete',T)],T,op('and',v('complete'),condition))
    params=[('left',READINGS),('right',READINGS)]
    add('readingssubset',params,T,every(v('left'),'item',call('readingcontains',v('right'),v('item'))))
    same=op('and',call('readingssubset',v('left'),v('right')),call('readingssubset',v('right'),v('left')))
    add('readingssame',params,T,same)
    add('readingnarrowing',[('before',READINGS),('after',READINGS)],T,
        op('and',op('not',empty(v('after'))),call('readingssubset',v('after'),v('before'))))
    params=[('source',I),('context',I),('before',READINGS),('beforeclosed',T),('after',READINGS),('afterclosed',T),
            ('reason',I),('change',CHANGE),('coverage',COVERAGE)]
    unchanged=op('and',call('readingssame',v('before'),v('after')),op('equal',v('beforeclosed'),v('afterclosed')))
    removed=every(v('before'),'item',op('implies',op('not',call('readingcontains',v('after'),v('item'))),
        app('change',v('source'),v('context'),v('item'),v('reason'),truth(False))))
    added=every(v('after'),'item',op('implies',op('not',call('readingcontains',v('before'),v('item'))),
        app('change',v('source'),v('context'),v('item'),v('reason'),truth(True))))
    cover=op('implies',op('or',v('afterclosed'),op('not',op('equal',v('beforeclosed'),v('afterclosed')))),
        app('coverage',v('source'),v('context'),v('after'),v('afterclosed'),v('reason')))
    add('readingrevision',params,T,allof(op('not',unchanged),removed,added,cover))
    params=[('priorsource',I),('priorcontext',I),('priorafter',READINGS),('priorclosed',T),
            ('nextsource',I),('nextcontext',I),('nextbefore',READINGS),('nextclosed',T)]
    add('readinglinked',params,T,allof(op('equal',v('priorsource'),v('nextsource')),
        op('equal',v('priorcontext'),v('nextcontext')),call('readingssame',v('priorafter'),v('nextbefore')),
        op('equal',v('priorclosed'),v('nextclosed'))))
    params=[('template',TEMPLATE),('subject',DI),('related',DI),('anchor',DS)]
    add('ellipsisresult',params,D,apply_description(*(v(n) for n,t in params)))
    add('ellipsisvalid',params+[('result',D)],T,op('equal',v('result'),call('ellipsisresult',*(v(n) for n,t in params))))
    licensing=[('source',I),('target',I),('context',I),('reason',I)]+params+[('result',D),('license',LICENSE)]
    add('ellipsislicensed',licensing,T,allof(op('not',op('equal',v('source'),v('target'))),
        call('ellipsisvalid',*(v(n) for n,t in params),v('result')),
        app('license',*(v(n) for n,t in licensing[:8]))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'readingcontains':'候補列に同じ構文の発話記述がある。内容を実行しない。',
 'readingsempty':'候補列が空である。列挙の完了や内容の偽は含意しない。',
 'readingsambiguous':'候補列に異なる発話記述が二つ以上ある。同じ記述の重複を数えない。',
 'readingssingle':'候補列に一種類だけの発話記述がある。列挙の完了は別条件。',
 'readingsabsence':'列挙が完了しており候補がない。内容の否定ではない。',
 'readingsresolved':'列挙が完了し、候補が一種類である。内容の真理を含意しない。',
 'readingssubset':'左の候補が全て右に含まれる。空の左も許す。',
 'readingssame':'左右の候補が相互に含まれる。順序と重複を候補集合の違いとしない。',
 'readingnarrowing':'変更後の候補が非空で全て変更前に含まれる。同じ集合も許す。',
 'readingrevision':'候補または完了状態が変化し、同じ出典・文脈・根拠で各追加/除外が許可され、必要な完了状態の根拠もある。',
 'readinglinked':'二更新の出典・文脈が同じで、前更新の後状態と次更新の前状態の候補集合と完了状態が等しい。',
 'ellipsisresult':'二つの個体と基準状況を受け取る閉じた発話ひな形の記述に、指定した三つの引数記述を適用する。',
 'ellipsisvalid':'与えた補完結果の記述が、同じひな形と三引数から構成した記述と厳密に一致する。',
 'ellipsislicensed':'異なる元箇所/補完先について、構成結果が一致し、同じ文脈・根拠・ひな形・引数の補完が許可される。'}
ROLES={
 'readings':'現在列挙した発話記述の列。内容の論理和ではない。','reading':'調べる一つの発話記述。',
 'complete':'候補の列挙がこの文脈と解釈基準で尽くされたという判断。根拠を保持する。',
 'left':'包含の左側の候補列。','right':'包含の右側の候補列。',
 'before':'変更前の候補列。','after':'変更後の候補列。','beforeclosed':'変更前の列挙完了状態。','afterclosed':'変更後の列挙完了状態。',
 'source':'解釈対象の出典箇所、または省略の先行箇所。','context':'同じ解釈文脈。','reason':'変更または補完を認める理由・証拠記録。',
 'change':'出典・文脈・候補記述・根拠・追加/除外の判断。真の極性が追加、偽が除外。',
 'coverage':'出典・文脈・変更後候補列・完了状態・根拠の整合する判断。列挙の十分性を自動証明しない。',
 'priorsource':'前更新の出典箇所。','priorcontext':'前更新の文脈。','priorafter':'前更新の変更後候補列。','priorclosed':'前更新の変更後完了状態。',
 'nextsource':'次更新の出典箇所。','nextcontext':'次更新の文脈。','nextbefore':'次更新の変更前候補列。','nextclosed':'次更新の変更前完了状態。',
 'template':'主体・関係項・基準状況を受け取る閉じた発話関数の記述。','subject':'補完後の主体の閉じた個体記述。',
 'related':'所有者等の関係項の閉じた個体記述。','anchor':'補完後の基準状況の閉じた記述。',
 'result':'補完後の発話の閉じた記述。','target':'省略を補う箇所。',
 'license':'先行箇所・補完先・文脈・根拠・ひな形・三引数に対する許可判断。構文一致と区別する。'}


def basis():
    return dict(status='shared_completion_and_unresolved_readings',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']])
            for p in d['parameters']],result=d['result']) for d in raw()['declarations']},
        design_sources=['docs/quotation-construction-v1.md','docs/shared-quotation-v1.md','docs/spec-v014.md'],
        limitations=['補完候補や省略の許可、候補列挙の完了、変更根拠の十分性は自動推測しない。',
          '構文上異なる同義表現を自動同一化しない。候補保持と内容の真理を区別する。',
          '共通の補完関数は個体二つと状況一つのひな形。その他の型には既存の可変長記述適用を使う。',
          '円文字の共有語彙登録と第三者読解は未完。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published readings module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
