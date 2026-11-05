"""Finite exact probability from existing arithmetic, membership and folds."""
from functools import lru_cache
from noema.constructed_discourse import function_sort,sequence_sort
from scripts.shared_modality import v,app,call,op
from scripts.shared_reference import definition,lam,truth
from scripts.shared_time import allof
from scripts.general_language import document

I='individual';N='number';T='truth';MEMBERS=sequence_sort(I)
WEIGHT=function_sort([I],N);EVENT=function_sort([I],T)
BASE=[('cases',MEMBERS),('weight',WEIGHT)]


def num(n):return dict(kind='number',numerator=n,denominator=1)
def eq(a,b):return op('equal',a,b)
def less(a,b):return call('rationalbelow',a,b)
def leq(a,b):return op('not',less(b,a))
def fold(xs,initial,name,sort,body):
    return dict(kind='fold',sequence=xs,initial=initial,step=lam([('acc',sort),(name,I)],body))
def every(body):return fold(v('cases'),truth(True),'case',T,op('and',v('acc'),body))
def args(ps):return [v(n) for n,t in ps]


@lru_cache(maxsize=1)
def raw():
    ds=[]
    def add(n,ps,result,body):ds.append(definition(n,ps,result,body))
    add('weightsum',BASE,N,fold(v('cases'),num(0),'case',N,call('rationaladd',v('acc'),app('weight',v('case')))))
    add('eventweight',BASE+[('event',EVENT)],N,fold(v('cases'),num(0),'case',N,
        call('rationaladd',v('acc'),call('rationalmultiply',app('weight',v('case')),call('truthindicator',app('event',v('case')))))))
    valid=allof(call('distinctmembers',v('cases')),every(leq(num(0),app('weight',v('case')))),eq(call('weightsum',*args(BASE)),num(1)))
    add('probabilityspace',BASE,T,valid)
    add('probabilityvalue',BASE+[('event',EVENT),('value',N)],T,allof(call('probabilityspace',*args(BASE)),call('indicatorvalid'),
        eq(call('eventweight',*args(BASE),v('event')),v('value'))))
    condition=BASE+[('condition',EVENT)]
    add('conditionaldefined',condition,T,allof(call('probabilityspace',*args(BASE)),call('indicatorvalid'),
        less(num(0),call('eventweight',*args(BASE),v('condition')))))
    intersection=lam([('item',I)],op('and',app('event',v('item')),app('condition',v('item'))))
    add('conditionalprobability',condition+[('event',EVENT),('value',N)],T,allof(call('conditionaldefined',*args(condition)),
        eq(call('eventweight',*args(BASE),intersection),call('rationalmultiply',v('value'),call('eventweight',*args(BASE),v('condition'))))))
    add('probabilityinterval',BASE+[('event',EVENT),('lower',N),('upper',N)],T,
        allof(call('probabilityspace',*args(BASE)),call('indicatorvalid'),leq(num(0),v('lower')),leq(v('lower'),v('upper')),leq(v('upper'),num(1)),
              leq(v('lower'),call('eventweight',*args(BASE),v('event'))),leq(call('eventweight',*args(BASE),v('event')),v('upper'))))
    pair=lam([('item',I)],op('and',app('left',v('item')),app('right',v('item'))))
    add('probabilityindependent',BASE+[('left',EVENT),('right',EVENT)],T,allof(call('probabilityspace',*args(BASE)),call('indicatorvalid'),
        eq(call('eventweight',*args(BASE),pair),call('rationalmultiply',call('eventweight',*args(BASE),v('left')),call('eventweight',*args(BASE),v('right'))))))
    likelihoodweight=lam([('item',I)],call('rationalmultiply',app('weight',v('item')),app('likelihood',v('item'))))
    total=call('weightsum',v('cases'),likelihoodweight)
    add('probabilityupdated',BASE+[('likelihood',WEIGHT),('posterior',WEIGHT)],T,
        allof(call('probabilityspace',*args(BASE)),call('probabilityspace',v('cases'),v('posterior')),
              every(op('and',leq(num(0),app('likelihood',v('case'))),leq(app('likelihood',v('case')),num(1)))),less(num(0),total),
              every(eq(call('rationalmultiply',app('posterior',v('case')),total),call('rationalmultiply',app('weight',v('case')),app('likelihood',v('case')))))))
    return ds


MEANINGS={
 'weightsum':'有限の事例列に割り当てた有理数の重みを加算する。事例の完全性・重複・非負性はこの関数だけでは要求しない。',
 'eventweight':'有限列のうち条件が真である事例の重みを加算する。条件は既知の真理値を返す。未確認の事例を偽や重み0へ補わない。',
 'probabilityspace':'事例に重複がなく、各重みが非負で、総和が厳密に1である有限確率モデル。何を一つの事例とし、その全範囲と重みをどう定めたかは明示する。',
 'probabilityvalue':'同じ有限確率モデルで、条件を満たす事例の重みの合計が指定値に等しい。実際にその条件が成立したこと、信念として採用したこと、単なる事例数の割合とは区別する。',
 'conditionaldefined':'同じ有効な有限確率モデルで、条件事象の重みが正である。重み0の条件に対する値は定めない。',
 'conditionalprobability':'正の重みを持つ条件事象について、同時事象の重みが指定値と条件事象の重みの積に等しい。条件の向きと同じ事例範囲を保持する。',
 'probabilityinterval':'同じモデルで事象の確率が指定された閉区間に属する。区間は0以上1以下で下限が上限以下。区間内の唯一の値や、範囲外のモデルについての保証は加えない。',
 'probabilityindependent':'同じモデルで二事象の同時確率がそれぞれの確率の積に等しい。情報の出所が異なることや、二事象が同時に起きなかったことから独立性を補わない。',
 'probabilityupdated':'同じ事例列について、事前確率と0以上1以下の尤度の積を、正の総和で正規化した事後分布が指定分布に一致する。尤度や事例範囲の適切さ、情報源の信頼性は別の判断として保持する。'}


def composed():return document(raw())


def basis():
    return dict(status='general_finite_probability',document='examples/v016/general-probability-v1.noema',primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort']) for p in d['parameters']],result=d['result']) for d in raw()},
        new_primitives=0,interpretation=['有限の相互排他的な事例とその完全な範囲、重みの出所を明示する。モデルの入力を結論から逆算しない。',
            '有理数の標準演算と指示関数は既存の意味規約を使う。無限分布・任意実数の確率を有限有理分布に置き換えたものではない。',
            '無限の事例域や実数値の測度を表す場合は既存の高階関数・実数切断と測度の条件を別に定義する。有限の計算結果をその証明には使わない。'])
