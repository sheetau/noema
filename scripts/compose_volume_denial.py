"""Keep the author's volume denial distinct from its physical truth."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_equal_volume_supposition import ROOT,read,TOTAL,VARIABLES,FIXED
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-equal-volume-supposition.noema';PARENT_BASIS='data/equal-volume-supposition-basis-v1.json'
FULL='examples/v014/einstein-volume-denial.noema';CORE='examples/v014/volume-denial-core.noema'
BASIS='data/volume-denial-basis-v1.json';ANNOTATIONS='data/volume-denial-identifiers-v1.json';INDEX=387
PRIMITIVES={'eisto':([], '固定原文einstein-1905:u0203[390,421)の第三文Dies ist jedoch nicht der Fall.の箇所。等体積の仮置きを受ける否定と対照の内容は別に合成する。')}
MEANINGS={
 'ekmz':'同じ70役割の実際の旧新体積volume/newvolumeが正で等しいというekl6。比較用hypovolumeとは区別し、比の条件文全体又は先行密度式を参照先に替えない。',
 'ekm2':'同じ実際の二体積についてekmzを否定する。適用する物理的設定と体積の正値は呼出し側のekmoで要求する。無効な体積から物理的な不等を認定しない。',
 'ekm3':'第二文と同じK・V・波範囲・部分zvaa・状況を固定し、残る65役割の全設定で、ekmoなら同じ実際の等体積ekmzを否定する。Dies ist jedoch nicht der Fallを、例外条件を付さない図式的な否定として帰属する明示的な強い読み。後続体積式の特殊方向では反例を持ち、その真理又は物理的証明を主張しない。',
 'ekm4':'同じ65役割と同じekmoの適用域について、実際の二体積が常に等しいという比較用の内容。第二文の等体積の仮置きekmsや、そこからの比の条件文ekmrと同一ではない。',
 'ekm5':'ekm4の全称的な等体積を外から否定する比較用の弱い内容。少なくとも一つ等体積でない設定があるという読みであり、全設定で不等とするekm3とは別。今回の著者の主張へ自動的に置き換えない。',
 'ekm6':'部分を引数とし、同じK・V・波範囲・状況の下でその部分に物理的な平均総量設定ekmoがあるという性質。仮の等体積と現実の体積の否定を対照する共通対象を指定し、対照の成否だけから物理設定の存在を認定しない。',
 'ekm7':'著者が第三文でekm3を述べ、第二文の等体積の仮置きekmsをeisraで受け直し、同じ部分の体積という観点ekm6で両内容をeisnpにより対照する。第二文の比の規則の否定、第一文の撤回、読者の心理又は引用した物理内容の実行は追加しない。',
 'ekna':'第三文の否定・後方参照・対照ekm7を述べるメッセージ。',
 'eknb':'同じ著者と論説へ第三文のメッセージを帰属し、第二文eistnに続く本文順序を保持する。',
}
LIMITS=[
 '原刊913頁と固定原文u0203[390,421)のDies ist jedoch nicht der Fall.を、前後の文脈と合わせて読む。本文26非空白文字、数式要素0。Diesは直前のwenn節の等体積を受け、第二文の条件付きエネルギー比全体を否定しない。',
 '主たる記述では、先行の図式的な議論を受けて、同じ適用域の各設定の実際の等体積を否定する強い読みを明示的に採る。原文が量化を明記しているとは主張しない。特定の未指定の一事例だけを指す読み、通常の場合だけを述べる読み、体積の一般的不変性を否定する弱い読みは区別される。',
 '強い読みは後続の体積式S′=S/[β(1−av/V)]から例外を持つ。V5,v3,n=(1/3,2/3,2/3)ではD=1である。速度零や振幅零だけの退化例ではなく、横波E=(-2,2,-1),H=(-2,-1,2),A=3でも、変換後A′=3となり等体積である。この反例を保存し、著者の提示を物理的な真理として認定しない。',
 '全設定で不等のekm3と、常に等しいわけではないekm5は別内容として構成する。検査を通すために前者を後者へ無言で弱めず、D≠1を前件へ追加して否定を同語反復にもしない。弱い読みを著者の別主張として追加しない。',
 '第二文の仮の比較体積と実際のnewvolumeを区別する。否定は実際の二体積にかかるため、仮置きそのものの不可能性や条件文の撤回とはしない。jedochは仮置きから実際の不等への対照として既存eisnpで示す。',
 'eisraの後方参照とeisnpの対照には具体的な先行構成ekmsと現在の否定ekm3を渡し、同じ部分をekm6へ結ぶ。どちらの言説関係も引用内容の真理を実行しない。新しい一般関係は追加せず、原始記号は原文箇所への参照一件だけとする。',
 '両系の物理的な領域・校正単位・振幅・平均密度・総量はekmoの同じ設定を引き継ぐ。位相平均と同時断面の積分、球による具体化の解釈上の制限は前版のまま保持する。',
 '有限診断は、量化と否定の順序・引数結合・引用・具体的な反例を確かめる。全実数域の物理理論、原文との同義性、強い読みが唯一の解釈であることを自動証明しない。u0203第四文以降の球面・無流出入・同じ光の集合・問いは未完。',
]
DIAGNOSTICS=['seaj','seal','sdq2','sdz2','sech','sedp']

def definitions():
    text='r eisto[] a.\n'
    text+=define('ekmz',TOTAL,k('ekl6',v('volume'),v('newvolume')))
    text+=define('ekm2',TOTAL,op('u',k('ekmz',*args(TOTAL))))
    actual=[FIXED.get(n,v(n)) for n,t in TOTAL]
    for name,result in [('ekm3','ekm2'),('ekm4','ekmz')]:
        text+=content(name,quantified('f',VARIABLES,op('y',k('ekmo',*actual),k(result,*actual))))
    text+=content('ekm5',op('u',evaluate('ekm4')))
    dimension=[v('portion') if n=='portion' else FIXED.get(n,v(n)) for n,t in TOTAL]
    text+='d ekm6[portion a] e[b point['+quantified('g',VARIABLES,k('ekmo',*dimension))+']].\n'
    node=k('eisto');prior=k('eistn');author=k('rd');scope=k('eistk');p=v('point')
    text+=content('ekm7',both(k('uh',node,author,quote('ekm3'),scope,p),k('eisra',node,author,k('eirf'),prior,quote('ekms'),quote('ekm3'),scope,p),k('eisnp',node,author,prior,quote('ekms'),node,quote('ekm3'),'r[p ekm6]',p)))
    text+='d ekna[] f[j s[k ekm7[]]].\n'
    text+=define('eknb',[],both(k('eir3',node,author,k('eirf'),quote('ekna'),k('ri')),k('ue',prior,node,k('ri')),op('u',op('e',prior,node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eknb',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='volume_denial_attribution_with_explicit_scope_and_counterexample',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS)+DIAGNOSTICS,statement_indices=[INDEX]).document
    ann=json.loads(read('data/equal-volume-supposition-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
