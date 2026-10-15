"""Bind a protected community and collective plans to the same command records."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both
from scripts.compose_situated_criticism import params
from scripts.compose_joint_readiness import BASE,av
from scripts.compose_community_continuity import PROTECTED,POSSIBLE
from scripts.compose_described_norms import DESCRIPTION

PARENT='examples/v016/community-continuity.noema'
PARENT_EXAMPLE='examples/v016/community-continuity-example.noema'
OBEDIENCE='examples/v016/scoped-obedience.noema'
LIBRARY='examples/v016/commanded-protection.noema'
EXAMPLE='examples/v016/commanded-protection-example.noema'
BASIS='data/commanded-protection-basis-v1.json'
COMMON=[('planner','a'),('group','a'),('person','a'),('plan','a'),('anchor','d')]
COMMANDS=[('commandrolescope','h[a a a a a d] c'),('commanditems','h[a a a a a d] c'),
    ('commandroles','h[a a a a a d] a'),('commandactions','h[a a a a a d] a'),
    ('commandcodes','h[a a a a a d] '+DESCRIPTION),('commandsigns','h[a a a a a d] c'),
    ('orders','h[a a a a a a '+DESCRIPTION+' c d] c')]
MEMBER=COMMON+COMMANDS
FIXED=[(n,t) for n,t in PROTECTED if n!='goals']+COMMANDS
READY=[(n,t) for n,t in POSSIBLE if n!='goals']+COMMANDS+[('criterion','h[b] c')]


def definitions():
    bound=[]
    for name,t in COMMANDS[:-1]:
        item='role' if name=='commandrolescope' else 'item'
        bound.append('i['+item+' a]['+app(v(name),v('planner'),v('group'),v('person'),v('plan'),v(item),v('anchor'))+']')
    orders='i[issuer a recipient a role a activity a code '+DESCRIPTION+' polarity c context d]['+app(v('orders'),
        v('issuer'),v('group'),v('plan'),v('recipient'),v('role'),v('activity'),v('code'),v('polarity'),v('context'))+']'
    text=definition('rvf',params(MEMBER),k('rty',v('planner'),v('person'),v('anchor'),*bound,orders),'e')
    goals='i[commander a cohort a person a strategy a start d]['+k('rvf',v('commander'),v('cohort'),v('person'),v('strategy'),v('start'),*av(COMMANDS))+']'
    def invoke(name,fields): return k(name,*[goals if n=='goals' else v(n) for n,t in fields])
    text+=definition('rvg',params(FIXED),invoke('rvd',PROTECTED))
    scope='i[person a]['+app(v('membersof'),v('group'),v('person'),v('anchor'))+']'
    text+=definition('rvh',params(READY),both(k('rup',v('members'),scope,v('criterion')),
        invoke('rut',BASE),invoke('rve',POSSIBLE)))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    obedience=parse((ROOT/OBEDIENCE).read_text(encoding='utf-8'))
    names={d['name'] for d in parent['declarations']}
    assert not names.intersection(d['name'] for d in obedience['declarations'])
    parent['declarations']+=obedience['declarations']
    library=parse(format_graph(parent,'compact')+definitions())
    previous=parse((ROOT/PARENT_EXAMPLE).read_text(encoding='utf-8'))
    names={d['name'] for d in library['declarations']}
    example=deepcopy(library)
    example['declarations']+=[d for d in previous['declarations'] if d['name'] not in names and d['name'] not in ('jggoals','jgexecuted')]
    text=format_graph(example,'compact')
    for name,sort in COMMANDS+[('criterion','h[b] c')]:
        if name=='commandcodes':continue
        depth=1
        for pos in range(2,len(sort)):
            depth+=(sort[pos]=='[')-(sort[pos]==']')
            if not depth:break
        text+='r jn'+name+'['+sort[2:pos]+'] '+sort[pos+1:].strip()+'.'
    text+='r jnexecuted[a a d] c.'
    text+=definition('jnact','person a activity a','b point[k jnexecuted[v person v activity v point]]','e')
    text+=definition('jncommandcodes','planner a group a person a plan a item a anchor d','r[p jnact]',DESCRIPTION)
    text+=definition('jggoals',params(COMMON),k('rvf',*av(COMMON),*['p jn'+n for n,t in COMMANDS]),'e')
    example=parse(text)
    example['statements']=deepcopy(previous['statements'][:4])
    text=format_graph(example,'compact')
    profile_names={'community','citizens','activities','possessions','holds','tasks','methods','taskoutcomes','taskselected'}
    refs={n:('p ' if t.startswith('h[') else 'k ')+('jc' if n in profile_names else 'jg')+n+('' if t.startswith('h[') else '[]') for n,t in PROTECTED}
    refs.update({n:'p jn'+n for n,t in COMMANDS+[('criterion','h[b] c')]})
    def invoke(name,fields):return k(name,*[refs[n] for n,t in fields])
    text+='q['+invoke('rvg',FIXED)+'].q['+invoke('rvh',READY)+'].'
    code='r b['+invoke('rvh',READY)+']';text+='q[e['+code+']['+code+']].'
    example=parse(text);example['statements']+=deepcopy(previous['statements'][7:])
    text=format_graph(example,'compact')
    member=[refs['planner'],refs['group'],'k jcsubject[]',refs['plan'],refs['anchor']]+[refs[n] for n,t in COMMANDS]
    text+='q[t['+k('rvf',*member)+'][k jcpoint[]]].q[t['+k('rvf',*member)+'][k jganchor[]]].'
    text+='q['+invoke('rut',BASE)+'].'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}


def basis():
    return dict(status='same_commander_group_plan_requirements_and_community_protection',definitions={
        'rvf':'同じ指揮者・集団・構成員・計画・基準文脈の役割範囲と要求記録をrtyへ結ぶ。要求関係にも集団・計画を固定し、別計画や別の集団の要求を流用しない。',
        'rvg':'rvfを各構成員の目標として、具体的な共同体の活動可能性・保有を保つrvdへ渡す。計画の成功、保護比較、記録適合に同じ要求への適合内容を使う。',
        'rvh':'同じ構成員の人数基準、全利用可能計画での要求適合rut、共同体を保護し記録も整合する計画の存在rveを合わせる。成功した一計画を、全計画での適合へ読み替えない。'},
        parameters={
            'commandrolescope/commanditems':'指揮者・集団・構成員・計画・基準文脈に依存する役割と要求記録の範囲。',
            'commandroles/commandactions/commandcodes/commandsigns':'同じ要求記録の役割・行為・閉じた行為記述・肯否。',
            'orders':'指揮者・集団・計画・受け手・役割・行為・記述・肯否・基準文脈の要求関係。正当な指揮権や実際の発令行為はこの関係だけで説明しない。'},
        limitations=[
            '軍隊という名詞の完成定義ではない。制度的位置、戦闘や身体的強制の能力、訓練、指揮系統、命令の伝達と指揮権の正当性は別に必要。',
            '要求への適合は、命令だから行ったという動機・意図を含まない。空の役割と空の要求なら適合は空虚に成立し得るが、それだけで保護の因果比較は成立しない。',
            'rvhの全計画条件は、指定した利用可能性と評価範囲での強い適合条件である。信頼性や例外の頻度、よく訓練されていることの全意味とは同一視しない。',
            '保存文書の要求網羅性は全行為記述へ量化する。有限診断では二記述に限定したコピーだけを評価し、全域を検証したとは扱わない。全域の直接評価は拒否する。',
            '共同体の維持対象の妥当性、暴力や騒擾の不在、公的平穏の全体、上位の発話可能性と原文への接続は残る。新たな原文対応範囲は追加しない。'])


def main():
    for path,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        target=ROOT/path
        if target.exists():assert target.read_text(encoding='utf-8')==body,path
        else:
            with target.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(path,len(body))


if __name__=='__main__':main()
