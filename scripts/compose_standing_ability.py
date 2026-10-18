"""Compose ability over anchored opportunities, separately from ability now."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_courageous_undertaking import FULL as SOURCE,BASIS as SOURCE_BASIS

LIBRARY='examples/v016/standing-ability.noema'
EXAMPLE='examples/v016/standing-ability-example.noema'
BASIS='data/standing-ability-basis-v1.json'
EXAMPLE_BASIS='data/standing-ability-example-basis-v1.json'
FIELDS='person a goal e anchor d cases h[a d d] c preserved h[a d d] c opportunity h[a d] c preferred h[a d d d] c available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c'
ARGS='v person v goal v anchor v cases v preserved v opportunity v preferred v available v outcomes v selected'
MEANINGS={
 'rqu6':'同じ本人と基準状況を固定した候補場面の条件。別人・別の基準時点の候補を借りない。',
 'rqu7':'採用した全候補が、基準の本人について判断の基礎にする内的状態を保持し、その課題の外的実行条件を備えることを要求する。違反した候補を黙って除外して母集団を縮めない。候補の非空性と通常性は呼出側で別に要求する。',
 'rqva':'rqu7の条件を満たす同じ候補範囲で、通常性に劣後しない場面が非空で、その全てに本人が同じ目標を指定結果範囲で達成する方法xdを持つ。方法は場面ごとに選べる。基準状況そのものの機会・実行・成功を要求しない。本人の保持条件や機会の意味が適切な場合に、機会を補った仮定場面での能力を述べる候補となる。',
 'rqvb':'同じ非空の通常場面全てで、全方法の評価が整い、達成方法がないxgが成立する。rqvaの単なる否定ではない。場面ごとに可否が分かれる場合を、通常はできないとまとめない。',
 'rqvc':'同じ非空の通常場面全てで、方法についてxfによる可否の判定条件が成立する。未評価を不能と補わない。',
 'rqvd':'rqvcの全通常場面で判定できる条件を満たし、rqvaの全通常場面で達成可能という条件は満たさない。少なくとも一つの通常場面で達成不能であり、全通常場面で不能というrqvbより弱い。空・不正なプロフィールや未判定からは成立しない。',
}
LIMITS=[
 '場面の広さと、現在の機会を要求するかどうかを別に扱う。多数の場面を並べるだけでは、機会から独立した能力の記述にはならない。',
 'preservedは能力そのものの同一性を仮定する関係ではない。身体・知識・習慣・意図等、判断の基礎に採った本人側の状態を保持する。何を保持するかは課題に即して明示する必要がある。',
 'opportunityは同じ課題についての外的実行条件であり、技能の存在・実行の成功・規範的な許可と同一化しない。候補・保持・機会・通常性を成功結果に合わせて選び直すことは正当化しない。',
 '候補をなす仮定場面は実際の過去・未来の履歴とは限らない。別の時期に学習した本人の状態を、そのまま基準状況の能力の証拠として使わない。',
 'xd・xgの結果評価範囲は継承する。技能・能力全般の必要十分条件、認識や自動推定、身体機構の一般理論は与えない。',
 'カントの現行本文は変更しない。Unvermögenを当該状況の不能と読むか、機会を与えた仮定場面での不能と読むかを比較するための構成であり、後者の採用や段落全体の意味一致を自動で認定しない。',
]
REFERENCE=dict(title='Simon Kittle, On General and Non-General Abilities',
    url='https://onlinelibrary.wiley.com/doi/full/10.1111/papq.12424',
    use='機会を要求するかという区別と、評価する場面範囲の広さという区別を混同しないために参照した。本実装の極小場面・全称条件を、この論文が提案した能力の完全な分析として帰属しない。')


def definitions():
    text='d rqu6[person a anchor d cases h[a d d] c] h[d] c[i[scene d][c[v cases][v person v anchor v scene]]].'
    text+='d rqu7[person a anchor d cases h[a d d] c preserved h[a d d] c opportunity h[a d] c] c[f scene d[y[c[v cases][v person v anchor v scene]][w[c[v preserved][v person v anchor v scene]][c[v opportunity][v person v scene]]]]].'
    valid='k rqu7[v person v anchor v cases v preserved v opportunity]'
    cases='k rqu6[v person v anchor v cases]'
    preferred='i[first d last d][c[v preferred][v person v anchor v first v last]]'
    for name,response in [('rqva','xd'),('rqvb','xg'),('rqvc','xf')]:
        condition='i[scene d][k '+response+'[v person v goal v scene v available v outcomes v selected]]'
        text+='d '+name+'['+FIELDS+'] c[w['+valid+'][k rqt4['+cases+' '+preferred+' '+condition+']]].'
    text+='d rqvd['+FIELDS+'] c[w[k rqvc['+ARGS+']][u[k rqva['+ARGS+']]]].'
    return text


@lru_cache(None)
def catalog():return load_catalog(ROOT,SOURCE_BASIS)


def basis_for(doc,path,new_primitives=None):
    old=catalog();new_primitives=new_primitives or {};primitives=[];meanings={}
    for d in doc['declarations']:
        name=d['name']
        if d['kind']=='primitive':
            entry=new_primitives.get(name) or old.entries[name]
            primitives.append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
        else:meanings[name]=MEANINGS.get(name) or old.entries[name]['meaning_ja']
    return dict(status='anchored_opportunity_profile_not_canonical_source_replacement',document=path,
        source_document=SOURCE,source_meaning_basis=SOURCE_BASIS,primitives=primitives,definitions=meanings,
        limitations=LIMITS,research_reference=REFERENCE,
        origin_sha256={p:digest((ROOT/p).read_bytes()) for p in (SOURCE,SOURCE_BASIS)})


def build():
    old=catalog();assert not set(MEANINGS)&set(old.entries)
    library=deepcopy(old.document);library['statements']=[];library['declarations']=closure(old.document,['xd','xg','xf','rqt4'])
    library=parse(format_graph(library,'compact')+definitions())
    example=deepcopy(old.document);example['statements']=[];example['declarations']=closure(old.document,['bc','bb','xd','xg','xf','rqt4'])
    params='k zperson[] k bb[k zperson[]] k zanchor[] p zcases p zpreserved p zopportunity p zpreferred p ae p af p ap'
    suffix='r zperson[] a.r zanchor[] d.r zcases[a d d] c.r zpreserved[a d d] c.r zopportunity[a d] c.r zpreferred[a d d d] c.'
    suffix+='q[k xd[k zperson[] k bb[k zperson[]] k zanchor[] p ae p af p ap]].q[k bc[k zperson[] k zanchor[]]].'
    suffix+=''.join('q[k '+name+'['+params+']].' for name in ('rqva','rqvb','rqvc','rqvd'))
    example=parse(format_graph(example,'compact')+definitions()+suffix)
    extras={
        'zperson':dict(arguments=[],meaning_ja='比較例で能力を評価する同じ本人。'),
        'zanchor':dict(arguments=[],meaning_ja='本人の現在の状態を固定する比較の基準状況。仮定場面の機会を現在へ移さない。'),
        'zcases':dict(arguments=['本人','基準状況','候補状況'],meaning_ja='同じ本人・基準に対して選ぶ仮定場面。実際にそこで活動したという履歴ではない。'),
        'zpreserved':dict(arguments=['本人','基準状況','候補状況'],meaning_ja='本人について課題の判断の基礎に採った内的状態を基準から保持した仮定場面である。新たな学習や別人への交換で成功させない。能力そのものが同一だという仮定で結論を先取りしない。'),
        'zopportunity':dict(arguments=['本人','候補状況'],meaning_ja='この課題を自ら試みる外的な条件が与えられる。実際の試み・技能・成功は要求しない。'),
        'zpreferred':dict(arguments=['本人','基準状況','優先候補','劣後候補'],meaning_ja='同じ本人と基準において、最初の候補を次の候補より文脈上通常とみなす厳密な比較。成功したことだけを優先理由にしない。'),
    }
    encoded=lambda value:json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n',
        BASIS:encoded(basis_for(library,LIBRARY)),EXAMPLE_BASIS:encoded(basis_for(example,EXAMPLE,extras))}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Anchored ability and present opportunity can be compared without changing the authored source',flush=True)


if __name__=='__main__':main()
