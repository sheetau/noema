"""Bind a written name use to the document's existing author reference."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-factive-cause.noema'
PARENT_BASIS='data/factive-cause-basis-v1.json'
FULL='examples/v016/kant-author-signature.noema'
LIBRARY='examples/v016/author-signature.noema'
BASIS='data/author-signature-basis-v1.json'
ANNOTATIONS='data/author-signature-identifiers-v1.json'
PRIMITIVES={
 'hzif':([], 'この署名で用いる名称を指す個体。名前を持つ人物そのものとは区別する。綴りは識別表記の別添えに保持し、同じ綴りから人物同一性を推論しない。'),
 'hzig':([], 'カント文書末尾u0018の署名における名称使用の提示行為。文書で表された提示を指し、原稿の筆跡や物理的な印刷作業を特定するものではない。'),
 'hzih':(['名称使用の行為','名称個体','指される対象','文脈'], '同じ提示行為で、この名称がこの対象へ適用される。名称の綴りが一致するだけでは成立せず、別の文脈や名称使用の適用先を自動的に引き継がない。'),
 'hzij':(['提示行為','文書','著者として表示される対象','文脈'], 'この文書の指定した提示行為が、その対象を文書の著者として表示する役割を持つ。単なる人物への言及、引用された他文書の署名、名前の一般的な使用とは区別する。表示の真実性や自筆であることは含まない。'),
 'hzik':([], '現在Noemaで記述しているカント1784年の論説を指す文書個体。別の文書や、その複製媒体の個体とは区別する。'),
 'hzim':([], 'この文書末尾の署名を提示する文脈。冒頭段落の文脈whと無条件に同一視しない。'),
}
MEANINGS={
 'rqqw':'同じ提示者・名称使用・名称・対象・文脈でrnhが成立し、その同じ使用が指定文書の著者として同じ対象を表示する。提示者と表示される著者は別引数で、代筆や編集上の提示も区別して記述できる。',
 'hzil':'本文全体で使う著者参照waを、末尾の名称使用hzigの同じ表示対象へ結ぶ。文書hzikと署名文脈hzimを固定し、原文の署名における著者自身の提示として扱う。現存媒体が自筆であるとは主張しない。',
}
LIMITS=[
 '原文単位はI.[mmanuel] Kant.という電子版の転記である。括弧内の展開を原刊の字面と同一視せず、綴りの形を別添えで区別する。原刊画像との照合は未完。',
 '識別表記は名称個体に付ける注記であり、人物の意味、概念の説明、名前の社会的な獲得過程を原語文字列で代用しない。名称の適用と著者表示はNoema本文で記述する。',
 '同じ文字列を持つ複数の名称個体や、複数の表記を持つ一名称個体を許す。名前の一致だけで、別人を統合したり指示対象を選んだりしない。',
 '署名の提示者を著者とする文書内の読みを採る。物理的な筆記・印刷の行為者や、自筆性・真正性・権利の認定は補わない。',
 '署名箇所を既存の著者参照へ接続するが、人物の伝記全体、出生地、日付、前後の論証、二作品全文の意味確認を完了したとはしない。',
]


def additions():
    return ('r hzif[] a.r hzig[] a.r hzih[a a a d] c.r hzij[a a a d] c.r hzik[] a.r hzim[] d.'+
        'd rqqw[presenter a activity a label a subject a document a context d occurs h[a d] c presents h[a a d] c assigns h[a a a d] c credits h[a a a d] c] c['+
        'w[k rnh[v presenter v activity v label v subject v context v occurs v presents v assigns]]'+
        '[c[v credits][v activity v document v subject v context]]].'+
        'd hzil[] c[w[u[e[k hzif[]][k wa[]]]][k rqqw[k wa[] k hzig[] k hzif[] k wa[] k hzik[] k hzim[] p dg p f3 p hzih p hzij]]].')


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document);old_statements=doc['statements'];doc['statements']=[]
    size=len(doc['declarations']);doc=parse(format_graph(doc,'compact')+additions()+'s[k hzil[]].')
    doc['statements']=deepcopy(old_statements)+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqqw'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            labels,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=[] if not d['parameters'] else labels,meaning_ja=meaning)
    basis=dict(status='partial_signature_naming_and_document_author_credit',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    annotations=dict(schema_version='noema-identifiers-1',document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(),entries=[dict(
        symbol='hzif',role='designation',forms=[
            dict(text='I.[mmanuel] Kant.',language='de',role='edition_transcription'),
            dict(text='I. Kant',language='de',role='abbreviated_identifying_form'),
            dict(text='Immanuel Kant',language='de',role='editorially_expanded_identifying_form')])])
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Author signature and separate identifier forms composed')


if __name__=='__main__':main()
