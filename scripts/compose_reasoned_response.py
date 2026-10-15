"""Fill the mediator with an assessed multi-topic reasoned-response profile."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_mediated_choice import ROOT,SOURCE as PARENT,HIGH,TAIL,STATE,CONTEXT,params,av
from scripts.compose_declining_hindrances import CHECKED,GRADUAL
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/reasoned-response.noema'
SOURCE='examples/v016/kant-reasoned-response.noema'
CORE='examples/v016/reasoned-response-core.noema'
BASIS='data/reasoned-response-basis-v1.json'
FIELDS=[('person','a'),('topics','j[a]'),('scope','h[a] c'),('history','h[d] c'),('before','h[d d] c'),
        ('start','d'),('end','d'),('bound','b'),('classified','h[a a d] c'),('response','h[a a d] c')]


def definitions():
    args=dict(history=v('history'),before=v('before'),start=v('start'),end=v('end'),obstacles=v('topics'),scope=v('scope'),
        assessed='i[topic a point d]['+app(v('classified'),v('person'),v('topic'),v('point'))+']',
        hindering='i[topic a point d]['+op('u',app(v('response'),v('person'),v('topic'),v('point')))+']',bound=v('bound'))
    text=definition('rxi',params(FIELDS),both(k('rl2',*[args[n] for n,t in CHECKED]),k('hc','n p a b',v('bound'))))
    text+=definition('rxj',params(FIELDS),k('rl6',*[args[n] for n,t in GRADUAL]))
    return text


def additions():
    providers=[('topics','h[a d] j[a]'),('scope','h[a d a] c'),('bound','h[a d] b'),
        ('probe','h[a a d '+STATE+'] d'),('presented','h[a a d] c'),('classified','h[a a d] c')]
    text=''.join(primitive('iam'+n,t) for n,t in providers)
    scene=k('iamprobe',v('person'),v('topic'),v('point'),v('state'))
    response=quant('g','judgment','a',both(k('rcr',v('person'),v('judgment'),scene,
        *['p '+n for n in ('ab','ac','fa','fb','fc','fd','ad')]),k('fb',v('judgment'),v('topic'),scene)))
    text+=definition('iamresponse','person a topic a point d state '+STATE,both(k('aa',v('person')),
        k('iampresented',v('person'),v('topic'),scene),response))
    text+=definition('iamassessed','person a topic a point d state '+STATE,both(k('aa',v('person')),
        k('iampresented',v('person'),v('topic'),scene),k('iamclassified',v('person'),v('topic'),scene)))
    context=av(CONTEXT)
    bindings=dict(person=v('person'),topics=k('iamtopics',v('person'),v('start')),
        scope='i[topic a][k iamscope[v person v start v topic]]',
        history='i[point d]['+k('iakhistory',*context,v('state'),v('point'))+']',
        before='i[left d right d]['+k('iakbefore',*context,v('state'),v('left'),v('right'))+']',
        start=k('iakbegin',*context,v('state')),end=k('iakend',*context,v('state')),bound=k('iambound',v('person'),v('start')),
        classified='i[person a topic a point d][k iamassessed[v person v topic v point v state]]',
        response='i[person a topic a point d][k iamresponse[v person v topic v point v state]]')
    for name,target in (('reviewed','rxi'),('change','rxj')):
        text+=definition('iam'+name,params(CONTEXT)+' state '+STATE,k(target,*[bindings[n] for n,t in FIELDS]))
    text+=definition('iamschema','reading '+HIGH+' remaining '+TAIL,
        k('ialschema',v('reading'),'p iamchange','p iamreviewed',v('remaining')))
    text+='r iamreport[a a i c[h['+HIGH+' '+TAIL+'] c] a d] c.'
    text+=definition('iamattribution','',k('iamreport',k('iagnode'),k('wa'),'r c[p iamschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rl2','rl6','hc'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iamattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='explicit_reasoned_response_profile_as_mediator_candidate',parent=PARENT,document=SOURCE,
        definitions={
            'rxi':'同じ本人・判断対象一覧・範囲・履歴・順序について、非空で重複のない完全列挙と、区間内の全対象への応答の分類、正の増加上限を確認する。応答の増加そのものは要求しない。',
            'rxj':'同じ対象範囲で応答が成立しない対象の集合にrl6を適用する。以前の応答を失わず、応答する対象が二回以上増え、隣接点の増加が同じ上限以内であるという強い段階的な変化。',
            'iamresponse':'同じ人に同じ判断対象が提示される仮定場面で、その人が自分の理解力を用い、自分の理由に支持され、他者の指導によらない判断rcrを行い、その判断が同じ提示対象について述べる。別の話題について考えただけでは成立しない。',
            'iamassessed':'同じ人・対象・仮定場面で、提示があり、その応答条件を満たすかどうかが分類済みである。応答の不成立と、提示や評価の不在を区別する。',
            'iamreviewed/iamchange':'実際の開始点で固定した判断対象と上限を、各介入解の同じ履歴へ結ぶ。仮定場面での実際の判断の定義を用い、評価可能性と応答傾向の段階的変化を別々に求める。',
            'iamschema':'前段の未充足だった媒介内容とその評価に、iamchangeとiamreviewedを具体的に渡す。発展、応答傾向、行為能力の増加、残余条件を同じ本人・基準区間で結ぶ。',
            'iamattribution':'候補の心理的内容を具体化した部分ひな形を同じ著者・箇所・範囲・文脈に帰属する。原文の唯一の読みや現実の判断を断定しない。'},
        inputs={
            'topics/scope/bound':'開始点で固定する同じ判断対象の全範囲と一段階の増加上限。対象を成功に合わせて選び直さず、介入側によって容易な話題へ交換しない。',
            'probe':'同じ本人・判断対象について、各時点と介入解に対応する評価場面。実際の現在の場面とは限らない。提示条件を比較できること、場面の選定が妥当であることは解釈の前提。',
            'presented/classified':'同じ本人が同じ対象の判断に直面すること、その場面での応答条件を評価済みであること。未回答や未評価を勝手に独立判断の不成立へ補わない。'},
        limitations=[
            'Sinnesartを、判断対象への理由ある独立した応答の傾向として読む操作的候補。欲求、感情、習慣的な行為、道徳的原則など心理的態度の全側面を尽くさず、唯一の原文解釈とはしない。',
            '有限の同じ判断対象で測る強い包含拡大であり、全ての将来の場面への確率的保証や性格の完全な推定ではない。提示の仕方、難しさ、状況の対応が同じであることの基礎説明は残る。',
            '単発の応答ではなく少なくとも二回の対象集合の拡大を要求するが、連続的な心理変化、応答強度、局所的な後退を含む全ての漸進を表したものではない。',
            '判断は指定した仮定場面で評価し、実際の開始点で既に考えたことや、行為を実行したことは含意しない。独立判断rcrの概念と評価の限定を引き継ぐ。',
            '媒介する変化の独立した時刻、各人と民衆全体の対応、自然の比喩、自由の語義、政府の原則と尊厳は残る。新たな原文範囲や意味確認済み区間は加算しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
