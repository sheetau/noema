"""Connect the concluding acknowledgment and the two distinct date notices."""
from scripts.compose_local_magnetic_radius import *
from scripts import compose_intellectual_credit as credit
from scripts import compose_sustained_assistance as assistance
from noema.constructed import parse as parse_constructed
from noema.linking import relocate
from noema.specialization import specialize_definition

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-closing-acknowledgment.noema';CORE='examples/v014/closing-acknowledgment-core.noema'
BASIS='data/closing-acknowledgment-basis-v1.json';ANNOTATIONS='data/closing-acknowledgment-identifiers-v1.json'
CALENDAR_LIBRARY='examples/v016/calendar-address.noema'
CALENDAR_BASIS='data/calendar-dateline-basis-v1.json'
RECEIPT_BASIS='data/unreceived-reference-basis-v1.json'
PERIOD_BASIS='data/dated-reading-basis-v1.json'
MONTH=[('calendar','a'),('year','a'),('month','a'),('yearnumber','b'),('monthindex','b'),('context','d')]
PRIMITIVES={
 'eis5t':([('first','a'),('second','a'),('context','d')],'二人が互いを個人的な親愛・継続的な好意と関心を向け合う相手として関係を持つ。単なる面識、同席、業務上の協力又は一方だけの評価と区別する友人関係。個別の援助の実行、意見の一致、無条件の信頼は含意しない。'),
 'eis5u':([('first','a'),('second','a'),('context','d')],'二人が同じ職業上の活動領域における仕事仲間として関係を持つ。私的な交友、仕事の一時的な援助だけとは区別する同僚関係。同じ雇用契約・階級・職場の所在地や共同著者であることは要求しない。'),
 'eis5v':([('work','a'),('problem','a'),('context','d')],'この研究活動が、指定された同じ問題を考察し解明しようとする作業である。問題の解決又は結論の真理は含意しない。'),
 'eis5w':([('document','a'),('problem','a'),('context','d')],'この文書が指定問題をその本文の考察対象として扱う。単なる他文献の紹介や名前への言及だけとは区別する。考察の成功や問題の解決は含意しない。'),
 'eis5x':([('node','a'),('document','a'),('context','d')],'この箇所が同じ文書の論述を閉じる際の付言として提示される。結語という談話上の役割であり、数学的結論・最終の物理命題・印刷物の最終行と同一視しない。後置の日付や編集注記を許す。'),
 'eis5y':([('recipient','a'),('work','a'),('history','h[d] c'),('scope','h[d] c'),('occasions','h[d] c'),('context','d')],'同じ本人が同じ研究に取り組んだ一続きの過去の作業を、history内のscopeが欠かさず指し、occasionsがその作業で支援の継続を評価すべき機会を全て指すという範囲の帰属。成功した支援だけから範囲を逆算せず、支援されなかった該当機会も含む。全ての時刻で行為を要求せず、別の研究や任意に短縮した区間を同一視しない。支援行為・意図・忠実さ自体の成立は含意しない。'),
 'eis6f':([('node','a'),('document','a'),('content','i[e]'),('context','d')],'この箇所で刊行側の注記が、同じ対象文書について引用した内容を報告する。著者の主張・同意や内容の真理を自動的に要求しない。報告内容の日時・対象・出来事は引用内容の別定義による。'),
 'eis6g':([('node','a'),('document','a'),('message','i[f]'),('context','d')],'指定文書に付された同じ箇所が引用した発話構成を提示するという文献上の帰属。著者の発話であるとは指定せず、日付行や刊行側注記も扱う。引用内容は実行せず、真偽・実際の印刷者を含意しない。'),
}
# Reuse the existing calendar and receipt contracts, including their argument roles.
COPIED={
 'eis5z':(CALENDAR_BASIS,'hzir'),'eis6a':(CALENDAR_BASIS,'hzis'),
 'eis6b':(CALENDAR_BASIS,'hzit'),'eis6c':(CALENDAR_BASIS,'hziu'),
 'eis6d':(CALENDAR_BASIS,'hziv'),'eis6e':(RECEIPT_BASIS,'hzji'),
 'eis6h':(PERIOD_BASIS,'hzjz'),
}
REFERENCES={
 'eis6i':'u0276の結語としての謝辞全体の箇所。',
 'eis6j':'u0275の三関係の完全性についての総括箇所。全文判断は別途行う。',
 'eis6k':'同じ論説で扱い、同じ研究zrqworkが取り組んだ問題。問題名だけで本文を代用しない。',
 'eis6l':'u0276で同じ人物zrqpersonへ適用する名称個体。M. Bessoの綴りは識別表記に保存する。',
 'eis6m':'u0277の日付行の提示箇所。',
 'eis6n':'u0278の受理日についての刊行側の注記箇所。',
 'eis6o':'末尾の日付に用いる民用暦。西暦紀元、1月から12月の順、通常の日付ラベルを持つグレゴリオ暦として読む。現地の民用日でありUTC時刻を指定しない。',
 'eis6p':'末尾二行が共用する年期間。年番号1905は本文の条件で結ぶ。',
 'eis6q':'末尾二行が共用する月期間。第6月は本文の条件で結ぶ。',
 'eis6r':'受理注記が指す日期間。第6月の第30日は本文の条件で結ぶ。',
 'eis6s':'u0277で場所に適用する名称個体Bern。場所自体とは別の個体。',
 'eis6t':'u0277のBernが指す都市ベルンの局所参照。名称、国家、現在の座標や執筆イベントとは区別する。',
 'eis6u':'同じ論説を受け取る刊行側の受領主体。原文が個人名を記さない編集側の受け手であり、著者自身又は任意の読者ではない。査読での採択は意味しない。',
}
MEANINGS={
 'etm':'同じ受け手・寄与者・入力・研究について、同じ非空の過去の作業区間のある時点で寄与・産出・思考上の使用sewcがあり、現在の肯定的評価sewdがある。時制を評価の現在から分ける。',
 'etn':'etmの四個体から内容への関数。過去の寄与と現在の価値判断の引数を同じ順序に保つ。',
 'eto':'etnを既存sewgの四個体列へ接続した基準記述。順序と長さを保存する。',
 'etp':'同じ著者が同じBessoについて、同じ研究への少なくとも二つの異なる有益な過去の入力をetoの基準で寄与として認める。現実の成功を認識へ追加しない。',
 'etq':'etpの既知の引用基準を静的に展開した内容。未知の記述の実行や原文の自動証明ではない。',
 'etr':'同じ研究と本文の問題を結び、同じ著者とBessoの友人・同僚関係、全作業・全支援機会の範囲帰属と、既存sewxの過去の継続的な目的志向の支援を合わせる。',
 'ets':'同じ相手による過去の継続的支援etrと、同じ相手への複数の有益な着想の寄与の認識etqを結ぶ謝辞の主張内容。',
 'ett':'結語として同じ著者がetsを述べ、M. Bessoという名称をその同じ相手へ適用する提示。引用内容の真理を実行しない。',
 'etu':'u0276全体のメッセージ。','etv':'同じ著者・論説へu0276を帰属し、三関係の総括の後へ置く。',
 'etw':'同じ暦・文脈の年番号と、その年の月列の指定位置の月を結ぶ。0始まりの月位置5は第6月。特定の日を選ばない。',
 'etx':'既存rqrmを改名してそのまま再利用した年・月・日の暦アドレス。年、月位置、日位置を別の役割として保持する。',
 'ety':'同じ論説の日付行で、名称Bernを同じ都市へ適用し、場所欄と1905年第6月の日期間表示を結ぶ。6月中の特定日や執筆完了日を追加しない。',
 'etz':'u0277の日付行のメッセージ。','et2':'日付行を同じ文書へ帰属し、謝辞に続ける。発話者を著者へ固定しない。',
 'et3':'同じ暦の1905年第6月第30日の内に、同じ論説が刊行側の受け手へ届く受領があるという内容。時刻は存在量化し、採択や刊行日とはしない。',
 'et4':'刊行側の注記がet3の受領内容を報告する提示。著者の主張とは別に保持する。',
 'et5':'u0278の受理日注記のメッセージ。','et6':'同じ文書の刊行側注記へu0278を帰属し、日付行の後へ置く。',
}
LIMITS=[
 '原刊921頁の結語・日付行・受理注記を読む。u0276のich/mir/meinは同じ著者rd、M. Besso/demselbenは同じzrqperson、hier behandelten Problemeは同じ論説eirfが扱い同じ研究zrqworkが取り組んだ問題へ結ぶ。',
 'treu zur Seite standは、同じ一続きの過去の研究の、支援が問われる全ての機会に、その研究を前進させる目的に向けた実行があるという明示した継続的支援の読み。機会を成功から選別せず、原文が特定しない時刻・頻度・援助方法・物理的同席・困難な状況を追加しない。目的の達成は必要条件にしない。',
 'manche wertvolle Anregungは少なくとも二つの異なる思考上の入力と読む。単なる受信や二つの記録ではなく、過去の寄与と同じ研究での使用、現在の仕事に相対的な肯定的評価への著者の認識を保つ。入力の真理、返礼義務、金銭債務や特定の感情は追加しない。',
 '新しい社会関係・範囲帰属・論述役割は一般的な意味規約であり、特定の人物や原文の一文全体を原始関係へ埋め込まない。友人関係だけから忠実な援助を推論せず、同僚関係から共同著作を推論しない。',
 'Bern, Juni 1905.は場所と月の精度の日付行。実際の執筆場所・書き終えた日・刊行日ではない。日付をグレゴリオ暦の現地の民用年月日として読み、日付行に6月30日を補わない。',
 'Eingegangen 30. Juni 1905.は同じ論説が刊行側へ届いた日を記す注記と読む。査読採択日ではない。日付行とは同じ年・月を共有し、日・時刻と受け手はその役割で別に結ぶ。括弧は独立した刊行側注記として保持し、著者の発話にしない。',
 '旧441主張、既存定義・意味判断・証拠を保存する。有限の対照検査と通読による意味判断を分け、歴史的事実又は同義性の自動証明としない。u0239・u0265・u0275の全文判断は残る。',
]

def copied_entries():
    return {name:json.loads(read(path))['primitives'][old] for name,(path,old) in COPIED.items()}

def calendar_definition():
    d=next(d for d in parse_constructed(read(CALENDAR_LIBRARY))['declarations'] if d['name']=='rqrm')
    return relocate(d,{'rqrm':'etx'})

def num(n):return 'n p '+number_word(n)+' b'

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=''.join('r '+n+'[] a.\n' for n in REFERENCES)
    context=v('context');point=v('point');slots=credit.SLOTS
    temporal={n:k('zrr'+n) for n,t in assistance.TEMP if n not in ('recipient','work','context')}
    valid=k('sewq',*[v(n) if n in ('recipient','work','context') else temporal[n] for n,t in assistance.TEMP])
    past=quantified('g',[('past','d')],both(app(k('zrrscope'),v('past')),app(k('zrrbefore'),v('past'),context),k('sewc',*args(slots),v('past'),*[k('zrq'+n) for n,t in credit.RELATIONS])))
    text+=define('etm',slots+[('context','d')],both(valid,past,k('sewd',*args(slots),context,*[k('zrq'+n) for n,t in credit.RELATIONS])))
    text+=define('etn',[],'i['+' '.join(n+' '+t for n,t in slots)+'][b context['+k('etm',*args(slots),context)+']]','h[a a a a] e')
    text+=define('eto',[],k('sewg',k('etn')),'h[j[a]] e')
    text+=content('etp',k('sewi',k('rd'),k('zrqperson'),k('zrqwork'),quote('eto'),point,*[k('zrq'+n) for n,t in credit.JUDGING]))
    before_specialization=text;text=''
    ev=lambda n:op('t',k(n),point)
    text+=content('etr',both(k('eis5t',k('rd'),k('zrqperson'),point),k('eis5u',k('rd'),k('zrqperson'),point),k('eis5v',k('zrqwork'),k('eis6k'),point),k('eis5w',k('eirf'),k('eis6k'),point),k('eis5y',k('rd'),k('zrqwork'),k('zrrhistory'),k('zrrscope'),k('zrroccasions'),point),ev('sewx')))
    text+=content('ets',both(ev('etr'),ev('etq')))
    node=k('eis6i');paper=k('eirf');author=k('rd')
    text+=content('ett',both(k('eis5x',node,paper,point),k('uh',node,author,quote('ets'),k('zrqscope'),point),k('eira',node,point),op('u',op('e',k('eis6l'),k('zrqperson'))),k('eirb',node,k('eis6l'),k('zrqperson'),point)))
    text+='d etu[] f[j s[k ett[]]].\n'
    text+=define('etv',[],both(k('eir3',node,author,paper,quote('etu'),k('ri')),k('ue',k('eis6j'),node,k('ri'))))
    text+=define('etw',MONTH,both(k('eis5z',v('calendar'),v('year'),v('yearnumber'),context),'a['+k('eis6a',v('calendar'),v('year'),context)+']['+v('monthindex')+']['+v('month')+']'))
    dateargs=[k(n) for n in ('eis6o','eis6p','eis6q')]
    text+=content('ety',both(k('etw',*dateargs,num(1905),num(5),point),k('eira',k('eis6m'),point),op('u',op('e',k('eis6s'),k('eis6t'))),k('eirb',k('eis6m'),k('eis6s'),k('eis6t'),point),k('eis6c',k('eis6m'),paper,k('eis6t'),point),k('eis6d',k('eis6m'),paper,k('eis6q'),point)))
    text+='d etz[] f[j s[k ety[]]].\n'
    text+=define('et2',[],both(k('eis6g',k('eis6m'),paper,quote('etz'),k('ri')),k('ue',node,k('eis6m'),k('ri'))))
    text+=content('et3',both(k('etx',*dateargs,k('eis6r'),num(1905),num(5),num(29),point,'p eis5z','p eis6a','p eis6b'),quantified('g',[('received','d')],both(k('eis6e',k('eis6u'),paper,v('received'),point),k('eis6h',v('received'),k('eis6r'),point)))))
    text+=content('et4',k('eis6f',k('eis6n'),paper,quote('et3'),point))
    text+='d et5[] f[j s[k et4[]]].\n'
    text+=define('et6',[],both(k('eis6g',k('eis6n'),paper,quote('et5'),k('ri')),k('ue',k('eis6m'),k('eis6n'),k('ri'))))
    return before_specialization,text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==441
    newnames=set(MEANINGS)|set(PRIMITIVES)|set(REFERENCES)|set(COPIED)
    assert not newnames&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc['declarations'].append(calendar_definition())
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=e['parameters'],result=e['result']) for n,e in copied_entries().items()]
    pre,post=definitions();doc=parse(format_graph(doc,'compact')+pre)
    doc=specialize_definition(doc,'etp','etq',{}).document
    doc=parse(format_graph(doc,'compact')+post)
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('etv','et2','et6')]
    added=doc['declarations'][len(old['declarations']):];copied=copied_entries()
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=copied[d['name']]['arguments'] if d['name'] in copied else [n for n,t in PRIMITIVES[d['name']][0]] if d['name'] in PRIMITIVES else [],meaning_ja=copied[d['name']]['meaning_ja'] if d['name'] in copied else PRIMITIVES[d['name']][1] if d['name'] in PRIMITIVES else REFERENCES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='closing_acknowledgment_and_distinct_dates_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS,reused_calendar_and_receipt_contracts=COPIED)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[441,442,443]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    for n,label in [('eis6l','M. Besso'),('eis6s','Bern')]:ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=label,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
