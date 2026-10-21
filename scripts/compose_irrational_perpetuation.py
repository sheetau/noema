"""Compose coherence failure, persistent social maintenance, and causal outcome."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/unrestricted-scholarly-freedom-basis-v1.json'
DEPENDENCY='data/spiritual-guardians-basis-v1.json'
LIBRARY='examples/v016/irrational-perpetuation.noema'
BASIS='data/irrational-perpetuation-basis-v1.json'
CODE='i c[h[j[a] d] e]'
FIELDS='source a people a community a standard a reference d'
ARGS='v source v people v community v standard v reference'
PRIMITIVES={
    'h253s':('[a a '+CODE+' j[a] d] c',['standard','requirement','description','bindings','reference'],
        '固定した同じ評価基準で、引用した内容関数へ同じ順序の個体列と基準を渡す内容の、要求・根拠・目的・手段の相互整合を合理的に評価するときに不可欠な条件として、この要件が適用される。単なる好み、語の響き、任意の目標達成だけの条件とは分ける。整合性の範囲を解釈で固定し、評価結果から都合よく要件を選ばない。対象内容の真理や実施はこの関係で実行しない。'),
    'h253t':('[a a '+CODE+' j[a] d c d] c',['standard','requirement','description','bindings','reference','positive','point'],
        '同じ基準・要件・閉じた内容関数・正確な束縛列・固定基準の対象について、この評価点でその要件を満たすなら正極性、満たさないなら負極性の判定が成立する。要件の適用は別に要求する。未知を負極性へ補わず、肯否の衝突も一方の確定判定として扱わない。対象内容の真理、規範の現実の成立や実施は実行しない。一般の合理性の決定アルゴリズムを与える関係ではない。'),
    'h253u':('[a a d] c',['community','formulation','reference'],
        'この共同体の宗教的な教え・実践を扱う同じ固定文脈で、維持や改訂が問題となる定式化の完全な対象範囲に属する。内容は同じh246eの閉じたNoema記述で指定する。不合理という評価や将来の維持に成功したものだけで範囲を事後に選ばず、無関係な共同体や全ての人間の命題へ拡張しない。'),
    'h253v':('[a a d] c',['community','formulation','point'],
        'この共同体で、同じ定式化の教え・実践上の規則が、参照・伝達・行動を方向付ける採用内容として維持されている。内容の真理ではなく社会的な存続であり、歴史資料に記録だけが残ることや、反駁のための引用とは区別する。全成員の内心の賛同、同じ物理媒体や担い手の不変を要求しない。'),
    'h253w':('[a d d] c',['community','candidate','point'],
        '同じ共同体の指定候補の経過にこの状況が属する。持続を評価する基準以後の経過全体を解釈で供給し、都合の悪い時点を除外した有限観測記録で代用しない。順序と基準時の包含はrcaで別に確認する。候補が現実の履歴であること、共同体や個人の不死、数値時間が無限であることは含意しない。'),
    'h253x':('['+CODE+' j[a] '+CODE+' j[a] d d] c',
        ['cause','cause_bindings','result','result_bindings','reference','point'],
        '同じ固定基準と評価点で考える構成について、第一の記述と束縛で指定した方針を適用・維持することが、第二の記述と束縛で指定した結果へ至るという因果的な帰結関係にある。単なる同時成立、時間的な前後、形式論理の含意、誰かが根拠として挙げた発話とは区別する。内容を引用したまま結び、現実に方針が存在・実施されたことや結果が既に生じたことを主張しない。全背景を越える無条件の物理法則や唯一原因性は要求しない。'),
}
MEANINGS={
    'r45j':'同じ基準・閉じた段階2の内容関数・束縛列・固定基準・評価点について、合理的な整合に不可欠な適用要件が少なくとも一つ、負極性で判定され正極性では判定されていない。不合理を対象の単なる偽や引用内容の実行と同一視せず、未知や同じ要件の肯否衝突を不適合の証人にしない。',
    'r45k':'同じ出所・人民・政治的共同体・基準のr45i、すなわち後見人自身の未成熟を要求する全方針を、同じ評価基準のr45jで不整合と評価する内容。方針の現実の成立や本人の未成熟を実行しない。',
    'r45l':'定式化だけの正確な一個体列と固定基準から、その同じh246eが与える閉じたNoema内容を評価する内容アダプター。規範方針以外の教え・規則も同じr45jの評価対象として記述できる。自然言語文字列を内容の代用にせず、このアダプターを引用するだけなら内容を実行しない。',
    'r45m':'同じ共同体・定式化・評価基準・固定基準について、対象範囲h253uに属し、同じ定式化の内容をr45lの記述と一個体列でr45jへ渡すと固定基準で不整合と評価される。将来に維持されるかどうかをこの対象選択の条件にしない。',
    'r45n':'同じ共同体と基準でr45mの不合理な定式化の範囲が非空であり、その全対象が同じ候補履歴の基準時以降の全状況で社会的に維持される内容。既存rcaの非空・厳密全順序・基準時包含を要求し、単に別の不合理が代わりに残ることでは満たさない。',
    'r45o':'共同体・評価基準の正確な二個体列と固定基準からr45nの持続内容を作る。記述を因果的帰結の対象へ渡せるが、引用しただけでは不合理な内容の社会的維持や真理を実行しない。',
    'r45p':'同じ出所・人民・共同体・評価基準・固定基準に、要求方針自体の不合理というr45kの評価と、同じr45i方針から同じ共同体のr45oの持続へ至るh253xの帰結を結ぶ。評価と帰結を独立に保ち、片方だけから他方を補わない。',
}
LIMITS=[
    'u0012[5022,5190)のUngereimtheitとVerewigung der Ungereimtheitenへの依存群。全文の参照供給・評価基準の内容指定・selbst wieder・Dennと著者帰属を未統合として保持し、本文95主張と意味確認文字数は増やさない。',
    '不合理は、明示した合理的整合の基準に不可欠な条件を満たさないという読み。古典論理の矛盾式であること、単なる偽、本人の好みに合わないことではない。合理性の最終理論や全対象の自動判定を主張しない。全文では後見役と自立的判断との関係に即した要件を供給し、名前だけの基準で判断済みとしない。',
    '第一の評価対象は未成熟を要求する方針r45i。複数形で持続する対象は、同じ共同体の宗教的な教え・実践の全関連定式化のうち同じ基準で不合理と評価されるもの。両者を同一の一命題へ縮めず、単数の方針だけが残れば全体を表現できたことにはしない。',
    'Verewigungは、固定した関連範囲の不合理な内容が、同じ共同体の基準以後の履歴全体で維持されることという明示読み。各対象を保ち、時点ごとに別の不合理を選び直す弱い読みは採らない。複数形を種類全体への一般化として扱い、原文にない同時存在の固定件数は追加しない。',
    '持続は内容の社会的な採用・伝達・実践上の存続であり、その内容が真になることではない。rcaの将来全体を用い、選んだ短期区間の観測へ縮めない。履歴自体の終点の不在や有理数時間の非有界性は要求せず、原文外の無限の数値時間や個人の不死は補わない。',
    'hinausläuftは、方針を適用・維持すると指定の持続に至るという因果的な帰結の読み。h253xは二つの閉じた構成と正確な束縛を扱う一般関係で、実際の原因・結果の共存を要求する関係や単なる論理的含意とは区別する。帰結の構成はr45nの合成に置く。',
    '候補履歴の完全さ・範囲、合理的整合の基準と要件、各定式化の内容は解釈入力の責任として明示する。有限の履歴診断を現実の無限将来の観測や因果関係の実証と扱わない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


def definitions():
    payload='v standard v requirement v description v bindings v reference '
    text='d r45j[standard a description '+CODE+' bindings j[a] reference d point d] c[g requirement a['+both(
        'k h253s['+payload+']','k h253t['+payload+FALSE+' v point]','u[k h253t['+payload+TRUE+' v point]]')+']].\n'
    policy='r c[p r45i] l[a][v source v people v community]'
    text+='d r45k['+FIELDS+'] e[b point[k r45j[v standard '+policy+' v reference v point]]].\n'
    text+='d r45l[bindings j[a] reference d] e[b point['+bind(('formulation',),
        't[s[k h246e[v formulation v reference]]][v point]')+']].\n'
    text+='d r45m[community a formulation a standard a reference d] c['+both('k h253u[v community v formulation v reference]',
        'k r45j[v standard r c[p r45l] l[a][v formulation] v reference v reference]')+'].\n'
    selected='k r45m[v community v formulation v standard v reference]'
    persistent='k rca[i[at d][k h253w[v community v candidate v at]] i[first d last d][k ic[v first v last v candidate]] v reference i[at d][k h253v[v community v formulation v at]]]'
    text+='d r45n[community a standard a reference d] e[b candidate['+both('g formulation a['+selected+']',
        'f formulation a[y['+selected+']['+persistent+']]')+']].\n'
    text+='d r45o[bindings j[a] reference d] e[b candidate['+bind(('community','standard'),
        't[k r45n[v community v standard v reference]][v candidate]')+']].\n'
    text+='d r45p['+FIELDS+'] e[b point['+both('t[k r45k['+ARGS+']][v point]',
        'k h253x['+policy+' r c[p r45o] l[a][v community v standard] v reference v point]')+']].\n'
    return text


def build():
    old,dep=parent(),dependency();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['rca','ic','h246e']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(dep.document,['r45i']):
        n=d['name'];e=dep.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(dep.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='coherence_evaluation_social_persistence_and_quoted_causal_consequence',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set(old.source_sha256)|set(dep.source_sha256))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
