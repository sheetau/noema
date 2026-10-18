"""Explain method admissibility through an assessed preparatory history."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_method_scope import EXAMPLE as PARENT,EXAMPLE_BASIS as PARENT_BASIS,SOURCE,SOURCE_BASIS
from scripts.compose_limits import v,call as k,app,op,both,quant,definition

LIBRARY='examples/v016/preparation-course.noema'
EXAMPLE='examples/v016/preparation-course-example.noema'
BASIS='data/preparation-course-basis-v1.json'
EXAMPLE_BASIS='data/preparation-course-example-basis-v1.json'
FIELDS='person a history h[d] c before h[d d] c start d end d assessed h[a d] c'
ARGS='v person v history v before v start v end v assessed'
MEANINGS={
 'rqvf':'本人について、指定履歴が厳密な全順序を持ち、両端が履歴内で開始が終了より前にあり、その閉区間の全状況で同じ基礎能力を評価できる。途中の未評価を省かない。履歴の現実的な完全性や粒度は入力の意味規約に依存する。',
 'rqvh':'rqvfを満たす区間内に、同じ本人の基礎能力がない先の状況と、能力がある後の状況が存在する。両端だけでなく途中の取得も検出する。経験への因果的帰属や、その能力の現在の保持を要求しない。',
 'rqvg':'rqvfを満たし、区間内にrqvhの不在から存在への変化がない。rqvhの単なる否定ではない。能力の低下は許し、全状態が一定であることや、学習一般の不在とは同一視しない。',
 'rqvi':'rqvfを満たす同じ本人・履歴・前後状況で、既存r5の経験による能力取得が成立し、選んだ経験時点も同じ履歴に属する。取得に寄与した経験の説明であり、r5不成立から取得がないとは推論しない。',
 'rqvj':'同じ本人・基準状況・実行状況について、利用できる全方法の分類用履歴が評価済みであることを、指定した検査関数で要求する。未評価方法の黙った除外から限定不能を確定するのを防ぐため、否定側の能力判定と結ぶ。',
 'zchecked':'診断例の同じ本人・方法・基準・実行状況から履歴と準備終了を取り出し、rqvfで全区間の評価を確認する。同じ履歴内の対象行為の時点が準備終了より後であることも要求する。',
 'zscope':'同じ準備履歴についてrqvgを評価する。基礎能力を新たに得る変化のない方法を選ぶ。この例の方法区分は外から与えた学習ラベルではなく、履歴と能力評価からNoema内で求める。',
 'zlearning':'同じ方法に対応する過程・経験列とその時点をrqviへ渡し、準備区間での経験による基礎能力取得を調べる。方法の成功から経験の寄与を補わない。',
}
LIMITS=[
 '基礎能力はこの方法評価に用いる性質として指定する。最終目標の達成可能性をそのまま自己参照させて分類する規則ではない。',
 'rqvgは指定した基礎能力の不在から存在への変化を除く。程度的改善、既存知識の活用、あらゆる学習一般を排除する定義ではない。',
 '履歴は指定方法の一つの評価コースを表す。可能な複数コース全体の選択・完全性や、現実の連続時間を自動で観測・証明するものではない。',
 '未評価や不正な履歴ではrqvgもrqvhも偽になる。その場合、方法を除いたxgだけで不能を確定せず、rqvjの全方法の分類確認も要求する。既知の適格な成功例による肯定には全方法の分類を要求しない。',
 'r5による経験・変化過程・寄与の結合は評価するが、その因果的入力の心理機構や真実性を自動推定しない。',
 'カントの採用本文と確認登録簿は変更しない。基礎能力の選定と方法の範囲の妥当性、本文への採用判断は残る。',
]


def definitions():
    interval=lambda point:app(k('rlz',v('history'),v('before'),v('start'),v('end')),v(point))
    checked=both(k('ta',v('history'),v('before')),app(v('history'),v('start')),app(v('history'),v('end')),
        app(v('before'),v('start'),v('end')),quant('f','point','d',op('y',interval('point'),app(v('assessed'),v('person'),v('point')))))
    text=definition('rqvf',FIELDS,checked)
    rise=quant('g','first','d',quant('g','last','d',both(interval('first'),interval('last'),
        app(v('before'),v('first'),v('last')),op('u',app(v('capable'),v('person'),v('first'))),app(v('capable'),v('person'),v('last')))))
    text+=definition('rqvh',FIELDS+' capable h[a d] c',both('k rqvf['+ARGS+']',rise))
    text+=definition('rqvg',FIELDS+' capable h[a d] c',both('k rqvf['+ARGS+']','u[k rqvh['+ARGS+' v capable]]'))
    extra=' process a events j[a] when h[a] d transitions h[a d d] c affected h[a a d d] c experience h[a a d] c contributes h[a a a d d] c'
    text+=definition('rqvi',FIELDS+' capable h[a d] c'+extra,both('k rqvf['+ARGS+']',
        'k r5[v person v process v events v when v before v start v end v assessed v capable v transitions v affected v experience v contributes]',
        'q[v events][e[n p a b][n p a b]][i[ok c event a][w[v ok][c[v history][c[v when][v event]]]]]'))
    text+=definition('rqvj','person a anchor d scene d available h[a a d] c checked h[a a d d] c',
        quant('f','method','a',op('y',app(v('available'),v('person'),v('method'),v('scene')),
            app(v('checked'),v('person'),v('method'),v('anchor'),v('scene')))))
    return text


EXTRAS={
 'zdirect':([], '比較する方法の局所参照。名前から方法の性質を推定しない。'),
 'ztraining':([], '比較する方法の局所参照。名前から方法の性質を推定しない。'),
 'zhistory':(['本人','方法','基準状況','実行開始','履歴の点'],'指定方法の評価コースの履歴。準備区間と対象行為の時点を含み、途中の能力変化を省かない範囲として与える。'),
 'zfinish':(['本人','方法','基準状況','実行開始'],'同じ方法の準備区間の終了。目標実行の結果とは区別する。'),
 'ztaskpoint':(['本人','方法','基準状況','実行開始'],'同じ評価コースにおける対象行為の時点。行為の成功は要求せず、準備終了より後で同じ履歴内にあることをzcheckedで確認する。'),
 'zassessed':(['本人','点'],'選んだ基礎能力について評価が整っている。未評価を不在へ補わない。'),
 'zcapable':(['本人','点'],'この方法評価で保持・取得を調べる同じ基礎能力の成立。最終的な方法の成功とは別の入力。'),
 'zprocess':(['方法'],'この評価コースで調べる変化過程。'),
 'zevents':(['方法'],'同じ準備過程への寄与を調べる経験の列。'),
 'zwhen':(['経験'],'経験の時点。'),
 'zbefore':(['先の点','後の点'],'評価履歴の時間的先行。'),
 'ztransitions':(['過程','開始','終了'],'同じ前後状況を結ぶ過程。'),
 'zaffected':(['本人','過程','開始','終了'],'その過程による変化を受ける本人。'),
 'zexperience':(['本人','経験','点'],'その本人に属するその時点の経験。'),
 'zcontributes':(['経験','本人','過程','開始','終了'],'同じ本人の同じ能力取得過程へ経験が因果的に寄与する。単なる先行や成功から導かない。'),
}


@lru_cache(None)
def catalogs():return load_catalog(ROOT,SOURCE_BASIS),load_catalog(ROOT,PARENT_BASIS)


def basis(doc,path):
    source,parent=catalogs();entries={**source.entries,**parent.entries};primitives=[];meanings={}
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='definition':meanings[n]=MEANINGS.get(n) or entries[n]['meaning_ja']
        else:
            arguments,meaning=EXTRAS[n] if n in EXTRAS else (entries[n]['arguments'],entries[n]['meaning_ja'])
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=arguments,meaning_ja=meaning))
    return dict(status='assessed_preparation_course_not_canonical_source_change',document=path,primitives=primitives,
        definitions=meanings,limitations=LIMITS,origin_sha256={p:digest((ROOT/p).read_bytes()) for p in (SOURCE,SOURCE_BASIS,PARENT,PARENT_BASIS)})


def build():
    source,parent=catalogs();assert not set(MEANINGS)&set(source.entries)
    lib=deepcopy(source.document);lib['declarations']=closure(source.document,['ta','rlz','r5']);lib['statements']=[]
    lib=parse(format_graph(lib,'compact')+definitions())
    example=deepcopy(parent.document);example['statements']=[]
    example['declarations']=[d for d in example['declarations'] if d['name']!='zscope']
    have={d['name'] for d in example['declarations']}
    example['declarations'] += [d for d in lib['declarations'] if d['name'] not in have]
    suffix='''
r zhistory[a a d d d] c.r zfinish[a a d d] d.r ztaskpoint[a a d d] d.r zassessed[a d] c.r zcapable[a d] c.
r zprocess[a] a.r zevents[a] j[a].r zwhen[a] d.r zbefore[d d] c.
r ztransitions[a d d] c.r zaffected[a a d d] c.r zexperience[a a d] c.r zcontributes[a a a d d] c.
'''
    args='v person i[point d][k zhistory[v person v method v anchor v scene v point]] p zbefore v scene k zfinish[v person v method v anchor v scene] p zassessed'
    fields='person a method a anchor d scene d'
    endpoint='k zfinish[v person v method v anchor v scene]';taskpoint='k ztaskpoint[v person v method v anchor v scene]'
    checked='k zchecked[v person v method v anchor v scene]'
    suffix+=definition('zchecked',fields,both('k rqvf['+args+']',
        'k zhistory[v person v method v anchor v scene '+taskpoint+']','k zbefore['+endpoint+' '+taskpoint+']'))
    suffix+=definition('zscope',fields,both(checked,'k rqvg['+args+' p zcapable]'))
    suffix+=definition('zlearning',fields,both(checked,'k rqvi['+args+' p zcapable k zprocess[v method] k zevents[v method] p zwhen p ztransitions p zaffected p zexperience p zcontributes]'))
    suffix+='r zdirect[] a.r ztraining[] a.'
    current='k zperson[] k bb[k zperson[]] k zanchor[] '
    scoped='k rqve[k zanchor[] p zscope p ae]'
    tail=' p af p ap'
    allchecked='k rqvj[k zperson[] k zanchor[] k zanchor[] p ae p zchecked]'
    positive='k xd['+current+scoped+tail+']';negative='k xg['+current+scoped+tail+']'
    suffix+=''.join('q[k zlearning[k zperson[] k '+method+'[] k zanchor[] k zanchor[]]].' for method in ('ztraining','zdirect'))
    suffix+='q[k xd['+current+'p ae'+tail+']].q['+positive+'].q['+negative+'].q['+allchecked+'].q[w['+allchecked+']['+negative+']].q[x['+positive+'][w['+allchecked+']['+negative+']]].'
    example=parse(format_graph(example,'compact')+suffix)
    encoded=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {LIBRARY:format_graph(lib,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n',
        BASIS:encoded(basis(lib,LIBRARY)),EXAMPLE_BASIS:encoded(basis(example,EXAMPLE))}


def main():
    for name,text in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==text,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print('Preparation histories and experiential acquisition composed',flush=True)


if __name__=='__main__':main()
