"""Keep an explicitly interpreted mediator in the same causal comparison."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_caused_choice import ROOT,SOURCE as PARENT,HIGH,TAIL,STATE,EQUATIONS,CAUSAL,CONTEXT,params,av
from scripts.compose_assessed_barriers import mask,fixed
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/mediated-choice.noema'
SOURCE='examples/v016/kant-mediated-choice.noema'
CORE='examples/v016/mediated-choice-core.noema'
BASIS='data/mediated-choice-basis-v1.json'
MEDIATOR='h[a d d '+STATE+'] c'
FIELDS=CAUSAL+[('mediator','a'),('meaning','h['+STATE+'] c'),('reviewed','h['+STATE+'] c')]


def definitions():
    state=v('state');factor=app(state,v('factor'));mediator=app(state,v('mediator'))
    checked=both(app(v('checked'),state),app(v('reviewed'),state),
        op('z',app(v('premise'),state),factor),op('z',app(v('meaning'),state),mediator))
    def factor_side(flag):
        return k('rw',v('variables'),v('equations'),mask(v('factor')),fixed(flag),
            'i[state '+STATE+']['+both(checked,mediator if flag else op('u',mediator))+']')
    selected='i[variable a]['+op('x',op('e',v('variable'),v('factor')),op('e',v('variable'),v('mediator')))+']'
    def joint_side(flag):
        values='i[variable a]['+op('x',op('e',v('variable'),v('factor')),
            op('e',v('variable'),v('mediator')) if flag else 'u[e[n p a b][n p a b]]')+']'
        effect=app(v('effect'),state)
        return k('rw',v('variables'),v('equations'),selected,values,
            'i[state '+STATE+']['+both(checked,effect if flag else op('u',effect))+']')
    return definition('rxh',params(FIELDS),both(k('rxg',*av(CAUSAL)),
        k('rz',v('variables'),v('mediator')),op('u',op('e',v('factor'),v('mediator'))),
        app(v('observed'),v('mediator')),app(v('reviewed'),v('observed')),app(v('meaning'),v('observed')),
        factor_side(False),factor_side(True),joint_side(False),joint_side(True)))


def additions():
    text=primitive('ialmediator','h[a d d] a')
    context=av(CONTEXT)
    bindings=dict(variables=k('iakvariables',*context),
        equations='i[variable a state '+STATE+']['+k('iakequations',*context,v('variable'),v('state'))+']',
        factor=k('iakfactor',*context),
        premise='i[state '+STATE+']['+op('t',app('s[v reading]',v('person')),k('iakbegin',*context,v('state')))+']',
        checked='i[state '+STATE+']['+k('iakchecked',*context,v('state'))+']',
        effect='i[state '+STATE+']['+k('iakeffect',*context,v('state'))+']',observed=k('iakobserved',*context),
        mediator=k('ialmediator',*context),meaning='i[state '+STATE+']['+app(v('meaning'),*context,v('state'))+']',
        reviewed='i[state '+STATE+']['+app(v('reviewed'),*context,v('state'))+']')
    text+=definition('ialcausal','reading '+HIGH+' meaning '+MEDIATOR+' reviewed '+MEDIATOR+' '+params(CONTEXT),
        both(k('iakaligned',*context),k('rxh',*[bindings[n] for n,t in FIELDS])))
    rest='i[reading '+HIGH+' person a start d end d]['+both(k('ialcausal',v('reading'),v('meaning'),v('reviewed'),*context),
        app(v('remaining'),v('reading'),*context))+']'
    text+=definition('ialschema','reading '+HIGH+' meaning '+MEDIATOR+' reviewed '+MEDIATOR+' remaining '+TAIL,
        k('iajschema',v('reading'),rest))
    text+='r ialreport[a a i c[h['+HIGH+' '+MEDIATOR+' '+MEDIATOR+' '+TAIL+'] c] a d] c.'
    text+=definition('ialattribution','',k('ialreport',k('iagnode'),k('wa'),'r c[p ialschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rxg','rz','rw'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k ialattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='controlled_mediation_template_with_unfilled_psychological_content',parent=PARENT,document=SOURCE,
        definitions={
            'rxh':'前段rxgの全体としての依存を保ち、異なる宣言済み変数を媒介に選ぶ。観測で媒介内容が評価済みで成立し、要因だけの両介入で媒介内容が要因と同じ真偽へ変わる。要因を真に保って媒介を偽・真へ固定する両側に解があり、その全解で評価済みの結果が媒介と同じ真偽になる。各解で要因・媒介の変数と、それぞれの実際の内容を照合する。',
            'ialcausal':'同じ本人・開始・終了の既存モデル、発展の実際の記述、実際の能力増加と評価条件をrxhへ渡す。媒介の内容と評価は引数で明示し、観測履歴の一致を保存する。',
            'ialschema':'前段iajschemaの後件に全体依存と媒介への介入比較を含むialcausalを接続し、残余条件も同じ語義・本人・時点で保持する。',
            'ialattribution':'内容と評価の引数を明示した部分ひな形を、同じ著者・箇所・範囲・文脈へ階数2で帰属する。帰属だけで内容を実行しない。'},
        inputs={
            'mediator':'同じ構造モデル内で要因と異なる宣言済みの媒介変数。対応する内容の実際の真偽を照合し、変数名だけを意味の代用にしない。',
            'meaning/reviewed':'同じ本人・元の開始点・終了点・モデルの解について、途中の変化を記述する条件と、それを評価できる条件。未充足の関数引数であり、民衆の態度を完成した基本語として追加しない。',
            'equations':'全比較で固定する方程式と背景。要因だけへの介入では媒介の元の方程式を残し、同時介入では要因と媒介の二式だけを置換する。'},
        limitations=[
            '途中の変化が要因に依存し、要因がある状態で結果が途中の変化に依存するという強い操作的な媒介候補。現実の因果機構や原文の唯一の読みを証明しない。',
            '要因が偽で媒介が真という比較は要求していない。要因の直接的な寄与と媒介の寄与が共同で必要なモデルも認め、完全媒介や直接作用の不存在を主張しない。',
            '意味と評価の対応は、媒介を強制する仮定世界でも必要。意味を伴わない変数の反転や、評価不能な仮定を成功としない。',
            '民衆の態度という心理的内容とその漸進的な変化は未充足。媒介関係の実装をその名詞の定義完了に数えない。',
            '媒介する変化の時刻を区間内で独立に順序付けること、各人と集団の関係、自由の語義、政府の原則と尊厳は残る。新たな原文範囲や意味確認済み区間を加算しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
