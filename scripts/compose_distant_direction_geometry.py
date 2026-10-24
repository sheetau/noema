"""Construct a receding source direction, a spatial angle and the printed factor."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_cycle_frequency import ROOT,read,SETTING as PRIOR,DOPPLER
from scripts.compose_field_equations import POINT
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-wave-cycle-frequency.noema';PARENT_BASIS='data/wave-cycle-frequency-basis-v1.json'
FULL='examples/v014/einstein-distant-direction-geometry.noema';CORE='examples/v014/distant-direction-geometry-core.noema'
BASIS='data/distant-direction-geometry-basis-v1.json';ANNOTATIONS='data/distant-direction-geometry-identifiers-v1.json'
DIRECTION=[(n,R) for n in ('ax','ay','az')];POSITION=[(n,R) for n in ('px','py','pz')]
CLOSE=DIRECTION+POSITION+[('distance',R),('epsilon',R)]
TAIL=DIRECTION+POSITION+[('epsilon',R),('cutoff',R)]
VECTOR=DIRECTION+[(n,R) for n in ('ux','uy','uz','speed','anglecos','anglesin')]
ANGLE=VECTOR+[(n,R) for n in ('ratio','principal','pi','angle')]
AXIAL=DIRECTION+[(n,R) for n in ('speed','anglecos','anglesin')]
AXIAL_ANGLE=AXIAL+[(n,R) for n in ('ratio','principal','pi','angle')]
PRINTED=[(n,R) for n in ('light','speed','frequency','anglecos')]
COMBINED=DOPPLER+[(n,R) for n in ('anglecos','anglesin','ratio','principal','pi','angle')]
ADDITIONS=[(n,R) for n in ('anglecos','anglesin','ratio','principal','angle')]
SETTING=PRIOR+ADDITIONS
WITNESSES=[(n,t) for n,t in SETTING if n not in ('frame','scope','context','light')]
MEANINGS={
 'ekdg':'同じ方向三成分nと距離パラメータRから−R*nの空間点を構成する。源から有限位置の観測者へ向く方向が+nとなる配置である。Rが正か、nが単位か、物理的な源がその位置にあるかは利用条件で指定する。',
 'ekdh':'同じ有限位置pからekdgの源位置を引いたp+R*nという三変位。観測者から源へ向く逆ベクトルや別の観測点を代入しない。',
 'ekdi':'各距離Rでekdgの三空間成分を固定し、第四成分だけを同じ時刻へ等置した数学的な四座標曲線。時刻を増やしても源位置は変わらないが、物理的な源の静止の帰属は別途必要である。',
 'ekdj':'単位n、有限位置p、正のRとepsilonについて、d=p+R*nの正の長さLを使い、各成分の|d_i−L*n_i|<epsilon*Lを要求する。d/Lがnへ成分ごとに近いことを零除算なしで表し、源と観測者の衝突点L=0を拒否する。',
 'ekdk':'単位nと有限位置pについて、正のepsilonと|p|より大きい正のcutoffを固定し、全ての有効なR>cutoffにekdjを要求する。選んだ遠距離一例や成功する距離だけへ量化範囲を縮めない。',
 'ekdl':'同じ単位nと有限位置pに対し、任意の正のepsilonごとにekdkを満たすcutoffが存在するという遠距離極限。cutoffはepsilonに依存してよいが、その後のRごとに選び直さない。',
 'ekdm':'同じ単位nについて全ての有効な有限三位置pでekdlを要求する。各固定位置での方向極限であり、Rと同時に無限遠へ移動する観測者や全空間での一様収束を追加しない。',
 'ekdn':'同じ単位方向nと非零三次元速度uについて、speed=|u|、speed*anglecos=n・u、anglecos²+anglesin²=1及びanglesin>=0を要求する。向きなし角の上半円成分を指定し、零速度には任意の角を与えない。',
 'ekdo':'ekdnの同じ三次元の方向と速度から得る余弦・非負正弦を、既存ejotの象限付き実数角へ接続する。比・主値・pi・角度を共有し、反対方向では+pi、直角ではpi/2を含む0からpiの角とする。',
 'ekdp':'正のspeedについて速度ベクトルを(speed,0,0)とし、同じ単位方向との角をekdnへ結ぶ。この標準軸配置ではanglecos=axとなる。負の符号付き速度を正の速さと取り違えず、横方向成分や反対向きを保存する。',
 'ekdq':'ekdpと同じ正の標準軸速度・方向の角を、比・主値・piを通じた実数測度へ結ぶ。単に角の余弦の数値だけを角度そのものにしない。',
 'ekdr':'原刊M0333のν*(1−cosφ*v/V)/sqrt(1−(v/V)^2)を既存の実数演算で構成する。正の平方根とその逆数を使う。値の構成だけでは許容速度、物理的周期数又は角度を保証しない。',
 'ekds':'同じ一周期の旧新の周期数と位相率を結ぶekddに、同じnと正のspeedの実数角ekdq、及びν′が印刷された平方根形式ekdrに等しいことを合わせる。cosφを別の波の方向成分へ交換しない。',
 'ekdt':'先行ekdeの同じ47設定役割に、同じ方向の遠距離極限ekdmと5つの角関連値を加え、同じpiと位相率・周期数のekdsを要求する依存条件。先行の有限だが遠い物理源と数学的な遠距離配置族の同一視はまだ行わない。',
 'ekdu':'同じK、V、第七節、評価状況を固定し、先行43証人と角関連5値を一つの48証人へ束縛したekdtの内容。物理的な理想化の帰属や原文の著者提示にはまだ接続しない。',
}
LIMITS=[
 'u0188–u0189の無限遠の読み・角度・表示式に必要な数学的依存群。既存370主張と全単位判断を保持する。光源に静止する系、実際の観測者の速度と受信周期、有限の源からこの理想化への同じ物理的役割の対応、folgt及びコロンによる導入は未接続であり、原文全体を完成済みに数えない。',
 '無限遠は実数座標値infinityを追加するのでなく、源配置−R*nでRを大きくしたとき、固定された任意の有限位置からの源―観測者方向がnに近づく極限として準備する。先行ekaxの単一の有限な遠方源とは別の数学的構成である。物理的な同一源の適用は次の統合で明示する。',
 '源の配置を点として書くのは方向の極限を指定する幾何学的な代表族であり、実際の光源が全時刻に点状である、単一の出来事だけで発光するという主張を追加しない。ekdiの静止曲線もまだ物理的な支持範囲や源の履歴への帰属ではない。',
 '源から観測者への向きを+nとする。正の速度を+x軸へ取る標準配置ではcosφ=aとなる。逆の視線向き又は負の符号付きvを同じ式へ混ぜない。零速度ではベクトル間角を定義せず、ν′=νへの連続的な拡張は別に扱う。',
 '三次元内積と正の速度の大きさから角の上半円成分を決め、既存の積分によるpiと逆正接の象限処理で実数角へ結ぶ。角度と余弦を同一視せず、直角と反対向きを排除しない。',
 '同じ先行波の数値設定へ式を結ぶが、成分誤差上限や数式の一致だけで光源と観測者の物理的周期数を同定しない。前段の一周期2*piと近似誤差・十分性を保持する。',
 '極限の全実数の量化を有限標本へ置き換えない。診断では有理数の正確な距離・成分及び有限の結合境界を用い、piや逆正接の有理数代用を真の値と称さない。未定義の平方根・未知の入力を成功例で補わない。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b')
    valid=lambda ns:[k('ba',v(n)) for n,t in ns]
    positive=lambda x:both(k('ba',x),k('bg',zero,x))
    n=args(DIRECTION);p=args(POSITION);distance=v('distance');eps=v('epsilon');cutoff=v('cutoff')
    unit=both(*valid(DIRECTION),k('sca',k('seag',*n),one))
    source=[k('bf',zero,k('shv',distance,x)) for x in n]
    text=define('ekdg',DIRECTION+[('distance',R)],k('ekbe',*source),POINT)
    displacement=[k('bf',x,app(k('ekdg',*n,distance),k(axis))) for x,axis in zip(p,('yn','yo','yp'))]
    text+=define('ekdh',DIRECTION+[('distance',R)]+POSITION,k('ekbe',*displacement),POINT)
    curve='i[time '+R+'][i[axis a]['+k('szi',op('e',v('axis'),k('zc7')),v('time'),app(k('ekdg',*n,distance),v('axis')))+']]'
    text+=define('ekdi',DIRECTION+[('distance',R)],curve,'h['+R+'] '+POINT)
    d=[app(k('ekdh',*n,distance,*p),k(a)) for a in ('yn','yo','yp')]
    length=k('sky',k('seag',*d));observerlength=k('sky',k('seag',*p))
    errors=[k('bg',k('shu',k('bf',x,k('shv',length,a))),k('shv',eps,length)) for x,a in zip(d,n)]
    text+=define('ekdj',CLOSE,both(unit,*valid(POSITION),positive(distance),positive(eps),positive(length),*errors))
    beyond=both(k('ba',distance),k('bg',cutoff,distance))
    text+=define('ekdk',TAIL,both(unit,*valid(POSITION),positive(eps),positive(cutoff),k('bg',observerlength,cutoff),q('f','distance',R,op('y',beyond,k('ekdj',*args(CLOSE))))))
    text+=define('ekdl',DIRECTION+POSITION,both(unit,*valid(POSITION),q('f','epsilon',R,op('y',positive(eps),q('g','cutoff',R,k('ekdk',*args(TAIL)))))))
    whole=op('y',both(*valid(POSITION)),k('ekdl',*n,*p))
    for name,t in reversed(POSITION):whole=q('f',name,t,whole)
    text+=define('ekdm',DIRECTION,both(unit,whole))
    u=[v(x) for x in ('ux','uy','uz')];speed=v('speed');co=v('anglecos');si=v('anglesin')
    text+=define('ekdn',VECTOR,both(unit,*valid(VECTOR[len(DIRECTION):]),positive(speed),k('seal',*u,speed),k('s2c',co,si),k('bc',zero,si),k('sca',k('shv',speed,co),k('seah',*n,*u))))
    circle=[co,si,*[v(x) for x in ('ratio','principal','pi','angle')]]
    text+=define('ekdo',ANGLE,both(k('ekdn',*args(VECTOR)),k('ejot',*circle)))
    text+=define('ekdp',AXIAL,k('ekdn',*n,speed,zero,zero,speed,co,si))
    text+=define('ekdq',AXIAL_ANGLE,both(k('ekdp',*args(AXIAL)),k('ejot',*circle)))
    V=v('light');ratio=k('shv',speed,k('sjd',V));numerator=k('bf',one,k('shv',co,ratio));denominator=k('sky',k('bf',one,k('shv',ratio,ratio)))
    text+=define('ekdr',PRINTED,k('shv',v('frequency'),k('shv',numerator,k('sjd',denominator))),R)
    text+=define('ekds',COMBINED,both(k('ekdd',*args(DOPPLER)),k('ekdq',*args(AXIAL_ANGLE)),k('sca',v('newfrequency'),k('ekdr',*args(PRINTED)))))
    overrides={'speed':k('zb7'),'newrate':k('sdn2',V,k('zb7'),v('rate'),v('ax'))}
    text+=define('ekdt',SETTING,both(k('ekde',*args(PRIOR)),k('ekdm',*n),k('ekds',*[overrides.get(name,v(name)) for name,t in COMBINED])))
    fixed={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')}
    text+=content('ekdu',bind(WITNESSES,k('ekdt',*[fixed.get(name,v(name)) for name,t in SETTING])))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==370
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='asymptotic_source_direction_and_spatial_angle_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/wave-cycle-frequency-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
