"""Compose time-function descriptions and prior clarification of physical time."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_point_position import ROOT,read,HISTORY
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,F,v,call as k,op,both,quant as q,lam

PARENT='examples/v014/einstein-point-position.noema';PARENT_BASIS='data/point-position-basis-v1.json'
FULL='examples/v014/einstein-motion-time-description.noema';CORE='examples/v014/motion-time-description-core.noema'
BASIS='data/motion-time-description-basis-v1.json';ANNOTATIONS='data/motion-time-description-identifiers-v1.json';INDICES=[224,225]
MATH=HISTORY[5:];RECORD=[('record','a')]+HISTORY
CRITERION='i[h['+' '.join(t for _,t in HISTORY)+'] c]'
PRIMITIVES={
 'eisem':(RECORD+[('criterion',CRITERION)],'recordが同じ物質点pointのframeに対する運動を記述するために、同じ長さ・時間単位、対象期間の下限と上限、三つの座標関数x,y,zを割り当てる数学的記述である。関数の入力は同じ時間変数、出力は同じ対象の各Cartesian座標である。期間はその記述課題の全対象期間で、測定済み時刻だけを抜き出さない。criterionはこのデータが物理的履歴に正しく対応するための閉じた条件の記述であり、単なる記号の綴りにせず同じ対象と全期間への対応を規定する。条件を引用したことからその成立や実測済みを導かない。'),
 'eisen':([('agent','a'),('point','a'),('frame','a'),('document','a'),('context','d')],'agentが同じdocumentの議論で、pointのframeに対する運動を記述しようとする意図を持つ。対象の位置の時間的な推移を説明することが目的であり、動かす意図、既に記述した事実、動力学法則を導出する意図へ替えない。条件文内の意図であり、その場での実際の意図の存在は別である。'),
 'eiseo':([('record','a'),('document','a'),('context','d')],'同じdocumentのここで扱う座標の時間関数による記述の範囲にrecordが属する。指定された全ての該当記述を対象とし、物理的意味や時間理解の得られた記述だけを後から選ばない。記述の数式上の型と対象への割当は別に合成する。'),
 'eisep':([('agent','a'),('record','a'),('document','a'),('context','d')],'agentが同じdocumentの記述手段としてrecordの三座標の値を時間の関数として与える。単なる三つの関数の存在ではなく、任意の対象時刻を入力として各座標値を指定する表示を提示する行為・方法である。数式、暗黙的な定義など表示形式を一つに固定せず、任意実数の全桁を有限計算するアルゴリズムや個別時刻の実測を要求しない。'),
 'eiseq':([('agent','a'),('record','a'),('document','a'),('context','d')],'agentがここで用いるrecordの数学的記述に、どの物質点のどの位置と時間を表すかという確定した物理的意味がある。数学的な変数を物理的な対象・出来事・尺度への指示として使う解釈の成立であり、式の型が合うことや数値計算できることだけとは区別する。軌道の予測が実際に正しいこと、観測で実証したこと、他の読者も理解したことは含意しない。'),
 'eiser':([('interpretation','a'),('record','a'),('document','a'),('context','d')],'interpretationがここでrecordの入力変数として用いる時間について、何を時間値として割り当て、どの出来事を同じ時刻と扱うのかを定める意味規約である。同じ記述の系と単位・指示対象を保持し、時間という綴りや無関係な哲学的定義だけにしない。後で論説が具体化する時計指示と同時性の規約を、この時点で完成・達成済みとは要求しない。'),
 'eises':([('agent','a'),('interpretation','a'),('record','a'),('document','a'),('context','d')],'agentが同じrecordの記述に用いる時間のinterpretationについて、その指示・適用条件を取り違えず把握できる明確な理解へ到達している。語を見たこと、何となく知っていること、物理的な記述が成功したことだけから推測しない。理解の対象と記述を保持し、到達の先行性は別の時間順序で指定する。'),
 'eiset':([], '固定原文einstein-1905:u0010[0,126)の第一文。物質点の運動を記述するため三座標を時間の関数として与えるという方法を述べる箇所。'),
 'eiseu':([], '固定原文einstein-1905:u0010[127,337)の第二文。数学的記述の物理的意味には時間の意味の先行理解が必要であると注意を促す箇所。'),
}
MEANINGS={
 'eiii':'同じ文脈で物体の構成点として追跡する物質点。物体全体や空間点へ替えず、静止・実際の位置変化は要求しない。',
 'eiij':'非退化な有効実時間区間と、その全入力で有効な実座標を返す三関数。数学的な時間依存を保ち、定数関数・往復・非等速を除かず、有限標本や微分可能性へ縮めない。',
 'eiik':'同じ物質点・系・文脈と異なる長さ・時間単位について、eiijの三関数を持つ記述recordを定める。既存seを正しい全履歴対応の基準として引用し、数学的な記述の提示からその物理的真理を実行しない。',
 'eiil':'同じ著者・物質点・系・論説に対して、同じ範囲の数学的記述eiikがあり、その同じrecordを三座標の時間関数という手段で与える。',
 'eiim':'先行の同じ系raで物質点の運動を記述しようとするとき、その点の三座標を時間の関数として与えるという一般的な方法の条件内容。特定の点の運動・記述意図の現実の存在を追加しない。',
 'eiin':'第一文の方法的条件内容eiimを主張するメッセージ。',
 'eiio':'第一文の同じ著者・論説への帰属と、前の位置指定段落からの本文順序。',
 'eiip':'同じ論説の範囲に属し、同じraの物質点と時間関数の型eiikを持つ全数学的記述の分類。物理的意味の成立や提示済みで対象範囲を制限しない。',
 'eiiq':'同じ記述の時間の意味規約があり、それについて同じ使用者が現在より厳密に前の状況で明確な理解へ到達している。本文順序ではなく既存zm4の時間的先行を使う。',
 'eiir':'同じ種類の全数学的記述と全使用者について、物理的意味があるなら時間の意味を先に理解しているという必要条件。逆向きの十分性・二条件の無条件の成立は追加しない。',
 'eiis':'第二文の必要条件eiirを主張するメッセージ。',
 'eiit':'第二文の同じ著者・論説への帰属と、第一文からの順序、既存zeiによる注意すべき事項としての提示を結ぶ。読者が実際に注意したことや証明済みは要求しない。',
}
LIMITS=[
 '第一文のWirは論述を進める著者の方法的な声として読み、複数人の集団や読者全員の現実の行為を補わない。Wollen … so …は意図に対する一般的な記述方法の条件で、実際の運動の存在や点を動かす意思ではない。',
 'Bewegungの記述は位置の時間的経過を表す運動学的な記述であり、定数の軌跡という特殊場合も許す。静止だけ、等速だけ、微分可能な関数だけへの限定や力・運動方程式を追加しない。',
 '三関数の型と、同じ物質点・系・尺度・対象期間への割当を明示し、seの完全な履歴対応を記述の正しさの基準として引用する。式に物理的意味があることと、その軌道が実際に正しいことを区別する。',
 'derartige mathematische Beschreibungは同じ三座標の時間関数の記述型を指す。erst dann … wennは先行理解を必要条件として読み、理解さえあれば全ての数学的記述が物理的意味を得るという十分条件は補わない。',
 'manはその記述を物理的に解釈して用いる任意の使用者として読む。時間の理解は同じ記述の変数の指示・適用規約の明確な把握で、単なる語の知識や成功結果からの推定とは区別する。vorherは現在の使用より厳密に前の状況とし、zeiで注意喚起も保持する。',
 '固定u0010の前二文286非空白文字を扱う。後二文の時間判断と同時的出来事、列車と時計の引用例、段落全体の通読判断は未完。局所検査を同義性の自動証明や全実数の列挙としない。',
]

def exists(fields,body):
    for n,t in reversed(fields):body=q('g',n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eiii',[('particle','a'),('context','d')],q('g','body','a',both(k('zm',v('body')),k('eirh',v('body'),v('particle'),v('context')))))
    domain=lam('time',R,k('lg',v('lower'),v('upper'),v('time')))
    text+=define('eiij',MATH,both(k('ba',v('lower')),k('ba',v('upper')),k('bg',v('lower'),v('upper')),*(k('la',domain,v(n)) for n in ('x','y','z'))))
    text+=define('eiik',RECORD,both(k('eiii',v('point'),v('context')),op('u',op('e',v('lengthunit'),v('timeunit'))),k('eiij',*[v(n) for n,_ in MATH]),k('eisem',*[v(n) for n,_ in RECORD],'r[p se]')))
    witnesses=[('record','a')]+HISTORY[3:]
    body=both(k('eiik',*[v(n) for n,_ in RECORD]),k('eiseo',v('record'),v('document'),v('context')),k('eisep',v('agent'),v('record'),v('document'),v('context')))
    text+=define('eiil',[(n,t) for n,t in [('agent','a'),*HISTORY[:3],('document','a')]],exists(witnesses,body))
    text+=content('eiim',q('f','particle','a',op('y',both(k('eiii',v('particle'),v('point')),k('eisen',k('rd'),v('particle'),k('ra'),k('eirf'),v('point'))),k('eiil',k('rd'),v('particle'),k('ra'),v('point'),k('eirf')))))
    text+='d eiin[] f[j s[k eiim[]]].\n'
    def attribution(name,node,message,previous,attention=False):
        items=[k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))]
        if attention:items.append(k('zei',k(node),k('rd'),k('eirf'),k('ri')))
        return define(name,[],both(*items))
    text+=attribution('eiio','eiset','eiin','eisel')
    text+=define('eiip',[('record','a'),('frame','a'),('document','a'),('context','d')],both(k('eiseo',v('record'),v('document'),v('context')),exists([HISTORY[0]]+HISTORY[3:],k('eiik',*[v(n) for n,_ in RECORD]))))
    text+=define('eiiq',[('agent','a'),('record','a'),('document','a'),('context','d')],exists([('interpretation','a'),('prior','d')],both(k('eiser',v('interpretation'),v('record'),v('document'),v('context')),k('zm4',v('prior'),v('context')),k('eises',v('agent'),v('interpretation'),v('record'),v('document'),v('prior')))))
    antecedent=both(k('eiip',v('record'),k('ra'),k('eirf'),v('point')),k('eiseq',v('agent'),v('record'),k('eirf'),v('point')))
    text+=content('eiir',q('f','record','a',q('f','agent','a',op('y',antecedent,k('eiiq',v('agent'),v('record'),k('eirf'),v('point'))))))
    text+='d eiis[] f[j s[k eiir[]]].\n'
    text+=attribution('eiit','eiseu','eiis','eiset',True)
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==224;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eiio','eiit')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='time_function_description_and_prior_physical_time_clarification',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=INDICES).document
    ann=json.loads(read('data/point-position-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
