"""Keep a courteous source mention distinct from an embedded citation."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-announced-answer.noema'
PARENT_BASIS='data/announced-answer-basis-v1.json'
FULL='examples/v016/kant-courteous-reference.noema'
LIBRARY='examples/v016/courteous-reference.noema'
BASIS='data/courteous-reference-basis-v1.json'
ANNOTATIONS='data/courteous-reference-identifiers-v1.json'
PRIMITIVES={
 'hzlp':('[] a',[],'この脚注のdes Herrn Mendelssohnで人物を指す名称使用の箇所。紹介記事内の引用・紹介行為hzjqとは別の使用である。肉筆、印刷作業、歴史的な提示者の同定は含まない。'),
 'hzlq':('[a a d] c',['名称使用','言及対象','文脈'],'この名称使用では、当該文脈の対人慣習上、その対象を丁寧に扱う形で言及している。表現の社会的な扱いの区別であり、話し手の実際の敬愛・賛同、対象の権限・身分、その場にいること、直接の呼びかけは含意しない。どの慣習が適用されるかを別文脈から自動補完しない。'),
}
MEANINGS={
 'rqsl':'同じ名称使用の成立、同じ名称の同じ対象への適用、その同じ使用での同じ対象の丁寧な扱いを結ぶ。敬愛という心理状態や対象の身分の真理を代わりに要求しない。三関係は明示した同じ文脈で評価する。',
 'hzlr':'カント脚注自身の名称使用hzlpが、Mendelssohnの既存名称hzjpで同じ人物hzjoを丁寧に指す。名称と人物を区別し、紹介記事内の使用hzjqとは別に要求する。人物の直接の呼びかけ・受領・賛同を主張しない。',
}


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqsl[use a name a target a context d occurs h[a d] c names h[a a a d] c courtesy h[a a d] c] c['+conjunction([
        'c[v occurs][v use v context]','c[v names][v use v name v target v context]',
        'c[v courtesy][v use v target v context]'])+'].'
    text+='d hzlr[] c['+conjunction(['u[e[k hzlp[]][k hzjq[]]]','u[e[k hzjp[]][k hzjo[]]]',
        'k rqsl[k hzlp[] k hzjp[] k hzjo[] k hzjl[] p dg p hzih p hzlq]'])+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzlr[]].');doc['statements']=statements+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqsl'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_conventional_courtesy_in_source_reference',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            'Herrnをこの箇所の敬称使用として読む。歴史的な語義の確認は資料に基づく読解であり、辞書照合や生成を行う翻訳規則は実装しない。',
            '丁寧な言及と心理的な敬愛・学説への賛同・身分や命令権を区別する。敬称だけからこれらを導かない。',
            '男性用の呼称や社会階層との歴史的な関係、他文化の全敬称の分類、皮肉の解釈はこの一般関係だけでは説明し尽くさない。原文の敬称全体の意味一致を自動認定しない。',
            '原文の姓の識別表記は保存し、Herrnを姓の一部へ混ぜない。新しい人物参照は作らず、同じMendelssohnに対する二つの使用を区別する。',
            '既存23文と全宣言・意味規約を保存し、新しい一文を加える。脚注全体の意味確認、二作品全文と任意の内容の表現可能性は未完。',
        ])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/announced-answer-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Courteous source reference composed separately from the embedded citation')


if __name__=='__main__':main()
