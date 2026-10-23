"""Bind the same frame, material axes and instrument placements to one motion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_frame_instruments import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,interval
from scripts.compose_moving_trip_geometry import zero
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-frame-instruments.noema';PARENT_BASIS='data/frame-instruments-basis-v1.json'
FULL='examples/v014/einstein-frame-motion.noema';CORE='examples/v014/frame-motion-core.noema'
BASIS='data/frame-motion-basis-v1.json';ANNOTATIONS='data/frame-motion-identifiers-v1.json'
TRACE=[('object','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a')]+[(n,R) for n in ('lower','upper')]+[(n,F) for n in ('x','y','z')]+[('speed',R)]
MEANINGS={
 'eivu':'指定対象の同じ基準系・単位・正の区間で、三代表位置関数の完全なse履歴と、下端での同じ位置から正のX速度で動くeitf履歴を結ぶ。全区間で同じ出来事・座標へ対応し、端点の値だけでは並進としない。時計の内部点は量化しない。',
 'eivv':'同じ物質軸又は物差しの全成員・全時刻の履歴へeipfとeigyを適用し、静止系raで既出zb7の正X並進と剛性を保持する。以前の棒の速度yb、初期静止長、加速過程を混ぜない。',
 'eivw':'同じ対象の代表位置をeismhから取得し、同じra・ta・rb・期間・zb7へeivuを適用する。原点又は時計の巨視的な配置を追い、時計表示の進みを位置の速度へ替えない。',
 'eivx':'sfjの初期設定から後の設定への対象保存を使い、同じ唯一の原点と異なる三軸の全役割を保持する。各軸は同じ原点から出るものとして引き継ぐが、初期静止のeivfを動く設定へ適用しない。時計群はsfjの両方向の範囲一致で保持する。',
 'eivy':'同じ対象を引き継いだ設定で、原点はeivw、三軸と物差しはeivv、配備した全時計は型・校正とeivwを満たす。物質軸と物差しの全点並進、時計の代表配置の並進を分け、どの計器も省略しない。',
 'eivz':'eivyの実物と位置履歴を、現行eiojの全固定配置・全時点の並進へ結び、同じ二系の三速度成分をzb7・零・零へ固定する。以前の相対速度候補zbiも同じ値とする。各系の時計時刻の一致や全時刻での平行軸配置の仮定を追加しない。',
}
LIMITS=[
 'u0044第一文の原点・軸・物差し・時計に共通する定速度の依存群。原刊897頁の文面と小文字k/v/x・大文字Kを照合した。設定指示の著者への帰属、後半の配置と対称性、括弧内の時刻呼称、段落全体の意味判断は未完。',
 'zb4からzb6へ同じ対象を引き継ぐ思考上の設定である。加速する物理的な方法、加速中の剛性、初期静止状態との長さ不変や時計の位相・同期を要求しない。',
 '時計はeismhの代表配置を追う。針・歯車の全物質点をeipfへ渡さない。軸と物差しは巨視的に理想化した物質体の全成員を追い、二端だけや一つの標識に縮めない。',
 '全位置履歴は既存se・eiad、全固定配置の範囲はeiojのeislbへ接続する。物理的な全対象・全時刻の完全性は有限標本から認定しない。原点と時計の同じ世界線への二履歴の結合により、候補の位置関数だけを信頼しない。',
 '静止系raの長さ単位taと時間単位rbで正X方向の速度zb7を用いる。三成分の値を明示し、旧棒設定のybと同一視しない。速度上限や光速の条件はこの文に加えない。',
 '後の軸の全時刻の平行性・配置の一意性と対称性による選択の正当化は別に接続する。初期のX支持直線一致、二原点一致、正方向一致を運動全区間へ追加しない。',
]

def definitions():
    shared=[v(n) for n in ('object','frame','context','lengthunit','timeunit','lower','upper')]
    text=define('eivu',TRACE,both(k('bg',v('lower'),v('upper')),k('sbg',v('speed')),k('eisdd',*[v(n) for n in ('frame','lengthunit','timeunit','context')]),k('se',*shared,*(v(a) for a in ('x','y','z'))),k('eitf',*shared,*(app(v(a),v('lower')) for a in ('x','y','z')),v('speed'),zero(),zero())))
    b=v('body');c=v('context');f=k('ra');bounds=interval(f,c)
    text+=define('eivv',[('body','a'),('context','d')],both(k('eipf',*history(b,f,c),k('zb7')),k('eigy',*history(b,f,c))))
    obj=v('object');traces=[k('eismh',obj,f,k('ta'),k('rb'),k(a),c) for a in ('yn','yo','yp')]
    text+=define('eivw',[('object','a'),('context','d')],k('eivu',obj,f,c,k('ta'),k('rb'),*bounds,*traces,k('zb7')))
    moving=k('zbm');origin=k('zbn',moving,k('zb4'));line=lambda a:k('zbo',moving,k(a),k('zb4'))
    choices=[both(op('e',v('role'),k(a)),op('e',v('line'),line(a))) for a in ('yn','yo','yp')]
    exact=q('f','line','a',q('f','role','a',op('z',k('zbw',moving,v('line'),v('role'),c),op('x',choices[0],op('x',*choices[1:])))))
    unique=q('f','point','a',op('y',k('zbv',moving,v('point'),c),op('e',v('point'),origin)))
    text+=define('eivx',[('context','d')],both(k('sfj',c),exact,unique,*(op('u',op('e',line(a),line(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp'))),*(k('zbr',line(a),origin,c) for a in ('yn','yo','yp'))))
    clocks=q('f','clock','a',op('y',k('zbz',moving,v('clock'),c),both(k('ca',v('clock')),k('eisdf',v('clock'),c),k('eivw',v('clock'),c))))
    text+=define('eivy',[('context','d')],both(k('eivx',c),k('eivw',origin,c),*(k('eivv',line(a),c) for a in ('yn','yo','yp')),k('xc',k('zby',moving,c)),k('eivv',k('zby',moving,c),c),clocks))
    frame=[f,moving,k('ta'),k('rb')]
    velocities=[k('eislc',*frame,k(a),c) for a in ('yn','yo','yp')]
    legacy=k('zbi',*frame,c)
    text+=define('eivz',[('context','d')],both(k('eivy',c),k('eioj',*frame,c),k('sbg',k('zb7')),*(k('ba',x) for x in [*velocities,legacy]),*(k('sca',a,b) for a,b in zip(velocities,[k('zb7'),zero(),zero()])),k('sca',legacy,k('zb7'))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==268;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='complete_frame_translation_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/frame-instruments-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
