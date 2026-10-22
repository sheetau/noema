"""Generalize the liberty pattern to government institutions and a common stance."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import quantify
from scripts.compose_all_offered_freedoms import CANDIDATES,COMPARISONS

PARENTS=('data/freedom-ethos-basis-v1.json','data/public-offers-sentence-basis-v1.json')
LIBRARY='examples/v016/shared-liberty-policy.noema';BASIS='data/shared-liberty-policy-basis-v1.json'
CONTENT='i c[e]'
FRAME=('government','rulingoffice','community','group','topic')
CLERICS=('person','office','church','creed','subject','scholar')
NAMES=('person','activity','scholar','audience','church','creed','subject')
MEANINGS={
 'r556':'同じ政府の公的活動r5zkが、同じ本人の宗教的自己選択r5vyへ介入する。能動的な行為者はr5zk内の人であり、政府組織をdfの人へ代入しない。政府の別の活動や別の宗教主題を流用しない。',
 'r557':'同じ本人の宗教的選択候補について、その政府からのr5v2の両方向許可・非指図と、同じ政府の公的活動r556による介入の不在を要求する。個人の統治者による非介入だけでは足りない。',
 'r56a':'非空の全対象集団と同じ宗教主題について、r5v5の候補非空・全評価を保ち、全成員の全宗教的選択にr557の政府側の自由を要求する。現在自由な候補だけに範囲を狭めない。',
 'r56b':'同じ政府と共同体のr5zj、公的意思決定役職h256p、非空の全員人間の集団r5tyを結び、その成員と同じ最高統治職の管轄下の人々h26hiを正確に一致させる。君主一人による保持や君主の功績を求めず、政府組織も人へ分類しない。',
 'r56c':'同じ聖職者・発表候補・職務・二項目列・比較内容をr54n/r54mへ結ぶ。公的自由の出所を明示された同じ政府に固定し、h247bの別の出所から許可を借りない。職務義務の出所は全出所のまま保ち、政府だけへ縮めない。',
 'r56d':'同じ聖職者について非空のr55a候補を要求し、全活動・公衆・任意の有限判断列・洞察列の該当候補にr56cを適用する。政府を渡す以外の発表内容・職務条件は既存定義を保持する。',
 'r56e':'同じ政府の同じ管轄下の全聖職者の六対象について、r54yで限定した同じ先行群の全候補へr56dを要求する。信条比較の呼称を確認し、同じ教会・信条・主題・基準へ閉じる。',
 'r56f':'同じ本人の非空のr55e公的提示候補の全てについて、その同じ政府がr37cの自由を認める。教会や採用信条を他者の必須条件にしない。',
 'r56g':'同じ管轄下の人々からr55jの先行聖職者群を除き、全員についてr55hの全職務による無制約を条件に、同じ政府のr56fの自由を要求する。無制約から自由を論理的に導くのではなく方針の条件として記述する。',
 'r56h':'同じ政府・最高統治職・共同体・全対象集団・宗教主題・固定基準で、r56bの設定とr56a/r56e/r56gの全宗教的自己選択・公的提示の自由を同じ評価点へ結ぶ。個人と組織の規範を自動的に同一視せず、政府の公的介入を明示する。',
 'r56i':'固定基準においてr56bの政府・管轄・集団が成立し、同じ主題が宗教領域h26j7である設定。自由政策の現在の実現、支持者の態度、君主の思想・功績を比較範囲の資格にしない。',
 'r56j':'同じ固定基準の全政府・職・共同体・集団・宗教主題の組について、r56iの適格設定であれば同じ組のr56hの自由があるという共通方針内容。適格性は固定基準、自由の成立は内容の評価点で調べる。',
 'r56k':'同じ固定基準の閉じた呼称でr56jを閉じた段階2の共通内容。保持者や保持者がいる国をこの引用の中へ挿入せず、全員が同じ方針内容を共有できる。',
 'r56l':'固定基準に少なくとも一つr56iの適格設定がある。空の比較範囲だけを自由の精神への支持とせず、政策の実現自体は要求しない。',
 'r56m':'同じ本人が人で、基準の呼称を確認し、r56lの非空の対象範囲を持つ同じr56jの自由方針をh26pgで好ましく支持している。支持時に政策内容を実行せず、支持者自身の政府が自由を実現したことや君主制であることを要求しない。',
 'r56n':'同じ固定基準の共通方針に向けたr56mの態度を人物性質にする。元と国外の異なる人へ同じ性質を渡せる。「この精神」の照応に共有する内容であり、共有されたことや伝播の発生は別に構成する。',
}
LIMITS=[
 'u0015第三文の精神の内容を、先行の宗教的自己選択・公的提示の自由を同じ管轄の人々へ認める一般方針への肯定的な支持と読む。前回r555の特定君主例への態度をそのまま全文へ採用せず、政府組織に相対的な同じ自由の型を全適格設定へ一般化した。',
 '政府はr5zjの公的組織であり、役職はh256p、管轄下の人はh26hiを用いる。h26hiが最高統治職への制度的服属を指定し、非空集団により空の職務分類だけでは満たさない。単独の君主、政府を人として行為させること、自由主義的政府だけへの限定を加えない。',
 '適格範囲は固定基準の全政府・職・共同体・全対象集団・宗教主題。既存の複数表記を同一化せず同じ対象へ束縛し、全候補への自由を要求する。これは明示した範囲の一般方針であり、あらゆる未来の政治形態や全人間活動の無制限な自由の記述ではない。',
 '同じ政府の宗教的自己選択の正負の許可と要求はr5v2で扱う。介入は同じ政府の公的な資格で行動する人をr5zkで結び、君主が個人的に介入していないだけの例を拒否する。評価完備性h26ndは同じ統治側と候補について引き継ぐ。',
 '公的提示の自由の出所は同じ政府へ明示的に渡す。聖職者の全職務要求、他者の全cf職務の制限不在は従来どおり全規範源を含み、政府からの要求だけへ縮めない。見解・洞察・採用信条差・審査目的・候補非空・任意有限列の範囲を保持する。',
 '共通方針の支持は規範的な賛成の態度であり、政策の実現、政策が真だという認識、実際の発話・思考・審査の成功とは別である。元と先の人の国を同じ国へ同定せず、外国の政府が支持者であるとも述べない。',
 'この一般方針への照応を本文で先行する自由の例へ結ぶ接続、社会的な取得・広がり、外的障害・格闘の必要・政府の自己誤解、auch/selbst、全文帰属・通読は残る。本文114主張と既存の意味判断分量は変更しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def av(ns):return ' '.join('v '+n for n in ns)
def af(ns):return ' '.join(n+' a' for n in ns)
def named(n):return 'k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']'
def definitions():
    choice=('government','person','community','undertaking','topic');f=af(choice)+' reference d';a=av(choice)+' v reference'
    role='k h26hn[v person v community v reference]'
    binding='l[a][v person v community v undertaking v topic '+role+']'
    text='d r556['+f+' activity a point d] c['+both('k r5zk[v activity v government v point]',
        'k h26ho[v activity v person r b[p r5vy] '+binding+' v reference v point]')+'].\n'
    candidate='k r5vw[v person v undertaking v topic v reference]'
    text+='d r557['+f+' point d] c['+both(candidate,'k r5v2['+a+' v point]',
        'u[g activity a[k r556['+a+' v activity v point]]]')+'].\n'
    member='k h246c[v group v person v reference]'
    text+='d r56a[government a group a community a topic a reference d] e[b point['+both(
        'k r5v5[v government v group v community v topic v reference v point]',
        'f person a[f undertaking a[y['+both(member,candidate)+'][k r557['+a+' v point]]]]')+']].\n'
    under=both('k aa[v person]','k h26hi[v person v rulingoffice v community v point]')
    text+='d r56b[government a rulingoffice a community a group a reference d point d] c['+both(
        'k r5zj[v government v community v point]','k h256p[v rulingoffice v government v point]',
        'k r5ty[v group v reference]','f person a[e['+member+']['+under+']]')+'].\n'
    t='k r536[k r543[v judgments] k r543[v insights] v comparisons]';b='l[a]['+av(NAMES)+']'
    cases='i[at d][k h26o4[v person '+t+' '+b+' v reference v anchor v at]]'
    pf='government a '+af(NAMES)+' office a judgments j[a] insights j[a] reference d anchor d comparisons '+COMPARISONS
    text+='d r56c['+pf+'] c['+both('k r54n[v person v office v church v creed v subject v scholar v reference v anchor]',
        'k r54m['+av(NAMES)+' v government v office v reference v anchor k r543[v judgments] k r543[v insights] v comparisons '+cases+']')+'].\n'
    local='government a '+af(CLERICS)+' reference d anchor d comparisons '+COMPARISONS
    eligible='k r55a['+av(NAMES)+' v judgments v insights v reference v anchor v comparisons]'
    granted='k r56c[v government '+av(NAMES)+' v office v judgments v insights v reference v anchor v comparisons]'
    text+='d r56d['+local+'] c['+both(quantify(CANDIDATES,eligible,'g'),quantify(CANDIDATES,'y['+eligible+']['+granted+']'))+'].\n'
    scope=both('k h26hi[v person v rulingoffice v community v point]',
        'k r54y['+av(CLERICS)+' v reference v point]')
    comp='k r546['+' '.join(named(n) for n in ('church','creed','subject','reference'))+']'
    valid=both(*('e[s['+named(n)+']][v '+n+']' for n in ('church','creed','subject','reference')))
    text+='d r56e[government a rulingoffice a community a reference d point d] c['+quantify([(n,'a') for n in CLERICS],
        'y['+scope+']['+both(valid,'k r56d[v government '+av(CLERICS)+' v reference v point '+comp+']')+']')+'].\n'
    eligible='k r55e['+av(NAMES[:4])+' v judgments v insights v reference v point]'
    target='k r53w[k r543[v judgments] k r543[v insights]]'
    granted='k r37c[v government v person v scholar '+target+' l[a]['+av(NAMES[:4])+'] v reference v point]'
    text+='d r56f[government a person a scholar a reference d point d] c['+both(quantify(CANDIDATES,eligible,'g'),quantify(CANDIDATES,'y['+eligible+']['+granted+']'))+'].\n'
    scholar='k h247d[v person v reference]'
    other=both(under,'u[k r55j[v person v reference v point]]','k r55h[v person '+scholar+' v reference v point]')
    text+='d r56g[government a rulingoffice a community a reference d point d] c[f person a[y['+other+'][k r56f[v government v person '+scholar+' v reference v point]]]].\n'
    fields=af(FRAME)+' reference d';args=av(FRAME)+' v reference'
    text+='d r56h['+fields+'] e[b point['+both('k r56b[v government v rulingoffice v community v group v reference v point]',
        't[k r56a[v government v group v community v topic v reference]][v point]',
        'k r56e[v government v rulingoffice v community v reference v point]',
        'k r56g[v government v rulingoffice v community v reference v point]')+']].\n'
    text+='d r56i['+fields+'] c['+both('k r56b[v government v rulingoffice v community v group v reference v reference]',
        'k h26j7[v topic v reference]')+'].\n'
    text+='d r56j[reference d] e[b point['+quantify([(n,'a') for n in FRAME],
        'y[k r56i['+args+']][t[k r56h['+args+']][v point]]')+']].\n'
    text+='d r56k[reference i[d]] '+CONTENT+'[o a[r c[p r56j]][v reference]].\n'
    text+='d r56l[reference d] c['+quantify([(n,'a') for n in FRAME],'k r56i['+args+']','g')+'].\n'
    text+='d r56m[holder a reference d point d] c['+both('k aa[v holder]',
        'e[s[k h223h[v reference]]][v reference]','k r56l[v reference]',
        'k h26pg[v holder k r56k[k h223h[v reference]] v point]')+'].\n'
    text+='d r56n[reference d] h[a] e[i[holder a][b point[k r56m[v holder v reference v point]]]].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    roots=(['h26pg','r55j','r55h','r55a','r55e','r54n','r54m','r54y','r546','r543','r536','r53w','r37c','h26o4','h247d','h26hi','h223g','h223h'],
        ['r5zk','r5zj','r5vw','r5vy','r5v2','r5v5','h26ho','h26hn','h246c','h256p','r5ty','aa','h26j7'])
    for c,rs in zip(sources,roots):
        for d in closure(c.document,rs):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+definitions())
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='shared_government_relative_liberty_policy_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
