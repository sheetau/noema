"""Separate ordered utterance realization, ability and necessary eligibility."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import TRUE
from scripts.compose_choice_permissions import MC
from scripts.compose_contextual_ability import AVAILABLE,OUTCOMES

LIBRARY='examples/v016/utterance-ability.noema'
EXAMPLE='examples/v016/utterance-ability-example.noema'
BASIS='data/utterance-ability-basis-v1.json'
ABILITY='examples/v013/contextual-ability.noema'
PARENT='examples/v016/shared-quotation-core.noema'
SEQ='j['+MC+']'
RELATIONS=[('occurs','h[a d] c'),('agent','h[a a d] c'),('presents','h[a a d] c'),('conveys','h[a '+MC+' d] c'),('before','h[a a d] c')]
UTTERANCE=[('actor','a'),('messages',SEQ),('audience','h[a] c'),('events','j[a]'),('point','d')]+RELATIONS
GOAL=[('actor','a'),('messages',SEQ),('audience','h[a] c'),('eventsfor','h[a d] j[a]')]+RELATIONS
EVALUATION=[('start','d'),('available',AVAILABLE),('outcomes',OUTCOMES),('selected',OUTCOMES)]
CAPABILITY=GOAL+EVALUATION
ONLY=[('population','h[a] c'),('eligible','h[a] c'),('messagesfor','h[a] '+SEQ),('audiencefor','h[a a] c')]+GOAL[3:]+EVALUATION
CONSUMER='h[c j[a]] c'
STATE='h['+CONSUMER+'] c'

def av(fields):return [v(n) for n,_ in fields]

def definitions():
    # A Church-encoded valid-prefix/event-list state retains the index without
    # numeric-domain quantification, arithmetic primitives or new tuple syntax.
    matched='q[v messages][u['+TRUE+']][i[found c message '+MC+']['+op('x',v('found'),both(
        'a[v messages][d[v seen]][v message]',app(v('conveys'),v('event'),v('message'),v('point'))))+']]'
    ordered='q[v seen]['+TRUE+'][i[valid c earlier a]['+both(v('valid'),op('u',op('e',v('earlier'),v('event'))),
        app(v('before'),v('earlier'),v('event'),v('point')),op('u',app(v('before'),v('event'),v('earlier'),v('point'))))+']]'
    received=quant('f','recipient','a',op('y',app(v('audience'),v('recipient')),
        app(v('presents'),v('event'),v('recipient'),v('point'))))
    valid=both(v('valid'),matched,ordered,op('u',app(v('before'),v('event'),v('event'),v('point'))),
        app(v('occurs'),v('event'),v('point')),app(v('agent'),v('actor'),v('event'),v('point')),received)
    initial='i[consume '+CONSUMER+']['+app(v('consume'),TRUE,'l[a][]')+']'
    inner='i[valid c seen j[a]]['+app(v('consume'),valid,'m[v seen][l[a][v event]]')+']'
    step='i[state '+STATE+' event a][i[consume '+CONSUMER+']['+app(v('state'),inner)+']]'
    finish='i[valid c seen j[a]][v valid]'
    folded=app('q[v events]['+initial+']['+step+']',finish)
    text=definition('rud',params(UTTERANCE),both(op('u',op('e','d[v messages]','n p a b')),
        op('e','d[v messages]','d[v events]'),quant('g','recipient','a',app(v('audience'),v('recipient'))),folded))
    values=[v('actor'),v('messages'),v('audience'),app(v('eventsfor'),v('actor'),v('point')),v('point')]+av(RELATIONS)
    text+=definition('rue',params(GOAL),'b point['+k('rud',*values)+']','e')
    for name,base in [('ruf','xd'),('rug','xg')]:
        text+=definition(name,params(CAPABILITY),k(base,v('actor'),k('rue',*av(GOAL)),*av(EVALUATION)))
    args=[v('actor'),app(v('messagesfor'),v('actor')),'i[recipient a]['+app(v('audiencefor'),v('actor'),v('recipient'))+']']+av(GOAL[3:]+EVALUATION)
    weak=op('y',k('ruf',*args),app(v('eligible'),v('actor')))
    strong=op('y',op('u',app(v('eligible'),v('actor'))),k('rug',*args))
    for name,condition in [('ruh',weak),('rui',strong)]:
        text+=definition(name,params(ONLY),quant('f','actor','a',op('y',app(v('population'),v('actor')),condition)))
    return text

def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));old=parse((ROOT/ABILITY).read_text(encoding='utf-8'))
    lib=dict(parent,declarations=[d for d in old['declarations'] if d['name'] in ('xa','xd','xe','xg')],statements=[])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[];names={d['name']:d for d in doc['declarations']}
    for d in lib['declarations']:
        if d['name'] in names:assert names[d['name']]==d
        else:doc['declarations'].append(d)
    text=format_graph(doc,'compact')
    for name,args,result in [('juperson','','a'),('juother','','a'),('juanchor','','d'),('jufirst','','d'),('jusecond','','d'),
        ('jupeople','a d','c'),('juaudience','a','c'),('jupopulation','a','c'),('jueligible','a','c'),
        ('jureference','a i b[a] i b[a]','i b[a]'),('juevents','a d','j[a]')]:
        text+='r '+name+'['+args+'] '+result+'.'
    for name,t in RELATIONS+EVALUATION[1:]:text+='r ju'+name+'['+t[2:t.rfind(']')]+'] '+t[t.rfind(']')+1:].strip()+'.'
    code=k('jureference',v('actor'),'r b[k juperson[]]','r b[k juother[]]')
    text+=definition('jumessages','actor a',k('hzsquotation',code,'r b[p jupeople]','r b[k juanchor[]]'),SEQ)
    text+=definition('juaudiencefor','actor a recipient a','k juaudience[v recipient]')
    refs={'actor':'k juperson[]','messages':'k jumessages[k juperson[]]','audience':'p juaudience','eventsfor':'p juevents','start':'k juanchor[]'}
    refs.update({n:'p ju'+n for n,_ in RELATIONS+EVALUATION[1:]})
    text+='q[t['+k('rue',*[refs[n] for n,_ in GOAL])+'][k jufirst[]]].'
    text+='q[t['+k('rue',*[refs[n] for n,_ in GOAL])+'][k jusecond[]]].'
    for name in ('ruf','rug'):text+='q['+k(name,*[refs[n] for n,_ in CAPABILITY])+'].'
    refs.update(population='p jupopulation',eligible='p jueligible',messagesfor='p jumessages',audiencefor='p juaudiencefor')
    for name in ('ruh','rui'):text+='q['+k(name,*[refs[n] for n,_ in ONLY])+'].'
    text+='q[e[r b['+k('rue',*[refs[n] for n,_ in GOAL])+']][r b['+k('rue',*[refs[n] for n,_ in GOAL])+']]].'
    return {LIBRARY:format_graph(lib,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}

def basis():
    return dict(status='ordered_utterance_realization_and_assessed_ability',parent=PARENT,
        definitions={
            'rud':'非空の発話記述列と同じ長さの相異なる発話出来事列を、各位置で結ぶ。同じ話者・同じ非空の聞き手範囲への提示、各出来事の生起、内容記述の伝達、列内の厳密な順序を要求する。内容の真偽や指令の達成は評価しない。',
            'rue':'同じ話者・発話記述列・聞き手範囲について、状況ごとの出来事列がrudを満たす内容。',
            'ruf':'利用できる方法に、非空で想定結果に含まれる評価範囲があり、その全結果で同じ発話列の提示を実現できる。既存xdの明示した能力評価を用いる。',
            'rug':'利用可能な全方法の評価範囲が整合し、発話列を評価範囲全体で実現する方法がない。未評価と不可能を分ける。',
            'ruh':'指定した人々のうち、rufが成立する人は全員指定条件を満たす。条件を満たす人が必ず言えるという逆向きの含意や、言える人の存在は要求しない。',
            'rui':'指定条件を満たさない全対象者についてrugが成立する。ruhに比べ、不適格者の評価不足を不可能として扱わない強い確認条件。',
            'jumessages':'前段の実際の本文ひな形hzsquotationへ話者・聞き手・基準文脈の閉じた参照を渡し、発話の内容記述列を構成する。'},
        parameters={
            'occurs/agent/presents/conveys/before':'出来事の生起、話者、聞き手への提示、段階1の発話内容記述の伝達、出来事間の順序。伝達の成立と内容の真理を分ける。音声・文字・媒体の実現や解釈を入力関係として残す。',
            'eventsfor':'同じ話者・評価状況で、その提示を構成する出来事列。一般に全出来事を列挙したとはしない。',
            'available/outcomes/selected':'利用可能な方法、その想定結果、能力評価に採用した結果。評価対象の非空性と想定結果への所属を検査する。',
            'eligible':'限定の条件を表す性質。この作例では内容未指定であり、啓蒙・影への恐れ・軍隊を説明済みとはしない。'},
        limitations=[
            '同じ引用を発言できることと、引用内容が真であること、許可を有効に新設すること、聞き手が従うことは別である。今回の目標は順序付き提示の実現。',
            '能力は明示した方法・想定結果・評価範囲に相対的な定義である。政治的に支障なく発言できることや、自然言語のkannの全語義をこの条件へ還元しない。',
            '同じ出来事を二回使うことは拒否するが、同じ発話内容を異なる出来事で繰り返すことは許す。発話以外の出来事の不存在は要求しない。',
            '列内で全ての先行出来事が後続出来事より前であり、逆向きと自己順序がないことを要求する。時間の計測や列外の順序全体の整合性は別。',
            'ruhは採用した能力条件の必要条件だけを述べる。ruiは不適格者の不可能を評価範囲の整合性とともに確認するための別条件。両者を同義とは扱わない。',
            '作例の話者参照関数と聞き手範囲の正しさは別に確認する必要がある。一般の型だけで現実の指示を保証しない。',
            '本文の限定条件、影への恐れ・軍隊・公的平穏・国家との対比、段落全体への帰属は未接続。新たな原文対応範囲は加えない。'])

def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))

if __name__=='__main__':main()
