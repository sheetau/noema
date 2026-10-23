"""Connect the displayed roundtrip rate and empirical universal-constant adoption."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_event_time_summary import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-event-time-summary.noema';PARENT_BASIS='data/event-time-summary-basis-v1.json'
FULL='examples/v014/einstein-empirical-light-constant.noema';CORE='examples/v014/empirical-light-constant-core.noema'
BASIS='data/empirical-light-constant-basis-v1.json';ANNOTATIONS='data/empirical-light-constant-identifiers-v1.json';INDEX=245
SCOPE=[(n,'a') for n in ('frame','timeunit','lengthunit','document')]+[('context','d')]
PRIMITIVES={
 'eiskr':([('trial','a')]+SCOPE, '同じdocumentでframeの真空中の光往復について普遍的な値を定める際の、全ての適用対象となる試行trialの範囲。二地点の位置・方向・正の距離・出発時刻を変えた、同じ時間単位・長さ単位で比較する理想的な往復も含む。既観測、同じ速度を返す成功例、固定された一距離や一方向だけを選ばない。具体的な距離・真空中の両区間・同じ出発時計の読み・単位整合と速度式の成立は別に検査する。基準系を勝手に他系へ替えず、有限検査の二試行を全物理的範囲と認定しない。範囲の未知を空集合にしない。'),
}
MEANINGS={
 'einq':'既存tdが選ぶ速度測定試行を、同じ系・時間単位・長さ単位・論説・状況の全適用範囲eiskrと一致させる。都合のよい部分範囲や異なる文脈の混入を認めない。',
 'einr':'全適用範囲への対応einqと、既存sanによる非空・完全な全試行で一つの同じ実数値tcを持つ速度法則を合わせる。位置・方向・距離・出発時刻ごとに値を選び直さない。',
 'eins':'M0040のA/Bの固定された代表往復を、同じ二時計・二地点・出発反射帰着・光・出発帰着の指示へ結び、距離tgと共通速度tcについてsal/saiの式を示す。分母はA時計の帰着値から出発値を引き、反射時計の値を引かない。',
 'eint':'著者がtmで、全適用試行に共通の速度法則einrを議論へ採用し、その採用を経験的根拠tnに従うものと位置付ける。原文にない実験名・現代の数値・観測による証明完了は補わない。',
 'einu':'経験に従う速度定数の採用eintを述べるメッセージ。引用した普遍法則の現実の真理を評価器で認定するものではない。',
 'einv':'同じ速度値tcが、選択された真空光往復の距離と同じ出発時計の経過時間を結ぶ正の速度であることを、既存sal/saiの少なくとも一つの適用で構成する。括弧内の真空中の光速度はこの同じ量の説明であり、別の定数を導入しない。',
 'einw':'三原文単位で一つの文をなす採用の著者帰属、一般法則とA/B表示式の具体化、同じ量への括弧内補足、先の時刻定義に加えるnoch、本文順序を保持する。',
}
LIMITS=[
 'u0019の46本文文字、u0020のM0040、u0021の66本文文字を一つの文として読む。Wir setzen ... festを現在の論述上の採用、der Erfahrung gemäßを経験に従う位置付けとし、物理的な実証完了や特定の実験結果を補わない。',
 'universelle Konstanteは同じ静止系・互換単位での全適用光往復に一つの値を固定する読み。位置・向き・正の距離・出発時刻を変えた理想的試行を含め、既観測又は成功した試行だけに制限しない。他系との不変性や光源運動からの独立性の詳しい条件はここで追加しない。',
 'M0040の2 AB/(t′_A−t_A)=Vを、正の距離・経過時間・速度の下でV×(t′_A−t_A)=AB+ABという既存saiに接続する。零・負の分母を許さず、往復距離と一方向距離を取り違えない。任意の曲がった経路の長さが2ABになるとは述べない。',
 'A/B、A側の出発・帰着、二つの時刻は先の同じ代表的往復へ結び、Vには既存の共通速度値tcを使う。距離は既存th、両真空区間はtk、単位はti/tjへ結び、単なる数式だけで物理的な対応を代用しない。',
 '反射側時計の指示は往復プロトコルの役割として保持するが、速度式の分母には使わない。同期の等時間式dbや反射時計の原点合わせを速度測定の必要条件へ加えない。',
 '括弧内のdie Lichtgeschwindigkeit im leeren Raumeは、同じtcの真空光往復速度としての説明と読む。nochの追加、先の定義からの順序、三単位が一文であることを保持する。',
 '距離・真空・単位・適用範囲は明示した物理的入力規約であり、ここで測定機器や真空の微視的理論を新たに定義しない。固定された正の距離と経過時間から速度が定まる算術と、全試行の値が共通である物理的採用を区別する。',
 '有限の数値例と試行モデルは接続・範囲・式の検査であり、任意の実数や全物理状況・意味同値の自動証明ではない。未知の読取り・距離・範囲を既定値で埋めず、全実数の標本化は拒否する。u0022以降は残る。',
]


def definitions():
    text='r eiskr['+' '.join(t for _,t in PRIMITIVES['eiskr'][0])+'] c.\n'
    selected=k('td',v('trial'),*[v(n) for n in ('frame','timeunit','lengthunit','context')])
    text+=define('einq',SCOPE,q('f','trial','a',op('z',selected,k('eiskr',v('trial'),*[v(n) for n,_ in SCOPE]))))
    text+=content('einr',both(k('einq',*[k(n) for n in ('ra','rb','ta','eirf')],v('point')),k('san',k('tc'),v('point'))))
    trial=k('eisjj');rate=lambda t:k('sal',t,*[k(n) for n in ('ra','rb','ta','tb','tc')],v('point'),'p sai')
    bindings=[op('e',k(fn,trial),k(ref)) for fn,ref in (('te','eisib'),('tf','eisik'),('qc','ziq'),('qd','zir'),('qe','eisjk'),('qf','eisjl'),('qg','eisjm'),('qh','eisjn'))]
    text+=content('eins',both(*bindings,k('sca',k('qi',trial),k('eisjo')),k('sca',k('qk',trial),k('eisjq')),k('td',trial,*[k(n) for n in ('ra','rb','ta')],v('point')),rate(trial)))
    text+=content('eint',both(k('ug',k('tm'),k('rd'),quote('einr'),k('eirf'),v('point')),k('to',k('tm'),k('rd'),k('tn'),k('eirf'),v('point'))))
    text+='d einu[] f[j s[k eint[]]].\n'
    text+=content('einv',q('g','trial','a',both(k('td',v('trial'),*[k(n) for n in ('ra','rb','ta')],v('point')),rate(v('trial')))))
    text+=define('einw',[],both(k('eir3',k('tm'),k('rd'),k('eirf'),quote('einu'),k('ri')),k('eisjt',k('tm'),k('rd'),quote('einr'),quote('eins'),k('eirf'),k('ri')),k('eisa5',k('tm'),k('rd'),quote('einr'),quote('einv'),k('ri')),k('eisb2',k('tm'),k('rd'),quote('eini'),quote('eint'),k('eirf'),k('ri')),k('ue',k('rj'),k('tm'),k('ri')),op('u',op('e',k('rj'),k('tm')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='einw',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='empirical_common_vacuum_light_speed_constant',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/event-time-summary-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
