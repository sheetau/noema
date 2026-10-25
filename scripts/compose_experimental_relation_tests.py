"""Compose independent tests of the potential and local-radius relations."""
from scripts.compose_closing_acknowledgment import *
from scripts import compose_traversed_potential as potential
from scripts import compose_local_magnetic_radius as radius
from scripts import compose_deflection_speed_determination as measurement
from scripts import compose_point_particle_dynamics as dynamics

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-experimental-relation-tests.noema';CORE='examples/v014/experimental-relation-tests-core.noema'
BASIS='data/experimental-relation-tests-basis-v1.json';ANNOTATIONS='data/experimental-relation-tests-identifiers-v1.json'
QUANTITY=measurement.QUANTITY;DEVICE=measurement.DEVICE;READOUT=measurement.READOUT
PBASE=potential.ALL
RBASE=radius.SETTING+[('speedunit','a'),('speedscale','b')]
COMMON=[('view','a'),('observer','a'),('scene','d'),('assessment','d'),('predicted',R),('agrees','c')]
PCHANNELS=('drop','speed','mass','charge');RCHANNELS=('radius','speed','mass','charge','magnetic')
PTEST=PBASE+COMMON+[(pre+'read'+n,t) for pre in PCHANNELS for n,t in DEVICE]
RTEST=RBASE+COMMON+[(pre+'read'+n,t) for pre in RCHANNELS for n,t in DEVICE]
PWS=[(n,t) for n,t in PBASE if n not in ('episode','frame','end','potentialunit','drop','context')]
RWS=[(n,t) for n,t in dynamics.KINEMATIC if n not in ('matter','frame','event','lengthunit','context')]+[('lengthscale','b'),('timescale','b')]
QWS=[('chargerecord','a'),('chargescale','b')]
MEANINGS={
 'et7':'指定した同じ静電加速の過程target・系・終端出来事・電位単位に、その過程で通過した電位降下valueを結ぶ量内容。er7の全軌道・実場・電位と仕事の対応に、eoyの同じ過程の実エネルギー取り出しを加え、始点と終点を持つ過程を単独の粒子時点に取り違えない。速度公式は前提にしない。',
 'eua':'同じ対象・系・出来事の校正された三次元実軌道の一階・二階微分ek3qから、sevcの正の幾何学的局所曲率半径を指定長さ単位へ結ぶ。磁場・電荷・運動方程式を半径の定義へ使わず、接線加速度と一般の局所法平面を許す。',
 'eub':'同じ対象・系・出来事・単位の正の低速慣性質量ek3oを測定の量記述へ結ぶ。現在の実速度を低速に限定しない。',
 'euc':'同じ対象・系・出来事・単位の非零の符号付き電荷ek3uを測定の量記述へ結ぶ。物理的記録と正の尺度を存在量化し、電荷の絶対値に交換しない。',
 'eud':'第二項の実軌道・初速零・実静電場・全電位区間と仕事、緩い加速・無放射・閉じたエネルギー収支・非負の光速未満の終速度という検査条件。第一(A)、運動エネルギーの速度式、検査するPの速度公式を入れない。',
 'eue':'第三項の実曲率・磁気だけによる偏向・同じ実二場と幾何学的単位espを、同じ長さ時間に校正された速度単位ernへ結ぶ検査条件。第二(A)や磁気半径公式を入れない。',
 'euf':'同じ可能な過程で第二項の電位降下・終速度・低速質量・符号付き電荷を校正して取得し、方法と校正がesdの式を算出前提にしないことを要求する。全記録を同じ観測者の評価点へ共有し、測定入力によるesaの予測値と実電位差を比較して正しい一致判定を得る。一致そのものは要求しない。',
 'eug':'同じ可能な第三項の過程で幾何学的半径・実速さ・低速質量・符号付き電荷・磁場z成分を校正して取得する。全方法のes2からの独立性、同じ評価点での記録共有、esrの予測値と実半径の正しい比較判定を保つ。幾何学的半径を理論の半径公式から測定したことにしない。',
 'euh':'同じ第二項の物理的設定と理論規約を固定し、eufの観測者・二状況・全測定装置と信号・予測値・判定が存在するという実験的検査へのアクセス。一致・実施済み・全設定への普遍性を付加しない。',
 'eui':'同じ第三項の物理的設定と理論規約を固定し、eugの全測定・比較の過程が存在するというアクセス。別々に可能な相容れない記録を集めない。',
 'euj':'現在の第二項の同じ過程・電子・K・単位・全物理量をeuhへ固定し、同じ論説の理論規約における実験可能性を述べる内容。',
 'euk':'現在の第三項の同じ局所事例・電子・K・単位・全物理量をeuiへ固定した実験可能性の内容。前項の静電軌道に取り違えない。',
 'eul':'第一項の独立比較erwと、第二項euj・第三項eukの比較可能性を合わせた全三項への実験的アクセス。各実験の条件と対象を保持し、一つの方法で同時に全実験を実施したとはしない。',
}
LIMITS=[
 'u0265のdem Experimente zugänglichen Eigenschaftenに必要な意味依存群。全三関係の具体的な測定と比較の接続を追加する。列挙する取組、(A)からの帰結、導入一文全体の提示は未接続であり、今回の検査だけでは全文判断を増やさない。',
 '第二項の電位差は同じ初期・終端を持つ過程に属する量として取得する。その他の量は同じ電子の同じ終端に属する。第三項の半径は同じ局所出来事の実三速度・実三加速度による幾何学的量であり、磁気力の式を測定定義に入れない。',
 '質量・電荷・速さ・磁場も校正と信号取得を要求する。Vは既存の同じ単位系の光速度定数を共有する。全チャンネルの校正と算出が検査対象の式を前提にしないこと、記録の同一可能過程内の共有を別に要求する。',
 '予測は測定された入力値から既存esa/esrで定め、比較は既存eis37の実操作として要求する。予測式の数値的成立を実験結果の一致へ替えない。個別の計算回路・実験装置の細目・全実数の全桁出力・現実の誤差零を原文に追加しない。',
 '第二項の緩い加速・無放射・閉収支、第三項のqN>0と磁気だけによる偏向という既存の読みを保つ。検査の物理的条件へ第一・第二(A)、運動エネルギーの速度式、PやRの正しい観測結果を隠して追加しない。',
 '一般の量内容・測定関係は再利用可能であるが、閉じた実験可能性は現在の各項の同じ事例を指す。全ての電子又は全ての測定法への普遍性を補わない。有限の束縛診断は全関数域の評価でも実験可能性の物理的証明でもない。旧444主張と意味判断・証拠を保存する。',
]

def values(fields,**replace):return [replace.get(n,v(n)) for n,t in fields]
def channel_specs(kind):
    return [('drop','et7','episode','end','potentialunit','drop'),('speed','erm','matter','end','speedunit','finalspeed'),('mass','eub','matter','end','massunit','mass'),('charge','euc','matter','end','chargeunit','charge')] if kind=='potential' else [('radius','eua','matter','event','radiusunit','radius'),('speed','erm','matter','event','speedunit','speed'),('mass','eub','matter','event','massunit','mass'),('charge','euc','matter','event','chargeunit','charge'),('magnetic','equ','matter','event','magneticunit','magnetic')]
def definitions():
    text='';ctx=v('context');zero=k('bb',rat(0));pvals=dict(episode=v('target'),frame=v('frame'),end=v('event'),potentialunit=v('unit'),drop=v('value'),context=ctx)
    text+=define('et7',QUANTITY,quantified('g',PWS,both(k('er7',*values(PBASE,**pvals)),k('eoy',*values(energy.ALL,**pvals)))))
    kvals=dict(matter=v('target'),lengthunit=v('unit'));moment=coord(v('point'),ROLES[3])
    geom=k('sevc',*(app(v(n),moment) for n,t in dynamics.PROFILES),*args(dynamics.ACCEL),v('value'))
    units=both(k('ejwb',v('unit'),rat(1),rat(0),rat(0),v('lengthscale'),ctx),k('ejwb',v('timeunit'),rat(0),rat(0),rat(1),v('timescale'),ctx),k('aa',rat(0),v('lengthscale')),k('aa',rat(0),v('timescale')))
    text+=define('eua',QUANTITY,quantified('g',RWS,both(k('ek3q',*values(dynamics.KINEMATIC,**kvals)),geom,units)))
    text+=define('eub',QUANTITY,k('ek3o',v('target'),v('frame'),v('event'),v('unit'),v('value'),ctx))
    text+=define('euc',QUANTITY,quantified('g',QWS,k('ek3u',v('target'),v('frame'),v('event'),v('chargerecord'),v('unit'),v('chargescale'),v('value'),ctx)))
    text+=define('eud',PBASE,both(k('er7',*args(PBASE)),*(k(n,*values(energy.ALL)) for n in ('eoy','eoz','eo2')),k('s45',v('light'),v('finalspeed')),k('bc',zero,v('finalspeed'))))
    text+=define('eue',RBASE,both(k('esp',*values(radius.SETTING)),k('ern',*values(potential.SPEED_UNITS))))
    for name,kind,fields,base,physical,claim,observed in [('euf','potential',PTEST,PBASE,'eud','esd','drop'),('eug','radius',RTEST,RBASE,'eue','es2','radius')]:
        scene=v('scene');assessment=v('assessment');observer=v('observer');parts=[k('eisoe',v('view'),ctx,scene),k('eisoe',v('view'),ctx,assessment),k(physical,*values(base,context=scene))]
        for pre,quantity,target,event,unit,value in channel_specs(kind):
            supplied={n:v(pre+'read'+n) for n,t in DEVICE}|dict(observer=observer,target=v(target),quantity='r[p '+quantity+']',frame=v('frame'),event=v(event),unit=v(unit),context=scene,value=v(value))
            parts += [k(quantity,*[supplied[n] for n,t in QUANTITY]),k('eqv',*[supplied[n] for n,t in READOUT]),k('eis36',v(pre+'readmethod'),quote(claim),scene),k('eis3u',observer,v(pre+'readrecord'),scene,assessment)]
        prediction=k('esa',v('light'),v('finalspeed'),v('mass'),v('charge'),v('predicted')) if kind=='potential' else k('esr',*values(radius.NUMERIC,radius=v('predicted')))
        parts += [prediction,k('eis37',observer,quote(claim),v(observed),v('predicted'),v('agrees'),assessment),op('z',v('agrees'),k('sca',v(observed),v('predicted')))]
        text+=define(name,fields,both(*parts))
    for name,fields,base,target in [('euh',PTEST,PBASE,'euf'),('eui',RTEST,RBASE,'eug')]:
        fixed=base+[('view','a')];ws=[(n,t) for n,t in fields if n not in dict(fixed)]
        text+=define(name,fixed,quantified('g',ws,k(target,*args(fields))))
    p=v('point');theory=k('eiscv',k('eis3k'),k('eirf'),quote('eigj'),p)
    text+=content('euj',both(theory,k('euh',*potential.actual(PBASE),k('eis3k'))))
    rfixed=radius.FIXED|{'speedunit':'eis4o','speedscale':'eis4p'}
    text+=content('euk',both(theory,k('eui',*[p if n=='context' else k(rfixed[n]) for n,t in RBASE],k('eis3k'))))
    text+=content('eul',both(*(op('t',k(n),p) for n in ('erw','euj','euk'))))
    return text
@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==444
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='independent_potential_and_curvature_comparisons_composed',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
