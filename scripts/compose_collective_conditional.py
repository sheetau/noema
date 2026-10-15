"""Keep the same coalition and cohort scopes across a collective conditional."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_joint_development import ROOT,SOURCE as PARENT,HIGH,STATE,params,av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/collective-conditional.noema'
SOURCE='examples/v016/kant-collective-conditional.noema'
CORE='examples/v016/collective-conditional-core.noema'
BASIS='data/collective-conditional-basis-v1.json'
RESULT='h['+HIGH+' j[a] d d] c'
REST='h['+HIGH+' a j[a] d d d] c'
WITNESS=[('reading',HIGH),('contributors','j[a]'),('people','h[a] c'),('cases','h[d] c'),('valid','h[d] c')]
FIELDS=WITNESS+[('history','h[d d] c'),('before','h[d d d] c'),('result',RESULT)]


def definitions():
    selected=app(v('cases'),v('scene'))
    premise=quant('f','person','a',op('y',app(v('people'),v('person')),
        op('t',app('s[v reading]',v('person')),v('scene'))))
    history='i[point d]['+app(v('history'),v('scene'),v('point'))+']'
    order='i[left d right d]['+app(v('before'),v('scene'),v('left'),v('right'))+']'
    valid=quant('f','scene','d',op('y',selected,both(app(v('valid'),v('scene')),
        k('ta',history,order),app(v('history'),v('scene'),v('scene')))))
    later=quant('g','end','d',both(app(v('history'),v('scene'),v('end')),
        app(v('before'),v('scene'),v('scene'),v('end')),
        app(v('result'),v('reading'),v('contributors'),v('scene'),v('end'))))
    text=definition('rxt',params(FIELDS),both(k('rcm',v('contributors'),v('people')),valid,
        quant('g','scene','d',selected),quant('f','scene','d',op('y',selected,op('y',premise,later)))))
    text+=definition('rxu',params(WITNESS),both(k('rcm',v('contributors'),v('people')),
        quant('g','scene','d',both(selected,app(v('valid'),v('scene')),premise))))
    return text


def additions():
    text=''.join(primitive('iaq'+name,sort) for name,sort in (
        ('communities','h[a d] c'),('cases','h[a d d] c'),('history','h[a d d d] c'),('before','h[a d d d d] c')))
    members=lambda point,person:k('ianmembers',v('community'),v(person),v(point))
    causes=lambda point,person:k('iappeople',v('community'),v(person),v(point))
    cohort=k('ianpopulation',v('community'),v('point'))
    people='i[person a]['+members('point','person')+']'
    catalogues=[]
    for catalogue,scope in (('iantopics','ianscope'),('iaoactivities','iaoscope')):
        catalogues.append(k('rxk',cohort,people,
            'i[person a]['+k(catalogue,v('community'),v('person'),v('point'))+']',
            'i[person a topic a]['+k(scope,v('community'),v('person'),v('point'),v('topic'))+']'))
    inventory=both(k('rcm',k('iapcontributors',v('community'),v('point')),
        'i[person a]['+causes('point','person')+']'),*catalogues,
        quant('f','person','a',op('y',causes('point','person'),both(k('aa',v('person')),members('point','person')))),
        quant('f','person','a',op('y',members('point','person'),k('aa',v('person')))),
        *[k('hc','n p a b',k(name,v('community'),v('point'))) for name in ('ianbound','iaobound')])
    text+=definition('iaqinventory','community a point d',inventory)
    same=both(quant('f','person','a',both(op('z',causes('anchor','person'),causes('scene','person')),
        op('z',members('anchor','person'),members('scene','person')))),
        *[op('e',k(name,v('community'),v('anchor')),k(name,v('community'),v('scene'))) for name in ('ianbound','iaobound')],
        quant('f','person','a',op('y',members('anchor','person'),quant('f','topic','a',both(*[
            op('z',k(name,v('community'),v('person'),v('anchor'),v('topic')),
                k(name,v('community'),v('person'),v('scene'),v('topic'))) for name in ('ianscope','iaoscope')])))))
    text+=definition('iaqfixed','community a anchor d scene d',both(k('iaqinventory',v('community'),v('anchor')),
        k('iaqinventory',v('community'),v('scene')),same))
    observed=k('iapobserved',v('community'),v('start'),v('end'))
    history=lambda point:k('iaqhistory',v('community'),v('anchor'),v('start'),v(point))
    aligned=both(op('e',k('ianbegin',v('community'),v('start'),v('end'),observed),v('start')),
        op('e',k('ianend',v('community'),v('start'),v('end'),observed),v('end')),
        quant('f','point','d',op('z',history('point'),k('ianhistory',v('community'),v('start'),v('end'),observed,v('point')))),
        quant('f','left','d',quant('f','right','d',op('y',both(history('left'),history('right')),
            op('z',k('iaqbefore',v('community'),v('anchor'),v('start'),v('left'),v('right')),
                k('ianbefore',v('community'),v('start'),v('end'),observed,v('left'),v('right')))))))
    text+=definition('iaqaligned','community a anchor d start d end d',aligned)
    bindings=dict(reading=v('reading'),contributors=k('iapcontributors',v('community'),v('anchor')),
        people='i[person a][k iappeople[v community v person v anchor]]',
        cases='i[scene d][k iaqcases[v community v anchor v scene]]',
        valid='i[scene d][k iaqfixed[v community v anchor v scene]]',
        history='i[scene d point d][k iaqhistory[v community v anchor v scene v point]]',
        before='i[scene d left d right d][k iaqbefore[v community v anchor v scene v left v right]]',
        result='i[reading '+HIGH+' contributors j[a] start d end d]['+both(
            k('iaqaligned',v('community'),v('anchor'),v('start'),v('end')),
            k('iapnecessary',v('reading'),v('community'),v('start'),v('end')),
            app(v('remaining'),v('reading'),v('community'),v('contributors'),v('anchor'),v('start'),v('end')))+']')
    text+=definition('iaqconditional','reading '+HIGH+' community a remaining '+REST,
        'b anchor['+k('rxt',*[bindings[n] for n,t in FIELDS])+']','e')
    text+=definition('iaqwitness','reading '+HIGH+' community a',
        'b anchor['+k('rxu',*[bindings[n] for n,t in WITNESS])+']','e')
    selected=lambda community:k('iaqcommunities',v(community),k('wh'))
    text+=definition('iaqschema','reading '+HIGH+' remaining '+REST,both(k('iahfamily',v('reading')),
        quant('g','community','a',selected('community')),quant('f','community','a',op('y',selected('community'),
            op('t',k('iaqconditional',v('reading'),v('community'),v('remaining')),k('wh'))))))
    text+='r iaqreport[a a i c[h['+HIGH+' '+REST+'] c] a d] c.'
    text+=definition('iaqattribution','',k('iaqreport',k('iagnode'),k('wa'),'r c[p iaqschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm','ta'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iaqattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='fixed_collective_antecedent_connected_to_mediated_consequence',parent=PARENT,document=SOURCE,
        definitions={
            'rxt':'同じ非空の完全列挙された原因側構成員について、選んだ同じ性質記述が全員に成立することを各仮定の前件とする。全仮定で範囲と履歴を先に検査し、前件が成立したなら同じ履歴の後の時点で、同じ記述と構成員列を渡した結果がある。',
            'rxu':'同じ構成員の全員が同じ記述を満たす、有効な仮定の実例があることを別に検査する。条件文の成立だけから、この実例や現在の事実を導かない。',
            'iaqinventory':'原因側の人々と影響先の構成員、各人の判断対象と活動を完全列挙し、全員が人で原因側が共同体に所属すること、両増加上限が正であることを確認する。',
            'iaqfixed':'基準文脈と各仮定の範囲をそれぞれ検査し、原因側・影響先の人々、判断対象、活動、増加上限を一致させる。列の順序は一致を要求せず、意味上の範囲を固定する。',
            'iaqaligned':'後件の共同原因モデルの観測割当てについて、始点・終点・全履歴・履歴内の順序を、その仮定の履歴と一致させる。',
            'iaqconditional/iaqschema':'二つの発展の読みから同じ一つを選び、固定した原因側全員の前件を、各人が必要な共同原因iapnecessaryによる集団の後件へ接続する。残余条件には同じ読み・共同体・原因側の列・基準文脈・始点・終点を渡す。',
            'iaqattribution':'前段で並べた注記を、集合的な条件文と集団の媒介を接続した階数2のひな形への帰属へ改訂する。親の全宣言と先行21文を保存する。'},
        inputs={
            'communities/cases/history/before':'同じ基準文脈で対象にする共同体と仮定、各仮定の時間経過。共同体と仮定は非空で、各履歴は始点を含む厳密な全順序である。',
            'remaining':'同じ集団と原因側を保持して後続の内容を付加する関係。政府の原則や尊厳の意味をこの未充足引数の名前だけで定義したとはしない。'},
        limitations=[
            '指定した原因側の全員が発展するという前件と、各人が必要な強い共同原因の後件を選んだ候補である。原文が特定の人数や必要性を明示したとはせず、全員・多数派・ある集団という読みの適合は別途確認する。',
            '仮定間でも原因側と影響先の人々・判断対象・活動・尺度を固定する。異なる集団へ一般化する条件文や構成員の出入りを含む意味は、この固定範囲の比較と分ける。',
            '前件が全仮定で偽でも条件文は成立し得るが、空の原因側や評価範囲の不整合を偽の前件へ変換して通さない。未知の原始関係は有限診断で例外として残す。',
            '発展・態度・行為能力の語義、単調な件数尺度、固定構造モデル、各人の必要性という前段の限定を引き継ぐ。現実の因果機構や自由一般を証明したものではない。',
            '作用の独立した時刻と遅延、政府の原則、尊厳、自然の比喩、原文との意味一致は未完である。',
            '新しい原文範囲と意味確認済み区間は加算しない。条件文の接続と有限検査を全文の意味確認に数えない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
