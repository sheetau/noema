"""Compose posterity's collective disadvantage and a tentative causal forecast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_compact_causal_denial import NAMES as FIVE_NAMES,FIVE

PARENTS=('data/compact-causal-denial-basis-v1.json','data/provisional-order-sentence-basis-v1.json')
LIBRARY='examples/v016/posterity-harm.noema'
BASIS='data/posterity-harm-basis-v1.json'
NAMES=(*FIVE_NAMES,'earlier','posterity','standard')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
EIGHT='l[a]['+ARGS+']'
FAMILY='i c[h[j[a] d] e]'
PRIMITIVES={
 'h26e4':('[a a d d] c',['group','standard','reference','outcome'],'同じ固定成員の集団の利益について、指定した評価観点・基準で、この状況の評価が与えられている。未知を無害へ補わず、評価対象を被害者だけや現在の当事者だけへ選び直さない。評価済みは望ましい・悪いという方向を含まない。'),
 'h26e5':('[a a d d d] c',['group','standard','reference','first','second'],'同じ集団・評価観点・固定基準について、第一状況は第二状況と少なくとも同程度にその集団の利益にかなう。個々人の利益の総和・全員への同一影響・多数決と同一視せず、集団的な機会や継承の条件を評価できる。比較の方向と評価対象は固定し、比較不能・未知を同程度としない。厳密な悪化は逆向きの否定と合成する。'),
 'h26e6':('[i a[h[j[a] d] e] j[a] d d d] c',['condition','bindings','reference','outcome','baseline'],'閉じた条件内容と同じ対象列・固定基準に関して、第一状況と比較する第二状況が、同じ関連背景を保ち、その条件の影響を比較するために指定された反事実的な基準状況である。都合のよい結果を見て選び直さない。条件の実際の真偽、集団成員の一致、評価や原因性は別に検査する。現実の別時代との単なる比較、無関係な背景変更、現実の発生の断言と区別する。'),
 'h26e7':('[] a',[],'本箇所で後代集団の利益を比較する観点。先行文の認識獲得・理由ある誤りの訂正・理由ある自己判断を継承し発展させる機会と条件を評価する。金銭所得、全員の感情、実際に全員が改善したことに置き換えず、比較結果そのものを名前だけで指定しない。'),
 'h26fa':('[a a i d[e] '+FAMILY+' '+FAMILY+' d d] c',['node','author','whole','scope','focus','reference','context'],'著者が同じ全体内容・箇所・提示文脈において、指定範囲の同じ対象列・固定基準について焦点の帰結内容を、見込みを伴うが確定はしない推量として提示する。単なる論理的可能性だけ、無条件の確言、数値確率や高確率、著者の伝記的な内心に置換しない。範囲・焦点は閉じた内容族のまま結び、提示から引用内容の現実の成立や全候補への必然性を導かない。'),
}
MEANINGS={
 'r5jy':'同じ固定基準と候補の有効な全時代区分で、指定した先行時代の全点より後に生存する人を表す。既存r5dsの後代人の式を基準引数へ一般化し、直後の時代・血縁・後に出生した者だけへ狭めない。',
 'r5jz':'指定集団の固定基準での成員を、同じ候補履歴のどこかでr5jyに当たる全ての人と過不足なく一致させ、集団の非空性を要求する。全員の同時生存や全員の個別被害は要求しない。',
 'r5j2':'同じ合意の固定基準h254zが指定先行時代内にあり、r5jzでその時代に対する完全な後代集団を結ぶ。固定化する期間の終了を後世の始まりに置き換えず、長期・無期限の合意でも後代を表せる。',
 'r5j3':'正確な八対象列から、同じ合意・先行時代に対する同じ後代集団が、指定評価観点で反事実的な基準状況より厳密に不利となる内容を返す。基準状況は同じ五対象の不毛化r5joの比較として固定し、そこでは不毛化しない。両状況の完全な後代成員・評価済み・自己比較・比較の方向を確認する。不毛化自体や原因性はこの害の結果条件に追加しない。',
 'r5j4':'同じ八対象列から、同じ五対象の不毛化r5joと同じ合意・先行時代の完全な後代集団r5j2を結ぶ。後代の害への因果的帰結の原因側であり、別期間の停滞へ取り替えない。',
 'r5j5':'同じ八対象列・基準・評価点について、不毛化r5j4から後代の不利益r5j3へのh253xの因果的帰結を結ぶ。最初の合意実施から不毛化への帰結とは別に保持し、因果の推移律や単なる共起から導かない。引用内容の現実の成立は要求しない。',
 'r5j6':'正確な八対象列と固定基準からr5j5の因果的帰結を返す内容族。推量の焦点として引用し、推量の提示とは独立に無条件の著者断言を追加しない。',
 'r5j7':'同じ八対象列の先頭五対象がr5jsの合意候補をなし、同じ合意の先行時代に対する完全な後代集団があり、評価観点がh26e7に一致するという範囲。合意の実際の形成、不毛化、害、比較基準の成功によって候補を選別しない。',
 'r5ka':'同じ全体内容・箇所・著者・固定基準・提示文脈で、r5j7の範囲についてr5j6の因果的帰結を推量として提示する。引用の対象列と基準を共通にし、禁止や第一の不毛化帰結へ留保を広げない。',
}
LIMITS=[
 'u0013第八文の後世への害と二つ目のdadurch、wohlの推量に向けた依存群。nachtheiligは、後代の集団が認識・訂正・自己判断を継承し発展させる機会と条件の不利益という読み。全員が個別に被害を受けること、任意の一人の被害だけ、金銭損失へ置き換えない。集団利益の比較は明示入力であり、その社会哲学的な一意の集約理論を証明したとはしない。',
 'Nachkommenschaftは先行する合意の時代の後に生存する人々全体。後の出生に限らず先行時代との重なりを許す。先行時代の区分と合意基準は固定し、制度固定化期間の終了後だけへ限定しない。候補枠組みの後代集団が空なら、この対象範囲の記述は成立しない。',
 '害の比較は同じ後代成員・同じ評価観点・関連背景を保つ基準状況で行い、基準状況では同じ期間が不毛でない。これは知的機会の不利益という採用読解の対照であり、人口そのものが変わる比較や全種類の害の一般定義ではない。選定された比較基準の存在と妥当性は入力の責任である。',
 '不毛化と害は別の結果条件。二つ目のdadurchは同じ不毛化から同じ後代への害へ至る因果的帰結として保持する。前段の合意実施から不毛化への原因性をコピーして代用せず、実際の原因推定や因果の推移律も追加しない。',
 'wohlは帰結を推量として提出する読みを採る。客観的な高確率や単なる存在可能性へ強めたり弱めたりせず、提示態度h26faに保持する。全文統合時、r5j6を留保なしに別途著者へ断言してはならない。garの増幅と内側のaberによる不毛から害への対照は、全文の同じ箇所へ別に接続する。',
 '全体内容と箇所・著者・参照はr5kaの引数として残る。期間の消去への見立て、gar・aber、規範出所と立場の固定、schlechterdings・auch nur・冒頭Aber・全文帰属と通読は未完。本文103主張・登録簿v186を保持し、意味確認文字数を増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    epoch='k h26ab[v earlier v reference v candidate v old]'
    later=both('k r5bw[v reference v candidate]','k h26aa[v earlier v reference]','k aa[v person]',
        'k h257z[v reference v candidate v point]','k h256o[v person v candidate v point]',
        'g old d['+epoch+']','f old d[y['+epoch+'][k ic[v old v point v candidate]]]')
    text='d r5jy[person a earlier a reference d candidate d point d] c['+later+'].\n'
    member='k h246c[v posterity v person v reference]'
    future='g point d[k r5jy[v person v earlier v reference v candidate v point]]'
    text+='d r5jz[posterity a earlier a reference d candidate d] c['+both('k r5bw[v reference v candidate]',
        'k h26aa[v earlier v reference]','g person a['+member+']','f person a[z['+member+']['+future+']]')+'].\n'
    text+='d r5j2[agreement a earlier a posterity a reference d candidate d] c['+both(
        'k r5jz[v posterity v earlier v reference v candidate]',
        'k h26ab[v earlier v reference v candidate k h254z[v agreement]]')+'].\n'
    def scope(scene):return 'k r5j2[v agreement v earlier v posterity v reference v '+scene+']'
    def assessed(scene):return 'k h26e4[v posterity v standard v reference v '+scene+']'
    def order(first,last):return 'k h26e5[v posterity v standard v reference v '+first+' v '+last+']'
    result='g baseline d['+both('k h26e6[r[p r5jo] '+FIVE+' v reference v candidate v baseline]',
        scope('baseline'),'u[t[k r5jo['+FIVE+' v reference]][v baseline]]',assessed('baseline'),
        order('baseline','baseline'),order('baseline','candidate'),'u['+order('candidate','baseline')+']')+']'
    text+='d r5j3[bindings j[a] reference d] e[b candidate['+bind(NAMES,both(scope('candidate'),assessed('candidate'),order('candidate','candidate'),result))+']].\n'
    text+='d r5j4[bindings j[a] reference d] e[b candidate['+bind(NAMES,both(scope('candidate'),'t[k r5jo['+FIVE+' v reference]][v candidate]'))+']].\n'
    text+='d r5j5['+FIELDS+' reference d point d] c[k h253x[r c[p r5j4] '+EIGHT+' r c[p r5j3] '+EIGHT+' v reference v point]].\n'
    text+='d r5j6[bindings j[a] reference d] e[b candidate['+bind(NAMES,'k r5j5['+ARGS+' v reference v candidate]')+']].\n'
    candidate='g group a[k r5js[v group '+' '.join('v '+n for n in FIVE_NAMES)+' v reference v candidate]]'
    text+='d r5j7[bindings j[a] reference d] e[b candidate['+bind(NAMES,both(candidate,scope('candidate'),'e[v standard][k h26e7[]]'))+']].\n'
    text+='d r5ka[node a author a whole i d[e] reference d context d] c[k h26fa[v node v author v whole r c[p r5j7] r c[p r5j6] v reference v context]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5jo','r5js','h253x'],['r5bw','h26ab','h246c','h256o'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='posterity_collective_comparative_harm_and_tentative_causal_consequence',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
