"""Connect every relevant material event to its carrier's own history and field domain."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_carrier_charge_composition import FAMILY,PARTITION,PACKET,ATTACHED,AMOUNTS,COUPLED_FAMILY,args
from scripts.compose_convective_charge_setting import CHART,SETTING,WITNESSES,FIELD_SETTING,SUPPORT,FLOW,at
from scripts.compose_field_equations import POINT,REGION,ROLES
from scripts.compose_doppler_infinity import quantified

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-carrier-charge-composition.noema';PARENT_BASIS='data/carrier-charge-composition-basis-v1.json'
FULL='examples/v014/einstein-carrier-field-correspondence.noema';CORE='examples/v014/carrier-field-correspondence-core.noema'
BASIS='data/carrier-field-correspondence-basis-v1.json';ANNOTATIONS='data/carrier-field-correspondence-identifiers-v1.json'
COORDS=[(n,t) for n,t in PACKET if n in ('ownx','owny','ownz')]
LOCATION=[('body','a'),('matter','a'),('owntime',R)]+COORDS
BRIDGE_BASE=CHART+[('distribution','a')]+FAMILY+[(n,t) for n,t in PACKET if n in ('ownframe','ownlower','ownupper','ownx','owny','ownz')]
EVENT=BRIDGE_BASE+[('matter','a'),('worldevent','a'),('point',POINT)]
BRIDGE=EVENT+[('body','a'),('owntime',R)]
TRANSFER=BRIDGE_BASE+[('region',REGION)]
GLOBAL=SETTING+PACKET
LOCAL=GLOBAL+[('point',POINT)]
LOCAL_WITNESSES=WITNESSES+[('amounts',AMOUNTS)]
MEANINGS={
 'ekyg':'同じbodyを索引して選んだownx/owny/ownzを同じmatter・owntimeへ適用し、三座標とowntimeから四座標関数を構成する。別の担体・物質点・時刻の成分を混ぜず、他の軸の値は零で場所の識別に用いない。',
 'ekyh':'場のframeでのpointと担体のownframeでのekygを、同じmatter・worldevent・長さ時間単位・文脈におけるzpb/eisqdへ結ぶ。担体選択・その全物質点への所属・全分布と局所成分の所属eirh/zqn、両座標校正、四値の実数妥当性、担体側区間内のowntimeを共有する。座標値や座標時刻の数値等置は要求しない。',
 'ekyi':'同じ全設定・物質点・世界線出来事・場の四座標について、ekyhを満たす一つの担体と担体側時刻を共有して存在量化する。担体だけ別の成功例、時刻だけ別の出来事から取らない。',
 'ekyj':'全分布の完全分割ekybを保ち、場の全領域に位置を割り当てられた全成員・全世界線出来事・全有効四座標についてekyiの同一対象対応を要求する。eisqdがないという理由で対象を前提から外さず、位置割当zpbに対応する明示単位を帰結側で要求する。',
 'ekyk':'同じ場の設定と全担体の族、同じ地点を固定し、領域電荷・球平均・21偏微分と成分電荷族の十個の局所証人を一組として存在量化し、ekyfへ渡す。場・担体・地点を証人ごとに変えず、総量を参照するeventを物質点のworldeventへ置き換えない。',
 'ekyl':'同じ全担体の完全付着ekyc、領域内の全物質出来事の座標対応ekyj、校正された二場ejsnと非空領域を共有する。その全有効点でekykの同じ局所電荷合成・密度・六式とekxkの非零密度支持を要求し、全成員の実際の座標時刻速度ekxlへ結ぶ。有限の成功地点だけへ縮めず、零密度で担体や速度零を要求しない。',
}
LIMITS=[
 '担体側の評価系はekycと同じ担体別関数から選ぶ。各物体の全点対距離と小ささを評価する系であり、一つの共通静止慣性系や全系同時の剛性、Born剛性、等速並進を補わない。特定のLorentz標準配置への数値変換はこの一般の同一出来事対応へ組み込まない。',
 '場の領域内にある同じ物質点・世界線出来事を、担体側の同じ物理履歴の区間内時刻へ対応させる。場の領域外の全履歴までその領域に押し込めない。両側の三座標と時刻はそれぞれの校正に従い、同じ数値時刻や同じ数値座標を要求しない。',
 '領域総電荷の同時刻断面を指すeventと、各物質点の世界線上のworldeventは別の束縛である。異なる場所の全物質点を一個の世界線出来事へ同一視しない。系間の同時性や電荷不変をこの参照対応から先取りしない。',
 '場のframeでの電荷合成には既存ekyd/ekyeのその系の物理量を使う。担体のownframeで固定された量の関数を代入しない。u0238の系間電荷不変、変換後の六式、磁気側発散零を追加しない。',
 '408主張と既存判断を保持する依存構成。イオン/電子という括弧内の読み、Lorentz理論の電磁的基礎、著者の条件付き提示、原文u0227–u0232全体の統合はまだ残る。有限の座標診断と束縛検査を連続体全域や原文同義性の証明としない。',
]

def definitions():
    body=v('body');matter=v('matter');time=v('owntime');axis=v('axis')
    values=[app(app(app(v('own'+a),body),matter),time) for a in ('x','y','z')]+[time]
    component=k('bb','n p a b')
    for role,value in reversed(list(zip(ROLES,values))):component=k('szi',op('e',axis,k(role)),value,component)
    text=define('ekyg',LOCATION,lam('axis','a',component),POINT)
    ownpoint=k('ekyg',*args(LOCATION));ownframe=app(v('ownframe'),body);ctx=v('context');ev=v('worldevent')
    valid=lambda p:both(*(k('ba',app(p,k(role))) for role in ROLES))
    position=lambda frame,p:both(k('zpb',matter,frame,ev,p,ctx),k('eisqd',matter,frame,ev,v('lengthunit'),v('timeunit'),p,ctx))
    conditions=[app(v('carriers'),body),app(app(v('portions'),body),matter),k('eirh',body,matter,ctx),
        app(k('zqn'),matter,v('distribution'),ctx),app(k('zqn'),matter,app(v('components'),body),ctx),
        k('ejsl',*args(CHART)),k('ejsl',*args(CHART,frame=ownframe)),
        k('lg',app(v('ownlower'),body),app(v('ownupper'),body),time),valid(v('point')),valid(ownpoint),
        position(v('frame'),v('point')),position(ownframe,ownpoint)]
    text+=define('ekyh',BRIDGE,both(*conditions))
    text+=define('ekyi',EVENT,quantified('g',[('body','a'),('owntime',R)],k('ekyh',*args(BRIDGE))))
    selected=both(app(k('zqn'),matter,v('distribution'),ctx),k('zpb',matter,v('frame'),ev,v('point'),ctx),k('ejsj',v('point'),v('region')))
    every=quantified('f',[('matter','a'),('worldevent','a'),('point',POINT)],op('y',selected,k('ekyi',*args(EVENT))))
    text+=define('ekyj',TRANSFER,both(k('ekyb',*args(PARTITION)),every))
    text+=define('ekyk',LOCAL,quantified('g',LOCAL_WITNESSES,k('ekyf',*args(COUPLED_FAMILY))))
    inside=k('ejsj',v('point'),v('region'))
    local=both(k('ekyk',*args(LOCAL)),k('ekxk',*args(SUPPORT,normalized=at(v('densityfield')))))
    text+=define('ekyl',GLOBAL,both(k('ekyc',*args(ATTACHED)),k('ekyj',*args(TRANSFER)),k('ejsn',*args(FIELD_SETTING)),q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,local)),k('ekxl',*args(FLOW))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='all_material_events_and_field_domain_correspondence_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/carrier-charge-composition-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
