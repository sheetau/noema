"""Connect a specified coherence requirement and the final paragraph sentence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_spiritual_guardians import quant
from scripts.compose_irrational_perpetuation import CODE

PARENT='examples/v016/kant-unrestricted-scholarly-freedom.noema'
PARENT_BASIS='data/unrestricted-scholarly-freedom-basis-v1.json'
DEPENDENCY='data/spiritual-guardians-basis-v2.json'
FULL='examples/v016/kant-guardian-irrationality.noema'
CORE='examples/v016/guardian-irrationality-core.noema'
BASIS='data/guardian-irrationality-basis-v1.json'
ANNOTATIONS='data/guardian-irrationality-identifiers-v1.json'
PRIMITIVES={
    'h253y':('[a a '+CODE+' d] c',['standard','requirement','condition','reference'],
        '同じ整合性基準のこの要件を満たす条件は、指定された閉じたNoema内容関数が表す条件である。対象内容の関数へ渡すのと同じ順序の個体列・固定基準をこの条件関数にも渡し、対象を適用する構成での条件充足として読む。単なる要件の呼称ではなく条件内容の指定であり、適用の有無と肯否の評価はh253s/tで別に結ぶ。条件記述を引用しただけで現在の世界に実行しない。'),
    'h253z':('[a d] a',['community','reference'],
        '同じ政治的共同体と固定基準について、この議論でVolkとして指す人々の集団。同じmpとh237cの全成員の過不足・非空性はr45dで別に要求する。読者世界全体や一教区の会衆を指す参照ではない。'),
    'h254a':('[a d] a',['community','reference'],
        '同じ共同体・固定基準のもとで、検討する未成熟要求方針の規範的な出所。方針の内容を固定する参照であり、現に命令した者がいること、著者が命令者であること、特定の教会・君主・国家であることは追加しない。'),
    'h254b':('[a d] a',['community','reference'],
        '同じ共同体・固定基準の宗教的な教えと実践を評価する合理的整合の基準。指導を担う役割と本人に求める判断能力を両立させるという採用読解の観点を含む。具体的な必要条件をh253yとr45wで指定し、名前だけの基準で評価を済ませない。'),
    'h254c':('[a d] a',['community','reference'],
        '同じ基準で適用する、判断を導く役割の本人に自立的な理解力使用の不能を要求しないという整合性要件。条件内容はr45wの閉じた記述に結ぶ。この参照だけではその条件や評価結果を肯定しない。'),
    'h254d':('[] a',[],'固定原文kant-1784:u0012[5022,5190)、Denn daß die Vormünderからhinausläuft.までの第五段落最終文全体。'),
    'h254e':('[] a',[],'同じ最終文の[5079,5092)、selbst wiederという、他者を導く役割の本人自身を未成熟要求の対象として取り立てる箇所。過去に成熟していた人の再転落の報告ではない。'),
}
MEANINGS={
    'r45v':'同じ出所・人民・共同体・固定基準の宗教上の全後見役r45qについて、同じ本人と役割にr45gの未成熟要求がないという条件内容。指導の役割を維持しつつ本人に通常の自立的理解力行使の不能を要求しない、という整合性要件の具体化。実際の本人の能力、要求の正当性、他の全行為への許可をこの条件に含めない。',
    'r45w':'出所・人民・共同体の正確な三個体列と固定基準からr45vの条件内容を作る。評価対象r45sと同じ引数順で条件を解釈でき、段階2で引用できる。',
    'r45x':'同じ人民の完全さr45dと宗教上の後見役の非空性を固定基準で要求し、指定の整合性基準・要件をr45wの具体的条件へ結ぶ。同じr45s方針についてその要件が適用され負極性のみで判定されることと、r45uの方針評価・同じ共同体での不合理な内容の持続への帰結を結ぶ。別要件の失敗だけでこの読みの評価を代用しない。条件や方針の現実の実施は引用から導かない。',
    'r45y':'第五段落で啓蒙の制限を議論する同じ公衆に対応する政治的共同体h227aを受け、その人民・検討方針の出所・整合性基準・具体的要件を同じ固定基準で供給し、r45xを述べる最終文内容。国名を補わず、公衆と政治的共同体を同一視しない。',
    'r45z':'人民・共同体・役割・事柄・本人の正確な五個体列について、同じ段落で指す人民と共同体に一致し、最後の本人が同じ役割・事柄の宗教上の後見役r45qである範囲内容。自己取り立ての対象を導かれる相手へすり替えない。',
    'r452':'r45zと同じ五個体列の最後の本人へ、同じ共同体の同じ検討出所から同じ役割で未成熟を要求するr45gの内容。取り立ての焦点であり、外側で本人が現に未成熟であることや著者の要求を断言しない。',
    'r453':'最終文r45yを同じ著者・第五段落の文脈へ帰属し、h224sで宗教上の指導者本人が未成熟要求の対象となる取り立てを、同じ範囲と焦点の五個体列で結ぶ。Dennを最終文から先行する無制限の公的自由の文への理由提示udに接続する。本文順序は前文から最終文であり、理由の向きと逆になる。内容の真理や理由の客観的十分性を帰属から導かない。',
}
LIMITS=[
    'u0012[5022,5190)146非空白文字。Vormünderは同じ政治的共同体の人民の宗教上の指導者で、sgの正しい事柄・人の引数順を使うr45qを採用する。旧r45e/h/i/k/pは履歴として保持し新文では使わない。',
    '不合理の具体的評価基準として、他者の判断を導く役割の本人に、自立的な理解力使用の不能を要求しないという整合性要件r45v/wを明示する。これは採用する評価解釈であって、カントが原文にない別の命令を発したという主張ではない。全後見役の現実の成熟、能力不足者が役職を持てないという事実法則も追加しない。',
    '要件の条件内容h253y、対象への適用h253s、負極性のみの判定h253tを同じ要件と方針へ結ぶ。合理性の一般的な決定手続や、原著者の判断の客観的正当性を証明することを翻訳の条件にはしない。',
    'Volkは同じ段落の政治的共同体の全成員。h234tの議論対象公衆に対するh227aの共同体を参照し、読者世界や教区会衆との同一視、特定国家の同定、全国家で同じ人々という読みを避ける。本文で既に使う固定基準h232vと提示文脈h232oを区別する。',
    '要求の出所h254aは検討される規範内容の参照であり、命令の実施者や歴史的な発令事実を捏造しない。本人の未成熟bfを要求する内容を評価の対象とし、本人の未成熟や著者の是認を事実へ昇格させない。',
    'selbst wiederは他者を導く本人も依存を要求されるという役割上の反転を伴う自己取り立てと読む。h224sの同じ五個体列の最後を本人に固定し、範囲r45zと要求焦点r452へ結ぶ。過去に成熟していた履歴、時間的な再発、原文にない比較対象の未成熟の事実は追加しない。',
    '複数形の不合理は、同じ共同体の宗教的な教え・実践の全関連定式化のうち固定基準時に不合理と評価する範囲。r45m/n/oを使い各対象の持続を保つ。一つだけ又は毎時点で別の内容が残ればよいという条件へ弱めない。原文の複数形は種類全体への一般化とし固定件数を加えない。',
    '永続化は同じ候補履歴の基準以後全体での社会的な維持rca。履歴の完全さは解釈入力の責任で、短期観測を未来全体へ置き換えない。履歴の終点の不在や数値時間の非有界性、個人の不死は補わない。',
    'hinausläuftは方針の適用・維持が指定の持続に至る因果的帰結として読む。h253xは同じr45s方針とr45o結果の段階2記述・正確な束縛を結ぶ。単なる同時成立や形式的含意へ置換せず、全背景での唯一原因性も追加しない。',
    'Dennはこの不合理とその帰結を、前文の学識者としての無制限の自由を支える理由として著者が提示すること。客観的な証明や因果作用は要求しない。理由提示、自己取り立て、全文主張をそれぞれ帰属し、引用を外側で実行しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependency():return load_catalog(ROOT,DEPENDENCY)


REF='k h232v[]'
COMMUNITY='k h227a[k h234t[k h232o[]] '+REF+']'
def supplied(symbol):return 'k '+symbol+'['+COMMUNITY+' '+REF+']'


def definitions():
    fields='source a people a community a reference d';args='v source v people v community v reference'
    guardian='k r45q[v person v role v people v community v matter v reference]'
    norm='t[k r45g[v source v person v role v reference]][v point]'
    text='d r45v['+fields+'] e[b point['+quant(('person','role','matter'),'y['+guardian+'][u['+norm+']]')+']].\n'
    text+='d r45w[bindings j[a] reference d] e[b point['+bind(('source','people','community'),'t[k r45v['+args+']][v point]')+']].\n'
    payload='v standard v requirement r c[p r45s] l[a][v source v people v community] v reference '
    text+='d r45x[source a people a community a standard a requirement a reference d] e[b point['+both(
        'k r45d[v people v community v reference]',quant(('person','role','matter'),guardian,'g'),
        'k h253y[v standard v requirement r c[p r45w] v reference]',
        'k h253s['+payload+']','k h253t['+payload+FALSE+' v point]','u[k h253t['+payload+TRUE+' v point]]',
        't[k r45u[v source v people v community v standard v reference]][v point]')+']].\n'
    values=' '.join((supplied('h254a'),supplied('h253z'),COMMUNITY,supplied('h254b'),supplied('h254c'),REF))
    text+='d r45y[] e[b point[t[k r45x['+values+']][v point]]].\n'
    members=('people','community','role','matter','person')
    scope=both('e[v community]['+COMMUNITY+']','e[v people]['+supplied('h253z')+']',
        'k r45q[v person v role v people v community v matter '+REF+']')
    text+='d r45z[bindings j[a]] e[b point['+bind(members,scope)+']].\n'
    focus='t[k r45g[k h254a[v community '+REF+'] v person v role '+REF+']][v point]'
    text+='d r452[bindings j[a]] e[b point['+bind(members,both(scope,focus))+']].\n'
    author,ctx='k wa[]','k h232o[]';whole='r d[k r45y[]]'
    claims=['k h236i[k h254d[] '+author+' '+whole+' '+ctx+']',
        'k h224s[k h254e[] '+author+' '+whole+' r d[p r45z] r d[p r452] '+ctx+']',
        'k ud['+author+' i[node a][e[v node][k h254d[]]] k h253m[] '+ctx+']',
        'k ue[k h253m[] k h254d[] '+ctx+']']
    nodes=('h253m','h254d','h254e')
    claims+=['u[e[k '+a+'[]][k '+b+'[]]]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    text+='d r453[] c['+both(*claims)+'].\n'
    return text


def build():
    old,lib=parent(),dependency();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    # Only corrected live dependencies enter the new manuscript.
    for d in closure(lib.document,['r45q','r45s','r45u']):
        n=d['name'];previous=old.entries.get(n)
        if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r453',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='guardian_irrationality_and_perpetuation_final_sentence',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(lib.source_sha256)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/unrestricted-scholarly-freedom-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
