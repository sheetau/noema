"""Compose assessed response growth over a fixed cohort and per-person topics."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_reasoned_response import ROOT,SOURCE as PARENT,STATE,params,av
from scripts.compose_declining_hindrances import TIME
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/cohort-response.noema'
SOURCE='examples/v016/kant-cohort-response.noema'
CORE='examples/v016/cohort-response-core.noema'
BASIS='data/cohort-response-basis-v1.json'
COHORT=[('population','j[a]'),('people','h[a] c'),('topics','h[a] j[a]'),('scope','h[a a] c')]
FIELDS=COHORT+TIME+[('bound','b'),('classified','h[a a d] c'),('response','h[a a d] c')]
CONTEXT=[('community','a'),('start','d'),('end','d')]


def definitions():
    person=app(v('people'),v('person'));topic=app(v('scope'),v('person'),v('topic'))
    text=definition('rxk',params(COHORT),both(k('rcm',v('population'),v('people')),
        quant('f','person','a',op('y',person,k('rcm',app(v('topics'),v('person')),
            'i[topic a]['+topic+']')))))
    count=k('hf',app(v('topics'),v('person')),'i[topic a]['+app(v('response'),v('person'),v('topic'),v('point'))+']')
    text+=definition('rxl','population j[a] topics h[a] j[a] response h[a a d] c point d',
        'q[v population][n p a b][i[total b person a]['+k('ha',v('total'),count)+']]','b')
    inside=lambda point:app(k('rlz',*av(TIME)),v(point))
    assessed=quant('f','point','d',op('y',inside('point'),quant('f','person','a',op('y',person,
        quant('f','topic','a',op('y',topic,app(v('classified'),v('person'),v('topic'),v('point'))))))))
    checked=both(k('rxk',*av(COHORT)),k('ta',v('history'),v('before')),
        app(v('history'),v('start')),app(v('history'),v('end')),app(v('before'),v('start'),v('end')),
        k('hc','n p a b',v('bound')),assessed)
    text+=definition('rxm',params(FIELDS),checked)
    score=lambda point:k('rxl',v('population'),v('topics'),v('response'),v(point))
    ordered=both(inside('first'),inside('last'),app(v('before'),v('first'),v('last')))
    every=lambda cond,body:quant('f','first','d',quant('f','last','d',op('y',cond,body)))
    retained=every(ordered,quant('f','person','a',op('y',person,quant('f','topic','a',op('y',
        both(topic,app(v('response'),v('person'),v('topic'),v('first'))),
        app(v('response'),v('person'),v('topic'),v('last')))))))
    bounded=every(both(inside('first'),inside('last'),k('rl5',v('history'),v('before'),v('first'),v('last'))),
        op('u',k('hc',k('ha',score('first'),v('bound')),score('last'))))
    between=lambda first,last:quant('g','middle','d',both(inside('middle'),
        app(v('before'),v(first),v('middle')),app(v('before'),v('middle'),v(last)),
        k('hc',score(first),score('middle')),k('hc',score('middle'),score(last))))
    resolved=every(both(ordered,k('hc',k('ha',score('first'),v('bound')),score('last'))),between('first','last'))
    text+=definition('rxn',params(FIELDS),both(k('rxm',*av(FIELDS)),retained,bounded,resolved,between('start','end')))
    return text


def additions():
    providers=[('population','h[a d] j[a]'),('members','h[a a d] c'),('topics','h[a a d] j[a]'),
        ('scope','h[a a d a] c'),('bound','h[a d] b'),('probe','h[a a a d '+STATE+'] d'),
        ('begin','h[a d d '+STATE+'] d'),('end','h[a d d '+STATE+'] d'),
        ('history','h[a d d '+STATE+' d] c'),('before','h[a d d '+STATE+' d d] c')]
    text=''.join(primitive('ian'+n,t) for n,t in providers)
    scene=k('ianprobe',v('community'),v('person'),v('topic'),v('point'),v('state'))
    response=quant('g','judgment','a',both(k('rcr',v('person'),v('judgment'),scene,
        *['p '+n for n in ('ab','ac','fa','fb','fc','fd','ad')]),k('fb',v('judgment'),v('topic'),scene)))
    fields='community a person a topic a point d state '+STATE
    text+=definition('ianresponse',fields,both(k('aa',v('person')),k('iampresented',v('person'),v('topic'),scene),response))
    text+=definition('ianassessed',fields,both(k('aa',v('person')),k('iampresented',v('person'),v('topic'),scene),
        k('iamclassified',v('person'),v('topic'),scene)))
    context=av(CONTEXT)
    bindings=dict(population=k('ianpopulation',v('community'),v('start')),
        people='i[person a][k ianmembers[v community v person v start]]',
        topics='i[person a][k iantopics[v community v person v start]]',
        scope='i[person a topic a][k ianscope[v community v person v start v topic]]',
        history='i[point d]['+k('ianhistory',*context,v('state'),v('point'))+']',
        before='i[left d right d]['+k('ianbefore',*context,v('state'),v('left'),v('right'))+']',
        start=k('ianbegin',*context,v('state')),end=k('ianend',*context,v('state')),
        bound=k('ianbound',v('community'),v('start')),
        classified='i[person a topic a point d][k ianassessed[v community v person v topic v point v state]]',
        response='i[person a topic a point d][k ianresponse[v community v person v topic v point v state]]')
    for name,target in (('reviewed','rxm'),('change','rxn')):
        text+=definition('ian'+name,params(CONTEXT)+' state '+STATE,k(target,*[bindings[n] for n,t in FIELDS]))
    text+='r ianreport[a a i b[h[a d d '+STATE+'] c] a d] c.'
    text+=definition('ianattribution','',k('ianreport',k('iagnode'),k('wa'),'r b[p ianchange]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm','hf','ta','rlz','rl5'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[w[k iamattribution[]][k ianattribution[]]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='fixed_cohort_response_growth_candidate_not_collective_causality',parent=PARENT,document=SOURCE,
        definitions={
            'rxk':'非空で重複のない構成員列が同じ範囲を完全列挙し、各構成員の非空の判断対象列も、その人の対象範囲を完全に列挙する。人と対象の組を、別の一個体へ符号化せず保持する。',
            'rxl':'各人の各判断対象について応答が成立する組の数を、二重の有限畳み込みで求める。人数そのものではなく、人と対象の組の数であり、同じ話題でも別の人の応答は別に数える。',
            'rxm':'rxkの同じ二範囲と、始点・終点を含む厳密な全順序の履歴、正の増加上限を要求する。区間内の全ての人と対象の組を分類済みとする。応答の成立や増加を要求しない。',
            'rxn':'rxmのもとで以前に成立した同じ人・対象への応答を失わず、二回以上の厳密な件数増加と、隣接点での上限を要求する。上限を超える区間には中間値を要求し、履歴の隙間だけで急増を許さない。',
            'ianresponse/ianassessed':'同じ共同体・人・対象・時点・モデルの解に対応する仮定場面で、前段と同じrcrの実際の判断と対象への言及を確認する。提示と分類の有無は応答の真偽と分ける。',
            'ianreviewed/ianchange':'共同体の構成員と各人の判断対象を元の開始点で固定し、各解の同じ履歴で評価可能性と集団の応答拡大を別々に求める。人ごとの二段階の拡大を全員に要求せず、別の人に一回ずつ増える場合も表せる。',
            'ianattribution':'前段の個人についての部分注記を保存し、集団の変化を記述する関数の階数1の引用を同じ著者・箇所・文脈へ追加する。二つの注記を同一の因果主張へ統合したとはしない。'},
        inputs={
            'population/members':'同じ共同体と基準時点における構成員の全範囲。現在の構成員の増減に応じて成功者だけへ交換しない。法的市民権、国家の成立、民衆の社会学的境界はこの所属関係だけで定義しない。',
            'topics/scope/bound':'各人の同じ判断対象の列・範囲と、集団全体での一段階の増加上限。固定基準で選び、介入側によって変えない。人ごとに異なる対象を許すが、比較の妥当性は別に必要。',
            'probe/history/before/begin/end':'各モデルの解を、同じ共同体・元の区間に対応する仮定場面と履歴へ結ぶ。人と対象を照合し、仮定場面の判断を現実の判断へ移さない。'},
        limitations=[
            '固定した有限の構成員と対象についての強い単調な応答拡大である。集団の一つの候補尺度であり、民衆の態度の全意味や多数派の賛同、全員の変化を意味しない。',
            '応答対象が多い人は総件数へ多く寄与し得る。人数比、各人を等しく重み付けした平均、集団的意思決定とは別であり、その差を隠さない。',
            '対象ごとの理由ある判断rcrを用いるが、心理的態度、思考一般、自由一般と原文の語義の全体は前段から未確定である。',
            '構成員の出入りや死亡を含む可変母集団の変化はこの固定集団の比較とは分ける。期間の途中で見えなくなった人を除外しないため、その評価が欠ければ評価済みとはしない。',
            '集団の応答拡大を思考の発展・集団の行為能力・政府の原則へ結ぶ一つの因果条件への統合は残る。個人への媒介条件と並べた注記を統合の完成とはしない。',
            '新しい原文範囲と意味確認済み区間は加算しない。有限診断は現実の民衆全体の調査、原文解釈の一意性、全文の意味一致を証明しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
