"""Transport the complete setting and preserve its physical law-answer class."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_point_particle_dynamics import SETTING,PROFILES,ACCEL,REST,POINT,DOMAIN,CURVE,ROLES,coord,args,ZERO
from scripts.compose_electron_rest_law_claim import FUTURE
from scripts.compose_electron_coordinate_normalization import MATRIX,NORMAL
from scripts.compose_field_transform import FIELD,REGION,point_expression
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-comoving-history.noema';PARENT_BASIS='data/electron-comoving-history-basis-v1.json'
FULL='examples/v014/einstein-electron-representative-scope.noema';CORE='examples/v014/electron-representative-scope-core.noema'
BASIS='data/electron-representative-scope-basis-v1.json';ANNOTATIONS='data/electron-representative-scope-identifiers-v1.json'
CHOICE=MATRIX+[('newframe','a'),('newrecord','a')]
PAIR=SETTING+CHOICE
EVENT=PAIR+[('observed','a'),('time',R)]
MEANINGS={
 'ek5z':'同じ四原点と正の向きの空間回転について、新座標をek5aで旧座標へ戻して同じ場を評価し、三成分をek45で回転する場の関数。単なる成分名の交換、一様場への固定、異なる時刻の評価ではない。',
 'ek52':'同じ逆座標写像ek5aによる旧場領域の逆像。新領域への所属を同じ出来事の旧領域への所属へ結ぶ。境界を勝手に拡張しない。',
 'ek53':'同じ時刻原点と回転のek5fから、指定空間軸の実速度関数を取り出す。三つの速度関数をそれぞれ独立に選び直さない。',
 'ek54':'同じ粒子の物理設定ek3v、導入粒子eisxhとの同一性、局所的な位置変化ek4m、同じ瞬間速さeisxtを保持し、座標系だけはraへ固定しない条件。ek4pのK固定を外して座標記述を比較するための一般化であり、既存規約を変更しない。',
 'ek55':'ek54の同じ物理設定に対する運動法則の答え候補。右側初期変化、運動法則の範囲、同じ粒子と系への適用、法則の成立、非空で完全な対応記述の全てへの適合をek4wと同じ役割で保持する。系をraへ固定すると既存の候補条件へ戻る。',
 'ek56':'ek54の同じ指定出来事の四座標が零で、同じ三速度関数の当該値が(eisxt,0,0)である代表配置。共動系の原点、加速度零、等速軌道又は光速上限をここでは追加しない。',
 'ek57':'元の設定と同じ回転・指定出来事の原点移動で作った代表履歴について、各側の指定座標時刻で同じ出来事のseoaがあれば相手系の対応時刻にも同じ出来事のseoaがあるという双方向条件。時刻の数値一致や別の出来事への交換では済ませない。',
 'ek6a':'元のek54設定から、同じ粒子・出来事・状況・全単位と尺度・電荷値・低速慣性質量を保ち、場と領域、軌道、三速度関数、加速度を同じ回転と原点移動で構成した実際のek56設定へ結ぶ。全時刻・全出来事のek57、物理的座標対応ek5h、速度の正X配置ek5cを要求する。記録の名称だけは新系に対応して選べる。',
 'ek6b':'同じ物理的な法則個体の全域で、元の設定のek55と、同じ回転・原点移動で構成した代表設定のek55が同値であるという答え候補の保存。空集合・複数候補を許し、数式の字面の同一性、発見済み又は唯一解を要求しない。',
 'ek6c':'同じ代表の証人について、完全な物理設定の再表現ek6aと法則の答え候補の双方向保存ek6bを結ぶ。物理設定と問いの保存に別々の回転・系・電荷記録を選ばない。',
 'ek6d':'同じ固定された元の設定に対し、一つの正の向きの回転、新しい座標記述、新系の電荷記録を共同で選んでek6cを満たせる。既存の物理的内容を保持する代表の存在であり、新しい実験や電子の生成ではない。',
 'ek6e':'同じ論述状況で全てのek54設定に対しek6dの代表があるという、一般性を保つ座標選択の閉じた内容。速度の向きや原点を予め限定した設定だけを全域にせず、法則の問いを保存する代表の範囲を明示する。著者の仮定採用や機械的な真理証明とは別である。',
}
LIMITS=[
 'u0245第一文の一般性を保つ代表配置に向けた依存群。旧417主張・全規約・証拠を保持し、新しい原始関係と本文主張、全文判断はない。',
 'ek4p/ek4wはK=raに固定されているため、一般の座標再表現ではek54/ek55を用いる。粒子の同一性、物理設定、位置変化、瞬間速さ、法則候補の他の全条件を保持する。',
 '回転と時空原点移動だけを扱い、二場はそれぞれ同じ逆座標で評価して空間成分を回転する。磁場は正の向きの回転では同じベクトル変換となり、鏡映を許して擬ベクトルの符号を混同しない。',
 '指定した同じ出来事を原点に取り、完全な同じ局所時間領域と二階履歴を移す。全物理量の単位尺度を変えず、電荷・質量値も共有する。低速慣性質量を現在の低速条件へ替えない。',
 '同じ物理的な法則個体の答え候補を全域で保存する読みを明示する。成分式の文字列の一致ではなく、同じ物理的な運動関係の内容である。法則の成立と全対応記述への適合を、有限点の数値一致へ縮めない。',
 '全設定への代表の存在はNoemaで述べる内容であり、有限の回転・非一様場・軌道・候補集合の診断から証明したとは扱わない。未知の物理設定・候補判定を真又は偽へ補わず、全関数域の有限量化拒否を保持する。',
 '仮定の許容と採用、考察する指定瞬間、明白な帰結、表記と著者帰属は次に統合する。共動系の原点ずれと局所的な光速未満の適用域は後段で共有し、回転だけの代表条件へ先取りしない。',
]

def transported(**replace):
    normal=[*args(MATRIX),v('point')]
    profile=[k('ek53',*normal,*args(PROFILES),k(a)) for a in ROLES[:3]]
    acceleration=k('ek5g',*args(MATRIX),*args(ACCEL))
    values=dict(frame=v('newframe'),chargerecord=v('newrecord'),region=k('ek52',*normal,v('region')),electricfield=k('ek5z',*normal,v('electricfield')),magneticfield=k('ek5z',*normal,v('magneticfield')),domain=k('ek5d',v('domain'),v('point')),curve=k('ek5e',*normal,v('curve')),point=k('ek47',*normal,v('point')))
    values.update({n:value for (n,t),value in zip(PROFILES,profile)})
    values.update({n:coord(acceleration,a) for (n,t),a in zip(ACCEL,ROLES[:3])})
    values.update(replace)
    return args(SETTING,**values)

def definitions():
    xyz=[('px',R),('py',R),('pz',R),('pt',R)];point=point_expression(args(xyz));normal=args(NORMAL)
    oldpoint=k('ek5a',*normal,point)
    # Bind evaluated coordinates and field values once. Repeating lazy point
    # projections inside each vector component multiplies evaluation work.
    oldcoords=[(n,R) for n in ('oldx','oldy','oldz','oldt')]
    components=[(n,R) for n in ('fieldx','fieldy','fieldz')]
    bind=lambda fields,values,body:app('i['+' '.join(n+' '+t for n,t in fields)+']['+body+']',*values)
    vector=point_expression([*args(components),ZERO])
    value=app(k('ek45',*args(MATRIX),vector),v('component'))
    value=bind(components,[app(app(v('field'),k(a)),*args(oldcoords)) for a in ROLES[:3]],value)
    value=bind(oldcoords,[coord(v('oldlocation'),a) for a in ROLES],value)
    value=app(lam('oldlocation',POINT,value),oldpoint)
    text=define('ek5z',NORMAL+[('field',FIELD)],lam('component','a','i['+' '.join(n+' '+t for n,t in xyz)+']['+value+']'),FIELD)
    inverse=lam('location',POINT,k('ek5a',*normal,v('location')))
    text+=define('ek52',NORMAL+[('region',REGION)],k('s6g',v('region'),inverse),REGION)
    velocities=app(k('ek5f',*normal,*args(PROFILES)),v('moment'))
    text+=define('ek53',NORMAL+PROFILES+[('axis','a')],lam('moment',R,app(velocities,v('axis'))),PROFILES[0][1])
    text+=define('ek54',SETTING,both(k('ek3v',*args(SETTING)),op('e',v('matter'),k('eisxh')),k('ek4m',v('domain'),v('curve')),k('ek4o',*args(REST),k('eisxt'))))
    law=v('law');ctx=v('context');represented=k('eisxo',v('representation'),*args(SETTING))
    text+=define('ek55',SETTING+[('law','a')],both(k('ek54',*args(SETTING)),k('ek32',*args(FUTURE)),k('vd',law,ctx),k('eisxn',law,v('matter'),v('frame'),ctx),k('eisbi',law,v('frame'),ctx),q('g','representation','a',represented),q('f','representation','a',op('y',represented,k('vi',law,v('representation'),ctx)))))
    moment=coord(v('point'),ROLES[3])
    text+=define('ek56',SETTING,both(k('ek54',*args(SETTING)),*(k('sca',coord(v('point'),a),ZERO) for a in ROLES),*(k('sca',app(v(n),moment),target) for (n,t),target in zip(PROFILES,(k('eisxt'),ZERO,ZERO)))))
    target=dict(zip((n for n,t in SETTING),transported()))
    t=v('time');event=v('observed');shift=coord(v('point'),ROLES[3])
    oldtrack=[v('matter'),v('frame'),ctx,v('domain'),v('curve')];newtrack=[v('matter'),v('newframe'),ctx,target['domain'],target['curve']]
    text+=define('ek57',EVENT,both(op('y',k('seoa',*oldtrack,event,t),k('seoa',*newtrack,event,k('bf',t,shift))),op('y',k('seoa',*newtrack,event,t),k('seoa',*oldtrack,event,k('bd',t,shift)))))
    normal=[*args(MATRIX),v('point')];velocity=point_expression([*(app(v(n),moment) for n,t in PROFILES),ZERO])
    text+=define('ek6a',PAIR,both(k('ek54',*args(SETTING)),k('ek56',*transported()),k('ek5h',v('frame'),v('newframe'),v('lengthunit'),v('timeunit'),ctx,*normal),k('ek5c',*normal,velocity,k('eisxt')),q('f','time',R,q('f','observed','a',k('ek57',*args(PAIR),v('observed'),t)))))
    text+=define('ek6b',PAIR,q('f','law','a',op('z',k('ek55',*args(SETTING),law),k('ek55',*transported(),law))))
    text+=define('ek6c',PAIR,both(k('ek6a',*args(PAIR)),k('ek6b',*args(PAIR))))
    text+=define('ek6d',SETTING,quantified('g',CHOICE,k('ek6c',*args(PAIR))))
    cases=[(('location' if n=='point' else n),t) for n,t in SETTING if n!='context']
    shared=args(SETTING,context=v('point'),point=v('location'))
    text+=content('ek6e',quantified('f',cases,op('y',k('ek54',*shared),k('ek6d',*shared))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==417
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='complete_electron_setting_representatives_preserving_law_questions',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electron-comoving-history-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
