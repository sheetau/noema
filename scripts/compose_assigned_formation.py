"""Describe an assigned formation without asserting mission success or legality."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_protective_qualification import SOURCE as PARENT,QUALIFICATION

LIBRARY='examples/v016/assigned-formation.noema'
EXAMPLE='examples/v016/assigned-formation-example.noema'
SOURCE='examples/v016/kant-assigned-formation.noema'
CORE='examples/v016/assigned-formation-core.noema'
BASIS='data/assigned-formation-basis-v1.json'
MISSION='i[h[a a] e]'
CONTEXT=[('institution','a'),('group','a'),('beneficiary','a'),('mission',MISSION),('anchor','d')]
ROLE=[('offices','h[a a a d] c'),('holders','h[a a a a d] c'),('responsibilities','h[a a a a '+MISSION+' d] c')]
RELATIONS=[('members','h[a a d] c'),('constituted','h[a a d] c'),('assigned','h[a a a '+MISSION+' d] c')]+ROLE
DIRECTS=[('directs','h[a a a d] c')]
POSITION=[('person','a'),('role','a')]+CONTEXT+ROLE
FORMATION=CONTEXT+RELATIONS
COMMANDED=[('actor','a')]+FORMATION+DIRECTS


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    text=definition('rvz',params(POSITION),both(
        app(v('offices'),v('role'),v('institution'),v('group'),v('anchor')),
        app(v('holders'),v('person'),v('role'),v('institution'),v('group'),v('anchor')),
        app(v('responsibilities'),v('role'),*av(CONTEXT))))
    member=app(v('members'),v('group'),v('person'),v('anchor'))
    position=quant('g','role','a',k('rvz',*av(POSITION)))
    text+=definition('rwa',params(FORMATION),both(
        app(v('constituted'),v('institution'),v('group'),v('anchor')),
        app(v('assigned'),*av(CONTEXT)),quant('g','person','a',member),quant('f','person','a',op('y',member,position))))
    leader=quant('g','role','a',both(k('rvz',v('actor'),v('role'),*av(CONTEXT+ROLE)),
        app(v('directs'),v('role'),v('institution'),v('group'),v('anchor'))))
    text+=definition('rwb',params(COMMANDED),both(k('rwa',*av(FORMATION)),leader))
    return text


def additions():
    text='r hzyinstitution[a a d] a.'
    for name,sort in RELATIONS[1:]+DIRECTS:
        text+='r hzy'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    refs={n:'p hzy'+n for n,t in RELATIONS+DIRECTS}
    refs.update(actor=v('actor'),institution=k('hzyinstitution',v('actor'),v('group'),v('anchor')),
        group=v('group'),beneficiary=v('community'),mission=v('mission'),anchor=v('anchor'),
        members=k('hzxmembersof',v('actor'),v('group'),v('anchor')))
    text+=definition('hzyformation','mission '+MISSION+' actor a group a community a anchor d',k('rwb',*[refs[n] for n,t in COMMANDED]))
    text+=definition('hzyqualified','mission '+MISSION+' remaining '+QUALIFICATION+' actor a group a community a anchor d',both(
        k('hzyformation',*map(v,('mission','actor','group','community','anchor'))),app(v('remaining'),*map(v,('actor','group','community','anchor')))))
    text+=definition('hzyonly','mission '+MISSION+' remaining '+QUALIFICATION+' anchor d',
        k('hzxonly','i[actor a group a community a point d]['+k('hzyqualified',*map(v,('mission','remaining','actor','group','community','point')))+']',v('anchor')))
    text+='r hzyannotation[a a i c[h['+MISSION+' '+QUALIFICATION+' d] c] a d] c.'
    text+=definition('hzyattribution','',k('hzyannotation','k hztnode[]','k wa[]','r c[p hzyonly]','k hztscope[]','k wh[]'))
    return text


def build():
    library=parse('p:'+definitions());text=format_graph(library,'compact')
    for name in ('actor','institution','group','beneficiary'):text+='r jp'+name+'[] a.'
    text+='r jpanchor[] d.r jpachieved[a a d] c.'
    text+=definition('jpmission','group a beneficiary a','b point[k jpachieved[v group v beneficiary v point]]','e')
    text+=definition('jpalias','group a beneficiary a','k jpmission[v group v beneficiary]','e')
    for name,sort in RELATIONS+DIRECTS:text+='r jp'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    refs={n:'p jp'+n for n,t in RELATIONS+DIRECTS}
    refs.update({n:'k jp'+n+'[]' for n in ('actor','institution','group','beneficiary','anchor')});refs['mission']='r[p jpmission]'
    questions=[k('rwa',*[refs[n] for n,t in FORMATION]),k('rwb',*[refs[n] for n,t in COMMANDED]),
        't[k jpmission[k jpgroup[] k jpbeneficiary[]]][k jpanchor[]]']
    questions+=['e[r['+questions[1]+']][r['+questions[1]+']]']
    example=parse(text+''.join('q['+x+'].' for x in questions))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);statements=doc['statements'];doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k hzyattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in [(LIBRARY,library),(EXAMPLE,example),(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='assigned_formation_not_complete_military_definition',definitions={
        'rvz':'同じ制度・集団・対象共同体・任務記述・文脈について、役職が置かれ、本人が保持し、その役職に任務上の責任がある。',
        'rwa':'制度が集団を構成し、対象共同体と任務を割り当てている。その文脈の構成員は非空で、各人がrvzを満たす役職を少なくとも一つ持つ。全員が同じ役職を持つ必要はない。',
        'rwb':'rwaと同じ制度・集団・任務で、指定した本人が責任を持つ役職を保持し、その役職が同じ集団を指揮する役割を持つ。指揮者が部隊の構成員であることは要求しない。',
        'hzyformation':'前段の保護条件と同じ構成員の関係を用い、同じ候補者・集団・共同体・文脈へrwbを適用する。',
        'hzyqualified':'hzyformationと残余の条件を同じ候補者・集団・共同体・文脈で合わせる。',
        'hzyonly':'この資格をhzxonlyへ渡す。軍事的任務の記述missionと残余remainingは未充足引数として保持する。',
        'hzyattribution':'更新した部分ひな形を記述として帰属し、任務の達成・遂行能力・法的正当性を断言しない。'},
        parameters={
            'constituted':'制度の構成・編成の扱いにおいて、当該集団が一つの単位として置かれているという関係。実際の保護能力や外部法体系による承認ではない。',
            'assigned':'制度が同じ集団に、同じ対象共同体について、指定した記述の任務を割り当てている関係。現在の実現を含意しない。',
            'offices/holders':'当該制度・集団に置かれた役職と、その時点の保持者。役職と人を同一視せず、複数役職や構成員の交代を許す。',
            'responsibilities':'役職が、指定した対象共同体・任務に関わる責任を負う関係。全員が任務全体を単独で遂行する義務や能力ではない。',
            'directs':'役職の機能として同じ集団の指揮を担当する関係。実際の発令、命令の正当性・履行は別の条件である。'},
        unresolved=[
            '任務を持つ組織の部分構造であり、軍隊を定義し終えたものではない。軍事的任務の内容、武力・戦闘・防衛と非軍事的救援の区別はmissionへ具体化する必要がある。',
            '同時代辞書のHeer項を調べたが、直接本文の取得は確認できなかった。検索断片を語義確定の根拠にはしない。本構成は組織役割の操作的な部分候補である。',
            '編成・任務割当・役職・保持・責任・指揮担当は意味規約を持つ入力関係であり、制度の成立過程や社会的承認、個々の指揮権の根拠は残る。',
            '任務記述を実行評価しない。任務の達成・能力・正当性を割当から導かない。同じ内容を持つ別記述への割当の移行には別の同一視が必要。',
            '全構成員が任務に関わる役職を持つという組織化の候補であり、一時的な未配置や名簿の不備を含む軍隊一般の必要十分条件ではない。',
            '公的平穏の全条件、軍事的内容、前段の保護・発言能力との統合解釈、原文単位全体の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
