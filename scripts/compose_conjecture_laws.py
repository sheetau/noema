"""Compose the content of the opening conjecture without asserting it as a fact."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_electrodynamics_title import ROOT,read
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-electrodynamics-title.noema';PARENT_BASIS='data/electrodynamics-title-basis-v1.json'
FULL='examples/v014/einstein-conjecture-laws.noema';CORE='examples/v014/conjecture-laws-core.noema'
BASIS='data/conjecture-laws-basis-v1.json';ANNOTATIONS='data/conjecture-laws-identifiers-v1.json'
FRAME=[('frame','a'),('context','d')];LAW=[('law','a'),('theory','a'),('context','d')]
PAIR=[('theory','a'),('first','a'),('second','a'),('context','d')]
THEORY=[('theory','a'),('context','d')];DOMAIN=[('branch','a'),('context','d')]
PRIMITIVES={
 'eisbd':(FRAME,'この座標系に関する物体の位置と時間、慣性質量と機械的作用の記述で、対象とするNewtonの力学方程式が成り立つという適格性。力を受けない物体の等速直線運動、力と運動変化の関係を同じ空間・時間尺度で記述し、座標選択だけで生じる見かけの力を加えない系を指定する。後続u0008でNewtonの方程式と明記される読みを採る。どの系が実際に適格かは物理的入力であり、座標系という名前だけから認めない。電気力学・光学の法則の成立、特定の相対速度・変換式・絶対静止をこの条件へ先取りしない。'),
 'eisbe':([('law','a'),('branch','a'),('theory','a'),('context','d')],'指定した物理的な法則体系theoryにおいてlawがbranchの現象に関する法則に属する。同じ法則は、物理量・適用条件・単位の規約を共有する一つの一般的な関係であり、名前だけが同じ別の式ではない。成立する法則だけを事後に選ぶ条件ではなく、体系が扱う全法則の分類である。分野は重なってよく、電気力学と光学を互いに排他的な法則一覧にはしない。'),
 'eisbf':([], '電気力学という分野への参照。eie5と同じく、電荷・電流、電気側と磁気側の場、その生成・変化と物質への作用を法則として扱う。特定のMaxwell理論や当時の通常理解への参照とは別である。'),
 'eisbg':([], '光学という分野への参照。発光・伝播・方向と速度・反射屈折・干渉など、光による物理的な現象とその関係を法則として扱う。ここで光を特定の粒子モデルや物質的な伝達媒体へ同一視せず、電気力学との重なりも排除しない。'),
 'eisbh':(THEORY,'この論点のtheoryについて、eisbeが電気力学・光学の対象法則を尽くし、eisbjがその許容・不許容を比較すべき全物理履歴候補を尽くし、vhが各適格座標系での対応する全記述を尽くすという範囲の完全性。法則は物理量とその関係の内容を備え、viはその内容への適合、eisbiは同じ内容の法則としての成立を評価する。観測済みの例・適合する履歴・一致する系・自明な法則だけを選ぶことを認めない。有限の検査標本から完全性を推論せず、全称の物理的な範囲入力として読む。'),
 'eisbi':([('law','a'),('frame','a'),('context','d')],'同じlawの物理量と適用条件を指定座標系で解釈したとき、その法則が対象となる現象を支配する一般的な関係として成り立つ。任意の仮想履歴がこの法則に適合することではなく、法則としての成立を述べる。記述候補への適合viや、異なる系での適合の保存とは区別する。法則の文字列が同じというだけでは成立せず、未知の物理入力を真に補完しない。'),
 'eisbj':([('history','a'),('context','d')],'この論点で法則の許容・不許容を比較する、物体・電荷・電流・電磁場・光などの状態と変化の物理的な候補履歴。対象と量の同一性、空間・時間の範囲、初期条件などの記述条件を備え、vhが同じ履歴を各系の量と座標で表す。実在した履歴だけや、比較対象の法則に適合する履歴だけに限定しない。候補としての物理的な記述可能性と法則への適合を区別する。必要な全候補範囲はeisbhで要求する。'),
 'eisbk':([], '絶対静止という概念への参照。どの座標系・他物体を選ぶかによらず特権的に定まる静止であり、ある基準系に対する位置不変eiahとは区別する。この概念を記述すること自体は、そのような静止・空間・媒体の物理的実在を主張しない。'),
 'eisbl':([], '力学という分野への参照。物体の運動、質量、力・運動量などの機械的な作用と状態変化の関係を扱う。ここではeisbdと同じNewtonの力学を参照し、電気力学・光学での主張を機械的作用だけの問題へ縮めない。'),
 'eisbm':([('concept','a'),('branch','a'),('property','a'),('context','d')],'指定分野の現象におけるpropertyがconceptに対応する物理的な特性である。絶対静止については、選んだ座標で位置が一定という記述上の差ではなく、物理的現象の側にその特権的な静止を特徴付ける違いがあることを指す。名称・座標値・説明形式だけの差や単なる未観測を対応する特性としない。この関係の否定を、物体・運動・相対静止そのものの不存在へ替えない。'),
}
MEANINGS={
 'eifb':'物理的な座標系vaであり、同じ文脈で力学方程式の成立eisbdを満たす系。旧satの相対等速・回転なし・二系の相異という条件を今回の量化範囲へ代用しない。',
 'eifc':'同じ体系・文脈の電気力学又は光学の法則。分野が重なる一法則も許し、別体系や別文脈の法則を混ぜない。',
 'eifd':'同じ体系に属するeifcの全法則について、全候補履歴eisbjの全対応記述vhが同じ法則への適合viを二つの系で保存する。既存sar/saq/sapの非空性・両側の記述存在・全対応対の同値を再利用する。数値座標の同一性ではない。',
 'eife':'指定体系の全ての対象法則が同じ指定系で法則として成り立つ。これだけで候補履歴の全てを法則適合としない。',
 'eiff':'完全な体系と候補・記述範囲、電気力学と光学の双方に対象法則があること、適格系があることを要求する。その全適格系でeifeが成立し、その全系対でeifdが成立する。空の系・片分野の欠落・都合のよい一対だけの一致を全ての系で同じ法則が成り立つことに替えない。',
 'eifg':'力学方程式が成り立つ全ての座標系に共通する、eiffの完全な電気力学・光学法則体系があるという内容。法則の実測済み一覧やMaxwellの既存体系だけに限定しない。',
 'eifh':'指定分野の現象に絶対静止eisbkに対応する特性が一つもない。どれか一つの特性がないだけでは足りず、基準系に対する運動や静止の記述は否定しない。',
 'eifi':'同じ文脈で、力学だけでなく電気力学でもeifhの対応特性が存在しないという内容。光学だけへの否定や、二分野の片方だけの否定へ縮めない。',
 'eifj':'絶対静止に対応する現象の特性が力学・電気力学にないというeifiと、全力学適格系で共通の電気力学・光学法則が成り立つというeifgを同じ評価点で結ぶ内容。推測としての提示・根拠・一次の量という留保は別途接続し、この内容自体を新しい著者主張として本文へ追加しない。',
}
LIMITS=[
 'u0004[148,460)の推測内部の二つの内容を構成する依存群。第一文の根拠・推測という力・対照の提示・一次での既証は未接続であり、一文や段落全体の判断ではない。',
 'Newtonの力学方程式が成立する系という読みを後続u0008と共有する。旧sawの等速・非回転という系対条件を同一と決めず、汎用のsarだけを再利用する。',
 '同じ法則は全候補の対応記述で許容条件が保存されるという外延的な読みと、その同じ法則の各系での成立を合わせる。説明機構の同一性や座標値の一致を要求しない。物理量・法則内容・範囲の充足は基礎入力であり、有限標本で実証しない。',
 '適格系と双方の法則の非空性を論点の前提として保持する。単一の適格系しか与えられないモデルも量化式自体は扱い、少なくとも二つの異なる系があるとの追加主張はしない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eifb',FRAME,both(k('va',v('frame')),k('eisbd',*args(FRAME))))
    text+=define('eifc',LAW,op('x',k('eisbe',v('law'),k('eisbf'),v('theory'),v('context')),k('eisbe',v('law'),k('eisbg'),v('theory'),v('context'))))
    text+=define('eifd',PAIR,k('sar',v('first'),v('second'),'i[law a]['+k('eifc',v('law'),v('theory'),v('context'))+']','i[history a]['+k('eisbj',v('history'),v('context'))+']','i[history a frame a representation a]['+k('vh',v('history'),v('frame'),v('representation'),v('context'))+']','i[law a representation a]['+k('vi',v('law'),v('representation'),v('context'))+']'))
    text+=define('eife',[('theory','a')]+FRAME,q('f','law','a',op('y',k('eifc',v('law'),v('theory'),v('context')),k('eisbi',v('law'),v('frame'),v('context')))))
    exists=lambda branch:q('g','law','a',k('eisbe',v('law'),k(branch),v('theory'),v('context')))
    every=q('f','frame','a',op('y',k('eifb',*args(FRAME)),k('eife',v('theory'),*args(FRAME))))
    pairs=q('f','first','a',q('f','second','a',op('y',both(k('eifb',v('first'),v('context')),k('eifb',v('second'),v('context'))),k('eifd',*args(PAIR)))))
    text+=define('eiff',THEORY,both(k('eisbh',*args(THEORY)),exists('eisbf'),exists('eisbg'),q('g','frame','a',k('eifb',*args(FRAME))),every,pairs))
    text+='d eifg[] e[b context['+q('g','theory','a',k('eiff',*args(THEORY)))+']].\n'
    text+=define('eifh',DOMAIN,op('u',q('g','property','a',k('eisbm',k('eisbk'),v('branch'),v('property'),v('context')))))
    text+='d eifi[] e[b context['+both(k('eifh',k('eisbl'),v('context')),k('eifh',k('eisbf'),v('context')))+']].\n'
    text+='d eifj[] e[b context['+both('t[k eifi[]][v context]','t[k eifg[]][v context]')+']].\n'
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==213;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='content_of_conjecture_with_qualified_frames_and_common_laws',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=['eifj'],statement_indices=[]).document
    ann=json.loads(read('data/electrodynamics-title-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
