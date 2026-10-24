"""Present the printed velocity quotient and the same easy calculation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_velocity_angle_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,app,op,both,quant as q
from scripts.compose_calculation_discourse import STEP,STEPS

PARENT='examples/v014/einstein-velocity-angle-claim.noema';PARENT_BASIS='data/velocity-angle-claim-basis-v1.json'
FULL='examples/v014/einstein-velocity-composition-claim.noema';CORE='examples/v014/velocity-composition-claim-core.noema'
BASIS='data/velocity-composition-claim-basis-v1.json';ANNOTATIONS='data/velocity-composition-claim-identifiers-v1.json';INDICES=(133,134,135)
MEANINGS={
 'ejpa':'同じ現在状況における同じ点のKの非負速さejoiと値zkp、kの非負速さejojと値zkq、同じ系速度から点速度への角ejowと実数測度eiso4を合わせる。全現在履歴・同じ実座標微分・速度成分・尺度を共有する。合成式の正の分母や点の光速上限を前提へ追加しない。',
 'ejpb':'既出の同じ点の運動・Kの厳密成分と、三量の定義を現在の設定zb6に適用したejpaを、計算の出発内容として保持する。',
 'ejpc':'現在の同じU/w/αの取得と値ejpaを保ち、その同じ光速・系速度・単位円二成分を原刊の角度付き速度合成式s2tへ渡す。零も含む非負の平方根と符号付きの非零分母を保つ。負の分母で非負Uと合わなければ、この内容は偽になり得る。',
 'ejpd':'著者が同じ評価文脈で利用できる方法があり、その同じ非空有限手順列がejpbからejpcまで許容された変形でつながり、各手順の非負負担の合計が文脈上の低負担基準に入る。別方法の低負担、実行済み履歴、結果の真理で代用しない。',
 'ejpe':'著者が同じ第五節の計算箇所zkxで、前提ejpbから原刊の式を含むejpcが得られると述べる帰結提示。式の成立や全適用域での導出の検証とは区別する。',
 'ejpf':'同じ著者・箇所・第五節で、同じ出発内容から同じ結果へ至る計算ejpdが文脈上低負担であると述べる評価。簡単な計算という修飾を省略しない。',
 'ejpg':'同じ計算の帰結提示ejpeを述べるメッセージ。',
 'ejph':'同じ計算への低負担評価ejpfを述べるメッセージ。',
 'ejpi':'計算からの帰結提示を同じ著者・論説へ帰属し、直前のαの意味説明zkvから計算導入zkxへの本文順序を保持する。',
 'ejpj':'同じ計算導入zkxでの容易さの評価を同じ著者・論説へ帰属する。引用された手順の存在や許容性をその場で実行しない。',
 'ejpk':'計算導入のコロンに続く原刊の表示式ejpcを、同じ著者・第五節の主張として式箇所zkwへ帰属する。計算箇所と表示式箇所の順序・区別を保持する。',
}
LIMITS=[
 'u0139全体とu0140を対象とする。前半のαを二速度間の角と見る説明ejo7は保持し、後半のNach einfacher Rechnung ergibt sich:と次の表示式を同じ計算へ接続する。',
 '固定電子転記M0257の分母sinは原刊906頁のcosと異なる。data/written-math-corrections-v1.jsonの既存訂正を明示して原刊の式を読む。原データのハッシュ・MathMLを変更せず、分子のsinはそのまま保持する。',
 'U,wは既出の同じ点の非負の速さ。αは正の系速度から点速度への向き付き角の代表(-π,π]という既出の明示した読みを保つ。実数測度と単位円二成分を結び、K/kの同じ点・尺度・全期間を保持する。零速度の角、縦成分零での商を補わず、点の光速上限は追加しない。',
 '印刷式は非負平方根を符号付き分母1+vw cosα/V²で割る式として保持する。分母の絶対値や二乗式へ替えない。分母負では非負のUと一致しない反例があるが、その条件を隠して前提を狭めたり、著者が正分母条件を明記したことにしたりしない。式の帰属を記述することと、広い前提からの普遍的な導出が正しいことは別である。',
 '前提ejpbは既出の運動・厳密成分・同じ三量の定義を合わせる。s2t自身の非零分母と非負被開平数は数式の定義域として保つ。前提がある場合でも結論内容が偽になり得ることを検査し、検証器による証明済みとはしない。',
 'einfacher Rechnungは、同じ前提から同じ結果までつながる非空有限手順列の非負負担合計が文脈上低いという明示した読み。既存s2w/s2x/s2yとzlw/zlx/zla/zlb/zlcを再利用し、手順数・負担値・数値閾値・実行時間は原文へ補わない。許容変形の関係や容易さの著者評価自体も偽であり得る。',
 '旧文133–135の式・帰結・計算評価を現行稿で置き換え、旧版・旧定義・旧証拠は保存する。現在の同じ物理設定へ接続し直し、旧s2v/s3c/s3dの内容と等価だとして判断を流用しない。未変更の既判断のみを依存一致で引き継ぐ。',
 '原刊の意味を記述する目標は、著者の理論・推論を全て正しいと証明することではない。有限対照、旧代数証拠、全実数域の拒否、原刊通読を区別する。後続u0141の対称性と軸方向の合成は別途。',
]


def definitions():
    ctx=v('context');point=v('point');author=k('rd');scope=k('eisoq')
    text=define('ejpa',[('context','d')],both(k('ejoi',k('zkp'),ctx),k('ejoj',k('zkq'),ctx),k('ejow',k('eiso4'),ctx)))
    text+=content('ejpb',k('ejpa',k('zb6')))
    truth=op('e','n p a b','n p a b');cosine=app(k('zkt'),truth);sine=app(k('zkt'),op('u',truth))
    text+=content('ejpc',both(k('ejpa',k('zb6')),k('s2t',k('tc'),k('zb7'),k('zkq'),cosine,sine,k('zkp'))))
    method=v('method');steps=k('zlx',method,point)
    easy=k('s2y',steps,quote('ejpb'),quote('ejpc'),'i[before i[e] after i[e]]['+k('zla',v('before'),v('after'),point)+']','i[step '+STEP+']['+k('zlb',v('step'),point)+']','i[burden b]['+k('zlc',v('burden'),point)+']')
    text+=content('ejpd',q('g','method','a',both(k('zlw',author,method,point),easy)))
    text+=content('ejpe',k('zc',k('zkx'),author,quote('ejpb'),quote('ejpc'),scope,point))
    text+=content('ejpf',k('uh',k('zkx'),author,quote('ejpd'),scope,point))
    text+='d ejpg[] f[j s[k ejpe[]]].\nd ejph[] f[j s[k ejpf[]]].\n'
    text+=define('ejpi',[],both(k('eir3',k('zkx'),author,k('eirf'),quote('ejpg'),k('ri')),k('ue',k('zkv'),k('zkx'),k('ri')),op('u',op('e',k('zkv'),k('zkx')))))
    text+=define('ejpj',[],k('eir3',k('zkx'),author,k('eirf'),quote('ejph'),k('ri')))
    text+=define('ejpk',[],both(k('uh',k('zkw'),author,quote('ejpc'),scope,k('ri')),k('ue',k('zkx'),k('zkw'),k('ri')),op('u',op('e',k('zkx'),k('zkw')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,name in zip(INDICES,('ejpk','ejpi','ejpj')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=name,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='printed_velocity_quotient_and_easy_calculation_attributed',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=list(INDICES),limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/velocity-angle-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
