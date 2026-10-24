"""Present the ninth-section charge result as a short, important, readily derived note."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,v,call as k,op,both,quant as q
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_calculation_discourse import STEP

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-moving-body-charge-history.noema';PARENT_BASIS='data/moving-body-charge-history-basis-v1.json'
FULL='examples/v014/einstein-charge-constancy-claim.noema';CORE='examples/v014/charge-constancy-claim-core.noema'
BASIS='data/charge-constancy-claim-basis-v1.json';ANNOTATIONS='data/charge-constancy-claim-identifiers-v1.json';INDEX=412
PRIMITIVES={
 'eiswr':([('subject','i[e]'),('scope','a'),('reference','d')],'同じscopeの研究・説明上の課題に照らし、subjectで指定する内容が、対象の理解又は適用上の帰結に相応の影響を持つ重要な事柄と評価される。単に注意を引くこと、驚き、長さ、計算の容易さ、人気又は真理とは区別する。評価対象は同じ閉じた内容であり、文脈上の課題と重要性の基準を固定して読む。唯一最重要、数値順位、全読者の一致や対象内容の実証を含めない。'),
 'eisws':([('begin','a'),('end','a'),('scope','a'),('reference','d')],'同じscopeにおけるbeginからendまでの提示範囲が、その論述で通常必要とされる説明の分量に比べて短い簡潔な扱いとして置かれる。対象となる範囲を固定し、最初の一語だけの長さ、対象内容の些細さ又は証明の容易さとは区別する。特定の字数・実行時間・必要事項の省略を要求せず、対象の説明の分量を評価する。'),
 'eiswt':([('node','a'),('author','a'),('remark','i[e]'),('previous','a'),('scope','a'),('reference','d')],'同じauthorがpreviousまでの論述に加えて、nodeで同じremarkへ注意を向ける補足を、ここで述べておくことを控えめに提案する形で提示する。主たる議論からの追加の注記であり、外部の許可が実際に与えられたこと、命令、未回答の質問、内容の不確かさ又は実際の読者の同意へ替えない。補足の具体的な内容は引用に保持し、内容の真理や一般的な導出の妥当性はこの提示関係自体から導かない。'),
 'eiswu':([], '固定u0238のEs möge noch kurz bemerkt werdenからkann:までの導入箇所。同じ節の最後に、後続の定理を容易に導ける重要な補足として導入する。'),
 'eiswv':([], '固定u0238のコロン後Bewegt sichからkonstant.までの条件付き定理を述べる箇所。任意運動する帯電物体の同じ電荷を随伴系とKから比較する。'),
}
MEANINGS={
 'ek3e':'第九節で先行した原系方程式ekzcと変換結果ekz7を、新三速度の物理的同定ek2jを含む同じ解釈で受け直した導出の出発内容。表示された二式群とその量の意味を共有し、独立した相対性適合の結論や後続の総電荷一定を前提へ加えない。',
 'ek3f':'同じ著者が利用できる一つの方法があり、その同じ非空有限手順列がek3eから全設定の定理ek3dまで許容された手順でつながり、各手順の非負負担の合計が文脈上の低負担基準に入る。leicht ... gefolgert werden kannの導出可能性と容易さを共有する。手順の実行済みや結論の真理を追加しない。',
 'ek3g':'同じ全設定の定理ek3dが、同じ第九節の課題にとって重要だという評価。計算の容易さ、注目だけ、独立した別命題の重要さへ替えない。',
 'ek3h':'同じ定理に至る容易な導出可能性ek3fと、その定理の重要さek3gを同じ点で結ぶ注記内容。二評価に異なる結論を選ばない。',
 'ek3i':'同じ著者が前文eiswqまでの論述に加えてek3hを控えめな注記として導入し、その導入から定理末尾までを短い扱いとして置く。先行の原系方程式、変換結果、量の同定の各内容へ照応して、entwickelten Gleichungenの出発点を固定する。',
 'ek3j':'後続の同じek3dを第九節の主張として述べ、引用符付きの静止系という呼称eisebを同じK=raへ再使用する。導入が指す定理をufによる説明と本文順序へ結び、原理における絶対静止の主張にしない。',
 'ek3k':'u0238の控えめで短い補足、容易な導出可能性、重要性、先行方程式への照応、コロン後の定理、引用符付きKを一続きに結ぶ全文内容。auchは同じ設定内で随伴側の一定を保持しKにも同じ一定性を加えるek3cの向きへ結ぶ。',
 'ek3l':'同じ全文内容ek3kを断定の伝達形式にする。引用した方法・定理の実際の成立をこの形式で実行しない。',
 'ek3m':'同じ著者rd・論説eirfへのek3lの帰属と、前文の相対性への適合eiswqから導入eiswuへの本文順序を保持する。旧412主張を保存して新しい一主張を加える。',
}
LIMITS=[
 'u0238全文とM0393を原刊917頁へ照合する。一つの単位の中で、コロン前の導入とコロン後の条件付き定理を別箇所に分け、同じ内容の前方参照と説明接続を保持する。',
 'Es möge ... bemerkt werdenは、著者が追加の注記をここで述べておくという控えめな提示として読む。許可を求める外部手続、読者への命令、物理的可能性だけの推測、仮定の未確定性へ替えない。nochは前文に加える補足、kurzは導入から定理末尾までの扱いの短さである。',
 'entwickelten Gleichungenは、同じ第九節の原系法則ekzcと変換結果ekz7を、直前に同定された新速度ek2jの物理的な読みで受け直す。原刊磁気側の1/V欠落はsemfのまま保存し、この導出を健全にするための修正又は追加物理前提を行わない。',
 '容易さは同じ出発点・終点を持つ非空有限の許容手順列と、その同じ手順列の低負担で構成する。方法が利用可能であるという可能性を実行済み・証明完了uiに替えない。方法・許容規則・負担と基準の物理的又は論理的な妥当性は著者の評価であり、有限検査による自動証明ではない。',
 '重要さ、扱いの短さ、控えめな補足の提示は三つの一般関係で区別する。いずれにも総電荷・任意運動・Einstein・Lorentz・特定定理の真理を埋め込まず、閉じた具体的内容又は本文範囲へ合成して適用する。',
 '定理の内容は前段ek3dを共有する。持続的な同じ全物質点の物体の完全な区間履歴、各系の全時刻における実際の全体電荷、追跡点へ原点を随伴する系、同じ追跡点の同じ出来事で対応する期間という明示した読みを採る。全体の剛性・等速・一様密度・共通静止慣性系・各部分の電荷不変を要求しない。',
 '随伴する系で一定ならKでも一定という条件を保つ。auchは同じ物体・量・比較期間について一定性をKにも加えることであり、二系の数値電荷の等値ではない。内部での電荷交換を許し、符号は正に限定しない。帯電は随伴側の正味総電荷の非零という巨視的な読みである。',
 '引用符付きruhendenは先行導入の同じ呼称eisebと同じKを指す。物体や宇宙全体の静止、特権的な絶対静止を含意しない。Kから見るという視点は、同じ物体をKの時計・単位・同時切片で記述する内容に接続済みである。',
 '形式検査は手順列・評価対象・範囲・参照・著者帰属と、前段の物理的履歴の結合を区別する。全連続体の物理法則、著者の一般的な導出の正しさ、原文同義性の自動証明とはしない。後続u0239以降の第十節は別範囲である。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    p=v('point');ev=lambda n:op('t',k(n),p);author=k('rd');scope=k('eisv6');paper=k('eirf');intro=k('eiswu');theorem=k('eiswv')
    text+=content('ek3e',both(*(ev(n) for n in ('ekzc','ekz7','ek2j'))))
    method=v('method');steps=k('zlx',method,p)
    easy=k('s2y',steps,quote('ek3e'),quote('ek3d'),'i[before i[e] after i[e]]['+k('zla',v('before'),v('after'),p)+']','i[step '+STEP+']['+k('zlb',v('step'),p)+']','i[burden b]['+k('zlc',v('burden'),p)+']')
    text+=content('ek3f',q('g','method','a',both(k('zlw',author,method,p),easy)))
    text+=content('ek3g',k('eiswr',quote('ek3d'),scope,p))
    text+=content('ek3h',both(ev('ek3f'),ev('ek3g')))
    refs=[k('eiswm',intro,author,k(node),quote(target),paper,p) for node,target in [('eiswf','ekzc'),('eiswn','ekz7'),('eiswq','ek2j')]]
    text+=content('ek3i',both(k('eiswt',intro,author,quote('ek3h'),k('eiswq'),scope,p),k('eisws',intro,theorem,scope,p),*refs))
    text+=content('ek3j',both(k('uh',theorem,author,quote('ek3d'),scope,p),k('eismz',theorem,k('eiseb'),k('ra'),paper,p),k('uf',author,intro,theorem,p),k('ue',intro,theorem,p),op('u',op('e',intro,theorem))))
    text+=content('ek3k',both(ev('ek3i'),ev('ek3j')))
    text+='d ek3l[] f[j s[k ek3k[]]].\n'
    text+=define('ek3m',[],both(k('eir3',intro,author,paper,quote('ek3l'),k('ri')),k('ue',k('eiswq'),intro,k('ri')),op('u',op('e',k('eiswq'),intro))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ek3m',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    prim={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='short_important_charge_constancy_theorem_and_easy_derivation',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=prim,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-body-charge-history-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
