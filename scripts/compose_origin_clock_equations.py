"""Apply the current transformation to the same clock's origin records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_origin_clock_question import ROOT,read
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-origin-clock-question.noema';PARENT_BASIS='data/origin-clock-question-basis-v1.json'
FULL='examples/v014/einstein-origin-clock-equations.noema';CORE='examples/v014/origin-clock-equations-core.noema'
BASIS='data/origin-clock-equations-basis-v1.json';ANNOTATIONS='data/origin-clock-equations-identifiers-v1.json';INDEX=339
MEANINGS={
 'ejjc':'同じ時計の現在のk/K記録対ejitを、既出の全座標変換のK範囲eiyz・k範囲eiy2・同じ出来事の対応eiyyへ結ぶ。k記録の空間三成分は零。全座標変換が固定している現在状況zb6との一致を明記する。',
 'ejjd':'k原点に校正した同じ時計ejipと全K時刻の実際の比較ejirを保持し、全ての局所記録対ejitがejjcを満たす。変換に都合のよい一対だけを候補に選ばず、対応の欠落や原点から外れた別記録も排除する。',
 'ejje':'同じK/k二記録のτ=β(t−vx/V²)と、同じK記録のx=vtをsvf/svgで連言する。β=1/√(1−(v/V)²)を同じ正の係数へ結び、光速V・速度v・符号付き座標時刻を保つ。',
 'ejjf':'同じ原点時計の完全な現在の記録範囲ejjdについて、全ての対応対ejitで同じ二式ejjeが成り立つ。一つの出来事のx,tと別の出来事のτを組み合わせない。',
 'ejjg':'同じ原点時計zieに関する二式の内容。u0119のx,t,τの参照、u0120の時間式、u0121の連言、u0122の原点軌道を一つの適用範囲に保持する。',
 'ejjh':'前の時計の設定ejiwと、同じ現在の最終四式ejeh、時計の全記録範囲ejjdを合わせた、二式を得る際の文脈上の前提。問いの答えや率の平方根は追加しない。',
 'ejji':'著者が既出の設定と変換ejjhから同じ二式ejjgが成り立つと提示し、その成立を明白とするzc/zdg。処理系の一般証明や観測の実施報告ではない。',
 'ejjj':'同じ時計の二式の成立と明白さejjiを述べるメッセージ。',
 'ejjk':'二式の提示を同じ著者・論説へ帰属し、同じ時計の進み方の問いzigに続ける。導入・式・連言・式の四単位を一つの文として接続する。',
}
LIMITS=[
 'u0119–u0122を原刊904頁のZwischen die Größenからx=vt.まで照合する。M0211=x、M0212=t、M0213=τは同じ時計の場所で生じる同じ出来事のK/k座標を指す。移動系のξを原文のxへ取り違えない。',
 '原文のZwischen die Größenという表現を固定原文のまま扱い、二式の成り立つ範囲を同じ時計の現在の記録へ限定する。一般の全空間点にx=vtを要求せず、時計の内部部品全ての座標も同じとしない。',
 '原点配置・正確なτ表示・全時刻の比較は前の思考設定と問いから継承する。全局所記録対を先に選び、その全てが既出の座標変換の範囲と同じ出来事対応に属することを要求する。式を満たす対だけを先に選ばない。',
 '時間式と軌道式は既存svf/svgを再利用する。正のβ=1/√(1−(v/V)²)とV/√(V²−v²)の同一性を明示し、平方根の逆数を平方根自身に替えない。現在の物理設定は既出の0<v<Vを継承し、数値核では負の座標時刻も許す。',
 'offenbarは同じ著者による成立の明白さの提示、コロンとundは同じ範囲の二式の導入と連言と読む。既出の時計設定と変換からの帰結を述べるzcは文脈上の前提を明示した読みで、原文がその前提をここで逐語的に再掲したとはしない。',
 'u0123–u0124のτ=t√(1−(v/V)²)と差の式、u0125の単位秒あたりの遅れ・近似は今回の内容へ加えない。二式を一時刻で評価しただけで、問いの率や答えの存在が証明されたとはしない。',
 '全実数時刻の量化を持つ実際の配置と比較は前の定義へ接続する。有限モデルの数値・結合検査と、原文四単位の通読判断、一般の物理的真理の証明を区別する。新しい基本記号は追加しない。',
]

def definitions():
    clock=v('clock');own=v('own');lab=v('lab');ctx=v('context');zero=k('bb','n p a b')
    fields=[('clock','a'),('own','a'),('lab','a'),('context','d')];selected=k('ejit',clock,own,lab,ctx)
    bridge=both(op('e',ctx,k('zb6')),selected,k('eiyz',lab),k('eiy2',own),k('eiyy',lab,own),*(k('sca',k('zc6',own,k(a)),zero) for a in ('yn','yo','yp')))
    text=define('ejjc',fields,bridge)
    allpairs=lambda body:bind(('own','lab'),'a','f',op('y',selected,body))
    text+=define('ejjd',[('clock','a'),('context','d')],both(k('ejip',clock,ctx),k('ejir',clock,ctx),allpairs(k('ejjc',clock,own,lab,ctx))))
    V=k('tc');speed=k('zb7')
    text+=define('ejje',[('lab','a'),('own','a')],both(k('svf',lab,own),k('svg',lab),k('sca',k('soy',V,speed),k('sjd',k('stw',V,speed)))))
    text+=define('ejjf',[('clock','a'),('context','d')],both(k('ejjd',clock,ctx),allpairs(k('ejje',lab,own))))
    text+=content('ejjg',k('ejjf',k('zie'),k('zb6')))
    point=v('point');ev=lambda n:op('t',k(n),point)
    text+=content('ejjh',both(ev('ejiw'),ev('ejeh'),k('ejjd',k('zie'),k('zb6'))))
    text+=content('ejji',both(k('zc',k('zii'),k('rd'),quote('ejjh'),quote('ejjg'),k('eisn5'),point),k('zdg',k('zii'),k('rd'),quote('ejjg'),k('eisn5'),point)))
    text+='d ejjj[] f[j s[k ejji[]]].\n'
    text+=define('ejjk',[],both(k('eir3',k('zii'),k('rd'),k('eirf'),quote('ejjj'),k('ri')),k('ue',k('zig'),k('zii'),k('ri')),op('u',op('e',k('zig'),k('zii')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejjk',arguments=[]))];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_origin_clock_current_coordinate_equations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/origin-clock-question-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
