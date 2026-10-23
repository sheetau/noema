"""Preserve one spatial construction across ruler placements and all components."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_coordinate_measurement import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import ROLES,at
from scripts.compose_moving_axes import direction
from scripts.compose_axis_projection import tracks,position
from scripts.compose_rod_methods import history,interval
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-coordinate-measurement.noema';PARENT_BASIS='data/coordinate-measurement-basis-v1.json'
FULL='examples/v014/einstein-spatial-coverage.noema';CORE='examples/v014/spatial-coverage-core.noema'
BASIS='data/spatial-coverage-basis-v1.json';ANNOTATIONS='data/spatial-coverage-identifiers-v1.json'
TRANSFER=[('frame','a'),('reference','d'),('setting','d')]
POINT=[('point','a')]+TRANSFER
ORIENT=[('axis','a')]+TRANSFER
AXIS=[('axis','a'),('origin','a'),('frame','a'),('context','d')]
CANDIDATE=[('place','a'),('frame','a'),('role','a'),('value',R),('reference','d')]
PRIMITIVES={
 'eisnd':(TRANSFER,'settingはreferenceで構想された同じframeの空間測定を実施するための測定配置の一つであるという帰属。単に実施できる別世界や成功例の標本ではなく、その測定構成で使う配置を指す。同じ物差しの置き直しと配置ごとの使用期間の違いは許すが、同じ空間・対象・原点・軸・尺度の保持は合成側で要求する。referenceの一つの時刻区間への包含や、物差しの配置がreferenceと同じであることを意味しない。測定結果、全地点の被覆と一意性は含意しない。'),
}
MEANINGS={
 'eixj':'同じ点を同じ系・単位で二つの配置の正の全期間に静止する完全履歴eit2へ結び、三位置座標が各期間の初期時刻で有効かつ一致する。静止履歴を先に要求するため、二端だけの一致で途中の移動を隠さない。期間や文脈の個体同一性は要求しない。',
 'eixk':'同じ軸・系・単位について両配置に正方向記録が存在し、両側の全記録対がsexdの同じ非零正方向を持つ。正の倍率と異なる記録個体を許し、零座標への射影だけでは見分けられない正方向の矛盾も拒否する。',
 'eixl':'指定系での同じ物質軸の完全な直線履歴eiv2と全成員の静止eipw、原点の完全な静止履歴、全正方向記録の整合性を要求する。各記録が同じ実物質方向と平行であることも確かめ、任意の方向標識を正方向と同一視しない。',
 'eixm':'その系自身に静止する三つの物質軸を、唯一の原点・相異なる三役割・実際の直交へsexで結ぶ。軸割当ては全役割を尽くす。原点・各軸・配備物差しは初期と同じ個体を保持するが、物差しの全期間の固定位置をここでは課さない。',
 'eixn':'同じ測定構成に帰属する二配置で、同じ原点・三軸・物差し・全地点範囲を保持する。各軸の全物質成員を両方向一致させ、全成員の位置と各軸の正方向を保持する。時計や物差しの全物質点を軸の位置保存へ混ぜない。',
 'eixo':'同じ基準設定の対象地点をその位置ごと保存した測定配置で、同じ系・役割・値の実測候補eixhを要求する。配置の帰属と幾何の保存、対象の場所、実測をすべて保持する。',
 'eixp':'同じ地点・系・役割・値についてeixoを満たす測定配置が存在する。配置による物差しの置き直しを許すが、対象・軸・尺度を交換した別設定で代用しない。',
 'eixq':'基準設定で選ぶ同じzcy座標がeixpとして実測され、全配置・全測定手順を含む全有効実数値候補がその値に一致する。配置間の不一致を局所的な一意性で隠さない。',
 'eixr':'非空の全空間地点範囲と異なる三役割の全組合せにeixqをsgfで要求し、eixmの同じ実三軸を保つ。一地点・一成分の欠落や地点範囲の縮小を許さない。',
 'eixs':'異なる二系raとzbmそれぞれの全空間・全三成分へeixrを適用する。両系の座標値、原点位置、正方向、時計時刻の一致は加えない。',
}
LIMITS=[
 'u0045第一文の空間測定依存群。270本文主張と既存判断を保持する。前段の平行候補の採用と測定設定の引用、両系の座標表記、時計配置点での時刻設定と全体意味判断はまだ統合しない。',
 '測定配置は同じ思考上の測定構成に属する設定として読む。元の運動履歴の時刻部分区間と同一視せず、物差しを置き直して長さを比較することと、軸・測定対象の位置を保持することを分ける。期間を等置して物差しを全空間で一位置に固定しない。',
 '位置比較の両側に完全な静止履歴を課し、三座標は同じ系と単位で比較する。各配置に異なる原点や尺度を隠す座標変換を許さない。異なる系の座標値を比較する条件ではない。',
 '原点・軸の全物質成員・対象地点を保存する。物差しや時計を全点座標の保存範囲へ無条件に追加しない。物差しの初期個体と局所測定での剛性・校正は保持する。',
 '一つの距離比較手続きの内部では既存eisef/eisncの長さ比較・移し取り・必要な分割の操作的意味を用いる。有限回で任意の実数を全桁算出する主張や、原文に記されていない特定の物差し再配置アルゴリズムを追加しない。',
 '全地点と全軸成員の範囲は既存の意味規約に従う。有限モデルは欠落・取り違えと引数接続を識別するもので、全空間の有限列挙による証明ではない。全実数候補と完全履歴は有限評価のまま証明しない。',
]

def args(fields):return [v(n) for n,_ in fields]
def roles(role):return op('x',op('e',role,k('yn')),op('x',op('e',role,k('yo')),op('e',role,k('yp'))))

def definitions():
    text='r eisnd[a d d] c.\n'
    p=v('point');f=v('frame');ref=v('reference');setting=v('setting');c=v('context');axis=v('axis');origin=v('origin')
    locs=[position(p,f,ctx,interval(f,ctx)[0]) for ctx in (ref,setting)]
    clauses=[k('eit2',p,f,ctx,k('ta'),k('rb'),*interval(f,ctx),*tracks(p,f,ctx)) for ctx in (ref,setting)]
    clauses += [k('eisdd',f,k('ta'),k('rb'),ctx) for ctx in (ref,setting)]
    text+=define('eixj',POINT,both(*clauses,*(k('ba',x) for xs in locs for x in xs),*(k('sca',a,b) for a,b in zip(*locs))))
    selected=lambda rec,ctx:k('zsa',rec,axis,f,k('ta'),ctx)
    components=lambda rec:[k('zsb',rec,k(a)) for a in ROLES]
    pairs=q('f','left','a',q('f','right','a',op('y',both(selected(v('left'),ref),selected(v('right'),setting)),k('sexd',*components(v('left')),*components(v('right'))))))
    text+=define('eixk',ORIENT,both(q('g','left','a',selected(v('left'),ref)),q('g','right','a',selected(v('right'),setting)),pairs))
    guide=k('eismu',axis,f,c);delta=direction(axis,origin,guide,f,c,interval(f,c)[0])
    records=q('f','record','a',op('y',selected(v('record'),c),k('sexc',*delta,*components(v('record')))))
    text+=define('eixl',AXIS,both(k('eiv2',axis,origin,guide,f,c),k('eipw',axis,f,c),k('eixj',origin,f,c,c),k('eixk',axis,f,c,c),records))
    origin=k('zbn',f,c);line=lambda a:k('zbo',f,k(a),c)
    material='i[line a]['+k('eixl',v('line'),origin,f,c)+']'
    rigid='i[line a context d]['+k('eigy',*history(v('line'),f,v('context')))+']'
    perpendicular='i[left a right a context d]['+k('eiv5',v('left'),origin,k('eismu',v('left'),f,v('context')),v('right'),origin,k('eismu',v('right'),f,v('context')),f,v('context'),interval(f,v('context'))[0])+']'
    triad=k('sex',f,origin,*(line(a) for a in ROLES),*(k(a) for a in ROLES),c,'p zbv','p zbw',material,rigid,'p zbr',perpendicular)
    choices=[both(op('e',v('role'),k(a)),op('e',v('line'),line(a))) for a in ROLES]
    exact=q('f','line','a',q('f','role','a',op('z',k('zbw',f,v('line'),v('role'),c),op('x',choices[0],op('x',*choices[1:])))))
    unique=q('f','point','a',op('y',k('zbv',f,p,c),op('e',p,origin)))
    ruler=k('zby',f,c)
    identities=[op('e',origin,k('zbn',f,k('zb4'))),op('e',ruler,k('zby',f,k('zb4'))),*(op('e',line(a),k('zbo',f,k(a),k('zb4'))) for a in ROLES)]
    text+=define('eixm',[('frame','a'),('context','d')],both(k('va',f),triad,exact,unique,k('xc',ruler),k('zbx',f,ruler,c),*identities))
    clauses=[k('eisnd',*args(TRANSFER)),k('eixm',f,ref),k('eixm',f,setting),op('e',k('zbn',f,ref),k('zbn',f,setting)),op('e',k('zby',f,ref),k('zby',f,setting)),k('eixj',k('zbn',f,ref),f,ref,setting),q('f','point','a',op('z',k('zcu',p,f,ref),k('zcu',p,f,setting)))]
    for a in ROLES:
        left=k('zbo',f,k(a),ref);right=k('zbo',f,k(a),setting)
        lm=k('eirh',left,p,ref);rm=k('eirh',right,p,setting)
        clauses += [op('e',left,right),k('eixk',left,f,ref,setting),q('f','point','a',both(op('z',lm,rm),op('y',op('x',lm,rm),k('eixj',p,f,ref,setting))))]
    text+=define('eixn',TRANSFER,both(*clauses))
    text+=define('eixo',CANDIDATE+[('setting','d')],both(k('eixn',*args(TRANSFER)),k('zcu',v('place'),f,ref),k('zcu',v('place'),f,setting),k('eixj',v('place'),f,ref,setting),k('eixh',v('place'),f,v('role'),v('value'),setting)))
    text+=define('eixp',CANDIDATE,q('g','setting','d',k('eixo',*args(CANDIDATE),setting)))
    selectedvalue=k('zcy',v('place'),f,v('role'),k('ta'),ref)
    text+=define('eixq',[(n,t) for n,t in CANDIDATE if n!='value'],both(k('eixp',v('place'),f,v('role'),selectedvalue,ref),q('f','value',R,op('y',k('eixp',*args(CANDIDATE)),k('sca',v('value'),selectedvalue)))))
    places='i[place a]['+k('zcu',v('place'),f,ref)+']';channels='i[role a]['+roles(v('role'))+']'
    supplied='i[place a role a]['+k('eixq',v('place'),f,v('role'),ref)+']'
    text+=define('eixr',[('frame','a'),('reference','d')],both(k('eixm',f,ref),k('sgf',places,channels,supplied)))
    text+=define('eixs',[('reference','d')],both(op('u',op('e',k('ra'),k('zbm'))),k('eixr',k('ra'),ref),k('eixr',k('zbm'),ref)))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==270;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='all_spatial_components_across_preserved_measurement_settings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/coordinate-measurement-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
