"""Return the same reflected wave to K and preserve every printed equality."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_wave_transform_application import transformed
from scripts.compose_reflected_light_inquiry import RETURN
from scripts.compose_wave_cycle_frequency import HARMONIC
from scripts.compose_doppler_infinity import quantified
from scripts.compose_mirror_wave_quantities import SETTING as PRIOR_SETTING,FIXED

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-mirror-wave-quantities.noema';PARENT_BASIS='data/mirror-wave-quantities-basis-v1.json'
FULL='examples/v014/einstein-reflected-return-quantities.noema';CORE='examples/v014/reflected-return-quantities-core.noema'
BASIS='data/reflected-return-quantities-basis-v1.json';ANNOTATIONS='data/reflected-return-quantities-identifiers-v1.json';INDICES=[400,401]
LAB_ANGLE=[(n,R) for n in ('labanglecos','labanglesin','labratio','labprincipal','labangle')]
SETTING=PRIOR_SETTING+LAB_ANGLE+[(n,R) for n in ('labamplitude','labperiod','labfrequency')]
VARIABLES=[(n,t) for n,t in SETTING if n not in FIXED]
NAMES=[('ektc','eisuw','labamplitude','A‴'),('ektd','eisux','labangle','φ‴'),('ekte','eisuy','labfrequency','ν‴')]
PRIMITIVES={
 'eisuu':([], 'u0220の、最後に同じ反射光を静止系Kへ戻す変換によって量を得るという導入箇所。'),
 'eisuv':([], 'u0221=M0376の三行・各二等号を持つ表示箇所。原刊の周波数最右辺の分母も保持する。'),
 'eisuz':([('node','a'),('author','a'),('series','h[a] c'),('scope','a'),('context','d')], 'authorがscopeの指定されたseriesの説明段階について、nodeを締めくくりの段階として提示する。単なる前後関係とは区別し、論説全体の終了、時間的な永久終了、提示内容の真理又は計算成功は含意しない。seriesは具体的な対象や式と独立な文章箇所の範囲で、各段階の内容と順序は別に構成する。'),
}
for rule,symbol,field,label in NAMES:PRIMITIVES[symbol]=([],f'同じ反射光をKで表す{label}の局所表記個体。量の種類・同じ対象と設定の結合は{rule}で定める。')
MEANINGS={
 'eks3':'同じ90設定でekrzを保持し、kで反射して速度−vでKへ戻した六係数の同じ選択側の大きさ、戻した法線とKの+x軸との実数角、同じ戻した位相の周期数を結ぶ。印刷等式は前件に含めない。',
 'eks4':'value*(1+(v/V)*cosφ″)/sqrt(1−(v/V)²)。ekr2の速度を−vにして逆変換の表示右辺を構成する。',
 'eks5':'同じ旧角と速度による1−2(v/V)cosφ+(v/V)²の分子。',
 'eks6':'value*eks5/(1−(v/V)²)。振幅の最右辺及び物理的な周期数の比較候補であり、周波数の原刊分母へ置き換えない。',
 'eks7':'−((1+(v/V)²)cosφ−2(v/V))/eks5というKでの方向余弦の表示最右辺。外側の負号を保持する。',
 'ekta':'value*eks5/(1−v/V)²という原刊の周波数最右辺。eks6の分母と異なる式を意図的に保存する。',
 'ektb':'M0376の三行について、A‴・cosφ‴・ν‴と中間右辺、中間右辺と最右辺の全六等式を保持する。同じ90設定を共有し、等式を物理設定の成立条件へ移さない。',
 'ektf':'Kでの同じ反射光の三つの量の表記を同じ論説・状況へ命名する。',
 'ektg':'K・V・先行波範囲・状況を固定した86証人による同じ鏡と逆変換量eks3の構成。逆変換は同じk入射波の反射を先に行ってから速度−vでKへ戻す既存ekrk–ekrnであり、別の波の選択ではない。',
 'ekth':'同じ86役割の全割当でeks3なら全六表示等式ektbという著者の内容。引用された不一致を外側の物理設定へ混入させない。',
 'ekti':'同じ反射のkでの表示からKへの再表示を、逆変換の構成ektgから全三行ekthを得るという著者の帰結として提示する。前の反射表示への照応、コロン、順序、入射指定→k反射→Kへの帰還の締めくくりというEndlichを保持する。',
 'ektj':'同じ反射光のKでの三表記を命名し、u0221の三行表示をekthへ結ぶ。',
}
for rule,symbol,field,label in NAMES:MEANINGS[rule]=f'同じwaveと{field}及び状況に、K・V・範囲を固定した84証人のeks3を結ぶ{label}の命名規則。印刷等式を語義へ含めない。'
for shown,msg,stmt,node,previous in [('ekti','ektk','ektl','eisuu','eisuk'),('ektj','ektm','ektn','eisuv','eisuu')]:
    MEANINGS[msg]=f'同じ提示内容{shown}を述べるメッセージ。'
    MEANINGS[stmt]=f'箇所{node}の{msg}を著者・論説へ帰属し、{previous}からの順序と箇所の区別を保持する。'
LIMITS=[
 'u0220–u0221とM0375–M0376を対象とする。原刊914頁末の導入と915頁冒頭の全三行、各二等号、根号・括弧・外側負号・三重プライムを保存する。',
 '完全鏡、同じ局所波モデル・両系・相互作用・単位・二偏光を継承し、kでの反射を速度−vでKへ戻す既存の三次元変換を再使用する。三重プライムは新しい光ではなく同じ反射光のK表示である。',
 'A‴は同じ電気側又は磁気側の非負の大きさ、ν‴は同じ位相の最小時間周期の逆数と読む。φ‴は戻したK法線とKの正速度方向+xとの角とする。旧φもこの軸に対する源―観測者方向の角である。kのφ′・φ″の先行結線角の読解は変更しない。',
 'M0376の周波数最右辺の分母(1−v/V)²は原刊にも存在する。振幅行の1−(v/V)²とは別であり、訂正した式を原文として代用しない。V5,v3の正面入射、旧周波数2では逆変換と中間右辺は1/2、原刊最右辺は2になる。',
 '継承した結線角の読みでは、斜め入射の中間右辺にも不一致がある。kの角を座標縦方向の余弦へ黙って変更せず、物理的逆変換候補、角の定義、著者が提示する六等式を区別する。',
 'Endlichは入射量の指定、kでの反射、Kへの帰還というこの局所の説明系列の最終段階と読む。後続の光圧の議論や論説全体が終了したという読みではない。得る・逆変換によっては著者の導出提示であり、式の健全性又は実験の実施済みを補わない。',
 '新一般関係eisuzは指定された説明系列の締めくくりの提示だけを扱い、光・K・変換・数式の意味を含まない。逆変換、量、式、照応、帰結、コロン、帰属と順序は既存規約で合成する。',
 '全実数・全関数の量化を有限対照へ縮めない。検査は接続・数値対照・引用・提示の証拠であり、物理法則又は意味同義性の自動証明ではない。後続の仕事・エネルギー収支・光圧と二作品全体は未完。',
]

def name_witnesses(field):return [(n,t) for n,t in SETTING if n not in {'wave','frame','light','scope','context',field}]

def returned_args():
    amps,shifted,_,_=transformed(v('speed'))
    return [v('light'),v('speed'),*shifted,*amps]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,meaning) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b');V=v('light');speed=v('speed');cos=v('anglecos');ret=returned_args()
    get=lambda name:[app(k(name,*ret),k(axis)) for axis in ('yn','yo','yp')]
    text+=define('eks3',SETTING,both(k('ekrz',*args(PRIOR_SETTING)),k('ekhz',v('magneticside'),*get('ekrm'),*get('ekrn'),v('labamplitude')),k('ekgf',*get('ekrl'),one,zero,zero,*[v(n) for n in ('labanglecos','labanglesin','labratio','labprincipal','pi','labangle')]),k('ekc7',*args(HARMONIC),k('ekrk',*ret),zero,v('labperiod'),v('labfrequency'))))
    scalar=[(n,R) for n in ('light','speed','value','anglecos')];geom=[(n,R) for n in ('light','speed','anglecos')]
    text+=define('eks4',scalar,k('ekr2',V,k('be',speed),v('value'),cos),R)
    ratio=k('shv',speed,k('sjd',V));square=k('shv',ratio,ratio);numerator=k('bd',k('bf',one,k('shv',two,k('shv',ratio,cos))),square)
    text+=define('eks5',geom,numerator,R)
    text+=define('eks6',scalar,k('shv',k('shv',v('value'),k('eks5',*args(geom))),k('sjd',k('bf',one,square))),R)
    text+=define('eks7',geom,k('be',k('shv',k('bf',k('shv',k('bd',one,square),cos),k('shv',two,ratio)),k('sjd',k('eks5',*args(geom))))),R)
    den=k('bf',one,ratio)
    text+=define('ekta',scalar,k('shv',k('shv',v('value'),k('eks5',*args(geom))),k('sjd',k('shv',den,den))),R)
    mid=[k('eks4',V,speed,v('refamplitude'),v('refanglecos')),k('sdo2',V,k('be',speed),v('refanglecos')),k('eks4',V,speed,v('reffrequency'),v('refanglecos'))]
    right=[k('eks6',V,speed,v('amplitude'),cos),k('eks7',V,speed,cos),k('ekta',V,speed,v('frequency'),cos)]
    text+=define('ektb',SETTING,both(*(k('sca',a,b) for lhs,middle,last in zip(('labamplitude','labanglecos','labfrequency'),mid,right) for a,b in [(v(lhs),middle),(middle,last)])))
    for rule,symbol,field,label in NAMES:
        fixed=dict(FIXED,context=v('context'),wave=v('object'));fixed[field]=v('value')
        text+=define(rule,[('object','a'),('value',R),('context','d')],quantified('g',name_witnesses(field),k('eks3',*[fixed.get(n,v(n)) for n,t in SETTING])))
    text+=content('ektf',both(*(k('eislo',k(symbol),'r[p '+rule+']',k('eirf'),v('point')) for rule,symbol,field,label in NAMES)))
    actual=[FIXED.get(n,v(n)) for n,t in SETTING]
    text+=content('ektg',quantified('g',VARIABLES,k('eks3',*actual)))
    text+=content('ekth',quantified('f',VARIABLES,op('y',k('eks3',*actual),k('ektb',*actual))))
    p=v('point');author=k('rd');scope=k('eistk');node=k('eisuu');display=k('eisuv')
    series='i[item a]['+op('x',op('e',v('item'),k('eisuh')),op('x',op('e',v('item'),k('eisuj')),op('e',v('item'),node)))+']'
    text+=content('ekti',both(k('zc',node,author,quote('ektg'),quote('ekth'),scope,p),k('eissb',node,k('eisuk'),author,quote('ekso'),quote('ekth'),scope,p),k('eisra',node,author,k('eirf'),k('eisuj'),quote('ekso'),quote('ekth'),scope,p),k('eisuz',node,author,series,scope,p),k('ue',k('eisuh'),k('eisuj'),p),k('ue',k('eisuj'),node,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ektj',both(evaluate('ektf'),k('eisox',display,quote('ekth'),p)))
    for shown,msg,stmt,item,previous in [('ekti','ektk','ektl','eisuu','eisuk'),('ektj','ektm','ektn','eisuv','eisuu')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(item),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==400
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ektl','ektn')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_reflected_wave_return_and_all_printed_equalities_preserved',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/mirror-wave-quantities-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=symbol,role='designation',forms=[dict(text=label,language='de',role='printed_identifying_form')]) for rule,symbol,field,label in NAMES]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
