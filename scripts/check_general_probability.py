"""Saved native probability contrasts under two explicitly finite readings."""
import json
from fractions import Fraction as F
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.general_probability import composed, I, N, T, call, app, op, v, lam
from scripts.general_language_release import save_text
from scripts.two_work_inventory import sha

LIBRARY='examples/v016/general-probability-contrasts-v1.noema'
BASIS='data/general-probability-contrasts-v1.json'


def number(n):
    n=F(n);return dict(kind='number',numerator=n.numerator,denominator=n.denominator)


def document():
    d=composed()
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in ('first','second')]
    cases=dict(kind='sequence',element=I,items=[call('first'),call('second')])
    first=lam([('x',I)],op('equal',v('x'),call('first')))
    yes=lam([('x',I)],op('equal',v('x'),v('x')))
    no=lam([('x',I)],op('not',op('equal',v('x'),v('x'))))
    second=call('truthindicator',op('equal',v('x'),call('second')))
    weight=lam([('x',I)],call('rationaladd',number(F(1,4)),call('rationalmultiply',number(F(1,2)),second)))
    likelihood=lam([('x',I)],call('rationaladd',number(1),call('rationalmultiply',number(F(-2,3)),second)))
    posterior=lam([('x',I)],number(F(1,2)))
    bodies=[call('probabilityspace',cases,weight),call('probabilityvalue',cases,weight,first,number(F(1,4))),
        call('probabilityvalue',cases,weight,first,number(F(1,2))),
        call('conditionalprobability',cases,weight,yes,first,number(F(1,4))),
        call('conditionalprobability',cases,weight,first,yes,number(1)),
        call('conditionaldefined',cases,weight,no),call('conditionalprobability',cases,weight,no,first,number(0)),
        call('probabilityindependent',cases,weight,first,first),
        call('probabilityinterval',cases,weight,first,number(F(1,5)),number(F(1,3))),
        call('probabilityupdated',cases,weight,likelihood,posterior),call('probabilityupdated',cases,weight,likelihood,weight)]
    d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)


EXPECTED=[True,True,False,True,True,False,False,False,True,True,False]
MEANING=['確率空間が有効','第一事例の確率は1/4','事例を等分した1/2ではない','全範囲を条件とする第一事例の確率は1/4',
         '第一事例を条件とする全範囲の確率は1','空事象による条件付けは未定義','未定義を0という値で埋めない',
         '第一事例は自分自身と独立ではない','確率は1/5以上1/3以下','尤度による更新は両方1/2','元の分布のままでは更新結果と異なる']


def prepare():
    save_text(LIBRARY,format_graph(document(),'compact')+'\n')
    save_text(BASIS,json.dumps(dict(expected=EXPECTED,statement_meanings=MEANING,
        cases=['first','second'],weights=['1/4','3/4'],likelihood=['1','1/3'],posterior=['1/2','1/2'],
        readings=['重みの異なる二種類の抽選結果と、その結果に依存して得られる印の観測',
                  '二つの排他的な仮説に対する事前確率と、それぞれの仮説の下で同じ観測が得られる尤度'],
        boundaries=['同じ事例範囲と同じ観測に関するモデルを固定する。実測データや尤度の適切さをこの例で認定しない。',
                    '未知・負の重み・重複・総和不正の拒否はtests/test_general_probability.pyで別に検査する。']),ensure_ascii=False,indent=2)+'\n')


def build_report():
    model=dict(first=lambda:'a',second=lambda:'b',rationaladd=lambda a,b:a+b,rationalmultiply=lambda a,b:a*b,
               rationalbelow=lambda a,b:a<b,truthindicator=lambda x:F(int(x)))
    result=[r['value'] for r in evaluate_document(document(),individuals=('a','b'),situations=('now','later'),primitives=model)]
    assert result==EXPECTED
    paths=[LIBRARY,BASIS,'scripts/check_general_probability.py','scripts/general_probability.py','scripts/general_language.py',
           'data/general-language-catalog-v1.json','noema/constructed_discourse.py','noema/constructed_semantics.py']
    return dict(schema='noema-general-probability-1',models=[dict(reading=r,values=result) for r in ('weighted-draw','hypothesis-update')],
                exact_rational=True,new_primitives=0,source_sha256={p:sha(p) for p in paths},
                boundary='同じ有限分布の二つの明示解釈。現実の確率・尤度の認定ではない。')
