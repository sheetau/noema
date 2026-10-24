"""Name enclosed light energies and present the general and zero-angle ratios."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_volume_ratio import ROOT,read,SETTING,FIXED,NAME
from scripts.compose_mean_light_energy import TOTAL,ARITHMETIC
from scripts.compose_observed_amplitude import SETTING as AMPLITUDE
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-light-volume-ratio.noema';PARENT_BASIS='data/light-volume-ratio-basis-v1.json'
FULL='examples/v014/einstein-light-energy-ratio.noema';CORE='examples/v014/light-energy-ratio-core.noema'
BASIS='data/light-energy-ratio-basis-v1.json';ANNOTATIONS='data/light-energy-ratio-identifiers-v1.json';INDEX=392
PRINTED=[(n,R) for n in ('light','speed','anglecos')]
PRODUCTS=[(n,R) for n in ('pi','amplitude','newamplitude','volume','newvolume')]
DISPLAY=PRINTED+ARITHMETIC
VARIABLES=[(n,t) for n,t in TOTAL if n not in FIXED]
PRIMITIVES={
 'eist2':'u0210の同じ面に囲まれた光エネルギーを各系でE/E′と名づけ、その比を導く本文箇所。',
 'eist3':'u0211=M0365の総量比・平均密度と体積の積の比・一般速度角の式を等号で結ぶ表示箇所。',
 'eist4':'u0212の直前の同じ式がφ=0でより簡明な形へ移るという関係節とコロンの箇所。',
 'eist5':'u0213=M0367のφ=0でのE′/E=√((1−v/V)/(1+v/V))の表示箇所。',
 'eist6':'この箇所で同じ放射部分の旧静止系での平均総エネルギーを指す量記号E。',
 'eist7':'この箇所で同じ放射部分の新移動系での平均総エネルギーを指す量記号E′。',
}
MEANINGS={
 'ekpj':'同じV,v,cosφから(1−(v/V)cosφ)/√(1−(v/V)²)を構成する。平方根を分母に置き、前の体積比と逆の因子を保つ。',
 'ekpk':'同じpi、旧新振幅、旧新体積から(A′²*S′/(8*pi))/(A²*S/(8*pi))を構成する。二つの平均密度をそれぞれの体積へ掛け、総量比の中間表示を明示する。',
 'ekpl':'有効な許容速度・角余弦、正のpi・旧振幅・二体積・旧総量と非負の新振幅・新総量について、E′/E=ekpk及びekpk=ekpjを同じ値で要求する。両等号と分子分母を保存し、0/0を認めない。',
 'ekpm':'同じ70設定で先行ekn7の物理的な同じ部分・二系・単位・平均・領域履歴を保持し、各系の重み付き空間積分ekmgを同じenergy/newenergyへ結ぶ。比を述べる旧総量だけは正とする。E=ρS、振幅比、体積比、総量比を前件へ追加しない。',
 'ekpn':'同じ70設定から十個の表示量をekplへ渡す一般表示の帰結。同じ対象・角・振幅・体積・エネルギーを共有する。',
 'ekpo':'同じ対象objectと状況contextでK,V,波の範囲を固定し、ekpmの旧系energy=valueとなる64残余証人を存在量化するEの量取得規則。',
 'ekpp':'同じ設定と対象の新系newenergy=valueを指定するE′の量取得規則。旧系の総量を新系へ流用しない。',
 'ekpq':'同じ論説・状況でEとE′をekpo/ekppの型付き量取得規則へ結ぶ命名。測定とは各系の校正単位で量を評価する役割であり、実験済みの記録を追加しない。',
 'ekpr':'同じ65全称役割でekpmなら、既存の各E=ρSのekmj、同じS′/Sのekoz、同じ電気側の二乗振幅変換ekijとなるという導出の前提内容。これらの関係を物理設定ekpmの許容条件へ混ぜない。',
 'ekps':'同じ65全称役割とekpmの下で、同じ総量の二等号の一般表示ekpnを述べる内容。',
 'ekpt':'同じ70設定のekpmに旧実数角angle=0を加える零角の場合。余弦だけを1へ替えたり、別の系の角を零にしたりしない。',
 'ekpu':'同じV,vから√((1−v/V)/(1+v/V))を構成する。和と差の向き及び比全体の正の平方根を保持する。',
 'ekpv':'同じ許容V,vと正の旧総量、非負の新総量についてE′/E=ekpuを述べる特殊表示の帰結。一般形との一致や零角条件は別に接続する。',
 'ekpw':'同じ65全称役割で零角条件ekptの下に一般表示ekpnを置く。特殊表示ekpxと適用域をそろえる。',
 'ekpx':'同じ65全称役割と同じ零角条件ekptの下で、同じ新旧総量の特殊表示ekpvを述べる。',
 'ekpy':'二総量の命名、先行密度・体積・振幅から一般比への著者の帰結提示、二表示、関係節の照応と同じ零角での書換え、特殊形が一般形より簡明という厳密比較、二つのコロンと本文順序を一文へ結ぶ。',
 'ekpz':'u0210–u0213の命名・一般比・零角でのより簡明な形という一文のメッセージ。',
 'ekp2':'u0210–u0213の一文を同じ著者と論説へ帰属し、直前の二体積の説明からの順序と各表示・量名の区別を保つ。',
}
LIMITS=[
 '原刊913–914頁のu0210–u0213を一文として読む。M0365の末尾はコンマであり、welche Formel以下の零角特殊化までを同時に接続する。ページ標識A0028は本文上の新しい物理条件ではない。',
 'Lichtenergieは先行する平均密度A²/(8*pi)と同じ位相平均の総量である。各系の同時内部で同じ部分の平均密度を積分する。特定位相の有限球の瞬間総量又は境界を追う時間平均へ読み替えない。',
 '囲む面は前の同じ移動球面とその新系の楕円体面であり、eistmと初期部分輸送を引き継ぐ。各系自身の零時刻の閉内部を用い、新旧零時刻を同じ出来事集合へ等置しない。',
 'gemessenは同じ仕事・交換収支と校正単位に属する量を各系で評価する理想化した役割と読む。個別の測定装置や二実験の実施済み履歴は補わない。命名の二規則は存在証人を持つが、実際の比は一つの70設定で二総量を共有する。',
 '総量の許容条件ekpmは重み付き空間積分を指定する。積分からE=ρS、既存の横波の振幅比、前文の体積比を帰結として引き継ぎ、総量比を前提として選別しない。旧振幅と旧総量は比の分母として正に限定する。',
 'φは先行する同じ旧系の角であり、実数角φ=0からcosφ=1となる既存の規約を使う。純粋な式は符号付き亜光速も診断するが著者の物理設定は既存の0<v<Vを保つ。',
 'einfachereは同じ零角条件での一般表示に比べて特殊表示がより見通しよいという厳密な形式比較eistbである。絶対的な最簡形や計算の容易さ、真理の証明を含めない。一般形から特殊形への移行と評価を分ける。',
 '有限の有理対照と代数補題は全実数の積分論・平方根論・物理法則又は意味同義性の自動証明ではない。π代用品は診断用であり本文の積分的πを置き換えない。後続のエネルギーと周波数の変換法則の同一性、完全鏡、節見出し全体は未完。',
]

def name_variables(which):
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'portion':v('object'),'context':v('context'),which:v('value')}
    return fixed,[(n,t) for n,t in TOTAL if n not in fixed]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES);zero=k('bb','n p a b');one=k('bb','n p b b');mul=lambda a,b:k('shv',a,b)
    positive=lambda x:both(k('ba',x),k('bg',zero,x));nonnegative=lambda x:both(k('ba',x),k('bc',zero,x))
    V=v('light');speed=v('speed');ratio=mul(speed,k('sjd',V));den=k('sky',k('bf',one,mul(ratio,ratio)))
    text+=define('ekpj',PRINTED,mul(k('bf',one,mul(ratio,v('anglecos'))),k('sjd',den)),R)
    old=mul(k('ekle',v('pi'),v('amplitude')),v('volume'));new=mul(k('ekle',v('pi'),v('newamplitude')),v('newvolume'))
    text+=define('ekpk',PRODUCTS,mul(new,k('sjd',old)),R)
    quotient=mul(v('newenergy'),k('sjd',v('energy')))
    guards=[k('s45',V,speed),k('bc',k('be',one),v('anglecos')),k('bc',v('anglecos'),one),*(positive(v(n)) for n in ('pi','amplitude','volume','newvolume','energy')),*(nonnegative(v(n)) for n in ('newamplitude','newenergy'))]
    text+=define('ekpl',DISPLAY,both(*(k('ba',x) for x in args(DISPLAY)),*guards,k('sca',quotient,k('ekpk',*args(PRODUCTS))),k('sca',k('ekpk',*args(PRODUCTS)),k('ekpj',*args(PRINTED)))))
    D=k('sdn2',V,speed,one,v('ax'))
    integrals=[k('ekmg',v('radius'),v('pi'),factor,k('ekle',v('pi'),v(A)),v(E),v(S)) for factor,A,E,S in [(one,'amplitude','energy','volume'),(D,'newamplitude','newenergy','newvolume')]]
    text+=define('ekpm',TOTAL,both(k('ekn7',*args(SETTING)),*integrals,positive(v('energy'))))
    text+=define('ekpn',TOTAL,k('ekpl',*args(DISPLAY)))
    for name,which in [('ekpo','energy'),('ekpp','newenergy')]:
        fixed,variables=name_variables(which);text+=define(name,NAME,quantified('g',variables,k('ekpm',*[fixed.get(n,v(n)) for n,t in TOTAL])))
    p=v('point');author=k('rd');scope=k('eistk');node=k('eist2');display=k('eist3');special=k('eist4');specialdisplay=k('eist5')
    text+=content('ekpq',both(*(k('eislo',k(sign),'r[p '+rule+']',k('eirf'),p) for sign,rule in [('eist6','ekpo'),('eist7','ekpp')])))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL];setting=[FIXED.get(n,v(n)) for n,t in SETTING]
    amp=[op('u',op('e','n p a b','n p a b')) if n=='magneticside' else FIXED.get(n,v(n)) for n,t in AMPLITUDE]
    premise=both(k('ekmj',*actual),k('ekoz',*setting),k('ekij',*amp))
    text+=content('ekpr',quantified('f',VARIABLES,op('y',k('ekpm',*actual),premise)))
    text+=content('ekps',quantified('f',VARIABLES,op('y',k('ekpm',*actual),k('ekpn',*actual))))
    text+=define('ekpt',TOTAL,both(k('ekpm',*args(TOTAL)),k('sca',v('angle'),zero)))
    text+=define('ekpu',PRINTED[:2],k('sky',mul(k('bf',one,ratio),k('sjd',k('bd',one,ratio)))),R)
    text+=define('ekpv',TOTAL,both(k('s45',V,speed),positive(v('energy')),nonnegative(v('newenergy')),k('sca',quotient,k('ekpu',V,speed))))
    for name,target in [('ekpw','ekpn'),('ekpx','ekpv')]:text+=content(name,quantified('f',VARIABLES,op('y',k('ekpt',*actual),k(target,*actual))))
    text+=content('ekpy',both('t[k ekpq[]][v point]',k('zc',node,author,quote('ekpr'),quote('ekps'),scope,p),k('uh',node,author,quote('ekps'),scope,p),k('eisox',display,quote('ekps'),p),k('uf',author,node,display,p),k('ue',node,display,p),k('eisra',node,author,k('eirf'),k('eistw'),quote('ekpe'),quote('ekpr'),scope,p),k('eissb',special,display,author,quote('ekpw'),quote('ekpx'),scope,p),k('eistb',quote('ekpx'),quote('ekpw'),scope,p),k('eisra',special,author,k('eirf'),display,quote('ekps'),quote('ekpw'),scope,p),k('uf',author,special,specialdisplay,p),k('eisox',specialdisplay,quote('ekpx'),p),k('ue',display,special,p),k('ue',special,specialdisplay,p)))
    text+='d ekpz[] f[j s[k ekpy[]]].\n'
    nodes=['eist2','eist3','eist4','eist5']
    text+=define('ekp2',[],both(k('eir3',node,author,k('eirf'),quote('ekpz'),k('ri')),k('ue',k('eistw'),node,k('ri')),op('u',op('e',k('eistw'),node)),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:]),op('u',op('e',k('eist6'),k('eist7')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekp2',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_enclosed_light_energy_names_general_and_zero_angle_ratios',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/light-volume-ratio-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for n,form in [('eist6','E'),('eist7','E′')]:ann['entries'].append(dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
