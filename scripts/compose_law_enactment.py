"""Bind a complete people's legal provisions to enactment and self-imposition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='data/posterity-rights-basis-v1.json'
LIBRARY='examples/v016/law-enactment.noema'
BASIS='data/law-enactment-basis-v1.json'
FAMILY='i[h[j[a]] e]'
NAMES=('people','community','law')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
CLAUSE_BINDINGS='l[a][v law v people v community]'
PRIMITIVES={
 'h26b7':('[] d',[],'第六段落の立法の試金石を扱う同じ評価基準。政治的共同体・人民・法案の一般的な範囲を検討し、特定国や直前の特定合意へ固定しない。候補ごとの評価点や現行制度と区別する。'),
 'h26ca':('[a a d] c',['law','community','reference'],'この内容は、同じ政治的共同体の人々の外的な共同行為・公的秩序を規律する規範を、公的に拘束する法として定める案の種類に属する。私的な希望、経験上の自然法則、任意の助言と分ける。実際の採択、現行法での承認、道徳的正当性、特定の法形式や強制の実行は要求しない。全規範内容は別に条項へ結ぶ。'),
 'h26cb':('[a a d] c',['law','clause','reference'],'同じ法案と固定基準について、その法として定める規範内容の完全な範囲にこの条項項目が含まれる。現在成立している条項や賛同できる条項だけへ狭めず、単なる文書の物理的な段落とも同一視しない。要求・許可・禁止だけでなく資格・権能・それらの維持や変更も対象とでき、具体的な内容は同じh26ccで指定する。'),
 'h26cc':('[a d] '+FAMILY,['clause','reference'],'同じ条項項目と固定基準に対応する、閉じたNoemaの規範内容関数。正確な法・人民・政治的共同体の順の三個体列を受け、その法における規律の成立状態を返す。適用される人・役割・条件・内容極性・規範上の効果は関数の中に明示し、条項の名称だけで代用しない。正当性の外部評価や規律対象の行為の実際の履行は、法の規律状態自体と区別する。対象外の項目には全域関数の任意の値を与えてよい。'),
 'h26cd':('[a a a a a d d d] c',['activity','actor','people','community','law','reference','candidate','point'],'この同じ行為は、同じ候補経過・点で、この主体による、この人民にこの法律を課す公的な採択判断として帰属され、その同じ法案を共同の規律として定める内容を持つ。単なる提案・要望・他法への投票・受動的な服従ではない。行為の生起、制度上の成立効果、正当な資格・理性的な共同意思は別に確認する。集団が主体でもよいが、全成員が直接投票したことや全員一致を補わない。'),
 'h26ce':('[a a a a d d d] c',['activity','people','community','law','reference','candidate','point'],'同じ候補経過・点で、この採択行為が、指定の法律を指定の人民の同じ政治的共同体において効力を持つ公的規律として定める制度上の働きをする。新設だけでなく同じ規律の確認・再設定を含む。条項状態の偶然の併存、別行為の効果、物理的な服従の強制とは区別する。規律状態は別に構成し、この制度的な働きだけで道徳的正当性・採択資格・現実の行為生起を導かない。'),
}
MEANINGS={
 'r5ei':'同じ固定基準の人民がr45dにより政治的共同体の全成員と過不足なく一致し、同じ法案がその共同体の公的規律h26caであり、条項h26cbの全範囲が非空である枠組み。採択済み・正当とされた案だけへ限定せず、条項内容を実行しない。',
 'r5ej':'同じr5eiの枠組みの全条項について、閉じたh26ccの規範内容を同じ法・人民・共同体の順の三対象に適用し、同じ点でその規律状態が成立する。全条項に同じ基準・同じ点を使い、別々の時点の成立を合算しない。規律が以前は不在だったという条件を加えない。',
 'r5ek':'同じ主体・人民・共同体・法律・活動・候補点について、r5ei、採択の行為生起dg、公的な採択判断h26cd、同じ行為による制度上の設定h26ce、同じ全条項状態r5ejを結ぶ。他人や別行為の採択と条項状態の偶然の共存を許さない。',
 'r5el':'同じ固定基準と候補経過の履歴h257z/icが厳密な全順序をなし、その履歴上の一点で同じ主体が同じ法を同じ人民へ課すr5ekの活動がある。現実の経過を断言する演算ではなく、指定候補の中での採択内容を構成する。',
 'r5em':'r5elの採択主体と規律の宛先の双方を同じ人民へ束縛する。人民自身が自らに同じ法を課すという内容であり、成員全員の個別の立法行為、現実の投票や理性的な正当性は追加しない。',
 'r5en':'正確な人民・政治的共同体・法律の三個体列と固定基準から、同じ候補経過のr5emの自己賦課内容を返す。法条項の内側の列は法・人民・共同体の順へ明示的に組み替え、外側の列との取り違えを許さない。',
 'r5eo':'立法の試金石の固定基準h26b7をr5enへ供給する閉じた三対象の自己賦課内容族。可能性や資格や問いの対象として引用でき、引用によって実際の立法を断言しない。',
}
LIMITS=[
 '第六文[1265,1436)に必要な人民・法案・全条項・公的採択・自らへの賦課の依存群。何が立法として許されるか、合理的に同意し得る候補の範囲、kann/könnteとwohl、試金石の基準の強さ、問いと著者帰属は次に接続する。確認済み文字数は増やさない。',
 '人民は既存r45dの、同じ共同体の全人間成員からなる非空の集団として保持する。法を課す側と課される側を同一の集団へ束縛するが、民族的同一性、現代的な国籍制度、全員一致・直接投票を追加しない。',
 '法案の内容は非空の全規範条項で指定する。要求・許可の二種だけに閉じず、権能・資格・維持等の規範内容を同じ形式で持てる。条項で誰に何が課されるかをNoema内容に示すことは解釈入力の責任であり、型だけでその内容を自動翻訳・決定しない。',
 '旧rj7/rka/rkdは成立と不在の切替を要求する規範変更用の部分構成である。今回の一般的な法の賦課では、以前から同じ規律が成立していて再確認する場合も排除しない。旧定義や証拠を変更せず、変更内容だけの模型を全ての自己立法の定義へ拡げない。',
 '採択行為の内容、実行、制度上の設定効果、全条項の規律状態を別々に結ぶ。制度上の効力は道徳的な正当性や現行権力による事実上の強制と区別する。規律対象の行為の履行は法の成立に要求しない。',
 'この群は指定候補経過内の採択内容であり、まだその可能性・許可・理性的な共同意思を定義していない。後続の規範判定で、現行制度上の採択が可能なことだけを原文のkönnteへ代用しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    clauses='k h26cb[v law v clause v reference]'
    text='d r5ei['+FIELDS+' reference d] c['+both('k r45d[v people v community v reference]',
        'k h26ca[v law v community v reference]','g clause a['+clauses+']')+'].\n'
    rule='t[c[s[k h26cc[v clause v reference]]]['+CLAUSE_BINDINGS+']][v point]'
    text+='d r5ej['+FIELDS+' reference d point d] c['+both('k r5ei['+ARGS+' v reference]','f clause a[y['+clauses+']['+rule+']]')+'].\n'
    fields='actor a '+FIELDS+' activity a reference d candidate d point d'
    text+='d r5ek['+fields+'] c['+both('k r5ei['+ARGS+' v reference]','k dg[v activity v point]',
        'k h26cd[v activity v actor '+ARGS+' v reference v candidate v point]',
        'k h26ce[v activity '+ARGS+' v reference v candidate v point]','k r5ej['+ARGS+' v reference v point]')+'].\n'
    history='i[point d][k h257z[v reference v candidate v point]]';order='i[before d after d][k ic[v before v after v candidate]]'
    text+='d r5el[actor a '+FIELDS+' reference d candidate d] c['+both('k ta['+history+' '+order+']',
        'g point d[g activity a['+both('k h257z[v reference v candidate v point]',
        'k r5ek[v actor '+ARGS+' v activity v reference v candidate v point]')+']]')+'].\n'
    text+='d r5em['+FIELDS+' reference d candidate d] c[k r5el[v people '+ARGS+' v reference v candidate]].\n'
    text+='d r5en[bindings j[a] reference d] e[b candidate['+bind(NAMES,'k r5em['+ARGS+' v reference v candidate]')+']].\n'
    text+='d r5eo[bindings j[a]] e[k r5en[v bindings k h26b7[]]].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r45d','dg','ta','h257z','ic']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='complete_peoples_law_provisions_enactment_and_self_imposition',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
