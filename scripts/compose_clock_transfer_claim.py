"""Connect the complete clock-transfer consequence without narrowing its antecedent."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_transfer_records import ROOT,read,COMMON,CONSTANTS,stamp,sub,mul,eq
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-clock-transfer-records.noema';PARENT_BASIS='data/clock-transfer-records-basis-v1.json'
FULL='examples/v014/einstein-clock-transfer-claim.noema';CORE='examples/v014/clock-transfer-claim-core.noema'
BASIS='data/clock-transfer-claim-basis-v1.json';ANNOTATIONS='data/clock-transfer-claim-identifiers-v1.json';INDICES=(343,344)
PRIMITIVES={
 'eisoi':([('node','a'),('author','a'),('claim','i[e]'),('focus','i[e]'),('discussion','j[a]'),('context','d')],'同じ主張と提示文脈の中で、指定された先行の議論に関して、焦点の内容を通常の予期から外れる特異な点として特に注意を向けて提示するという帰属。先行議論の文章箇所の列を明示する。客観的な発生頻度・確率、主張の確信度や必然性の増加、引用内容の真理を含意しない。構成版のh224rと同じ一般的な提示規約を、この本文の引用型i[e]へ適用する。時計や特定文に専用の概念ではない。'),
 'eisoj':([], '固定原文einstein-1905:u0126第一文、Hieraus ergibt sich folgende eigentümliche Konsequenz.の提示箇所。次の条件付き移送結果を予告する。'),
 'eisok':([], '固定原文einstein-1905:u0126のM0229/M0230で、AからBへ移送する所要時間を指すtの識別表記。同じ時計の移送経過を秒へ換算する規則ejkiへ結び、以前の座標時刻tと区別する。'),
}
MEANINGS={
 'ejki':'同じ移送時計zieと移送状況zi5について、出発と到着の現在K記録の正の時間差を、既存svpの共通の正の尺度で秒へ換算した値。tという所要時間の規則であり、出発・到着の絶対時刻や時計の指示経過を代用しない。',
 'ejkj':'同じ二時計・A/B・三出来事・三記録・四指示・二状況のejkfによる、初期同期と直線移送の設定内容。平方根の進み率や到着時の遅れの成否で設定を狭めない。',
 'ejkk':'同じBでの同じ到着出来事に属する両時計の現在の局所指示が有効で等しくないという内容。nicht mehr synchronを、全初期区間で同期した二時計の到着直後の同所比較として読む。',
 'ejkl':'同じ到着時の二つの現在表示について、B時計に対する移送時計の正の遅れ、同じK所要時間と指示差の共通秒換算、二次近似と固定所要時間の四次以上の留保swwを結ぶ。前段の厳密な遅れ率から残差を構成し、近似値を厳密値に等置しない。',
 'ejkm':'初期同期と直線移送の設定ejkjなら、同じ到着時の非同期ejkkと留保付きの遅れejklをともに得るという原文第二文の条件付き内容。追加の加速応答の区間法則ejknを前件へ挿入しない。',
 'ejkn':'同じ移送の全期間の指示法則と実際の端点差ejkh、および共通の秒換算を合わせた、厳密な遅れと近似を構成するための追加解釈。発進停止で追加の指示変化がないという理想化を含む。',
 'ejko':'ejknを十分条件として同じ到着時の遅れejklへ接続するzflの解釈注記。著者の発話メッセージの外側に置き、原文が加速応答を証明したことや追加前提を明記したことにしない。',
 'ejkp':'前の単位秒の厳密な遅れと留保付き近似ejjvから、次に述べる同じ条件付き移送結果ejkmが得られるという著者の帰結提示。eigentümlicheを先の二表示に関する特異性の評価として同じ結果へ帰属する。',
 'ejkq':'同じ設定ejkjの下で到着時に非同期となるejkkという条件付きの対照第一項。否定だけを仮定範囲の外へ出さない。',
 'ejkr':'同じ設定ejkjの下で、初めからBにある時計に対して移送時計が留保付きの量だけ遅れるejklという条件付きの対照第二項。',
 'ejks':'著者が移送条件からの結果ejkmを述べ、nicht mehr synchronとsondern以下の遅れを同じ前件の二項ejkq/ejkrとして対照する。所要時間tの記号を同じ時計・状況の規則ejkiへ結ぶ。',
 'ejkt':'u0126第一文の帰結予告と特異性の評価ejkpを述べるメッセージ。結果の真理をここで実行評価しない。',
 'ejku':'第一文を同じ著者・論説に帰属し、前の一秒当たりの近似表示zinに続ける。',
 'ejkv':'u0126第二文の条件・比較・近似・所要時間の説明ejksを述べるメッセージ。',
 'ejkw':'第二文を同じ著者・論説に帰属し、第一文の予告に続ける。補足の区間法則ejkoはメッセージの外に併記する。',
}
LIMITS=[
 'u0126の二文全体、424非空白本文文字と14数式要素を原刊904頁へ照合する。導入のHieraus/folgende/eigentümliche、Kでの初期同期、AからBへの同じ時計の直線移送、到着時の非同期とB時計に対する遅れ、秒・四次以上の留保・所要時間tを保持する。',
 'ejkfの現在表示、全初期期間の同期、三次元の全直線経路、Bへの全期間の残留、同じ到着出来事とBでの比較を引き継ぐ。初期同期は共通の指示原点を許し、初期区間は出発で終わる。数値の一致だけで同じ出来事・時計・場所を認定しない。',
 'nach Ankunft/nicht mehr synchronは到着直後の同所の指示が一致しないという読み。全初期期間の同期からの変化を保持するが、以後の未指定の運転・再調整を含む無限の未来まで同じ差が続くことは補わない。B時計との差は移送時計が小さい方向であり、遠隔信号の受信遅延とはしない。',
 'M0229のtはKでの正の所要時間を秒で表した数値。座標時刻そのものではなく出発と到着の差であり、M0230で同じ量を説明する。到着指示差と同じ正の尺度で換算する。tという綴りだけで以前の時刻規則と同一視しない。',
 '原文は留保付きの二次表示を述べる。残差を同じ前段の厳密率1−√(1−(v/V)²)に基づくものとして構成し、固定した所要時間TでT*(1−√(1−u²)−u²/2)=O(u⁴)と読む。全速度での実用精度や距離固定でTも速度に依存する族の一様性を主張しない。具体的な残差係数の上下限は加えない。',
 '全期間の率fと1、発進停止の追加指示変化がないというejknは、swwの厳密な補間と近似を用いるための明示した解釈注記ejkoに置く。原文の前件ejkjをこれで狭めず、著者の条件付き帰結ejkmを保持する。著者の主張の記述は物理的な一般導出の完了を条件としない。',
 'Hierausの参照は前の同じ原点時計のejjv、folgendeの内容は後続する同じejkm。eigentümlicheは通常の予期から外れる特有の帰結としての著者の評価と読む。数値的な稀少性、論理的矛盾、全読者の心理的驚き、単なる注目価値とは同一視しない。',
 '特異性の提示規約はKantで使ったh224rの一般的な内容・焦点・先行議論の帰属と同じ意味を、この本文の引用型で適用する。新しい実世界の時計法則を原始記号へ隠さず、物理条件は既存定義の合成を保つ。',
 '有限検査、原文の通読判断、一般の数学的・物理的真理の証明を区別する。u0127の折れ線と帰還、u0128の曲線と地球上の時計は後続である。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    point=v('point');ev=lambda n:op('t',k(n),point);constants=[k(CONSTANTS[n]) for n,_ in COMMON]
    T=sub(stamp(k('zix')),stamp(k('ziv')));scale=v('scale');seconds=mul(scale,T)
    text+=define('ejki',[('clock','a'),('value',R),('context','d')],both(op('e',v('clock'),k('zie')),op('e',v('context'),k('zi5')),k('sbg',T),k('ba',v('value')),q('g','scale',R,both(k('svp',scale,v('context')),eq(v('value'),seconds)))))
    text+=content('ejkj',k('ejkf',*constants))
    current=both(k('ejj7',k('zie'),k('ziu'),k('zix'),k('zir'),k('zi2'),k('zi5')),k('ejj7',k('zip'),k('ziu'),k('zix'),k('zir'),k('zi3'),k('zi5')))
    text+=content('ejkk',both(current,k('ba',k('zi2')),k('ba',k('zi3')),op('u',eq(k('zi2'),k('zi3')))))
    text+=content('ejkl',both(current,ev('sww')))
    text+=content('ejkm',op('y',ev('ejkj'),both(ev('ejkk'),ev('ejkl'))))
    text+=content('ejkn',both(k('ejkh',*constants),q('g','scale',R,k('svp',scale,k('zi5')))))
    text+=define('ejko',[],k('zfl',k('zja'),k('rd'),quote('ejkn'),quote('ejkl'),k('eisn5'),k('ri')))
    text+=content('ejkp',both(k('zc',k('eisoj'),k('rd'),quote('ejjv'),quote('ejkm'),k('eisn5'),point),k('eisoi',k('eisoj'),k('rd'),quote('ejkm'),quote('ejkm'),'l[a][k zim[] k zin[]]',point)))
    text+=content('ejkq',op('y',ev('ejkj'),ev('ejkk')))
    text+=content('ejkr',op('y',ev('ejkj'),ev('ejkl')))
    text+=content('ejks',both(k('uh',k('zi7'),k('rd'),quote('ejkm'),k('eisn5'),point),k('zbc',k('zi7'),k('rd'),quote('ejkq'),quote('ejkr'),k('eisn5'),point),k('eislo',k('eisok'),'r[p ejki]',k('eirf'),point)))
    for name,body in (('ejkt','ejkp'),('ejkv','ejks')):text+='d '+name+'[] f[j s[k '+body+'[]]].\n'
    for name,message,node,previous in (('ejku','ejkt','eisoj','zin'),('ejkw','ejkv','zi7','eisoj')):
        rows=[k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if name=='ejkw':rows.insert(0,k('ejko'))
        text+=define(name,[],both(*rows))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejku','ejkw')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='complete_current_clock_transfer_consequence_and_qualified_lag',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/clock-transfer-records-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisok',role='designation',forms=[dict(text='t',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
