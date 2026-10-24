"""Compose both research subjects of the sixth section without asserting results."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read,FIELDS as FIELD_REGIME
from scripts.compose_magnetic_action import FIELDS as MAGNETIC
from scripts.compose_field_equations import POINT
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import v,call as k,app,op,both

PARENT='examples/v014/einstein-vacuum-field-domain.noema'
PARENT_BASIS='data/vacuum-field-domain-basis-v1.json'
FULL='examples/v014/einstein-sixth-section-heading.noema'
CORE='examples/v014/sixth-section-heading-core.noema'
BASIS='data/sixth-section-heading-basis-v1.json'
ANNOTATIONS='data/sixth-section-heading-identifiers-v1.json';INDEX=357
DRIVING=MAGNETIC+[('driveunit','a'),('driving',POINT)]
code=lambda fs:'i[h['+' '.join(t for _,t in fs)+'] c]'
PRIMITIVES={
 'eispd':([('inquiry','a'),('designation','a'),('equations',code(FIELD_REGIME)),('coordinates','i[h[a a a a d] c]'),('context','d')], 'inquiryが、designationで指されequationsの閉じた規約で内容を特定した場の方程式について、coordinatesが保つ同じ出来事の二表示と二座標系を用い、表示系を変更したときの式の形・成分と独立変数の対応・適用条件を調べる研究である。equationsの第一引数の系、同じ長さ時間尺度・文脈・領域・電荷と場と力の単位・二換算係数・電気側と磁気側の二場の役割を保つ。二つの別の物理的過程の式の比較、原語名だけの引用、成分の単なる改名とは区別する。これは式の変換を扱う主題関係であり、特定の変換式・連鎖律・法則の不変性・導出の完了を断言しない。呼称の綴りは別添えに置き、閉じた規約を変えて同じ主題と扱わない。'),
 'eispe':([('inquiry','a'),('phenomenon',code(DRIVING)),('context','d')], 'inquiryが、閉じたphenomenonの同じ担体・系・出来事・文脈、電荷と力の記録・単位、場と領域・局所値、座標時刻の軌跡と速度、力/電荷の駆動により特定した作用について、その物理的な性格、何に由来しどの条件で現れるか、既存の記述の中でどう解釈されるかを検討する研究である。単なる出現個数や語源だけの研究とは分ける。現象の型を研究対象として参照し、実際の一試行の存在、原因や解釈の確定、根本概念か補助概念かの結論を要求しない。作用が現れない比較例を検討することも許す。'),
 'eispf':([], 'この論説のMaxwell-Hertzsche Gleichungenという歴史的な呼称の個体。電気側と磁気側の場の方程式を指す用法であり、真空における式の内容と物理的な適用規約はejsqへ別に接続する。二人の人物個体、Maxwell理論の全ての主張、固有名そのものの真理とは区別する。'),
 'eispg':([], 'この論説の第六節という区分。u0152の見出しから次の第七節u0178の直前u0177までを含み、第二部eispbの直接の下位区分である。冒頭だけの仮定範囲znoとは別の範囲である。'),
 'eisph':([], '固定原文einstein-1905:u0152全体の第六節見出しの箇所。二つの文による主題を一つの節題として案内する。区分eispg、前の部見出しeispc、次の本文仮定znpとは別である。'),
}
MEANINGS={
 'ejsq':'真空領域・物理的な二場と単位のejspへ、既出の光速度tcを渡す。同じ系の長さ時間尺度をeisccで同じ速度単位tbへ結び、正の無名数だけをVへ代用しない。方程式を研究対象として指定するための条件規約であり、現在の全ての場が満たすという断言ではない。',
 'ejsr':'同じ点状担体・系・出来事の電荷数値を正の単位1に固定し、磁気的な力の記録と場の局所評価・実際の座標時刻速度をeicoで結ぶ。力/電荷の単位をeisar、同じ速度・磁気側値・換算係数による局所駆動をeidzへ結ぶ。導体・磁石や閉回路の存在は要求しない。',
 'ejss':'ejsrの同じ局所駆動の少なくとも一空間成分が非零であるという、磁場中の運動に伴って作用が現れる場合の条件。単位・場・速度を共有し、磁場だけの非零や運動だけから非零作用を補わない。',
 'ejst':'同じ研究主題が、Maxwell-Hertzの呼称eispfで指す真空の場の六方程式と物理的規約ejsqの変換を、同じ出来事の二座標系の表示対応eiu2を保って扱う。後の本文の仮定や変換結果を先取りしない。',
 'ejsu':'同じ研究主題が、磁場中の運動に伴う局所的な単位電荷あたりの作用ejssの物理的な性質・由来・解釈を検討する。場の系依存性や補助概念という後続の結論をこの見出しから断言しない。',
 'ejsv':'同じ研究・文脈に、真空の方程式の変換ejstと、運動に伴う起電力の性質ejsuの両主題を結ぶ。二つの無関係な研究に分けず、一方だけで第六節の主題としない。',
 'ejsw':'同じ第二部に属する深さ2・表示番号6の第六節を、二つの主題ejsvを案内する見出しへ結ぶ。部見出しからの順序、箇所・節・部と冒頭仮定範囲との区別を保持する。',
}
LIMITS=[
 'u0152全文を原刊907頁で照合する。§6の番号、真空のMaxwell-Hertz方程式の変換、磁場中の運動で現れる起電力の性質についてという二つの主題を保持する。見出しを本文の仮定や帰結の断言へ変換しない。',
 '第一主題は、この節で扱う六つの回転式s5yを、同じ系・領域・単位と物理的な二場、物質占有のない領域、既出V=tcの速度単位へ接続した規約として読む。Maxwell-Hertzの歴史的な呼称を同じ規約へ結び、全ての時代の同名の式や現代の物質中の構成則まで同じ式としない。',
 '変換は第三節における同じ出来事の座標と時刻の対応eiu2を保つ、表示系の変更として読む。原文の主題から、方程式の不変性、同じ形の成立、逆変換、特定の場の変換式や導出の健全性を補わない。',
 '見出しは式の一般的な研究対象を案内するため、場・領域を引数とする閉じた規約を渡す。続く本文が選ぶ現在の場znl/znmと領域znkをここで既に真として仮定しない。その具体的な仮定、表示式、物理的な場の成分の説明はu0153以降で接続する。',
 '起電力はu0173–u0176の説明を参照し、動く正の単位試験電荷に対する局所的な力/電荷の作用として読む。閉回路の電圧だけや機械力そのものの単位と同一視しない。本文が単位電荷を具体的なcm・Dynで定義する箇所は、この見出しでは先取りしない。',
 '運動は同じ系・出来事の実際の座標時刻微分seocと全軌跡規約sepwに接続する。導体の全体運動や磁石の静止を一律の条件にせず、同じ磁気側場の局所値と速度による作用をeico/eidzで指定する。磁場と速度が平行な場合などの零作用は、現れる作用の非零な事例から外れるが、研究の比較対象として禁止しない。',
 '起電力の性質の研究では、同じ系の局所的な磁気作用と物理的同定規約を対象の記述に使う。u0174の一次近似の旧表現を厳密な系間の力変換へ昇格させず、u0175の新表現やu0176の補助概念という結論も見出しの意味へ追加しない。',
 '真空条件は方程式の適用領域へ課し、力を定義する試験電荷の記述へ同時に物質不在を要求しない。主題の二部分は同じ節で扱うが、同じ実際の一試行で全条件を充足済みとはしない。',
 '今回の新しい基本関係は、閉じた方程式規約と座標対応を使う変換研究、閉じた作用の規約を使う物理的性質の研究という二種類の主題関係である。固有名・方程式・真空・運動・力の内容そのものは引数の既存合成へ置く。他の三基本記号は呼称・節・箇所への参照だけである。',
 '有限検査は規約の引数結合、局所駆動の三成分、零作用、単位、主題の引用、見出しの階層と順序を調べる。全実数の軌跡・領域・微分を列挙せず、引用から実際の物理法則を実行しない。原文全体の判断は別記録に置く。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('ejsq',FIELD_REGIME,both(k('ejsp',*[v(n) for n,_ in FIELD_REGIME],k('tc')),k('eiscc',v('frame'),v('lengthunit'),v('timeunit'),k('tb'),v('context'))))
    text+=define('ejsr',DRIVING,both(k('sca',v('charge'),k('bb','n p b b')),k('eico',*[v(n) for n,_ in MAGNETIC]),k('eisar',v('driveunit'),v('forceunit'),v('chargeunit'),v('context')),k('eidz',v('velocity'),v('magnetic'),v('conversion'),v('driving'))))
    nonzero=[op('u',k('sca',app(v('driving'),k(axis)),k('bb','n p a b'))) for axis in ('yn','yo','yp')]
    text+=define('ejss',DRIVING,both(k('ejsr',*[v(n) for n,_ in DRIVING]),op('x',nonzero[0],op('x',nonzero[1],nonzero[2]))))
    topic=[('inquiry','a'),('context','d')]
    text+=define('ejst',topic,k('eispd',v('inquiry'),k('eispf'),'r[p ejsq]','r[p eiu2]',v('context')))
    text+=define('ejsu',topic,k('eispe',v('inquiry'),'r[p ejss]',v('context')))
    text+=define('ejsv',topic,both(k('ejst',v('inquiry'),v('context')),k('ejsu',v('inquiry'),v('context'))))
    text+=define('ejsw',[],both(k('eihq',k('eisph'),k('eispg'),k('eispb'),k('eirf'),'n p c b','n p g b','r[p ejsv]',k('ri')),k('ue',k('eispc'),k('eisph'),k('ri')),op('u',op('e',k('eispc'),k('eisph'))),op('u',op('e',k('eispg'),k('zno')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])+[dict(kind='assert',body=dict(kind='call',symbol='ejsw',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='vacuum_equation_transformation_and_motional_driving_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/vacuum-field-domain-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eispf',role='designation',forms=[dict(text='Maxwell-Hertzschen Gleichungen',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
