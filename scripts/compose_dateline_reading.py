"""Fix the adopted civil-calendar reading and stale period conventions."""
import hashlib
import json

from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT

PARENT='examples/v016/kant-gregorian-rules.noema'
PARENT_BASIS='data/gregorian-rules-basis-v1.json'
FULL='examples/v016/kant-dateline-reading.noema'
BASIS='data/dateline-reading-basis-v1.json'
ANNOTATIONS='data/dateline-reading-identifiers-v1.json'
MEANINGS={
    'hzix':'この日付行で用いる民用暦の局所参照。採用する読解は、西暦の紀元と1月1日の年始を持つグレゴリオ暦の年月日である。1784年のプロイセンに関する歴史的読解として明示し、原文が暦名を明記したとは扱わない。日付は現地の民用日を指し、UTCオフセット・時刻・実際の執筆時点を補わない。数値的な閏年と月長はrqsh・rqsi・rqsjに記述するが、それらの成立だけからこの歴史的同定を導かない。',
    'hzjg':'この日付行が指定する月期間の局所参照。指定した暦・年・文脈で月番号9がこの期間を一意に指すことを本文のrqsdで要求する。月列の位置として指定しない。',
    'hzjh':'この日付行が指定する日期間の局所参照。指定した暦・月・文脈で日番号30がこの期間を一意に指すことを本文のrqsdで要求する。欠番を詰めた日列の位置として指定しない。',
}


def build():
    cat=load_catalog(ROOT,PARENT_BASIS)
    primitives=[];definitions={}
    for d in cat.document['declarations']:
        n=d['name'];entry=cat.entries[n]
        if d['kind']=='primitive':
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],
                arguments=entry['arguments'],meaning_ja=MEANINGS.get(n,entry['meaning_ja'])))
        else:definitions[n]=entry['meaning_ja']
    body=(ROOT/PARENT).read_text(encoding='utf-8')
    basis=dict(status='explicit_historically_supported_dateline_reading',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_primitive_meanings=list(MEANINGS),changed_declarations=[],new_primitives=[],new_definitions=[]),
        primitives=primitives,definitions=definitions,
        limitations=[
            '年月日の歴史的読解を意味規約に明記する改訂。本文の全宣言と23文、固有名の識別表記、数値的な暦規則は保存する。',
            '原刊494頁の略記と電子転記の展開を区別する。グレゴリオ暦という名称は原文にないため、採用した読解として記録する。',
            '暦の採用を有限モデルから証明しない。史料に基づく同定はdata/dateline-calendar-evidence-v1.jsonとdocs/dateline-reading-v1.mdに根拠と限界を置く。',
            '原文は日付を示し、時刻・UTCオフセット・書き終えた瞬間を指定しない。日付の表示と実際の執筆・刊行イベントを区別する。',
            '日付行全体の判断は別の単位別レビューに置く。脚注と他の本文に残る意味上の課題を、この規約の改訂だけで解消したとはしない。',
        ],unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in cat.lineage],
        predecessor_source_sha256=cat.source_sha256)
    ann=json.loads((ROOT/'data/gregorian-rules-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Explicit dateline calendar reading; Noema manuscript unchanged')


if __name__=='__main__':main()
