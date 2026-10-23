"""Bind modern measurements to same-event coordinates and the equation task."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_site_time import ROOT,read
from scripts.compose_coordinate_correspondence import SYSTEM
from scripts.compose_measured_space_sentence import COORDINATES
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-clock-site-time.noema';PARENT_BASIS='data/clock-site-time-basis-v1.json'
FULL='examples/v014/einstein-event-coordinate-task.noema';CORE='examples/v014/event-coordinate-task-core.noema'
BASIS='data/event-coordinate-task-basis-v1.json';ANNOTATIONS='data/event-coordinate-task-identifiers-v1.json';INDEX=272
MEANINGS={
 'eiyu':'四成分の組がshaの有効性と役割の区別を満たし、同じ系の測定空間内の地点について三成分がそれぞれeixuの測定済み一意座標に一致する。時刻成分の局所付与はここから推論せず別に結ぶ。',
 'eiyv':'同じ四成分の三位置値を持つ測定空間内の全地点をeiyuで取り出し、指定地点がその唯一の場所であることをshlで要求する。出来事の識別子や時点記述の一意性とは分ける。',
 'eiyw':'同じ対象出来事・四座標・地点・系・状況について、場所の全候補にわたる特定eiyv、同所性、配備時計の局所時刻eiyi、系内時点との対応eiyj、第四成分とその時刻値の一致を保持する。四値を別々の出来事や場所から集めない。',
 'eiyx':'同じ出来事と四座標を指定系の一つの場所でeiywへ結ぶ存在条件。場所候補の名前だけでなく同じ測定と時刻付与を満たす。',
 'eiyy':'同じ一つの対象出来事が、静止系と移動系でそれぞれ指定された四座標を持つというsguの対応。二つの異なる出来事から一方ずつを選ばない。',
 'eiyz':'全対象出来事のいずれかに静止系のeiyxで付与される四座標の全範囲。有限の成功標本でも任意の実数四組全部でもない。',
 'eiy2':'同じ全対象出来事のいずれかに移動系のeiyxで付与される四座標の全範囲。静止系の値との一致は要求しない。',
 'eiy3':'全対象出来事が両系の四座標を値として一意に持ち、全静止系の四座標に、同じ出来事に属する移動系の四座標が値として一意に対応する内容。sgvとsgwにより別記録・同じ時空位置の別出来事を許し、逆方向の一意性は追加しない。',
 'eiy4':'同じ両系の四座標範囲で、非空の有限方程式列の全式を満たすことがeiyyの対応と過不足なく一致するというsgyの候補条件。各式の左右は実数値であり、余分な解と対応の欠落を共に拒否する。',
 'eiy5':'eiy4と同じ条件を満たす方程式系を答えとするsgzの質問。存在・発見済み・唯一性・線形性・具体的変換式を先に主張しない。',
 'eiy6':'x,y,z,tとξ,η,ζ,τをそれぞれの既存の測定・時刻規則へ結び、kが先行zcgで命名された同じ移動系であることを保持する。順序は三位置役割と第四の時刻役割で保持する。',
 'eiy7':'同じ思考設定の下での四座標対応eiy3の主張、現在その対応を表す方程式系eiy5を求める課題、両者の順序と既出の空間・時計設定への追加、八量の表記を同じ本文箇所へ結ぶ。',
 'eiza':'四座標の対応と方程式を求める課題eiy7を述べるメッセージ。解法の実行や未指定の方程式の答えに置き換えない。',
 'eizb':'u0046一文全体の対応主張と課題提示を同じ著者・論説へ帰属し、u0045の時刻設定からの本文順序を保持する。',
}
LIMITS=[
 'u0046全289文字・227本文文字を対象とする。原刊898頁ではWertsystemと続けて印字され、固定本文のWert Systemという分かち書きは同じ値の組を指すものとして読む。固定原文を変更しない。',
 'Zu jedemの対象は、その系で出来事の場所と時刻を完全に指定する有効な四座標の全範囲である。対象出来事zc4も同じ全比較範囲を保持し、成功する標本に限定しない。任意の実数四組が物理的に実現するという全域性は加えない。',
 '場所の完全な特定は、現在の三軸測定eixuを満たす全地点を比較し、shlで唯一の場所を要求するという内容として表す。前段の全空間測定eixsを受け、測れなかった地点を除いて唯一と見なさない。この一意性の条件を幾何学的に証明したと主張するわけではない。',
 '時刻は同じ出来事の同じ場所におけるeiyiの一意な局所表示と、eiyjの系内時点の値に一致する。時点の記述名の一意性や、同じ時空位置における出来事個体の一意性を要求しない。時計のない地点への新しい時刻拡張は加えない。',
 '同じ一つの出来事に二系の四座標を結ぶ。全対象出来事の両系での値の存在・一意性と、同じK側の値から同じk側の値へ対応する条件を保つ。別記録の同値を数値の一致で扱い、逆方向の一意性や両系の値の一致は追加しない。',
 'M0081のx,y,z,t、M0082のk、M0083のξ,η,ζ,τを既出の同じ系・三軸・時計規則へ接続する。tの規則eiwtを変更せず、新たな命名宣言や二系共通の瞬間を補わない。',
 '後半は今解くべき課題として方程式系を見いだすことの提示である。非空の有限方程式列を左右の実数値を返す関数の列として扱い、対応範囲内で全式の解と対応が過不足なく一致することを求める。特定の代数構文・線形性・Lorentz変換や探索アルゴリズムを先取りしない。',
 '対応の主張と課題は同じ第三節の仮定の範囲内に帰属する。引用から実測・解の存在・発見済みを導かない。有限対照検査、原文の意味判断、一般の物理的真理や同義性の証明は区別する。',
]

def definitions():
    t=v('tuple');p=v('place');f=v('frame');c=v('context');e=v('event')
    located=[(n,'a') for n in ('tuple','place','frame')]+[('context','d')]
    text=define('eiyu',located,both(k('sha',t,'p ba'),k('zcu',p,f,c),*(k('eixu',p,f,k(a),k('zc6',t,k(a)),c) for a in ('yn','yo','yp'))))
    text+=define('eiyv',located,k('shl',p,'i[other a]['+k('eiyu',t,v('other'),f,c)+']'))
    local=[('event','a')]+located
    text+=define('eiyw',local,both(k('zc4',e),k('zcz',e,f,c),k('zbd',e),k('va',f),k('ti',k('ta')),k('ci',k('rb')),k('eiyv',t,p,f,c),k('cb',e,p,f),k('eiyi',e,p,f,c),k('eiyj',e,f,c),k('sca',k('zc6',t,k('zc7')),k('zbe',e,f,k('rb'),c))))
    fields=[(n,s) for n,s in local if n!='place']
    text+=define('eiyx',fields,q('g','place','a',k('eiyw',*[v(n) for n,_ in local])))
    side=lambda frame:'i[event a tuple a]['+k('eiyx',e,t,k(frame),k('zb6'))+']'
    text+=define('eiyy',[('first','a'),('second','a')],k('sgu','p zc4',side('ra'),side('zbm'),v('first'),v('second')))
    for name,frame in (('eiyz','ra'),('eiy2','zbm')):
        text+=define(name,[('tuple','a')],q('g','event','a',both(k('zc4',e),k('eiyx',e,t,k(frame),k('zb6')))))
    text+=content('eiy3',both(k('sgv','p zc4',side('ra'),side('zbm'),'p shh'),k('sgw','p eiyz','p eiy2','p eiyy','p shh')))
    args=['p eiyz','p eiy2','p eiyy','p shh','p ba','p sca']
    text+=define('eiy4',[('equations',SYSTEM)],k('sgy',v('equations'),*args))
    text+='d eiy5[] g['+SYSTEM+']['+k('sgz',*args)+'].\n'
    notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,_,rule,_,_ in COORDINATES]
    notation += [k('eislo',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,rule in (('eism5','eiwt'),('eisnl','eiym'))]
    notation += [k('eisd4',k('zcg'),k('rd'),k('eisna'),k('zbm'),k('eirf'),v('point'))]
    text+=content('eiy6',both(*notation))
    text+=content('eiy7',both(k('uh',k('zda'),k('rd'),quote('eiy3'),k('eisms'),v('point')),k('zao',k('zc3'),k('zda'),k('eisms'),v('point')),k('zdc',k('zdb'),k('rd'),quote('eiy5'),k('eisms'),v('point')),k('ue',k('zda'),k('zdb'),v('point')),op('u',op('e',k('zda'),k('zdb'))),'t[k eiy6[]][v point]'))
    text+='d eiza[] f[j s[k eiy7[]]].\n'
    text+=define('eizb',[],both(k('eir3',k('zda'),k('rd'),k('eirf'),quote('eiza'),k('ri')),k('ue',k('zc3'),k('zda'),k('ri')),op('u',op('e',k('zc3'),k('zda')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eizb',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_event_coordinates_and_equation_task',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/clock-site-time-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
