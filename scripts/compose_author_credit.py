"""Represent a printed author credit without identifying its physical presenter."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-author-signature.noema'
PARENT_BASIS='data/author-signature-basis-v1.json'
FULL='examples/v016/kant-author-credit.noema'
LIBRARY='examples/v016/author-credit.noema'
BASIS='data/author-credit-basis-v1.json'
ANNOTATIONS='data/author-credit-identifiers-v1.json'
MEANINGS={
 'rqqx':'同じ名称使用が同じ文脈で成立し、同じ名称を同じ対象へ適用し、その同じ使用が指定文書の著者としてその対象を表示する。誰が実際に表示を行ったか、表示の真正性・自筆性は要求しない。',
 'hzil':'末尾の署名の名称hzifを、本文で共有する著者参照waへ適用し、同じ文書hzikの著者表示として結ぶ。名称個体と人物を区別し、末尾の文脈hzimを使う。表示を行った人物をwaに固定しない。',
}


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document)
    names={d['name'] for d in doc['declarations']};assert 'rqqx' not in names
    generic=parse('p:d rqqx[activity a label a subject a document a context d occurs h[a d] c assigns h[a a a d] c credits h[a a a d] c] c['+
        'w[c[v occurs][v activity v context]][w[c[v assigns][v activity v label v subject v context]]'+
        '[c[v credits][v activity v document v subject v context]]]].')['declarations'][0]
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='hzil')
    doc['declarations'].insert(index,generic)
    prefix=deepcopy(doc);prefix['declarations']=doc['declarations'][:index+1];prefix['statements']=[]
    revised=parse(format_graph(prefix,'compact')+
        'd hzil[] c[w[u[e[k hzif[]][k wa[]]]][k rqqx[k hzig[] k hzif[] k wa[] k hzik[] k hzim[] p dg p hzih p hzij]]].')['declarations'][-1]
    doc['declarations'][index+1]=revised;doc=parse(format_graph(doc,'compact'))
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqqx'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        name=d['name'];entry=catalog.entries.get(name)
        if d['kind']=='primitive':
            primitives.append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
        else:definitions[name]=MEANINGS[name] if name in MEANINGS else entry['meaning_ja']
    basis=dict(status='printed_author_credit_without_presenter_inference',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,revision=dict(changed_bodies=['hzil'],new_definitions=['rqqx'],new_primitives=0),
        primitives=primitives,definitions=definitions,
        limitations=['表記の画像照合は別記録author-signature-facsimile-v1.jsonを参照する。本文の転記と編集上の展開を区別する。',
            '表示された著者と表示の実行者を同一視しない。人物の全経歴、表示の真正性、自筆性の証明をこの記述に加えない。',
            '署名以外の本文の未解決点は継承する。この修正だけで他の原文単位を意味確認済みとしない。'],
        superseded_parent_limitations=['原刊画像未照合という旧時点の記録は、保存した494頁の視認で更新する。',
            '著者自身を提示者とする旧hzilの読みを撤回し、提示者を指定しない著者表示へ変更する。'],
        unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in catalog.lineage],predecessor_source_sha256=catalog.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    annotation=json.loads((ROOT/'data/author-signature-identifiers-v1.json').read_text(encoding='utf-8'))
    annotation.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    annotation['entries'][0]['forms'].append(dict(text='I. Kant.',language='de',role='facsimile_reading_following_transcription_convention'))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(annotation,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Author credit is represented without an inferred presenter')


if __name__=='__main__':main()
