"""Connect pointwise possible light trials to the all-space differential claim."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_translated_light_trial import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-translated-light-trial.noema';PARENT_BASIS='data/translated-light-trial-basis-v1.json'
FULL='examples/v014/einstein-arbitrary-start-claim.noema';CORE='examples/v014/arbitrary-start-claim-core.noema'
BASIS='data/arbitrary-start-claim-basis-v1.json';ANNOTATIONS='data/arbitrary-start-claim-identifiers-v1.json';INDEX=282
MEANINGS={
 'ei3m':'指定試行を選んだ可能設定で、元設定と同じ地点・補助座標x′,y,z・出発K時刻をei3lへ結び、その試行の現在の全時計・座標・全光路ei3kと、同じτ候補の平行移動した近傍条件・局所全微分可能性・同じ点の二偏微分sklを要求する。元と候補を実際に同一の状況とはしない。',
 'ei3n':'指定した空間座標と時刻を表す同じ元設定の地点があり、議論主体zeeがその設定で選べる試行の可能な結果の一つで、その同じ地点のei3mが成立する。地点ごとに異なる試行を許し、実際の全試行や全結果の保証を含意しない。',
 'ei3o':'同じ元設定・候補τ・出発時刻について、現在の全指示条件ei3cを保持し、全有効実数値x′,y,zでei3nの選択可能性を要求する。原点の既存例と任意の他の点を合わせた全空間の範囲であり、記録済み地点だけへ限定しない。',
 'ei3p':'先行する同じ正側極限の前提ei2wと、その同じ出発時刻・状況について任意の出発点を選べるei3oを合わせた内容。局所正則性を明示する既出の読みを引き継ぎ、別のτ解を地点ごとに選び直さない。',
 'ei3q':'著者が任意の出発点を選べたというei3pを述べ、同じ第三節で注意すべき点として提示する内容。Es ist zu bemerkenを明白さや証明済みの宣言へ変えない。',
 'ei3r':'任意の出発点の選択可能性と注意喚起ei3qを述べるメッセージ。',
 'ei3s':'u0058前半の注意喚起と可能選択を同じ著者・論説へ帰属し、直前の偏微分式の整理からの本文順序を保持する。',
 'ei3t':'同じ任意の出発点の選択可能性ei3pを理由に、直前の整理後の式が同じ候補τ・速度・時刻について全空間座標値で成立するskvが従うという著者の提示。deshalbの理由と帰結、eben erhalteneの同じ式への参照を保持する。',
 'ei3u':'任意の出発点から全空間の微分条件への帰結ei3tを述べるメッセージ。',
 'ei3v':'u0058後半の全空間への帰結を同じ著者・論説へ帰属し、同じ文前半の注意喚起と選択可能性に続ける。',
}
LIMITS=[
 'u0058全213文字・175本文文字とM0105 x′,y,zを対象とする。注意喚起、議論主体wir、原点の代わりの任意の他の点、光の出発点として選べた可能性、deshalbの帰結、同じ整理後の式、全空間値を保持する。',
 'hätten wählen könnenは同じ思考設定で選べた試行と、その可能な結果の存在として読む。元と候補の同じ地点・補助座標・K出発時刻を結び、実際に全地点で光を発したことや全結果での成功とはしない。地点ごとに試行や可能設定を選べる。wirは議論を行う側として保持し、構成員を確定しない。',
 '先行する原点での試行を含め、全ての有効実数値のx′,y,zを量化する。原点以外だけを結論の範囲にせず、存在する有限の記録地点だけへ縮めない。全地点と候補試行の存在は著者が述べる内容であり、この通読判断が現実の存在を証明したとはしない。',
 '同じ候補τ、V、v、二基準系と単位を保つ。任意の候補設定で現在の全座標対応と全時計指示、完全な光往復、両K光区間の原理と局所表示をei3kへ結ぶ。時刻は前段と同じパラメータであり、ここで全時刻の量化やt=τを新たに補わない。',
 'skiは空間三引数の原点だけを移し、時刻引数・τ値・尺度を変更しない。sklは移した近傍全体の式と元の同じ関数の指定点での全微分可能性・二偏微分を結ぶ。十分な局所正則性を明示した既出の読みを引き継ぎ、原文がε–δ条件を逐語的に述べたとはしない。',
 '結論skv/skn/skmは全空間点ごとに同じτの二偏微分値を存在量化し、その値で既存sjyのτx′+v/(V²-v²)*τt=0を要求する。原点の候補値zd6/zd7を全空間で同じ定数とせず、具体的τの関数形やy,z方向の条件を先取りしない。',
 'Es ist zu bemerkenは選択可能性への注意喚起、deshalbはその内容から同じ微分式の全空間範囲への帰結の提示と読む。著者・論説・第三節と直前の式からの本文順序を保持し、提示の帰属と処理系による物理的含意の証明を区別する。',
 '旧空間平行移動・可能選択・局所微分・全空間量化とその証拠を再利用し、新規原始語は追加しない。有限の例は作用範囲と引数を調べるものであり、全実数・全地点の一般物理定理を代用しない。',
]

def definitions():
    spatial=[(n,R) for n in ('x','y','z','time')];xs=[v(n) for n,_ in spatial]
    trial=v('trial');point=v('point');base=v('baseline');alt=v('alternative');ctx=v('context')
    text=define('ei3m',[('trial','a'),('point','a')]+spatial+[('baseline','d'),('alternative','d')],both(k('ei3l',point,*xs,base),k('ei3l',point,*xs,alt),k('ei3k',trial,point,*xs,alt),k('skl',k('zd4'),*xs[:3],k('tc'),k('zb7'),xs[3])))
    succeeds='i[trial a point a alternative d]['+k('ei3m',trial,point,*xs,ctx,alt)+']'
    text+=define('ei3n',spatial+[('context','d')],q('g','point','a',both(k('ei3l',point,*xs,ctx),k('skj',point,k('zee'),ctx,'p zec','p zed',succeeds))))
    allpoints=op('y',both(*(k('ba',v(n)) for n in ('x','y','z'))),k('ei3n',*xs,ctx))
    for n in reversed(('x','y','z')):allpoints=q('f',n,R,allpoints)
    text+=define('ei3o',[('time',R),('context','d')],both(k('ba',v('time')),k('ba',k('tc')),k('sbg',k('zb7')),k('bg',k('zb7'),k('tc')),k('ei3c',k('zd4'),ctx),allpoints))
    time=k('sjh',k('qe',k('zdq')),k('zb6'))
    text+=content('ei3p',both(k('ei2w'),k('ei3o',time,k('zb6'))))
    text+=content('ei3q',both(k('uh',k('zeg'),k('rd'),quote('ei3p'),k('eisms'),v('point')),k('zei',k('zeg'),k('rd'),k('eisms'),v('point'))))
    text+='d ei3r[] f[j s[k ei3q[]]].\n'
    def author(name,node,message,prior):return define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    text+=author('ei3s','zeg','ei3r','zeb')
    text+=content('ei3t',k('zc',k('zeh'),k('rd'),quote('ei3p'),quote('skv'),k('eisms'),v('point')))
    text+='d ei3u[] f[j s[k ei3t[]]].\n';text+=author('ei3v','zeh','ei3u','zeg')
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ei3s','ei3v')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='pointwise_possible_starts_and_all_space_differential_claim',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/translated-light-trial-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
