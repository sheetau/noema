"""Attribute the persistent enclosure of one advected radiation portion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_ball_transport import ROOT,read,TOTAL,FRAME,PLANE,OLD,SCALAR,COORDS,TAU,POINT
from scripts.compose_equal_volume_supposition import FIXED,VARIABLES
from scripts.compose_field_equations import REGION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-moving-ball-transport.noema';PARENT_BASIS='data/moving-ball-transport-basis-v1.json'
FULL='examples/v014/einstein-same-light-portion.noema';CORE='examples/v014/same-light-portion-core.noema'
BASIS='data/same-light-portion-basis-v1.json';ANNOTATIONS='data/same-light-portion-identifiers-v1.json';INDEX=388
DIRECTION=[(n,R) for n in ('light','ax','ay','az')]
TRANSPORT=[('region',REGION),('densityfield',TAU)]+DIRECTION
PRIMITIVES={
 'eistp':([], 'u0203[422,597)–u0204=M0355–u0205[0,23)の、波面法線の方向余弦と移動球面を指定し、表面要素をエネルギーが通らないと述べる箇所。'),
 'eistq':([], 'u0205[23,107)のwir können daher sagenに続く、同じ球面が永久に同じ光の集合を囲むという記述の仕方とその提示箇所。具体的内容は閉じた合成記述へ結ぶ。'),
 'eistr':([], 'u0203[422,597)–u0204–u0205[0,107)のセミコロンを挟む一続きの文全体。続くエネルギーの問いとは分ける。'),
}
MEANINGS={
 'eknr':'同じ光速度と波面方向に沿う並進について、現在位置からV*n*timeを引いた初期位置の三成分を返す。時刻成分を持たない位置ベクトルで、初期時刻の評価には別に零を渡す。',
 'ekns':'同じ領域履歴と瞬間密度から、その領域内部では密度を保持し外部では零とする部分密度場を構成する。正弦の節を領域の穴にせず、幾何学的な所属と密度値を別に保持する。',
 'eknt':'同じ初期時刻零の領域と部分密度を、現在点の初期位置eknrへ適用する輸送密度場。各時刻で都合のよい別の初期領域・初期密度へ選び直さない。',
 'eknu':'同じ現在点と時刻で、前進・逆向き並進がそれぞれ元の三位置成分へ戻ること、現在領域の所属が逆向きにたどる同じ初期領域の所属と一致すること、非負の現在部分密度が同じ初期部分から輸送したekntに等しいことを結ぶ。総量や領域の大きさだけの一致ではない。',
 'eknv':'正のVと単位方向について、全有効四座標でeknuを要求する。初期部分と現在部分の一対一な点の対応とその密度を全時刻で保持する連続体輸送の条件。任意の観測不能な粒子の交換履歴の同一性は含めない。',
 'eknw':'同じ物理的な波・過程・単位・部分を持つeknoの球面無流出入と内部持続へ、同じ閉内部eklwと瞬間密度ekkyの初期部分輸送eknvを加える。same Lichtkomplexを、この初期部分の輸送で同定する連続体モデルの読みとして使う。',
 'eknx':'前二文と同じ70役割から、同じK側・第八節・部分・半径・波の係数をeknwへ接続する。新系の別の対象を囲むという記述へ替えない。',
 'ekny':'同じK,V,波範囲,部分zvaa,状況を固定し、残る65役割でeknpの全時刻モデルを採るなら、同じ平面波と球面の局所無流出入eknkが成立するという内容。Sind ... so ...の同じ設定の条件を保持する。',
 'eknz':'同じ65役割と同じeknpの下で、球面の無流出入・内部輸送・同じ初期部分の一対一な輸送eknxを述べる内容。dauerndは全実時刻であり、離散的な標本時刻へ縮めない。',
 'ekn2':'同じ第八節で、無流出入の内容eknyを、同じ初期部分が持続して囲まれるeknzという記述の仕方eistqで述べることができるという既存eisqoの内容。著者がこの可能性を述べることは別に帰属し、論理的な必然や処理系の証明済みへ強めない。',
 'ekn3':'著者が第一節の無流出入eknyと、第二節の記述可能性ekn2を述べる。udが前者を根拠として後者を提示する向きを、eisraが同じ球面と内容を受ける後方参照を保持する。実際の発話能力、政治的許可又は全読者の同意を付け加えない。',
 'ekn4':'球面の無流出入と同じ初期部分の持続を述べ得るという帰結提示ekn3をまとめるメッセージ。',
 'ekn5':'一続きの文全体eistrを同じ著者・論説へ帰属し、前の体積否定eistoの後に置く。',
}
LIMITS=[
 '原刊913頁でu0203[422,597)–u0204–u0205[0,107)を一文として通読した。本文はu0203側148文字とu0205側94文字、合計242非空白文字。M0354=a,b,cとM0355の球面式を含む。次のWir fragenからの問いは含めない。',
 '同じ光の集合を、初期球の内部の連続的な放射部分を同じV*nの流れで運んだものとして同定する明示した読み。各初期位置への一対一な対応と点ごとの部分密度を保持し、同じ体積や総エネルギー値だけがある別の分布とは区別する。光子や原子状の個体の同一性を追加しない。',
 'この連続体モデルでは同じ初期データと流れによって部分系の同一性を指定する。現実に観測不能な生成・消滅・置換がありながら全ての場と流が同じになる別の微視的履歴まで排除したとは主張しない。その追加存在論は原文から要求しない。',
 '先行の局所近似は保持し、球の全時刻の領域履歴で流・密度の理想モデルを採ることをeknpで明示する。原文dauerndを有限時間のモデルに無言で弱めず、現実の遠方光源の局所近似が永久に妥当だと証明したことにもならない。',
 '原文のkeine Energie hindurchは単一の平面波連続体における局所相対流の不存在と読む。正味総量の相殺だけではない。波面法線と球面の外向き法線、瞬間密度と先行の位相平均、動く幾何学的境界と慣性観測者を区別する。',
 'wir können daher sagenは、前節を根拠に同じ内容をこのように記述できるという著者の提示としてeisqo・uh・udへ結ぶ。must followのzcや明白性zdgへ強めない。wirは論説の著者による議論の提示として読み、実際の共同発話者や全読者の同意を導入しない。',
 'diese Flächeは直前の球面を受ける。両内容は同じ半径・方向・光速度・同じ部分を共有し、eisraに両箇所と閉じた内容を渡す。der gleiche Lichtkomplexの後続の新系質問は次に同じ部分へ結ぶ。',
 '初期時刻零の選択は原文の中心V*n*tによる座標規約に従う。球の正の半径と、前文の比を扱う非零振幅・正の旧総量は引き継ぎ、空部分だけの保存で本文を満たさない。密度の節は幾何学的な占有範囲の穴とはしない。',
 '有限の切断診断と束縛検査は全実数域の物理的存在、一般輸送定理、原文との意味同義性の自動証明ではない。前の第三文について採った強い否定の読みとその等体積反例も変更しない。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);z=k('bb','n p a b');one=k('bb','n p b b');mul=lambda a,b:k('shv',a,b)
    coords=args(COORDS);V=v('light');ns=[v(n) for n in ('ax','ay','az')];xyz=[v(n) for n in ('x','y','z')];time=v('time');axes=('yn','yo','yp')
    text+=define('eknr',DIRECTION+COORDS,k('ekbe',*[k('bf',x,mul(mul(V,n),time)) for x,n in zip(xyz,ns)]),POINT)
    mask=k('szi',app(v('region'),*coords),app(v('densityfield'),*coords),z)
    text+=define('ekns',TRANSPORT[:2],'i['+' '.join(n+' '+t for n,t in COORDS)+']['+mask+']',TAU)
    back=k('eknr',*args(DIRECTION),*coords);initial=[app(back,k(axis)) for axis in axes]+[z]
    masked=k('ekns',v('region'),v('densityfield'));transported=app(masked,*initial)
    text+=define('eknt',TRANSPORT,'i['+' '.join(n+' '+t for n,t in COORDS)+']['+transported+']',TAU)
    forward=k('segb',*args(DIRECTION),*initial[:3],time)
    firstforward=k('segb',*args(DIRECTION),*xyz,time);inverse=k('eknr',*args(DIRECTION),*[app(firstforward,k(axis)) for axis in axes],time)
    actual=app(masked,*coords);expected=app(k('eknt',*args(TRANSPORT)),*coords)
    text+=define('eknu',TRANSPORT+COORDS,both(*(k('sca',app(point,k(axis)),x) for point in (forward,inverse) for axis,x in zip(axes,xyz)),op('z',app(v('region'),*coords),app(v('region'),*initial)),k('ba',actual),k('ba',expected),k('bc',z,actual),k('sca',actual,expected)))
    valid=both(*(k('ba',x) for x in coords))
    text+=define('eknv',TRANSPORT,both(*(k('ba',x) for x in args(DIRECTION)),k('bg',z,V),k('sca',k('seag',*ns),one),quantified('f',COORDS,op('y',valid,k('eknu',*args(TRANSPORT),*coords)))))
    actual={n:v(n) for n,t in FRAME}|dict(phase=k('ekbf',V,v('rate'),*ns))
    density=k('ekky',*[actual[n] for n,t in SCALAR]);region=k('eklw',*args(OLD))
    text+=define('eknw',FRAME,both(k('ekno',*args(FRAME)),k('eknv',region,density,*args(DIRECTION))))
    actual={n:v(n) for n,t in TOTAL}|dict(scope=k('eistk'))
    text+=define('eknx',TOTAL,k('eknw',*[actual[n] for n,t in FRAME]))
    total=[FIXED.get(n,v(n)) for n,t in TOTAL];plane=[FIXED.get(n,v(n)) for n,t in PLANE]
    text+=content('ekny',quantified('f',VARIABLES,op('y',k('eknp',*total),k('eknk',*plane))))
    text+=content('eknz',quantified('f',VARIABLES,op('y',k('eknp',*total),k('eknx',*total))))
    p=v('point');author=k('rd');scope=k('eistk');first=k('eistp');second=k('eistq')
    text+=content('ekn2',k('eisqo',second,quote('ekny'),quote('eknz'),scope,p))
    nodes='i[node a]['+op('e',v('node'),first)+']'
    text+=content('ekn3',both(k('uh',first,author,quote('ekny'),scope,p),k('uh',second,author,quote('ekn2'),scope,p),k('ud',author,nodes,second,p),k('eisra',second,author,k('eirf'),first,quote('ekny'),quote('eknz'),scope,p)))
    text+='d ekn4[] f[j s[k ekn3[]]].\n'
    text+=define('ekn5',[],both(k('eir3',k('eistr'),author,k('eirf'),quote('ekn4'),k('ri')),k('ue',k('eisto'),k('eistr'),k('ri')),op('u',op('e',k('eisto'),k('eistr'))),op('u',op('e',first,second))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekn5',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_initial_radiation_portion_enclosure_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-ball-transport-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
