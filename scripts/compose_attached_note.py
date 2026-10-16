"""Compose document membership, note attachment and displayed authorship."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT, closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-current-answer.noema'
PARENT_BASIS='data/current-answer-basis-v1.json'
FULL='examples/v016/kant-attached-note.noema'
LIBRARY='examples/v016/attached-note.noema'
BASIS='data/attached-note-basis-v1.json'
ANNOTATIONS='data/attached-note-identifiers-v1.json'
PRIMITIVES={
 'hzlu':('[] a',[],'原刊494頁の末尾にある著者注u0020を指す文書箇所。注の内容は既存の七文で記述し、この参照だけを内容の代用にしない。'),
 'hzlv':('[] a',[],'同じ論説の本文最終段落u0017の末尾にある注標識の位置。直前の文の意味や注の話題の範囲そのものを指す個体ではない。'),
 'hzlw':('[] a',[],'本文末尾の標識と著者注を結んで表示する構成上の使用。実際の印刷作業や組版者の行為を同定するものではない。'),
 'hzlx':('[a a d] c',['文書箇所','文書','解釈文脈'],'この箇所は、指定された文書の構造上区別される真の部分である。注・節・標識位置などを扱い、単なる引用先や外部文書へのリンク、同名の別文書とは区別する。箇所の内容の真偽や物理的な紙片の包含は主張しない。'),
 'hzly':('[a a a a d] c',['接続の表示','注の箇所','標識の位置','文書','解釈文脈'],'この構成上の表示では、同じ文書のこの位置に付された注としてこの箇所を結ぶ。標識の綴りや紙面上の距離を一致条件にせず、異なる文書の同じ標識を流用しない。注が直前の主張だけを説明すること、因果・証明・論理的含意は含まない。'),
}
MEANINGS={
 'rqsm':'異なる注と標識位置が同じ文書の真の部分であり、成立した同じ表示が両者をその文書内で結び、注の著者を同じ表示で帰属させる。注の話題範囲・真理・実際の印刷者は補わない。',
 'hzlz':'現在の論説hzikの末尾の標識位置hzlvと著者注hzluを同じ表示hzlwで結び、注の著者を既存のwaとして表示する。脚注の解釈文脈hzjlを既存七文と共用する。本文末尾の文への論理的な説明関係は追加しない。',
}


def additions():
    text=''.join('r '+name+sig+'.' for name,(sig,_,_) in PRIMITIVES.items())
    text+='d rqsm[display a author a note a anchor a document a context d occurs h[a d] c part h[a a d] c links h[a a a a d] c credit h[a a a d] c] c['+conjunction([
        'u[e[v note][v anchor]]','u[e[v note][v document]]','u[e[v anchor][v document]]',
        'c[v occurs][v display v context]',
        'c[v part][v note v document v context]','c[v part][v anchor v document v context]',
        'c[v links][v display v note v anchor v document v context]',
        'c[v credit][v display v note v author v context]',
    ])+'].'
    text+='d hzlz[] c[k rqsm[k hzlw[] k wa[] k hzlu[] k hzlv[] k hzik[] k hzjl[] p dg p hzlx p hzly p hzij]].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(cat.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzlz[]].');doc['statements']=old+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqsm'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_attached_author_note',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            '原刊の二つの標識に基づく構造上の接続を記述する。脚注が直前の一文だけを説明するとは主張しない。',
            '著者注という帰属は論説末尾の表示・一人称の連続性と固定資料の区分に基づく読み。肉筆の真正性や実際の組版者を認証しない。',
            '既存25文・全宣言・意味規約・名前の識別表記を保存する。標識位置の参照は最終段落の思想内容の翻訳を代用しない。',
            '注内容の各文と注の内部位置の細分対応、全本文の構成、他の注記慣行の分類は別の課題。脚注全体と二作品全文の意味一致は未完。',
        ])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/current-answer-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Author note attached through shared document membership and a distinct anchor')


if __name__=='__main__':main()
