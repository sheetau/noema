"""Integrate the same government's manifest example with explanatory discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import quantify
from scripts.compose_spreading_spirit_sentence import RULERS,FOREIGN,DESTINATIONS,REF,ANCHOR,AUTHOR,args,fields,quant,qualified

PARENT='examples/v016/kant-spreading-spirit-sentence.noema';PARENT_BASIS='data/spreading-spirit-sentence-basis-v1.json'
DEPENDENCIES=('data/manifest-example-basis-v1.json',)
FULL='examples/v016/kant-manifest-example-sentence.noema';CORE='examples/v016/manifest-example-sentence-core.noema'
BASIS='data/manifest-example-sentence-basis-v1.json';ANNOTATIONS='data/manifest-example-sentence-identifiers-v1.json'
CTX='k h26q2[]';C3='i d[e]';EIGHT='h['+'a '*8+'d]'
EXTRAS=('sourcegovernment','sourcegroup','sourcetopic','targetgroup','targettopic','example')
PRIMITIVES={
 'h26q2':('[] d',[],'固定原文kant-1784:u0015第四文を著者が述べる論述文脈。内容の固定基準h26ppと本文現在h26kn(h26km)は第三文と共有し、照応時に別の基準や評価点へ移さない。'),
 'h26q3':('[a a '+C3+' '+C3+' d] c',['node','author','explained','reason','context'],
   '著者が指定箇所で、後者の内容を前者が成り立つとする説明上の理由として提示する。理由の向きを保ち、単なる並列、客観的な十分原因、論理的含意や証明の成功、受け手の実際の納得とは区別する。引用内容をこの関係から実行しない。'),
 'h26q4':('[a a '+C3+' '+C3+' '+C3+' d] c',['node','author','whole','background','focus','context'],
   '著者が同じ全体内で、指定背景から焦点内容まで退ける見通しに抗して、なお焦点を保持するものとして取り立てる。背景の撤回、実際の読者の期待、論理的矛盾、焦点内容の真理の実行を追加しない。'),
 'h26q5':('[a a a '+C3+' i d['+EIGHT+' c] i d['+EIGHT+' c] i['+EIGHT+' a] d d] c',
   ['mention','author','antecedent_node','whole','prior_scope','extended_scope','referent_projection','reference','context'],
   '著者が指定表現で、先行箇所の八個体と基準を引数に取る範囲から、同じ引数の拡張範囲へ引き継いだ対象を参照する。どの個体を指すかは同じ引数列への射影記述で指定する。全体内の量化の下で同じ証人を共有し、独立に選んだ別の証人や類似した別対象へ取り替えない。範囲の包含と射影は合成側で構成し、この談話関係自体は引用内容の真理を実行しない。'),
}
NODE_INFO={
 'h26ra':([1050,1209],'第四文全体。'),
 'h26rb':([1050,1054],'Dennの前文に対する説明上の理由提示。'),
 'h26rc':([1067,1073],'dieserの同じ政府への照応。'),
 'h26rd':([1074,1078],'dochの留保に抗する提示。'),
 'h26re':([1079,1091],'ein Beispielの先行自由例。'),
 'h26rf':([1097,1209],'daß以下の、実例により支持される内容。'),
 'h26rg':([991,1034],'前文のeiner sich selbst mißverstehenden Regierungという照応元。'),
}
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0015['+str(span[0])+','+str(span[1])+')の'+m) for n,(span,m) in NODE_INFO.items()})
MEANINGS={
 'r6ai':'前文と同じ君主・職・共同体と外国政府・職・共同体の下で、元の政府・対象集団・宗教主題の実例を、外国側の同じ対象集団・主題の懸念の不在へr6afで結ぶ。事例と評価は同じ本文現在とし、元の君主と政府組織を同一個体へ強制しない。',
 'r6aj':'前文と同じ八対象と基準のr57lを保持し、その同じ政府へr6aiの明瞭な実例が示されるように、元の政府・二集団・二主題・例の証人を存在量化する。新しい外国政府を別に選ばず、前文の証人を拡張する。',
 'r6ak':'同じ八対象列の第四位置である政府を返す射影。dieserの参照先を元の君主・出発者・外国の取得者から区別し、先行・拡張範囲に共通の対象として指す。',
 'r6al':'同じ元の君主・最高職・共同体について、共通出発者からの国内の経路と、r6ajの同じ国外経路に実例の提示を加えた証人を結ぶ。前文r57mの内外経路を保ち、別の出発者や別政府の例示だけでは満たさない。',
 'r6am':'前文と同じ限定君主r53bの全組について、同じ本文現在の限定が成り立つ場合にr6alを要求する全文内容。前文の存在証人を共同で拡張する読みを明示し、全外国政府への無制限な全称や実在する特定の王の名を追加しない。',
 'r6an':'第四文の全文を第三文と同じ固定基準へ閉じる。外側の評価点を変えて本文現在や事例点を動かさない。',
 'r6ao':'第四文全文を著者へ帰属し、Dennによる前文への理由提示、dochの先行困難にもかかわらず示される例の取り立て、dieserの同じ政府への射影付き照応、先行二文の自由の型の継承、本文順序と箇所の区別を結ぶ。引用の真理を実行しない。',
}
LIMITS=[
 '固定原文u0015第四文[1050,1209)の134非空白文字。先行三文と同じ一般的な君主条件を保ち、同じ内外への広がりの証人を、同じ外国政府に明瞭な例が示される証人へ拡張して読む。全世界の各政府への主張や、独立の存在証人を同じだとする処理にはしない。',
 'dieserは前文の自己誤解する政府を受ける。r6ajが同じr57lの八対象を保持し、r6akで政府を射影する。政府を元の君主や取得者の個人へ同一視せず、政府の自己誤解の撤回や実際の納得は要求しない。',
 'ein Beispielは先行二文で示された自由の型が、同じ元の統治圏で平穏・一致と共存する実例。現在の実例として読むため事例点を先行文と同じ本文現在に置く。元の最高職と共同体をr6afの実例側へ渡し、政府組織はその職に属する公的主体として構成する。国名・日付・例の唯一性は補わない。',
 '例から対象政府側の内容への支持は、政府間の相違を踏まえた実質的な根拠と明瞭さであり、単なる話題の一致や一例からの形式的演繹ではない。利用可能な情報と把握可能性は政府の実際の信念から分ける。leuchtet vorはこの明瞭な根拠提示と読み、光源や照明の現実の出来事を加えない。',
 'daß以下は、自由条件の下で同じ共同体の公共の平穏か一致への危害を根拠を持って見込む候補が一つもないという閉じた支持対象。今だけの無害、全未来の無害の保証、心理的不安の不在、一方の安全だけに替えない。自由条件の非空性・関連候補の全評価・未知の拒否はr577に保つ。',
 'Dennは、障害のある国外にも自由の精神が広がるという前文を、明瞭な実例が示されているという後続内容によって説明する提示。dochは、自己誤解と外的障害があってもその例を退けられないという取り立てと読む。因果の実証、努力の不要性、読者の実際の驚きは追加しない。',
 '原刊492頁を拡大再読すると末尾はseiであり、旧照合v1のistは誤読だった。訂正記録v2を採用し、固定本文・AAと接続法の読みが一致することを確認した。旧記録やそれを参照する過去証拠は履歴として保存し、新しい判断で版差の存在を主張しない。',
 '全文判断は明示した解釈に基づくアシスタントの原文再読判断であり、有限検査による自動同義証明や独立査読ではない。第五文・u0016/u0017・Einsteinは未完。既存17単位判断と先行三文899文字を保存する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def definitions():
    source=('sourcegovernment','rulingoffice','community','sourcegroup','sourcetopic')
    target=('government','foreignoffice','foreigncommunity','targetgroup','targettopic')
    text='d r6ai['+fields((*FOREIGN,*EXTRAS))+' reference d] c[k r6af[v example '+args((*source,*target))+' v reference '+ANCHOR+' '+ANCHOR+']].\n'
    text+='d r6aj['+fields(FOREIGN)+' reference d] c['+both('k r57l['+args(FOREIGN)+' v reference]',
        quant(EXTRAS,'k r6ai['+args((*FOREIGN,*EXTRAS))+' v reference]','g'))+'].\n'
    text+='d r6ak['+fields(FOREIGN)+' reference d] a[v government].\n'
    domestic=quant(('target',),'k r57j['+args((*RULERS,'origin','target'))+' v reference]','g')
    abroad=quant(DESTINATIONS,'k r6aj['+args(FOREIGN)+' v reference]','g')
    text+='d r6al['+fields(RULERS)+' reference d] c['+quant(('origin',),both(domestic,abroad),'g')+'].\n'
    text+='d r6am[reference d] e[b outer['+quant(RULERS,'y['+qualified()+'][k r6al['+args(RULERS)+' v reference]]')+']].\n'
    text+='d r6an[] e[k r6am['+REF+']].\n'
    return text
def discourse():
    node=lambda n:'k '+n+'[]';code=lambda n:'r d[k '+n+'[]]'
    parts=['k h236i['+node('h26ra')+' '+AUTHOR+' '+code('r6an')+' '+CTX+']',
        'k h26q3['+node('h26rb')+' '+AUTHOR+' '+code('r57r')+' '+code('r6an')+' '+CTX+']',
        'k h26q4['+node('h26rd')+' '+AUTHOR+' '+code('r6an')+' '+code('r57u')+' '+code('r6an')+' '+CTX+']',
        'k h26q5['+node('h26rc')+' '+AUTHOR+' '+node('h26rg')+' '+code('r6an')+' r d[p r57l] r d[p r6aj] r[p r6ak] '+REF+' '+CTX+']']
    parts+=['k h26qe['+node('h26re')+' '+AUTHOR+' '+code(n)+' r c[k r57w[]] '+REF+' '+CTX+']' for n in ('r53k','r55s')]
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in (('h26qi','h26ra'),('h26rg','h26rc'),('h26re','h26rf'))]
    nodes=(*NODE_INFO,'h26qi');parts+=['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return 'd r6ao[] c['+both(*parts)+'].\n'
def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in closure(lib.document,['r6af']):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r6ao',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r6ao']),statements=[new])
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='manifest_example_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/spreading-spirit-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
