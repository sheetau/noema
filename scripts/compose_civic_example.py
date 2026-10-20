"""Integrate the citizen's levy, refusal prohibition and qualified punishability."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_civic_levy_refusal import NAMES as PAYMENT_NAMES

PARENT='examples/v016/kant-protected-remarks.noema'
PARENT_BASIS='data/protected-remarks-basis-v1.json'
DEPENDENCIES=tuple('data/'+n+'-basis-v1.json' for n in ('civic-levy-refusal','levy-reproof','general-resistance','scandal-sanction'))
FULL='examples/v016/kant-civic-example.noema'
CORE='examples/v016/civic-example-core.noema'
BASIS='data/civic-example-basis-v1.json'
ANNOTATIONS='data/civic-example-identifiers-v1.json'
NAMES=('levy','community',*PAYMENT_NAMES)
DETAILS=('criticism','audience','criterion','standing')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
DETAIL_FIELDS=' '.join(n+' a' for n in (*NAMES,*DETAILS))+' reference d'
DETAIL_ARGS=' '.join('v '+n for n in (*NAMES,*DETAILS))+' v reference'
PAYMENT='l[a][v person v transfer v receiver v medium]'
PRIMITIVES={
    'h245d':('[a d] a',['community','reference'],
        '著者がこの共同体の市民的な負担・公的規律について、拒否の禁止と処罰の許否を述べる際に採る規範の出所。実際の賦課発令者・法典・特定裁判所や著者個人の命令行為とは別に参照する。具体的な禁止・許可や正当性はこの参照だけから導かない。'),
    'h245e':('['+'a '*8+'d] a',[*NAMES,'reference'],
        '同じ賦課・共同体・出所・本人・市民の立場・納付行為・受取先・媒体・基準の要求について、その履行を市民的な義務として重んじる際の規則。Skandalとしての評価に使う規則を同じ要求へ結び、無関係な規則を借りない。規則の厳格さ・軽視や処罰の許可は別の内容として記述する。'),
    'h245f':('[] a',[],'固定原文kant-1784:u0012[2513,2770)、Der Bürgerからbestraft werden.までの市民の一文全体。'),
    'h245g':('[] a',[],'同じ一文の[2513,2588)、市民の納付拒否の禁止を述べる第一節。'),
    'h245h':('[] a',[],'同じ一文の[2589,2770)、sogarを伴う賦課批判の処罰可能性の節。挿入箇所h245iを含む範囲の主たる処罰内容への参照。'),
    'h245i':('[] a',[],'同じ一文の[2698,2753)、das allgemeine Widersetzlichkeiten veranlassen könnteを囲む括弧による補足箇所。'),
    'h245j':('[a i c[e] i c[e] d] c',['view','left','right','reference'],
        '同じ視点・固定基準の提示上の期待比較で、左の内容記述は右と少なくとも同程度に見込まれる。hzptと同じ比較を段階2の閉じた内容に広げる。数値確率、内容の真理、実際の驚き、伝記的な内心の測定ではない。'),
    'h245k':('[a a a i d[e] a i d[e] i d[e] d] c',
        ['node','author','baseline_node','baseline','focus_node','focus','background','context'],
        '提示者が先行内容に加えて焦点内容まで成立するものとして取り立て、指定の期待背景をその焦点に付随させる。同じ閉じた内容・原文箇所・提示文脈を保持し、背景を主たる世界内容へ混ぜない。前内容の撤回、数値差、引用内容の真理は含意しない。'),
    'h245l':('[a a a i d[e] a i d[e] i[h[a a a d] e] d] c',
        ['node','author','main_node','main','aside_node','aside','assessment','context'],
        '同じ提示者が、主たる内容で用いる評価の性質を説明する補足として、別箇所の内容を結ぶ。主内容・補足・評価記述を明示し、同じ仮定・対象・様相を保持する。補足を現実の既成事実や許可を論理的に導く十分条件には変えない。'),
    'h245m':('[a a a i d[e] i d[e] d] c',
        ['node','author','prior_node','prior','current','context'],
        '同じ提示者が、役割に関わる制約を説明する先行の例に並べて、指定内容を別の立場の例として提示する。人物・役割の同一性、内容間の論理的含意、現実の実例の存在、先行例の撤回は含意しない。'),
}
MEANINGS={
    'r34p':'同じ共同体の評価規範h245dから、同じ納付要求への全候補反応h244kについて、同じ本人・立場・要求内容を保つr33yの拒否を負極性で要求する。要求対象の拒否を実行せず、現に拒否した反応だけへ範囲を縮めない。',
    'r34q':'同じ賦課・市民・納付要求・批判のr34dが評価点で成立するなら、同じ規範源h245dと同じ要求に関する義務規則h245eの下で、その本人・批判がr34oの規範的処罰可能性を持つ内容。物理的可能性や実際の処罰は加えない。',
    'r34r':'同じr34dの条件の下で、同じ批判が同じ共同体に一般的反抗を誘発し得るr34iを要求する補足内容。現実の反抗を仮定せず、同じ批判への条件付き可能性を保持する。',
    'r34s':'同じ賦課事例について、批判活動・宛先範囲・論点の条件・発言上の立場の全組へr34qを適用する。処罰が既に許されている批判だけへ対象を縮めない。',
    'r34t':'同じ賦課事例と同じ四引数の全組へr34rの補足を適用する。処罰内容と別の批判や共同体を説明しない。',
    'r34u':'固定基準h232vで全ての同じ八個体の賦課事例r33wにr34pの拒否禁止が及ぶという第一節の内容。出過ぎた批判の有無から独立する。',
    'r34v':'同じ全賦課事例にr34sの条件付き処罰可能性が及ぶ第二節の主内容。拒否の実行は条件にしない。',
    'r34w':'同じ全賦課事例にr34tの条件付き誘発可能性が及ぶ括弧の内容。処罰可能性の前件へ現実の反抗を移さない。',
    'r34x':'同じ評価点で拒否禁止r34u、条件付き処罰可能性r34v、補足の誘発可能性r34wを合わせる一文全体の内容。三内容の談話上の地位は帰属側で別に保持する。',
    'r34y':'著者が提示する同じ基準の期待比較で、第一節と焦点となる処罰内容への比較が反射的で、第一節は焦点以上に見込まれ逆は成立しないという背景。二内容の真理や数値確率は評価しない。',
    'r34z':'一文全体と各節・補足を同じ著者waと提示h232oへ帰属する。sogarの追加と期待背景、Skandal評価への括弧の説明、先行将校例への並列と本文順序を保持し、引用内容を実行しない。',
}
LIMITS=[
    'Der Bürgerは公的賦課を受ける政治的共同体の成員という一般例として、同じ賦課事例に関する条件付き全称で読む。職務委託や現代的な選挙権を市民の要件にしない。実際の賦課事例の存在をこの文の独立主張として加えない。',
    'kann sich nicht weigernは規範的な拒否禁止。未払い・不能だけを拒否とせず、同じ要求への反応として反対の実践方針を取る内容を全候補反応で禁じる。禁止の出所は本文の規範評価h245dであり、実際の発令者が追加の禁止を発令した事実とはしない。',
    'vorwitziger Tadelは、自ら評価上の立場を取り、その立場の固定した条件の不足がある批判という明示した読み。批判内容の偽、委任・許可の欠如、単なる否定文だけに置換しない。',
    'wenn節は同じ本人に同じ賦課の納付が批判時にも要求される状況を限定する。基準時の対象指定だけで済ませず、納付済み・特定の期限・実際の拒否を追加しない。',
    'bestraft werden kannは制度上の施行者・立場・措置に関する規範的可能性r34oを採る。h245dの出所を拒否禁止と共有し、現実の法令の存在・処罰の実行・物理的可能性・義務・倫理的正当性は補わない。',
    'als ein Skandalは同じ批判を、公然と示される義務規則の軽視の例として評価することを処罰の根拠にする読み。同じ賦課の義務規則h245eを渡し、別の規則の軽視や現代の報道騒動へ置換しない。1797年AA6/474は補助根拠であり当該文の唯一の語義の証明ではない。',
    '括弧内のdasはこの批判をSkandalとして扱う評価への補足説明とする。同じ批判・共同体の一般的反抗の誘発可能性を条件付きで保ち、現実の反抗を処罰許可の必要条件にしない。因果的可能性から一般法として許可を導く規則も置かない。',
    'allgemeineは固定された有限共同体の全成員に占める反抗事例の広がりと読む。全員や過半数を固定せず、納付以外の公的指図への反抗も含める。全要求記述・引数列の量化は有限の既知要求へ置換せず、有限評価拒否を保持する。',
    'sogarは拒否を禁じるだけでなく、条件に該当する批判の処罰可能性まで述べる取り立てとし、後者を前者より期待されにくい内容として提示する背景を分ける。全批判の禁止や、第一節の撤回を含めない。',
    '原文とNoemaの意味判断は明示した読みの下での通読による。有限模型の検査・型付き境界・帰属の非事実性を区別し、同義性の自動証明、現実の全対象の網羅、制度や因果の正当化とはしない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)


def quantify(names,body):
    for n in reversed(names):body='f '+n+' a['+body+']'
    return body


def definitions():
    payargs=' '.join('v '+n for n in PAYMENT_NAMES)
    target='l[a]['+payargs+' v response]'
    match='k h244k[v response v issuer v person v role r[p r33u] '+PAYMENT+' '+TRUE+' v reference]'
    ban='k h237z[k h245d[v community v reference] v person v role r b[p r33y] '+target+' v reference '+FALSE+' v point]'
    text='d r34p[community a '+' '.join(n+' a' for n in PAYMENT_NAMES)+' reference d] e[b point[f response a[y['+match+']['+ban+']]]].\n'
    antecedent='t[k r34d['+DETAIL_ARGS+']][v point]'
    permission='t[k r34o[k h245d[v community v reference] v person v criticism v community k h245e['+ARGS+'] v reference]][v point]'
    for name,result in [('r34q',permission),('r34r','t[k r34i[v criticism v community v reference]][v point]')]:
        text+='d '+name+'['+DETAIL_FIELDS+'] e[b point[y['+antecedent+']['+result+']]].\n'
    for name,target in [('r34s','r34q'),('r34t','r34r')]:
        text+='d '+name+'['+FIELDS+'] e[b point['+quantify(DETAILS,'t[k '+target+'['+DETAIL_ARGS+']][v point]')+']].\n'
    fixed=' '.join('v '+n for n in NAMES)+' k h232v[]'
    for name,target,args in [('r34u','r34p','v community '+payargs+' k h232v[]'),('r34v','r34s',fixed),('r34w','r34t',fixed)]:
        text+='d '+name+'[] e[b point['+quantify(NAMES,'y[k r33w['+fixed+']][t[k '+target+'['+args+']][v point]]')+']].\n'
    text+='d r34x[] e[b point['+both(*( 't[k '+n+'[]][v point]' for n in ('r34u','r34v','r34w')))+']].\n'
    compare=lambda a,b:'k h245j[k wa[] r c[k '+a+'[]] r c[k '+b+'[]] k h232v[]]'
    text+='d r34y[] e[b point['+both(compare('r34u','r34u'),compare('r34v','r34v'),compare('r34u','r34v'),'u['+compare('r34v','r34u')+']')+']].\n'
    a,ctx='k wa[]','k h232o[]';quote=lambda n:'r d[k '+n+'[]]'
    claims=['k h236i[k '+node+'[] '+a+' '+quote(content)+' '+ctx+']' for node,content in (
        ('h245f','r34x'),('h245g','r34u'),('h245h','r34v'),('h245i','r34w'))]
    claims+=['k h245k[k h245f[] '+a+' k h245g[] '+quote('r34u')+' k h245h[] '+quote('r34v')+' '+quote('r34y')+' '+ctx+']',
        'k h234k[k h245i[] '+a+' k h245h[] '+ctx+']',
        'k h245l[k h245f[] '+a+' k h245h[] '+quote('r34v')+' k h245i[] '+quote('r34w')+' r[p r34j] '+ctx+']',
        'k h245m[k h245f[] '+a+' k h243t[] '+quote('r324')+' '+quote('r34x')+' '+ctx+']',
        'k ue[k h244f[] k h245f[] '+ctx+']','u[e[k h244f[]][k h245f[]]]',
        'k ue[k h245g[] k h245h[] '+ctx+']','u[e[k h245g[]][k h245h[]]]','u[e[k h245h[]][k h245i[]]]']
    text+='d r34z[] c['+both(*claims)+'].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & (set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r34z',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    primitives={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='civic_levy_refusal_and_qualified_normative_sanction',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=primitives,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/protected-remarks-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
