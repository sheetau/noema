"""Describe the periodical header without conflating month and issue numbers."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction
from scripts.check_calendar_dateline import num

PARENT='examples/v016/kant-projected-classification.noema'
PARENT_BASIS='data/projected-classification-basis-v1.json'
FULL='examples/v016/kant-publication-header.noema'
LIBRARY='examples/v016/publication-number.noema'
BASIS='data/publication-header-basis-v1.json'
ANNOTATIONS='data/publication-header-identifiers-v1.json'
PRIMITIVES={
 'hzme':('[] a',[],'カント論説冒頭に表示されたBerlinische Monatsschriftの1784年12月号。脚注の案内対象である同年9月号hzkfとは別の号である。'),
 'hzmf':('[] d',[],'原刊481頁の誌名・年・号数・月・記事番号の表示を読む文脈。脚注・署名・日付行の表示文脈とは区別する。'),
 'hzmg':('[] a',[],'冒頭に表示された1784年12月の期間。本文で同じ暦hzix・年hzjfの月番号12へ結ぶ。'),
 'hzmh':('[] a',[],'冒頭で刊行系列の名称を誌名として表示する使用。実際の印刷作業を同定しない。'),
 'hzmi':('[a a j[a] b d] c',['番号付けの規約','番号を持つ項目','親参照の順序付き経路','表示番号','表示文脈'],'この番号規約で、この項目に、指定した親参照の経路の下でこの数値の番号が表示されている。号数・記事番号・頁番号などの規約は区別して渡し、異なる規約・親・年・文脈の同じ数字を流用しない。実際の発行順・既刊個数・日付・PDF画像番号は含意しない。'),
 'hzmj':('[] a',[],'この刊行系列の年内の号に付された順序番号の規約。親経路は刊行系列と年期間の順である。月番号や巻内の号数とは区別する。'),
 'hzmk':('[] a',[],'一つの号に収められた記事の表示順序番号の規約。親経路はその号であり、号数や頁番号とは区別する。'),
}
MEANINGS={
 'rqso':'同じ番号付け規約・親参照経路・表示番号・文脈で指定項目への割当が成立し、同じ条件で割り当てられる他項目がないこと。番号の値を月や物理的な位置から算出せず、別規約の同じ数字は一意性の比較に混ぜない。',
 'hzml':'冒頭の表示で、既存の名称hzkhを同じ刊行系列hzkgの誌名として用い、現在の号hzmeをその系列へ結ぶ。名称・系列・号を区別し、9月号とも区別する。',
 'hzmm':'同じ暦hzixの年番号1784が既存年期間hzjfを一意に指し、現在の号の表示年がその年である。実際の刊行日・執筆日・閲読日を述べない。',
 'hzmn':'現在の号に年内第12号の番号と12月の表示をそれぞれ結ぶ。号番号は刊行系列・1784年の経路、月番号は同じ暦・年で解釈し、両者を同じ関係で代用しない。',
 'hzmo':'現在の論説hzikが現在の号hzmeに掲載され、その号内の記事の表示番号1を一意に持つ。論説の内容の正しさや刊行時刻を主張しない。',
}


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqso[scheme a item a parents j[a] number b context d assigned h[a a j[a] b d] c] c['+conjunction([
        'c[v assigned][v scheme v item v parents v number v context]',
        'f other a[y[c[v assigned][v scheme v other v parents v number v context]][e[v other][v item]]]',
    ])+'].'
    text+='d hzml[] c['+conjunction([
        'u[e[k hzkh[]][k hzkg[]]]','u[e[k hzme[]][k hzkg[]]]','u[e[k hzme[]][k hzkf[]]]',
        'k dg[k hzmh[] k hzmf[]]','k hzih[k hzmh[] k hzkh[] k hzkg[] k hzmf[]]',
        'k hzka[k hzme[] k hzkg[] k hzmf[]]',
    ])+'].'
    text+='d hzmm[] c['+conjunction([
        'k hzir[k hzix[] k hzjf[] '+num(1784)+' k hzmf[]]',
        'f year a[y[k hzir[k hzix[] v year '+num(1784)+' k hzmf[]]][e[v year][k hzjf[]]]]',
        'k hzjy[k hzme[] k hzjf[] k hzmf[]]',
    ])+'].'
    text+='d hzmn[] c['+conjunction([
        'k hzlm[k hzix[] k hzjf[] k hzmg[] '+num(12)+' k hzmf[]]',
        'f month a[y[k hzlm[k hzix[] k hzjf[] v month '+num(12)+' k hzmf[]]][e[v month][k hzmg[]]]]',
        'k hzjy[k hzme[] k hzmg[] k hzmf[]]',
        'k rqso[k hzmj[] k hzme[] l[a][k hzkg[] k hzjf[]] '+num(12)+' k hzmf[] p hzmi]',
    ])+'].'
    text+='d hzmo[] c['+conjunction([
        'u[e[k hzik[]][k hzme[]]]','k hzjw[k hzik[] k hzme[] k hzmf[]]',
        'k rqso[k hzmk[] k hzik[] l[a][k hzme[]] '+num(1)+' k hzmf[] p hzmi]',
    ])+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+''.join('s[k '+n+'[]].' for n in ('hzml','hzmm','hzmn','hzmo')))
    doc['statements']=old+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqso'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='publication_header_under_displayed_metadata_reading',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            '冒頭四単位を誌名・表示年・年内の号番号と表示月・記事番号として読む。表示番号と実際の刊行順・個数を同一視しない。',
            '年1784と暦・誌名・系列・現在の論説は既存参照を共用し、12月号と12月期間だけを新たに指定する。原文の月の指定に日・時刻を補わない。',
            '番号規約と親経路を明示し、月番号・年内の号数・巻内の号数・記事番号・頁番号を混同しない。',
            '同頁の1783年12月516頁への参照指示は今回の四単位に含めず、引き続き記述を要する。',
            '既存27文・全宣言・意味規約・名称表記を保存する。前付の記述から本文や脚注全体の意味一致を導かない。',
        ])
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/projected-classification-identifiers-v1.json').read_text(encoding='utf-8'))
    designation=next(e for e in ann['entries'] if e['symbol']=='hzkh')
    designation['forms'].append(dict(text='Berlinische Monatsschrift',language='de',role='edition_heading'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Publication name, year, issue/month and article number composed')


if __name__=='__main__':main()
