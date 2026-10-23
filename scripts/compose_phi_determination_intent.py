"""Bind the still-undetermined scale in the current equations to its intended determination."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_wave_compatibility_conclusion import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-wave-compatibility-conclusion.noema';PARENT_BASIS='data/wave-compatibility-conclusion-basis-v1.json'
FULL='examples/v014/einstein-phi-determination-intent.noema';CORE='examples/v014/phi-determination-intent-core.noema'
BASIS='data/phi-determination-intent-basis-v1.json';ANNOTATIONS='data/phi-determination-intent-identifiers-v1.json';INDEX=309
MEANINGS={
 'ejaw':'既に得た現在の四変換式ei7cに同じφ=spcが現れ、先行段階zfmでの未決定性sqdに続いて、決定へ進む現在段階zglでも未決定性srpが残る内容。同じ候補族・現在関数・対象速度域を保ち、nochを後の決定済みへ替えない。',
 'ejax':'同じ著者が現在の四式にφがなお未知として残るejawを述べ、その同じ関数spcを今の段階zglから決定する意図zgmを同じ第三節で示す。未知性zgtから意図zgnへの本文順序を保持し、決定完了・唯一解・具体的方法を断定しない。',
 'ejay':'残る未知関数とその決定の意図ejaxを断定の伝達形式にする。意図の引用対象を実行して関数値を決めない。',
 'ejaz':'u0092の一文全体を同じ著者・論説へ帰属し、先行の両立性の結論zggから未知関数を決める議論への進行を保持する。',
}
LIMITS=[
 'u0092全文を原刊901頁へ照合する。entwickelten Transformationsgleichungenは現在の四式ei7c、φは同じ正規化後のspc、vは同じ相対速度の引数である。前の係数a=zeqとφ=aβを同一値にしない。',
 'unbekannte Funktionは、現在の関数を含む有効な候補族が残り、対象速度域のどこかで値が異なる候補も残るという既存の未決定性の読みを採る。関数の不存在、各速度で値が全て違うこと、現代の知識や著者の伝記的内心に替えない。',
 'nochは先行zfmのsqdから現在zglのsrpへ同じ未決定性が残ることと読む。両段階の候補集合が同一だとは要求せず、間の全瞬間について心理状態が連続したという主張は加えない。',
 '先行と同じ0≤v<Vの対象域で有効性・現在候補の保持・現在関数と候補値の一致・異なる候補値の存在を保持する。u0093以降で使う負速度の値をここで一意に補わず、原文にないφの正値・非零・φ=1を追加しない。',
 'welcheは未知として述べた同じ関数spcを受ける。wir nun bestimmen wollenは同じ著者が今の論述段階からその関数の値を決める意図を示すzgmとして読み、実行済み・成功・一意解・方法が見つかったことを含めない。',
 'この一文の既出式の指示、残存、未知関数の速度依存、同じ対象を受ける関係節、論述の現在と意図を記述する。第三系の導入・二回変換・相反性・符号規約は後続へ残す。',
 '有限対照は同じ段階・候補・関数・速度域の引数と引用・意図の帰属を検査する。実切断や関数全体への量化を有限標本で置換せず、例化した本体と有限境界を明示する。一般的な認識理論や意味同値の自動証明ではない。',
]


def definitions():
    point=v('point')
    text=content('ejaw',both(*(op('t',k(n),point) for n in ('ei7c','sqd','srp'))))
    text+=content('ejax',both(k('uh',k('zgt'),k('rd'),quote('ejaw'),k('eisms'),point),k('zgm',k('zgn'),k('rd'),quote('spc'),k('zgl'),k('eisms'),point),k('ue',k('zgt'),k('zgn'),point),op('u',op('e',k('zgt'),k('zgn')))))
    text+='d ejay[] f[j s[k ejax[]]].\n'
    text+=define('ejaz',[],both(k('eir3',k('zgt'),k('rd'),k('eirf'),quote('ejay'),k('ri')),k('ue',k('zgg'),k('zgt'),k('ri')),op('u',op('e',k('zgg'),k('zgt')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejaz',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_equations_still_unknown_phi_and_determination_intent',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/wave-compatibility-conclusion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
