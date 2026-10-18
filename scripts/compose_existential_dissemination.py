"""State unbounded route existence, with one shared departure per origin."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT, closure
from scripts.compose_thinking_disseminators import THINKING, call as k, conjunction as both
from scripts.compose_described_dissemination import PER_PERSON, declaration
from scripts.compose_focused_dissemination import BASE

PARENT = 'examples/v016/kant-conditional-dissemination.noema'
PARENT_BASIS = 'data/conditional-dissemination-basis-v1.json'
FULL = 'examples/v016/kant-existential-dissemination.noema'
CORE = 'examples/v016/existential-dissemination-core.noema'
BASIS = 'data/existential-dissemination-basis-v1.json'
ROUTE = [('origin','a'),('target','a'),('subject','a'),('message','i[h[a] f]'),('state','i[h[a] e]'),
         ('frame','a'),('initial','d'),('anchor','d'),('departure','a'),('prior','d'),('attained','d'),
         ('sender','h[a] a'),('recipient','h[a] a'),('activity','h[a] a'),('point','h[a] d')]
WITNESSES = [('first','a'),('rest','j[a]'),('process','a'),('start','d'),('end','d')]
DEPARTURE = [('departure','a'),('prior','d'),('attained','d')]
SHARED = [('reference','d')] + [(n,t) for n,t in ROUTE if n != 'target'] + [
    ('extent','h[h[a] c h[a] c] c'),('scope','h[a a d] c')]
EXISTENTIAL = [(n,t) for n,t in SHARED if n not in dict(DEPARTURE)]
REMOVED = {'departure','prior','attained','firsts','tails','processes','starts','ends'}
FUTURE = [(n,t) for n,t in BASE if n not in REMOVED]
MEANINGS = {
 'hzpb':'同じ発信者・受け手・内容・自己離脱の前後について、最初の伝達、中継の有限列、取得過程と前後点が存在し、指定期間内で将来の取得と持続hzoeを満たす。中継列は全ての有限長を量化し、長さ上限や候補一覧を意味に加えない。',
 'hzpc':'同じ発信者を中心にした非空の人の範囲について、hzpbの存在条件を満たす人の正確な範囲を内部で作り、指定する広がりの基準へ渡す。自己離脱とその前後は全受け手で共用し、経路と取得過程だけは受け手ごとに異なってよい。',
 'hzpd':'一つの自己離脱過程とその前後点が存在し、その同じ組を全受け手に共用してhzpcを満たす。受け手ごとに異なる離脱を継ぎ合わせない。発信者、内容、期間枠、基準点は量化の外で保持する。',
 'hzpe':'同じ本人・同じ初期機会に独立判断hzhhとhzpdを要求する。独立して考えた人と伝播した人を別々の存在として足し合わせない。',
 'hzpf':'基準点より後の全機会で、母集団に複数のhzpe該当者がおり、その中に指定部分集団の人がいる内容。各人の離脱と受け手ごとの経路を存在で記述し、外部の経路供給関数を必要としない。',
}
LIMITS = [
 '任意長の有限経路を表現する文法と、それを全探索できる計算手続は別である。既存有限評価器は列の無制限量化を拒否する。列の長さに上限を加えたり、候補が見つからないことを不存在としたりしない。',
 '新しい証人検証は先頭の存在量化だけを具体的な閉じたNoema項で実例化する。成功は指定解釈内の存在を示す。失敗はその証人の不成立であり、存在命題の否定ではない。未知入力と資源上限はエラーとして保持する。',
 '経路ごとの証人の成功だけでは、存在を満たす受け手の正確な範囲や、任意の広がり関数を含む集団命題全体を証明できない。特に非単調な広がり基準へ、見つかった受け手だけを渡して同値としない。',
 '内容・伝達行為の対応関数・評価場面・社会的範囲・広がり・期間は依然として解釈引数である。語彙を追加しただけで原文に適した値が決まるとはしない。発話内容と期間まで全て存在閉包した全文ではない。',
 '既存33文と七単位の確認を保存する。自由の条件や比較背景へ渡せる内容を作るが、未確定の解釈値を決めた本文主張は追加しない。新たな原文範囲・意味確認済み単位は加算しない。',
]


def exists(fields, body):
    for name, sort in reversed(fields):
        body = 'g '+name+' '+sort+'['+body+']'
    return body


def definitions():
    route = k('hzoe', *('v '+n for n in ('first','rest','origin','target','subject','message','state',
        'process','start','end','anchor','sender','recipient','activity','point','departure','prior','attained')))
    checks = [k('h7q','v frame','v anchor',x) for x in ('c[v point][v first]','v start','v end')]
    checks += [k('ic','v initial','v end','v anchor'), route]
    text = declaration('hzpb', ROUTE, 'c', exists(WITNESSES, both(*checks)))
    relative = 'i[center a person a context d]['+k('rqth','v center','v person','v context','v scope')+']'
    population = 'i[target a]['+k('rqth','v origin','v target','v reference','v scope')+']'
    changed = 'i[target a]['+k('hzpb', *('v '+n for n,t in ROUTE))+']'
    text += declaration('hzpc', SHARED, 'c', both(k('hzne','v frame','v initial','v anchor'),
        k('h7q','v frame','v anchor','v prior'), k('h7q','v frame','v anchor','v attained'),
        k('rqsz','v origin','v reference',relative,'p aa'), k('rqsw',population,changed,'v extent')))
    text += declaration('hzpd', EXISTENTIAL, 'c', exists(DEPARTURE,k('hzpc',*('v '+n for n,t in SHARED))))
    text += declaration('hzpe', EXISTENTIAL+THINKING, 'c', both(
        k('hzhh','v origin','v initial',*('v '+n for n,t in THINKING)),
        k('hzpd',*('v '+n for n,t in EXISTENTIAL))))
    args = []
    for name, sort in EXISTENTIAL+THINKING:
        args.append('v person' if name=='origin' else 'v opportunity' if name=='initial' else
                    'c[v '+name+'][v person v opportunity]' if name in PER_PERSON else 'v '+name)
    qualified = 'i[person a opportunity d]['+k('hzpe',*args)+']'
    human = 'f person a[y[c[v members][v person v opportunity]][k aa[v person]]]'
    atpoint = both(human,k('rqti','v opportunity','v members','v subgroup',qualified))
    text += declaration('hzpf', FUTURE+[('subgroup','h[a d] c')], 'e',
        'b base['+k('rqtj','v history','v before','v base','i[opportunity d]['+atpoint+']')+']')
    return text


def build():
    old = load_catalog(ROOT,PARENT_BASIS)
    doc = deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements = doc['statements']; doc['statements'] = []; size = len(doc['declarations'])
    doc = parse(format_graph(doc,'compact')+definitions()); doc['statements'] = statements
    core = deepcopy(doc); core['statements'] = []
    core['declarations'] = closure(doc,['hzpf','hzny','rqsx','hzpa','hzon','hzp5','hzp3','wa','hzhb'])
    basis = dict(status='unbounded_finite_route_existence_with_shared_origin_departure',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
            BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists(): assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
    print('Route and departure existence composed without sequence length bounds',flush=True)


if __name__=='__main__': main()
