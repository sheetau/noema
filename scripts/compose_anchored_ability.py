"""Validate quoted speech references before judging ability or inability."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_shared_quotation import TEMPLATE
from scripts.compose_utterance_ability import LIBRARY as PREVIOUS,EXAMPLE as PARENT,GOAL,EVALUATION

LIBRARY='examples/v016/anchored-ability.noema'
EXAMPLE='examples/v016/anchored-ability-example.noema'
BASIS='data/anchored-ability-basis-v1.json'
IDENTITY=[('actor','a'),('start','d'),('audience','h[a] c'),('speaker','i b[a]'),('hearers','i b[h[a d] c]'),('context','i b[d]')]
GOAL_FIELDS=IDENTITY+[('template',TEMPLATE)]+GOAL[3:]
BOUND=GOAL_FIELDS+EVALUATION[1:]
ONLY=[('population','h[a] c'),('eligible','h[a] c'),('start','d'),('audiencefor','h[a a] c'),
      ('speakerfor','h[a] i b[a]'),('hearersfor','h[a] i b[h[a d] c]'),('contextfor','h[a] i b[d]')]+GOAL_FIELDS[6:]+EVALUATION[1:]

def av(fields):return [v(n) for n,_ in fields]

def definitions():
    match=quant('f','recipient','a',op('e',app(v('audience'),v('recipient')),
        app('s[v hearers]',v('recipient'),v('start'))))
    text=definition('ruj',params(IDENTITY),both(op('e',v('actor'),'s[v speaker]'),op('e',v('start'),'s[v context]'),match))
    messages=app(v('template'),v('speaker'),v('hearers'),v('context'))
    text+=definition('ruk',params(GOAL_FIELDS),k('rue',v('actor'),messages,v('audience'),*av(GOAL[3:])),'e')
    for name,base in [('rul','xd'),('rum','xg')]:
        assessment=k(base,v('actor'),k('ruk',*av(GOAL_FIELDS)),v('start'),*av(EVALUATION[1:]))
        text+=definition(name,params(BOUND),both(k('ruj',*av(IDENTITY)),assessment))
    refs={'actor':v('actor'),'audience':'i[recipient a]['+app(v('audiencefor'),v('actor'),v('recipient'))+']'}
    refs.update({n:app(v(n+'for'),v('actor')) for n in ('speaker','hearers','context')})
    arguments=[refs.get(n,v(n)) for n,_ in BOUND]
    aligned=k('ruj',*[refs.get(n,v(n)) for n,_ in IDENTITY])
    for name,condition in [('run',op('y',k('rul',*arguments),app(v('eligible'),v('actor')))),
                           ('ruo',op('y',op('u',app(v('eligible'),v('actor'))),k('rum',*arguments)))]:
        text+=definition(name,params(ONLY),quant('f','actor','a',op('y',app(v('population'),v('actor')),both(aligned,condition))))
    return text

def example_refs():
    refs={'actor':'k juperson[]','start':'k juanchor[]','audience':'p juaudience','speaker':'k jbspeaker[k juperson[]]',
          'hearers':'k jbhearers[k juperson[]]','context':'k jbcontext[k juperson[]]','template':'p hzsquotation','eventsfor':'p juevents'}
    refs.update({n:'p ju'+n for n,_ in GOAL[4:]+EVALUATION[1:]})
    return refs

def build():
    old=parse((ROOT/PREVIOUS).read_text(encoding='utf-8'));library=parse(format_graph(old,'compact')+definitions())
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    text=format_graph(doc,'compact')+definitions()
    text+=definition('jbspeaker','actor a','k jureference[v actor r b[k juperson[]] r b[k juother[]]]','i b[a]')
    text+=definition('jbhearers','actor a','r b[p jupeople]','i b[h[a d] c]')
    text+=definition('jbcontext','actor a','r b[k juanchor[]]','i b[d]')
    refs=example_refs()
    for name,fields in [('ruj',IDENTITY),('rul',BOUND),('rum',BOUND)]:text+='q['+k(name,*[refs[n] for n,_ in fields])+'].'
    only=refs|dict(population='p jupopulation',eligible='p jueligible',audiencefor='p juaudiencefor',speakerfor='p jbspeaker',hearersfor='p jbhearers',contextfor='p jbcontext')
    for name in ('run','ruo'):text+='q['+k(name,*[only[n] for n,_ in ONLY])+'].'
    for name in ('xd','xg'):text+='q['+k(name,refs['actor'],k('ruk',*[refs[n] for n,_ in GOAL_FIELDS]),refs['start'],*[refs[n] for n,_ in EVALUATION[1:]])+'].'
    quoted='r c['+k('rul',*[refs[n] for n,_ in BOUND])+']'
    text+='q[e['+quoted+']['+quoted+']].'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}

def basis():
    return dict(status='aligned_quotation_references_required_for_both_ability_polarities',parent=PARENT,
        definitions={
            'ruj':'引用の話者記述が評価対象者を、文脈記述が能力評価の基準文脈を指し、引用の聞き手条件がその文脈で実際に指定した聞き手範囲と一致する。',
            'ruk':'同じ三つの参照記述を引用ひな形に渡し、その発話列を評価対象者が指定した聞き手へ順序付きで提示する目標内容を作る。この定義単独では参照整合を要求しない。',
            'rul':'rujの整合性と、rukの目標を達成する利用可能な方法があるという既存xdの条件をともに要求する。',
            'rum':'rujの整合性と、全方法の評価範囲が整合し達成方法がないという既存xgの条件をともに要求する。参照不整合を不可能の証拠としない。',
            'run':'全対象者の参照整合を要求したうえで、発言できる人への必要条件を述べる。参照不整合によるrulの偽から限定を空虚に成立させない。',
            'ruo':'全対象者の参照整合を要求したうえで、条件を満たさない人についてrumによる不可能の確認を要求する。'},
        scope={
            'speaker/context':'記述の文字列一致ではなく、同じ解釈内での指示先の一致を検査する。異なる閉じた記述が同じ対象を指すことは許す。',
            'hearers':'指定した基準文脈における範囲の一致であり、別の状況も含む関数全体の同一性は要求しない。余分な聞き手や欠けた聞き手を許さない。',
            'template':'同じ参照記述を受け取って発話記述列を構成する関数。任意の関数が引数を適切に使うことまで型だけで保証しない。作例は本文の実際のhzsquotationを使う。'},
        limitations=[
            'この一致は今回の自己発話ひな形との接続条件であり、他人の発言や別時点の内容を引用する一般の能力を禁止する規則ではない。rukではそのような発言自体も記述できる。',
            '妥当な参照であること、達成方法があること、達成方法がないと確認できることを区別する。参照不整合の場合はrulとrumがともに偽になる。未知の参照は偽へ補わず評価を拒否する。',
            '同じ対象を指す別記述を認めても、引用内容の記述自体を自動で同義化・書き換えはしない。どの記述が発言されたかは引き続き保持する。',
            '段階1の参照記述を評価するため、結果を引用する場合は段階2を使う。引用の構成時には能力や参照を評価しない。',
            '聞き手の一致は指定文脈だけに関する。時間経過による聞き手の変化や指示の同定そのものの社会的説明は未完。',
            '能力評価に用いる方法・結果・評価基準の妥当性、政治的に発言できること、原文の啓蒙・軍隊・平穏の条件と上位主張への接続は残る。新たな原文対応範囲は加えない。'])

def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))

if __name__=='__main__':main()
