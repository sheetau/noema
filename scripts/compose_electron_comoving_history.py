"""Join calibrated histories to the same event's native coordinate derivatives."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_material_velocity import POINT,DOMAIN,CURVE,ROLES,coord,valid,equalpoints
from scripts.compose_point_particle_dynamics import SETTING,PROFILES,ZERO,args
from scripts.compose_field_transform import point_expression

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-coordinate-normalization.noema';PARENT_BASIS='data/electron-coordinate-normalization-basis-v1.json'
FULL='examples/v014/einstein-electron-comoving-history.noema';CORE='examples/v014/electron-comoving-history-core.noema'
BASIS='data/electron-comoving-history-basis-v1.json';ANNOTATIONS='data/electron-comoving-history-identifiers-v1.json'
BOOST=[('light',R),('speed',R),('offset',POINT)]
FRAME=[('first','a'),('second','a'),('lengthunit','a'),('timeunit','a'),('context','d')]+BOOST
MAPTRACK=BOOST+[(prefix+n,t) for prefix in ('old','new') for n,t in (('domain',DOMAIN),('curve',CURVE))]
HISTORY=[('matter','a')]+FRAME+MAPTRACK[len(BOOST):]
EVENT=HISTORY+[('event','a'),('point',POINT),('velocity',POINT)]
CURRENT=SETTING+[('second','a'),('light',R),('offset',POINT),('newdomain',DOMAIN),('newcurve',CURVE)]
MEANINGS={
 'ek5n':'同じ長さ時間単位で校正した二系の全配置・全比較時点の等速並進eiojを、(speed,0,0)という一つの速度へ結ぶ。正の光速度、非負の光速未満のspeed、任意の有効四原点ずれを保ち、ek5iを全域の同一出来事対応eisqtにする。数値写像だけで物理的な系を認定しない。',
 'ek5o':'旧曲線を旧時刻で評価し、同じ原点ずれを持つboostで移した点の新時刻を返す。新曲線の引数へ旧時刻をそのまま流用しない。',
 'ek5p':'新曲線を新時刻で評価し、同じ逆boostで戻した点の旧時刻を返す。新旧の時刻原点を別に置いたまま逆対応する。',
 'ek5q':'旧時間領域の指定実時刻について、旧曲線の時刻成分、変換点の有効性、新領域への所属、新曲線との全四成分の一致、逆変換による復帰を要求する。領域外には対応を要求しない。',
 'ek5r':'新時間領域の指定実時刻からek5qと逆方向の全四成分・領域・曲線・正逆写像の対応を要求する。旧から新の片側だけでは新側の余分な履歴を許さない。',
 'ek5s':'同じ粒子の両系での非空で完全なseob履歴を、ek5nの物理的な座標対応と全実時刻でのek5q/rへ結ぶ。両系の領域内の全座標出来事を同じ長さ時間単位のeisqdへ結び、その同じ出来事が相手系の対応時刻のseoaにもあることを両方向に要求する。別粒子・別出来事・別尺度・部分履歴を混ぜない。',
 'ek5t':'ek5sの同じ粒子・出来事・旧四座標で、旧三速度をseocの実際の三つの座標時刻微分へ結ぶ。ek5mの正の時刻変化率を要求し、新系の静止や微分値を前提にはしない。',
 'ek5u':'同じ電子・出来事をek5iで移した新四座標で、新曲線の実際の三つの座標時刻微分seocをek5lの変換三速度へ結ぶ。数値速度の割当だけへ縮めず、新系の完全な履歴と内点を含む。',
 'ek5v':'同じ共有引数に対しek5tならek5uという条件付きの速度変換の内容。両系の完全な物理的履歴と旧微分を前提、新系の実際の微分を帰結として区別する。全実数の連鎖律の自動証明又は著者の新主張ではない。',
 'ek5w':'前段の同じ電子の設定ek4pを保ち、指定出来事の四座標零、同じ三速度関数の当該値(v,0,0)、同じvの等速並進系と両履歴ek5tを結ぶ代表配置。vはeisxtであり、別の系間速度へ置換しない。一般性を保つ選択の提示は別に必要である。',
 'ek5x':'同じ電子の同じ出来事について、旧点を任意の原点ずれを持つboostで移した新点で、seocの三つの実際の座標時刻微分が零となる。新点を先取りして零とせず、前後の静止や加速度零を要求しない。',
 'ek5y':'同じ共有設定の代表配置ek5wから同じ新系の瞬間静止ek5xへ至る条件付きの内容。前提と帰結を混ぜず、同じ粒子・出来事・速さ・単位・新旧履歴を保持する。著者の明白さの提示と本文帰属は後続で接続する。',
}
LIMITS=[
 'u0245の瞬間静止の帰結へ向けた依存群。旧417主張・規約・証拠を保持し、新しい原始関係と本文主張、全文判断はない。',
 '共動系の全固定配置の等速並進と、加速してよい同じ電子の局所履歴を区別する。原点ずれを固定してよいが、その四値を零には制限しない。後続u0248の零原点指定を先取りしない。',
 '時間領域の双方向の全域対応と両系の完全な履歴を要求する。選択する局所領域は両側内点を含み、新系の座標時刻でパラメーター化する。全生涯、有限区間の等速又は無放射は追加しない。',
 '新旧の三速度は同じseocの三微分へ接続する。数値のboost式と実際の物理的な対応を区別し、ek5v/yは条件付きの内容として保持する。有限検査から一般の連鎖律、物理的真理又は原文同義性を自動認定しない。',
 '検査は登録された解析的多項式の微分と、全域式から取り出した時刻・出来事の診断を区別する。未知の履歴や微分は拒否し、実数全域の量化を有限の例で認定しない。',
 '一般性を失わない代表配置の範囲、仮定の許容と採用、明白さ、七つの記号表記、著者帰属は未統合。後続の静止系の運動式と前のlaw候補への接続も残る。',
]

def definitions():
    first,second,ctx=v('first'),v('second'),v('context');lu,tu=v('lengthunit'),v('timeunit');speed=v('speed')
    text=define('ek5n',FRAME,both(k('s45',v('light'),speed),k('bc',ZERO,speed),valid(v('offset')),k('eioj',first,second,lu,tu,ctx),
        *(k('ejsl',f,lu,tu,ctx) for f in (first,second)),
        *(k('sca',k('eislc',first,second,lu,tu,k(a),ctx),s) for a,s in zip(ROLES[:3],(speed,ZERO,ZERO))),
        k('eisqt',first,second,lu,tu,lam('location',POINT,k('ek5i',*args(BOOST),v('location'))),ctx)))
    for name,prefix,transform in [('ek5o','old','ek5i'),('ek5p','new','ek5j')]:
        text+=define(name,BOOST+[(prefix+'curve',CURVE),('time',R)],coord(k(transform,*args(BOOST),app(v(prefix+'curve'),v('time'))),ROLES[3]),R)
    for name,source,target,transform,inverse in [('ek5q','old','new','ek5i','ek5j'),('ek5r','new','old','ek5j','ek5i')]:
        time=v('time');p=app(v(source+'curve'),time);mapped=k(transform,*args(BOOST),p);mappedtime=coord(mapped,ROLES[3])
        text+=define(name,MAPTRACK+[('time',R)],op('y',both(k('ba',time),app(v(source+'domain'),time)),both(valid(p),k('sca',coord(p,ROLES[3]),time),valid(mapped),app(v(target+'domain'),mappedtime),equalpoints(app(v(target+'curve'),mappedtime),mapped),equalpoints(k(inverse,*args(BOOST),mapped),p))))
    histories=[]
    for prefix,frame in [('old',first),('new',second)]:
        track=[v('matter'),frame,ctx,v(prefix+'domain'),v(prefix+'curve')]
        t=v('time');event=v('observed');p=app(v(prefix+'curve'),t)
        other,otherframe,transform=('new',second,'ek5i') if prefix=='old' else ('old',first,'ek5j')
        counterpart=k('seoa',v('matter'),otherframe,ctx,v(other+'domain'),v(other+'curve'),event,coord(k(transform,*args(BOOST),p),ROLES[3]))
        calibrated=q('f','time',R,q('f','observed','a',op('y',k('seoa',*track,event,t),both(k('eisqd',v('matter'),frame,event,lu,tu,p,ctx),counterpart))))
        histories.extend([k('seob',*track),calibrated])
    text+=define('ek5s',HISTORY,both(k('ek5n',*args(FRAME)),*histories,*(q('f','time',R,k(n,*args(MAPTRACK),v('time'))) for n in ('ek5q','ek5r'))))
    velocity=v('velocity');point=v('point');event=v('event');oldvelocity=[coord(velocity,a) for a in ROLES[:3]]
    text+=define('ek5t',EVENT,both(k('ek5s',*args(HISTORY)),k('ek5m',v('light'),speed,velocity),k('seoc',v('matter'),first,ctx,v('olddomain'),v('oldcurve'),event,point,*oldvelocity)))
    newpoint=k('ek5i',*args(BOOST),point);newvelocity=k('ek5l',v('light'),speed,velocity)
    text+=define('ek5u',EVENT,k('seoc',v('matter'),second,ctx,v('newdomain'),v('newcurve'),event,newpoint,*(coord(newvelocity,a) for a in ROLES[:3])))
    text+=define('ek5v',EVENT,op('y',k('ek5t',*args(EVENT)),k('ek5u',*args(EVENT))))
    time=coord(point,ROLES[3]);fixedspeed=k('eisxt');axial=point_expression([fixedspeed,ZERO,ZERO,ZERO])
    shared=args(EVENT,first=v('frame'),speed=fixedspeed,olddomain=v('domain'),oldcurve=v('curve'),velocity=axial)
    text+=define('ek5w',CURRENT,both(k('ek4p',*args(SETTING)),*(k('sca',coord(point,a),ZERO) for a in ROLES),*(k('sca',app(v(n),time),s) for (n,t),s in zip(PROFILES,(fixedspeed,ZERO,ZERO))),k('ek5t',*shared)))
    newpoint=k('ek5i',v('light'),fixedspeed,v('offset'),point)
    text+=define('ek5x',CURRENT,k('seoc',v('matter'),second,ctx,v('newdomain'),v('newcurve'),event,newpoint,ZERO,ZERO,ZERO))
    text+=define('ek5y',CURRENT,op('y',k('ek5w',*args(CURRENT)),k('ek5x',*args(CURRENT))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==417
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_electron_comoving_history_and_native_instant_rest_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electron-coordinate-normalization-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
