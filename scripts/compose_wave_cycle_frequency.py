"""Connect angular phase rate, least periods and cycle frequency on one wave."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_transform_application import ROOT,read,FAMILY
from scripts.compose_field_equations import TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_electromotive_wording import bind
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-wave-transform-application.noema';PARENT_BASIS='data/wave-transform-application-basis-v1.json'
FULL='examples/v014/einstein-wave-cycle-frequency.noema';CORE='examples/v014/wave-cycle-frequency-core.noema'
BASIS='data/wave-cycle-frequency-basis-v1.json';ANNOTATIONS='data/wave-cycle-frequency-identifiers-v1.json'
PAIR=[('first',F),('second',F)]
PERIOD=PAIR+[('period',R)]
HARMONIC=[('sine',F),('cosine',F)]+[(n,R) for n in ('pi','cycle')]
FREQUENCY=[(n,R) for n in ('cycle','rate','period','frequency')]
TIMEWAVE=HARMONIC+[(n,R) for n in ('rate','offset','period','frequency')]
TRACE=[('phase',TAU)]+[(n,F) for n in ('x','y','z')]
TRACE_POINT=TRACE+[(n,R) for n in ('time','rate','offset')]
TRACE_INTERVAL=TRACE+[(n,R) for n in ('lower','upper','rate','offset')]
DOPPLER=[(n,R) for n in ('cycle','light','speed','ax','ay','az','rate','newrate','oldperiod','newperiod','frequency','newfrequency')]
ADDITIONS=[(n,R) for n in ('pi','cycle','oldperiod','newperiod','frequency','newfrequency')]
SETTING=FAMILY+ADDITIONS
WITNESSES=[(n,t) for n,t in SETTING if n not in ('frame','scope','context','light')]
MEANINGS={
 'ekcy':'指定した二つの実数値関数が、同じ有効な位相pointとpoint+periodでそれぞれ一致する点条件。二関数の値を相互に交換せず、位相が零の一点だけの一致へ縮めない。',
 'ekcz':'正の有効なperiodについて、二関数が全ての有効な実数pointでekcyを満たす共通周期条件。有限標本の反復や一箇所の零点間隔を周期の定義にしない。',
 'ekc2':'二関数の共通周期periodが正であり、それより小さい正の共通周期が存在しないという最小正周期。周期の整数倍、定数関数の任意の間隔、半周期の符号反転を一周期にしない。',
 'ekc3':'既存sdv2の正規化した正弦・余弦、積分で定めるsediのpi、cycle=2*pi及び同じ二関数の最小正周期を結ぶ。2*piを任意の換算係数にせず、この構成自体を周期定理の機械的証明とはしない。',
 'ekc4':'同じrateとoffsetから、timeに対する実数位相rate*time+offsetを構成する。offsetとtimeを交換せず、率の逆数を位相率にしない。引数妥当性は利用条件で要求する。',
 'ekc5':'同じprofileをekc4のアフィン位相へ適用した時間関数。任意の位相原点offsetを保持し、観測地点の位相を零へ限定しない。',
 'ekc6':'正の一周期位相cycle、角周波数rate、時間周期period、周期数frequencyについてrate*period=cycleとfrequency*period=1を同時に要求する。frequency=rate/cycleであり角周波数との数値同一視や時間周期との交換を拒否する。',
 'ekc7':'同じ正弦・余弦の一周期ekc3、率と周期数のekc6、同じ任意offsetを持つ二時間関数ekc5の最小正周期を合わせる。場の零振幅から一周期を選ばず、正規化した位相対の周期を使う。物理的な受信又は実測の認定ではない。',
 'ekda':'同じ四座標位相を三つの位置関数と同じ時刻へ適用した、軌跡に沿う位相の時間関数。x(t),y(t),z(t),tの順序と同一時刻を保つ。任意の位置関数を物理的な観測者の履歴と認定しない。',
 'ekdb':'同じ有効時刻の三位置と位相値が有効で、軌跡上の位相ekdaがrate*time+offsetに一致する点条件。静止点の偏りだけでなく、経路上の時間率を照合する。',
 'ekdc':'正の長さの閉時間区間の全有効時刻にekdbを要求し、正のrateと有効offsetを固定する。同じ区間・軌跡上のアフィン位相であり、領域外・全時間への物理的な適用や実測完了を追加しない。',
 'ekdd':'許容V,vと単位方向、同じ正の一周期に結ばれた旧新の角周波数・時間周期・周期数について、角周波数と周期数が共にβ(1−av/V)倍になることを要求する。周期はその逆倍率であり、二系で周期位相を別々に選ばない。',
 'ekde':'先行ekclの同じ41役割の波と変換表示へ、共通のpiと一周期、旧新の時間周期・周期数を結ぶ。正弦の位相原点零で周期を指定するが、実際の観測者の位相原点を零へ制限しない。場の近似と物理的な調査は先行条件に保存し、周期数の物理的同定はこの数値橋渡しだけから導かない。',
 'ekdf':'同じK、V、第七節、評価状況を固定し、先行37役割と六つの周期関連値を一つの43証人の割当へ束縛したekdeの内容。著者の提示へはまだ接続しない依存内容。',
}
LIMITS=[
 'u0188–u0189に必要な、角周波数ωと通常の周期数νの区別を合成する依存群。本文370主張と既存の全単位判断を保持し、新しい著者主張・全単位判断は追加しない。源の静止、無限遠の読み、角φ、観測者による知覚、folgtと式の前方参照は次の統合で必要である。',
 'νは同じ時間単位あたりの周期数、時間周期の逆数と読む。ωは同じ位相尺度の時間率であり、一周期2*piを共有して初めてν=ω/(2*pi)となる。任意の正の係数で同じ比になればよいという定義にはしない。',
 '正弦と余弦は既存の全実数の初期値微分条件、piは既存の積分sedi、一周期は全位相の共通最小正周期で指定する。周期に関する標準解析の性質を明示的条件として結ぶもので、全実数の存在・一意性・周期定理を有限検査だけで証明しない。',
 '周期は正規化された位相対について指定する。六つの場成分が零の場合や誤差を含む実際の場から一意の周期を推定する構成ではない。源の放射・受信の周期として同定するには、次に物理的な役割と同じ波・時間単位・観測者の履歴を結ぶ必要がある。',
 '有限な局所観測区間が一周期を含むとは仮定しない。数学的な正弦表現の周期と、同じ局所軌跡上の位相の式を分けて保持し、短い実測から無限時間の周期を認定しない。',
 '二系の数値条件は共通の一周期位相を使う。実際の場と近似表現との成分誤差及び用途上の十分性は先行ekclから保ち、その誤差上限だけで実際の放射・受信の周期数が一意に決まるとはしない。',
 '全実数の量化を保持する。局所診断の有限周期関数は正弦と称さず、piや最小周期を入力境界とする検査と定義本体の検査を区別する。未知の算術・解析・物理入力を既知の真理にしない。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b')
    positive=lambda x:both(k('ba',x),k('bg',zero,x))
    period=v('period');point=v('point');shift=k('bd',point,period)
    values=[app(v(n),x) for n in ('first','second') for x in (point,shift)]
    text=define('ekcy',PERIOD+[('point',R)],both(k('ba',point),k('ba',period),*(k('ba',x) for x in values),k('sca',values[0],values[1]),k('sca',values[2],values[3])))
    text+=define('ekcz',PERIOD,both(positive(period),q('f','point',R,op('y',k('ba',point),k('ekcy',*args(PERIOD),point)))))
    candidate=v('candidate');smaller=both(positive(candidate),k('bg',candidate,period))
    text+=define('ekc2',PERIOD,both(k('ekcz',*args(PERIOD)),q('f','candidate',R,op('y',smaller,op('u',k('ekcz',v('first'),v('second'),candidate))))))
    cycle=v('cycle');rate=v('rate');frequency=v('frequency');offset=v('offset')
    text+=define('ekc3',HARMONIC,both(k('sdv2',v('sine'),v('cosine')),k('sedi',v('pi')),positive(cycle),k('sca',cycle,k('shv',two,v('pi'))),k('ekc2',v('sine'),v('cosine'),cycle)))
    text+=define('ekc4',[(n,R) for n in ('rate','offset','time')],k('bd',k('shv',rate,v('time')),offset),R)
    text+=define('ekc5',[('profile',F),('rate',R),('offset',R)],'i[time '+R+']['+app(v('profile'),k('ekc4',rate,offset,v('time')))+']',F)
    text+=define('ekc6',FREQUENCY,both(*(positive(v(n)) for n,t in FREQUENCY),k('sca',k('shv',rate,period),cycle),k('sca',k('shv',frequency,period),one)))
    text+=define('ekc7',TIMEWAVE,both(k('ekc3',*args(HARMONIC)),k('ba',offset),k('ekc6',*args(FREQUENCY)),k('ekc2',*(k('ekc5',v(n),rate,offset) for n in ('sine','cosine')),period)))
    coordinates=[app(v(n),v('time')) for n in ('x','y','z')]+[v('time')]
    trace=app(v('phase'),*coordinates)
    text+=define('ekda',TRACE,'i[time '+R+']['+trace+']',F)
    text+=define('ekdb',TRACE_POINT,both(*(k('ba',x) for x in coordinates+[rate,offset,trace]),k('sca',app(k('ekda',*args(TRACE)),v('time')),k('ekc4',rate,offset,v('time')))))
    inside=both(k('ba',v('time')),k('lg',v('lower'),v('upper'),v('time')))
    text+=define('ekdc',TRACE_INTERVAL,both(*(k('ba',v(n)) for n in ('lower','upper','offset')),positive(rate),k('bg',v('lower'),v('upper')),q('f','time',R,op('y',inside,k('ekdb',*args(TRACE_POINT))))))
    V=v('light');speed=v('speed');ax=v('ax');newrate=v('newrate');newfrequency=v('newfrequency')
    text+=define('ekdd',DOPPLER,both(k('sdl2',V,speed,rate,ax,v('ay'),v('az')),k('ekc6',cycle,rate,v('oldperiod'),frequency),k('ekc6',cycle,newrate,v('newperiod'),newfrequency),k('sca',newrate,k('sdn2',V,speed,rate,ax)),k('sca',newfrequency,k('sdn2',V,speed,frequency,ax))))
    speed=k('zb7');newrate=k('sdn2',V,speed,rate,ax)
    temporal=[k('ekc7',*args(HARMONIC),r,zero,v(p),v(f)) for r,p,f in [(rate,'oldperiod','frequency'),(newrate,'newperiod','newfrequency')]]
    text+=define('ekde',SETTING,both(k('ekcl',*args(FAMILY)),*temporal,k('ekdd',cycle,V,speed,ax,v('ay'),v('az'),rate,newrate,v('oldperiod'),v('newperiod'),frequency,newfrequency)))
    override={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')}
    text+=content('ekdf',bind(WITNESSES,k('ekde',*[override.get(n,v(n)) for n,t in SETTING])))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==370
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='phase_cycle_frequency_dependencies_not_physical_observation_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/wave-transform-application-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
