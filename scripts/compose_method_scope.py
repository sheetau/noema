"""Restrict methods explicitly while retaining the original outcome scope."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_standing_ability import ROOT,EXAMPLE as PARENT,EXAMPLE_BASIS as PARENT_BASIS,SOURCE,SOURCE_BASIS

LIBRARY='examples/v016/method-scope.noema'
EXAMPLE='examples/v016/method-scope-example.noema'
BASIS='data/method-scope-basis-v1.json'
EXAMPLE_BASIS='data/method-scope-example-basis-v1.json'
MEANING='基準状況を固定し、同じ本人・方法・実行状況について、利用可能であり、指定した方法範囲にも入ることを要求する関数。候補状況が変わっても基準状況を取り替えない。結果集合やその評価範囲は変更しない。範囲外を物理的に実行不能とする主張ではなく、この能力判断で量化する方法の制限である。'
LIMITS=[
 '方法の範囲を別途記述するための合成。ある方法が範囲内かを自動推定する機能や、能力・学習の必要十分条件ではない。',
 '習得過程を含めるか、既有の状態で行う試行だけを含めるかは、指定した課題と方法の意味に依存する。比較例のzscopeはその区分を与えた診断用入力であり、学習自体の構成的な説明を代用しない。',
 '空の方法範囲なら、その範囲内に達成方法がないと判定し得る。範囲外にも方法がないという結論や、本人に能力一般がないという結論へ拡張しない。',
 '方法を除外しても、残った方法の評価対象を成功した結果だけへ変更しない。範囲の妥当性や完全性は型だけでは証明できず、成功結果に合わせた範囲の後付けを正当化しない。',
 '機会プロフィールの本人状態の保持は候補場面の始点に対するもの。方法の途中の学習を排除する条件ではない。この区別のために方法範囲を別に渡す。',
 'カント本文と確認済み八単位は変更しない。本文の能力の読み、採る方法範囲、その範囲の説明は未確定である。',
]


def definition():
    return 'd rqve[anchor d scope h[a a d d] c available h[a a d] c] h[a a d] c[i[person a method a scene d][w[c[v available][v person v method v scene]][c[v scope][v person v method v anchor v scene]]]].'


@lru_cache(None)
def catalog():return load_catalog(ROOT,PARENT_BASIS)


def basis(doc,path):
    old=catalog();primitives=[];meanings={}
    for d in doc['declarations']:
        name=d['name']
        if d['kind']=='definition':meanings[name]=MEANING if name=='rqve' else old.entries[name]['meaning_ja']
        else:
            entry=dict(arguments=['本人','方法','基準状況','実行状況'],meaning_ja='比較する課題について、同じ本人・基準から評価に含める方法の範囲。比較例では準備的な習得を含む方法を除く条件を与える。未知の区分を範囲外と補わない。これは診断用の明示的な入力で、現実の学習判定器や著者の指定ではない。') if name=='zscope' else old.entries[name]
            primitives.append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
    return dict(status='explicit_method_scope_comparison_not_canonical_source_change',document=path,
        primitives=primitives,definitions=meanings,limitations=LIMITS,
        origin_sha256={p:digest((ROOT/p).read_bytes()) for p in (PARENT,PARENT_BASIS,SOURCE,SOURCE_BASIS)})


def build():
    old=catalog();assert 'rqve' not in old.entries
    lib=parse('p:'+definition())
    example=deepcopy(old.document);example['statements']=[]
    scoped='k rqve[k zanchor[] p zscope p ae]'
    current='k zperson[] k bb[k zperson[]] k zanchor[] '
    profile=current+'p zcases p zpreserved p zopportunity p zpreferred '
    tail=' p af p ap'
    queries='q[k xd['+current+'p ae'+tail+']].q[k bc[k zperson[] k zanchor[]]].'
    queries+='q[k xd['+current+scoped+tail+']].q[k xg['+current+scoped+tail+']].'
    queries+='q[k rqva['+profile+'p ae'+tail+']].q[k rqva['+profile+scoped+tail+']].q[k rqvb['+profile+scoped+tail+']].'
    example=parse(format_graph(example,'compact')+definition()+'r zscope[a a d d] c.'+queries)
    encoded=lambda value:json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    return {LIBRARY:format_graph(lib,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n',
        BASIS:encoded(basis(lib,LIBRARY)),EXAMPLE_BASIS:encoded(basis(example,EXAMPLE))}


def main():
    for name,text in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==text,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print('Method scope composed independently of opportunity and outcome scope',flush=True)


if __name__=='__main__':main()
