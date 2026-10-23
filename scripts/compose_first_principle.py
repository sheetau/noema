"""Compose common physical laws over uniformly translating coordinate frames."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_second_section_opening import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-second-section-opening.noema';PARENT_BASIS='data/second-section-opening-basis-v1.json'
FULL='examples/v014/einstein-first-principle.noema';CORE='examples/v014/first-principle-core.noema'
BASIS='data/first-principle-basis-v1.json';ANNOTATIONS='data/first-principle-identifiers-v1.json';INDEX=249
PAIR=[('first','a'),('second','a'),('context','d')]
FRAME=[('first','a'),('second','a'),('lengthunit','a'),('timeunit','a'),('context','d')]
PRIMITIVES={
 'eisk6':(FRAME, '同じ物理的座標系firstとsecondについて、firstの空間配置を原点と正規直交した三軸yn/yo/yp及び静止した長さ尺度で表し、その系に静止する時計の同期・共通参照・校正で時刻を付与する記述規約。lengthunitとtimeunitはその尺度である。secondの原点・軸・格子・計器の設置位置を同じfirstの座標と時刻で記述し、軸の単なる名札や別の系の時計読みを混ぜない。第二系の全配置点や全時点の範囲、値の存在、運動の種類は別に要求する。'),
 'eisk7':([('frame','a'),('point','a'),('context','d')], 'frameに固定された原点・三軸・座標格子と計器の設置配置を担う点pointの全範囲。時刻を変えても同じ配置位置を追跡し、各時刻で一致する別物への交換をしない。三次元の配置を決める非共線の方向を含む。時計内部の針や歯車の運動まで静止させる条件ではない。'),
 'eisla':([('first','a'),('second','a'),('moment','a'),('context','d')], 'firstに対するsecondの運動を比較する時間幅を持つ区間の全時点の範囲。firstの同じ時刻規約で数値化され、端点だけ・測定済み標本だけ・等速に見える時点だけへの抜粋を許さない。時点を表す複数の記録が同じ時刻を持つことは許し、値の妥当性と時間幅は別に要求する。'),
 'eislb':(FRAME, 'この二系・尺度・文脈の運動記述で、eisk7がsecondの全固定配置を、eislaが比較区間の全時点を尽くし、ym/ylが同じfirstの尺度でその配置と時刻を対応させるという範囲と対応の完全性。軸向きの異なる点や途中の加速時点を省かず、未知の範囲を完全と扱わない。値の利用可能性、等速性、法則の成立は含意しない。'),
 'eislc':([('first','a'),('second','a'),('lengthunit','a'),('timeunit','a'),('axis','a'),('context','d')], '同じfirstに対するsecondの全配置点・全時点に共通に試す速度ベクトルのaxis成分。数値はlengthunit/timeunitで表し、点又は時点を引数に取って速度を選び直さない。正・負・零を許す候補値であり、一定速度の成立は変位条件で別に要求する。'),
 'eisld':([('system','a'),('context','d')], '同じ文脈で状態とその変化を物理的に記述する系。物質の構成部分や場と、それらの位置・運動・電気量・場の値などの物理量及び相互作用の対象を同定し、どの範囲を一つの系として追うかを固定する。剛体や単一粒子、電気力学だけに限らず、力学・場・光を含む。系の孤立、平衡、状態の不変、特定法則への適合は要求しない。'),
 'eisle':([('theory','a'),('law','a'),('context','d')], '同じtheoryで物理系の状態変化を支配する一般的な物理量の関係と適用条件を持つ法則lawの全範囲。量・単位・対象の対応を固定した同じ内容を各座標系へ適用し、系ごとに別の法則へ交換しない。電気力学又は光学だけ、成功した法則だけ、式の字面の一致だけに限定しない。各系での法則としての成立はeisbi、候補記述の適合はviで別に与える。'),
 'eislf':([('theory','a'),('history','a'),('context','d')], '同じtheoryの各法則の許容・不許容を比較すべき、物理系の状態とその変化を追う全候補履歴。対象となる系、同じ構成部分・場・物理量と出来事の対応を保つ。実際に生じた履歴又は法則に適合する履歴だけへ縮めず、変化しない退化例も候補に含む。vfが同じ系へ結び、vhが同じ履歴の各座標系での記述へ結ぶ。'),
 'eislg':([('theory','a'),('context','d')], 'この原理で比較するtheoryの全物理法則をeisle、全物理的候補履歴をeislf、各適格系における同じ履歴の全対応記述をvhが尽くすという範囲の完全性。許容・不許容両方の候補を対象にし、不一致例や一方で記述が欠ける例を外して保存を成立させない。全法則を有限列挙できたという認定でも、法則の真理の代用でもない。'),
 'eislh':([('node','a'),('author','a'),('designation','a'),('antecedent','i[e]'),('formulation','i[e]'),('document','a'),('context','d')], 'authorがnodeのformulationを、同じdocumentでdesignationにより先にantecedentとして指した原理の定式化として提示する。原理の指示を保つ談話上の対応であり、二つの閉じた式の構文一致又は論理的同値を処理系が証明したことではない。範囲の異なる二表現の差を隠さず、定式化の具体的内容は別に保持する。'),
 'eisli':(PAIR, 'この二系の比較に用いるfirstの長さ尺度への参照。同じ組・文脈で固定し、secondの別尺度や時間単位と混ぜない。'),
 'eislj':(PAIR, 'この二系の比較に用いるfirstの共通時間尺度への参照。同じ組・文脈で固定し、secondの時計読みそのものをfirstの時刻へ無条件に置き換えない。'),
 'eislk':([('node','a'),('intro','a'),('ordinal','b'),('document','a'),('context','d')], '同じdocumentでintroが導入した番号付き列挙のordinal番目としてnodeを提示する。表示番号を位置・順序へ結び、番号を物理量や対象個数にしない。導入末尾の句読点がコロンであることは要求しない。'),
}
RESULTS={'eislc':R,'eisli':'a','eislj':'a'}
MEANINGS={
 'eioh':'五つの有効な実数表現について、同じ成分の変位が一定速度候補と経過時間の積に等しい。速度の符号・零、時刻と位置の原点を限定しない。',
 'eioi':'同じ二系・尺度・時点対・配置点の三座標を、一つの共通速度ベクトルの各成分へeiohで接続する。異なる点・時点の速度を許さない。',
 'eioj':'正しい同じ系と尺度の記述、全配置点・全時点の範囲、全点時点の座標と時刻の利用可能性を要求し、非空の配置と時間幅のある全時点対へ同じ三成分の等速変位を課す。固定配置全体の同一変位で非回転の並進を表す。',
 'eiok':'二系に固定した長さ・時間単位をeiojへ渡す、相対的に等速並進する異なる二座標系の条件。零速度を退化例として許し、軸の一致や特定の速度方向を要求しない。',
 'eiol':'候補履歴が、状態と物理量を持つ同じ物理系eisldへ既存vfで結ばれる。実際の変化や法則適合を別途要求しない。',
 'eiom':'完全な全法則・全候補範囲の下で、各候補が物理系へ結ばれ、全法則が両系で成り立ち、同じ法則への適合が全履歴の全対応記述対で一致する。非空性と両側の記述存在は既存sar/saq/sapを再利用する。',
 'eion':'等速並進する系対があり、同じ一つの物理法則体系について、その全適格系対でeiomが成立するという第一原理の定式化内容。座標値の一致や全候補の適合ではない。',
 'eioo':'同じ著者がvkでeionを後続範囲wvの原理定義として提示し、先に呼称で指した相対性原理eifjの定式化へ結ぶ。引用から物理的真理やeifjとの論理同値を導かない。',
 'eiop':'第一原理をこの内容で定義するeiooを述べるメッセージ。処理系自身による法則の実証宣言にしない。',
 'eioq':'第一原理の定義を同じ著者・論説へ帰属し、導入wuの番号付き列挙の1番目と本文順序を保持する。',
}
LIMITS=[
 'u0025の全255文字・226本文文字を原刊895頁に照合する。番号1、物理系の状態変化、その法則、二座標系の相対的な等速並進、どちらへ関係づけるかへの独立性を全て保持する。',
 '法則の同じ内容が両系で成立することと、同じ履歴の全対応記述の適合が保存されることを合わせた読みを採る。現実の履歴だけの一致、全履歴が法則に従う条件、座標値・式の字面の一致へ替えない。物理法則の内容と範囲の充足は明示した物理的入力である。',
 '等速並進は、一方の系に固定した全配置点が、他方の系の全比較時点対で、同じ一定速度ベクトルによる変位を持つこととして構成する。全配置と全時点への対応の完全性を要求する。軸が一致する必要はなく、方向・速度の符号を限定しない。零速度を退化例として許す。',
 'この運動条件は一方の系から見た配置の履歴であり、二系の時刻を同一にするGalilei変換や、未導出のLorentz変換を仮定しない。加速中の剛性、運動前後の棒の長さ、時計の進みの同一性は補わない。',
 'eifjは先の電気力学・光学の法則と絶対静止の特性否定を含む推測内容である。u0025は物理系の状態変化一般の法則を定式化する。原理の指示の連続性をeislhで保持し、異なる量化範囲の二式の論理的同値を主張しない。',
 '原理の定義提示は既存vlを用い、番号1と導入からの順序を別に保持する。句読点を固定した旧eiskjをこの列挙へ無条件に使わず、句読点に依存しない番号付き列挙eislkを使う。',
 '有限例では数値核・全配置の結合・履歴同一性・法則成立・適合保存・提示を分けて検査する。全連続時間・全実数・全物理法則の真理や原文との意味同値を有限標本から証明しない。u0026以降は残る。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+RESULTS.get(n,'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fs=[(n,R) for n in ('speed','start','end','initial','final')]
    text+=define('eioh',fs,both(*(k('ba',v(n)) for n,_ in fs),k('sca',k('bf',v('final'),v('initial')),k('shv',v('speed'),k('bf',v('end'),v('start'))))))
    pointfields=FRAME+[('point','a'),('start','a'),('end','a')]
    coords=lambda axis,m:k('ym',v('point'),v(m),v('first'),v('lengthunit'),k(axis),v('context'))
    moment=lambda m:k('yl',v(m),v('first'),v('timeunit'),v('context'))
    text+=define('eioi',pointfields,both(*(k('eioh',k('eislc',*[v(n) for n in ('first','second','lengthunit','timeunit')],k(axis),v('context')),moment('start'),moment('end'),coords(axis,'start'),coords(axis,'end')) for axis in ('yn','yo','yp'))))
    points=lambda x:k('eisk7',v('second'),x,v('context'))
    moments=lambda x:k('eisla',v('first'),v('second'),x,v('context'))
    available=both(k('zce',v('point'),v('moment'),v('first'),v('lengthunit'),v('context')),k('zcf',v('moment'),v('first'),v('timeunit'),v('context')))
    coverage=q('f','point','a',q('f','moment','a',op('y',both(points(v('point')),moments(v('moment'))),available)))
    numeric=k('sbn','i[point a]['+points(v('point'))+']','i[moment a]['+moments(v('moment'))+']','i[start a end a]['+k('bg',moment('start'),moment('end'))+']','i[point a start a end a]['+k('eioi',*[v(n) for n,_ in pointfields])+']')
    text+=define('eioj',FRAME,both(k('va',v('first')),k('va',v('second')),op('u',op('e',v('first'),v('second'))),op('u',op('e',v('lengthunit'),v('timeunit'))),k('ti',v('lengthunit')),k('ci',v('timeunit')),*(op('u',op('e',k(a),k(b))) for a,b in (('yn','yo'),('yn','yp'),('yo','yp'))),k('eisk6',*[v(n) for n,_ in FRAME]),k('eislb',*[v(n) for n,_ in FRAME]),coverage,numeric))
    text+=define('eiok',PAIR,k('eioj',v('first'),v('second'),k('eisli',*[v(n) for n,_ in PAIR]),k('eislj',*[v(n) for n,_ in PAIR]),v('context')))
    text+=define('eiol',[('history','a'),('context','d')],q('g','system','a',both(k('eisld',v('system'),v('context')),k('vf',v('history'),v('system'),v('context')))))
    law=lambda x:k('eisle',v('theory'),x,v('context'))
    history=lambda x:k('eislf',v('theory'),x,v('context'))
    saved=k('sar',v('first'),v('second'),'i[law a]['+law(v('law'))+']','i[history a]['+history(v('history'))+']','i[history a frame a representation a]['+k('vh',v('history'),v('frame'),v('representation'),v('context'))+']','i[law a representation a]['+k('vi',v('law'),v('representation'),v('context'))+']')
    text+=define('eiom',[('first','a'),('second','a'),('theory','a'),('context','d')],both(k('eislg',v('theory'),v('context')),q('f','history','a',op('y',history(v('history')),k('eiol',v('history'),v('context')))),q('f','law','a',op('y',law(v('law')),both(k('eisbi',v('law'),v('first'),v('context')),k('eisbi',v('law'),v('second'),v('context'))))),saved))
    eligible=k('eiok',v('first'),v('second'),v('point'))
    exists=q('g','first','a',q('g','second','a',eligible))
    allpairs=q('f','first','a',q('f','second','a',op('y',eligible,k('eiom',v('first'),v('second'),v('theory'),v('point')))))
    text+=content('eion',both(exists,q('g','theory','a',allpairs)))
    text+=content('eioo',both(k('vl',k('vk'),k('rd'),quote('eion'),k('wv'),v('point')),k('eislh',k('vk'),k('rd'),k('eisk3'),quote('eifj'),quote('eion'),k('eirf'),v('point'))))
    text+='d eiop[] f[j s[k eioo[]]].\n'
    text+=define('eioq',[],both(k('eir3',k('vk'),k('rd'),k('eirf'),quote('eiop'),k('ri')),k('eislk',k('vk'),k('wu'),'n p b b',k('eirf'),k('ri')),k('ue',k('wu'),k('vk'),k('ri')),op('u',op('e',k('wu'),k('vk')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eioq',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='first_principle_with_uniform_frame_motion_and_all_physical_laws',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/second-section-opening-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
