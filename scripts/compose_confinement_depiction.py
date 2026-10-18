"""Connect the confinement depiction to the current factual target reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_prevented_attempt import ROOT,closure

PARENT='examples/v016/kant-prevented-attempt.noema'
PARENT_BASIS='data/prevented-attempt-basis-v1.json'
FULL='examples/v016/kant-confinement-depiction.noema'
CORE='examples/v016/confinement-depiction-core.noema'
BASIS='data/confinement-depiction-basis-v1.json'
ANNOTATIONS='data/confinement-depiction-identifiers-v1.json'
MEANINGS={
 'hzss':'提示時点でqjの監督対象として選ばれた同じ本人について、それより前の状況に同じ後見人群dbの行為が非試行hzsnを生じさせたという対象側の部分記述。対象者を過去の信念で選び直さず、提示時点の非試行や特定の因果方程式を要求しない。',
 'hzsu':'閉じ込めの関係節hzstで、著者が対象側hzssを描写側zbfに対応させて非字義的に提示する。対象と描写の人物引数を対応させるが、内容の同値性や動物としての現実の分類を主張しない。箇所を同じ複文hzsqの一部として扱う。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|{'hzst'})&set(old.entries)
    doc=parse(format_graph(doc,'compact')+'''
d hzss[person a] e[b anchor[w[t[k qj[v person]][v anchor]][g prior d[w[k dd[v prior v anchor]][t[k hzsn[k db[] v person]][v prior]]]]]].
r hzst[] a.
d hzsu[] c[k qh[k hzst[] k wa[] r[p hzss] r[p zbf] k wh[]]].
''')
    doc['statements']=statements+parse(format_graph(doc,'compact')+'s[k hzsu[]].')['statements']
    doc=parse(format_graph(doc,'compact'));core=deepcopy(doc);core['declarations']=closure(doc,['hzsu']);core['statements']=[doc['statements'][-1]]
    added=doc['declarations'][size:];ref=next(d for d in added if d['name']=='hzst')
    basis=dict(status='confinement_depiction_connected_to_factual_target_partial_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzst':dict(parameters=ref['parameters'],result=ref['result'],arguments=[],meaning_ja='第二段落の同じ複文hzsqにある、歩行器へ閉じ込めたことを述べる関係節の箇所。注記の提示点であり、意味を表す基本関係ではない。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        limitations=['対象側は監督対象と先行する試みの阻止を結ぶ部分読解。許可・機会・勇気の全意味を解決しない。',
            '描写側zbfは既存の飼育・帰属・歩行訓練装置・閉じ込めの成立と継続を含む。履歴内の継続を採る解釈候補であり、原文から唯一の時間構造や物理機構を導いたものではない。',
            'hzstがhzsq内の原文箇所であることは局所参照の規約と対応記録で固定する。文脈内包を実行する新しい原始述語は追加しない。',
            '身体的な歩行の詳細、穏順さ、慎重さ、評価的効果、家畜概念の境界、比喩全体と第二段落全体の意味確認は残る。',
            '旧q3・zbgは保存する。既存36文と九単位の意味判断は変更しない。'])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/prevented-attempt-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Confinement depiction connected to the factual target reading',flush=True)


if __name__=='__main__':main()
