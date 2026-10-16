"""Distinguish an actual causal condition from adopting a causal explanation."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-described-transition.noema'
PARENT_BASIS='data/described-transition-basis-v1.json'
FULL='examples/v016/kant-factive-cause.noema'
LIBRARY='examples/v016/factive-cause.noema'
BASIS='data/factive-cause-basis-v1.json'
CONVENTION='指定した評価状況で、第一対象について記述された要因が、第二対象について記述された結果の成立に因果的に寄与する関係。説明としての採用、二内容の単なる共存、時間的先行だけでは成立しない。要因と結果はNoemaの性質記述で指定し、両内容の実際の成立はrqquで別に検査する。唯一・十分・必要な原因であることや、特定の介入モデルを付け加えない。'
MEANINGS={
 'rqqu':'同じ二対象・要因記述・結果記述・状況で両内容が成立し、hzieの因果的な寄与関係がある。原因説明として採用されたというeaや、両内容の共存だけとは区別する。',
 'rqqv':'同じ本人・結果記述・状況について、選択した要因がrqquの実際の原因であり、除外した要因はその実際の原因ではない。除外した要因自体が存在しないという条件にはしない。',
 'bd':'bcの未成熟にあり、同じ本人について決意と勇気の不足bsがその未成熟bfの実際の原因で、理解能力の不足bjはその実際の原因ではない。説明に採用されたというedから区別する。bsの連言の読みは保持する。',
 'be':'同じ本人の自己に原因が帰せられた未成熟から自立的使用の能力への変化である。ag・bd・xd・laを満たし、同じ過程の構成内容を本人のbpからupへの変化としてhzidに結ぶ。この版のbdは実際の因果条件を用いる。能力評価の範囲と過程の接続は前版を保持する。',
}
LIMITS=[
 '実際の原因という条件を定義内容に含めることと、原著者の哲学的主張を実証することは別である。本文のuaによる定義提示は内容を評価せず、現実の事例の存在を補わない。',
 'hzieは意味を明示した基本関係。因果の発見・実証方法、心理機構、因果寄与の一般理論をこの宣言だけで与えたとはしない。',
 '先行するea・eb・ec・edを改変せず、説明への採用と実際の原因の二種類を言語内で保持する。他の段落で説明への採用を用いる箇所の再点検は残る。',
 '除外した要因が存在するが結果の原因ではない場合を許す。理解能力が十分であることを新しい必要条件にしない。',
 '決意の不足と勇気の不足をbsの連言で扱う従来の読み、程度の基準、能力評価範囲ap、wennによる条件提示と定義の範囲、第一段落全体の意味確認は残る。',
 '因果関係は同じ評価状況を引数にする。内容自体が過去・持続などを記述することは妨げないが、今回の既存bsとbfから詳細な時間機構を導かない。',
]


def additions():
    code='i[h[a] e]'
    return ('r hzie[a '+code+' a '+code+' d] c.'+
        'd rqqu[actor a factor '+code+' target a result '+code+' scene d] c['+
        'w[k eb[v actor v factor v target v result v scene]][k hzie[v actor v factor v target v result v scene]]].'+
        'd rqqv[person a selected '+code+' excluded '+code+' result '+code+' scene d] c['+
        'w[k rqqu[v person v selected v person v result v scene]][u[k rqqu[v person v excluded v person v result v scene]]]].')


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document);assert catalog.document_path==PARENT
    names={d['name'] for d in doc['declarations']};assert not names&{'hzie','rqqu','rqqv'}
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='bd')
    prefix=deepcopy(doc);prefix['declarations']=prefix['declarations'][:index];prefix['statements']=[]
    extended=parse(format_graph(prefix,'compact')+additions())
    doc['declarations'][index:index]=extended['declarations'][index:]
    bd=next(d for d in doc['declarations'] if d['name']=='bd')
    assert bd['body']['arguments'][1]['symbol']=='ed'
    # Generic rqqv evaluates arbitrary quoted descriptions and therefore has a
    # rank-1 effect. The manuscript quotes bi at rank 0. Specialize its fixed
    # property references as direct calls instead of silently raising or
    # weakening the quotation boundary.
    person=dict(kind='variable',name='va');scene=dict(kind='variable',name='vb')
    quote=lambda n:dict(kind='quote',body=dict(kind='function_ref',symbol=n))
    truth=lambda n:dict(kind='evaluate',content=dict(kind='call',symbol=n,arguments=[deepcopy(person)]),situation=deepcopy(scene))
    cause=lambda n:dict(kind='call',symbol='hzie',arguments=[deepcopy(person),quote(n),deepcopy(person),quote('bf'),deepcopy(scene)])
    both=lambda left,right:dict(kind='and',arguments=[left,right])
    excluded=both(truth('bj'),cause('bj'))
    bd['body']=both(deepcopy(bd['body']['arguments'][0]),both(truth('bs'),both(cause('bs'),dict(kind='not',arguments=[excluded]))))
    doc=parse(format_graph(doc,'compact'));lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['bi','ed','rqqv'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        name=d['name'];entry=catalog.entries.get(name)
        if d['kind']=='primitive':
            primitives.append(dict(symbol=name,parameters=d['parameters'],result=d['result'],
                arguments=['要因側の対象','要因の性質記述','結果側の対象','結果の性質記述','評価状況'] if name=='hzie' else entry['arguments'],
                meaning_ja=CONVENTION if name=='hzie' else entry['meaning_ja']))
        else:definitions[name]=MEANINGS[name] if name in MEANINGS else entry['meaning_ja']
    basis=dict(status='factive_causal_condition_in_opening_definition',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['bd'],clarified_inherited_conventions=['be'],new_primitives=['hzie'],new_definitions=['rqqu','rqqv'],statement_syntax_unchanged=True),
        primitives=primitives,definitions=definitions,limitations=LIMITS,
        unresolved=[dict(basis=row['basis'],caveats=row['caveats']) for row in catalog.lineage],predecessor_source_sha256=catalog.source_sha256)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Opening causal condition distinguishes actual contribution from explanatory adoption')


if __name__=='__main__':main()
