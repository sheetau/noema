"""Compose outcome control with finite alternatives and nondeterministic results."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure
from scripts.compose_relational_departure import SETTINGS

PARENT='examples/v016/kant-unilateral-decision.noema'
PARENT_BASIS='data/unilateral-decision-basis-v1.json'
FULL='examples/v016/kant-outcome-choice.noema'
LIBRARY='examples/v016/outcome-choice.noema'
BASIS='data/outcome-choice-basis-v1.json'
MODEL=[('methods','j[a]'),('responses','j[a]'),('outcomes','j[a]'),
    ('methodscope','h[a] c'),('responsescope','h[a] c'),('outcomescope','h[a] c'),
    ('possible','h[a a a] c'),('checked','h[a a] c')]
PROVIDERS=[(n,'h[a a d] '+t) for n,t in MODEL]
FIELDS=[(n,t) for n,t in SETTINGS if n!='relation']+[('reference','d')]+PROVIDERS
CODES=[(n,'i['+t+']') for n,t in FIELDS]
OUTER=[('target','i b[a]'),('kind','i b[h[a] c]'),('second','i b[i[h[a] e]]'),
    ('anchor','i b[d]'),('prospects','i b[h[a d d] c]')]+CODES
TRUE='e[n p a b][n p a b]'
FALSE='u['+TRUE+']'


def av(fields):return [v(n) for n,t in fields]


def fold(sequence,item,body,all=True):
    return 'q['+sequence+']['+(TRUE if all else FALSE)+'][i[acc c '+item+' a]['+op('w' if all else 'x',v('acc'),body)+']]'


def definitions():
    edge=lambda outcome:app(v('possible'),v('method'),v('response'),outcome)
    inhabited=fold(v('outcomes'),'outcome',edge(v('outcome')),False)
    closed=quant('f','outcome','a',op('y',edge(v('outcome')),k('rz',v('outcomes'),v('outcome'))))
    pair=both(app(v('checked'),v('method'),v('response')),inhabited,closed)
    lists=[k('rcm',v(n),v(scope)) for n,scope in (('methods','methodscope'),('responses','responsescope'),('outcomes','outcomescope'))]
    text=definition('rqqa',params(MODEL),both(*lists,fold(v('methods'),'method',fold(v('responses'),'response',pair))))
    sure=fold(v('outcomes'),'outcome',op('y',edge(v('outcome')),op('e',v('outcome'),v('wanted'))))
    text+=definition('rqqb',params([('method','a'),('wanted','a')]+MODEL),both(k('rqqa',*av(MODEL)),
        k('rz',v('methods'),v('method')),k('rz',v('outcomes'),v('wanted')),fold(v('responses'),'response',sure)))
    text+=definition('rqqc',params([('wanted','a')]+MODEL),fold(v('methods'),'method',k('rqqb',v('method'),v('wanted'),*av(MODEL)),False))
    plural=k('hc','n p b b','d[v outcomes]')
    text+=definition('rqqd',params(MODEL),both(k('rqqa',*av(MODEL)),plural,
        fold(v('outcomes'),'wanted',k('rqqc',v('wanted'),*av(MODEL)))))
    hindsight=fold(v('outcomes'),'wanted',fold(v('responses'),'response',fold(v('methods'),'method',sure,False)))
    text+=definition('rqqe',params(MODEL),both(k('rqqa',*av(MODEL)),plural,hindsight))
    references=[app(v(n),v('holder'),v('target'),v('reference' if n in ('outcomes','outcomescope') else 'point')) for n,t in MODEL]
    context=[('holder','a'),('target','a'),('point','d'),('reference','d')]+PROVIDERS
    text+=definition('rqqg',params(context),both(k('rqqa',*references),k('hc','n p b b','d['+references[2]+']')))
    text+=definition('rqqf',params(context),both(op('u',op('e',v('holder'),v('target'))),k('rqqd',*references)))
    relation='i[holder a target a point d]['+k('rqqf',v('holder'),v('target'),v('point'),v('reference'),*av(PROVIDERS))+']'
    checked='i[holder a target a point d]['+both(app(v('assessed'),v('holder'),v('target'),v('point')),
        k('rqqg',v('holder'),v('target'),v('point'),v('reference'),*av(PROVIDERS)))+']'
    replacements=dict(relation=relation,assessed=checked)
    text+=definition('hzhu',params(FIELDS),k('hzhn',*[replacements.get(n,v(n)) for n,t in SETTINGS]),'h[a] e')
    text+=definition('hzhv',params(CODES),'o a[r[p hzhu]]['+' '.join(av(CODES))+']','i[h[a] e]')
    args=[v('target'),v('kind'),'o r['+k('hzhv',*av(CODES))+']',v('second'),v('anchor'),v('prospects')]
    text+=definition('hzhw',params(OUTER),'o a[r b[p hzhk]]['+' '.join(args)+']','i b[c]')
    return text


MEANINGS={
    'rqqa':'方法・他者側の応答・結果の三範囲が、それぞれ非空で重複のない完全な列である。全ての方法と応答の組合せが評価済みで、少なくとも一つの可能な結果があり、列外の可能結果はない。',
    'rqqb':'有効な同じモデルで、指定した方法と目標結果がそれぞれの列に属し、全応答で可能な全結果がその目標と一致する。相手の応答を見る前に一つの方法を固定する。',
    'rqqc':'指定した目標結果についてrqqbを満たす方法がある。可能な結果が一つ存在するだけでは保証としない。',
    'rqqd':'有効なモデルの結果範囲が二つ以上の結果を含み、その全てについて本人がそれぞれ一つの方法を選んでrqqcの保証を得られる。目標ごとに方法は異なってよい。',
    'rqqe':'有効な同じモデルで二つ以上の全目標について、応答ごとに、その目標を保証する方法がある。応答を知ってからの選択であり、rqqdの先行選択と区別する診断。',
    'rqqg':'同じ相手・対象について、結果列と結果範囲を指定基準点に固定し、それ以外を評価状況から得た設定がrqqaを満たす。固定した結果は二つ以上ある。前後両側に要求し、空・未評価・範囲欠落を関係終了の根拠にしない。',
    'rqqf':'同じ相手・対象について結果範囲を指定基準点に固定し、評価状況の方法・応答・可能性・評価を使い、対象とは別の相手がrqqdの結果選択能力を持つ。',
    'hzhu':'rqqfの関係について、評価済みかつrqqgの有効な前後で、同じ対象と相手の関係から離れる変化を構成する。',
    'hzhv':'閉じた設定記述から、同じhzhuの離脱内容の記述を構成する。方法や結果を実行しない。',
    'hzhw':'既存の因果対比の第一の結果にhzhvの記述を渡す。原因側の結果記録と、結果内容の評価は同じ記述を保持する。',
}
LIMITS=[
    '方法は本人に利用可能とする手段、応答は他者側・環境側の応答配置、結果は同じ対象について区別する結果である。これらの範囲は同じ比較基準で指定し、結果に合わせて都合の悪い応答を除外しない。',
    '方法と応答の全組合せを比較する独立選択のモデルである。組合せが不可能な場合を空の結果集合で表すと全体を無効にする。順次ゲーム、観察に応じた方策、相手の応答可能性が方法で変わるモデルは別に構成する必要がある。',
    'possibleは確率を持たない可能結果関係で、複数結果を許す。少なくとも一つの失敗結果があれば保証しない。稀な失敗を無視した高確率成功とは区別する。',
    '範囲の完全性は指定したscopeと比較する。実際の全手段・全応答・全結果の網羅や利用可能性を外部観測なしに発見するものではない。未知の入力は偽として補完しない。',
    'rqqdは全ての目標結果を一つずつ実現できる能力であり、全ての方法が他者に左右されないことまでは要求しない。結果を保証しない余分な方法があっても、保証する方法が各目標にあれば成立する。',
    '現実の行為、既遂、命令、服従、権限、正当性、身体的な強制の機構はこの可能結果モデルだけでは確定しない。単独で個人的専制や圧迫の完成した意味としない。',
    '前後のモデルは各点で有効である必要がある。結果列と結果範囲を同じ相手・対象・指定基準点へ固定し、比較中の目標の増減を関係終了の根拠にしない。方法や応答の構成は変わってよい。結果識別子の指す内容そのものの同一性は共有する参照規約に依存する。',
    '新しい原始記号・著者主張・原文対応範囲・意味確認済み区間は加算しない。有限モデルでの検査は現実世界の完全な意味一致を認定しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqqe','hzhw'])
    basis=dict(status='partial_multivalued_outcome_control_not_complete_domination',document=FULL,library=LIBRARY,
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
    print('Finite multivalued outcome choice composed',flush=True)


if __name__=='__main__':main()
