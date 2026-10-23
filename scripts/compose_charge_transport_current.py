"""Compose signed current from transport across a material section."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_relative_history_match import ROOT,read,FIELDS as MOTION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,F,D,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-relative-history-match.noema'
PARENT_BASIS='data/relative-history-match-basis-v1.json'
FULL='examples/v014/einstein-charge-transport-current.noema'
CORE='examples/v014/charge-transport-current-core.noema'
BASIS='data/charge-transport-current-basis-v1.json'
ANNOTATIONS='data/charge-transport-current-identifiers-v1.json'
FIELDS=[('body','a'),('section','a'),('orientation','a'),('kind','a'),('frame','a'),('context','d'),
        ('timeunit','a'),('quantityunit','a'),('lower',R),('upper',R),('cumulative',F)]
ELECTRIC=[(n,t) for n,t in FIELDS if n!='kind']
MATCH=[('body','a'),('section','a'),('orientation','a'),('timeunit','a'),('quantityunit','a')]+[
    (c+n,t) for c in ('first','second') for n,t in [('frame','a'),('context','d'),('lower',R),('upper',R),('cumulative',F),('current',F)]]+[('offset',R)]
SNAP=[(n,R) for n in ('firstlower','firstupper','secondlower','secondupper','offset')]+[
    ('firstcurrent',F),('secondcurrent',F),('time',R)]
EXTRA=[('section','a'),('orientation','a'),('quantityunit','a')]+[(c+n,F) for c in ('first','second') for n in ('cumulative','current')]
MEANINGS={
 'eia4':'同じ物体に付随する有向断面、量の種類、系、文脈、単位、区間について、順序付き二時刻の累積値の差が同じ符号付き通過量としてeiriの基礎入力へ結ばれる。ここで通過量は断面に対する通過であり、物体の絶対的移動や領域内の保有量の差ではない。',
 'eia5':'非零幅区間の有効な累積関数について、全ての順序付き区間内二時刻でeia4が成立する。累積値の原点は任意であり、始点値を零に固定しない。全時刻対応と物理的な通過の帰属を有限標本から補わない。',
 'eia6':'eia5と同じ累積関数・閉区間に既存liの微分関係を結ぶ、指定時刻の符号付き通過率。端点は区間への片側微分であり、区間外の振舞いを断言しない。無効な時刻、微分の不存在、単なる二時刻平均を除く。',
 'eia7':'eia6の量の種類を既存zorの電気量に固定した符号付き電流。単位はquantityunit/timeunitという組で指定し、アンペアという固有名や現代SIの定数を本文へ補わない。',
 'eiba':'同じ断面・向き・電荷と時間の単位について、区間内の全実時刻にeia7を満たすcurrent関数。電流の時間的経過を表し、零電流、逆向き電流、途中で符号が変わる電流を許す。',
 'eibb':'eiavの同じ経過時間対応の下で、第一時刻と定数offset後の第二時刻における二電流値が有効で等しいという照合。絶対値だけでは比較せず、両時刻を各区間へ結ぶ。',
 'eibc':'同じ物体・断面・向き・単位での二場合のeibaを、時刻原点の差と全区間内実時刻のeibbへ結ぶ。同じ符号付きの大きさと経過という読みであり、累積値の原点や絶対座標の一致は要求しない。',
 'eibd':'同じ相対運動と逆の運動/静止の役割eia3へ、右側物体の同じ有向断面における二場合の電流履歴一致eibcを同時に結ぶ候補条件。運動学的条件から電流一致を導く含意ではなく、磁石・導体の種類や原文への帰属も別途必要。',
}
PRIMITIVE_MEANING='同じ物体に追随する物理的な断面とその正方向について、指定系の第一時刻から第二時刻までに断面を相対的に横切った量の符号付き正味総量を、量の種類・時間単位・量単位・文脈へ結ぶ。正方向への正の量と逆方向への負の量は正に、逆の組合せは負に数える。等時刻は零。sectionは実際の断面の同定、orientationはその一貫した正方向の同定を含む物理入力であり、名前だけや数値の差だけでは成立しない。量の種類が電気量なら正負の電荷の通過を扱い、質量等と混同しない。断面と共に動く物質だけから相対通過を認定せず、保有量の時間差や変位電流をこの入力に代入しない。量の物理的同定・実現は入力の契約で、測定を実行したという断言ではない。'
LIMITS=[
 '導入の導体電流を、マクロ尺度で同じ物体に付随する有向断面を横切る電荷の通過率として構成する。電荷の離散的な通過の微視的跳躍を全時刻で微分可能とせず、採用する連続体尺度と断面族は本文への統合で明示する。',
 'eiriは種類付きの量の通過という再利用可能な基礎関係であり、電流、磁石、導体、原文一文を新原始記号にしたものではない。電気量zorの電気的作用・校正との基礎接続、断面の幾何学的実現、量単位の次元規約は依然必要。',
 '端点では既存liの区間への相対微分を使う。微分が存在しない時刻を含む一般の電流履歴には別の弱い記述が必要。実数の全域と極限を有限サンプルで検証済みとはしない。',
 'eibcは一つの対応する断面を比較する。導体全体の電流分布、全断面の対応、磁化や導電性等を保つ比較条件は未完。電荷輸送の起因、電場、起電力、エネルギー、著者の説明と留保をこの層から推論しない。',
 '原文207主張を保持し、原文の対応範囲・全単位意味確認を増やさない。',
]

def electric_args():return [k('zor') if n=='kind' else v(n) for n,_ in FIELDS]
def interval():return lam('t',R,k('lg',v('lower'),v('upper'),v('t')))

def definitions():
    primitive=FIELDS[:8]+[('first',R),('second',R),('amount',R)]
    text='r eiri['+' '.join(t for _,t in primitive)+'] c.\n'
    a,b=v('first'),v('second');ca,cb=app(v('cumulative'),a),app(v('cumulative'),b)
    text+=define('eia4',FIELDS+[('first',R),('second',R),('amount',R)],both(k('zm',v('body')),
        op('u',op('e',v('timeunit'),v('quantityunit'))),k('lg',v('lower'),v('upper'),a),k('lg',v('lower'),v('upper'),b),
        k('bc',a,b),k('ba',ca),k('ba',cb),k('ba',v('amount')),k('sca',v('amount'),k('bf',cb,ca)),k('eiri',*args(primitive))))
    inside=both(k('lg',v('lower'),v('upper'),a),k('lg',v('lower'),v('upper'),b),k('bc',a,b))
    text+=define('eia5',FIELDS,both(k('ba',v('lower')),k('ba',v('upper')),k('bg',v('lower'),v('upper')),
        k('la',interval(),v('cumulative')),q('f','first',R,q('f','second',R,op('y',inside,
        k('eia4',*args(FIELDS),a,b,k('bf',cb,ca)))))))
    text+=define('eia6',FIELDS+[('time',R),('rate',R)],both(k('eia5',*args(FIELDS)),
        k('lg',v('lower'),v('upper'),v('time')),k('li',interval(),v('cumulative'),v('time'),v('rate'))))
    text+=define('eia7',ELECTRIC+[('time',R),('rate',R)],k('eia6',*electric_args(),v('time'),v('rate')))
    text+=define('eiba',ELECTRIC+[('current',F)],both(k('eia5',*electric_args()),k('la',interval(),v('current')),
        q('f','time',R,op('y',k('lg',v('lower'),v('upper'),v('time')),
        k('eia7',*args(ELECTRIC),v('time'),app(v('current'),v('time')))))))
    shifted=k('bd',v('time'),v('offset'));one=app(v('firstcurrent'),v('time'));two=app(v('secondcurrent'),shifted)
    text+=define('eibb',SNAP,both(k('eiav',*args(SNAP[:5])),k('lg',v('firstlower'),v('firstupper'),v('time')),
        k('lg',v('secondlower'),v('secondupper'),shifted),k('ba',one),k('ba',two),k('sca',one,two)))
    case=lambda c:[v(c+n) if n in ('frame','context','lower','upper','cumulative') else v(n) for n,_ in ELECTRIC]+[v(c+'current')]
    text+=define('eibc',MATCH,both(k('eiav',*args(SNAP[:5])),k('eiba',*case('first')),k('eiba',*case('second')),
        q('f','time',R,op('y',k('lg',v('firstlower'),v('firstupper'),v('time')),k('eibb',*args(SNAP))))))
    combined=[v('right') if n=='body' else v(n) for n,_ in MATCH]
    text+=define('eibd',MOTION+EXTRA,both(k('eia3',*args(MOTION)),k('eibc',*combined)))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eiri'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];p=added[0]
    basis=dict(status='charge_transport_current_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eiri':dict(parameters=p['parameters'],result=p['result'],arguments=[n for n,_ in FIELDS[:8]]+['first','second','amount'],meaning_ja=PRIMITIVE_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/relative-history-match-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Charge transport and current profiles composed; 207 assertions preserved')
