"""Describe influence and unilateral binary decision control compositionally."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure
from scripts.compose_relational_departure import SETTINGS

PARENT='examples/v016/kant-relational-departure.noema'
PARENT_BASIS='data/relational-departure-basis-v1.json'
FULL='examples/v016/kant-unilateral-decision.noema'
LIBRARY='examples/v016/unilateral-decision.noema'
BASIS='data/unilateral-decision-basis-v1.json'
PROFILE='h[a] c'
RULE='h[j[c]] c'
CONTROL=[('participants','h[a d] j[a]'),('rules','h[a d] '+RULE),('contributors','h[a a d] c')]
FIELDS=[(n,t) for n,t in SETTINGS if n!='relation']+CONTROL
CODES=[(n,'i['+t+']') for n,t in FIELDS]
OUTER=[('target','i b[a]'),('kind','i b[h[a] c]'),('second','i b[i[h[a] e]]'),
    ('anchor','i b[d]'),('prospects','i b[h[a d d] c]')]+CODES
TRUE='e[n p a b][n p a b]'
FALSE='u['+TRUE+']'


def av(fields):return [v(n) for n,t in fields]


def definitions():
    project='q[v people][l[c][]][i[values j[c] person a][m[v values][l[c]['+app(v('profile'),v('person'))+']]]]'
    text=definition('rqt','people j[a] profile '+PROFILE,project,'j[c]')
    text+=definition('rqu','voter a value c','i[person a]['+both(op('e',v('person'),v('voter')),v('value'))+']',PROFILE)
    flip='i[person a]['+op('x',both(op('e',v('person'),v('voter')),op('u',app(v('profile'),v('person')))),
        both(op('u',op('e',v('person'),v('voter'))),app(v('profile'),v('person'))))+']'
    output=lambda profile:app(v('rule'),k('rqt',v('people'),profile))
    effect=op('u',op('e',output(v('profile')),output(flip)))
    search='q[k rs[v people]]['+FALSE+'][i[found c profile '+PROFILE+']['+op('x',v('found'),effect)+']]'
    valid=both(k('rt',v('people')),k('rz',v('people'),v('voter')))
    args='voter a people j[a] rule '+RULE
    text+=definition('rqv',args,both(valid,search))
    fixed=k('rqu',v('voter'),app(v('profile'),v('voter')))
    independent='q[k rs[v people]]['+TRUE+'][i[valid c profile '+PROFILE+']['+both(v('valid'),op('e',output(v('profile')),output(fixed)))+']]'
    responsive=op('u',op('e',output(k('rqu',v('voter'),FALSE)),output(k('rqu',v('voter'),TRUE))))
    text+=definition('rqw',args,both(valid,responsive,independent))
    people=app(v('participants'),v('target'),v('point'))
    rule=app(v('rules'),v('target'),v('point'))
    scope='i[person a]['+app(v('contributors'),v('person'),v('target'),v('point'))+']'
    text+=definition('rqy',params([('target','a'),('point','d')]+CONTROL),both(k('rcm',people,scope),k('rz',people,v('target'))))
    configuration=k('rqy',v('target'),v('point'),*av(CONTROL))
    text+=definition('rqx',params([('holder','a'),('target','a'),('point','d')]+CONTROL),both(
        op('u',op('e',v('holder'),v('target'))),configuration,k('rqw',v('holder'),people,rule)))
    relation='i[holder a target a point d]['+k('rqx',v('holder'),v('target'),v('point'),*av(CONTROL))+']'
    assessed='i[holder a target a point d]['+both(app(v('assessed'),v('holder'),v('target'),v('point')),configuration)+']'
    refs=dict(relation=relation,assessed=assessed)
    text+=definition('hzhr',params(FIELDS),k('hzhn',*[refs.get(n,v(n)) for n,t in SETTINGS]),'h[a] e')
    text+=definition('hzhs',params(CODES),'o a[r[p hzhr]]['+' '.join(av(CODES))+']','i[h[a] e]')
    args=[v('target'),v('kind'),'o r['+k('hzhs',*av(CODES))+']',v('second'),v('anchor'),v('prospects')]
    text+=definition('hzht',params(OUTER),'o a[r b[p hzhk]]['+' '.join(args)+']','i b[c]')
    return text


MEANINGS={
    'rqt':'人物列の各位置へ、その人の二値入力を対応させる。列を並べ替えるときは結果規則の位置も対応させる。',
    'rqu':'指定した本人だけが指定値を持ち、他の人物の入力は偽となる比較用の入力配置。実際の入力や他者の不参加は主張しない。',
    'rqv':'重複のない人物列に本人が含まれ、本人の入力だけを反転すると結果が変わる配置が少なくとも一つある。',
    'rqw':'重複のない人物列に本人が含まれ、全二値入力配置で、結果が本人の入力だけから決まる。本人の二つの入力は異なる結果を生む。結果が本人の入力の反転である規則も含み、定数規則は含めない。',
    'rqy':'同じ対象・状況に結び付いた入力者列が指定範囲の重複のない完全な列であり、対象自身を含む。離脱判定では前後両方に要求し、不完全な終了点を関係不成立の根拠としない。',
    'rqx':'同じ対象・状況に結び付いた完全な入力者列と結果規則について、対象自身が入力者であり、別の相手がrqwの決定力を持つ。対象の入力も他の入力もその相手の決定結果を変えない。',
    'hzhr':'既存hzhnの関係をrqxに具体化する。同じ相手・対象への一方的な二値決定関係が、評価済みかつrqyの設定が有効な前では成立し、同様に有効な後では成立しない変化の内容。',
    'hzhs':'閉じた設定記述からhzhrへの適用記述を構成する。決定規則、関係、変化過程を実行しない。',
    'hzht':'因果対比hzhkの第一の結果をhzhsの内容記述に固定する。因果記録と内容評価に同じ記述を渡す。',
}
LIMITS=[
    '二値の全入力配置に関する純粋な結果規則の定義。実行可能な介入、身体的強制、意思形成の独立性、実際の服従や規範上の権限を、この関数の性質だけから導かない。',
    'participantsとcontributorsは同じ対象・状況で完全性を照合するが、その範囲が現実の全要因を網羅するという外部の主張までは証明しない。未評価の入力を偽に置換しない。',
    '対象も入力者である場合に限定する。対象にそもそも選択肢がない支配、複数値の選択、議題設定、確率的結果、複数主体の連合支配は未記述。',
    'rqxは支配概念の一部に向けた操作的候補。個人的専制、利欲や支配欲による圧迫、政治的制度、正当性の語義全体とは同一視しない。',
    '決定規則と入力者範囲は前後で変化してよい。各点の対象と状況は揃える。離脱した相手以外への支配の交替や、その後の恒久的な自由は排除も保証もしない。',
    '全二値配置を既存rsで有限列挙するため、入力者数に対して指数的な評価費用がある。真理値表検査は有限モデルの検査であり、任意の人数の形式証明ではない。',
    '新しい原始記号、自然言語との対訳、原文の主張は追加しない。新規原文範囲や意味確認済み区間も加算しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqv','hzht'])
    basis=dict(status='partial_unilateral_binary_decision_not_complete_domination',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'] if d['name'] in MEANINGS},
        limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Unilateral decision control composed without new primitives',flush=True)


if __name__=='__main__':main()
