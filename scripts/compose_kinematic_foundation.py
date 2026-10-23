"""Compose the physical referents and kinematic foundation of electrodynamics."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rigid_body_kinematics import ROOT,read
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-rigid-body-kinematics.noema';PARENT_BASIS='data/rigid-body-kinematics-basis-v1.json'
FULL='examples/v014/einstein-kinematic-foundation.noema';CORE='examples/v014/kinematic-foundation-core.noema'
BASIS='data/kinematic-foundation-basis-v1.json';ANNOTATIONS='data/kinematic-foundation-identifiers-v1.json';INDEX=217
CLASS='i[h[a d] c]';RIGID='i[h['+' '.join(t for _,t in FIELDS)+'] c]'
PRIMITIVES={
 'eisde':([('body','a'),('frame','a'),('reference','d')],'bodyをframeの位置指定の物理的な参照物体として用いるという役割。物体上の基準点・尺度と、指定した原点・方向によって、出来事や物体の位置を同じ座標へ対応させる。剛性は別条件で要求する。抽象的な座標系そのものと物体を同一視せず、棒だけで三次元の全軸を決めるとも要求しない。補助的な方向・軸の規約を許す。実験装置の現存や全座標系での剛性は含意しない。'),
 'eisdf':([('clock','a'),('reference','d')],'clockの再現可能な反復過程・進行を、指定した時間尺度で経過と順序の指示へ対応させる校正規約。理想時計として同じ尺度の等しい経過に対応する読みの増分を定め、原点と単位を保持する。機械式など特定の構造や無限の実機精度は要求しない。遠隔時計との同期、全系に共通の絶対時刻、現に読まれた値や全地点への設置は別条件である。'),
 'eisdg':([('claim','a'),('first',CLASS),('second',CLASS),('third',CLASS),('reference','d')],'claimの物理的な指示内容が、閉じたfirst・second・thirdで指定した三種の役割を持つ対象の間の位置・時刻・数量の関係によって解釈されるという意味対応。これらの対象を備えた物理的設定における指示・測定の規約が主張の量と適用条件を定める。個々の式が三種類の名詞を全て明記することや、毎回三者の実在を断言することは要求しない。部分式、特別な場合、論理的帰結にも同じ解釈規約を継承する。単に三つの語を含むこと、主張の真理や測定済みの標本とは区別する。引数の対象分類と関係の意味を保持し、未知の指示規約を適合と認定しない。'),
 'eisdh':([('inquiry','a'),('body_kind',RIGID),('reference','d')],'inquiryがbody_kindの物体の位置・時刻・相対配置とそれらの変化を、運動を生じさせる力や原因の法則に先立って記述する運動学の研究領域である。閉じた型の全物質点・全区間・系・尺度の規約を保持する。単なる静止の研究や力学的原因の理論と同一視しない。全ての物理的運動の実現可能性、特定の時空変換則をこの分類から導かない。'),
 'eisdi':([('theory','a'),('inquiry','a'),('reference','d')],'theoryの量・適用条件・主張を意味ある形で定めるため、inquiryの基本的な関係と記述規約を基礎として用いるという依存。単に同じ主題への言及、時間的な先行、好み、両者の真理の一致とは異なる。上位理論が既存の細部の規約を修正・精密化することを許し、基礎の全ての古い法則をそのまま採用するとは要求しない。基礎だけで理論全体を導ける十分性でもない。'),
 'eisdj':([('theory','a'),('document','a'),('project','i[e]'),('reference','d')],'theoryが同じdocumentでこれから展開される、projectの理論構成の到達先として意図された同じ体系であるという指示。先行する構成課題とその見解を継承し、条件を満たす無関係な別理論への交換を許さない。理論個体は予定された体系として指示でき、完成済み・実証済みであることやprojectの真理を引用から要求しない。'),
 'eisdk':([('document','a'),('grounds','i[e]'),('conclusion','i[e]'),('reference','d')],'同じdocumentの説明で、groundsに述べる事情がconclusionに述べる事柄の成り立つ理由として提示される。閉じた両内容の対象・範囲と向きを保ち、単なる並置や時系列とは区別する。理由の唯一性、論理的同値、計算器による導出完了は要求しない。両内容の成立や発話の力は別に合成し、この関係だけから引用を実行しない。'),
 'eisdl':([], '固定原文einstein-1905:u0005[0,260)の第一文。これから展開する理論の運動学的基礎、他のあらゆる電気力学との比較、各理論の主張の物理的指示関係による理由を述べる箇所。'),
}
MEANINGS={
 'eigz':'同じ物体が同じ評価系の位置指定に用いられる参照物体であり、同じ文脈の全履歴についてeigyの剛性を満たす。座標系という括弧説明を物理的な参照の役割へ結び、物体と抽象座標系を同一視しない。',
 'eig2':'既存caの時間経過を指示する時計に、反復過程と時間尺度の校正eisdfを結ぶ。遠隔同期や実測値を時計の存在条件へ混ぜない。',
 'eig3':'同じ過程が、ある空間範囲で既存の電荷輸送・電気側と磁気側の作用によって同定される電磁過程である。光だけへ狭めず、全三作用の同時発生も要求しない。',
 'eig4':'同じ理論が既存eie5の電気力学の研究対象を記述する体系である。比較の範囲を動く物体の場合だけへ狭めない。',
 'eig5':'同じ理論の全主張・全論理的帰結が、剛体の座標基準・時計・電磁過程という同じ三分類の物理的指示関係を扱う。検査済みの有限一覧を全主張としない。',
 'eig6':'同じ理論が、eigyの剛体の位置・時刻・配置の変化を記述する運動学を基礎に用いる。基礎の研究対象と依存先を同じ証人へ結ぶ。',
 'eig7':'この論説でこれから展開する同じeigjの構成課題の到達先であり、電気力学の理論である。予定された理論を完成済みや任意の他理論に替えない。',
 'eiha':'文脈上の全電気力学の各理論についてeig5を要求する、理由節の内容。量化範囲の中から都合のよい理論だけを選ばない。',
 'eihb':'これからの同じ理論にeig6を要求し、その理論以外のあらゆる電気力学にも同じ基礎関係を要求する。主節と挿入比較を同じ全範囲の中で結ぶ。',
 'eihc':'理由節eihaと主節・比較eihbの成立を同じ判断点で結び、前者が後者の説明理由であるというdaの向きを保つ。',
 'eihd':'第三段落第一文の全内容eihcを主張として提示するメッセージ。理由の提示を単なる問いや希望へ替えない。',
 'eihe':'同じ著者・論説へeihdを帰属し、前段落の最終文に続く別箇所として本文順序を保持する。',
}
LIMITS=[
 'einer jeden Theorieは電気力学という文脈での各理論と読む。数学を含む全学問へ無条件に広げず、同時に動く物体だけ又は当人の理論一つへ狭めない。',
 '剛体（座標系）は位置を指定する物理的な基準物体の役割を説明すると読む。時計は校正された経過の指示を与え、電磁過程とこれらとの関係が理論の物理的解釈を定める。各式が三種を全て明記するという字面の条件や、毎回三者の現実の存在を要求する条件ではない。',
 '運動学への基礎依存は数量・適用条件を定める依存であり、既成のNewton的時間規約の全採用、剛体の運動学だけからの電磁法則の導出を意味しない。',
 'zu entwickelndeは同じ先行構成課題の理論をこれから展開するという位置付け。第一文はその理論の構造を述べ、導出完了を前提にしない。',
 '剛体の全実数履歴、物理的指示の規約、理論の全主張の帰属は有限例から証明しない。分類を引用して述べることと、全分類の具体例を評価することを区別する。',
 '第一文全体を記述する。第二文の考慮不足と当時の困難の根、及び第三段落全体の通読判断は残る。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fs=[('body','a'),('reference','d')]
    args=[v('reference' if n=='context' else n) for n,_ in FIELDS]
    body=both(k('eigy',*args),k('eisde',v('body'),v('frame'),v('reference')))
    for n,t in reversed([(n,t) for n,t in FIELDS if n not in ('body','context')]):body=q('g',n,t,body)
    text+=define('eigz',fs,body)
    text+=define('eig2',[('clock','a'),('reference','d')],both(k('ca',v('clock')),k('eisdf',v('clock'),v('reference'))))
    text+=define('eig3',[('process','a'),('reference','d')],q('g','region','a',k('eisc3',v('process'),v('region'),'r[p eibf]','r[p eibs]','r[p eico]',v('reference'))))
    fs=[('theory','a'),('reference','d')]
    text+=define('eig4',fs,q('g','inquiry','a',both(k('eiscm',v('theory'),v('inquiry'),v('reference')),k('eie5',v('inquiry'),v('reference')))))
    text+=define('eig5',fs,q('f','claim','a',op('y',k('eiscr',v('theory'),v('claim'),v('reference')),k('eisdg',v('claim'),'r[p eigz]','r[p eig2]','r[p eig3]',v('reference')))))
    text+=define('eig6',fs,q('g','inquiry','a',both(k('eisdh',v('inquiry'),'r[p eigy]',v('reference')),k('eisdi',v('theory'),v('inquiry'),v('reference')))))
    text+=define('eig7',fs,both(k('eisdj',v('theory'),k('eirf'),quote('eigj'),v('reference')),k('eig4',v('theory'),v('reference'))))
    text+=content('eiha',q('f','theory','a',op('y',k('eig4',v('theory'),v('point')),k('eig5',v('theory'),v('point')))))
    others=q('f','other','a',op('y',both(op('u',op('e',v('other'),v('theory'))),k('eig4',v('other'),v('point'))),k('eig6',v('other'),v('point'))))
    text+=content('eihb',q('g','theory','a',both(k('eig7',v('theory'),v('point')),k('eig6',v('theory'),v('point')),others)))
    text+=content('eihc',both(evaluate('eiha'),evaluate('eihb'),k('eisdk',k('eirf'),quote('eiha'),quote('eihb'),v('point'))))
    text+='d eihd[] f[j s[k eihc[]]].\n'
    text+=define('eihe',[],both(k('eir3',k('eisdl'),k('rd'),k('eirf'),quote('eihd'),k('ri')),k('ue',k('eisdc'),k('eisdl'),k('ri')),op('u',op('e',k('eisdc'),k('eisdl')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eihe',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='kinematic_foundation_with_universal_physical_referents',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/rigid-body-kinematics-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
