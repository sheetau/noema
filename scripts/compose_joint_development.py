"""Distinguish a jointly varied source set from an individually necessary coalition."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_cohort_mediation import ROOT,SOURCE as PARENT,HIGH,STATE,params,av
from scripts.compose_assessed_barriers import EQUATIONS,fixed
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/joint-development.noema'
SOURCE='examples/v016/kant-joint-development.noema'
CORE='examples/v016/joint-development-core.noema'
BASIS='data/joint-development-basis-v1.json'
SCOPE=[('contributors','j[a]'),('people','h[a] c'),('factors','h[a] a'),('variables','j[a]'),('mediator','a')]
FIELDS=SCOPE+[('equations',EQUATIONS),('premise','h[a '+STATE+'] c'),('checked','h['+STATE+'] c'),
    ('effect','h['+STATE+'] c'),('observed',STATE),('meaning','h['+STATE+'] c'),('reviewed','h['+STATE+'] c')]
CONTEXT=[('community','a'),('start','d'),('end','d')]


def definitions():
    selected=lambda person:app(v('people'),v(person))
    factor=lambda person:app(v('factors'),v(person))
    distinct=quant('f','left','a',quant('f','right','a',op('y',both(selected('left'),selected('right'),
        op('e',factor('left'),factor('right'))),op('e',v('left'),v('right')))))
    valid=quant('f','person','a',op('y',selected('person'),both(k('rz',v('variables'),factor('person')),
        op('u',op('e',factor('person'),v('mediator'))))))
    text=definition('rxq',params(SCOPE),both(k('rcm',v('contributors'),v('people')),k('rz',v('variables'),v('mediator')),valid,distinct))
    causal=lambda variable:quant('g','person','a',both(selected('person'),op('e',v(variable),factor('person'))))
    mask='i[variable a]['+causal('variable')+']'
    state=v('state');m=app(state,v('mediator'))
    matched=quant('f','person','a',op('y',selected('person'),op('z',app(v('premise'),v('person'),state),app(state,factor('person')))))
    checked=both(app(v('checked'),state),app(v('reviewed'),state),matched,op('z',app(v('meaning'),state),m))
    def side(selection,assignment,positive):
        return k('rw',v('variables'),v('equations'),selection,assignment,'i[state '+STATE+']['+both(checked,
            m if positive else op('u',m),app(v('effect'),state) if positive else op('u',app(v('effect'),state)))+']')
    observed=v('observed')
    actual=both(k('ru',v('variables'),v('equations'),fixed(False),fixed(False),observed),
        quant('f','person','a',op('y',selected('person'),both(app(observed,factor('person')),app(v('premise'),v('person'),observed)))),
        app(observed,v('mediator')),app(v('meaning'),observed),app(v('reviewed'),observed),app(v('checked'),observed),app(v('effect'),observed))
    joint='i[variable a]['+op('x',causal('variable'),op('e',v('variable'),v('mediator')))+']'
    text+=definition('rxr',params(FIELDS),both(k('rxq',*av(SCOPE)),actual,
        side(mask,fixed(False),False),side(mask,fixed(True),True),
        side(joint,mask,False),side(joint,fixed(True),True)))
    except_one='i[variable a]['+both(causal('variable'),op('u',op('e',v('variable'),factor('removed'))))+']'
    necessary=quant('f','removed','a',op('y',selected('removed'),side(mask,except_one,False)))
    text+=definition('rxs',params(FIELDS),both(k('rxr',*av(FIELDS)),necessary))
    return text


def additions():
    text=''.join(primitive('iap'+name,sort) for name,sort in (
        ('contributors','h[a d] j[a]'),('people','h[a a d] c'),('factors','h[a d d a] a'),
        ('variables','h[a d d] j[a]'),('equations','h[a d d a '+STATE+'] c'),
        ('observed','h[a d d] '+STATE),('mediator','h[a d d] a')))
    context=av(CONTEXT)
    observed=k('iapobserved',*context)
    people='i[person a][k iappeople[v community v person v start]]'
    bindings=dict(contributors=k('iapcontributors',v('community'),v('start')),people=people,
        factors='i[person a]['+k('iapfactors',*context,v('person'))+']',variables=k('iapvariables',*context),
        mediator=k('iapmediator',*context),equations='i[variable a state '+STATE+']['+k('iapequations',*context,v('variable'),v('state'))+']',
        premise='i[person a state '+STATE+']['+op('t',app('s[v reading]',v('person')),k('ianbegin',*context,v('state')))+']',
        checked='i[state '+STATE+']['+k('iaochecked',*context,v('state'))+']',
        effect='i[state '+STATE+']['+k('iaoeffect',*context,v('state'))+']',observed=observed,
        meaning='i[state '+STATE+']['+k('ianchange',*context,v('state'))+']',
        reviewed='i[state '+STATE+']['+k('ianreviewed',*context,v('state'))+']')
    members=quant('f','person','a',op('y',app(people,v('person')),both(k('aa',v('person')),
        k('ianmembers',v('community'),v('person'),v('start')))))
    aligned=both(op('e',k('ianbegin',*context,observed),v('start')),op('e',k('ianend',*context,observed),v('end')))
    for name,target in (('joint','rxr'),('necessary','rxs')):
        text+=definition('iap'+name,'reading '+HIGH+' '+params(CONTEXT),both(members,aligned,k(target,*[bindings[n] for n,t in FIELDS])))
    text+='r iapreport[a a i c[h['+HIGH+' a d d] c] a d] c.'
    text+=definition('iapattribution','',k('iapreport',k('iagnode'),k('wa'),'r c[p iapnecessary]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm','rz','ru','rw'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[w[k iaoattribution[]][k iapattribution[]]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='joint_development_and_each_member_necessity_candidates',parent=PARENT,document=SOURCE,
        definitions={
            'rxq':'原因側の非空の人々を完全列挙し、各人を相異なる宣言済みの原因変数へ結ぶ。原因変数と媒介変数を分け、一つの変数を複数人の発展として流用しない。',
            'rxr':'同じ方程式の観測で全原因・媒介・結果が成立する。全原因を同時に偽・真へ固定した両側で、評価済みの媒介・結果が偽・真となる。全原因を真に保って媒介を偽・真へ固定した両側でも結果が同じ真偽となる。各解で各人の実際の前件と、その人の変数を照合する。',
            'rxs':'rxrに加え、他の全原因を真に保ち、選んだ一人の原因だけを偽にした各側で、非空の全解の媒介と結果が評価済みで成立しない。全員をまとめた比較と、各人がこの組合せに必要である条件を分ける。',
            'iapjoint/iapnecessary':'同じ共同体の元の開始点で固定した原因側構成員について、選んだ思考の発展の内容を各解の共通始点で評価する。前段の同じ集団の応答拡大と行為選択拡大へ接続し、原因側の人々が影響先共同体の構成員であることも要求する。',
            'iapattribution':'前段の一人からの条件文の注記を保存し、共同原因の強い候補を別の階数2の関数記述として同じ著者・箇所・文脈へ帰属する。条件文全体の集合的な前件への統合を完了したとはしない。'},
        inputs={
            'contributors/people':'原因側に採る人々の列と範囲。元の開始点へ固定し、途中で不要だった人だけを外して必要性を作り直さない。影響先集団の全員である必要はない。',
            'factors/variables/equations/mediator':'各人を区別した固定構造モデル。集団の人数や一つの総合要因だけへ置換せず、各人を外す介入にも対応する。',
            'observed/history':'観測した割当ての共通始点・終点を元の区間に一致させる。各仮定解では原因側の全員、集団の態度、集団の行為能力が同じ履歴を使う。'},
        limitations=[
            'rxsは他の全原因が成立する背景で各人が必要な強い候補である。一般の共同寄与、代替可能な参加者、過剰決定、確率的な寄与、協力の意図や共同意思まで定義しない。',
            'rxrは全員をまとめた変化と媒介への依存を要求するが、各人の必要性までは要求しない。非単調な方程式での全ての部分集団の比較をrxsだけで済ませたとはしない。',
            '原因側が一人の場合も許す。複数人であることは原因側の列で明示し、共同原因という語から人数を暗黙に補わない。',
            '思考の発展・態度・行為能力の具体的内容と尺度は前段の限定を引き継ぐ。原因側の各人の発展を同じ始点で評価するが、発展開始の同時性は含意しない。',
            '集合的な前件を持つ条件文全体と残余条件への統合、作用の独立した時刻、政府の原則と尊厳、原文の語義との一致は残る。',
            '原文の新しい文字範囲と意味確認済み区間は加算しない。有限モデルで共同原因を区別できることを、原文の唯一の解釈や全文の意味一致としない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
