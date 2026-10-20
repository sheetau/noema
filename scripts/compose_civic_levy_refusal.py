"""Bind a civic levy, its payment requirement, and a distinct refusal response."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENT_BASIS='data/protected-remarks-basis-v1.json'
LIBRARY='examples/v016/civic-levy-refusal.noema'
BASIS='data/civic-levy-refusal-basis-v1.json'
CODE='i[h[j[a]] e]'
NAMES=('issuer','person','role','transfer','receiver','medium')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
PAYMENT='l[a][v person v transfer v receiver v medium]'
PRIMITIVES={
    'h244g':('[a a d] c',['role','community','reference'],
        'この立場は、同じ政治的共同体の一般の成員として共同の規律・負担に関わる市民の立場である。官吏として委ねられた職務、特定階級・職業、納付した人だけの分類とは分ける。現代の国籍法・選挙権・特定身分の要件を補わず、本人の成員性と役割保持は別に結ぶ。'),
    'h244h':('[a a d] c',['levy','community','reference'],
        'この賦課は同じ政治的共同体の公的な収入・共同負担に向けて制度的に課される金銭・現物等の給付負担である。私人間の贈与や個別売買の対価だけとは区別する。特定税目・金額・通貨・期限、合法性・公正さ・本人の同意・納付済みは要求しない。'),
    'h244i':('[a a a a a a a d] c',['levy','issuer','person','role','transfer','receiver','medium','reference'],
        '同じ賦課の制度上の対象指定が、この出所・本人・立場・納付行為・受取先・価値媒体という同じ組を指す。賦課という負担対象と、その履行となる移転行為を区別する。対象指定だけでは要求の規範的効力・正当性・実際の移転を認めず、要求は別に確認する。'),
    'h244j':('[a a '+CODE+' j[a] c d] c',['person','response','content_family','bindings','polarity','point'],
        '本人はこの反応において、閉じた内容関数へ同じ順序の引数列を渡した内容を、指定極性で自分の実践上の方針として明確に引き受ける。発言による表明または行動上の選択としての立場であり、単なる予測・希望・未達成・能力不足とは区別する。その方針の実行成功、内容の真理、外からの要求の存在は含意しない。'),
    'h244k':('[a a a a '+CODE+' j[a] c d] c',['response','issuer','person','role','content_family','bindings','required_sign','reference'],
        'この反応活動は、指定された同じ出所・本人・立場・閉じた内容関数・引数列・要求極性の要求への応答として位置付けられている。別の要求への応答や単なる同時発生とは区別する。活動構成上の対応であり、要求の存在・反応の実行・受諾や拒否の向きは別に確認する。'),
}
MEANINGS={
    'r33s':'同じ本人・立場・政治的共同体・基準について、人aa、共同体成員h237c、役割保持hzwn、市民の立場h244gを結ぶ。官職への任用hzxfや職務委託cfを市民一般の条件にしない。',
    'r33t':'同じ本人・納付行為・受取先・価値媒体にrfaの移転tiと媒体の受容tjを適用する支払い内容。受取先は本人とは別であり、特定の金額・通貨や要求の正当性は含めない。',
    'r33u':'本人・納付行為・受取先・価値媒体の正確な四個体列から、同じr33tの支払い内容を構成する閉じたアダプター。長さ・位置の違いを許さない。',
    'r33v':'同じ出所が同じ本人に同じ市民の立場で、同じ納付行為・受取先・価値媒体のr33uを正極性で要求する。要求時に支払い内容を実行せず、納付済み・本人の同意・正当性を導かない。',
    'r33w':'同じ市民r33sと共同体の公的賦課h244hを、その同じ賦課の対象指定h244iと納付要求r33vへ結ぶ。賦課の対象と要求内容に別の本人・行為・受取先・媒体を使わない。',
    'r33x':'基準時に同じ納付要求r33vがあり、その同じ要求への応答h244kとして本人がこの反応活動を評価点で実行し、同じ支払い内容に負極性の実践的方針h244jを取る。拒否という読みであり、未払い・支払不能・別の要求への応答だけでは成立しない。拒否後の実際の不払いも要求しない。',
    'r33y':'出所・本人・市民の立場・納付行為・受取先・媒体・反応の正確な七個体列と固定基準から、同じ拒否内容r33xを構成する。段階1の閉じた対象として引用でき、列の不足・余分を拒否する。',
    'r33z':'同じ出所から同じ本人・市民の立場へ、同じ要求と同じ反応のr33yを負極性で要求する内容。拒否してはならないという規範の構成であり、拒否する物理的能力の不在・現実の無拒否・納付済み・要求の正当性を意味しない。',
}
LIMITS=[
    'u0012[2513,2770)の市民の例の前半に向けた依存群。全文の主張にはまだ統合せず、新しい文単位・全単位の意味確認文字数は加算しない。批判の評価、一般的反抗の可能性、処罰可能性、sogarと全文帰属は残る。',
    'Bürgerは政治的共同体の成員として共同の規律・負担に関わる立場と読む。官吏への任用や現代の国籍・選挙権を要求しない。Abgabenは公的賦課の金銭・現物等の給付負担とし、原文にない金額・税目・期限を補わない。',
    'auferlegtenは同じ本人・立場・納付行為・受取先・媒体を指定した公的な負担の賦課と、その内容への要求を結ぶ。賦課の対象を批判する後続節でも同じ賦課を追跡できるよう、対象個体と移転行為を分ける。',
    'kann sich nicht weigernは拒否してはならないという規範的な読みの候補としてr33zを準備する。要求があることから拒否禁止を自動的に導く規則は追加せず、原文の内容として別に結ぶ必要がある。',
    '拒否は同じ要求への応答として不履行の実践的立場を取ることとする。未払い・支払能力の不足・単なる内心の希望や予測から拒否を推定しない。発話に限定せず、行動上の拒否も含み得る。拒否した後に要求どおり支払う場合も排除しない。',
    'r33zは一つの反応内容への拒否禁止を構成する。本文統合では、同じ要求への候補反応h244kの全範囲へ適用し、現に拒否した反応だけを選んだり、特定の一活動だけを禁止したりしない。',
    '支払い内容は価値媒体の移転であり、命令の承認や道徳的賛同とは分ける。公的負担の正当性や全市民の実際の義務を独立に証明したとはしない。意味判断は全文への接続と通読の後に行う。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    text='d r33s[person a role a community a reference d] c['+both('k aa[v person]',
        'k h237c[v person v community v reference]','k hzwn[v person v role v reference]',
        'k h244g[v role v community v reference]')+'].\n'
    text+='d r33t[person a transfer a receiver a medium a] e[b point[k rfa[v person v receiver v transfer v medium v point p ti p tj]]].\n'
    names=('person','transfer','receiver','medium')
    text+='d r33u[bindings j[a]] e[b point['+bind(names,'t[k r33t['+' '.join('v '+n for n in names)+']][v point]')+']].\n'
    text+='d r33v['+FIELDS+' reference d] c[k h7k[v issuer v person v role r[p r33u] '+PAYMENT+' '+TRUE+' v reference]].\n'
    text+='d r33w[levy a community a '+FIELDS+' reference d] c['+both(
        'k r33s[v person v role v community v reference]', 'k h244h[v levy v community v reference]',
        'k h244i[v levy '+ARGS+' v reference]', 'k r33v['+ARGS+' v reference]')+'].\n'
    text+='d r33x['+FIELDS+' response a reference d] e[b point['+both(
        'k r33v['+ARGS+' v reference]',
        'k h244k[v response v issuer v person v role r[p r33u] '+PAYMENT+' '+TRUE+' v reference]',
        't[k zzq[v person v response]][v point]',
        'k h244j[v person v response r[p r33u] '+PAYMENT+' '+FALSE+' v point]')+']].\n'
    names=(*NAMES,'response')
    text+='d r33y[bindings j[a] reference d] e[b point['+bind(names,
        't[k r33x['+' '.join('v '+n for n in names)+' v reference]][v point]')+']].\n'
    text+='d r33z['+FIELDS+' response a reference d] e[b point[k h237z[v issuer v person v role r b[p r33y] l[a]['+' '.join('v '+n for n in names)+'] v reference '+FALSE+' v point]]].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['aa','h237c','hzwn','rfa','ti','tj','h7k','zzq','h237z']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS)) & set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
                for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='civic_levy_payment_requirement_and_distinct_refusal_response',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
