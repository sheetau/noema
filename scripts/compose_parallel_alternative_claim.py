"""Connect the alternative derivation to the current point and axial conclusion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_parallel_current_records import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_calculation_discourse import STEPS
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-parallel-current-records.noema';PARENT_BASIS='data/parallel-current-records-basis-v1.json'
FULL='examples/v014/einstein-parallel-alternative-claim.noema';CORE='examples/v014/parallel-alternative-claim-core.noema'
BASIS='data/parallel-alternative-claim-basis-v1.json';ANNOTATIONS='data/parallel-alternative-claim-identifiers-v1.json';INDEX=148
MEANINGS={
 'ejra':'指定対象の第一系又は第二系での現在世界線出来事ejm3の全範囲を、同じ第三系の原点上の出来事へ結ぶ補助設定。対象範囲は非空で、全対象出来事に第三系の現在記録が存在し、全候補記録の三位置が零になる。第三系の時刻は零にせず、範囲を変換式の成否で選ばない。',
 'ejrb':'同じ二記録が指定光速度・符号付き速度の係数1の四変換s4lを満たし、最後の三位置が零なら、最初の三位置は指定速度×最初の時刻・零・零というsyrを満たすという条件付き関係。第三系原点の世界線を第一系で読む代数的な接続であり、単一記録から速度の測定を認定しない。',
 'ejrc':'現在の同方向の点の取得ejpp、三系と二変換の前提ejq7、第三系のk速度zltと点のk速さzkqの一致、その同じ点の全現在出来事を第三系原点へ合わせるejraを保持する補助的な導出の出発内容。点の速さと第三系速度を無条件には同一視しない。',
 'ejrd':'合成速度s3j(tc,zb7,zlt)に対し、同じ点のKの全現在履歴がその縦速度と横二成分零を持つejmv、実際の座標微分の非負ノルムが同じ値になるejoi、全対応記録の原点軌道syrを合わせる。速度式の記号だけを同じUと呼んで済ませない。',
 'ejre':'同じ補助設定ejrcと合成四式ejq6の下なら、同じ点の全K履歴と実際の速さejrd、および前段と同じ同方向の数式内容ejpqを得るという条件付きの接続。補助第三系が許されない点速度へ前提を拡張せず、元のejprの範囲も書き換えない。',
 'ejrf':'現在より前の同じ段階zlyで、既出方法zlvの非空有限列がejpbからejpcを経て同じ条件付き結論ejprへ至り、別の利用可能な一方法が補助設定ejrcから同じejprへ至る。別方法の同じ列にejrc→ejq7→ejq6→ejre→ejprの各一手を要求し、二変換・物理的な点への接続・同じ結論を保つ。規則の許容、列の接続、利用可能性を述べ、実行・健全性や補助設定の一般的存在を証明しない。',
 'ejrg':'著者が同じ第五節のzm2で、現在より前に別方法でも同方向の式を得られたというejrfを述べる。方法が用いる変換を同じ論説の先行第三節の最終変換ejehへ参照する。',
 'ejrh':'過去の別導出の利用可能性と§3参照ejrgを述べるメッセージ。',
 'ejri':'同じ著者・論説に別導出の振り返りを帰属し、前の光速度の表示式zlnからzm2への本文順序と箇所の区別を保持する。',
}
LIMITS=[
 'u0147第一文の過去の別導出と、その第三系原点による物理的な読みの関連依存群。現行文148を更新する。u0147第二文の命名・参照・提示とu0149の群・必要性を含む全単位判断は次の本文統合へ残す。',
 'hätten…auch…könnenは以前の同じ導出段階で利用できた別の方法と読む。実行済み、歴史上の不採用、心理的な容易さ、反実条件文一般の意味を補わない。前の計算はejpb→ejpcであり、同方向の結論ejprへの特殊化までを同じ以前の方法の列に含める。',
 '第三系の原点を同じ点の世界線へ合わせ、第三系の速度wをその場合の点のk速度へ対応させる補助的な読みを明示する。各系の現在記録・同じ対象・出来事範囲・全期間の履歴・実際の座標微分の非負ノルムを保持する。単一の原点記録や変換係数だけで速さの測定を代用しない。',
 'ejq7の二つの物理的な系速度は光速未満だが、前段の点の速度にはその上限がない。補助設定ejrcはその場合に適用できる狭い条件である。元のejpp/ejprへ上限を追加せず、著者が同じ結論を得られたと述べる有限手順の終点は同じejprへ保つ。補助設定から一般の結論への許容ステップzlaの真理・妥当性を検証器が認定したとはしない。',
 'ここに示す中間内容と列の制約は明示した解釈における方法の構造であり、原文に列挙された逐語的な証明や実行ログではない。引用された内容は偽でも引用でき、方法の存在・規則許容の主張も偽であり得る。検査成功を著者の一般物理導出の正しさへ替えない。',
 '旧s5m/s3c/s3mの参照を現行内容へ更新するが、旧定義と証拠を保存する。新しい基本記号は追加しない。',
]

def definitions():
    obj=v('object');firstframe=v('firstframe');secondframe=v('secondframe');thirdframe=v('thirdframe');ctx=v('context');event=v('event');record=v('record');zero=k('bb','n p a b')
    selected=op('x',k('ejm3',obj,event,firstframe,ctx),k('ejm3',obj,event,secondframe,ctx))
    chart=k('eiyx',event,record,thirdframe,ctx);origin=k('zbn',thirdframe,ctx)
    spatial=both(*(k('sca',k('zc6',record,k(a)),zero) for a in ('yn','yo','yp')))
    at_origin=both(k('zbv',thirdframe,origin,ctx),k('cb',event,origin,thirdframe),q('g','record','a',chart),q('f','record','a',op('y',chart,spatial)))
    text=define('ejra',[('object','a'),('firstframe','a'),('secondframe','a'),('thirdframe','a'),('context','d')],both(q('g','event','a',selected),q('f','event','a',op('y',selected,at_origin))))
    first=v('first');last=v('last');light=v('light');speed=v('speed');coords=lambda rec:[k('zc6',rec,k(a)) for a in ('yn','yo','yp','zc7')]
    origin=both(*(k('sca',x,zero) for x in coords(last)[:3]))
    text+=define('ejrb',[('first','a'),('last','a'),('light',R),('speed',R)],op('y',both(k('s4l',first,last,light,speed),origin),k('syr',speed,zero,*coords(first))))
    ev=lambda n:op('t',k(n),v('point'));fixedctx=k('zb6');fixedobj=k('zkb');frames=[k(n) for n in ('ra','zbm','zlo')]
    text+=content('ejrc',both(ev('ejpp'),ev('ejq7'),k('sca',k('zlt'),k('zkq')),k('ejra',fixedobj,*frames,fixedctx)))
    result=k('s3j',k('tc'),k('zb7'),k('zlt'))
    current=both(k('ejm3',fixedobj,event,frames[0],fixedctx),k('ejqv',*frames,event,first,v('middle'),last,fixedctx))
    line=op('y',current,both(k('ejrb',first,last,k('tc'),result),k('syr',result,zero,*coords(first))))
    for n in reversed(('event','first','middle','last')):line=q('f',n,'a',line)
    text+=content('ejrd',both(k('ejmv',fixedobj,frames[0],result,zero,zero,fixedctx),k('ejoi',result,fixedctx),line))
    text+=content('ejre',op('y',both(ev('ejrc'),ev('ejq6')),both(ev('ejrd'),ev('ejpq'))))
    stage=k('zly');previous=k('zlv');method=v('method');oldsteps=k('zlx',previous,stage);steps=k('zlx',method,stage)
    rules='i[before i[e] after i[e]]['+k('zla',v('before'),v('after'),stage)+']'
    old=both(k('s2w',oldsteps,quote('ejpb'),quote('ejpr'),rules),*(k('s5h',oldsteps,quote(a),quote(b)) for a,b in (('ejpb','ejpc'),('ejpc','ejpr'))))
    chain=('ejrc','ejq7','ejq6','ejre','ejpr')
    alternative=both(op('u',op('e',method,previous)),k('s5i',k('rd'),method,stage,quote('ejrc'),quote('ejpr'),'p zlw','p zlx','p zla'),*(k('s5h',steps,quote(a),quote(b)) for a,b in zip(chain,chain[1:])))
    text+=content('ejrf',both(k('zm4',stage,v('point')),old,q('g','method','a',alternative)))
    text+=content('ejrg',both(k('uh',k('zm2'),k('rd'),quote('ejrf'),k('eisoq'),v('point')),k('eisov',k('zm2'),k('rd'),k('eisms'),quote('ejeh'),k('eirf'),v('point'))))
    text+='d ejrh[] f[j s[k ejrg[]]].\n'
    text+=define('ejri',[],both(k('eir3',k('zm2'),k('rd'),k('eirf'),quote('ejrh'),k('ri')),k('ue',k('zln'),k('zm2'),k('ri')),op('u',op('e',k('zln'),k('zm2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==356;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejri',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='past_alternative_to_current_axial_conclusion',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},replaced_partial_statements=[INDEX],limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/parallel-current-records-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
