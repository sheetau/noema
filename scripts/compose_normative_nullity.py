"""Deny source-grounded normative consequences beyond duties and permissions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/covenant-question-basis-v1.json'
LIBRARY='examples/v016/normative-nullity.noema'
BASIS='data/normative-nullity-basis-v1.json'
PRIMITIVES={
 'h256j':('[a a d] c',['position','assessor','reference'],
     '指定した正当性の評価規範と固定基準について検討する規範的地位・帰結の対象範囲に、この項目が含まれる。要求・許可だけでなく権利・権能・免責・資格・規範の変更や維持も含め、実際に成立するもの、既に有効と判定したもの、当事者が一覧に掲げたものだけに範囲を狭めない。各項目の具体的内容はh256kで指定する。全対象範囲の完全さは解釈入力の責任であり、有限検査の一覧が現実の全対象だとはしない。'),
 'h256k':('[a d] i d[e]',['position','reference'],
     '同じ規範的地位・帰結の項目と固定基準に対応する、閉じた段階3のNoema内容記述。要求や許可の対象、当事者・立場・内容の肯否、権能の変更対象など、当該帰結を識別する参照をその内容に保持する。自然言語の名前だけで帰結を代用しない。同じ名前でも異なる帰結なら別項目であり、内容を引用しただけで成立を断言しない。対象外の項目への値は全域関数の任意値でよく、範囲条件により判断から除かれる。'),
 'h256l':('[a a i d[e] d d] c',['assessor','source','consequence','reference','point'],
     '指定した正当性の評価規範・固定基準の下で、この出所が、指定した閉じた規範的帰結の成立・維持を正当化する根拠として、この評価点で働く。単独の十分根拠だけでなく、他の条件や承認を伴って規範的効力を支える場合も含む。別の出所の独立した根拠、物理的な因果作用、現行の権力による強制や効力の主張、その帰結の単なる真理とは区別する。根拠の認定基準そのものを自動決定する手続ではない。'),
}
MEANINGS={
 'r474':'同じ規範的帰結の項目が指定の全対象範囲に含まれるなら、同じ項目の閉じた内容を指定の出所が正当化する根拠にならない。内容を脱引用せず、評価規範・基準・点を保持して否定する。',
 'r475':'指定出所についてr474が全項目で成立する内容。要求・許可の二種だけに制限せず、当該出所が正当な規範的効力の根拠にならないという無効性を構成する。他の独立した根拠による帰結や現実の強制は否定しない。',
 'r476':'同じ出所・評価規範・固定基準について、評価点でのr475と、同じ基準で固定した候補状況において指定主体の非空な全員の承認があってもr475である条件を結ぶ。出所を承認主体へ置き換えず、承認の実在や承認候補の存在を主張しない。通常予想に反する譲歩の提示は別に結ぶ。',
 'r477':'第六段落の同じ政治的共同体と固定基準に対応する正当性の評価規範h255pを供給し、指定した契約のr475を内容にする。契約が形成済みであることや、全契約の無効性をそれ自体で断言しない。',
}
LIMITS=[
 'null und nichtigは二つの独立した効力の欠如ではなく、効力のないことを強調する一まとまりと読む。無効性を形成事実の不存在、内容の偽、物理的不可能性へ置き換えない。原文への適用では正当な規範上の効力を評価し、現行権力の承認とは分ける。',
 '全帰結の範囲h256jは、既に認められた帰結や要求・許可だけへの制限を許さない。帰結項目ごとに閉じたNoema内容を指定し、権能などの複合した地位も内容として持てる。段階3の記述を使うこの構成は全ての記述段階の有限列挙や言語の万能性の証明ではない。',
 '出所が単独で十分な根拠になる場合だけを否定すると、別の承認との組合せで効力を生む余地が残る。h256lは同じ出所が他条件とともに正当化の根拠として働く場合も含む。契約の締結を契機に外部の規範源から生じる救済・返還・制裁等の帰結は、この契約が効力の根拠になる場合とは区別する。',
 'r476は基準で固定した全候補にわたる条件内容。候補の完全さや承認主体の歴史的分類、通常期待への譲歩、契約の特定と目的・仮定形成、schlechterdingsの無留保の提示、全文の帰属は別に必要である。これだけで原文一文の完成とはしない。',
 '全項目への量化を既知の有限一覧へ書き換えない。検査の有限モデルは、異なる帰結・根拠・評価点・承認を区別する検査であり、現実の全規範的帰結の網羅や正当性判断の正しさを証明しない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    text='d r474[source a assessor a position a reference d point d] c[y[k h256j[v position v assessor v reference]][u[k h256l[v assessor v source k h256k[v position v reference] v reference v point]]]].\n'
    text+='d r475[source a assessor a reference d] e[b point[f position a[k r474[v source v assessor v position v reference v point]]]].\n'
    fields='source a assessor a reference d candidates h[d d] c authorities h[a] c confirms h[a a d] c'
    candidates='i[scene d][c[v candidates][v reference v scene]]'
    condition='i[source a scene d][t[k r475[v source v assessor v reference]][v scene]]'
    text+='d r476['+fields+'] e[b point['+both('t[k r475[v source v assessor v reference]][v point]',
        'k rhv[v source '+candidates+' v authorities v confirms '+condition+']')+']].\n'
    text+='d r477[contract a] e[k r475[v contract k h255p[k h255r[] k h255o[]] k h255o[]]].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['rhv','h255p','h255r','h255o']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='normative_nullity_as_absence_of_source_grounded_consequences',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
