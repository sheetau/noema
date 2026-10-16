"""Compose departure from one relation without silently abolishing the whole kind."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure

PARENT='examples/v016/kant-quoted-outcomes.noema'
PARENT_BASIS='data/quoted-outcomes-basis-v1.json'
FULL='examples/v016/kant-relational-departure.noema'
LIBRARY='examples/v016/relational-departure.noema'
BASIS='data/relational-departure-basis-v1.json'
SETTINGS=[('holders','h[a] c'),('history','h[d] c'),('before','h[d d] c'),('assessed','h[a a d] c'),
    ('relation','h[a a d] c'),('transitions','h[a d d] c'),('affected','h[a a d d] c')]
EVENT=[('target','a'),('holder','a'),('process','a'),('start','d'),('end','d')]+SETTINGS
CODES=[(n,'i['+t+']') for n,t in SETTINGS]
OUTER=[('target','i b[a]'),('kind','i b[h[a] c]'),('second','i b[i[h[a] e]]'),
    ('anchor','i b[d]'),('prospects','i b[h[a d d] c]')]+CODES


def av(fields):return [v(n) for n,t in fields]


def definitions():
    rel=lambda name,point:app(v(name),v('holder'),v('target'),v(point))
    text=definition('rqr',params(EVENT),both(app(v('holders'),v('holder')),
        k('tg',v('history'),v('before'),v('process'),v('start'),v('end'),v('transitions')),
        rel('assessed','start'),rel('assessed','end'),rel('relation','start'),op('u',rel('relation','end')),
        app(v('affected'),v('target'),v('process'),v('start'),v('end'))))
    absent=q('f','other','a',op('y',app(v('holders'),v('other')),both(
        app(v('assessed'),v('other'),v('target'),v('end')),op('u',app(v('relation'),v('other'),v('target'),v('end'))))))
    text+=definition('rqs',params(EVENT),both(k('rqr',*av(EVENT)),absent))
    body=q('g','holder','a',q('g','process','a',q('g','start','d',k('rqr',*av(EVENT)))))
    text+=definition('hzhn',params(SETTINGS),'i[target a][b end['+body+']]','h[a] e')
    text+=definition('hzho',params(CODES),'o a[r[p hzhn]]['+' '.join(av(CODES))+']','i[h[a] e]')
    departure='o r['+k('hzho',*av(CODES))+']'
    args=[v('target'),v('kind'),departure,v('second'),v('anchor'),v('prospects')]
    text+=definition('hzhp',params(OUTER),'o a[r b[p hzhk]]['+' '.join(args)+']','i b[c]')
    return text


MEANINGS={
    'rqr':'指定した同じ相手・対象の関係が、評価済みの開始点では成立し終了点では成立しない。同じ順序付き履歴で同じ過程がその二点を結び、同じ対象がその過程の影響対象である。相手の範囲への所属も保持する。',
    'rqs':'rqrに加え、終了点で指定範囲の全ての相手との関係が評価済みかつ不成立である。特定の相手から離れたことと、その範囲の全相手から離れたことを分ける強い診断。',
    'hzhn':'同じ関係・相手範囲・履歴・評価・過程接続について、対象がその状況を終了点とするrqrの離脱を持つ内容を作る。別の相手への交替や別種類の関係の継続は、この内容だけでは否定しない。',
    'hzho':'明示された設定の閉じた層0の記述から、同じhzhnへの適用を記述として構成する。関係や過程を実行せず、結果は因果生成の対象として渡せる同じ離脱内容の記述になる。',
    'hzhp':'既存hzhkの第一の結果をhzhoの離脱記述に固定して対比全体の引用を作る。因果関係が受け取る記述と、明示的に評価する離脱内容を同じ構文へ結ぶ。第二の結果、活動種類、対象、候補関係は明示した記述で保持する。',
}
LIMITS=[
    'Abfallからの部分読解に向けて、指定された相手との関係の終了を構成する。専制や圧迫の全廃、後継者の不在、判断の自立、離脱の正当性や恒久性は補わない。語の唯一の読みを確定したものではない。',
    'relationは、同じ相手・対象・状況に成立する依存や従属などの関係を渡す。holdersはその比較で関連する相手の範囲。専制・利欲や支配欲による圧迫の概念説明と、その範囲の完全性は未完である。',
    '単に関係が不成立な状態、前後で別人の関係を調べた場合、無関係な過程の生起、未評価の終了点は離脱の証拠にしない。前後二点の構成であり、途中全体の経過や唯一の終了時点は要求しない。',
    'rqsは比較用の強い条件で、原文の離脱へ自動的に付け加えない。相手の集合を結果を見て狭めることも、無条件に世界全体の集合と見なすこともしない。',
    '変化過程と、その離脱を生じさせた活動は別の役割でよい。前者の当事者・前後はrqrで、後者と同じ候補での結果生成は既存hzhkとg3で結ぶ。両者を同一の出来事と勝手に決めない。',
    '第一の結果の構造を充足した候補だが、革命の種類と支配関係、複合した圧迫条件、第二の真の改革、認識的な留保、具体的な著者帰属と全文の意味一致は未完。新しい原文範囲や主張は加算しない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqs','hzho','hzhp'])
    basis=dict(status='partial_relational_departure_result_not_complete_source_concept',document=FULL,library=LIBRARY,
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
    print('A same-relation departure is bound into the first causal outcome',flush=True)


if __name__=='__main__':main()
