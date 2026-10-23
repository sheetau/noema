"""Compose a conditional train/clock utterance and its approximate paraphrase."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_temporal_judgments import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-temporal-judgments.noema';PARENT_BASIS='data/temporal-judgments-basis-v1.json'
FULL='examples/v014/einstein-train-clock-example.noema';CORE='examples/v014/train-clock-example-core.noema'
BASIS='data/train-clock-example-basis-v1.json';ANNOTATIONS='data/train-clock-example-identifiers-v1.json';INDEX=227
BASE=[(n,'a') for n in ('speaker','train','clock','hand','place','frame','unit')]+[('context','d')]
FIRST=BASE+[('arrival','a')];SECOND=FIRST+[('display','a')]
PRIMITIVES={
 'eise4':([('train','a'),('context','d')],'trainはレールに沿って走行し人又は物を運ぶ、連結された車両又はその編成としての列車である。この例で指示される同じ車両編成を追跡し、光信号、時計、語の列と取り違えない。特定の路線・動力・速度・時刻表は補わない。'),
 'eise5':([('place','a'),('speaker','a'),('context','d')],'placeが同じ例示状況でspeakerの「ここ」という指示が指す場所である。発言の場の位置に固定し、聞き手の別地点や後で光を受信する場所へ交換しない。地名・駅名・絶対座標を補わない。'),
 'eise6':([('clock','a'),('speaker','a'),('context','d')],'clockが同じ例でspeakerが自分の時計として用いる対象である。所有又は携用の指示を固定し、別人の時計や任意の参照時計と無条件に同一視しない。法律上の所有証明は要求しない。'),
 'eise7':([('hand','a'),('clock','a'),('context','d')],'handは同じclockの小さい針、すなわち時を指す短針である。文字盤の時の目盛を巡って進み、長い分針や秒針ではない。時針という機能を明示し、単に小さい棒という物体分類にしない。'),
 'eisfa':([('clock','a'),('hand','a'),('unit','a'),('context','d')],'同じclockのhandが指す文字盤の時の目盛と、unitによる時刻表示を対応させる校正・表示規約。unitは時の単位で、短針の一周を十二の等しい時の区分に分け、番号7の位置を7時の表示に対応させる。12時の位置と0の位相は同じであり、午前・午後や日付をこの表示だけで特定しない。単なる経過時間七単位や七回目の測定へ替えず、同じ例の表示周期と時計を保持する。実機の無限精度や遠隔同期は要求しない。'),
 'eisfb':([('arrival','a'),('target','a'),('place','a'),('frame','a'),('context','d')],'arrivalは同じtargetが、frameで指定したplaceへ到着する出来事である。近づいてきた対象がその到着地点へ達する位置変化を指し、既にそこにある状態や別地点での目撃だけとは区別する。停止、乗降、到着後の滞在、特定の速度を加えない。'),
 'eisfc':([('display','a'),('hand','a'),('clock','a'),('reading',R),('context','d')],'displayは同じclockのhandが、同じ表示規約でreadingに対応する時の目盛の位置を示す出来事である。針の姿勢と文字盤の目盛との物理的な指示関係を保ち、別の時計や別時点での読取りへ交換しない。readingの数値の有効性・校正・出来事の時刻と他の出来事との同時性は別に確認する。'),
 'eisfd':([('speaker','a'),('claim','i[e]'),('document','a'),('context','d')],'speakerが同じdocumentで考える発言状況で、claimに記述する内容を発言する。内容を持つ発言の成立であり、その内容の真理、列車等の物理的実現、著者が実際にこの発言をした履歴をこの関係だけから導かない。条件文の前件として使うときは、その仮定として扱う。'),
 'eisfe':([('speaker','a'),('claim','i[e]'),('paraphrase','i[e]'),('document','a'),('context','d')],'同じspeakerのclaimという発言を、paraphraseの内容によっておおよそ説明する約言の関係である。同じ対象・指示文脈と発言の論点を保持するが、全状況での厳密な論理的同値、二内容の真理、測定精度の数値的な一致は要求しない。元の発言から説明先への向きを保持し、曖昧な無関係の類似や文字列だけの置換ではない。'),
 'eisff':([], '引用例のJener Zugが指す同じ列車の談話上の対象。物理的な列車の型は引用内容内でeise4により保持する。実際の列車の存在をこの参照だけから断言しない。'),
 'eisfg':([], '引用例のmeiner Uhrが指す同じ時計の談話上の対象。話者への帰属・時計型・校正は引用内容内で要求する。'),
 'eisfh':([], '引用例で同じ時計の小さい針として述べる時針の対象。短針の役割はeise7で別に要求する。'),
 'eisfi':([], '引用例のhierで指す同じ場所。原刊の物理的な印刷場所や遠隔の受信地点ではない。'),
 'eisfj':([], '引用例の時刻表示で用いる時の単位。時計の十二の等しい時の区分と文字盤の番号に対応する尺度としてeisfaで固定し、暦上の日付・午前午後を指定しない。'),
 'eisfk':([], '二つの引用内容を通じて同じものとして述べる列車到着の出来事。到着の物理的内容はeisfbで要求し、この参照だけで実際の発生を断言しない。'),
 'eisfl':([], '引用例の同じ時計の短針が7を示す出来事。列車到着とは区別した出来事として指し、両者の同時性を引用内容内で述べる。'),
 'eisfm':([], '固定原文einstein-1905:u0010[482,666)の第四文。列車到着と短針の指示による同時性の約言を、条件付きの発言例として提示する箇所。'),
 'eisfn':([], '固定原文einstein-1905:u0279の著者脚注1)の箇所。原刊893頁下部にある局所同時性概念の不精密さ・抽象化・不議論の留保を述べる注。内容全体はこの参照だけでは記述済みとしない。'),
 'eisfo':([('node','a'),('note','a'),('document','a'),('number','b'),('context','d')],'同じdocumentのnodeに付された著者脚注番号numberがnoteの注本文を指すという参照。番号は正の整数で、本文中の印字された注番号と同じ注を保持する。編集者注、後続本文の独立段落、物理的な出来事の順序へ替えない。注の内容そのものの成立・記述完了とは別の文書上の対応である。'),
}
MEANINGS={
 'eii3':'引用例の同じ話者・列車・時計・短針・ここに当たる場所・基準系・時の単位について、型・指示・時計校正と十二時表示の規約、時計の局所配置を結ぶ。時計の世界線全体の静止や特定の日時は要求しない。',
 'eii4':'eii3の下で、同じ列車が同じ場所へ到着する出来事に、同じ時計・系・時の単位で7という読みが対応する。7時の到着という第一の引用内容の構成。',
 'eii5':'eii3の下で、同じ到着と、短針が同じ時計で7を示す別の出来事を、同じ場所へ結び、後者の時計の読みを7とする。二出来事の同じ系・単位での同時性を既存eihmで要求する。',
 'eii6':'話者rdと同じra、例で固定した列車・時計・針・場所・単位・到着にeii4を適用した第一の引用内容。評価状況は引用を解釈するpointであり、論説の提示時点の実測とはしない。',
 'eii7':'同じ例の同じ指示対象と到着・表示の二出来事へeii5を適用した第二の引用内容。第一の引用の到着を別の出来事へ交換しない。',
 'eija':'著者がeii6の内容を発言するなら、その同じ発言はeii7によっておおよそ説明されるという条件内容。発言済み・両内容の真理・厳密な同義性は追加しない。',
 'eijb':'第四文の条件付き約言eijaを主張するメッセージ。引用内の列車到着自体を著者が無条件に主張する発話へ替えない。',
 'eijc':'同じ著者・論説へのeijbの帰属、第三文の時間判断の論点を説明する具体例eir5、本文順序、同じ著者脚注1)への参照を結ぶ。',
}
LIMITS=[
 '第一人称ich/meinerは例の中で発言する著者の声に結び、同じ時計と場所の指示を保持する。特定の列車・駅・日付や著者の実際の発言歴を補わない。',
 '7 Uhrは校正された十二時表示の7時として読み、任意の経過時間七単位や午前・午後の確定に替えない。短針の指示、同じ時計の読み、同じ表示出来事を別々の関係で結ぶ。',
 '局所例では到着・表示・時計を同じ場所へ割り当てる理想化を採る。原刊脚注u0279が指摘するほぼ同じ場所での不精密さは既に読み取っており、無限精度の実測やその問題の解決済みとはしない。脚注の内容は別単位として記述を続ける。',
 '同時性は既存eihmの同じ系・尺度で有効かつ一意に付与された時刻の一致として記述する。局所の時計の読みと、共通の系で比較する時刻の割当を区別し、遠隔同期や絶対同時性を例だけから証明しない。',
 'Wenn ich sageは発言を前件に置く条件、z. B.は先行論点の具体例、etwaは約言として保持する。両引用内容をその場で実行せず、正確な論理的同値の証明にも替えない。',
 'u0010第四文151非空白文字と著者脚注1)への参照を扱う。脚注u0279の内容のNoema記述、段落全体の通読判断はまだ別に必要である。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    seven=k('bb','n p h b')
    text+=define('eii3',BASE,both(k('eise4',v('train'),v('context')),k('ca',v('clock')),k('ci',v('unit')),k('va',v('frame')),k('eisdf',v('clock'),v('context')),k('eise5',v('place'),v('speaker'),v('context')),k('eise6',v('clock'),v('speaker'),v('context')),k('eise7',v('hand'),v('clock'),v('context')),k('eisfa',v('clock'),v('hand'),v('unit'),v('context')),k('cb',v('clock'),v('place'),v('frame'))))
    arrival=[k('eisfb',*[v(n) for n in ('arrival','train','place','frame','context')]),k('cb',v('arrival'),v('place'),v('frame'))]
    text+=define('eii4',FIRST,both(k('eii3',*[v(n) for n,_ in BASE]),*arrival,k('ce',v('clock'),v('arrival'),v('frame'),v('unit'),seven)))
    text+=define('eii5',SECOND,both(k('eii3',*[v(n) for n,_ in BASE]),*arrival,op('u',op('e',v('arrival'),v('display'))),k('eisfc',v('display'),v('hand'),v('clock'),seven,v('context')),k('cb',v('display'),v('place'),v('frame')),k('ce',v('clock'),v('display'),v('frame'),v('unit'),seven),k('eihm',*[v(n) for n in ('display','arrival','frame','unit','context')])) )
    refs=[k(n) for n in ('rd','eisff','eisfg','eisfh','eisfi','ra','eisfj')]+[v('point'),k('eisfk')]
    text+=content('eii6',k('eii4',*refs));text+=content('eii7',k('eii5',*refs,k('eisfl')))
    text+=content('eija',op('y',k('eisfd',k('rd'),quote('eii6'),k('eirf'),v('point')),k('eisfe',k('rd'),quote('eii6'),quote('eii7'),k('eirf'),v('point'))))
    text+='d eijb[] f[j s[k eija[]]].\n'
    text+=define('eijc',[],both(k('eir3',k('eisfm'),k('rd'),k('eirf'),quote('eijb'),k('ri')),k('eir5',k('eisfm'),k('rd'),k('eise3'),quote('eija'),k('ri')),k('ue',k('eise3'),k('eisfm'),k('ri')),op('u',op('e',k('eise3'),k('eisfm'))),k('eisfo',k('eisfm'),k('eisfn'),k('eirf'),'n p b b',k('ri')),op('u',op('e',k('eisfm'),k('eisfn')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eijc',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='conditional_train_arrival_clock_hand_example_and_author_note_anchor',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/temporal-judgments-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
