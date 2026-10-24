"""Connect the two normalized boosts to current three-frame measurements."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_velocity_light_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-velocity-light-claim.noema';PARENT_BASIS='data/velocity-light-claim-basis-v1.json'
FULL='examples/v014/einstein-parallel-current-records.noema';CORE='examples/v014/parallel-current-records-core.noema'
BASIS='data/parallel-current-records-basis-v1.json';ANNOTATIONS='data/parallel-current-records-identifiers-v1.json';INDICES=(145,146)
FRAMES=[(n,'a') for n in ('initial','intermediate','final')]
RECORDS=[(n,'a') for n in ('event','first','middle','last')]
SPEEDS=[(n,R) for n in ('light','speed','moving')]
CONTEXT=[('context','d')]
MEANINGS={
 'ejqv':'相異なる指定三系の同じ対象出来事・状況を、現在の測定規則eiyxによる三つの四座標記録へ結ぶ。§3の逆変換用第三系zgiや旧shdを流用しない。',
 'ejqw':'相異なる三系について、非空の全対象出来事が各系で現在の記録を持ち、同じ系の全候補が四座標値として一致する。隣接二組のsgvを同じ中間系へ結び、別記録の同値を許す。',
 'ejqx':'同じ対象出来事の現在三記録ejqvにおいて、各系の実際の原点で出来事が起こり、三位置と時刻が全て零である。同じ時刻値を全出来事で要求せず、共通の原点出来事だけに規約を置く。',
 'ejqy':'三系の同じ尺度・時刻校正eisdd、初系から中間系への速度speedと中間系から第三系への速度movingの全体並進eja2、両速度の符号付き光速未満条件s45を結ぶ。共通原点・零時刻を持つ現在三記録が存在することを要求し、原点ずれや未校正の尺度を同形式の変換へ混ぜない。',
 'ejqz':'指定三系の同じ対象出来事の全対応三記録ejqvで、渡した三記録関係が成立する。対象範囲を式の成否で選ばず、存在・値の一意性はejqwで別に要求する。',
 'ejq2':'全対象出来事の現在三記録の存在・値の一意性ejqwと、同じ中間記録を共有する二回の係数1の四変換s4mを結ぶ。各回の速度・光速度・時刻・横二成分を保持する。',
 'ejq3':'同じ全対応三記録について、初系から第三系への係数1の四変換s4lへ、速度引数として同じs3j(light,speed,moving)を渡す。βの引数も合成速度へ変わり、横二成分を落とさない。',
 'ejq4':'現在のK/kの全装置・全体並進eivzを保ち、第三系k′=zloを同じ状況zb6へ導入する設定ejqy。第三系速度zltはkに対する符号付き速度で、以前の点の速さzkqや逆変換第三系zgiとは同一視しない。',
 'ejq5':'同じK・k・k′、現在状況zb6、光速度tc、速度zb7/zltを用いて、全現在記録へ§3の規約による二変換ejq2を適用する内容。',
 'ejq6':'同じK・k・k′の全現在記録に、§3の四式の速度だけを(v+w)/(1+vw/V²)へ置き換えたejq3を適用する結論内容。物理的な出来事の範囲と任意の実数四入力の関数全域を同一視しない。',
 'ejq7':'現在三系の設定ejq4と二回の変換適用ejq5を合わせた、同形式の合成結果ejq6へ渡す前提内容。結論の真理や著者の導出の健全性を前提へ先取りしない。',
}
LIMITS=[
 'u0147第二文からu0148/M0285とu0149冒頭trittまでの物理依存群を現在本文へ接続する。旧文145/146だけを更新する。第一文の別導出・全群の主張・必要性・全単位判断は次の関連群統合へ残し、完成数を増やさない。',
 '原刊906頁から907頁へ続く条件文を一つとして読む。§3と同じ式という記述は、同じ校正と共通原点・零時刻の規約の下での係数1の四変換を指す。原点ずれや任意の尺度率を速度の置換だけから消さない。',
 'k′は新たな第三系zloであり、§3の逆変換のK′=zgiとは別である。wはk′のkに対する速度zltで、前の点の速さzkqを無条件に代入しない。群への拡張を妨げない符号付き−V<w<Vの範囲を使い、正方向への特殊化は別導出の接続で扱う。',
 '原点の軸上条件と全固定配置・全比較時点の並進は既存eja2へ、測定記録はeiyxへ、値の一意性はsgv/shhへ結ぶ。対象範囲zc4は既存の全対象範囲であり、変換式が成立した標本へ縮めない。',
 '有限対照検査は全実切断の体・正平方根法則や物理的導出の証明ではない。既存の有理多項式証拠と区別する。古い証拠とs5mの旧参照は保存し、その本文接続の更新を未完として記録する。',
]

def definitions():
    frames=[v(n) for n,_ in FRAMES];event,first,middle,last=[v(n) for n,_ in RECORDS]
    ctx=v('context');light,speed,moving=[v(n) for n,_ in SPEEDS];zero=k('bb','n p a b')
    distinct=both(*(op('u',op('e',frames[a],frames[b])) for a,b in ((0,1),(0,2),(1,2))))
    fields=FRAMES+RECORDS+CONTEXT
    text=define('ejqv',fields,both(distinct,k('zc4',event),*(k('eiyx',event,rec,frame,ctx) for rec,frame in zip((first,middle,last),frames))))
    side=lambda frame:'i[event a tuple a]['+k('eiyx',event,v('tuple'),frame,ctx)+']'
    text+=define('ejqw',FRAMES+CONTEXT,both(distinct,*(k('sgv','p zc4',side(frames[a]),side(frames[b]),'p shh') for a,b in ((0,1),(1,2)))))
    rows=[k('ejqv',*frames,event,first,middle,last,ctx)]
    for frame,rec in zip(frames,(first,middle,last)):
        origin=k('zbn',frame,ctx)
        rows += [k('zbv',frame,origin,ctx),k('cb',event,origin,frame),*(k('sca',k('zc6',rec,k(role)),zero) for role in ('yn','yo','yp','zc7'))]
    text+=define('ejqx',fields,both(*rows))
    origin=k('ejqx',*frames,event,first,middle,last,ctx)
    for n,_ in reversed(RECORDS):origin=q('g',n,'a',origin)
    text+=define('ejqy',FRAMES+SPEEDS+CONTEXT,both(*(k('eisdd',frame,k('ta'),k('rb'),ctx) for frame in frames),k('eja2',frames[0],frames[1],speed,ctx),k('eja2',frames[1],frames[2],moving,ctx),k('s45',light,speed),k('s45',light,moving),origin))
    every=op('y',k('ejqv',*frames,event,first,middle,last,ctx),'c[v relation][v first v middle v last]')
    for n,_ in reversed(RECORDS):every=q('f',n,'a',every)
    text+=define('ejqz',FRAMES+CONTEXT+[('relation','h[a a a] c')],every)
    for name,body in (('ejq2',k('s4m',first,middle,last,light,speed,moving)),('ejq3',k('s4l',first,last,light,k('s3j',light,speed,moving)))):
        relation='i[first a middle a last a]['+body+']'
        text+=define(name,FRAMES+SPEEDS+CONTEXT,both(k('ejqw',*frames,ctx),k('ejqz',*frames,ctx,relation)))
    fixed=[k(n) for n in ('ra','zbm','zlo','tc','zb7','zlt','zb6')]
    text+=content('ejq4',both(k('eivz',k('zb6')),k('ejqy',*fixed)))
    text+=content('ejq5',k('ejq2',*fixed))
    text+=content('ejq6',k('ejq3',*fixed))
    text+=content('ejq7',both(*(op('t',k(n),v('point')) for n in ('ejq4','ejq5'))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    statements=parse('n:r ug[a a i[e] a d] c.r zc[a a i[e] i[e] a d] c.'+'r zlr[] a.r zls[] a.r rd[] a.r zlq[] a.r ri[] d.r ejq4[] e.r ejq6[] e.r ejq7[] e.'+
        's['+k('ug',k('zlr'),k('rd'),quote('ejq4'),k('zlq'),k('ri'))+'].'+
        's['+k('zc',k('zls'),k('rd'),quote('ejq7'),quote('ejq6'),k('zlq'),k('ri'))+'].')['statements']
    for i,st in zip(INDICES,statements):doc['statements'][i]=st
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_three_frame_composition_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/velocity-light-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
