"""Use Kant's own gloss to interpret the Latin directive in this passage."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-exercise-capacity.noema'
PARENT_BASIS='data/exercise-capacity-basis-v1.json'
FULL='examples/v016/kant-contextual-motto.noema'
CORE='examples/v016/contextual-motto-core.noema'
BASIS='data/contextual-motto-basis-v1.json'
ANNOTATIONS='data/contextual-motto-identifiers-v1.json'
MEANINGS={
 'hzsi':'この箇所のsapere audeを、著者自身の後続説明に従い、自分の理解力を使うbmへ勇気を持って取り組む呼びかけと読む。既存hzs5を用い、判断能力の取得や全対象に対する理由ある判断の成功を追加しない。sapere一般の全語義をbmと同一視する定義ではない。',
 'hzsj':'この文脈で解釈したラテン語hzsiと後続ドイツ語bnを、この順序で保持する二つの閉じた発話記述。目標を共有しても、取り組みを求める発話と勇気を求める発話を同一の引用へ縮めない。',
 'hzsk':'hzsjの二つの発話全体を、啓蒙の性質biについての標語として位置付ける内容。引用から実際の実行や成功を推論しない。',
 'hzsl':'冒頭の六箇所を、定義二つ・条件的主張・ラテン語の呼びかけ・ドイツ語の説明・標語の帰結として提示する。hzsbのラテン語と標語の参照だけをhzsiとhzskへ更新し、著者・本文順序・説明の向き・根拠範囲を保つ。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not set(MEANINGS)&set(old.entries);size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+'''
d hzsi[person a] f[k hzs5[v person r[p bm]]].
d hzsj[] j[i[f]][l[i[f]][r[k hzsi[k ao[]]] r[k bn[k ao[]]]]].
''')
    for original,name,mapping in [('hzsa','hzsk',{'hzs7':'hzsj'}),('hzsb','hzsl',{'hzs6':'hzsi','hzsa':'hzsk'})]:
        d=replace_symbols(deepcopy(old.entries[original]['declaration']),mapping);d['name']=name;doc['declarations'].append(d)
    doc['statements']=deepcopy(statements);doc['statements'][1]=replace_symbols(statements[1],{'hzsb':'hzsl'})
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['declarations']=closure(doc,['hzsl','wa','wh','wb','wc','wd','we','wf','wg']);core['statements']=[doc['statements'][1]]
    basis=dict(status='adopted_author_gloss_reading_of_latin_motto',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={},definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=['カントのこの箇所での説明に即した読解。ラテン語の一般辞書定義や全歴史的含意を置き換えない。',
            '旧bk・yb・hzs6は比較用に保持するが、新しい冒頭のラテン語の意味依存には含めない。',
            '単位全体の同義判断は別の読解記録で行う。型検査や有限モデルの全通過だけから判定しない。',
            '原文の綴り・書体・韻律の再現を意味記述の条件にしない。引用の二箇所と著者の説明関係は保持する。'])
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/exercise-capacity-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Latin directive now follows the author gloss without the added competence test',flush=True)


if __name__=='__main__':main()
