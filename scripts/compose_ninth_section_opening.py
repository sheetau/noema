"""Present the starting curl laws, density explanation and conditional foundation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_convective_foundation_reading import GLOBAL,JETS,typed
from scripts.compose_convective_charge_setting import SETTING,WITNESSES,FIELD_SETTING,NORMAL,SUPPORT,FLOW,at,velocity,args
from scripts.compose_field_equations import FIELD,TAU,POINT,JET,ROLES
from scripts.compose_doppler_infinity import quantified
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-convective-foundation-reading.noema';PARENT_BASIS='data/convective-foundation-reading-basis-v1.json'
FULL='examples/v014/einstein-ninth-section-opening.noema';CORE='examples/v014/ninth-section-opening-core.noema'
BASIS='data/ninth-section-opening-basis-v1.json';ANNOTATIONS='data/ninth-section-opening-identifiers-v1.json';INDEX=408
PHYSICAL_WITNESSES=[(n,t) for n,t in WITNESSES if n not in ('electricjet','magneticjet')]
PHYSICAL_LOCAL=SETTING+[('point',POINT)]+PHYSICAL_WITNESSES
CASES=[(n,t) for n,t in GLOBAL if n!='context']
PROJECTED=[(n,t) for n,t in GLOBAL if n not in dict(FIELD_SETTING)]
SELECTOR=lambda result:'i[h['+' '.join(t for n,t in GLOBAL)+'] '+result+']'
PRIMITIVES={
 'eiswb':([], 'u0231–u0232の規格化電荷密度ρという表記。実際の電荷密度の4π倍という意味をekyzの物理的規約とekzfの射影で指定し、記号名だけで意味を代用しない。'),
 'eiswc':([], 'u0232の三速度成分(ux,uy,uz)の順序付き表記。三空間軸の流速場をekyzとekzgへ結び、時刻を第四の速度成分へ追加しない。'),
 'eiswd':([('designation','a'),('setting',typed(GLOBAL)),('selector',SELECTOR(TAU)),('document','a'),('scope','a'),('reference','d')],'同じdocumentとscopeでdesignationが表すスカラー場を、settingの閉じた規約に従う各設定からselectorが取り出す四座標の実数値関数として解釈する。同じ設定の系・場・分布・単位・密度などの役割を共有し、別設定から値だけ取り替えない。規則内の物理的同定と量の換算を保持し、原語の綴りや偶然の数値一致で意味を代用しない。規約の仮定に従う記号の解釈であり、現実の設定の存在や場の方程式の真理を認定しない。既存eislo/eispiと同種の表記解釈を、設定からのスカラー場射影の型で用いる。'),
 'eiswe':([('designation','a'),('setting',typed(GLOBAL)),('selector',SELECTOR(FIELD)),('document','a'),('scope','a'),('reference','d')],'同じdocumentとscopeでdesignationという順序付き三成分の表記を、settingの同じ設定からselectorが取り出す三空間軸の場として解釈する。軸yn/yo/ypの順に対応する四座標上の実数値関数で、時刻軸を第四成分にせず、系・単位・対象・評価点を共有する。物理的なベクトルの種類はsettingの規約で合成し、単なる三数の列や関数実装名に縮めない。記号解釈だけから物理的仮定や方程式の現実成立を実行しない。既存eispiを設定からのベクトル場射影の型で用いる。'),
 'eiswf':([], '固定原文u0228のWir gehen aus von den Gleichungenという導入箇所。'),
 'eiswg':([], '固定原文u0229のM0383、原系の三行二列の六つの回転方程式の表示箇所。'),
 'eiswh':([], '固定原文u0230のwobeiという、同じ式の記号説明を導く箇所。'),
 'eiswi':([], '固定原文u0231のM0384、ρと電場の発散の等式の表示箇所。'),
 'eiswj':([], '固定原文u0232第一文、die 4π-fache Dichteからbedeutetまでの意味説明箇所。直前のρの式を主語として受ける。'),
 'eiswk':([], '固定原文u0232第二文、Denkt man sichからbewegter Körperまでの条件付きの基礎を述べる箇所。'),
 'eiswl':([], '固定原文u0227の第九節見出しの箇所。既存の節区分eisv6及びその本文導入とは別である。'),
 'eiswm':([('node','a'),('author','a'),('prior','a'),('referent','i[e]'),('document','a'),('reference','d')],'同じdocumentにおけるauthorのnodeの指示表現が、先行箇所priorで提示した同じ閉じたreferentの内容を再び指すという照応。内容の量化・対象・条件と先行箇所を保持し、似た別命題や後続の変形式へ交換しない。指示した内容の真理、導出の健全性、著者の同意の強さはこの照応だけから認定しない。'),
}
MEANINGS={
 'ekzq':'同じ場の設定・地点・七つの局所証人について、実際の電荷密度場と規格化密度場の値を同じekxgへ渡す。担体別の成分電荷合成又は方程式を局所解釈の条件へ加えない。',
 'ekyy':'対流を含む同じ分布・二場・単位・密度場・速度場の物理的解釈。非空領域の全有効点で七つの局所証人による球平均極限と4π規格化ekxg、非零密度の支持ekxk、全成員の実際の速度ekxlを結ぶ。方程式又は剛体への付着を前提に加えない。',
 'ekyz':'同じGLOBAL引数のekyyに、K=ra・長さta・時間rb・速度tbの校正、V=tc、電気換算1・磁気換算1/Vを要求する原系の記号解釈条件。担体パケットの十三引数は後の条件付き基礎と同じインターフェースを保持するために受け取り、この条件では制約しない。',
 'ekza':'同じGLOBAL設定の非空領域の全有効点で、二場の18偏微分s5uと規格化密度・同じ流速を使う原系六式semeが成立する。M0383の表示規則で、電気側発散は別のekzbへ分ける。',
 'ekzb':'同じ設定の全有効点で、電場の三対角偏微分を実際のs5tへ結び、その和と同じ規格化密度の等号semdを要求する。M0384のρの表示規則で、磁気側発散零を補わない。',
 'ekzc':'同じ論述での物理的contextについて、ekyzの原系解釈に従う全設定に原系の六式と電気側発散ekyqを要求する内容。初めの式を出発点として採用するときの閉じた内容で、現実の実証済みとはしない。',
 'ekzd':'ekzcと同じ全設定・解釈条件について、六回転式だけのekzaを表示する内容。密度・速度・単位・二場の指示を全体と共有する。',
 'ekze':'ekzcと同じ全設定・解釈条件について、電気側発散と規格化密度のekzbを表示する内容。後続のρ′又は別の系の密度へ交換しない。',
 'ekzf':'同じGLOBAL設定からdensityfieldをそのまま返す射影。実際の電荷密度chargefield又は総量を返さず、4π規格化の物理的内容はekyz内のekxgで指定する。',
 'ekzg':'同じGLOBAL設定からvelocityfieldをそのまま返す射影。ekyzの全成員の座標時刻速度と単位へ結び、任意の三数や固有時速度へ代用しない。',
 'ekzh':'ρの表記をekyz/ekzf、三速度成分を同じekyz/ekzgへ結ぶ二つの意味説明。同じ論説・第九節範囲・文脈を共有し、方程式の真理の主張とは区別する。',
 'ekzi':'著者が原系の同じ六式・発散と物理的解釈ekzcを第九節の出発前提ugとして採用する。コロン後の六式ekzd、wobei後の発散式ekzeと意味説明ekzhを、それぞれの表示箇所・説明関係へ結ぶ。',
 'ekzj':'著者が第二文で条件付き基礎ekyxを主張し、diese Gleichungenが先行導入の同じekzcを指すことを保持する。基礎内の原系法則ekyqと先行のekzcは同じ規則を使用する。仮定の内容とその現実成立を混ぜない。',
 'ekzk':'第九節冒頭の出発点・二つの式の表示・wobei・密度と速度の意味・条件付き基礎を一続きの内容として結び、六箇所の順序と区別を保持する。',
 'ekzl':'u0228–u0232の全内容ekzkを述べるメッセージ。出発前提の採用を、全物理領域における方程式の実証へ変換しない。',
 'ekzm':'同じ著者・論説へekzlを帰属し、第九節見出しに続く本文導入として提示する。既存本文の主張を上書きしない。',
 'ekzn':'場の13引数に、残る19引数を一組で存在量化して対流の物理的解釈ekyyと原系六式・電気側発散ekyqを結ぶ、見出し用の方程式規約。V=tcと速度単位tbを共有する。担体パケットは制約せず、付着・剛性・有限個の担体・物質不在を見出しへ加えない。',
 'ekzo':'同じ研究が、Maxwell-Hertzの歴史的呼称の原系方程式ekznの表示系変更を、同じ出来事の二座標表示eiu2に従って扱う主題。対流項ρuを含む規約を使い、真空の規約ejsqへ戻さない。',
 'ekzp':'第二部に直接属する深さ2・番号9のeisv6を、対流電流を考慮する方程式変換ekzoの主題へ結ぶ見出し。前節末尾eisvu、今回の見出し、本文導入の順序と箇所の区別を保つ。',
}
LIMITS=[
 'u0227–u0232全体を原刊916頁と固定MathMLで照合する。u0228の導入からu0232第一文のbedeutetまでを、式と記号説明を含む一文として読む。第二文は担体解釈を仮定した場合の理論的な基礎の提示として区別する。',
 'Wir gehen ausは同じ六式とρの定義・物理的解釈を議論の出発前提として採用する著者の声と読む。独立の証明、現実の実験実施、読者全員の同意を含めない。式は同じKの記号解釈に従う任意の設定についての法則の内容とし、特定の観測例だけへ縮めない。',
 '同じGLOBAL型を先行の方程式と後の条件付き基礎に使い、物理的contextは閉じた内容の評価点へ固定する。他の31引数は全称量化する。最初の解釈条件ekyzでは担体パケットの十三引数を一切制約せず、方程式の真偽もこれらに依存しない。剛体への付着を第一文の前提へ逆流させない。',
 'M0383は18偏微分を持つ六回転式、M0384は三対角偏微分の和によるρの式として表示内容を分ける。全体のekyqは同じ地点の21偏微分を共有する。独立な微分表を物理的に選び直す自由を与えず、全てを同じ二場・領域・地点の実際の偏微分へ結ぶ。',
 'ρは実際の同時刻球平均極限による電荷密度の4π倍、速度ベクトルは同じ分布の全成員の同じ系における座標時刻速度と読む。零密度で物質や速度を消さず、異なる流速の種を単一のρuへ勝手に合成しない。有限密度が存在する古典的適用領域の読みを保つ。',
 'Ionen/Elektronenの別の歴史的名称と共通モデル、完全な物質部分への不変な電荷付着、小ささ・剛性、同じLorentz理論の二主題と条件付き法則の採用はekyxを再使用する。現代の粒子構造・負符号・特定電荷値・共通静止系・Born剛性を補わない。',
 'diese Gleichungenはこの導入の原系方程式とρの説明を指す。後続の変換後M0389ではない。磁気側発散零、後続の系間総電荷不変、変換後の式の正しさをここで追加しない。印刷されたM0389の磁気側1/V欠落は旧規約のまま保持する。',
 '見出しは同じ式の表示系変更を研究する主題を案内する。変換式の導出・不変性・全域性・正しさを見出しから断言しない。節の範囲はu0227–u0238であり、次の第十節u0239に先立つ。',
 '有限検査・原刊照合・全単位の意味判断は別の証拠とする。旧408主張・規約・識別表記・判断を保存し、新しい本文二主張を追加する。全実数・全関数域の評価を有限標本へ置き換えない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    point=v('point');inside=k('ejsj',point,v('region'))
    normal=k('ekxg',*args(NORMAL,density=at(v('chargefield')),normalized=at(v('densityfield'))))
    text+=define('ekzq',PHYSICAL_LOCAL,normal)
    physical=both(quantified('g',PHYSICAL_WITNESSES,k('ekzq',*args(PHYSICAL_LOCAL))),k('ekxk',*args(SUPPORT,normalized=at(v('densityfield')))))
    text+=define('ekyy',SETTING,both(k('ejsn',*args(FIELD_SETTING)),q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,physical)),k('ekxl',*args(FLOW))))
    text+=define('ekyz',GLOBAL,both(k('ekyy',*args(SETTING)),*(op('e',v(n),k(s)) for n,s in [('frame','ra'),('lengthunit','ta'),('timeunit','rb')]),k('sca',v('light'),k('tc')),k('sca',v('electricconversion'),k('bb','n p b b')),k('sca',v('magneticconversion'),k('sjd',v('light'))),k('eiscc',v('frame'),v('lengthunit'),v('timeunit'),k('tb'),v('context'))))
    partials=k('s5u',v('electricfield'),v('magneticfield'),v('region'),point,v('electricjet'),v('magneticjet'))
    curls=both(partials,k('seme',v('light'),at(v('densityfield')),velocity(),v('electricjet'),v('magneticjet')))
    div=both(*(k('s5t',app(v('electricfield'),k(a)),v('region'),point,k(a),app(v('electricjet'),k(a),k(a))) for a in ROLES[:3]),k('semd',v('electricjet'),at(v('densityfield'))))
    for name,fs,body in [('ekza',JETS,curls),('ekzb',JETS[:1],div)]:text+=define(name,GLOBAL,both(q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,quantified('g',fs,body)))))
    for name,law in [('ekzc','ekyq'),('ekzd','ekza'),('ekze','ekzb')]:
        values=args(GLOBAL,context=v('point'));text+=content(name,quantified('f',CASES,op('y',k('ekyz',*values),k(law,*values))))
    text+=define('ekzf',GLOBAL,v('densityfield'),TAU);text+=define('ekzg',GLOBAL,v('velocityfield'),FIELD)
    p=v('point');paper=k('eirf');scope=k('eisv6');author=k('rd');intro=k('eiswf')
    text+=content('ekzh',both(k('eiswd',k('eiswb'),'r[p ekyz]','r[p ekzf]',paper,scope,p),k('eiswe',k('eiswc'),'r[p ekyz]','r[p ekzg]',paper,scope,p)))
    explanations=[('eiswf','eiswg'),('eiswg','eiswh'),('eiswh','eiswi'),('eiswi','eiswj')]
    text+=content('ekzi',both(k('ug',intro,author,quote('ekzc'),scope,p),k('eisox',k('eiswg'),quote('ekzd'),p),k('eisox',k('eiswi'),quote('ekze'),p),evaluate('ekzh'),*(k('uf',author,k(a),k(b),p) for a,b in explanations)))
    text+=content('ekzj',both(k('uh',k('eiswk'),author,quote('ekyx'),scope,p),k('eiswm',k('eiswk'),author,intro,quote('ekzc'),paper,p)))
    nodes=('eiswf','eiswg','eiswh','eiswi','eiswj','eiswk')
    text+=content('ekzk',both(evaluate('ekzi'),evaluate('ekzj'),*(k('ue',k(a),k(b),p) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ekzl[] f[j s[k ekzk[]]].\n'
    text+=define('ekzm',[],both(k('eir3',intro,author,paper,quote('ekzl'),k('ri')),k('ue',k('eiswl'),intro,k('ri')),op('u',op('e',k('eiswl'),intro))))
    text+=define('ekzn',FIELD_SETTING,quantified('g',PROJECTED,both(k('ekyy',*args(SETTING)),k('ekyq',*args(GLOBAL)),k('sca',v('light'),k('tc')),k('eiscc',v('frame'),v('lengthunit'),v('timeunit'),k('tb'),v('context')))))
    text+=define('ekzo',[('inquiry','a'),('context','d')],k('eispd',v('inquiry'),k('eispf'),'r[p ekzn]','r[p eiu2]',v('context')))
    text+=define('ekzp',[],both(k('eihq',k('eiswl'),scope,k('eispb'),paper,'n p c b','n p j b','r[p ekzo]',k('ri')),k('ue',k('eisvu'),k('eiswl'),k('ri')),k('ue',k('eiswl'),intro,k('ri')),op('u',op('e',k('eisvu'),k('eiswl'))),op('u',op('e',k('eiswl'),intro))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekzm','ekzp')]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='ninth_section_opening_equations_notation_foundation_and_heading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/convective-foundation-reading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    ann['entries'] += [dict(symbol=n,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]) for n,form in [('eiswb','ϱ'),('eiswc','(u_x,u_y,u_z)')]]
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
