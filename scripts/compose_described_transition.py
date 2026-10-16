"""Bind a process to its before/after content, without treating it as a cause."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-subject-bound-departure.noema'
PARENT_BASIS='data/subject-bound-departure-basis-v1.json'
FULL='examples/v016/kant-described-transition.noema'
LIBRARY='examples/v016/described-transition.noema'
BASIS='data/described-transition-basis-v1.json'
PRIMITIVE='hzid'
DECLARATION='r hzid[a a i[h[a] e] i[h[a] e] d d] c.'
ARGUMENTS=['対象','変化過程','前状態の性質記述','後状態の性質記述','先行状況','後行状況']
CONVENTION='指定した同じ対象について、前状態の性質から後状態の性質へ移ることが、この前後状況を結ぶ同じ変化過程の構成内容である。別の性質の変化、同時に起きた別の過程、前後の状態がたまたま成立しただけの場合とは区別する。前後の性質は閉じたNoemaの記述で指定する。外部の先行原因や本人の意図的な行為を要求しない。記述の内容が両端で成立するか、対象がその過程に関わるかは、合成定義で別に検査する。'
MEANING='同じ本人の自己に原因が帰せられた未成熟から自立的使用の能力への変化である。従来のag・bd・xd・laの条件に加え、その同じ過程の構成内容を、同じ本人のbpからupへの変化としてhzidに結ぶ。本人の別の性質が変わるだけの過程では成立しない。能力評価・原因説明の従来の読みは引き継ぐ。'
LIMITS=[
    'hzidは変化過程とその内容を結ぶ一般的な基本関係であり、啓蒙という原語を直接ラベルにした関係ではない。前後の内容は既存bpとupの合成定義で説明する。',
    '引用した前後内容の同定、状態の実際の成立、本人への関与を分ける。前後内容が同じ真理値を持つだけでは、その変化過程の構成内容とは認定しない。',
    '関係は引用記述を引数に持つ。等しい外延を持つ別の記述の代入は自動では行わない。同じ内容の別の記述も適用される場合は、その適用をモデルで別途与える。',
    'この関係の観測・判定を自動化するものではない。検査モデルに与えた関係を、原文の著者が現実の個別過程について認定した事実と混同しない。',
    '過程の構成内容と因果的な先行活動を区別する。本人の意図的行為、単独の実現、唯一の過程、恒久的な達成は付け加えない。',
    '能力評価の結果範囲ap、原因説明eaと自己責任の関係、決意と勇気の不足の読み、過程全体と第一段落全体の意味確認は残る。',
]


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document)
    assert catalog.document_path==PARENT
    lookup={d['name']:d for d in doc['declarations']};assert PRIMITIVE not in lookup
    moved=[lookup[n] for n in ('bp','up')]
    doc['declarations']=[d for d in doc['declarations'] if d['name'] not in ('bp','up')]
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='be')
    new=parse('p:'+DECLARATION)['declarations'][0]
    doc['declarations'][index:index]=moved+[new]
    ref=lambda n:dict(kind='variable',name=n)
    quote=lambda n:dict(kind='quote',body=dict(kind='function_ref',symbol=n))
    link=dict(kind='call',symbol=PRIMITIVE,arguments=[ref('va'),ref('vb'),quote('bp'),quote('up'),ref('vc'),ref('vd')])
    lookup['be']['body']=dict(kind='and',arguments=[deepcopy(lookup['be']['body']),link])
    doc=parse(format_graph(doc,'compact'));lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['bi'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        name=d['name']
        if d['kind']=='primitive':
            entry=catalog.entries.get(name)
            primitives.append(dict(symbol=name,parameters=d['parameters'],result=d['result'],
                arguments=ARGUMENTS if name==PRIMITIVE else entry['arguments'],meaning_ja=CONVENTION if name==PRIMITIVE else entry['meaning_ja']))
        else:definitions[name]=MEANING if name=='be' else catalog.entries[name]['meaning_ja']
    basis=dict(status='revised_departure_bound_to_its_before_after_content',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['be'],moved_declarations=['bp','up'],new_primitives=[PRIMITIVE],new_definitions=0,statement_syntax_unchanged=True),
        primitives=primitives,definitions=definitions,limitations=LIMITS,
        unresolved=[dict(basis=row['basis'],caveats=row['caveats']) for row in catalog.lineage],
        predecessor_source_sha256=catalog.source_sha256)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('The opening departure is bound to the same before/after property descriptions')


if __name__=='__main__':main()
