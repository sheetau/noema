"""Restrict the same amplitude law to zero angle and compare its displayed forms."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_observed_amplitude import ROOT,read,SETTING,VARIABLES
from scripts.compose_aberration_presentation import allq
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-observed-amplitude.noema';PARENT_BASIS='data/observed-amplitude-basis-v1.json'
FULL='examples/v014/einstein-amplitude-specialization.noema';CORE='examples/v014/amplitude-specialization-core.noema'
BASIS='data/amplitude-specialization-basis-v1.json';ANNOTATIONS='data/amplitude-specialization-identifiers-v1.json';INDICES=[381,382]
PRIMITIVES={
 'eistb':([('form','i[e]'),('comparison','i[e]'),('scope','a'),('context','d')],'同じscopeの既出の記号・演算規約で二つの記述を読むとき、formがcomparisonより、式の構成と量の依存を少ない入れ子の追跡・補助量の再構成で見渡せる形として評価されるという厳密な比較。eisspの形式評価と同じ観点の比較であり、両方が簡明である場合にも成立し得るが、同程度又は逆方向の評価を含めない。文脈上の対象記述と比較相手を固定し、同値な別表記へ評価を自動移転しない。内容の真理や同値性、導出の容易さ、全読者の心理、計算時間、絶対的な最簡形は含意しない。'),
 'eistc':([], 'u0199の直前の二乗振幅の式がφ=0でより簡明な形に移ることと、コロンによる表示導入の箇所。'),
 'eistd':([], 'u0200=M0347のφ=0での二乗振幅比A′²=A²(1−v/V)/(1+v/V)の表示箇所。'),
}
MEANINGS={
 'ekiu':'同じ旧振幅Aの二乗に(1−v/V)/(1+v/V)を掛ける実数式。分子の差と分母の和を保持し、振幅の平方根比や逆数比へ替えない。',
 'ekiv':'同じ63役割の物理設定と選んだ側の旧新振幅ekibを保持し、同じ旧実数角angle=0を加えた場合。余弦だけを1へ替えたり、別の波・側・系の角を零にしたりしない。',
 'ekiw':'同じ設定の新振幅の二乗が、同じV・speed・旧振幅のekiuに等しいという特殊表示の帰結。前件へこの等式を加えない。',
 'ekix':'同じ59全称役割について、同じ零角条件ekivの下で原刊の一般二乗比ekijを述べる。特殊表示ekiyと適用域を一致させる。',
 'ekiy':'同じ59全称役割と零角条件ekivの下で、同じ選択側の振幅の特殊比ekiwを述べる。前後で値と対象を選び直さない。',
 'ekiz':'welche Gleichungを直前の表示eiss6とそのekikへ結び、同じ零角条件のekixからekiyへ移るという著者の提示と、後者が前者より簡明であるという厳密比較、コロンと同じ表示への説明・順序を保つ。',
 'ekja':'u0199の照応・零角条件・より簡明な形への提示ekizを述べるメッセージ。',
 'ekjb':'u0199全文を同じ著者・論説へ帰属し、直前の一般二乗振幅比の表示に続ける。',
 'ekjc':'u0200の表示箇所を同じ零角設定の二乗比ekiyへ結ぶ。振幅そのものの式や無条件の式にしない。',
 'ekjd':'u0200の表示対応ekjcを述べるメッセージ。',
 'ekje':'u0200の表示を同じ著者・論説へ帰属し、u0199のコロンに続ける。',
}
LIMITS=[
 'u0199–u0200を原刊912頁へ照合する。M0346はφ=0、M0347はA′²=A²(1−v/V)/(1+v/V)。直前M0345の電子在庫と原刊の相違は既存の別記録を継承し、M0347へ根号を補わない。',
 '同じ旧実数角angle=0と同じ63設定を保持する。先行の角の規約からcosφ=1となり、一般形の右辺A²(1−r)²/(1−r²)が許容域0<v<VでA²(1−r)/(1+r)へ整理できる。因子の約分を新しい物理的測定や仮定の追加にしない。',
 'welche Gleichungは直前の同じ表示に係る関係節として読む。φ=0の場合の同じ一般形と特殊形を比較し、別のドップラー式や光行差式を比較相手にしない。二つの表示の前件は同じ零角条件にそろえる。',
 'einfachereは先行形に対してより見通しのよい形という厳密な形式比較と読む。単に新しい形が簡明という絶対評価に縮めず、両方が簡明な場合も許す。内容の真理、同値性、導出の容易さ、最短の文字列、唯一の最簡形とは区別する。',
 '電気側又は磁気側の選択、旧新の非負の振幅、同じ波・源・過程・二系・単位・観測者、先行の局所近似と校正を継承する。厳密な実測記録や電気側と磁気側の振幅等値、横波条件を新たに追加しない。',
 '式の整理は数値的対照と既存の代数証拠で確認するが、全許容物理場の法則の証明や意味同義性の自動証明ではない。全59役割を有限標本へ縮めず、引用された内容の真理を著者帰属時に評価しない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');V=v('light');speed=v('speed');A=v('amplitude');newA=v('newamplitude');mul=lambda x,y:k('shv',x,y);ratio=mul(speed,k('sjd',V))
    text+=define('ekiu',[(n,R) for n in ('light','speed','amplitude')],mul(mul(A,A),mul(k('bf',one,ratio),k('sjd',k('bd',one,ratio)))),R)
    text+=define('ekiv',SETTING,both(k('ekib',*args(SETTING)),k('sca',v('angle'),zero)))
    text+=define('ekiw',SETTING,k('sca',mul(newA,newA),k('ekiu',V,speed,A)))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in SETTING]
    for name,conclusion in [('ekix','ekij'),('ekiy','ekiw')]:text+=content(name,allq(VARIABLES,op('y',k('ekiv',*actual),k(conclusion,*actual))))
    node=k('eistc');display=k('eistd');prior=k('eiss6');author=k('rd');scope=k('eisrx');p=v('point')
    text+=content('ekiz',both(k('eisox',prior,quote('ekik'),p),k('eissb',node,prior,author,quote('ekix'),quote('ekiy'),scope,p),k('eistb',quote('ekiy'),quote('ekix'),scope,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ekjc',k('eisox',display,quote('ekiy'),p))
    for shown,msg,stmt,item,previous in [('ekiz','ekja','ekjb','eistc','eiss6'),('ekjc','ekjd','ekje','eistd','eistc')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(item),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==381
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekjb','ekje')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_zero_angle_amplitudes_and_comparatively_simpler_form',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/observed-amplitude-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
