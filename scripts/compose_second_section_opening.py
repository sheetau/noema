"""Compose a section topic and the paired-principle definition announcement."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rest_system_time import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-rest-system-time.noema';PARENT_BASIS='data/rest-system-time-basis-v1.json'
FULL='examples/v014/einstein-second-section-opening.noema';CORE='examples/v014/second-section-opening-core.noema'
BASIS='data/second-section-opening-basis-v1.json';ANNOTATIONS='data/second-section-opening-identifiers-v1.json';INDICES=(247,248)
PRIMITIVES={
 'eiskw':([('inquiry','a'),('distance','i[h[a a a a '+R+'] c]'),('context','d')], 'inquiryが、distanceの閉じた関係で与える二地点・基準系・校正した長さ単位・値の対応を用いる空間的な長さを主題とする。物体の長さは測定方法に従って定めた両端の地点の距離として扱う。光の曲がった経路長、経過時間、文字列の長さとは分ける。どの端点事象を選ぶか、物差しの配置、運動する棒の同時刻条件は各測定方法で指定し、この研究主題の指定だけから実際の測定や全方法の一致を要求しない。'),
 'eiskx':([('inquiry','a'),('assignment','i[h[a a a d] '+R+']'),('simultaneity','i[h[a a a a d] c]'),('context','d')], 'inquiryが、assignmentで出来事・系・時間単位・状況へ付与する時刻と、その差による時間間隔及びsimultaneityの時刻一致を主題とする。時刻の数値は各系の静止時計・共通参照・同期・校正に従い、付与の有効性と一意性を同時性の型の規約に保つ。読みの未付与や異なる原点を物理的な時間差の実例へ補わない。時間そのものを時計という物体や呼称の文字列と同一視せず、具体的な出来事の存在や実測をこの分類から導かない。'),
 'eisky':([('inquiry','a'),('context','d')], 'inquiryで対象とする量について、同じ物理的な対象・出来事の対応と校正した尺度を保ち、基準系とその系での測定規約に対して値や一致の判定がどう依存するかを研究の主題とする。単なる単位換算や名前の変更、主観的な好みとは分ける。全ての系対・方向・事例で必ず値が異なるとは述べず、一致する特例を許す。研究領域の指定であり、特定の変換式や結論の証明済みを意味しない。'),
 'eiskz':([], '第二節という文書区分。固定原文u0023から第三節u0042の直前u0041まで。第一部の直接の下位区分で、本文の命題や見出しの箇所とは区別する。'),
 'eisk2':([], '固定原文u0023の第二節見出しの箇所。番号・主題・区分は合成で指定する。'),
 'eisk3':([], 'u0024のRelativitätsprinzipという呼称個体。既出のPrinzip der Relativitätと同じ内容eifjを指すことを命名規約で結び、綴りだけから同一内容を推論しない。'),
 'eisk4':([], 'u0024のPrinzip der Konstanz der Lichtgeschwindigkeitという呼称個体。何をその原理と呼ぶかは同じ真空光速度の内容への対応で指定する。'),
 'eisk5':([('node','a'),('author','a'),('target','i[e]'),('definition','a'),('document','a'),('context','d')], 'authorがnodeで、targetとして同定した原理内容を、同じdocumentの後続箇所definitionで以下の仕方により定式化・定義すると読者に予告する。直後の定義への前方参照であり、単に後で語を使うこと、別内容の定義、過去の定義への振り返りとは分ける。参照先の順序は合成で指定し、この予告から定式化の完了・内容の真理・実証を導かない。'),
}
MEANINGS={
 'ein7':'二地点間距離thに結ぶ長さの主題と、その系・測定規約への依存という研究主題を同じinquiryに結ぶ。特定の棒の測定や収縮を断言しない。',
 'eioa':'出来事の時刻付与zbeと有効な同時性eihmに結ぶ時間の主題と、その系への依存という研究主題を同じinquiryに結ぶ。全系での絶対的同時性を加えない。',
 'eiob':'長さein7と時間eioaの両方の相対性を扱う一つの複合研究主題。一方だけの案内にはしない。',
 'eioc':'第一部に属する深さ2・表示番号2の第二節を、長さと時間の相対性eiobの主題へ結ぶ見出し。先行の時間命名箇所の後という本文順序を保つ。',
 'eiod':'同じ後続議論scopeで、二呼称を既出の相対性原理eifjと真空光速度原理eifyへ対応させ、同じ著者が両方を議論の根拠となる仮定として採用する。実証、必要最小性、二原理だけで全結論を導出した事実は要求しない。',
 'eioe':'後続本文の範囲wvを現在のwuより後へ固定し、eiodの両原理への依拠と、その同じ二内容を順にvk・wtで定義する予告を結ぶ。',
 'eiof':'二原理への依拠と前方の定義予告eioeを述べるメッセージ。原理内容自体の現実の真理の断言へ替えない。',
 'eiog':'導入文を同じ著者・論説へ帰属し、第二節見出しからの順序を保持する。先行節の時間規約の範囲を後続議論の範囲へ取り違えない。',
}
LIMITS=[
 'u0023の見出し全48文字・40本文文字と、u0024の一文全182文字・161本文文字を原刊895頁に照合する。§と番号2は見出し構造に、長さと時間の両主題は合成へ保持する。',
 '相対性を同じ対象の量・時刻関係の基準系への依存という研究主題として読む。見出しから全事例の不一致、収縮率、時間遅れの式、定義や証明の完成を主張しない。時刻付与と長さの具体的方法は本文の各箇所で扱う。',
 'Die folgenden Überlegungenはこの導入の後に続く論述の範囲wvと読む。現実の将来時刻、先行節だけ、検査済み部分だけへ狭めない。両原理をその範囲の推論の前提として用いるという採用をugで保持する。原理以外の定義・数学・測定規約を使わないとは補わない。',
 '相対性原理は先行するeifj、光速度一定の原理は同じ真空光伝播のeifyへ照応させる。呼称を二つとも固定し、片方だけの仮定採用や名前だけの一覧では済ませない。両内容の真理や実証を命名・採用から導かない。',
 'welche beiden Prinzipienとfolgendermaßenは、同じ二内容を直後の番号1・2の箇所vk・wtで定式化するという予告として読む。具体的な後続定式化との内容比較と全単位判断はu0025以降で進める。古い部分草案saw/sbdを同値と認定したという意味ではない。',
 '見出しの主題引用と導入の原理引用は、全物理設定・全実数を有限例で実行する要求ではない。有限検査は結合・指示・順序を調べ、原文との意味同値の自動証明や後続節の完成を認定しない。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fs=[('inquiry','a'),('context','d')]
    text+=define('ein7',fs,both(k('eiskw',v('inquiry'),'r[p th]',v('context')),k('eisky',v('inquiry'),v('context'))))
    text+=define('eioa',fs,both(k('eiskx',v('inquiry'),'r[p zbe]','r[p eihm]',v('context')),k('eisky',v('inquiry'),v('context'))))
    text+=define('eiob',fs,both(k('ein7',v('inquiry'),v('context')),k('eioa',v('inquiry'),v('context'))))
    text+=define('eioc',[],both(k('eihq',k('eisk2'),k('eiskz'),k('eisdx'),k('eirf'),'n p c b','n p c b','r[p eiob]',k('ri')),k('ue',k('eiskt'),k('eisk2'),k('ri')),op('u',op('e',k('eiskt'),k('eisk2')))))
    clauses=[]
    for designation,target in (('eisk3','eifj'),('eisk4','eify')):
        clauses.extend((k('eisch',k(designation),quote(target),v('scope'),v('context')),k('ug',k('wu'),k('rd'),quote(target),v('scope'),v('context'))))
    text+=define('eiod',[('scope','a'),('context','d')],both(*clauses))
    clauses=[k('eisci',k('wv'),k('eirf'),k('wu'),v('point')),k('eiod',k('wv'),v('point'))]
    for target,node in (('eifj','vk'),('eify','wt')):clauses.append(k('eisk5',k('wu'),k('rd'),quote(target),k(node),k('eirf'),v('point')))
    for first,last in (('wu','vk'),('vk','wt')):clauses.extend((k('ue',k(first),k(last),v('point')),op('u',op('e',k(first),k(last)))))
    text+=content('eioe',both(*clauses))
    text+='d eiof[] f[j s[k eioe[]]].\n'
    text+=define('eiog',[],both(k('eir3',k('wu'),k('rd'),k('eirf'),quote('eiof'),k('ri')),k('ue',k('eisk2'),k('wu'),k('ri')),op('u',op('e',k('eisk2'),k('wu')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eioc','eiog')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='second_section_topic_and_two_principle_definition_announcement',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/rest-system-time-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for n,form in (('eisk3','Relativitätsprinzip'),('eisk4','Prinzip der Konstanz der Lichtgeschwindigkeit')):ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
