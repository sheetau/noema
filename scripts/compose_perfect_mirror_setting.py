"""Present the same preceding plane wave at a lossless stationary mirror model."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_mirror_surface_pressure import ROOT,read
from scripts.compose_doppler_specialization import EXTENDED
from scripts.compose_stationary_mirror_boundary import HARMONIC_MODEL,WAVE,GEOMETRY
from scripts.compose_observed_intensity import COEFFICIENT
from scripts.compose_wave_transform_application import transformed
from scripts.compose_rod_methods import interval
from scripts.compose_field_equations import FIELD,REGION,TAU
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-mirror-surface-pressure.noema';PARENT_BASIS='data/mirror-surface-pressure-basis-v1.json'
FULL='examples/v014/einstein-perfect-mirror-setting.noema';CORE='examples/v014/perfect-mirror-setting-core.noema'
BASIS='data/perfect-mirror-setting-basis-v1.json';ANNOTATIONS='data/perfect-mirror-setting-identifiers-v1.json';INDEX=394
COORDS=[(n,R) for n in ('x','y','z','time')]
INTERACTION=[(n,'a') for n in ('interaction','body','wave','process','reflectedwave','reflectedprocess','frame','lengthunit','timeunit','electricunit','magneticunit')]+[(n,FIELD) for n in ('incidentE','incidentH','reflectedE','reflectedH')]+[('region',REGION),('scope','a'),('context','d')]
RATES=[(n,TAU) for n in ('incoming','outgoing','through','retained')]
BUDGET=[(n,'a') for n in ('interaction','body','frame','lengthunit','timeunit','energyunit')]+[('region',REGION)]+RATES+[('scope','a'),('context','d')]
FLOW=[('coefficient',R),('electric',FIELD),('magnetic',FIELD)]
SETTING=EXTENDED+[(n,'a') for n in ('body','interaction','reflectedwave','reflectedprocess','energyunit')]+[('coefficient',R)]
FIXED={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')}
VARIABLES=[(n,t) for n,t in SETTING if n not in FIXED]
PRIMITIVES={
 'eisuc':(INTERACTION,'同じbodyの界面への入射波waveとその電磁過程processとの相互作用interactionが、同じ入射側へ戻る波reflectedwaveと過程reflectedprocessを生むという物理的な帰属。指定frame・長さ時間・二場の単位とregion・contextで、四つの場を入射成分と戻る成分の局所代表モデルとして採用し、scopeの反射の考察に十分な表現として扱う。無関係な放射の偶然の一致や面を通り抜ける成分を反射へ替えない。界面の位置、戻る方向、偏光・位相・周期、損失、場の数式は別に構成する。全電磁場は複数過程の重ね合わせを許し、入射成分を面と反射成分を含む合成場と混同しない。実際の場と近似代表場の同一性や誤差零、全領域外の測定、鏡の製作又は実験実施を要求しない。このモデル採用の仮定を先行近似の誤差上限だけから自動推論しない。'),
 'eisud':(BUDGET,'同じinteractionとbodyの界面について、指定frame・長さ時間・エネルギー単位・regionで、incomingを入射側から界面へ向かう単位面積時間あたりのエネルギー、outgoingを同じ側へ戻るエネルギー、throughを反対側へ通過するエネルギー、retainedを物体への正味の移転として記述する完全な収支モデルをscopeに採用する物理的対応。retainedは仕事・蓄積・熱等への移転を合わせた符号付き寄与であり、それらを別の見落とした経路へ逃がさない。外部からの追加供給も黙って除外せず、この四経路で扱う設定を明示する。数値的な収支の一致と各経路の零は別に要求する。単に四関数へ名前を付けることや無関係な領域・系・単位の流を並べることではない。エネルギーは同じ機械的仕事と交換収支へ同定し、物理的な全域測定を要求しない。'),
 'eisue':([], '固定原文einstein-1905:u0215[0,157)のEs sei nunからreflektiert werden.まで、ξ=0の完全反射面と前節の平面波を仮定する第一文の箇所。'),
}
MEANINGS={
 'ekq7':'同じ四座標領域のうち有効な座標でx<=0となる入射側を取る。境界を含めるが反対側の透過領域を反射側にしない。',
 'ekra':'同じ四座標領域とx=0の平面との共通部分。局所の光の領域を物体全体の形状へ取り違えない。',
 'ekrb':'同じ領域が有効なx=0の境界点を少なくとも一つ持つ。面と光の考察範囲が交わらない空の条件を排除する。',
 'ekrc':'同じ係数と同じ電気・磁気の場の三成分から、各四座標における+x方向のκ(E×H)成分を返す。電場と磁場の順序、同じ時刻と場所を保つ。',
 'ekrd':'同じ四経路の値が有効で、入射・戻り・通過が非負、入射=戻り+通過+物体移転であり、通過と物体移転がともに零という完全反射モデルの一点条件。戻りの値だけを入射へ等置して未計上の経路を隠さない。',
 'ekre':'同じ非空の境界領域の全有効四座標でekrdを要求する。有限の一地点や一時刻の零損失を全面の条件にしない。',
 'ekrf':'同じ66設定で先行の波・源・観測者・二系のeket、同じbodyの完全な物質面ekqu、同じk側の正弦・位相率・三方向・六係数・周期を持つekqnを保つ。その同じ代表場をeisucの入射・反射過程へ、正の校正係数をeisteへ、同じ界面の四エネルギー経路をeisudとekreへ結ぶ。',
 'ekrg':'同じK、V、先行の第七節の波範囲、評価状況を固定し、残る62役割を一つの存在割当として束縛したekrfの仮定内容。波・面・過程・単位・領域を各節ごとに選び直さない。',
 'ekrh':'著者が同じ第八節でekrgを思考上の設定として想定し採用するeislz/ugに、前の第七節で考察した同じ波への区分参照eisovと内容照応eisraを結ぶ。現実の鏡の発見・実験又は仮定の処理系による証明とはしない。',
 'ekri':'同じ完全反射面と先行平面波の仮定の提示ekrhを述べるメッセージ。',
 'ekrj':'u0215第一文を同じ著者・論説へ帰属し、u0214の共通変換則の観察に続ける。第二文の四量の問いをこの主張へ省略して含めない。',
}
LIMITS=[
 '原刊914頁u0215[0,157)の第一文、130非空白本文文字とM0368=ξ=0を対象とする。Es seiを思考上の仮定の採用、nunをここでの論述の進行、im letzten Paragraphを直前の番号付き区分である第七節への参照として読む。第二文は未完であり、全単位判断は増やさない。',
 '面は先行ekquの厚さ零の剛な物質的平面シートの理想化であり、kのξ=0、Kのx=v*tを同一物質点・同一出来事の全記録へ結ぶ。本文が厚さ・密度・材質の実測値を指定したとする読みではない。',
 '完全反射の具体的候補は静止した完全導体の平滑面という読みを採る。入射側はξ<0、kでの法線余弦は正、非零の横波とし、全三方向と二偏光を保持する。完全反射一般の全材料・全周波数の偏光位相をこの候補に限定する語義判断ではない。',
 '前節の同じ波とその局所近似を引き継ぐ。入射成分と反射成分を分けた代表モデルをこの仮定の反射の考察に採用する物理的対応を明示し、先行の実際の場を代表正弦場と同一視したり誤差上限を零に変更したりしない。全境界の正弦モデルを現実の全空間全時刻の測定へ外挿しない。',
 'vollkommenは考察する理想モデルで通過と面への正味エネルギー移転が零であることと、全四経路の収支に結ぶ。面の静止系で評価し、Kでの鏡への仕事まで零と結論しない。反射以外の供給や散逸を未計上の経路へ逃がすモデルにはしない。',
 'エネルギー流は同じ単位校正のκ(E×H)を各進行波で用い、入射を+x、戻りを−xへ取る。周期平均ではなく瞬間の境界収支である。場・位相・偏光と完全導体境界の数学的構成、物理的モデル採用、著者の仮定提示を別に保持する。',
 '同じ局所の光の領域を同じ物体履歴のk側時間範囲へ制限し、面との交わりを非空とする。その範囲の全四座標の条件を保持する。候補モデルの反射解の唯一性、実際の材料の微視的な表面電荷・電流、鏡の製作可能性をこの文の翻訳条件に追加しない。',
 '62の存在証人を同じ仮定へ共有する。先行の仮定ekbnと現在の光・源・物理場・位相・単位・観測者の関係はeketの既存依存に保持する。新しい一般関係二つは任意の界面での波の帰属と四経路のモデル対応であり、本文の位置・完全性・方向・周期や原文一文の意味を隠さない。',
 '第二文の光圧と反射後の方向・周波数・強度の問い、及び後続の式の提示は未完。先行の圧力質問ekq6へは同じinteractionを力の過程として、周期と有限面部分を共有する必要がある。後続の答えや問いの解の存在・一意性を今回の著者提示へ追加しない。',
]

def models():
    zero=k('bb','n p a b');V=v('light');speed=v('speed');amps,shifted,_,_=transformed(speed)
    numeric={n:v(n) for n,t in HARMONIC_MODEL}|dict(rate=shifted[0],ax=shifted[1],ay=shifted[2],az=shifted[3],period=v('newperiod'),frequency=v('newfrequency'),**dict(zip(('ex','ey','ez','hx','hy','hz'),amps)))
    wave=[v('sine') if n=='profile' else numeric[n] for n,t in WAVE]
    inc=[k('sdx2',v('sine'),V,*shifted,*a) for a in (amps[:3],amps[3:])]
    reflected=[k(n,*wave) for n in ('ekqi','ekqj')]
    original=k('eken',speed,v('space'),v('lower'),v('upper'),V)
    params=' '.join(n+' '+t for n,t in COORDS)
    region='i['+params+']['+both(app(original,*args(COORDS)),k('lg',*interval(k('zbm'),v('context')),v('time')))+']'
    front=k('ekq7',region);boundary=k('ekra',region)
    incoming=k('ekrc',v('coefficient'),*inc);raw=k('ekrc',v('coefficient'),*reflected)
    outgoing='i['+params+']['+k('be',app(raw,*args(COORDS)))+']';null='i['+params+']['+zero+']'
    return numeric,inc,reflected,front,boundary,[incoming,outgoing,null,null]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');coords=args(COORDS);valid=both(*(k('ba',x) for x in coords));region=v('region')
    for name,extra in [('ekq7',k('bc',v('x'),zero)),('ekra',k('sejm',*coords))]:
        text+=define(name,[('region',REGION)],'i['+' '.join(n+' '+t for n,t in COORDS)+']['+both(valid,app(region,*coords),extra)+']',REGION)
    text+=define('ekrb',[('region',REGION)],quantified('g',COORDS,both(valid,app(region,*coords),k('sejm',*coords))))
    fields=[app(app(v(field),k(axis)),*coords) for field in ('electric','magnetic') for axis in ('yn','yo','yp')]
    text+=define('ekrc',FLOW,'i['+' '.join(n+' '+t for n,t in COORDS)+']['+k('ekjf',v('coefficient'),one,zero,zero,*fields)+']',TAU)
    incoming,outgoing,through,retained=[app(v(n),*coords) for n,t in RATES]
    text+=define('ekrd',RATES+COORDS,both(valid,*(k('ba',x) for x in (incoming,outgoing,through,retained)),*(k('bc',zero,x) for x in (incoming,outgoing,through)),k('sca',incoming,k('bd',outgoing,k('bd',through,retained))),k('sca',through,zero),k('sca',retained,zero)))
    text+=define('ekre',[('region',REGION)]+RATES,both(k('ekrb',region),quantified('f',COORDS,op('y',both(valid,app(region,*coords)),k('ekrd',*args(RATES),*coords)))))
    numeric,inc,reflected,front,boundary,rates=models()
    shared={n:v(n) for n,t in SETTING}|dict(frame=k('zbm'),scope=k('eistk'))
    physical=shared|dict(incidentE=inc[0],incidentH=inc[1],reflectedE=reflected[0],reflectedH=reflected[1],region=front)
    budget=shared|dict(region=boundary,**dict(zip((n for n,t in RATES),rates)))
    text+=define('ekrf',SETTING,both(k('eket',*args(EXTENDED)),k('ekqu',v('body'),v('light'),v('speed'),v('context')),k('ekqn',*[numeric[n] for n,t in HARMONIC_MODEL]),k('eiste',*[shared[n] for n,t in COEFFICIENT]),k('eisuc',*[physical[n] for n,t in INTERACTION]),k('eisud',*[budget[n] for n,t in BUDGET]),k('ekre',boundary,*rates)))
    text+=content('ekrg',quantified('g',VARIABLES,k('ekrf',*[FIXED.get(n,v(n)) for n,t in SETTING])))
    p=v('point');node=k('eisue');author=k('rd');paper=k('eirf');scope=k('eistk')
    text+=content('ekrh',both(k('eislz',node,author,quote('ekrg'),scope,p),k('ug',node,author,quote('ekrg'),scope,p),k('eisov',node,author,k('eisrx'),quote('ekbn'),paper,p),k('eisra',node,author,paper,k('eissc'),quote('ekbn'),quote('ekrg'),scope,p)))
    text+='d ekri[] f[j s[k ekrh[]]].\n'
    text+=define('ekrj',[],both(k('eir3',node,author,paper,quote('ekri'),k('ri')),k('ue',k('eisua'),node,k('ri')),op('u',op('e',k('eisua'),node))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekrj',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_preceding_wave_at_material_lossless_mirror_supposition',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/mirror-surface-pressure-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
