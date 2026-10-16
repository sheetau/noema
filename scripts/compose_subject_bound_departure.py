"""Connect the opening departure to the person undergoing that process."""
from copy import deepcopy
import json
from pathlib import Path

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.extraction import _references

ROOT=Path(__file__).resolve().parents[1]
PARENT='examples/v016/kant-definition-question.noema'
PARENT_BASIS='data/definition-question-basis-v1.json'
FULL='examples/v016/kant-subject-bound-departure.noema'
LIBRARY='examples/v016/subject-bound-departure.noema'
BASIS='data/subject-bound-departure-basis-v1.json'
MEANING='同じ人について、自己に原因が帰せられた未成熟bdから、自立的使用bbを達成する方法がある状態へ移る。agの同じ変化過程・同じ前後状況で、その人が状態変化を受ける対象であることを既存laで要求する。無関係な人の過程や、単なる目撃・原因としての関与では満たさない。'
LIMITS=[
    '本人と変化過程の接続を修正する。能力評価の範囲ap、原因説明ea、決意と勇気の不足の読みは前版を引き継ぎ、ここで原文との同義性を認定しない。',
    'laは対象・過程・前後状況を結ぶ基本関係である。原因となる活動や本人の意図的行為と同一視せず、他者の助力も排除しない。',
    'agは先行から後行への実際の変化、laはその変化を受ける対象という意味規約を使う。独立した二つの状態の存在だけから両関係を導かない。',
    '過程の全時間範囲、最初・唯一の完了点、能力の恒久的保持や全ての評価方法の妥当性を追加条件にしない。原文の完全な意味確認は未完。',
    'beの意味を改訂した完全な規約であり、前版へ宣言を追加するだけの互換差分ではない。biを参照する全ての定義と引用は、この文書の改訂されたbeを参照する。',
]


def closure(doc,roots):
    lookup={d['name']:d for d in doc['declarations']};pending=set(roots);keep=set()
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    return [deepcopy(d) for d in doc['declarations'] if d['name'] in keep]


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);old=catalog.document
    assert catalog.document_path==PARENT
    doc=deepcopy(old);lookup={d['name']:d for d in doc['declarations']}
    affected=lookup['la'];assert affected['kind']=='primitive'
    doc['declarations'].remove(affected)
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='be')
    doc['declarations'].insert(index,affected)
    departure=lookup['be']
    assert [p['name'] for p in departure['parameters']]==['va','vb','vc','vd']
    binding=dict(kind='call',symbol='la',arguments=[dict(kind='variable',name=n) for n in ('va','vb','vc','vd')])
    departure['body']=dict(kind='and',arguments=[deepcopy(departure['body']),binding])
    doc=parse(format_graph(doc,'compact'))
    library=deepcopy(doc);library['statements']=[];library['declarations']=closure(doc,['bi'])
    primitives=[];definitions={}
    for declaration in doc['declarations']:
        name=declaration['name'];entry=catalog.entries[name]
        if declaration['kind']=='primitive':
            primitives.append(dict(symbol=name,parameters=declaration['parameters'],result=declaration['result'],
                arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
        else:definitions[name]=MEANING if name=='be' else entry['meaning_ja']
    basis=dict(status='revised_opening_departure_bound_to_its_subject',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['be'],moved_declarations=['la'],new_declarations=0,statement_syntax_unchanged=True),
        primitives=primitives,definitions=definitions,limitations=LIMITS,
        unresolved=[dict(basis=row['basis'],caveats=row['caveats']) for row in catalog.lineage],
        predecessor_source_sha256=catalog.source_sha256)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Opening departure now requires the same person in the same process and endpoints')


if __name__=='__main__':main()
