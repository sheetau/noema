"""Compose per-second loss, observed intervals and a quantified approximation."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, CUT, definition
from scripts.compose_limits import call as k, app, op, both, quant as q, lam

v=lambda name:'v '+name
FUNCTION='h['+CUT+'] '+CUT
DOMAIN='h['+CUT+'] c'


def rational_definitions():
    z='n p a b';one='n p b b';mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b))
    rate=v('rate');s=v('squaredratio')
    text=definition('svn','squaredratio b rate b lag b approximation b error b',both(
        op('u',k('aa',s,z)),k('aa',s,one),k('aa',z,rate),op('e',mul(rate,rate),sub(one,s)),
        op('e',v('lag'),sub(one,rate)),op('e',mul('n p c b',v('approximation')),s),op('e',v('error'),sub(v('lag'),v('approximation')))))
    text+=definition('svo','duration b rate b elapsed b lost b',both(k('aa',z,v('duration')),k('aa',z,rate),op('u',k('aa',one,rate)),
        op('e',v('elapsed'),mul(v('duration'),rate)),op('e',v('lost'),sub(v('duration'),v('elapsed')))))
    return text


MEANINGS={
    'svn':'速度比の二乗が0以上1未満のとき、正の進み率・単位時間の遅れ・二次近似・残差を結ぶ有理数条件。近似を厳密値と等置しない。',
    'svo':'正の観測経過時間と正で1以下の進み率について、指示の経過と遅れを結ぶ有理数条件。'}


def generic_composed():
    doc=parse((ROOT/'examples/v014/origin-clock.noema').read_text(encoding='utf-8')+rational_definitions())
    basis=deepcopy(json.loads((ROOT/'data/origin-clock-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='clock-delay-basis-v1',document='examples/v014/clock-delay.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved']+=['遅れ率は無次元であり、秒での遅れには観測時間と単位換算が必要。四次残差の係数の境界は原文にない数学的補足。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/'examples/v014/einstein-origin-clock.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+rational_definitions()
    z=k('bb','n p a b');one=k('bb','n p b b');half=k('bb','n p b c');eighth=k('bb','n p b i')
    mul=lambda a,b:k('shv',a,b);sq=lambda a:mul(a,a);sub=lambda a,b:k('bf',a,b)
    eq=lambda a,b:k('sca',a,b);valid=lambda a:k('ba',a)
    V,s,rate,lag,approx,error=map(v,('light','speed','rate','lag','approximation','error'))
    ratio=k('sje',s,V);fourth=sq(sq(ratio))
    text+='r zik[] a.r zil[a a '+CUT+' d] c.r zim[] a.r zin[] a.r zio[] a.\n'
    text+=definition('svp','scale '+CUT+' setting d',both(k('ci',k('rb')),k('ci',k('zik')),k('sbg',v('scale')),
        k('zil',k('rb'),k('zik'),v('scale'),v('setting'))))
    params=' '.join(name+' '+CUT for name in ('light','speed','rate','lag','approximation','error'))
    text+=definition('svq',params,both(k('stx',V,s,rate),*(valid(x) for x in (lag,approx,error)),
        eq(lag,sub(one,rate)),eq(approx,mul(half,sq(ratio))),eq(error,sub(lag,approx))))
    text+=definition('svr',params,both(k('svq',V,s,rate,lag,approx,error),k('bc',mul(eighth,fourth),error),k('bc',error,mul(half,fourth))))
    text+=definition('svt','',sub(one,k('svm')),CUT)
    text+=definition('svu','',mul(half,sq(k('sje',k('zb7'),k('tc')))),CUT)
    text+=definition('svv','',sub(k('svt'),k('svu')),CUT)
    # Nonnegative comparison scales allow signed errors without a new abs oracle.
    text+=definition('svw','error '+CUT+' bound '+CUT,both(valid(v('error')),valid(v('bound')),k('bc',z,v('bound')),
        k('bc',sub(z,v('bound')),v('error')),k('bc',v('error'),v('bound'))))
    parameters='domain '+DOMAIN+' function '+FUNCTION+' approximation '+FUNCTION+' scale '+FUNCTION+' point '+CUT
    x=v('x');inside=both(valid(x),app(v('domain'),x))
    near=both(inside,op('u',eq(x,v('point'))),k('sjp',x,v('point'),v('delta')))
    scale=app(v('scale'),x);residual=sub(app(v('function'),x),app(v('approximation'),x))
    text+=definition('svx',parameters+' constant '+CUT+' delta '+CUT,both(
        *(k('sjo',v('domain'),v(name)) for name in ('function','approximation','scale')),valid(v('point')),
        k('sbg',v('constant')),k('sbg',v('delta')),q('f','x',CUT,op('y',near,both(k('bc',z,scale),k('svw',residual,mul(v('constant'),scale)))))))
    text+=definition('svy',parameters,both(k('sjq',v('domain'),v('point')),q('g','constant',CUT,q('g','delta',CUT,
        k('svx',*(v(name) for name in ('domain','function','approximation','scale','point','constant','delta')))))))
    text+=definition('svz','ratio '+CUT,sub(one,k('sky',sub(one,sq(v('ratio'))))),CUT)
    text+=definition('swa','ratio '+CUT,mul(half,sq(v('ratio'))),CUT)
    text+=definition('swb','ratio '+CUT,sq(sq(v('ratio'))),CUT)
    domain=lam('ratio',CUT,both(valid(v('ratio')),k('bg',sq(v('ratio')),one)))
    text+=definition('swc','',k('svy',domain,'p svz','p swa','p swb',z))
    # Bind actual elapsed readings to seconds, preserving the clock and records.
    record=lambda name:v(name)
    instant=lambda name:k('zc6',k('zdz',k('zad',record(name)),k('ra'),v('setting')),k('zc7'))
    delta=sub(instant('last'),instant('first'))
    elapsed=sub(k('zag',record('last')),k('zag',record('first')))
    duration_seconds=mul(v('scale'),delta);elapsed_seconds=mul(v('scale'),elapsed)
    pair=both(k('zac',v('first'),k('zie'),v('setting')),k('zac',v('last'),k('zie'),v('setting')),k('bg',instant('first'),instant('last')))
    text+=definition('swd','first a last a scale '+CUT+' duration '+CUT+' elapsed '+CUT+' lost '+CUT+' approximation '+CUT+' error '+CUT+' setting d',both(
        k('svp',v('scale'),v('setting')),k('svq',*(k(n) for n in ('tc','zb7','svm','svt','svu','svv'))),k('svc',k('zie'),k('svm'),v('setting')),pair,
        *(valid(v(n)) for n in ('duration','elapsed','lost','approximation','error')),
        eq(v('duration'),duration_seconds),eq(v('elapsed'),elapsed_seconds),eq(v('lost'),sub(v('duration'),v('elapsed'))),
        eq(v('approximation'),mul(v('duration'),k('svu'))),eq(v('error'),sub(v('lost'),v('approximation'))),
        eq(v('elapsed'),mul(v('duration'),k('svm'))),eq(v('lost'),mul(v('duration'),k('svt')))))
    lost=sub(duration_seconds,elapsed_seconds);estimate=mul(duration_seconds,k('svu'))
    text+=definition('swe','scale '+CUT+' setting d',both(k('svp',v('scale'),v('setting')),
        k('svc',k('zie'),k('svm'),v('setting')),q('f','first','a',q('f','last','a',op('y',pair,
            k('swd',v('first'),v('last'),v('scale'),duration_seconds,elapsed_seconds,lost,estimate,sub(lost,estimate),v('setting')))))))
    scalars=[k(n) for n in ('tc','zb7','svm','svt','svu','svv')]
    exact=both(k('svq',*scalars),q('g','scale',CUT,k('swe',v('scale'),k('zb6'))))
    text+=definition('swf','','b context['+exact+']','e')
    text+=definition('swg','','b context['+both('t[k swf[]][v context]',k('swc'))+']','e')
    text+=definition('swh','','b context['+k('svr',*scalars)+']','e')
    firsttime=k('zc6',k('zdz',k('zad',v('first')),k('ra'),k('zb6')),k('zc7'))
    lasttime=k('zc6',k('zdz',k('zad',v('last')),k('ra'),k('zb6')),k('zc7'))
    width=q('g','first','a',q('g','last','a',both(k('zac',v('first'),k('zie'),k('zb6')),k('zac',v('last'),k('zie'),k('zb6')),k('bg',firsttime,lasttime))))
    text+=definition('swi','','b context['+both('t[k sve[]][v context]','t[k svk[]][v context]',width,
        q('g','scale',CUT,k('svp',v('scale'),k('zb6'))))+']','e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k zc[k zim[] k rd[] r[k swi[]] r[k swf[]] k rh[] k ri[]]].
s[k uh[k zin[] k rd[] r[k swg[]] k rh[] k ri[]]].
s[k zfl[k zio[] k rd[] r[k swf[]] r[k swh[]] k rh[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-origin-clock-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-clock-delay-basis-v1',document='examples/v014/einstein-clock-delay.noema')
    basis['definitions'].update(MEANINGS|{
        'svp':'座標と指示に共通の時間単位から秒への正の換算尺度を、同じ設定で指定する。',
        'svq':'許容速度と正の率について、厳密な遅れ率1-rate、二次近似(v/V)²/2、両者の残差を区別する。',
        'svr':'svqの残差が(v/V)^4/8以上、(v/V)^4/2以下という数学的な補足。係数の境界は原文の逐語的内容ではない。',
        'svt':'対象時計の理論上の厳密な単位時間あたりの遅れ率。',
        'svu':'対象速度での二次近似した遅れ率。',
        'svv':'対象速度での厳密な遅れ率と二次近似の差。',
        'svw':'有効な実切断による非負の上限で、符号付き誤差を両側から抑える。',
        'svx':'全域で有効な関数・近似・非負比較尺度について、指定点の穿孔近傍で同じ正の定数と近傍幅を使い、誤差を定数倍の尺度で抑える。',
        'svy':'指定点が実切断の定義域の集積点であり、svxを満たす正の定数と近傍幅が存在するというBig-O型の条件。',
        'svz':'無次元の速度比に対する厳密な遅れ率1-sqrt(1-ratio²)。',
        'swa':'無次元の速度比に対する二次近似ratio²/2。',
        'swb':'無次元の速度比の四乗。',
        'swc':'速度比の二乗が1未満の定義域で、零の近傍の遅れ率の二次近似誤差が四乗のオーダーであるという条件。',
        'swd':'同じ時計の時間順の二記録について、観測時間と指示差を共通尺度で秒へ換算し、正の経過・厳密な遅れ・二次近似・残差を結ぶ。',
        'swe':'指定した一つの共通換算尺度で、対象時計の全ての時間順の記録対がswdを満たす。各記録ごとに尺度を変えない。',
        'swf':'遅れ率の式を同じ時計の全記録対と秒の単位へ結ぶ内容。一秒区間が観測済みとは要求せず、経過を一秒に規格化したとき遅れ率と同じ数値の秒だけ遅れる。',
        'swg':'swfと、速度比の零近傍における四次残差というswcの留保を合わせた近似の内容。',
        'swh':'対象速度での残差の具体的な上下限という補足内容。',
        'swi':'原点の同じ時計の設定と比例式に、正の観測時間幅と秒への換算を合わせた推論前提。'})
    decls={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zik',[],'原文が時間量に用いる秒という時間単位。歴史的な単位の実現方法の構成は未完。'),
        ('zil',['from_unit','to_unit','scale','setting'],'同じ種類の時間量の数値にscaleを掛けると移換先単位の数値になるという、原点移動を含まない線形換算。尺度の正性と時間単位の型はsvpで要求する。'),
        ('zim',[],'原点の時計の式から一秒あたりの厳密な遅れを導く箇所。'),
        ('zin',[],'四次以上を省いた二次近似の遅れを提示する箇所。'),
        ('zio',[],'原文にない具体的な残差の上下限を追加解釈として記す箇所。')):
        d=decls[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['unresolved']+=[
        'u0125の部分記述。四次以上の省略は零近傍のBig-O型の誤差として表す。任意次数の解析的展開全体を確立したことにはしない。',
        '速度比が大きい場合も具体的な上下限は成り立つが、二次近似が実用上十分小さい誤差になるとは限らない。許容精度は別途指定が必要。',
        '秒の実現と換算規約は外部に残る。一般の実切断の演算法則と全速度域の極限の機械的証明、原刊照合と全文の意味確認は未完。',
        '正の時間幅で進み率を評価する。単一時刻での絶対指示の大小から遅れを結論しない。',
        'AからBへの移送、初期同期と到着時の比較、加速・折れ線と曲線への適用は後続の本文として未接続。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for compose,name in ((generic_composed,'clock-delay'),(source_composed,'einstein-clock-delay')):
        text,basis=compose()
        for relative,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/relative
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored clock delay differs: '+relative)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Per-second delay, elapsed readings and fourth-order approximation composed')


if __name__=='__main__':main()
