"""Present the charged-particle setup and its sole local rest-law assumption."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_point_particle_dynamics import SETTING,CASES,PROFILES,ACCEL,DOMAIN,CURVE,POINT,ROLES,REST,VECTOR,args,coord,ZERO,ONE
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-point-particle-dynamics.noema';PARENT_BASIS='data/point-particle-dynamics-basis-v1.json'
FULL='examples/v014/einstein-electron-rest-law-claim.noema';CORE='examples/v014/electron-rest-law-claim-core.noema'
BASIS='data/electron-rest-law-claim-basis-v1.json';ANNOTATIONS='data/electron-rest-law-claim-identifiers-v1.json';INDICES=(413,414)
RIGHT=[('domain',DOMAIN),('velocity',PROFILES[0][1]),('time',R),('acceleration',R)]
FUTURE=[('domain',DOMAIN),('point',POINT)]+PROFILES+ACCEL
MOTION=[('domain',DOMAIN),('curve',CURVE)]
TYPES=' '.join(t for n,t in SETTING)
RULE='i[h['+TYPES+'] c]';SCALAR='i[h['+TYPES+'] '+R+']';POSITION='i[h['+TYPES+'] '+POINT+']'
PRIMITIVES={
 'eiswx':([('node','a'),('author','a'),('subject','a'),('premise','i[e]'),('scope','a'),('reference','d')],'同じauthorがnodeの導出段階で、同じsubjectの運動を支配する法則について、premiseの閉じた内容を独立な前提として採用する。範囲はscopeでの同じ対象の運動法則であり、対象を置く設定、記号や単位の意味規約、先行の背景原理、採った前提から得る帰結を独立な追加前提として数えない。前提の内容は引用の合成規則で与え、実証済み又は現実に真とはしない。一つの前提の同値な表示はその同じ指定内容へ正規化して参照し、式の行数を前提数と同一視しない。'),
 'eiswy':([('designation','a'),('setting',RULE),('selector',SCALAR),('document','a'),('scope','a'),('reference','d')],'同じdocumentとscopeで、designationの数量の意味を、閉じたsettingの条件を満たす同じ設定からselectorが取り出す実数値として指定する。対象・出来事・系・単位・値の物理的帰属をsettingに保持し、他の設定での値や単なる綴りへ取り替えない。記号解釈であり、全設定の実在又はその運動法則の真理を要求しない。既存の設定からの量の射影と同じ構成を、点粒子の設定引数型で使う。'),
 'eiswz':([('designation','a'),('axes','j[a]'),('setting',RULE),('selector',POSITION),('document','a'),('scope','a'),('reference','d')],'同じdocumentとscopeで、designationという順序付き座標表記を、settingの同じ対象・系・出来事・尺度からselectorが取り出す座標関数のaxesの各値へ対応させる。axesの順・区別と同じ設定を保ち、場の三成分、速度又は別の対象の座標へ交換しない。指定していない軸の値を表記へ追加せず、実測済みや記号の字面からの物理的帰属を含めない。'),
 'eisxa':([], 'u0240冒頭の電磁場中で電荷εを持つ点状粒子を運動させる仮定的設定の箇所。'),
 'eisxb':([], 'u0240の括弧内im folgenden Elektron genanntの、以後の呼称を採る箇所。'),
 'eisxc':([], 'u0240のüber dessen Bewegungsgesetz wir nur folgendes annehmen:という運動法則の前提を限定して予告する箇所。'),
 'eisxd':([], 'u0241の瞬間静止を条件として直後の運動を同じ三式へ結ぶ導入箇所。'),
 'eisxe':([], 'u0242の三行の運動方程式M0395を表示する箇所。'),
 'eisxf':([], 'u0243のwobei以下で座標と低速時の質量の意味を説明する箇所。'),
 'eisxg':([], '同じ論説の第十節という論述範囲。u0239の見出しから第十節の本文末までを対象とする。'),
 'eisxh':([], 'u0240で仮定的に導入する同じ点状荷電粒子の参照。物理的内容はek34とek36で与え、以後の電子という呼称の対象とする。'),
 'eisxi':([], 'u0240で同じ導入粒子に採るElektronという呼称。現代の特定粒子種又は固定された負の電荷値を名称から補わない。'),
 'eisxj':([], 'u0240の同じ粒子の電気量εの表記。値・符号・単位と物理的帰属は同じek34のchargeの射影へ結ぶ。'),
 'eisxk':([], 'u0243の同じ粒子の座標x,y,zの順序付き表記。意味は同じek34のpointの三空間軸への射影へ結ぶ。'),
 'eisxl':([], 'u0243の低速時の同じ粒子の慣性質量μの表記。意味は同じek34のmassの射影へ結ぶ。'),
 'eisxm':([], 'u0239の第十節見出しの箇所。見出しの主題全体の判断は別途行い、この参照だけで緩い加速の意味を済ませない。'),
}
MEANINGS={
 'ek3y':'同じ時間領域のうち、有効な時刻time以上の有効な時刻だけを取る右側領域。基点timeを含め、過去側を含めず、元の局所領域の外へ延長しない。',
 'ek3z':'元の時間領域の両側内点timeで、同じ速度関数の右側領域ek3yにおける差商極限sjsが同じaccelerationとなる。通常実数の右微分として直後の初期変化を指定し、有限時間全体で一定加速する条件を加えない。',
 'ek32':'同じ四座標の時刻成分と時間領域を共有し、三つの実速度関数の右微分を対応する三つの座標加速度へek3zで結ぶ。別の時点や時刻軸の微分に替えない。',
 'ek33':'同じ瞬間静止ek3rを条件に、三つの局所方程式ek3tと、同じ加速度による直後への初期速度変化ek32を結ぶ。前後の静止、一定加速度の有限区間、後続の任意速度の運動法則を先取りしない。',
 'ek34':'同じ点粒子の物理的設定ek3vに、対象が導入参照eisxh、系がK=raであることを固定する。記号解釈、導入、条件付き法則でこの同じ全設定を共有する。',
 'ek4m':'指定時間領域に、第一時刻より後の第二時刻があり、曲線の少なくとも一空間座標が異なるという実際の位置変化。全時刻の速度非零を要求せず、途中又は初期の瞬間静止を許す。履歴・座標の妥当性はek34とともに用いる。',
 'ek35':'同じ評価点の全設定でek34ならek33となる閉じた条件付き法則。著者が独立に採る一つの運動法則の前提として、三行を一組の内容へまとめる。',
 'ek36':'同じ導入粒子に、ek34の物理的設定とek4mの位置変化を持つ局所的な運動履歴があるという仮定内容。現実の粒子の存在は著者の設定操作から実行しない。',
 'ek37':'同じ設定のchargeを取り出す射影。εを質量、正電荷だけ、値1へ替えない。',
 'ek4a':'同じ設定のpointという座標関数を取り出す射影。表記では指定した三空間軸だけを順に使い、時刻軸を第四の座標表記へ加えない。',
 'ek4b':'同じ設定のmassという低速慣性質量の値を取り出す射影。今の運動速度が低速であることを付加せず、基準となる低速域の係数を保持する。',
 'ek4c':'ε、x,y,z、μの意味を同じ物理的設定ek34と三つの射影へ結ぶ。記号だけで量の種類を済ませず、説明のwobeiに対応する同じ粒子・出来事・系・単位の解釈規約をまとめる。',
 'ek4d':'著者が同じ粒子参照を導入し、位置変化を持つ局所設定ek36を仮定して議論を進める操作。bewege sichの設定指示であり、物理的に粒子を動かす実験命令ではない。',
 'ek4e':'同じ著者が括弧内で、同じ導入粒子に以後Elektronという呼称を採る。物理的な粒子の生成や現代の電子への分類を意味しない。',
 'ek4f':'同じ著者・導入粒子・第十節・導出段階で、運動法則について独立に採る前提が同じek35に限られるという全引用内容の条件と、その同じ内容の仮定採用ug。背景原理、記号解釈、導出した帰結まで否定しない。',
 'ek4g':'限定した前提の予告から瞬間静止の条件、三式の表示、座標と質量の説明へ、同じ内容の説明関係と本文順序を結ぶ。表示式は同じ条件付きek35を受け、無条件の法則又は検証器の証明にしない。',
 'ek4h':'命名、限定した前提、同じ数量表記の意味、条件から表示と意味説明への接続を一続きの著者提示として統合する。導入・括弧・限定・条件・式・意味説明の各箇所は区別する。',
 'ek4i':'仮定的な粒子設定ek4dを行う指示の伝達形式。',
 'ek4j':'粒子設定の指示を同じ著者・論説へ帰属し、第十節見出しの後へ置く新主張413。',
 'ek4k':'命名・限定した前提・条件付き表示・意味説明の統合内容ek4hを断定として伝える形式。',
 'ek4l':'括弧内の命名から意味説明までの提示を同じ著者・論説へ帰属し、同じ粒子の設定指示に続ける新主張414。',
}
LIMITS=[
 'u0240–u0243を原刊917頁に照合する。u0240の設定指示と、その後の命名・運動法則の仮定・表示・意味説明を二つの伝達形式で保持する。第十節見出しu0239の緩い加速と動力学の主題全体は別の範囲。',
 'In einem ... bewege sichは、同じ点状粒子が電磁場の中で動く仮定的な場合を置く指示と読む。導入内容では実際の位置変化を要求するが、途中の瞬間静止を許す。現実の粒子、実験の実行、全時刻の速度非零は要求しない。',
 'im folgenden Elektron genanntは同じ論説の以後の呼称の採用である。点状担体の理想化と電荷εは既存の物理的設定へ接続し、現代の固定負電荷、粒子種、量子論又は第九節の剛体担体への同一視を加えない。',
 'nur folgendes annehmenは、同じ粒子の運動法則に関してこの導出段階で独立に採る前提が、後続の条件付き三式に限られるという読み。三式を一つのベクトル法則の内容として参照し、同値な表示は同じ指定内容へ正規化する。背景の運動学的原理、単位や物理量の意味、対象の設定、後の導出結果まで存在しないとは述べない。',
 'in einer bestimmten Epocheは、任意の設定で選んだ同じ出来事の座標時刻である。in dem nächsten Zeitteilchenは、その時刻の右側への初期速度変化を通常実数の右差商極限で与える読みを採る。基点を含む右側領域を用い、物理的な最小時間粒や非アルキメデス無限小、固定長の時間区間を仮定しない。',
 '同じ速度関数の両側微分と右側微分を同じ加速度に結び、μa=εEの三成分を同じ初期変化へ用いる。有限時間ずっと静止又は一定加速、有限時間の厳密な二次軌道、微分方程式の解の存在一意性をこの文へ補わない。',
 '座標x,y,zと時間tは同じ校正座標の値、εは同じ出来事の符号付き非零電荷、μは同じ粒子の低速域の慣性係数である。sofern dasselbe langsam bewegt istはμの意味の限定として保持し、現在の全設定を低速に制限しない。三記号群を同じek34の設定から取り出すため、別粒子や別時点の量を接合しない。',
 '古典的な局所モデルの正の慣性質量、完全な二階微分可能な局所履歴、整合単位という明示した読みを継承する。Kでの同じ電場と磁場の設定を保つが、真空・無磁場・無放射・局所保存則を追加前提にしない。',
 '導入の存在は仮定内容に保持し、法則の条件性・仮定採用・式の表示・意味説明・著者帰属から物理的な真理を導かない。有限モデルは接続の診断であり、全連続体、全引用内容又は原文同義性の自動証明ではない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('ek3y',RIGHT[:1]+[RIGHT[2]],lam('candidate',R,both(k('ba',v('time')),k('ba',v('candidate')),app(v('domain'),v('candidate')),k('bc',v('time'),v('candidate')))),DOMAIN)
    text+=define('ek3z',RIGHT,both(k('senz',v('domain'),v('time')),k('sjs',k('ek3y',v('domain'),v('time')),v('velocity'),v('time'),v('acceleration'))))
    moment=coord(v('point'),ROLES[3])
    text+=define('ek32',FUTURE,both(*(k('ek3z',v('domain'),v(profile),moment,v(acc)) for (profile,t),(acc,s) in zip(PROFILES,ACCEL))))
    text+=define('ek33',SETTING,op('y',k('ek3r',*args(REST)),both(k('ek3t',*args(VECTOR)),k('ek32',*args(FUTURE)))))
    text+=define('ek34',SETTING,both(k('ek3v',*args(SETTING)),op('e',v('matter'),k('eisxh')),op('e',v('frame'),k('ra'))))
    a,b=v('first'),v('last');different=op('x',op('u',k('sca',coord(app(v('curve'),a),'yn'),coord(app(v('curve'),b),'yn'))),op('x',op('u',k('sca',coord(app(v('curve'),a),'yo'),coord(app(v('curve'),b),'yo'))),op('u',k('sca',coord(app(v('curve'),a),'yp'),coord(app(v('curve'),b),'yp')))))
    text+=define('ek4m',MOTION,quantified('g',[('first',R),('last',R)],both(k('ba',a),k('ba',b),k('bg',a,b),app(v('domain'),a),app(v('domain'),b),different)))
    cases=[(('location' if n=='point' else n),t) for n,t in CASES]
    bound=args(SETTING,frame=k('ra'),context=v('point'),electricconversion=ONE,point=v('location'))
    text+=content('ek35',quantified('f',cases,op('y',k('ek34',*bound),k('ek33',*bound))))
    text+=content('ek36',quantified('g',cases,both(k('ek34',*bound),k('ek4m',v('domain'),v('curve')))))
    for name,target,result in [('ek37','charge',R),('ek4a','point',POINT),('ek4b','mass',R)]:text+=define(name,SETTING,v(target),result)
    p=v('point');author=k('rd');paper=k('eirf');scope=k('eisxg');particle=k('eisxh');axes='l[a][k yn[] k yo[] k yp[]]'
    quantities=[k('eiswy',k(name),'r[p ek34]','r[p '+selector+']',paper,scope,p) for name,selector in [('eisxj','ek37'),('eisxl','ek4b')]]
    text+=content('ek4c',both(*quantities,k('eiswz',k('eisxk'),axes,'r[p ek34]','r[p ek4a]',paper,scope,p)))
    text+=content('ek4d',both(k('eisd3',k('eisxa'),particle,paper,p),k('ug',k('eisxa'),author,quote('ek36'),scope,p)))
    text+=content('ek4e',k('eisd4',k('eisxb'),author,k('eisxi'),particle,paper,p))
    adopted=k('eiswx',k('eisxc'),author,particle,v('premise'),scope,p)
    text+=content('ek4f',both(k('ug',k('eisxc'),author,quote('ek35'),scope,p),q('f','premise','i[e]',op('z',adopted,op('e',v('premise'),quote('ek35'))))))
    links=[('eisxc','eisxd'),('eisxd','eisxe'),('eisxe','eisxf')]
    text+=content('ek4g',both(k('eisox',k('eisxe'),quote('ek35'),p),*(k('uf',author,k(a),k(b),p) for a,b in links),*(k('ue',k(a),k(b),p) for a,b in links),k('uf',author,k('eisxf'),k('eisxe'),p)))
    nodes=('eisxa','eisxb','eisxc','eisxd','eisxe','eisxf')
    text+=content('ek4h',both(*(op('t',k(n),p) for n in ('ek4e','ek4f','ek4c','ek4g')),k('ue',k('eisxa'),k('eisxb'),p),k('ue',k('eisxb'),k('eisxc'),p),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ek4i[] f[j m[k ek4d[]]].\n'
    text+=define('ek4j',[],both(k('eir3',k('eisxa'),author,paper,quote('ek4i'),k('ri')),k('ue',k('eisxm'),k('eisxa'),k('ri')),op('u',op('e',k('eisxm'),k('eisxa')))))
    text+='d ek4k[] f[j s[k ek4h[]]].\n'
    text+=define('ek4l',[],both(k('eir3',k('eisxb'),author,paper,quote('ek4k'),k('ri')),k('ue',k('eisxa'),k('eisxb'),k('ri')),op('u',op('e',k('eisxa'),k('eisxb')))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek4j','ek4l')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='electron_setup_naming_sole_rest_law_and_coordinate_meanings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/point-particle-dynamics-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]) for n,form in [('eisxi','Elektron'),('eisxj','ε'),('eisxk','(x,y,z)'),('eisxl','μ')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
