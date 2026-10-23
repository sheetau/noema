"""Connect the unfixed normalized function and four common origin constants."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_four_coordinate_claim import ROOT,read
from scripts.compose_affine_time_form import CUT
from scripts.compose_origin_constants import OFFSETS
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-four-coordinate-claim.noema';PARENT_BASIS='data/four-coordinate-claim-basis-v1.json'
FULL='examples/v014/einstein-origin-constants-claim.noema';CORE='examples/v014/origin-constants-claim-core.noema'
BASIS='data/origin-constants-claim-basis-v1.json';ANNOTATIONS='data/origin-constants-claim-identifiers-v1.json';INDEX=302
MEANINGS={
 'ei7m':'指定設定の現在の全出来事対応ei3aを保ち、その全K/k記録対で四加法定数を含むspuの四式がei26の対応と過不足なく一致する。一組の定数を全記録対で共有する。',
 'ei7n':'指定設定について、ei7mを満たす時間・縦・横二成分の四実数定数が存在する。存在量化は全記録対の量化の外に置き、定数は独立で零も許す。',
 'ei7o':'その設定の全現在対応を四加法定数付きの式で表すという内容。評価状況をそのままei7nへ渡し、元の零原点状況zb6へ戻さない。',
 'ei7p':'四式で使う正規化後のφがこの段階では未決定であるというsqdを、直前のβの補足に続く著者の説明として提示する。',
 'ei7q':'正規化後のφの暫定的未決定性ei7pを断定の伝達形式にする。',
 'ei7r':'φの未決定性を同じ著者・論説へ帰属し、βの定義zfkからの順序を保持する。',
 'ei7s':'同じ条件を保ちながら初期空間原点とτ零点の仮定を採らないsqaなら、各式に共通の一組の加法定数を加えたei7oが必要になるという著者の条件付き提示。',
 'ei7t':'四加法定数についての条件付き提示ei7sを断定の伝達形式にする。前件の現実の成立や加算行為の実行は主張しない。',
 'ei7u':'四加法定数の条件付き提示を同じ著者・論説へ帰属し、φの未決定性zfpに続ける。',
}
LIMITS=[
 'u0085の全二文とM0137–M0139を原刊900頁へ照合する。冒頭undは直前のβに続けて四式のφを説明する接続として読む。先行aと現在のφ=spcを区別する。',
 'vorläufig unbekannteは、導出段階zfmで現在のφを含む有効な関数候補が残り、ある許容速度で異なる値を持つ候補も残るという既存sqdの読みを採る。後続のφ=1を先取りせず、主体の全知識についての否定や史実上の心理状態の復元とはしない。',
 'φは同じvの関数である。候補族sqcは先行aの族zerを同じβで正規化し、現在の候補と現在のspcを全許容速度で結ぶ。一速度で一致する候補も許し、異なる候補名だけを未決定性の証拠にしない。',
 'Macht man ... keinerlei Voraussetzungは、同じ物理条件・系・単位・V,v,φを保つ設定で、運動系の初期空間原点とτの零点についての仮定を採らないという条件。既存zfn/zfoの外部意味規約を維持し、零点の物理的不一致や全前提の廃棄に置き換えない。',
 '各右辺へ加える定数の順はτ,ξ,η,ζ。四定数は互いに独立で零も許すが、同じ設定の全記録対で同じ一組を使う。既存spuは同じV,v,φを使い、四出力の有効性と各加法を保持する。',
 '現在の測定eiyxを使う既存ei26/ei27/ei3aを再利用し、指定設定の同じ出来事・全座標範囲・値としての一意性を保つ。原点仮定を外した設定へ固定zb6やei46の零点条件を再要求しない。未測定の全実数四組の実在は追加しない。',
 'zuzufügenは四式の一般形に必要な加法定数を述べる数学的帰結として読む。人への行為命令や実際の加算履歴にしない。定数の存在を引用内容から現実の成立へ移さない。',
 '原点のアフィン代数と候補の対照検査は補助証拠であり、一般実数体・物理的真理・意味同値の自動証明ではない。次の光速度の保存の証明課題は後続単位へ残す。',
]
GROUPS=(('ei7p','ei7q','ei7r','zfp','zfk'),('ei7s','ei7t','ei7u','zfq','zfp'))

def definitions():
    c=v('setting');first=v('first');second=v('second');offsets=[v(n) for n in OFFSETS]
    selected=both(k('ei27',first,k('ra'),c),k('ei27',second,k('zbm'),c))
    exact=q('f','first','a',q('f','second','a',op('y',selected,op('z',k('spu',first,second,*offsets),k('ei26',first,second,c)))))
    text=define('ei7m',[(n,CUT) for n in OFFSETS]+[('setting','d')],both(*(k('ba',n) for n in offsets),k('ei3a',c),exact))
    body=k('ei7m',*offsets,c)
    for n in reversed(OFFSETS):body=q('g',n,CUT,body)
    text+=define('ei7n',[('setting','d')],body)
    text+=content('ei7o',k('ei7n',v('point')))
    text+=content('ei7p',k('uh',k('zfp'),k('rd'),quote('sqd'),k('eisms'),v('point')))
    text+=content('ei7s',k('zc',k('zfq'),k('rd'),quote('sqa'),quote('ei7o'),k('eisms'),v('point')))
    for body,message,author,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(author,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_origin_constants_and_unfixed_normalized_function',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS)+['sqe','sqf'],statement_indices=list(range(INDEX,INDEX+2))).document
    ann=json.loads(read('data/four-coordinate-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
