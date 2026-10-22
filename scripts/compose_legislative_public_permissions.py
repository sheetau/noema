"""Bind all subjects and all legislative public-use candidates to permission."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind
from scripts.compose_clerical_duty_scope import quantify
from scripts.compose_legislative_thoughts import NAMES

PARENT='data/religious-emphasis-sentence-basis-v1.json'
DEPENDENCIES=('data/frank-legal-criticism-basis-v1.json','data/legislative-thoughts-basis-v1.json')
LIBRARY='examples/v016/legislative-public-permissions.noema';BASIS='data/legislative-public-permissions-basis-v1.json'
CODE='i b[h[j[a] d] e]';CRITERIA='i[h[a] a]'
PUBLIC=('person','activity','scholar','audience')
FRAME=('ruler','people','community','baseline','oldform','standard')
OFFER=(*PUBLIC,*FRAME)
ROWS=[('activity','a'),('audience','a'),('people','a'),('baseline','a'),('oldform','a'),('standard','a'),('thoughts','j[a]')]
CRITICAL=ROWS+[('criticisms','j[a]'),('criteria',CRITERIA)]
LOCAL='ruler a community a person a scholar a reference d anchor d'
LARGS='v ruler v community v person v scholar v reference v anchor'
PRIMITIVES={
 'h26tn':('[a a d] c',['activity','target','reference'],
   'この理性使用活動は、同じ固定基準で指定対象について考察・検討・論議する企てとして構成されている。対象の名を偶然含むだけ、別の対象についての活動とは分ける。主張だけでなく問い・検討・留保も扱え、よりよい案への賛成、実行済み、本人の現在の信念、許可の成立や内容の真理を分類条件にしない。対象が誰のどの立法範囲に属すかは合成側で確認する。'),
}
MEANINGS={
 'r6da':'正確な本人・活動の二対象列について、本人による同じ活動の実行cgと、その活動で本人の理解力を使うab/acを結ぶ内容。公的分類は候補側で別に確認し、実行内容を引用したまま許可へ渡す。',
 'r6db':'同じ本人・活動・学識者の立場の公的理性使用r2ziが、同じ統治者・共同体のr6ckの立法範囲に属する法を検討対象h26tnとする候補である。改善案の肯定、保持判断、既に発表したことを要求せず、思想の提示や批判だけに一般の使用を狭めない。',
 'r6dc':'同じ統治者から同じ本人の学識者の立場へ、r6daの同じ本人・活動による自分の理性使用実行についてr37cの積極的許可と反対要求の不在を要求する。別の規範源の許可を借りず、現実の実行や不実行への許可を導かない。',
 'r6dd':'同じ本人・学識者・統治者・共同体・基準に少なくとも一つr6dbの候補があり、全活動の該当候補へr6dcの許可を要求する。現在の信念や実行を分類に追加しない。',
 'r6de':'任意有限の思想列をr543で閉じ、正確な列名r544と非空性を確認して、同じ十対象・基準・起点でr6cyの公的思想提示にr547の実行候補があることを確認する。保持判断・公的提示は候補の内部にあり、現在の事実へ移さない。',
 'r6df':'r6deと同じr543の思想列・r6cyの目標・十対象列・基準を、同じ統治者が同じ本人の学識者の立場へ許すr37c。許可の評価点と候補比較の固定起点を区別する。',
 'r6dg':'同じ本人について、活動・公衆・法の人民・比較元法・定式・評価観点・任意有限の思想列を全称で扱い、非空のr6de候補の全てにr6dfを要求する。既知の列・真の見解・現在許された発表に範囲を狭めず、法の人民を臣民の集団と同一化しない。',
 'r6dh':'任意有限の思想列・批判列と閉じた評価条件選択、固定した履歴と起点の名前を、同じr6c7の複合提示へ組み込む。二列の正確さ・非空性と二状況の名前を確認し、r547で同じ十対象と基準の候補を調べる。制定済みの起点は将来の発表点へ動かさない。',
 'r6di':'r6dhと同じ複合提示の引用・二列・条件選択・履歴・起点・十対象列・基準を、同じ統治者が同じ本人の学識者の立場へ許すr37c。思想のみへの許可から批判付きの許可を補わない。',
 'r6dj':'r6dgの全候補引数に、任意有限の批判列と全閉じた評価条件選択の記述を加え、非空のr6dh候補の全てへr6diを要求する。特定の条件一つ・既知の批判だけへ範囲を限定しない。条件選択は内容をNoemaで記述した型付き関数であり、外部の題名だけではない。',
 'r6dk':'同じ統治者・共同体の全臣民集団r6boを固定し、全成員について同じ学識者の立場h247d/cdでr6dd・r6dg・r6djの三つの許可を同時に要求する政策内容。一般の理性使用・思想のみ・率直な批判付きの各対象を別々に保持し、三つの単独行為の実行や政策の現実の成立は引用だけから導かない。',
 'r6dl':'同じ統治者・共同体・全臣民集団・基準・履歴・起点の閉じた呼称から、r6dkの全許可方針を閉じた段階2の内容として作る。危険や洞察で参照する方針はこの同じ内容へ結べる。呼称の具体的な本文束縛と全文帰属は後で行う。',
}
LIMITS=[
 'u0016第二文seinen Unterthanen zu erlaubenからder Welt öffentlich vorzulegenまでの許可を、同じ国家元首の立法に関する一般の公的理性使用、改善についての思想提示、既存法への率直な批判を伴う思想提示の三対象へ分けて構成する。in Ansehung seiner Gesetzgebungの範囲を保ち、あらゆる私的行為や法の実行・反乱への許可とはしない。',
 '許可は同じ統治者を出所とするr37cの積極的許可と反対要求の不在である。権利の道徳的正当性、物理的な無妨害、実際の発表、内容の真理、発表しないことへの許可は別である。別の学識者規範源や政府の許可を借りない。',
 '全臣民は同じ統治者・共同体のr6boで過不足なく一致させ、非空・人間性を要求する。各法の規範を受ける人民は発表候補ごとに量化し、臣民の集団と同一視しない。同じ本人の学識者の立場はh247dとcdで固定する。',
 '一般の使用はr2ziと同じ立法対象についての企てを分類し、実行時には同じ活動で自分の理解力を用いる。問いや検討を全て肯定判断へ狭めない。思想と批判の側では、非空の任意有限列と全評価観点・条件選択を量化し、完成した改善案や成功した批判だけを選ばない。',
 '思想・批判の候補はr547と既存h26o4の全関連比較範囲で実行内容を満たす候補があることとする。基準時の制度的事情の下での規範対象の実行候補であり、許可・職務要求の履行・物理的能力・現実の未来への到達・現在の保持判断を資格にしない。現実の発表がない者や誤った見解も範囲へ残す。',
 'h26o4の全範囲供給と、h26tlの発表に関係する全評価範囲は解釈入力の責任を保つ。有限標本でその現実の網羅性を証明しない。全列と全コードの量化を有限評価器で実行できたことにもせず、診断では置き換えた標本範囲と下位境界を明記する。',
 '同じ履歴・起点は政策の候補比較に固定し、制定済み法の採択もその起点より前へ結ぶ。政策の許可を評価する点と、発表を実行する候補点は別である。一般・思想のみ・批判付きの許可を連言にし、一方への許可から他方を論理的に推論しない。',
 '国家元首のDenkungsart、啓蒙を支持するというdie erstereへの照応、宗教領域からの拡張とselbst、危険と洞察、実例・尊敬する君主の先行者不在、Aber/sogar、全文帰属と通読は残る。今回の依存群の検査を原文全文の意味判断へ換算しない。',
]
def av(ns):return ' '.join('v '+n for n in ns)
def af(ns):return ' '.join(n+' a' for n in ns)
def binding():return 'l[a]['+av(NAMES)+']'
def target(critical=False):
    if not critical:return 'k r6cy[k r543[v thoughts]]'
    return 'k r6c7[k r543[v thoughts] k r543[v criticisms] v criteria k h223h[v history] k h223h[v anchor]]'
def fields(critical=False):return af(OFFER)+' thoughts j[a]'+(' criticisms j[a] criteria '+CRITERIA if critical else '')+' reference d anchor d'+(' history d' if critical else '')
def args(critical=False):return av(OFFER)+' v thoughts'+(' v criticisms v criteria' if critical else '')+' v reference v anchor'+(' v history' if critical else '')
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    own='g faculty a['+both('k ab[v faculty v person v point]','k ac[v person v faculty v activity v point]')+']'
    text='d r6da[bindings j[a] reference d] e[b point['+bind(('person','activity'),both('k cg[v person v activity v point]',own))+']].\n'
    general='person a activity a scholar a ruler a community a reference d';ga='v person v activity v scholar v ruler v community v reference'
    text+='d r6db['+general+'] c['+both('k r2zi[v person v activity v scholar v reference]',
        'g law a['+both('k r6ck[v ruler v community v law v reference]','k h26tn[v activity v law v reference]')+']')+'].\n'
    text+='d r6dc['+general+' point d] c[k r37c[v ruler v person v scholar r b[p r6da] l[a][v person v activity] v reference v point]].\n'
    candidate='k r6db['+ga+']'
    text+='d r6dd['+LOCAL+' point d] c['+both('g activity a['+candidate+']','f activity a[y['+candidate+'][k r6dc['+ga+' v point]]]')+'].\n'
    for eligible,grant,critical in (('r6de','r6df',False),('r6dh','r6di',True)):
        lists=('thoughts','criticisms') if critical else ('thoughts',)
        valid=[both('k r544[v '+n+']','u[e[d[v '+n+']][n p a b]]') for n in lists]
        if critical:valid += ['e[s[k h223h[v '+n+']]][v '+n+']' for n in ('history','anchor')]
        text+='d '+eligible+'['+fields(critical)+'] c['+both(*valid,'k r547[v person '+target(critical)+' '+binding()+' v reference v anchor]')+'].\n'
        text+='d '+grant+'['+fields(critical)+' point d] c[k r37c[v ruler v person v scholar '+target(critical)+' '+binding()+' v reference v point]].\n'
    for name,eligible,grant,critical in (('r6dg','r6de','r6df',False),('r6dj','r6dh','r6di',True)):
        c='k '+eligible+'['+args(critical)+']';g='k '+grant+'['+args(critical)+' v point]';rows=CRITICAL if critical else ROWS
        text+='d '+name+'['+LOCAL+(' history d' if critical else '')+' point d] c['+both(quantify(rows,c,'g'),quantify(rows,'y['+c+']['+g+']'))+'].\n'
    scholar='k h247d[v person v reference]';la='v ruler v community v person '+scholar+' v reference v anchor'
    freedoms=both('k cd['+scholar+' v reference]','k r6dd['+la+' v point]','k r6dg['+la+' v point]','k r6dj['+la+' v history v point]')
    names=('ruler','community','group');times=('reference','history','anchor')
    text+='d r6dk['+af(names)+' reference d history d anchor d] e[b point['+both('k r6bo[v ruler v community v group v reference]',
        'f person a[y[k h246c[v group v person v reference]]['+freedoms+']]')+']].\n'
    text+='d r6dl['+' '.join(n+' i[a]' for n in names)+' '+' '.join(n+' i[d]' for n in times)+'] i c[e][o a[r c[p r6dk]]['+av((*names,*times))+']].\n'
    return text

def build():
    sources=(parent(),*dependencies());roots=(('r6bo','r37c','r547','r543','r544','r2zi','h247d','cg','ab','ac'),('r6c7','r6ck'),('r6cy',))
    doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,roots):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))
    basis=dict(status='all_subjects_and_legislative_public_permissions_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
