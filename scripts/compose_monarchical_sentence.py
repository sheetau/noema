"""Integrate the tenth sentence: legislative limits, comparison and grounding."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='examples/v016/kant-personal-renunciation-sentence.noema'
PARENT_BASIS='data/personal-renunciation-sentence-basis-v1.json'
DEPENDENCIES=('data/monarchical-legislation-basis-v1.json',)
FULL='examples/v016/kant-monarchical-sentence.noema'
CORE='examples/v016/monarchical-sentence-core.noema'
BASIS='data/monarchical-sentence-basis-v1.json'
ANNOTATIONS='data/monarchical-sentence-identifiers-v1.json'
FAMILY='i c[h[j[a] d] e]'
REF='k h26b7[]';CTX='k h255n[]'
FOUR_NAMES=('actor','people','community','law')
THREE_NAMES=FOUR_NAMES[:3]
NODE_INFO={
 'h26gw':([2986,3225],'第十文全体。人民自身と君主への禁止の比較と、全人民意志の統合に置かれる立法権威の根拠。'),
 'h26gx':([2986,3112],'Wasから最初のbeschließen;までの、人民自身に許されない決定は君主にはなおさら許されないという条件付き比較。'),
 'h26gy':([3113,3225],'dennから文末までの、立法権威を全人民意志の統合に基づける理由節。'),
 'h26gz':([2990,2994],'aberによる直前の本人・後代の放棄評価から政治的決定への対照。'),
 'h26g2':([2995,3007],'nicht einmalによる、人民自身でさえ許されないという比較の基準側。'),
 'h26g3':([3061,3073],'noch wenigerによる、君主にはなおさら許されないという比較の焦点側。'),
 'h26g4':([3113,3117],'dennによる、後続節を先行節の理由として提示する接続。'),
 'h26g5':([3153,3157],'ebenによる、同じ意志統合に基づくという根拠関係への焦点。'),
}
PRIMITIVES={
 'h26gu':('[a a a i d[e] '+FAMILY+' '+FAMILY+' '+FAMILY+' d d] c',
   ['baseline_node','focus_node','author','whole','scope','baseline_denial','focus_denial','reference','context'],
   '著者が同じ全体・対象範囲・固定基準の下で、比較上は許容に近い側でさえ否認される場合に、他方にはなおさら許されないという方向付きの比較を提示する。基準側と焦点側の箇所を区別し、三内容族には同じ対象列と固定基準を渡す。全対象が基準側で否認されるという断言、許容の数値的確率、物理的不可能性、逆向きの許可を加えず、引用内容を現実として実行しない。'),
 'h26gv':('[a a i d[e] '+FAMILY+' '+FAMILY+' d d] c',
   ['node','author','whole','scope','grounding','reference','context'],
   '著者が同じ全体・範囲の下で、指定した根拠関係そのものを、まさにそこで述べる根拠として特定して取り立てる提示。同じ対象列・固定基準を範囲と根拠内容族へ渡し、その関係の主体と限定を保持する。他の根拠すべての排除や唯一原因、引用内容の現実の実行は要求しない。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0013['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r5mp':'正確な君主・人民・共同体・法案の四対象列から、同じ固定基準・候補についてr5mbの全仮定範囲を返す。比較対象の許可・禁止・実行を先に範囲へ加えない。',
 'r5mq':'同じ四対象列の人民・共同体・法案をr5mdへ射影し、人民自身の同じ決定への明示的な否認を返す。君主の同一性を人民側の禁止へ混入しない。',
 'r5mr':'同じ四対象列をr5meへ渡し、同じ人民について君主が同じ法案を採択することへの明示的な否認を返す。',
 'r5ms':'正確な君主・人民・共同体の三対象列から、同じ基準・候補の役職範囲r5mmを返す。立法権威の正当性や意志統合を範囲へ先取りしない。',
 'r5mt':'固定政治基準h26b7における、人民自身に禁じられる同じ決定は君主にも禁じられるというr5mgの条件命題。第十文前半の引用内容。',
 'r5mu':'固定政治基準h26b7における、全人民意志の統合に立法権威の根拠を置き、その統合を権威の必要条件とするr5mn。第十文理由節の引用内容。',
 'r5mv':'第十文全体と二節を同じ著者・段落へ帰属し、前文との対照、人民側でさえ禁じられる場合の君主側へのなおさらの否認、後半から前半への理由提示、同じ根拠関係への焦点、提示順序を結ぶ。中心内容はr5moのまま保持し、引用された決定や正当な権威を現実として断言しない。',
}
LIMITS=[
 'u0013第十文[2986,3225)の203非空白文字全体を対象とする。beschließenは同じ人民の共同生活を拘束する公的規律の採択と読む。要求・許可・資格・権能とその維持変更を含む全条項を保持し、宗教制度だけに限定しない。',
 'Was ... dasは全法案と候補にわたる条件付きの対応であり、人民が一切の決定を禁じられるという断言ではない。darf nichtは明示的な負極性の規範要求として保持し、積極的許可の不存在や実行不能から禁止を補わない。',
 'über sich selbstとüber das Volkは同じ人民・共同体・法案を保つ。前者の決定主体は人民自身、後者は同じ共同体の君主。君主の役職と採択を同一点で結び、役職の存在から正当な権威・個別法の許可・実際の採択を導かない。',
 'nicht einmal ... noch wenigerは、人民自身でさえ許されない場合に君主にはなおさら許されないという方向付き比較。同じ四対象列・固定基準を共有する。数値的な許容度や禁止の物理的強度、人民に許される場合の君主への逆向きの許可は追加しない。',
 'gesammten Volkswillenは、先の立法の試金石と同じ、理性的に可能な人民の自己賦課に関する公的な引受けの全範囲という規範的な読解。人民全成員と関連全法案を固定し、現在の全員一致や多数決、実際の全採択法へ置換しない。可能な全法案の同時採択も要求しない。',
 'in dem seinigen vereinigtは、同じ君主自身の公的意志への構成的な取り込みと、その全引受け範囲を過不足なく保つことを要求する。一部の代表や偶然の選択一致では足りない。sein、er、seinigenは同じ君主を受ける。',
 'gesetzgebendes Ansehenは正当な立法上の資格・権威、beruht daraufは意志統合に置かれる規範的な根拠と読む。その統合を権威の必要条件とし、十分条件へ逆転しない。現に全君主が正当であるという主張も追加しない。',
 'aberは前文の本人・後代の放棄評価から、同じ人々に関わる政治的決定への対照。先行命題を撤回しない。dennは全人民意志を根拠とする後半を、君主への制約を述べる前半の理由として提示する。規範上の根拠関係と著者の論述上の理由は別に保持する。',
 'ebenはまさにその意志統合に基づくという根拠関係への焦点であり、他の根拠をすべて排除する唯一性を加えない。全体・二節・比較と焦点を同じ著者と段落へ帰属し、引用された内容をその帰属から現実として実行しない。',
 '全語句との対応と通読は明示読解の下でのアシスタントの判断であり、有限検査からの自動同値証明、独立査読、唯一の歴史解釈ではない。第六段落残部と二作品全体は未完である。',
]
NODES=('h26gd',*NODE_INFO)
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    def emit(n,names,body):return 'd '+n+'[bindings j[a] reference d] e[b candidate['+bind(names,body)+']].\n'
    text=''
    for n,names,target,args in (
        ('r5mp',FOUR_NAMES,'r5mb',FOUR_NAMES),('r5mq',FOUR_NAMES,'r5md',FOUR_NAMES[1:]),
        ('r5mr',FOUR_NAMES,'r5me',FOUR_NAMES),('r5ms',THREE_NAMES,'r5mm',THREE_NAMES)):
        text+=emit(n,names,'k '+target+'['+' '.join('v '+name for name in args)+' v reference v candidate]')
    for n,target in (('r5mt','r5mg'),('r5mu','r5mn')):
        text+='d '+n+'[] e[b point[t[k '+target+'['+REF+']][v point]]].\n'
    a='k wa[]';whole='r d[k r5mo[]]';q=lambda n:'r c[p '+n+']'
    clauses=['k h236i[k '+node+'[] '+a+' r d[k '+target+'[]] '+CTX+']' for node,target in (('h26gw','r5mo'),('h26gx','r5mt'),('h26gy','r5mu'))]
    clauses += [
        'k h222q[k h26gz[] '+a+' k h26gd[] r b[k r5l3[]] k h26gw[] r b[k r5mo[]] r[p r5l4] '+CTX+']',
        'k h26gu[k h26g2[] k h26g3[] '+a+' '+whole+' '+q('r5mp')+' '+q('r5mq')+' '+q('r5mr')+' '+REF+' '+CTX+']',
        'k h26gv[k h26g5[] '+a+' '+whole+' '+q('r5ms')+' '+q('r5ml')+' '+REF+' '+CTX+']',
        'k ud['+a+' i[node a][e[v node][k h26gy[]]] k h26gx[] '+CTX+']',
    ]
    edges=(('h26gd','h26gw'),('h26gx','h26gy'),('h26gz','h26g2'),('h26g2','h26g3'),('h26g3','h26g4'),('h26g4','h26g5'))
    clauses+=['k ue[k '+x+'[] k '+y+'[] '+CTX+']' for x,y in edges]
    distinct=['u[e[k '+x+'[]][k '+y+'[]]]' for i,x in enumerate(NODES) for y in NODES[i+1:]]
    clauses += [both(*distinct[i:i+12]) for i in range(0,len(distinct),12)]
    text+='d r5mv[] c['+both(*clauses)+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r5mv',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='monarchical_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/personal-renunciation-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
