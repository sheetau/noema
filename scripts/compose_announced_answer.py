"""Connect the cited answer to the issue announced in the source footnote."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT

PARENT='examples/v016/kant-dateline-reading.noema'
PARENT_BASIS='data/dateline-reading-basis-v1.json'
FULL='examples/v016/kant-announced-answer.noema'
BASIS='data/announced-answer-basis-v1.json'
ANNOTATIONS='data/announced-answer-identifiers-v1.json'


def membership():
    return {'kind':'call','symbol':'hzjw','arguments':[
        {'kind':'call','symbol':n,'arguments':[]} for n in ('hzjn','hzkf','hzjl')]}


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    declaration=next(d for d in doc['declarations'] if d['name']=='hzkk')
    # Obtain the conjunction node from the parser rather than duplicating its schema.
    template=parse('p:r ja[] c.r jb[] c.d jc[] c[w[k ja[]][k jb[]]].')['declarations'][-1]['body']
    assert template['kind']=='and'
    declaration['body']=dict(template,arguments=[declaration['body'],membership()])
    doc=parse(format_graph(doc,'compact'))
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];entry=cat.entries[n]
        if d['kind']=='primitive':
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
        else:definitions[n]=entry['meaning_ja']
    definitions['hzkk']+=' 紹介された同じ回答hzjnは、案内対象である同じ9月号hzkfに掲載される。別の号にしか載っていない回答や案内そのものを代用しない。これは当該号の内容案内としての文脈的な読みであり、著者が回答自体を読んだことや受け取ったことは要求しない。'
    basis=dict(status='partial_announced_issue_answer_membership',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_definitions=['hzkk'],new_definitions=[],new_primitives=[]),
        primitives=primitives,definitions=definitions,
        limitations=[
            '原刊の週報37号289頁と291〜293頁、案内対象の月刊誌193頁・198頁を照合し、同じ回答が案内対象の9月号の収録内容であるという読みを採用する。カントの原文に頁数や号数を追加しない。',
            '掲載関係hzjwを一回追加する。読書・受領・賛同・案内への回答全文の収録を推定しない。新しい基本記号、宣言、本文の文は増やさない。',
            '史料の所在を記録したことは、当時の読書や未受領の史実を証明したことではない。採用した読解と有限対照検査を区別する。',
            '週刊という頻度と人名を含む刊行物名の記述的な働き、敬称、代名詞、思想比較など脚注全体の意味確認は残る。署名と日付行の依存内容は保存する。',
        ],unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in cat.lineage],
        predecessor_source_sha256=cat.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/dateline-reading-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Cited answer connected to the announced issue')


if __name__=='__main__':main()
