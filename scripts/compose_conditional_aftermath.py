"""Keep one described antecedent across scoped, temporally ordered consequences."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_thinking_disposition import ROOT,SOURCE as PARENT,HIGH
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/conditional-aftermath.noema'
SOURCE='examples/v016/kant-conditional-aftermath.noema'
CORE='examples/v016/conditional-aftermath-core.noema'
BASIS='data/conditional-aftermath-basis-v1.json'
TAIL='h['+HIGH+' a d d] c'
FIELDS=[('reading',HIGH),('person','a'),('cases','h[d] c'),('history','h[d d] c'),
        ('before','h[d d d] c'),('result',TAIL)]


def definitions():
    history='i[point d]['+app(v('history'),v('scene'),v('point'))+']'
    order='i[left d right d]['+app(v('before'),v('scene'),v('left'),v('right'))+']'
    valid=quant('f','scene','d',op('y',app(v('cases'),v('scene')),both(
        k('ta',history,order),app(v('history'),v('scene'),v('scene')))))
    later=quant('g','end','d',both(app(v('history'),v('scene'),v('end')),
        app(v('before'),v('scene'),v('scene'),v('end')),
        app(v('result'),v('reading'),v('person'),v('scene'),v('end'))))
    premise='s[v reading]'
    conditional=quant('f','scene','d',op('y',app(v('cases'),v('scene')),
        op('y',op('t',app(premise,v('person')),v('scene')),later)))
    text=definition('rxa',' '.join(n+' '+t for n,t in FIELDS),both(valid,
        quant('g','scene','d',app(v('cases'),v('scene'))),conditional))
    text+=definition('rxb','reading '+HIGH+' person a cases h[d] c',
        k('re',v('person'),premise,v('cases')))
    return text


def additions():
    providers=[('people','h[a d] c'),('cases','h[a d d] c'),('history','h[a d d d] c'),
               ('before','h[a d d d d] c')]
    text=''.join(primitive('iai'+n,t) for n,t in providers)
    bound=dict(reading=v('reading'),person=v('person'),
        cases='i[scene d][k iaicases[v person v anchor v scene]]',
        history='i[scene d point d][k iaihistory[v person v anchor v scene v point]]',
        before='i[scene d left d right d][k iaibefore[v person v anchor v scene v left v right]]',result=v('result'))
    text+=definition('iaiconditional','reading '+HIGH+' person a result '+TAIL,
        'b anchor['+k('rxa',*[bound[n] for n,t in FIELDS])+']','e')
    text+=definition('iaiwitness','reading '+HIGH+' person a',
        'b anchor['+k('rxb',bound['reading'],bound['person'],bound['cases'])+']','e')
    people=lambda name:k('iaipeople',v(name),k('wh'))
    text+=definition('iaiframe','reading '+HIGH+' result '+TAIL,both(
        k('iahfamily',v('reading')),quant('g','person','a',people('person')),
        quant('f','person','a',op('y',people('person'),op('t',
            k('iaiconditional',v('reading'),v('person'),v('result')),k('wh'))))))
    text+='r iaireport[a a i c[h['+HIGH+' '+TAIL+'] c] a d] c.'
    text+=definition('iaiattribution','',k('iaireport',k('iagnode'),k('wa'),'r c[p iaiframe]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['re','ta'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iaiattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='conditional_scope_with_explicit_unfilled_consequent',parent=PARENT,document=SOURCE,
        definitions={
            'rxa':'非空の候補状況について、同じ階数1の性質記述と同じ人を前件として評価する。各候補は自分自身を含む厳密な全順序の履歴taを持つ。前件が真なら、その候補の履歴の後の時点に、同じ記述・人・起点を引数とする後件の実例がある。rcと同様の範囲付き条件を、後件の起点を明示して構成する。',
            'rxb':'既存reを用い、選んだ候補範囲のどこかで同じ記述を同じ人について実行した内容が成立するかを別に問う。現在の事実を含意しない。',
            'iaiconditional':'候補、履歴、順序を同じ本人・基準文脈に固定してrxaへ渡す。基準文脈そのものを候補や前件の成立点へ補わない。',
            'iaiwitness':'同じ本人・基準文脈の候補にrxbを適用する独立した診断内容。本文の条件へ実例の存在を追加しない。',
            'iaiframe':'前段iahfamilyの二つの読みから一つを選び、非空の対象者範囲の全員・全候補に同じ読みと同じ後件関数を使う。候補ごとに都合のよい語義へ切り替えない。',
            'iaiattribution':'後件引数を明示したひな形の階数2の記述を、同じ箇所・著者・範囲・基準文脈の注記として帰属する。ひな形の真理や前件の現実の成立を帰属から導かない。'},
        inputs={
            'result':'同じ選択済みの記述、本人、前件の成立点、帰結の成立点を受け取る関係。未充足の関数引数であり、原文の社会への作用を表す新しい未説明の単語で置換しない。',
            'people/cases':'文脈ごとに指定する対象者と仮定状況。空の対象者・候補は拒否するが、前件が全候補で偽である場合は条件文と適用例の存在を分ける。',
            'history/before':'同じ人・基準文脈・仮定状況に属する時点と順序。有限診断で全現実の時間や反事実の選択規則を証明しない。'},
        limitations=[
            '条件文の作用範囲と後続時点への接続を記述した段階。後件resultは未充足であり、民衆の心的態度への漸進的な作用、自由な行為能力の増加、政府の原則と尊厳は未記述。',
            '後の出来事があるという順序条件だけでは因果や反作用を定義できない。原文のwirkt zurükは後件に別途因果条件を組み込む必要がある。',
            '現行の対象側は一人ずつの発展候補であり、民衆全体への集団的な作用への接続、自然の世話と制度の覆いの対応は未完。',
            'Berufの二候補と自由な思考の読みは前段の限定を引き継ぐ。ひな形があることを新しい原文範囲の意味一致や全文完成に数えない。',
            '厳密に後の時点での結果を要求する操作的な候補である。同時に始まる作用の過程や継続的な変化の全内容は表していない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
