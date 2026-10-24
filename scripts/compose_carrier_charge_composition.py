"""Compose signed charge from a complete family of distinct material carriers."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,quant as q,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_attached_material_charge import ALL,LABELS,BALL,args
from scripts.compose_convective_charge_setting import REGIONAL_TOTAL,COUPLED,AMOUNT

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-complete-material-attachment.noema';PARENT_BASIS='data/complete-material-attachment-basis-v1.json'
FULL='examples/v014/einstein-carrier-charge-composition.noema';CORE='examples/v014/carrier-charge-composition-core.noema'
BASIS='data/carrier-charge-composition-basis-v1.json';ANNOTATIONS='data/carrier-charge-composition-identifiers-v1.json'
LIST='j[a]';WEIGHTS='h[a] '+R;COMPONENTS='h[a] a';PORTIONS='h[a] '+LABELS
SUM=[('carriers',LABELS),('weights',WEIGHTS),('value',R)]
FAMILY=[('carriers',LABELS),('components',COMPONENTS),('portions',PORTIONS)]
PARTITION=[('distribution','a'),('context','d')]+FAMILY
SHARED=('context','lengthunit','timeunit','chargeunit','scope')
OWN=[(n,'h[a] '+t) for n,t in ALL if n not in ('body','distribution','members',*SHARED)]
PACKET=FAMILY+[('scope','a')]+[('own'+n,t) for n,t in OWN]
ATTACHED=PARTITION+[(n,t) for n,t in ALL if n in SHARED and n!='context']+[('own'+n,t) for n,t in OWN]
REGIONAL=[('distribution','a'),('kind','a'),('frame','a'),('event','a'),('time',R),('region',BALL),('lengthunit','a'),('timeunit','a'),('quantityunit','a'),('context','d')]+FAMILY+[('weights',WEIGHTS),('value',R)]
AMOUNTS='h['+BALL+'] '+WEIGHTS
TOTAL=REGIONAL_TOTAL+FAMILY+[('amounts',AMOUNTS)]
COUPLED_FAMILY=COUPLED+PACKET+[('amounts',AMOUNTS)]
MEANINGS={
 'ekx4':'有限個体列の中に同じ個体が現れることを、空列の偽から各項との同一性の選言を畳み込んで表す。',
 'ekx5':'同じcarriersの要素だけからなる重複のない有限列。全個体について出現回数を実数の零と一の和で数え、現れる個体が一度だけ現れることを要求する。空列を許し、担体全体が有限だとは要求しない。',
 'ekx6':'有限列の各項に同じweightsを適用して、実数零から符号付き加算を畳み込んだ和。重複禁止と量の妥当性は呼出側で要求し、空列の和は零。',
 'ekx7':'二つの重複なし有限選択について、baseの全成員がextendedにも現れる包含。順序や接頭列の一致は要求しない。',
 'ekya':'全担体の実数値weightsの順序に依存しない総和。全ての正の実数epsilonについて、ある有限選択base以後の全有限拡張のekx6が同じvalueからepsilon未満に入る。有限個への限定、単一の都合よい順序、発散又は無限大の実数化を避ける。',
 'ekyb':'同じ全分布の全物質成員を、指定した担体の非空な全物質点eiacで漏れなく重複なく分割する。各componentの全成員zqnとその担体の全物質点を一致させる。零電荷によって物質成員を除外せず、空の全分布は空の担体族で表せる。',
 'ekyc':'ekybの同じ各担体・局所成分・全物質点について、小さい剛体への完全な不変付着ekx3を要求する。評価系、区間、座標族、部分量関数は担体ごとの関数で明示し、contextと長さ時間電荷単位、比較scopeを共有する。担体全体を一剛体にしない。',
 'ekyd':'同じ系・出来事・時刻・空間領域・量種・単位・文脈における各局所成分のeisvxの値をweightsへ結び、そのekyaの符号付き総和を全分布の同じeisvxの値へ結ぶ。単に成員集合を分けるだけで量の合成を認定しない。',
 'ekye':'ekxeの同じ物理的な領域総量とekybの分割について、選択領域族の全領域でekydを要求し、その総和を同じtotalの値へ一致させる。地域ごとの重み関数はamountsから選ぶが、分布・担体族・分割・系・出来事・単位を選び直さない。',
 'ekyf':'同じ局所設定の密度・規格化・六方程式ekxj、各領域での電荷合成ekye、全担体への小さい剛体の付着ekycを同時に接続する。場の系と各担体の剛性評価系は別の引数として保持し、この結合だけで両系の座標変換や電荷不変性を証明しない。',
}
LIMITS=[
 '有限電荷を持つ領域で、離散的な担体成分の符号付き電荷を順序に依存しない和として読む。担体族は任意で、有限個又は一つの都合よい列挙順へ限定しない。実数値族の無条件収束の条件を明示し、条件収束する並べ替えや発散する領域は有限総量として採用しない。連続体に無数の原子電荷を無条件に割り当てる意味ではなく、各担体の内部は既存の連続体部分量で扱う。',
 'eiac/eirhとzqnを通じて物質同一性と分布の全範囲を接続する。全点が一意な担体へ属するが、異なる担体が空間的に重なることや正負電荷の相殺を集合の重複と取り違えない。零電荷の担体・部分も成員対応を保持する。',
 'ekydの値は場を評価する同じ系・出来事・時刻に属する。担体のownframeで固定する部分量関数を場のframeでの値へ代入しないため、u0238の系間電荷不変を前提としていない。全体の運動を一つの静止慣性系へ限定しない。',
 'ekyfは一地点の完全な引数接続である。場の全領域の局所証人と、各担体の剛性評価系の同じ物質点・出来事・期間との座標対応はまだ明示適用が必要である。イオン/電子、Lorentz理論の電磁的基礎、著者提示と原文単位全体の統合も残る。',
 '408主張・旧定義・意味判断・旧証拠を保持する。有限診断は実際の畳込み・分割・引数共有・全有限拡張の標本を区別し、無限担体族の収束や原文同義性の自動証明としない。',
]

def fold(sequence,initial,params,body):return 'q['+sequence+']['+initial+'][i['+params+']['+body+']]'

def definitions():
    seq=v('sequence');item=v('item');zero='n p a b';one='n p b b';truth=op('e',zero,zero)
    membership=fold(seq,op('u',truth),'found c item a',op('x',v('found'),op('e',item,v('body'))))
    text=define('ekx4',[('sequence',LIST),('body','a')],membership)
    count=fold(seq,k('bb',zero),'count '+R+' item a',k('bd',v('count'),k('szi',op('e',item,v('body')),k('bb',one),k('bb',zero))))
    selected=fold(seq,truth,'ok c item a',both(v('ok'),app(v('carriers'),item)))
    text+=define('ekx5',[('carriers',LABELS),('sequence',LIST)],both(selected,q('f','body','a',op('y',k('ekx4',seq,v('body')),k('sca',count,k('bb',one))))))
    summed=fold(seq,k('bb',zero),'sum '+R+' item a',k('bd',v('sum'),app(v('weights'),item)))
    text+=define('ekx6',[('weights',WEIGHTS),('sequence',LIST)],summed,R)
    extension=q('f','body','a',op('y',k('ekx4',v('base'),v('body')),k('ekx4',v('extended'),v('body'))))
    text+=define('ekx7',[('carriers',LABELS),('base',LIST),('extended',LIST)],both(k('ekx5',v('carriers'),v('base')),k('ekx5',v('carriers'),v('extended')),extension))
    epsilon=v('epsilon');positive=both(k('ba',epsilon),k('bg',k('bb',zero),epsilon))
    limit=q('f','epsilon',R,op('y',positive,q('g','base',LIST,both(k('ekx5',v('carriers'),v('base')),q('f','extended',LIST,op('y',k('ekx7',v('carriers'),v('base'),v('extended')),k('lb',k('ekx6',v('weights'),v('extended')),v('value'),epsilon)))))))
    text+=define('ekya',SUM,both(k('ba',v('value')),q('f','body','a',op('y',app(v('carriers'),v('body')),k('ba',app(v('weights'),v('body'))))),limit))
    body=v('body');label=v('label');part=app(v('portions'),body);component=app(v('components'),body)
    local=both(k('eiac',body,v('context'),part),q('f','label','a',op('z',app(part,label),app(k('zqn'),label,component,v('context')))))
    cover=q('f','label','a',op('z',app(k('zqn'),label,v('distribution'),v('context')),q('g','body','a',both(app(v('carriers'),body),app(part,label)))))
    unique=q('f','label','a',q('f','body','a',q('f','other','a',op('y',both(app(v('carriers'),body),app(v('carriers'),v('other')),app(part,label),app(app(v('portions'),v('other')),label)),op('e',body,v('other'))))))
    text+=define('ekyb',PARTITION,both(q('f','body','a',op('y',app(v('carriers'),body),local)),cover,unique))
    attached=[body if n=='body' else component if n=='distribution' else part if n=='members' else v(n) if n in SHARED else app(v('own'+n),body) for n,t in ALL]
    text+=define('ekyc',ATTACHED,both(k('ekyb',*args(PARTITION)),q('f','body','a',op('y',app(v('carriers'),body),k('ekx3',*attached)))))
    physical=lambda dist,value:k('eisvx',*args(AMOUNT,distribution=dist,amount=value))
    text+=define('ekyd',REGIONAL,both(k('ba',v('time')),k('ekya',v('carriers'),v('weights'),v('value')),physical(v('distribution'),v('value')),q('f','body','a',op('y',app(v('carriers'),body),physical(component,app(v('weights'),body))))))
    regional=args(REGIONAL,kind=k('zor'),time=app(v('point'),k('zc7')),region=v('space'),quantityunit=v('chargeunit'),weights=app(v('amounts'),v('space')),value=app(v('total'),v('space')))
    text+=define('ekye',TOTAL,both(k('ekxe',*args(REGIONAL_TOTAL)),k('ekyb',*args(PARTITION)),q('f','space',BALL,op('y',app(v('sets'),v('space')),k('ekyd',*regional)))))
    text+=define('ekyf',COUPLED_FAMILY,both(k('ekxj',*args(COUPLED)),k('ekye',*args(TOTAL)),k('ekyc',*args(ATTACHED))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==408
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='material_carrier_charge_composition_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/complete-material-attachment-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
