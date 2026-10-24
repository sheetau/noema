"""Connect a body's moving/rest histories to the same process and both transformed fields."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define,args
from scripts.compose_material_body_motion import FAMILY
from scripts.compose_field_equations import FIELD,REGION

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-problem-series-reduction.noema';PARENT_BASIS='data/problem-series-reduction-basis-v1.json'
FULL='examples/v014/einstein-body-rest-field-method.noema';CORE='examples/v014/body-rest-field-method-core.noema'
BASIS='data/body-rest-field-method-basis-v1.json';ANNOTATIONS='data/body-rest-field-method-identifiers-v1.json'
FRAMES=[('process','a'),('oldframe','a'),('newframe','a'),('context','d')]
PAIR=FRAMES+[('oldrecord','a'),('newrecord','a')]
BOOST=FRAMES+[('light',R),('speed',R)]
LOCAL=BOOST+[('region',REGION)]
FIELDS=LOCAL+[(n,'a') for n in ('chargeunit','electricunit','magneticunit','forceunit')]+[('electricfield',FIELD),('magneticfield',FIELD)]
TIMES=[(n,R) for n in ('oldlower','oldupper','newlower','newupper')]
HISTORY=[('body','a'),('members','h[a] c')]+TIMES+[(side+axis,FAMILY) for side in ('old','new') for axis in ('x','y','z')]
MOTION=[('oldframe','a'),('newframe','a'),('context','d')]+HISTORY
SETTING=FIELDS+HISTORY
CANDIDATE=[('newelectric',FIELD),('newmagnetic',FIELD)]
INFLUENCE=[('body','a'),('process','a'),('frame','a'),('region',REGION),('context','d')]
PRIMITIVES={'eisvi':(INFLUENCE,'指定された同じbodyの物理的作用が、frameの同じregionでprocessの状態又は伝播を変化させることへの因果的な寄与。単なる同時生起・空間的一致・観測者の表示変更ではない。反射だけ、完全な鏡、唯一原因、特定の材質又は機構へ限定しない。過程の範囲と物体の同一性、物理的な場・単位・運動又は静止、場の変換則は別に接続する。この関係は実測を済ませたことや、全問題が解けることを含意しない。')}
MEANINGS={
 'ekvv':'指定した同じprocessの一つの同じ出来事に、oldframeのoldrecordとnewframeのnewrecordをejtfで結ぶ。系を固定されたra/zbmへ置き換えず、異なる出来事の片側ずつの記録を組にしない。座標の長さ時間単位は既存eiyxと同じta/rbである。',
 'ekvw':'同じ過程の全所属出来事が非空で、その各出来事が指定した両系の座標記録を持つ。変換式の成否で出来事を選ばず、両系で別の出来事を存在証人にしない。',
 'ekvx':'同じekvwの全ての同一出来事の記録対について、同じV/vでekceの正逆の四座標変換が成立する。単一の成功対や同じ数値四組だけの比較に縮めない。',
 'ekvy':'ekvxの同じ過程・両系・V/vについて旧領域内の出来事が少なくとも一つあり、全同一出来事記録対で旧領域とs6mの新逆像領域への所属が一致する。過程全体をその局所領域へ押し込めず、領域外の記録対応も保つ。',
 'ekvz':'指定された旧両場と候補の新両場を、同じprocess・二系・ta/rb・四物理単位へ結び、旧領域と同じ逆像領域について双方でejsnの物理的同定とeispnの過程帰属を要求する。換算は既出のGaussian規約と同じ1及び1/Vで、Vの許容域を保持する。候補の数値一致だけを物理的帰属とせず、この定義自体では候補に変換式を要求しない。',
 'ekv2':'異なる指定二系で同じbody・全members・context・ta/rbを共有する。旧系の全物質点履歴ではeiagの運動、新系の全履歴ではeiahの静止を要求する。両区間は別々の座標時刻で、双方の正の長さと四端点の実数妥当性を保持する。重心や三つの標識点だけの静止、情報不足による非運動判定で代用しない。',
 'ekv3':'全ての同一出来事記録対のうち旧領域内のものについて、旧時刻が同じ旧履歴区間、新時刻が同じ新履歴区間に入る。新旧で同じ数値区間や同時刻とせず、関与する過程の出来事を物体履歴の期間へ結ぶ。',
 'ekv4':'同じ設定で全出来事・領域対応ekvy、両系の物理的な候補場ekvz、同じ物体の運動と静止ekv2、対象出来事の両履歴期間への所属ekv3、旧領域での同じ物体から同じ過程への作用eisviを接続する。場候補ごとに物体・過程・静止系・単位又は期間を選び直さない。',
 'ekv5':'ekv4の一つの固定設定の下で、新系における同じ過程の物理的な電場・磁場という二関数を同時に問うNoema質問。片方の場だけ、自然言語の答え名、既知性や実行済みを答えの代用にしない。',
 'ekv6':'同じ旧両場を同じV/vでs6kとs6lにより混合し、同じ逆座標で引数を写した二関数が、ekv5の同じ設定の質問に答える。両場の変換を単なる原始的な変換済みフラグにせず、実際の構成と物理的な答え条件へ結ぶ。',
}
LIMITS=[
 'u0226に必要な物理的な依存群である。新しい原始関係は物体の作用が過程へ因果的に寄与するeisvi一つで、運動・静止・両場・座標・領域・質問・変換は既存構成から組み立てる。既存406主張と判断を保ち、この段階だけで原文単位の完成件数を増やさない。',
 '対象は任意の電磁過程の両場であり、平面波・正弦波・完全鏡に限定しない。光としての帰属、光学問題の全範囲、解答記録と質問族、方法の実効的な手続き案、本質的役割と著者提示は後続で接続する。',
 '座標記録eiyxの測定規約に合わせta/rbを両系の尺度として使う。両場も同じ電荷・力・電場・磁場単位で表し、係数1と1/Vの既出規約を明示する。正の数というだけでVが物理的な光速度だと認定せず、本文接続時には同じV=tcを保つ。',
 's46及びs6k/s6lは軸を相対速度に合わせた標準配置の一様なLorentz変換である。任意の動体にこの形の静止系が存在することをここで証明せず、加速・回転・変形を勝手に除外して原文のalle/jedesを真にしない。現在の構成はこの方法の適用条件を明示する候補であり、全問題への適用可能性は著者の主張として別に記述する。',
 '同じ物体の全物質点履歴を指定した記述尺度で追跡する。旧新の区間は座標時刻が異なり、同じ数値区間を要求しない。対象領域内の全過程出来事の旧新記録を両区間へ収め、無関係な期間の静止で代用しない。内部構成の変化する物体への拡張は既存履歴の限界として残る。',
 'eisviは同じ領域での物理的な作用の帰属であり、数値変換から因果を推測しない。領域は同じ作用の対象範囲を後続の問題設定と共有し、成功する出来事だけへ縮めない。全過程の座標対応と、局所領域での場及び作用を区別する。',
 '新候補場が同じ過程の物理的な場であることは、旧場の数値変換だけから自動的に導かない。質問への合致は物理的な帰属入力を別に要求する。場の方程式・実測・実行済み・解の唯一性や全問題の解決は含めない。',
 '全物質点・全実時刻の履歴と全出来事記録対の量化を維持する。有限検査は境界の引数共有、実際の座標・領域・場の計算、二関数質問への合致、無限域の評価拒否を分け、有限例を物理法則又は原文同義性の証明としない。',
]

def coordinates(record):return 'i[role a]['+k('zc6',record,v('role'))+']'
def allpairs(body):return q('f','oldrecord','a',q('f','newrecord','a',op('y',k('ekvv',*args(PAIR)),body)))
def history(side):return [v('body'),v(side+'frame'),v('context'),k('ta'),k('rb'),v(side+'lower'),v(side+'upper'),v('members'),*(v(side+a) for a in ('x','y','z'))]

def definitions():
    text='r eisvi[a a a '+REGION+' d] c.\n'
    process=v('process');ctx=v('context');V=v('light');speed=v('speed');old=coordinates(v('oldrecord'));new=coordinates(v('newrecord'))
    pair=both(*(k('ejtf',process,v('event'),v(side+'record'),v(side+'frame'),ctx) for side in ('old','new')))
    text+=define('ekvv',PAIR,q('g','event','a',pair))
    member=k('eispo',v('event'),process,ctx)
    records=both(*(q('g','record','a',k('ejtf',process,v('event'),v('record'),v(side+'frame'),ctx)) for side in ('old','new')))
    text+=define('ekvw',FRAMES,both(q('g','event','a',member),q('f','event','a',op('y',member,records))))
    text+=define('ekvx',BOOST,both(k('ekvw',*args(FRAMES)),allpairs(k('ekce',V,speed,old,new))))
    region=k('s6m',V,speed,v('region'));inside=k('ejsj',old,v('region'))
    exists=q('g','oldrecord','a',q('g','newrecord','a',both(k('ekvv',*args(PAIR)),inside)))
    text+=define('ekvy',LOCAL,both(k('ekvx',*args(BOOST)),exists,allpairs(op('z',inside,k('ejsj',new,region)))))
    one=k('bb','n p b b');rows=[k('s45',V,speed)]
    for side,reg,ef,hf in [('old',v('region'),v('electricfield'),v('magneticfield')),('new',region,v('newelectric'),v('newmagnetic'))]:
        frame=v(side+'frame')
        rows.extend([k('ejsn',frame,k('ta'),k('rb'),ctx,reg,*(v(n) for n in ('chargeunit','electricunit','magneticunit','forceunit')),one,k('sjd',V),ef,hf),k('eispn',process,frame,ef,hf,reg,ctx)])
    text+=define('ekvz',FIELDS+CANDIDATE,both(*rows))
    times=[k('ba',v(n)) for n,t in TIMES]+[k('bg',v(side+'lower'),v(side+'upper')) for side in ('old','new')]
    text+=define('ekv2',MOTION,both(op('u',op('e',v('oldframe'),v('newframe'))),*times,k('eiag',*history('old')),k('eiah',*history('new'))))
    intervals=both(*(k('lg',v(side+'lower'),v(side+'upper'),k('zc6',v(side+'record'),k('zc7'))) for side in ('old','new')))
    text+=define('ekv3',LOCAL+TIMES,allpairs(op('y',inside,intervals)))
    text+=define('ekv4',SETTING+CANDIDATE,both(k('ekvy',*args(LOCAL)),k('ekvz',*args(FIELDS+CANDIDATE)),k('ekv2',*args(MOTION)),k('ekv3',*args(LOCAL+TIMES)),k('eisvi',v('body'),process,v('oldframe'),v('region'),ctx)))
    text+=define('ekv5',SETTING,'j v[i['+' '.join(n+' '+t for n,t in CANDIDATE)+']['+k('ekv4',*args(SETTING+CANDIDATE))+']]','g['+FIELD+' '+FIELD+']')
    transformed=[k(n,V,speed,v('electricfield'),v('magneticfield')) for n in ('s6k','s6l')]
    text+=define('ekv6',SETTING,'h['+k('ekv5',*args(SETTING))+']['+' '.join(transformed)+']')
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==406
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_body_rest_frame_and_both_field_question_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/problem-series-reduction-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
