"""Integrate the second prince paragraph sentence and its a-fortiori extension."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_clerical_duty_scope import quantify
from scripts.compose_prince_sentence import ANCHOR

PARENT='examples/v016/kant-prince-sentence.noema';PARENT_BASIS='data/prince-sentence-basis-v1.json'
DEPENDENCIES=('data/all-offered-freedoms-basis-v1.json',)
FULL='examples/v016/kant-public-offers-sentence.noema';CORE='examples/v016/public-offers-sentence-core.noema'
BASIS='data/public-offers-sentence-basis-v1.json';ANNOTATIONS='data/public-offers-sentence-identifiers-v1.json'
REF='k h26pa[]';CTX='k h26pb[]';AUTHOR='k wa[]'
T3='i c[h[a a a] e]';T4='i c[h[a a a a] e]';WHOLE='i d[e]'
RULERS=('ruler','rulingoffice','community')
CLERICS=('person','office','church','creed','subject','scholar')
PRIMITIVES={
 'h26o7':('[a a a a '+WHOLE+' '+T3+' '+T3+' '+T3+' '+T4+' '+T4+' d d] c',
   ['node','author','baseline_node','focus_node','whole','ruler_scope','baseline_permission','focus_permission','other_people','nonrestriction','reference','context'],
   '著者が同じ全体・固定基準で、基準側の許容を維持しつつ、その職務条件と比較側の職務制限の不在を対照し、比較側の許容をなおさら認める理由があるものとして提示する。三つの性質は同じ統治者・統治職・共同体を共有し、他者範囲と無制約の二性質はさらに同じ本人を共有する。論述の向きと対象条件を引用へ保ち、許可の数値的強度、全義務の不存在、論理的妥当性又は引用内容の現実の真理を導かない。否認側のなおさらを表すh26guと区別した、許容側の対照と比較的な理由付けである。'),
 'h26pa':('[] d',[],'固定原文kant-1784:u0015第二文における、聖職者・採用信条・見解・全比較範囲・職務規範・敬意評価の解釈基準。先行文の君主条件は既存の基準を保って照応し、本文の現在点と提示文脈は別に共有する。結果で基準を変更しない。'),
 'h26pb':('[] d',[],'固定原文kant-1784:u0015第二文を同じ著者が提示する第八段落の論述文脈。内容の解釈基準・現在点とは分け、前文からの順序と同じ文内の二節の対照をここへ帰属する。'),
}
NODE_INFO={
 'h26pc':([574,889],'Unter ihmから第二文末までの全文。'),
 'h26pd':([574,813],'Unter ihmからdarlegen;までの聖職者側の節。'),
 'h26pe':([814,889],'noch mehr aberから第二文末までの他者側の節。'),
 'h26pf':([814,828],'noch mehr aberの対照と、なおさらという論述接続。'),
}
# The source checker verifies the exact offsets, including the semicolon.
PRIMITIVES.update({n:('[] a',[],'固定原文kant-1784:u0015['+str(span[0])+','+str(span[1])+')の'+meaning) for n,(span,meaning) in NODE_INFO.items()})
MEANINGS={
 'r55j':'同じ本人・固定基準・現在点について、ある職務・教会・採用信条・主題の組でr54yの敬意に値する同じ聖職者に該当する。学識者の立場は同じ本人のh247dを用い、先行節で扱う人物群の除外範囲を定める。',
 'r55k':'先行文と同じ限定君主の同じ統治職・共同体の下にあるr54xの本人で、同じ現在点のr55jの先行群には属さない。jeder andereの他者を話者以外や、別の国の任意の人へ取り違えない。',
 'r55l':'同じ限定君主・統治職・共同体について、r55kの全ての他者のうち、公的提示全般が全職務義務に制限されないr55hの同じ本人に、その全候補へのr55iの自由を要求する。無制約からの定理ではなく本文の条件命題であり、対象者の存在を補わない。',
 'r55m':'同じ統治者・統治職・共同体・固定基準について、全本人・全聖職者職務・全教会・全信条・全主題・全学識者の組へr55dの条件付き自由を適用する。資格や許可を満たす代表例だけへ全称範囲を縮めない。',
 'r55n':'全統治者・全統治職・全共同体について、r55mの聖職者側とr55lの他者側を連言する第二文の内容。先行限定君主の条件と同じ本文現在点を内部に保ち、外側の評価点で現在を動かさない。',
 'r55o':'本文の固定基準のr55mを、同じ統治者・統治職・共同体の三引数の性質として閉じる。なおさらの比較の基準側である。',
 'r55p':'本文の固定基準のr55lを、r55oと同じ三引数の性質として閉じる。なおさらの比較側であり、先行の聖職者の自由を撤回しない。',
 'r55q':'本文のr55kの他者範囲を、同じ統治者・統治職・共同体・本人の四引数の性質として閉じる。',
 'r55r':'同じ四引数の本人について、同じ本文基準・現在点で公的提示全般が全職務義務に制限されないr55hを返す。三つの統治引数はr55qとの共用束縛で、無制約だけから統治資格を導かない。',
 'r55s':'本文の固定基準へr55nを接続した全文内容。二節の全称・条件・同じ人物への参照を保持する。',
 'r55t':'本文のr55oを全統治者・統治職・共同体へ量化した前節の内容。全文の前半と同じ範囲に固定する。',
 'r55u':'本文のr55pを全統治者・統治職・共同体へ量化した後節の内容。全文の後半と同じ範囲に固定する。',
 'r55v':'全文と二節を同じ著者へ帰属し、同じ限定君主の下の前節の許容を保ったまま、他者の職務制限不在を根拠とするなおさらの許容と対照を提示する。本文順序と異なる箇所を保持し、引用された自由・義務・判断・発表を現実として実行しない。',
}
LIMITS=[
 '固定原文u0015第二文[574,889)の273非空白文字を対象とする。Unter ihmは第一文の条件を満たす同じ一般的君主・統治職・共同体の下と読み、特定の実在王を追加しない。現在点は先行文と同じh26kn(h26km)に固定し、内容基準と著者の提示文脈は第二文用に分ける。',
 'verehrungswürdige Geistlicheは聖職者として敬意に値するという評価による限定として読む。真の同じ聖職者性質と非空の全適合基準を要求し、現実の人気・敬意・発話・服従とは分ける。単なる慣習的敬称や全聖職者への非制限的な添え評価が唯一の読みだとはしない。',
 'jeder andereは、同じ君主の下の人々から前節の敬意に値する聖職者群を除く。聖職者という身分だけで一律に除外せず、前節と同じ人物条件の存在を調べる。各人物の同じ学識者の立場で、全職務義務が該当公的提示全般を制限しないことを関係節の条件に置く。',
 '判断は本人の保持する肯定見解、洞察は同じ内容の把握と根拠ある判断として扱う。公に提出する本人の認識上の立場であり、全内容の客観的真理を著者が保証するものではない。内容・受容・発表・審査目的は同じ候補内に保持し、許可時点に実際の発表や審査成功を要求しない。',
 '採用信条との相違は同じ論点の内容を全関連候補で比べた差であり、発表項目群の少なくとも一項目での相違とする。厳密な少数、他の全論点での一致、全信条の否認又は教示基準への不適合だけとはしない。非聖職者の他者へ教会・採用信条を必須にはしない。',
 '自由は同じ公的提示への積極的許可と反対要求の不在。unbeschadetは同じ職務要求の非免除と、同じ一候補での発表・全義務履行の共充足として読む。物理的能力・因果的無害性・実際の履行や法的優先を追加しない。義務は既存の段階1規範形式で表す全要求を直接量化する。',
 '世界は本来の全読者公衆。公的理性使用と本人名義の発表を同じ一活動へ結び、少なくとも一人の公衆による同じ内容の検討を目的とする。全世界の受領・理解・賛同・審査の実現、特定媒体や学識者の職業免許を追加しない。',
 '全活動・全公衆・任意の有限判断列・洞察列を量化し、候補範囲は許可・義務履行・審査成功の結果で狭めない。該当人物の発表候補には非空性を要求するが、君主や対象人物の現実の存在を一般条件から追加しない。全列・全規範目標の有限列挙は拒否し、限定診断を全域証明にしない。',
 'noch mehr aberは前節を維持した対照と、職務義務を保つ側にも自由がある以上、職務制限のない他者にはなおさらという許容側の理由付けとして提示する。許可の数値的大きさや心理的確信、論理的妥当性・真理の自動導出ではない。',
 '見解・信条の比較範囲、制度的な規範候補、敬意の全適合基準は、明示した意味規約の解釈入力である。その正当性や現実の網羅性を有限モデルから証明しない。各項目の内容と基準はNoema記述で保持し、一文の真偽だけを返す基本記号を置かない。',
 '全文の判断は原文全語句と作用域を再読した明示解釈の下でのアシスタント判断である。有限検査による自動同値証明や独立査読ではない。第三文以後と二作品全体は未完であり、第四文のist/sei版差は保持する。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)
def args(ns):return ' '.join('v '+n for n in ns)
def fields(ns):return ' '.join(n+' a' for n in ns)
def forall(ns,body):return quantify([(n,'a') for n in ns],body)

def definitions():
    scholar='k h247d[v person v reference]'
    excluded='k r54y[v person v office v church v creed v subject '+scholar+' v reference v anchor]'
    text='d r55j[person a reference d anchor d] c['+quantify([(n,'a') for n in ('office','church','creed','subject')],excluded,'g')+'].\n'
    frame=fields(RULERS)+' person a reference d'
    text+='d r55k['+frame+'] c['+both('k r54x['+args(RULERS)+' v person]',
        'u[k r55j[v person v reference '+ANCHOR+']]')+'].\n'
    eligible=both('k r55k['+args(RULERS)+' v person v reference]','k r55h[v person '+scholar+' v reference '+ANCHOR+']')
    permitted='k r55i[v person '+scholar+' v reference '+ANCHOR+']'
    text+='d r55l['+fields(RULERS)+' reference d] c['+forall(('person',),'y['+eligible+']['+permitted+']')+'].\n'
    text+='d r55m['+fields(RULERS)+' reference d] c['+forall(CLERICS,'k r55d['+args((*RULERS,*CLERICS))+' v reference]')+'].\n'
    bothsides=both('k r55m['+args(RULERS)+' v reference]','k r55l['+args(RULERS)+' v reference]')
    text+='d r55n[reference d] e[b outer['+forall(RULERS,bothsides)+']].\n'
    for name,target in (('r55o','r55m'),('r55p','r55l')):
        text+='d '+name+'[] h[a a a] e[i['+fields(RULERS)+'][b outer[k '+target+'['+args(RULERS)+' '+REF+']]]].\n'
    text+='d r55q[] h[a a a a] e[i['+fields((*RULERS,'person'))+'][b outer[k r55k['+args((*RULERS,'person'))+' '+REF+']]]].\n'
    text+='d r55r[] h[a a a a] e[i['+fields((*RULERS,'person'))+'][b outer[k r55h[v person k h247d[v person '+REF+'] '+REF+' '+ANCHOR+']]]].\n'
    text+='d r55s[] e[k r55n['+REF+']].\n'
    for name,target in (('r55t','r55o'),('r55u','r55p')):
        text+='d '+name+'[] e[b outer['+forall(RULERS,'t[c[k '+target+'[]]['+args(RULERS)+']]['+ANCHOR+']')+']].\n'
    return text

def discourse():
    node=lambda n:'k '+n+'[]';code=lambda n:'r d[k '+n+'[]]';profile=lambda n:'r c[k '+n+'[]]'
    parts=['k h236i['+node(n)+' '+AUTHOR+' '+code(t)+' '+CTX+']' for n,t in (('h26pc','r55s'),('h26pd','r55t'),('h26pe','r55u'))]
    parts+=['k h26o7['+node('h26pf')+' '+AUTHOR+' '+node('h26pd')+' '+node('h26pe')+' '+code('r55s')+' '+profile('r53b')+' '+profile('r55o')+' '+profile('r55p')+' '+profile('r55q')+' '+profile('r55r')+' '+REF+' '+CTX+']',
        'k ud['+AUTHOR+' i[node a][e[v node]['+node('h26pd')+']] '+node('h26pe')+' '+CTX+']']
    parts+=['k ue['+node(a)+' '+node(b)+' '+CTX+']' for a,b in (('h26oq','h26pc'),('h26pd','h26pe'))]
    nodes=(*NODE_INFO,'h26oq')
    parts+=['u[e['+node(a)+']['+node(b)+']]' for i,a in enumerate(nodes) for b in nodes[i+1:]]
    return 'd r55v[] c['+both(*parts)+'].\n'

def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in closure(lib.document,['r55d','r55h','r55i','r54y','r54x']):
            n=d['name'];e=lib.entries[n]
            if n in old.entries:assert d==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
            elif n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&(set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions()+discourse())
    added=doc['declarations'][len(old.document['declarations']):];ds={d['name']:d for d in added}
    new=dict(kind='assert',body=dict(kind='call',symbol='r55v',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,['r55v']),statements=[new])
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    paths=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='public_offers_sentence_under_explicit_reading',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,primitives=prims,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/prince-sentence-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
