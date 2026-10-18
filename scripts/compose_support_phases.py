"""Compose contact and load transfer over an explicitly covered episode."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from scripts.compose_bodily_acquisition import ROOT
from noema.meaning_catalog import load_catalog
from scripts.compose_falling_depiction import closure
from scripts.compose_limits import v,app,call,op,both,quant,definition

LIBRARY='examples/v016/support-phases.noema'
EXAMPLE='examples/v016/support-phases-example.noema'
BASIS='data/support-phases-basis-v1.json'
EXAMPLE_BASIS='data/support-phases-example-basis-v1.json'
FIELDS='person a act a first a second a context d history h[d] c scope h[d] c before h[d d] c start d end d foot h[a a d] c complete h[a a h[d] c d] c known h[a a a d] c contact h[a a a d] c load h[a a a d] c'
ARGS=' '.join('v '+n for n in ('person','act','first','second','context','history','scope','before','start','end','foot','complete','known','contact','load'))
MEANINGS={
 'rqvx':'同じ履歴の非空で連続した範囲に異なる開始と終了があり、全点が両端の間にある。履歴内の区間性を検査するが、有限の観測が現実の時間を尽くすことは証明しない。',
 'rqvy':'同じ本人・活動の全範囲について完全性が明示され、区別できる二つの足の接地と荷重支持が全点で評価済みであり、荷重支持には接地を要する。活動全体の分類ではなく、足の状態の記述を利用できる条件。',
 'rqvz':'rqvyが整った同じ活動範囲の全点で、少なくとも一方の足が接地している。両足接地だけ、荷重支持、歩行という分類、外部補助の不在とは同一視しない。',
 'rqwa':'rqvzの同じ全範囲に、第一の足だけの荷重支持、両足の荷重支持、第二の足だけの荷重支持がこの順である。三点だけの測定から中間の接地を補わず、同じ本人・活動・二足の役割を保持する。',
 'rqwb':'rqvyが整った同じ活動範囲に、両足とも接地しない点がある。手や装置による支持の不在、全身の空中状態、走行という分類を含意しない。',
}
LIMITS=[
 '歩行と走行の語義全体を接地の有無だけで定義しない。荷重の移行と接地を別に記述するための部品であり、接地を保った走行や発達中の混合的な運動もこの記述を共有しうる。',
 'completeは同じ本人・活動・範囲・文脈に結ぶ明示的な完全性の入力。有限モデルで検査した点の集合が現実の連続時間を尽くすことは、テストから証明できない。未知なら拒否し、測定点だけを全範囲だと補わない。',
 'footは同じ身体の足という部分関係、contactは支持面との接触、loadはその接触を通じた荷重支持、knownは両事実の評価済み状態を表す。各入力を歩行・走行という判定済みの語で置換しない。',
 '速度、前進方向、周期数、左右の対称性、エネルギー交換、技能、身体制御、外部補助の不在はこの一般形から導かない。これらは別々に記述する内容である。',
 'カントのgehen lernenに採る歩行の語義はまだ確定しない。現行本文・能力取得・九単位の意味判断を変えず、原文範囲や確認済み587文字も増やさない。',
]


@lru_cache(None)
def source():return load_catalog(ROOT,'data/bodily-acquisition-basis-v1.json')


def definitions():
    inside=lambda s:app(v('scope'),v(s))
    before=lambda a,b:app(v('before'),v(a),v(b))
    state=lambda fn,part,s:app(v(fn),v('person'),v('act'),v(part),v(s))
    interval=both(call('tb',v('history'),v('scope'),v('before')),inside('start'),inside('end'),before('start','end'),
        quant('f','point','d',op('y',inside('point'),both(op('x',op('e',v('point'),v('start')),before('start','point')),
            op('x',op('e',v('point'),v('end')),before('point','end'))))))
    text=definition('rqvx','history h[d] c scope h[d] c before h[d d] c start d end d',interval)
    assessed=both(call('rqvx',*[v(n) for n in ('history','scope','before','start','end')]),
        op('u',op('e',v('first'),v('second'))),*[app(v('foot'),v('person'),v(n),v('context')) for n in ('first','second')],
        app(v('complete'),v('person'),v('act'),v('scope'),v('context')),
        quant('f','point','d',op('y',inside('point'),both(*[state('known',n,'point') for n in ('first','second')],
            *[op('y',state('load',n,'point'),state('contact',n,'point')) for n in ('first','second')]))))
    text+=definition('rqvy',FIELDS,assessed)
    base='k rqvy['+ARGS+']'
    text+=definition('rqvz',FIELDS,both(base,quant('f','point','d',op('y',inside('point'),
        op('x',state('contact','first','point'),state('contact','second','point'))))))
    transfer=both(*[inside(n) for n in ('earlier','middle','later')],before('earlier','middle'),before('middle','later'),
        state('load','first','earlier'),op('u',state('load','second','earlier')),
        state('load','first','middle'),state('load','second','middle'),
        op('u',state('load','first','later')),state('load','second','later'))
    text+=definition('rqwa',FIELDS,both('k rqvz['+ARGS+']',quant('g','earlier','d',quant('g','middle','d',quant('g','later','d',transfer)))))
    text+=definition('rqwb',FIELDS,both(base,quant('g','point','d',both(inside('point'),
        op('u',state('contact','first','point')),op('u',state('contact','second','point'))))))
    return text


EXAMPLE_PRIMITIVES={
 'za':([], '記述する身体主体。'), 'zb':([], '同じ主体の移動の活動。'),
 'zc':([], '第一の足。'), 'zd':([], '第二の足。'), 'ze':([], '記述の文脈。'),
 'zf':([], '選んだ範囲の開始。'), 'zg':([], '選んだ範囲の終了。'),
 'zh':(['point'],'記述対象の時間履歴に含む点。'), 'zi':(['point'],'同じ活動の全過程として記述する範囲。'),
 'zj':(['earlier','later'],'同じ履歴の厳密な時間順序。'),
 'zk':(['person','part','context'],'同じ本人の身体の足である。'),
 'zl':(['person','act','scope','context'],'同じ本人の同じ活動の全過程について、この範囲が接地・荷重の変化を欠落なく含むと確認されている。観測点が非空なだけでは成立しない。'),
 'zm':(['person','act','part','point'],'この本人・活動・足・時点の接地と荷重支持の事実がともに評価済みである。'),
 'zn':(['person','act','part','point'],'この本人のこの活動で、この足が地面等の支持面へ接触している。荷重支持とは区別する。'),
 'zo':(['person','act','part','point'],'この本人のこの活動で、この足が接触した支持面へ身体の荷重を伝えている。触れているだけとは区別する。'),
}


def build():
    cat=source();d=deepcopy(cat.document);d['declarations']=closure(d,['tb']);d['statements']=[]
    assert not set(MEANINGS)&set(cat.entries)
    generic=parse(format_graph(d,'compact')+definitions())
    basis=dict(document=LIBRARY,primitives={},definitions={**{x['name']:cat.entries[x['name']]['meaning_ja'] for x in d['declarations']},**MEANINGS},limitations=LIMITS)
    extra='r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.r zf[] d.r zg[] d.r zh[d] c.r zi[d] c.r zj[d d] c.r zk[a a d] c.r zl[a a h[d] c d] c.r zm[a a a d] c.r zn[a a a d] c.r zo[a a a d] c.'
    args='k za[] k zb[] k zc[] k zd[] k ze[] p zh p zi p zj k zf[] k zg[] p zk p zl p zm p zn p zo'
    example=parse(format_graph(generic,'compact')+extra+''.join('q[k '+n+'['+args+']].' for n in ('rqvy','rqvz','rqwa','rqwb')))
    added=example['declarations'][len(generic['declarations']):];by_name={x['name']:x for x in added}
    eb=dict(document=EXAMPLE,parent=LIBRARY,inherited_meaning_basis=BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=a,meaning_ja=m) for n,(a,m) in EXAMPLE_PRIMITIVES.items()},
        definitions={},new_signatures={x['name']:{k:x[k] for k in ('parameters','result')} for x in added},limitations=LIMITS)
    enc=lambda obj:json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    return {LIBRARY:format_graph(generic,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n',BASIS:enc(basis),EXAMPLE_BASIS:enc(eb)}


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print('Contact, load and covered support transitions composed',flush=True)


if __name__=='__main__':main()
