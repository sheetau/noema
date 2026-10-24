"""Attribute a nonvacuous equal-volume comparison of the same light portion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_mean_light_energy import ROOT,read,TOTAL,ARITHMETIC
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-mean-light-energy.noema';PARENT_BASIS='data/mean-light-energy-basis-v1.json'
FULL='examples/v014/einstein-equal-volume-supposition.noema';CORE='examples/v014/equal-volume-supposition-core.noema'
BASIS='data/equal-volume-supposition-basis-v1.json';ANNOTATIONS='data/equal-volume-supposition-identifiers-v1.json';INDEX=386
COMPARISON=TOTAL+[('hypovolume',R)]
FIXED={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point'),'portion':k('zvaa')}
VARIABLES=[(n,t) for n,t in TOTAL if n not in FIXED]
COMPARISON_VARIABLES=VARIABLES+[('hypovolume',R)]
PRIMITIVES={'eistn':([], '固定原文einstein-1905:u0203[164,389)の第二文。特定の同じ光の集合について、旧新で同じ体積だと仮定すれば、二乗振幅比が新旧エネルギー比になるという、先行密度説明からの仮の帰結を述べる箇所。後続の体積不一致の文とは区別する。')}
MEANINGS={
 'ekmn':'同じpi・新系振幅を保持し、比較のために仮置きしたhypovolumeへ新系の平均密度ekleを掛けた総量候補。実際の新系体積newvolumeと実際の総量newenergyをこの値へ上書きしない。',
 'ekmo':'同じ70役割の物理的な平均総量設定ekmi、その同じ積分からのE=ρSの関係ekmj、比を定めるための旧振幅と旧総量の正値を保持する。新系の実際の体積・総量が旧系と等しいとは要求しない。',
 'ekmp':'ekmoの同じ物理的な対象・波・二系・単位・振幅を固定して、正の比較体積hypovolumeを旧系の体積と等しく置く。仮に等しいとする値と実際の新系体積は別の引数であり、実際のLorentz体積比に反するという理由でこの仮の計算を空にしない。',
 'ekmq':'同じ旧振幅・新振幅・旧総量と、ekmnで計算した同じ比較総量をekmlへ結び、その比が新旧の二乗振幅比に等しいという帰結。新旧の分子分母を逆にしない。',
 'ekmt':'ekmpの等体積の仮置きへ、同じpi・両振幅・旧体積・比較体積・旧総量・比較総量によるekmkの平均密度と総量の関係を結ぶ。仮の新総量の役割を数値だけの独立変数へ放置しない。比の帰結ekmqを前提に含めない。',
 'ekmv':'同じK・V・先行波の範囲・光の部分zvaa・状況を固定し、残る65役割で、平均総量の積分設定ekmiなら同じ二つのE=ρSの関係ekmjとなるという説明内容。空間積分と一様密度の関係を、第二文が引き継ぐ密度の根拠へ接続する。',
 'ekms':'同じ65役割でekmoが成り立つ場合、旧体積volumeそのものを比較体積に使ったekmtを構成する。正の旧体積があるので具体的な比較値を持ち、実際の新旧体積が異なる場合も仮の計算ができる。実際の新系体積が旧体積であるという内容ではない。',
 'ekmr':'同じ65役割と独立な比較体積の全66役割について、等体積の仮の比較ekmtなら、その同じ値の帰結ekmqとなるという条件内容。実際の測定済みや現実の等体積を主張せず、全ての物理的可能世界での変化を量化する読みへ替えない。',
 'ekmu':'同じ旧系密度eklq、新系密度eklr、一様平均密度から総量へのekmvを同じ状況で結ぶ、daherによる仮の帰結提示の根拠内容。',
 'ekmw':'同じ著者が第二文で等体積の比較ekmsを思考上の構成として取り上げ、先行密度の根拠ekmuから条件内容ekmrが従うと提示し、その条件内容を述べる。eislz・zc・uhを分け、仮の計算と実際の新系の値を混同しない。',
 'ekmx':'第二文の同体積の仮の構成と帰結提示ekmwを述べるメッセージ。',
 'ekmy':'第二文のメッセージを同じ著者・論説へ帰属し、特定の光の部分zvaaを同じ考察の指示対象へ結び、第一文eistlからの本文順序を保持する。',
}
LIMITS=[
 'u0203第二文[164,389)全体、本文174非空白文字とM0351–M0353を原刊913頁へ照合する。M0351はA′²/A²、M0352はK、M0353はk。新系で測るエネルギーが分子、旧系で測るエネルギーが分母である。',
 'eines bestimmten Lichtkomplexesは、直後に移動球面で具体化して追跡する同じ特定の光の部分zvaaを指すという、前後の文脈を共有する読みを採る。ここで光子の集合を導入せず、部分の物理的な意味はeistm、単位と密度はeiste/eistj、総量はekmiの平均と空間積分に接続する。一般の形状での一様密度の代数規則ekmmは既に独立に保持し、球でのみ成立する比の法則とは読まない。',
 'Es wäre ... wenn ... das gleiche wäreを、密度とその物理的な対象を保って、体積については等しいと仮置きして総量比を計算する、思考上の条件付き比較として読む。実際の新系体積を同じ値へ書き換えず、比較用の値hypovolumeを別に持つ。全Lorentz幾何を保った物理的可能世界で実現できるという主張、又は実際の等体積の主張ではない。',
 '比較の設定をeislzへ、daherの密度からの帰結提示をzcへ、条件文の主張をuhへ接続する。密度から総量への一様平均の積分の説明は引き継ぐ。等体積の仮定と現実の体積変換式を同じ値に課して、偽の前件から空虚に比を得たことにはしない。',
 'A及びA′は同じ校正された両系の振幅であり、原文のbewegt gemessen/ruhend gemessenは、その系で量を評価する役割として読む。実際に計測器を用いた二つの実験を追加しない。K・kの二体積と二エネルギーは同じ光の部分に属する。',
 '先行版と同じ平均モデルを継承する。領域を固定した位相平均により得る平均総エネルギーであり、有限球の瞬間総量や境界を追跡する時間平均へ置き換えない。比を述べる旧振幅・旧総量は正に限定し、0/0を認定しない。',
 '後続Dies ist jedoch nicht der Fallと球面を挟む無流出入・同じ集合・問いは今回の第二文へ先取りしない。非零速度でも等体積となる方向があるという前版の対照を保持し、第三文の一般性の読みは次に扱う。',
 '第一文の127本文文字と今回174文字を合わせてもu0203全体の判断にはしない。有限検査は束縛・数式・提示関係の診断であり、全実数域・物理理論・原文の意味同義性の自動証明ではない。',
]

def definitions():
    text='r eistn[] a.\n';z=k('bb','n p a b');positive=lambda x:both(k('ba',x),k('bg',z,x))
    text+=define('ekmn',[(n,R) for n in ('pi','newamplitude','hypovolume')],k('shv',k('ekle',v('pi'),v('newamplitude')),v('hypovolume')),R)
    text+=define('ekmo',TOTAL,both(k('ekmi',*args(TOTAL)),k('ekmj',*args(TOTAL)),positive(v('amplitude')),positive(v('energy'))))
    text+=define('ekmp',COMPARISON,both(k('ekmo',*args(TOTAL)),k('ekl6',v('volume'),v('hypovolume'))))
    hypo=k('ekmn',v('pi'),v('newamplitude'),v('hypovolume'))
    text+=define('ekmq',COMPARISON,k('ekml',v('amplitude'),v('newamplitude'),v('energy'),hypo))
    arithmetic=[v('pi'),v('amplitude'),v('newamplitude'),v('volume'),v('hypovolume'),v('energy'),hypo]
    text+=define('ekmt',COMPARISON,both(k('ekmp',*args(COMPARISON)),k('ekmk',*arithmetic)))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL];comparison=actual+[v('hypovolume')]
    text+=content('ekmv',quantified('f',VARIABLES,op('y',k('ekmi',*actual),k('ekmj',*actual))))
    text+=content('ekms',quantified('f',VARIABLES,op('y',k('ekmo',*actual),k('ekmt',*actual,v('volume')))))
    text+=content('ekmr',quantified('f',COMPARISON_VARIABLES,op('y',k('ekmt',*comparison),k('ekmq',*comparison))))
    text+=content('ekmu',both(evaluate('eklq'),evaluate('eklr'),evaluate('ekmv')))
    node=k('eistn');author=k('rd');scope=k('eistk');p=v('point')
    text+=content('ekmw',both(k('eislz',node,author,quote('ekms'),scope,p),k('zc',node,author,quote('ekmu'),quote('ekmr'),scope,p),k('uh',node,author,quote('ekmr'),scope,p)))
    text+='d ekmx[] f[j s[k ekmw[]]].\n'
    text+=define('ekmy',[],both(k('eir3',node,author,k('eirf'),quote('ekmx'),k('ri')),k('eisd3',node,k('zvaa'),k('eirf'),k('ri')),k('ue',k('eistl'),node,k('ri')),op('u',op('e',k('eistl'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekmy',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='equal_volume_hypothetical_energy_ratio_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/mean-light-energy-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
