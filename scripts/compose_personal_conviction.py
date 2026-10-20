"""Separate personal affirmation, full conviction and hypothetical non-endorsement."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE

PARENT='data/clerical-report-forecast-basis-v1.json'
LIBRARY='examples/v016/personal-conviction.noema'
BASIS='data/personal-conviction-basis-v1.json'
CONTENT='i[h[a d] e]'
PREMISE='i[h[d] c]'
PRIMITIVES={
    'h252d':('[a d] c',['judgment','point'],
        'この判断における本人の受け入れ方は、本人にとって承認を確定させるだけの根拠を得たという確信に支えられ、なお疑わしいという留保を伴わない。単なる仮の見込み、確率が高いという評価、外からの命令に従うだけの場合とは区別する。判断主体と肯定する内容は別に結ぶ。根拠の客観的な十分性・真理・全員への妥当性・将来も疑わないことをこの関係だけから導かない。'),
}
MEANINGS={
    'r42c':'同じ本人の同じ判断行為faを、同じ対象・閉じた内容関数・固定基準について肯定するh245qへ結ぶ。本人自身の賛同という読みの基本構成。組織の教示の帰属、単なる検討、否定的見解、物理的署名、内容の真理とは区別する。',
    'r42d':'r42cの同じ判断について、h252dの留保を伴わない本人の確信がある。別の判断に属する確信を流用しない。ここでの確信は明示した本人の受け入れ方であり、客観的な十分性を含む認識論の全理論ではない。',
    'r42e':'同じ本人・対象・内容関数・固定基準について、評価点にr42dを満たす判断が少なくとも一つある。否定すればそのような確信を伴う肯定がないことであり、あらゆる賛同の不在や内容の否定を意味しない。',
    'r42f':'同じ人物の視点・閉じた前提記述・評価点でhzkoにより選ぶ比較状況が非空であり、その全てで前提と指定帰結が成立する。現実の前提の偽を要求しない仮定的条件構成。前提が偽の比較状況や空の選択を成功にせず、現実の帰結・未来性・全可能世界への一般化を追加しない。',
    'r42g':'同じ本人と前提の下で、同じ対象・内容関数・固定基準への確信を伴う肯定r42eが成立しないだろう、というr42fの構成。否定を各比較状況の帰結の内側へ置く。単に「肯定するだろう」が成立しないことや、一候補だけの不賛同とは異なる。',
}
LIMITS=[
    'u0012[3899,4278)のうち本人の確信と仮定的な賛同の否定に用いる依存群。規定群・本文の具体的内容関数・仮定の補充・著者への帰属はまだ接続せず、全文の意味判断や確認文字数を増やさない。',
    'unterschreibenを内容への本人自身の賛同と読むための構成。署名行為や公的宣言を必須としない読みは、現代辞書の比喩的用法と前後の職務上の教示との対照を参照する。歴史的な唯一解釈を証明したとはしない。',
    'voller Ueberzeugungについて、本人にとって承認を確定させる根拠を得て疑いの留保を置かないという読みに限定する。KrV AA III 531–532の客観的に十分な根拠を含む技術的区別を、この心理的な基本関係だけで表したとはしない。本文統合時に採用解釈として明示する。',
    'wouldの前提をまだ固定していない。r42gは呼び出し側で閉じた前提記述を指定する。実際の署名要求・比較の最類似性・全ての反事実条件文の一般理論は補わない。旧rqrsは実際の前提の偽を要求するため流用しない。',
    '旧rgjの判断候補に一つでも賛同しない状況があるという条件を、全面的確信の不足の必要十分条件へ昇格させない。混在候補と空範囲、賛同しているが十分な確信がない場合を区別する。',
    'Satzungenの対象同定、会衆への全実益、引受け可能性、真理の隠れ方・可能性、内面の宗教との抵触不在と談話関係は未接続。教示の能力・許可・義務を確信の有無から導かない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    fields='person a judgment a target a content '+CONTENT+' reference d point d'
    args='v person v judgment v target v content v reference v point'
    text='d r42c['+fields+'] c['+both('k fa[v person v judgment v point]',
        'k h245q[v judgment v target v content v reference '+TRUE+' v point]')+'].\n'
    text+='d r42d['+fields+'] c['+both('k r42c['+args+']','k h252d[v judgment v point]')+'].\n'
    fields='person a target a content '+CONTENT+' reference d point d'
    text+='d r42e['+fields+'] c[g judgment a[k r42d['+args+']]].\n'
    chosen='k hzko[v person v premise v actual v candidate]'
    text+='d r42f[person a premise '+PREMISE+' consequent h[d] c actual d] c['+both(
        'g candidate d['+chosen+']',
        'f candidate d[y['+chosen+']['+both('c[s[v premise]][v candidate]',
            'c[v consequent][v candidate]')+']]')+'].\n'
    text+='d r42g[person a target a content '+CONTENT+' reference d premise '+PREMISE+' actual d] c['
    text+='k r42f[v person v premise i[point d][u[k r42e[v person v target v content v reference v point]]] v actual]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['fa','h245q','hzko']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='personal_conviction_and_hypothetical_nonendorsement',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
