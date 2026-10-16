"""Compose an addressed consultation directive with a descriptive page address."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction
from scripts.check_calendar_dateline import num

PARENT='examples/v016/kant-publication-header.noema'
PARENT_BASIS='data/publication-header-basis-v1.json'
FULL='examples/v016/kant-cross-reference.noema'
LIBRARY='examples/v016/periodical-page-address.noema'
BASIS='data/cross-reference-basis-v1.json'
ANNOTATIONS='data/cross-reference-identifiers-v1.json'
PRIMITIVES={
 'hzmp':('[a a i[h[a] f] d] c',['文章箇所','提示者','受け手を引数にする発話の記述','提示文脈'],'提示者がこの箇所で、暗黙に呼びかける受け手に対し、指定された発話を提示する。引数の人物は実際に呼びかけを受ける者として代入し、特定の人物や全人類を指定しない。発話の働きと内容は記述側に保持する。単なる他者発話の引用、受け手の行動の成立、法的義務、内容への賛同は含意しない。'),
 'hzmq':('[a a a d] c',['行為','参照する人','情報の所在','状況'],'指定した人が、情報を確認するため指定された所在の記載を参照する行為。全文の通読、内容の真偽の認定、理解の成功、物理的な頁の移動を含意しない。行為が成立することは別にdgで記す。'),
 'hzmr':('[] a',[],'参照先の刊行物に印刷された頁番号の規約。親経路はその号である。号番号、記事番号、画像やPDFの通し番号とは区別する。'),
 'hzms':('[] a',[],'カント論説の表題直後にある1783年12月516頁への参照指示の文章箇所。参照先の頁そのものではない。'),
 'hzmv':('[] d',[],'表題直後の括弧内の参照指示を提示する文脈。参照を実行する状況や掲載情報の表示文脈と区別する。'),
}
MEANINGS={
 'rqsp':'指定系列・暦の年番号・月番号で示す号において、指定規約の頁番号が対象を一意に指すという住所条件。年期間・月期間・号を存在量化で結び、同じ号の表示年と表示月、その号を親とする頁番号を共用する。日・実際の刊行日・参照の実行・頁の内容を補わない。',
 'hzmt':'受け手に、同じ誌名系列の1783年12月号の印刷頁516を参照するよう促す発話。所在地の条件と参照行為は要求される内容の内部に置く。受け手は引数であり、著者や特定の実在人物へ固定しない。',
 'hzmu':'表題直後の箇所で、著者が暗黙の受け手へhzmtの促しを提示すること。住所の現実の解決や読者の行動を評価してから提示を認める構成にはしない。',
}


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqsp[page a series a calendar a yn b mn b pn b scheme a context d] c[g year a[g month a[g issue a['+conjunction([
        'k hzir[v calendar v year v yn v context]',
        'k hzlm[v calendar v year v month v mn v context]',
        'k hzka[v issue v series v context]',
        'k hzjy[v issue v year v context]',
        'k hzjy[v issue v month v context]',
        'k rqso[v scheme v page l[a][v issue] v pn v context p hzmi]',
    ])+']]]].'
    text+='d hzmt[reader a] f[j m[b context[g page a['+conjunction([
        'k rqsp[v page k hzkg[] k hzix[] '+num(1783)+' '+num(12)+' '+num(516)+' k hzmr[] v context]',
        'g act a['+conjunction(['k dg[v act v context]','k hzmq[v act v reader v page v context]'])+']',
    ])+']]]].'
    text+='d hzmu[] c[k hzmp[k hzms[] k wa[] r[p hzmt] k hzmv[]]].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzmu[]].')
    doc['statements']=old+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqsp'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='cross_reference_under_addressed_consultation_reading',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            'S.[iehe]を参照への促しと読む。同じ刊行系列への参照という文脈的な読みを採用する。',
            '第2のS.は頁番号。516を記事番号・号番号・画像位置へ置換しない。',
            '住所と参照行為は要求内容の内部にある。参照先の内容、実際の閲読、理解、賛同や法的義務を主張しない。',
            '参照指示の提示を記述し、特定の読者を新たに同定しない。括弧は補足的な独立箇所として保持する。',
            '既存31文・全宣言・意味規約・名称表記を保存する。指示対象の実物の調査や本文全体の確認は含まない。',
        ])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/publication-header-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Cross-reference directive composed separately from its fulfillment')


if __name__=='__main__':main()
