"""Allow gaps between use occasions while preserving causal effects over full histories."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_limits import v,call,app,op,both,quant,lam,definition

PARENT='examples/v016/kant-shared-fetters-scope.noema'
PARENT_BASIS='data/shared-fetters-scope-basis-v1.json'
FULL='examples/v016/kant-occasional-continuation.noema'
CORE='examples/v016/occasional-continuation-core.noema'
LIBRARY='examples/v016/occasions-and-delayed-effects.noema'
BASIS='data/occasional-continuation-basis-v1.json'
ANNOTATIONS='data/occasional-continuation-identifiers-v1.json'
MEANINGS={
    'r2g4':'指定された履歴の基準以降の全点について、適用局面なら使用内容が成立するという候補条件。局面でない時点での行為は要求しない。履歴・順序・基準と開始局面の正当性は呼出側r2g5で全候補について別に検査する。',
    'r2g5':'全比較候補の履歴が基準を含む厳密全順序を持ち、基準が適用局面であることを要求する。以降の全適用局面で使う候補が少なくとも一つあり、そのような全候補では基準以降の全点で、同じ候補と点の結果が成立する。適用局面だけへ結果範囲を切り縮めない。',
    'r2g6':'正当な同じ履歴の現在で結果内容が成立し、その履歴の現在以前に生起した同じ行為が現在の結果に因果的に関わる。原因行為の現在の生起は要求せず、未来や別履歴の行為、単なる時間的先行や結果の共存を根拠にしない。',
    'r2g7':'同じ対象・本人・基準・候補履歴で、現在以前のr2evの使用活動そのものが現在の同じ本人の未成熟bfを生じさせ、bfも成立する。行為が今起きない点でも、その行為の因果的関与が現在に残る場合を扱う。',
    'r2ga':'基準で規定または定型表現r2fhに属する対象について、同じ本人が以後の適用局面で吟味せず使う比較候補では、同じ全履歴の将来各点にr2g7の因果的結果が続く。局面のない点を履歴から除外しない。',
    'r2gb':'規定と定型表現を種類ごとに一般化する既存r2fuの応答を、局面ごとの使用と全将来の結果r2g8へ更新する。同じ事例の対象・本人・基準、種類ごとの通常性を保持する。',
    'r2gc':'前二文からの同じ人物範囲r2fyを保ち、同じ提示文脈でr2g9を要求する第三文の候補内容。',
    'r2gd':'前二文からの人物範囲と対象・本人の二位置を保ち、局面ごとの使用と全将来の結果r2g8を足枷の比喩の対象側へ渡す。',
    'r2ge':'第三文の主張内容をr2gc、比喩の対象側をr2gbへ更新する。同格、言い直し、前後文との順序、引用内容を実行しない帰属を保持する。',
}
OCCASION_MEANING='同じ提示文脈・対象・本人・基準・候補履歴において、その対象を手段に使うか、自分で適用を検討するかが問題になる活動の局面。実際に使用したか・未成熟が成立したかとは独立した背景入力であり、使わなかった反例を消すために局面でないことにしない。局面のない点も履歴と結果評価には残す。'
LIMITS=[
    '使用を各瞬間の活動へ固定しない読みとして、適用局面での継続使用と、行為の間にも残る因果的結果を採用する。原文が一意にこの条件付き形式を指定しているという主張ではない。',
    '適用局面は背景として明示する。結果や使用の成否から都合よく選ばないが、現実の適用局面を漏れなく同定することは形式検査だけで証明できない。基準は使用を開始して比較する局面という既存の読みを保つ。',
    '適用局面での行動の継続は、経験由来の慣れrch、無意識の習慣、意図的に採用された方針、技能や成功の保証とは別である。本文に学習経験や本人の宣言を補わない。',
    '結果は基準以降の全点で要求する。過去の同じ使用活動から現在の結果への因果的関与も要求し、単に未成熟が続くだけでその対象の作用を認めない。各点で原因となる活動が同一である必要はない。',
    '使用をやめた候補の停止以前だけを保証する演算や、使用をやめれば必ず成熟するとの逆向きの結論は含まない。無限の寿命、終点の不存在、時間の無上界性も要求しない。',
    '第三文の語義・持続の強さの通し判断と、第四文の指示・知的活動への比喩対応は未完。新しい原文対応文字数や意味確認済み分量は加えない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)

def definitions():
    tail=call('rby',v('history'),v('before'),v('anchor'))
    text=definition('r2g4','use e anchor d history h[d] c before h[d d] c occasions h[d] c',
        quant('f','point','d',op('y',app(tail,v('point')),op('y',app(v('occasions'),v('point')),op('t',v('use'),v('point'))))))
    history=lam('point','d',app(v('histories'),v('anchor'),v('branch'),v('point')))
    order='i[first d last d]['+app(v('before'),v('anchor'),v('branch'),v('first'),v('last'))+']'
    occasions=lam('point','d',app(v('occasions'),v('anchor'),v('branch'),v('point')))
    candidate=app(v('candidates'),v('anchor'),v('branch'))
    valid=both(app(history,v('anchor')),call('ta',history,order),app(occasions,v('anchor')))
    eligible=call('r2g4',v('use'),v('anchor'),history,order,occasions)
    results=quant('f','point','d',op('y',app(call('rby',history,order,v('anchor')),v('point')),app(v('result'),v('branch'),v('point'))))
    text+=definition('r2g5','use e anchor d candidates h[d d] c histories h[d d d] c before h[d d d d] c occasions h[d d d] c result h[d d] c',
        both(quant('f','branch','d',op('y',candidate,valid)),quant('g','branch','d',both(candidate,eligible)),quant('f','branch','d',op('y',both(candidate,eligible),results))))
    past=both(app(v('history'),v('earlier')),op('x',op('e',v('earlier'),v('now')),app(v('before'),v('earlier'),v('now'))),
        app(v('occurs'),v('act'),v('earlier')),app(v('causes'),v('act'),v('now')))
    text+=definition('r2g6','now d history h[d] c before h[d d] c occurs h[a d] c causes h[a d] c result e',
        both(call('ta',v('history'),v('before')),app(v('history'),v('now')),op('t',v('result'),v('now')),quant('g','act','a',quant('g','earlier','d',past))))
    args=[v(n) for n in ('scope','object','person','anchor','branch')]
    history=lam('entry','d',call('hzzzh',*args,v('entry')))
    order='i[first d last d]['+call('hzzzi',*args,v('first'),v('last'))+']'
    occurs='i[act a earlier d]['+quant('g','faculty','a',call('r2ev',v('object'),v('person'),v('faculty'),v('act'),v('earlier')))+']'
    causes='i[act a now d]['+call('g3',v('act'),v('person'),'r[p bf]',v('now'))+']'
    text+=definition('r2g7','scope d object a person a anchor d branch d point d',call('r2g6',v('point'),history,order,occurs,causes,call('bf',v('person'))))
    args=[v(n) for n in ('scope','object','person')]
    candidates='i[start d branch d]['+call('hzzzg',*args,v('start'),v('branch'))+']'
    histories='i[start d branch d point d]['+call('hzzzh',*args,v('start'),v('branch'),v('point'))+']'
    order='i[start d branch d first d last d]['+call('hzzzi',*args,v('start'),v('branch'),v('first'),v('last'))+']'
    occasions='i[start d branch d point d]['+call('hzzzl',*args,v('start'),v('branch'),v('point'))+']'
    result='i[branch d point d]['+call('r2g7',*args,v('anchor'),v('branch'),v('point'))+']'
    text+=definition('r2ga','scope d object a person a anchor d',both(op('t',call('r2fh',v('object')),v('anchor')),
        call('r2g5',call('r2ew',v('object'),v('person')),v('anchor'),candidates,histories,order,occasions,result)))
    return text

def extend(old):
    doc=deepcopy(old);statements=doc['statements'];doc['statements']=[]
    assert not (set(MEANINGS)|{'hzzzl'})&{d['name'] for d in doc['declarations']}
    lookup={d['name']:d for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+'r hzzzl[d a a d d d] c.'+definitions())
    for before,after,mapping in (
        ('r2fu','r2gb',{'r2fs':'r2ga'}),('r2fz','r2gc',{'r2fu':'r2gb'}),
        ('r2g3','r2gd',{'r2fs':'r2ga'}),('r2g2','r2ge',{'r2fz':'r2gc','r2g3':'r2gd'})):
        row=deepcopy(lookup[before]);row['name']=after
        def replace(node):
            if isinstance(node,dict):
                if node.get('symbol') in mapping:node['symbol']=mapping[node['symbol']]
                for value in node.values():replace(value)
            elif isinstance(node,list):
                for value in node:replace(value)
        replace(row);doc['declarations'].append(row)
    assert len(statements)==54 and statements[52]['body']['symbol']=='r2g2'
    statements[52]=dict(kind='assert',body=dict(kind='call',symbol='r2ge',arguments=[]))
    doc['statements']=statements
    return parse(format_graph(doc,'compact'))

def build():
    old=parent();doc=extend(old.document);added=doc['declarations'][len(old.document['declarations']):];assert len(added)==10
    core=deepcopy(doc);core.update(declarations=closure(doc,['r2ge']),statements=doc['statements'][52:53])
    library=deepcopy(doc);library.update(declarations=closure(doc,['r2g4','r2g5','r2g6']),statements=[])
    primitive=next(d for d in added if d['name']=='hzzzl')
    basis=dict(status='occasion_conditioned_continuation_candidate',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzzzl':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=['scope','object','person','anchor','branch','point'],meaning_ja=OCCASION_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/shared-fetters-scope-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    print('Use occasions and delayed effects joined without omitting quiet history points',flush=True)
