"""Connect the final heading to dynamics of the same slowly accelerated electron."""
from scripts.compose_complete_motion_expression import *
from scripts import compose_point_particle_dynamics as particle

PARENT=FULL;PARENT_BASIS=BASIS;PARENT_ANNOTATIONS=ANNOTATIONS
FULL='examples/v014/einstein-tenth-section-heading.noema';CORE='examples/v014/tenth-section-heading-core.noema'
BASIS='data/tenth-section-heading-basis-v1.json';ANNOTATIONS='data/tenth-section-heading-identifiers-v1.json'
SMALL=particle.ACCEL+[('bound',R)]
LOCAL=[('domain',DOMAIN),('curve',CURVE)]+particle.PROFILES+[('time',R)]+particle.ACCEL
SLOW=particle.HISTORY+particle.PROFILES+[('bound',R),('scope','a')]
SETTING=particle.SETTING+[('bound',R)]
VARIABLES=[(('location' if n=='point' else n),t) for n,t in SETTING if n not in ('frame','context','electricconversion')]
MEANINGS={
 'evf':'三つの有効な座標加速度と正の比較基準について、ax²+ay²+az²<bound²を要求する。三次元の大きさの上限であり、各成分が個々に小さいだけの場合や速度の小ささへ替えない。',
 'evg':'同じ実軌道の三空間座標について、同じ時間領域の一階微分関数とその時刻での二階微分sepoを三加速度へ結ぶ。異なる軌道や時刻、固有時の微分へ替えない。',
 'evh':'同じ校正された完全な非空履歴ek3pと、全区間の外で固定した正の程度基準eiszxを共有し、全有効時刻で実三加速度evgの大きさがevfを満たすという緩い加速。単独の時刻・端点だけで代表させず、無放射・低速・運動方程式を含めない。',
 'evi':'同じ電子・Kの点状荷電粒子、低速慣性質量、単位、場、実履歴の物理設定ek34に、同じ履歴の緩い三次元加速evhを結ぶ。括弧の限定を別粒子・別過程の加速へ分離しない。',
 'evj':'同じ第十節・K・導入粒子についてeviの全役割を一組で存在量化した見出しの設定記述。引用の中の研究対象であり、実際の電子の存在や見出しでの実験を要求しない。',
 'evk':'同じ研究が、緩い加速をする電子の物理設定evjと、同じ対象・力・慣性・実加速度を結ぶ運動法則の定式化elmを対象として、規則性・成立条件・原理との関係・説明と導出を扱う動力学の主題。設定だけの運動学又は法則の真理の主張とは分ける。',
 'evl':'第二部に直接属する深さ2・表示番号10の第十節を、同じ電子の動力学evkの主題へ結ぶ見出し。第九節の定理末尾、見出し、粒子設定導入という順序と箇所の区別を保つ。',
}
LIMITS=[
 '原刊917頁u0239の§ 10. Dynamik des (langsam beschleunigten) Elektrons.を確認した。第九節の定理末尾eiswvから既存の見出しeisxm、同じ第十節eisxg、直後の導入eisxaへ結ぶ。第二部の深さ2・番号10として扱う。',
 'Elektronは直後に仮定的に導入して以後そう呼ぶ同じ点状荷電粒子。現代の固定負電荷や量子粒子の性質を名前から追加しない。物理的設定ek34と運動法則の定式化elmを既存のまま再利用する。',
 '括弧内のlangsam beschleunigtenは、同じ系・長さ時間尺度・第十節の文脈的な正の基準より、全対象区間の実三加速度の大きさが小さいという理想化の限定として読む。基準はeiszxで指定し、軌道を見て都合のよい大きい数を選ぶだけにしない。',
 '緩さは速度ではなく加速度の大きさへ掛かる。全三成分を合成し、直線運動・x軸だけ・全軌道の円を要求しない。微分は同じ校正座標時刻についての実二階微分である。無放射や特定の放射理論は見出しに補わない。',
 'Dynamikは同じ粒子の場による作用・慣性・運動変化を結ぶ法則の規則性、条件、説明、導出を扱う主題。既存eisthで設定と検討する定式化を分け、物理的実例・法則の真理・導出成功を見出しの成立条件にしない。',
 '原始関係を追加せず、既存の物理履歴・微分・程度基準・研究主題・見出し階層から合成する。旧446主張と意味・証拠を保存する。全原文単位の判断後も二作品の最終完成監査は別に行う。',
]
def definitions():
    zero=k('bb',rat(0));bound=v('bound');sq=lambda x:k('shv',x,x)
    norm=k('bd',k('bd',sq(v('ax')),sq(v('ay'))),sq(v('az')))
    text=define('evf',SMALL,both(*(k('ba',v(n)) for n,t in SMALL),k('bg',zero,bound),k('bg',norm,sq(bound))))
    parts=[]
    for axis,(profile,t),(acc,s) in zip(ROLES[:3],particle.PROFILES,particle.ACCEL):
        position='i[moment '+R+']['+coord(app(v('curve'),v('moment')),axis)+']'
        parts.append(k('sepo',v('domain'),position,v(profile),v('time'),v(acc)))
    text+=define('evg',LOCAL,both(*parts))
    time=v('time');selected=both(k('ba',time),app(v('domain'),time))
    small=quantified('g',particle.ACCEL,both(k('evg',*args(LOCAL)),k('evf',*args(SMALL))))
    text+=define('evh',SLOW,both(k('ek3p',*args(particle.HISTORY)),k('ba',bound),k('bg',zero,bound),k('eiszx',v('frame'),v('lengthunit'),v('timeunit'),bound,v('scope'),v('context')),q('f','time',R,op('y',selected,small))))
    supplied={n:v(n) for n,t in SETTING}|{'scope':k('eisxg')}
    text+=define('evi',SETTING,both(k('ek34',*args(particle.SETTING)),k('evh',*[supplied[n] for n,t in SLOW])))
    fixed={'frame':k('ra'),'context':v('point'),'electricconversion':k('bb',rat(1)),'point':v('location')}
    text+=content('evj',quantified('g',VARIABLES,k('evi',*[fixed.get(n,v(n)) for n,t in SETTING])))
    text+=define('evk',[('inquiry','a'),('context','d')],k('eisth',v('inquiry'),quote('evj'),quote('elm'),v('context')))
    node=k('eisxm');previous=k('eiswv');following=k('eisxa');p=k('ri')
    text+=define('evl',[],both(k('eihq',node,k('eisxg'),k('eispb'),k('eirf'),num(2),num(10),'r[p evk]',p),k('ue',previous,node,p),k('ue',node,following,p),op('u',op('e',previous,node)),op('u',op('e',node,following))))
    return text
@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==446
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='evl',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='tenth_section_slowly_accelerated_electron_dynamics_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[446]).document
    ann=json.loads(read(PARENT_ANNOTATIONS));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
