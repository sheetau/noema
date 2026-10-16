"""Keep the descriptive classification of an honorific inside designation scope."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT

PARENT='examples/v016/kant-attached-note.noema'
PARENT_BASIS='data/attached-note-basis-v1.json'
FULL='examples/v016/kant-projected-classification.noema'
BASIS='data/projected-classification-basis-v1.json'
ANNOTATIONS='data/projected-classification-identifiers-v1.json'
MEANINGS={
 'hzmb':'対象が既存のMendelssohn参照hzjoと同一であるという人物選択の性質。呼称の性別描写とは区別し、人物の取り違えを呼称の共通性で許さない。',
 'hzmc':'人であり、指定文脈の男性分類hzmaに当たるという描写内容。成人年齢、法的地位、権限、女性分類の否定を定義に加えない。',
 'hzmd':'既存の丁寧な名称使用hzlrに加え、著者がその同じ箇所hzlpで、同じ人物を選ぶ記述hzmbに対して男性分類の描写hzmcを呼称として用いる。描写を引用で保持し、その人の実際の属性や著者の内心として実行しない。',
}


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document)
    assert not {'hzma',*MEANINGS}&set(catalog.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text=('r hzma[a d] c.'
        'd hzmb[person a] e[b context[e[v person][k hzjo[]]]].'
        'd hzmc[person a] e[b context[w[k aa[v person]][k hzma[v person v context]]]].'
        'd hzmd[] c[w[k hzlr[]][k rq[k wa[] k hzlp[] r[p hzmb] r[p hzmc] k hzjl[] p du]]].'
        's[k hzmd[]].')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=old+doc['statements']
    added=doc['declarations'][size:];primitive=added[0]
    basis=dict(status='partial_projected_masculine_honorific_classification',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzma':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=['人物','分類文脈'],
            meaning_ja='この文脈の人物分類において、その人を男性の分類に含める。分類基準は文脈に依存し、生殖器・染色体・自己認識・法的登録の一つへ無断で還元しない。既存の女性分類daの否定とは定義しない。呼称がこの分類を描写に使うことと、この分類が実際に成立することは別である。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        limitations=[
            'Herrnの男性向けの呼称という側面を、同じ人物への丁寧な言及と合成する。呼称の全歴史的用法や他言語への自動対訳を定義するものではない。',
            '男性分類は明示した意味上の基本関係であり、女性分類の補集合・生物学的な二分法・成人年齢から導かない。分類基準自体の詳しい構成説明は別途必要。',
            '分類を呼称内の描写として保持する。相手の実際の性別、身分、命令権、話者の真摯な信念へ昇格させない。',
            '既存のrq・duと閉じた性質記述を再利用する。新しい人物・名前・呼称使用の参照は作らず、Herrnの文字列を意味本体には格納しない。',
            '既存26文・全宣言・意味規約・名称表記を保存する。社会的な敬意の規約、偶発性・思想比較、脚注全体と二作品全文の意味確認は未完。',
        ])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/attached-note-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Honorific classification retained as a description, separate from actual membership')


if __name__=='__main__':main()
