"""Connect the leading pressure approximation with empirical and theoretical agreement."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,F,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_mirror_energy_principle import TOTAL,VARIABLES,FIXED

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-mirror-energy-principle.noema';PARENT_BASIS='data/mirror-energy-principle-basis-v1.json'
FULL='examples/v014/einstein-pressure-leading-approximation.noema';CORE='examples/v014/pressure-leading-approximation-core.noema'
BASIS='data/pressure-leading-approximation-basis-v1.json';ANNOTATIONS='data/pressure-leading-approximation-identifiers-v1.json';INDICES=[404,405]
LEADING=[(n,R) for n in ('pi','amplitude','anglecos')]
FAMILY=[(n,R) for n in ('pi','amplitude','light','anglecos')]
PRIMITIVES={
 'eisvc':([('source','a'),('claim','i[e]'),('scope','a'),('context','d')], '同じscopeで比較するsourceの量的な内容が、同じ閉じたclaimとして対応付けられる。sourceは経験から認められた量的な規則のまとまり又は理論であり、そこで比較される対象・量・適用条件・単位・近似次数をclaimのまま保つ。経験の場合は経験から得られた規則の内容を指し、個々の生の測定値が全て厳密に同一という意味ではない。理論の場合はその比較範囲で与える予測の内容であり、理論全体がclaimだけからなるとも、同じ方法で導出されるとも要求しない。この内容対応自体はclaimの物理的真理や実証完了を含意せず、近似を無制限の等式へ変えない。異なる出所に同じclaimを渡すことによる一致、出所の種類・選択範囲・複数性は合成側で構成する。'),
 'eisvd':([('theory','a'),('document','a'),('scope','a'),('context','d')], '同じdocumentとscopeの論述で比較対象として取り上げられる理論theoryの全範囲。理論は関連する現象の量・適用条件・法則を体系的に与える説明であり、単なる数表・観測記録とは区別する。現在の著者の理論以外であること、複数性、指定内容との一致は別に要求する。世界中の全理論又は後世の理論を指す範囲ではなく、結果の一致するものだけを後から選んだ範囲でもない。原文が固有名を与えないとき、特定の理論名や厳密な件数を補わない。'),
 'eisve':([], 'u0224でErfahrungとして指す、この光圧の比較に関係する経験から認められた規則のまとまり。光の作用で物体に力が生じるという経験的な内容の出所であり、原文にない実験名、装置、日時、数値表は補わない。比較される量的内容と近似範囲はeisvcへ別に渡す。'),
 'eisvf':([], '同じKの圧力法則で、pi・入射振幅・Kの旧角・正の光速を固定し、鏡の速度比v/Vを零へ近づける展開変数への参照。係数族の実体はekux、領域はekuy、零での先頭項と極限はekuzへ別に構成する。全ての鏡の内部状態や全波形を固定したまま実験的に加減速するという主張ではない。'),
 'eisvg':([], 'u0224の第一近似として経験及び他理論と一致する結果を得るという導入箇所。'),
 'eisvh':([], 'u0225=M0382の同じPについての近似表示箇所。'),
}
MEANINGS={
 'ekuw':'M0382の右辺2*A²/(8*pi)*cos²φという先頭値を構成する。同じ入射振幅とKの旧角を使い、非零速度での厳密圧力へ直ちに等置しない。',
 'ekux':'同じpi,A,V,cosφを固定し、ratioを受け取って先行の圧力右辺ekt3をspeed=ratio*Vで評価する実数関数。入力は無次元の速度比で、速度そのものや角を展開変数へ取り違えない。',
 'ekuy':'有効な速度比ratioでratio²<1という零の両側の局所定義域。零を含め、分母が零となる両端を除く。実際の全物理設定をこの数学的な両側族に沿って実現できるとは主張しない。',
 'ekuz':'有効な正のpi,V、非負Aと絶対値1以下のcosφについて、ekuxの零での値がekuwであり、全実数のsjrの意味で同じ零への極限がekuwとなる。単一点の代入や有限の小速度例を極限の代用にしない。',
 'eku2':'同じ102設定のPをM0382の先頭値ekuwへ等置する数的な式。後続で次数制限して引用する内容であり、この定義だけで非零速度の厳密一致を断言しない。',
 'eku3':'同じ98可変役割の全割当でekt6ならeku2という、先頭表示の次数制限前の内容。外側の本文でそのまま実行せずeku5の引用対象とする。',
 'eku4':'同じ設定のpi,A,V,cosφについてekuzの実数極限を要求する内容。同じ物理量の圧力右辺へ接続した数学的な近似の規約であり、経験からの証明ではない。',
 'eku5':'eku3の同じ圧力等式を、eisvfの速度比による展開の零次までの内容としてeisbnで読む。原文のerste Annäherungを最初の先頭近似とする明示的な読みであり、一次まで保持するという意味へ変えない。',
 'eku6':'先行の同じ厳密圧力表示ekufと、同じ右辺の先頭値・極限eku4を合わせた近似への導出根拠。近似等式の無制限な成立eku3を根拠へ先取りしない。',
 'eku7':'同じ近似結果eku5を、経験的な規則の出所eisveと、文脈で指定した複数の他理論の全てへ同じeisvcで結ぶ。各理論は著者の同じ理論eisqwと異なる。厳密式や全理論体系の一致へ範囲を広げない。',
 'ekva':'同じ原理と光圧表示の続きで、eku6から近似eku5を得るという著者の帰結提示と、その結果が経験・他理論と一致するeku7の提示を結ぶ。先行式への照応と後続表示への順序を保持し、原文にないコロンを追加しない。',
 'ekvb':'同じPの命名規則ekuhを維持し、u0225の表示を次数制限したeku5へ結ぶ。印刷の等号を無制限の厳密等式として再解釈しない。',
 'ekvc':'u0224の近似・一致・帰結提示ekvaを述べるメッセージ。',
 'ekvd':'同じ導入を著者と論説へ帰属し、先行の光圧表示u0223からの順序を保持する。',
 'ekve':'u0225の同じ近似表示ekvbを述べるメッセージ。',
 'ekvf':'同じ近似表示を著者と論説へ帰属し、u0224の導入からの順序を保持する。',
}
LIMITS=[
 '原刊915頁u0224–u0225の一続きの文、80非空白本文文字とM0382を対象とする。導入末にコロンはなく、後続の表示末に句点がある。P、2、A²、8*pi、cos²φを保持する。',
 'erste Annäherungは同じ速度比v/Vに関する零次の先頭近似と読む。先行の別箇所で用いた定数項と一次項の一致の規約を変更しない。実際の式は一般には速度比の線形項を含まないため、この箇所へ一次Taylor近似を代用しない。',
 '固定するのはpi・同じ入射振幅・Kの旧角・Vと量の単位である。数学的な圧力係数族を全実数の極限で指定し、実際の鏡の全状態を同じまま連続加減速する存在主張は追加しない。全物理設定に同一の誤差幅や適用速度の数値を指定したとはしない。',
 'Pは先行と同じ物質的面部分・力・区間・面積の平均光圧である。近似式の次数を限定し、非零速度のPを先頭値へ厳密に等置しない。先行の零速度での仕事による圧力未決定性を、数学的な右辺の極限だけで物理的に解消したとはしない。',
 '経験との一致は、経験から認められた量的規則がこの同じ先頭近似の結果を与えるという読みである。生の全測定値が厳密に等しいという読みではない。実験名・データ・誤差率を原文へ補わず、同じ限定した内容への対応を記述する。',
 '他理論との一致は、文脈で対象とされた少なくとも二つの理論が同じ近似結果を与えることと読む。著者の展開した理論eisqwと区別し、全ての他理論や後世の理論の一致、同じ導出方法、理論全体の同値を要求しない。範囲を結果に合わせて選び直さない。',
 '一般関係eisvcは出所と量的内容の対応、eisvdは文脈の理論範囲だけを担う。式・圧力・近似・一致・複数性・著者帰属を一つの原始関係へ隠さず、同じ閉じた近似内容の共有と全称条件で構成する。',
 '実数極限・出所の内容対応・著者の導出提示を区別する。有限対照と代数的な誤差説明は接続と読みの証拠であり、全実数の自動証明、経験データの実証又は意味同義性の自動証明ではない。次の光学問題の一般的方法を述べる三文、第八節見出し及び二作品全体は未完。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');two=k('bb','n p c b');mul=lambda a,b:k('shv',a,b)
    text+=define('ekuw',LEADING,mul(mul(two,k('ekle',v('pi'),v('amplitude'))),mul(v('anglecos'),v('anglecos'))),R)
    text+=define('ekux',FAMILY,'i[ratio '+R+']['+k('ekt3',v('pi'),v('amplitude'),v('light'),mul(v('ratio'),v('light')),v('anglecos'))+']',F)
    text+=define('ekuy',[('ratio',R)],both(k('ba',v('ratio')),k('bg',mul(v('ratio'),v('ratio')),one)))
    leading=k('ekuw',*args(LEADING));family=k('ekux',*args(FAMILY))
    text+=define('ekuz',FAMILY,both(*(k('ba',v(n)) for n,t in FAMILY),k('bg',zero,v('pi')),k('bg',zero,v('light')),k('bc',zero,v('amplitude')),k('bc',mul(v('anglecos'),v('anglecos')),one),k('sca',app(family,zero),leading),k('sjr','p ekuy',family,zero,leading)))
    text+=define('eku2',TOTAL,k('sca',v('pressure'),leading))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL]
    text+=content('eku3',quantified('f',VARIABLES,op('y',k('ekt6',*actual),k('eku2',*actual))))
    text+=content('eku4',quantified('f',VARIABLES,op('y',k('ekt6',*actual),k('ekuz',*[FIXED.get(n,v(n)) for n,t in FAMILY]))))
    text+=content('eku5',k('eisbn',quote('eku3'),k('eisvf'),'n p a b',v('point')))
    text+=content('eku6',both(evaluate('ekuf'),evaluate('eku4')))
    p=v('point');scope=k('eistk');paper=k('eirf');a=k('rd');node=k('eisvg');display=k('eisvh');theory=v('theory')
    selected=k('eisvd',theory,paper,scope,p)
    text+=content('eku7',both(k('eisvc',k('eisve'),quote('eku5'),scope,p),k('eifk','i[theory a]['+selected+']'),q('f','theory','a',op('y',selected,both(op('u',op('e',theory,k('eisqw'))),k('eisvc',theory,quote('eku5'),scope,p))))))
    text+=content('ekva',both(k('zc',node,a,quote('eku6'),quote('eku5'),scope,p),k('uh',node,a,quote('eku7'),scope,p),k('eisra',node,a,paper,k('eisu7'),quote('ekuf'),quote('eku5'),scope,p),k('ue',node,display,p)))
    text+=content('ekvb',both(k('eislo',k('eisvb'),'r[p ekuh]',paper,p),k('eisox',display,quote('eku5'),p)))
    for shown,msg,stmt,item,previous in [('ekva','ekvc','ekvd',node,k('eisu7')),('ekvb','ekve','ekvf',display,node)]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',item,a,paper,quote(msg),k('ri')),k('ue',previous,item,k('ri')),op('u',op('e',previous,item))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==404
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekvd','ekvf')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_pressure_leading_limit_and_empirical_theory_agreement_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/mirror-energy-principle-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
