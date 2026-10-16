"""Connect reading an announcement, its carrier, and their stated periods."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction,num

PARENT='examples/v016/kant-unreceived-reference.noema'
PARENT_BASIS='data/unreceived-reference-basis-v1.json'
FULL='examples/v016/kant-dated-reading.noema'
LIBRARY='examples/v016/mediated-reading.noema'
BASIS='data/dated-reading-basis-v1.json'
ANNOTATIONS='data/dated-reading-identifiers-v1.json'
PRIMITIVES={
 'hzjv':('[a a a d d] c',['読書行為','読者','読む文書','読書時点','評価文脈'],'この行為において、この読者がこの文書を指定時点に読む。文字の知覚・読解を伴う読書としての基本関係。全文の精読、完全な理解、同意、引用先文献の閲読は含意しない。'),
 'hzjw':('[a a d] c',['掲載される文書','掲載媒体の号','文脈'],'この文書がこの号の内容として掲載されている。別の号への掲載、言及だけ、外部のリンク先であることとは区別する。'),
 'hzjx':('[a a d] c',['案内文書','案内される号','文脈'],'この文書がこの号についての案内・告知である。号自体の内容の全部や、紹介された文献の全文と同一視しない。'),
 'hzjy':('[a a d] c',['号','表示される暦期間','文脈'],'その号がこの暦期間を対象とする号として表示される。日付付きの号・月号を扱い、実際の印刷日・刊行日・受領日とは区別する。'),
 'hzjz':('[d a d] c',['時点','暦期間','文脈'],'この評価文脈で、その時点がその暦期間内にある。表示する文脈と表示された日時を同一視せず、瞬間の完全な日時指定は要求しない。'),
 'hzka':('[a a d] c',['号','刊行系列','文脈'],'その号がその継続刊行系列に属する。系列全体と一つの号を同一視せず、発行間隔・編集者・媒体形式は別に記述する。'),
 'hzkb':('[] a',[],'脚注で著者が案内を読むと述べる読書行為。紹介された回答文献の読書とは区別する。'),
 'hzkc':('[] a',[],'脚注の読書媒体である、9月13日付の週報の号。刊行系列全体とは区別する。'),
 'hzkd':('[] a',[],'脚注でBüsching’schen wöchentlichen Nachrichtenと指される刊行系列。人物ビュッシング本人ではない。'),
 'hzke':('[] a',[],'脚注で週報の系列を指す名称個体。人物の編集関与と週ごとの発行の仕組みは、名称の綴りだけでは定義しない。'),
 'hzkf':('[] a',[],'脚注の案内の対象である、同じ9月のBerlinische Monatsschriftの号。案内・週報・系列とは区別する。'),
 'hzkg':('[] a',[],'脚注でBerlinische Monatsschriftと指される刊行系列。特定の号とは区別する。'),
 'hzkh':('[] a',[],'脚注でBerlinische Monatsschriftの系列を指す名称個体。綴りは識別表記の別添えへ置く。'),
 'hzki':('[] a',[],'脚注で週報の号の日付として指定される日期間。本文で同じ暦・年・9月の第13日と結ぶ。'),
 'hzkj':('[] a',[],'脚注で二つの刊行系列の名称を用いる提示行為。著者が案内を読んだ行為と同一視しない。'),
 'hzkl':('[] d',[],'脚注の案内を読む行為の時点。未受領を述べる基準時hzjmと同一の瞬間とは要求せず、同じ「今日」の内に結ぶ。'),
}
MEANINGS={
 'rqrp':'同じ読書行為の成立、同じ人による同じ文書の読書、同じ文書の同じ号への掲載を共通の文脈で結ぶ。媒体や引用先を読む対象にすり替えない。',
 'hzkk':'脚注の著者waが、13日付の週報の号に掲載された案内hzjrを、同月30日に読む。案内の対象は同じ月の別系列の号である。刊行系列と号、名称、案内、引用先の回答を区別する。読書と未受領の基準時を同じ日へ結ぶが、同一瞬間には固定しない。',
}
LIMITS=[
 '脚注冒頭の読書・掲載・号の表示期間を追加する部分草案。週刊の周期とBüschingの人物・編集関係は名称参照だけで定義せず、未記述として残す。',
 '1784年と民用暦は前の文書日付行から引き継ぐ文脈的な読み。脚注自体が年番号を明記したとは扱わない。歴史的な暦の同定と改暦等は前版から未完。',
 '「同じ月」と「この月」を日付行と共通の第9月へ結ぶ読みを採る。読書時点と未受領の基準時を同じ日に置き、時刻の一致や正確な時間差は補わない。',
 '号に表示された期間と実際の刊行日時を区別する。読書の全認知過程、記事の全内容、継続刊行の制度、敬称・代名詞・反事実と脚注全体の意味確認は未完。',
 '既存20文と全宣言・意味規約は保存する。以前の「日付未接続」という制限のうち脚注の二時点と日付行の日の接続は今回追加したが、日時全般の問題を解決済みとはしない。',
]


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqrp[act a reader a text a issue a moment d context d occurs h[a d] c reads h[a a a d d] c contains h[a a d] c] c['+conjunction([
        'c[v occurs][v act v context]','c[v reads][v act v reader v text v moment v context]',
        'c[v contains][v text v issue v context]',
    ])+'].'
    def date(day,index):
        return 'k rqrm[k hzix[] k hzjf[] k hzjg[] k '+day+'[] '+num(1784)+' '+num(8)+' '+num(index)+' k hzjl[] p hzir p hzis p hzit]'
    text+='d hzkk[] c['+conjunction([
        'k rqrp[k hzkb[] k wa[] k hzjr[] k hzkc[] k hzkl[] k hzjl[] p dg p hzjv p hzjw]',
        'k dg[k hzkj[] k hzjl[]]',
        'u[e[k hzke[]][k hzkd[]]]','u[e[k hzkh[]][k hzkg[]]]',
        'u[e[k hzkc[]][k hzkd[]]]','u[e[k hzkf[]][k hzkg[]]]',
        'k hzih[k hzkj[] k hzke[] k hzkd[] k hzjl[]]',
        'k hzih[k hzkj[] k hzkh[] k hzkg[] k hzjl[]]',
        'k hzka[k hzkc[] k hzkd[] k hzjl[]]','k hzka[k hzkf[] k hzkg[] k hzjl[]]',
        'k hzjx[k hzjr[] k hzkf[] k hzjl[]]',date('hzki',12),date('hzjh',29),
        'k hzjy[k hzkc[] k hzki[] k hzjl[]]','k hzjy[k hzkf[] k hzjg[] k hzjl[]]',
        'k hzjz[k hzkl[] k hzjh[] k hzjl[]]','k hzjz[k hzjm[] k hzjh[] k hzjl[]]',
    ])+'].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzkk[]].');doc['statements']=statements+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrp'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_dated_reading_and_distinct_periodical_issues',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/unreceived-reference-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    for symbol,form in [('hzke','Büsching’schen wöchentlichen Nachrichten'),('hzkh','Berlinischen Monatsschrift')]:
        ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='inflected_edition_transcription')]))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Dated reading and distinct publication references composed')


if __name__=='__main__':main()
