"""Connect exact instruments and the complete initial two-frame setting."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_material_axes import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,interval
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-material-axes.noema';PARENT_BASIS='data/material-axes-basis-v1.json'
FULL='examples/v014/einstein-frame-instruments.noema';CORE='examples/v014/frame-instruments-core.noema'
BASIS='data/frame-instruments-basis-v1.json';ANNOTATIONS='data/frame-instruments-identifiers-v1.json';INDEX=267
FEATURE=[(n,'a') for n in ('left','right','feature','standard','document')]+[('context','d')]
PAIR=[(n,'a') for n in ('left','right','document')]+[('context','d')]
PRIMITIVES={
 'eismw':([(n,'a') for n in ('left','right','standard','document')]+[('context','d')], 'standardが同じ二物差しの構成と目盛りを比較する完全な共通規約を定める。材質、形状・寸法、部品の構成と結合、目盛の配置と同じ長さ単位への校正、同じ条件での固有応答を対象とする。一致した特徴だけを選ぶ検査表ではない。個体番号、設置場所、測定中の位置を構成上の同一性へ含めず、全運動状態で同じ測定値になるとの法則も含めない。個々の特徴の一致は別に合成する。'),
 'eismx':([(n,'a') for n in ('standard','feature','document')]+[('context','d')], '物差しの同じstandardで、構成と目盛りを漏れなく比較すべき全特徴範囲にfeatureが属する。一致した項目や測定済み標本だけへ狭めない。方式や形状を特定の製品へ限定せず、同じ意味・物理単位で比較できる規約を使う。'),
 'eismy':([(n,'a') for n in ('ruler','feature','standard','value','document')]+[('context','d')], 'rulerの構成について、同じstandardのfeatureの質的又は数量的な内容がvalueで記述される。共通規約で同定する内容であり、単なる型番の同一性、検査結果の真偽、現在の測定結果ではない。余分な部品・異なる目盛りなども全記述へ含め、未知を空集合や共通値へ補わない。数量的な記述は同じ単位で同定する。'),
 'eismz':([('node','a'),('designation','a'),('frame','a'),('document','a'),('context','d')], 'nodeが空間的な配置を指定するとき、同じdocumentでframeに与えたdesignationの呼称を引用的に再使用し、そのframeを静止した空間配置の記述基準とする。原呼称を文法的に活用した修飾語も同じ対象への参照として扱う。新しい絶対静止空間の導入、別の系への改名、全物体が静止する事実ではなく、同じ既出基準への呼称上の照応である。個々の配置の静止は別に合成する。'),
 'eism2':([('node','a'),('author','a'),('base','i[e]'),('explanation','i[e]'),('document','a'),('context','d')], 'authorがnodeでbaseに導入又は指定した同じ対象について、それがこの文脈でどのような構成・理解を指すかをexplanationとして説明的に言い直す。d. h.のような同じ対象への説明を保ち、別案への交換、単なる追加事実、原因又は時間的後続へ替えない。二つの記述の構文一致や全文脈での論理的同値の証明を要求せず、引用内容の条件は別に保持する。'),
}
MEANINGS={
 'eivh':'物差しの同じ一特徴について、両者の非空の構成記述集合が両方向に一致する。余分な記述又は片側の未知を、共通する一項目で隠さない。',
 'eivi':'二つの物差しについて、完全な共通規約と非空の全特徴範囲を選び、全特徴にeivhの厳密な一致を要求する。近似や現在の長さ測定値一つの一致へ弱めない。',
 'eivj':'同じ時計の型と校正eisdf、時間単位rb、初期静止基準raへの静止cc、同じ期間と三位置関数のeit2による代表配置の完全な静止を結ぶ。歯車・針の全物質点を静止させず、遠隔同期や表示値の一致は加えない。',
 'eivk':'同じ物差しの型、共通の長さ単位、全物質点の静止eipwと剛性eigy、初期期間の目盛付き長さ比較尺度としての校正eisefを結ぶ。対応する方法があることを要求するが、位置決定や実測の実行は要求しない。',
 'eivl':'異なる二系に異なる剛な物差しと非空の全時計範囲を与えるsfaを、物差しの全特徴一致eiviと時計の全構成一致eildへ接続する。両物差しの現行eivkと、両群に属するすべての時計のeivjを保持する。',
 'eivm':'既出の静止基準raと後で動かすzbmを異なる二つの座標系として置く、説明元の内容。二系だけが世界に存在するという限定ではない。',
 'eivn':'同じ二系のそれぞれにeivfの三本の剛な物質線・共通原点・直交・全軸範囲・初期静止を要求する、第一文の説明内容。',
 'eivo':'同じ初期設定zb4のraとzbmにeivgのX支持直線一致と対応Y/Z平行を要求する、第二文の配置内容。',
 'eivp':'同じ初期設定・二系の物差しと全時計にeivlを要求する、第三文の計器と厳密な一致の内容。',
 'eivq':'第一文の二系とその構成、第二文の対応軸配置、第三文の同等な計器を同じ初期設定へ合わせる。後続の運動付与は含めない。',
 'eivr':'後で動かす同じ第二系の参照を導入し、既出静止基準の引用呼称を保持し、二系の構成を説明的に言い直したうえで、同じ全設定eivqを第三節の議論の仮定として採用する操作。',
 'eivs':'u0043の三文にわたる同じ設定操作eivrを指示するメッセージ。現実の実験設置や内容の真理の報告へ替えない。',
 'eivt':'段落全体の設定指示eivsを同じ著者・論説へ帰属し、第三節見出しからの本文順序を保持する。',
}
LIMITS=[
 '原刊897頁のu0043全441文字・361非空白本文文字とM0063/M0064/M0065のX/Y/Zを対象とする。三文のSeien ... gegeben、mögen、sei、es seienを一つの初期設定への指示として読む。',
 '静止空間は既出の静止系raを基準とする配置であり、引用されたruhendenは同じ呼称への文法的な再使用として保持する。絶対静止空間又は全物体の静止を導入しない。第二系zbmはこの設定で新たに参照を置き、後続で動かす同じ対象として追う。',
 'd. h.は同じ二座標系の構成を三物質線によって説明する言い直しである。原点の場所には各物質線の点があるが、二系の原点や二X軸の物体そのものを同一視しない。逆向きの平行軸も許し、原文にない右手性を加えない。',
 'genau gleichは両物差しと両群の全時計について、その構成と尺度仕様の全特徴が正確に一致するという読みを採る。時計には第一節のeildを再利用し、物差しにも非空の全特徴と全記述集合の両方向一致を要求する。型番や近似測定、特徴の一部だけで済ませない。',
 '構成の一致は同じ個体、現在の指示値、初期の表示位相、遠隔同期、運動後の同じ進みや全系の長さ不変ではない。仕様比較の完全性は物理的な記述規約であり、製作・検定の手順を原文へ追加せず、仮定的な理想計器の厳密な一致を記述できるようにする。',
 '各系に非空の時計群を与え、両群の全時計のすべての組合せを比較する。時計数の具体値・一台だけ・すでに同期済みという条件は追加しない。初期配置の静止は時計の代表位置に適用し、内部機構の運動を止めない。',
 '物差しは初期設定の全物質点の静止と剛性、校正された長さ尺度へ結ぶ。校正方法の存在は物差しとしての条件であり、実際の測定結果や後続での空間測定の完了ではない。物差しの記述尺度と計器の仕様の完全性を有限標本から推測しない。',
 '有限検査、原刊照合、明示した読みでの通読判断を分ける。u0044の原点・軸・計器への運動付与、対称性の説明と後続の変換は未完であり、今回の設定へ先取りしない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    attr=lambda side:k('eismy',v(side),v('feature'),v('standard'),v('value'),v('document'),v('context'))
    text+=define('eivh',FEATURE,both(q('g','value','a',attr('left')),q('f','value','a',op('z',attr('left'),attr('right')))))
    member=k('eismx',v('standard'),v('feature'),v('document'),v('context'))
    exact=q('g','standard','a',both(k('eismw',v('left'),v('right'),v('standard'),v('document'),v('context')),q('g','feature','a',member),q('f','feature','a',op('y',member,k('eivh',*[v(n) for n,_ in FEATURE])))))
    text+=define('eivi',PAIR,both(k('xc',v('left')),k('xc',v('right')),exact))
    c=v('context');b=v('body');f=k('ra');bounds=interval(f,c)
    trajectories=[k('eismh',b,f,k('ta'),k('rb'),k(a),c) for a in ('yn','yo','yp')]
    text+=define('eivj',[('body','a'),('context','d')],both(k('ca',b),k('ci',k('rb')),k('eisdf',b,c),k('cc',b,f),k('eit2',b,f,c,k('ta'),k('rb'),*bounds,*trajectories)))
    calibration=q('g','method','a',k('eisef',b,v('method'),f,k('ta'),k('rb'),*bounds,c))
    text+=define('eivk',[('body','a'),('context','d')],both(k('xc',b),k('ti',k('ta')),k('eipw',b,f,c),k('eigy',*history(b,f,c)),calibration))
    left=v('left');right=v('right');lr=k('zby',left,c);rr=k('zby',right,c)
    rigid='i[body a context d]['+k('eigy',*history(b,f,c))+']'
    same=lambda name:'i[left a right a context d]['+k(name,left,right,k('eirf'),c)+']'
    given=k('sfa',left,right,lr,rr,c,'p xc','p ca',rigid,'p zbx','p zbz',same('eivi'),same('eild'))
    selected=op('x',k('zbz',left,v('clock'),c),k('zbz',right,v('clock'),c))
    allclocks=q('f','clock','a',op('y',selected,k('eivj',v('clock'),c)))
    text+=define('eivl',[('left','a'),('right','a'),('context','d')],both(given,k('eivk',lr,c),k('eivk',rr,c),allclocks))
    text+=content('eivm',both(k('va',k('ra')),k('va',k('zbm')),op('u',op('e',k('ra'),k('zbm')))))
    text+=content('eivn',both('t[k eivm[]][v point]',k('eivf',k('ra'),k('zb4')),k('eivf',k('zbm'),k('zb4'))))
    text+=content('eivo',k('eivg',k('ra'),k('zbm'),k('zb4')))
    text+=content('eivp',k('eivl',k('ra'),k('zbm'),k('zb4')))
    text+=content('eivq',both(*('t[k '+n+'[]][v point]' for n in ('eivn','eivo','eivp'))))
    text+=content('eivr',both(k('eisd3',k('zb5'),k('zbm'),k('eirf'),v('point')),k('eismz',k('zb5'),k('eiseb'),k('ra'),k('eirf'),v('point')),k('eism2',k('zb5'),k('rd'),quote('eivm'),quote('eivn'),k('eirf'),v('point')),k('ug',k('zb5'),k('rd'),quote('eivq'),k('eisms'),v('point'))))
    text+='d eivs[] f[j m[k eivr[]]].\n'
    text+=define('eivt',[],both(k('eir3',k('zb5'),k('rd'),k('eirf'),quote('eivs'),k('ri')),k('ue',k('eismt'),k('zb5'),k('ri')),op('u',op('e',k('eismt'),k('zb5')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eivt',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='initial_frames_and_exact_instruments_setting',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/material-axes-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
