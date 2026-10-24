"""Separate a material interpretation from the equations used as a theory's basis."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_carrier_field_correspondence import GLOBAL,LOCAL,TRANSFER
from scripts.compose_carrier_charge_composition import ATTACHED,TOTAL,AMOUNTS,args
from scripts.compose_attached_material_charge import ALL,LABELS
from scripts.compose_convective_charge_setting import SETTING,WITNESSES,FIELD_SETTING,NORMAL,SUPPORT,FLOW,at,velocity
from scripts.compose_field_equations import POINT,JET
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-carrier-field-correspondence.noema';PARENT_BASIS='data/carrier-field-correspondence-basis-v1.json'
FULL='examples/v014/einstein-convective-foundation-reading.noema';CORE='examples/v014/convective-foundation-reading-core.noema'
BASIS='data/convective-foundation-reading-basis-v1.json';ANNOTATIONS='data/convective-foundation-reading-identifiers-v1.json'
PHYSICAL_WITNESSES=[(n,t) for n,t in WITNESSES if n not in ('electricjet','magneticjet')]+[('amounts',AMOUNTS)]
PHYSICAL_LOCAL=LOCAL+PHYSICAL_WITNESSES
JETS=[('electricjet',JET),('magneticjet',JET)]
LAW_LOCAL=SETTING+[('point',POINT)]+JETS
TOPIC=[('inquiry','a'),('reference','d')]
typed=lambda fields:'i[h['+' '.join(t for n,t in fields)+'] c]'
PRIMITIVES={
 'eisv2':([('designation','a'),('model',typed(ALL)),('scope','a'),('reference','d')],'scopeの用法におけるdesignationの対象種を、閉じたmodelに明示された性質と関係を持つ担体モデルで表すという対応。モデルが指定する物体・量・全履歴・単位の役割を保つ。この抽象化で扱わない構成・種差まで同じとせず、名称の全用法の同義、モデルを満たす全対象への名称の逆適用、対象種の網羅や排他的分類を含意しない。引用したモデルの現実の実在や法則の成立を認定しない。名称だけで内容を代用せず、モデル内の物理的帰属は別の基礎関係で構成する。'),
 'eisv3':([], 'u0232括弧内のIonenという歴史的な担体種の名称。現代の原子・分子の電離状態という分類を自動的に加えず、ここでの物理モデルはeisv2を通じekyrへ結ぶ。'),
 'eisv4':([], 'u0232括弧内のElektronenという歴史的な担体種の名称。負号・特定の電荷質量・点粒子・量子論を名前から補わず、ここでの物理モデルはeisv2を通じekyrへ結ぶ。'),
 'eisv5':([], 'u0232のLorentzschenで指示されるH. A. Lorentzの電気力学と動く物体の光学の同じ理論体系。後代のLorentz共変な全理論やEinsteinのこれからの理論へ交換しない。研究対象と基礎の内容は別に合成する。'),
 'eisv6':([], 'この論説の第九節u0227–u0238という論述範囲への参照。第八節の光学的方法又は後続第十節とは別である。'),
 'eisv7':([('inquiry','a'),('problems','i[h[a d] c]'),('reference','d')],'同じinquiryが、閉じたproblemsの分類に属する問いの全範囲について、その量・性質・規則性と説明を研究対象として扱う。個々の問題の固定条件と実際の質問内容を分類から引き継ぎ、成功例又は既知の答えだけに範囲を縮めない。全問題が解決済み、全ての仮定が現実に成立、分類外の主題を扱わないとは含意しない。'),
 'eiswa':([('theory','a'),('inquiry','a'),('condition',typed(GLOBAL)),('law',typed(GLOBAL)),('reference','d')],'同じtheoryがinquiryの領域について、conditionが指定する物理的解釈・適用仮定の下でlawを自らの基礎的な法則として採用するという位置付け。単にinquiryの概念を借りるだけで指定lawを採用しない理論は含まない。二つの閉じた規則は同じ型・順序の設定引数を共有し、各仮定設定について同じ対象・単位・場へ法則を適用する。別々の成功設定の存在や同じ真偽値だけで代用しない。conditionを採用して構成する同じ理論の基礎であり、conditionの現実成立、lawの真理、論理的含意の証明、全理論の十分な導出をこの位置付けだけで認定しない。物理内容・条件と法則の区別は引用された合成規則で明示する。'),
}
MEANINGS={
 'ekym':'第九節原系の校正规約を、同じframe=ra、lengthunit=ta、timeunit=rb、light=tc、電気換算1・磁気換算1/Vへ固定する。数値比だけで単位付き二場を代用せずejsnを併せる。',
 'ekyn':'同じ地点の密度の物理的解釈ekxgと全担体からの領域電荷合成ekyeを共有する。偏微分や六式を含まず、電荷単位・分布・領域・局所総量を同じ証人に束縛する。',
 'ekyo':'同じ全設定の原系校正ekym、全担体の完全な付着ekyc、全物質出来事の対応ekyjを保持する。非空領域の全有効点で八つの局所物理証人によるekynと非零密度の支持を要求し、全成員の流速ekxlへ結ぶ。方程式の成立をこの解釈条件に入れない。',
 'ekyp':'同じ地点の密度場値と速度場値、二場・二偏微分族を原系M0383の六式とM0384の電気側発散semhへ渡す。変換後の印刷式や磁気側発散零を追加しない。',
 'ekyq':'GLOBALと同じ引数型を持つ原系方程式の規則。非空領域の全有効点で同じ設定に対する二偏微分族がありekypを満たす。担体記述は同じ設定引数として保持するが、方程式の本体へ余分な担体制約を加えない。',
 'ekyr':'全物質部分への固定電荷と小さな剛体のekx3に、許容された少なくとも一つの物質部分の非零な符号付き電荷を結ぶ担体モデル。全体の正味電荷だけでは判定せず、符号・値・内部構造や形を特定しない。',
 'ekys':'同じ論述範囲と文脈において、IonenとElektronenの二つの相異なる名称の対象を同じekyrの担体モデルで表す。二種類の区別を消さず、モデル上で扱う共通の関係を指定する。全担体が二種類だけであるという分類又は現実の二標本の存在を加えない。',
 'ekyt':'同じ問題の実際の質問eisvmと、動く物体に作用される光の閉じた主題条件ekwmをeisvkへ結ぶ第九節の光学問題分類。第八節の方法や解の存在を要求しない。',
 'ekyu':'同じ研究・論述文脈で、運動を含む物体の電気力学eie6と、ekytの全光学問題を研究対象とするeisv7を結ぶ。二主題に別々の研究を選ばず、光学を電気力学という名称だけで省略しない。',
 'ekyv':'同じ理論がekyuの二主題を扱う非空の体系であるというeiscmへの接続。対象分類と理論個体を一つの研究証人へ束縛する。',
 'ekyw':'同じ理論の研究対象ekyvを保ち、その同じ理論がある一つの基礎研究について同じekyo条件の下で同じekyq方程式を基礎法則として採用するeiswaと、それを基礎として用いるeisdiを結ぶ。仮定と法則を引用し、位置付けから物理的真理を脱引用しない。指定法則を採用せず概念だけ借りる場合は除く。Lorentz理論への特定はekyxで行う。',
 'ekyx':'第九節という同じ論述範囲での二つの歴史的担体名のモデル対応ekysと、同じLorentz理論の条件付きの電磁的基礎ekywを結ぶ内容。著者による本文箇所の提示はまだ別に接続する。',
}
LIMITS=[
 'u0232の条件付き基礎の内容を構成する依存群。現行408主張・旧規約・旧判断は保持し、u0227–u0232の出発点、where説明、式、著者提示、見出しの統合までは全単位判断を増やさない。',
 '歴史的な二つの担体種の対象を、この箇所で必要な共通の古典的モデルへ写すという明示した読み。現代のイオンと電子を同義とする読みではない。個々の種の全構造・質量・電荷値を本文が与えると仮定せず、Lorentz 1899年及び1902年の説明を補助資料にする。対応はそのモデルに必要な性質の指定で、全ての中性物体又は任意の電荷分布に逆向きに二名称を与えない。',
 'ekyrの非零は少なくとも一つの物質部分について要求する。正負の相殺を許す。二名称のモデルを例示するだけで、ekyoの全担体へ非零総量・二種類のみという条件を加えない。全電荷が零でも物質や速度を消さない。',
 'Denkt man sich ... so ...は担体解釈を仮定して構成する理論における方程式の基礎的役割と読む。観察者の心理状態や現実の担体の存在を要求しない。eiswaは一般的な条件付き法則の位置付けで、物理の意味はekyoとekyqに保持し、eisdiの意味上の基礎依存と併用する。方程式を条件へ入れて帰結の対象を真の場合だけに狭めない。',
 '同じ閉じたekyo/ekyqはGLOBALの全32引数を共有する。物理的なcontextは引数内にあり、基礎の位置付けを述べるreferenceとは分ける。後者の一致から実際の物理世界を一つ選ばない。',
 'Lorentzschenは電気力学と光学をともに修飾し、bewegter Körperは両主題に共通の運動を含む範囲と読む。静止との比較は排除せず、任意の加速体に一つの静止慣性系を要求しない。基礎から理論全体を導ける十分性や独立な運動方程式の不要を補わない。',
 '密度は既存の球平均極限が有限に存在する古典的領域の読みを保持する。点電荷特異点、別速度の複数種の合成流、後続u0238の系間総電荷不変をこの構成から認定しない。M0389磁気側の印刷された1/V欠落は旧semfのまま保持する。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    one=k('bb','n p b b');zero=k('bb','n p a b')
    text+=define('ekym',GLOBAL,both(k('ejsn',*args(FIELD_SETTING)),*(op('e',v(n),k(symbol)) for n,symbol in [('frame','ra'),('lengthunit','ta'),('timeunit','rb')]),k('sca',v('light'),k('tc')),k('sca',v('electricconversion'),one),k('sca',v('magneticconversion'),k('sjd',v('light')))))
    text+=define('ekyn',PHYSICAL_LOCAL,both(k('ekxg',*args(NORMAL,density=at(v('chargefield')),normalized=at(v('densityfield')))),k('ekye',*args(TOTAL))))
    inside=k('ejsj',v('point'),v('region'))
    physical=both(quantified('g',PHYSICAL_WITNESSES,k('ekyn',*args(PHYSICAL_LOCAL))),k('ekxk',*args(SUPPORT,normalized=at(v('densityfield')))))
    text+=define('ekyo',GLOBAL,both(k('ekym',*args(GLOBAL)),k('ekyc',*args(ATTACHED)),k('ekyj',*args(TRANSFER)),q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,physical)),k('ekxl',*args(FLOW))))
    text+=define('ekyp',LAW_LOCAL,k('semh',v('electricfield'),v('magneticfield'),v('region'),v('point'),v('light'),at(v('densityfield')),velocity(),v('electricjet'),v('magneticjet')))
    text+=define('ekyq',GLOBAL,both(q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,quantified('g',JETS,k('ekyp',*args(LAW_LOCAL)))))))
    part=v('part');amount=app(v('total'),part)
    text+=define('ekyr',ALL,both(k('ekx3',*args(ALL)),q('g','part',LABELS,both(app(v('parts'),part),k('ba',amount),op('u',k('sca',amount,zero))))))
    text+=define('ekys',[('scope','a'),('reference','d')],both(op('u',op('e',k('eisv3'),k('eisv4'))),*(k('eisv2',k(n),'r[p ekyr]',v('scope'),v('reference')) for n in ('eisv3','eisv4'))))
    text+=define('ekyt',[('problem','a'),('reference','d')],k('eisvk',v('problem'),k('eisvm',v('problem'),v('reference')),'r[p ekwm]',k('eisv6'),v('reference')))
    text+=define('ekyu',TOPIC,both(k('eie6',v('inquiry'),v('reference')),k('eisv7',v('inquiry'),'r[p ekyt]',v('reference'))))
    fields=[('theory','a'),('reference','d')]
    text+=define('ekyv',fields,q('g','inquiry','a',both(k('eiscm',v('theory'),v('inquiry'),v('reference')),k('ekyu',v('inquiry'),v('reference')))))
    text+=define('ekyw',fields,both(k('ekyv',*args(fields)),q('g','inquiry','a',both(k('eiswa',v('theory'),v('inquiry'),'r[p ekyo]','r[p ekyq]',v('reference')),k('eisdi',v('theory'),v('inquiry'),v('reference'))))))
    text+=content('ekyx',both(k('ekys',k('eisv6'),v('point')),k('ekyw',k('eisv5'),v('point'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='conditional_convective_foundation_and_historical_carrier_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/carrier-field-correspondence-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]) for n,form in [('eisv3','Ionen'),('eisv4','Elektronen')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
