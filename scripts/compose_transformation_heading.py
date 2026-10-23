"""Compose the directed space-time transformation topic and third heading."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_simultaneity_conclusion import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-simultaneity-conclusion.noema';PARENT_BASIS='data/simultaneity-conclusion-basis-v1.json'
FULL='examples/v014/einstein-transformation-heading.noema';CORE='examples/v014/transformation-heading-core.noema'
BASIS='data/transformation-heading-basis-v1.json';ANNOTATIONS='data/transformation-heading-identifiers-v1.json';INDEX=266
ASSIGN=[('event','a'),('tuple','a'),('frame','a'),('context','d')]
PAIR=[('first','a'),('second','a'),('frame','a'),('other','a'),('context','d')]
PRIMITIVES={
 'eismr':([('inquiry','a'),('correspondence','i[h[a a a a d] c]'),('context','d')], 'inquiryが、correspondenceの閉じた関係により同じ対象へ結ばれる第一の値表現・第二の値表現と、それぞれの表示系を保って、第一の表示から第二の表示へ移す規則、その条件と理論的な説明・導出を研究の主題とする。関係の引数は第一表現・第二表現・第一表示系・第二表示系・状況の順であり、対象同一性・量・尺度・適格な表示系は引用する関係で指定する。単なる名称変更や二表現の一覧ではなく変換規則を扱うが、この主題の提示自体から規則の発見済み・証明済み・全域性・可逆性・線形性・特定の公式の正しさを導かない。'),
 'eisms':([], 'この論説の第三節という文書区分。固定原文u0042から第四節u0109直前のu0108までを含み、第一部の直接の下位区分である。見出し箇所、番号、主題は別に結ぶ。'),
 'eismt':([], '固定原文einstein-1905:u0042の第三節見出しの箇所。区分そのものや物理的な系とは区別する。'),
}
MEANINGS={
 'eiuz':'同じ出来事の同じ系・文脈における三位置座標と時刻を、型付き四組shaの各成分へ結ぶ。共通単位ta/rbとCartesian計量eisdd、全実数割当ての一意性sd、現行eiukの有効で一意な局所時刻、実際の座標sa及び同じ時刻候補zbeとの一致を保持する。組の名前や四数値だけを物理的な割当てとしない。',
 'eiu2':'第一の系を比較の静止した基準、第二の系をそれに対して非零等速並進する系としてeiuoへ結び、同じ一つの出来事の四座標が第一組と第二組へeiuzで付与される対応をsguで構成する。両組の時刻もそれぞれの局所時計規約を保持し、異なる二出来事や第一系の時刻を第二系へ転用しない。',
 'eiu3':'静止基準側から相対的に等速並進する側への三座標と時刻の対応eiu2を、その変換規則と理論的説明を扱う一つの研究主題として指定する。空間成分又は時間だけへの縮小や、既知の特定変換式の断言にしない。',
 'eiu4':'第一部に直接属する深さ2・表示番号3の第三節を、eiu3の座標と時刻の変換理論の主題に結ぶ見出し。直前の同時性への結論zbkからの本文順序と、見出し箇所・節・親区分の違いを保持する。',
}
LIMITS=[
 '原刊897頁のu0042全155文字・136非空白文字を対象とする。§3、座標と時間の両方、静止系から相対的に等速並進する系への向き、Theorieという研究主題を保持する。後続u0043の具体設定はまだこの単位へ含めない。',
 '静止系はこの比較の基準として静止した座標格子と時計を使う第一系の役割であり、絶対静止を特権づける物理的主張ではない。第二系の全固定配置と全比較時点の等速並進を現行eiuoへ結ぶ。非零の運動を扱い、特定の正方向、軸一致、速度の上限をこの見出しへ追加しない。',
 '三位置成分と時刻を同じ出来事と各系へ結び、各系の共通参照時計・局所表示・有効で一意な時刻付与を保持する。第一系の数値時刻を第二系へコピーせず、同じ物理的出来事の異なる座標表現として扱う。',
 '四組には既存のzc5/zc6/shaを用い、共通の長さ単位taと時間単位rbで値を表す。同じ数値単位の採用は両系での長さ・同時性・時計表示の一致や、後続で述べる物差しと時計の同一性を意味しない。',
 '変換理論は対応に基づく規則とその条件・説明・導出を扱う主題として読む。見出しの時点で具体的な変換式の存在・導出・証明、任意の実数四組の実現、逆変換、線形性を要求しない。規則の完成を主題の提示から自動認定しない。',
 '第三節は第一部の直接の下位区分で、表示番号3は階層深さ2と別である。固定転記の次の同階層見出しu0109により節末をu0108と同定する。区分全体を案内することと、その後続本文の意味確認が済むことを分ける。',
 '有限検査は四組・出来事・二系・単位の対応、同じ対象の存在結合、主題引用と見出し構造を調べる。全実数の座標一意性と時刻付与を有限標本へ置き換えず、引用した全物理条件を見出しで実行しない。u0043以降と二作品全体は未完。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    event=v('event');frame=v('frame');ctx=v('context');tup=v('tuple')
    component=lambda r:k('zc6',tup,k(r))
    text+=define('eiuz',ASSIGN,both(k('zbd',event),k('va',frame),k('ti',k('ta')),k('ci',k('rb')),op('u',op('e',k('ta'),k('rb'))),k('sha',tup,'p ba'),k('eisdd',frame,k('ta'),k('rb'),ctx),k('sd',frame,ctx,k('ta'),k('rb')),k('eiuk',event,frame,k('rb'),ctx),k('sa',event,frame,ctx,k('ta'),k('rb'),*(component(r) for r in ('zc7','yn','yo','yp'))),k('sca',component('zc7'),k('zbe',event,frame,k('rb'),ctx))))
    assignment=lambda f:'i[event a tuple a]['+k('eiuz',event,tup,v(f),ctx)+']'
    text+=define('eiu2',PAIR,both(k('eiuo',frame,v('other'),ctx),k('sgu','p zbd',assignment('frame'),assignment('other'),v('first'),v('second'))))
    text+=define('eiu3',[('inquiry','a'),('context','d')],k('eismr',v('inquiry'),'r[p eiu2]',ctx))
    text+=define('eiu4',[],both(k('eihq',k('eismt'),k('eisms'),k('eisdx'),k('eirf'),'n p c b','n p d b','r[p eiu3]',k('ri')),k('ue',k('zbk'),k('eismt'),k('ri')),op('u',op('e',k('zbk'),k('eismt')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiu4',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='directed_coordinate_and_time_transformation_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/simultaneity-conclusion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
