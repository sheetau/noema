"""Connect an independent carrier worldline to a material host and force event."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_material_relative_frame import ROOT,read,R,FAMILY,HISTORY,FRAME,AXES,define,args
from scripts.compose_electric_action import FIELDS as ELECTRIC
from scripts.compose_field_equations import ROLES
from scripts.compose_limits import v,call as k,app,op,both,quant as q,ZERO

PARENT='examples/v014/einstein-electric-action.noema'
PARENT_BASIS='data/electric-action-basis-v1.json'
FULL='examples/v014/einstein-carrier-relative-motion.noema'
CORE='examples/v014/carrier-relative-motion-core.noema'
BASIS='data/carrier-relative-motion-basis-v1.json'
ANNOTATIONS='data/carrier-relative-motion-identifiers-v1.json'
FIELDS=HISTORY+[('carrier','a')]+[('carrier'+a,FAMILY) for a in AXES]
INSTANT=FIELDS+[('time',R)]
WITNESS=FIELDS+[('first',R),('second',R)]
ACTION=WITNESS+[(n,t) for n,t in ELECTRIC if n not in ('carrier','frame','context')]+[('actiontime',R)]
OCCUPANCY=[('body','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a')]+[(n,R) for n in ('x','y','z','time')]
MEANINGS={
 'eibt':'同じ系・文脈・長さと時間の単位・閉区間で、物体の剛な参照履歴eiaqと、別の点状担体の完全な軌跡seを結ぶ。担体を参照物体の物質点集合へ追加しない。carrierx/y/zのうち同じcarrierの枝だけを担体の軌跡として使う。担体の電荷や物体内部への所在は別条件である。',
 'eibu':'eibtの下で、区間内の指定時刻における同じ担体の有効な三座標が、eiroの同じ物体の物質領域に属する。物体と共に移動すること、構成点であること、電荷を持つことのいずれも所在だけから導かない。',
 'eibv':'eibtを満たし、閉区間の全実時刻にeibuが成立する担体の物体内履歴。両端だけが内部で途中に外へ出る軌跡を許さない。物体全体に対する担体の所属や永続的な閉じ込めではなく、指定区間の所在である。',
 'eibw':'eibvの下で、区間内の前後二時刻に同じ担体の物体付随軸での位置が異なるという相対移動の証人。物体と担体の共通並進・共通回転だけでは成立せず、剛な参照物体の構成点と担体を混同しない。往復運動では両端以外の証人を選べる。',
 'eibx':'eibwの相対移動と、同じ担体・系・文脈へのeibsの電気的作用を結ぶ。作用時刻は履歴区間内で、同じ出来事がsbにより担体軌跡に属し、場評価用の四座標もその三座標と時刻へ等置する。その出来事の電荷は非零とするが、電荷の時間不変や力の非零を追加しない。作用が移動を引き起こしたこと、巨視的電流、導電性をこれだけで主張しない。',
}
OCCUPANCY_MEANING='指定の系・文脈と長さ・時間単位による三座標と時刻が、その物体の物質のある領域に属する。物体を記述する尺度で占有を判断し、物質がある表面も含む。穴や外側の空間を単なる外接領域によって含めない。これは時刻ごとの物理的な位置割当であり、座標値の妥当性や担体の軌跡、剛体の物質点集合への所属とは別である。量化して全区間を述べる場合も観測標本だけで成立を認定しない。'
LIMITS=[
 '導入の導体内の移動に必要な位置・軌跡・作用の接続である。原文207主張と著者表示の判断を保持し、導体の語義や導入段落全体の完成とは数えない。',
 '参照物体は既存eiaqの剛な配置と非共線三標識点を持つという解釈に限る。担体はその尺度で点状に扱える対象であり、原文へ電子の種類・微視的散乱機構を追加しない。',
 'eiroは物質領域の基礎的な所在規約である。既存zkは位置個体で表され、数値座標への接続がないため転用しない。物体領域の数値形状を有限の標本から完全同定したという規約ではない。',
 '電荷は作用出来事で非零であり、履歴の全時刻で一定とは主張しない。移動と電気的作用の併存は因果関係や電流の正味通過量を含意しない。許容試行、電流、応答時間・強度・材料保持条件との接続を残す。',
 '有限検査は有理数座標と明示した全履歴境界の接続を検査する。全実時刻の所在・軌跡を有限評価器へ渡した場合は拒否し、標本検査で代用しない。',
]

def xyz(time):return [app(app(v('carrier'+a),v('carrier')),time) for a in AXES]

def definitions():
    text='r eiro['+' '.join(t for _,t in OCCUPANCY)+'] c.\n'
    text+=define('eibt',FIELDS,both(op('u',op('e',v('body'),v('carrier'))),
        app(k('zrdpointlike'),v('carrier'),v('context')),k('eiaq',*args(HISTORY)),
        k('se',v('carrier'),*[v(n) for n in ('frame','context','lengthunit','timeunit','lower','upper')],
          *(app(v('carrier'+a),v('carrier')) for a in AXES))))
    time=v('time');inside=lambda t:k('lg',v('lower'),v('upper'),t)
    text+=define('eibu',INSTANT,both(k('eibt',*args(FIELDS)),inside(time),*(k('ba',x) for x in xyz(time)),
        k('eiro',*[v(n) for n in ('body','frame','context','lengthunit','timeunit')],*xyz(time),time)))
    text+=define('eibv',FIELDS,both(k('eibt',*args(FIELDS)),q('f','time',R,op('y',inside(time),k('eibu',*args(INSTANT))))))
    projected=[k(n,v('origin'),*(v(a) for a in AXES),*(v('carrier'+a) for a in AXES),*args(FRAME)) for n in ('eian','eiao','eiap')]
    text+=define('eibw',WITNESS,both(k('eibv',*args(FIELDS)),inside(v('first')),inside(v('second')),
        k('zzbg',v('first'),v('second')),k('eiae',v('carrier'),v('first'),v('second'),*projected)))
    t=v('actiontime');coordinates=xyz(t)+[t]
    text+=define('eibx',ACTION,both(k('eibw',*args(WITNESS)),inside(t),k('eibs',*args(ELECTRIC)),
        op('x',k('bg',v('charge'),k('bb',ZERO)),k('bg',k('bb',ZERO),v('charge'))),
        k('sb',*[v(n) for n in ('carrier','event','frame','context','lengthunit','timeunit')],t,*xyz(t)),
        *(k('sca',app(v('point'),k(role)),value) for role,value in zip(ROLES,coordinates))))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|{'eiro'})&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):];primitive=next(d for d in added if d['name']=='eiro')
    basis=dict(status='carrier_relative_motion_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'eiro':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=[n for n,_ in OCCUPANCY],meaning_ja=OCCUPANCY_MEANING)},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electric-action-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Carrier relative motion and electric event composed')
