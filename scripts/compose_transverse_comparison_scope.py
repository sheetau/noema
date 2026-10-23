"""Compose intrinsic rod matching, complete velocity scope and signed comparisons."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_measured_length import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transverse-measured-length.noema';PARENT_BASIS='data/transverse-measured-length-basis-v1.json'
FULL='examples/v014/einstein-transverse-comparison-scope.noema';CORE='examples/v014/transverse-comparison-scope-core.noema'
BASIS='data/transverse-comparison-scope-basis-v1.json';ANNOTATIONS='data/transverse-comparison-scope-identifiers-v1.json'
VECTOR=[(n,R) for n in ('vx','vy','vz')]
MEANINGS={
 'ejc6':'同じ物体・固有系・単位について、二設定の完全な物質点履歴と計量、正の時間幅を保持し、全物質点の所属を双方向に一致させる。両設定の各自の開始時刻で、同じ全成員対の有効な位置と距離二乗を一致させる。位置・向き・時刻原点は変えられるが、内部の形状や材料の別集団への交換を同じ棒としない。利用側では両設定の全点静止・剛性を別に要求する。',
 'ejc7':'三つの実成分の二乗和。速度の大きさの二乗として、正負の向きと座標方向に依存せず比較できる。値の有効性と非零・光速未満の範囲は利用側で要求する。',
 'ejda':'現在の横棒の固有静止配置を基準に、同じ全物質点・固有形状・固有長・二端・尺度を持つ一つの比較設定と正の測定長。測定系Kと固有系kの全配置の並進eioj、同じ速度三成分の全物質点の横運動・現在測定ejc5、固有形状の対応ejc6を結ぶ。速さは非零で光速未満。測定長の基準値との一致やφの対称性は候補条件にしない。',
 'ejdb':'ejdaの設定の全体並進の速度三成分を、指定した三実値へそれぞれ一致させる。速度の大きさだけで符号・方向の取り違えを通さない。',
 'ejdc':'有効な三実成分の二乗和が0より大きく光速二乗より小さい全ベクトルについて、それを速度とするejdbの設定と正の現在測定長が存在する。比較用の理想化した設定群を全方向に開き、反転二例や既観測の有限標本へ限定しない。',
 'ejdd':'同じ対象の二つの適格な比較設定とそれぞれの測定長を保持し、速度三成分の二乗和が等しいという同速条件。長さの一致をこの比較の前提へ含めない。',
 'ejde':'現在の正速度設定も適格であり、全速度ベクトルの設定存在ejdcを保持した上で、全設定と全測定長についてejddの同速条件なら長さが等しいとする方向・向きへの不変性。現実に全設定を実験したことや物理原理からの証明ではなく、後続で著者が採用する内容。',
 'ejdf':'指定した符号付き速度について、同じ端の全K時刻の現在二系記録ejciを保持し、全対応記録ejcgへsrwの四変換とkでの(0,proper,0)、sryのK端点式を課す。現在の正規化後の同じφを指定速度で評価し、負速度へ正速度の値を流用しない。',
 'ejdg':'同じ棒の適格設定ejdaを速度(speed,0,0)へ固定し、kの同じη軸全区間、全時刻の両端の現在式ejdfと、正の測定長=l/φ(speed)を結ぶ。正負のどちらも同じ規則へ渡し、符号付き商が正の距離となる向きの読みを保つ。',
 'ejdh':'現在のzb6と異なる逆向き設定zg2について、同じ棒・固有形状・長さ尺度のejdgをvと−vで満たすことを二つの測定長へ結ぶ。K/kを交換せず、設定の速度の向きだけを反転する。',
 'ejdi':'同じ正のlと同じφの非零の正負速度値について、l/φ(v)=l/φ(−v)という二つの分数の等値内容。測定長の名前の等値だけにせず、M0186の両方の商を実際に合成する。',
}
LIMITS=[
 'u0101–u0104の同じ棒の比較範囲と正負速度の測定を構成する依存群。著者の理由・明白さ・測定長による物理的意味・結論・oderの提示、本文統合と通読判断はまだ追加しない。既存318主張を保持する。',
 '同じ棒は同じ物質点と固有系の全点対距離が一致するという剛体の読み。各設定で静止と剛性を保つので比較には各自の開始時刻を使える。位置・向き・時刻原点の一致や、異なる系での同時性の一致を加えない。固有長lだけを合わせて内部の形状・構成点を変えることを許さない。',
 '比較範囲はejdaを満たす全設定と全正の測定長で構成し、等長という結論やφの対称性を候補選択に使わない。同じK/k・単位・棒・二端は固定するが、設定ごとの位置と向きは変えられる。速度は全系のeiojと全点のejc3に共通のeislc三成分を渡す。',
 '方向一般を表すため、0<|v⃗|<Vの任意の三成分に適格設定が存在する比較用の理想化をejdcで明示する。測定の実行履歴や加速して各設定を実現できるという主張ではない。止まった棒・光速以上は先行する移動系設定の範囲外とし、全方向の表現を正負反転二例へ縮めない。',
 '同速は三成分の二乗和の等値であり、符号付き第一成分の等値ではない。不変性ejdeはこの範囲への著者の採用内容として後で帰属する。設定の存在や形状の保存から測定長の不変性が機械的に証明されたと扱わない。',
 '正負の比較は同じKから見た同じk・同じ棒の二設定。逆向きでは同じφを−vへ適用し、元の正速度専用ejcjを使い回さない。正の測定長とl/φの等値が選ぶ符号の条件は前段ejc2と同様に明示し、絶対距離から正値性を自動導出しない。',
 '固有形状、方向一般、正負設定、純粋な分数等値を分けて局所検査する。全実数と全実関数を有限標本へ置換せず、未知入力を補わない。有限例と依存関係の保持を原文の全文判断へ変換しない。',
]

def velocity(ctx):return [k('eislc',k('ra'),k('zbm'),k('ta'),k('rb'),k(role),ctx) for role in ('yn','yo','yp')]

def definitions():
    body=v('body');frame=v('frame');first=v('first');second=v('second');ctx=v('context');length=v('length');zero=k('bb','n p a b')
    population=q('f','point','a',op('z',k('eirh',body,v('point'),first),k('eirh',body,v('point'),second)))
    ts=[interval(frame,s)[0] for s in (first,second)];families=[coords(body,frame,s) for s in (first,second)]
    valid=[k('ba',app(app(fn,v(p)),t)) for t,fs in zip(ts,families) for p in ('left','right') for fn in fs]
    distances=[k('eigw',v('left'),v('right'),t,*fs) for t,fs in zip(ts,families)]
    matching=q('f','left','a',q('f','right','a',op('y',both(*(k('eirh',body,v(p),first) for p in ('left','right'))),both(*valid,k('sca',*distances)))))
    bases=[k('eiad',*history(body,frame,s)) for s in (first,second)]+[k('eisdd',frame,k('ta'),k('rb'),s) for s in (first,second)]+[k('bg',*interval(frame,s)) for s in (first,second)]
    text=define('ejc6',[('body','a'),('frame','a'),('first','d'),('second','d')],both(*bases,population,matching))
    terms=[k('shv',v(n),v(n)) for n,_ in VECTOR]
    text+=define('ejc7',VECTOR,k('bd',terms[0],k('bd',terms[1],terms[2])),R)
    rod=k('zgu');ends=[k('zgv'),k('zgw')];proper=k('zgz');anchor=k('zb6');K=k('ra');ks=k('zbm');vel=velocity(ctx);size=k('ejc7',*vel)
    text+=define('ejda',[('context','d'),('length',R)],both(k('ejcc',rod,*ends,anchor,proper),k('ejc5',rod,*ends,K,ctx,ks,proper,*vel,length),k('eioj',K,ks,k('ta'),k('rb'),ctx),k('ejc6',rod,ks,anchor,ctx),k('sbg',k('tc')),k('sbg',size),k('bg',size,k('shv',k('tc'),k('tc')))))
    text+=define('ejdb',[('context','d')]+VECTOR+[('length',R)],both(k('ejda',ctx,length),*(k('sca',a,v(n)) for a,(n,_) in zip(vel,VECTOR))))
    vector=[v(n) for n,_ in VECTOR];size=k('ejc7',*vector)
    exists=q('g','context','d',q('g','length',R,k('ejdb',ctx,*vector,length)))
    allvectors=op('y',both(*(k('ba',x) for x in vector),k('sbg',size),k('bg',size,k('shv',k('tc'),k('tc')))),exists)
    for n,t in reversed(VECTOR):allvectors=q('f',n,t,allvectors)
    text+=define('ejdc',[],both(k('sbg',k('tc')),allvectors))
    text+=define('ejdd',[('first','d'),('firstlength',R),('second','d'),('secondlength',R)],both(k('ejda',first,v('firstlength')),k('ejda',second,v('secondlength')),k('sca',k('ejc7',*velocity(first)),k('ejc7',*velocity(second)))))
    conclusion=op('y',k('ejdd',first,v('firstlength'),second,v('secondlength')),k('sca',v('firstlength'),v('secondlength')))
    for n,t in reversed([('first','d'),('firstlength',R),('second','d'),('secondlength',R)]):conclusion=q('f',n,t,conclusion)
    text+=define('ejde',[],both(q('g','length',R,k('ejda',anchor,length)),k('ejdc'),conclusion))
    endpoint=v('endpoint');event=v('event');rest=v('rest');moving=v('moving');speed=v('speed')
    comparison=op('y',k('ejcg',body,endpoint,event,rest,moving,ctx),both(k('srw',rest,moving,speed,v('proper')),k('sry',rest,speed,v('proper'),app(k('spc'),speed))))
    for n in reversed(('event','rest','moving')):comparison=q('f',n,'a',comparison)
    text+=define('ejdf',[('body','a'),('endpoint','a'),('proper',R),('speed',R),('context','d')],both(k('ejci',body,endpoint,ctx),comparison))
    text+=define('ejdg',[('context','d'),('speed',R),('length',R)],both(k('ejdb',ctx,speed,zero,zero,length),k('ejcc',rod,*ends,ctx,proper),k('ejdf',rod,ends[0],zero,speed,ctx),k('ejdf',rod,ends[1],proper,speed,ctx),k('sca',length,k('srx',proper,app(k('spc'),speed)))))
    speed=k('zb7');reverse=k('bf',zero,speed);other=k('zg2')
    text+=define('ejdh',[('forward',R),('backward',R)],both(op('u',op('e',anchor,other)),k('ejdg',anchor,speed,v('forward')),k('ejdg',other,reverse,v('backward'))))
    plus=app(k('spc'),speed);minus=app(k('spc'),reverse)
    text+=content('ejdi',both(k('sbg',proper),*(k('ba',x) for x in (plus,minus)),*(op('u',k('sca',x,zero)) for x in (plus,minus)),k('sca',k('srx',proper,plus),k('srx',proper,minus))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==318;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_intrinsic_rod_complete_direction_scope_and_signed_comparisons',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/transverse-measured-length-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
