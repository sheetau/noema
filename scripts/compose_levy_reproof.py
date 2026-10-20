"""Bind reproof of the same levy to an explicit presumptuous-standing reading."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_levy_refusal import NAMES

PARENTS=('data/protected-remarks-basis-v1.json','data/civic-levy-refusal-basis-v1.json')
LIBRARY='examples/v016/levy-reproof.noema'
BASIS='data/levy-reproof-basis-v1.json'
PRIMITIVES={
    'h244l':('[a a a d] c',['person','activity','standing','point'],
        '本人がこの活動で、指定の事柄の評価・裁定をする側としての立場を、自分から前に出て取る。単なる役割分類、他者による割当て、たまたま発言したこととは区別する。正式な官職への就任・委任・正当な権限や、その立場が不適切だという結論は含意しない。'),
    'h244m':('[a a d] j[h[a a] e]',['standing','subject','reference'],
        '同じ対象についてこの発言上の立場を取る際に、同じ固定基準で採用する評価条件の有限列。関連する事情・理由を十分検討すること、判断範囲や時機を踏まえること等の観点を明示して渡す。条件の真偽に応じて事後選択せず、職務委託や許可の不在だけを全ての批判の不適切さにしない。条件関数は同じ本人・立場を引数とし、内容の正しさや制裁の可否は別である。'),
    'h244n':('[a a a d] c',['person','activity','subject','point'],
        '本人がこの活動で、指定対象を是認できないものとして否定的に評価する立場を表す。単なる話題の言及、他人の批判の中立的な紹介、否定文という形だけとは区別する。非難される対象の実際の欠点・発言の正しさ・怒りの強さ・処罰の正当性を含意しない。'),
    'h244o':('[a a a a i[h[a a d] f] d d] c',
        ['activity','recipient','subject','criterion','message_family','reference','point'],
        '同じ提示活動で、この受け手へ、同じ対象・評価条件・固定基準を閉じた発話関数へ渡した発話を示す。既存f2の一対象束縛を二対象と明示基準へ広げた関係である。提示者・活動の生起は別に結び、発話の力は渡す関数で構成する。発話内容の真理、受け手の理解や賛同は含意しない。'),
}
MEANINGS={
    'r34a':'同じ賦課と評価条件・固定基準について、備えるべき条件の不充足r326を主張する発話を構成する。主張の力を持つことと内容の真理、実際にその発話を行うことは別である。',
    'r34b':'同じ本人の同じ生起する提示活動が、同じ固定した非空の宛先範囲の各人へ、同じ賦課・条件・基準のr34aを示し、その賦課を否定的に評価する立場h244nを表す内容。全読者世界への刊行、納付拒否、内容の真理や受け手の同意は要求しない。',
    'r34c':'同じ本人・批判活動・発言上の立場について、既存rfqを、同じ賦課・固定基準の評価条件h244mと、自分から立場を取るh244lへ適用する。少なくとも一条件の不充足があり、空列・単なる未評価・役割分類だけで出過ぎた振舞いとはしない。',
    'r34d':'同じ市民・共同体・賦課・納付内容r33wに、批判する評価点でも同じ納付要求r33vが適用されることを結ぶ。その同じ時点で、同じ賦課への批判r34bと、同じ本人・活動の出過ぎた立場の読みr34cを要求する。要求時の条件を、実際に支払ったことへ置き換えない。',
}
LIMITS=[
    'u0012[2513,2770)のvorwitziger Tadelと、同じ賦課が本人に要求される状況を結ぶ依存群。一般的反抗の誘発可能性、Skandalとしての評価と処罰可能性、sogar、文全体の帰属は未統合。新規意味確認文字数は加算しない。',
    'Tadelは同じ賦課について不充足を述べ、否定的に評価する立場を示す発言行為として読む。批判の全内容を一つの短い命題へ縮める主張ではなく、批判の評価上の論点を指定する。宛先は非空だが、公衆の全読者世界であることや刊行はこの節から要求しない。',
    'vorwitzigは、自ら評価・裁定する側として前に出る活動と、その立場を取るために採用した検討・範囲・時機等の条件の不足を結ぶ明示した読みの候補。保存済みAdelungとDWBの語義資料はこの選択の根拠であり、必要十分条件の証明や当該語の全語義ではない。',
    '旧hzbaの役割分類と実行だけの候補では、自分から前に出ることを表し切らないため、rfqへh244lを渡す。cfの委任不在、許可の不在、納付拒否、批判内容の偽、処罰可能性から不適切さを補わない。先行候補と証拠は変更しない。',
    '条件列の評価点と批判の評価点は同じにし、条件列・宛先範囲・対象指定は固定基準で保持する。具体的な条件の根拠は意味規約で明示し、反政府的な内容なら自動で条件不足と判定する規則はない。',
    'wenn sie von ihm geleistet werden sollenは、批判する評価点で同じ本人・役割・納付行為・受取先・媒体への要求が適用されるという読みの候補。原文にない日付や具体的な期限、実際の納付・未払いを加えない。全文通読で作用域を再確認する。',
    '本群は仮定内の批判を評価する内容を作る。現在その批判が起きたという独立の著者主張は追加しない。原文の次文にある学識者の批評の保護を、全批判の禁止へ撤回しない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r34a[levy a criterion a reference d] f[j s[k r326[v levy v criterion v reference]]].\n'
    text+='d r34b[person a criticism a audience a levy a criterion a reference d] e[b point['+both(
        'k dg[v criticism v point]','k f3[v person v criticism v point]',
        'g recipient a[k h6t[v audience v recipient v reference]]',
        'f recipient a[y[k h6t[v audience v recipient v reference]][k h244o[v criticism v recipient v levy v criterion r[p r34a] v reference v point]]]',
        'k h244n[v person v criticism v levy v point]')+']].\n'
    text+='d r34c[person a criticism a standing a levy a reference d] e[k rfq[v criticism v person v standing k h244m[v standing v levy v reference] p h244l]].\n'
    fields='levy a community a '+' '.join(n+' a' for n in NAMES)+' criticism a audience a criterion a standing a reference d'
    args=' '.join('v '+n for n in NAMES)
    text+='d r34d['+fields+'] e[b point['+both(
        'k r33w[v levy v community '+args+' v reference]',
        'k r33v['+args+' v point]',
        't[k r34b[v person v criticism v audience v levy v criterion v reference]][v point]',
        't[k r34c[v person v criticism v standing v levy v reference]][v point]')+']].\n'
    return text


def build():
    old,civic=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['r326','dg','f3','h6t','rfq']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(civic.document,['r33w']):
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'] and civic.entries[n]['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=civic.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & (set(old.entries)|set(civic.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
                for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_levy_reproof_and_presumptuous_standing_reading',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
