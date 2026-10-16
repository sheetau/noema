"""Distinguish a cited answer from receiving that answer by a reference time."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-calendar-dateline.noema'
PARENT_BASIS='data/calendar-dateline-basis-v1.json'
FULL='examples/v016/kant-unreceived-reference.noema'
LIBRARY='examples/v016/unreceived-reference.noema'
BASIS='data/unreceived-reference-basis-v1.json'
ANNOTATIONS='data/unreceived-reference-identifiers-v1.json'
PRIMITIVES={
 'hzji':('[a a d d] c',['受け手','対象文献','受領時点','評価文脈'],'その時点で、対象文献が受け手の手元へ届く受領が成立する。文献の利用可能な写しの取得も含み、単に宛てられたこと、紹介を読んだこと、内容の理解・賛同とは区別する。継続的な所持状態ではない。'),
 'hzjj':('[a a a d] c',['紹介行為','対象文献','問いの箇所','文脈'],'同じ紹介行為が、その対象文献を、この箇所が表す問いの内容への回答として言及する。問いの箇所に物理的に返信したことや、回答の正しさ・十分性を含意しない。'),
 'hzjk':('[a a d] c',['紹介行為','紹介を含む文書','文脈'],'この文書内にその紹介行為の記載がある。対象文献の全文がそこに収録されること、受け手への到達や読解は含意しない。'),
 'hzjl':('[] d',[],'カント末尾の著者脚注を解釈する文脈。署名・日付行の表示文脈とは区別する。'),
 'hzjm':('[] d',[],'脚注で著者が「まだ手元に届いていない」と述べる基準時点。暦の日時への接続は別途必要で、既存の日付行の表示文脈と同一視しない。'),
 'hzjn':('[] a',[],'脚注で紹介されるメンデルスゾーンの回答文献の局所参照。回答内容そのものの定義ではない。続くsieをこの回答へ受ける読みを採用する。'),
 'hzjo':('[] a',[],'脚注でMendelssohnと名指される人物の局所参照。綴りの一致から他の人物参照と統合しない。'),
 'hzjp':('[] a',[],'脚注でその人物を指すMendelssohnという名称個体。人物とは区別し、綴りを別添えに保持する。'),
 'hzjq':('[] a',[],'脚注で述べられる、他の回答への紹介行為の局所参照。著者自身によるその回答の閲読とは区別する。'),
 'hzjr':('[] a',[],'脚注で著者が読んだと述べる雑誌の案内・告知の局所参照。worinをこの案内へ受ける読みを採る。案内を掲載する週報や案内の対象雑誌とは区別する。'),
 'hzjs':('[] a',[],'脚注の受領の有無を評価する履歴枠。対象文献の受領が問題になる期間から基準時までを欠かさない実際の経過を指定するという意味契約。反事実や任意に切り詰めた過去へ置き換えない。'),
}
MEANINGS={
 'rqrn':'指定履歴がtaの厳密な全順序を持ち、基準点がその履歴に属し、履歴内の基準点以前の全点で指定事象が成立しない。基準点も含む。将来の発生、期待、実現可能性、履歴の最初の点の存在を主張しない。履歴の現実への適用と完全性は入力の意味契約である。',
 'rqro':'同じ受け手・文献・履歴枠・評価文脈を固定し、基準時までの受領がないことをrqrnで記述する。現在の非所持ではなく過去の受領の不在を要求する。',
 'hzjt':'同じ案内中の紹介が成立し、名称Mendelssohnを同じ人物へ適用し、その人物を同じ回答の著者として表示し、その回答を既存表題の問いの内容への回答として言及する。著者本人の閲読や回答の正しさは補わない。',
 'hzju':'脚注で紹介された同じ回答文献が、この論説の著者waに基準時まで届いていないという読み。後の受領や反事実の結論は追加しない。',
}
LIMITS=[
 '著者脚注の二箇所だけの部分草案。先行する週報・雑誌・読書の日付、反事実条件、試み・偶然・思想の一致は未記述。',
 'worinは案内・告知、sieはメンデルスゾーンの回答へ受ける読みを採用する。雑誌を介する指示を含む別の読みを排除できたとはしない。',
 'Mendelssohnの識別表記は原文の姓に限定する。名、生涯、称号の社会的効果は補わない。Herrnの敬称の働きは未記述。',
 '「まだ」の基準時以前の受領不在を表す。到来への期待等の語用論、取得媒体、歴史的な事実確認は未完。',
 '時間履歴の完全性や現実性を順序検査だけから導かない。未知の受領記録を偽に補う使い方はしない。',
 '既存本文の全宣言と18文を保存する。単位全体の意味確認、任意の内容への表現率、翻訳機の完成は主張しない。',
]


def additions():
    text=''.join('r '+name+sig+'.' for name,(sig,_,_) in PRIMITIVES.items())
    text+='d rqrn[history h[d] c before h[d d] c anchor d occurred h[d] c] c['+conjunction([
        'k ta[v history v before]','c[v history][v anchor]',
        'f moment d[y[w[c[v history][v moment]][x[c[v before][v moment v anchor]][e[v moment][v anchor]]]][u[c[v occurred][v moment]]]]',
    ])+'].'
    text+=('d rqro[person a item a frame a anchor d context d history h[a d d] c before h[d d d] c received h[a a d d] c] c['
        'k rqrn[i[moment d][c[v history][v frame v context v moment]] '
        'i[left d right d][c[v before][v left v right v context]] v anchor '
        'i[moment d][c[v received][v person v item v moment v context]]]].')
    text+='d hzjt[] c['+conjunction([
        'k dg[k hzjq[] k hzjl[]]','u[e[k hzjp[]][k hzjo[]]]',
        'k hzjk[k hzjq[] k hzjr[] k hzjl[]]',
        'k hzih[k hzjq[] k hzjp[] k hzjo[] k hzjl[]]',
        'k hzij[k hzjq[] k hzjn[] k hzjo[] k hzjl[]]',
        'k hzjj[k hzjq[] k hzjn[] k hzia[] k hzjl[]]',
    ])+'].'
    text+='d hzju[] c[k rqro[k wa[] k hzjn[] k hzjs[] k hzjm[] k hzjl[] p h7q p ic p hzji]].'
    return text


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(cat.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzjt[]].s[k hzju[]].')
    doc['statements']=statements+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrn','rqro'])
    primitives={}
    for d in doc['declarations'][size:]:
        if d['kind']=='primitive':
            _,args,meaning=PRIMITIVES[d['name']]
            primitives[d['name']]=dict(parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning)
    basis=dict(status='partial_cited_answer_and_nonreceipt_before_anchor',document=FULL,library=LIBRARY,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/calendar-dateline-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    annotations['entries'].append(dict(symbol='hzjp',role='designation',forms=[dict(text='Mendelssohn',language='de',role='edition_transcription')]))
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Cited answer and nonreceipt composed')


if __name__=='__main__':main()
