"""Connect the same assessed choice-growth content to a scoped causal model."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_gradual_choice import ROOT,SOURCE as PARENT,HIGH,TAIL,FIELDS,ABILITY
from scripts.compose_declining_hindrances import CHECKED
from scripts.compose_assessed_barriers import STATE,EQUATIONS,mask,fixed
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/caused-choice.noema'
SOURCE='examples/v016/kant-caused-choice.noema'
CORE='examples/v016/caused-choice-core.noema'
BASIS='data/caused-choice-basis-v1.json'
CAUSAL=[('variables','j[a]'),('equations',EQUATIONS),('factor','a'),('premise','h['+STATE+'] c'),
        ('checked','h['+STATE+'] c'),('effect','h['+STATE+'] c'),('observed',STATE)]
CONTEXT=[('person','a'),('start','d'),('end','d')]
def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    arguments=[v('person'),app(v('goals'),v('person'),v('activity')),v('point')]+av(ABILITY[3:])
    checked=dict(history=v('history'),before=v('before'),start=v('start'),end=v('end'),obstacles=v('activities'),
        scope=v('scope'),assessed='i[activity a point d]['+k('rxd',*arguments)+']')
    text=definition('rxf',params(FIELDS),both(k('rl2',*[checked[n] for n,t in CHECKED]),k('hc','n p a b',v('bound'))))
    def side(flag):
        conclusion=app(v('effect'),v('state'))
        if not flag:conclusion=op('u',conclusion)
        return k('rw',v('variables'),v('equations'),mask(v('factor')),fixed(flag),
            'i[state '+STATE+']['+both(app(v('checked'),v('state')),
                op('z',app(v('premise'),v('state')),app(v('state'),v('factor'))),conclusion)+']')
    actual=both(k('ru',v('variables'),v('equations'),fixed(False),fixed(False),v('observed')),
        app(v('observed'),v('factor')),app(v('premise'),v('observed')),app(v('checked'),v('observed')),app(v('effect'),v('observed')))
    text+=definition('rxg',params(CAUSAL),both(k('rz',v('variables'),v('factor')),actual,side(False),side(True)))
    return text


def additions():
    prefix='h[a d d'
    providers=[('variables',prefix+'] j[a]'),('equations',prefix+' a '+STATE+'] c'),('factor',prefix+'] a'),
        ('observed',prefix+'] '+STATE),('begin',prefix+' '+STATE+'] d'),('end',prefix+' '+STATE+'] d'),
        ('history',prefix+' '+STATE+' d] c'),('before',prefix+' '+STATE+' d d] c')]
    text=''.join(primitive('iak'+n,t) for n,t in providers)
    context=av(CONTEXT)
    binding=dict(person=v('person'),activities=k('iajactivities',v('person'),v('start')),
        scope='i[activity a][k iajscope[v person v start v activity]]',goals='p iajexecution',
        history='i[point d]['+k('iakhistory',*context,v('state'),v('point'))+']',
        before='i[left d right d]['+k('iakbefore',*context,v('state'),v('left'),v('right'))+']',
        start=k('iakbegin',*context,v('state')),end=k('iakend',*context,v('state')),bound=k('iajbound',v('person'),v('start')),
        **{n:'p iaj'+n for n,t in ABILITY[3:]})
    for name,target in (('checked','rxf'),('effect','rxe')):
        text+=definition('iak'+name,params(CONTEXT)+' state '+STATE,both(k('aa',v('person')),k(target,*[binding[n] for n,t in FIELDS])))
    observed=k('iakobserved',*context)
    oldhistory=lambda point:k('iaihistory',v('person'),k('wh'),v('start'),v(point))
    oldorder=k('iaibefore',v('person'),k('wh'),v('start'),v('left'),v('right'))
    match=both(op('e',k('iakbegin',*context,observed),v('start')),op('e',k('iakend',*context,observed),v('end')),
        quant('f','point','d',op('z',oldhistory('point'),k('iakhistory',*context,observed,v('point')))),
        quant('f','left','d',quant('f','right','d',op('y',both(oldhistory('left'),oldhistory('right')),
            op('z',oldorder,k('iakbefore',*context,observed,v('left'),v('right')))))))
    text+=definition('iakaligned',params(CONTEXT),match)
    premise='i[state '+STATE+']['+op('t',app('s[v reading]',v('person')),k('iakbegin',*context,v('state')))+']'
    bindings=dict(variables=k('iakvariables',*context),equations='i[variable a state '+STATE+']['+k('iakequations',*context,v('variable'),v('state'))+']',
        factor=k('iakfactor',*context),premise=premise,checked='i[state '+STATE+']['+k('iakchecked',*context,v('state'))+']',
        effect='i[state '+STATE+']['+k('iakeffect',*context,v('state'))+']',observed=observed)
    text+=definition('iakcausal','reading '+HIGH+' '+params(CONTEXT),both(k('iakaligned',*context),k('rxg',*[bindings[n] for n,t in CAUSAL])))
    rest='i[reading '+HIGH+' person a start d end d]['+both(k('iakcausal',v('reading'),*context),
        app(v('remaining'),v('reading'),*context))+']'
    text+=definition('iakschema','reading '+HIGH+' remaining '+TAIL,k('iajschema',v('reading'),rest))
    text+='r iakreport[a a i c[h['+HIGH+' '+TAIL+'] c] a d] c.'
    text+=definition('iakattribution','',k('iakreport',k('iagnode'),k('wa'),'r c[p iakschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rxd','rl2','rz','ru','rw','hc'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iakattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='model_relative_causal_dependency_of_choice_growth',parent=PARENT,document=SOURCE,
        definitions={
            'rxf':'rxeと同じ活動範囲・方法・結果・時系列について、能力増加を判定するための評価条件を確認する。rl2による完全列挙、履歴、全時点の両側能力評価に、正の増加上限を加える。増加そのものは要求しない。',
            'rxg':'観測割当てが介入前の方程式を満たし、要因・対応する前件・評価条件・結果が成立する。要因を真または偽に固定した各側に解があり、全解で評価条件と要因・前件の対応が成立する。真側の全解では結果が成立し、偽側の全解では成立しないという強い依存条件。',
            'iakchecked/iakeffect':'同じ本人・実行内容・実際の開始点で固定した活動範囲と上限を用い、各介入解の履歴でrxfとrxeを評価する。未評価や不正な履歴を能力増加なしの証拠にしない。',
            'iakaligned':'観測割当ての始点・終点・履歴・履歴内の順序を前段の実際の条件文に一致させる。別の時間経過でモデルだけを成功させない。',
            'iakcausal':'選んだ階数1の発展の記述を同じ本人について実行し、各解の開始点での真偽を要因と照合する。観測履歴の一致とrxgを同時に要求する。',
            'iakschema':'前段の能力増加に因果モデル内の依存を加え、残りの社会的・政治的条件を同じ語義・本人・起点・終点で保持する。',
            'iakattribution':'同じ著者・箇所・範囲・文脈に階数2の部分ひな形を帰属する。帰属だけから現実の発展や増加を断定しない。'},
        inputs={
            'variables/equations/factor':'同じ本人・開始・終了に対して固定した二値構造モデル。介入の両側で方程式と背景を共有し、要因の方程式だけを指定値で置換する。',
            'begin/end/history/before':'同じモデルの解と、その解が表す時間経過との対応。観測解は前段の履歴と一致する。仮定側の時間点の名称は実際の点と同一である必要はない。',
            'observed':'介入前の方程式に従う割当て。現実とモデルの対応を与える入力であり、観測手続きや因果機構の実証を自動的に提供しない。'},
        limitations=[
            '要因ありの全解で増加し、なしの全解では増加しないという強い操作的候補。部分的な寄与、確率的な増加、他の原因による同じ増加、過剰決定の全意味を含まない。',
            '解と原文の内容の整合を検査するが、方程式や反事実世界が現実の因果機構に適合することは証明しない。モデルの選定を変えて望む結論を得ることは正当化しない。',
            '全体としての依存であり、思考から民衆の態度を経由する媒介機構や反作用の段階はまだ記述していない。直接の作用だけを意味するものでもない。',
            '行為選択の定義、単調な件数増加、各人への分配、自然と覆いの比喩、語義候補の限定は前段から引き継ぐ。',
            'remainingには民衆の態度への作用、政府の原則と尊厳などが残る。モデルへの接続だけで原文範囲や意味確認済み区間を加算しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
