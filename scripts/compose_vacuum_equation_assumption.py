"""Connect the current vacuum-law assumption, six equations and vector notation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read,FIELDS
from scripts.compose_field_equations import FIELD,POINT,REGION,ROLES
from scripts.compose_material_relative_frame import define
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-sixth-section-heading.noema'
PARENT_BASIS='data/sixth-section-heading-basis-v1.json'
FULL='examples/v014/einstein-vacuum-equation-assumption.noema'
CORE='examples/v014/vacuum-equation-assumption-core.noema'
BASIS='data/vacuum-equation-assumption-basis-v1.json'
ANNOTATIONS='data/vacuum-equation-assumption-identifiers-v1.json';INDEX=152
UNITS=('chargeunit','electricunit','magneticunit','forceunit')
FACTORS=('electricconversion','magneticconversion')
PARAMS=[(n,'a') for n in UNITS]+[(n,R) for n in FACTORS]+[('context','d')]
PRIMITIVES={
 'eispi':([('designation','a'),('rule','i[h['+FIELD+' d] c]'),('document','a'),('context','d')], '同じdocumentの当該議論でdesignationという順序付き三成分の表記が指す場を、成分役割から四座標の実数値関数を返す場と状況に対する閉じたruleの規約に従って解釈する。三成分は当該系の三空間軸の順に対応し、時刻を第四のベクトル成分へ加えない。別の場・系・単位や順序違いを同一表記の意味へ代入しない。物理的な種類と領域内での同じ成分値の条件はruleに合成する。既存eisloの表記解釈を三成分場の型へ適用する一般関係であり、語形の一致、関数の実装識別子、実際の測定実行、引用した法則の真理とは区別する。'),
 'eispj':([], 'u0155の(X,Y,Z)という電気側の三成分の順序付き表記。既出の場znlの三空間役割yn/yo/ypへ規則ejs4で結ぶ。'),
 'eispk':([], 'u0155の(L,M,N)という磁気側の三成分の順序付き表記。既出の場znmの三空間役割yn/yo/ypへ規則ejs5で結ぶ。'),
 'eispl':([], 'u0154のM0287という六方程式の表示箇所。直前znpで導入する仮定を具体化し、後続の成分説明eispmとは別の箇所である。'),
 'eispm':([], 'u0155のwobei以下の二ベクトルの意味を説明する箇所。前の六式eisplと同じ仮定文に属し、独立の実験報告や別の力の法則ではない。'),
}
MEANINGS={
 'ejsx':'既出のK=ra、長さta・時間rb、領域znkと二場znl/znmを、同じ四単位・二換算係数・文脈のejsnへ適用する。速度単位tbの校正eisccも同じ系と尺度へ結ぶ。',
 'ejsy':'同じ現在の二場と領域について、四単位と二つの正の有効換算係数を共有するejsxの証人が存在する。係数を1や1/Vへ固定しない。',
 'ejsz':'同じ現在の物理的な場と尺度ejsy、同じ領域の真空ejsm、同じ二場・領域・既出V=tcへの全六式s5yを結ぶ。一般規約ejsqを本文の具体的な参照へ適用した仮定の条件である。',
 'ejs2':'同じ有効な四座標で、相異なる三空間役割について二つの場を評価し、両側が有効な実数かつ対応成分が等しいことを要求する。関数実装の同一性ではない。',
 'ejs3':'指定領域に有効な点が存在し、領域内の全有効四座標についてejs2が成立するという三成分場の外延的一致。領域外や時刻役割の値をベクトルの第四成分として比較しない。',
 'ejs4':'指定する場が、同じ文脈の物理的な二場・単位の規約ejsyの下で、同じ領域znkの全有効点において電気側znlと三成分で一致する。(X,Y,Z)が指す場の規則。',
 'ejs5':'指定する場が、同じ文脈の物理的な二場・単位の規約ejsyの下で、同じ領域znkの全有効点において磁気側znmと三成分で一致する。(L,M,N)が指す場の規則。',
 'ejs6':'同じKで現在の二場に真空の六式が成立するejszという閉じた内容。本文では仮定として引用し、無条件の物理的真理にしない。',
 'ejs7':'同じ論説の二つの順序付き表記を、それぞれ現在の電気側・磁気側の場を意味するejs4/ejs5の規則へ結ぶ説明内容。',
 'ejta':'著者がznpでejs6を同じ範囲znoに仮定として採用する。Maxwell-Hertzの呼称もその内容へ結び、六式eisplを同じ仮定の具体化として説明し、その表示箇所の内容をejs6へ固定する。',
 'ejtb':'仮定と表示式のejta、成分の意味を述べるejs7を、znpからeispl、eispmへ続く同じ一文の内容として結ぶ。wobei以下は同じ表示式の説明であり、別の仮定や実験事実にしない。',
 'ejtc':'u0153–u0155の仮定・六式・二ベクトルの説明ejtbを述べるメッセージ。',
 'ejtd':'同じ著者と論説へこの一文を帰属し、第六節見出しeisphの後へ置く。旧文152の部分的な仮定提示を置き換える。',
}
LIMITS=[
 '原刊907頁のu0153–u0155を一つの仮定文として読む。mögen ... so daß gelten mögeは、後続の式によって具体化される仮定の採用であり、真空だけから法則が導けたという証明ではない。wobei以下の成分説明も同じ文へ結ぶ。',
 '静止系Kは既出raへの呼称であり、絶対静止を追加しない。場znl/znm、領域znk、光速度tc、長さta・時間rb・速度tbは同じ本文の参照を保つ。四単位と二係数の物理規約は仮定内容の内側へ置く。',
 '真空は同じ全領域で物質の占有がないという既存ejsmの古典的な読みを共有する。外部源や非零場は許す。全領域と実際の偏微分を有限標本へ置換しない。',
 '電気的・磁気的なKraftは当該系の場の強さとして読む。電気側は静止試験電荷への力/電荷、磁気側は電気的寄与と区別した運動電荷への横向きの作用で同定する既存の規約を使う。機械力そのものの次元、現代SIの物質中のH、特定の透磁率を補わない。後続u0161の磁気的質量の説明は別に確認する。',
 '二つの順序付き三成分表記は、同じ領域の全有効四座標における対応成分の一致へ結ぶ。関数の実装同一性を要求せず、領域外の値や時刻役割の成分を比較対象に加えない。物理的な場の同定を三数の綴りだけで代用しない。',
 'M0287の六つの回転式と18偏微分を符号・軸順まで保持する。正のVの下で分母を払った形を用いる。発散条件は追加せず、真空の語から変換後の六式や導出の健全性を認定しない。',
 '今回の一般関係は閉じた規則で三成分場の表記を解釈する一関係。残る四基本記号は二表記と二箇所の参照である。場の意味、真空、微分方程式、仮定・説明の内容は既存関係と合成で記述する。',
 '旧文152だけを新しい提示へ置き換える。旧版・旧定義・旧証拠は保存し、未変更の既判断だけを依存一致で引き継ぐ。引用した仮定を検査の場で真として実行せず、原文の全単位判断は別記録にする。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    ctx=v('context');fixed={'frame':k('ra'),'lengthunit':k('ta'),'timeunit':k('rb'),'region':k('znk'),'electricfield':k('znl'),'magneticfield':k('znm')}
    fields=[fixed.get(n,v(n)) for n,_ in FIELDS]
    text+=define('ejsx',PARAMS,both(k('ejsn',*fields),k('eiscc',k('ra'),k('ta'),k('rb'),k('tb'),ctx)))
    text+=define('ejsy',[('context','d')],bind(UNITS,'a','g',bind(FACTORS,R,'g',k('ejsx',*[v(n) for n,_ in PARAMS]))))
    text+=define('ejsz',[('context','d')],both(k('ejsy',ctx),k('ejsm',k('ra'),k('ta'),k('rb'),ctx,k('znk')),k('s5y',k('znl'),k('znm'),k('znk'),k('tc'))))
    fs=[('field',FIELD),('expected',FIELD)];point=v('point');coords=[app(point,k(n)) for n in ROLES]
    eq=[]
    for axis in ROLES[:3]:
        a,b=[app(app(v(n),k(axis)),*coords) for n in ('field','expected')]
        eq.extend([k('ba',a),k('ba',b),k('sca',a,b)])
    distinct=[op('u',op('e',k(a),k(b))) for i,a in enumerate(ROLES[:3]) for b in ROLES[:3][i+1:]]
    text+=define('ejs2',fs+[('point',POINT)],both(*distinct,*(k('ba',x) for x in coords),*eq))
    inside=k('ejsj',point,v('region'))
    text+=define('ejs3',fs+[('region',REGION)],both(q('g','point',POINT,inside),q('f','point',POINT,op('y',inside,k('ejs2',v('field'),v('expected'),point)))))
    for name,field in (('ejs4','znl'),('ejs5','znm')):
        text+=define(name,[('field',FIELD),('context','d')],both(k('ejsy',ctx),k('ejs3',v('field'),k(field),k('znk'))))
    text+=content('ejs6',k('ejsz',v('point')))
    text+=content('ejs7',both(*(k('eispi',k(sign),'r[p '+rule+']',k('eirf'),v('point')) for sign,rule in (('eispj','ejs4'),('eispk','ejs5')))))
    text+=content('ejta',both(k('ug',k('znp'),k('rd'),quote('ejs6'),k('zno'),v('point')),k('eisch',k('eispf'),quote('ejs6'),k('zno'),v('point')),k('eisox',k('eispl'),quote('ejs6'),v('point')),k('uf',k('rd'),k('znp'),k('eispl'),v('point'))))
    nodes=('znp','eispl','eispm')
    text+=content('ejtb',both(evaluate('ejta'),evaluate('ejs7'),k('uf',k('rd'),k('eispl'),k('eispm'),v('point')),*(k('ue',k(a),k(b),v('point')) for a,b in zip(nodes,nodes[1:])),*(op('u',op('e',k(a),k(b))) for i,a in enumerate(nodes) for b in nodes[i+1:])))
    text+='d ejtc[] f[j s[k ejtb[]]].\n'
    text+=define('ejtd',[],both(k('eir3',k('znp'),k('rd'),k('eirf'),quote('ejtc'),k('ri')),k('ue',k('eisph'),k('znp'),k('ri')),op('u',op('e',k('eisph'),k('znp')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejtd',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='current_vacuum_law_assumption_and_two_vector_meanings',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/sixth-section-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for symbol,form in (('eispj','(X,Y,Z)'),('eispk','(L,M,N)')):ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
