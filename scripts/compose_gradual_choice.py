"""Compose gradual growth in assessed ability both to act and to refrain."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_conditional_aftermath import ROOT,SOURCE as PARENT,HIGH,TAIL
from scripts.compose_declining_hindrances import GRADUAL
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/gradual-choice.noema'
SOURCE='examples/v016/kant-gradual-choice.noema'
CORE='examples/v016/gradual-choice-core.noema'
BASIS='data/gradual-choice-basis-v1.json'
ABILITY=[('person','a'),('goal','e'),('point','d'),('available','h[a a d] c'),
         ('prospects','h[a a d d] c'),('evaluated','h[a a d d] c')]
FIELDS=[('person','a'),('activities','j[a]'),('scope','h[a] c'),('goals','h[a a] e'),
        ('history','h[d] c'),('before','h[d d] c'),('start','d'),('end','d'),('bound','b')]+ABILITY[3:]


def definitions():
    text=''
    negative='b result['+op('u',op('t',v('goal'),v('result')))+']'
    for name,base in (('rxc','xd'),('rxd','xf')):
        body=both(*[k(base,v('person'),goal,v('point'),*[v(n) for n,t in ABILITY[3:]]) for goal in (v('goal'),negative)])
        text+=definition(name,' '.join(n+' '+t for n,t in ABILITY),body)
    argument=[v('person'),app(v('goals'),v('person'),v('activity')),v('point')]+[v(n) for n,t in ABILITY[3:]]
    args=dict(history=v('history'),before=v('before'),start=v('start'),end=v('end'),obstacles=v('activities'),
        scope=v('scope'),assessed='i[activity a point d]['+k('rxd',*argument)+']',
        hindering='i[activity a point d]['+op('u',k('rxc',*argument))+']',bound=v('bound'))
    text+=definition('rxe',' '.join(n+' '+t for n,t in FIELDS),k('rl6',*[args[n] for n,t in GRADUAL]))
    return text


def additions():
    providers=[('activities','h[a d] j[a]'),('scope','h[a d a] c'),('bound','h[a d] b'),
        ('performs','h[a a d] c')]+ABILITY[3:]
    text=''.join(primitive('iaj'+n,t) for n,t in providers)
    text+=definition('iajexecution','person a activity a','b point['+both(k('dg',v('activity'),v('point')),
        k('iajperforms',v('person'),v('activity'),v('point')))+']','e')
    bindings=dict(person=v('person'),activities=k('iajactivities',v('person'),v('start')),
        scope='i[activity a][k iajscope[v person v start v activity]]',goals='p iajexecution',
        history='i[point d][k iaihistory[v person k wh[] v start v point]]',
        before='i[left d right d][k iaibefore[v person k wh[] v start v left v right]]',
        start=v('start'),end=v('end'),bound=k('iajbound',v('person'),v('start')),
        **{n:'p iaj'+n for n,t in ABILITY[3:]})
    text+=definition('iajgrowth','person a start d end d',both(k('aa',v('person')),k('rxe',*[bindings[n] for n,t in FIELDS])))
    result='i[reading '+HIGH+' person a start d end d]['+both(k('iajgrowth',v('person'),v('start'),v('end')),
        app(v('remaining'),*[v(n) for n in ('reading','person','start','end')]))+']'
    text+=definition('iajschema','reading '+HIGH+' remaining '+TAIL,k('iaiframe',v('reading'),result))
    text+='r iajreport[a a i c[h['+HIGH+' '+TAIL+'] c] a d] c.'
    text+=definition('iajattribution','',k('iajreport',k('iagnode'),k('wa'),'r c[p iajschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['xd','xf','rl6'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iajattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='partial_gradual_choice_capacity_reading',parent=PARENT,document=SOURCE,
        definitions={
            'rxc':'同じ本人・目標内容・時点に、実行を満たすxdの方法と不実行を満たすxdの方法がそれぞれある。選択結果は非空で、想定結果に含まれ、各側の全評価結果がその側の内容を満たす。二つの方法は別でよく、現在どちらを選んだかは主張しない。',
            'rxd':'同じ条件で実行と不実行の双方についてxfの評価条件が成立する。未評価の方法を持つことと、選択能力がないことを区別する。',
            'rxe':'固定した非空の活動一覧を重複なく完全に列挙し、区間内の全時点で全活動のrxdを要求する。rxcがない活動の集合に既存rl6を適用し、選択能力を失わず二回以上増し、隣接時点の増加を同じ正の上限以内にする。',
            'iajexecution':'指定した活動が起こり、同じ本人がそれを自分の行為として遂行する内容。活動の単なる発生や別人の遂行は本人の実行にならない。',
            'iajgrowth':'同じ人について、iajexecutionとその不実行への方法を用いてrxeを評価する。活動範囲と上限は開始点で固定し、前段の同じ仮定履歴と時間順序を用いる。',
            'iajschema':'前段iaiframeの後件へiajgrowthを加え、残りの社会的・因果的条件remainingを連言する。同じ語義・本人・起点・終点を残りの条件へ渡す。',
            'iajattribution':'同じ著者・箇所・範囲・文脈へ階数2の部分ひな形を帰属する。帰属だけから発展や行為の現実の成立を導かない。'},
        inputs={
            'activities/scope/bound':'開始点で固定する評価対象の活動、完全列挙と一段階の上限。結果に合わせて都合のよい活動や時間の刻みを選び直さない。',
            'available/prospects/evaluated':'本人が利用可能な方法、想定結果、評価対象。実行側と不実行側で同じ方法空間と評価基準を共有する。',
            'performs':'本人が活動を自分の行為として遂行する関係。単なる立会いや受動的な参加とは区別する。意思決定、身体的な実現、熟慮の基礎説明は残る。',
            'remaining':'民衆の態度への反作用、思考の発展との因果、政府の原則・尊厳など、ここで具体化していない条件を受ける明示的な引数。'},
        limitations=[
            '自由な行為の能力を、同じ実行内容と不実行内容を本人がそれぞれ実現できる選択能力として読む候補。規範的許可、自律・合理的判断・責任の全意味を定義したものではない。',
            '活動数による単調な二段階以上の増加という強い読み。質や熟練、局所的な後退、連続的な変化、実時間に対する速度は表していない。上限を原文の数値とはしない。',
            '対象者各人の能力増加を要求する分配的な候補であり、集合としての民衆の能力を確定した読みではない。全員を同時に行為させる共通計画は要求しない。',
            '能力と方法の評価は指定した解釈内の条件である。現実の全方法・全活動・全時点を網羅した保証や、現在行為したという断定は含まない。',
            '条件文の後件を一部具体化したが、反作用・因果・政治的帰結のremainingは未充足。前段の語義候補と自然・比喩の限定も引き継ぎ、新しい原文対応範囲や意味確認済み区間を加算しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
