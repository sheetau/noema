"""Compose one shared synchronization realization for arbitrarily large finite families."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_roundtrip_definition import ROOT,read,SYNC
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-light-roundtrip-definition.noema';PARENT_BASIS='data/light-roundtrip-definition-basis-v1.json'
FULL='examples/v014/einstein-consistent-synchrony.noema';CORE='examples/v014/consistent-synchrony-core.noema'
BASIS='data/consistent-synchrony-basis-v1.json';ANNOTATIONS='data/consistent-synchrony-identifiers-v1.json';INDEX=240
RULE='i[h['+' '.join(t for _,t in SYNC)+'] c]'
FAMILY=[('points','j[a]')]+[(n,'a') for n in ('frame','unit','document')]+[('reference','d')]
PAIR=[(n,'a') for n in ('configuration','left','right','frame','unit','document')]+[('result','d')]
PRIMITIVES={
 'eisjv':([('point','a'),('frame','a'),('reference','d')],'同じ静止基準系で同期する時計の設置を考える空間点の全範囲にpointが属する。成功した配置だけや既に時計のある二・三点へ絞らず、同じ議論の任意の地点を対象とする。点の未知を範囲外へ補わない。'),
 'eisjw':(FAMILY+[('configuration','a'),('result','d')],'referenceから、指定したpoints・frame・unitの同じ同期定義を実現するために検討する配置候補configurationとその評価状況result。時計の校正・初期指示の調整を含む候補を扱い、成功する候補だけを選別しない。元の地点・系・単位・定義の意味を保持し、整合性と全条件の成立は合成側で別に要求する。'),
 'eisjx':([('configuration','a'),('point','a')],'同じconfigurationでpointに割り当てる時計。全地点でこの一つの配置写像を共有し、比較相手ごとに時計を交換しない。割当て先が有効な静止時計で同じ点にあることと、異なる地点で同じ時計を共用しないことは別に検査する。'),
 'eisjy':([(n,'a') for n in ('configuration','clock','event','frame','unit')]+[('result','d')],'同じconfigurationの同じclockが同じeventに与える指示値の候補。系・単位・評価状況を固定した一つの履歴として共有し、試行や比較する時計対の違いを追加の引数にして値を変更しない。実数条件・許容される時計履歴・同期式は別に要求する。未知の値を零で埋めない。'),
 'eisjz':([(n,'a') for n in ('configuration','clock','frame','unit')]+[('history','h[a] '+R),('result','d')],'historyは同じconfigurationのclockに許容される一つの指示履歴である。各出来事への値を同じ校正・時計の作動に沿って割り当て、局所的な時刻付与を保つ。個々の値だけを別々の許容履歴から拾い集めない。これは一時計の履歴の許容性であり、他時計との同期・全配置の無矛盾性を認める入力ではない。全履歴の未知を許容済みとしない。'),
 'eiska':(PAIR+[('trial','a')],'同じconfiguration・二地点・系・単位・resultで、同期条件を課す必要のある光往復試行trialの全範囲。実際に一回測定した標本だけでなく必要な理想試行を含め、成功した試行だけを選別しない。非空性・同じ光の設定・時刻の等式は別に要求する。'),
 'eiskb':([('node','a'),('author','a'),('priornode','a'),('rule',RULE),('document','a'),('context','d')],'nodeの「この同期の定義」は、priornodeで採用した同じruleを指す。新しい無関係な同期概念や二法則だけへ置き換えず、その定義を任意個数へ適用する仮定の対象とする言説参照。引用から定義の実現済みを導かない。'),
 'eiskc':([], '固定einstein-1905:u0015の仮定導入箇所。任意個数で同期を矛盾なく定義できることと、一般に続く二関係が成り立つことを仮定する。'),
 'eiskd':([], '固定einstein-1905:u0016の第一の関係法則の箇所。BがAと同期するときAがBと同期する条件を述べる。'),
 'eiske':([], '固定einstein-1905:u0017の第二の関係法則の箇所。AがBおよびCと同期するときBとCが互いに同期する条件を述べる。'),
 'eiskf':([('node','a'),('author','a'),('firstnode','a'),('secondnode','a'),('firstlaw','i[e]'),('secondlaw','i[e]'),('document','a'),('context','d')],'同じnodeがコロンの後で列挙する二関係を、firstnodeのfirstlawとsecondnodeのsecondlawへ順序付きで予告する。一般性を各法則の量化へ結び、別の法則・既に証明済みの結論へ替えない。'),
}
MEANINGS={
 'eimt':'同じ系で考える点の非空・重複のない有限列。shmとsxbを再利用して全出現を確認し、列長の上限を置かない。',
 'eimu':'同じ配置が指定点へ割り当てる静止時計と単位、その配置に一つに固定した全指示履歴の局所的許容性を結ぶ。',
 'eimv':'同じ配置の異なる二地点に関する一光往復について、全物理的役割・正確な時計構成・同じ時計履歴による三読み・等時間式を結ぶ。値を比較時計対ごとに選び直さない。',
 'eimw':'同一点では同じ有効時計の自己同期、異なる二点では非空の全必要試行にeimvを要求する。その配置における前の同期条件の実現である。',
 'eimx':'同じ有限点列の全点・全点対に、一つの配置写像・一つの評価状況・各時計の一つの指示履歴を共有してeimwを要求する。異なる地点には異なる時計を割り当てる。',
 'eimy':'同じ点列について、検討する配置候補と評価状況が存在し、その同じ組で全地点を一緒に扱うeimxを満たす。点対ごとの別候補の存在ではない。',
 'eimz':'上限を設けない全有限点列について、適格な非空・重複なしの配置ならeimyの共有された実現が可能であるという一般内容。全有限列の量化を固定した有限標本へ置き換えない。',
 'eim2':'同じ静止系ra・単位rb・論説で、任意個数の地点への同期定義の無矛盾な実現可能性eimzを述べる内容。',
 'eim3':'任意個数での共有実現可能性と、既存qp/qqの一般関係法則を同じ点で結び、alsoの説明理由を前者から二法則へ向ける、仮定の対象。',
 'eim4':'著者が同じ論説でeim3を仮定として採用する行為の内容。引用した物理的実現可能性を実証済みとしない。',
 'eim5':'仮定採用eim4を述べる主張メッセージ。全配置が現実に同期済みという命題へ替えない。',
 'eim6':'同じ著者・論説への帰属、直前の同期定義への参照、コロン後の二法則への前方参照、本文順序を保持する。',
}
LIMITS=[
 'beliebig viele Punkteを、個数の上限を置かない任意の有限個の地点として読む。二・三点の検査例への限定ではなく、全有限列に量化する。無限個の時計を一度に実現する強い主張までは補わない。この読みの限界を明示する。',
 'widerspruchsfreier Weise möglichは、一つの配置と一つの評価状況で全点対の条件を同時に満たせるという読み。時計ごとの指示履歴を共有し、同じ時計・出来事の値を点対ごとに変えて見かけ上整合させない。候補の存在と各候補の成功を分ける。',
 '配置の許容候補と各時計の許容指示履歴は物理的意味規約付きの入力である。全時計対の等時間式を満たすかは合成で別に確認する。原文はその実現可能性を仮定しており、ここで物理的な存在定理を証明したとはしない。',
 '同一点の自己同期は既存qoと同じ規約で扱い、異なる地点の同期は既存eimkの光往復条件と同じ物理的役割・式を、同じ候補配置の指示履歴へ適用する。候補値を現在の実測値ceへ混ぜず、各履歴の許容性を別に要求する。',
 '一般関係は既存qp/qqを再利用する。これらの対称性と三時計条件だけでは任意個数での実現可能性を保証しないので、追加した共有実現可能性と分ける。alsoは著者が結ぶ説明の向きとして保持し、検査器が導出を証明したことにしない。',
 'Wir nehmen anは著者の仮定採用である。現在の物理的な真理や実証へ変えない。diese Definitionは直前のeimkへの参照、コロンはu0016/u0017の同じ二法則への予告として保持する。',
 'u0015全149非空白本文文字を対象とする。u0016・u0017の場所記号と列挙の提示の接続・通読判断は次に残る。',
]

def args(fs):return [v(n) for n,_ in fs]
def lam(n,t,b):return 'i['+n+' '+t+']['+b+']'
def clock(p):return k('eisjx',v('configuration'),p)
def reading(c,e):return k('eisjy',v('configuration'),c,e,v('frame'),v('unit'),v('result'))


def definitions():
    text=''
    for n,(fs,_) in PRIMITIVES.items():
        result=R if n=='eisjy' else 'a' if not fs or n=='eisjx' else 'c'
        text+='r '+n+'['+' '.join(t for _,t in fs)+'] '+result+'.\n'
    text+=define('eimt',[('points','j[a]'),('frame','a'),('reference','d')],both(k('shm',v('points')),k('sxb',v('points'),lam('point','a',k('eisjv',v('point'),v('frame'),v('reference'))))))
    local=[(n,'a') for n in ('configuration','point','frame','unit')]+[('result','d')];c=clock(v('point'))
    text+=define('eimu',local,both(k('ca',c),k('cc',c,v('frame')),k('cb',c,v('point'),v('frame')),k('ci',v('unit')),k('eisjz',v('configuration'),c,v('frame'),v('unit'),lam('event','a',reading(c,v('event'))),v('result'))))
    a,b=clock(v('left')),clock(v('right'));trial=v('trial');depart,reflect,arrive,ray=[k(n,trial) for n in ('qe','qf','qg','qh')]
    first,middle,last=reading(a,depart),reading(b,reflect),reading(a,arrive)
    physical=both(op('u',op('e',v('left'),v('right'))),op('u',op('e',a,b)),op('u',op('e',depart,arrive)),op('e',k('qc',trial),v('left')),op('e',k('qd',trial),v('right')),*[k('eimu',v('configuration'),v(p),v('frame'),v('unit'),v('result')) for p in ('left','right')],*[k('zbd',e) for e in (depart,reflect,arrive)],k('cb',depart,v('left'),v('frame')),k('cb',reflect,v('right'),v('frame')),k('cb',arrive,v('left'),v('frame')),k('cf',ray),k('cg',ray,depart,reflect,v('frame')),k('cg',ray,reflect,arrive,v('frame')),k('ch',ray,reflect,v('frame')),k('cd',a,b),k('eild',b,a,v('document'),v('result')),k('eimi',first,middle,last))
    text+=define('eimv',PAIR+[('trial','a')],physical)
    scope=k('eiska',*args(PAIR),trial)
    alltrials=both(q('g','trial','a',scope),q('f','trial','a',op('y',scope,k('eimv',*args(PAIR),trial))))
    text+=define('eimw',PAIR,op('x',both(op('e',v('left'),v('right')),k('eimu',v('configuration'),v('left'),v('frame'),v('unit'),v('result'))),both(op('u',op('e',v('left'),v('right'))),alltrials)))
    fs=FAMILY+[('configuration','a'),('result','d')]
    pairbody=both(op('y',op('u',op('e',v('left'),v('right'))),op('u',op('e',clock(v('left')),clock(v('right'))))),k('eimw',*args(PAIR)))
    text+=define('eimx',fs,both(k('eimt',v('points'),v('frame'),v('reference')),k('sxb',v('points'),lam('left','a',k('sxb',v('points'),lam('right','a',pairbody))))))
    text+=define('eimy',FAMILY,q('g','configuration','a',q('g','result','d',both(k('eisjw',*args(fs)),k('eimx',*args(fs))))))
    text+=define('eimz',FAMILY[1:],q('f','points','j[a]',op('y',k('eimt',v('points'),v('frame'),v('reference')),k('eimy',*args(FAMILY)))))
    text+=content('eim2',k('eimz',k('ra'),k('rb'),k('eirf'),v('point')))
    ev=lambda n:'t[k '+n+'[]][v point]'
    text+=content('eim3',both(ev('eim2'),ev('qr'),k('eisdk',k('eirf'),quote('eim2'),quote('qr'),v('point'))))
    text+=content('eim4',k('ug',k('eiskc'),k('rd'),quote('eim3'),k('eirf'),v('point')))
    text+='d eim5[] f[j s[k eim4[]]].\n'
    text+=define('eim6',[],both(k('eir3',k('eiskc'),k('rd'),k('eirf'),quote('eim5'),k('ri')),k('eiskb',k('eiskc'),k('rd'),k('eisjs'),'r[p eimk]',k('eirf'),k('ri')),k('eiskf',k('eiskc'),k('rd'),k('eiskd'),k('eiske'),quote('qp'),quote('qq'),k('eirf'),k('ri')),k('ue',k('eisjs'),k('eiskc'),k('ri')),k('ue',k('eiskc'),k('eiskd'),k('ri')),k('ue',k('eiskd'),k('eiske'),k('ri')),op('u',op('e',k('eiskc'),k('eisjs')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eim6',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='assumed_consistent_synchrony_for_unbounded_finite_point_families',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/light-roundtrip-definition-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
