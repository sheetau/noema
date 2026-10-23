"""Compose the qualified forecast of dispensing with the light ether."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_sufficient_postulates import ROOT,read
from scripts.compose_two_postulates import quote
from scripts.compose_electrodynamics_title import FIELD_TOPIC
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-sufficient-postulates.noema';PARENT_BASIS='data/sufficient-postulates-basis-v1.json'
FULL='examples/v014/einstein-ether-dispensability.noema';CORE='examples/v014/ether-dispensability-core.noema'
BASIS='data/ether-dispensability-basis-v1.json';ANNOTATIONS='data/ether-dispensability-identifiers-v1.json';INDEX=216
V='h[a] '+R;VIEW=[('view','a'),('reference','d')];VIEW_CODE='i[h[a d] c]'
PRIMITIVES={
 'eiscv':([('view','a'),('document','a'),('project','i[e]'),('reference','d')],'viewが、同じdocumentでこれから展開するprojectの理論構成についての見解・概念的な記述規約である。先行の構成課題を同じ内容として参照し、他者の既成理論や現在の読者の見解へ替えない。将来の本文で展開するという位置付けを含み、展開や証明が既に完了したことは要求しない。計画された理論を記述対象とすることと、その物理的真理は別である。'),
 'eiscw':([('view','a'),('concept','a'),('reference','d')],'viewがconceptで指定する対象・概念を、物理的記述や説明のための理論的な構成要素として導入する。語への言及、他説の引用、否定するための参照だけとは区別する。導入の有無はその理論の全規約について与え、未調査を不導入としない。導入すること自体は対象の実在の実証ではなく、不導入はその実在の否定ではない。'),
 'eiscx':([('space','a'),('rest','a'),('reference','d')],'spaceが、restで指定する絶対静止を空間自体の特権的な状態として持つと考える理論的空間の概念である。どの物体や任意の座標系を選ぶかによらない静止の基準を空間へ置くことを意味し、ある系に対する位置不変や座標格子の選択だけとは区別する。その空間の実在やこの見解による導入は別の条件である。'),
 'eiscy':([('view','a'),('space','a'),('property','a'),('reference','d')],'viewがspaceに、普通の位置・幾何学的座標の指定を超えて物理的に特権的な静止を特徴付ける特殊なpropertyを備えさせる。特定の属性名や測定値は原文へ補わない。この属性の帰属を、空間を実際に理論へ導入することやその実在の証明と同一視しない。'),
 'eiscz':([('region','a'),('reference','d')],'regionが、この物理的記述で物質的な伝播媒体を置かない真空の空間範囲である。電磁場や光の存在を排除せず、空間全体や任意の領域を扱い、既に観測した有限部分だけに限定しない。物質媒体が未検出だから真空だと推論する関係ではない。'),
 'eisc2':([('point','a'),('region','a'),('reference','d')],'pointが同じregionに属する空間的位置である。空間点の全範囲に対する関係として与え、物質点、電荷担体、光線や測定済み位置だけへ替えない。点に座標を与えることと、点自体を運動する物理的対象として扱うことを区別する。'),
 'eisc3':([('process','a'),('region','a')]+FIELD_TOPIC[1:],'同じregionにおいてprocessとして電磁的な過程が生じるという記述。閉じたcurrent・electric・magnetic型で同定する電荷輸送、電気側と磁気側の場と物質への作用を共有する物理語彙を使い、場の変化・相互作用・伝播を扱う。全ての過程が三種類の作用を同時に含むとは要求せず、光だけにも限定しない。仮定上の物理的設定を許し、空間内の全点で過程が起きることや実験の実施は加えない。'),
 'eisc4':([('vector','a'),('reference','d')],'vectorが方向と大きさを持つ速度量の記録である。指定された同じ空間基底・基準系・長さと時間の単位による三つの実数成分で、位置の変化率を表す量として解釈する。成分表現はeisc5から取り、共通の既存軸yn/yo/ypへ対応させる。速さという非負スカラー、空間座標、力や場のベクトルと区別する。零ベクトルも速度の指定であり除外しない。点へ実際に付与することは別関係である。'),
 'eisc5':([('vector','a'),('reference','d')],'同じ速度量の記録vectorの、既存の空間軸yn/yo/ypに対応する三実成分を返す表現。基準系・単位・基底と記録の同一性はeisc4の規約に従い、別記録や大きさだけを代入しない。成分の有効性と軸の相違は既存sch2で別に要求する。'),
 'eisc6':([('view','a'),('point','a'),('vector','a'),('reference','d')],'viewが、同じ空間点pointそのものにvectorの速度量を物理的な属性として付与する。空間を運動状態を持つ担い手と扱う帰属であり、その点を通る物体・光・電荷の速度、場の変化率、座標変換で座標値を指定することとは区別する。零速度の付与も含み、物体の速度を許すためにこの帰属を要求しない。'),
 'eisc7':([('alternative','a'),('view','a'),('reference','d')],'alternativeが、この論点におけるviewと同じ物理的な対象範囲・量・予測と説明上の役割を保つ、利用可能な理論的記述の仕方である。別の現象だけを説明する方式や未説明部分の切り捨ては認めない。表記・補助概念を替えることを許し、別個体であることや既に著述されていることは要求しない。どの構成要素を導入するかはeiscwで別に述べる。'),
 'eisda':([('view','a'),('grounds',VIEW_CODE),('conclusion',VIEW_CODE),('reference','d')],'同じviewについて、groundsが示す点・範囲における帰結としてconclusionを理由付けるという限定付きの説明関係。その限りでという範囲を保ち、単なる並置、無限定な全目的への一般化、必要十分条件の同値とは区別する。閉じた両型は同じviewと判断点へ結び、対象や意味を途中で交換しない。ここでの不要性を他の目的での不要性や対象の実在否定へ広げない。'),
 'eisdb':([('view','a'),('claim',VIEW_CODE),('document','a'),('reference','d')],'同じdocumentのこれからの理論展開で、同じviewについてclaimの成立が明らかになると予告する。単なる願望や可能性ではなく、今後の結果への主張として提示する。閉じた型へ同じviewを与えるが、今この時点で実証・導出が完了済みという事実へ替えない。処理系がその予告の物理的真理を証明したことも含意しない。'),
 'eisdc':([], '固定原文einstein-1905:u0004[1082,1425)の第四文。開発予定の見解における二つの不導入・不付与を理由とし、その限りで光エーテル導入の不要が明らかになると予告する箇所。'),
}
MEANINGS={
 'eigm':'同じ速度記録についてeisc4の速度量としての意味と、eisc5の三成分の有効性を結ぶ。sch2を同じベクトルへ二度渡して軸の相違と実数成分を検査し、零速度も除外しない。',
 'eign':'同じ空間範囲に、既存の電荷輸送・電気的作用・磁気的作用の物理語彙で記述される電磁過程がある。過程を空間内の各点へ個別に要求しない。',
 'eigo':'同じviewが、絶対静止を備えた空間概念を導入し、かつそれに特殊な物理的性質を帰属するという組が存在しない。普通の幾何学的空間や相対静止の禁止ではない。',
 'eigp':'電磁過程が生じる真空空間のどの点にも、同じviewで有効な速度ベクトルを付与する組が存在しない。零を含む全速度記録を対象とし、物体や光の速度を否定しない。',
 'eigq':'絶対静止空間の不導入eigoと真空の点への速度不付与eigpを同じ見解・判断点で結ぶ。weder/nochの二つの否定を片方へ縮めない。',
 'eigr':'同じ物理的対象・量・説明を保持する記述の仕方があり、それが先行の光媒体eisbyを理論構成要素として導入しない。光エーテルの導入がこの論点で不要という内容であり、存在しないという主張ではない。',
 'eigs':'同じviewで二つの否定eigqを述べ、その点・範囲を理由として同じ不要性eigrが今後の論説展開で明らかになると予告する。不要性の現在の実証完了は要求しない。',
 'eigt':'前文の同じ理論構成eigjについてこれから展開する見解があり、その同じ見解についてeigsの二否定・限定付き理由・不要性の予告が成立するという第四文の内容。',
 'eigu':'eigtの内容を主張するメッセージ。未来の予告を現在の完成証明や単なる希望へ替えない。',
 'eigv':'第四文のeiguを同じ著者・論説へ帰属し、第三文に続く別箇所として本文順序を保持する。',
}
LIMITS=[
 'Lichtätherは先行のLichtmediumと同じ、光の伝達媒体として仮定される対象eisbyを指すと読む。不要なのは理論への導入であり、その対象の物理的実在の否定や語への言及禁止ではない。',
 'in welchem elektromagnetische Prozesse stattfindenは真空空間を修飾する読みを採る。その空間の点への速度付与を否定し、電磁過程が現に起きる点だけへ対象を狭めない。',
 'absolut ruhender Raumは絶対静止を空間の特権的な状態とする概念と読む。特殊な性質を備えさせて理論へ導入する組を否定し、普通の空間・座標系・物体の相対静止は排除しない。',
 '速度ベクトルは共通の空間基底と単位に対応する三つの実数成分を持つ速度量とし、零も含む。空間点への物理的な付与を否定し、物体・光の速度や座標変換そのものへ否定を広げない。',
 'wird sich ... erweisenは今後の理論展開で成立が明らかになるという予告、zu entwickelnden Auffassungは同じ論説の構成課題をこれから展開する見解と読む。現在の実証や完成を要求しない。',
 'insofern/alsは同じ二否定を理由とする、その点・範囲での不要性として保持する。無限定な不要性や必要十分条件の同値を加えない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+(V if n=='eisc5' else 'a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    vector=k('eisc5',v('vector'),v('reference'))
    text+=define('eigm',[('vector','a'),('reference','d')],both(k('eisc4',v('vector'),v('reference')),k('sch2',vector,vector)))
    text+=define('eign',[('region','a'),('reference','d')],q('g','process','a',k('eisc3',v('process'),v('region'),'r[p eibf]','r[p eibs]','r[p eico]',v('reference'))))
    absolute=both(k('eiscx',v('space'),k('eisbk'),v('reference')),k('eiscw',v('view'),v('space'),v('reference')),k('eiscy',v('view'),v('space'),v('property'),v('reference')))
    text+=define('eigo',VIEW,op('u',q('g','space','a',q('g','property','a',absolute))))
    assigned=both(k('eiscz',v('region'),v('reference')),k('eisc2',v('point'),v('region'),v('reference')),k('eign',v('region'),v('reference')),k('eigm',v('vector'),v('reference')),k('eisc6',v('view'),v('point'),v('vector'),v('reference')))
    for name in ('vector','point','region'):assigned=q('g',name,'a',assigned)
    text+=define('eigp',VIEW,op('u',assigned))
    text+=define('eigq',VIEW,both(k('eigo',v('view'),v('reference')),k('eigp',v('view'),v('reference'))))
    text+=define('eigr',VIEW,q('g','alternative','a',both(k('eisc7',v('alternative'),v('view'),v('reference')),op('u',k('eiscw',v('alternative'),k('eisby'),v('reference'))))))
    text+=define('eigs',VIEW,both(k('eigq',v('view'),v('reference')),k('eisdb',v('view'),'r[p eigr]',k('eirf'),v('reference')),k('eisda',v('view'),'r[p eigq]','r[p eigr]',v('reference'))))
    text+=content('eigt',q('g','view','a',both(k('eiscv',v('view'),k('eirf'),quote('eigj'),v('point')),k('eigs',v('view'),v('point')))))
    text+='d eigu[] f[j s[k eigt[]]].\n'
    text+=define('eigv',[],both(k('eir3',k('eisdc'),k('rd'),k('eirf'),quote('eigu'),k('ri')),k('ue',k('eiscu'),k('eisdc'),k('ri')),op('u',op('e',k('eiscu'),k('eisdc')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eigv',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='qualified_forecast_of_light_ether_dispensability',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/sufficient-postulates-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
