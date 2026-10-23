"""Compose noninvariance of reception assignment and empirical knowledge of it."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_reception_time_alternative import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-reception-time-alternative.noema';PARENT_BASIS='data/reception-time-alternative-basis-v1.json'
FULL='examples/v014/einstein-reception-position-dependence.noema';CORE='examples/v014/reception-position-dependence-core.noema'
BASIS='data/reception-position-dependence-basis-v1.json';ANNOTATIONS='data/reception-position-dependence-identifiers-v1.json';INDEX=232
CASE=[(n,'a') for n in ('case','scheme','task','event','document')]+[('reference','d')]
PAIR=[(n,'a') for n in ('left','right','scheme','task','event','document')]+[('reference','d')]
PRIMITIVES={
 'eishh':(CASE,'caseが同じschemeをtaskの同じeventへ適用した配置の場合として、referenceの議論で比較対象となる。観測者・時計・指針・所在する原点・系・尺度・到達記録・評価状況を保持し、候補の適用が実際にその方式を満たすかは別に確認する。別の方式で得た値や単なる名前だけの事例を混ぜず、既に位置依存があるかどうかは先取りしない。'),
 'eishi':([('case','a'),('slot','b'),('reference','d')],'同じcaseの指定欄の個体を取り出す。整数slotの1は到達記録、2は観測者、3は時計、4は指針表示部分、5は観測者と時計が所在する原点の物理的な場所、6はその場合の座標系、7は時間単位である。原点は単なる座標値0ではなく配置する場所を指す。欠落・範囲外・未知欄を既定値で補わない。'),
 'eishj':([('case','a'),('reference','d')],'caseの設定と受信時の対応を評価する状況を取り出す。比較の基準referenceとは区別し、同じ配置の全関係に同じ状況を渡す。状況を取り出すだけでその場合の適用成功を認定しない。'),
 'eishk':(PAIR,'leftとrightが同じscheme・task・eventについて観測者の空間的位置への依存を調べるための比較可能な二配置である。対象出来事の生起と物理的準備、光学的証拠の追跡、時間単位の意味、時計の校正・進み方・基準の合わせ方を保ち、任意の時計の初期ずれや別の対象だけで読みの差を作らない。時計を携えた観測者の位置とそれに伴う光の到達を変え得る比較である。各原点の場所は同じ物理的空間への対応で比較し、座標系を各観測者の原点へ取り直しても対象を交換しない。場所の相違と読取り値の差は合成側で別に要求する。二配置を現実に同時に実施したとは要求しない。'),
 'eishl':([('scheme','a'),('property','i[e]'),('document','a'),('context','d')],'同じschemeを採るとpropertyで指定する性質を伴うという方式に内在する帰結の関係。無関係な計器故障・偶然の共起・著者の感想ではなく、その割当の仕方から生じる特徴として提示する。propertyの内容をこの一関係へ隠さず、同じ内容の成立を合成で別に確認する。'),
 'eishm':([('property','i[e]'),('task','a'),('document','a'),('context','d')],'propertyの性質が同じtaskの時間的規定を使ううえで不都合な点となる。対象出来事の時間関係を観測者の都合だけに左右されず扱いたいという課題に対する障害であり、単なる好み・倫理的非難・方式の全面的無意味さではない。不都合の所在を引用内容で固定し、観測者に依存しない完成した解法をここで追加しない。'),
 'eishn':([('author','a'),('property','i[e]'),('document','a'),('context','d')],'authorが同じdocumentの議論でpropertyを経験に基づいて知っているという知識の帰属。観察や実際の光・時計の経験を根拠とする認識として述べ、純粋な定義による演繹だけ、未確認の予想、個人的な気分とは区別する。特定の実験名・実験者・全人類の承認は補わない。内容自体は別に主張し、処理系が実験したことをこの帰属から導かない。'),
 'eisho':([('node','a'),('author','a'),('target','i[e]'),('knowledge','i[e]'),('document','a'),('context','d')],'authorがnodeでtargetを述べる際、knowledgeを「われわれが経験から知るように」という挿入として提示する。知識の根拠付けが同じtargetへ向くことを保ち、別の現象の知識や、挿入を削除した単なる主張へ替えない。挿入の提示と知識内容の成立を分けて保持する。'),
 'eishp':([], '固定原文einstein-1905:u0012[310,488)の第二文の箇所。受信時の割当が観測者位置に独立でないという欠点と、経験から知るという挿入を述べる。'),
}
RESULTS={'eishi':'a','eishj':'d'}
MEANINGS={
 'eikk':'同じ方式の一配置の七つの欄と評価状況を、前文の方式の規則eikd・対応記録へ結ぶ。記録中の原出来事を同じeventに固定し、前文と別方式の値を持ち込まない。',
 'eikl':'同じ方式・課題・原出来事の比較可能な二配置が、それぞれ前文の受信割当を満たし、観測者と時計の物理的な場所が異なり、同じ時間単位で割り当てる値が実数値として異なる。時計の初期ずれや座標ラベルだけの差は比較条件で除く。',
 'eikm':'同じ方式が位置から独立でないことを示す、同じ対象出来事とeiklの二配置が存在する。全ての二位置で必ず違うことや、未測定・未知であることとは区別する。',
 'eikn':'前文の同じ方式eisg7と課題eisheについてeikmの非独立性を述べる内容。観測者の心理的意見への依存ではなく、時計を伴う空間的位置への依存として読む。',
 'eiko':'著者が同じeiknを経験から知るという知識の内容。知識の対象を別の命題へ交換しない。',
 'eikp':'eiknの非独立性、その性質を同じ方式が伴うこと、同じ時間的評価の課題で不都合であること、経験による知識eikoを結ぶ第二文の全内容。',
 'eikq':'第二文の欠点と知識eikpを主張するメッセージ。先行する採用可能性の撤回や後続の解法の完成を追加しない。',
 'eikr':'同じ著者・論説への帰属、前文の可能な選択とのaberの対比、同じ非独立性を経験から知る挿入、本文順序を結ぶ。',
}
LIMITS=[
 'Eine solche Zuordnungを前文の同じscheme・taskとeikdの規則へ結ぶ。原出来事、受信、指針表示を分ける前文の解釈を保持し、受信の読みを伝播補正済みの元の出来事の時刻へ替えない。',
 'Standpunktはこの光信号と時計の文脈で観測者の空間的位置として読む。二配置の原点が同じ数値0であることを、同じ物理的場所であることと混同しない。系を原点に合わせて指定し直す場合も同じ対象と尺度を保つ。',
 'nicht unabhängigは、比較可能な二配置で同じ出来事への割当値が異なるという反例の存在として読む。任意の二位置で必ず値が違うこと、情報不足、未知入力の不成立への変換ではない。時計の校正・進み方・基準を合わせ、初期ずれだけで差を作らない。',
 '比較可能性と経験からの知識は意味規約付きの入力である。二配置を現実に同時実施したとは要求せず、有限の数値例から全配置の物理的真理や知識の正当化を自動証明しない。',
 '方式に伴う性質と課題に対する不都合を分けて結び、aberは前文の選択可能性との対比、wie以下は同じ非独立性についての経験的知識の挿入として保持する。知識の声は著者の論述上のWirと読む。',
 '第二文151非空白文字を対象とする。第三文71文字のより実用的な取り決めへの導入と、三文全体の通読判断は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def field(case,slot):return k('eishi',case,'n p '+number_word(slot)+' b',v('reference'))
def situation(case):return k('eishj',case,v('reference'))
def reading(case):return k('eisgz',field(case,1),field(case,3),field(case,7),situation(case))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+RESULTS.get(n,'a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    c=v('case');ctx=situation(c)
    text+=define('eikk',CASE,both(k('eishh',*args(CASE)),k('eisg3',v('scheme'),v('task'),*[field(c,i) for i in (2,3,4,5,6,7)],v('document'),'r[p eikd]',ctx),k('eikd',v('task'),*[field(c,i) for i in (1,2,3,4,5,6,7)],ctx),op('e',k('eisgx',field(c,1),'n p b b',ctx),v('event'))))
    left=v('left');right=v('right');common=[v(n) for n in ('scheme','task','event','document','reference')]
    text+=define('eikl',PAIR,both(k('eikk',left,*common),k('eikk',right,*common),k('eishk',*args(PAIR)),op('u',op('e',field(left,5),field(right,5))),op('e',field(left,7),field(right,7)),op('u',k('sca',reading(left),reading(right)))))
    body=k('eikl',v('left'),v('right'),v('scheme'),v('task'),v('event'),v('document'),v('reference'))
    for name in ('right','left','event'):body=q('g',name,'a',body)
    text+=define('eikm',[(n,'a') for n in ('scheme','task','document')]+[('reference','d')],body)
    text+=content('eikn',k('eikm',k('eisg7'),k('eishe'),k('eirf'),v('point')))
    text+=content('eiko',k('eishn',k('rd'),quote('eikn'),k('eirf'),v('point')))
    text+=content('eikp',both('t[k eikn[]][v point]',k('eishl',k('eisg7'),quote('eikn'),k('eirf'),v('point')),k('eishm',quote('eikn'),k('eishe'),k('eirf'),v('point')),'t[k eiko[]][v point]'))
    text+='d eikq[] f[j s[k eikp[]]].\n'
    text+=define('eikr',[],both(k('eir3',k('eishp'),k('rd'),k('eirf'),quote('eikq'),k('ri')),k('zbc',k('eishp'),k('rd'),quote('eikh'),quote('eikp'),k('eishe'),k('ri')),k('eisho',k('eishp'),k('rd'),quote('eikn'),quote('eiko'),k('eirf'),k('ri')),k('ue',k('eishg'),k('eishp'),k('ri')),op('u',op('e',k('eishg'),k('eishp')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eikr',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='reception_assignment_position_noninvariance_and_empirical_knowledge',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/reception-time-alternative-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
