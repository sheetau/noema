"""Keep a rooted, scoped delegation path distinct from command conformity."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_joint_readiness import BASE,av
from scripts.compose_community_continuity import POSSIBLE
from scripts.compose_commanded_protection import COMMON,COMMANDS,MEMBER,READY
from scripts.compose_described_norms import DESCRIPTION,TRUE

PARENT='examples/v016/commanded-protection.noema'
PARENT_EXAMPLE='examples/v016/commanded-protection-example.noema'
LIBRARY='examples/v016/command-authority.noema'
CORE='examples/v016/command-authority-core.noema'
EXAMPLE='examples/v016/command-authority-example.noema'
BASIS='data/command-authority-basis-v1.json'
INSTRUCTION=[('institution','a'),('commander','a'),('group','a'),('person','a'),('role','a'),('activity','a'),
    ('code',DESCRIPTION),('sign','c'),('anchor','d')]
AUTHORITY=[('roots','h[a a a a a a '+DESCRIPTION+' c d] c'),('delegable','h[a a a a a a '+DESCRIPTION+' c d] c'),
    ('delegated','h[a a a a a a a '+DESCRIPTION+' c d] c')]
PATH=INSTRUCTION+[('chain','j[a]')]+AUTHORITY
EXTRA=[('institution','a'),('paths','h[a a a a a d] j[a]')]+AUTHORITY
AUTHORIZED=MEMBER+EXTRA
GROUP=READY+EXTRA
CONSUMER='h[c a j[a]] c'
STATE='h['+CONSUMER+'] c'


def definitions():
    tail=[v(n) for n in ('group','person','role','activity','code','sign','anchor')]
    root=app(v('roots'),v('institution'),v('node'),*tail)
    delegation=both(app(v('delegable'),v('institution'),v('last'),*tail),
        app(v('delegated'),v('institution'),v('last'),v('node'),*tail))
    empty=op('e','d[v seen]','n p a b')
    valid=both(v('valid'),op('u',k('hg',v('seen'),v('node'))),
        op('x',both(empty,root),both(op('u',empty),delegation)))
    initial='i[consume '+CONSUMER+']['+app(v('consume'),TRUE,v('commander'),'l[a][]')+']'
    inner='i[valid c last a seen j[a]]['+app(v('consume'),valid,v('node'),'m[v seen][l[a][v node]]')+']'
    step='i[state '+STATE+' node a][i[consume '+CONSUMER+']['+app(v('state'),inner)+']]'
    finish='i[valid c last a seen j[a]]['+both(v('valid'),op('u',empty),op('e',v('last'),v('commander')))+']'
    text=definition('rvi',params(PATH),app('q[v chain]['+initial+']['+step+']',finish))
    selectors=[app(v(n),v('planner'),v('group'),v('person'),v('plan'),v('item'),v('anchor')) for n in
        ('commandroles','commandactions','commandcodes','commandsigns')]
    path=app(v('paths'),v('planner'),v('group'),v('person'),v('plan'),v('item'),v('anchor'))
    authorized=k('rvi',v('institution'),v('planner'),v('group'),v('person'),*selectors,v('anchor'),path,*av(AUTHORITY))
    item=app(v('commanditems'),v('planner'),v('group'),v('person'),v('plan'),v('item'),v('anchor'))
    text+=definition('rvj',params(AUTHORIZED),quant('f','item','a',op('y',item,authorized)))
    text+=definition('rvk',params(AUTHORIZED),'b point['+both(k('rvj',*av(AUTHORIZED)),op('t',k('rvf',*av(MEMBER)),v('point')))+']','e')
    goals='i[commander a cohort a person a strategy a start d]['+k('rvk',v('commander'),v('cohort'),v('person'),v('strategy'),v('start'),*av(COMMANDS+EXTRA))+']'
    def invoke(name,fields):return k(name,*[goals if n=='goals' else v(n) for n,t in fields])
    scope='i[person a]['+app(v('membersof'),v('group'),v('person'),v('anchor'))+']'
    text+=definition('rvl',params(GROUP),both(k('rup',v('members'),scope,v('criterion')),invoke('rut',BASE),invoke('rve',POSSIBLE)))
    return text


def primitive(name,sort):
    if not sort.startswith('h['):return 'r '+name+'[] '+sort+'.'
    depth=1
    for pos in range(2,len(sort)):
        depth+=(sort[pos]=='[')-(sort[pos]==']')
        if not depth:break
    return 'r '+name+'['+sort[2:pos]+'] '+sort[pos+1:].strip()+'.'


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    library=parse(format_graph(parent,'compact')+definitions())
    lookup={d['name']:d for d in library['declarations']};keep=set();pending={'rvi'}
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    core=dict(library,declarations=[d for d in library['declarations'] if d['name'] in keep],statements=[])
    text=format_graph(core,'compact')
    for name,sort in PATH:
        if name!='code':text+=primitive('ja'+name,sort)
    text+='r jaexecuted[a a d] c.'
    text+=definition('jaaction','person a activity a','b point[k jaexecuted[v person v activity v point]]','e')
    text+=definition('jacode','','r[p jaaction]',DESCRIPTION)
    refs={n:('p ja'+n if t.startswith('h[') else 'k ja'+n+'[]') for n,t in PATH}
    expr=k('rvi',*[refs[n] for n,t in PATH]);code='r b['+expr+']'
    text+='q['+expr+'].q[e['+code+']['+code+']].'
    core=parse(text)
    previous=parse((ROOT/PARENT_EXAMPLE).read_text(encoding='utf-8'));example=deepcopy(library)
    names={d['name'] for d in library['declarations']}
    example['declarations']+=[d for d in previous['declarations'] if d['name'] not in names]
    text=format_graph(example,'compact')
    for name,sort in EXTRA:text+=primitive('ja'+name,sort)
    example=parse(text);example['statements']=deepcopy(previous['statements'])
    text=format_graph(example,'compact')
    profile={'community','citizens','activities','possessions','holds','tasks','methods','taskoutcomes','taskselected'}
    command={n for n,t in COMMANDS}|{'criterion'};authority={n for n,t in EXTRA}
    refs={n:('p ' if t.startswith('h[') else 'k ')+('ja' if n in authority else 'jn' if n in command else 'jc' if n in profile else 'jg')+n+('' if t.startswith('h[') else '[]') for n,t in GROUP}
    refs['person']='k jcsubject[]';refs['plan']='k jgplan[]'
    def invoke(name,fields):return k(name,*[refs[n] for n,t in fields])
    text+='q['+invoke('rvj',AUTHORIZED)+'].q[t['+invoke('rvk',AUTHORIZED)+'][k jcpoint[]]].'
    text+='q['+invoke('rvl',GROUP)+'].'
    code='r b['+invoke('rvl',GROUP)+']';text+='q[e['+code+']['+code+']].'
    return {LIBRARY:format_graph(library,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}


def basis():
    return dict(status='scoped_rooted_command_authority_separate_from_conformity',definitions={
        'rvi':'非空で同じ人を重複させない委任列。最初の人は同じ組織・集団・受け手・役割・行為・記述・極性・基準文脈について根拠となる権限を持つ。隣接する各段階で前者がその権限を委任でき、同じ範囲を後者へ委任している。末尾は指定した指揮者である。',
        'rvj':'同じ指揮者・集団・構成員・計画・基準文脈の選択された全要求記録に、rviの委任列がある。要求の存在・一覧の網羅性・履行は単独では含めない。',
        'rvk':'rvjの権限条件と、既存rvfの要求記録の妥当性・網羅性・履行を合わせた内容。',
        'rvl':'同じ構成員の人数基準、全利用可能計画でのrvk、具体的共同体を保護する記録整合性付き計画の存在を合わせる。既存rvhより強い別条件として保持する。'},
        parameters={
            'roots':'組織・権限者・集団・受け手・役割・行為・記述・極性・基準文脈について、委任列の出発点となる根拠。根拠の社会的承認や制度そのものの正当性は別の説明が必要。',
            'delegable':'同じ範囲の権限を他者へ委任できること。要求する権限があるだけで再委任もできるとは推定しない。',
            'delegated':'同じ組織と要求範囲を保持した委任関係。別の受け手・対象・肯否・時点への委任を混ぜない。',
            'paths':'同じ指揮者・集団・構成員・計画・記録・基準文脈の委任列。全ての可能な経路を列挙する必要はない。'},
        limitations=[
            '明示した根拠・再委任可能性・委任関係に相対的な権限モデルである。根拠の事実認定、法体系や道徳的正当性、発令行為や命令の伝達を完了したとは扱わない。',
            '単一要素の列では本人の根拠を要求する。空列や、出発点の根拠がない循環によって権限を作り出さない。同じ人の反復はこの経路表現では拒否する。',
            '権限と履行を区別する。要求の記述だけから権限を推定せず、権限だけから実際の要求や履行も推定しない。',
            '根拠と委任は基準文脈で照合する。複数時点にわたる発令・失効・撤回・継承の履歴や、その優先規則は別に必要。',
            '権限を追加したrvlは独立の強い条件であり、カントの軍隊が手元にあるという表現へ正当性の条件を自動追加しない。既存の権限を問わないrvhも保持する。',
            '軍隊の軍事的役割・訓練・身体的強制、公的平穏の全体と本文への接続は未完。全行為記述への網羅性は有限診断で代用せず、新たな原文対応範囲も追加しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
