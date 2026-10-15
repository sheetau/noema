"""Give a collective protection target a fixed community, activities and holdings."""
import json
from copy import deepcopy

from noema.constructed import parse, format_graph
from scripts.compose_collective_protection import ROOT, OBSERVED, OBSERVED_POSSIBLE
from scripts.compose_joint_readiness import av
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params

PARENT = 'examples/v016/collective-protection.noema'
PARENT_EXAMPLE = 'examples/v016/collective-protection-example.noema'
ABILITY = 'examples/v013/contextual-ability.noema'
LIBRARY = 'examples/v016/community-continuity.noema'
EXAMPLE = 'examples/v016/community-continuity-example.noema'
BASIS = 'data/community-continuity-basis-v1.json'
TASKS = [('tasks','h[a a] e'), ('methods','h[a a a d] c'),
         ('taskoutcomes','h[a a a d d] c'), ('taskselected','h[a a a d d] c')]
CAPABILITY = [('person','a'), ('activity','a'), ('point','d')] + TASKS
PROFILE = [('community','a'), ('anchor','d'), ('citizens','h[a a d] c'),
           ('activities','h[a a a d] c'), ('possessions','h[a a a d] c'), ('holds','h[a a d] c')] + TASKS
PROTECTED = [(n,t) for n,t in OBSERVED if n != 'activity'] + [(n,t) for n,t in PROFILE if n != 'anchor']
POSSIBLE = [(n,t) for n,t in OBSERVED_POSSIBLE if n != 'activity'] + [(n,t) for n,t in PROFILE if n != 'anchor']


def definitions():
    bound = []
    for name, fields in [('methods','actor a method a start d'),
                         ('taskoutcomes','actor a method a start d end d'),
                         ('taskselected','actor a method a start d end d')]:
        args = [v('actor'),v('activity'),v('method'),v('start')]
        if name != 'methods': args += [v('end')]
        bound.append('i['+fields+']['+app(v(name),*args)+']')
    text = definition('rva', params(CAPABILITY), k('xd',v('person'),app(v('tasks'),v('person'),v('activity')),v('point'),*bound))
    citizen = app(v('citizens'),v('community'),v('person'),v('anchor'))
    chosen = app(v('activities'),v('community'),v('person'),v('activity'),v('anchor'))
    capability = both(k('rva',v('person'),v('activity'),v('anchor'),*av(TASKS)),
                      k('rva',v('person'),v('activity'),v('point'),*av(TASKS)))
    possession = app(v('possessions'),v('community'),v('person'),v('thing'),v('anchor'))
    retained = both(app(v('holds'),v('person'),v('thing'),v('anchor')),app(v('holds'),v('person'),v('thing'),v('point')))
    individual = both(quant('g','activity','a',chosen), quant('f','activity','a',op('y',chosen,capability)),
                      quant('f','thing','a',op('y',possession,retained)))
    text += definition('rvb', params(PROFILE+[('point','d')]), both(quant('g','person','a',citizen),
        quant('f','person','a',op('y',citizen,individual))))
    text += definition('rvc', params(PROFILE), 'b point['+k('rvb',*av(PROFILE),v('point'))+']','e')
    for name,target,fields,old in [('rvd','ruy',PROTECTED,OBSERVED),('rve','ruz',POSSIBLE,OBSERVED_POSSIBLE)]:
        arguments = [k('rvc',*av(PROFILE)) if n == 'activity' else v(n) for n,t in old]
        text += definition(name,params(fields),k(target,*arguments))
    return text


def build():
    parent = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    ability = parse((ROOT/ABILITY).read_text(encoding='utf-8'))
    parent['declarations'] += [d for d in ability['declarations'] if d['name'] in ('xa','xd')]
    library = parse(format_graph(parent,'compact')+definitions())
    previous = parse((ROOT/PARENT_EXAMPLE).read_text(encoding='utf-8'))
    inherited = {d['name'] for d in library['declarations']}
    example = deepcopy(library)
    example['declarations'] += [d for d in previous['declarations'] if d['name'] not in inherited and d['name'] != 'jgactivity']
    text = format_graph(example,'compact')
    refs = {'anchor':'k jganchor[]','tasks':'p jctasks'}
    for name,sort in PROFILE+[('subject','a'),('task','a'),('point','d')]:
        if name in refs: continue
        symbol = 'jc'+name
        if sort.startswith('h['):
            depth = 1
            for pos in range(2,len(sort)):
                depth += (sort[pos]=='[') - (sort[pos]==']')
                if not depth: break
            text += 'r '+symbol+'['+sort[2:pos]+'] '+sort[pos+1:].strip()+'.'
            refs[name] = 'p '+symbol
        else:
            text += 'r '+symbol+'[] '+sort+'.';refs[name] = k(symbol)
    text += 'r jcachieved[a a d] c.'
    text += definition('jctasks','person a activity a','b point[k jcachieved[v person v activity v point]]','e')
    text += definition('jgactivity','',k('rvc',*[refs[n] for n,t in PROFILE]),'e')
    oldrefs = {n: ('p jg'+n if t.startswith('h[') else 'k jg'+n+'[]') for n,t in OBSERVED}
    merged = oldrefs | refs
    example = parse(text)
    example['statements'] = deepcopy(previous['statements'][:4])
    text = format_graph(example,'compact')
    def invoke(name,fields): return k(name,*[merged[n] for n,t in fields])
    text += 'q['+invoke('rvd',PROTECTED)+'].q['+invoke('rve',POSSIBLE)+'].'
    code = 'r b['+invoke('rvd',PROTECTED)+']'
    text += 'q[e['+code+']['+code+']].'
    text += 'q[t[k jgactivity[]][k jganchor[]]].q[t[k jgactivity[]][k jcpoint[]]].'
    text += 'q['+k('rva',refs['subject'],refs['task'],refs['point'],*[refs[n] for n,t in TASKS])+'].'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}


def basis():
    return dict(status='community_activity_and_holding_continuity_not_full_public_peace', definitions={
        'rva':'同じ人・活動・評価時点に方法と結果評価を束縛して既存xdを適用する。その人の活動内容を満たす方法があり、非空で整合した全評価結果で成功する。',
        'rvb':'基準時点で選んだ非空の共同体構成員について、各人の指定活動は非空で、その全活動が基準時点にも評価時点にも可能であり、指定した全保有物を同じ人が両時点で保有する。',
        'rvc':'共同体・構成員・活動・保有物の選択を同じ基準時点へ固定したrvbの内容。結果に応じて失敗した人や失った物を対象から外さない。',
        'rvd':'rvcを共同保護ruyの共通目的に接続する。同じ内容が計画の評価結果、保護の介入比較、記録適合の全てで使われる。',
        'rve':'同じ保護対象と機構のもとでrvdの条件を満たす計画が存在する。'},
        parameters={
            'citizens':'共同体と人と時点の所属関係。法的市民権を自動的に意味せず、保護対象の居住者等の範囲として解釈する。',
            'activities/possessions':'共同体・人・対象・基準時点で指定する維持対象。全活動や全所有物を暗黙に列挙したとはしない。',
            'holds':'人が物を保有するという状態関係。権利の正当性や所有法の理論をこの関係だけで定義したとはしない。',
            'tasks':'各人・活動の達成内容。例では同じ本人と活動の達成関係から構成し、実際の実行を能力の条件にはしない。'},
        lexical_context={
            'source':'https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_1_2_2757',
            'entry':'Adelung, Der Friede, senses 1.1 and 1.2',
            'accessed':'2026-10-15',
            'use':'公共の平穏・安全を人の安全と財産の安定へ関連付ける語義の参考。Friedeとカントのöffentliche Ruheを完全同義とせず、この形式化を辞書の定義そのものとも扱わない。'},
        limitations=[
            '共同体の指定された活動可能性と保有を維持する一つの具体的な目標内容である。公的平穏の全語義、暴力・騒擾の不在、身体安全や制度秩序を完成させていない。',
            '能力は指定方法と結果評価に相対的であり、現実の全実行可能性や行為の法的許可を意味しない。実際に活動したことや全員共通の一方法も要求しない。',
            '活動と保有物の選択を基準時点に固定するが、その選択の社会的妥当性や完全性を証明しない。移転・消費・任意の放棄等を許す別の目標をこの維持条件と同一視しない。',
            '保有物がない人も対象にできる。構成員が空の共同体や活動対象が空の人を空虚な維持成功とは扱わない。',
            '保護側集団groupと保護される共同体communityは別の引数である。軍隊の制度的位置、指揮権、公的平穏と本文主張への接続は残る。新しい原文対応範囲は加えない。'])


def main():
    for path,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        target = ROOT/path
        if target.exists(): assert target.read_text(encoding='utf-8')==body,path
        else:
            with target.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
        print(path,len(body))


if __name__=='__main__': main()
