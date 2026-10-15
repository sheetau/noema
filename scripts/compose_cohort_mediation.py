"""Connect one member's development to mediated changes in a fixed cohort."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_cohort_response import ROOT,SOURCE as PARENT,COHORT,FIELDS as PROFILE,CONTEXT as GROUP,STATE,params,av
from scripts.compose_declining_hindrances import TIME
from scripts.compose_gradual_choice import ABILITY,HIGH,TAIL
from scripts.compose_mediated_choice import FIELDS as CAUSAL,CONTEXT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/cohort-mediation.noema'
SOURCE='examples/v016/kant-cohort-mediation.noema'
CORE='examples/v016/cohort-mediation-core.noema'
BASIS='data/cohort-mediation-basis-v1.json'
REST='h['+HIGH+' a a d d] c'
FIELDS=COHORT+TIME+[('bound','b'),('goals','h[a a] e')]+ABILITY[3:]


def definitions():
    bindings={n:v(n) for n,t in FIELDS}
    args=[v('person'),app(v('goals'),v('person'),v('topic')),v('point')]+av(ABILITY[3:])
    bindings.update(classified='i[person a topic a point d]['+k('rxd',*args)+']',
        response='i[person a topic a point d]['+k('rxc',*args)+']')
    return ''.join(definition(name,params(FIELDS),k(target,*[bindings[n] for n,t in PROFILE]))
        for name,target in (('rxo','rxm'),('rxp','rxn')))


def additions():
    text=''.join(primitive('iao'+n,t) for n,t in (
        ('community','h[a d] a'),('activities','h[a a d] j[a]'),
        ('scope','h[a a d a] c'),('bound','h[a d] b')))
    context=av(GROUP)
    bindings=dict(population=k('ianpopulation',v('community'),v('start')),
        people='i[person a][k ianmembers[v community v person v start]]',
        topics='i[person a][k iaoactivities[v community v person v start]]',
        scope='i[person a activity a][k iaoscope[v community v person v start v activity]]',
        history='i[point d]['+k('ianhistory',*context,v('state'),v('point'))+']',
        before='i[left d right d]['+k('ianbefore',*context,v('state'),v('left'),v('right'))+']',
        start=k('ianbegin',*context,v('state')),end=k('ianend',*context,v('state')),
        bound=k('iaobound',v('community'),v('start')),goals='p iajexecution',
        **{n:'p iaj'+n for n,t in ABILITY[3:]})
    human=quant('f','member','a',op('y',k('ianmembers',v('community'),v('member'),v('start')),k('aa',v('member'))))
    for name,target in (('checked','rxo'),('effect','rxp')):
        text+=definition('iao'+name,params(GROUP)+' state '+STATE,both(human,k(target,*[bindings[n] for n,t in FIELDS])))
    context=av(CONTEXT)
    community=k('iaocommunity',v('person'),v('start'))
    group=[community,v('start'),v('end')]
    history=lambda point:k('iakhistory',*context,v('state'),v(point))
    matched=both(*[op('e',k('iak'+name,*context,v('state')),k('ian'+name,*group,v('state'))) for name in ('begin','end')],
        quant('f','point','d',op('z',history('point'),k('ianhistory',*group,v('state'),v('point')))),
        quant('f','left','d',quant('f','right','d',op('y',both(history('left'),history('right')),
            op('z',k('iakbefore',*context,v('state'),v('left'),v('right')),
                k('ianbefore',*group,v('state'),v('left'),v('right')))))))
    text+=definition('iaomatched',params(CONTEXT)+' state '+STATE,matched)
    bindings=dict(variables=k('iakvariables',*context),
        equations='i[variable a state '+STATE+']['+k('iakequations',*context,v('variable'),v('state'))+']',
        factor=k('iakfactor',*context),
        premise='i[state '+STATE+']['+op('t',app('s[v reading]',v('person')),k('iakbegin',*context,v('state')))+']',
        checked='i[state '+STATE+']['+both(k('iaomatched',*context,v('state')),k('iaochecked',*group,v('state')))+']',
        effect='i[state '+STATE+']['+k('iaoeffect',*group,v('state'))+']',observed=k('iakobserved',*context),
        mediator=k('ialmediator',*context),meaning='i[state '+STATE+']['+k('ianchange',*group,v('state'))+']',
        reviewed='i[state '+STATE+']['+both(k('iaomatched',*context,v('state')),k('ianreviewed',*group,v('state')))+']')
    text+=definition('iaocausal','reading '+HIGH+' '+params(CONTEXT),both(k('aa',v('person')),
        k('ianmembers',community,v('person'),v('start')),k('iakaligned',*context),k('rxh',*[bindings[n] for n,t in CAUSAL])))
    rest='i[reading '+HIGH+' person a start d end d]['+both(k('iaocausal',v('reading'),*context),
        app(v('remaining'),v('reading'),v('person'),community,v('start'),v('end')))+']'
    text+=definition('iaoschema','reading '+HIGH+' remaining '+REST,k('iaiframe',v('reading'),rest))
    text+='r iaoreport[a a i c[h['+HIGH+' '+REST+'] c] a d] c.'
    text+=definition('iaoattribution','',k('iaoreport',k('iagnode'),k('wa'),'r c[p iaoschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rxm','rxn','rxc','rxd'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iaoattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='member_development_mediated_cohort_choice_candidate',parent=PARENT,document=SOURCE,
        definitions={
            'rxo/rxp':'同じ構成員と各人の活動を固定し、実行と不実行の双方を選べるrxc、その評価条件rxdを、集団の評価rxmと段階的拡大rxnへ接続する。全員がそれぞれ二段階で伸びることや全員共通の一方法を要求しない。',
            'iaochecked/iaoeffect':'同じ共同体・元の開始点の構成員と活動を用い、同じ本人による実行iajexecutionと不実行を各解の履歴で評価する。応答拡大と同じ構成員・時間経過を用いるが、判断対象と行為の活動は区別する。',
            'iaomatched':'前件の本人についてのモデルと影響先共同体のモデル対応の始点・終点・全履歴・履歴内の順序を、各解で一致させる。観測だけ一致して仮定側で別の期間へ交換することを許さない。',
            'iaocausal':'元の開始点で共同体に所属する同じ本人の発展を前件にし、同じ共同体の応答拡大を媒介、同じ構成員の行為選択の拡大を結果としてrxhを実行する。変数だけを反転せず、全介入解で実際の内容と評価を照合する。',
            'iaoschema':'選んだ発展の読みと本人を前件から後件まで保持し、集団の媒介条件を後件へ接続する。残余条件には同じ読み・本人・共同体・元の区間を渡す。個人が二段階で能力を増す条件を集団の条件へ暗黙に重ねない。',
            'iaoattribution':'前段で並べていた個人と集団の部分注記を、接続した候補の階数2のひな形への帰属に改訂する。親の宣言と先行21文は保存する。'},
        inputs={
            'community':'前件の本人と元の開始点で指定する影響先共同体。媒介と結果と残余条件で同じ値を使い、結果によって別集団へ交換しない。',
            'activities/scope/bound':'同じ共同体の各人に、元の開始点で固定した行為の活動範囲と集団の増加上限。判断対象の一覧とは独立に指定する。',
            'models':'前段の同一構造方程式と介入比較を用い、各解に対応する本人の履歴と共同体の履歴を明示的に照合する。仮定場面の応答と行為の実行可能性を現実の実行へ補わない。'},
        limitations=[
            '一人の構成員の発展が同じ集団へ作用するという接続候補であり、全員の発展、集団としての思考、複数人の発展が共同して原因になる場合の全意味へ同一視しない。原文の原因側の集合的な読みはさらに必要である。',
            '媒介と結果は同じ構成員の人・対象または人・活動の組の単調な件数拡大。多数派、全員の改善、局所的な後退を伴う進歩、集団共通の行為方法、法的な自由を暗黙に含めない。',
            '各人の行為の実行と不実行を選べることを結果に用い、集団が一つの主体として行動する共同的能力とは分ける。',
            '原因を偽にした全解で結果がなく、原因を真に保って媒介だけを偽にした全解でも結果がないという強い依存候補である。完全媒介や現実の因果機構の実証ではない。',
            '集団と本人の履歴を一致させるが、思考・態度・能力の三段階の独立した時刻や作用の遅延はまだ指定していない。政府の原則、尊厳、自然の比喩、語義の適合も残る。',
            '新しい原文範囲や意味確認済み区間は加算しない。有限モデルでの接続の成立を全文の意味一致の証明とはしない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
